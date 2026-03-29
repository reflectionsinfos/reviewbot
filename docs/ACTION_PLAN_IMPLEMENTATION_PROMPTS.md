# Two-Track Action Item System — Implementation Prompts

> Use these prompts with any LLM (Claude, GPT-4o, Gemini, Qwen, etc.) to build the feature.
> Each prompt is self-contained. Work through them in order (1 → 5).

---

## Prompt 1 — Backend Service: ActionPlanGenerator

```
You are an expert Python / FastAPI developer. You are working inside the ReviewBot codebase.

### Context

ReviewBot is a FastAPI application (Python 3.11, SQLAlchemy 2.0 async, PostgreSQL).
After an autonomous code review completes, results are stored across these models
(all defined in app/models.py):

- AutonomousReviewJob
    id, project_id, checklist_id, source_path, status, agent_metadata (JSONB)

- AutonomousReviewResult
    id, job_id, checklist_item_id,
    rag_status (green|amber|red|na|skipped),
    evidence (str), files_checked (JSON list of str),
    needs_human_sign_off (bool), confidence (float),
    evidence_hint (str)

- ChecklistItem
    id, checklist_id, item_code, area, question, category,
    weight, is_review_mandatory, expected_evidence, order

- Project
    id, name, domain, tech_stack (JSON list of str)

### Task

Create `app/services/action_plan_generator.py` with a class `ActionPlanGenerator`
that has the following interface:

```python
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class AIPrompt:
    generic: str       # plain instruction usable in any AI IDE
    cursor: str        # prefixed with @workspace for Cursor / GitHub Copilot Chat
    claude_code: str   # task-description style for Claude Code CLI

@dataclass
class ActionCard:
    item_code: str
    area: str
    question: str
    priority: str           # "High" (red) | "Medium" (amber)
    rag_status: str
    what_was_found: str     # from AutonomousReviewResult.evidence
    what_to_fix: str        # derived sentence from expected_evidence gap
    expected_outcome: str   # ChecklistItem.expected_evidence (or empty string)
    assigned_to: str = "TBD"
    due_date: str = "TBD"
    ai_prompt: Optional[AIPrompt] = None

@dataclass
class ActionPlanResponse:
    job_id: int
    project: str
    checklist: str
    generated_at: str       # ISO datetime
    summary: dict           # total, critical_blockers, advisories, sign_off_required, compliant
    critical_blockers: List[ActionCard]   # red items
    advisories: List[ActionCard]          # amber items
    sign_off_required: List[ActionCard]   # needs_human_sign_off=True (any rag_status)
    compliant_summary: List[dict]         # [{item_code, area, question}] for green items

class ActionPlanGenerator:
    def generate(
        self,
        job: "AutonomousReviewJob",
        results: list,              # list of AutonomousReviewResult
        checklist_items: dict,      # {checklist_item_id: ChecklistItem}
        project: "Project",
        checklist_name: str
    ) -> ActionPlanResponse:
        ...

    def _build_prompt(
        self,
        result: "AutonomousReviewResult",
        item: "ChecklistItem",
        project: "Project"
    ) -> AIPrompt:
        ...
```

### Prompt template rules

For `_build_prompt`, construct three flavours from these slots:
- CONTEXT block: project name, tech_stack joined as comma-separated string, files_checked list
- FINDING block: result.evidence
- STANDARD EXPECTED block: item.expected_evidence (if None, use "Not specified")
- TASK block: "Fix the above gap. Ensure the solution satisfies: '<item.question>'"
- ACCEPTANCE CRITERIA: item.expected_evidence or item.question

Generic flavour: the four blocks above, plain text, no special prefix.
Cursor flavour: prefix with "@workspace " and add "Search the workspace for related files before making changes."
Claude Code flavour: wrap in "Task:\n" prefix and add "Run tests after making changes."

### What to fix derivation

`what_to_fix` should be a single imperative sentence generated from:
  - If item.expected_evidence is not None/empty:
      "Implement: {item.expected_evidence}"
  - Else:
      "Address the following: {item.question}"

### Requirements
- No external dependencies beyond Python stdlib and the app's existing imports
- All methods are synchronous (caller handles async DB fetching separately)
- Type hints on all methods
- Do not import from FastAPI or SQLAlchemy inside the generator — accept plain model objects
```

---

## Prompt 2 — API Endpoint: GET action-plan

