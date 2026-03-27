# Persona-Based & Single Review Modes

> Flexible self-review approach supporting both single and persona-based reviews

**Version:** 1.1  
**Date:** March 27, 2026  
**Status:** For Review

---

## 🎯 Flexible Review Approach

### **Both Modes Supported!**

```
┌─────────────────────────────────────────────────────────────┐
│         ReviewBot v2.0: Flexible Review Modes               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Mode 1: Single Review (Current)                           │
│  ────────────────────────────────────────────────────────   │
│  ✅ Simple, quick setup                                     │
│  ✅ Good for small teams (< 5 people)                      │
│  ✅ Everyone answers same questions                         │
│  ✅ Single report, easy to manage                          │
│  ✅ Best for: Routine reviews, small projects              │
│                                                             │
│  Mode 2: Persona-Based Review (Enhanced)                   │
│  ────────────────────────────────────────────────────────   │
│  ✅ Role-specific questions                                 │
│  ✅ Deep, expert answers                                    │
│  ✅ Clear ownership of gaps                                │
│  ✅ Efficient use of time                                  │
│  ✅ Best for: Complex projects, large teams, critical reviews │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  🎯 You Choose Per Project!                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎛️ Mode Selection

### Configuration Options

```
┌─────────────────────────────────────────────────────────────┐
│         Self-Review Mode Configuration                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Review Mode:                                               │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  ◉ Single Review (All participants together)               │
│  ○ Persona-Based Review (Separate sessions per role)       │
│  ○ Hybrid (Base together, persona-specific separately)     │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  When to Use Each Mode:                                     │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Single Review:                                             │
│  ☑ Small team (< 5 people)                                 │
│  ☑ Routine/low-risk review                                 │
│  ☑ Time-constrained                                        │
│  ☑ Team familiar with each other's work                    │
│                                                             │
│  Persona-Based Review:                                      │
│  ☑ Large team (5+ people)                                  │
│  ☑ Complex/critical review                                 │
│  ☑ Cross-functional team                                   │
│  ☑ Need deep expertise per area                            │
│  ☑ Clear ownership important                               │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  [Save Configuration]  [Preview Mode]                       │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 👥 Persona Definitions

### Primary Personas

| Persona | Role | Focus Areas | Review Depth |
|---------|------|-------------|--------------|
| **Project Manager** | PM Priya | Timeline, risks, stakeholders, budget | High-level + Governance |
| **Technical Lead** | Tech Lead Sanju | Architecture, technical decisions, code quality | Deep technical |
| **DevOps Engineer** | DevOps Priya | Deployment, CI/CD, monitoring, operations | Deep operational |
| **QA Lead** | QA Rahul | Testing strategy, quality metrics, defects | Deep quality |
| **Security Engineer** | Security Alex | Security controls, compliance, vulnerabilities | Deep security |
| **Product Owner** | PO John | Requirements, user value, acceptance | Business value |

---

## 🎭 Self-Review Models

### Model 1: Single Checklist for All (Current)

