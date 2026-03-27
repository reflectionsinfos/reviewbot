# Self-Review Accountability & Stakeholder Preparation

> Ensuring self-reviews happen and stakeholders are prepared

**Version:** 1.0  
**Date:** March 27, 2026  
**Status:** For Review

---

## 🎯 Problem Statement

### The Accountability Gap

```
┌─────────────────────────────────────────────────────────────┐
│  Current Challenge (Without Accountability)                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Policy: "Self-review is mandatory"                        │
│  │                                                          │
│  ▼                                                          │
│  No enforcement mechanism                                   │
│  │                                                          │
│  ▼                                                          │
│  Team skips self-review                                     │
│  │                                                          │
│  ▼                                                          │
│  Stakeholder meeting happens anyway                         │
│  │                                                          │
│  ▼                                                          │
│  Poor outcome, Red/Amber assessment                         │
│  │                                                          │
│  ▼                                                          │
│  Policy ignored, no consequences                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### The Solution: Accountability + Stakeholder Prep

```
┌─────────────────────────────────────────────────────────────┐
│  With Accountability & Stakeholder Preparation              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Policy: "Self-review is mandatory"                        │
│  │                                                          │
│  ▼                                                          │
│  Automated reminders + blocking controls                    │
│  │                                                          │
│  ▼                                                          │
│  Team completes self-review                                 │
│  │                                                          │
│  ▼                                                          │
│  Readiness score shared with stakeholders                  │
│  │                                                          │
│  ▼                                                          │
│  Stakeholders prepare based on report                       │
│  │                                                          │
│  ▼                                                          │
│  Productive meeting, focused discussion                     │
│  │                                                          │
│  ▼                                                          │
│  Green assessment, quick approval                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔔 Accountability Features

### Feature 1: Automated Reminder System

#### Reminder Timeline

```
┌─────────────────────────────────────────────────────────────┐
│              Self-Review Reminder Timeline                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Stakeholder Meeting: Friday, March 29, 2:00 PM            │
│  ═══════════════════════════════════════════════════════   │
│                                                             │
│  T-7 Days (Friday before):                                 │
│  ───────────────────────────────────────────────────────   │
│  📧 Email to Project Manager                               │
│  "Your stakeholder review is scheduled for March 29.       │
│   Self-review is required. Schedule it now!"               │
│   [Schedule Self-Review]  [Dismiss]                        │
│                                                             │
│  T-5 Days (Sunday):                                        │
│  ───────────────────────────────────────────────────────   │
│  💬 Teams/Slack Notification                               │
│  "⚠️ Self-review pending for NeuMoney review"              │
│   [Schedule Now]                                           │
│                                                             │
│  T-3 Days (Tuesday):                                       │
│  ───────────────────────────────────────────────────────   │
│  📧 Email to Project Manager + Tech Lead                   │
│  "Self-review still not completed. This is required        │
│   before the stakeholder meeting."                         │
│   [Schedule Self-Review]  [Request Extension]              │
│                                                             │
│  T-2 Days (Wednesday) - ESCALATION:                        │
│  ───────────────────────────────────────────────────────   │
│  📧 Email to Manager (CC'd)                                │
│  "Team hasn't completed required self-review.              │
│   Stakeholder meeting at risk."                            │
│   [View Details]  [Grant Extension]                        │
│                                                             │
│  T-1 Day (Thursday) - FINAL WARNING:                       │
│  ───────────────────────────────────────────────────────   │
│  📧 Email + Teams Message                                  │
│  "⚠️ URGENT: Self-review must be completed today.         │
│   Stakeholder meeting may be rescheduled."                 │
│   [Complete Self-Review Now]  [Request Reschedule]         │
│                                                             │
│  Meeting Day (Friday) - BLOCKING:                          │
│  ───────────────────────────────────────────────────────   │
│  🚫 Meeting Blocked                                          │
│  "Cannot proceed - self-review not completed.              │
│   Please contact your manager."                            │
│   [Contact Manager]  [Reschedule Meeting]                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

#### Reminder Escalation Matrix

```
┌─────────────────────────────────────────────────────────────┐
│              Reminder Escalation Matrix                     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Days Before  │ Recipients          │ Channel │ Tone       │
│  ─────────────────────────────────────────────────────────  │
│  T-7          │ Project Manager     │ Email   │ Friendly   │
│  T-5          │ Project Manager     │ Chat    │ Casual     │
│  T-3          │ PM + Tech Lead      │ Email   │ Firm       │
│  T-2          │ + Manager (CC)      │ Email   │ Serious    │
│  T-1          │ + Director (CC)     │ Email+  │ Urgent     │
│               │                     │ Chat    │            │
│  T-0          │ All Stakeholders    │ System  │ Blocked    │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Escalation Triggers:                                       │
│  - No self-review scheduled by T-3                         │
│  - Self-review completed but readiness < threshold         │
│  - Action items from self-review not addressed             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

