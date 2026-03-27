# ReviewBot 2.0 - Real-Time Meeting Participation

> Vision Document: Autonomous AI Meeting Participant

**Version:** 0.1 (Draft)  
**Date:** March 27, 2026  
**Status:** For Discussion  
**Owner:** Product Team

---

## 📋 Executive Summary

### Current State (v1.0)
- **Manual review process** - Human conducts review, uses AI for report generation
- **Post-meeting tool** - ReviewBot processes information after the fact
- **Human-driven** - Human does all real-time interaction

### Vision (v2.0)
- **Real-time participation** - ReviewBot joins meetings, listens, observes
- **Context-aware** - Prepares before meetings, understands project context
- **Semi-autonomous to autonomous** - Can ask questions, conduct reviews independently

---

## 🎯 Proposed Capabilities

### Capability 1: Meeting Listener (Human + AI Co-pilot)

**Description:** ReviewBot joins meetings as a silent observer, listens to conversation, reads shared screens, and provides real-time assistance to human reviewer.

**Features:**
- Join video calls (Teams, Zoom, Google Meet)
- Speech-to-text transcription (real-time)
- Screen content understanding (OCR + vision)
- Context-aware suggestions to human reviewer
- Queue questions for human to ask

**Autonomy Level:** 🟡 **Low** (Human in control)

```
┌────────────────────────────────────────────────────────────┐
│                    Meeting Room                            │
│  ┌──────────┐     ┌──────────┐                            │
│  │  Human   │◀───▶│ReviewBot │                            │
│  │Reviewer  │     │ (Silent) │                            │
│  └──────────┘     └──────────┘                            │
│        │                  │                                │
│        │                  │ Real-time suggestions          │
│        │                  │ "Ask about deployment strategy"│
│        ▼                  │                                │
│  ┌──────────────────────────────────────────┐             │
│  │         Meeting Participants             │             │
│  │    (Project Team being reviewed)         │             │
│  └──────────────────────────────────────────┘             │
└────────────────────────────────────────────────────────────┘
```

---

### Capability 2: Active Co-Reviewer (Human Supervised)

**Description:** ReviewBot actively participates in meetings, asks questions from checklist, but human reviewer can override, skip, or intervene.

**Features:**
- All Capability 1 features, PLUS:
- Ask questions directly to participants
- Follow-up on vague answers
- Adapt questions based on conversation flow
- Human can mute, skip, or take over at any time
- Real-time RAG assessment visible to human

**Autonomy Level:** 🟠 **Medium** (Human supervised)

```
┌────────────────────────────────────────────────────────────┐
│                    Meeting Room                            │
│  ┌──────────┐     ┌──────────┐                            │
│  │  Human   │◀───▶│ReviewBot │                            │
│  │Reviewer  │     │ (Active) │                            │
│  │          │     │          │                            │
│  │ [Override]│     │ [Ask Q]  │                            │
│  │ [Skip]    │     │ [Follow-up]                          │
│  │ [Mute]    │     │          │                            │
│  └──────────┘     └──────────┘                            │
│        │                  │                                │
│        │                  │ Both can ask questions         │
│        │                  │ Human has final control        │
│        ▼                  ▼                                │
│  ┌──────────────────────────────────────────┐             │
│  │         Meeting Participants             │             │
│  │    (Project Team being reviewed)         │             │
│  └──────────────────────────────────────────┘             │
└────────────────────────────────────────────────────────────┘
```

---

### Capability 3: Autonomous Reviewer (AI-Led)

**Description:** ReviewBot conducts entire review meeting independently. Human reviewer joins as observer or not at all.

**Features:**
- All Capability 2 features, PLUS:
- Schedule and send meeting invites
- Prepare context before meeting
- Conduct full review autonomously
- Make judgment calls on follow-ups
- Generate and send report (with human approval option)
- Escalate to human if needed (confidence threshold)

**Autonomy Level:** 🔴 **High** (AI in control, human optional)