```
┌─────────────────────────────────────────────────────────────┐
│  Single Checklist Approach                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  One Review Session                                         │
│  │                                                          │
│  ▼                                                          │
│  Single Checklist (35 questions)                           │
│  ├── Architecture (5 questions)                            │
│  ├── Deployment (5 questions)                              │
│  ├── Testing (5 questions)                                 │
│  ├── Security (5 questions)                                │
│  ├── Timeline (5 questions)                                │
│  └── ...                                                   │
│                                                             │
│  All participants answer all questions                     │
│  │                                                          │
│  ▼                                                          │
│  Problem: Questions not relevant to all roles              │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Pros:**
- Simple to manage
- Single report
- Consistent coverage

**Cons:**
- Questions not relevant to all roles
- Shallow answers from non-experts
- Unclear ownership
- Wasted time

---

### Model 2: Separate Checklists per Persona (Recommended)

```
┌─────────────────────────────────────────────────────────────┐
│  Persona-Based Checklist Approach                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Multiple Review Sessions (by persona)                      │
│  │                                                          │
│  ├── PM Self-Review (30 min)                               │
│  │   └─ PM Checklist (15 questions)                        │
│  │       - Timeline & milestones                           │
│  │       - Risk management                                 │
│  │       - Stakeholder communication                       │
│  │       - Budget & resources                              │
│  │                                                          │
│  ├── Tech Lead Self-Review (45 min)                        │
│  │   └─ Tech Lead Checklist (20 questions)                 │
│  │       - Architecture decisions                          │
│  │       - Technical debt                                  │
│  │       - Code quality                                    │
│  │       - System design                                   │
│  │                                                          │
│  ├── DevOps Self-Review (45 min)                           │
│  │   └─ DevOps Checklist (20 questions)                    │
│  │       - CI/CD pipeline                                  │
│  │       - Deployment strategy                             │
│  │       - Monitoring & alerting                           │
│  │       - Incident response                               │
│  │                                                          │
│  └── QA Self-Review (30 min)                               │
│      └─ QA Checklist (15 questions)                        │
│          - Test strategy                                   │
│          - Coverage metrics                                │
│          - Defect tracking                                 │
│          - Quality gates                                   │
│                                                             │
│  ▼                                                          │
│  Consolidated Report                                        │
│  │                                                          │
│  ▼                                                          │
│  Complete picture with clear ownership                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Pros:**
- Relevant questions per role
- Deep, expert answers
- Clear ownership
- Efficient use of time
- Better gap identification

**Cons:**
- More coordination needed
- Multiple sessions to schedule
- Consolidation complexity

---

### Model 3: Hybrid Approach (Base + Persona-Specific)

```
┌─────────────────────────────────────────────────────────────┐
│  Hybrid Checklist Approach                                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Two-Tier Checklist Structure                               │
│  │                                                          │
│  ├── Base Checklist (Common for All)                       │
│  │   - Project overview                                    │
│  │   - Goals & objectives                                  │
│  │   - Key risks                                           │
│  │   - Stakeholder alignment                               │
│  │   (10 questions, everyone answers)                      │
│  │                                                          │
│  └── Persona-Specific Checklists                           │
│      - PM: Governance, timeline                            │
│      - Tech Lead: Architecture                             │
│      - DevOps: Operations                                  │
│      - QA: Quality                                         │
│      (15-20 questions, role-specific)                      │
│                                                             │
│  ▼                                                          │
│  Combined Report (Base + Role-specific)                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Pros:**
- Common understanding (base)
- Role-specific depth
- Balanced approach
- Easier consolidation

**Cons:**
- Still some redundancy
- Moderate complexity

---

## 📊 Recommendation

### **Recommended: Model 2 (Persona-Based Checklists)**

```
┌─────────────────────────────────────────────────────────────┐
│  Recommended Approach: Persona-Based with Consolidation     │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Why Model 2?                                               │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  ✅ Maximum relevance - Questions match expertise          │
│  ✅ Deep insights - Experts answer their domain            │
│  ✅ Clear ownership - Gaps assigned to specific roles      │
│  ✅ Time efficient - No irrelevant questions               │
│  ✅ Better preparation - Focused practice                  │
│                                                             │
│  Mitigation for Cons:                                       │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  ⚠️ Coordination complexity → Automated scheduling         │
│  ⚠️ Multiple sessions → Can be done async                 │
│  ⚠️ Consolidation → Automated report aggregation           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🏗️ Implementation Design

### Checklist Hierarchy

