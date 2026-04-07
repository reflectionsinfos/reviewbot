# AI Meeting Recorder Agent — System Design

## Architecture Overview

The system is built around a **multi-agent pipeline** layered on top of a chunked video processing backbone. OBS produces 2-minute mp4 segments; the pipeline transcribes each segment incrementally, scores relevance against each active persona, and distributes chunks to the right specialist agents. An orchestrator coordinates all agents, routes queries, detects conflicts, and synthesizes the shared output.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                          Meeting Capture Layer                           │
│   OBS 3.11 (2-min mp4 segments) → Watched Output Folder                 │
└──────────────────────────────────────┬───────────────────────────────────┘
                                       │ new file event
                                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          Processing Pipeline                             │
│   File Watcher → FFmpeg (audio) → Faster-Whisper → Transcript Chunks    │
│                                           │                              │
│                                           ▼                              │
│                               Relevance Scorer                           │
│                          (scores each chunk per agent)                   │
│                                           │                              │
│                    ┌──────────────────────┼──────────────────────┐       │
│                    ▼                      ▼                      ▼       │
│             Agent A queue          Agent B queue          Shared store   │
│             (high relevance)       (high relevance)       (all chunks)   │
└──────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          Intelligence Layer                              │
│                                                                          │
│  ┌────────────────────────────────────────────────────────────────────┐  │
│  │                      Orchestrator Agent                            │  │
│  │  - Query routing           - Conflict detection                    │  │
│  │  - Multi-agent synthesis   - Meeting health monitor               │  │
│  │  - Shared understanding doc management                             │  │
│  └──────────┬──────────────────────────────────────────┬─────────────┘  │
│             │                                          │                 │
│    ┌────────┴──────────────────────────────────────────┴────────┐       │
│    │              Specialist Persona Agents                      │       │
│    │                                                             │       │
│    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │       │
│    │  │  Architect   │  │   Security   │  │     PM       │     │       │
│    │  │    Agent     │  │    Agent     │  │    Agent     │     │       │
│    │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │       │
│    │         │                 │                  │             │       │
│    │  ┌──────┴───────┐  ┌──────┴───────┐  ┌──────┴───────┐    │       │
│    │  │ Static KB    │  │ Static KB    │  │ Static KB    │    │       │
│    │  │ (Architect)  │  │ (Security)   │  │ (PM)         │    │       │
│    │  └──────────────┘  └──────────────┘  └──────────────┘    │       │
│    │                                                             │       │
│    │  ┌──────────────┐  (up to 6 active agents per session)     │       │
│    │  │Default Expert│                                           │       │
│    │  │   Agent      │  ← always active, handles unrouted queries│       │
│    │  └──────────────┘                                           │       │
│    └─────────────────────────────────────────────────────────────┘       │
│                                                                          │
│              Shared Session Vector Store (all transcript chunks)         │
└──────────────────────────────────────────────────────────────────────────┘
                                       │
                                       ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                          Application Layer                               │
│   Chat UI (React) │ Voice Interface │ REST API (FastAPI) │ Doc Export    │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## Component Design

### 1. File Watcher (Watchdog)

Monitors the OBS output folder for new mp4 files.

```
Responsibilities:
  - Detect new mp4 files written by OBS
  - Debounce: wait for file write to complete (poll size stability)
  - Enqueue file path to segment processing queue

Config:
  watch_folder: str           # OBS output directory
  debounce_seconds: int       # default 3s
  segment_duration_secs: int  # expected 120s — for validation
```

**Debounce logic:** Poll file size every 1 second; trigger only when size is stable for 2+ consecutive checks.

---

### 2. Audio Extraction Service (FFmpeg)

```
Input:  segment_0042.mp4
Output: segment_0042.wav  (16kHz mono, PCM)

Command:
  ffmpeg -i segment_0042.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 segment_0042.wav
```

Subprocess call. On failure: log and skip segment (non-blocking).

---

### 3. Transcription Service (Faster-Whisper)

