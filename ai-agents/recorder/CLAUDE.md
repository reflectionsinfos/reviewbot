# Nexus AI — Meeting Recorder Agent: Claude Code Reference

## Project Overview

AI-powered **Multi-Agent Meeting Intelligence System**. Multiple specialist agents (Solutions Architect, Security Engineer, PM, Data Engineer, DevOps/SRE, BA, Default Expert) participate in meetings as expert observers, grounded in a persistent **Project Brain** (per-project knowledge: codebase, docs, prior meetings).

OBS produces 2-minute mp4 segments → pipeline transcribes → agents process in parallel → voice Q&A answered via earphone → role-specific briefings + shared understanding document generated post-meeting.

---

## Project Structure

```
src/recorder/
├── main.py                        # FastAPI entry point + lifespan
├── core/
│   ├── config.py                  # ALL env vars via Pydantic Settings
│   ├── logging.py                 # Structured logging setup
│   └── exceptions.py              # Domain exception hierarchy
├── db/
│   ├── session.py                 # Async engine, get_db, init_db
│   ├── models.py                  # SQLAlchemy ORM models
│   └── migrations/                # Alembic migrations
├── api/
│   ├── routes/                    # FastAPI routers (projects, sessions, personas, chat)
│   └── websockets/                # WebSocket handlers for live chat
├── agents/
│   ├── orchestrator/              # Orchestrator LangGraph agent
│   │   ├── agent.py               # Graph definition
│   │   ├── states.py              # OrchestratorState TypedDict
│   │   └── nodes/                 # One file per node function
│   ├── persona/                   # Specialist persona agent
│   │   ├── agent.py               # Graph definition
│   │   ├── states.py              # PersonaAgentState TypedDict
│   │   └── nodes/                 # receive_chunk, answer_query, generate_briefing, ...
│   ├── onboarding/                # Role Onboarding Interview state machine
│   │   ├── role_interview.py      # LangGraph interview flow
│   │   └── states.py              # OnboardingState TypedDict
│   └── templates/                 # Built-in persona configs (architect, security, pm, ...)
├── project_brain/
│   ├── setup_wizard.py            # PB-1: Conversational project setup (LangGraph)
│   ├── document_indexer.py        # PB-2: doc chunking + embedding → project_brain_{id}
│   ├── code_indexer.py            # PB-3: AST parse → LLM summary → project_code_{id}
│   ├── incremental_sync.py        # PB-4: git diff + Watchdog file watcher
│   ├── external_connectors/       # PB-5: Jira, GitHub, Confluence, SharePoint
│   ├── profile_card.py            # PB-6: < 500 token card always in system prompt
│   └── context_injection.py       # PB-7: targeted pre-retrieval before meeting
├── pipeline/
│   ├── file_watcher.py            # Watchdog OBS folder monitor
│   ├── audio_extractor.py         # FFmpeg subprocess: mp4 → 16kHz mono wav
│   ├── transcription.py           # Faster-Whisper STT
│   ├── chunking.py                # 60s windows, 15s overlap
│   └── relevance_scorer.py        # sentence-transformers scoring per chunk per agent
├── voice/
│   ├── wake_word.py               # Porcupine / Vosk wake word detection
│   ├── stt.py                     # Faster-Whisper for voice query STT
│   ├── tts.py                     # OpenAI TTS / ElevenLabs / Kokoro
│   └── audio_router.py            # sounddevice output device routing (earphone only)
├── vector_store/
│   ├── client.py                  # ChromaDB persistent client
│   ├── namespaces.py              # Namespace management + metadata schemas
│   └── retrieval.py               # Role-filtered retrieval helpers
├── services/
│   ├── session_manager.py         # Session lifecycle (PRE_MEETING → ARCHIVED)
│   ├── briefing_generator.py      # Role-specific briefing generation (parallel)
│   ├── understanding_doc.py       # Shared understanding document co-creation
│   ├── conflict_detector.py       # Inter-agent conflict detection + ConflictRecord
│   ├── health_monitor.py          # Background meeting health coroutine
│   └── export.py                  # Markdown + PDF export (ReportLab)
└── schemas/                       # Pydantic request/response schemas
```

