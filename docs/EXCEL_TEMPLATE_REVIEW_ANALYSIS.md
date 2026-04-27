# Excel Template-Based External Review - Feature Analysis

**Date:** 2026-04-23
**Last Updated:** 2026-04-26 (v1.6 - Phase 1 item 1 complete; org-scoped global checklists implemented)
**Status:** In Progress
**Author:** Mallikarjun Shankesi
**Reviewed by:** Codex

---

## 1. Executive Summary

The Excel template-based external review feature is still a strong product opportunity, but the design should now be tightened around a single operating model:

- One global master checklist is the source of truth
- Each project gets its own editable project-scoped checklist derived from that master
- Each external review is distributed as team-scoped Excel exports generated from a frozen review snapshot
- Teams upload their scoped responses independently
- The system consolidates those uploads into one review report

This is better than maintaining two separate standard templates forever, and it is safer than sending one giant spreadsheet to everyone. The right target is not "one raw Excel for all teams." The right target is "one global checklist library, many filtered project/team views."

The async review flow remains the first shipping milestone. Live review should remain a later enhancement. Screen sharing and full duplex voice conversation should stay out of scope.

---

## 2. Updated Product Decision

### 2.1 Recommended Operating Model

ReviewBot should move to a **single global master checklist** that contains all review questions across technical, delivery, governance, resourcing, client, and behavioral areas.

That master checklist should not be used directly as the distributed file. Instead:

1. A reviewer selects the global master checklist during project setup
2. ReviewBot creates a **project checklist copy** that can be edited for that project
3. The reviewer assigns teams and owners to checklist categories
4. ReviewBot generates one or more **team-scoped Excel templates**
5. ReviewBot freezes a **review snapshot** at distribution time so later template edits do not break uploads

### 2.2 Why This Is Better Than the Current Two-Template Model

The current two-template model (`technical` and `delivery`) is too rigid once ownership is introduced. It creates artificial boundaries between questions that are really part of the same review journey.

With a single master checklist:

- one source of truth is easier to maintain
- cross-functional reviews no longer require merging results from unrelated base templates
- item ownership can be modeled per question instead of per file
- project-specific exclusions and overrides become easier
- future web-based review flows can reuse the same data model

### 2.3 Important Clarification

The recommendation is **one global checklist source**, not one giant spreadsheet that every team edits directly.

For Milestone 1, the best UX is still:

- one project-scoped checklist in ReviewBot
- one frozen snapshot per review run
- one Excel export per team

---

## 3. Clarified Design Principles

### 3.1 Separate the Four Layers

The previous design mixed template structure, project customization, team assignment, and runtime review state. These should be distinct layers:

| Layer | Purpose | Editable? |
|------|---------|-----------|
| Global master checklist | Source-of-truth library of all possible questions | Yes, by admins/template authors |
| Project checklist | Project-specific working copy derived from the master checklist | Yes, before distribution |
| Review snapshot | Frozen copy used for one external review cycle | No |
| Team distribution | Team-scoped Excel export or portal view derived from the snapshot | Response-only |

### 3.2 Separate Team Category From Owner

`Team Category` and `Owner` should not mean the same thing.

| Concept | Meaning |
|---------|---------|
| `team_category` | Structural classification on the checklist item, such as Development, QA, DevOps, Delivery |
| `review_team` | Project-specific team participating in the review, such as "iOS Development" |
| `assigned_owner` | Named person responsible for responding for that team's scoped items |

This avoids baking temporary project assignments into the global template itself.

### 3.3 Edit Timing Rule

The user suggestion is good with one guardrail:

- Reviewers should be able to edit, delete, exclude, or reassign checklist items **after project creation and before distribution**
- Once team files are distributed, the checklist for that review should be frozen
- If the reviewer needs to change the review after distribution, the system should create a new review revision or regenerate the team exports

This protects upload integrity and prevents version mismatch confusion.

---

## 4. Updated Detailed Design

### 4.1 Global Master Checklist

Each checklist item in the global master checklist should include:

| Field | Purpose |
|------|---------|
| Item ID | Stable internal identifier |
| Area | High-level grouping |
| Question | Review prompt |
| Guidance | One to two sentences explaining what a good answer contains |
| Team Category | Development, QA, DevOps, CloudOps, Delivery, Governance, Resourcing, Client, Human Behavioural |
| Expected Evidence | Suggested artifacts |
| Weight | Scoring weight |
| Mandatory Flag | Whether the item blocks completion when applicable |
| Applicability Tags | Optional filters such as project type, phase, domain, platform |

### 4.2 Project Checklist

At project creation, ReviewBot should derive a project-scoped checklist from the global master checklist. The reviewer can then:

- exclude irrelevant items
- edit wording where project language needs clarification
- adjust mandatory flags
- reassign team category for project-specific ownership
- add a few project-only custom questions if needed

This project checklist is the working surface the reviewer owns before distribution.

### 4.3 Review Teams

Each project review defines one or more participating teams:

| Field | Example |
|------|---------|
| Team name | iOS Development |
| Team category | Development |
| Lead name | Savin Mathew |
| Lead email | savin@project.com |
| Team responsibility scope | iOS UI only - no backend, infra, or API visibility |

If a category has no mapped team, the reviewer must either:

- assign one
- exclude those items from the project checklist
- or proceed with those items marked unassigned and visible in the final report

### 4.4 Review Snapshot

When the reviewer clicks distribute, ReviewBot must create a frozen snapshot containing:

- the exact checklist item set
- the item text and guidance at that moment
- the project context used for scoring
- the mapped teams and owners
- the scoring rules for that run
- a snapshot version or checksum used during upload validation

This is the key gap missing from the earlier design. Without snapshot freezing, dynamic generation is unsafe.

### 4.5 Team-Scoped Excel Export

Each team should receive only its relevant rows.

Recommended Excel columns:

| Column | Editable | Notes |
|------|----------|-------|
| Snapshot ID | No | Used for upload validation |
| Item ID | No | Stable row mapping key |
| Area | No | Copied from checklist |
| Question | No | Copied from checklist |
| Guidance | No | Clarifies expected answer |
| Team Name | No | Distribution target |
| Assigned Owner | Yes | Defaults to team lead name |
| Response State | Yes | `answered`, `na_out_of_scope`, `delegated`, `needs_clarification` |
| Response | Yes | Main answer |
| Confidence | Yes | High / Medium / Low |
| Notes | Yes | Additional context |
| Questions / Doubts | Yes | Reviewee uncertainty or clarification request |
| Evidence Refs | Yes | Stable evidence IDs or upload placeholders, not just filenames |

Locked columns must be worksheet-protected. The parser should reject uploads where protected values do not match the snapshot.

### 4.6 Response State Model

The earlier design used plain `NA`, but the workflow needs more precision.

Recommended states:

| State | Meaning | Scoring Impact |
|------|---------|----------------|
| `answered` | Team provided an answer | Included in score |
| `na_out_of_scope` | Item is outside declared team responsibility | Excluded from denominator |
| `delegated` | Team knows another team should answer | Excluded for that team, flagged for reassignment |
| `needs_clarification` | Team cannot answer without clarification | Not scored until resolved |
| `not_submitted` | No response received | Blocks completion unless reviewer chooses partial report |

### 4.7 Scoring and Completion Rules

These rules should be explicit:

1. Only `answered` items count in the scoring denominator
2. `na_out_of_scope` items are excluded from the denominator and listed separately in the report
3. Mandatory items in `needs_clarification` or `not_submitted` state block completion by default
4. The reviewer can explicitly proceed with a partial report, but the report must show missing teams and incomplete items
5. Items marked `delegated` should be surfaced as assignment gaps, not scored as failures

### 4.8 Evidence Model

The previous filename-only model is too fragile.

Recommended change:

- each exported row gets a stable evidence slot identifier
- uploads are bound server-side to `snapshot_id + item_id + team_id`
- Excel may still show human-readable filenames, but parsing should not depend only on filename text

AI handling of evidence should stay conservative:

- acknowledge receipt
- extract visible text where feasible
- use evidence as supporting context
- do not claim deep review of screenshots or documents

