# ReviewBot v2.0 - Database Schema Design

> Complete database schema for Meeting Participation, Self-Review, Autonomous Review, and Accountability features

**Version:** 1.0  
**Date:** March 27, 2026  
**Status:** Ready for Implementation  
**Owner:** Database Team

---

## 📊 Entity Relationship Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    ReviewBot v2.0 - Complete ERD                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐ │
│  │   User       │      │   Project    │      │   Checklist  │ │
│  ├──────────────┤      ├──────────────┤      ├──────────────┤ │
│  │ id           │      │ id           │      │ id           │ │
│  │ email        │      │ name         │      │ name         │ │
│  │ full_name    │      │ domain       │      │ type         │ │
│  │ role         │      │ description  │      │ version      │ │
│  └──────────────┘      └──────────────┘      └──────────────┘ │
│         │                      │                      │        │
│         │                      │                      │        │
│         ▼                      ▼                      ▼        │
│  ┌──────────────┐      ┌──────────────┐      ┌──────────────┐ │
│  │ ProjectMember│      │ProjectMember │      │ChecklistItem │ │
│  ├──────────────┤      ├──────────────┤      ├──────────────┤ │
│  │ project_id   │      │ user_id      │      │ checklist_id │ │
│  │ user_id      │      │ persona      │      │ question     │ │
│  │ role         │      │ is_active    │      │ review_type  │ │
│  └──────────────┘      └──────────────┘      │ data_sources │ │
│                                              │ criteria     │ │
│                                              └──────────────┘ │
│                                                       │        │
│                                                       │        │
│         ┌─────────────────────────────────────────────┘        │
│         │                                                       │
│         ▼                                                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              Review Session (Parent)                     │  │
│  ├──────────────────────────────────────────────────────────┤  │
│  │ id                                                       │  │
│  │ project_id                                               │  │
│  │ checklist_id                                             │  │
│  │ review_type: self_review, stakeholder, autonomous        │  │
│  │ review_mode: single, persona_based, hybrid               │  │
│  │ status: draft, in_progress, completed, pending_approval  │  │
│  │ overall_readiness_score                                  │  │
│  └──────────────────────────────────────────────────────────┘  │
│         │                                                       │
│         │                                                       │
│         ├──────────────┬──────────────┬──────────────┐         │
│         ▼              ▼              ▼              ▼         │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────┐│
│  │SelfReview    │ │Stakeholder   │ │Autonomous    │ │Human   ││
│  │Session       │ │Meeting       │ │ReviewResult  │ │Review  ││
│  ├──────────────┤ ├──────────────┤ ├──────────────┤ ├────────┤│
│  │ persona      │ │ meeting_url  │ │ checklist_   │ │checkl..││
│  │ participant_ │ │ platform     │ │ item_id      │ │item_id ││
│  │ readiness_   │ │ transcript   │ │ autonomous_  │ │human_  ││
│  │ score        │ │ recording    │ │ rag          │ │rag     ││
│  └──────────────┘ └──────────────┘ │ evidence     │ │comments││
│                                    └──────────────┘ └────────┘│
│                                           │              │      │
│                                           └──────┬───────┘      │
│                                                  │              │
│                                                  ▼              │
│                                         ┌──────────────┐       │
│                                         │ Override     │       │
│                                         │ Request      │       │
│                                         ├──────────────┤       │
│                                         │ autonomous_  │       │
│                                         │ result_id    │       │
│                                         │ human_result_│       │
│                                         │ id           │       │
│                                         │ reason       │       │
│                                         │ status       │       │
│                                         └──────────────┘       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📋 Core Tables

### Users & Projects

```sql
-- Users table (existing, enhanced)
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(50) DEFAULT 'reviewer',  -- reviewer, manager, admin, director
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Projects table (existing, enhanced)
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    domain VARCHAR(100),  -- fintech, healthcare, ecommerce, etc.
    description TEXT,
    tech_stack JSON,  -- ["Python", "FastAPI", "PostgreSQL"]
    stakeholders JSON,  -- {"product_owner": "John", "tech_lead": "Sanju"}
    status VARCHAR(50) DEFAULT 'active',  -- active, completed, on_hold
    owner_id INTEGER REFERENCES users(id),
    risk_level VARCHAR(50) DEFAULT 'medium',  -- low, medium, high, critical
    team_size INTEGER,
    budget DECIMAL(15, 2),
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Project Members (NEW - for persona tracking)
CREATE TABLE project_members (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    persona VARCHAR(100),  -- project_manager, tech_lead, devops, qa, security
    is_active BOOLEAN DEFAULT TRUE,
    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(project_id, user_id, persona)
);

-- Index for fast lookups
CREATE INDEX idx_project_members_project ON project_members(project_id);
CREATE INDEX idx_project_members_user ON project_members(user_id);
CREATE INDEX idx_project_members_persona ON project_members(persona);
```

