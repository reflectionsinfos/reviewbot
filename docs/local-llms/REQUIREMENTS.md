# Hybrid LLM Feature — Requirements

**Feature:** Hybrid LLM Routing with Local Model Support  
**Version:** 1.1  
**Status:** Approved — In Development  
**Created:** 2026-04-02  
**Updated:** 2026-04-02  
**Author:** ReviewBot Team

---

## 1. Background

### 1.1 Current Problem

Code analysis confirmed that **all 103 checklist items are unconditionally routed to
`llm_analysis`** via `StrategyRouter._auto_route()`. The strategies `file_presence`,
`pattern_scan`, and `metadata_check` exist in the codebase but are dead code paths —
they only activate if an admin manually creates a `ChecklistRoutingRule` DB row per item,
which never happens in practice.

This causes two critical failures:

1. **Rate limit exhaustion** — At Groq's 100K TPD limit, a single 103-item review
   consumes ~60-80K tokens. The second review of the day fails with `429` errors,
   leaving all remaining items as `na` in the DB.
2. **Unnecessary LLM cost** — ~35 of 103 items (file existence, dependency checks,
   secret detection) can be answered deterministically in milliseconds with zero LLM calls.

### 1.2 Root Cause

`strategy_router_agent.py` `_auto_route()` always returns `llm_analysis`. No keyword
rules or heuristics are applied to route items to cheaper strategies automatically.

---

## 2. Goals

| # | Goal |
|---|---|
| G1 | Reduce cloud LLM calls from 103 → ~23 per review through smart pre-routing |
| G2 | Use a single planning LLM call to intelligently assign strategies and file targets |
| G3 | Route complex reasoning items to cloud LLM, simple checks to local Ollama |
| G4 | Support automatic fallback chain when cloud hits rate limits |
| G5 | UI lets admins manage the hybrid chain (priority, role, strategy affinity) |
| G6 | No degradation in review quality for architecture/security/process items |
| G7 | Development testing works on 3 small sample projects via local Ollama |

---

## 3. Architecture — 3-Phase Execution Model

```
Phase 0: Deterministic Pre-filter  (ZERO LLM calls, < 100ms)
    │  Keyword/area rules classify ~25-35 items instantly
    ↓
Phase 1: Planning LLM  (ONE LLM call — local Ollama preferred)
    │  File tree + project description + remaining items → JSON routing plan
    │  Plan assigns: strategy, complexity (simple|complex), files_to_read per item
    ↓
Phase 2: Parallel Execution
    ├─ file_presence / pattern_scan / metadata_check  → no LLM, instant
    ├─ llm_analysis [complexity=simple]               → Local Ollama
    └─ llm_analysis [complexity=complex]              → Cloud LLM (primary → fallback chain)
```

**Expected token reduction per review:**

| Phase | Items | LLM Calls | Tokens |
|---|---|---|---|
| Before (current) | 103 | 103 | ~75,000 |
| Phase 0 (deterministic) | ~30 resolved | 0 | 0 |
| Phase 1 (planning) | 1 planning call | 1 | ~3,000 |
| Phase 2 simple (local) | ~25 items | 25 (local) | 0 cloud tokens |
| Phase 2 complex (cloud) | ~23 items | 23 | ~17,000 |
| **Total cloud tokens** | | | **~20,000** (was 75,000) |

---

## 4. Functional Requirements

### FR-1: Phase 0 — Deterministic Pre-filter

The strategy router must apply keyword/area rules **before** any LLM call to classify
items that can be answered mechanically.

Mandatory rules (applied in order):

| Trigger | Strategy | Examples |
|---|---|---|
| Question contains: "is there a", "does the repo have", "exists" + file noun | `file_presence` | "Is there a README?", "Is there a Dockerfile?" |
| Area = "Dependencies" OR question contains "package", "library", "dependency" | `metadata_check` | "What packages are used?", "Are dependencies pinned?" |
| Question contains "hardcoded", "secret", "API key", "password" in code | `pattern_scan` | "Are secrets hardcoded?", "Are credentials in source?" |
| Question contains "test", "unit test", "test coverage" | `pattern_scan` | "Are there unit tests?", "What is test coverage?" |
| Area contains "Governance", "Ownership", "Financial", "Legal", "Process" | `human_required` | "Who owns this system?", "Is there a budget approval?" |
| Area contains "Sign-off", "Approval", "Stakeholder" | `human_required` | "Has this been approved by?" |

Items classified in Phase 0 **never reach the planning LLM or execution LLM**.

### FR-2: Phase 1 — Planning LLM

A single LLM call must be made before item execution with:

**Input:**
- Project name, description, detected stack (from file extensions)
- Full file tree with file sizes (paths only — no file contents)
- All remaining checklist items (id, area, question) after Phase 0
- Available strategies and their meanings

**Output (structured JSON):**
```json
[
  {
    "item_id": 5,
    "strategy": "pattern_scan",
    "patterns": ["import pytest", "def test_", "@Test"],
    "files_scope": ["*.py", "*.java"],
    "rationale": "Test framework detectable by import pattern"
  },
  {
    "item_id": 12,
    "strategy": "llm_analysis",
    "complexity": "complex",
    "files_to_read": ["src/auth.py", "src/middleware.py"],
    "rationale": "JWT security design requires cross-file reasoning"
  },
  {
    "item_id": 23,
    "strategy": "llm_analysis",
    "complexity": "simple",
    "files_to_read": ["src/routes/users.py"],
    "rationale": "Error handling presence checkable from single file"
  }
]
```