#### Reminder Templates

```
┌─────────────────────────────────────────────────────────────┐
│  T-7 Days: Friendly Reminder                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Subject: 📋 Upcoming Stakeholder Review - Action Required │
│                                                             │
│  Hi [Name],                                                │
│                                                             │
│  Your stakeholder review for [Project] is scheduled for    │
│  [Date/Time].                                              │
│                                                             │
│  📋 Required: Self-Review Session                          │
│  Teams who complete self-reviews are 3x more likely to     │
│  get Green status and quick approval!                      │
│                                                             │
│  [Schedule Self-Review Now] (takes 30-60 min)              │
│                                                             │
│  Benefits:                                                  │
│  ✅ Identify gaps before the meeting                       │
│  ✅ Practice your responses                                │
│  ✅ Build confidence                                       │
│  ✅ Reduce meeting time                                    │
│                                                             │
│  Questions? Reply to this email.                           │
│                                                             │
│  Thanks,                                                   │
│  ReviewBot Team                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  T-2 Days: Escalation (Manager CC'd)                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Subject: ⚠️ ACTION REQUIRED: Self-Review Not Completed    │
│                                                             │
│  Hi [Name],                                                │
│                                                             │
│  This is a reminder that the required self-review for      │
│  [Project] has not been completed.                         │
│                                                             │
│  Stakeholder Meeting: [Date/Time]                          │
│  Self-Review Status: ❌ Not Started                        │
│  Policy: Mandatory for this review type                    │
│                                                             │
│  ⚠️ Important:                                             │
│  Without completing self-review, the stakeholder           │
│  meeting cannot proceed.                                   │
│                                                             │
│  [Complete Self-Review Now]                                │
│  [Request Extension] (requires manager approval)           │
│                                                             │
│  CC: [Manager Name] - Please ensure team completes         │
│  required preparation.                                     │
│                                                             │
│  Thanks,                                                   │
│  ReviewBot Team                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  T-0 Days: Meeting Blocked                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Subject: 🚫 Meeting Blocked - Self-Review Required        │
│                                                             │
│  Hi [Name],                                                │
│                                                             │
│  Your stakeholder review meeting scheduled for today       │
│  has been blocked because the required self-review         │
│  was not completed.                                        │
│                                                             │
│  Next Steps:                                                │
│  1. Complete self-review session                           │
│  2. Achieve minimum readiness score (80/100)               │
│  3. Address critical action items                          │
│  4. Reschedule stakeholder meeting                         │
│                                                             │
│  [Complete Self-Review Now]                                │
│  [Contact Manager for Exception]                           │
│  [Reschedule Stakeholder Meeting]                          │
│                                                             │
│  All stakeholders have been notified of the reschedule.    │
│                                                             │
│  Thanks,                                                   │
│  ReviewBot Team                                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### Feature 2: Meeting Access Control

#### Blocking Logic

```python
def can_proceed_to_stakeholder_meeting(project_id, meeting_id):
    """
    Check if team can proceed to stakeholder meeting
    """
    # Get self-review status
    self_review = get_self_review(project_id, meeting_id)
    
    # Check 1: Was self-review completed?
    if not self_review:
        return {
            'allowed': False,
            'reason': 'Self-review not completed',
            'action': 'complete_self_review'
        }
    
    # Check 2: Is readiness score above threshold?
    if self_review.readiness_score < get_minimum_score(project_id):
        return {
            'allowed': False,
            'reason': f'Readiness score {self_review.readiness_score}/100 '
                     f'below minimum {get_minimum_score(project_id)}/100',
            'action': 'improve_preparation'
        }
    
    # Check 3: Are critical action items addressed?
    critical_items = get_critical_action_items(self_review)
    if critical_items:
        return {
            'allowed': False,
            'reason': f'{len(critical_items)} critical action items pending',
            'action': 'address_action_items'
        }
    
    # All checks passed
    return {
        'allowed': True,
        'reason': 'All requirements met',
        'readiness_score': self_review.readiness_score
    }
