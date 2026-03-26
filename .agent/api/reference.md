# API Reference

Complete API documentation for AI Tech & Delivery Review Agent.

**Base URL:** `http://localhost:8000`  
**API Docs:** `http://localhost:8000/docs`  
**Version:** 1.0.0

---

## Authentication

### Register User

```http
POST /api/auth/register
Content-Type: application/x-www-form-urlencoded
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| email | string | Yes | User email |
| password | string | Yes | Password (min 8 chars) |
| full_name | string | Yes | Display name |
| role | string | No | reviewer/manager/admin (default: reviewer) |

**Response:**
```json
{
  "message": "User created successfully",
  "user_id": 1,
  "email": "user@example.com"
}
```

---

### Login

```http
POST /api/auth/login
Content-Type: application/x-www-form-urlencoded
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| username | string | Yes | Email address |
| password | string | Yes | Password |

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

**Usage:**
```bash
curl -X POST "http://localhost:8000/api/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=user@example.com&password=securepass123"
```

---

### Get Current User

```http
GET /api/auth/me
Authorization: Bearer <token>
```

**Response:**
```json
{
  "email": "user@example.com",
  "full_name": "John Doe",
  "role": "reviewer"
}
```

---

## Projects

### List Projects

```http
GET /api/projects/?skip=0&limit=100&status=active
```

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| skip | int | 0 | Pagination offset |
| limit | int | 100 | Max results |
| status | string | - | Filter by status (active/completed/on_hold) |

**Response:**
```json
{
  "projects": [
    {
      "id": 1,
      "name": "NeuMoney Platform",
      "domain": "fintech",
      "status": "active",
      "created_at": "2026-03-25T10:00:00"
    }
  ],
  "total": 1
}
```

---

### Get Project

```http
GET /api/projects/{project_id}
```

**Response:**
```json
{
  "id": 1,
  "name": "NeuMoney Platform",
  "domain": "fintech",
  "description": "Digital payment processing platform",
  "tech_stack": ["Java", "Spring Boot", "PostgreSQL", "AWS"],
  "stakeholders": {
    "product_owner": "John",
    "tech_lead": "Sanju"
  },
  "status": "active",
  "start_date": "2026-01-01T00:00:00",
  "end_date": null
}
```

---

### Create Project

```http
POST /api/projects/
Content-Type: multipart/form-data
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| name | string | Yes | Project name |
| domain | string | No | fintech/healthcare/ecommerce/etc |
| description | string | No | Project description |
| tech_stack | string (JSON) | No | Array of technologies |
| stakeholders | string (JSON) | No | Object with roles/names |
| status | string | No | active/completed/on_hold |

**Example:**
```bash
curl -X POST "http://localhost:8000/api/projects/" \
  -F "name=NeuMoney Platform" \
  -F "domain=fintech" \
  -F "description=Digital payment platform" \
  -F 'tech_stack=["Java", "Spring Boot"]' \
  -F 'stakeholders={"tech_lead": "Sanju"}'
```

---

### Upload Checklist

```http
POST /api/projects/{project_id}/upload-checklist
Content-Type: multipart/form-data
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | file | Yes | Excel file (.xlsx) |

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

## Reviews

### Create Review

```http
POST /api/reviews/
Content-Type: application/json
```

**Request Body:**
```json
{
  "project_id": 1,
  "checklist_id": 1,
  "title": "Q1 2026 Technical Review",
  "voice_enabled": true,
  "participants": ["Sanju", "Chakravarthy"]
}
```

**Response:**
```json
{
  "message": "Review created successfully",
  "review_id": 1,
  "project_name": "NeuMoney Platform",
  "checklist_name": "Technical Check List"
}
```

---

### Start Review Agent

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

---

### Submit Response (Text)

```http
POST /api/reviews/{review_id}/respond
Content-Type: application/json
```

