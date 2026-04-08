# AI Meeting Recorder Agent — Requirements

## Objective

Build an LLM-powered **Multi-Agent Meeting Intelligence System** where multiple specialist agents — each embodying a distinct professional role — participate in meetings as expert observers, **anchored to a persistent Project Brain** that gives every agent deep knowledge of the project before the meeting starts.

Each project has a Project Brain: a structured, persisted knowledge layer covering project goals, documents, codebase, architecture decisions, and prior meeting history. Every agent draws from this brain during and after meetings — so responses are grounded in actual project reality, not generic domain knowledge alone.

Each participant (human or async) selects a role. The system interviews them to understand their responsibilities and accountability before the meeting. During the meeting, each agent maintains a role-filtered view of what was discussed. After the meeting, every role receives a personalised briefing — and a shared collaborative understanding document is co-created across all agents.

A **Default Expert Agent** is always present as a generalist fallback.

---

## System Variants

### 1. Local Agent (Primary MVP)

A locally running Python app that:

- Monitors OBS-generated mp4 segments (2-min chunks) from a watched folder
- Transcribes each chunk incrementally as it arrives
- Distributes transcript chunks to all active persona agents for role-filtered processing
- Answers questions in real-time via text or voice (during or after the meeting)
- Produces role-specific briefings and a shared collaborative understanding document post-meeting

### 2. Teams Bot Participant (Automation Layer — Phase 3)

- Joins meetings automatically as a named bot participant
- Records via Microsoft Graph API
- Runs the full multi-agent pipeline
- Posts a shared summary + per-role threads to a Teams channel

---

## Functional Requirements

### F1 — Role Onboarding Interview

Before the meeting starts, the agent **interviews** each participant — it does not present a static form. The conversation establishes the persona's context.

**Interview questions (conversational, not a form):**
- "What's your role in this meeting?"
- "What are you accountable for in this project or team?"
- "What decisions fall within your domain?"
- "What would make this meeting a success for you?"
- "Are there topics you already know are irrelevant to your role?"
- "Any open questions you're hoping this meeting will resolve?"

The answers become the persona's system prompt and accountability map. They also seed the relevance scoring model for that agent — topics marked irrelevant by the user are downweighted in that agent's processing.

Returning users can reuse a saved persona profile or update it before each meeting.

---

### F2 — Multi-Agent Architecture

The system supports multiple concurrent persona agents per session, coordinated by an orchestrator.

**Orchestrator Agent:**
- Receives all incoming queries (voice or text)
- Classifies the query and routes it to the most relevant specialist agent(s)
- For cross-cutting queries, collects responses from multiple agents and synthesizes
- Monitors for inter-agent conflicts and surfaces them explicitly
- Manages the shared understanding document
- Runs the Meeting Health Monitor in the background

**Persona Agents (specialist, role-scoped):**
- Each agent has its own: system prompt, rolling summary, relevance filter, and accountability map
- Processes only transcript chunks that score above a relevance threshold for its domain
- Maintains its own action item and risk register, scoped to its role
- Can be queried directly or through the orchestrator

**Built-in persona templates (pre-configured, user-customisable):**

| Persona | Domain focus |
|---|---|
| Solutions Architect | System design, trade-offs, integration patterns, scalability |
| Security Engineer | Threats, compliance, data exposure, auth/authz |
| Product Manager | Scope, timelines, stakeholder impact, feature decisions |
| Data Engineer | Data flows, pipelines, schema, storage, quality |
| DevOps / SRE | Deployment, reliability, observability, infra |
| Business Analyst | Requirements clarity, process gaps, user stories |
| Default Expert | Generalist fallback — always active, handles anything unrouted |

Users can define fully custom personas with any role description, domain, and accountability scope.

**Session cap:** Maximum 6 active agents per session to avoid incoherent output. The orchestrator merges agents with heavily overlapping domains.

---

### F3 — Project Brain (Persistent Project Knowledge)

