# AI Meeting Recorder Agent — System Design

## Architecture Overview

The agent is built around a **chunked video pipeline**: OBS produces 2-minute mp4 segments continuously, and the agent processes each segment as it arrives — transcribing, embedding, and updating its context window incrementally. This gives the agent near-real-time awareness of the meeting without requiring a live audio stream.

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Meeting Capture Layer                        │
│   OBS 3.11 (2-min mp4 segments) → Watched Output Folder            │
└─────────────────────────────┬───────────────────────────────────────┘
                              │ new file event
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       Processing Pipeline                           │
│   File Watcher → FFmpeg (audio) → Faster-Whisper → Transcript       │
│                                        │                            │
│                                        ▼                            │
│                              Chunking Service                       │
│                                        │                            │
│                                        ▼                            │
│                         Embedding → Session Vector Store            │
│                                        │                            │
│                                        ▼                            │
│                           Rolling Summary Updater                   │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Intelligence Layer                          │
│                                                                     │
│   ┌──────────────────────┐     ┌──────────────────────────────┐    │
│   │  Static Knowledge DB │     │    Session Vector Store      │    │
│   │  (domain, project,   │     │    (this meeting transcript) │    │
│   │   industry trends)   │     └──────────────────────────────┘    │
│   └──────────┬───────────┘                   │                     │
│              └──────────────┬─────────────────┘                    │
│                             ▼                                       │
│                     LLM Agent (LangGraph)                           │
│                     - Query understanding                           │
│                     - Context retrieval (RAG)                       │
│                     - Response generation                           │
│                     - Gap & risk detection                          │
└─────────────────────────────┬───────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         Application Layer                           │
│   Chat UI (React)  │  REST API (FastAPI)  │  Document Export        │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Design

### 1. File Watcher (Watchdog)

Monitors the OBS output folder for new mp4 files.

```
Responsibilities:
  - Detect new mp4 files written by OBS
  - Debounce: wait for file write to complete before triggering (check file size stability)
  - Enqueue file path to processing queue

Config:
  watch_folder: str           # OBS output directory
  debounce_seconds: int       # default 3s — wait for OBS to finish writing
  segment_duration_secs: int  # expected 120s — for validation
```

**Debounce logic:** Poll file size every 1 second; trigger processing only when size is stable for 2+ consecutive checks. This prevents reading a partially-written mp4.

---

### 2. Audio Extraction Service (FFmpeg)

Extracts audio track from each mp4 segment.

```
Input:  path/to/segment_0001.mp4
Output: path/to/segment_0001.wav  (16kHz mono, PCM)

Command:
  ffmpeg -i segment_0001.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 segment_0001.wav
```

Runs as a subprocess call. On failure, logs error and skips segment (does not block pipeline).

---

### 3. Transcription Service (Faster-Whisper)

Transcribes audio to timestamped segments.

```python
Output schema:
{
  "session_id": "uuid",
  "segment_file": "segment_0001.mp4",
  "segment_index": 1,
  "segment_start_offset_secs": 120,   # cumulative offset in meeting
  "transcription": [
    {
      "start": 121.4,   # absolute time in meeting
      "end": 124.8,
      "text": "So the question is whether we go with a monolith or microservices.",
      "speaker": "SPEAKER_01"   # optional, from diarization
    }
  ]
}
```

- Model: `large-v3` for accuracy, `medium` for speed
- GPU preferred; falls back to CPU
- Per-segment absolute timestamps: `segment_index * segment_duration + relative_offset`

---

### 4. Chunking Service

Splits transcript into overlapping text chunks for embedding.

```
Strategy:
  - Chunk by time window (e.g., 60-second windows with 15-second overlap)
  - OR chunk by token count (e.g., 300 tokens with 50-token overlap)
  - Each chunk retains: start_time, end_time, speaker(s), text

Output per chunk:
{
  "chunk_id": "session_id::chunk_042",
  "session_id": "uuid",
  "start_time": 180.0,
  "end_time": 240.0,
  "speakers": ["SPEAKER_01", "SPEAKER_02"],
  "text": "..."
}
```

