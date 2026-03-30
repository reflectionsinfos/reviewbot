# ReviewBot Architecture

> AI-Powered Tech & Delivery Review Platform - System Architecture

**Version:** 2.1.0  
**Last Updated:** March 29, 2026  
**Status:** Stable / Production-Ready  

---

## 🏗️ High-Level System Architecture

ReviewBot follows a modern, asynchronous-first, micro-service-ready architecture centered around a **Strategy-Based Autonomous Review Engine** and a **LangGraph-driven Conversational Agent**.

```mermaid
graph TD
    subgraph Client Layer
        VSCode[VS Code Extension]
        WebUI[Autonomous Review UI / Swagger]
    end

    subgraph API Layer (FastAPI)
        Router[Strategy Router]
        Agent[Review Agent - LangGraph]
        Auth[JWT Auth Service]
    end

    subgraph Service Layer
        Orchestrator[Review Job Orchestrator]
        Analyzers[Autonomous Analyzers - file, pattern, llm, metadata]
        ReportGen[Report Generator - MD/PDF]
        Voice[Voice Interface - STT/TTS]
    end

    subgraph Data & AI Layer
        ChromaDB[(ChromaDB - Vector Store)]
        PostgreSQL[(GCP Cloud SQL - PostgreSQL)]
        LLM[LLM Provider - OpenAI/Anthropic/Groq]
    end

    VSCode --> Router
    WebUI --> Router
    Router --> Orchestrator
    Orchestrator --> Analyzers
    Analyzers --> LLM
    Agent --> LLM
    Analyzers --> PostgreSQL
    Analyzers --> ChromaDB
```

---

## 🔬 Core Components

### 1. Autonomous Review Engine
This module performs zero-human-input reviews by scanning repositories.

- **Connectors**: Abstracts file system access (e.g., `LocalFolderConnector` for volume mounts).
- **Orchestrator**: Manages background jobs via Python `asyncio`.
- **Strategy Router**: Dynamically assigns checklist items to specialized **Analyzers**:
    - **LLM Analyzer (34%)**: Context-rich architectural/code quality evaluation.
    - **File Presence (13%)**: Verifies critical project structure.
    - **Pattern Scan (7%)**: Highly optimized regex for security/performance markers.
    - **Metadata Check (3%)**: Deep inspection of dependency/CI configs.
    - **Human Required (43%)**: Marks non-scannable items (e.g., "team morale").

### 2. Conversational Review Agent (LangGraph)
Uses LangGraph to orchestrate multi-turn conversations for human Q&A reviews.

- **Nodes**: `ask_question`, `assess_rag`, `generate_report`.
- **Edges**: Conditional logic based on user input or state (e.g., skip, probe deeper).

### 3. Data Persistence Layer
- **PostgreSQL 15 (Async)**: Core relational data (Users, Projects, ChecklistItems, Jobs, Reports). Fixed for production with automated primary key sequence repair.
- **ChromaDB**: Lightweight vector storage for semantic search of checklist knowledge.

---

## 🚀 Deployment Architecture (GCP)

ReviewBot is fully productionized on Google Cloud Platform:

- **Compute**: **Cloud Run** (Serverless) — Provides automatic scaling, SSL termination, and secure HTTP endpoints.
- **Database**: **Cloud SQL** (Managed PostgreSQL) — High availability with encrypted storage.
- **Networking**: Cloud SQL Proxy for secure connection handling via Unix Domain Sockets.
- **Security**: Environment-specific configuration naming (`env.non-prod.gcp`) with secret injection.

---

## 📜 Key Architectural Decisions (ADR Summary)

| ADR | Decision | Rationale |
|-----|----------|-----------|
| **ADR-001** | **FastAPI Async** | High performance, non-blocking I/O for LLM streaming and job orchestration. |
| **ADR-002** | **LangGraph** | Enables complex, non-linear review workflows with persistent state management. |
| **ADR-003** | **Strategy Routing** | Decouples checklist questions from the underlying scanning mechanism. |
| **ADR-004** | **Asyncpg (SQLAlchemy)** | Required for high-concurrency database interactions in an async-first server. |
| **ADR-005** | **Self-Healing DB** | Prevents sequence-integrity-related startup failures in new Cloud SQL environments. |

---

## 🛠️ Data Flow: Single Review Cycle

1. **Initiation**: Client triggers job via `POST /api/autonomous-reviews/`.
2. **Indexing**: Connector builds an in-memory index of the project (skipping irrelevant paths).
3. **Execution**: Orchestrator fans out tasks. Strategy Router determines the best analyzer per item.
4. **Analysis**: Analyzers execute synchronously/asynchronously and stream RAG results to PostgreSQL and WebSocket.
5. **Report**: Upon completion, the Report Generator synthesizes findings, calculates compliance metrics, and persists the final report.
6. **Delivery**: Report is approved via the `ReportApproval` workflow and available for download.