```
You are an expert Python / FastAPI developer working in the ReviewBot codebase.

### Context

- `app/services/action_plan_generator.py` has been created (see Prompt 1).
- The route file for autonomous reviews is `app/api/routes/reports.py`.
- Relevant models: AutonomousReviewJob, AutonomousReviewResult, ChecklistItem, Checklist, Project
  (all in app/models.py, all SQLAlchemy async).
- Database session dependency: `get_db` from `app/db/session.py`.
- Auth dependency: `get_current_user` from `app/api/routes/auth.py`.
- Existing pattern for eager loading:
  ```python
  result = await db.execute(
      select(AutonomousReviewJob)
      .options(selectinload(AutonomousReviewJob.results))
      .where(AutonomousReviewJob.id == job_id)
  )
  ```

### Task

Add two endpoints to `app/api/routes/reports.py`:

#### Endpoint 1: GET /api/autonomous-reviews/{job_id}/action-plan

- Require authentication (Bearer JWT via get_current_user).
- Load the AutonomousReviewJob. Return 404 if not found.
- Load all AutonomousReviewResult records for the job (eager load).
- Load all ChecklistItem records for the job's checklist_id (eager load).
- Load the Project for the job's project_id.
- Load the Checklist name.
- Build a dict: {result.checklist_item_id: ChecklistItem} from the checklist items.
- Instantiate ActionPlanGenerator and call .generate(...).
- Return the ActionPlanResponse as a dict (use dataclasses.asdict()).
- Return 400 if the job status is not "completed".

#### Endpoint 2: POST /api/autonomous-reviews/{job_id}/action-plan/enhance

- Require authentication.
- Load the job. Return 404 if not found, 400 if not completed.
- Check if agent_metadata already contains "action_plan_prompts" key — if so return 200
  with {"status": "already_enhanced"} (idempotent).
- Otherwise: run LLM enrichment inline for now (async) using the existing LLM provider
  configured in `app/core/config.py` settings (reuse the same pattern as
  `app/services/checklist_optimizer.py` for calling the LLM).
  For each red/amber result, call the LLM with a prompt asking it to improve the
  ActionPlanGenerator._build_prompt() output with codebase-specific context.
  Store results in job.agent_metadata["action_plan_prompts"] = {result_id: {generic, cursor, claude_code}}.
- Return 200 {"status": "enhanced", "prompts_generated": N}.

### Requirements
- async def + await for all DB operations
- selectinload() for all relationship access
- wrap DB writes in try/except with db.rollback() on error
- Type hints on the function signature
```

---

## Prompt 3 — Frontend: Action Plan Tab in history.html

```
You are an expert frontend developer (vanilla JS, no framework).
You are working on `static/history.html` in the ReviewBot project.

### Context

history.html shows a list of autonomous review jobs. When the user clicks "Details"
on a job, a details panel is shown. This panel currently has:
- A stats header (compliance score, red/amber/green counts, override count)
- Filter pills and search
- A grid of item cards (one per checklist item)

The details panel is populated by calling:
  GET /api/reports/{job_id}/details
and the existing `renderDetails(data)` function renders the item cards.

### Task

Add a two-tab layout to the details panel:

Tab 1: "Review Items" — the existing item cards grid (unchanged behaviour)
Tab 2: "Action Plan" — new content described below

#### Tab bar HTML to insert above the existing item grid:
```html
<div id="details-tabs" style="display:flex;gap:0;border-bottom:1px solid #334155;margin-bottom:16px;">
  <button class="dtab active" onclick="switchDetailsTab('items')">Review Items</button>
  <button class="dtab" onclick="switchDetailsTab('action-plan')">Action Plan</button>
</div>
<div id="tab-items"><!-- existing item grid goes here --></div>
<div id="tab-action-plan" style="display:none;"><!-- new content --></div>
```

#### Action Plan tab content

At the top of #tab-action-plan render:
1. A toolbar:
   - "IDE Flavour:" label + `<select id="ide-flavour">` with options: Generic, Cursor/Copilot, Claude Code
     - Store selection in localStorage key "reviewbot_ide_flavour"; restore on load.
   - "Export MD" button (calls exportActionPlan())
   - "Enhance with AI" button (calls enhanceActionPlan(jobId); shows spinner; on completion refreshes)

2. Three collapsible sections:
   a) "🔴 Critical Blockers (N)" — red items
   b) "🟡 Advisories (N)" — amber items
   c) "🟣 Needs Human Sign-off (N)" — sign_off_required items
   d) "✅ Already Compliant (N)" — collapsed by default, shows simple list

3. Each action card renders:
```
┌──────────────────────────────────────────────────────┐
│  [AREA]  [PRIORITY badge]  [item_code]               │
│  Question: <question>                                 │
│  What was found: <what_was_found>                     │
│  What to fix: <what_to_fix>                           │
│  Expected outcome: <expected_outcome>                 │
│  [▶ Show AI Prompt]                                   │
│  (when expanded:)                                     │
│    <pre class="prompt-text">{flavour-specific prompt}</pre>  │
│    [📋 Copy]                                          │
└──────────────────────────────────────────────────────┘
```

#### JS functions to add:

```javascript
async function loadActionPlan(jobId) {
  // GET /api/autonomous-reviews/{jobId}/action-plan
  // Store result in window._actionPlanData
  // Call renderActionPlan()
}