Every project has a **Project Brain** — a structured, persisted knowledge layer set up once and reused across all meetings in that project. It is the single source of project truth for all agents.

The Project Brain has four layers:

| Layer | Contents | Indexing method |
|---|---|---|
| Project Profile | Goals, tech stack, team structure, key decisions, known risks | Always injected into system prompt (no retrieval needed) |
| Document Store | Architecture docs, HLD/LLD, ADRs, specs, requirements, runbooks | Chunked and embedded (standard RAG) |
| Code Index | Module summaries, API contracts, DB schemas, dependency map | LLM-generated summaries embedded; raw code retrieved by path |
| Meeting Archive | Prior meeting transcripts and understanding documents | Chunked and embedded; cross-session retrieval |

The Project Brain is shared across all agents in all sessions for that project. Agents retrieve from it with role-specific filters — the Security Agent prioritises auth/security code and docs; the Architect prioritises design docs and system boundaries; the PM gets only high-level module descriptions.

---

### F4 — Project Setup Wizard

The Project Brain is built via a one-time **conversational setup wizard** run before the first meeting. The agent interviews the user:

- "What is this project and what is it trying to achieve?"
- "Where is the codebase? (local folder path or git URL)"
- "Where are the project documents? (folder, Confluence space, SharePoint site)"
- "Are there any directories or files that must never be indexed? (credentials, generated files)"
- "Do you use Jira or GitHub Issues for tracking work?" (optional)
- "What meeting is coming up and what aspect of the project does it focus on?"

After the interview, the agent crawls and indexes all provided sources automatically. The user can review what was indexed, add or remove sources, and save the Project Brain before the first meeting.

Subsequent meetings in the same project skip the wizard — the brain is already loaded. Before each meeting, a **freshness check** offers to re-index any changed files.

---

### F5 — Code Indexing Strategy

Raw code files must **not** be embedded directly into the vector store — this produces noisy, low-quality retrieval. Instead, the system generates **LLM-produced natural-language summaries** at each level of the codebase and embeds those.

**Indexing levels:**

| Level | What is extracted | Stored as |
|---|---|---|
| Repository | README, overall architecture description | Embed as-is |
| Module / Package | LLM summary: purpose, key classes, external dependencies | Embed summary + store file path |
| Class / Service | LLM summary: responsibilities, public interface, design decisions | Embed summary + store file path |
| API Endpoints | Endpoint name, method, parameters, response schema (from OpenAPI / docstrings) | Embed structured description |
| Database Schema | Tables, columns, relationships, constraints | Embed structured description |
| Configuration | Key settings and what they control (.yaml, .env.example) | Embed summary |

Raw code is **not embedded** — it is stored separately and retrieved by exact file path when a deeper dive is needed during a session.

**Excluded by default (never indexed):**
- `.env`, `secrets/`, `credentials/`, `*.key`, `*.pem`
- `node_modules/`, `__pycache__/`, `dist/`, `build/`, `.git/`
- Auto-generated migrations, compiled artifacts, test fixtures with dummy data

The user can extend the exclusion list during setup.

---

### F6 — Role-Based Code Access Tiers

Not every agent needs access to all levels of the codebase. The system applies role-based code access to keep each agent's retrieval focused and relevant:

| Agent | Code access level |
|---|---|
| Solutions Architect | API contracts, module summaries, system boundaries, dependency map |
| Security Engineer | Auth modules, data handling code, third-party dependency list (CVE-relevant), config |
| Data Engineer | DB schemas, data pipeline code, transformation logic, storage config |
| DevOps / SRE | Infrastructure config, deployment scripts, health check endpoints, Dockerfile/Helm |
| Product Manager / BA | README, high-level module descriptions only |
| Default Expert | All levels — full access |

This prevents the PM agent from being confused by 10,000 lines of business logic while ensuring the Security Agent always sees the auth implementation.

---

### F7 — Semantic Doc-to-Code Linking