---

## Key Models (SQLAlchemy)

- `Project` — git_repo_path, docs_folder, profile_card (text), last_indexed_at, last_git_commit
- `Session` — project_id, meeting_focus, preloaded_context (text), status, global_rolling_summary
- `Persona` — session_id, role_title, accountability_areas (JSON), rolling_summary, is_async, briefing (JSON)
- `TranscriptChunk` — session_id, segment_index, start_time, end_time, speakers (JSON), text, relevance_scores (JSON)
- `ProjectCodeIndex` — project_id, file_path, component_name, level (module|class|endpoint|schema), summary (text), git_commit
- `Conflict` — session_id, topic, agents_involved (JSON), agent_positions (JSON), conflict_type, resolution_status
- `UnderstandingDocument` — session_id, version, content (JSON)

---

## Vector Store Namespaces

| Namespace | Scope | Contents |
|---|---|---|
| `project_brain_{project_id}` | Project, persistent | Docs, ADRs, specs, runbooks, external integrations |
| `project_code_{project_id}` | Project, persistent | LLM-generated code summaries (role-filtered at retrieval) |
| `project_meetings_{project_id}` | Project, growing | Prior meeting transcripts + understanding docs |
| `persona_domain_{persona_id}` | Persona, persistent | Generic domain knowledge (not project-specific) |
| `session_transcript_{session_id}` | Session only | This meeting's transcript chunks |

**Profile Card is NOT in ChromaDB** — injected verbatim into system prompt, always, no retrieval.

---

## Agent Retrieval Order (answer_query node)

```
1. inject:    project.profile_card          (always, no retrieval)
2. inject:    session.preloaded_context     (pre-retrieved for this meeting topic)
3. inject:    agent.rolling_summary         (always, no retrieval)
4. retrieve:  session_transcript_{id}       (what was said so far)
5. retrieve:  project_brain_{id}            (docs, ADRs, specs)
6. retrieve:  project_code_{id}             (role-filtered code summaries)
7. retrieve:  persona_domain_{id}           (generic domain knowledge)
8. generate:  LLM response with citations
```

---

## Environment Variables

All vars in `src/recorder/core/config.py` (Pydantic Settings). Key ones:

```env
# Required
DATABASE_URL=postgresql+asyncpg://recorder_user:password@localhost:5432/recorder_db
SECRET_KEY=<generate: python -c "import secrets; print(secrets.token_urlsafe(32))">

# LLM (at least one required)
ACTIVE_LLM_PROVIDER=anthropic       # anthropic | openai | groq | qwen
ANTHROPIC_API_KEY=
OPENAI_API_KEY=
GROQ_API_KEY=

# OBS Pipeline
OBS_WATCH_FOLDER=/path/to/obs/output
WHISPER_MODEL=large-v3              # large-v3 (GPU) | medium (CPU)
SEGMENT_DURATION_SECS=120

# Voice
VOICE_ENABLED=true
TTS_PROVIDER=openai                 # openai | elevenlabs | kokoro
TTS_OUTPUT_DEVICE_INDEX=1           # sounddevice index for headset
WAKE_WORD=hey nexus
ACTIVATION_HOTKEY=ctrl+space
STT_LISTEN_DURATION_SECS=8

# Vector Store
CHROMA_PERSIST_DIR=./data/chroma
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

# Optional: External Integrations
JIRA_URL=
JIRA_EMAIL=
JIRA_API_TOKEN=
GITHUB_TOKEN=
CONFLUENCE_URL=
CONFLUENCE_TOKEN=
SHAREPOINT_TENANT_ID=
SHAREPOINT_CLIENT_ID=
SHAREPOINT_CLIENT_SECRET=
ELEVENLABS_API_KEY=
```

---

## Running

```bash
# Development
pip install -e ".[dev]"
uvicorn src.recorder.main:app --reload --port 8100

# Docker
docker-compose up --build
# API:  http://localhost:8100
# Docs: http://localhost:8100/docs
```

---

## Coding Conventions

