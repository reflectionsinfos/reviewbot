# AI Review Agent - Sample Workflows

This document provides example workflows for common use cases.

---

## Workflow 1: First-Time Setup

### Step 1: Install and Configure

```bash
# Navigate to project
cd c:\projects\project-reviews

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run setup script
python setup.py
```

### Step 2: Configure API Key

Edit `.env` file:
```env
OPENAI_API_KEY=sk-your-actual-key-here
```

### Step 3: Start Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Step 4: Verify Setup

Open browser: http://localhost:8000/health

Expected response:
```json
{
  "status": "healthy",
  "database": "connected",
  "voice_enabled": true,
  "human_approval_required": true
}
```

---

## Workflow 2: Upload Existing Excel Checklists

### Step 1: Create Project

```bash
curl -X POST "http://localhost:8000/api/projects/" \
  -F "name=NeuMoney Platform" \
  -F "domain=fintech" \
  -F "description=Digital payment processing platform" \
  -F "tech_stack=[\"Java\", \"Spring Boot\", \"PostgreSQL\", \"AWS\"]" \
  -F "stakeholders={\"product_owner\": \"John\", \"tech_lead\": \"Sanju\"}"
```

Response:
```json
{
  "message": "Project created successfully",
  "project_id": 1,
  "name": "NeuMoney Platform"
}
```

### Step 2: Upload Checklist Excel

```bash
curl -X POST "http://localhost:8000/api/projects/1/upload-checklist" \
  -F "file=@Project Review Check List V 1.0 -Delivery Updated -NeuMoney.xlsx"
```

Response:
```json
{
  "message": "Checklist uploaded and parsed successfully",
  "project_id": 1,
  "checklists": [
    {"id": 1, "type": "delivery", "items_count": 35},
    {"id": 2, "type": "technical", "items_count": 52}
  ],
  "statistics": {
    "file_name": "Project Review Check List V 1.0 -Delivery Updated -NeuMoney.xlsx",
    "sheets": ["Delivery Check List V 1.0", "Technical Check List V 1.0"]
  }
}
```

---

## Workflow 3: Conduct AI-Powered Review

### Step 1: Create Review Session

```bash
curl -X POST "http://localhost:8000/api/reviews/" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "checklist_id": 1,
    "title": "Q1 2026 Delivery Review",
    "voice_enabled": true,
    "participants": ["Sanju", "Chakravarthy", "John"]
  }'
```

### Step 2: Start Review Agent

```bash
curl -X POST "http://localhost:8000/api/reviews/1/start"
```

Response:
```json
{
  "message": "Review session started",
  "review_id": 1,
  "checklist_items_count": 35,
  "voice_enabled": true,
  "first_question": "Are scope / SoW / baselines clearly defined, signed off, and tracked?"
}
```

### Step 3: Submit Responses (Iterate through questions)

**Question 1:**
```bash
curl -X POST "http://localhost:8000/api/reviews/1/respond" \
  -H "Content-Type: application/json" \
  -d '{
    "question_index": 0,
    "answer": "Yes",
    "comments": "All baselines are signed off. Project charter v2.1 approved."
  }'
```

**Question 2:**
```bash
curl -X POST "http://localhost:8000/api/reviews/1/respond" \
  -H "Content-Type: application/json" \
  -d '{
    "question_index": 1,
    "answer": "Yes",
    "comments": "Change requests tracked in Jira. RAID log updated weekly."
  }'
```

**Question 3 (Partial compliance):**
```bash
curl -X POST "http://localhost:8000/api/reviews/1/respond" \
  -H "Content-Type: application/json" \
  -d '{
    "question_index": 2,
    "answer": "Partial",
    "comments": "Project plan is realistic but critical path not communicated to all stakeholders"
  }'
```

### Step 4: Complete Review

```bash
curl -X POST "http://localhost:8000/api/reviews/1/complete"
```

Response:
```json
{
  "message": "Review completed",
  "review_id": 1,
  "status": "pending_approval",
  "next_step": "Report generated and awaiting human approval"
}
```

---

## Workflow 4: Human Approval Process

### Step 1: View Pending Approvals

```bash
curl "http://localhost:8000/api/reports/pending/approvals"
```

Response:
```json
{
  "pending_reports": [
    {
      "id": 1,
      "review_id": 1,
      "project_name": "NeuMoney Platform",
      "compliance_score": 72.5,
      "overall_rag": "amber",
      "created_at": "2026-03-25T10:30:00"
    }
  ],
  "total_pending": 1
}
```

### Step 2: Review Report Details

```bash
curl "http://localhost:8000/api/reports/1"
```

