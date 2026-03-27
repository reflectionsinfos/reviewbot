# Periodic & Recurring Self-Reviews

> Tracking reviews over time for projects, teams, and team members

**Version:** 1.0  
**Date:** March 27, 2026  
**Status:** For Review

---

## 🎯 Overview

Reviews are **not one-time events** - they happen periodically throughout the project lifecycle. This document specifies how ReviewBot handles recurring self-reviews, tracks history, and provides trend analysis.

---

## 📊 Review Cadence

### Typical Review Schedule

```
┌─────────────────────────────────────────────────────────────┐
│         Project Lifecycle Review Cadence                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Project Phase          │ Review Frequency                 │
│  ─────────────────────────────────────────────────────────  │
│  Initiation             │ Once (baseline review)            │
│  Planning               │ Bi-weekly                         │
│  Execution              │ Weekly or Bi-weekly               │
│  Pre-Launch             │ Weekly (critical phase)           │
│  Launch                 │ Daily (hypercare)                 │
│  Post-Launch            │ Monthly (maintenance)             │
│  ─────────────────────────────────────────────────────────  │
│                                                             │
│  Review Triggers:                                           │
│  ────────────────────────────────────────────────────────   │
│  📅 Scheduled: Every Monday at 10 AM                       │
│  🎯 Milestone: Before major release                         │
│  ⚠️  Event-driven: After production incident               │
│  📋 Ad-hoc: On-demand review                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Recurring Review Types

### Type 1: Scheduled Recurring Reviews

```
┌─────────────────────────────────────────────────────────────┐
│         Scheduled Recurring Review Configuration            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Project: NeuMoney Platform                                 │
│                                                             │
│  Review Cadence:                                            │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Frequency:                                                 │
│  ○ Daily                                                    │
│  ◉ Weekly (Every Monday at 10:00 AM)                       │
│  ○ Bi-weekly (Every other Monday)                          │
│  ○ Monthly (First Monday of month)                         │
│  ○ Quarterly                                               │
│  ○ Custom: [Every 3 weeks]                                 │
│                                                             │
│  Start Date: [March 31, 2026]                              │
│  End Date: [Project completion] or [Specific date]         │
│                                                             │
│  Review Mode:                                               │
│  ○ Single Review                                            │
│  ◉ Persona-Based Review                                    │
│  ○ Hybrid                                                   │
│                                                             │
│  Participants:                                              │
│  - Priya (PM) - Always                                     │
│  - Sanju (Tech Lead) - Always                              │
│  - Priya K (DevOps) - Always                               │
│  - Rahul (QA) - Always                                     │
│  - [Add more...]                                           │
│                                                             │
│  Notifications:                                             │
│  ☑ Send reminder 24 hours before                           │
│  ☑ Send reminder 1 hour before                             │
│  ☑ Escalate if not completed within 2 hours                │
│                                                             │
│  [Save Schedule]  [Preview Schedule]                        │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### Type 2: Milestone-Triggered Reviews