```

---

#### Meeting Status Display

```
┌─────────────────────────────────────────────────────────────┐
│         Stakeholder Meeting Status Dashboard                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Meeting: NeuMoney Q2 Technical Review                     │
│  Date: Friday, March 29, 2:00 PM                           │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Preparation Status:                                        │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  ✅ Self-Review Completed (March 27)                       │
│     Readiness Score: 85/100                                 │
│     Status: 🟢 Ready for Stakeholder Meeting               │
│                                                             │
│  ✅ Critical Action Items: 0/0                             │
│     All critical gaps addressed                            │
│                                                             │
│  ✅ Stakeholder Materials Uploaded                         │
│     - Architecture diagram                                  │
│     - Test results summary                                  │
│     - Deployment runbook                                    │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Meeting Status: ✅ CONFIRMED                              │
│                                                             │
│  [View Preparation Report]  [Join Meeting]                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│         Meeting Blocked - Not Ready                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Meeting: NeuMoney Q2 Technical Review                     │
│  Date: Friday, March 29, 2:00 PM                           │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  ❌ BLOCKED - Cannot Proceed to Stakeholder Meeting        │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Missing Requirements:                                      │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  ❌ Self-Review Not Completed                               │
│     Status: Not Started                                     │
│     [Complete Self-Review Now]                              │
│                                                             │
│  ⏳ Critical Action Items: 0/3                             │
│     - Document rollback procedure (HIGH)                   │
│     - Create monitoring runbook (MEDIUM)                   │
│     - Prepare architecture diagram (LOW)                   │
│     [View Action Items]                                     │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Options:                                                   │
│  [Complete Preparation]                                     │
│  [Request Exception] (requires VP approval)                │
│  [Reschedule Meeting]                                       │
│  [Contact Manager]                                          │
│                                                             │
│  All stakeholders have been notified of the delay.         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### Feature 3: Readiness Score Publication

#### Automatic Score Sharing

```
┌─────────────────────────────────────────────────────────────┐
│          Readiness Score in Meeting Invite                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Calendar Invite: NeuMoney Q2 Technical Review             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  When: Friday, March 29, 2:00 PM - 3:30 PM                 │
│  Where: Conference Room A + Teams                          │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  📊 Preparation Status:                                     │
│                                                             │
│  ✅ Self-Review Completed                                   │
│     Readiness Score: 85/100                                 │
│     Completed: March 27, 2026                               │
│                                                             │
│  🟢 Status: READY FOR REVIEW                               │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Agenda:                                                    │
│  1. Architecture overview (15 min)                         │
│  2. Deployment strategy (20 min)                           │
│  3. Testing approach (15 min)                              │
│  4. Q&A and decision (30 min)                              │
│                                                             │
│  Pre-Reading:                                               │
│  - Self-Review Preparation Report [PDF]                    │
│  - Architecture Diagram [PDF]                              │
│  - Test Summary Report [PDF]                               │
│                                                             │
│  Note: Team has completed self-review preparation.         │
│  Readiness score indicates strong preparation. Focus       │
│  areas: Rollback procedure, monitoring runbook.            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

#### Stakeholder Briefing Email

```
┌─────────────────────────────────────────────────────────────┐
│         Stakeholder Briefing (Sent T-1 Day)                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Subject: Briefing: NeuMoney Review Tomorrow (Readiness:   │
│           85/100)                                          │
│                                                             │
│  Hi [Stakeholder Name],                                     │
│                                                             │
│  Tomorrow's review for NeuMoney is confirmed for 2:00 PM.  │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  📊 Team Preparation Status:                                │
│                                                             │
│  ✅ Self-Review Completed                                   │
│     Readiness Score: 85/100                                 │
│     Status: Ready for Review                                │
│                                                             │
│  Strong Areas:                                              │
│  ✅ Architecture & Design (92/100)                         │
│  ✅ Testing Strategy (85/100)                              │
│                                                             │
│  Areas to Probe:                                            │
│  🟡 Deployment Strategy (68/100)                           │
│     - Rollback procedure needs review                      │
│     - Ask about: Testing of rollback, success criteria     │
│                                                             │
│  🟡 Monitoring (72/100)                                     │
│     - Alert thresholds not documented                      │
│     - Ask about: On-call process, escalation path          │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Recommended Questions:                                     │
│  1. "Can you walk me through your rollback procedure?"     │
│  2. "What happens when an alert fires at 3 AM?"            │
│  3. "How do you measure deployment success?"               │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Pre-Reading Attached:                                      │
│  - Self-Review Preparation Report                          │
│  - Architecture Diagram                                    │
│  - Test Summary                                            │
│                                                             │
│  See you tomorrow!                                         │
│                                                             │
│  ReviewBot                                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Stakeholder Preparation Requirements

