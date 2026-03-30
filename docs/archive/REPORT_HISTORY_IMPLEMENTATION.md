# Report History & Management - Implementation Plan

> Complete backend and UI specification for report history with override support

**Version:** 1.0  
**Date:** March 27, 2026  
**Status:** Ready for Implementation

---

## 🎯 Requirements

### **UI Requirements:**
1. List all generated reports
2. Show: Project name, Checklist name, Source path (editable), Generated date
3. Regenerate button for each report
4. Override feature for each checklist item in report details

### **Backend Requirements:**
1. API to list all reports with full details
2. API to update source path
3. API to regenerate report
4. API to get report details with override status
5. API to get overrides for specific items

---

## 📊 Database Changes

### **Migration 003: Add Report History Support**

```python
"""Add report history and override support

Revision ID: 003
Revises: 002
Create Date: 2026-03-27

"""
from alembic import op
import sqlalchemy as sa

revision = '003'
down_revision = '002'

def upgrade() -> None:
    # Add autonomous_review_job_id to reports table
    op.add_column('reports', 
                  sa.Column('autonomous_review_job_id', sa.Integer(), 
                           sa.ForeignKey('autonomous_review_jobs.id'), nullable=True))
    
    # Add index for faster lookups
    op.create_index('idx_report_autonomous_job', 'reports', ['autonomous_review_job_id'])


def downgrade() -> None:
    op.drop_index('idx_report_autonomous_job', table_name='reports')
    op.drop_column('reports', 'autonomous_review_job_id')
```

---

## 🔌 API Endpoints

### **1. GET /api/reports/history** - List All Reports

**Request:**
```http
GET /api/reports/history?project_id=1&limit=20&offset=0
```

**Response:**
```json
{
  "total": 45,
  "reports": [
    {
      "id": 1,
      "project_id": 1,
      "project_name": "Hatch Pay",
      "checklist_id": 2,
      "checklist_name": "Hatch Pay — Technical Checklist",
      "source_path": "/host-projects/hatch-pay/backend/hatch-pay-accounting-day-service",
      "generated_at": "2026-03-27T10:30:00",
      "total_items": 103,
      "green_count": 10,
      "amber_count": 0,
      "red_count": 27,
      "compliance_score": 27.0,
      "override_count": 5,
      "adjusted_score": 32.0,
      "status": "completed"
    }
  ]
}
```

---

### **2. PUT /api/reports/{report_id}/source-path** - Update Source Path

**Request:**
```http
PUT /api/reports/1/source-path
Content-Type: application/json

{
  "source_path": "/host-projects/hatch-pay/backend/new-path"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Source path updated successfully",
  "report_id": 1,
  "old_path": "/host-projects/hatch-pay/backend/old-path",
  "new_path": "/host-projects/hatch-pay/backend/new-path"
}
```

---

### **3. POST /api/reports/{report_id}/regenerate** - Regenerate Report

**Request:**
```http
POST /api/reports/1/regenerate
Content-Type: application/json

{
  "use_updated_source_path": true,  // Use the updated path if changed
  "include_overrides": true  // Carry forward previous overrides
}
```

**Response:**
```json
{
  "status": "accepted",
  "message": "Report regeneration started",
  "job_id": 42,
  "report_id": 1,
  "estimated_time_seconds": 120
}
```

---

### **4. GET /api/reports/{report_id}/details** - Get Report with Overrides

**Request:**
```http
GET /api/reports/1/details
```

**Response:**
```json
{
  "report": {
    "id": 1,
    "project_name": "Hatch Pay",
    "checklist_name": "Technical Checklist",
    "source_path": "/host-projects/...",
    "generated_at": "2026-03-27T10:30:00",
    "compliance_score": 27.0,
    "override_count": 5,
    "adjusted_score": 32.0
  },
  "summary": {
    "total": 103,
    "green": 10,
    "amber": 0,
    "red": 27,
    "human_required": 0,
    "na": 66
  },
  "items": [
    {
      "item_id": 1,
      "item_code": "1.2",
      "area": "Architecture",
      "question": "Is the target architecture documented...",
      "rag_status": "red",
      "evidence": "No matching files found...",
      "confidence": 0.95,
      "is_overridden": true,
      "overrides": [
        {
          "override_id": 1,
          "new_rag_status": "green",
          "comments": "We use Confluence for all documentation",
          "reason": "alternative_approach",
          "overridden_by": "Admin User",
          "overridden_at": "2026-03-27T11:00:00"
        }
      ]
    }
  ]
}
```

