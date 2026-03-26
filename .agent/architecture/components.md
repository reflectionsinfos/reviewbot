# Component Details

## Core Components

### 1. Review Agent (LangGraph)

**Location:** `app/agents/review_agent.py`

**Purpose:** Orchestrates the review workflow using stateful graphs

**Key Responsibilities:**
- Initialize review sessions
- Ask questions one at a time
- Process responses (text/voice)
- Assess RAG status
- Generate reports
- Request human approval

**Workflow:**
```
Initialize → Optimize Checklist? → Ask Question → Process Response → Assess RAG
     ↓                                                                  ↓
     └──────────────────── More Questions? ────────────────────────────┘
                                    ↓ No
                            Generate Report → Request Approval → End
```

**State Management:**
```python
class ReviewState(TypedDict):
    project_id: Optional[int]
    project_name: str
    checklist_items: List[Dict[str, Any]]
    current_item_index: int
    responses: List[Dict[str, Any]]
    conversation_history: List[Dict[str, str]]
    report_data: Optional[Dict[str, Any]]
    compliance_score: float
    approval_status: str
```

---

### 2. Checklist Parser

**Location:** `app/services/checklist_parser.py`

**Purpose:** Parse Excel checklist files into structured data

**Key Functions:**
- `load()` - Load all sheets from Excel
- `parse_delivery_checklist()` - Extract delivery questions
- `parse_technical_checklist()` - Extract technical questions
- `parse_all()` - Parse all checklists
- `get_statistics()` - Get file statistics

**Input Format:**
```
Excel Sheet: "Delivery Check List V 1.0"
Columns: SNO, Area, Key Review Question, Inputs from Delivery, Comments, RAG
```

**Output Format:**
```python
[
    {
        "item_code": "1.1",
        "area": "Scope, Planning & Governance",
        "question": "Are scope / SoW / baselines clearly defined?",
        "category": "delivery",
        "weight": 1.0,
        "is_required": True
    }
]
```

---

### 3. Checklist Optimizer

**Location:** `app/services/checklist_optimizer.py`

**Purpose:** Generate AI-powered checklist recommendations

**Key Features:**
- Domain-specific additions (fintech, healthcare, e-commerce, etc.)
- LLM-based contextual recommendations
- Redundancy detection
- Template generation for new projects

**Domain Additions Example:**
```python
"fintech": {
    "delivery": [
        "Are PCI-DSS compliance requirements identified?",
        "Is SOX compliance addressed?",
        "Are fraud detection mechanisms in place?"
    ],
    "technical": [
        "Is transaction integrity ensured with audit trails?",
        "Are payment gateway integrations PCI-compliant?"
    ]
}
```

---

### 4. Report Generator

**Location:** `app/services/report_generator.py`

**Purpose:** Generate comprehensive review reports

**Output Formats:**
- Markdown (.md)
- PDF (.pdf)

**Report Sections:**
1. Executive Summary
2. Areas Followed Well (Green items)
3. Gaps Identified (Red/Amber items)
4. Recommendations
5. Action Items
6. Detailed Findings
7. Approval Status

**Scoring Logic:**
```python
# RAG Scores
green = 100
amber = 50
red = 0
na = None  # Excluded

# Compliance Score
score = (sum of weighted RAG scores) / (total weight)

# Overall RAG
score >= 80 → green
score 50-79 → amber
score < 50 → red
```

---

### 5. Voice Interface

**Location:** `app/services/voice_interface.py`

**Purpose:** Handle speech-to-text and text-to-speech

**STT (Speech-to-Text):**
```python
async def speech_to_text(audio_file_path: str) -> str:
    # Uses OpenAI Whisper API
    transcript = openai_client.audio.transcriptions.create(
        model="whisper-1",
        file=audio_file
    )
    return transcript.text
```

**TTS (Text-to-Speech):**
```python
async def text_to_speech(text: str, output_path: str, voice: str) -> bool:
    # Uses OpenAI TTS API
    response = openai_client.audio.speech.create(
        model="tts-1",
        voice=voice,
        input=text
    )
    response.stream_to_file(output_path)
```

**Intent Detection:**
- affirmative (yes, yeah, yep)
- negative (no, nope)
- skip (skip, next, later)
- clarify (repeat, again, what)

---

### 6. API Routes

**Location:** `app/api/routes/`

#### Authentication (`auth.py`)
- POST `/api/auth/register` - Register user
- POST `/api/auth/login` - Login (JWT)
- GET `/api/auth/me` - Current user

#### Projects (`projects.py`)
- GET `/api/projects/` - List projects
- POST `/api/projects/` - Create project
- POST `/api/projects/{id}/upload-checklist` - Upload Excel
- GET/PUT/DELETE `/api/projects/{id}` - CRUD

#### Reviews (`reviews.py`)
- GET `/api/reviews/` - List reviews
- POST `/api/reviews/` - Create review
- POST `/api/reviews/{id}/start` - Start agent
- POST `/api/reviews/{id}/respond` - Submit response
- POST `/api/reviews/{id}/voice-response` - Submit voice
- POST `/api/reviews/{id}/complete` - Complete review

#### Reports (`reports.py`)
- GET `/api/reports/` - List reports
- GET `/api/reports/{id}` - Get report
- GET `/api/reports/{id}/download/{format}` - Download
- POST `/api/reports/{id}/approve` - Approve
- POST `/api/reports/{id}/reject` - Reject
- GET `/api/reports/pending/approvals` - Pending

#### Checklists (`checklists.py`)
- GET `/api/checklists/{id}` - Get checklist
- POST `/api/checklists/{id}/optimize` - Optimize
- GET `/api/checklists/templates/global` - Templates
- POST `/api/checklists/templates/use/{id}` - Use template

---

### 7. Database Models

**Location:** `app/models.py`

**Tables:**
1. **Users** - Authentication and authorization
2. **Projects** - Project information
3. **Checklists** - Checklist templates
4. **ChecklistItems** - Individual questions
5. **Reviews** - Review sessions
6. **ReviewResponses** - Question responses
7. **Reports** - Generated reports
8. **ReportApprovals** - Approval tracking

See: [../database/schema.md](../database/schema.md)

---

### 8. Configuration

**Location:** `app/core/config.py`

**Settings:**
```python
class Settings(BaseSettings):
    APP_NAME: str = "AI Tech & Delivery Review Agent"
    DATABASE_URL: str = "sqlite+aiosqlite:///./reviews.db"
    OPENAI_API_KEY: Optional[str] = None
    SECRET_KEY: str = "change-this"
    VOICE_ENABLED: bool = True
    REQUIRE_HUMAN_APPROVAL: bool = True
```

---

## Component Interactions

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP
       ▼
┌─────────────┐     ┌─────────────┐
│  API Routes │────▶│  Services   │
└──────┬──────┘     └──────┬──────┘
       │                   │
       │                   │ SQLAlchemy
       ▼                   ▼
┌─────────────┐     ┌─────────────┐
│   Agent     │     │  Database   │
│  (LangGraph)│     │  (SQLite)   │
└──────┬──────┘     └─────────────┘
       │
       │ OpenAI API
       ▼
┌─────────────┐
│   Voice     │
│  Interface  │
└─────────────┘
```

---

*Last Updated: 2026-03-25*