```
┌─────────────────────────────────────────────────────────────┐
│         Milestone-Triggered Review Configuration            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Project: NeuMoney Platform                                 │
│                                                             │
│  Milestone Reviews:                                         │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  ☑ Before Sprint Review                                    │
│     Trigger: Sprint end date                               │
│     Timing: 1 day before sprint review                     │
│     Participants: Full team                                │
│                                                             │
│  ☑ Before Production Release                               │
│     Trigger: Release scheduled                             │
│     Timing: 2 days before release                          │
│     Participants: Full team + stakeholders                 │
│     Mandatory: Yes                                         │
│                                                             │
│  ☑ Before Go/No-Go Decision                                │
│     Trigger: Decision meeting scheduled                    │
│     Timing: 1 day before decision                          │
│     Participants: Leadership team                          │
│     Mandatory: Yes                                         │
│                                                             │
│  ☑ After Major Incident                                    │
│     Trigger: P0/P1 incident resolved                       │
│     Timing: Within 24 hours of resolution                  │
│     Participants: Incident response team                   │
│     Mandatory: Yes                                         │
│                                                             │
│  [Add Milestone]  [Save Configuration]                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### Type 3: Ad-Hoc Reviews

```
┌─────────────────────────────────────────────────────────────┐
│         Ad-Hoc Review Scheduling                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Project: NeuMoney Platform                                 │
│                                                             │
│  Review Type:                                               │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  ○ Quick Check-in (15 min)                                 │
│     Purpose: Quick status, unblock issues                  │
│     Participants: Key team members                         │
│                                                             │
│  ◉ Focused Review (30-45 min)                              │
│     Purpose: Deep dive on specific area                    │
│     Focus Area: [Security / Performance / Quality / etc.]  │
│     Participants: Relevant personas                        │
│                                                             │
│  ○ Emergency Review (as needed)                            │
│     Purpose: Critical issue, immediate attention           │
│     Trigger: [Describe trigger]                            │
│     Participants: Full team                                │
│                                                             │
│  Scheduled For: [Date/Time]                                │
│  Reason: [Why this ad-hoc review is needed]                │
│                                                             │
│  [Schedule Review]                                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📈 Tracking & History

### Review History Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│         Review History Dashboard                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Project: NeuMoney Platform                                 │
│  Team: Core Team (8 members)                               │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Review Summary:                                            │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Total Reviews Completed: 24                               │
│  Average Readiness Score: 84/100                           │
│  Trend: ↗️ Improving (+5 points last 4 weeks)              │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Recent Reviews:                                            │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Date         │ Type        │ Score  │ Status    │ Actions │
│  ─────────────────────────────────────────────────────────  │
│  Mar 24, 2026 │ Weekly      │ 86/100 │ ✅ Ready  │ [View]  │
│  Mar 17, 2026 │ Weekly      │ 82/100 │ ✅ Ready  │ [View]  │
│  Mar 10, 2026 │ Weekly      │ 79/100 │ ✅ Ready  │ [View]  │
│  Mar 03, 2026 │ Weekly      │ 81/100 │ ✅ Ready  │ [View]  │
│  Feb 28, 2026 │ Pre-Release │ 88/100 │ ✅ Ready  │ [View]  │
│  Feb 24, 2026 │ Weekly      │ 76/100 │ ⚠️ Needs Work│ [View]│
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Upcoming Reviews:                                          │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  📅 Mar 31, 2026 at 10:00 AM (Weekly)                      │
│     Status: ⏳ Scheduled                                     │
│     Participants: 8 invited, 3 confirmed                    │
│     [Send Reminder] [Reschedule]                           │
│                                                             │
│  📅 Apr 07, 2026 at 10:00 AM (Weekly)                      │
│     Status: ⏳ Scheduled                                     │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  [View Full History]  [Export Report]  [Manage Schedule]   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### Team Member Review History