---

### 5. Embedding & Session Vector Store

Each chunk is embedded and stored in the session's isolated namespace.

```
Vector Store: ChromaDB (local) or FAISS
Collection naming: session_{session_id}_transcript

Metadata stored per chunk:
  - chunk_id, start_time, end_time, speakers, segment_index

Two namespaces:
  static_knowledge    → pre-meeting domain/project/industry docs (persists across sessions)
  session_transcript  → this meeting's chunks (session-scoped, archived after meeting)
```

**Static knowledge** is loaded once before the meeting starts and reused across sessions for the same project or domain.

---

### 6. Rolling Summary Updater

After each new segment is processed and embedded, the running summary is updated.

```
Trigger: every N new segments (default N=2, i.e., every ~4 minutes)

Input:
  - Previous rolling summary
  - New transcript chunks since last update

Prompt pattern (LLM call):
  "You are updating a running summary of a meeting in progress.
   Previous summary: {prev_summary}
   New content (last ~4 minutes): {new_chunks}
   Update the summary to reflect what has been discussed so far.
   Keep it factual and concise. Flag any new decisions, action items, or risks."

Output stored in: session.rolling_summary (DB field, overwritten each update)
```

This rolling summary is injected into the system prompt for every query — giving the LLM fast global meeting context without retrieving all chunks every time.

---

### 7. Voice Interface (STT + TTS)

Voice is the primary interaction mode during a meeting. The agent listens for a wake word or hotkey, captures the question, and speaks the response back — all without disrupting the meeting.

```
Activation:
  Option A — Wake word: "Hey Nexus" (using Porcupine or Vosk keyword detection)
  Option B — Hotkey: Ctrl+Space (using pynput, always-listening in background)

STT (question capture):
  - Open mic capture for 5–10 seconds after activation
  - Transcribe using Faster-Whisper (same model already loaded)
  - No extra model cost — reuses the transcription service

TTS (spoken response):
  - Generate spoken response via OpenAI TTS / ElevenLabs / Kokoro (local)
  - Route audio output ONLY to headset/earphone output device
  - Never route to system speakers or the OBS/meeting capture device
  - Use sounddevice or pyaudio with explicit output device selection

Audio device isolation (critical):
  - OBS captures: virtual audio cable or specific input device (meeting audio)
  - TTS output device: headset output (separate from OBS input)
  - Mic for voice queries: same or different mic from meeting mic — configurable
    Recommended: use a separate push-to-talk approach so query mic doesn't
    bleed into the meeting when you speak to the agent

Config:
  wake_word: str                  # e.g., "hey nexus"
  activation_hotkey: str          # e.g., "ctrl+space"
  stt_listen_duration_secs: int   # default 8
  tts_output_device: str          # e.g., "Headphones (Realtek Audio)"
  tts_provider: str               # openai | elevenlabs | kokoro (local)
  tts_voice: str                  # e.g., "alloy", "nova"
  also_show_in_chat: bool         # default true — display response in UI too
```

**Response length for voice:** TTS responses are automatically condensed to 2–3 sentences. The full detailed response is still shown in the chat UI. The agent is prompted: "Give a concise spoken answer (2-3 sentences). Full detail will be shown in the chat."

---

### 8. Agent Persona & Pre-Meeting Knowledge Loading

Before the meeting starts, the agent is configured with a **persona** and **knowledge brief**.

```python
PersonaConfig:
  name: str                        # e.g., "Nexus AI Recorder"
  role_description: str            # e.g., "Senior Solution Architect with expertise in..."
  domain_knowledge_docs: list[str] # file paths or doc IDs → embedded into static_knowledge
  industry_trends_docs: list[str]  # curated trend docs (PDF, Markdown, etc.)
  project_context_docs: list[str]  # project architecture, ADRs, prior meeting notes
  meeting_brief: MeetingBrief

MeetingBrief:
  title: str
  agenda: list[str]
  attendees: list[str]
  objectives: list[str]
  known_open_questions: list[str]
```