**Request Body:**
```json
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
    "question": "Are change requests managed?",
    "area": "Scope, Planning & Governance"
  },
  "progress": "1/35"
}
```

---

### Submit Response (Voice)

```http
POST /api/reviews/{review_id}/voice-response
Content-Type: multipart/form-data
```

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| file | file | Yes | Audio file (WAV recommended) |

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

---

### Complete Review

```http
POST /api/reviews/{review_id}/complete
```

**Response:**
```json
{
  "message": "Review completed",
  "review_id": 1,
  "status": "pending_approval",
  "next_step": "Report generated and awaiting human approval"
}
```

---

## Reports

### List Reports

```http
GET /api/reports/?project_id=1&approval_status=pending
```

**Response:**
```json
{
  "reports": [
    {
      "id": 1,
      "review_id": 1,
      "project_name": "NeuMoney Platform",
      "overall_rag_status": "amber",
      "compliance_score": 72.5,
      "approval_status": "pending",
      "created_at": "2026-03-25T10:30:00"
    }
  ]
}
```

---

### Get Report

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
    "Document architectural decisions and trade-offs"
  ],
  "action_items": [
    {
      "item": "Document ADRs",
      "owner": "Sanju",
      "due_date": "2026-03-30",
      "priority": "High"
    }
  ],
  "approval_status": "pending"
}
```

---

### Get Pending Approvals

```http
GET /api/reports/pending/approvals
```

**Response:**
```json
{
  "pending_reports": [
    {
      "id": 1,
      "project_name": "NeuMoney Platform",
      "compliance_score": 72.5,
      "overall_rag": "amber"
    }
  ],
  "total_pending": 1
}
```

---

### Approve Report

```http
POST /api/reports/{report_id}/approve
Content-Type: application/json
```

**Request Body:**
```json
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

---

### Reject Report

```http
POST /api/reports/{report_id}/reject
Content-Type: application/json
```

**Request Body:**
```json
{
  "approver_id": 1,
  "comments": "Please add more details on security architecture gaps."
}
```

**Response:**
```json
{
  "message": "Report rejected - revision requested",
  "report_id": 1,
  "comments": "Please add more details on security architecture gaps.",
  "next_step": "Review needs to be revised and resubmitted"
}
```

---

### Download Report

```http
GET /api/reports/{report_id}/download/markdown
GET /api/reports/{report_id}/download/pdf
```

**Response:** File download

---

## Checklists

### Get Checklist

```http
GET /api/checklists/{checklist_id}?include_items=true
```

**Response:**
```json
{
  "id": 1,
  "name": "Technical Check List",
  "type": "technical",
  "version": "1.0",
  "is_global": false,
  "items": [
    {
      "id": 1,
      "item_code": "1.10",
      "area": "Architecture & Design",
      "question": "Who is responsible for architecture?",
      "weight": 1.0
    }
  ],
  "items_count": 52
}
```

---

### Optimize Checklist

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

---

### Get Recommendations

```http
GET /api/checklists/{checklist_id}/recommendations
```

**Response:**
```json
{
  "checklist_id": 1,
  "recommendations": [
    {
      "id": 1,
      "type": "add_item",
      "description": "Are PCI-DSS compliance requirements identified?",
      "rationale": "Critical for fintech domain",
      "priority": "high",
      "confidence_score": 0.9,
      "status": "pending"
    }
  ]
}
```

---

## Error Responses

### 400 Bad Request

```json
{
  "detail": "Invalid input"
}
```

### 401 Unauthorized

```json
{
  "detail": "Could not validate credentials",
  "headers": {
    "WWW-Authenticate": "Bearer"
  }
}
```

### 404 Not Found

```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error

```json
{
  "detail": "Internal server error"
}
```

---

## Rate Limiting

Default rate limits:
- Authentication: 10 requests/minute
- File uploads: 5 requests/minute
- General API: 100 requests/minute

---

*Last Updated: 2026-03-25*