---

### Checklists (Enhanced for Autonomous Review)

```sql
-- Checklist templates
CREATE TABLE checklists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50) NOT NULL,  -- delivery, technical, security, compliance
    version VARCHAR(50) DEFAULT '1.0',
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,  -- NULL = global template
    is_global BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Checklist Items (ENHANCED for autonomous review)
CREATE TABLE checklist_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    checklist_id INTEGER REFERENCES checklists(id) ON DELETE CASCADE,
    item_code VARCHAR(50),  -- "1.1", "1.10", etc.
    area VARCHAR(255),  -- "Scope, Planning & Governance"
    question TEXT NOT NULL,
    category VARCHAR(100),
    weight DECIMAL(5, 2) DEFAULT 1.0,
    is_review_mandatory BOOLEAN DEFAULT TRUE,  -- blocks review completion until reviewed
    expected_evidence TEXT,
    
    -- NEW: Autonomous Review Configuration
    review_type VARCHAR(50) DEFAULT 'human',  -- human, autonomous, both
    data_sources JSON,  -- {"sonarqube": {"project": "xyz"}, "github": {"repo": "abc"}}
    verification_criteria JSON,  -- {"coverage": {"min": 80}, "quality": {"min": "A"}}
    
    -- NEW: Override Configuration
    can_override BOOLEAN DEFAULT TRUE,
    override_requires_approval BOOLEAN DEFAULT FALSE,
    override_approver_roles JSON,  -- ["tech_lead", "director"]
    
    -- Metadata
    suggested_for_domains JSON,  -- ["fintech", "healthcare"]
    order_index INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_checklist_items_checklist ON checklist_items(checklist_id);
CREATE INDEX idx_checklist_items_review_type ON checklist_items(review_type);
```

---

### Review Sessions

```sql
-- Review sessions (parent table)
CREATE TABLE review_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    checklist_id INTEGER REFERENCES checklists(id),
    title VARCHAR(255),
    review_type VARCHAR(50) NOT NULL,  -- self_review, stakeholder_meeting, autonomous
    review_mode VARCHAR(50),  -- single, persona_based, hybrid
    conducted_by INTEGER REFERENCES users(id),
    participants JSON,  -- ["Sanju", "Priya", "ReviewBot"]
    review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(50) DEFAULT 'draft',  -- draft, in_progress, completed, pending_approval, blocked
    voice_enabled BOOLEAN DEFAULT TRUE,
    notes TEXT,
    scheduled_at TIMESTAMP,  -- For recurring reviews
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recurring Review Schedules (NEW)
CREATE TABLE recurring_review_schedules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    frequency VARCHAR(50) NOT NULL,  -- daily, weekly, bi-weekly, monthly, quarterly
    day_of_week VARCHAR(20),  -- Monday, Tuesday, etc.
    time_of_day TIME,
    start_date DATE NOT NULL,
    end_date DATE,  -- NULL = ongoing
    review_mode VARCHAR(50),  -- single, persona_based, hybrid
    participant_ids JSON,  -- [1, 2, 3]
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Milestone Review Triggers (NEW)
CREATE TABLE milestone_review_triggers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    milestone_name VARCHAR(255) NOT NULL,  -- "Pre-Release", "Sprint End"
    trigger_event VARCHAR(255),  -- "release_scheduled", "sprint_end"
    timing_offset_days INTEGER,  -- -2 (2 days before)
    review_mode VARCHAR(50),
    participant_ids JSON,
    is_mandatory BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Review Instances (actual occurrences from schedules)
CREATE TABLE review_instances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    schedule_id INTEGER REFERENCES recurring_review_schedules(id),
    milestone_trigger_id INTEGER REFERENCES milestone_review_triggers(id),
    review_type VARCHAR(50),  -- scheduled, milestone, ad_hoc
    scheduled_date TIMESTAMP NOT NULL,
    completed_date TIMESTAMP,
    status VARCHAR(50) DEFAULT 'scheduled',  -- scheduled, in_progress, completed, cancelled, blocked
    review_mode VARCHAR(50),
    overall_readiness_score DECIMAL(5, 2),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_review_sessions_project ON review_sessions(project_id);
CREATE INDEX idx_review_sessions_status ON review_sessions(status);
CREATE INDEX idx_recurring_schedules_project ON recurring_review_schedules(project_id);
CREATE INDEX idx_review_instances_scheduled ON review_instances(scheduled_date);
CREATE INDEX idx_review_instances_status ON review_instances(status);
```

