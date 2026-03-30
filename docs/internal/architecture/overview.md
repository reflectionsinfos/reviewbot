# Architecture Overview

> High-level system architecture for the AI Tech & Delivery Review Agent

---

## 📋 Table of Contents

1. [System Architecture](#system-architecture)
2. [Component Architecture](#component-architecture)
3. [File Structure](#file-structure)
4. [Technology Stack](#technology-stack)
5. [Design Principles](#design-principles)

---

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
│  │  ┌──────────────────┐  ┌──────────────────────────────┐  │  │
│  │  │ ChecklistParser  │  │ ChecklistOptimizer (AI)      │  │  │
│  │  │ - Excel parsing  │  │ - Domain recommendations     │  │  │
│  │  └──────────────────┘  └──────────────────────────────┘  │  │
│  │  ┌──────────────────┐  ┌──────────────────────────────┐  │  │
│  │  │ ReviewAgent      │  │ ReportGenerator              │  │  │
│  │  │ - LangGraph      │  │ - Markdown/PDF               │  │  │
│  │  │ - Workflow mgmt  │  │ - Compliance scoring         │  │  │
│  │  └──────────────────┘  └──────────────────────────────┘  │  │
│  │  ┌──────────────────┐                                    │  │
│  │  │ VoiceInterface   │                                    │  │
│  │  │ - Whisper STT    │                                    │  │
│  │  │ - OpenAI TTS     │                                    │  │
│  │  └──────────────────┘                                    │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Data Access Layer                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                 SQLAlchemy ORM (Async)                   │  │
│  │  Projects │ Checklists │ Reviews │ Reports │ Users       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       Storage Layer                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐ │
│  │  PostgreSQL │  │  ChromaDB   │  │  File System            │ │
│  │ (Cloud SQL) │  │  (Vector)   │  │  (Cloud Run Storage)    │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Component Architecture

### Review Agent Workflow

```
┌────────────────────────────────────────────────────────────┐
│                    Review Agent Core                       │
│                                                            │
│  ┌──────────────┐                                         │
│  │  Initialize  │                                         │
│  │   Review     │                                         │
│  └──────┬───────┘                                         │
│         │                                                  │
│         ▼                                                  │
│  ┌──────────────┐     Yes                                  │
│  │  Optimize    │────────┐                                 │
│  │  Checklist?  │        │                                 │
│  └──────┬───────┘        │                                 │
│         │ No            ▼                                 │
│         │        ┌────────────────┐                        │
│         │        │  AI-powered    │                        │
│         │        │  Recommendations│                       │
│         │        └───────┬────────┘                        │
│         ▼                │                                 │
│  ┌──────────────┐        │                                 │
│  │  Ask         │◄───────┘                                 │
│  │  Question    │                                          │
│  └──────┬───────┘                                          │
│         │                                                  │
│         ▼                                                  │
│  ┌──────────────┐                                          │
│  │  Process     │                                          │
│  │  Response    │                                          │
│  └──────┬───────┘                                          │
│         │                                                  │
│         ▼                                                  │
│  ┌──────────────┐                                          │
│  │  Assess RAG  │                                          │
│  │  Status      │                                          │
│  └──────┬───────┘                                          │
│         │                                                  │
│         ▼                                                  │
│    More Questions?                                         │
│    ┌───Yes───┐                                             │
│    │         ▼                                             │
│    │   (loop back)                                         │
│    │                                                       │
│    No                                                      │
│    │                                                       │
│    ▼                                                       │
│  ┌──────────────┐                                          │
│  │  Generate    │                                          │
│  │  Report      │                                          │
│  └──────┬───────┘                                          │
│         │                                                  │
│         ▼                                                  │
│  ┌──────────────┐                                          │
│  │  Request     │                                          │
│  │  Human       │                                          │
│  │  Approval    │                                          │
│  └──────────────┘                                          │
└────────────────────────────────────────────────────────────┘
```

---

## File Structure

```
reviewbot/
├── main.py                          # FastAPI application entry point
├── requirements.txt                 # Python dependencies
├── setup.py                         # One-time setup script
├── .env.example                     # Environment configuration template
├── .gitignore                       # Git exclusions
├── pytest.ini                       # Pytest configuration
│
├── docs/                            # Documentation (NEW)
│   ├── README.md                    # Documentation index
│   ├── internal/                    # For developers
│   │   ├── architecture/
│   │   ├── development/
│   │   ├── deployment/
│   │   ├── api/
│   │   ├── services/
│   │   ├── database/
│   │   └── agent/
│   ├── external/                    # For end users
│   │   ├── workflows/
│   │   ├── features/
│   │   └── getting-started.md
│   └── api/                         # API documentation
│
├── app/
│   ├── __init__.py
│   ├── agents/                      # AI Agent (LangGraph)
│   │   ├── __init__.py
│   │   ├── review_agent.py          # Main agent workflow
│   │   └── states.py                # State definitions
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/                  # REST API endpoints
│   │       ├── auth.py
│   │       ├── projects.py
│   │       ├── checklists.py
│   │       ├── reviews.py
│   │       └── reports.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py                # Settings management
│   ├── db/
│   │   ├── __init__.py
│   │   └── session.py               # Database session
│   ├── services/                    # Business logic
│   │   ├── __init__.py
│   │   ├── checklist_parser.py
│   │   ├── checklist_optimizer.py
│   │   ├── report_generator.py
│   │   └── voice_interface.py
│   └── models.py                    # SQLAlchemy ORM models
│
├── tests/
│   ├── __init__.py
│   └── test_agent.py                # Test suite
│
├── .qwen/                           # Qwen AI agent config
│   ├── config.md
│   └── skills/
│
├── .claude/                         # Claude AI agent config
│   ├── config.md
│   └── skills/
│
├── .agent/                          # Generic AI agent config
│   ├── README.md
│   ├── agent/
│   ├── api/
│   ├── architecture/
│   ├── deployment/
│   └── skills/
│
├── uploads/                         # File uploads (runtime)
│   └── voice/                       # Voice recordings
│
├── reports/                         # Generated reports (runtime)
│   ├── *.md                         # Markdown reports
│   └── *.pdf                        # PDF reports
│
└── chroma_db/                       # Vector database (runtime)
```

---

## Technology Stack

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| **Python** | 3.10+ | Runtime |
| **FastAPI** | 0.109+ | Web framework |
| **Uvicorn** | 0.27+ | ASGI server |
| **SQLAlchemy** | 2.0+ | ORM |
| **Pydantic** | 2.0+ | Data validation |
| **GCP Cloud Run** | Prod | Application Hosting |

### AI/ML

| Technology | Version | Purpose |
|------------|---------|---------|
| **LangChain** | 0.1+ | LLM orchestration |
| **LangGraph** | 0.0.1+ | Stateful workflows |
| **OpenAI** | 1.0+ | LLM and voice |
| **ChromaDB** | 0.4+ | Vector store |

### Data & Storage

| Technology | Version | Purpose |
|------------|---------|---------|
| **SQLite** | 3.0+ | Development database |
| **PostgreSQL** | 15+ | Production database |
| **Asyncpg** | 0.29+ | Async PostgreSQL driver |
| **Pandas** | 2.0+ | Data processing |
| **OpenPyXL** | 3.1+ | Excel parsing |

### Authentication & Security

| Technology | Version | Purpose |
|------------|---------|---------|
| **Passlib** | 0.17+ | Password hashing |
| **Python-Jose** | 3.3+ | JWT handling |
| **Bcrypt** | 4.0+ | Password encryption |

### Reporting & File Handling

| Technology | Version | Purpose |
|------------|---------|---------|
| **ReportLab** | 4.0+ | PDF generation |
| **Python-Multipart** | 0.0.6+ | File uploads |

### Testing

| Technology | Version | Purpose |
|------------|---------|---------|
| **Pytest** | 8.0+ | Test framework |
| **Pytest-asyncio** | 0.23+ | Async test support |
| **Pytest-cov** | 4.1+ | Coverage reporting |
| **HTTPX** | 0.26+ | Async HTTP client |

---

## Design Principles

### 1. Separation of Concerns

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  API Layer  │────▶│  Services   │────▶│   Models    │
│  (Routes)   │     │  (Logic)    │     │  (ORM)      │
└─────────────┘     └─────────────┘     └─────────────┘
```

- **API Routes**: Handle HTTP requests/responses
- **Services**: Business logic and orchestration
- **Models**: Data structures and database mapping

### 2. Async-First

All I/O operations use async/await:

```python
async def get_project(db: AsyncSession, project_id: int) -> Project:
    result = await db.execute(select(Project).where(Project.id == project_id))
    return result.scalar_one_or_none()
```

### 3. Type Safety

Full type hints throughout the codebase:

```python
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, EmailStr

class ProjectCreate(BaseModel):
    name: str
    domain: str
    description: Optional[str] = None
    tech_stack: List[str] = []
```

### 4. Error Handling

Consistent error handling with HTTPException:

```python
from fastapi import HTTPException, status

if not project:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Project not found"
    )
```

### 5. Dependency Injection

FastAPI's dependency injection for reusable components:

```python
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

@router.get("/{project_id}")
async def get_project(
    db: AsyncSession = Depends(get_db),
    project_id: int = Path(...)
):
    ...
```

---

## Related Documents

- [Components](components.md) - Detailed component documentation
- [Data Flow](data-flow.md) - Data flow diagrams
- [Database Schema](../internal/database/schema.md) - Database structure
- [API Reference](../internal/api/reference.md) - Complete API docs

---

*Last updated: March 27, 2026*  
*AI Tech & Delivery Review Agent v1.0.0*