```
┌────────────────────────────────────────────────────────────┐
│                    Meeting Room                            │
│                                                            │
│  ┌──────────────────────────────────────────┐             │
│  │         ReviewBot                        │             │
│  │         (Autonomous Reviewer)            │             │
│  │                                          │             │
│  │  - Asks questions                        │             │
│  │  - Follows up                            │             │
│  │  - Assesses RAG                          │             │
│  │  - Takes notes                           │             │
│  └──────────────────────────────────────────┘             │
│                          │                                 │
│                          │ Conducts review                 │
│                          │                                 │
│        ┌─────────────────┴─────────────────┐              │
│        ▼                                   ▼              │
│  ┌──────────┐                        ┌──────────┐         │
│  │ Observer │                        │ Meeting  │         │
│  │  Human   │                        │Participants│        │
│  │(Optional)│                        │          │         │
│  └──────────┘                        └──────────┘         │
└────────────────────────────────────────────────────────────┘
```

---

### Capability 4: Pre-Meeting Preparation

**Description:** ReviewBot prepares for meetings by gathering context, sending pre-meeting questionnaires, and reviewing project documents.

**Features:**
- Calendar integration (schedule/receive meeting invites)
- Automated pre-meeting emails
- Document collection and analysis
- Context building from project artifacts
- Identify knowledge gaps before meeting
- Prepare targeted questions

**Workflow:**
```
┌─────────────────────────────────────────────────────────────┐
│              Pre-Meeting Preparation (2-3 days before)      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Meeting Scheduled                                       │
│     └─▶ ReviewBot receives calendar invite                 │
│                                                             │
│  2. Context Request Email                                   │
│     └─▶ Send email to project team                         │
│     └─▶ Request: Project docs, status reports, artifacts   │
│                                                             │
│  3. Document Analysis                                       │
│     └─▶ Parse received documents                           │
│     └─▶ Build knowledge base                               │
│     └─▶ Identify gaps                                      │
│                                                             │
│  4. Pre-Meeting Questionnaire                               │
│     └─▶ Send targeted questions                            │
│     └─▶ Collect responses                                  │
│     └─▶ Update preparation                                 │
│                                                             │
│  5. Meeting Agenda Generation                               │
│     └─▶ Create focused agenda                              │
│     └─▶ Prioritize questions                               │
│     └─▶ Share with human reviewer                          │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔧 Technical Requirements

### TR-1: Meeting Integration

| Requirement | Description | Priority | Complexity |
|-------------|-------------|----------|------------|
| TR-1.1 | Join Microsoft Teams meetings | Must Have | High |
| TR-1.2 | Join Zoom meetings | Must Have | High |
| TR-1.3 | Join Google Meet meetings | Should Have | High |
| TR-1.4 | Real-time transcription | Must Have | Medium |
| TR-1.5 | Speaker identification | Should Have | Medium |
| TR-1.6 | Screen content understanding | Could Have | High |

**Implementation Options:**
- **Microsoft Graph API** - For Teams integration
- **Zoom API** - For Zoom integration
- **Google Meet API** - For Google Meet integration
- **Universal bot** - Join as participant with screen capture

---

### TR-2: Real-Time Processing

| Requirement | Description | Priority | Complexity |
|-------------|-------------|----------|------------|
| TR-2.1 | Real-time STT (< 2s latency) | Must Have | Medium |
| TR-2.2 | Context tracking | Must Have | High |
| TR-2.3 | Conversation state management | Must Have | High |
| TR-2.4 | Multi-speaker handling | Should Have | Medium |
| TR-2.5 | Interruption handling | Should Have | High |
| TR-2.6 | Screen OCR + understanding | Could Have | High |

**Architecture:**
```
┌────────────────────────────────────────────────────────────┐
│                 Real-Time Processing Pipeline              │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Audio/Video Stream                                        │
│       │                                                    │
│       ▼                                                    │
│  ┌──────────────────┐                                     │
│  │  Speech-to-Text  │ (Whisper Streaming / Azure STT)     │
│  └────────┬─────────┘                                     │
│           │                                                │
│           ▼                                                │
│  ┌──────────────────┐                                     │
│  │  Speaker         │ (Voice fingerprinting)              │
│  │  Identification  │                                     │
│  └────────┬─────────┘                                     │
│           │                                                │
│           ▼                                                │
│  ┌──────────────────┐                                     │
│  │  Context         │ (Track conversation state)          │
│  │  Tracker         │                                     │
│  └────────┬─────────┘                                     │
│           │                                                │
│           ▼                                                │
│  ┌──────────────────┐                                     │
│  │  Decision        │ (When to ask, what to ask)          │
│  │  Engine          │                                     │
│  └────────┬─────────┘                                     │
│           │                                                │
│           ▼                                                │
│  ┌──────────────────┐                                     │
│  │  Response        │ (TTS or text to chat)               │
│  │  Generator       │                                     │
│  └──────────────────┘                                     │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