---

### Self-Review Results

```sql
-- Self-Review Sessions (per persona)
CREATE TABLE self_review_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_session_id INTEGER REFERENCES review_sessions(id) ON DELETE CASCADE,
    persona VARCHAR(100),  -- project_manager, tech_lead, devops, qa
    participant_id INTEGER REFERENCES users(id),
    checklist_id INTEGER REFERENCES checklists(id),
    session_type VARCHAR(50),  -- individual, consolidated
    readiness_score DECIMAL(5, 2),
    status VARCHAR(50) DEFAULT 'pending',  -- pending, in_progress, completed
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Autonomous Review Results (NEW)
CREATE TABLE autonomous_review_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    checklist_item_id INTEGER REFERENCES checklist_items(id),
    review_session_id INTEGER REFERENCES review_sessions(id) ON DELETE CASCADE,
    autonomous_rag VARCHAR(50) NOT NULL,  -- green, amber, red, na
    autonomous_evidence JSON NOT NULL,  -- {metrics: {...}, files: [...], urls: [...]}
    autonomous_notes TEXT,
    execution_time_seconds INTEGER,
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Human Review Results
CREATE TABLE human_review_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    checklist_item_id INTEGER REFERENCES checklist_items(id),
    review_session_id INTEGER REFERENCES review_sessions(id) ON DELETE CASCADE,
    human_rag VARCHAR(50) NOT NULL,  -- green, amber, red, na
    human_comments TEXT,
    human_evidence JSON,  -- uploaded files, links, notes
    reviewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reviewed_by INTEGER REFERENCES users(id)
);

-- Override Requests (NEW)
CREATE TABLE override_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    autonomous_result_id INTEGER REFERENCES autonomous_review_results(id),
    human_result_id INTEGER REFERENCES human_review_results(id),
    override_reason TEXT NOT NULL,
    requires_approval BOOLEAN DEFAULT FALSE,
    approver_role_required VARCHAR(100),
    status VARCHAR(50) DEFAULT 'pending',  -- pending, approved, rejected, more_info_requested
    requested_by INTEGER REFERENCES users(id),
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    decided_at TIMESTAMP
);

-- Override Approvals (NEW)
CREATE TABLE override_approvals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    override_request_id INTEGER REFERENCES override_requests(id) ON DELETE CASCADE,
    approver_id INTEGER REFERENCES users(id),
    approver_role VARCHAR(100),
    decision VARCHAR(50) NOT NULL,  -- approved, rejected
    comments TEXT,
    decided_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Final Review Results (consolidated)
CREATE TABLE final_review_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    checklist_item_id INTEGER REFERENCES checklist_items(id),
    review_session_id INTEGER REFERENCES review_sessions(id) ON DELETE CASCADE,
    autonomous_rag VARCHAR(50),  -- NULL if human-only review
    human_rag VARCHAR(50),  -- NULL if autonomous-only review
    final_rag VARCHAR(50) NOT NULL,
    is_overridden BOOLEAN DEFAULT FALSE,
    override_request_id INTEGER REFERENCES override_requests(id),
    final_status VARCHAR(50),  -- autonomous_only, human_only, overridden, agreed
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Consolidated Self-Review Reports
CREATE TABLE consolidated_self_review_reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    review_session_id INTEGER REFERENCES review_sessions(id),
    overall_readiness_score DECIMAL(5, 2),
    persona_breakdown JSON,  -- {pm: 85, tech_lead: 78, devops: 92, qa: 88}
    cross_persona_gaps JSON,  -- gaps affecting multiple personas
    overall_status VARCHAR(50),  -- ready, not_ready, needs_work
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_self_review_sessions_review ON self_review_sessions(review_session_id);
CREATE INDEX idx_autonomous_results_session ON autonomous_review_results(review_session_id);
CREATE INDEX idx_human_results_session ON human_review_results(review_session_id);
CREATE INDEX idx_override_requests_status ON override_requests(status);
CREATE INDEX idx_final_results_session ON final_review_results(review_session_id);
```

---

### Accountability & Reminders