```python
Output schema per segment:
{
  "session_id": "uuid",
  "segment_index": 42,
  "segment_start_offset_secs": 5040,  # 42 * 120
  "transcription": [
    {
      "start": 5041.2,
      "end": 5044.7,
      "text": "The question is whether we shard at the application or database layer.",
      "speaker": "SPEAKER_01"          # from diarization (Phase 2+)
    }
  ]
}
```

- Model: `large-v3` (accuracy) or `medium` (speed)
- GPU preferred; CPU fallback
- Absolute timestamps: `segment_index * segment_duration + relative_offset`

---

### 4. Chunking Service

```
Strategy: time-window chunking
  - 60-second windows, 15-second overlap
  - Each chunk retains: start_time, end_time, speaker(s), text

Output per chunk:
{
  "chunk_id": "{session_id}::chunk_{n}",
  "session_id": "uuid",
  "start_time": 5040.0,
  "end_time": 5100.0,
  "speakers": ["SPEAKER_01", "SPEAKER_02"],
  "text": "..."
}
```

---

### 5. Relevance Scorer

After chunking, each chunk is scored against every active persona's domain before distribution. This is a lightweight fast operation — uses a small cross-encoder or sentence similarity model, not the full LLM.

```python
RelevanceScore:
  chunk_id: str
  agent_id: str
  score: float        # 0.0 – 1.0
  routing_tier: str   # "deep" | "light" | "skip"

Routing tiers:
  deep  (>0.7):  Full embed into agent's namespace, included in agent's rolling summary
  light (0.4-0.7): Embedded in shared store, retrievable by agent on query
  skip  (<0.4):  Skipped by this agent; in shared store for orchestrator only

Model: sentence-transformers/all-MiniLM-L6-v2 (fast, runs on CPU)
Latency target: < 1s per chunk per agent
```

The relevance scoring is run in parallel across all active agents for each chunk.

---

### 6. Embedding & Vector Store

```
Namespaces per session:

  static_knowledge_{agent_id}  → pre-meeting docs per persona (persists)
  session_transcript            → all chunks, shared across agents
  prior_meetings_{project_id}   → archived transcripts from past meetings

Chunk metadata stored:
  chunk_id, start_time, end_time, speakers, segment_index,
  relevance_scores: {agent_id: score, ...}
```

Per-agent retrieval uses the shared `session_transcript` collection filtered by relevance score metadata. Agents with `score > 0.4` can retrieve a chunk; agents with `score < 0.4` cannot.

---

### 7. Rolling Summary Updater (Per Agent)

Each agent maintains its own rolling summary, updated independently every 2 segments.

```
Trigger: every 2 new "deep" chunks delivered to this agent (~4 minutes of relevant content)

Prompt pattern:
  "You are {agent.role_description} updating your running notes on a meeting.
   Your focus areas: {agent.domain_focus}
   Previous notes: {agent.rolling_summary}
   New relevant content: {new_deep_chunks}
   Update your notes. Flag any new decisions, action items, or risks in your domain.
   Note anything that conflicts with your prior understanding."

Output: stored in agent.rolling_summary (DB, overwritten per update)
```

The orchestrator also maintains a **global rolling summary** by periodically requesting a cross-agent synthesis.

---

### 8. Role Onboarding Interview

Before the meeting, each user is interviewed by the agent. This is a multi-turn conversation, not a form.

```python
Interview flow (LangGraph state machine):

  State: awaiting_role
    Agent: "What's your role in this meeting?"
    → captures: persona.role_title, persona.role_description

  State: awaiting_accountability
    Agent: "What are you accountable for in this project?"
    → captures: persona.accountability_areas[]

  State: awaiting_decisions
    Agent: "What decisions fall within your domain?"
    → captures: persona.decision_domains[]

  State: awaiting_success
    Agent: "What would make this meeting a success for you?"
    → captures: persona.success_criteria[]

  State: awaiting_irrelevant
    Agent: "Are there topics you know are irrelevant to your role?"
    → captures: persona.irrelevant_topics[] (used to suppress relevance scoring)

  State: awaiting_open_questions
    Agent: "Any open questions you're hoping this meeting will resolve?"
    → captures: persona.prior_open_questions[]

  State: complete
    → PersonaConfig created and saved
    → Knowledge loading begins
```

