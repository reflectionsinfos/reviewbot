# Nexus AI — Meeting Recorder Agent

An enterprise-grade **Multi-Agent Meeting Intelligence System** powered by LangGraph, Faster-Whisper, and large language models. Multiple specialist AI agents participate in meetings as expert observers, grounded in a persistent **Project Brain** that gives every agent deep knowledge of your project before the meeting starts.

---

## What It Does

- **Records and transcribes** meetings in real-time from OBS-generated video segments
- **Deploys specialist AI agents** (Solutions Architect, Security Engineer, PM, Data Engineer, DevOps/SRE, BA, Default Expert) that each maintain a role-filtered view of the discussion
- **Grounds every agent** in a persistent Project Brain: your codebase, architecture docs, ADRs, past meetings — so answers reflect your actual project, not generic domain knowledge
- **Answers questions live** via voice (wake word "Hey Nexus" or Ctrl+Space) — response in your earphone, never in the meeting audio
- **Detects inter-agent conflicts** and surfaces them explicitly — disagreements between agents appear in the chat UI and the final document
- **Generates role-specific briefings** post-meeting — every participant (present or async) gets a personalised summary scoped to their domain
- **Co-creates a shared understanding document** across all agents — decisions, action items, risks, RACI map, open questions

---

## Architecture at a Glance

```
┌─────────────────────────────────────────────────────┐
│                  PROJECT BRAIN                       │
│  Profile Card │ Doc Store │ Code Index │ Meeting Archive │
└───────────────────────────┬─────────────────────────┘
                            │ all agents read from here
                            ▼
OBS (2-min mp4) → File Watcher → FFmpeg → Faster-Whisper
                            │
                    Relevance Scorer
                            │
           ┌────────────────┼────────────────┐
           ▼                ▼                ▼
    Architect Agent   Security Agent    PM Agent  ...
           └────────────────┴────────────────┘
                            │
                    Orchestrator Agent
                    (route │ conflict detect │ synthesize)
                            │
              Chat UI │ Voice Interface │ REST API
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web Framework | FastAPI + Uvicorn (async) |
| AI Orchestration | LangGraph + LangChain |
| LLM | Claude / OpenAI GPT-4o / Llama (configurable) |
| Transcription | Faster-Whisper (GPU-accelerated) |
| Relevance Scoring | sentence-transformers/all-MiniLM-L6-v2 |
| Wake Word | Porcupine / Vosk |
| TTS | OpenAI TTS / ElevenLabs / Kokoro (local) |
| Vector Store | ChromaDB (local) → Pinecone/Weaviate (Phase 3+) |
| Database | PostgreSQL 15 via asyncpg |
| Code Parsing | tree-sitter / Python ast |
| Doc Parsing | PyPDF2, python-docx, unstructured |
| Audio | FFmpeg, sounddevice |
| File Watching | Watchdog |
| Frontend | React / Next.js (Phase 4+) |

---

## Project Structure

```
recorder/
├── README.md
├── CLAUDE.md                          # Developer reference for Claude Code
├── pyproject.toml                     # Python project config + dependencies
├── .env.example                       # Required environment variables
├── docker-compose.yml
├── Dockerfile
├── docs/
│   ├── requirements.md                # Functional + non-functional requirements
│   ├── design.md                      # System design + component specs
│   └── implementation_plan.md         # Stories, tasks, phases
├── src/recorder/
│   ├── main.py                        # FastAPI app entry point
│   ├── core/                          # Config, logging, exceptions
│   ├── db/                            # SQLAlchemy models, migrations
│   ├── api/                           # REST routes + WebSocket handlers
│   ├── agents/
│   │   ├── orchestrator/              # Orchestrator LangGraph agent
│   │   ├── persona/                   # Persona agent + nodes
│   │   ├── onboarding/                # Role interview state machine
│   │   └── templates/                 # Built-in persona templates
│   ├── project_brain/
│   │   ├── setup_wizard.py            # Conversational project setup (PB-1)
│   │   ├── document_indexer.py        # Doc chunking + embedding (PB-2)
│   │   ├── code_indexer.py            # AST parse + LLM summaries (PB-3)
│   │   ├── incremental_sync.py        # Git diff + file watcher (PB-4)
│   │   ├── external_connectors/       # Jira, GitHub, Confluence, SharePoint (PB-5)
│   │   ├── profile_card.py            # Project Profile Card (PB-6)
│   │   └── context_injection.py       # Meeting-specific pre-retrieval (PB-7)
│   ├── pipeline/                      # OBS segment processing pipeline
│   ├── voice/                         # Wake word, STT, TTS, audio routing
│   ├── vector_store/                  # ChromaDB client, namespaces, retrieval
│   ├── services/                      # Session mgmt, briefings, conflict detection
│   └── schemas/                       # Pydantic schemas
├── tests/
│   ├── unit/
│   ├── integration/
│   └── fixtures/
└── scripts/
```

---

## Getting Started

### Prerequisites

- Python 3.11+
- PostgreSQL 15
- FFmpeg (on PATH)
- CUDA GPU recommended (for Faster-Whisper `large-v3`; CPU fallback available)
- OBS 32.1+ configured for 2-minute segment output

### OBS Configuration

In OBS: **Settings → Output → Recording**:
- Output format: `mp4`
- Enable automatic file splitting: every `2 minutes` (120 seconds)
- Output folder: set `OBS_WATCH_FOLDER` in `.env` to match

### Installation

```bash
cd recorder/
pip install -e ".[dev]"
cp .env.example .env
# Edit .env with your API keys and paths
```

### Database Setup

```bash
# Start PostgreSQL (or use Docker)
docker-compose up db -d