All `*_docs` are chunked, embedded, and stored in the `static_knowledge` namespace before the meeting begins. The `meeting_brief` is injected verbatim into the agent's system prompt so it understands the context and goals of the meeting from the start.

---

### 8. LLM Agent (LangGraph)

The core reasoning engine, implemented as a LangGraph state graph.

```
Nodes:
  classify_query            → mid-meeting or post-meeting? factual or analytical?
  retrieve_context          → hybrid retrieval: session transcript + static knowledge
  inject_summary            → prepend rolling summary to context (always)
  generate_response         → LLM call with assembled context
  detect_gaps               → identify unanswered questions and missing decisions
  update_understanding_doc  → append findings to the co-created document

System prompt includes:
  - Agent persona and role description
  - Meeting brief (title, agenda, objectives, known open questions)
  - Rolling summary of the meeting so far
  - Instruction: "Answer as an expert participant who was in this meeting.
                  If the answer is not in the transcript, reason from your
                  domain knowledge and clearly flag that you are doing so.
                  Always flag uncertainty."
```

**Retrieval strategy:**
- Query embedded → top-K chunks from `session_transcript` (vector search)
- Query embedded → top-K chunks from `static_knowledge` (vector search)
- Rolling summary always prepended (not retrieved)
- Optional cross-encoder re-ranker for relevance scoring

---

### 9. Chat Service & Session Management

```
Session lifecycle:
  PRE_MEETING   → persona loaded, knowledge indexed, folder watcher active
  IN_PROGRESS   → segments arriving, transcript accumulating, chat active (live mode)
  POST_MEETING  → full transcript available, brainstorming mode active
  ARCHIVED      → session stored, understanding document finalized

Session state (PostgreSQL):
  session_id, title, status, start_time, end_time
  rolling_summary          (text, updated live during meeting)
  understanding_document   (JSON / Markdown, built post-meeting)
  persona_config           (JSON)

Chat messages stored per session. Multi-turn context maintained by including
last N chat turns in the LLM prompt.
```

**Live mode indicator:** During `IN_PROGRESS`, the chat UI shows a live badge and the agent's responses include the timestamp of the latest processed segment so the human knows how current the context is. If asked about something after that timestamp, the agent explicitly says it hasn't processed audio past that point yet.

---

### 10. Collaborative Understanding Document

Post-meeting, the agent shifts into **brainstorming mode**. It does not generate a dump — it engages humans to co-create a structured document through dialogue.

```json
{
  "session_id": "uuid",
  "version": 3,
  "sections": {
    "context_and_objectives": "...",
    "key_decisions": [
      {"decision": "...", "rationale": "...", "owner": "..."}
    ],
    "action_items": [
      {"task": "...", "owner": "...", "deadline": "..."}
    ],
    "open_questions": ["...", "..."],
    "gaps_identified": ["...", "..."],
    "risks_and_concerns": ["...", "..."],
    "expert_commentary": "...",
    "next_steps": ["...", "..."]
  }
}
```

The agent proactively asks clarifying questions to fill gaps:

- "You discussed migrating the auth service — was the target platform decided?"
- "The timeline was mentioned but no deadline was agreed. Can you confirm?"
- "I noticed a potential conflict between the caching strategy and the consistency requirement raised at 14:32. Was this resolved?"

The `expert_commentary` section is where the agent contributes its own perspective from domain and industry knowledge — not just what was said, but what it means and what was missed.

Document is exported as Markdown or PDF on request.

---

## Data Flow Diagrams

### Segment Processing Flow