### Why Stakeholders Should Prepare Too

```
┌─────────────────────────────────────────────────────────────┐
│         Two-Way Preparation Model                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Traditional (One-Way):                                     │
│  ────────────────────────────────────────────────────────   │
│  Team prepares ← Stakeholders show up unprepared           │
│  │                                                          │
│  ▼                                                          │
│  Stakeholders ask random questions                         │
│  │                                                          │
│  ▼                                                          │
│  Meeting goes off-track                                    │
│  │                                                          │
│  ▼                                                          │
│  Poor outcome                                               │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  ReviewBot (Two-Way):                                       │
│  ────────────────────────────────────────────────────────   │
│  Team prepares ← Stakeholders prepare                      │
│  │                        │                                 │
│  │                        └─ Know focus areas              │
│  │                        └─ Have suggested questions      │
│  │                        └─ Read pre-materials            │
│  ▼                                                          │
│  Focused, productive discussion                            │
│  │                                                          │
│  ▼                                                          │
│  Clear decision, quick approval                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### Stakeholder Preparation Features

#### 1. Pre-Meeting Briefing Pack

```
┌─────────────────────────────────────────────────────────────┐
│         Stakeholder Preparation Pack                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Review: NeuMoney Q2 Technical Review                      │
│  Date: March 29, 2026                                      │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  📋 What You'll Receive (T-1 Day):                         │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  1. Self-Review Preparation Report                         │
│     - Readiness score (85/100)                             │
│     - Strong areas (Green)                                 │
│     - Gaps identified (Amber/Red)                          │
│     - Action items completed                               │
│                                                             │
│  2. Suggested Questions for You to Ask                     │
│     Based on self-review gaps:                             │
│     - "Can you show me your rollback procedure?"           │
│     - "What's your alert response time?"                   │
│     - "How do you measure deployment success?"             │
│                                                             │
│  3. Project Artifacts                                      │
│     - Architecture diagram                                 │
│     - Test coverage report                                 │
│     - Deployment metrics                                   │
│     - Recent incident summaries                            │
│                                                             │
│  4. Review Checklist                                       │
│     - What will be covered                                 │
│     - Decision criteria                                    │
│     - Time allocation                                      │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  ⏱️  Expected Preparation Time: 15-20 minutes              │
│                                                             │
│  [Download Preparation Pack]                               │
│  [Acknowledge Receipt]                                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

#### 2. Stakeholder Accountability

