# System Design Specification

> AI Tech & Delivery Review Agent - Technical Design Document

**Version:** 1.0.0  
**Last Updated:** March 27, 2026  
**Status:** Approved  
**Owner:** Architecture Team

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Decisions](#architecture-decisions)
3. [Component Design](#component-design)
4. [Data Design](#data-design)
5. [API Design](#api-design)
6. [AI Agent Design](#ai-agent-design)
7. [Security Design](#security-design)
8. [Deployment Design](#deployment-design)
9. [Design Patterns](#design-patterns)

---

## System Overview

### Context Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         External Systems                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Users   │  │  OpenAI  │  │  Jira    │  │  Email   │       │
│  │ (Web/Mob)│  │   API    │  │ (Future) │  │  (Future)│       │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘       │
└───────┼─────────────┼─────────────┼─────────────┼──────────────┘
        │             │             │             │
        │ HTTPS       │ HTTPS       │ API         │ SMTP
        │             │             │             │
        ▼             ▼             ▼             ▼
┌─────────────────────────────────────────────────────────────────┐
│                  AI Tech & Delivery Review Agent                │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │                    API Gateway (FastAPI)                  │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │ │
│  │  │  Auth    │ │ Projects │ │ Reviews  │ │ Reports  │    │ │
│  │  │  Routes  │ │  Routes  │ │  Routes  │ │  Routes  │    │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │ │
│  └─────────────────────────┬─────────────────────────────────┘ │
│                            │                                   │
│  ┌─────────────────────────▼─────────────────────────────────┐ │
│  │                   Business Logic Layer                    │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │ │
│  │  │ Review Agent │ │  Checklist   │ │   Report     │      │ │
│  │  │ (LangGraph)  │ │  Optimizer   │ │  Generator   │      │ │
│  │  └──────────────┘ └──────────────┘ └──────────────┘      │ │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐      │ │
│  │  │   Checklist  │ │    Voice     │ │   Domain     │      │ │
│  │  │    Parser    │ │  Interface   │ │ Intelligence │      │ │
│  │  └──────────────┘ └──────────────┘ └──────────────┘      │ │
│  └─────────────────────────┬─────────────────────────────────┘ │
│                            │                                   │
│  ┌─────────────────────────▼─────────────────────────────────┐ │
│  │                    Data Access Layer                      │ │
│  │  ┌──────────────────────────────────────────────────────┐│ │
│  │  │           SQLAlchemy ORM (Async) + Repositories      ││ │
│  │  └──────────────────────────────────────────────────────┘│ │
│  └─────────────────────────┬─────────────────────────────────┘ │
│                            │                                   │
│  ┌─────────────────────────▼─────────────────────────────────┐ │
│  │                     Storage Layer                         │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐    │ │
│  │  │PostgreSQL│ │ ChromaDB │ │   File   │ │   Logs   │    │ │
│  │  │ (SQLite) │ │ (Vector) │ │  System  │ │  (ELK)   │    │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘    │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Architecture Decisions

### ADR-001: FastAPI for Backend Framework

**Status:** Accepted  
**Date:** 2026-01-15

**Context:**
- Need modern, high-performance Python web framework
- Async support required for I/O operations
- Automatic API documentation desired
- Type safety important for maintainability

**Decision:** Use FastAPI

**Rationale:**
- Native async/await support
- Automatic OpenAPI documentation
- Pydantic integration for validation
- High performance (on par with Node.js/Go)
- Growing ecosystem and community

**Consequences:**
- ✅ Fast development with auto-docs
- ✅ Type-safe endpoints
- ✅ Easy to learn for Python developers
- ⚠️ Smaller ecosystem than Django/Flask
- ⚠️ Breaking changes in early versions

---

### ADR-002: LangGraph for AI Workflow Orchestration

**Status:** Accepted  
**Date:** 2026-01-20

**Context:**
- Review process is stateful (multi-turn conversation)
- Need conditional branching based on responses
- Want to visualize workflow
- May add more AI agents in future

**Decision:** Use LangGraph (LangChain extension)

**Rationale:**
- Built for stateful, multi-turn workflows
- Visual graph representation
- Integrates with LangChain ecosystem
- Supports conditional edges and loops
- Easy to add new nodes/agents

**Consequences:**
- ✅ Clear workflow visualization
- ✅ Easy to modify review flow
- ✅ State management built-in
- ⚠️ Learning curve for team
- ⚠️ Additional dependency

---

### ADR-003: PostgreSQL for Production Database

**Status:** Accepted  
**Date:** 2026-01-15

**Context:**
- Need reliable, ACID-compliant database
- Complex queries for analytics
- JSON support for flexible fields
- SQLite for development simplicity

**Decision:** PostgreSQL (production), SQLite (development)

**Rationale:**
- PostgreSQL: Enterprise-grade, JSONB support, advanced queries
- SQLite: Zero-config, perfect for development/testing
- SQLAlchemy abstraction allows easy switching

**Consequences:**
- ✅ Production reliability
- ✅ Development simplicity
- ✅ Rich query capabilities
- ⚠️ Need to manage two database types
- ⚠️ Migration complexity

---

### ADR-004: ChromaDB for Vector Storage

**Status:** Accepted  
**Date:** 2026-02-01

**Context:**
- Need to store checklist embeddings
- Domain knowledge base for AI
- Semantic search capabilities
- Simple integration preferred

**Decision:** Use ChromaDB

**Rationale:**
- Lightweight, easy to setup
- Built-in persistence
- Good Python integration
- No external dependencies
- Scales to millions of vectors

**Consequences:**
- ✅ Simple setup and maintenance
- ✅ Good performance for our scale
- ✅ No external service dependency
- ⚠️ Less mature than Pinecone/Weaviate
- ⚠️ Limited distributed deployment options

---

### ADR-005: Async-First Architecture

**Status:** Accepted  
**Date:** 2026-01-15

**Context:**
- I/O-bound operations (API calls, DB queries)
- Voice processing is async
- Need to handle concurrent requests
- Performance important for UX

**Decision:** Async/await throughout the codebase

**Rationale:**
- Better resource utilization
- Handles concurrent requests efficiently
- Natural fit for I/O operations
- Modern Python best practice

**Consequences:**
- ✅ Better performance under load
- ✅ Efficient I/O handling
- ✅ Modern, clean code
- ⚠️ More complex error handling
- ⚠️ Need async-aware libraries

---

## Component Design

### Component: ReviewAgent

**Responsibility:** Orchestrate review workflow using LangGraph

```
┌─────────────────────────────────────────────────────────┐
│                    ReviewAgent                          │
├─────────────────────────────────────────────────────────┤
│ - llm: ChatOpenAI                                       │
│ - graph: StateGraph                                     │
│ - app: CompiledGraph                                    │
├─────────────────────────────────────────────────────────┤
│ + __init__()                                            │
│ + _build_graph() -> StateGraph                          │
│ + initialize(project_id, checklist_id) -> ReviewState   │
│ + ask_question(state) -> ReviewState                    │
│ + process_response(state) -> ReviewState                │
│ + assess_rag(state) -> ReviewState                      │
│ + generate_report(state) -> ReviewState                 │
│ + run(review_id, user_input) -> Response                │
└─────────────────────────────────────────────────────────┘
```

**Dependencies:**
- LangGraph (workflow orchestration)
- LangChain (LLM abstraction)
- OpenAI (LLM provider)

**Interfaces:**
- Input: User responses (text/voice)
- Output: Next question, RAG status, report data

---

### Component: ChecklistParser

**Responsibility:** Parse Excel checklist files into structured data

```
┌─────────────────────────────────────────────────────────┐
│                  ChecklistParser                        │
├─────────────────────────────────────────────────────────┤
│ - file_path: Path                                       │
│ - workbook: Workbook                                    │
├─────────────────────────────────────────────────────────┤
│ + __init__(file_path)                                   │
│ + parse_delivery_checklist() -> List[Dict]              │
│ + parse_technical_checklist() -> List[Dict]             │
│ + extract_item_code() -> str                            │
│ + determine_area() -> str                               │
│ + save_to_database(project_id) -> List[Checklist]       │
└─────────────────────────────────────────────────────────┘
```

**Dependencies:**
- OpenPyXL (Excel parsing)
- Pandas (data transformation)

**Interfaces:**
- Input: Excel file path
- Output: List of checklist items

---

### Component: ReportGenerator

**Responsibility:** Generate Markdown and PDF reports

```
┌─────────────────────────────────────────────────────────┐
│                  ReportGenerator                        │
├─────────────────────────────────────────────────────────┤
│ - reports_dir: Path                                     │
│ - template_env: Environment                             │
├─────────────────────────────────────────────────────────┤
│ + __init__()                                            │
│ + generate_markdown(report_data) -> str                 │
│ + generate_pdf(report_data) -> str                      │
│ + calculate_compliance_score() -> float                 │
│ + analyze_gaps(responses) -> List[Gap]                  │
│ + generate_action_items(gaps) -> List[ActionItem]       │
└─────────────────────────────────────────────────────────┘
```

**Dependencies:**
- ReportLab (PDF generation)
- Jinja2 (template engine)

**Interfaces:**
- Input: Review responses, project data
- Output: Markdown/PDF file paths

---

### Component: VoiceInterface

**Responsibility:** Handle speech-to-text and text-to-speech

```
┌─────────────────────────────────────────────────────────┐
│                   VoiceInterface                        │
├─────────────────────────────────────────────────────────┤
│ - openai_client: OpenAI                                 │
│ - elevenlabs_client: Optional[ElevenLabs]               │
├─────────────────────────────────────────────────────────┤
│ + __init__()                                            │
│ + speech_to_text(audio_path) -> str                     │
│ + text_to_speech(text, output_path) -> bool             │
│ + process_voice_input(audio_path) -> Dict               │
│ + detect_intent(transcript) -> str                      │
└─────────────────────────────────────────────────────────┘
```

**Dependencies:**
- OpenAI (Whisper STT, TTS)
- ElevenLabs (optional, advanced TTS)

**Interfaces:**
- Input: Audio file path, text
- Output: Transcript, audio file

---

## Data Design

### Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐
│    User     │       │   Project   │
├─────────────┤       ├─────────────┤
│ id (PK)     │       │ id (PK)     │
│ email       │◄──────│ owner_id(FK)│
│ full_name   │       │ name        │
│ hashed_pw   │       │ domain      │
│ role        │       │ description │
│ created_at  │       │ status      │
└─────────────┘       └──────┬──────┘
                             │
                             │ 1:M
                             ▼
                      ┌─────────────┐
                      │  Checklist  │
                      ├─────────────┤
                      │ id (PK)     │
                      │ project_id  │
                      │ type        │
                      │ version     │
                      └──────┬──────┘
                             │
                             │ 1:M
                             ▼
                      ┌─────────────┐
                      │ Checklist   │
                      │    Item     │
                      ├─────────────┤
                      │ id (PK)     │
                      │ question    │
                      │ area        │
                      │ weight      │
                      └─────────────┘

┌─────────────┐       ┌─────────────┐
│    Review   │       │   Report    │
├─────────────┤       ├─────────────┤
│ id (PK)     │       │ id (PK)     │
│ project_id  │       │ review_id   │
│ checklist_id│       │ score       │
│ status      │──────►│ rag_status  │
│ voice_enabled│      │ approval    │
└──────┬──────┘       └──────┬──────┘
       │                     │
       │ 1:M                 │ 1:1
       ▼                     ▼
┌─────────────┐       ┌─────────────┐
│   Review    │       │   Report    │
│  Response   │       │  Approval   │
├─────────────┤       ├─────────────┤
│ id (PK)     │       │ id (PK)     │
│ answer      │       │ approver_id │
│ rag_status  │       │ status      │
│ comments    │       │ comments    │
└─────────────┘       └─────────────┘
```

### Schema Evolution Strategy

**Version:** Current = v1

**Migration Approach:**
- Alembic for schema migrations
- Forward-only migrations (no downgrades in prod)
- Test migrations on staging first
- Backup before production migration

**Future Schema Changes:**
```
v2 (Planned):
- Add trend_analytics table
- Add project_benchmarks table
- Add notification_preferences table
- Add audit_logs table

v3 (Planned):
- Multi-tenant support (organization_id)
- Custom fields for projects
- Webhook integrations
```

---

## API Design

### RESTful Endpoints

```yaml
openapi: 3.0.3
info:
  title: AI Tech & Delivery Review Agent API
  version: 1.0.0

paths:
  /api/auth/register:
    post:
      summary: Register new user
      tags: [Authentication]
      requestBody:
        content:
          application/x-www-form-urlencoded:
            schema:
              type: object
              properties:
                email: { type: string, format: email }
                password: { type: string, minLength: 8 }
                full_name: { type: string }
                role: { type: string, enum: [reviewer, manager, admin] }
      responses:
        200:
          description: User created successfully

  /api/auth/login:
    post:
      summary: Login and get JWT token
      tags: [Authentication]
      requestBody:
        content:
          application/x-www-form-urlencoded:
            schema:
              type: object
              properties:
                username: { type: string, format: email }
                password: { type: string }
      responses:
        200:
          description: Login successful
          content:
            application/json:
              schema:
                type: object
                properties:
                  access_token: { type: string }
                  token_type: { type: string, enum: [bearer] }
                  user: { $ref: '#/components/schemas/User' }

  /api/projects:
    get:
      summary: List all projects
      tags: [Projects]
      security:
        - bearerAuth: []
      parameters:
        - name: skip
          in: query
          schema: { type: integer, default: 0 }
        - name: limit
          in: query
          schema: { type: integer, default: 100 }
        - name: status
          in: query
          schema: { type: string, enum: [active, completed, on_hold] }
      responses:
        200:
          description: List of projects

    post:
      summary: Create new project
      tags: [Projects]
      security:
        - bearerAuth: []
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                name: { type: string }
                domain: { type: string }
                description: { type: string }
                tech_stack: { type: array, items: { type: string } }
                stakeholders: { type: object }
      responses:
        200:
          description: Project created

  /api/projects/{project_id}/upload-checklist:
    post:
      summary: Upload Excel checklist
      tags: [Projects]
      security:
        - bearerAuth: []
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                file: { type: string, format: binary }
      responses:
        200:
          description: Checklist uploaded and parsed

  /api/reviews:
    post:
      summary: Create review session
      tags: [Reviews]
      security:
        - bearerAuth: []
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                project_id: { type: integer }
                checklist_id: { type: integer }
                title: { type: string }
                voice_enabled: { type: boolean, default: true }
                participants: { type: array, items: { type: string } }
      responses:
        200:
          description: Review created

  /api/reviews/{review_id}/start:
    post:
      summary: Start AI review agent
      tags: [Reviews]
      security:
        - bearerAuth: []
      responses:
        200:
          description: Review started
          content:
            application/json:
              schema:
                type: object
                properties:
                  message: { type: string }
                  first_question: { type: string }
                  checklist_items_count: { type: integer }

  /api/reviews/{review_id}/respond:
    post:
      summary: Submit text response
      tags: [Reviews]
      security:
        - bearerAuth: []
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                question_index: { type: integer }
                answer: { type: string }
                comments: { type: string }
      responses:
        200:
          description: Response recorded
          content:
            application/json:
              schema:
                type: object
                properties:
                  message: { type: string }
                  rag_status: { type: string, enum: [green, amber, red, na] }
                  next_question: { type: object }
                  progress: { type: string }

  /api/reviews/{review_id}/voice-response:
    post:
      summary: Submit voice response
      tags: [Reviews]
      security:
        - bearerAuth: []
      requestBody:
        content:
          multipart/form-data:
            schema:
              type: object
              properties:
                file: { type: string, format: binary }
      responses:
        200:
          description: Voice response processed
          content:
            application/json:
              schema:
                type: object
                properties:
                  transcript: { type: string }
                  intent: { type: string }
                  answer: { type: string }

  /api/reports/pending/approvals:
    get:
      summary: Get pending report approvals
      tags: [Reports]
      security:
        - bearerAuth: []
      responses:
        200:
          description: List of pending approvals

  /api/reports/{report_id}/approve:
    post:
      summary: Approve report
      tags: [Reports]
      security:
        - bearerAuth: []
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                approver_id: { type: integer }
                comments: { type: string }
      responses:
        200:
          description: Report approved

  /api/reports/{report_id}/download/{format}:
    get:
      summary: Download report
      tags: [Reports]
      security:
        - bearerAuth: []
      parameters:
        - name: format
          in: path
          schema: { type: string, enum: [markdown, pdf] }
      responses:
        200:
          description: Report file
```

---

## Two-Track Action Item System Design

### Overview

After an autonomous review completes, the system produces an **Action Plan** from existing review data. No new DB columns are required for the MVP — all data is assembled from `AutonomousReviewResult`, `ChecklistItem`, and `Project` records already on disk.

### Data Flow

```
AutonomousReviewJob
  └─ results[]  (AutonomousReviewResult per checklist item)
       ├─ rag_status        → determines if item appears in action plan
       ├─ evidence          → "What was found / what is missing"
       ├─ files_checked     → "Which files to touch" injected into prompt
       └─ checklist_item_id ─→ ChecklistItem
                                 ├─ expected_evidence  → "What the standard expects"
                                 ├─ area               → used for grouping
                                 └─ question           → action card title

Project.tech_stack  → injected into prompt for framework-aware fix instructions
```

### Track 2 — Structured Action Cards (Team/Manager View)

Each red/amber `AutonomousReviewResult` is transformed into an **Action Card**:

```
ActionCard {
  item_code:        string          # e.g. "3.2"
  area:             string          # e.g. "Security"
  question:         string          # checklist question text
  priority:         "High"|"Medium" # red → High, amber → Medium
  rag_status:       string
  what_was_found:   string          # AutonomousReviewResult.evidence
  what_to_fix:      string          # derived from expected_evidence + evidence gap
  expected_outcome: string          # ChecklistItem.expected_evidence
  assigned_to:      string          # "TBD" default, user-editable
  due_date:         string          # "TBD" default, user-editable
  ai_prompt:        AIPrompt        # Track 1 payload for this card
}
```

Cards are grouped in this order:
1. **Critical Blockers** (red, High priority)
2. **Advisories** (amber, Medium priority)
3. **Needs Human Sign-off** (`needs_human_sign_off = true`)
4. **Already Compliant** (green, summarised — gives team confidence)

### Track 1 — AI IDE Prompts (Developer View)

Each Action Card has an associated `AIPrompt` object:

```
AIPrompt {
  generic:      string    # Default — plain instruction, usable in any AI IDE
  cursor:       string    # Prefixed with @workspace context hint for Cursor/Copilot Chat
  claude_code:  string    # Task-description style for Claude Code CLI
}
```

**Prompt template structure (template-generated, no LLM cost):**

```
[CONTEXT]
Project: {project.name} | Tech stack: {project.tech_stack}
File(s) examined: {result.files_checked}

[FINDING]
{result.evidence}

[STANDARD EXPECTED]
{checklist_item.expected_evidence}

[TASK]
Fix the above gap. {framework-specific instruction derived from tech_stack}.
Ensure the solution satisfies: "{checklist_item.question}"

[ACCEPTANCE CRITERIA]
{checklist_item.expected_evidence}
```

**Optional LLM enrichment** (on-demand, not default):
- Triggered by `POST /api/autonomous-reviews/{job_id}/action-plan/enhance`
- Uses the same configured LLM provider as the review agent
- Enriched prompts are cached on the job record (stored in `agent_metadata` JSON) to avoid re-charging on re-fetch

### New API Endpoint

```
GET /api/autonomous-reviews/{job_id}/action-plan

Response:
{
  "job_id": int,
  "project": string,
  "checklist": string,
  "generated_at": datetime,
  "summary": {
    "total_items": int,
    "critical_blockers": int,
    "advisories": int,
    "sign_off_required": int,
    "compliant": int
  },
  "critical_blockers": [ActionCard],
  "advisories":        [ActionCard],
  "sign_off_required": [ActionCard],
  "compliant_summary": [{ area, item_code, question }]
}

POST /api/autonomous-reviews/{job_id}/action-plan/enhance
  → triggers LLM enrichment of all Track 1 prompts for this job
  → returns 202 Accepted while enrichment runs in background
```

### UI — Action Plan Tab in History Details

The existing `history.html` details view gains a third tab alongside the item grid:

```
[Item Grid]  [Action Plan]  [Summary Stats]   ← tab row

Action Plan tab layout:
┌─────────────────────────────────────────────────────┐
│  IDE Flavour: [Generic ▾]  [Export MD]  [Enhance AI] │
├─────────────────────────────────────────────────────┤
│  🔴 Critical Blockers (N)                            │
│  ┌───────────────────────────────────────────┐       │
│  │ 3.2 · Security · HIGH                     │       │
│  │ No JWT expiry validation found            │       │
│  │ Evidence: auth.py checked — no exp check  │       │
│  │ Fix: Add token expiry validation          │       │
│  │ [▶ Show AI Prompt]  [📋 Copy Prompt]       │       │
│  └───────────────────────────────────────────┘       │
│  ...                                                 │
│  🟡 Advisories (N)                                   │
│  ✅ Already Compliant (N items)  [expand]            │
└─────────────────────────────────────────────────────┘
```

### Service Layer

New file: `app/services/action_plan_generator.py`

```python
class ActionPlanGenerator:
    def generate(job: AutonomousReviewJob, results: list[AutonomousReviewResult],
                 checklist_items: dict[int, ChecklistItem],
                 project: Project) -> ActionPlanResponse

    def _build_prompt(result, item, project, flavour="generic") -> str

    async def enhance_with_llm(job_id, results, items, project) -> None
        # Stores enriched prompts in job.agent_metadata["action_plan_prompts"]
```

---

## AI Agent Design

### Review Agent Workflow

```
┌────────────────────────────────────────────────────────────┐
│                    Review Agent Graph                      │
│                                                            │
│  ┌──────────────┐                                         │
│  │   START     │                                         │
│  └──────┬──────┘                                         │
│         │                                                  │
│         ▼                                                  │
│  ┌──────────────┐                                         │
│  │  initialize  │                                         │
│  │  - Load project context                                │
│  │  - Load checklist                                      │
│  │  - Create review session                               │
│  └──────┬───────┘                                         │
│         │                                                  │
│         ▼                                                  │
│  ┌──────────────┐     Yes     ┌──────────────────┐       │
│  │  Optimize    │────────────▶│  checklist_      │       │
│  │  Checklist?  │             │  optimization    │       │
│  └──────┬───────┘             └────────┬─────────┘       │
│         │ No                           │                  │
│         │                              │                  │
│         └──────────────┬───────────────┘                  │
│                        │                                   │
│                        ▼                                   │
│               ┌────────────────┐                          │
│               │  ask_question  │                          │
│               │  - Present Q   │                          │
│               │  - Wait for A  │                          │
│               └───────┬────────┘                          │
│                       │                                    │
│                       ▼                                    │
│               ┌────────────────┐                          │
│               │ process_response│                         │
│               │ - Parse answer  │                          │
│               │ - Extract intent│                          │
│               └───────┬────────┘                          │
│                       │                                    │
│                       ▼                                    │
│               ┌────────────────┐                          │
│               │   assess_rag   │                          │
│               │ - Rule-based   │                          │
│               │ - Or LLM-based │                          │
│               └───────┬────────┘                          │
│                       │                                    │
│                       ▼                                    │
│               ┌────────────────┐                          │
│               │ More items?    │                          │
│               └───────┬────────┘                          │
│                  ┌────┴────┐                              │
│                  │         │                              │
│               Yes│         │No                            │
│                  │         │                              │
│                  │         ▼                              │
│                  │  ┌────────────────┐                   │
│                  │  │ generate_report│                   │
│                  │  │ - Calculate    │                   │
│                  │  │ - Analyze gaps │                   │
│                  │  │ - Recommendations│                 │
│                  │  └───────┬────────┘                   │
│                  │          │                             │
│                  │          ▼                             │
│                  │  ┌────────────────┐                   │
│                  │  │request_approval│                   │
│                  │  └───────┬────────┘                   │
│                  │          │                             │
│                  │          ▼                             │
│                  │  ┌────────────────┐                   │
│                  └─▶│     END        │                   │
│                     └────────────────┘                   │
└────────────────────────────────────────────────────────────┘
```

### State Transitions

```python
# State transitions in LangGraph
workflow = StateGraph(ReviewState)

# Add nodes
workflow.add_node("initialize", initialize_review)
workflow.add_node("ask_question", ask_question)
workflow.add_node("process_response", process_response)
workflow.add_node("assess_rag", assess_rag_status)
workflow.add_node("generate_report", generate_report)
workflow.add_node("request_approval", request_approval)

# Add edges
workflow.set_entry_point("initialize")
workflow.add_edge("initialize", "ask_question")
workflow.add_edge("ask_question", "process_response")
workflow.add_edge("process_response", "assess_rag")

# Conditional edge
workflow.add_conditional_edges(
    "assess_rag",
    should_continue,
    {
        "continue": "ask_question",
        "end": "generate_report"
    }
)

workflow.add_edge("generate_report", "request_approval")
workflow.add_edge("request_approval", END)

app = workflow.compile()
```

---

## Security Design

### Authentication Flow

```
┌──────────┐      ┌──────────┐      ┌──────────┐
│  Client  │      │   API    │      │   DB     │
└────┬─────┘      └────┬─────┘      └────┬─────┘
     │                 │                 │
     │  POST /login    │                 │
     │  (credentials)  │                 │
     │────────────────▶│                 │
     │                 │                 │
     │                 │  Verify user    │
     │                 │────────────────▶│
     │                 │                 │
     │                 │  User data      │
     │                 │◀────────────────│
     │                 │                 │
     │                 │  Generate JWT   │
     │                 │                 │
     │  JWT token      │                 │
     │◀────────────────│                 │
     │                 │                 │
     │  Request + JWT  │                 │
     │────────────────▶│                 │
     │                 │                 │
     │                 │  Validate JWT   │
     │                 │                 │
     │                 │  Process request│
     │                 │                 │
     │  Response       │                 │
     │◀────────────────│                 │
     │                 │                 │
```

### Authorization Model

```
┌─────────────────────────────────────────────────────────┐
│                    RBAC Model                           │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Role        │ Permissions                              │
│  ────────────┼─────────────────────────────────────────│
│  reviewer    │ - Create/edit reviews                    │
│              │ - View own projects                      │
│              │ - Submit responses                       │
│                                                         │
│  manager     │ - All reviewer permissions               │
│              │ - Approve reports                        │
│              │ - View all projects in org               │
│              │ - Manage team members                    │
│                                                         │
│  admin       │ - All manager permissions                │
│              │ - System configuration                   │
│              │ - User management                        │
│              │ - Audit logs access                      │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Security Controls

| Control | Implementation | Status |
|---------|----------------|--------|
| **Authentication** | JWT with expiration | ✅ Done |
| **Authorization** | Role-based access control | ✅ Done |
| **Password Hashing** | Bcrypt (cost=12) | ✅ Done |
| **Input Validation** | Pydantic models | ✅ Done |
| **SQL Injection** | Parameterized queries | ✅ Done |
| **XSS Prevention** | HTML escaping | ✅ Done |
| **CORS** | Configurable origins | ✅ Done |
| **Rate Limiting** | SlowAPI (TODO) | ⏳ TODO |
| **Audit Logging** | Structured logs (TODO) | ⏳ TODO |
| **Secrets Management** | Environment variables | ✅ Done |

---

## Deployment Design

### Docker Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Docker Network                       │
│                                                         │
│  ┌─────────────┐     ┌─────────────┐                   │
│  │   Nginx     │────▶│    App      │                   │
│  │  (Reverse   │     │  (FastAPI)  │                   │
│  │   Proxy)    │     │  Gunicorn   │                   │
│  │  :80, :443  │     │  :8000      │                   │
│  └─────────────┘     └──────┬──────┘                   │
│                             │                           │
│                      ┌──────▼──────┐                   │
│                      │  PostgreSQL │                   │
│                      │    :5432    │                   │
│                      └─────────────┘                   │
│                                                         │
│  ┌─────────────┐     (Optional)                        │
│  │   pgAdmin   │                                       │
│  │    :5050    │                                       │
│  └─────────────┘                                       │
│                                                         │
│  Volume Mounts:                                         │
│  - ./data/postgres:/var/lib/postgresql/data             │
│  - ./chroma_db:/app/chroma_db                           │
│  - ./uploads:/app/uploads                               │
│  - ./reports:/app/reports                               │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Environment Configuration

```yaml
# Development
environment:
  - ENVIRONMENT=development
  - DEBUG=true
  - DATABASE_URL=sqlite+aiosqlite:///./reviews.db
  - LOG_LEVEL=DEBUG

# Production
environment:
  - ENVIRONMENT=production
  - DEBUG=false
  - DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/reviews_db
  - LOG_LEVEL=INFO
  - UVICORN_WORKERS=4
  - SECRET_KEY=${SECRET_KEY_FROM_VAULT}
```

---

## Design Patterns

### 1. Repository Pattern

```python
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

class ProjectRepository:
    """Repository for Project data access"""
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_by_id(self, project_id: int) -> Optional[Project]:
        """Get project by ID"""
        result = await self.session.execute(
            select(Project).where(Project.id == project_id)
        )
        return result.scalar_one_or_none()
    
    async def get_all(self, skip: int = 0, limit: int = 100) -> List[Project]:
        """Get all projects with pagination"""
        result = await self.session.execute(
            select(Project).offset(skip).limit(limit)
        )
        return result.scalars().all()
    
    async def create(self, project: Project) -> Project:
        """Create new project"""
        self.session.add(project)
        await self.session.commit()
        await self.session.refresh(project)
        return project
```

### 2. Factory Pattern

```python
from app.services.checklist_parser import ChecklistParser
from app.services.report_generator import ReportGenerator

class ServiceFactory:
    """Factory for creating service instances"""
    
    @staticmethod
    def get_checklist_parser(file_path: str) -> ChecklistParser:
        """Get checklist parser instance"""
        return ChecklistParser(file_path)
    
    @staticmethod
    def get_report_generator() -> ReportGenerator:
        """Get report generator instance"""
        return ReportGenerator()
```

### 3. Strategy Pattern

```python
from typing import Protocol

class RAGAssessmentStrategy(Protocol):
    def assess(self, answer: str) -> str:
        """Assess RAG status from answer"""
        ...

class RuleBasedRAG:
    """Rule-based RAG assessment"""
    
    def assess(self, answer: str) -> str:
        answer_lower = answer.lower()
        if any(word in answer_lower for word in ["yes", "done"]):
            return "green"
        elif any(word in answer_lower for word in ["partial", "working"]):
            return "amber"
        elif any(word in answer_lower for word in ["no", "missing"]):
            return "red"
        return "na"

class LLMBasedRAG:
    """LLM-based RAG assessment"""
    
    def __init__(self, llm):
        self.llm = llm
    
    def assess(self, answer: str) -> str:
        # Use LLM for nuanced assessment
        prompt = f"Evaluate: {answer}"
        response = self.llm.invoke(prompt)
        return response.content

# Context
class RAGAssessor:
    def __init__(self, strategy: RAGAssessmentStrategy):
        self.strategy = strategy
    
    def assess(self, answer: str) -> str:
        return self.strategy.assess(answer)
```

### 4. Dependency Injection

```python
from fastapi import Depends

async def get_db() -> AsyncSession:
    """Dependency: Database session"""
    async with AsyncSessionLocal() as session:
        yield session

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Dependency: Current authenticated user"""
    # Decode JWT and get user
    ...

@router.get("/projects")
async def list_projects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    skip: int = 0,
    limit: int = 100
):
    """Endpoint with dependency injection"""
    ...
```

---

## Appendix

### A. References

- [PRD](requirements.md)
- [Test Strategy](test-strategy.md)
- [API Reference](internal/api/reference.md)

### B. Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-03-27 | Architecture Team | Initial release |

---

*Document Owner: Architecture Team*  
*Next Review: June 2026*  
*AI Tech & Delivery Review Agent v1.0.0*