```python
PersonaConfig:
  persona_id: str
  session_id: str
  role_title: str                    # e.g., "Solutions Architect"
  role_description: str              # free text from interview
  accountability_areas: list[str]
  decision_domains: list[str]
  success_criteria: list[str]
  irrelevant_topics: list[str]
  prior_open_questions: list[str]
  domain_knowledge_docs: list[str]   # files → static_knowledge_{persona_id}
  industry_trends_docs: list[str]
  project_context_docs: list[str]
  is_async: bool                     # true for absent stakeholders
  template: str | None               # built-in template if used
```

---

### 9. Orchestrator Agent (LangGraph)

The orchestrator is a LangGraph graph that coordinates all persona agents.

```
Nodes:

  receive_query
    → input: user query (text or STT-transcribed voice)
    → classifies: topic domain, urgency, scope (single-agent or multi-agent)

  route_to_agent(s)
    → fast path: single most relevant agent (mid-meeting voice queries)
    → synthesis path: multiple agents (post-meeting or explicit "all perspectives" request)

  collect_responses
    → awaits responses from dispatched agents
    → timeout: 4s per agent for fast path, 12s for synthesis path

  detect_conflicts
    → compares agent responses on the same topic
    → flags contradictions, unacknowledged dependencies
    → creates ConflictRecord if found

  synthesize
    → merges agent responses into a coherent answer
    → labels each perspective with the agent's role
    → highlights conflicts inline

  update_understanding_doc
    → appends decisions, action items, risks, conflicts to the shared doc

  health_monitor (background, continuous)
    → checks: time since last decision, scope drift, unresolved prior questions,
              duplicate risk flags across agents
    → emits: HealthAlert to chat UI sidebar
```

**System prompt for orchestrator:**
```
You are the meeting orchestrator. You coordinate {n} specialist agents.
Your job is NOT to answer questions yourself — it is to route them to the right
specialist, synthesize their responses, and surface conflicts. Always attribute
each perspective to its agent's role. Never suppress disagreements.
```

---

### 10. Persona Agent (LangGraph)

Each persona agent is an independent LangGraph graph with its own state.

```
Nodes:

  receive_chunk
    → scores relevance (already done by Relevance Scorer)
    → if "deep": embed + add to rolling summary trigger queue
    → if "light": embed only

  answer_query
    → retrieve: top-K from session_transcript (filtered by relevance score)
    → retrieve: top-K from static_knowledge_{persona_id}
    → inject: agent.rolling_summary (always prepended)
    → generate: LLM response from role's perspective
    → include: confidence, domain alignment note

  generate_briefing
    → post-meeting: full pass over agent's deep chunks
    → produces: PersonaBriefing (see schema below)

  generate_accountability_map
    → maps decisions and action items to accountability owners
    → tags items with: Responsible, Accountable, Consulted, Informed
```

**Agent system prompt template:**
```
You are a {role_title} participating in this meeting as an expert observer.
Your accountability areas: {accountability_areas}
Your domain focus: {role_description}

Answer questions from your professional perspective. If something is outside your
domain, say so and redirect to the appropriate specialist. Always flag uncertainty.
If you notice something that contradicts your understanding or domain knowledge,
raise it explicitly — do not smooth it over.
```

---

### 11. Voice Interface (STT + TTS)

