# Architecture Overview

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client Layer                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │   Web UI    │  │  Mobile App │  │  API Clients (curl)     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API Gateway Layer                          │
│                    FastAPI Application (main.py)                │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    API Routes                            │  │
│  │  /api/auth      /api/projects   /api/reviews             │  │
│  │  /api/checklists               /api/reports               │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Business Logic Layer                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    Services                              │  │
│  │  ChecklistParser    ChecklistOptimizer (AI)              │  │
│  │  ReviewAgent        ReportGenerator                      │  │
│  │  VoiceInterface                                          │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Access Layer                          │
│                 SQLAlchemy ORM (Async)                          │
│  Projects │ Checklists │ Reviews │ Reports │ Users             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Storage Layer                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  SQLite/    │  │  ChromaDB   │  │  File System            │ │
│  │  PostgreSQL │  │  (Vector)   │  │  (uploads, reports)     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

## Component Architecture

See: [components.md](components.md)

## Data Flow

See: [data-flow.md](data-flow.md)

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Web Framework** | FastAPI | REST API |
| **Database ORM** | SQLAlchemy + Alembic | Data access |
| **AI Orchestration** | LangChain + LangGraph | Agent workflows |
| **LLM** | OpenAI GPT-4o | Intelligence |
| **Voice STT** | OpenAI Whisper | Speech-to-text |
| **Voice TTS** | OpenAI TTS | Text-to-speech |
| **Vector DB** | ChromaDB | Embeddings storage |
| **File Parsing** | Pandas + OpenPyXL | Excel processing |
| **PDF Generation** | ReportLab | PDF reports |
| **Authentication** | JWT + Passlib | Security |

## Key Design Decisions

See: [decisions.md](decisions.md)

---

*Last Updated: 2026-03-25*