### TR-3: Pre-Meeting Automation

| Requirement | Description | Priority | Complexity |
|-------------|-------------|----------|------------|
| TR-3.1 | Calendar integration (Office 365) | Must Have | Medium |
| TR-3.2 | Calendar integration (Google) | Should Have | Medium |
| TR-3.3 | Automated email sending | Must Have | Low |
| TR-3.4 | Document parsing | Must Have | Medium |
| TR-3.5 | Context extraction | Should Have | High |
| TR-3.6 | Knowledge gap identification | Could Have | High |

---

### TR-4: Vision/Screen Understanding

| Requirement | Description | Priority | Complexity |
|-------------|-------------|----------|------------|
| TR-4.1 | Screen capture | Should Have | Medium |
| TR-4.2 | OCR for text extraction | Should Have | Medium |
| TR-4.3 | UI element recognition | Could Have | High |
| TR-4.4 | Dashboard/metric understanding | Could Have | High |
| TR-4.5 | Code review from screen | Won't Have (v2) | Very High |

**Implementation:**
- **GPT-4 Vision** - For screen understanding
- **Azure Computer Vision** - For OCR
- **Custom models** - For UI element detection

---

## 🎛️ Autonomy Levels

### Level 1: Silent Observer (Current + Enhancement)

```
Human: "ReviewBot, what should I ask about deployment?"
ReviewBot: "Based on the checklist, ask about rollback strategy."
```

**Control:** Human fully in control  
**Risk:** Low  
**Implementation:** Easy enhancement to v1.0

---

### Level 2: Suggested Questions (Co-pilot)

```
ReviewBot: [In chat] "Suggested: Ask about deployment frequency"
Human: [Reads and asks question]
```

**Control:** Human reviews suggestions before asking  
**Risk:** Low-Medium  
**Implementation:** Medium complexity

---

### Level 3: Active Participant (Supervised)

```
ReviewBot: "Can you tell me about your deployment strategy?"
[Team member responds]
ReviewBot: "Thank you. Do you have automated rollback?"
Human: [Can mute or override at any time]
```

**Control:** AI asks, human supervises  
**Risk:** Medium  
**Implementation:** High complexity

---

### Level 4: Autonomous (Human Optional)

```
ReviewBot: [Conducts entire review]
ReviewBot: "I'll generate a report and send it to your manager for approval."
Human: [Receives report, reviews, approves]
```

**Control:** AI fully autonomous  
**Risk:** High  
**Implementation:** Very high complexity

---

## ⚠️ Risks & Concerns

### Risk 1: Loss of Human Control

**Concern:** "This becomes more autonomous and human reviewer may not have the control"

**Mitigation:**
- **Granular control settings** - Configure autonomy level per meeting
- **Emergency override** - Human can always take over
- **Confidence thresholds** - AI escalates when uncertain
- **Approval gates** - Critical decisions require human approval