During indexing, the system attempts to **link documents to the code that implements them**. This allows the agent to surface both the decision and its implementation when either is referenced in a meeting.

Examples:
- "ADR-012 (payment service scaling)" → linked to `payment_service/` module summary
- "HLD Section 4.2 (auth flow)" → linked to `auth/` module and `/auth/token` endpoint
- "Database schema v3" → linked to `models.py` or migration files

When a meeting participant references ADR-012, the agent retrieves both the ADR document and the code that implements it, giving a grounded, implementation-aware answer.

---

### F8 — Project Knowledge Freshness & Incremental Sync

The Project Brain must stay current as the codebase and documents evolve.

**Code sync (git-based):**
- Before each meeting: `git diff HEAD~1 --name-only` identifies changed files
- Changed files are re-summarised (LLM call) and re-embedded
- Takes < 30s for typical daily changesets

**Document sync (file watcher):**
- Watchdog monitors the project docs folder continuously
- Any modified `.md`, `.pdf`, `.docx` triggers re-indexing of that file only

**Pre-meeting freshness prompt:**
- When a session is created: "Last indexed 2 days ago. 4 files changed since then. Re-index now?"
- User can accept (one click) or skip

**Stale warning during meetings:**
- If a file referenced in discussion has changed since it was indexed, the agent flags: "Note: this file was modified after my last index. My knowledge of it may be outdated."

---

### F9 — Project Profile Card (Always in Context)

For core project facts, retrieval is too slow and unreliable. The **Project Profile Card** is a short structured summary (< 500 tokens) injected verbatim into every agent's system prompt — no retrieval needed, always present.

```
Project: Nexus Payment Platform
Stack: Python FastAPI, PostgreSQL, Redis, Kubernetes on GCP
Team: 8 engineers, 2 squads (core-payments, integrations)
Current sprint goal: PCI-DSS compliance for card tokenisation
Key open risks: throughput at 2000 req/s not load-tested; auth token TTL under review
Architecture style: event-driven microservices, Kafka for async
Last updated: 2026-04-07
```

The card is maintained by the team and updated before meetings when the project state changes. It is the first thing every agent reads.

---

### F10 — External Project Integrations (Optional Connectors)

The Project Brain can be enriched from external systems:

| Source | What is indexed | How |
|---|---|---|
| Jira | Open issues, current sprint, epics, recent decisions in comments | Jira REST API → LLM-summarised per issue |
| GitHub / GitLab Issues | Open bugs, feature requests, recent PR discussions | GitHub REST API → LLM-summarised |
| Confluence | Linked pages and spaces specified during setup | Confluence REST API → chunked and embedded |
| SharePoint | Linked document libraries | Microsoft Graph API → chunked and embedded |
| Slack / Teams channels | Pinned messages, recent decisions in specified channels (optional) | Slack/Teams API → LLM-summarised |

All connectors are optional. Each is configured during the Project Setup Wizard and can be enabled or disabled per project.

---

### F11 — Meeting-Specific Context Injection

When creating a session within a project, the system prompts:

- "What aspect of the project does this meeting focus on?" (e.g., "auth service refactor", "Q2 planning")
- "Are there specific components or features being discussed?"
- "Any recent incidents, changes, or context relevant to this meeting?"

These answers trigger a **targeted pre-retrieval**: the system fetches the most relevant Project Brain content for this specific meeting topic and pre-loads it into each agent's working context before the meeting starts — so the first question gets a grounded answer immediately, without cold-start latency.

---

### F12 — Role Onboarding Interview

---

### F4 — OBS Chunked Video Pipeline

OBS is configured to produce continuous 2-minute mp4 segments into a watched folder.

- **Watch** the folder for new mp4 files (file watcher with debounce)
- **Extract audio** from each new segment using FFmpeg
- **Transcribe** using Faster-Whisper, producing timestamped segments
- **Score relevance** of each chunk against each active persona's domain
- **Distribute** chunks to each agent's processing queue based on relevance score
- **Re-embed and index** chunks into the shared session vector store
- **Update each agent's rolling summary** independently every N segments

