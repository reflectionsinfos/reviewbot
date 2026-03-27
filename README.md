# AI Tech & Delivery Review Agent

A conversational, voice-based AI agent for conducting comprehensive technical and delivery project reviews.

## 🎯 Overview

This AI agent acts as an expert team member who knows everything about your projects - from domain functionality and coding practices to testing, delivery, and stakeholder management. After each review, it generates comprehensive reports showing what's being followed and what needs improvement.

### Key Features

- **🎤 Voice-Based Interaction**: Conduct reviews using natural voice conversations
- **📋 Checklist Management**: Parse Excel checklists and generate AI-powered recommendations
- **🤖 AI-Powered Agent**: LangGraph-based workflow for intelligent review orchestration
- **📊 Compliance Scoring**: Automatic RAG (Red/Amber/Green) status and compliance calculation
- **📝 Report Generation**: Markdown and PDF reports with actionable insights
- **🔐 Human Approval Workflow**: No report is sent without human boss approval
- **🧠 Domain Awareness**: Adapts checklists based on project domain (fintech, healthcare, etc.)

---

## 📚 Documentation

### Quick Links

| Audience | Documentation | Description |
|----------|---------------|-------------|
| **Everyone** | [`docs/`](docs/) | Documentation hub with all guides |
| **New Users** | [`docs/external/getting-started.md`](docs/external/getting-started.md) | Getting started guide |
| **Users** | [`docs/external/workflows/`](docs/external/workflows/) | Step-by-step workflows |
| **Developers** | [`docs/internal/`](docs/internal/) | Developer documentation |
| **DevOps** | [`docs/internal/deployment/`](docs/internal/deployment/) | Deployment guides |
| **API Consumers** | [`docs/api/`](docs/api/) | API documentation |

### Documentation Categories

- **📖 External Docs** (`docs/external/`) - For end users, PMs, stakeholders
- **🔒 Internal Docs** (`docs/internal/`) - For developers, DevOps, maintainers
- **🔌 API Docs** (`docs/api/`) - For API consumers and integrators

### AI/LLM Context

- **Full Context:** [`llms.txt`](llms.txt) - Complete project context for AI agents
- **Public Context:** [`llms-public.txt`](llms-public.txt) - Public-only context (no secrets)
- **Qwen Config:** [`.qwen/`](.qwen/) - Qwen AI configuration and skills
- **Claude Config:** [`.claude/`](.claude/) - Claude AI configuration and skills
- **Generic Agent:** [`.agent/`](.agent/) - Generic AI agent configuration

---

## 🏗️ Architecture

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Backend                        │
├─────────────────────────────────────────────────────────────┤
│  API Routes                                                 │
│  ├── /api/auth      - Authentication & Users               │
│  ├── /api/projects  - Project Management                   │
│  ├── /api/checklists - Checklist Templates & Optimization  │
│  ├── /api/reviews   - Review Sessions                      │
│  └── /api/reports   - Reports & Approvals                  │
├─────────────────────────────────────────────────────────────┤
│  Services                                                   │
│  ├── ChecklistParser    - Excel file parsing               │
│  ├── ChecklistOptimizer - AI recommendations               │
│  ├── ReviewAgent        - LangGraph workflow               │
│  ├── ReportGenerator    - Markdown/PDF generation          │
│  └── VoiceInterface     - STT/TTS (Whisper, OpenAI)        │
├─────────────────────────────────────────────────────────────┤
│  Database (SQLite/PostgreSQL)                               │
│  ├── Projects, Checklists, ChecklistItems                  │
│  ├── Reviews, ReviewResponses                              │
│  ├── Reports, ReportApprovals                              │
│  └── Users                                                  │
└─────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Prerequisites

- **Docker Desktop** (Windows/Mac) or Docker + Docker Compose (Linux)
- **OpenAI API Key** (for LLM and voice features)

---

### Option 1: Docker (Recommended) ⭐

**Perfect for Windows 11 with Docker Desktop**

#### Step 1: Clone and Configure

```bash
# Navigate to project
cd c:\projects\reviewbot

# Copy environment template
copy .env.docker .env

# Edit .env and add your API keys
notepad .env
```

**Required environment variables:**
```env
# OpenAI API Key (REQUIRED)
OPENAI_API_KEY=sk-your-actual-api-key-here

# Database (PostgreSQL)
DATABASE_URL="postgresql+asyncpg://review_user:review_password_change_me@localhost:5432/reviews_db"

# Security (CHANGE IN PRODUCTION!)
SECRET_KEY=your-super-secret-key-change-this
```

