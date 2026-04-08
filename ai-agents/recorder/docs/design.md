# AI Meeting Recorder Agent — System Design

## Architecture Overview

Operational workflow references:

- [Live Local OBS Session](use-cases/live-local-obs-session.md) - primary Phase 1 flow
- [Uploaded Recording Analysis](use-cases/uploaded-recording-analysis.md) - optional post-meeting ingestion
- [Teams Bot Participant](use-cases/teams-bot-future.md) - future automation flow

The system has three major layers: a **Project Brain** (persistent, per-project knowledge), a **multi-agent pipeline** (meeting processing and reasoning), and an **application layer** (user interaction). The Project Brain is the foundation — without it, agents give generic answers. With it, they answer like someone who has been on the team for months.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         PROJECT BRAIN LAYER                              │
│                      (persistent, per-project)                           │
│                                                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────┐  │
│  │ Project Profile │  │  Document Store  │  │      Code Index         │  │
│  │ Card (always    │  │  (ADRs, specs,   │  │  (module summaries,     │  │
│  │  in prompt)     │  │   runbooks, HLD) │  │   API contracts,        │  │
│  └─────────────────┘  └─────────────────┘  │   DB schemas)           │  │
│                                             └─────────────────────────┘  │
│  ┌─────────────────────────┐  ┌──────────────────────────────────────┐   │
│  │    Meeting Archive      │  │     External Integrations            │   │
│  │  (prior transcripts +   │  │  (Jira, GitHub, Confluence,         │   │
│  │   understanding docs)   │  │   SharePoint — optional)             │   │
│  └─────────────────────────┘  └──────────────────────────────────────┘   │
│                                                                          │
│  ┌──────────────────────────────────────────────────────────────────┐    │
│  │  ChromaDB: project_brain_{id} │ project_code_{id} │ meetings_{id}│    │
│  └──────────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────┬───────────────────────────────────┘
                                       │ all agents read from Project Brain
                                       ▼
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
│             Agent A queue          Agent B queue       session_transcript │
│             (deep relevance)       (deep relevance)    (all chunks)      │
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
│    │    each agent retrieves from Project Brain + session        │       │
│    │    transcript, filtered by role-based access tier          │       │
│    │                                                             │       │
│    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │       │
│    │  │  Architect   │  │   Security   │  │     PM       │     │       │
│    │  │    Agent     │  │    Agent     │  │    Agent     │     │       │
│    │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │       │
│    │    code: API+modules  code: auth+deps    code: README only  │       │
│    │                                                             │       │
│    │  ┌──────────────┐  (up to 6 active agents per session)     │       │
│    │  │Default Expert│  ← full project brain access             │       │
│    │  │   Agent      │  ← handles unrouted queries              │       │
│    │  └──────────────┘                                           │       │
│    └─────────────────────────────────────────────────────────────┘       │
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

---

### PB-1. Project Setup Wizard

Runs once per project. A conversational LangGraph interview that collects project sources and triggers indexing.

```python
SetupInterview (LangGraph state machine):

  State: awaiting_project_info
    Agent: "What is this project and what is it trying to achieve?"
    → captures: project.name, project.description, project.goals[]

  State: awaiting_codebase
    Agent: "Where is the codebase? Local path or git URL?"
    → captures: project.git_repo_path, project.git_url

  State: awaiting_docs
    Agent: "Where are the project documents? Folder, Confluence, or SharePoint?"
    → captures: project.docs_folder, project.confluence_space, project.sharepoint_url

  State: awaiting_exclusions
    Agent: "Any directories or files to never index? (credentials, generated files)"
    → captures: project.excluded_paths[] (merged with built-in exclusions)

  State: awaiting_integrations
    Agent: "Do you use Jira, GitHub Issues, or Confluence for tracking?"
    → captures: project.jira_project_key, project.github_repo, project.confluence_space

  State: trigger_indexing
    → Spawns: DocumentIndexer, CodeIndexer, ExternalConnectors (async, parallel)
    → Agent: "Indexing in progress. I'll let you know when it's ready."

  State: review_profile_card
    → Agent generates draft Project Profile Card
    → User reviews, edits, confirms
    → Saved to project.profile_card (injected into all agent prompts)

  State: complete
    → Project Brain ready — all future sessions in this project inherit it
```

```python
ProjectConfig:
  project_id: str
  name: str
  description: str
  goals: list[str]
  git_repo_path: str | None
  docs_folder: str | None
  excluded_paths: list[str]
  jira_project_key: str | None
  github_repo: str | None
  confluence_space: str | None
  profile_card: str              # < 500 tokens, always in system prompt
  last_indexed_at: datetime
  last_git_commit: str           # for incremental sync
```