This enables both global context (orchestrator) and role-filtered context (persona agents).

---

### F5 — Role-Filtered Transcript Attention

Each persona agent scores every incoming transcript chunk for relevance to its domain. This determines what the agent deeply processes vs skims.

- **High relevance (>0.7):** Full embedding, included in agent's rolling summary, flagged for its briefing
- **Medium relevance (0.4–0.7):** Embedded but not in rolling summary; retrievable on query
- **Low relevance (<0.4):** Skipped by this agent; still in shared session store for the orchestrator

This gives users role-specific value: a Security Engineer doesn't have their summary polluted with UX copy discussions. A PM doesn't wade through database schema debates unless they ask.

**Late joiner / replay mode:** A user who joins late or starts listening to an already-recorded meeting selects their role, and the system immediately generates a role-filtered catch-up summary: "Here's what was discussed that's relevant to you as a [Security Engineer]."

---

### F6 — Real-Time Q&A During Meeting (Text + Voice)

During the meeting, humans interact via **text or voice**. Voice is the primary mode — typing is disruptive.

**Voice interaction flow:**
1. Wake word (`"Hey Nexus"`) or hotkey (`Ctrl+Space`) activates the agent
2. STT captures the question (Faster-Whisper, same model already running)
3. Orchestrator classifies and routes to the best specialist agent
4. Response spoken back via TTS — through earphone only, never into meeting audio
5. Full response shown in chat UI for reference

**Critical constraint:** TTS output must never bleed into the meeting microphone or OBS capture. Routed exclusively to a configured headset output device.

**Fast path for voice:** Mid-meeting voice queries route to a single most-relevant agent (low latency). Multi-agent synthesis only happens post-meeting or on explicit user request.

Example queries and routing:
- "What are the risks in this approach?" → Security Agent
- "Is this consistent with our architecture?" → Solutions Architect Agent
- "What did they commit to and by when?" → PM Agent
- "What does this mean for our data pipeline?" → Data Engineer Agent
- "Summarise everything so far" → Orchestrator (synthesizes all agents)

---

### F7 — Inter-Agent Conflict Detection

When two or more persona agents reach conflicting conclusions about the same topic, the orchestrator **surfaces the conflict explicitly** rather than silently resolving it.

Conflicts appear in the chat UI immediately and are recorded in the understanding document as open questions.

**Example conflicts:**
> **Conflict — Caching Strategy [14:32]**
> Solutions Architect Agent: Accepted the Redis caching approach as proposed.
> Security Agent: Flagged this as a potential data exposure risk — session tokens may be cached without TTL.
> → Not resolved in meeting. → **Open Question**

> **Conflict — API Contract [22:15]**
> Backend Agent: Proposed breaking change to the `/auth/token` endpoint.
> Frontend Agent: Current implementation depends on this contract.
> → Cross-role dependency not acknowledged. → **Action Item: Backend + Frontend to align.**

---

### F8 — Role-Specific Post-Meeting Briefings

After the meeting, each persona receives a **personalised briefing** tailored to its domain — not one shared dump.

Each briefing contains:

| Section | Description |
|---|---|
| What Matters to You | High-relevance discussion filtered for this role |
| Your Action Items | Tasks assigned to or owned by this role |
| Decisions in Your Domain | Decisions made that fall within your accountability |
| Risks in Your Area | Risks identified relevant to your domain |
| Open Questions for You | Unresolved questions you need to answer |
| Safe to Ignore | Topics discussed that are not relevant to your role |
| Cross-Role Dependencies | Things others committed to that affect your work |

Briefings are generated automatically after the meeting ends and are available before the shared understanding document is co-created.

---

### F9 — Shared Collaborative Understanding Document

After individual briefings are generated, the orchestrator facilitates a **shared understanding document** co-created across all active agents and the human participants.