```
Activation:
  Option A — Wake word: "Hey Nexus" (Porcupine or Vosk)
  Option B — Hotkey: Ctrl+Space (pynput)

STT (question capture):
  - Mic capture: 5–10 seconds after activation
  - Transcribe: Faster-Whisper (same model, no extra cost)

Routing:
  - Voice query goes to Orchestrator first
  - Orchestrator routes to single best agent (fast path) for voice
  - Full multi-agent synthesis only for post-meeting or explicit requests

TTS (spoken response):
  - Condensed to 2–3 sentences for voice
  - Full response shown in chat UI simultaneously
  - Provider: OpenAI TTS / ElevenLabs / Kokoro (local, offline)
  - Output device: explicitly configured headset (sounddevice with device index)
  - Never routed to system speaker or OBS capture device

Audio device isolation:
  OBS input:     virtual audio cable or specific meeting input device
  TTS output:    headset output device (separate device index)
  STT mic:       push-to-talk mic (same or different from meeting mic — configurable)

Config:
  wake_word: str                  # "hey nexus"
  activation_hotkey: str          # "ctrl+space"
  stt_listen_duration_secs: int   # 8
  tts_output_device_index: int    # sounddevice device index
  tts_provider: str               # openai | elevenlabs | kokoro
  tts_voice: str                  # "alloy" | "nova" | ...
  also_show_in_chat: bool         # true
```

---

### 12. Inter-Agent Conflict Detection

The orchestrator compares agent responses on the same topic after each synthesis call and after each rolling summary update cycle.

```python
ConflictRecord:
  conflict_id: str
  session_id: str
  timestamp_in_meeting: float     # when in the meeting the conflict topic arose
  detected_at: datetime
  topic: str
  agents_involved: list[str]
  agent_positions: dict[str, str] # agent_id → their position
  conflict_type: str              # "contradiction" | "unacknowledged_dependency" | "risk_gap"
  resolution_status: str          # "unresolved" | "resolved" | "deferred"
  resolution_notes: str | None
```

Conflicts are surfaced in:
- Chat UI immediately (inline notification)
- Each affected agent's briefing
- The shared understanding document as open questions

---

### 13. Meeting Health Monitor

Runs as a background coroutine on the orchestrator. Evaluates health conditions every 5 minutes.

```python
HealthConditions checked:
  - time_since_last_decision > 15min          → "No decisions captured in 15+ minutes"
  - scope_drift_detected()                    → "Agenda scope appears to have expanded"
  - prior_open_questions_unaddressed()        → "3 open questions from last meeting not addressed"
  - topic_tabled_without_owner()              → "Topic tabled with no owner assigned"
  - duplicate_risk_flags >= 2 agents          → "Multiple agents flagged the same risk"

HealthAlert:
  condition: str
  severity: "info" | "warning"
  message: str
  timestamp: datetime

Output: emitted to chat UI sidebar (non-intrusive notification, not spoken)
```

---

### 14. Session & Persona State Management

```
Session lifecycle:
  PRE_MEETING   → interviews running, knowledge loading, watcher active
  IN_PROGRESS   → segments arriving, agents processing, chat active
  POST_MEETING  → briefings generated, co-creation dialogue active
  ARCHIVED      → understanding doc finalised, briefings delivered

PostgreSQL schema (key tables):

  sessions:
    session_id, title, status, start_time, end_time
    global_rolling_summary, meeting_brief (JSON)

  personas:
    persona_id, session_id, role_title, role_description
    accountability_areas (JSON), decision_domains (JSON)
    rolling_summary, is_async, template
    briefing (JSON, populated post-meeting)

  transcript_chunks:
    chunk_id, session_id, segment_index
    start_time, end_time, speakers (JSON), text
    relevance_scores (JSON)  -- {agent_id: score}

  conflicts:
    conflict_id, session_id, topic, agents_involved (JSON)
    agent_positions (JSON), conflict_type, resolution_status

  understanding_documents:
    doc_id, session_id, version
    content (JSON), last_updated
```

---

### 15. Role-Specific Briefing Schema

Generated per persona after the meeting ends.