---

### PB-2. Document Indexer

Crawls and embeds all project documentation into `project_brain_{project_id}`.

```
Supported formats:
  .md, .txt          → read directly
  .pdf               → PyPDF2 / pdfplumber
  .docx              → python-docx
  .html              → BeautifulSoup
  Confluence pages   → Confluence REST API
  SharePoint docs    → Microsoft Graph API

Chunking strategy:
  - 512-token chunks with 64-token overlap
  - Heading-aware: respect markdown/document section boundaries
  - Each chunk metadata: source_file, section_heading, last_modified

Semantic linking (doc → code):
  - During indexing, agent scans each doc for references to code components
    (module names, class names, API endpoints, service names)
  - Stores links: doc_chunk_id → [code_summary_ids]
  - Used at retrieval time to surface linked code alongside doc content

Exclusions:
  - project.excluded_paths[]
  - Files modified > 2 years ago (configurable threshold)
```

---

### PB-3. Code Indexer

Parses the codebase and generates LLM-produced summaries at each structural level. **Raw code is never embedded.** Only summaries are embedded; raw code is retrieved by path when needed.

```
Indexing pipeline per file:

  1. AST Parse (tree-sitter or Python ast module)
     → extract: classes, functions, imports, decorators, route definitions

  2. Structure Extraction per level:
     Module level:
       - File purpose, key classes, external dependencies, module-level docstring
     Class / Service level:
       - Class name, responsibilities, public methods, key attributes
     API Endpoint level (FastAPI/Flask/Express):
       - Route, method, parameters, response schema, auth requirements
     DB Schema level (SQLAlchemy / Prisma / raw SQL):
       - Table name, columns, types, relationships, constraints, indexes

  3. LLM Summary Generation (per module and class):
     Prompt: "Summarise this {Python module / class / API endpoint} in plain English.
              Include: purpose, key responsibilities, important design decisions,
              external dependencies, and anything a team member joining this code
              should know. Be concise but complete."
     Output: 200–400 word summary per module/class

  4. Embed summary → project_code_{project_id}
     Metadata: file_path, level (module/class/endpoint/schema),
               component_name, last_modified, git_commit

  5. Store raw code → local FS / S3 (retrieved by file_path on demand)

Role-based access filter applied at retrieval (not at indexing):
  level filter per agent role stored in agent config:
    PM / BA:        level IN ("module")   — only high-level module descriptions
    Architect:      level IN ("module", "class", "endpoint")
    Security:       level IN ("module", "class", "endpoint", "schema")
                    + filter: component_name contains auth|security|token|crypt|hash
    Data Engineer:  level IN ("schema", "module", "class")
                    + filter: component_name contains data|pipeline|etl|transform|db
    DevOps / SRE:   level IN ("module") + file_path contains infra|deploy|config|helm|docker
    Default Expert: no filter — all levels
```

---

### PB-4. Incremental Sync

Keeps the Project Brain current without full re-indexing.

```
Code sync (triggered before each session or on demand):
  git_diff = GitPython.diff(project.last_git_commit, "HEAD")
  changed_files = [f for f in git_diff if f not in excluded_paths]
  for file in changed_files:
    re-parse → re-summarise → re-embed → update project.last_git_commit

Document sync (continuous, via Watchdog on docs_folder):
  on file_modified or file_created:
    re-chunk → re-embed → update metadata.last_modified

Stale file detection during meetings:
  when an agent retrieves a code or doc chunk:
    if chunk.last_modified < file.actual_last_modified:
      agent appends: "[Note: this file was modified after my last index.
                      My knowledge may be outdated.]"

Pre-session freshness prompt:
  "Last indexed: {last_indexed_at}. {n} files changed since then.
   Re-index now? (recommended before important meetings)"
```

---

### PB-5. External Connectors

Optional integrations that enrich the Project Brain with live project data.

```
Jira Connector:
  Input: project.jira_project_key
  Fetches: open issues, current sprint, epics, recent comments
  Processing: LLM summarises each issue → embed in project_brain_{id}
  Metadata: issue_key, status, assignee, priority, last_updated
  Refresh: before each session (delta sync — only changed issues)

GitHub / GitLab Connector:
  Input: project.github_repo
  Fetches: open issues, recent PR descriptions and review comments
  Processing: LLM summarises → embed
  Refresh: before each session

Confluence Connector:
  Input: project.confluence_space
  Fetches: pages in the space (respects Confluence permissions)
  Processing: same as Document Indexer
  Refresh: file watcher on Confluence webhook (or daily sync)

SharePoint Connector:
  Input: document library URL
  Fetches: .docx, .pdf, .md files
  Processing: same as Document Indexer
  Uses: Microsoft Graph API

All connectors write to: project_brain_{project_id}
Connector metadata tags each chunk with: source="jira" | "github" | "confluence" | "sharepoint"
```

