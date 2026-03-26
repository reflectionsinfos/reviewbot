# Data Flow

## Review Workflow Data Flow

### 1. Project Creation

```
Client ──▶ API ──▶ Database
                    │
                    ▼
              Project Created
              - id: 1
              - name: "NeuMoney"
              - domain: "fintech"
```

**Data:**
```json
{
  "name": "NeuMoney Platform",
  "domain": "fintech",
  "description": "Digital payment platform",
  "tech_stack": ["Java", "Spring Boot", "PostgreSQL"],
  "status": "active"
}
```

---

### 2. Checklist Upload

```
Excel File ──▶ API ──▶ ChecklistParser ──▶ Database
                                              │
                                              ▼
                                        Checklists Created
                                        - Delivery (35 items)
                                        - Technical (52 items)
```

**Data Flow:**
```
1. Upload Excel file
2. Parse sheets:
   - "Delivery Check List V 1.0"
   - "Technical Check List V 1.0"
3. Extract items
4. Store in database
```

**Parsed Output:**
```python
{
  "checklists": {
    "delivery": [
      {
        "item_code": "1.1",
        "area": "Scope, Planning & Governance",
        "question": "Are scope / SoW / baselines clearly defined?"
      }
    ],
    "technical": [...]
  }
}
```

---

### 3. Review Session Creation

```
Client ──▶ API ──▶ Database ──▶ Review Created
                                  │
                                  ▼
                            Review ID: 1
                            Status: draft
```

**Data:**
```json
{
  "project_id": 1,
  "checklist_id": 1,
  "title": "Q1 2026 Technical Review",
  "voice_enabled": true,
  "participants": ["Sanju", "Chakravarthy"]
}
```

---

### 4. Review Agent Execution

```
┌────────────────────────────────────────────────────────────┐
│                    Review Agent State                       │
├────────────────────────────────────────────────────────────┤
│  initialize_review                                          │
│    ↓                                                        │
│  should_optimize_checklist? ──Yes──▶ optimize_checklist    │
│    ↓ No                                                     │
│  ask_question (item 0)                                      │
│    ↓                                                        │
│  process_response (user answer)                             │
│    ↓                                                        │
│  assess_rag_status (auto-score)                             │
│    ↓                                                        │
│  more_questions? ──Yes──▶ ask_question (item 1)             │
│    ↓ No                                                     │
│  generate_report                                            │
│    ↓                                                        │
│  request_approval                                           │
│    ↓                                                        │
│  END                                                        │
└────────────────────────────────────────────────────────────┘
```

**State Transitions:**
```python
# Initial State
{
  "project_id": 1,
  "checklist_items": [...],
  "current_item_index": 0,
  "responses": [],
  "session_status": "draft"
}

# After Question 1
{
  "current_question": "Are scope baselines defined?",
  "conversation_history": [
    {"role": "assistant", "content": "Are scope baselines defined?"}
  ]
}

# After Response 1
{
  "responses": [
    {
      "question": "Are scope baselines defined?",
      "answer": "Yes, all signed off",
      "rag_status": "green"
    }
  ],
  "current_item_index": 1
}

# After All Questions
{
  "compliance_score": 72.5,
  "overall_rag": "amber",
  "report_data": {...},
  "approval_status": "pending"
}
```

---

### 5. Response Submission

#### Text Response

```
Client ──▶ API ──▶ RAG Assessment ──▶ Database
                                        │
                                        ▼
                                  Response Saved
                                  - answer: "Yes"
                                  - rag_status: "green"
```

**Data:**
```json
{
  "question_index": 0,
  "answer": "Yes",
  "comments": "All baselines signed off. Project charter v2.1 approved."
}
```

#### Voice Response

```
Audio File ──▶ API ──▶ VoiceInterface ──▶ Whisper STT ──▶ Transcript
                       │                                      │
                       │                                      ▼
                       │                                Intent Detection
                       │                                      │
                       ▼                                      ▼
                       └──────────▶ Database ◀────────────────┘
                                      │
                                      ▼
                                Response Saved
                                - transcript: "Yes..."
                                - rag_status: "green"
```

---

### 6. Report Generation

```
Agent ──▶ ReportGenerator ──▶ Calculate Score ──▶ Analyze Gaps
               │                                      │
               │                                      ▼
               │                                Generate Action Items
               │                                      │
               ▼                                      ▼
         Markdown Report ◀────────────────────────────┘
               │
               ▼
            PDF Report
```