```
┌─────────────────────────────────────────────────────────────┐
│  Checklist Structure                                        │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Checklist Template Library                                 │
│  │                                                          │
│  ├── Base Checklist Template                               │
│  │   (10 questions - Common for all)                       │
│  │                                                          │
│  ├── PM Checklist Template                                 │
│  │   (15 questions - Governance, timeline, risks)          │
│  │                                                          │
│  ├── Tech Lead Checklist Template                          │
│  │   (20 questions - Architecture, technical)              │
│  │                                                          │
│  ├── DevOps Checklist Template                             │
│  │   (20 questions - Deployment, operations)               │
│  │                                                          │
│  ├── QA Checklist Template                                 │
│  │   (15 questions - Testing, quality)                     │
│  │                                                          │
│  └── Security Checklist Template                           │
│      (15 questions - Security, compliance)                 │
│                                                             │
│  ▼                                                          │
│  Project-Specific Customization                             │
│  │                                                          │
│  ▼                                                          │
│  Active Checklists (per project)                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### Self-Review Session Flow

```
┌─────────────────────────────────────────────────────────────┐
│  Persona-Based Self-Review Flow                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Project Manager Initiates                               │
│     │                                                       │
│     ▼                                                       │
│  2. ReviewBot Identifies Required Personas                 │
│     (Based on project type, checklist configuration)        │
│     │                                                       │
│     ▼                                                       │
│  3. Automated Scheduling                                    │
│     ├── PM self-review scheduled                            │
│     ├── Tech Lead self-review scheduled                     │
│     ├── DevOps self-review scheduled                        │
│     └── QA self-review scheduled                            │
│     │                                                       │
│     ▼                                                       │
│  4. Individual Sessions Conducted                          │
│     (Each person does their role-specific review)           │
│     │                                                       │
│     ▼                                                       │
│  5. Individual Reports Generated                           │
│     ├── PM readiness: 85/100                               │
│     ├── Tech Lead readiness: 78/100                        │
│     ├── DevOps readiness: 92/100                           │
│     └── QA readiness: 88/100                               │
│     │                                                       │
│     ▼                                                       │
│  6. Consolidated Report Created                            │
│     ├── Overall readiness: 86/100                          │
│     ├── By persona breakdown                               │
│     ├── Cross-persona gaps identified                      │
│     └── Ownership clearly assigned                         │
│     │                                                       │
│     ▼                                                       │
│  7. Team Sync Meeting (Optional)                           │
│     Review consolidated findings together                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

### Database Schema

```python
# Checklist Templates
class ChecklistTemplate(Base):
    __tablename__ = "checklist_templates"
    
    id = Column(Integer, primary_key=True)
    name = Column(String)  # "PM Checklist", "Tech Lead Checklist"
    persona = Column(String)  # "project_manager", "tech_lead"
    template_type = Column(String)  # "base", "persona_specific"
    questions = Column(JSON)  # List of questions
    is_active = Column(Boolean)

# Project-Specific Checklists
class ProjectChecklist(Base):
    __tablename__ = "project_checklists"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    template_id = Column(Integer, ForeignKey("checklist_templates.id"))
    persona = Column(String)
    assigned_to = Column(Integer, ForeignKey("users.id"))  # Person responsible
    status = Column(String)  # pending, in_progress, completed
    readiness_score = Column(Float)
    
# Self-Review Sessions
class SelfReviewSession(Base):
    __tablename__ = "self_review_sessions"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    persona = Column(String)
    participant_id = Column(Integer, ForeignKey("users.id"))
    checklist_id = Column(Integer, ForeignKey("project_checklists.id"))
    session_type = Column(String)  # individual, consolidated
    readiness_score = Column(Float)
    status = Column(String)
    completed_at = Column(DateTime)
    
# Consolidated Report
class ConsolidatedSelfReviewReport(Base):
    __tablename__ = "consolidated_self_review_reports"
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    overall_readiness_score = Column(Float)
    persona_breakdown = Column(JSON)  # {pm: 85, tech_lead: 78, ...}
    cross_persona_gaps = Column(JSON)  # Gaps requiring multiple roles
    overall_status = Column(String)  # ready, not_ready, needs_work
    created_at = Column(DateTime)
```

---

### Report Aggregation Logic

