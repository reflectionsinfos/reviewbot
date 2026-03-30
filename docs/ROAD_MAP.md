# ReviewBot v2.0 - Implementation Roadmap

> Complete implementation plan with phases, tasks, and tracking

**Version:** 2.0
**Last Updated:** March 28, 2026
**Status:** Phase 1 in progress; Document Review, QUIZ, Repo Integration added to scope
**Owner:** Engineering Team

---

## 📊 Implementation Overview

| Phase | Name | Duration | Status | Start |
|-------|------|----------|--------|-------|
| **Phase 1** | Foundation + Autonomous Review | 8 weeks | 🔄 In Progress | Mar 27, 2026 |
| **Phase 1c** | Two-Track Action Item System | 2 weeks | 📋 Planned | Apr 14, 2026 |
| **Phase 1b** | Repository Integration + Source Types | 2 weeks | 📋 Planned | Apr 28, 2026 |
| **Phase 2** | Document Review Engine | 6 weeks | 📋 Planned | May 12, 2026 |
| **Phase 3** | Knowledge QUIZ (text + voice) | 6 weeks | 📋 Planned | Jun 23, 2026 |
| **Phase 4** | Self-Review Core | 8 weeks | 📋 Planned | Aug 4, 2026 |
| **Phase 5** | Accountability & Scheduling | 6 weeks | 📋 Planned | Oct 1, 2026 |
| **Phase 6** | Meeting Integration (Teams/Zoom) | 8 weeks | 📋 Planned | Nov 12, 2026 |
| **Phase 7** | Control Panel UI | 8 weeks | 📋 Planned | Jan 7, 2027 |
| **Phase 8** | Analytics & Trends | 6 weeks | 📋 Planned | Mar 4, 2027 |

---

## 🎯 Phase 1: Foundation (8 weeks)

**Status:** 🔄 **IN PROGRESS**
**Started:** March 27, 2026
**Duration:** March 27 - May 27, 2026
**Priority:** HIGH
**Dependencies:** None

### Week 1-2: Database & Infrastructure

#### Task 1.1: Database Setup
- [x] **1.1.1** Setup PostgreSQL development database
  - Owner: DevOps
  - Estimate: 2h
  - Status: ✅ Done (PostgreSQL 15 in Docker on port 5435; fixed port conflict with local PostgreSQL on 5432)
- [x] **1.1.2** Create Migration 001 script (all 21 tables)
  - Owner: Database Team
  - Estimate: 8h
  - Status: ✅ Done (scripts/db_test.py creates core schema; full schema in app/models.py)
- [x] **1.1.3** Test migration on dev database
  - Owner: Database Team
  - Estimate: 4h
  - Status: ✅ Done (db_test.py ran successfully; migrate_xlsx_to_db.py loaded real project data)
- [x] **1.1.4** Setup SQLAlchemy base models
  - Owner: Backend Team
  - Estimate: 8h
  - Status: ✅ Done (app/models.py — fixed deprecated declarative_base import)
- [x] **1.1.5** Create database connection pooling
  - Owner: Backend Team
  - Estimate: 4h
  - Status: ✅ Done (app/db/session.py — async SQLAlchemy with asyncpg)

#### Task 1.2: Production Infrastructure (GCP)
- [x] **1.2.1** Setup Cloud Run + Cloud SQL environment
  - Status: ✅ Done (reviewbot-web service + reviewbot-db instance)
- [x] **1.2.2** Configure CI/CD pipeline (Cloud Build / GitHub Actions)
  - Status: ✅ Done (App deployed via gcp_scripts/05_deploy_app.sh)
- [x] **1.2.3** Setup Secret Manager for production keys
  - Status: ✅ Done (DATABASE_URL, SECRET_KEY, OPENAI_API_KEY)
- [x] **1.2.4** Implement modular SQL restoration (Cloud SQL safe)
  - Status: ✅ Done (01-05 scripts in scripts/db/)
- [ ] **1.2.5** Setup logging & monitoring (Cloud Logging/Monitoring)
  - Status: 🔄 In Progress (GCP_TROUBLESHOOTING.md baseline)

### Week 3-4: Base API Endpoints