**Planning LLM selection (in priority order):**
1. Local Ollama (if configured and running) — preferred, free, no rate limit
2. Cloud LLM fallback (Groq, then OpenAI) if Ollama not available

**Plan validation:**
- All `files_to_read` paths must be cross-checked against the actual file index
- Invalid paths are dropped silently; item falls back to `llm_analysis` with no file hint
- Items missing from the plan fall back to `llm_analysis` with `complexity=complex`

**Plan caching:**
- The plan is stored as JSON on `AutonomousReviewJob.routing_plan` (new column)
- Re-reviews of the same project+checklist can optionally reuse the cached plan

### FR-3: Phase 2 — Execution Split

**Deterministic strategies** (`file_presence`, `pattern_scan`, `metadata_check`):
- Run immediately with no LLM call
- Use plan-provided patterns/file scopes where available
- Confidence: 0.85–1.0

**`llm_analysis` with `complexity=simple` → Local Ollama:**
- Items where specific files are identified and the question is factual/presence-based
- e.g., "Is logging implemented?", "Is error handling present in this module?"
- Local model receives only the 1-2 identified files as context
- Locked areas that must NOT be downgraded to local:
  - Architecture & Design
  - Security Architecture
  - Governance & Compliance

**`llm_analysis` with `complexity=complex` → Cloud LLM:**
- Cross-file reasoning, quality assessment, design pattern evaluation
- Uses the priority fallback chain (FR-5)

### FR-4: Multiple Enabled LLM Configs

- More than one LLM config can be enabled simultaneously
- Each config has: `role` (`primary`/`fallback`/`local`), `priority` (int), `is_enabled` (bool)
- `strategy_affinity` (JSON list) — which strategies this config handles; `null` = all
- The priority chain replaces the current single-active mutex

### FR-5: Automatic Fallback on Rate Limit

- On `429 RateLimitError` from active config, retry with next config in priority chain
- Fallback is at **item level** — completed items are not re-run
- If all configs exhausted: item stored as `na` with error summary; job continues

### FR-6: Local LLM via Ollama

- `provider = "ollama"` supported in `LLMConfig`
- UI auto-fills Base URL `http://localhost:11434/v1`, API Key `ollama`
- Backend treats Ollama as OpenAI-compatible endpoint
- Pre-flight check before job start: ping Ollama `/api/tags`, verify model is pulled

### FR-7: UI — System Config

- Admin sets `role`, `priority`, `strategy_affinity` per config
- Fallback Chain visualizer: `[1] GPT-4o → [2] Groq → [3] Ollama`
- Up/down arrows to reorder priority
- "Add Local (Ollama)" quick-setup button
- "Test Connection" works for both cloud and Ollama URLs

### FR-8: Usage Tracking

- `total_tokens_used` and `total_requests_made` tracked per `LLMConfig` row
- Dashboard cards show cloud vs local usage split

---

## 5. Non-Functional Requirements

| # | Requirement |
|---|---|
| NFR-1 | Phase 0 pre-filter completes in < 100ms for 103 items |
| NFR-2 | Planning LLM call completes in < 30s (local) / < 10s (cloud) |
| NFR-3 | Config chain loaded once per job — not per item |
| NFR-4 | All new DB columns have server defaults — zero-downtime migration |
| NFR-5 | Existing single-active configs work without manual changes post-migration |
| NFR-6 | Ollama pre-flight check runs before first item, not mid-run |
| NFR-7 | Locked areas (Architecture, Security, Governance) always use cloud LLM |

---

## 6. Out of Scope (v1.0)

- Per-item LLM assignment via UI (planned v1.2)
- Load balancing across multiple Ollama instances
- Fine-tuning local models on checklist data
- HuggingFace Inference Endpoints (v1.1)
- Streaming responses to frontend during review

---

## 7. Sample Projects for Development & Testing

Three minimal codebases at `C:\projects\nexus-ai\sample-projects\` for fast local testing.
Each has 5–8 files — a full review completes in 5–15 min on local Ollama CPU.

| Project | Stack | Path |
|---|---|---|
| `python-api-sample` | Python / FastAPI | `sample-projects/python-api-sample/` |
| `java-service-sample` | Java / Spring Boot | `sample-projects/java-service-sample/` |
| `nodejs-service-sample` | Node.js / Express | `sample-projects/nodejs-service-sample/` |

---

## 8. Acceptance Criteria

| ID | Scenario | Expected Result |
|---|---|---|
| AC-1 | Review of `python-api-sample` with Ollama + GPT-4o | Phase 0 classifies ≥ 15 items without LLM; cloud receives ≤ 30 items |
| AC-2 | Cloud hits 429 mid-review | Item retried on fallback; job continues; no crash |
| AC-3 | Ollama not running, used as planning LLM | Falls back to cloud for planning; logs warning |
| AC-4 | Architecture item goes through planning LLM | Plan assigns `complexity=complex`; goes to cloud LLM regardless of Ollama config |
| AC-5 | "Are secrets hardcoded?" item | Phase 0 routes to `pattern_scan`; no LLM call |
| AC-6 | All configs exhausted | Remaining items stored as `na`; job marked `completed` not `failed` |
| AC-7 | Existing single-active config, no migration changes | Works identically to before |
| AC-8 | Admin adds Ollama + sets priority=2 | Chain visualizer shows: Cloud #1 → Ollama #2 |
| AC-9 | Plan caching | Second review of same project reuses stored routing plan |