```json
{
  "persona_id": "uuid",
  "session_id": "uuid",
  "role_title": "Security Engineer",
  "generated_at": "2026-04-08T11:00:00Z",
  "sections": {
    "what_matters_to_you": "...",
    "your_action_items": [
      {"task": "...", "owner": "...", "deadline": "...", "timestamp": 1842.0}
    ],
    "decisions_in_your_domain": [
      {"decision": "...", "rationale": "...", "owner": "...", "timestamp": 920.0}
    ],
    "risks_in_your_area": [
      {"risk": "...", "severity": "high", "timestamp": 1435.0}
    ],
    "open_questions_for_you": ["...", "..."],
    "safe_to_ignore": ["topic A", "topic B"],
    "cross_role_dependencies": [
      {
        "depends_on_role": "Backend Engineer",
        "dependency": "API contract for /auth/token — breaking change proposed",
        "timestamp": 2215.0
      }
    ],
    "expert_commentary": "...",
    "conflicts_involving_you": ["conflict_id_1"]
  }
}
```

---

### 16. Shared Understanding Document Schema

```json
{
  "session_id": "uuid",
  "version": 4,
  "co_created_by": ["SPEAKER_01", "Security Agent", "Architect Agent"],
  "sections": {
    "context_and_objectives": "...",
    "key_decisions": [
      {
        "decision": "...",
        "rationale": "...",
        "owner": "...",
        "accountable_role": "Solutions Architect",
        "timestamp": 920.0
      }
    ],
    "action_items": [
      {
        "task": "...",
        "responsible": "...",
        "accountable_role": "...",
        "deadline": "...",
        "timestamp": 1842.0
      }
    ],
    "open_questions": ["...", "..."],
    "gaps_identified": ["...", "..."],
    "conflicts": [
      {
        "conflict_id": "...",
        "topic": "...",
        "positions": {"Security Agent": "...", "Architect Agent": "..."},
        "resolution_status": "unresolved"
      }
    ],
    "cross_role_dependencies": ["...", "..."],
    "risks_and_concerns": ["...", "..."],
    "accountability_map": {
      "decisions": [{"decision": "...", "R": "...", "A": "...", "C": "...", "I": "..."}],
      "action_items": [{"task": "...", "R": "...", "A": "...", "C": "...", "I": "..."}]
    },
    "expert_commentary_by_role": {
      "Security Engineer": "...",
      "Solutions Architect": "..."
    },
    "next_steps": ["...", "..."]
  }
}
```

---

## Data Flow Diagrams

### Segment Processing + Multi-Agent Distribution

```
OBS writes segment_0042.mp4
    │
    ▼
File Watcher (debounce 3s) → processing queue
    │
    ▼
FFmpeg → segment_0042.wav
    │
    ▼
Faster-Whisper → [{start, end, text, speaker}, ...]
    │
    ▼
Chunking → [{chunk_id, start, end, text}, ...]
    │
    ▼
Relevance Scorer (parallel across all agents)
    │
    ├── Architect Agent: score=0.82 → deep  → embed in static_knowledge_arch + rolling summary trigger
    ├── Security Agent:  score=0.31 → skip  → shared store only
    ├── PM Agent:        score=0.65 → light → embed in shared store
    └── Shared session store: all chunks always written here

    (every 2 deep chunks per agent)
    └── Each agent updates its own rolling summary independently
    └── Orchestrator checks for cross-agent conflicts
```

### Mid-Meeting Voice Query (Fast Path)

```
"Hey Nexus, what are the security risks in this approach?"
    │
    ▼
Wake word detected → mic capture (8s)
    │
    ▼
STT (Faster-Whisper) → "what are the security risks in this approach?"
    │
    ▼
Orchestrator: classifies as Security domain → routes to Security Agent
    │
    ▼
Security Agent:
    ├── inject:   security_agent.rolling_summary
    ├── retrieve: top-K from session_transcript (score > 0.4 for Security)
    ├── retrieve: top-K from static_knowledge_security
    └── generate: response from Security perspective
    │
    ▼
Orchestrator: no conflict detected (single agent fast path)
    │
    ├── TTS (2-3 sentences) → earphone only
    └── Chat UI: full response + "Context as of [timestamp]"
```

### Post-Meeting Briefing Generation (Parallel)