- **Async everywhere** — `async def` + `await` for all I/O (DB, HTTP, file, LLM calls)
- **Eager loading** — always use `selectinload()` when accessing SQLAlchemy relationships to avoid `MissingGreenlet` in async context
- **Config via settings** — all environment values through `settings.*` (never hardcoded)
- **Type hints required** on all functions and methods
- **Pydantic schemas** for all API request/response bodies
- **DB error handling** — wrap operations in try/except, always rollback on error
- **Raw code never embedded** — code indexer generates LLM summaries; raw code stored to FS, retrieved by path
- **Profile Card never retrieved** — injected verbatim into system prompt every time
- **TTS to headset only** — never route TTS to system default speaker or OBS capture device

---

## Common Pitfalls

1. **Lazy loading crash** — always `selectinload(Model.relationship)` before accessing related objects in async SQLAlchemy
2. **OBS file not complete** — File Watcher debounces 3s; poll size stability before enqueuing. Never open a segment until size is stable for 2+ consecutive checks
3. **TTS audio bleed** — always pass explicit `device` index to `sounddevice` — do NOT use default output
4. **Raw code in vector store** — raw code files must never be passed to ChromaDB. Only LLM-generated summaries are embedded; raw code goes to local FS
5. **Profile Card retrieval** — profile card must be injected directly as a string into the system prompt. It must never go through ChromaDB retrieval
6. **Code indexer exclusions** — always apply the exclusion list (`.env`, `secrets/`, `node_modules/`, `__pycache__/`, etc.) before parsing any file
7. **Conflict suppression** — inter-agent conflicts must be recorded and surfaced, never silently merged or resolved by the orchestrator
8. **Stale chunk warning** — when a retrieved chunk's `last_modified` is older than the actual file's modification time, the agent must prepend a stale warning

---

## API Endpoints

```
POST   /api/projects/                     Create project (triggers Setup Wizard)
GET    /api/projects/                     List projects
GET    /api/projects/{id}                 Get project + brain status
POST   /api/projects/{id}/sync            Trigger incremental sync
GET    /api/projects/{id}/profile-card    Get current profile card
PUT    /api/projects/{id}/profile-card    Update profile card

POST   /api/sessions/                     Create session (triggers pre-retrieval)
GET    /api/sessions/                     List sessions
POST   /api/sessions/{id}/start           Start OBS watcher + agents
POST   /api/sessions/{id}/complete        End meeting → trigger briefing generation
GET    /api/sessions/{id}/transcript      Full session transcript

POST   /api/personas/                     Create persona (triggers role interview)
GET    /api/sessions/{id}/personas        List personas in session
GET    /api/personas/{id}/briefing        Get role-specific briefing (post-meeting)

POST   /api/sessions/{id}/query           Submit text query → agent response
WS     /ws/sessions/{id}/chat             Live chat WebSocket

GET    /api/sessions/{id}/understanding   Get understanding document
POST   /api/sessions/{id}/understanding   Update / co-create understanding document
GET    /api/sessions/{id}/conflicts       List detected conflicts
GET    /api/sessions/{id}/health          Meeting health status

GET    /api/sessions/{id}/export/{format} Export: markdown | pdf

GET    /health
```

---

## Database Migrations

```bash
alembic revision --autogenerate -m "description"
alembic upgrade head
alembic downgrade -1
```

---

## Testing

```bash
pytest tests/ -v
pytest tests/ -v --cov=src/recorder
pytest tests/unit/ -v          # fast, no external deps
pytest tests/integration/ -v   # requires running PostgreSQL + ChromaDB
```

---

## Docker Architecture

- **app** — FastAPI (waits for db health check)
- **db** — PostgreSQL 15 (`scripts/init-db.sql`)
- **chroma** — ChromaDB persistent server (optional; default is embedded)
- DB host port: **5436** (avoids clash with ReviewBot on 5435 and local PG on 5432)

---

## Implementation Phases

See [docs/implementation_plan.md](docs/implementation_plan.md).

Phase 1 (MVP) is the starting point — single Default Expert agent, post-meeting chat, OBS pipeline only.