#### Task 1.3: User & Project APIs
- [x] **1.3.1** Implement User CRUD endpoints
  - Owner: Backend Team
  - Estimate: 8h
  - Status: ✅ Done (app/api/routes/users.py — CRUD with selectinload for async)
- [x] **1.3.2** Implement Project CRUD endpoints
  - Owner: Backend Team
  - Estimate: 12h
  - Status: ✅ Done (app/api/routes/projects.py — fixed duplicate import, async eager loading)
- [ ] **1.3.3** Implement ProjectMember endpoints
  - Owner: Backend Team
  - Estimate: 8h
  - Status: ⏳ Not Started
- [x] **1.3.4** Add authentication middleware (JWT)
  - Owner: Backend Team
  - Estimate: 8h
  - Status: ✅ Done (app/api/routes/auth.py — fixed register to save to DB, fixed login to query by email, pinned bcrypt==4.0.1 for passlib compatibility)
- [ ] **1.3.5** Add role-based authorization
  - Owner: Backend Team
  - Estimate: 8h
  - Status: ⏳ Not Started

#### Task 1.4: Checklist APIs
- [x] **1.4.1** Implement Checklist CRUD endpoints
  - Owner: Backend Team
  - Estimate: 8h
  - Status: ✅ Done (app/api/routes/checklists.py — fixed async relationship loading)
- [x] **1.4.2** Implement ChecklistItem CRUD endpoints
  - Owner: Backend Team
  - Estimate: 12h
  - Status: ✅ Done (checklist items endpoints with area/category/weight support)