### 4.9 Clarification Model

Milestone 1 should include:

- inline Guidance column
- Questions / Doubts column in Excel

Milestone 2 should include:

- async Q&A web surface against a specific review snapshot and item ID

### 4.10 Live Review Scope

Live review still makes sense as a later extension of the same model:

- present snapshot items one by one
- allow `explain`
- accept text or STT responses
- optionally request evidence

Do not build:

- screen sharing
- full duplex voice conversation
- real-time AI screen interpretation

---

## 5. Multi-Team Distribution Model

### 5.1 Team Category Taxonomy

| Category | Typical Owner | Question Types |
|----------|--------------|----------------|
| Development | Dev Lead / Tech Lead | Architecture, code quality, testing, technical debt |
| QA | QA Lead | Test coverage, defects, release quality |
| DevOps | DevOps Lead | CI/CD, deployment, environment controls |
| CloudOps | Infra Lead | Reliability, scalability, cost, observability |
| Delivery | Delivery Manager / PM | Milestones, scope, risk, communication |
| Governance | PMO / Governance | Compliance, process adherence, documentation controls |
| Resourcing | Delivery Manager / HR | Capacity, skills, attrition risk |
| Client | Account Manager | Client responsiveness, decision velocity, feedback cycle |
| Human Behavioural | Delivery Manager | Team morale, collaboration, conflict, engagement |

Design principle: one checklist item has one primary team category for ownership, even if multiple teams may care about the outcome.

### 5.2 Distribution Options

| Option | Description | Recommendation |
|--------|-------------|----------------|
| One Excel per team | Each team receives only its rows and uploads independently | Best for Milestone 1 |
| One workbook with one sheet per team | Easier for one coordinator, but weaker privacy separation | Optional later |
| Web portal | Each team responds in browser | Long-term target |

Recommendation: ship one Excel per team first.

### 5.3 Consolidated Report Structure

The consolidated report should include:

- executive summary
- overall score
- teams completed vs pending
- findings by team category
- cross-team conflicts
- unassigned or delegated items
- out-of-scope items
- prioritized recommendations with suggested owner

---

## 6. End-to-End Distribution Sequence

### What is the snapshot?

The snapshot is a **frozen point-in-time copy of the project checklist at the moment the reviewer chooses to distribute**. It captures:

| What is frozen | Why |
|----------------|-----|
| The exact item set (after reviewer exclusions and edits) | Upload validation needs a stable row list to match against |
| Item wording, guidance, and expected evidence | If the project checklist is edited later, teams' Excels stay consistent |
| Team-to-category mapping | Determines which rows go into which team's export |
| Mandatory flags, weights, and scoring rules | Score is reproducible and auditable after the fact |
| A snapshot version identifier and checksum | Lets the parser reject stale or tampered uploads |

The snapshot is **not** a copy of the global master checklist, not the project record, and not the responses (those arrive after distribution). Think of it as a tagged release: the project checklist is the main branch still open for edits; the snapshot is the commit that gets shipped. If a post-distribution change is required, a new snapshot revision is cut and the affected teams re-download.

---

### Distribution sequence diagram