```python
def generate_consolidated_report(project_id):
    """
    Aggregate individual persona reports into consolidated view
    """
    # Get all self-review sessions for project
    sessions = get_self_review_sessions(project_id)
    
    # Calculate overall readiness
    overall_score = weighted_average([
        session.readiness_score 
        for session in sessions 
        if session.readiness_score
    ])
    
    # Persona breakdown
    persona_scores = {
        session.persona: session.readiness_score
        for session in sessions
    }
    
    # Identify cross-persona gaps
    cross_persona_gaps = []
    for gap in all_gaps:
        if gap.affects_multiple_personas:
            cross_persona_gaps.append(gap)
    
    # Determine overall status
    if overall_score >= 85 and not critical_gaps:
        status = "ready"
    elif overall_score >= 70:
        status = "needs_work"
    else:
        status = "not_ready"
    
    return {
        "overall_readiness_score": overall_score,
        "persona_breakdown": persona_scores,
        "cross_persona_gaps": cross_persona_gaps,
        "overall_status": status,
        "individual_reports": sessions
    }
```

---

## 📊 Example: Persona-Based Reports

### Individual Report (Tech Lead)

```
┌─────────────────────────────────────────────────────────────┐
│  Self-Review Report: Technical Lead                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Project: NeuMoney Platform                                 │
│  Participant: Sanju (Tech Lead)                            │
│  Completed: March 27, 2026                                 │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Readiness Score: 78/100                                   │
│  Status: 🟡 Needs Improvement                              │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Strong Areas:                                              │
│  ✅ Architecture Design (92/100)                           │
│     - Clear microservices architecture                     │
│     - ADRs well-documented                                 │
│     - Technology choices justified                         │
│                                                             │
│  ✅ Code Quality (85/100)                                  │
│     - Code review process in place                         │
│     - Static analysis configured                           │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Gaps Identified:                                           │
│  🟡 Technical Debt (68/100)                                │
│     Gap: No technical debt tracking                        │
│     Action: Create debt backlog, prioritize                │
│     Owner: Sanju (Tech Lead)                               │
│                                                             │
│  🟡 Performance Testing (72/100)                           │
│     Gap: Load testing not done                             │
│     Action: Schedule performance testing sprint            │
│     Owner: Sanju + Priya (DevOps)                          │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Recommended Questions for Stakeholder Meeting:            │
│  1. "What's our technical debt reduction strategy?"        │
│  2. "When will performance testing be completed?"          │
│  3. "How do we handle architectural exceptions?"           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Consolidated Report (All Personas)

```
┌─────────────────────────────────────────────────────────────┐
│  Consolidated Self-Review Report                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Project: NeuMoney Platform                                 │
│  Generated: March 28, 2026                                 │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Overall Readiness Score: 86/100                           │
│  Status: 🟢 Ready for Stakeholder Meeting                  │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Persona Breakdown:                                         │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  👤 PM Priya (Project Manager)                             │
│     Readiness: 85/100 🟢                                   │
│     Strong: Stakeholder alignment, risk management         │
│     Gap: Budget contingency planning                       │
│                                                             │
│  👤 Sanju (Technical Lead)                                 │
│     Readiness: 78/100 🟡                                   │
│     Strong: Architecture design                            │
│     Gap: Technical debt tracking                           │
│                                                             │
│  👤 Priya (DevOps)                                         │
│     Readiness: 92/100 🟢                                   │
│     Strong: CI/CD, monitoring                              │
│     Gap: Disaster recovery testing                         │
│                                                             │
│  👤 Rahul (QA Lead)                                        │
│     Readiness: 88/100 🟢                                   │
│     Strong: Test automation                                │
│     Gap: Performance test coverage                         │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Cross-Persona Gaps (Require Collaboration):               │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  🔴 Performance Testing                                    │
│     Affects: Tech Lead, DevOps, QA                         │
│     Action: Joint planning needed                          │
│     Owner: Sanju (coordination)                            │
│                                                             │
│  🟡 Technical Debt Management                              │
│     Affects: PM, Tech Lead                                 │
│     Action: Prioritize in backlog                          │
│     Owner: Priya (PM) + Sanju                              │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Stakeholder Meeting Focus Areas:                          │
│  1. Performance testing strategy & timeline                │
│  2. Technical debt reduction plan                          │
│  3. Disaster recovery readiness                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🎯 Checklist Strategy

