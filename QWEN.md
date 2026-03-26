# AI Tech & Delivery Review Agent - QWEN Complete Guide

> Comprehensive documentation for the AI-powered project review system

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Installation & Setup](#installation--setup)
4. [Configuration](#configuration)
5. [API Reference](#api-reference)
6. [Agent Workflow](#agent-workflow)
7. [Database Schema](#database-schema)
8. [Voice Integration](#voice-integration)
9. [Report Generation](#report-generation)
10. [Approval Workflow](#approval-workflow)
11. [Domain Intelligence](#domain-intelligence)
12. [Testing](#testing)
13. [Deployment](#deployment)
14. [Troubleshooting](#troubleshooting)
15. [Best Practices](#best-practices)

---

## Overview

### What is This?

The **AI Tech & Delivery Review Agent** is a conversational, voice-enabled AI system that conducts comprehensive technical and delivery project reviews. It acts as an expert team member who knows everything about your projects—from domain functionality and coding practices to testing, delivery, and stakeholder management.

### Core Capabilities

| Capability | Description |
|------------|-------------|
| 🎤 **Voice Interaction** | Conduct reviews using natural voice conversations (OpenAI Whisper + TTS) |
| 📋 **Checklist Management** | Parse Excel checklists, generate AI-powered recommendations |
| 🤖 **AI Orchestration** | LangGraph-based workflow for intelligent review flow |
| 📊 **Compliance Scoring** | Automatic RAG (Red/Amber/Green) status calculation |
| 📝 **Report Generation** | Markdown and PDF reports with actionable insights |
| 🔐 **Human Approval** | No report sent without human boss approval (mandatory) |
| 🧠 **Domain Awareness** | Adapts checklists based on project domain |

### Key Features

- ✅ Parses your existing Excel checklist files
- ✅ Conducts reviews via voice or text
- ✅ Automatically assesses compliance (RAG status)
- ✅ Generates comprehensive reports with gaps and recommendations
- ✅ **Requires human approval** before any report distribution
- ✅ Suggests domain-specific checklist enhancements
- ✅ Tracks review history and trend analysis
- ✅ Secure JWT-based authentication

---

## Architecture

### System Architecture

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
│  │  SQLite/    │  │  ChromaDB   │  │  File System            │ │
│  │  PostgreSQL │  │  (Vector)   │  │  (uploads, reports)     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Component Architecture

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
│         │ No             ▼                                 │
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

### File Structure

```
project-reviews/
├── main.py                          # FastAPI application entry point
├── requirements.txt                 # Python dependencies (30+)
├── setup.py                         # One-time setup script
├── .env.example                     # Environment configuration template
├── .gitignore                       # Git exclusions
├── pytest.ini                       # Pytest configuration
│
├── README.md                        # User-facing documentation
├── WORKFLOWS.md                     # Step-by-step usage workflows
├── QUICK_REFERENCE.md               # Quick lookup card
├── QWEN.md                          # This file - complete technical guide
│
├── app/
│   ├── __init__.py
│   │
│   ├── agents/                      # AI Agent (LangGraph)
│   │   ├── __init__.py
│   │   ├── review_agent.py          # Main agent workflow implementation
│   │   └── states.py                # State definitions for LangGraph
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   └── routes/                  # REST API endpoints
│   │       ├── auth.py              # JWT authentication
│   │       ├── projects.py          # Project CRUD + checklist upload
│   │       ├── checklists.py        # Checklist optimization
│   │       ├── reviews.py           # Review sessions + voice
│   │       └── reports.py           # Reports + approval workflow
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   └── config.py                # Settings management
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   └── session.py               # Database session management
│   │
│   ├── services/                    # Business logic
│   │   ├── __init__.py
│   │   ├── checklist_parser.py      # Excel file parsing
│   │   ├── checklist_optimizer.py   # AI-powered recommendations
│   │   ├── report_generator.py      # Markdown/PDF generation
│   │   └── voice_interface.py       # STT/TTS integration
│   │
│   └── models.py                    # SQLAlchemy ORM models (8 tables)
│
├── tests/
│   ├── __init__.py
│   └── test_agent.py                # Test suite (30+ tests)
│
├── uploads/                         # File uploads (created at runtime)
│   └── voice/                       # Voice recordings
│
├── reports/                         # Generated reports (created at runtime)
│   ├── *.md                         # Markdown reports
│   └── *.pdf                        # PDF reports
│
└── chroma_db/                       # Vector database (created at runtime)
```

---

## Installation & Setup

### Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.10+ | Runtime |
| pip | 22.0+ | Package manager |
| OpenAI API Key | - | LLM and voice features |
| (Optional) ElevenLabs API Key | - | Advanced TTS |

### Step-by-Step Installation

#### 1. Navigate to Project Directory

```bash
cd c:\projects\project-reviews
```

#### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

#### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies include:**
- FastAPI + Uvicorn (web framework)
- SQLAlchemy + Alembic (database)
- LangChain + LangGraph (AI orchestration)
- OpenAI (LLM and voice)
- ChromaDB (vector store)
- Pandas + OpenPyXL (Excel parsing)
- ReportLab (PDF generation)
- Passlib + Python-JOSE (authentication)

#### 4. Run Setup Script

```bash
python setup.py
```

This will:
- Create required directories (`uploads/`, `reports/`, `chroma_db/`)
- Initialize SQLite database
- Create demo admin user
- Generate `.env` file template

#### 5. Configure Environment

Edit `.env` file:

```bash
# Open in editor
notepad .env

# Or use VS Code
code .env
```

**Required configuration:**

```env
# OpenAI API Key (REQUIRED)
OPENAI_API_KEY=sk-your-actual-api-key-here

# Database (SQLite for development)
DATABASE_URL="sqlite+aiosqlite:///./reviews.db"

# Security (CHANGE IN PRODUCTION!)
SECRET_KEY=your-super-secret-key-change-this
ALGORITHM="HS256"
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Application Settings
APP_NAME="AI Tech & Delivery Review Agent"
DEBUG=true
VOICE_ENABLED=true
REQUIRE_HUMAN_APPROVAL=true

# Storage Paths
CHROMA_PERSIST_DIR="./chroma_db"
UPLOAD_DIR="./uploads"
REPORTS_DIR="./reports"
```

#### 6. Start the Server

```bash
# Development mode (auto-reload)
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

#### 7. Verify Installation

Open browser and navigate to:

- **Health Check**: http://localhost:8000/health
- **API Docs**: http://localhost:8000/docs
- **Root**: http://localhost:8000/

**Expected health response:**

```json
{
  "status": "healthy",
  "database": "connected",
  "voice_enabled": true,
  "human_approval_required": true
}
```

---

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `OPENAI_API_KEY` | OpenAI API key for LLM & voice | - | ✅ Yes |
| `ELEVENLABS_API_KEY` | ElevenLabs API key (optional TTS) | - | ❌ No |
| `DATABASE_URL` | Database connection string | `sqlite+aiosqlite:///./reviews.db` | ✅ Yes |
| `SECRET_KEY` | JWT signing key | `change-this-secret-key` | ✅ Yes |
| `ALGORITHM` | JWT algorithm | `HS256` | ❌ No |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token expiration | `30` | ❌ No |
| `APP_NAME` | Application name | `AI Tech & Delivery Review Agent` | ❌ No |
| `DEBUG` | Debug mode | `true` | ❌ No |
| `VOICE_ENABLED` | Enable voice features | `true` | ❌ No |
| `REQUIRE_HUMAN_APPROVAL` | Require approval before sending reports | `true` | ❌ No |
| `CHROMA_PERSIST_DIR` | Vector DB storage path | `./chroma_db` | ❌ No |
| `UPLOAD_DIR` | File uploads path | `./uploads` | ❌ No |
| `REPORTS_DIR` | Generated reports path | `./reports` | ❌ No |

### Security Configuration

**For Production:**

1. **Change SECRET_KEY:**
   ```bash
   # Generate secure random key
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Use PostgreSQL instead of SQLite:**
   ```env
   DATABASE_URL="postgresql+asyncpg://user:password@localhost:5432/reviews_db"
   ```

3. **Enable HTTPS:**
   - Use reverse proxy (nginx) with SSL certificate
   - Or use cloud platform with managed SSL

4. **Configure CORS:**
   ```python
   # In main.py
   app.add_middleware(
       CORSMiddleware,
       allow_origins=["https://your-domain.com"],  # Specific domain
       allow_credentials=True,
       allow_methods=["*"],
       allow_headers=["*"],
   )
   ```

---

## API Reference

### Authentication

#### Register User

```http
POST /api/auth/register
Content-Type: application/x-www-form-urlencoded

email=user@example.com&password=securepass123&full_name=John+Doe&role=reviewer
```

**Response:**
```json
{
  "message": "User created successfully",
  "user_id": 1,
  "email": "user@example.com"
}
```

#### Login

```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=securepass123
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "reviewer"
  }
}
```

#### Get Current User

```http
GET /api/auth/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

---

### Projects

#### List Projects

```http
GET /api/projects/?skip=0&limit=100&status=active
```

#### Get Project

```http
GET /api/projects/{project_id}
```

#### Create Project

```http
POST /api/projects/
Content-Type: multipart/form-data

name: NeuMoney Platform
domain: fintech
description: Digital payment processing platform
tech_stack: ["Java", "Spring Boot", "PostgreSQL", "AWS"]
stakeholders: {"product_owner": "John", "tech_lead": "Sanju"}
status: active
```

#### Upload Checklist

```http
POST /api/projects/{project_id}/upload-checklist
Content-Type: multipart/form-data

file: [Excel file]
```

**Response:**
```json
{
  "message": "Checklist uploaded and parsed successfully",
  "project_id": 1,
  "checklists": [
    {"id": 1, "type": "delivery", "items_count": 35},
    {"id": 2, "type": "technical", "items_count": 52}
  ],
  "statistics": {
    "file_name": "Project Review Check List V 1.0.xlsx",
    "sheets": ["Delivery Check List V 1.0", "Technical Check List V 1.0"]
  }
}
```

---

### Reviews

#### Create Review

```http
POST /api/reviews/
Content-Type: application/json

{
  "project_id": 1,
  "checklist_id": 1,
  "title": "Q1 2026 Technical Review",
  "voice_enabled": true,
  "participants": ["Sanju", "Chakravarthy"]
}
```

#### Start Review Agent

```http
POST /api/reviews/{review_id}/start
```

**Response:**
```json
{
  "message": "Review session started",
  "review_id": 1,
  "checklist_items_count": 35,
  "voice_enabled": true,
  "first_question": "Are scope / SoW / baselines clearly defined, signed off, and tracked?"
}
```

#### Submit Text Response

```http
POST /api/reviews/{review_id}/respond
Content-Type: application/json

{
  "question_index": 0,
  "answer": "Yes",
  "comments": "All baselines are signed off. Project charter v2.1 approved."
}
```

**Response:**
```json
{
  "message": "Response recorded",
  "rag_status": "green",
  "next_question": {
    "index": 1,
    "question": "Are change requests, assumptions, and dependencies captured?",
    "area": "Scope, Planning & Governance"
  },
  "progress": "1/35"
}
```

#### Submit Voice Response

```http
POST /api/reviews/{review_id}/voice-response
Content-Type: multipart/form-data

file: [audio.wav]
```

**Response:**
```json
{
  "message": "Voice response processed",
  "file_path": "./uploads/voice/review_1_20260325_103000.wav",
  "transcript": "Yes, all change requests are tracked in Jira",
  "intent": "affirmative",
  "answer": "Yes, all change requests are tracked in Jira"
}
```

#### Complete Review

```http
POST /api/reviews/{review_id}/complete
```

---

### Reports

#### List Reports

```http
GET /api/reports/?project_id=1&approval_status=pending
```

#### Get Report

```http
GET /api/reports/{report_id}
```

**Response:**
```json
{
  "id": 1,
  "review_id": 1,
  "summary": "Comprehensive review with 72.5% compliance",
  "overall_rag_status": "amber",
  "compliance_score": 72.5,
  "areas_followed": [
    "Scope baselines signed off",
    "Governance cadence followed"
  ],
  "gaps_identified": [
    {
      "title": "Architectural Decisions Not Documented",
      "description": "ADRs need to be documented",
      "severity": "high"
    }
  ],
  "recommendations": [
    "Document architectural decisions and trade-offs",
    "Update deployment validation procedures"
  ],
  "action_items": [
    {
      "item": "Document ADRs",
      "owner": "Sanju",
      "due_date": "2026-03-30",
      "priority": "High"
    }
  ],
  "approval_status": "pending",
  "requires_approval": true,
  "created_at": "2026-03-25T10:30:00"
}
```

#### Get Pending Approvals

```http
GET /api/reports/pending/approvals
```

#### Approve Report

```http
POST /api/reports/{report_id}/approve
Content-Type: application/json

{
  "approver_id": 1,
  "comments": "Comprehensive review. Approved for distribution."
}
```

**Response:**
```json
{
  "message": "Report approved successfully",
  "report_id": 1,
  "approved_by": "Admin User",
  "approved_at": "2026-03-25T11:00:00"
}
```

#### Reject Report

```http
POST /api/reports/{report_id}/reject
Content-Type: application/json

{
  "approver_id": 1,
  "comments": "Please add more details on security architecture gaps."
}
```

#### Download Report

```http
# Markdown format
GET /api/reports/{report_id}/download/markdown

# PDF format
GET /api/reports/{report_id}/download/pdf
```

---

### Checklists

#### Get Checklist

```http
GET /api/checklists/{checklist_id}?include_items=true
```

#### Optimize Checklist

```http
POST /api/checklists/{checklist_id}/optimize
```

**Response:**
```json
{
  "message": "Generated 6 recommendations",
  "checklist_id": 1,
  "domain": "fintech",
  "recommendations_count": 6
}
```

#### Get Recommendations

```http
GET /api/checklists/{checklist_id}/recommendations
```

#### Get Global Templates

```http
GET /api/checklists/templates/global?type=delivery
```

#### Use Template

```http
POST /api/checklists/templates/use/{template_id}?project_id=1
```

---

## Agent Workflow

### State Management

The agent uses LangGraph for stateful workflow management:

```python
class ReviewState(TypedDict):
    # Project context
    project_id: Optional[int]
    project_name: str
    project_domain: str
    project_context: Dict[str, Any]
    
    # Checklist data
    checklist_id: Optional[int]
    checklist_items: List[Dict[str, Any]]
    current_item_index: int
    
    # Review session
    review_id: Optional[int]
    responses: List[Dict[str, Any]]
    session_status: str
    
    # Voice interaction
    voice_enabled: bool
    last_transcript: Optional[str]
    
    # Agent conversation
    conversation_history: List[Dict[str, str]]
    current_question: Optional[str]
    user_answer: Optional[str]
    
    # Report generation
    report_data: Optional[Dict[str, Any]]
    compliance_score: float
    overall_rag: str
    
    # Approval workflow
    requires_approval: bool
    approval_status: str
    approver_id: Optional[int]
    
    # Errors and metadata
    errors: List[str]
    warnings: List[str]
    metadata: Dict[str, Any]
```

### Workflow Nodes

| Node | Purpose | Output |
|------|---------|--------|
| `initialize` | Setup review session | State with session_id, checklist loaded |
| `checklist_optimization` | AI-powered recommendations | Enhanced checklist items |
| `ask_question` | Present question to user | Question in conversation_history |
| `process_response` | Parse user answer | Response added to responses list |
| `assess_rag` | Determine RAG status | RAG status assigned to response |
| `generate_report` | Create comprehensive report | Report data with scores and gaps |
| `request_approval` | Set approval workflow | approval_status = "pending" |

### Conditional Edges

```python
# After initialize
if project_domain and llm_available:
    → checklist_optimization
else:
    → ask_question

# After assess_rag
if current_item_index < len(checklist_items):
    → ask_question (continue)
else:
    → generate_report

# After generate_report
→ request_approval → END
```

### RAG Assessment Logic

**Rule-Based (Default):**

```python
answer_lower = answer.lower()

if any(word in answer_lower for word in ["yes", "yeah", "yep", "done"]):
    rag_status = "green"      # Score: 100
elif any(word in answer_lower for word in ["no", "nope", "missing"]):
    rag_status = "red"        # Score: 0
elif any(word in answer_lower for word in ["partial", "in progress", "working"]):
    rag_status = "amber"      # Score: 50
else:
    rag_status = "na"         # Excluded from score
```

**LLM-Enhanced (Optional):**

```python
# Use LLM for nuanced assessment
system_prompt = """
Evaluate response quality and suggest RAG status:
- GREEN: Clear affirmative with evidence
- AMBER: Partial compliance or concerns mentioned
- RED: Negative response or significant gaps
"""

# LLM analyzes context and suggests RAG
```

### Compliance Score Calculation

```python
def calculate_compliance_score(responses, checklist_items):
    total_weight = 0
    weighted_score = 0
    
    rag_scores = {
        'green': 100,
        'amber': 50,
        'red': 0,
        'na': None  # Exclude
    }
    
    for response in responses:
        rag = response['rag_status'].lower()
        weight = response.get('weight', 1.0)
        
        score = rag_scores.get(rag)
        if score is not None:
            weighted_score += score * weight
            total_weight += weight
    
    return (weighted_score / total_weight) if total_weight > 0 else 0.0
```

**Overall RAG Determination:**

```python
def determine_overall_rag(compliance_score):
    if compliance_score >= 80:
        return 'green'
    elif compliance_score >= 50:
        return 'amber'
    else:
        return 'red'
```

---

## Database Schema

### Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐
│    User     │       │   Project   │
├─────────────┤       ├─────────────┤
│ id          │       │ id          │
│ email       │       │ name        │
│ full_name   │       │ domain      │
│ hashed_pw   │       │ description │
│ role        │       │ owner_id FK │───┐
│ created_at  │       │ status      │    │
└─────────────┘       └─────────────┘    │
       │                  │              │
       │                  │              │
       │                  ▼              │
       │         ┌─────────────┐         │
       │         │  Checklist  │         │
       │         ├─────────────┤         │
       │         │ id          │         │
       │         │ name        │         │
       │         │ type        │         │
       │         │ project_id FK│────────┘
       │         │ is_global   │
       │         └─────────────┘
       │                │
       │                │
       │                ▼
       │         ┌─────────────┐
       │         │ Checklist   │
       │         │    Item     │
       │         ├─────────────┤
       │         │ id          │
       │         │ checklist_id│
       │         │ question    │
       │         │ area        │
       │         │ weight      │
       │         └─────────────┘
       │
       │         ┌─────────────┐
       │         │    Review   │
       │         ├─────────────┤
       │         │ id          │
       │         │ project_id  │
       │         │ checklist_id│
       │         │ conducted_by│───┐
       │         │ status      │    │
       │         └─────────────┘    │
       │                │           │
       │                │           │
       │                ▼           │
       │         ┌─────────────┐    │
       │         │   Review    │    │
       │         │  Response   │    │
       │         ├─────────────┤    │
       │         │ review_id   │    │
       │         │ item_id     │    │
       │         │ answer      │    │
       │         │ rag_status  │    │
       │         └─────────────┘    │
       │                            │
       │         ┌─────────────┐    │
       │         │   Report    │    │
       │         ├─────────────┤    │
       │         │ review_id   │    │
       │         │ score       │    │
       │         │ rag_status  │    │
       │         │ approval_   │    │
       │         │   status    │    │
       │         └─────────────┘    │
       │                │           │
       │                │           │
       │                ▼           │
       │         ┌─────────────┐    │
       │         │   Report    │    │
       │         │  Approval   │    │
       │         ├─────────────┤    │
       │         │ report_id   │    │
       │         │ approver_id │────┘
       │         │ status      │
       │         │ comments    │
       │         └─────────────┘
```

### Table Schemas

#### Users

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Index | Auto-increment ID |
| email | String | Unique, Index | User email |
| full_name | String | Not Null | Display name |
| hashed_password | String | Not Null | Bcrypt hash |
| role | String | Default: "reviewer" | reviewer/manager/admin |
| is_active | Boolean | Default: true | Account status |
| created_at | DateTime | Default: utcnow | Creation timestamp |

#### Projects

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Index | Auto-increment ID |
| name | String | Not Null | Project name |
| domain | String | - | fintech/healthcare/etc |
| description | Text | - | Project description |
| tech_stack | JSON | - | List of technologies |
| stakeholders | JSON | - | Dict with roles/names |
| start_date | DateTime | - | Project start |
| end_date | DateTime | - | Project end |
| status | String | Default: "active" | active/completed/on_hold |
| owner_id | Integer | FK → Users | Project owner |
| created_at | DateTime | Default: utcnow | Creation timestamp |
| updated_at | DateTime | Default: utcnow | Last update |

#### Checklists

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Index | Auto-increment ID |
| name | String | Not Null | Checklist name |
| type | String | Not Null | delivery/technical |
| version | String | Default: "1.0" | Version string |
| project_id | Integer | FK → Projects | Owner project (nullable) |
| is_global | Boolean | Default: true | Global template flag |
| created_at | DateTime | Default: utcnow | Creation timestamp |
| updated_at | DateTime | Default: utcnow | Last update |

#### ChecklistItems

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Index | Auto-increment ID |
| checklist_id | Integer | FK → Checklists | Parent checklist |
| item_code | String | - | e.g., "1.1", "1.10" |
| area | String | - | e.g., "Scope, Planning" |
| question | Text | Not Null | Review question |
| category | String | - | For grouping |
| weight | Float | Default: 1.0 | Scoring weight |
| is_required | Boolean | Default: true | Mandatory flag |
| expected_evidence | Text | - | What to look for |
| suggested_for_domains | JSON | - | Domain relevance |
| order | Integer | Default: 0 | Display order |
| created_at | DateTime | Default: utcnow | Creation timestamp |

#### Reviews

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Index | Auto-increment ID |
| project_id | Integer | FK → Projects | Owner project |
| checklist_id | Integer | FK → Checklists | Used checklist |
| title | String | - | Review title |
| conducted_by | Integer | FK → Users | Reviewer |
| participants | JSON | - | List of names |
| review_date | DateTime | Default: utcnow | Review date |
| status | String | Default: "draft" | draft/in_progress/completed/pending_approval |
| voice_enabled | Boolean | Default: true | Voice feature flag |
| notes | Text | - | Reviewer notes |
| created_at | DateTime | Default: utcnow | Creation timestamp |
| completed_at | DateTime | - | Completion timestamp |

#### ReviewResponses

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Index | Auto-increment ID |
| review_id | Integer | FK → Reviews | Parent review |
| checklist_item_id | Integer | FK → ChecklistItems | Question answered |
| answer | String | - | User response |
| comments | Text | - | Additional context |
| rag_status | String | Default: "na" | red/amber/green/na |
| evidence_links | JSON | - | URLs or file paths |
| attachments | JSON | - | File metadata |
| voice_recording_path | String | - | Audio file path |
| transcript | Text | - | STT transcript |
| created_at | DateTime | Default: utcnow | Creation timestamp |
| updated_at | DateTime | Default: utcnow | Last update |

#### Reports

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Index | Auto-increment ID |
| review_id | Integer | FK → Reviews, Unique | Parent review |
| summary | Text | - | Executive summary |
| overall_rag_status | String | - | Overall RAG |
| compliance_score | Float | - | 0-100 score |
| areas_followed | JSON | - | List of compliant areas |
| gaps_identified | JSON | - | List of gaps |
| recommendations | JSON | - | List of recommendations |
| action_items | JSON | - | List of action items |
| pdf_path | String | - | PDF file path |
| markdown_path | String | - | Markdown file path |
| approval_status | String | Default: "pending" | pending/approved/rejected/revision_requested |
| requires_approval | Boolean | Default: true | Approval required |
| created_at | DateTime | Default: utcnow | Creation timestamp |
| approved_at | DateTime | - | Approval timestamp |

#### ReportApprovals

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| id | Integer | PK, Index | Auto-increment ID |
| report_id | Integer | FK → Reports | Report being approved |
| approver_id | Integer | FK → Users | Approver |
| status | String | Default: "pending" | Approval status |
| comments | Text | - | Approval comments |
| decided_at | DateTime | - | Decision timestamp |
| created_at | DateTime | Default: utcnow | Creation timestamp |

---

## Voice Integration

### Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   User      │────▶│  Voice     │────▶│  OpenAI     │
│   Speaks    │     │  Interface │     │  Whisper    │
└─────────────┘     └─────────────┘     └─────────────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │  Transcript │
                                        │  Text       │
                                        └─────────────┘
                                               │
                                               ▼
                                        ┌─────────────┐
                                        │  Intent     │
                                        │  Detection  │
                                        └─────────────┘
```

### Speech-to-Text (STT)

```python
async def speech_to_text(self, audio_file_path: str) -> Optional[str]:
    """Convert speech audio file to text transcript"""
    if not self.openai_client:
        return None
    
    with open(audio_path, "rb") as audio_file:
        transcript = self.openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language=settings.DEFAULT_LANGUAGE
        )
    
    return transcript.text
```

**Supported Audio Formats:**
- WAV (recommended)
- MP3
- M4A
- WebM
- FLAC

**File Size Limit:** 25 MB

### Text-to-Speech (TTS)

```python
async def text_to_speech(self, text: str, output_path: str, voice: str = "alloy") -> bool:
    """Convert text to speech audio"""
    response = self.openai_client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text
    )
    
    response.stream_to_file(str(output_path))
    return True
```

**Available Voices:**

| Voice ID | Name | Characteristics |
|----------|------|-----------------|
| `alloy` | Alloy | Neutral, balanced |
| `echo` | Echo | Male, warm |
| `fable` | Fable | British, articulate |
| `onyx` | Onyx | Deep, authoritative |
| `nova` | Nova | Female, clear |
| `shimmer` | Shimmer | Warm, friendly |

### Intent Detection

```python
async def process_voice_input(self, audio_file_path: str, context: Optional[str] = None) -> dict:
    """Process voice input and return structured response"""
    transcript = await self.speech_to_text(audio_file_path)
    
    # Intent detection based on keywords
    transcript_lower = transcript.lower()
    intent = "answer"
    
    if any(word in transcript_lower for word in ["yes", "yeah", "yep", "correct"]):
        intent = "affirmative"
    elif any(word in transcript_lower for word in ["no", "nope", "incorrect"]):
        intent = "negative"
    elif any(word in transcript_lower for word in ["skip", "next", "later"]):
        intent = "skip"
    elif any(word in transcript_lower for word in ["repeat", "again", "what"]):
        intent = "clarify"
    
    return {
        "success": True,
        "transcript": transcript,
        "intent": intent,
        "context": context
    }
```

### Voice Workflow Example

```python
# 1. User records audio
audio_file = "response.wav"

# 2. Submit to API
response = requests.post(
    f"http://localhost:8000/api/reviews/1/voice-response",
    files={"file": open(audio_file, "rb")}
)

# 3. Receive transcript and intent
data = response.json()
print(f"Transcript: {data['transcript']}")
print(f"Intent: {data['intent']}")

# 4. Use transcript as answer
answer = data['transcript']
```

---

## Report Generation

### Report Structure

```markdown
# Project Review Report - [Project Name]

## Executive Summary
- Project: [Name]
- Review Date: [Date]
- Overall RAG Status: 🟢/🟡/🔴 [Status]
- Compliance Score: [XX.X]%
- Participants: [Names]

---

## 🟢 Areas Followed Well

✅ [Item 1]
✅ [Item 2]
...

---

## 🔴 Gaps Identified

🔴 **[Gap Title 1]**
   [Description]

🟡 **[Gap Title 2]**
   [Description]

---

## 💡 Recommendations

1. [Recommendation 1]
2. [Recommendation 2]
...

---

## 📋 Action Items

| Item | Owner | Due Date | Priority |
|------|-------|----------|----------|
| [Item] | [Owner] | [Date] | [Priority] |

---

## Detailed Findings

### [Area 1]
[Description]

### [Area 2]
[Description]

---

## Approval Status

**Status:** PENDING/APPROVED/REJECTED

> ⚠️ This report requires human approval before distribution.

---

*Generated by AI Tech & Delivery Review Agent v1.0.0*
*Generated at: [Timestamp]*
```

### Markdown Generation

```python
def generate_markdown_report(self, report_data: Dict[str, Any]) -> str:
    """Generate markdown format report"""
    
    md_content = f"""# Project Review Report

## Executive Summary
- **Project:** {report_data.get('project_name', 'N/A')}
- **Review Date:** {report_data.get('review_date')}
- **Overall RAG Status:** {self._get_rag_emoji(report_data.get('overall_rag_status'))} {report_data.get('overall_rag_status', 'N/A').upper()}
- **Compliance Score:** {report_data.get('compliance_score', 0):.1f}%

---

## {self._get_rag_emoji('green')} Areas Followed Well

{self._format_list(report_data.get('areas_followed', []))}

---

## {self._get_rag_emoji('red')} Gaps Identified

{self._format_gaps(report_data.get('gaps_identified', []))}

---

## 💡 Recommendations

{self._format_list(report_data.get('recommendations', []))}

---

## 📋 Action Items

{self._format_action_items(report_data.get('action_items', []))}

---

*Generated by AI Tech & Delivery Review Agent*
"""
    
    # Save to file
    filename = f"report_{project_name}_{timestamp}.md"
    file_path = self.reports_dir / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(md_content)
    
    return str(file_path)
```

### PDF Generation

```python
def generate_pdf_report(self, report_data: Dict[str, Any]) -> str:
    """Generate PDF format report using ReportLab"""
    
    doc = SimpleDocTemplate(
        str(file_path),
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=72,
        bottomMargin=72
    )
    
    content = []
    styles = getSampleStyleSheet()
    
    # Title
    content.append(Paragraph("Project Review Report", styles['Heading1']))
    
    # Summary table
    summary_data = [
        ['Project', report_data.get('project_name', 'N/A')],
        ['Review Date', report_data.get('review_date')],
        ['RAG Status', f"{report_data.get('overall_rag_status', 'N/A').upper()}"],
        ['Compliance Score', f"{report_data.get('compliance_score', 0):.1f}%"]
    ]
    
    summary_table = Table(summary_data, colWidths=[150, 300])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f0f0f0')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey)
    ]))
    content.append(summary_table)
    
    # Build PDF
    doc.build(content)
    return str(file_path)
```

### Gap Analysis

```python
def analyze_gaps(self, responses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Analyze responses to identify gaps"""
    gaps = []
    
    for response in responses:
        rag = response.get('rag_status', 'na').lower()
        
        if rag in ['red', 'amber']:
            gaps.append({
                'title': response.get('question', 'Unknown'),
                'description': response.get('comments', ''),
                'rag_status': rag,
                'area': response.get('area', 'General'),
                'severity': 'high' if rag == 'red' else 'medium'
            })
    
    return gaps
```

### Action Item Generation

```python
def generate_action_items(
    self,
    gaps: List[Dict[str, Any]],
    participants: List[str]
) -> List[Dict[str, Any]]:
    """Generate action items from identified gaps"""
    action_items = []
    
    for idx, gap in enumerate(gaps, 1):
        action_items.append({
            'item': f"Address: {gap['title']}",
            'owner': 'TBD',
            'due_date': 'TBD',
            'priority': gap.get('severity', 'medium').capitalize(),
            'related_gap': gap['title']
        })
    
    return action_items
```

---

## Approval Workflow

### Workflow States

```
┌─────────────┐
│   PENDING   │───────┐
└─────────────┘       │
       │              │
       │ Approve      │ Reject
       ▼              ▼
┌─────────────┐  ┌─────────────┐
│  APPROVED   │  │   REJECTED  │
└─────────────┘  └─────────────┘
                        │
                        │ Revision
                        ▼
               ┌─────────────────┐
               │ REVISION_       │
               │ REQUESTED       │
               └─────────────────┘
```

### Approval Process

```python
# 1. Report generated - status set to PENDING
report.approval_status = "pending"
report.requires_approval = True

# 2. Human reviewer views report
GET /api/reports/pending/approvals

# 3A. Approve report
POST /api/reports/{report_id}/approve
{
  "approver_id": 1,
  "comments": "Approved for distribution"
}

# Updates:
report.approval_status = "approved"
report.approved_at = datetime.utcnow()

# 3B. Reject report
POST /api/reports/{report_id}/reject
{
  "approver_id": 1,
  "comments": "Please add more details on security gaps"
}

# Updates:
report.approval_status = "revision_requested"
review.status = "pending_approval"

# 4. Download approved report
GET /api/reports/{report_id}/download/pdf
```

### Approval Tracking

```python
# Create approval record
approval = ReportApproval(
    report_id=report_id,
    approver_id=approver_id,
    status="approved",  # or "rejected"
    comments=comments,
    decided_at=datetime.utcnow()
)

db.add(approval)
await db.commit()
```

### Approval History

```http
GET /api/reports/{report_id}/approvals
```

**Response:**
```json
{
  "report_id": 1,
  "approvals": [
    {
      "id": 1,
      "approver_id": 1,
      "approver_name": "Admin User",
      "status": "approved",
      "comments": "Comprehensive review. Approved.",
      "decided_at": "2026-03-25T11:00:00"
    }
  ]
}
```

---

## Domain Intelligence

### Domain-Specific Checklist Additions

The agent automatically suggests additional checklist items based on project domain:

### Fintech

```python
DOMAIN_CHECKLIST_ADDITIONS = {
    "fintech": {
        "delivery": [
            {
                "area": "Compliance & Regulatory",
                "question": "Are PCI-DSS compliance requirements identified and tracked?",
                "category": "compliance",
                "priority": "high"
            },
            {
                "area": "Compliance & Regulatory",
                "question": "Is SOX compliance addressed for financial reporting systems?",
                "category": "compliance",
                "priority": "high"
            },
            {
                "area": "Security",
                "question": "Are fraud detection and prevention mechanisms in place?",
                "category": "security",
                "priority": "high"
            }
        ],
        "technical": [
            {
                "area": "Security Architecture",
                "question": "Is transaction integrity ensured with proper audit trails?",
                "category": "security",
                "priority": "high"
            },
            {
                "area": "Data & Storage Design",
                "question": "Are financial data retention policies compliant with regulatory requirements?",
                "category": "compliance",
                "priority": "high"
            },
            {
                "area": "Integration Design",
                "question": "Are payment gateway integrations secure and PCI-compliant?",
                "category": "security",
                "priority": "high"
            }
        ]
    }
}
```

### Healthcare

```python
"healthcare": {
    "delivery": [
        {
            "area": "Compliance & Regulatory",
            "question": "Is HIPAA compliance validated and documented?",
            "category": "compliance",
            "priority": "critical"
        },
        {
            "area": "Risk Management",
            "question": "Are patient safety risks identified and mitigated?",
            "category": "risk",
            "priority": "critical"
        }
    ],
    "technical": [
        {
            "area": "Security Architecture",
            "question": "Is PHI (Protected Health Information) properly encrypted and access-controlled?",
            "category": "security",
            "priority": "critical"
        },
        {
            "area": "Audit & Compliance",
            "question": "Are audit logs comprehensive for HIPAA compliance (who accessed what when)?",
            "category": "compliance",
            "priority": "critical"
        },
        {
            "area": "Integration Design",
            "question": "Are healthcare integrations (HL7, FHIR) implemented correctly?",
            "category": "integration",
            "priority": "high"
        }
    ]
}
```

### E-commerce

```python
"ecommerce": {
    "delivery": [
        {
            "area": "Performance & Scalability",
            "question": "Is the system tested for peak load (Black Friday scenarios)?",
            "category": "performance",
            "priority": "high"
        },
        {
            "area": "Customer Experience",
            "question": "Is the checkout flow optimized and tested for abandonment?",
            "category": "ux",
            "priority": "high"
        }
    ],
    "technical": [
        {
            "area": "Scalability Design",
            "question": "Can the system handle 10x normal load during sales events?",
            "category": "scalability",
            "priority": "high"
        },
        {
            "area": "Inventory Management",
            "question": "Is inventory consistency ensured across channels (no overselling)?",
            "category": "data_integrity",
            "priority": "high"
        }
    ]
}
```

### Data Migration

```python
"data_migration": {
    "delivery": [
        {
            "area": "Migration Planning",
            "question": "Is there a detailed cutover plan with rollback strategy?",
            "category": "planning",
            "priority": "critical"
        },
        {
            "area": "Data Validation",
            "question": "Are reconciliation processes defined for post-migration validation?",
            "category": "validation",
            "priority": "critical"
        }
    ],
    "technical": [
        {
            "area": "Migration Strategy",
            "question": "Is the migration approach (big bang vs phased) documented and justified?",
            "category": "architecture",
            "priority": "high"
        },
        {
            "area": "Data Quality",
            "question": "Are data cleansing and transformation rules documented and tested?",
            "category": "data_quality",
            "priority": "high"
        },
        {
            "area": "Rollback Design",
            "question": "Is rollback tested and validated for failure scenarios?",
            "category": "resilience",
            "priority": "critical"
        }
    ]
}
```

### AI/ML Projects

```python
"ai_ml": {
    "delivery": [
        {
            "area": "Model Governance",
            "question": "Is there a model validation and approval process?",
            "category": "governance",
            "priority": "high"
        },
        {
            "area": "Ethics & Bias",
            "question": "Are bias testing and fairness assessments conducted?",
            "category": "ethics",
            "priority": "high"
        }
    ],
    "technical": [
        {
            "area": "Model Architecture",
            "question": "Is model versioning and lineage tracking implemented?",
            "category": "mlops",
            "priority": "high"
        },
        {
            "area": "Monitoring",
            "question": "Is model drift detection and retraining automated?",
            "category": "monitoring",
            "priority": "high"
        }
    ]
}
```

### Domain Inference

```python
def infer_domain_from_checklist_responses(
    delivery_responses: Dict[str, str],
    technical_responses: Dict[str, str]
) -> List[Dict[str, str]]:
    """Infer project domain based on checklist responses"""
    
    domain_indicators = {
        "fintech": {
            "keywords": ["payment", "financial", "transaction", "pci", "sox", "banking"],
            "score": 0.0
        },
        "healthcare": {
            "keywords": ["hipaa", "patient", "medical", "health", "ehr", "phi"],
            "score": 0.0
        },
        "ecommerce": {
            "keywords": ["cart", "order", "product", "inventory", "shipping", "retail"],
            "score": 0.0
        },
        "data_migration": {
            "keywords": ["migration", "etl", "cutover", "legacy", "data transfer"],
            "score": 0.0
        }
    }
    
    # Combine all responses
    all_text = " ".join([
        " ".join(delivery_responses.values()),
        " ".join(technical_responses.values())
    ]).lower()
    
    # Score each domain
    for domain, data in domain_indicators.items():
        for keyword in data["keywords"]:
            if keyword in all_text:
                data["score"] += 0.2
        data["score"] = min(data["score"], 1.0)
    
    # Return sorted by confidence
    results = [
        {"domain": domain, "confidence": data["score"]}
        for domain, data in domain_indicators.items()
        if data["score"] > 0.0
    ]
    
    return sorted(results, key=lambda x: x["confidence"], reverse=True)
```

---

## Testing

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=app

# Run specific test file
pytest tests/test_agent.py -v

# Run specific test
pytest tests/test_agent.py::TestReportGenerator::test_calculate_compliance_score -v
```

### Test Structure

```python
import pytest
from app.services.report_generator import ReportGenerator
from app.models import RAGStatus, Project, Review

class TestChecklistParser:
    """Test Excel checklist parsing"""
    
    def test_parser_initialization(self):
        from app.services.checklist_parser import ChecklistParser
        parser = ChecklistParser("test.xlsx")
        assert parser.file_path.name == "test.xlsx"
    
    def test_parse_delivery_checklist_structure(self):
        item = {
            "item_code": "1.1",
            "area": "Scope, Planning & Governance",
            "question": "Are scope / SoW / baselines clearly defined?",
            "category": "delivery",
            "weight": 1.0,
            "is_required": True
        }
        assert item["item_code"] == "1.1"
        assert item["category"] == "delivery"


class TestReportGenerator:
    """Test report generation"""
    
    def test_calculate_compliance_score_all_green(self):
        generator = ReportGenerator()
        responses = [
            {"rag_status": "green", "weight": 1.0},
            {"rag_status": "green", "weight": 1.0},
            {"rag_status": "green", "weight": 1.0}
        ]
        score = generator.calculate_compliance_score(responses, [])
        assert score == 100.0
    
    def test_calculate_compliance_score_mixed(self):
        generator = ReportGenerator()
        responses = [
            {"rag_status": "green", "weight": 1.0},  # 100
            {"rag_status": "amber", "weight": 1.0},  # 50
            {"rag_status": "red", "weight": 1.0}     # 0
        ]
        score = generator.calculate_compliance_score(responses, [])
        assert score == 50.0  # (100 + 50 + 0) / 3


class TestDatabaseModels:
    """Test database models"""
    
    def test_project_model(self):
        from app.models import Project
        project = Project(
            name="Test Project",
            domain="fintech",
            description="Test description"
        )
        assert project.name == "Test Project"
        assert project.domain == "fintech"
        assert project.status == "active"


class TestAPIEndpoints:
    """Test API endpoint availability"""
    
    @pytest.mark.asyncio
    async def test_health_endpoint(self):
        from fastapi.testclient import TestClient
        from main import app
        
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
```

---

## Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create directories
RUN mkdir -p uploads reports chroma_db

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+asyncpg://user:password@db:5432/reviews_db
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - SECRET_KEY=${SECRET_KEY}
    volumes:
      - ./uploads:/app/uploads
      - ./reports:/app/reports
      - chroma_data:/app/chroma_db
    depends_on:
      - db
  
  db:
    image: postgres:15
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=password
      - POSTGRES_DB=reviews_db
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
  chroma_data:
```

### Production Checklist

- [ ] Use PostgreSQL instead of SQLite
- [ ] Configure proper CORS origins
- [ ] Enable HTTPS/TLS
- [ ] Set up logging and monitoring (ELK stack, CloudWatch)
- [ ] Configure backup strategy (daily DB backups)
- [ ] Set up CI/CD pipeline (GitHub Actions, GitLab CI)
- [ ] Add rate limiting (slowapi)
- [ ] Enable audit logging
- [ ] Configure secrets management (AWS Secrets Manager, HashiCorp Vault)
- [ ] Set up health checks and alerts
- [ ] Use gunicorn with uvicorn workers
- [ ] Configure proper logging (JSON format, structured logs)

### Environment-Specific Configuration

```env
# .env.production

# Database
DATABASE_URL="postgresql+asyncpg://user:password@prod-db:5432/reviews_db"

# Security
SECRET_KEY=${SECRET_KEY_FROM_VAULT}
DEBUG=false

# API Keys
OPENAI_API_KEY=${OPENAI_API_KEY_FROM_SECRETS}

# Application
VOICE_ENABLED=true
REQUIRE_HUMAN_APPROVAL=true

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

---

## Troubleshooting

### Common Issues

#### Database Not Found

**Error:**
```
sqlalchemy.exc.OperationalError: (sqlite3.OperationalError) unable to open database file
```

**Solution:**
```bash
# Run setup script
python setup.py

# Or manually create database
python -c "from app.db.session import init_db; import asyncio; asyncio.run(init_db())"
```

---

#### OpenAI API Errors

**Error:**
```
openai.AuthenticationError: Error code: 401 - Invalid API key
```

**Solution:**
1. Check `.env` file:
   ```env
   OPENAI_API_KEY=sk-valid-key-here
   ```

2. Verify API key is valid:
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

3. Restart server after changing `.env`

---

#### Voice Transcription Fails

**Error:**
```
STT Error: Could not transcribe audio
```

**Solution:**
1. Verify audio file format (WAV recommended)
2. Check file size (< 25 MB)
3. Ensure OpenAI API key has Whisper access
4. Test with sample audio file

---

#### PDF Generation Fails

**Error:**
```
ImportError: No module named 'reportlab'
```

**Solution:**
```bash
pip install reportlab
```

---

#### Import Errors

**Error:**
```
ModuleNotFoundError: No module named 'langchain'
```

**Solution:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

---

#### CORS Errors

**Error:**
```
Access to XMLHttpRequest has been blocked by CORS policy
```

**Solution:**
```python
# In main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],  # Specific domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

#### Permission Denied (File Operations)

**Error:**
```
PermissionError: [Errno 13] Permission denied: './reports/report.md'
```

**Solution:**
```bash
# Create directories with proper permissions
mkdir -p uploads reports chroma_db
chmod 755 uploads reports chroma_db

# Or on Windows
icacls uploads /grant Everyone:F
icacls reports /grant Everyone:F
icacls chroma_db /grant Everyone:F
```

---

#### Slow Performance

**Symptoms:**
- Slow API responses
- Database queries taking long

**Solutions:**
1. Enable database query logging:
   ```python
   engine = create_async_engine(
       settings.DATABASE_URL,
       echo=True  # Log queries
   )
   ```

2. Add database indexes:
   ```python
   class Project(Base):
       id = Column(Integer, primary_key=True, index=True)
       email = Column(String, unique=True, index=True)
   ```

3. Use connection pooling (default in SQLAlchemy)

4. Cache frequently accessed data (Redis)

---

## Best Practices

### Development

1. **Use Virtual Environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # or venv\Scripts\activate on Windows
   ```

2. **Keep Dependencies Updated:**
   ```bash
   pip list --outdated
   pip install --upgrade package-name
   ```

3. **Run Tests Before Commit:**
   ```bash
   pytest tests/ -v
   ```

4. **Use Pre-commit Hooks:**
   ```bash
   pip install pre-commit
   pre-commit install
   ```

5. **Format Code:**
   ```bash
   pip install black isort
   black app/
   isort app/
   ```

---

### Security

1. **Never Commit Secrets:**
   ```bash
   # Add to .gitignore
   .env
   *.db
   uploads/
   reports/
   ```

2. **Use Environment Variables:**
   ```python
   from app.core.config import settings
   api_key = settings.OPENAI_API_KEY
   ```

3. **Hash Passwords:**
   ```python
   from passlib.context import CryptContext
   pwd_context = CryptContext(schemes=["bcrypt"])
   hashed = pwd_context.hash("password")
   ```

4. **Validate Input:**
   ```python
   from pydantic import BaseModel, EmailStr
   
   class UserCreate(BaseModel):
       email: EmailStr
       password: str
   ```

5. **Use HTTPS in Production:**
   - Configure SSL certificate
   - Use reverse proxy (nginx)
   - Or use cloud platform with managed SSL

---

### Database

1. **Use Async Operations:**
   ```python
   async with AsyncSessionLocal() as session:
       result = await session.execute(query)
       items = result.scalars().all()
   ```

2. **Handle Transactions:**
   ```python
   async with session.begin():
       # Auto-commit on success
       # Auto-rollback on exception
       db.add(item)
   ```

3. **Add Indexes:**
   ```python
   email = Column(String, unique=True, index=True)
   ```

4. **Use Connection Pooling:**
   ```python
   engine = create_async_engine(
       DATABASE_URL,
       pool_size=10,
       max_overflow=20
   )
   ```

---

### API Design

1. **Use Consistent Response Format:**
   ```python
   return {
       "success": True,
       "data": {...},
       "message": "Operation completed"
   }
   ```

2. **Proper Error Handling:**
   ```python
   from fastapi import HTTPException
   
   if not item:
       raise HTTPException(status_code=404, detail="Item not found")
   ```

3. **Pagination:**
   ```python
   @router.get("/")
   async def list_items(skip: int = 0, limit: int = 100):
       items = await db.query().offset(skip).limit(limit).all()
       return {"items": items, "total": len(items)}
   ```

4. **Rate Limiting:**
   ```python
   from slowapi import Limiter
   limiter = Limiter(key_func=get_remote_address)
   
   @router.get("/")
   @limiter.limit("10/minute")
   async def get_items(request: Request):
       ...
   ```

---

### Monitoring

1. **Add Logging:**
   ```python
   import logging
   
   logger = logging.getLogger(__name__)
   
   logger.info("Review started")
   logger.error(f"Error: {str(e)}")
   ```

2. **Health Checks:**
   ```python
   @app.get("/health")
   async def health_check():
       return {
           "status": "healthy",
           "database": "connected",
           "timestamp": datetime.utcnow().isoformat()
       }
   ```

3. **Metrics:**
   - Track API response times
   - Monitor database query performance
   - Track review completion rates
   - Monitor approval turnaround times

---

### Deployment

1. **Use Production Server:**
   ```bash
   # Development
   uvicorn main:app --reload
   
   # Production
   gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker
   ```

2. **Configure Logging:**
   ```python
   import logging
   
   logging.basicConfig(
       level=logging.INFO,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   ```

3. **Backup Strategy:**
   - Daily database backups
   - Weekly full system backup
   - Test restore procedures monthly

4. **Disaster Recovery:**
   - Document recovery procedures
   - Maintain backup of critical configurations
   - Test failover procedures

---

## Appendix

### A. API Quick Reference

| Category | Endpoint | Method | Description |
|----------|----------|--------|-------------|
| Auth | `/api/auth/register` | POST | Register user |
| Auth | `/api/auth/login` | POST | Login |
| Auth | `/api/auth/me` | GET | Get current user |
| Projects | `/api/projects/` | GET | List projects |
| Projects | `/api/projects/` | POST | Create project |
| Projects | `/api/projects/{id}` | GET | Get project |
| Projects | `/api/projects/{id}` | PUT | Update project |
| Projects | `/api/projects/{id}` | DELETE | Delete project |
| Projects | `/api/projects/{id}/upload-checklist` | POST | Upload Excel |
| Reviews | `/api/reviews/` | GET | List reviews |
| Reviews | `/api/reviews/` | POST | Create review |
| Reviews | `/api/reviews/{id}/start` | POST | Start agent |
| Reviews | `/api/reviews/{id}/respond` | POST | Submit response |
| Reviews | `/api/reviews/{id}/voice-response` | POST | Submit voice |
| Reviews | `/api/reviews/{id}/complete` | POST | Complete review |
| Reports | `/api/reports/` | GET | List reports |
| Reports | `/api/reports/{id}` | GET | Get report |
| Reports | `/api/reports/{id}/download/{format}` | GET | Download |
| Reports | `/api/reports/{id}/approve` | POST | Approve |
| Reports | `/api/reports/{id}/reject` | POST | Reject |
| Reports | `/api/reports/pending/approvals` | GET | Pending |
| Checklists | `/api/checklists/{id}` | GET | Get checklist |
| Checklists | `/api/checklists/{id}/optimize` | POST | Optimize |
| Checklists | `/api/checklists/templates/global` | GET | Templates |

---

### B. Glossary

| Term | Definition |
|------|------------|
| **RAG** | Red/Amber/Green status indicator |
| **STT** | Speech-to-Text (voice transcription) |
| **TTS** | Text-to-Speech (voice synthesis) |
| **ADRs** | Architectural Decision Records |
| **PHI** | Protected Health Information |
| **PCI-DSS** | Payment Card Industry Data Security Standard |
| **SOX** | Sarbanes-Oxley Act (financial compliance) |
| **HIPAA** | Health Insurance Portability and Accountability Act |
| **LangGraph** | Library for building stateful AI workflows |
| **FastAPI** | Modern Python web framework |
| **SQLAlchemy** | SQL toolkit and ORM |

---

### C. Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **LangGraph Documentation**: https://langchain-ai.github.io/langgraph/
- **OpenAI API**: https://platform.openai.com/docs/
- **SQLAlchemy**: https://docs.sqlalchemy.org/
- **ReportLab**: https://www.reportlab.com/docs/reportlab-userguide.pdf

---

*Document Version: 1.0.0*
*Last Updated: March 25, 2026*
*AI Tech & Delivery Review Agent*