```sql
-- Reminder Queue (NEW)
CREATE TABLE reminder_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_instance_id INTEGER REFERENCES review_instances(id),
    reminder_type VARCHAR(50),  -- email, chat, escalation
    scheduled_at TIMESTAMP NOT NULL,
    sent_at TIMESTAMP,
    status VARCHAR(50) DEFAULT 'pending',  -- pending, sent, failed, skipped
    recipient_ids JSON,  -- [1, 2, 3]
    template_name VARCHAR(100),
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Meeting Blocks (NEW)
CREATE TABLE meeting_blocks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_instance_id INTEGER REFERENCES review_instances(id),
    reason VARCHAR(255) NOT NULL,  -- "Self-review not completed"
    blocked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    unblocked_at TIMESTAMP,
    blocked_by INTEGER REFERENCES users(id),  -- system or human
    unblocked_by INTEGER REFERENCES users(id),
    override_approved_by INTEGER REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'active'  -- active, resolved, overridden
);

-- Stakeholder Preparation (NEW)
CREATE TABLE stakeholder_preparation (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    review_instance_id INTEGER REFERENCES review_instances(id),
    stakeholder_id INTEGER REFERENCES users(id),
    preparation_pack_sent_at TIMESTAMP,
    preparation_pack_viewed_at TIMESTAMP,
    readiness_score_viewed BOOLEAN DEFAULT FALSE,
    suggested_questions_viewed BOOLEAN DEFAULT FALSE,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_reminder_queue_scheduled ON reminder_queue(scheduled_at);
CREATE INDEX idx_reminder_queue_status ON reminder_queue(status);
CREATE INDEX idx_meeting_blocks_status ON meeting_blocks(status);
CREATE INDEX idx_stakeholder_prep_instance ON stakeholder_preparation(review_instance_id);
```

---

### Analytics & Trends

```sql
-- Review Trend Analytics (NEW)
CREATE TABLE review_trend_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    team_member_id INTEGER REFERENCES users(id),  -- NULL for team-level
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    review_count INTEGER,
    avg_readiness_score DECIMAL(5, 2),
    score_trend VARCHAR(50),  -- improving, stable, declining
    recurring_gaps JSON,
    resolved_gaps JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Gap Tracking (NEW)
CREATE TABLE gap_tracking (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    checklist_item_id INTEGER REFERENCES checklist_items(id),
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    first_identified_review_id INTEGER REFERENCES review_sessions(id),
    gap_description TEXT,
    severity VARCHAR(50),  -- critical, high, medium, low
    status VARCHAR(50) DEFAULT 'open',  -- open, in_progress, resolved
    owner_id INTEGER REFERENCES users(id),
    identified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    resolved_at TIMESTAMP,
    appeared_in_review_count INTEGER DEFAULT 1
);

-- Indexes
CREATE INDEX idx_trend_analytics_project ON review_trend_analytics(project_id);
CREATE INDEX idx_trend_analytics_period ON review_trend_analytics(period_start, period_end);
CREATE INDEX idx_gap_tracking_project ON gap_tracking(project_id);
CREATE INDEX idx_gap_tracking_status ON gap_tracking(status);
```

---

## 🔧 Migration Scripts

### Migration 001: Initial v2.0 Schema

```sql
-- Migration: 001_initial_v2_schema.sql
-- Date: March 27, 2026
-- Description: Add all v2.0 tables

BEGIN TRANSACTION;

-- Create all new tables (as defined above)
-- 1. Project members
-- 2. Enhanced checklist items
-- 3. Recurring schedules
-- 4. Milestone triggers
-- 5. Review instances
-- 6. Self-review sessions
-- 7. Autonomous review results
-- 8. Human review results
-- 9. Override requests
-- 10. Override approvals
-- 11. Final review results
-- 12. Consolidated reports
-- 13. Reminder queue
-- 14. Meeting blocks
-- 15. Stakeholder preparation
-- 16. Trend analytics
-- 17. Gap tracking

-- Add indexes
-- (all indexes as defined above)

COMMIT;
```

---

## 📊 Database Statistics

| Category | Tables | Columns | Indexes |
|----------|--------|---------|---------|
| **Users & Projects** | 3 | 35 | 6 |
| **Checklists** | 2 | 25 | 2 |
| **Review Sessions** | 4 | 50 | 6 |
| **Self-Review** | 7 | 80 | 7 |
| **Accountability** | 3 | 35 | 4 |
| **Analytics** | 2 | 25 | 4 |
| **TOTAL** | **21** | **250** | **29** |

---

## 🔗 Related Documents

- [Requirements Document](requirements.md)
- [Autonomous Code Review Spec](AUTONOMOUS_CODE_REVIEW.md)
- [Periodic Reviews Spec](PERIODIC_REVIEWS.md)
- [Design Phase Kickoff](DESIGN_PHASE_KICKOFF.md)

---

*Document Owner: Database Team*  
*Status: Ready for Implementation*  
*Next: Create migration scripts*