---

## 🎨 UI Components

### **1. Report History Page**

```javascript
function ReportHistoryPage() {
  const [reports, setReports] = useState([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    fetchReports();
  }, []);
  
  const fetchReports = async () => {
    const response = await fetch('/api/reports/history');
    const data = await response.json();
    setReports(data.reports);
    setLoading(false);
  };
  
  return (
    <div className="report-history">
      <h1>Report History</h1>
      
      {loading ? (
        <LoadingSpinner />
      ) : (
        <ReportTable 
          reports={reports}
          onRegenerate={handleRegenerate}
          onViewDetails={handleViewDetails}
        />
      )}
    </div>
  );
}
```

---

### **2. Report Table Component**

```javascript
function ReportTable({ reports, onRegenerate, onViewDetails }) {
  return (
    <table className="report-table">
      <thead>
        <tr>
          <th>Project</th>
          <th>Checklist</th>
          <th>Source Path</th>
          <th>Generated</th>
          <th>Score</th>
          <th>Overrides</th>
          <th>Actions</th>
        </tr>
      </thead>
      <tbody>
        {reports.map(report => (
          <tr key={report.id}>
            <td>{report.project_name}</td>
            <td>{report.checklist_name}</td>
            <td>
              <EditableSourcePath 
                value={report.source_path}
                reportId={report.id}
                onSave={handleSourcePathUpdate}
              />
            </td>
            <td>{formatDate(report.generated_at)}</td>
            <td>
              <ScoreBadge 
                score={report.compliance_score}
                adjustedScore={report.adjusted_score}
              />
            </td>
            <td>
              {report.override_count > 0 && (
                <OverrideBadge count={report.override_count} />
              )}
            </td>
            <td>
              <button onClick={() => onViewDetails(report.id)}>
                View Details
              </button>
              <button onClick={() => onRegenerate(report.id)}>
                🔄 Regenerate
              </button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

---

### **3. Editable Source Path**

```javascript
function EditableSourcePath({ value, reportId, onSave }) {
  const [editing, setEditing] = useState(false);
  const [path, setPath] = useState(value);
  
  const handleSave = async () => {
    await fetch(`/api/reports/${reportId}/source-path`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source_path: path })
    });
    setEditing(false);
    onSave(reportId, path);
  };
  
  if (editing) {
    return (
      <div className="editable-path">
        <input 
          type="text" 
          value={path}
          onChange={e => setPath(e.target.value)}
          className="path-input"
        />
        <button onClick={handleSave}>💾 Save</button>
        <button onClick={() => setEditing(false)}>❌ Cancel</button>
      </div>
    );
  }
  
  return (
    <div className="source-path">
      <span className="path-text">{path}</span>
      <button onClick={() => setEditing(true)}>✏️ Edit</button>
    </div>
  );
}
```

---

### **4. Report Details with Overrides**

```javascript
function ReportDetailsPage({ reportId }) {
  const [report, setReport] = useState(null);
  const [items, setItems] = useState([]);
  
  useEffect(() => {
    fetchReportDetails();
  }, [reportId]);
  
  const fetchReportDetails = async () => {
    const response = await fetch(`/api/reports/${reportId}/details`);
    const data = await response.json();
    setReport(data.report);
    setItems(data.items);
  };
  
  const handleOverride = async (itemId, overrideData) => {
    await fetch(`/api/autonomous-reviews/${reportId}/results/${itemId}/override`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(overrideData)
    });
    // Refresh to show updated override
    fetchReportDetails();
  };
  
  return (
    <div className="report-details">
      <ReportSummary report={report} />
      
      <h2>Critical Issues (RED)</h2>
      <CriticalIssuesList 
        items={items.filter(i => i.rag_status === 'red')}
        onOverride={handleOverride}
      />
      
      <h2>Amber Issues</h2>
      <AmberIssuesList 
        items={items.filter(i => i.rag_status === 'amber')}
        onOverride={handleOverride}
      />
    </div>
  );
}
```

---

### **5. Override Button with Existing Overrides Display**

```javascript
function ChecklistItem({ item, onOverride }) {
  const [showOverrideModal, setShowOverrideModal] = useState(false);
  
  return (
    <div className={`checklist-item ${item.rag_status}`}>
      <div className="item-header">
        <RagBadge status={item.is_overridden ? item.overrides[0].new_rag_status : item.rag_status} />
        <span className="item-code">{item.item_code}</span>
        <span className="item-question">{item.question}</span>
      </div>
      
      <div className="item-evidence">
        {item.evidence}
      </div>
      
      {/* Show existing overrides */}
      {item.is_overridden && (
        <div className="overrides-display">
          <h4>Overrides ({item.overrides.length})</h4>
          {item.overrides.map(override => (
            <div key={override.override_id} className="override-card">
              <div className="override-header">
                <span className="override-status">
                  ✅ Overridden to {override.new_rag_status.toUpperCase()}
                </span>
                <span className="override-by">
                  by {override.overridden_by}
                </span>
              </div>
              <p className="override-comments">
                {override.comments}
              </p>
              <span className="override-reason">
                Reason: {override.reason}
              </span>
              <span className="override-date">
                {formatDate(override.overridden_at)}
              </span>
            </div>
          ))}
        </div>
      )}
      
      {/* Override Button */}
      <button 
        className="btn-override"
        onClick={() => setShowOverrideModal(true)}
      >
        📝 Override with Comment
      </button>
      
      {showOverrideModal && (
        <OverrideModal
          item={item}
          onClose={() => setShowOverrideModal(false)}
          onSubmit={(data) => {
            onOverride(item.item_id, data);
            setShowOverrideModal(false);
          }}
        />
      )}
    </div>
  );
}
```

---

## 📝 Implementation Steps

### **Backend (Today)**

1. ✅ Update models (DONE - added relationships)
2. ⏳ Create migration 003
3. ⏳ Create API endpoints in `app/api/routes/reports.py`:
   - `GET /history`
   - `PUT /{id}/source-path`
   - `POST /{id}/regenerate`
   - `GET /{id}/details`
4. ⏳ Test all endpoints

### **Frontend (Tomorrow)**

5. ⏳ Create Report History page
6. ⏳ Create Report Table component
7. ⏳ Create EditableSourcePath component
8. ⏳ Create Report Details page
9. ⏳ Integrate override feature
10. ⏳ Test end-to-end

---

## 🚀 Quick Start

### **1. Run Migration**
```bash
docker-compose exec app alembic upgrade head
```

### **2. Test API**
```bash
# List reports
curl http://localhost:8000/api/reports/history