function renderActionPlan() {
  // Render from window._actionPlanData using current ide-flavour select value
}

function switchDetailsTab(tab) {
  // Show/hide #tab-items vs #tab-action-plan
  // Update .dtab active class
  // If 'action-plan' selected and _actionPlanData not loaded, call loadActionPlan(currentJobId)
}

function copyPrompt(cardIndex) {
  // navigator.clipboard.writeText(prompt text for card at index)
  // Show "Copied!" tooltip for 1.5s
}

function exportActionPlan() {
  // Build Markdown string from _actionPlanData
  // Download as "action-plan-{jobId}.md" using Blob + <a download>
}

async function enhanceActionPlan(jobId) {
  // POST /api/autonomous-reviews/{jobId}/action-plan/enhance
  // On success: reload action plan data and re-render
}
```

#### Markdown export format:
```
# Action Plan — {project} | {checklist}
Generated: {generated_at}
Compliance: {summary.compliant}/{summary.total_items} items

## 🔴 Critical Blockers

### {item_code} — {area}
**{question}**

**What was found:** {what_was_found}
**What to fix:** {what_to_fix}
**Expected outcome:** {expected_outcome}

**AI Prompt (Generic):**
\```
{ai_prompt.generic}
\```

---
... (repeat for each card)
```

### Requirements
- Vanilla JS only — no external libraries
- The api() helper already exists in history.html: `async function api(path, opts={})` — use it
- escapeHtml() already exists — use it
- Match the existing dark theme (background #0f172a, card background #1e293b, border #334155, text #e2e8f0)
- The details panel is shown/hidden elsewhere — do not change that logic
- switchDetailsTab('items') should be called when opening a new details panel so it always starts on Review Items tab
```

---

## Prompt 4 — CSS Additions for Action Plan UI

```
You are a CSS developer working on static/history.html in ReviewBot.

Add the following CSS rules into the existing <style> block.
Match the existing dark theme: background #0f172a, card #1e293b, border #334155, accent #38bdf8.

Rules needed:

1. `.dtab` — details tab button
   - No border, no background, color #94a3b8, padding 10px 18px, font-size 13px, font-weight 600
   - cursor pointer, border-bottom 2px solid transparent, transition all 0.15s
   - `.dtab.active` → color #38bdf8, border-bottom-color #38bdf8
   - `.dtab:hover:not(.active)` → color #e2e8f0

2. `.action-card` — individual action card
   - background #1e293b, border 1px solid #334155, border-radius 10px
   - padding 16px 20px, margin-bottom 10px
   - `.action-card.priority-high` → border-left 3px solid #ef4444
   - `.action-card.priority-medium` → border-left 3px solid #f59e0b

3. `.action-section-header` — collapsible section header
   - display flex, align-items center, gap 10px
   - font-size 14px, font-weight 700, color #e2e8f0
   - cursor pointer, padding 10px 0, user-select none
   - `:hover` → color #38bdf8

4. `.prompt-block` — the pre element containing the AI prompt
   - display none (hidden until expanded)
   - background #0f172a, border 1px solid #334155, border-radius 8px
   - padding 12px 14px, font-size 12px, color #7dd3fc, white-space pre-wrap, word-break break-word
   - margin-top 10px
   - `.prompt-block.visible` → display block

5. `.btn-copy-prompt`
   - background transparent, border 1px solid #334155, color #94a3b8
   - padding 4px 10px, border-radius 6px, font-size 11px, cursor pointer
   - `:hover` → border-color #38bdf8, color #38bdf8

6. `.copied-badge`
   - display inline-block, background #14532d, color #4ade80
   - font-size 11px, padding 2px 8px, border-radius 4px, margin-left 6px
   - animation: fadeOut 1.5s forwards

   @keyframes fadeOut { 0% { opacity:1 } 80% { opacity:1 } 100% { opacity:0 } }
```

---

## Prompt 5 — Integration Test

```
You are a Python testing expert working on the ReviewBot codebase (pytest + httpx AsyncClient).

### Context

- Test infrastructure is in `tests/conftest.py`:
  - `async_client` — AsyncClient with JWT auth (reviewer role)
  - `project_factory(owner_id)` — creates a Project
  - `checklist_factory(is_global, project_id, source_checklist_id)` — creates a Checklist
  - `item_factory(checklist_id, item_code, question, expected_evidence)` — creates a ChecklistItem
  - `create_test_user(role)` — returns (User, auth_headers)

- The AutonomousReviewJob and AutonomousReviewResult models are in app/models.py.
- The action plan endpoint is: GET /api/autonomous-reviews/{job_id}/action-plan

### Task

Add the following tests to `tests/test_action_plan_integration.py` (new file):

#### Test 1: test_action_plan_groups_by_rag
Setup:
- Create a project and checklist with 4 items (item codes 1.1, 1.2, 1.3, 1.4)
- Create an AutonomousReviewJob with status="completed" for that project+checklist
- Create AutonomousReviewResult records:
  - item 1.1 → rag_status="red", evidence="No rate limiting found", needs_human_sign_off=False
  - item 1.2 → rag_status="amber", evidence="Partial logging", needs_human_sign_off=False
  - item 1.3 → rag_status="green", evidence="JWT implemented", needs_human_sign_off=False
  - item 1.4 → rag_status="red", evidence="No auth", needs_human_sign_off=True
Assert:
- GET /api/autonomous-reviews/{job_id}/action-plan returns 200
- response["critical_blockers"] has 2 items (1.1 and 1.4 — red items NOT in sign_off if needs_human_sign_off=True is excluded)
  Actually: item 1.4 goes to sign_off_required since needs_human_sign_off=True
  So critical_blockers should have 1 item (1.1), advisories 1 (1.2), sign_off_required 1 (1.4)
- response["compliant_summary"] has 1 item (1.3)
- Each card in critical_blockers has: item_code, area, question, priority="High", what_was_found, ai_prompt fields (generic, cursor, claude_code) all non-empty strings

#### Test 2: test_action_plan_404_for_unknown_job
Assert:
- GET /api/autonomous-reviews/99999/action-plan returns 404

#### Test 3: test_action_plan_400_for_non_completed_job
Setup: Create an AutonomousReviewJob with status="running"
Assert:
- GET /api/autonomous-reviews/{job_id}/action-plan returns 400

#### Test 4: test_action_plan_prompt_contains_file_context
Setup:
- Create job + result where result.files_checked = ["src/auth.py", "src/middleware.py"]
  and item.expected_evidence = "JWT tokens must be validated with expiry check"
Assert:
- response["critical_blockers"][0]["ai_prompt"]["generic"] contains "src/auth.py"
- response["critical_blockers"][0]["ai_prompt"]["generic"] contains "JWT tokens must be validated"

### Requirements
- Use pytest.mark.asyncio on all tests
- Use the existing conftest fixtures
- Create the AutonomousReviewJob and AutonomousReviewResult directly via db_session fixture
  (db_session is available in conftest.py)
- Commit the session after adding objects: await db_session.commit()
- All tests should be independent (use function-scoped fixtures)
```

---

## Prompt 6 — Prompt Enhance LLM Integration (Optional / Phase 2)

```
You are a Python developer working on the ReviewBot codebase.

### Context

- `app/services/action_plan_generator.py` exists with ActionPlanGenerator (see Prompt 1).
- The existing LLM invocation pattern can be found in `app/services/checklist_optimizer.py`.
  It uses `app/core/config.py` settings to select the active provider
  (ACTIVE_LLM_PROVIDER: openai | anthropic | google | groq | qwen | azure).
- The POST /api/autonomous-reviews/{job_id}/action-plan/enhance endpoint exists (see Prompt 2)
  but currently stores a placeholder.

### Task

Implement the LLM enrichment logic inside the enhance endpoint:

For each red/amber AutonomousReviewResult in the job:
1. Build a base prompt using ActionPlanGenerator._build_prompt() for the "generic" flavour.
2. Call the configured LLM with this system prompt:
   ```
   You are a senior software engineer writing actionable remediation prompts
   for developers to paste into their AI IDE. Given the context below, produce
   an improved, specific, file-aware prompt that a developer can paste directly
   into Cursor, GitHub Copilot Chat, or Claude Code to fix the issue.
   Be specific: reference exact file paths, suggest the fix pattern, and include
   the acceptance criteria.
   ```
   And user message = the base prompt.
3. For the "cursor" flavour: prefix LLM output with "@workspace\n".
4. For the "claude_code" flavour: prefix LLM output with "Task:\n" and append "\n\nAfter making changes, run the test suite to confirm the fix."
5. Store all three flavours in job.agent_metadata["action_plan_prompts"][str(result.id)] = {generic, cursor, claude_code}.
6. Commit after processing all results.

### Error handling
- If the LLM call fails for any individual result, log the error and continue to the next
  (partial enrichment is acceptable — store what succeeded).
- If the LLM provider is not configured (no API key), return 400:
  {"detail": "No LLM provider configured. Set ACTIVE_LLM_PROVIDER and the corresponding API key."}

### Requirements
- async def / await throughout
- Reuse the existing LLM client factory from checklist_optimizer.py — do not duplicate the provider-selection logic
- Type hints on all functions
- Max LLM concurrency: process results sequentially (not parallel) to avoid rate limit errors
```