```
┌─────────────────────────────────────────────────────────────┐
│         Stakeholder Preparation Tracking                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Stakeholder Preparation Status:                           │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Stakeholder        │ Prep Status │ Materials Viewed       │
│  ─────────────────────────────────────────────────────────  │
│  John (CTO)        │ ✅ Prepared │ ✅ (Yesterday)         │
│  Sanju (Architect) │ ✅ Prepared │ ✅ (This morning)      │
│  Priya (DevOps)    │ ⏳ Pending  │ ⏳ (Reminder sent)     │
│  You               │ ✅ Prepared │ ✅ (This morning)      │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Reminder to Unprepared Stakeholders:                       │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  "Hi Priya, just a reminder to review the preparation      │
│   pack for tomorrow's NeuMoney review. It'll only          │
│   take 15 minutes and will help us have a more             │
│   productive discussion."                                  │
│                                                             │
│  [Send Reminder]  [Skip]                                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

#### 3. Stakeholder Preparation Checklist

```
┌─────────────────────────────────────────────────────────────┐
│         Stakeholder Preparation Checklist                   │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Before the Meeting:                                        │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  ☐ Review Self-Review Preparation Report                   │
│     (Readiness score, gaps, strong areas)                  │
│                                                             │
│  ☐ Review Suggested Questions                              │
│     (Focus on Amber/Red areas)                             │
│                                                             │
│  ☐ Review Project Artifacts                                │
│     (Architecture, tests, metrics)                         │
│                                                             │
│  ☐ Prepare Your Questions                                  │
│     (Based on gaps and your priorities)                    │
│                                                             │
│  ☐ Confirm Attendance                                      │
│     (Or send delegate)                                     │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Expected Time: 15-20 minutes                              │
│                                                             │
│  [Mark as Prepared]                                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Enforcement Workflow

### Complete Accountability Flow

```
┌─────────────────────────────────────────────────────────────┐
│         Complete Accountability Workflow                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  T-10 Days: Stakeholder Meeting Scheduled                  │
│  │                                                          │
│  ▼                                                          │
│  T-7 Days: Self-Review Reminder #1 (Team)                  │
│  │                                                          │
│  ▼                                                          │
│  T-5 Days: Self-Review Reminder #2 (Team)                  │
│  │                                                          │
│  ▼                                                          │
│  T-3 Days: Self-Review Reminder #3 + Manager CC (Team)     │
│  │                                                          │
│  ▼                                                          │
│  T-2 Days: Self-Review Escalation (Manager)                │
│  │                                                          │
│  ▼                                                          │
│  T-1 Day:                                                   │
│  │                                                          │
│  ├─▶ If Self-Review Complete:                              │
│  │   ✓ Send briefing pack to stakeholders                  │
│  │   ✓ Share readiness score                               │
│  │   ✓ Stakeholder preparation reminders                   │
│  │                                                          │
│  └─▶ If Self-Review NOT Complete:                          │
│      ✗ Block meeting                                       │
│      ✗ Notify all stakeholders                             │
│      ✗ Require manager intervention                        │
│      ✗ Reschedule meeting                                  │
│                                                             │
│  Meeting Day:                                               │
│  │                                                          │
│  ├─▶ If Ready:                                             │
│  │   ✓ Meeting proceeds                                    │
│  │   ✓ Focused discussion on gaps                          │
│  │   ✓ Quick decision                                      │
│  │                                                          │
│  └─▶ If NOT Ready:                                         │
│      ✗ Meeting blocked                                     │
│      ✗ All stakeholders notified                           │
│      ✗ Reschedule required                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Success Metrics

### Accountability Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Self-Review Completion Rate** | > 95% | % of stakeholder meetings preceded by self-review |
| **On-Time Completion** | > 85% | Self-reviews completed by T-1 day |
| **Meeting Block Rate** | < 5% | % of meetings blocked due to no self-review |
| **Stakeholder Prep Rate** | > 80% | % of stakeholders who review prep pack |
| **Time to Approval** | -50% | Reduction in approval time |

---

## 🔗 Related Documents

- [Self-Review Specification](SELF_REVIEW_SPEC.md)
- [Requirements Document](requirements.md#FR-10)
- [Meeting Control Panel Spec](MEETING_CONTROL_PANEL_SPEC.md)

---

*Document Owner: Product Team*  
*Status: Draft for Review*  
*Next Review: After stakeholder feedback*