---

### PB-6. Project Profile Card

A short structured text block (< 500 tokens) injected verbatim into **every agent's system prompt** for every session. Never retrieved — always present. This eliminates cold-start latency for core project facts.

```
Format (Markdown, maintained by team):

  ## Project: {name}
  **Goal:** {one-line description}
  **Stack:** {tech_stack}
  **Team:** {team_size}, {squad_structure}
  **Current focus:** {current_sprint_goal_or_milestone}
  **Key open risks:** {top_3_risks}
  **Architecture style:** {style}
  **Key decisions in effect:**
    - {ADR-001 summary}
    - {ADR-007 summary}
  **Last updated:** {date}
```

The agent drafts an initial card from indexed content during setup. The team reviews and edits it. It is re-confirmed before each meeting (< 30s review).

---

### PB-7. Meeting-Specific Context Injection

When a session is created, the agent asks what the meeting focuses on and pre-retrieves relevant Project Brain content before the meeting starts.

```
Interview:
  "What aspect of the project does this meeting focus on?"
  "Any specific components, features, or recent changes relevant to this meeting?"

Pre-retrieval:
  query = meeting_focus + components_mentioned
  top-K results from:
    project_brain_{id}     → most relevant docs and ADRs
    project_code_{id}      → most relevant code summaries
    project_meetings_{id}  → most relevant prior meeting content

Pre-loaded context stored in: session.preloaded_context (injected alongside
rolling summary in all agent prompts for this session)

Effect: the very first question in the meeting gets a project-grounded answer
with zero retrieval cold-start.
```

---

### PB-8. Session Binding and Ingestion Modes

The recorder must attach media to an explicit session before any processing pipeline step runs. File ownership is session-driven, not filename-driven.

```
Binding rules:
  session_id -> project_id
  session_id -> active personas
  session_id -> primary_persona_id
  session_id -> meeting focus
  session_id -> preloaded_context

Phase 1 supported modes:
  live_obs
    - user creates session in UI
    - user starts local OBS recording
    - watcher binds new segments to the active live session

  upload_recording
    - user creates session in UI
    - user uploads meeting files
    - uploaded files are stored under that session before processing

Future mode:
  teams_bot
    - session still exists as the canonical owner
    - Graph or Teams media attaches to the session before processing
```

**Phase 1 simplification:** only one active live capture session should exist per local machine. This avoids ambiguous ownership when OBS writes to a shared watch folder.

**Persona setup requirements:**

- user selects one or more active personas before processing starts
- one persona may be marked as `primary_persona`
- saved persona profiles may be reused and updated per session
- persona metadata includes accountability areas, irrelevant topics, and open questions

**Phase 1 execution model:**

- transcription remains shared and session-scoped
- the Default Expert may be the only live runtime agent in Phase 1
- persona-specific summaries, action items, risks, and post-meeting briefings are still generated from the shared transcript plus persona profiles

**Recommended storage shape:**

```
data/
  sessions/
    {session_id}/
      segments/
      audio/
      transcript/
```

**Continuity model for recurring meetings:**

```
Session continuity fields:
  previous_session_id: str | None
  meeting_series_id: str | None

UI actions:
  - Start Next Session
  - Link Previous
  - Unlink
  - View Carry-Forward

Carry-forward defaults:
  - active personas
  - primary_persona_id
  - unresolved action items
  - unresolved open questions
  - unresolved risks or conflicts
  - prior meeting summary

Do not blindly carry forward:
  - completed action items
  - stale temporary notes
  - raw transcript blocks injected directly into prompts
  - outdated meeting-specific context
```

See:

- [Live Local OBS Session](use-cases/live-local-obs-session.md)
- [Uploaded Recording Analysis](use-cases/uploaded-recording-analysis.md)
- [Teams Bot Participant](use-cases/teams-bot-future.md)

---

### 1. File Watcher (Watchdog)

Monitors the OBS output folder for new mp4 files.

```
Responsibilities:
  - Detect new mp4 files written by OBS
  - Debounce: wait for file write to complete (poll size stability)
  - Attach each stable file to the currently active live session
  - Enqueue file path to segment processing queue with session metadata

Config:
  watch_folder: str           # OBS output directory
  debounce_seconds: int       # default 3s
  segment_duration_secs: int  # expected 120s — for validation
```