# Apply migrations
alembic upgrade head
```

### Running (Development)

```bash
uvicorn src.recorder.main:app --reload --port 8100
# API docs: http://localhost:8100/docs
```

### Running (Docker)

```bash
docker-compose up --build
```

---

## Environment Variables

See `.env.example` for all variables. Key ones:

```env
# Database
DATABASE_URL=postgresql+asyncpg://recorder_user:password@localhost:5432/recorder_db

# LLM (at least one required)
ACTIVE_LLM_PROVIDER=anthropic       # anthropic | openai | groq | qwen
ANTHROPIC_API_KEY=
OPENAI_API_KEY=

# OBS Pipeline
OBS_WATCH_FOLDER=/path/to/obs/output
WHISPER_MODEL=large-v3              # or "medium" for CPU

# Voice Interface
VOICE_ENABLED=true
TTS_PROVIDER=openai                 # openai | elevenlabs | kokoro
TTS_OUTPUT_DEVICE_INDEX=1           # sounddevice device index for headset
WAKE_WORD=hey nexus
ACTIVATION_HOTKEY=ctrl+space

# Optional: External Integrations
JIRA_URL=
JIRA_API_TOKEN=
GITHUB_TOKEN=
CONFLUENCE_URL=
CONFLUENCE_TOKEN=
```

---

## Delivery Phases

| Phase | Scope | Status |
|---|---|---|
| 1 | MVP — Single agent, post-meeting Q&A, OBS pipeline | Planned |
| 2 | Project Brain — doc/code indexing, profile card, sync | Planned |
| 3 | Real-Time + Voice — live Q&A, wake word, TTS to earphone | Planned |
| 4 | Multi-Agent — orchestrator + specialist personas | Planned |
| 5 | Briefings + Understanding Doc — role-specific output | Planned |
| 6 | External Integrations + Meeting Archive | Planned |
| 7 | Teams Bot — auto-join, Graph API, per-role threads | Planned |

See [docs/implementation_plan.md](docs/implementation_plan.md) for detailed stories and tasks.

---

## Key Design Decisions

- **OBS chunked pipeline**: 2-minute mp4 segments allow incremental processing without waiting for the meeting to end
- **LLM-generated code summaries, not raw code embeddings**: AST parse → natural-language summary per module/class/endpoint — eliminates noisy vector search on syntax
- **Project Profile Card always in system prompt**: < 500 tokens, zero retrieval latency, eliminates cold-start for core project facts
- **TTS to earphone only**: Voice responses never enter the meeting audio or OBS capture — audio device isolation enforced at the sounddevice level
- **Role-based code access tiers**: PM sees README only; Security sees auth/data code; Default Expert sees all — keeps each agent's retrieval focused
- **Conflict surfacing, not resolution**: Inter-agent disagreements are recorded and shown explicitly — never silently merged

See [docs/design.md](docs/design.md) for the full system design.

---

## Contributing

See [CLAUDE.md](CLAUDE.md) for developer conventions and coding guidelines.