```
OBS writes segment_0042.mp4 to watched folder
    │
    ▼
File Watcher (debounce 3s) → enqueue to processing queue
    │
    ▼
FFmpeg → segment_0042.wav (16kHz mono)
    │
    ▼
Faster-Whisper → [{start, end, text, speaker}, ...]
    │
    ▼
Chunking Service → [{chunk_id, start, end, text}, ...]
    │
    ├──→ Embed → Session Vector Store (ChromaDB)
    │
    └──→ (every 2 segments) Rolling Summary Updater → LLM → updated summary → DB
```

### Mid-Meeting Query Flow

```
                    ┌─────────────────────────────────┐
                    │         Human Input              │
                    │                                  │
  Wake word /       │  Voice query        Text query   │
  hotkey            │  (mic capture)      (chat UI)    │
    │               └────────┬────────────────┬────────┘
    │                        │                │
    ▼                        ▼                │
Activation            Faster-Whisper          │
listener              STT → text query        │
                             │                │
                             └────────┬───────┘
                                      │
                                      ▼
                          FastAPI POST /sessions/{id}/chat
                                      │
                                      ▼
                              LangGraph Agent
                          ├── inject:   rolling_summary
                          ├── retrieve: top-K session_transcript
                          ├── retrieve: top-K static_knowledge
                          └── generate: LLM → full response
                                      │
                    ┌─────────────────┴──────────────────┐
                    │                                     │
                    ▼                                     ▼
           TTS (condensed 2-3 sentences)        Chat UI (full response)
           → routed to earphone only            + "Context as of [timestamp]"
           (never into meeting audio)
```

### Post-Meeting Brainstorming Flow

```
Meeting ends → session status → POST_MEETING
    │
    ▼
Agent generates initial draft of understanding document
    │
    ▼
Human reviews → asks questions → agent elaborates
    │
    ▼
Agent detects gaps → asks clarifying questions proactively
    │
    ▼
Understanding document updated incrementally through dialogue
    │
    ▼
Human confirms → Export as Markdown / PDF
```

---

## Teams Bot Design (Phase 3)

```
Components:
  Azure Bot Service      → bot registration and messaging endpoint
  Microsoft Graph API    → meeting join, recording trigger, transcript fetch
  Graph Webhook          → notification when recording is available

Flow:
  Scheduled trigger / manual start
      → Bot joins meeting via Graph API as named participant
      → Recording triggered
      → On meeting end: Graph API webhook fires
      → Recording downloaded → same processing pipeline as local agent
      → Understanding document generated
      → Summary + open questions posted to Teams channel
      → Discussion thread created with action items and gaps
```

---

## Security Design

| Concern | Approach |
|---|---|
| Audio / transcript privacy | MVP: all data stays on local machine. LLM API is the only external call. |
| Fully offline option | Use local Llama/Ollama model — no data leaves the machine at all |
| API keys | Loaded from `.env` (never committed to git). |
| Teams bot auth | OAuth2 with least-privilege Graph API scopes |
| Stored transcripts | Encrypted at rest (Phase 2+) |
| `.env` files | Excluded from git via `.gitignore`. Never committed. |

---

## Scalability

- **MVP**: single machine, ChromaDB/FAISS, local or API-based LLM
- **Phase 3+**: containerised microservices, Celery workers for segment processing, cloud vector store (Pinecone/Weaviate), S3 for recordings
- **Horizontal scaling**: stateless processing workers; session state in PostgreSQL; queue-based segment pipeline (Redis / Kafka)

---

## Performance Targets

| Operation | Target |
|---|---|
| File watcher → processing trigger | < 5s after OBS finishes writing |
| FFmpeg audio extraction | < 5s per 2-min segment |
| Faster-Whisper transcription (GPU) | < 15s per 2-min segment |
| Embedding + vector store indexing | < 5s per segment |
| Total segment-to-searchable latency | < 30s per segment |
| LLM chat response | < 5s p95 |
| Voice STT (question transcription) | < 2s for 8-second clip |
| TTS generation + playback start | < 3s after LLM response |
| End-to-end voice round trip | < 10s (activation → spoken answer) |
| Rolling summary update | < 10s (background, non-blocking to chat) |