The orchestrator actively asks clarifying questions to fill gaps:
- "You mentioned migrating the database — was the target platform decided?"
- "The Security Agent flagged a risk at 14:32. Was this acknowledged by the team?"
- "I noticed three open questions from the last meeting on this topic were not addressed."

The document includes all role perspectives, surfaced conflicts, and expert commentary from each agent.

---

### F10 — Asynchronous Agent Participation

A stakeholder who **cannot attend** sends their persona agent ahead of time. The agent:

- Monitors the transcript passively during the meeting
- Applies its relevance filter to flag what falls in the stakeholder's domain
- After the meeting, generates a personalised briefing for the absent stakeholder
- Flags anything that requires the stakeholder's input or decision as a priority item

This extends the value of the system to people who were not in the room.

---

### F11 — Accountability Mapping

The role onboarding interview captures the user's accountability scope. The system maps every decision, action item, and risk to an accountability owner based on this.

Output: automatic lightweight **RACI summary** per meeting.

- **Responsible**: who does the task
- **Accountable**: whose domain owns the outcome
- **Consulted**: who was asked for input
- **Informed**: who needs to know the decision

This is derived from transcript + role definitions, not manually filled.

---

### F12 — Meeting Health Monitor

The orchestrator runs a background health monitor during the meeting and surfaces gentle nudges in the chat UI. These are informational — not intrusive.

**Trigger conditions:**
- 15+ minutes with no decisions or action items captured
- Scope expanded significantly from the stated agenda
- Open questions from a prior meeting on this topic were not addressed
- A topic was tabled without a resolution or owner assigned
- Two or more agents have flagged the same risk independently

Health alerts appear as a sidebar notification, not as spoken interruptions.

---

### F13 — Transcription

- Full verbatim transcription with timestamps (not summaries)
- Per-segment transcription as each mp4 chunk arrives
- Speaker diarization (who said what) — Phase 2
- Transcript stored persistently per session and reusable for replay

---

### F14 — LLM Reasoning (per agent)

Each persona agent generates on demand or post-meeting:

- Role-filtered summary
- Decisions in its domain
- Action items with owners
- Risks in its domain
- Gap analysis from its perspective
- Expert commentary from its domain and industry knowledge

The orchestrator synthesizes across all agents into the shared output.

---

### F15 — Chat & Voice Interface

**Input modes:**
- **Text**: typed query in the chat UI (always available)
- **Voice**: wake word or hotkey → STT → routed via orchestrator → TTS response to earphone

**Session states:**
- **During Meeting** (live): answers based on transcript processed so far. Live badge + "context current as of [timestamp]" shown.
- **Post-Meeting**: full transcript available. Multi-agent synthesis, brainstorming, and conflict resolution supported.

**Voice output routing:**
- TTS routed exclusively to configured headset/earphone output device
- Never routed to system speakers or meeting microphone
- Spoken responses condensed to 2–3 sentences; full response shown in chat UI

---

### F16 — Knowledge Integration (RAG)

Vector store namespaces:

| Namespace | Contents | Scope |
|---|---|---|
| `project_brain_{project_id}` | Document store: architecture docs, ADRs, specs, runbooks | Project-scoped, persists |
| `project_code_{project_id}` | Code index: module summaries, API contracts, DB schemas | Project-scoped, incrementally updated |
| `project_meetings_{project_id}` | Meeting archive: prior transcripts + understanding docs | Project-scoped, grows over time |
| `persona_domain_{persona_id}` | Role-specific domain knowledge, industry trends | Persona-scoped, persists |
| `session_transcript_{session_id}` | This meeting's transcript chunks | Session-scoped |

All agents share the `project_*` namespaces. Role-based code access tiers control which levels of `project_code_{project_id}` each agent can retrieve. The `persona_domain_{persona_id}` namespace contains generic domain knowledge not tied to any specific project (e.g., security best practices for the Security Agent).

---

### F17 — Teams Bot Features (Phase 3)