- [x] **1.4.3** Add checklist template system
  - Owner: Backend Team
  - Estimate: 8h
  - Status: ✅ Done (global templates loaded from data/templates/*.xlsx via migrate_xlsx_to_db.py)
- [x] **1.4.4** Implement checklist parsing (Excel)
  - Owner: Backend Team
  - Estimate: 12h
  - Status: ✅ Done (scripts/migrate_xlsx_to_db.py — handles merged cells, RAG normalisation, all project xlsx files migrated)

### Week 5-6: GitHub Integration

#### Task 1.5: GitHub OAuth & Repository Access
- [ ] **1.5.1** Implement GitHub OAuth flow
  - Owner: Backend Team
  - Estimate: 8h
  - Status: ⏳ Not Started
- [ ] **1.5.2** Store GitHub tokens securely (secrets manager)
  - Owner: Backend Team
  - Estimate: 4h
  - Status: ⏳ Not Started
- [ ] **1.5.3** Implement repository access API
  - Owner: Backend Team
  - Estimate: 8h
  - Status: ⏳ Not Started
- [ ] **1.5.4** Implement file content retrieval
  - Owner: Backend Team
  - Estimate: 8h
  - Status: ⏳ Not Started
- [ ] **1.5.5** Implement pull request analysis
  - Owner: Backend Team
  - Estimate: 12h
  - Status: ⏳ Not Started
- [ ] **1.5.6** Implement commit history analysis
  - Owner: Backend Team
  - Estimate: 8h
  - Status: ⏳ Not Started

#### Task 1.6: Rate Limiting & Caching
- [ ] **1.6.1** Implement GitHub API rate limit handling
  - Owner: Backend Team
  - Estimate: 8h
  - Status: ⏳ Not Started
- [ ] **1.6.2** Implement response caching (Redis)
  - Owner: Backend Team
  - Estimate: 8h
  - Status: ⏳ Not Started
- [ ] **1.6.3** Implement exponential backoff
  - Owner: Backend Team
  - Estimate: 4h
  - Status: ⏳ Not Started

### Week 7-8: SonarQube Integration & Autonomous Review

#### Task 1.7: SonarQube Integration
- [ ] **1.7.1** Implement SonarQube API client
  - Owner: Backend Team
  - Estimate: 8h
  - Status: ⏳ Not Started
- [ ] **1.7.2** Implement quality gate checks
  - Owner: Backend Team
  - Estimate: 8h
  - Status: ⏳ Not Started
- [ ] **1.7.3** Implement code quality metrics retrieval
  - Owner: Backend Team
  - Estimate: 8h
  - Status: ⏳ Not Started
- [ ] **1.7.4** Implement issue/vulnerability retrieval
  - Owner: Backend Team
  - Estimate: 8h
  - Status: ⏳ Not Started

#### Task 1.8: Basic Autonomous Review
- [x] **1.8.1** Implement autonomous review initiation endpoint
  - Owner: Backend Team
  - Estimate: 8h
  - Status: ✅ Done (POST /api/autonomous-reviews/ — validates project, checklist, source path; creates job; fires BackgroundTask)
- [x] **1.8.2** Implement checklist-to-data-source mapping
  - Owner: Backend Team
  - Estimate: 8h
  - Status: ✅ Done (app/services/autonomous_review/strategy_router.py — routes all 152 checklist items across 5 strategies based on area + question keywords)
- [x] **1.8.3** Implement basic verification logic (all 152 items — exceeded target of 15-20)
  - Owner: Backend Team
  - Estimate: 16h
  - Status: ✅ Done — 5 analyzers implemented:
    - file_presence (13% of items) — checks for architecture docs, CI/CD, README, HLD/LLD, Dockerfile
    - pattern_scan (7%) — regex scans for secrets, HTTPS, test count, error handling, retry patterns
    - llm_analysis (34%) — top-3 relevant files sent to LLM (gpt-4o-mini), returns RAG + evidence + confidence
    - metadata_check (3%) — Dependabot/Snyk config, coverage thresholds
    - human_required (43%) — financial, governance, people items flagged with evidence hints
- [x] **1.8.4** Generate autonomous review findings
  - Owner: Backend Team
  - Estimate: 8h
  - Status: ✅ Done (GET /api/autonomous-reviews/{job_id}/report — structured report with red/amber/green/skipped sections, compliance score, recommendations)
- [x] **1.8.5** Store autonomous review results in database
  - Owner: Backend Team
  - Estimate: 4h
  - Status: ✅ Done (AutonomousReviewJob + AutonomousReviewResult models in app/models.py)

#### Task 1.8 (Additional — not in original plan)
- [x] **1.8.6** Real-time WebSocket progress streaming
  - Status: ✅ Done (WS /ws/autonomous-reviews/{job_id} — broadcasts scanning → scan_complete → item_start → item_complete → completed)
- [x] **1.8.7** Frontend UI for autonomous reviews
  - Status: ✅ Done (static/index.html served at /ui — login, project/checklist selector, live results table, report view; report history page added at /history)
- [x] **1.8.8** Host path scanning via Docker volume mount
  - Status: ✅ Done (C:\projects mounted as /host-projects:ro in docker-compose.yml — enables scanning local microservices)
- [x] **1.8.9** Microservices support assessment + roadmap
  - Status: ✅ Done (docs/MICROSERVICES_REVIEW_PLAN.md — 5-phase plan; current support: one service at a time via /host-projects/ path)
- [x] **1.8.10** Report History UI at /history (view all reports, edit source path, override RAG)
  - Status: ✅ Done
- [x] **1.8.11** Agent bridge API (7 endpoints at /api/v1/agent/scan/) for reviewbot-agent CLI
  - Status: ✅ Done (upload, start, status, results, override, file-content, file-requests)
- [x] **1.8.12** V2 database schema (23 tables including 11 new v2 tables via models.py)
  - Status: ✅ Done
- [x] **1.8.13** Fixed reports.py missing router = APIRouter() bug
  - Status: ✅ Done
- [x] **1.8.14** Multi-provider LLM support in autonomous review (Groq, OpenAI, Anthropic, Google, Azure)
  - Status: ✅ Done (llm_analyzer.py — provider-aware client + model selection via ACTIVE_LLM_PROVIDER)
- [x] **1.8.15** reviewbot-agent CLI: 2-phase upload (metadata → file content → start)
  - Status: ✅ Done — fixes race condition where LLM items were skipped before files arrived
- [x] **1.8.16** Agent metadata capture + storage (hostname, IP, OS, username, agent version)
  - Status: ✅ Done (agent_metadata JSONB column on autonomous_review_jobs; displayed in Details UI)
- [x] **1.8.17** History UI — source path fix, table responsive resize, agent metadata chips in details
  - Status: ✅ Done
- [x] **1.8.18** JWT token expiry extended to 8 hours (was 30 min — too short for CLI sessions)
  - Status: ✅ Done
- [x] **1.8.19** DB-driven routing rules (ChecklistRoutingRule table; admin/PM/lead can mark items human_required)
  - Status: ✅ Done (POST/GET/DELETE /api/routing-rules/items/{item_id})

### Phase 1 Deliverables

- [x] ✅ Database schema (core tables + AutonomousReviewJob + AutonomousReviewResult)
- [x] ✅ Base API endpoints (Auth, Projects, Checklists, Reviews, Reports, Autonomous Reviews)
- [x] ✅ Full autonomous review — all 152 checklist items across 5 strategies
- [x] ✅ Real-time WebSocket progress stream
- [x] ✅ Frontend UI at /ui (login, project selector, live results, report view)
- [x] ✅ Development environment (Docker — PostgreSQL 15 on port 5435)
- [x] ✅ Seed scripts (seed_data.sql, seed_hatchpay.sql, migrate_xlsx_to_db.py)
- [x] ✅ Postman collection (25 requests, auto-token)
- [x] ✅ Host path scanning via Docker volume mount (/host-projects)
- [ ] ⏳ GitHub integration (OAuth, repository access)
- [ ] ⏳ SonarQube integration (quality metrics)
- [ ] ⏳ CI/CD pipeline

### Phase 1 Success Criteria

- [x] All database migrations run successfully
- [x] Core API endpoints implemented (Auth, Projects, Checklists, Reviews, Reports)
- [x] Autonomous review completes successfully (all 152 items, < 5 min for single service)
- [x] Real-time progress visible in UI during scan
- [ ] GitHub OAuth working end-to-end
- [ ] SonarQube quality metrics retrieved successfully
- [ ] Code coverage > 80%
- [ ] All Phase 1 tests passing

---

## 🎯 Phase 1c: Two-Track Action Item System (2 weeks)

**Status:** 📋 Planned
**Start:** April 14, 2026
**Duration:** 2 weeks
**Depends on:** Phase 1 (Autonomous Review)
**Requirements:** FR-21.1 – FR-21.4

### Goal
Transform raw review results into actionable, developer-ready output — structured action cards for teams and copy-paste AI IDE prompts for developers.

### Key Deliverables
- `app/services/action_plan_generator.py` — assembles action plan from existing review data (no new DB schema)
- `GET /api/autonomous-reviews/{job_id}/action-plan` — new endpoint
- `POST /api/autonomous-reviews/{job_id}/action-plan/enhance` — optional LLM prompt enrichment (202 Async)
- Action Plan tab in `history.html` with expand-to-reveal prompts, IDE flavour toggle, copy buttons, export

### Tasks

#### Week 1: Backend

- [ ] **1c.1** Create `app/services/action_plan_generator.py`
  - `ActionPlanGenerator.generate()` — assemble Track 2 cards from AutonomousReviewResult + ChecklistItem + Project
  - `ActionPlanGenerator._build_prompt()` — template-based Track 1 prompt per card (generic / cursor / claude_code flavours)
  - Estimate: 8h

- [ ] **1c.2** Add `GET /api/autonomous-reviews/{job_id}/action-plan` endpoint in `app/api/routes/reports.py`
  - Loads results with selectinload, calls generator, returns structured response
  - Estimate: 4h

- [ ] **1c.3** Add `POST /api/autonomous-reviews/{job_id}/action-plan/enhance` endpoint
  - Background LLM enrichment; caches enriched prompts in `AutonomousReviewJob.agent_metadata["action_plan_prompts"]`
  - Estimate: 6h

- [ ] **1c.4** Unit tests for `ActionPlanGenerator` (red/amber/green grouping, prompt template correctness, tech stack injection)
  - Estimate: 4h

#### Week 2: Frontend

- [ ] **1c.5** Add "Action Plan" tab to `history.html` details view
  - IDE flavour toggle (Generic / Cursor / Claude Code) stored in localStorage
  - Render Track 2 action cards grouped by priority
  - Expand-to-reveal Track 1 prompt per card
  - Estimate: 8h

- [ ] **1c.6** Copy-to-clipboard per prompt (Clipboard API + visual feedback)
  - Estimate: 2h

- [ ] **1c.7** "Export Action Plan" button → download Markdown with all cards + prompts
  - Estimate: 3h

- [ ] **1c.8** "Enhance with AI" button — calls enhance endpoint, polls until done, refreshes prompts
  - Estimate: 4h

- [ ] **1c.9** Integration test: full review → action plan endpoint → verify grouping and prompt fields populated
  - Estimate: 3h

### Definition of Done
- [ ] Action plan renders for any completed autonomous review job
- [ ] All red/amber items produce action cards with populated evidence, fix guidance, and all 3 prompt flavours
- [ ] Copy button works; Export downloads valid Markdown
- [ ] "Enhance with AI" enriches prompts and refreshes UI without page reload
- [ ] Tests pass

---

## 📋 Phase 1b: Repository Integration + Source Types (2 weeks)

**Status:** 📋 Planned
**Start:** April 28, 2026
**Duration:** 2 weeks

### Key Features
- GitHub/GitLab/Bitbucket public and private repo support
- Personal Access Token (PAT) secure storage per project
- UI redesign: source type selector (Repo URL / Local Path / Upload Agent)
- Branch/tag/commit selection
- Auto-detect provider from URL
- PAT generation guide per provider
- VS Code Extension (replaces reviewbot-agent CLI for developer use)
- reviewbot-agent CLI: fix login to use JWT (email/password) instead of API key

### Tasks
- [ ] 1b.1 Repo connector service (clone/fetch via URL + token)
- [ ] 1b.2 Encrypted PAT storage per project
- [ ] 1b.3 UI: source type selector + repo URL + token field + branch selector
- [ ] 1b.4 Provider auto-detection (github.com / gitlab.com / bitbucket.org / Azure DevOps)
- [ ] 1b.5 PAT guidance tooltips per provider in UI
- [ ] 1b.6 VS Code extension scaffold (sidebar panel, auth, review trigger)

VS Code Extension capabilities:
- Sidebar panel: project selector, checklist selector, start review
- Direct file system access (workspace folder) - no metadata-only limitation
- Auth: email/password login stored in VS Code secrets
- Real-time progress in output panel
- Inline code annotations for red/amber items
- No install beyond VS Code marketplace

- [ ] 1b.7 Fix reviewbot-agent login: use email/password → JWT (no API key)

---

## 📋 Phase 2: Document Review Engine (6 weeks)

**Status:** 📋 Planned
**Start:** May 12, 2026
**Duration:** 6 weeks

### Key Features
- Upload and parse: PDF, Word (.docx), Markdown, Confluence pages
- Document types: HLD, LLD, Architecture Doc, Process Doc, Runbook, Compliance Doc
- AI-powered gap analysis against checklist requirements
- Document completeness scoring
- Cross-reference documents with code findings
- Extract key decisions, assumptions, risks from documents
- Document review report generation

### Tasks
- [ ] 2.1 Document upload API (PDF, DOCX, MD support)
- [ ] 2.2 Document parser (extract structured text + sections)
- [ ] 2.3 Document-to-checklist mapper (AI-powered)
- [ ] 2.4 Gap analysis engine (what's missing vs checklist)
- [ ] 2.5 Document completeness scorer
- [ ] 2.6 Key decision/assumption extractor (LLM)
- [ ] 2.7 Combined report: code + document findings
- [ ] 2.8 Confluence integration (pull pages by URL)

---

## 📋 Phase 3: Knowledge QUIZ / QUIZE (text + voice) (6 weeks)

**Status:** 📋 Planned
**Start:** June 23, 2026
**Duration:** 6 weeks

### Key Features
- Domain-specific knowledge quizzes per role/persona (PM, Tech Lead, DevOps, QA, Security)
- Text mode: conversational Q&A in the browser
- Voice mode: AI speaks questions (TTS), listens to answers (STT), responds verbally
- Adaptive questioning: follow up on weak/vague answers
- Per-domain scoring: architecture, security, DevOps, domain knowledge
- Team knowledge gap report (anonymised)
- Track knowledge improvement over time
- Custom QUIZ templates per project domain
- Multi-participant QUIZ sessions

### Tasks
- [ ] 3.1 QUIZ template system (per domain, per role)
- [ ] 3.2 Text-mode QUIZ session API + UI
- [ ] 3.3 Voice-mode QUIZ (STT input → LLM assessment → TTS response)
- [ ] 3.4 Adaptive follow-up question engine
- [ ] 3.5 Per-domain knowledge scoring
- [ ] 3.6 Team gap report generation (anonymised)
- [ ] 3.7 Individual knowledge trend tracking
- [ ] 3.8 QUIZ results integrated into self-review report

---

## 📋 Phase 4: Self-Review Core (8 weeks)

**Status:** 📋 Planned
**Start:** August 4, 2026
**Duration:** 8 weeks

### Key Features
- [ ] Self-review session management
- [ ] Single review mode implementation
- [ ] Persona-based review mode implementation
- [ ] Checklist template system
- [ ] Report generation (individual + consolidated)
- [ ] Recurring review scheduling

### Tasks (High-Level)
- [ ] **4.1** Self-review session CRUD
- [ ] **4.2** Persona-based session handling
- [ ] **4.3** Individual report generation
- [ ] **4.4** Consolidated report generation
- [ ] **4.5** Recurring review scheduler (Celery Beat)
- [ ] **4.6** Milestone-triggered reviews

---

## 📋 Phase 5: Accountability & Scheduling (6 weeks)

**Status:** 📋 Planned
**Start:** October 1, 2026
**Duration:** 6 weeks

### Key Features
- [ ] Automated reminder system
- [ ] Escalation workflow
- [ ] Meeting blocking logic
- [ ] Exception approval workflow
- [ ] Stakeholder notification system

### Tasks (High-Level)
- [ ] **5.1** Reminder scheduling system
- [ ] **5.2** Email templates
- [ ] **5.3** Escalation workflow
- [ ] **5.4** Meeting blocking
- [ ] **5.5** Exception approval
- [ ] **5.6** Stakeholder notifications

---

## 📋 Phase 6: Meeting Integration (Teams/Zoom) (8 weeks)

**Status:** 📋 Planned
**Start:** November 12, 2026
**Duration:** 8 weeks

### Key Features
- [ ] Teams bot adapter
- [ ] Zoom bot adapter
- [ ] Real-time transcription pipeline
- [ ] TTS integration
- [ ] Turn-taking detection
- [ ] Speaker identification

### Tasks (High-Level)
- [ ] **6.1** Microsoft Teams bot integration
- [ ] **6.2** Zoom bot integration
- [ ] **6.3** Real-time STT (Whisper Streaming)
- [ ] **6.4** TTS integration
- [ ] **6.5** Turn-taking detection
- [ ] **6.6** Speaker identification

---

## 📋 Phase 7: Control Panel UI (8 weeks)

**Status:** 📋 Planned
**Start:** January 7, 2027
**Duration:** 8 weeks

### Key Features
- [ ] Control panel web application
- [ ] Mute/Speak toggle
- [ ] Question approval queue
- [ ] Real-time status indicators
- [ ] Mobile-responsive design
- [ ] Meeting plugin (Teams/Zoom)

### Tasks (High-Level)
- [ ] **7.1** UI mockups (Figma)
- [ ] **7.2** Component library
- [ ] **7.3** Control panel frontend (React)
- [ ] **7.4** Mute/Speak toggle implementation
- [ ] **7.5** Question approval queue UI
- [ ] **7.6** Meeting plugin UI

---

## 📋 Phase 8: Analytics & Trends (6 weeks)

**Status:** 📋 Planned
**Start:** March 4, 2027
**Duration:** 6 weeks

### Key Features
- [ ] Review history dashboard
- [ ] Trend analysis engine
- [ ] Gap closure metrics
- [ ] Readiness score trends
- [ ] Team performance analytics
- [ ] Export functionality

### Tasks (High-Level)
- [ ] **8.1** Analytics database tables
- [ ] **8.2** Trend analysis engine
- [ ] **8.3** Dashboard API endpoints
- [ ] **8.4** Frontend dashboard (React)
- [ ] **8.5** Export functionality (PDF, CSV)
- [ ] **8.6** Gap closure tracking

---

## 🚀 Future Phases (Q1 2027+)

### Phase 9: Extended Capabilities
- [ ] AWS infrastructure verification (FR-12)
- [ ] Database connectivity & verification (FR-13)
- [ ] Deployment auditing (FR-14)

### Phase 10: Multi-Agent Collaboration
- [ ] A2A protocol implementation (FR-15)
- [ ] MCP integration (FR-15)
- [ ] OpenClaw integration (FR-15)

### Phase 11: Skills Marketplace
- [ ] Skills marketplace UI (FR-16)
- [ ] Skill SDK/API (FR-16)
- [ ] Community skills (FR-16)

---

## 📊 Tracking & Reporting

### Weekly Status Updates

**Every Friday:**
- Update task status (Not Started → In Progress → Done)
- Log actual hours vs estimates
- Identify blockers
- Plan next week's tasks

**Status Indicators:**
- ⏳ Not Started
- 🔄 In Progress
- ✅ Done
- 🚫 Blocked

### Burn-down Chart

```
Week 1-2:  ████████████████████ 100% (Database & Infrastructure)
Week 3-4:  ████████████████████ 100% (Base APIs)
Week 5-6:  ████████████████████ 100% (GitHub Integration)
Week 7-8:  ████████████████████ 100% (SonarQube + Autonomous)
```

### Risk Register

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| GitHub API rate limits | Medium | Medium | Caching, backoff |
| SonarQube integration complexity | Medium | Low | Early POC |
| Database migration issues | High | Low | Test on staging first |
| Team capacity constraints | High | Medium | Prioritize, defer non-critical |

---

## 📞 Governance

### Daily Standup
- **When:** Daily, 9:45 AM
- **Duration:** 15 minutes
- **Attendees:** All team members
- **Format:** What I did yesterday, What I'll do today, Blockers

### Sprint Cadence
- **Sprint Length:** 2 weeks
- **Sprint Planning:** First Monday of sprint
- **Sprint Review:** Last Friday of sprint
- **Retrospective:** After review

### Architecture Review
- **When:** Weekly, Wednesdays 2 PM
- **Attendees:** Architecture Team, Tech Leads
- **Focus:** Design decisions, technical debt, code quality

---

## 🔗 Related Documents

- [Requirements Document](requirements.md)
- [Database Schema](DATABASE_SCHEMA_V2.md)
- [Integration Specs](INTEGRATION_SPECS.md)
- [Design Phase Status](DESIGN_PHASE_STATUS.md)

---

*Document Owner: Engineering Team*
*Last Updated: March 28, 2026*
*Next Update: After Phase 1 Week 2 (GitHub integration)*

---

## 📝 Phase 1 Progress Notes

### Session 1 — March 27, 2026 (Infrastructure + APIs)

- **Infrastructure**: Docker environment fully configured (PostgreSQL 15 on port 5435). Port 5435 used to avoid conflict with local PostgreSQL on 5432.
- **Database**: Core schema tables created and tested. Real project data migrated from Excel files (AAA PDH + NeUMoney — 456 checklist items, 304 review responses, 6 checklists, 4 reviews, 4 reports).
- **API**: All core CRUD endpoints implemented and fixed for async SQLAlchemy (selectinload pattern required for all relationship access).
- **Bug fixes (Session 1)**: Fixed critical bugs in agent.py (wrong parameter name), report_generator.py (missing import), models.py (deprecated import), config.py (extra env vars rejected), reviews/reports/checklists routes (MissingGreenlet async issue).
- **Scripts created**: `scripts/db_test.py` (schema + sample data), `scripts/migrate_xlsx_to_db.py` (full Excel migration).

### Session 2 — March 27, 2026 (Autonomous Review — Full Implementation)

**Completed all of Task 1.8 and beyond:**

- **Autonomous review engine** — full pipeline: LocalFolderConnector (file indexer) → StrategyRouter (152 items across 5 strategies) → 5 analyzers (file_presence, pattern_scan, llm_analysis, metadata_check, human_required) → AutonomousReviewResult storage
- **WebSocket progress** — real-time per-item broadcasts (scanning → scan_complete → started → item_start → item_complete → completed/error) via ProgressManager singleton
- **REST API** — POST/GET/DELETE /api/autonomous-reviews/ + GET /report endpoint with structured findings
- **Frontend UI** — single-page app at /ui (dark theme, login overlay, project/checklist selector, live results table with RAG colour coding, report panel)
- **Postman collection** — 25 requests, auto-saves token/project_id/review_id/job_id

**Bug fixes (Session 2)**:
- Auth: `/register` was not saving to DB; `/login` used hardcoded `db.get(User, 1)` instead of email lookup — both fixed
- bcrypt==4.0.1 pinned to fix passlib scram-sha-256 incompatibility
- PostgreSQL init SQL: removed `SET password_encryption = 'md5'` (PG15 needs scram-sha-256)
- DATABASE_URL port fixed: `db:5435` → `db:5432` (internal Docker port)
- Projects checklists endpoint: added `selectinload(Checklist.items)` to fix MissingGreenlet crash
- UI: fixed `(projects || []).forEach is not a function` — API returns `{projects: [...]}` not a plain array

**Seed data**:
- `scripts/seed_data.sql` — pre-generated full seed (users + AAA PDH + NeUMoney + global checklists)
- `scripts/seed_hatchpay.sql` — Hatch Pay project (copies NeUMoney delivery + technical data)
- `scripts/generate_seed.py` — regenerates seed_data.sql from xlsx source files

**Microservices**:
- Mounted `C:\projects` as `/host-projects:ro` in Docker — enables scanning local project folders
- Assessed microservices support: one service at a time works; full fleet scanning needs Phase 2+ work
- Created `docs/MICROSERVICES_REVIEW_PLAN.md` — 5-phase roadmap (~8–9 days to full fleet support)

### Session 3 — March 28, 2026 (reviewbot-agent CLI + LLM Fix + Security)

- **reviewbot-agent CLI integration**: Full end-to-end working. 2-phase upload (metadata scan → file content → start trigger) eliminates race condition. 192 files uploaded in ~3 s; 26 LLM items now properly analyzed.
- **Multi-provider LLM**: llm_analyzer.py now routes to correct API client + model per provider (Groq → llama-3.3-70b-versatile, OpenAI → gpt-4o-mini, etc.). Fixed "Connection error" caused by always using AsyncOpenAI with empty OPENAI_API_KEY.
- **Agent metadata**: Hostname, IP, OS, username, agent version captured at scan time and stored in DB (JSONB column). Displayed as chips in the Details panel.
- **Security hardening**: JWT expiry increased 30 min → 8 hours. Agent info logged per job for auditability.
- **Docs reorganisation**: Root .md files moved to docs/ops/ and docs/archive/; docs folder now the single source of truth.
- **History UI**: Table horizontal scroll fix (overflow-x: auto + min-width: 860px). Source path now sent from CLI. Agent metadata banner in details view.

### Session 4 — March 30, 2026 (Production GCP Migration)

- **GCP Infrastructure**: Deployed `reviewbot-web` to Cloud Run and `reviews_db_dev1` to Cloud SQL. Configured asyncpg driver for production connectivity.
- **Database Restoration**: Modularised SQL schema into 5 stages (Extensions, Tables, Constraints, Indexes, Data). Fixed sequence primary key ownership order in `02_tables.sql`.
- **Operational Docs**: Created `docs/GCP_TROUBLESHOOTING.md` with common `gcloud` commands for logs, deployment, and multi-account management.
- **Workspace Cleanup**: Archived stale 1.0 phase docs to `docs/archive/`. Updated all root documentation (README, Design, Architecture, Roadmap) to reflect production-ready status.
- **Security**: Synchronized `SECRET_KEY` between Cloud Run and clients to ensure stable JWT authentication.

### Current Blockers / Next Priorities

- **Two-Track Action Item System**: Implementation of action cards and AI IDE prompts (Phase 1c).
- **Checklist item editor**: Admin/PM/DM UI to add/edit/delete checklist items.
- **Cloud Monitoring**: Configure official alerts for 5xx errors and database connections in GCP Console.