#### Step 2: Start Docker Containers

```bash
# Development mode (with pgAdmin tools)
docker-compose --profile tools up --build

# Or run in background
docker-compose --profile tools up -d --build
```

#### Step 3: Setup Database

**Windows (PowerShell):**
```bash
# Run database setup script
.\scripts\setup-database.ps1
```

**Manual setup:**
```bash
# Wait for PostgreSQL to be ready
docker-compose logs db

# Run migrations
docker-compose exec app alembic upgrade head

# Verify tables created (should show 21 tables)
docker-compose exec db psql -U review_user -d reviews_db -c "\dt"
```

#### Step 4: Verify Setup

```bash
# Check all services are running
docker-compose ps

# Test health endpoint
curl http://localhost:8000/health

# Expected response:
# {"status":"healthy","database":"connected","voice_enabled":true}
```

#### Step 5: Access Services

| Service | URL | Credentials |
|---------|-----|-------------|
| **API** | http://localhost:8000 | - |
| **API Docs** | http://localhost:8000/docs | - |
| **pgAdmin** | http://localhost:5050 | admin@example.com / admin_change_me |

---

### Quick Commands

```bash
# Start all services
docker-compose --profile tools up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f app
docker-compose logs -f db

# Open shell in app container
docker-compose exec app bash

# Run database migrations
docker-compose exec app alembic upgrade head

# Run tests
docker-compose exec app pytest tests/ -v

# Reset database (WARNING: deletes all data!)
docker-compose down -v
docker-compose up -d db
docker-compose exec app alembic upgrade head
```

---

### Troubleshooting

**Issue: Port already in use**
```bash
# Check what's using the port
netstat -ano | findstr :8000
netstat -ano | findstr :5435

# Stop conflicting service or change port in .env
APP_PORT=8001
DB_PORT=5433
```

**Issue: Database connection failed**
```bash
# Check database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Restart database
docker-compose restart db
```

**Issue: Migration failed**
```bash
# Check current migration version
docker-compose exec app alembic current

# Rollback and retry
docker-compose exec app alembic downgrade -1
docker-compose exec app alembic upgrade head
```

---

See [DOCKER_GUIDE.md](DOCKER_GUIDE.md) for complete Docker documentation.

---

### Option 2: Local Python Installation

#### Prerequisites

- Python 3.10+
- OpenAI API Key (for LLM and voice features)
- (Optional) ElevenLabs API Key (for advanced TTS)

#### Installation

1. **Clone or navigate to the project directory**
   ```bash
   cd c:\projects\project-reviews
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # Linux/Mac
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment**
   ```bash
   copy .env.example .env
   ```
   
   Edit `.env` and add your API keys:
   ```env
   OPENAI_API_KEY=sk-your-key-here
   DATABASE_URL="sqlite+aiosqlite:///./reviews.db"
   SECRET_KEY=your-secret-key-change-in-production
   ```

5. **Create required directories**
   ```bash
   mkdir uploads reports chroma_db
   ```

6. **Run the application**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

7. **Access the API**
   - API Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/health

---

## 📖 Usage Guide

### 1. Create a Project

```bash
curl -X POST "http://localhost:8000/api/projects/" \
  -F "name=NeuMoney Platform" \
  -F "domain=fintech" \
  -F "description=Digital payment processing platform" \
  -F "status=active"
```

### 2. Upload Checklist

Upload your Excel checklist file:

```bash
curl -X POST "http://localhost:8000/api/projects/{project_id}/upload-checklist" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@Project Review Check List V 1.0.xlsx"
```

### 3. Create Review Session

```bash
curl -X POST "http://localhost:8000/api/reviews/" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "checklist_id": 1,
    "title": "Q1 2026 Technical Review",
    "voice_enabled": true,
    "participants": ["Sanju", "Chakravarthy"]
  }'
```

### 4. Start AI Review Agent

```bash
curl -X POST "http://localhost:8000/api/reviews/{review_id}/start"
```

The agent will:
1. Load the checklist
2. Analyze project domain
3. Suggest checklist enhancements (optional)
4. Begin asking questions one by one

### 5. Submit Responses

**Text Response:**
```bash
curl -X POST "http://localhost:8000/api/reviews/{review_id}/respond" \
  -H "Content-Type: application/json" \
  -d '{
    "question_index": 0,
    "answer": "Yes, all baselines are signed off and tracked in Jira",
    "comments": "See project charter v2.1"
  }'
```

**Voice Response:**
```bash
curl -X POST "http://localhost:8000/api/reviews/{review_id}/voice-response" \
  -F "file=@response.wav"