```
Reviewer / Admin                  ReviewBot                         External Team
─────────────────                 ─────────────────                 ─────────────

1. Completes project checklist
   edits and team mapping
        │
        ▼
2. Clicks "Distribute"
        │
        ├──► [Snapshot service]
        │         Freezes item set, team mapping,
        │         mandatory flags, weights, guidance.
        │         Assigns snapshot_id + checksum.
        │         Stores as immutable DB record.
        │
        ├──► [Excel export service]
        │         Generates one workbook per team.
        │         Locks read-only columns.
        │         Embeds snapshot_id + team_id in
        │         protected metadata sheet.
        │         Adds data-validation dropdowns for
        │         Response State and Confidence.
        │
        ├──► [Distribution token service]
        │         Mints one signed, time-limited token
        │         per team scoped to snapshot_id + team_id.
        │         Records token creation in audit log.
        │
        └──► [SMTP / notification]
                  Sends email to each team lead with
                  a unique signed download link
                  (token embedded in URL).
                  ──────────────────────────────────────────────────────►
                                                              3. Team lead receives email
                                                                   │
                                                                   ▼
                                                              4. Opens signed download link
                                                                   │
                                                                   ▼
                                                              ◄── ReviewBot verifies token
                                                                   (not expired, not revoked,
                                                                   correct team).
                                                                   Serves team-scoped Excel.
                                                                   │
                                                                   ▼
                                                              5. Team fills in:
                                                                   - Response State (dropdown)
                                                                   - Response text
                                                                   - Confidence
                                                                   - Notes
                                                                   - Questions / Doubts
                                                                   - Evidence Refs
                                                                   │
                                                                   ▼
                                                              6. Uploads completed Excel
                                                                   via signed upload URL
                  ◄──────────────────────────────────────────────────────
        │
        ├──► [Upload parser]
        │         Reads metadata sheet: validates
        │         snapshot_id and checksum match
        │         server-side frozen record.
        │         Validates team_id matches upload token.
        │         Rejects if protected columns tampered.
        │         Parses response rows into ReviewResponse
        │         records (response_state, answer, notes,
        │         confidence, questions, evidence refs).
        │         Stores parse errors per row for surfacing
        │         back to reviewer.
        │
        ├──► [Notification to coordinator]
        │         Sends confirmation to reviewer:
        │         "Team X submitted N responses.
        │          Y rows have parse warnings."
        │
        └──► [Team upload status dashboard]
                  Updates status for this team from
                  "pending" to "submitted" (or "error").

        │
        ▼
7. Reviewer monitors upload status dashboard
   (shows: teams submitted, pending, errors per team)
        │
        ▼  (once all teams submitted, or reviewer
             chooses partial report)
8. Reviewer triggers "Generate Consolidated Report"
        │
        ├──► [Scoring engine]
        │         Applies denominator rules:
        │           - Only "answered" items count.
        │           - "na_out_of_scope" excluded from denominator.
        │           - "delegated" flagged as assignment gap.
        │           - "needs_clarification" blocks mandatory items.
        │           - "not_submitted" blocks completion (unless override).
        │         Calculates per-team and overall compliance score.
        │
        └──► [Report generator]
                  Produces consolidated report containing:
                    - Executive summary + overall score
                    - Per-team scores and status
                    - Missing / pending teams
                    - Findings grouped by team category
                    - Delegated items and assignment gaps
                    - Out-of-scope items
                    - Clarification questions outstanding
                    - Prioritised recommendations with owner

        │
        ▼
9. Report enters existing approval workflow
   (approve / reject / download as PDF or Markdown)
```

### Key invariants enforced by the sequence

| Invariant | Where enforced |
|-----------|---------------|
| Snapshot is immutable after distribution | Snapshot service; write-protected DB record |
| Team can only upload against the snapshot version they received | Upload parser validates `snapshot_id` + `checksum` |
| Protected Excel columns cannot be overwritten on re-upload | Parser rejects rows where locked fields differ from snapshot |
| External access is scoped per team and per snapshot | Signed token contains both `snapshot_id` and `team_id` |
| Re-upload replaces that team's responses atomically | Parser deletes existing `ReviewResponse` rows for that team+snapshot before inserting new ones; old set archived |

---

## 8. Fit With Existing ReviewBot Architecture

The existing codebase provides useful building blocks:

| Existing Component | Reuse |
|-------------------|-------|
| `Checklist` and `ChecklistItem` | Base for master checklist and project checklist |
| Global template CRUD | Starting point for master checklist management |
| Project checklist cloning | Good base for project-scoped checklist creation |
| `Review` and `ReviewResponse` | Good base for review session persistence |
| `checklist_parser.py` | Extend incrementally — see note below |
| `IntegrationConfig` / dispatcher | Reuse for distribution emails — see note below |
| `voice_interface.py` | Useful later for live review input |
| Report generation and approval flow | Can be reused for external review outputs |

### Note: Extending `checklist_parser.py` incrementally