**Recommended Approach:**
```
┌────────────────────────────────────────────────────────────┐
│              Autonomy Control Settings                     │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Meeting: NeuMoney Project Review                          │
│                                                            │
│  Autonomy Level:                                           │
│  ○ Silent Observer (Level 1)                              │
│  ◐ Suggested Questions (Level 2)                          │
│  ● Active Participant (Level 3) ← Current                 │
│  ○ Autonomous (Level 4)                                   │
│                                                            │
│  Override Settings:                                        │
│  ☑ Human can mute AI at any time                          │
│  ☑ AI must ask before sensitive topics                    │
│  ☑ RAG assessments require human confirmation             │
│  ☐ Escalate to human if confidence < 80%                  │
│                                                            │
│  Approval Required For:                                    │
│  ☑ Red RAG assessments                                    │
│  ☑ Report finalization                                    │
│  ☐ Scheduling follow-up meetings                          │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

### Risk 2: Meeting Etiquette

**Concern:** AI interrupting at wrong times, asking inappropriate questions

**Mitigation:**
- **Turn-taking detection** - Wait for natural pauses
- **Priority queuing** - Important questions interrupt, others wait
- **Social cues learning** - Learn from human behavior
- **Cultural adaptation** - Adjust for different meeting cultures

---

### Risk 3: Privacy & Security

**Concern:** AI listening to sensitive discussions, screen content

**Mitigation:**
- **Encryption** - All audio/video encrypted
- **Access control** - Only authorized meetings
- **Data retention policy** - Auto-delete after processing
- **Compliance** - GDPR, SOC2, industry-specific

---

### Risk 4: Accuracy & Context

**Concern:** AI misunderstanding context, making wrong assessments

**Mitigation:**
- **Confidence scoring** - AI indicates confidence level
- **Human confirmation** - Verify uncertain interpretations
- **Learning from corrections** - Improve from feedback
- **Domain specialization** - Better accuracy in known domains

---

## 📊 Recommendations

### Recommendation 1: Phased Approach

**Phase 1: Enhanced Co-pilot (Q2 2026)**
- Join meetings as silent observer
- Real-time transcription
- Suggest questions to human (in chat)
- Post-meeting report generation

**Phase 2: Active Assistant (Q3 2026)**
- Ask questions with human permission
- Follow-up on answers
- Real-time RAG assessment
- Human can override anytime

**Phase 3: Supervised Autonomy (Q4 2026)**
- Conduct reviews independently
- Human joins as observer (optional)
- AI makes judgment calls
- Human approval before report distribution

**Phase 4: Full Autonomy (Q1 2027)**
- Complete autonomous reviews
- Human not required to attend
- AI schedules, conducts, reports
- Optional human approval

---

### Recommendation 2: Human-in-the-Loop Design

**Always maintain human oversight:**

```
┌────────────────────────────────────────────────────────────┐
│              Human-in-the-Loop Architecture                │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  AI Capabilities:                                          │
│  - Listen and transcribe                                   │
│  - Understand context                                      │
│  - Ask questions                                           │
│  - Assess RAG                                              │
│  - Generate report                                         │
│                                                            │
│  Human Control Points: ⭐                                  │
│  ⭐ Approve meeting participation                          │
│  ⭐ Override/skip questions                                │
│  ⭐ Confirm RAG assessments (red/amber)                    │
│  ⭐ Approve final report                                   │
│  ⭐ Escalation decisions                                   │
│                                                            │
│  AI Escalation Triggers:                                   │
│  - Confidence < threshold                                  │
│  - Contradictory information                               │
│  - Sensitive topics                                        │
│  - Participant requests human                              │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

### Recommendation 3: Start with Low-Risk Scenarios

**Initial Use Cases:**
1. **Internal team reviews** - Low stakes, familiar audience
2. **Status update meetings** - Routine, predictable
3. **Documentation reviews** - Less sensitive than technical deep-dives

**Later Use Cases:**
1. **Client-facing reviews** - Higher stakes
2. **Executive presentations** - High visibility
3. **Compliance audits** - Regulatory implications

---

### Recommendation 4: Transparency & Trust

**Make AI behavior transparent:**