```

### 6. Complete Review & Generate Report

```bash
curl -X POST "http://localhost:8000/api/reviews/{review_id}/complete"
```

### 7. Human Approval Workflow

The report is generated but **requires approval** before distribution:

```bash
# View pending approvals
curl "http://localhost:8000/api/reports/pending/approvals"

# Approve report
curl -X POST "http://localhost:8000/api/reports/{report_id}/approve" \
  -H "Content-Type: application/json" \
  -d '{
    "approver_id": 1,
    "comments": "Comprehensive review. Approved for distribution."
  }'

# Reject for revision
curl -X POST "http://localhost:8000/api/reports/{report_id}/reject" \
  -H "Content-Type: application/json" \
  -d '{
    "approver_id": 1,
    "comments": "Please add more details on security architecture gaps."
  }'
```

### 8. Download Report

```bash
# Markdown format
curl "http://localhost:8000/api/reports/{report_id}/download/markdown" \
  -o report.md

# PDF format
curl "http://localhost:8000/api/reports/{report_id}/download/pdf" \
  -o report.pdf
```

---

## 🧠 AI Agent Workflow

The review agent uses LangGraph for workflow orchestration:

```
┌─────────────────┐
│   Initialize    │
│  Review Session │
└────────┬────────┘
         │
         ▼
┌─────────────────┐     Yes
│  Optimize       │──────┐
│  Checklist?     │      │
└────────┬────────┘      │
         │ No            ▼
         │        ┌──────────────┐
         │        │  AI-powered  │
         │        │  Recommendations │
         │        └──────┬───────┘
         ▼               │
┌─────────────────┐     │
│  Ask Question   │◄────┘
│  (one at a time)│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Process        │
│  Response       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Assess RAG     │
│  Status         │
└────────┬────────┘
         │
         ▼
    More Questions?
    ┌───Yes───┐
    │         ▼
    │   (loop back)
    │
    No
    │
    ▼
┌─────────────────┐
│  Generate       │
│  Report         │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Request Human  │
│  Approval       │
└─────────────────┘
```

---

## 📊 RAG Assessment Guidelines

The agent automatically assesses responses:

| Status | Score | Criteria |
|--------|-------|----------|
| 🟢 **Green** | 100% | Fully compliant, evidence provided |
| 🟡 **Amber** | 50% | Partially compliant, minor gaps |
| 🔴 **Red** | 0% | Not compliant, significant gaps |
| ⚪ **NA** | - | Not applicable to this project |

**Compliance Score Calculation:**
```
Score = (Sum of weighted RAG scores) / (Total weight)
```

**Overall RAG:**
- 🟢 Green: Score ≥ 80%
- 🟡 Amber: Score 50-79%
- 🔴 Red: Score < 50%

---

## 🔧 Domain-Specific Enhancements

The agent suggests additional checklist items based on domain:

### Fintech
- PCI-DSS compliance checks
- SOX compliance for financial reporting
- Fraud detection mechanisms
- Transaction audit trails

### Healthcare
- HIPAA compliance validation
- PHI encryption and access controls
- Patient safety risk assessment
- HL7/FHIR integration checks

### E-commerce
- Peak load testing (Black Friday scenarios)
- Inventory consistency across channels
- Checkout flow optimization
- Payment gateway security

### Data Migration
- Cutover planning with rollback
- Data reconciliation processes
- Legacy component containment
- Data quality validation

---

## 🗄️ Database Schema

### Key Tables

**Projects**
- id, name, domain, description, tech_stack, stakeholders, status

**Checklists**
- id, name, type (delivery/technical), version, project_id, is_global

**ChecklistItems**
- id, checklist_id, item_code, area, question, weight, is_required

**Reviews**
- id, project_id, checklist_id, status, voice_enabled, conducted_by

**ReviewResponses**
- id, review_id, checklist_item_id, answer, comments, rag_status

**Reports**
- id, review_id, compliance_score, overall_rag_status, approval_status

**ReportApprovals**
- id, report_id, approver_id, status, comments, decided_at

---

## 🔐 Security

### Authentication

The API uses JWT (JSON Web Tokens) for authentication:

```bash
# Login
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@example.com&password=yourpassword"

# Use token in subsequent requests
curl "http://localhost:8000/api/projects/" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Best Practices

1. **Change the default SECRET_KEY** in `.env`
2. **Use HTTPS** in production
3. **Enable CORS** only for trusted domains
4. **Rotate API keys** regularly
5. **Audit log** all approval decisions