```
┌─────────────────────────────────────────────────────────────┐
│         Team Member Review History                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Team Member: Sanju (Technical Lead)                       │
│  Project: NeuMoney Platform                                 │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Participation Summary:                                     │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Reviews Participated: 24/24 (100%)                        │
│  Average Readiness Score: 82/100                           │
│  Trend: ↗️ Improving                                       │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Recent Reviews:                                            │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Date         │ Role       │ Score  │ Gaps Found │ Status  │
│  ─────────────────────────────────────────────────────────  │
│  Mar 24, 2026 │ Tech Lead  │ 85/100 │ 2          │ ✅      │
│  Mar 17, 2026 │ Tech Lead  │ 78/100 │ 3          │ ✅      │
│  Mar 10, 2026 │ Tech Lead  │ 80/100 │ 2          │ ✅      │
│  Mar 03, 2026 │ Tech Lead  │ 76/100 │ 4          │ ✅      │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Common Gap Areas:                                          │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  🔴 Technical Debt Tracking (appeared in 8 reviews)        │
│  🟡 Performance Testing (appeared in 5 reviews)            │
│  🟡 Documentation (appeared in 3 reviews)                  │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Improvement Over Time:                                     │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Technical Debt: ❌ (Reviews 1-8) → 🟡 (Reviews 9-16)      │
│                  → ✅ (Reviews 17-24) - RESOLVED           │
│                                                             │
│  [View Detailed History]  [Compare with Team]              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### Team-Level Review History

```
┌─────────────────────────────────────────────────────────────┐
│         Team Review History                                 │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Team: NeuMoney Core Team                                  │
│  Project: NeuMoney Platform                                 │
│  Period: Last 6 months                                     │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Team Performance Trends:                                   │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Overall Readiness Score Trend:                            │
│                                                             │
│     90 ┤                                    ╭─── 88        │
│        │                              ╭─────╯              │
│     80 ┤                        ╭─────╯        82          │
│        │                  ╭─────╯      79                  │
│     70 ┤            ╭─────╯    76                          │
│        │      ╭─────╯  72                                   │
│     60 ┤─────╯                                               │
│        └────────────────────────────────────────────        │
│        Jan   Feb   Mar   Apr   May   Jun                    │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Team Statistics:                                           │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Total Reviews: 24                                         │
│  Average Score: 80/100                                     │
│  Best Score: 88/100 (Jun 2026)                             │
│  Improvement: +16 points (Jan to Jun)                      │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Recurring Gaps (Appeared in 3+ reviews):                  │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  🔴 Performance Testing (12 reviews)                       │
│     Status: ⏳ In Progress                                  │
│     Owner: Sanju + Priya                                   │
│     First Appeared: Feb 2026                               │
│                                                             │
│  🟡 Documentation (6 reviews)                              │
│     Status: ✅ Resolved (May 2026)                         │
│     Owner: Full team                                       │
│     Resolved After: 4 reviews                              │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  [View Team Analytics]  [Export Trends]                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Trend Analysis

### Gap Trend Report

```
┌─────────────────────────────────────────────────────────────┐
│         Gap Trend Analysis                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Project: NeuMoney Platform                                 │
│  Period: Last 12 reviews (Mar-Jun 2026)                    │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Recurring Gaps:                                            │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  1. Performance Testing                                    │
│     ────────────────────────────────────────────────────   │
│     First Appeared: Review #3 (Feb 15)                    │
│     Appeared In: 12 reviews                                │
│     Status: ⏳ In Progress                                 │
│     Trend: ↘️ Decreasing (improving)                      │
│                                                             │
│     Review History:                                        │
│     #3: ❌ Not started                                     │
│     #4-6: 🟡 Planned                                       │
│     #7-9: 🟡 In Progress                                   │
│     #10-12: 🟡 Testing phase                               │
│                                                             │
│     Actions Taken:                                         │
│     - Performance testing sprint scheduled                │
│     - Load testing tools procured                         │
│     - External consultant engaged                         │
│                                                             │
│  2. Technical Debt Tracking                                │
│     ────────────────────────────────────────────────────   │
│     First Appeared: Review #1 (Mar 1)                     │
│     Appeared In: 8 reviews                                 │
│     Status: ✅ Resolved (Review #9)                       │
│     Trend: ✅ Closed                                       │
│                                                             │
│     Resolution:                                            │
│     - Technical debt backlog created                      │
│     - 20% sprint capacity allocated                       │
│     - Debt reduction tracking dashboard built             │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  [View All Gap Trends]  [Export Analysis]                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### Readiness Score Trends

```
┌─────────────────────────────────────────────────────────────┐
│         Readiness Score Trend Report                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Project: NeuMoney Platform                                 │
│  Period: Q1-Q2 2026                                        │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Overall Trend:                                             │
│                                                             │
│     90 ┤                                    ╭─── 88        │
│        │                              ╭─────╯              │
│     80 ┤                        ╭─────╯        82          │
│        │                  ╭─────╯      79                  │
│     70 ┤            ╭─────╯    76                          │
│        │      ╭─────╯  72                                   │
│     60 ┤─────╯                                               │
│        └────────────────────────────────────────────        │
│        R1  R2  R3  R4  R5  R6  R7  R8  ...  R24             │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  By Persona Trend:                                          │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Persona      │ R1  │ R6   │ R12  │ R18  │ R24  │ Trend   │
│  ─────────────────────────────────────────────────────────  │
│  PM           │ 75  │ 78   │ 82   │ 84   │ 86   │ ↗️ +11  │
│  Tech Lead    │ 68  │ 72   │ 76   │ 80   │ 83   │ ↗️ +15  │
│  DevOps       │ 80  │ 82   │ 85   │ 88   │ 90   │ ↗️ +10  │
│  QA           │ 72  │ 75   │ 79   │ 83   │ 86   │ ↗️ +14  │
│  ─────────────────────────────────────────────────────────  │
│  Team Average │ 74  │ 77   │ 81   │ 84   │ 86   │ ↗️ +12  │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Insights:                                                  │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  ✅ All personas showing improvement                       │
│  ✅ Tech Lead showing biggest improvement (+15 points)     │
│  ✅ DevOps consistently highest performer                  │
│  ⚠️  PM started lowest, now catching up                    │
│                                                             │
│  [View Detailed Analytics]  [Compare Projects]             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🗓️ Review Cadence Dashboard