**Debounce logic:** Poll file size every 1 second; trigger only when size is stable for 2+ consecutive checks.
**Ownership rule:** the watcher does not infer project or persona ownership from the mp4 filename. It resolves ownership from the active live `session_id`.

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
- Output is written to the shared session transcript first
- Persona-specific filtering and role-aware outcome generation happen after transcription, not during capture

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

All storage uses ChromaDB locally (Pinecone/Weaviate in Phase 3+).

```
Namespace structure:

  ── Project-scoped (persistent, shared across all sessions and agents) ──
  project_brain_{project_id}   → document store: ADRs, specs, runbooks, HLD,
                                  Jira summaries, Confluence, external integrations
  project_code_{project_id}    → code index: module/class/API/schema summaries
                                  (role-based access filter applied at retrieval)
  project_meetings_{project_id}→ meeting archive: prior transcripts + understanding docs

  ── Persona-scoped (persists across sessions for this persona role) ──
  persona_domain_{persona_id}  → generic domain knowledge, industry trends
                                  (not project-specific — e.g., "security best practices")

  ── Session-scoped (this meeting only) ──
  session_transcript_{session_id} → all transcript chunks from this meeting,
                                     shared across agents
                                     metadata: relevance_scores: {agent_id: score}

Retrieval per agent per query:
  1. session_transcript_{session_id}   filtered by relevance_score[agent_id] > 0.4
  2. project_brain_{project_id}        filtered by role access + semantic similarity
  3. project_code_{project_id}         filtered by role-based level filter
  4. project_meetings_{project_id}     for prior meeting context (Phase 3+)
  5. persona_domain_{persona_id}       always accessible (generic domain knowledge)

Profile Card: NOT retrieved — injected verbatim into system prompt always.
```

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

For Phase 1, the same shared transcript can still be re-read through selected persona profiles to produce persona-aware notes and outputs even if only the Default Expert is active at live runtime.

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
{project.profile_card}                        ← always injected, no retrieval

You are a {role_title} participating in this meeting as an expert observer.
Your accountability areas: {accountability_areas}
Your domain focus: {role_description}

Meeting focus: {session.meeting_focus}
Pre-loaded context for this meeting: {session.preloaded_context}
Meeting summary so far: {agent.rolling_summary}

Answer questions from your professional perspective, grounded in the project
knowledge above. Cite specific documents, ADRs, or code modules when relevant.
If something is outside your domain, redirect to the appropriate specialist.
Always flag uncertainty. If you notice something that contradicts the project
docs or codebase, raise it explicitly — do not smooth it over.
```

**Retrieval order in `answer_query` node:**
```
1. inject:    project.profile_card (always — no retrieval)
2. inject:    session.preloaded_context (pre-retrieved for this meeting topic)
3. inject:    agent.rolling_summary (always — no retrieval)
4. retrieve:  top-K from session_transcript_{session_id} (what was said so far)
5. retrieve:  top-K from project_brain_{project_id} (docs, ADRs, specs)
6. retrieve:  top-K from project_code_{project_id} (role-filtered code summaries)
7. retrieve:  top-K from persona_domain_{persona_id} (generic domain knowledge)
8. generate:  LLM response with citations
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

Continuity behaviors:
  - a session may link to a previous session in the same project
  - multiple sessions may belong to a meeting series
  - users may unlink or relink sessions later without breaking transcript ownership
  - "Start Next Session" creates a new session prefilled from the linked prior session
  - carry-forward material is generated as a summary artifact, not by copying raw transcript into prompts

PostgreSQL schema (key tables):

  projects:
    project_id, name, description, goals (JSON)
    git_repo_path, docs_folder, excluded_paths (JSON)
    jira_project_key, github_repo, confluence_space
    profile_card (text)          ← always injected into agent prompts
    last_indexed_at, last_git_commit
    indexing_status              ← idle | running | complete | error

  sessions:
    session_id, project_id, title, status, start_time, end_time
    previous_session_id, meeting_series_id
    meeting_focus, global_rolling_summary
    preloaded_context (text)     ← pre-retrieved for this meeting topic
    meeting_brief (JSON)

  personas:
    persona_id, session_id, role_title, role_description
    accountability_areas (JSON), decision_domains (JSON)
    rolling_summary, is_async, template
    briefing (JSON, populated post-meeting)

  transcript_chunks:
    chunk_id, session_id, segment_index
    start_time, end_time, speakers (JSON), text
    relevance_scores (JSON)      ← {agent_id: score}

  project_code_index:
    entry_id, project_id, file_path, component_name
    level (module|class|endpoint|schema)
    summary (text)               ← LLM-generated, embedded in ChromaDB
    git_commit, last_modified

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