# Update source path
curl -X PUT http://localhost:8000/api/reports/1/source-path \
  -H "Content-Type: application/json" \
  -d '{"source_path": "/new/path"}'

# Regenerate report
curl -X POST http://localhost:8000/api/reports/1/regenerate \
  -H "Content-Type: application/json" \
  -d '{"use_updated_source_path": true}'

# Get report details
curl http://localhost:8000/api/reports/1/details
```

---

## 📊 Expected UI Flow

```
User clicks "Reports" in navigation
    ↓
Report History Page loads
    ↓
Shows table of all reports:
- Project name
- Checklist name  
- Source path (with edit button)
- Generated date
- Score (with override adjustment)
- Override count badge
- View Details & Regenerate buttons
    ↓
User clicks "Edit" on source path
    ↓
Inline edit appears
User updates path and saves
    ↓
User clicks "Regenerate"
    ↓
Confirmation modal: "Regenerate with updated path?"
User confirms
    ↓
Background job starts
Progress indicator shows
    ↓
Report regenerated with new path
    ↓
User clicks "View Details"
    ↓
Report Details Page shows:
- Summary with override count
- Critical Issues (RED) with override buttons
- Amber Issues with override buttons
- Existing overrides displayed below each item
    ↓
User clicks "Override with Comment" on RED item
    ↓
Override modal opens
User selects new status, reason, adds comments
    ↓
Override saved and displayed immediately
```

---

## ✅ Success Criteria

- [ ] All reports listed with full details
- [ ] Source path editable inline
- [ ] Regenerate button works
- [ ] Report details show all items
- [ ] Override button on each RED/AMBER item
- [ ] Existing overrides displayed clearly
- [ ] Override count shown in summary
- [ ] Adjusted score calculated correctly

---

*Document Owner: Engineering Team*  
*Last Updated: March 27, 2026*  
*Status: Ready for Implementation*