```
Meeting ends → status: POST_MEETING
    │
    ▼
Orchestrator triggers briefing generation (parallel across all agents)
    │
    ├── Architect Agent  → PersonaBriefing (architect perspective)
    ├── Security Agent   → PersonaBriefing (security perspective)
    ├── PM Agent         → PersonaBriefing (PM perspective)
    └── Async Agent(s)   → PersonaBriefing (for absent stakeholders)
    │
    ▼ (all complete)
Orchestrator synthesizes:
    ├── Collects all briefings
    ├── Identifies conflicts not yet resolved
    ├── Identifies cross-role dependencies
    └── Generates shared understanding document draft
    │
    ▼
Collaborative dialogue: humans + agents refine draft
    │
    ▼
Final document exported → Markdown / PDF
Async briefings delivered to absent stakeholders
```

### Multi-Agent Synthesis Query (Post-Meeting)

```
Human: "What are all the perspectives on the caching decision?"
    │
    ▼
Orchestrator: synthesis path (all agents)
    │
    ├── Architect Agent  → "Agreed. Redis fits the latency SLA."
    ├── Security Agent   → "Risk: session tokens without TTL — flagged as high risk."
    └── PM Agent         → "Timeline impact unclear — no deadline assigned."
    │
    ▼
Orchestrator detects: Architect vs Security conflict (positions differ)
    │
    ▼
ConflictRecord created → added to understanding doc as Open Question
    │
    ▼
Synthesized response shown in chat:
  "[Architect] Agreed on Redis for latency.
   [Security] ⚠ Risk: tokens without TTL.
   [PM] No deadline assigned.
   → Conflict between Architect and Security views. Added as Open Question."
```

---

## Teams Bot Design (Phase 3)

```
Azure Bot Service      → bot registration
Microsoft Graph API    → meeting join, recording, transcript
Graph Webhook          → notified on recording availability

Flow:
  Bot joins meeting as named participant (e.g., "Nexus Recorder")
  → Recording triggered via Graph API
  → Segments streamed or downloaded post-meeting
  → Full multi-agent pipeline runs
  → Per-role briefings posted to tagged members in Teams
  → Shared understanding doc posted to meeting channel
  → Discussion thread created with open questions and conflicts
```

---

## Security Design

| Concern | Approach |
|---|---|
| Audio / transcript privacy | MVP: all processing on local machine. Only LLM API calls leave. |
| Fully offline option | Local Llama/Ollama — no data leaves the machine |
| Persona data | Stored locally in PostgreSQL; never sent to LLM providers without explicit opt-in |
| API keys | `.env` only, never committed to git |
| Teams bot | OAuth2 with least-privilege Graph API scopes |
| Stored transcripts | Encrypted at rest (Phase 2+) |
| Async briefings | Delivered over authenticated channel (Teams / email) |

---

## Scalability

- **MVP**: single machine, ChromaDB, local or API-based LLM, async Python workers
- **Phase 3+**: containerised microservices, Celery for parallel agent processing, Redis queue, cloud vector store, S3 for recordings
- **Agent parallelism**: each persona agent runs as an independent async worker; orchestrator coordinates via message passing

---

## Performance Targets

| Operation | Target |
|---|---|
| File watcher → processing trigger | < 5s after OBS write completes |
| FFmpeg audio extraction | < 5s per 2-min segment |
| Faster-Whisper transcription (GPU) | < 15s per 2-min segment |
| Relevance scoring (per chunk, all agents) | < 1s per agent, parallel |
| Embedding + vector store indexing | < 5s per segment |
| Total segment-to-searchable latency | < 30s per segment |
| Voice STT (question, 8s clip) | < 2s |
| LLM response — single agent fast path | < 5s p95 |
| LLM response — multi-agent synthesis | < 15s p95 |
| TTS generation + playback start | < 3s after LLM response |
| End-to-end voice round trip | < 10s (activation → spoken answer) |
| Per-persona briefing generation | < 60s post-meeting |
| All briefings (parallel, 5 agents) | < 90s post-meeting |
| Rolling summary update (per agent) | < 10s (background, non-blocking) |
