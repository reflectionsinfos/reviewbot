# AI Tech & Delivery Review Agent - Quick Reference

## 🚀 Quick Start Commands

```bash
# Setup
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python setup.py

# Run server
uvicorn main:app --reload

# Test
pytest tests/ -v
```

---

## 📡 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login (returns JWT token) |
| GET | `/api/auth/me` | Get current user |

### Projects
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/projects/` | List projects |
| GET | `/api/projects/{id}` | Get project |
| POST | `/api/projects/` | Create project |
| POST | `/api/projects/{id}/upload-checklist` | Upload Excel |
| DELETE | `/api/projects/{id}` | Delete project |

### Reviews
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/reviews/` | List reviews |
| POST | `/api/reviews/` | Create review |
| POST | `/api/reviews/{id}/start` | Start AI agent |
| POST | `/api/reviews/{id}/respond` | Submit answer |
| POST | `/api/reviews/{id}/voice-response` | Submit audio |
| POST | `/api/reviews/{id}/complete` | Generate report |

### Reports
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/reports/` | List reports |
| GET | `/api/reports/{id}` | Get report |
| GET | `/api/reports/pending/approvals` | Pending approvals |
| POST | `/api/reports/{id}/approve` | Approve report |
| POST | `/api/reports/{id}/reject` | Reject report |
| GET | `/api/reports/{id}/download/{format}` | Download |

---

## 🔑 Key Configuration (.env)

```env
OPENAI_API_KEY=sk-...              # Required
DATABASE_URL=sqlite+aiosqlite:///./reviews.db
SECRET_KEY=change-in-production    # Change!
VOICE_ENABLED=true
REQUIRE_HUMAN_APPROVAL=true
```

---

## 📊 RAG Status Rules

| Answer Keywords | RAG Status | Score |
|----------------|------------|-------|
| yes, yeah, yep, done | 🟢 Green | 100 |
| partial, in progress, working | 🟡 Amber | 50 |
| no, nope, missing, not done | 🔴 Red | 0 |

**Overall RAG:**
- ≥80% → 🟢 Green
- 50-79% → 🟡 Amber
- <50% → 🔴 Red

---

## 🧠 Agent Workflow

```
Start → Initialize → [Optimize Checklist?] → Ask Question → Process Response → Assess RAG
   ↓
More Questions? → Yes → Ask Question (loop)
   ↓ No
Generate Report → Request Approval → End
```

---

## 📁 Project Structure

```
project-reviews/
├── main.py                    # FastAPI app entry
├── requirements.txt           # Python dependencies
├── setup.py                   # Setup script
├── .env.example              # Environment template
├── app/
│   ├── agents/               # AI agent (LangGraph)
│   │   ├── review_agent.py
│   │   └── states.py
│   ├── api/routes/           # API endpoints
│   │   ├── auth.py
│   │   ├── projects.py
│   │   ├── reviews.py
│   │   ├── checklists.py
│   │   └── reports.py
│   ├── core/                 # Configuration
│   │   └── config.py
│   ├── db/                   # Database
│   │   └── session.py
│   ├── services/             # Business logic
│   │   ├── checklist_parser.py
│   │   ├── checklist_optimizer.py
│   │   ├── report_generator.py
│   │   └── voice_interface.py
│   └── models.py             # SQLAlchemy models
├── tests/                    # Test suite
├── uploads/                  # File uploads
├── reports/                  # Generated reports
└── chroma_db/                # Vector database
```

---

## 🔐 Default Credentials (Demo)

```
Email: admin@example.com
Password: admin123
⚠️ Change immediately in production!
```

---

## 📝 Example cURL Commands

### Create Project
```bash
curl -X POST "http://localhost:8000/api/projects/" \
  -F "name=My Project" \
  -F "domain=fintech"
```

### Start Review
```bash
curl -X POST "http://localhost:8000/api/reviews/" \
  -H "Content-Type: application/json" \
  -d '{"project_id": 1, "checklist_id": 1}'
```

### Submit Response
```bash
curl -X POST "http://localhost:8000/api/reviews/1/respond" \
  -H "Content-Type: application/json" \
  -d '{"question_index": 0, "answer": "Yes"}'
```

### Approve Report
```bash
curl -X POST "http://localhost:8000/api/reports/1/approve" \
  -H "Content-Type: application/json" \
  -d '{"approver_id": 1, "comments": "Approved"}'
```

---

## 🛠️ Troubleshooting

| Issue | Solution |
|-------|----------|
| Database not found | Run `python setup.py` |
| OpenAI errors | Check API key in `.env` |
| Voice fails | Verify WAV format, <25MB |
| PDF generation fails | `pip install reportlab` |
| Import errors | `pip install -r requirements.txt` |

---

## 📚 Documentation

- `README.md` - Full documentation
- `WORKFLOWS.md` - Step-by-step workflows
- `http://localhost:8000/docs` - Interactive API docs

---

## 🎯 Domain-Specific Checklists

| Domain | Additional Checks |
|--------|------------------|
| Fintech | PCI-DSS, SOX, fraud detection |
| Healthcare | HIPAA, PHI encryption, audit logs |
| E-commerce | Peak load, inventory consistency |
| Data Migration | Cutover plan, rollback, reconciliation |
| AI/ML | Model governance, bias testing, drift detection |

---

*For detailed information, see README.md and WORKFLOWS.md*
