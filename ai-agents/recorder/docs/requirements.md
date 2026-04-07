# AI Meeting Recorder Agent — Requirements

## Objective

Build an LLM-powered Meeting Intelligence Agent that joins meetings as an **expert participant** — with pre-loaded domain knowledge, industry awareness, and project context — captures the meeting, provides real-time Q&A during the meeting, and collaborates with humans after the meeting to produce a structured understanding document.

The agent operates like a senior expert who was in the room: it understands what was said, can answer questions about it, identifies gaps, flags risks, and helps the team arrive at shared understanding.

---

## System Variants

### 1. Local Agent (Primary MVP)

A locally running Python app that:

- Monitors OBS-generated mp4 segments (2-min chunks) from a folder
- Transcribes each chunk incrementally as it arrives
- Maintains a rolling meeting context window
- Answers questions in real-time via a chat UI (during or after the meeting)
- Produces a collaborative understanding document post-meeting

### 2. Teams Bot Participant (Automation Layer — Phase 3)

- Joins meetings automatically as a named bot participant
- Records the meeting via Microsoft Graph API
- Processes transcript and posts insights to a Teams channel
- Creates a dedicated discussion thread with gaps and open questions

---

## Functional Requirements

### F1 — Agent Persona & Pre-Meeting Knowledge Loading

The agent must be configurable with **prior knowledge** before the meeting starts, acting like a human expert who prepared for the call.

- **Domain Knowledge**: industry concepts, terminology, architectural patterns, best practices
- **Industry Trends**: recent developments, emerging technologies relevant to the meeting topic
- **Project Context**: project docs, architecture decisions, codebase summaries, prior meeting notes
- **Meeting Brief**: agenda, attendees, stated objectives, known open questions

The agent loads this knowledge into a vector store before the meeting and uses it to reason about what is said — not just transcribe it.

### F2 — OBS Chunked Video Pipeline

OBS is configured to produce continuous 2-minute mp4 segments into a watched folder. The agent must:

- **Watch** the output folder for new mp4 files (file watcher with debounce)
- **Extract audio** from each new segment using FFmpeg
- **Transcribe** the audio using Faster-Whisper, producing timestamped segments
- **Accumulate** the transcript across all segments into a growing meeting context
- **Re-embed and index** new transcript chunks into the session's vector store after each segment
- **Maintain a rolling summary** of the meeting so far, updated every N segments

This enables the agent to answer questions about anything said earlier in the meeting, even before it ends.

### F3 — Real-Time Q&A During Meeting (Text + Voice)

During the meeting (while OBS is still recording), humans can ask the agent questions via **text or voice**. Voice is the primary interaction mode — typing during a meeting is disruptive and breaks focus.

The agent answers using:

- All transcript chunks processed so far
- Pre-loaded domain and project knowledge
- Its running summary of the meeting context

**Voice interaction flow:**
1. Human activates the agent with a wake word or hotkey (e.g., "Hey Nexus" or `Ctrl+Space`)
2. Agent opens a short STT listening window (captures the question)
3. Question is transcribed using Whisper (same model already running)
4. Agent generates a response
5. Response is spoken back via TTS — quietly, through the user's earphone, not into the meeting audio
6. Optionally, the response also appears in the chat UI for reference

**Critical design constraint:** The agent's spoken responses must never bleed into the meeting's microphone or OBS capture. This is achieved by routing TTS output to a separate audio device (earphones/headset), not the system speaker.

Example mid-meeting voice queries:
- "Hey Nexus, what did they decide about the auth service?"
- "Is the approach they're proposing consistent with our architecture?"
- "What are the risks in what was just discussed?"

The agent should clearly indicate if a question references content not yet captured (e.g., "I haven't processed audio past [timestamp] yet").

**Voice STT:** Reuses the Faster-Whisper model already loaded — no additional model needed for question transcription.

### F4 — Post-Meeting Collaborative Understanding Document

After the meeting ends, the agent collaborates interactively with the humans present to produce a structured **Meeting Understanding Document**. This is not an automatic summary — it is a co-created artifact built through dialogue.

The document includes:

| Section | Description |
|---|---|
| Context & Objectives | What the meeting was about and why it was held |
| Key Decisions | Decisions made, with rationale and owners |
| Action Items | Tasks, owners, and deadlines |
| Open Questions | Questions raised but not resolved |
| Gaps Identified | Topics that needed more depth or were skipped |
| Risks & Concerns | Risks flagged during discussion |
| Expert Commentary | Agent's perspective based on domain/industry knowledge |
| Next Steps | Agreed follow-up path |

The agent actively asks clarifying questions to fill gaps: "You mentioned migrating the database — was the target platform decided?" It does not just passively summarize.

### F5 — Transcription

- Full verbatim transcription with timestamps (not summaries)
- Per-segment transcription as each mp4 chunk arrives
- Optional speaker diarization (who said what)
- Transcript stored persistently per session

### F6 — LLM Reasoning

Generate on demand or post-meeting:

- Detailed summaries
- Decisions log
- Action items with owners
- Risk register
- Gap analysis
- Answers to arbitrary user queries

### F7 — Chat & Voice Interface

Two interaction modes, two session states:

**Input:**
- **Text**: typed query in the chat UI (available always)
- **Voice**: wake word or hotkey → STT → agent response spoken via TTS (primary during-meeting mode)

**Session state:**
- **During Meeting** (live): answers based on transcript so far + pre-loaded knowledge. Chat UI shows a live indicator with timestamp of latest processed segment.
- **Post-Meeting**: full transcript available. Deeper analysis, synthesis, and brainstorming supported. Voice still available for hands-free post-meeting review.

**Voice output routing:**
- TTS audio routed exclusively to headset/earphone output device
- Never routed to system speakers or meeting microphone
- Volume and voice (speed, pitch) configurable

Supports multi-turn conversation — the agent maintains context across the chat/voice session.

### F8 — Knowledge Integration (RAG)

Integrates knowledge from multiple sources into a vector store:

- Project documentation and architecture docs
- Codebase summaries
- Domain knowledge corpus (manually curated or imported)
- Industry knowledge and trends (can be seeded from curated documents)
- Prior meeting transcripts and notes

Knowledge is separated into two namespaces within the vector store:
- **Static knowledge** (pre-meeting, persists across sessions)
- **Session knowledge** (this meeting's transcript, only for this session)

### F9 — Teams Bot Features (Phase 3)

- Auto-join meeting as named participant
- Record session via Microsoft Graph API
- Upload and process transcript
- Post structured summary to Teams channel
- Create discussion thread with open questions and gaps

---

## Non-Functional Requirements

| Requirement | Target |
|---|---|
| Segment processing latency | < 30 seconds per 2-min mp4 chunk |
| Transcription accuracy | > 90% WER on clear audio |
| Chat response time | < 5 seconds for mid-meeting queries |
| Storage | Local FS for MVP; S3-compatible for cloud |
| Security | No audio/transcript leaves local machine in MVP |
| Modularity | Each component (watcher, transcriber, embedder, LLM) independently replaceable |
| Scalability | Cloud-ready architecture for Phase 3+ |

---

## Tech Stack

### Backend
- Python (FastAPI) — transcription pipeline + agent API
- Watchdog — folder watcher for OBS mp4 segments

### AI / ML
- Faster-Whisper — GPU-accelerated transcription (meeting audio + voice query STT)
- WhisperX / pyannote — speaker diarization
- Claude / OpenAI / Llama — LLM reasoning
- LangChain / LangGraph — agent orchestration
- OpenAI TTS / ElevenLabs / Kokoro — spoken agent responses (routed to earphone only)
- Pynput / keyboard — hotkey detection for voice activation

### Audio Processing
- FFmpeg — audio extraction from mp4 segments
- OBS 3.11 — capture source (configured for 2-min segment output)

### Storage
- PostgreSQL — session metadata, transcript storage
- Local FS / S3 — mp4 segment storage
- Vector DB:
  - FAISS (local MVP)
  - ChromaDB (local, persistent)
  - Pinecone / Weaviate (cloud, Phase 3+)

### Frontend
- React / Next.js — chat UI
- Electron (optional) — desktop app wrapper

### Integration
- Microsoft Graph API — Teams bot (Phase 3)
- Azure Bot Service — Teams bot hosting (Phase 3)

---

## High-Level Flows

### During Meeting (Local Agent)

```
OBS mp4 segments (every 2 min)                 Human voice query (wake word / hotkey)
    → File Watcher detects new file                 → STT (Faster-Whisper, mic input)
    → FFmpeg extracts audio                         → Text question
    → Faster-Whisper transcribes                    ↓
    → Chunks embedded → Session Vector Store   LLM Agent (transcript + domain knowledge)
    → Rolling summary updated                       ↓
    → Chat UI reflects latest context          TTS response → earphone only (not meeting audio)
                                               + response shown in chat UI
```

### Post-Meeting (Collaborative Understanding)

```
Full transcript available
    → Agent generates initial understanding document draft
    → Human reviews → asks questions → agent elaborates
    → Agent identifies gaps → asks clarifying questions
    → Co-created understanding document finalized
    → Exported as Markdown / PDF
```

### Teams Bot (Phase 3)

```
Meeting Join → Record via Graph API → Process segments → Transcript
    → LLM → Post summary + gaps to Teams channel → Create discussion thread
```

---

## Delivery Phases

### Phase 1 — MVP (Local Agent, Post-Meeting)
- OBS folder watcher + FFmpeg audio extraction
- Faster-Whisper transcription per segment
- Post-meeting chat UI
- Basic LLM Q&A over full transcript

### Phase 2 — Real-Time During Meeting (Text + Voice)
- Incremental transcript accumulation
- Mid-meeting chat with live context
- Voice query via wake word / hotkey → STT → TTS response to earphone
- Rolling summary updates per segment
- Agent persona with pre-loaded domain knowledge

### Phase 3 — Knowledge Integration (RAG)
- Pre-meeting knowledge loading (project docs, domain corpus)
- Static + session vector store namespaces
- Speaker diarization
- Gap and risk detection

### Phase 4 — Collaborative Understanding Document
- Post-meeting brainstorming dialogue
- Co-created understanding document with gaps, risks, expert commentary
- Export to Markdown / PDF

### Phase 5 — Teams Bot Integration
- Auto-join meeting as participant
- Graph API recording
- Post to Teams channel with structured output
