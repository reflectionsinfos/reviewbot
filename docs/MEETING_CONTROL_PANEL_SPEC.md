# ReviewBot Meeting Control Panel Specification

> Human control interface for AI meeting participation

**Version:** 1.0 (Draft)  
**Date:** March 27, 2026  
**Status:** For Review

---

## 📋 Overview

The **Meeting Control Panel** is the human reviewer's interface for controlling ReviewBot during meetings. It provides real-time control over AI behavior, ensuring human oversight while leveraging AI capabilities.

---

## 🎛️ Control Panel Layout

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    ReviewBot Meeting Control Panel                      │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  MEETING STATUS                                                  │  │
│  │  ─────────────────────────────────────────────────────────────   │  │
│  │  📹 Meeting: NeuMoney Project Review                             │  │
│  │  👥 Participants: 5 (John, Sanju, Priya, ReviewBot, You)        │  │
│  │  ⏱️  Duration: 00:23:45                                          │  │
│  │  🎤 AI Status: 🔵 ENABLED (Can speak when you approve)           │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  QUICK CONTROLS                                                  │  │
│  │  ─────────────────────────────────────────────────────────────   │  │
│  │                                                                  │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │  │
│  │  │   🔇 MUTE    │  │   🎤 ENABLE  │  │   🙋 TAKE    │          │  │
│  │  │   AI         │  │   AI         │  │   OVER       │          │  │
│  │  │              │  │              │  │              │          │  │
│  │  │  AI cannot   │  │  AI can      │  │  You resume  │          │  │
│  │  │  speak       │  │  suggest     │  │  immediately │          │  │
│  │  └──────────────┘  └──────────────┘  └──────────────┘          │  │
│  │                                                                  │  │
│  │  Current Mode: ◉ APPROVED (AI asks approved questions)          │  │
│  │  ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━   │  │
│  │  ○ SILENT    ○ SUGGESTED    ◉ APPROVED    ○ AUTONOMOUS         │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  AI SUGGESTION QUEUE                                             │  │
│  │  ─────────────────────────────────────────────────────────────   │  │
│  │                                                                  │  │
│  │  💡 Suggested Question #12                                       │  │
│  │  ────────────────────────────────────────────────────────────   │  │
│  │  "Can you walk me through your deployment pipeline?"            │  │
│  │                                                                  │  │
│  │  Checklist: Technical → Deployment → CI/CD                      │  │
│  │  Priority: High                                                  │  │
│  │  Context: They mentioned Jenkins but no details on testing      │  │
│  │                                                                  │  │
│  │  [✅ Approve & Ask]  [✏️ Modify]  [⏭️ Skip]  [📝 Save for Later] │  │
│  │                                                                  │  │
│  │  ────────────────────────────────────────────────────────────   │  │
│  │  💡 Suggested Question #13 (Queued)                              │  │
│  │  "What's your rollback strategy if deployment fails?"           │  │
│  │  [Preview] [Approve Next] [Skip]                                │  │
│  │                                                                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  LIVE TRANSCRIPTION & ASSESSMENT                                 │  │
│  │  ─────────────────────────────────────────────────────────────   │  │
│  │                                                                  │  │
│  │  [10:23] John: We use Jenkins for CI/CD...                      │  │
│  │  [10:25] ReviewBot: [Typing response...]                        │  │
│  │  [10:26] ReviewBot: "Can you tell me more about your            │  │
│  │           automated testing in the pipeline?"                    │  │
│  │                                                                  │  │
│  │  Current Assessment:                                             │  │
│  │  ✅ CI/CD Pipeline - Green (Automated, well-documented)         │  │
│  │  ⏳ Testing Strategy - Processing...                             │  │
│  │  ☐ Rollback Plan - Pending                                      │  │
│  │                                                                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  PARTICIPANT QUESTIONS FOR AI                                    │  │
│  │  ─────────────────────────────────────────────────────────────   │  │
│  │                                                                  │  │
│  │  ❓ Sanju asked: "How many areas are you covering in this       │  │
│  │     review?"                                                     │  │
│  │                                                                  │  │
│  │  Suggested Response:                                             │  │
│  │  "This technical review covers 8 areas: Architecture,           │  │
│  │   Deployment, Testing, Security, Performance, Monitoring,       │  │
│  │   Documentation, and Operations."                                │  │
│  │                                                                  │  │
│  │  [✅ Send Response]  [✏️ Edit]  [🙋 I'll Answer]                │  │
│  │                                                                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
│  ┌──────────────────────────────────────────────────────────────────┐  │
│  │  CHECKLIST PROGRESS                                              │  │
│  │  ─────────────────────────────────────────────────────────────   │  │
│  │                                                                  │  │
│  │  ████████████████████░░░░░░░░░  24/35 Complete (68%)            │  │
│  │                                                                  │  │
│  │  ✅ Scope & Planning (5/5)                                      │  │
│  │  ✅ Architecture (4/4)                                          │  │
│  │  ✅ Deployment (3/5)                                            │  │
│  │  ⏳ Testing (2/6)                                                │  │
│  │  ☐ Security (0/5)                                                │  │
│  │  ☐ Performance (0/4)                                             │  │
│  │  ☐ Monitoring (0/3)                                              │  │
│  │  ☐ Documentation (0/3)                                           │  │
│  │                                                                  │  │
│  └──────────────────────────────────────────────────────────────────┘  │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🎛️ Control Modes

### Mode 1: SILENT 🔇

**AI Behavior:**
- ❌ Cannot speak at all
- ✅ Listens and transcribes
- ✅ Shows suggestions to human (in chat/panel)
- ✅ Tracks RAG assessments
- ✅ Takes notes

**When to Use:**
- First meeting with new team (build trust)
- Sensitive discussions
- Human wants full control
- Technical issues with TTS

**Human Actions:**
- Reviews AI suggestions privately
- Asks questions manually
- Has full control over flow

---

### Mode 2: SUGGESTED 💡

**AI Behavior:**
- ❌ Cannot speak without approval
- ✅ Shows question suggestions to human
- ✅ Waits for human approval
- ✅ Provides context for each suggestion
- ✅ Queues multiple questions

**When to Use:**
- Building trust with team
- Complex/nuanced topics
- Human wants to review before asking
- Training new reviewers

**Human Actions:**
- Reviews each suggestion
- Can: Approve / Modify / Skip / Save for later
- Asks approved questions (or lets AI ask)

---

### Mode 3: APPROVED ✅ (RECOMMENDED)

**AI Behavior:**
- ✅ Suggests questions to human
- ✅ Asks immediately after approval
- ✅ Handles follow-ups automatically
- ✅ Answers participant questions (factual only)
- ⚠️ Escalates judgment questions to human

**When to Use:**
- Routine reviews
- Established trust with team
- Balanced human+AI participation
- **Default mode for most reviews**

**Human Actions:**
- Quick approve/skip decisions
- Can override anytime
- Handles sensitive topics
- Final authority on assessments

---

### Mode 4: AUTONOMOUS 🤖

**AI Behavior:**
- ✅ Conducts review independently
- ✅ Asks questions without approval
- ✅ Follows up on answers
- ✅ Makes RAG assessments
- ⚠️ Escalates when confidence < threshold
- ⚠️ Red/Amber require human confirmation

**When to Use:**
- Routine, low-risk reviews
- Experienced with team
- Human as observer
- Time-constrained situations

**Human Actions:**
- Observes (can intervene anytime)
- Confirms Red/Amber assessments
- Can take over at any point
- Approves final report

---

## 🔘 Control Buttons

### Primary Controls

| Button | Icon | Action | When to Use |
|--------|------|--------|-------------|
| **Mute AI** | 🔇 | AI cannot speak | Sensitive discussion, AI about to say something inappropriate |
| **Enable AI** | 🎤 | AI can speak (in current mode) | Ready for AI participation |
| **Take Over** | 🙋 | Human resumes immediately | AI struggling, participant requests human |
| **Pause AI** | ⏸️ | Temporarily disable AI | Need to discuss privately with team |

### Question Controls

| Button | Icon | Action | When to Use |
|--------|------|--------|-------------|
| **Approve & Ask** | ✅ | AI asks immediately | Good question, ready to proceed |
| **Modify** | ✏️ | Edit question before asking | Needs refinement, add context |
| **Skip** | ⏭️ | Move to next question | Not relevant, already answered |
| **Save for Later** | 📝 | Queue for later | Important but wrong timing |

### Response Controls (for participant questions)

| Button | Icon | Action | When to Use |
|--------|------|--------|-------------|
| **Send Response** | ✅ | AI sends suggested answer | Factual question, answer is correct |
| **Edit Response** | ✏️ | Modify before sending | Needs adjustment |
| **I'll Answer** | 🙋 | Human responds | Sensitive topic, requires judgment |

---

## 🎯 Visual Indicators

### AI Status Indicators

```
┌─────────────────────────────────────────────────────────┐
│  AI Status          │  Indicator      │  Meaning        │
├─────────────────────────────────────────────────────────┤
│  Listening          │  🔵 Blue        │  AI is listening│
│  Thinking           │  🟡 Yellow      │  Processing     │
│  About to Speak     │  🟠 Orange      │  Preparing TTS  │
│  Speaking           │  🟢 Green       │  AI is talking  │
│  Muted              │  🔴 Red         │  AI cannot speak│
│  Escalating         │  🟣 Purple      │  Asking human   │
└─────────────────────────────────────────────────────────┘
```

### Confidence Indicators

```
AI: "Based on their answer, I'm 87% confident this is Green status"
    └─▶ High confidence (can auto-confirm)

AI: "I'm about 60% confident, but I need clarification on..."
    └─▶ Medium confidence (human should review)

AI: "I'm uncertain about this assessment. Human review needed."
    └─▶ Low confidence (escalate to human)
```

---

## 🔔 Notifications & Alerts

### AI → Human Notifications

```
┌─────────────────────────────────────────────────────────────┐
│  💡 Suggestion Ready                                        │
│  "I suggest asking about rollback testing"                  │
│  [View] [Approve] [Skip]                                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  ❓ Participant Question for AI                             │
│  Sanju: "How long will this review take?"                   │
│  [View Suggested Response] [I'll Answer]                    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  ⚠️ Escalation Needed                                       │
│  "I'm uncertain about this assessment. Confidence: 45%"     │
│  [Review] [Take Over]                                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  🎯 RAG Assessment Ready                                    │
│  Deployment Strategy: 🟡 Amber                              │
│  Reasoning: Rollback exists but untested                   │
│  [Confirm] [Modify] [Discuss with Team]                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 📱 Device Support

### Desktop Application (Full Control Panel)

**Features:**
- Complete control panel
- Multi-window support
- Keyboard shortcuts
- Second monitor support

**Keyboard Shortcuts:**
```
Ctrl+M     Mute/Unmute AI
Ctrl+A     Approve current question
Ctrl+S     Skip current question
Ctrl+T     Take over from AI
Ctrl+E     Edit suggested question
Esc        Pause AI immediately
```

### Mobile App (Limited Controls)

**Features:**
- Mute/Enable toggle
- Approve/Skip questions
- View transcription
- Receive escalations

**Use Case:**
- Human reviewer on-the-go
- Backup control method
- Quick interventions

---

## 🔐 Access Control

### Who Can Control AI?

| Role | Can Mute | Can Approve | Can Change Mode | Can View Transcript |
|------|----------|-------------|-----------------|---------------------|
| **Lead Reviewer** | ✅ | ✅ | ✅ | ✅ |
| **Co-Reviewer** | ✅ | ✅ | ⚠️ (With permission) | ✅ |
| **Observer** | ⚠️ (Can mute only) | ❌ | ❌ | ✅ |
| **Participant** | ❌ | ❌ | ❌ | ❌ |

---

## 🎭 Participant Disclosure (Fair Practice)

### Automatic Disclosure on Join

```
┌─────────────────────────────────────────────────────────────┐
│  Meeting Chat                                               │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  [ReviewBot joined the meeting]                            │
│                                                             │
│  🤖 ReviewBot: "Hello everyone! I'm ReviewBot, an AI      │
│       assistant helping with today's review. I'll be       │
│       asking questions from the checklist and taking       │
│       notes. My human colleague [Your Name] is also        │
│       here and oversees everything I do. Feel free to      │
│       ask me questions about the review process!"          │
│                                                             │
│  ℹ️  This meeting is being transcribed for review purposes.│
│     Transcriptions will be deleted after report approval.  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### When Participants Ask About AI

```
Participant: "Are you a real person or AI?"

ReviewBot: "Great question! I'm ReviewBot, an AI assistant.
           I'm here to help conduct this review by asking
           questions from the checklist and taking notes.
           My human colleague [Your Name] is overseeing
           everything I do and makes the final decisions.
           Is that okay with everyone?"
```

### End-of-Meeting Disclosure

```
ReviewBot: "Thank you everyone! Just to confirm:
           - I've transcribed this meeting for the review report
           - The transcript will be reviewed by [Your Name]
           - The report will be sent for approval before distribution
           - You'll receive a summary within 24 hours
           
           Any questions about the next steps?"
```

---

## 🛡️ Safety Features

### Emergency Override

**Always Available:**
- Physical mute button (keyboard shortcut)
- Works even if UI is frozen
- AI acknowledges immediately
- Visual confirmation

### AI Misfire Prevention

```
┌─────────────────────────────────────────────────────────────┐
│  AI About to Speak...                                       │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  "Can you explain why this feature wasn't completed?"      │
│                                                             │
│  [✅ Approve]  [✏️ Modify]  [🚫 Block & Skip]              │
│                                                             │
│  ⏱️ Auto-approve in 5s (configurable)                      │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Confidence-Based Escalation

```
If AI confidence < threshold:
  ├─ 80%+: Auto-proceed (log only)
  ├─ 60-79%: Suggest, wait for approval
  ├─ 40-59%: Escalate to human
  └─ <40%: Defer to human immediately
```

---

## 📊 Analytics & Feedback

### Post-Meeting Report to Human

```
┌─────────────────────────────────────────────────────────────┐
│  Meeting Summary: NeuMoney Review #1                        │
│  ────────────────────────────────────────────────────────   │
│                                                             │
│  Duration: 45 minutes                                       │
│  Questions Asked: 24                                        │
│    - By AI (approved): 18                                   │
│    - By You: 6                                              │
│                                                             │
│  Participant Questions to AI: 5                             │
│    - Answered by AI: 4                                      │
│    - Escalated to You: 1                                    │
│                                                             │
│  Overrides: 2                                               │
│    - You muted AI: 1                                        │
│    - You took over: 1                                       │
│                                                             │
│  AI Confidence:                                             │
│    - High (>80%): 20 assessments                            │
│    - Medium (60-79%): 3 assessments                         │
│    - Low (<60%): 1 assessment (escalated)                   │
│                                                             │
│  Feedback: [Rate AI Performance] ⭐⭐⭐⭐⭐                   │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔗 Implementation Notes

### Technical Requirements

1. **Low Latency** - Control actions must be instant (< 200ms)
2. **Reliability** - Mute button must always work
3. **Visual Feedback** - Clear indication of AI state
4. **Accessibility** - Keyboard shortcuts, screen reader support
5. **Mobile Responsive** - Works on phones/tablets

### Integration Points

- Microsoft Teams Bot API
- Zoom Bot API
- Google Meet API (future)
- Azure OpenAI (TTS/STT)
- ReviewBot backend (question queue, RAG)

---

## 📞 Next Steps

1. **Review this spec** - Confirm control panel design
2. **User testing** - Get feedback on control layout
3. **Technical feasibility** - Architecture review
4. **Prototype** - Build basic control panel
5. **Iterate** - Refine based on testing

---

*Document Owner: Product Team*  
*Status: Draft for Review*  
*Next Review: After stakeholder feedback*
