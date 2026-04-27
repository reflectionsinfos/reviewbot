# ReviewBot — Review Agent Workflow & RAG Assessment

> Reference for the LangGraph-based conversational review agent.
> Last updated: 2026-04-27

---

## LangGraph Review Agent

The conversational review agent is implemented as a LangGraph state machine in `app/agents/review_agent/`.

### State (ReviewState TypedDict)

```python
class ReviewState(TypedDict):
    review_id: int
    project_id: int
    checklist_id: int
    current_item_index: int
    checklist_items: List[dict]
    conversation_history: List[dict]
    responses: List[dict]
    review_complete: bool
    report_data: Optional[dict]
    current_question: Optional[str]
    awaiting_response: bool
```

### Workflow Graph

```
START → initialize_review
           │
           ▼
        ask_question ←──────────────┐
           │                        │
           ▼                        │
        process_response            │
           │                        │
           ▼                        │
        assess_rag                  │
           │                        │
           ├─── more_items ─────────┘
           │
           └─── all_done
                    │
                    ▼
             generate_report
                    │
                    ▼
                  END
```

### Node Functions (`agent.py`)

| Node | Action |
|------|--------|
| `initialize_review` | Load checklist items, set `current_item_index = 0` |
| `ask_question` | Retrieve current checklist item, generate contextual question using LLM, set `awaiting_response = True` |
| `process_response` | Accept user response text, add to `conversation_history`, mark `awaiting_response = False` |
| `assess_rag` | Use LLM to assess response against `expected_evidence`, assign `rag_status` (red/amber/green/na), advance index |
| `generate_report` | Aggregate all responses, calculate compliance score, generate findings and recommendations |

### Conditional Edge

```python
def should_continue(state: ReviewState) -> str:
    if state["current_item_index"] >= len(state["checklist_items"]):
        return "all_done"
    return "more_items"
```

**Important:** The `generate_report` node parameter must be named `state` (not `ReviewState` or other names) due to LangGraph node signature requirements.

---

## RAG Assessment Logic

### Traffic Light System

| Status | Meaning | Score |
|--------|---------|-------|
| `green` | Compliant — evidence meets expected standard | 1.0 |
| `amber` | Partially compliant — some evidence but gaps | 0.5 |
| `red` | Non-compliant — missing or inadequate evidence | 0.0 |
| `na` | Not applicable — excluded from scoring | excluded |

### Compliance Score Formula

```
compliance_score = sum(weight × points for non-NA items)
                 / sum(weight for non-NA items)

Where points: green=1.0, amber=0.5, red=0.0
```

Stored as a float 0.0–1.0 on the `Report` model (`compliance_score` column).

### Assessment Prompt Pattern

The `assess_rag` node calls the LLM with:
1. The checklist item question
2. The `expected_evidence` field (what good looks like)
3. The reviewer's response text
4. Instructions to classify as green/amber/red/na with reasoning

---

## Report Generation

Reports are generated in two formats via `app/services/report_generator.py`:

1. **Markdown** — human-readable `.md` file with:
   - Project overview
   - Compliance score
   - Item-by-item RAG breakdown
   - Gap analysis (red/amber items)
   - Recommendations

2. **PDF** — generated from Markdown content using ReportLab.
   - Use `Paragraph` with heading styles, **not** `Heading` class (which doesn't exist in ReportLab platypus)

---

## Conversational Review Flow (API)

```
POST /api/reviews/           # Create review (status: pending)
POST /api/reviews/{id}/start # Initialize LangGraph agent (status: in_progress)
                             # Returns: first question
POST /api/reviews/{id}/respond   # Submit answer → get next question
...repeat...
POST /api/reviews/{id}/complete  # Finalize (status: completed)
                                  # Triggers report generation
```

---

## Offline Review Flow (Excel)

```
POST /api/reviews/offline        # Create review + upload_token
                                  # Sends email with Excel + portal link
                                  # (portal_url derived from Request headers)

GET /api/reviews/upload/{token}  # Reviewer downloads pre-filled Excel
POST /api/reviews/upload/{token} # Reviewer uploads completed Excel
                                  # Parses responses → creates ReviewResponses
                                  # Calculates compliance score → creates Report
```

---

## Manual / Self Review Flow (Portal)

```
POST /api/reviews/manual          # Create review + portal_url (no email)
                                   # portal_url = base_url + /manual-review/{id}?token={token}

GET /api/reviews/portal/{id}?token={token}   # Load review in browser
POST /api/reviews/portal/{id}/submit?token={token}  # Submit responses
```

**portal_url uses `_get_base_url(http_request)` — never `settings.APP_BASE_URL`.**

---

## Key Services

### ChecklistService (`app/services/checklist_service.py`)
- `get_global_templates(db, type, organization_id)` — org-scoped template listing
- `get_checklist_with_items(db, checklist_id)` — eager-loads items
- Applies `or_(org_id == None, org_id == user_org)` filter

### Excel Services
- `ChecklistParser` (`checklist_parser.py`) — reads `.xlsx`, expects sheets "Delivery Check List V 1.0" and "Technical Check List V 1.0"
- `ExcelOfflineExporter` (`excel_offline_exporter.py`) — generates reviewer Excel from checklist items
- `ExcelResponseParser` (`excel_response_parser.py`) — parses uploaded completed Excel back into responses

### Email Integration (`app/services/integrations/`)
- `_get_email_integration(db)` — returns first enabled `smtp` or `resend` config
- `email_smtp.py` — SMTP via aiosmtplib; `send_offline_review_email`, `send_summary_email`, `test_connection`
- `email_resend.py` — Resend.com HTTP API; same interface