---

## 🧪 Testing

Run tests with pytest:

```bash
pytest tests/ -v --cov=app
```

### Sample Test Cases

```python
# tests/test_checklist_parser.py
def test_parse_delivery_checklist():
    parser = ChecklistParser("test_file.xlsx")
    items = parser.parse_delivery_checklist()
    assert len(items) > 0
    assert items[0]["question"] is not None

# tests/test_report_generator.py
def test_calculate_compliance_score():
    generator = ReportGenerator()
    responses = [
        {"rag_status": "green", "weight": 1.0},
        {"rag_status": "red", "weight": 1.0},
        {"rag_status": "green", "weight": 1.0}
    ]
    score = generator.calculate_compliance_score(responses, [])
    assert score == 66.67  # 2 green, 1 red
```

---

## 📦 API Reference

### Projects

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/projects/` | List all projects |
| GET | `/api/projects/{id}` | Get project details |
| POST | `/api/projects/` | Create project |
| PUT | `/api/projects/{id}` | Update project |
| DELETE | `/api/projects/{id}` | Delete project |
| POST | `/api/projects/{id}/upload-checklist` | Upload Excel checklist |

### Reviews

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/reviews/` | List reviews |
| GET | `/api/reviews/{id}` | Get review details |
| POST | `/api/reviews/` | Create review |
| POST | `/api/reviews/{id}/start` | Start AI agent |
| POST | `/api/reviews/{id}/respond` | Submit response |
| POST | `/api/reviews/{id}/voice-response` | Submit voice response |
| POST | `/api/reviews/{id}/complete` | Complete & generate report |

### Reports

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/reports/` | List reports |
| GET | `/api/reports/{id}` | Get report details |
| GET | `/api/reports/{id}/download/{format}` | Download report |
| POST | `/api/reports/{id}/approve` | Approve report |
| POST | `/api/reports/{id}/reject` | Reject report |
| GET | `/api/reports/pending/approvals` | Get pending approvals |

---

## 🛠️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key for LLM & voice | Required |
| `ELEVENLABS_API_KEY` | ElevenLabs API key (optional TTS) | - |
| `DATABASE_URL` | Database connection string | SQLite |
| `SECRET_KEY` | JWT signing key | Change in prod! |
| `VOICE_ENABLED` | Enable voice features | `true` |
| `REQUIRE_HUMAN_APPROVAL` | Require approval before sending reports | `true` |
| `CHROMA_PERSIST_DIR` | Vector DB storage path | `./chroma_db` |

---

## 🚀 Deployment

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Production Checklist

- [ ] Use PostgreSQL instead of SQLite
- [ ] Configure proper CORS origins
- [ ] Enable HTTPS/TLS
- [ ] Set up logging and monitoring
- [ ] Configure backup strategy
- [ ] Set up CI/CD pipeline
- [ ] Add rate limiting
- [ ] Enable audit logging

---

## 📝 Example Report Output

```markdown
# Project Review Report

## Executive Summary
- **Project:** NeuMoney Platform
- **Review Date:** 2026-03-25
- **Overall RAG Status:** 🟡 AMBER
- **Compliance Score:** 72.5%
- **Participants:** Sanju, Chakravarthy

---

## 🟢 Areas Followed Well

✅ Scope / SoW / baselines clearly defined and signed off
✅ Governance cadence followed (status reviews, steering committee)
✅ Project risks logged with owners and mitigations
✅ Team morale and collaboration reported as Good

---

## 🔴 Gaps Identified

🔴 **Architectural Decisions Not Documented**
   ADRs need to be documented for key technology choices

🟡 **Deployment Documentation Incomplete**
   LLD need to be updated with 14 months retention instead of 90 days

🔴 **Indexing Strategy Not Defined**
   Partitioning and sharding strategies not adequate for expected scale

---

## 💡 Recommendations

1. Document architectural decisions and trade-offs (High Priority)
2. Update deployment validation procedures
3. Define database scaling strategy
4. Add fintech-specific security checklist items

---

## 📋 Action Items

| Item | Owner | Due Date | Priority |
|------|-------|----------|----------|
| Document ADRs | Sanju | 30-Mar | High |
| Update LLD retention policy | Chakravarthy | 05-Apr | Medium |
| Define indexing strategy | DBA Team | 10-Apr | High |
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## 📄 License

This project is proprietary software. All rights reserved.

---

## 📞 Support

For issues, questions, or feature requests, please contact the development team.

---

*Built with ❤️ using FastAPI, LangGraph, and OpenAI*
