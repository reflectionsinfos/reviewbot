# Override Feature - Implementation Guide

> Human override for autonomous review RAG status

**Version:** 1.0  
**Date:** March 27, 2026  
**Status:** Ready for Testing

---

## 🎯 Overview

The **Override Feature** allows human reviewers to override the AI-assessed RAG status for any checklist item with proper justification and audit trail.

### Use Cases

1. **Alternative Approach** - Project uses valid but non-standard approach
2. **Not Applicable** - Checklist item doesn't apply to this project type
3. **Project Specific** - Project has specific constraints/requirements
4. **Evidence Elsewhere** - Evidence exists but in non-standard location

---

## 📊 Database Schema

### New Table: `autonomous_review_overrides`

```sql
CREATE TABLE autonomous_review_overrides (
    id INTEGER PRIMARY KEY,
    result_id INTEGER NOT NULL,
    new_rag_status VARCHAR NOT NULL,  -- green | amber | red | na
    comments TEXT NOT NULL,
    reason VARCHAR,  -- project_specific | not_applicable | alternative_approach | other
    overridden_by INTEGER NOT NULL,
    overridden_at TIMESTAMP NOT NULL,
    
    FOREIGN KEY (result_id) REFERENCES autonomous_review_results(id) ON DELETE CASCADE,
    FOREIGN KEY (overridden_by) REFERENCES users(id)
);

CREATE INDEX idx_override_result ON autonomous_review_overrides(result_id);
CREATE INDEX idx_override_user ON autonomous_review_overrides(overridden_by);
```

### Relationships

```
AutonomousReviewResult (1) ──→ (M) AutonomousReviewOverride
```

---

## 🔧 API Endpoints

### **POST /api/autonomous-reviews/{job_id}/results/{result_id}/override**

Override the RAG status of a checklist item.

**Request:**
```json
POST /api/autonomous-reviews/1/results/42/override
Content-Type: application/json

{
  "new_rag_status": "green",
  "comments": "We use a different approach - all documentation is in Confluence with proper versioning and access controls.",
  "reason": "alternative_approach"
}
```

**Response:**
```json
{
  "status": "success",
  "message": "Override recorded successfully",
  "override_id": 1,
  "new_rag_status": "green"
}
```

**Status Codes:**
- `200` - Success
- `400` - Invalid RAG status or result doesn't belong to job
- `404` - Job or result not found

---

### **GET /api/autonomous-reviews/{job_id}/results/{result_id}/overrides**

Get all overrides for a specific result.

**Response:**
```json
{
  "result_id": 42,
  "overrides": [
    {
      "override_id": 1,
      "new_rag_status": "green",
      "comments": "We use Confluence for documentation...",
      "reason": "alternative_approach",
      "overridden_by": "Admin User",
      "overridden_at": "2026-03-27T10:30:00"
    }
  ]
}
```

---

## 🎨 UI Integration

### **Override Button (Critical Issues List)**

```javascript
function CriticalIssuesList({ issues, onOverride }) {
  return (
    <div className="critical-issues">
      {issues.map(issue => (
        <div key={issue.id} className="issue-item">
          <div className="issue-header">
            <span className="rag-badge red">RED</span>
            <span className="item-code">{issue.item_code}</span>
          </div>
          
          <p className="issue-question">{issue.question}</p>
          
          <div className="issue-evidence">
            {issue.evidence}
          </div>
          
          {/* Override Button */}
          <button 
            onClick={() => onOverride(issue)}
            className="btn-override"
          >
            📝 Override with Comment
          </button>
          
          {/* Show existing overrides */}
          {issue.overrides && issue.overrides.length > 0 && (
            <div className="overrides-list">
              {issue.overrides.map(override => (
                <div key={override.id} className="override-item">
                  <span className="override-badge">
                    ✅ Overridden to {override.new_rag_status}
                  </span>
                  <span className="override-by">
                    by {override.overridden_by}
                  </span>
                  <p className="override-comments">
                    {override.comments}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
```

---

### **Override Modal**

```javascript
function OverrideModal({ issue, onClose, onSubmit }) {
  const [formData, setFormData] = useState({
    new_rag_status: 'green',
    comments: '',
    reason: 'alternative_approach'
  });
  
  const handleSubmit = async () => {
    try {
      const response = await fetch(
        `/api/autonomous-reviews/${issue.job_id}/results/${issue.id}/override`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(formData)
        }
      );
      
      if (response.ok) {
        onSubmit();
        onClose();
      }
    } catch (error) {
      console.error('Override failed:', error);
    }
  };
  
  return (
    <Modal isOpen onClose={onClose}>
      <h3>Override RAG Status</h3>
      
      <div className="form-group">
        <label>New RAG Status</label>
        <select 
          value={formData.new_rag_status}
          onChange={e => setFormData({...formData, new_rag_status: e.target.value})}
        >
          <option value="green">🟢 Green</option>
          <option value="amber">🟡 Amber</option>
          <option value="red">🔴 Red</option>
          <option value="na">⚪ N/A</option>
        </select>
      </div>
      
      <div className="form-group">
        <label>Reason for Override</label>
        <select
          value={formData.reason}
          onChange={e => setFormData({...formData, reason: e.target.value})}
        >
          <option value="alternative_approach">
            Alternative Approach Used
          </option>
          <option value="project_specific">
            Project Specific Requirement
          </option>
          <option value="not_applicable">
            Not Applicable to This Project
          </option>
          <option value="other">
            Other (explain in comments)
          </option>
        </select>
      </div>
      
      <div className="form-group">
        <label>Comments *</label>
        <textarea
          value={formData.comments}
          onChange={e => setFormData({...formData, comments: e.target.value})}
          placeholder="Explain why you're overriding this assessment. Include details about your alternative approach or why this item is not applicable."
          rows={5}
          required
        />
      </div>
      
      <div className="modal-actions">
        <button onClick={onClose} className="btn-cancel">Cancel</button>
        <button onClick={handleSubmit} className="btn-submit">
          Submit Override
        </button>
      </div>
    </Modal>
  );
}
```

