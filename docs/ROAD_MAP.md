# ReviewBot v2.0 - Implementation Roadmap

> Complete implementation plan with phases, tasks, and tracking

**Version:** 2.0
**Last Updated:** March 27, 2026
**Status:** Phase 1 — Autonomous Review Complete; GitHub/SonarQube pending
**Owner:** Engineering Team

---

## 📊 Implementation Overview

| Phase | Name | Duration | Status | Start Date | End Date |
|-------|------|----------|--------|------------|----------|
| **Phase 1** | Foundation | 8 weeks | 🔄 In Progress | Mar 27, 2026 | May 27, 2026 |
| **Phase 2** | Self-Review Core | 8 weeks | 📋 Planned | May 28, 2026 | Jul 22, 2026 |
| **Phase 3** | Accountability | 6 weeks | 📋 Planned | Jul 23, 2026 | Sep 2, 2026 |
| **Phase 4** | Meeting Integration | 8 weeks | 📋 Planned | Sep 3, 2026 | Oct 28, 2026 |
| **Phase 5** | Control Panel UI | 8 weeks | 📋 Planned | Oct 29, 2026 | Dec 23, 2026 |
| **Phase 6** | Analytics | 6 weeks | 📋 Planned | Dec 24, 2026 | Feb 3, 2027 |

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
  - Status: ✅ Done (PostgreSQL 15 in Docker on port 5435; fixed port conflict with local PostgreSQL)
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

#### Task 1.2: Development Infrastructure
- [x] **1.2.1** Setup Docker development environment
  - Owner: DevOps
  - Estimate: 4h
  - Status: ✅ Done (docker-compose.yml fixed: health checks, env defaults, removed duplicate env blocks)
- [ ] **1.2.2** Configure CI/CD pipeline (GitHub Actions)
  - Owner: DevOps
  - Estimate: 8h
  - Status: ⏳ Not Started
- [x] **1.2.3** Setup Redis for caching
  - Owner: DevOps
  - Estimate: 4h
  - Status: ✅ Done (Redis 7 Alpine in docker-compose, AOF persistence enabled)
- [ ] **1.2.4** Configure Celery for async tasks
  - Owner: Backend Team
  - Estimate: 8h
  - Status: ⏳ Not Started
- [ ] **1.2.5** Setup logging & monitoring (ELK stack)
  - Owner: DevOps
  - Estimate: 8h
  - Status: ⏳ Not Started

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
  - Status: ✅ Done (static/index.html served at /ui — login, project/checklist selector, live results table, report view)
- [x] **1.8.8** Host path scanning via Docker volume mount
  - Status: ✅ Done (C:\projects mounted as /host-projects:ro in docker-compose.yml — enables scanning local microservices)
- [x] **1.8.9** Microservices support assessment + roadmap
  - Status: ✅ Done (docs/MICROSERVICES_REVIEW_PLAN.md — 5-phase plan; current support: one service at a time via /host-projects/ path)

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

## 📋 Phase 2: Self-Review Core (8 weeks)

**Status:** 📋 Planned  
**Duration:** May 28 - July 22, 2026

### Key Features
- [ ] Self-review session management
- [ ] Single review mode implementation
- [ ] Persona-based review mode implementation
- [ ] Checklist template system
- [ ] Report generation (individual + consolidated)
- [ ] Recurring review scheduling

### Tasks (High-Level)
- [ ] **2.1** Self-review session CRUD
- [ ] **2.2** Persona-based session handling
- [ ] **2.3** Individual report generation
- [ ] **2.4** Consolidated report generation
- [ ] **2.5** Recurring review scheduler (Celery Beat)
- [ ] **2.6** Milestone-triggered reviews

---

## 📋 Phase 3: Accountability (6 weeks)

**Status:** 📋 Planned  
**Duration:** July 23 - September 2, 2026

### Key Features
- [ ] Automated reminder system
- [ ] Escalation workflow
- [ ] Meeting blocking logic
- [ ] Exception approval workflow
- [ ] Stakeholder notification system

### Tasks (High-Level)
- [ ] **3.1** Reminder scheduling system
- [ ] **3.2** Email templates
- [ ] **3.3** Escalation workflow
- [ ] **3.4** Meeting blocking
- [ ] **3.5** Exception approval
- [ ] **3.6** Stakeholder notifications

---

## 📋 Phase 4: Meeting Integration (8 weeks)

**Status:** 📋 Planned  
**Duration:** September 3 - October 28, 2026

### Key Features
- [ ] Teams bot adapter
- [ ] Zoom bot adapter
- [ ] Real-time transcription pipeline
- [ ] TTS integration
- [ ] Turn-taking detection
- [ ] Speaker identification

### Tasks (High-Level)
- [ ] **4.1** Microsoft Teams bot integration
- [ ] **4.2** Zoom bot integration
- [ ] **4.3** Real-time STT (Whisper Streaming)
- [ ] **4.4** TTS integration
- [ ] **4.5** Turn-taking detection
- [ ] **4.6** Speaker identification

---

## 📋 Phase 5: Control Panel UI (8 weeks)

**Status:** 📋 Planned  
**Duration:** October 29 - December 23, 2026

### Key Features
- [ ] Control panel web application
- [ ] Mute/Speak toggle
- [ ] Question approval queue
- [ ] Real-time status indicators
- [ ] Mobile-responsive design
- [ ] Meeting plugin (Teams/Zoom)

### Tasks (High-Level)
- [ ] **5.1** UI mockups (Figma)
- [ ] **5.2** Component library
- [ ] **5.3** Control panel frontend (React)
- [ ] **5.4** Mute/Speak toggle implementation
- [ ] **5.5** Question approval queue UI
- [ ] **5.6** Meeting plugin UI

---

## 📋 Phase 6: Analytics (6 weeks)

**Status:** 📋 Planned  
**Duration:** December 24, 2026 - February 3, 2027

### Key Features
- [ ] Review history dashboard
- [ ] Trend analysis engine
- [ ] Gap closure metrics
- [ ] Readiness score trends
- [ ] Team performance analytics
- [ ] Export functionality

### Tasks (High-Level)
- [ ] **6.1** Analytics database tables
- [ ] **6.2** Trend analysis engine
- [ ] **6.3** Dashboard API endpoints
- [ ] **6.4** Frontend dashboard (React)
- [ ] **6.5** Export functionality (PDF, CSV)
- [ ] **6.6** Gap closure tracking

---

## 🚀 Future Phases (Q1 2027+)

### Phase 7: Extended Capabilities
- [ ] AWS infrastructure verification (FR-12)
- [ ] Database connectivity & verification (FR-13)
- [ ] Deployment auditing (FR-14)

### Phase 8: Multi-Agent Collaboration
- [ ] A2A protocol implementation (FR-15)
- [ ] MCP integration (FR-15)
- [ ] OpenClaw integration (FR-15)

### Phase 9: Skills Marketplace
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
*Last Updated: March 27, 2026*
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

### Current Blockers / Next Priorities

- **1.2.2**: CI/CD pipeline (GitHub Actions) — not started
- **1.2.4**: Celery for async tasks — BackgroundTasks used for now (adequate for MVP)
- **1.5.x**: GitHub OAuth + repository access — next major feature
- **1.7.x**: SonarQube integration — next major feature
- **Microservices Phase 2**: Per-service job mode — needs schema change (service_name column on results)