```
┌─────────────────────────────────────────────────────────────┐
│         Review Cadence Dashboard                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  View: [All Projects ▼]  Period: [Q2 2026 ▼]              │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Upcoming Reviews (Next 7 Days):                           │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  📅 Today, 10:00 AM                                        │
│     NeuMoney - Weekly Review                               │
│     Participants: 8 invited, 5 confirmed                   │
│     Mode: Persona-Based                                    │
│     Status: ⏳ Upcoming                                     │
│     [Join] [Reschedule] [Message Team]                     │
│                                                             │
│  📅 Tomorrow, 2:00 PM                                      │
│     PayGateway - Pre-Release Review                        │
│     Participants: 6 invited, 6 confirmed                   │
│     Mode: Single Review                                    │
│     Status: ⏳ Upcoming                                     │
│     [Join] [Reschedule] [Message Team]                     │
│                                                             │
│  📅 Mar 29, 10:00 AM                                       │
│     Analytics - Bi-weekly Review                           │
│     Participants: 5 invited, 2 confirmed                   │
│     Mode: Persona-Based                                    │
│     Status: ⏳ Upcoming                                     │
│     [Join] [Reschedule] [Message Team]                     │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  This Week's Summary:                                       │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Total Reviews: 8                                          │
│  Completed: 3                                              │
│  Upcoming: 5                                               │
│  Overdue: 0                                                │
│                                                             │
│  Average Readiness: 84/100                                 │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Calendar View:                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  [Monthly Calendar Showing All Reviews]                    │
│  Color-coded by: Project / Status / Mode                   │
│                                                             │
│  [View Full Calendar]                                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 Database Schema Updates

```python
# Recurring Review Schedule
class RecurringReviewSchedule(Base):
    __tablename__ = "recurring_review_schedules"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    frequency = Column(String)  # daily, weekly, bi-weekly, monthly, quarterly
    day_of_week = Column(String)  # Monday, Tuesday, etc.
    time_of_day = Column(Time)
    start_date = Column(Date)
    end_date = Column(Date, nullable=True)
    review_mode = Column(String)  # single, persona_based, hybrid
    participant_ids = Column(JSON)  # List of user IDs
    is_active = Column(Boolean)
    created_at = Column(DateTime)

# Milestone-Triggered Review
class MilestoneReviewTrigger(Base):
    __tablename__ = "milestone_review_triggers"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    milestone_name = Column(String)  # "Pre-Release", "Sprint End", etc.
    trigger_event = Column(String)  # "release_scheduled", "sprint_end"
    timing_offset_days = Column(Integer)  # -2 (2 days before)
    review_mode = Column(String)
    participant_ids = Column(JSON)
    is_mandatory = Column(Boolean)