- Auto-join meeting as named participant
- Record session via Microsoft Graph API
- Run full multi-agent pipeline
- Post shared summary to Teams channel
- Create per-role threads with tailored briefings
- Tag relevant team members in their respective threads

---

## Non-Functional Requirements

| Requirement | Target |
|---|---|
| Segment processing latency | < 30s per 2-min mp4 chunk |
| Transcription accuracy | > 90% WER on clear audio |
| Voice round-trip (activation → spoken answer) | < 10s |
| LLM chat response (single agent) | < 5s p95 |
| Multi-agent synthesis response | < 15s p95 |
| Relevance scoring per chunk per agent | < 1s per agent |
| Post-meeting briefing generation | < 60s per persona |
| Max active agents per session | 6 |
| Storage | Local FS for MVP; S3-compatible for cloud |
| Security | No audio/transcript leaves local machine in MVP |
| Modularity | Each component independently replaceable |
| Scalability | Cloud-ready for Phase 3+ |

---

## Tech Stack

### Backend
- Python (FastAPI) — transcription pipeline + agent API
- Watchdog — folder watcher for OBS mp4 segments and document changes
- Celery / asyncio — parallel agent processing

### AI / ML
- Faster-Whisper — GPU-accelerated transcription (meeting audio + voice query STT)
- WhisperX / pyannote — speaker diarization
- Claude / OpenAI / Llama — LLM reasoning (per agent, orchestrator, code summarisation)
- LangGraph — multi-agent orchestration and state graph
- Sentence-Transformers — relevance scoring (lightweight, fast)
- OpenAI TTS / ElevenLabs / Kokoro — TTS for spoken responses (earphone only)
- Pynput / keyboard — hotkey detection for voice activation
- Porcupine / Vosk — wake word detection

### Code Indexing
- tree-sitter / ast (Python) — AST parsing for code structure extraction
- GitPython — git integration for change detection and incremental sync
- PyPDF2 / python-docx / unstructured — document parsing (PDF, DOCX, MD)

### Audio Processing
- FFmpeg — audio extraction from mp4 segments
- OBS 3.11 — capture source (2-min segment output)
- sounddevice / pyaudio — TTS output device routing

### Storage
- PostgreSQL — session metadata, persona profiles, transcript, understanding docs, project brain metadata
- Local FS / S3 — mp4 segment storage, raw code files, document files
- Vector DB:
  - ChromaDB (local, persistent, per-project and per-persona namespaces)
  - Pinecone / Weaviate (cloud, Phase 3+)

### Frontend
- React / Next.js — chat UI with multi-agent panel + project brain status panel
- Electron (optional) — desktop app wrapper

### Integration
- Jira REST API — issue and sprint context (optional connector)
- GitHub / GitLab REST API — issues and PR discussions (optional connector)
- Confluence REST API — page crawling (optional connector)
- Microsoft Graph API — SharePoint, Teams bot (Phase 3)
- Azure Bot Service — Teams bot hosting (Phase 3)

---

## High-Level Flows

### First-Time Project Setup (one-time per project)

```
User creates a new project
    → Agent runs Project Setup Wizard (conversational interview)
    → Crawls: git repo, docs folder, optional Jira/Confluence/GitHub
    → Code indexer: AST parse → LLM summarise per module/class/API/schema
    → Document indexer: chunk + embed all docs → project_brain_{project_id}
    → Code summaries embedded → project_code_{project_id}
    → Project Profile Card drafted by agent → user reviews and confirms
    → Project Brain ready — shared by all future meetings in this project
```

### Pre-Meeting Setup (per session)

```
User creates a session for an existing project
    → Freshness check: "4 files changed since last index. Re-index now?"
    → Meeting-specific context interview: "What aspect of the project does this meeting focus on?"
    → Targeted pre-retrieval: top-K project brain chunks for this meeting's topic pre-loaded
    → Agent conducts role onboarding interview for each participant
    → Persona profiles created (role, accountability, relevance filters)
    → Per-persona domain knowledge loaded → persona_domain_{persona_id}
    → OBS folder watcher activated
    → Orchestrator initialised with all active personas + Project Brain access
```