### Step 3A: Approve Report

```bash
curl -X POST "http://localhost:8000/api/reports/1/approve" \
  -H "Content-Type: application/json" \
  -d '{
    "approver_id": 1,
    "comments": "Comprehensive review. Good identification of gaps. Approved for distribution."
  }'
```

### Step 3B: OR Reject for Revision

```bash
curl -X POST "http://localhost:8000/api/reports/1/reject" \
  -H "Content-Type: application/json" \
  -d '{
    "approver_id": 1,
    "comments": "Please add more specific recommendations for the indexing strategy gap. Also include timeline estimates."
  }'
```

### Step 4: Download Approved Report

```bash
# Markdown
curl "http://localhost:8000/api/reports/1/download/markdown" -o report.md

# PDF
curl "http://localhost:8000/api/reports/1/download/pdf" -o report.pdf
```

---

## Workflow 5: Checklist Optimization

### Step 1: Get AI Recommendations

```bash
curl -X POST "http://localhost:8000/api/checklists/1/optimize"
```

Response:
```json
{
  "message": "Generated 6 recommendations",
  "checklist_id": 1,
  "domain": "fintech",
  "recommendations_count": 6
}
```

### Step 2: View Recommendations

```bash
curl "http://localhost:8000/api/checklists/1/recommendations"
```

Response:
```json
{
  "checklist_id": 1,
  "recommendations": [
    {
      "id": 1,
      "type": "add_item",
      "description": "Are PCI-DSS compliance requirements identified and tracked?",
      "rationale": "Critical for fintech domain",
      "priority": "high",
      "confidence_score": 0.9,
      "status": "pending"
    },
    {
      "id": 2,
      "type": "add_item",
      "description": "Is SOX compliance addressed for financial reporting systems?",
      "rationale": "Critical for fintech domain",
      "priority": "high",
      "confidence_score": 0.9,
      "status": "pending"
    }
  ]
}
```

### Step 3: Apply Recommendations (Manual for now)

Review recommendations and manually add relevant items to your checklist.

---

## Workflow 6: Voice-Based Review

### Prerequisites

1. OpenAI API key with Whisper access
2. Audio recording capability

### Step 1: Start Review with Voice Enabled

```bash
curl -X POST "http://localhost:8000/api/reviews/" \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": 1,
    "checklist_id": 1,
    "title": "Voice Review Session",
    "voice_enabled": true
  }'
```

### Step 2: Submit Voice Response

Record your answer (e.g., using phone or microphone) and save as `answer.wav`

```bash
curl -X POST "http://localhost:8000/api/reviews/2/voice-response" \
  -F "file=@answer.wav"
```

Response:
```json
{
  "message": "Voice response processed",
  "file_path": "./uploads/voice/review_2_20260325_103000.wav",
  "transcript": "Yes, we have completed all the security architecture reviews",
  "intent": "affirmative",
  "answer": "Yes, we have completed all the security architecture reviews"
}
```

### Step 3: Confirm and Continue

The transcript is used as the answer. Continue with next question.

---

## Workflow 7: Multi-Project Review Dashboard

### Step 1: List All Projects

```bash
curl "http://localhost:8000/api/projects/"
```

### Step 2: List Reviews for Specific Project

```bash
curl "http://localhost:8000/api/reviews/?project_id=1"
```

### Step 3: Compare Compliance Scores

```bash
# Get all reports for project
curl "http://localhost:8000/api/reports/?project_id=1"

# Compare scores across review cycles
```

Example comparison:
```
Review 1 (Q1 2026): 72.5% - Amber
Review 2 (Q2 2026): 85.0% - Green  ↑ Improvement!
```

---

## Troubleshooting

### Issue: Database not found

```bash
# Run setup again
python setup.py
```

### Issue: OpenAI API errors

Check your API key in `.env`:
```env
OPENAI_API_KEY=sk-valid-key-here
```

### Issue: Voice transcription fails

1. Verify OpenAI API key has Whisper access
2. Check audio file format (WAV recommended)
3. Ensure file size is under 25MB

### Issue: PDF generation fails

Install additional dependencies:
```bash
pip install reportlab
```

---

## Best Practices

1. **Regular Reviews**: Schedule reviews every sprint/quarter
2. **Trend Analysis**: Compare scores across review cycles
3. **Action Item Tracking**: Follow up on gaps identified
4. **Stakeholder Involvement**: Include relevant team members
5. **Documentation**: Keep all evidence and comments
6. **Human Oversight**: Always review AI-generated reports before distribution

---

*For more information, see README.md*