```
┌────────────────────────────────────────────────────────────┐
│              Meeting Interface Example                     │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Participants: John (PM), Sanju (Tech Lead), ReviewBot    │
│                                                            │
│  ┌──────────────────────────────────────────────────────┐ │
│  │ ReviewBot Status:                                    │ │
│  │ 🟢 Listening                                         │ │
│  │ Current topic: Deployment Strategy                   │ │
│  │ Confidence: 87%                                      │ │
│  │                                                       │ │
│  │ [💬 Suggested Question]                              │ │
│  │ "Ask about rollback testing frequency"               │ │
│  │ [Ask] [Skip] [Modify]                                │ │
│  └──────────────────────────────────────────────────────┘ │
│                                                            │
│  Recent Assessments:                                       │
│  ✅ Scope Management - Green                              │
│  ⏳ Deployment Strategy - Processing...                   │
│  ⏳ Testing Coverage - Pending                            │
│                                                            │
│  [🔇 Mute ReviewBot] [⏸️ Pause AI] [🙋 Take Over]        │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## 🗺️ Implementation Roadmap

### Phase 1: Foundation (Q2 2026)

**Meeting Integration:**
- [ ] Microsoft Teams bot integration
- [ ] Real-time transcription (Whisper Streaming)
- [ ] Basic speaker identification

**Co-pilot Features:**
- [ ] In-meeting chat for suggestions
- [ ] Question queue for human reviewer
- [ ] Post-meeting report generation

**Pre-Meeting:**
- [ ] Calendar integration (Office 365)
- [ ] Automated context request emails
- [ ] Document parsing

---

### Phase 2: Active Participation (Q3 2026)

**AI Questioning:**
- [ ] Text-to-speech for asking questions
- [ ] Turn-taking detection
- [ ] Follow-up question logic

**Control Features:**
- [ ] Human override controls
- [ ] Mute/skip functionality
- [ ] Confidence thresholds

**Context Management:**
- [ ] Real-time conversation tracking
- [ ] Multi-meeting context
- [ ] Knowledge gap identification

---

### Phase 3: Supervised Autonomy (Q4 2026)

**Autonomous Features:**
- [ ] Independent question flow
- [ ] Judgment calls on follow-ups
- [ ] Adaptive questioning

**Safety Features:**
- [ ] Escalation to human
- [ ] Sensitive topic detection
- [ ] Cultural adaptation

**Vision Integration:**
- [ ] Screen sharing analysis
- [ ] OCR for shared documents
- [ ] Dashboard understanding

---

### Phase 4: Full Autonomy (Q1 2027)

**Complete Automation:**
- [ ] End-to-end autonomous reviews
- [ ] Self-scheduling
- [ ] Independent report distribution (with approval)

**Advanced Features:**
- [ ] Predictive insights during meeting
- [ ] Cross-meeting learning
- [ ] Natural conversation flow

---

## 📋 Decision Framework

### When to Use Each Autonomy Level

| Scenario | Recommended Level | Rationale |
|----------|-------------------|-----------|
| **First review with new team** | Level 1 (Observer) | Build trust, understand dynamics |
| **Routine status review** | Level 2 (Suggested) | Predictable, low risk |
| **Technical deep-dive** | Level 3 (Active) | Need expertise, human supervision |
| **Compliance audit** | Level 3 (Active) | High stakes, need accuracy |
| **Internal team retrospective** | Level 4 (Autonomous) | Familiar audience, low risk |
| **Client-facing review** | Level 2 (Suggested) | Relationship management important |
| **Executive presentation** | Level 1 (Observer) | High visibility, human control critical |

---

## 🎯 Success Metrics

### Adoption Metrics
- % of meetings with ReviewBot participation
- % of reviews conducted autonomously
- User satisfaction scores

### Quality Metrics
- RAG assessment accuracy (vs human)
- Question relevance scores
- Context understanding accuracy

### Efficiency Metrics
- Review time reduction
- Human reviewer time saved
- Report generation time

### Trust Metrics
- Override rate (how often human intervenes)
- Escalation rate (AI asking for help)
- User confidence in AI assessments

---

## 🔗 Related Documents

- [PRD v1.0](requirements.md) - Current requirements
- [Design Spec](design.md) - Current architecture
- [Agent Spec](../app/agents/review_agent/AGENT_SPEC.md) - ReviewAgent implementation
- [Test Strategy](test-strategy.md) - Testing approach

---

## 📞 Next Steps

### Immediate (This Week)
1. **Review this vision** - Team discussion
2. **Prioritize capabilities** - Which to build first
3. **Technical feasibility** - Architecture review
4. **Risk assessment** - Legal, compliance review

### Short Term (Next Month)
5. **Phase 1 spec** - Detailed requirements for Phase 1
6. **Technical design** - Architecture for meeting integration
7. **Prototype** - Basic Teams/Zoom integration
8. **User testing** - Internal alpha testing

### Long Term (Next Quarter)
9. **Phase 1 launch** - Beta with select users
10. **Feedback incorporation** - Iterate based on feedback
11. **Phase 2 planning** - Detailed planning for next phase

---

## ❓ Open Questions for Discussion

1. **Control vs Autonomy:** What's the right balance for your use case?
2. **Meeting platforms:** Which platforms are most critical? (Teams, Zoom, Google Meet)
3. **Risk tolerance:** How much autonomy are you comfortable with?
4. **Privacy requirements:** Any industry-specific compliance needs?
5. **Success criteria:** What would make this valuable enough to adopt?

---

*Document Owner: Product Team*  
*Status: Draft for Discussion*  
*Next Review: After team feedback*