### During Meeting (Multi-Agent Pipeline)

```
OBS mp4 segment (every 2 min)
    → File Watcher → FFmpeg → Faster-Whisper → transcript chunks
    → Relevance scorer: scores chunks against each active persona
    → Chunks distributed to relevant agents + shared session store
    → Each agent updates its own rolling summary
    → Orchestrator monitors for conflicts across agent summaries
    → Meeting Health Monitor runs in background

Human voice query (wake word / hotkey)
    → STT → Orchestrator classifies query
    → Routes to best specialist agent (fast path)
    → TTS response → earphone only
    → Full response in chat UI
```

### Post-Meeting (Briefings + Shared Understanding)

```
Meeting ends
    → Each persona agent generates its role-specific briefing (parallel)
    → Orchestrator collects all briefings + identifies conflicts + cross-role dependencies
    → Shared understanding document draft created
    → Collaborative dialogue: humans + agents refine, fill gaps, resolve conflicts
    → Final document exported as Markdown / PDF
    → Absent stakeholders receive their async briefings
```

### Async Participant

```
Absent stakeholder registers persona before meeting
    → Agent runs passively during meeting (no voice interaction)
    → Post-meeting: generates personalised briefing + priority flags
    → Briefing delivered to stakeholder (email / Teams / chat)
```

### Late Joiner / Replay Mode

```
User joins late or starts replay of recorded meeting
    → Selects role (or onboarded via interview)
    → Agent generates role-filtered catch-up summary: "Here's what matters to you"
    → Full Q&A available over the already-processed transcript
```

---

## Delivery Phases

### Phase 1 — MVP (Single Agent, Post-Meeting, No Project Brain)
- OBS folder watcher + FFmpeg audio extraction
- Faster-Whisper transcription per segment
- Default Expert Agent only
- Post-meeting text chat over full transcript
- Basic role onboarding interview

### Phase 2 — Project Brain (Core Knowledge Foundation)
- Project Setup Wizard (conversational, one-time per project)
- Document indexer: architecture docs, ADRs, specs → ChromaDB
- Code indexer: AST parsing → LLM module/class/API summaries → ChromaDB
- Project Profile Card always injected into agent system prompt
- Meeting-specific context injection (targeted pre-retrieval)
- Incremental sync: git diff + file watcher for freshness
- Role-based code access tiers per agent

### Phase 3 — Real-Time + Voice (Single Agent + Project Brain)
- Incremental transcript accumulation during meeting
- Mid-meeting voice Q&A (wake word / hotkey → earphone response)
- Rolling summary updates per segment
- Agents retrieve from Project Brain during Q&A — project-grounded answers
- Semantic doc-to-code linking

### Phase 4 — Multi-Agent Architecture
- Orchestrator + multiple specialist persona agents
- Role-filtered transcript attention and relevance scoring
- Inter-agent conflict detection and surfacing
- Meeting Health Monitor
- Each agent retrieves from Project Brain with role-based access filter

### Phase 5 — Role-Specific Briefings + Understanding Document
- Per-persona post-meeting briefings (parallel generation)
- Accountability mapping and RACI output
- Shared collaborative understanding document via orchestrator
- Cross-role dependency detection
- Async agent participation for absent stakeholders

### Phase 6 — External Integrations + Meeting Archive
- Jira / GitHub Issues connector
- Confluence / SharePoint connector
- Prior meeting transcript retrieval (cross-session RAG from meeting archive)
- Role-filtered catch-up for late joiners
- Speaker diarization
- Export to Markdown / PDF

### Phase 7 — Teams Bot Integration
- Auto-join as named participant
- Graph API recording
- Per-role Teams threads with tailored briefings
- Tag relevant team members automatically