Do not rewrite `checklist_parser.py`. Instead, add a second class `ExcelResponseParser` in the same module that reuses the file-reading and workbook-opening infrastructure but has its own column mapping, snapshot validation logic, and response-state parsing. The existing class handles source checklist ingestion (admin upload of a question template). The new class handles response import (external team upload of a filled workbook). Keeping them separate avoids breaking the working upload path and makes each parser testable independently.

```
checklist_parser.py
  ├── ChecklistParser          ← existing, handles source checklist ingestion
  └── ExcelResponseParser      ← new, handles team response import
        - validates snapshot_id and checksum from metadata sheet
        - validates team_id matches upload token
        - rejects rows where locked columns differ from snapshot
        - parses Response State, Response, Confidence, Notes,
          Questions/Doubts, Evidence Refs columns
        - returns structured list of ParsedResponse + list of ParseError
```

### Note: Reusing the SMTP integration for distribution emails

Rather than building a separate email path for distribution notifications, Phase 4 distribution emails should route through the existing `IntegrationConfig` / dispatcher infrastructure already built for post-review notifications. This avoids maintaining two independent email codepaths and means distribution email attempts are automatically recorded in `IntegrationDispatch` audit records alongside other dispatch history. The dispatcher will need a new trigger type (`distribution`) and a new handler alongside the existing `_smtp()` handler, but the session isolation, error handling, and credential masking are already in place.

Main new components required:

- checklist item metadata extensions (`team_category`, `guidance`, applicability)
- `ProjectReviewTeam` model for team mapping at project level
- `ReviewSnapshot` entity (see section on `ReviewRevision` below)
- Excel template export service
- `ExcelResponseParser` class (extends `checklist_parser.py`)
- partial completion and scoring rules
- evidence binding model
- signed token service for distribution and upload links

### Note: `ReviewSnapshot` and the `ReviewRevision` concept

The snapshot entity must carry a version number so that post-distribution changes can produce a second snapshot (v2) without destroying the first. This is the `ReviewRevision` concept: each distribution cycle for a given project review is a numbered revision of the snapshot.

Recommended shape:

| Field | Type | Purpose |
|-------|------|---------|
| `id` | UUID | Primary key |
| `review_id` | FK → `Review` | Parent review |
| `revision` | int | 1, 2, 3 … increments each time "Distribute" is clicked |
| `checksum` | string | SHA-256 of the serialised item set at freeze time |
| `frozen_at` | timestamp | When this snapshot was created |
| `status` | enum | `active`, `superseded`, `revoked` |
| `item_snapshot` | JSONB | Full frozen item list with text, guidance, weights |
| `team_snapshot` | JSONB | Frozen team-to-category mapping |
| `scoring_rules` | JSONB | Denominator rules, mandatory flags active at freeze time |

When a reviewer clicks "Distribute" again after changes, a new `ReviewSnapshot` row is created with `revision = previous + 1` and the previous row's `status` is set to `superseded`. Upload tokens are scoped to a specific `snapshot_id`, so uploads against the old revision are still valid until explicitly revoked. The consolidated report always states which revision it is based on.

---

## 9. Risks and Gaps

| Risk / Gap | Why It Matters | Recommendation |
|-----------|----------------|----------------|
| No frozen snapshot model | Uploads can mismatch changed templates | Introduce snapshot ID and checksum |
| `NA` not clearly defined | Scores become inconsistent and untrusted | Use explicit response states and scoring rules |
| Owner and team category conflated | Template design becomes messy and brittle | Separate structural ownership from named owner |
| Filename-only evidence mapping | Easy to break on rename or typo | Use stable evidence binding IDs |
| Giant shared workbook | Cross-team leakage and tracking confusion | Prefer one export per team |
| Post-distribution edits mutate live review | Teams answer against stale files | Allow edits before distribution only, then regenerate |
| External links not governed | Security and privacy exposure | Add expiry, revocation, and audit trail |

---

## 10. Final Recommendation

The product should move toward a **single global master checklist** with project-specific customization and team-scoped distribution.

That means:

- yes, the two standard templates should be replaced by one master checklist over time
- yes, reviewers should be able to edit and delete items after assigning the checklist to a project
- but those edits should happen on the project checklist before distribution
- and once the review is distributed, the system should freeze a snapshot for that review cycle

This gives you the maintainability benefits of one global checklist without the operational risks of one uncontrolled spreadsheet.

---

## 11. Implementation Task List

### Phase 0 - Technical Spike (de-risk before committing)

Before committing to the full phase plan, run a short spike (1–2 days) to validate the Excel generation library against the exact requirements:

1. Confirm that `openpyxl` (preferred) or `xlsxwriter` can produce worksheet-protected workbooks that remain protected after a round-trip through Microsoft Excel, LibreOffice, and Google Sheets
2. Verify that data-validation dropdowns (`Response State`, `Confidence`) survive the same round-trip
3. Confirm that a protected metadata sheet survives without user prompts on open
4. Test that the parser can read back the generated file after a human has filled in the editable columns
5. Document which library is selected and any version constraints

Outcome: a single `spike_excel_roundtrip.py` script that generates a sample workbook and asserts the invariants. This script becomes the regression baseline for Phase 4.

> **Why this matters:** Excel worksheet protection and dropdown validation behaviour differ between `openpyxl` and `xlsxwriter`, and both have known gaps when files are opened in non-Excel applications. Discovering this in Phase 0 costs one day; discovering it in Phase 4 costs a sprint.

### Phase 0.5 — Organization Scoping ✅ Done (2026-04-26)

A lightweight organization-scoping layer was added to enable multi-org deployments without a full multi-tenant rewrite. This is a prerequisite for scoped global checklist distribution.

1. ✅ Added `Organization` model with `id`, `name`, `slug`, `description`, `is_active`, `created_at`, `updated_at`
2. ✅ Added `organization_id` FK (nullable) to `User`, `Project`, and `Checklist` tables
3. ✅ Added `/api/organizations` CRUD router — any authenticated user can list/read; admin-only writes
4. ✅ Global checklist visibility rule: `WHERE is_global=true AND (organization_id IS NULL OR organization_id = current_user.organization_id)` — `NULL` means platform-wide
5. ✅ `GlobalChecklistCreate.type` changed from `Literal["delivery", "technical"]` to `str = "master"` — supports free-form master checklist model
6. ✅ `/api/auth/me` and `/api/auth/register` return and accept `organization_id`
7. ✅ `/globals` UI shows org-badge on org-scoped templates and includes scope filter (All / Platform-only / My org only) and type text filter
8. ✅ Create modal in `/globals` has scope dropdown defaulting to "My organization" when user has an org

### Phase 1 - Data Model and Requirements Baseline

1. ✅ **Done** — Add `team_category`, `guidance`, and optional applicability metadata to `ChecklistItem` — `team_category` (string, optional), `guidance` (text, optional), and `applicability_tags` (JSON array, optional) are stored on `ChecklistItem` and exposed through all item create/update/list APIs and the `/globals` UI
2. Define `ProjectReviewTeam` model for team mapping at project level
3. Extend `Review` with `mode`, `snapshot_id`, and partial-completion flags
4. Extend `ReviewResponse` with `team_id`, `response_state`, `confidence`, `assigned_owner`, and clarification text
5. Define `ReviewSnapshot` entity with `revision`, `checksum`, `frozen_at`, `status`, `item_snapshot` (JSONB), `team_snapshot` (JSONB), and `scoring_rules` (JSONB) — see `ReviewRevision` note in section 8
6. Document explicit scoring rules for `answered`, `na_out_of_scope`, `delegated`, `needs_clarification`, and partial submission

### Phase 2 - Global Master Checklist and Project Checklist UX

1. Update global checklist UI and APIs to require `team_category`
2. Add `guidance` editing to checklist item create and update flows
3. Add project-level checklist override flow: exclude, edit wording, change mandatory, reassign category
4. Add validation for uncategorized items before distribution
5. Migrate current seeded technical and delivery templates into the new master checklist structure

### Phase 3 - Project Setup and Team Mapping