### Project Brain Setup (one-time per project)

```
User starts new project
    │
    ▼
Project Setup Wizard (conversational interview)
    │ captures: git_repo_path, docs_folder, exclusions, integrations
    │
    ▼ (parallel)
    ├── Document Indexer
    │     crawl docs_folder (+ Confluence / SharePoint if configured)
    │     → chunk + embed → project_brain_{project_id}
    │
    ├── Code Indexer
    │     git clone / local path
    │     → AST parse per file → extract structure
    │     → LLM summarise per module / class / endpoint / schema
    │     → embed summaries → project_code_{project_id}
    │     → store raw code → local FS (retrieved by path on demand)
    │
    └── External Connectors (if configured)
          Jira / GitHub / Confluence → LLM summarise → project_brain_{project_id}
    │
    ▼ (all complete)
Agent drafts Project Profile Card (< 500 tokens)
    │
    ▼
User reviews + confirms Profile Card
    │
    ▼
Project Brain ready ✓ — all future sessions inherit it

─── On subsequent sessions: ───────────────────────────────────────
git diff → changed files → re-summarise + re-embed (< 30s typically)
File watcher → changed docs → re-chunk + re-embed
Freshness prompt shown to user before session starts
```

### Mid-Meeting Voice Query — Project-Grounded Answer

```
"Hey Nexus, can the payment service handle the throughput we're discussing?"
    │
    ▼
STT → Orchestrator → routes to Architect Agent (and Data Engineer Agent)
    │
    ▼
Architect Agent retrieval stack:
    1. project.profile_card            ← "Stack: FastAPI, PostgreSQL, Redis on GCP"
    2. session.preloaded_context       ← pre-retrieved for "payment service throughput"
    3. agent.rolling_summary           ← what's been discussed so far
    4. session_transcript (top-K)      ← what was just said
    5. project_brain (top-K)          ← finds: ADR-012 (payment scaling decision)
    6. project_code (top-K)           ← finds: payment_service module summary
                                              "handles ~500 req/s, async queue,
                                               horizontal scaling planned in ADR-012"
    7. persona_domain (top-K)         ← scalability patterns domain knowledge
    │
    ▼
Agent response:
  "[Architect] Based on ADR-012 (March 2026), the payment service was designed
   to scale to 2000 req/s with horizontal Pod scaling. The current module
   handles ~500 req/s via the async queue. However, the load test docs show
   testing was only run to 800 req/s — there's a gap between the design target
   and what's been validated."

TTS → earphone │ Full response → chat UI
```

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

### Project Brain Setup (one-time)

| Operation | Target |
|---|---|
| Document indexing (100 docs, avg 10 pages) | < 5 minutes |
| Code indexing — AST parse (1000 files) | < 2 minutes |
| Code indexing — LLM summarisation (1000 files) | < 15 minutes (parallelised, 10 concurrent) |
| External connector sync (Jira, 200 issues) | < 3 minutes |
| Total initial Project Brain setup | < 30 minutes (typical project) |

### Incremental Sync (per session)

| Operation | Target |
|---|---|
| Git diff + changed file detection | < 5s |
| Re-summarise + re-embed changed files (< 20 files) | < 60s |
| Document file watcher re-index (single file) | < 10s |
| Pre-session freshness check | < 5s |

### Meeting-Specific Context Injection

| Operation | Target |
|---|---|
| Meeting topic interview | < 2 minutes |
| Targeted pre-retrieval from Project Brain | < 10s |

### Meeting Runtime

| Operation | Target |
|---|---|
| File watcher → processing trigger | < 5s after OBS write completes |
| FFmpeg audio extraction | < 5s per 2-min segment |
| Faster-Whisper transcription (GPU) | < 15s per 2-min segment |
| Relevance scoring (per chunk, all agents) | < 1s per agent, parallel |
| Embedding + vector store indexing | < 5s per segment |
| Total segment-to-searchable latency | < 30s per segment |
| Voice STT (question, 8s clip) | < 2s |
| LLM response — single agent (project-grounded) | < 5s p95 |
| LLM response — multi-agent synthesis | < 15s p95 |
| TTS generation + playback start | < 3s after LLM response |
| End-to-end voice round trip | < 10s (activation → spoken answer) |
| Rolling summary update (per agent, background) | < 10s |

### Post-Meeting

| Operation | Target |
|---|---|
| Per-persona briefing generation | < 60s |
| All briefings (parallel, 5 agents) | < 90s |
| Shared understanding document draft | < 30s after briefings complete |
| Archive session to project_meetings | < 10s |