---

### **Updated Report Summary**

```javascript
function ReportSummary({ summary, overrides }) {
  const overrideCount = overrides?.length || 0;
  const adjustedScore = calculateAdjustedScore(summary, overrides);
  
  return (
    <div className="report-summary">
      <div className="summary-stats">
        <StatBox label="Total" value={summary.total} />
        <StatBox label="Green" value={summary.green} color="green" />
        <StatBox label="Amber" value={summary.amber} color="amber" />
        <StatBox label="Red" value={summary.red} color="red" />
        <StatBox label="Human" value={summary.human} color="purple" />
      </div>
      
      {overrideCount > 0 && (
        <div className="override-summary">
          <span className="override-count">
            ✅ {overrideCount} Override{overrideCount > 1 ? 's' : ''} Applied
          </span>
          <span className="score-adjustment">
            Score: {summary.red_percentage}% → {adjustedScore}%
          </span>
        </div>
      )}
    </div>
  );
}
```

---

## 📝 Migration

### **Step 1: Run Migration**

```bash
cd c:\projects\reviewbot

# Apply migration
docker-compose exec app alembic upgrade head

# Verify table created
docker-compose exec db psql -U review_user -d reviews_db -c "\dt autonomous_review_overrides"
```

### **Step 2: Test API**

```bash
# Test override endpoint
curl -X POST http://localhost:8000/api/autonomous-reviews/1/results/1/override \
  -H "Content-Type: application/json" \
  -d '{
    "new_rag_status": "green",
    "comments": "Test override - alternative approach used",
    "reason": "alternative_approach"
  }'

# Expected: {"status":"success","message":"Override recorded successfully"}
```

### **Step 3: Update UI**

Add override button to your Critical Issues list (see UI Integration above).

---

## 🎯 Reason Options

| Reason | Description | When to Use |
|--------|-------------|-------------|
| `alternative_approach` | Different but valid approach | Team uses different tool/method that achieves same goal |
| `project_specific` | Project has specific constraints | Budget, timeline, or technical constraints |
| `not_applicable` | Doesn't apply to this project | Checklist item irrelevant to project type |
| `other` | Other reason | Custom explanation in comments |

---

## 🔒 Audit Trail

Every override records:

1. **Who** - User who overridden (`overridden_by`)
2. **When** - Timestamp (`overridden_at`)
3. **What** - New RAG status (`new_rag_status`)
4. **Why** - Reason and comments (`reason`, `comments`)

### Query All Overrides

```sql
SELECT 
    o.id,
    o.new_rag_status,
    o.comments,
    o.reason,
    u.full_name as overridden_by,
    o.overridden_at,
    ci.question,
    ci.item_code
FROM autonomous_review_overrides o
JOIN users u ON o.overridden_by = u.id
JOIN autonomous_review_results r ON o.result_id = r.id
JOIN checklist_items ci ON r.checklist_item_id = ci.id
ORDER BY o.overridden_at DESC;
```

---

## 📊 Reporting Impact

### **Before Override:**
```
Total: 103
Green: 10 (10%)
Amber: 0 (0%)
Red: 27 (26%)
Score: 27%
```

### **After 5 Overrides:**
```
Total: 103
Green: 10 + 5 = 15 (15%)
Amber: 0 (0%)
Red: 27 - 5 = 22 (21%)
Score: 32% (+5%)

Overrides Applied: 5
- Alternative Approach: 3
- Not Applicable: 2
```

---

## ✅ Testing Checklist

- [ ] Migration runs successfully
- [ ] Table `autonomous_review_overrides` created
- [ ] POST endpoint creates override record
- [ ] GET endpoint returns overrides
- [ ] Invalid RAG status returns 400
- [ ] Non-existent result returns 404
- [ ] UI shows override button
- [ ] Modal opens and submits correctly
- [ ] Overrides display in results list
- [ ] Report summary shows override count

---

## 🔗 Related Documents

- [Autonomous Code Review Spec](AUTONOMOUS_CODE_REVIEW.md)
- [Database Schema](DATABASE_SCHEMA_V2.md)
- [API Reference](internal/api/reference.md)

---

*Document Owner: Engineering Team*  
*Last Updated: March 27, 2026*  
*Status: Ready for Testing*