1. Add project setup step for defining review teams
2. Add mapping validation between checklist categories and project teams
3. Show item counts per team before distribution
4. Add support for unassigned category warnings
5. Store team scope text for later scoring and report explanations

### Phase 4 - Snapshot and Excel Distribution

1. Build review snapshot generation service (freeze item set, team mapping, scoring rules, checksum)
2. Build team-scoped Excel export service with locked columns, dropdown validation, metadata sheet, and instructions sheet
3. Mint signed, time-limited, per-team download and upload tokens scoped to `snapshot_id + team_id`
4. Add token revocation support so individual team access can be cancelled without affecting others
5. Send distribution email to each team lead containing their signed download link (reuse SMTP integration where possible)
6. Add admin audit log for token creation, download, and revocation events
7. Track distribution status per team (generated / sent / downloaded / submitted / error)

### Phase 5 - Upload, Parse, and Evidence Binding

1. Build upload endpoint for team response files (authenticated via signed upload token from Phase 4)
2. Validate snapshot ID, checksum, team ID, and protected column integrity on upload
3. Implement `ExcelResponseParser` class in `checklist_parser.py` (see section 8 note); parse response state, answer, notes, confidence, and questions columns; reject rows with invalid response state values
4. Implement atomic re-upload: archive previous responses for that team+snapshot before inserting new ones
5. Add stable evidence binding model (`snapshot_id + item_id + team_id`) instead of filename-only matching
6. Surface precise parse errors (row number, column name, reason) back to the reviewer
7. Notify the review coordinator on successful upload: team name, response count, parse warnings

### Phase 6 - Scoring, Consolidation, and Reporting

1. Implement denominator rules for out-of-scope items
2. Block completion on mandatory unresolved items by default
3. Add explicit partial-report override flow
4. Generate consolidated report with team summaries, missing teams, and delegated items
5. Group recommendations by owner or team

### Phase 7 - Clarification and Live Review Enhancements

1. Ship Guidance and Questions / Doubts columns in Milestone 1
2. Add async Q&A portal tied to snapshot and item ID
3. Extend live review flow to use the same snapshot model
4. Support `explain` in live review
5. Keep STT optional and bounded; do not add full duplex voice

### Phase 8 - Security, Audit, and Operations

1. Add expiring and revocable distribution links
2. Add audit log for file distribution, upload, and review completion
3. Define retention policy for external evidence uploads
4. Add file size, type, and count limits
5. Add admin visibility into team upload status

### Phase 9 - Testing and Rollout

1. Add unit tests for scoring state transitions and denominator logic
2. Add parser tests for protected-field tampering and version mismatch
3. Add integration tests for multi-team distribution and consolidation
4. Seed a demo master checklist with category and guidance metadata
5. Roll out async external review before live review enhancements

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0 | 2026-04-23 | Initial analysis document |
| 1.1 | 2026-04-23 | Added field observations from NeuMoney-iOS review: offline clarification gap, owner column requirement, team scope handling |
| 1.2 | 2026-04-23 | Added multi-team distribution model, team category taxonomy, per-team Excel distribution, and consolidated report structure |
| 1.3 | 2026-04-23 | Reframed design around one global master checklist, project-level edits before distribution, frozen review snapshots, explicit response states and scoring rules, and a phased implementation task list |
| 1.4 | 2026-04-23 | Added section 6: snapshot definition and end-to-end distribution sequence diagram with key invariants; renumbered subsequent sections; moved external auth tokens and revocation into Phase 4; moved coordinator notifications and atomic re-upload into Phase 5 |
| 1.5 | 2026-04-23 | Added Phase 0 (Excel library spike); added ExcelResponseParser incremental extension note; added SMTP integration reuse note; added ReviewSnapshot / ReviewRevision data model with field table; updated Phase 1 and Phase 5 task lists to reference these decisions |
| 1.6 | 2026-04-26 | Added Phase 0.5 (Organization Scoping — fully implemented); marked Phase 1 item 1 (`team_category`, `guidance`, `applicability_tags` on ChecklistItem) as done; updated document status to In Progress |

---

*Document generated: 2026-04-23*