**Report Data:**
```python
{
  "project_name": "NeuMoney Platform",
  "review_date": "2026-03-25",
  "overall_rag_status": "amber",
  "compliance_score": 72.5,
  "areas_followed": [
    "Scope baselines signed off",
    "Governance cadence followed"
  ],
  "gaps_identified": [
    {
      "title": "ADRs Not Documented",
      "description": "Architectural decisions need documentation",
      "severity": "high"
    }
  ],
  "recommendations": [
    "Document architectural decisions and trade-offs"
  ],
  "action_items": [
    {
      "item": "Document ADRs",
      "owner": "Sanju",
      "due_date": "2026-03-30",
      "priority": "High"
    }
  ]
}
```

---

### 7. Approval Workflow

```
Report Generated
       │
       ▼
┌─────────────┐
│  PENDING    │◀─── Requires Human Approval
└──────┬──────┘
       │
       │ Human Reviews
       │
       ├───Approve───▶ APPROVED ──▶ Report Released
       │
       └───Reject────▶ REJECTED ──▶ Revision Requested
                              │
                              ▼
                       REVISION_REQUESTED
                              │
                              ▼
                       Back to Review
```

**Approval Data:**
```json
{
  "report_id": 1,
  "approver_id": 1,
  "status": "approved",
  "comments": "Comprehensive review. Approved for distribution.",
  "decided_at": "2026-03-25T11:00:00"
}
```

---

## Database Entity Relationships

```
┌─────────────┐       ┌─────────────┐
│    User     │       │   Project   │
│  id, email  │◀──────│  id, name   │
│  role       │       │  domain     │
└─────────────┘       └──────┬──────┘
                             │
                             │ 1:N
                             ▼
                      ┌─────────────┐
                      │  Checklist  │
                      │  id, type   │
                      └──────┬──────┘
                             │
                             │ 1:N
                             ▼
                      ┌─────────────┐
                      │ Checklist   │
                      │    Item     │
                      └─────────────┘

┌─────────────┐       ┌─────────────┐
│   Review    │──────▶│   Report    │
│  id, status │   1:1 │  id, score  │
└──────┬──────┘       └──────┬──────┘
       │                     │
       │ 1:N                 │ 1:N
       ▼                     ▼
┌─────────────┐       ┌─────────────┐
│   Review    │       │   Report    │
│  Response   │       │  Approval   │
└─────────────┘       └─────────────┘
```

---

## API Request/Response Flow

### Create Review

```
POST /api/reviews/
Content-Type: application/json

{
  "project_id": 1,
  "checklist_id": 1,
  "title": "Q1 2026 Review"
}

▼

API Route: reviews.create_review()
  │
  ├─▶ Validate project exists
  ├─▶ Validate checklist exists
  ├─▶ Create Review object
  └─▶ Save to database

▼

Response: 201 Created
{
  "message": "Review created successfully",
  "review_id": 1,
  "project_name": "NeuMoney Platform"
}
```

### Start Review Agent

```
POST /api/reviews/1/start

▼

API Route: reviews.start_review()
  │
  ├─▶ Load review
  ├─▶ Load checklist items
  ├─▶ Load project info
  ├─▶ Initialize agent state
  │   {
  │     "project_id": 1,
  │     "checklist_items": [...],
  │     "current_item_index": 0,
  │     "responses": []
  │   }
  ├─▶ Update review status: "in_progress"
  └─▶ Return first question

▼

Response: 200 OK
{
  "message": "Review session started",
  "checklist_items_count": 35,
  "first_question": "Are scope baselines defined?"
}
```

### Submit Response

```
POST /api/reviews/1/respond
{
  "question_index": 0,
  "answer": "Yes"
}

▼

API Route: reviews.submit_response()
  │
  ├─▶ Load review
  ├─▶ Get checklist item
  ├─▶ Determine RAG status
  │   answer contains "Yes" → rag_status = "green"
  ├─▶ Create ReviewResponse
  └─▶ Save to database

▼

Response: 200 OK
{
  "message": "Response recorded",
  "rag_status": "green",
  "next_question": {
    "index": 1,
    "question": "Are change requests managed?"
  },
  "progress": "1/35"
}
```

---

## File Storage Flow

### Checklist Upload

```
Client Upload
     │
     ▼
┌─────────────┐
│ Temp File   │  (uploads/temp_*.xlsx)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Parse Excel │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Database    │  (Checklists, Items)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Delete Temp │
└─────────────┘
```

### Voice Recording

```
Client Upload (audio.wav)
     │
     ▼
┌─────────────┐
│ Save File   │  (uploads/voice/review_1_*.wav)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Transcribe  │  (Whisper API)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Store       │  (transcript in DB)
└─────────────┘
```

### Report Generation

```
Agent Generates Data
     │
     ▼
┌─────────────┐
│ Markdown    │  (reports/report_1.md)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ PDF         │  (reports/report_1.pdf)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Store Paths │  (in Report record)
└─────────────┘
```

---

*Last Updated: 2026-03-25*