# Review Instance (actual review session)
class ReviewInstance(Base):
    __tablename__ = "review_instances"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    schedule_id = Column(Integer, ForeignKey("recurring_review_schedules.id"), nullable=True)
    milestone_trigger_id = Column(Integer, ForeignKey("milestone_review_triggers.id"), nullable=True)
    review_type = Column(String)  # scheduled, milestone, ad_hoc
    scheduled_date = Column(DateTime)
    completed_date = Column(DateTime, nullable=True)
    status = Column(String)  # scheduled, in_progress, completed, cancelled
    review_mode = Column(String)
    overall_readiness_score = Column(Float, nullable=True)
    
# Review Trend Analytics
class ReviewTrendAnalytics(Base):
    __tablename__ = "review_trend_analytics"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    team_member_id = Column(Integer, ForeignKey("users.id"), nullable=True)  # Null for team-level
    period_start = Column(Date)
    period_end = Column(Date)
    review_count = Column(Integer)
    avg_readiness_score = Column(Float)
    score_trend = Column(String)  # improving, stable, declining
    recurring_gaps = Column(JSON)  # List of gaps that appeared multiple times
    resolved_gaps = Column(JSON)  # List of gaps that were closed
```

---

## 📊 Analytics & Insights

### Gap Closure Rate

```python
def calculate_gap_closure_rate(project_id, period_days=90):
    """
    Calculate how quickly team closes identified gaps
    """
    reviews = get_reviews_in_period(project_id, period_days)
    
    total_gaps_identified = 0
    total_gaps_closed = 0
    avg_closure_time_days = 0
    
    for review in reviews:
        for gap in review.gaps:
            total_gaps_identified += 1
            if gap.closed:
                total_gaps_closed += 1
                closure_time = gap.closed_date - gap.identification_date
                avg_closure_time_days += closure_time.days
    
    closure_rate = (total_gaps_closed / total_gaps_identified * 100) if total_gaps_identified > 0 else 0
    avg_closure_time = (avg_closure_time_days / total_gaps_closed) if total_gaps_closed > 0 else 0
    
    return {
        'closure_rate': closure_rate,
        'avg_closure_time_days': avg_closure_time,
        'total_gaps': total_gaps_identified,
        'closed_gaps': total_gaps_closed
    }

# Example Result:
# {
#     'closure_rate': 78%,  # Good
#     'avg_closure_time_days': 12,  # Takes 12 days on average
#     'total_gaps': 45,
#     'closed_gaps': 35
# }
```

---

## 🎯 Recommendations

### Automatic Frequency Recommendation

```python
def recommend_review_frequency(project):
    """
    Recommend review frequency based on project characteristics
    """
    risk_level = project.risk_level  # low, medium, high
    team_size = project.team_size
    phase = project.phase  # initiation, planning, execution, launch, maintenance
    stakeholder_visibility = project.stakeholder_visibility  # low, medium, high
    
    # High-risk, large team, execution phase = frequent reviews
    if risk_level == 'high' or (team_size > 10 and phase == 'execution'):
        return 'weekly'
    
    # Medium risk, medium team = bi-weekly
    elif risk_level == 'medium' or team_size > 5:
        return 'bi-weekly'
    
    # Low risk, small team, maintenance = monthly
    else:
        return 'monthly'

# Example:
# NeuMoney Project:
# - Risk: High
# - Team: 8 people
# - Phase: Execution
# Recommendation: Weekly reviews
```

---

## 🔗 Related Documents

- [Self-Review Specification](SELF_REVIEW_SPEC.md)
- [Persona-Based Reviews](PERSONA_BASED_SELF_REVIEW.md)
- [Accountability Specification](SELF_REVIEW_ACCOUNTABILITY.md)
- [Requirements Document](requirements.md#FR-1011)

---

*Document Owner: Product Team*  
*Status: Draft for Review*  
*Next Review: After team feedback*