### Should Checklists be Persona-Level?

**Answer: YES** - Here's why:

```
┌─────────────────────────────────────────────────────────────┐
│  Checklist Strategy Recommendation                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ✅ Base Checklist (Common for All)                        │
│     - 10 questions                                          │
│     - Project overview, goals, alignment                   │
│     - Everyone completes this                             │
│                                                             │
│  ✅ Persona-Specific Checklists                            │
│     - 15-20 questions each                                │
│     - Role-specific expertise                              │
│     - Only relevant persona completes                      │
│                                                             │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Checklist Templates by Persona:                           │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  | Persona          | Questions | Focus Areas             │
│  |──────────────────|───────────|─────────────────────────|
│  | Base (All)       | 10        | Overview, alignment     │
│  | PM               | 15        | Governance, timeline    │
│  | Tech Lead        | 20        | Architecture, code      │
│  | DevOps           | 20        | Deployment, ops         │
│  | QA               | 15        | Testing, quality        │
│  | Security         | 15        | Security, compliance    │
│  | Product Owner    | 15        | Requirements, value     │
│                                                             │
│  Total: ~110 questions (but each person answers 25-30)     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Comparison Matrix

| Aspect | Single Checklist | Hybrid | **Persona-Based (Recommended)** |
|--------|-----------------|--------|--------------------------------|
| **Relevance** | Low | Medium | **High** |
| **Depth** | Shallow | Medium | **Deep** |
| **Ownership** | Unclear | Medium | **Clear** |
| **Time Efficiency** | Low | Medium | **High** |
| **Gap Identification** | Poor | Good | **Excellent** |
| **Coordination** | Easy | Medium | **Complex (but manageable)** |
| **Report Clarity** | Confusing | Good | **Excellent** |

---

## 🗺️ Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
- [ ] Define persona templates
- [ ] Create base checklist
- [ ] Create persona-specific checklists
- [ ] Update database schema

### Phase 2: Individual Reviews (Week 3-4)
- [ ] Implement persona-based self-review sessions
- [ ] Individual report generation
- [ ] Automated scheduling per persona

### Phase 3: Consolidation (Week 5-6)
- [ ] Report aggregation logic
- [ ] Cross-persona gap identification
- [ ] Consolidated report generation
- [ ] Team sync workflow

### Phase 4: Refinement (Week 7-8)
- [ ] User feedback incorporation
- [ ] Checklist optimization
- [ ] Performance improvements
- [ ] Documentation

---

## 📋 Recommendations Summary

### 1. **Self-Review: Persona-Level** ✅
- Each persona does their own self-review
- Role-specific questions
- Individual readiness scores
- Clear ownership

### 2. **Checklists: Hybrid Structure** ✅
- Base checklist (common for all)
- Persona-specific checklists
- Template library
- Project customization

### 3. **Reports: Two Levels** ✅
- Individual persona reports
- Consolidated team report
- Cross-persona gaps highlighted
- Clear action items with owners

### 4. **Scheduling: Automated** ✅
- ReviewBot schedules per-persona sessions
- Async completion allowed
- Reminders per persona
- Consolidation automatic

---

## 🔗 Related Documents

- [Self-Review Specification](SELF_REVIEW_SPEC.md)
- [Accountability Specification](SELF_REVIEW_ACCOUNTABILITY.md)
- [Requirements Document](requirements.md#FR-10)

---

*Document Owner: Product Team*  
*Status: Draft for Review*  
*Next Review: After team feedback*
