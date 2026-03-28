# Two-Track Action Item System — Implementation Prompts (Qwen Coder Edition)

> Use these prompts with **Qwen2.5-Coder** (or any capable LLM).
> Work through them **in order (1 → 5)**. Each prompt is self-contained.
>
> **Qwen Coder tips (apply to every prompt below):**
> - Output **complete files**, not fragments or diffs
> - Do **not** add docstrings, comments, or type annotations to code you are not changing
> - Do **not** introduce new abstractions or helpers beyond what is explicitly requested
> - Do **not** change existing logic — only add what is described
> - Preserve all existing imports; merge new imports into the existing import block at the top
> - Use the exact surrounding code shown in each prompt as your insertion anchor

---

## Prompt 1 — Backend Service: `app/services/action_plan_generator.py`

```
You are an expert Python developer. Create the file app/services/action_plan_generator.py
from scratch. This is a brand-new file — it does not exist yet.

### Project context

ReviewBot is a FastAPI app (Python 3.11). After an autonomous code review runs, results
are stored in these SQLAlchemy models (defined in app/models.py):

  AutonomousReviewJob
    id: int
    project_id: int
    checklist_id: int
    source_path: str
    status: str                   # "queued" | "running" | "completed" | "failed"
    agent_metadata: dict | None   # JSON column — may be None

  AutonomousReviewResult
    id: int
    job_id: int
    checklist_item_id: int
    rag_status: str               # "green" | "amber" | "red" | "na" | "skipped"
    evidence: str                 # What the agent found
    confidence: float
    files_checked: list[str]      # List of file paths examined
    needs_human_sign_off: bool    # True means human must confirm even if agent ran
    evidence_hint: str | None     # Hint to a human reviewer

  ChecklistItem
    id: int
    checklist_id: int
    item_code: str                # e.g. "1.1", "2.3"
    area: str                     # e.g. "Security Architecture"
    question: str
    category: str
    weight: float
    is_required: bool
    expected_evidence: str | None
    order: int

  Project
    id: int
    name: str
    domain: str
    tech_stack: list[str]         # JSON column — list of strings

The generator receives plain Python model objects (already fetched from DB by the caller).
It must not import from FastAPI or SQLAlchemy.

### Exact file to create

Create app/services/action_plan_generator.py with the following content.
Use these exact imports at the top:

  from dataclasses import dataclass, field
  from typing import List, Optional
  from datetime import datetime, timezone

Define these three dataclasses in this order:

  @dataclass
  class AIPrompt:
      generic: str
      cursor: str
      claude_code: str

  @dataclass
  class ActionCard:
      item_code: str
      area: str
      question: str
      priority: str              # "High" (red) | "Medium" (amber)
      rag_status: str
      what_was_found: str        # = result.evidence
      what_to_fix: str           # derived (see rules below)
      expected_outcome: str      # = item.expected_evidence or ""
      assigned_to: str = "TBD"
      due_date: str = "TBD"
      ai_prompt: Optional[AIPrompt] = None

  @dataclass
  class ActionPlanResponse:
      job_id: int
      project: str
      checklist: str
      generated_at: str                       # ISO 8601 UTC datetime string
      summary: dict                            # keys: total, critical_blockers, advisories,
                                               #       sign_off_required, compliant
      critical_blockers: List[ActionCard]      # red items where needs_human_sign_off=False
      advisories: List[ActionCard]             # amber items where needs_human_sign_off=False
      sign_off_required: List[ActionCard]      # needs_human_sign_off=True (any rag_status)
      compliant_summary: List[dict]            # [{item_code, area, question}] for green items

Then define class ActionPlanGenerator with two methods:

  def generate(
      self,
      job: object,            # AutonomousReviewJob instance
      results: list,          # list of AutonomousReviewResult instances
      checklist_items: dict,  # {checklist_item_id: ChecklistItem}
      project: object,        # Project instance
      checklist_name: str
  ) -> ActionPlanResponse:

  def _build_prompt(
      self,
      result: object,         # AutonomousReviewResult
      item: object,           # ChecklistItem
      project: object         # Project
  ) -> AIPrompt:

### generate() logic

  generated_at = datetime.now(timezone.utc).isoformat()

  For each result in results:
    item = checklist_items.get(result.checklist_item_id)
    if item is None: skip

    if result.needs_human_sign_off is True:
      add to sign_off_required (priority based on rag_status: red→"High", amber→"Medium", else "Medium")
    elif result.rag_status == "red":
      add to critical_blockers with priority="High"
    elif result.rag_status == "amber":
      add to advisories with priority="Medium"
    elif result.rag_status == "green":
      add {"item_code": item.item_code, "area": item.area, "question": item.question}
      to compliant_summary

  For action cards (critical_blockers, advisories, sign_off_required):
    what_to_fix = "Implement: {item.expected_evidence}" if item.expected_evidence else
                  "Address the following: {item.question}"
    expected_outcome = item.expected_evidence or ""
    ai_prompt = self._build_prompt(result, item, project)

  summary = {
    "total": len(results),
    "critical_blockers": len(critical_blockers),
    "advisories": len(advisories),
    "sign_off_required": len(sign_off_required),
    "compliant": len(compliant_summary)
  }

### _build_prompt() logic

  Build a multi-line base string using these labelled blocks:

    CONTEXT:
    Project: {project.name}
    Tech stack: {", ".join(project.tech_stack) if project.tech_stack else "Not specified"}
    Files examined: {", ".join(result.files_checked) if result.files_checked else "None"}

    FINDING:
    {result.evidence}

    EXPECTED STANDARD:
    {item.expected_evidence if item.expected_evidence else "Not specified"}

    TASK:
    Fix the above gap. Ensure the solution satisfies: "{item.question}"

    ACCEPTANCE CRITERIA:
    {item.expected_evidence if item.expected_evidence else item.question}

  generic = base string (no prefix)
  cursor  = "@workspace\n" + base + "\nSearch the workspace for related files before making changes."
  claude_code = "Task:\n" + base + "\n\nRun tests after making changes."

### Important rules
- dataclasses.asdict() works recursively on nested dataclasses — AIPrompt inside ActionCard
  will be serialised correctly when the caller calls dataclasses.asdict(response)
- All methods are synchronous (no async, no await)
- Type hints on all method signatures
- Do NOT add docstrings or comments
- Do NOT import from fastapi, sqlalchemy, or any third-party library
```

---

## Prompt 2 — API Endpoints: GET + POST action-plan in `app/api/routes/reports.py`

```
You are an expert Python / FastAPI developer working in the ReviewBot codebase.

### What already exists in app/api/routes/reports.py

The current imports block at the top of reports.py is:

  """
  Reports API Routes
  """
  from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
  from fastapi.responses import FileResponse
  from sqlalchemy.ext.asyncio import AsyncSession
  from sqlalchemy import select, func
  from typing import List, Optional
  from datetime import datetime
  from pathlib import Path

  from app.db.session import get_db
  from app.models import (
      Report, ReportApproval, Review, User,
      Project, Checklist, AutonomousReviewJob,
      AutonomousReviewResult, AutonomousReviewOverride
  )
  from app.core.config import settings
  from sqlalchemy.orm import selectinload, joinedload
  from pydantic import BaseModel

  router = APIRouter()

The existing auth dependency is in app/api/routes/auth.py:

  from app.api.routes.auth import get_current_user

The existing LLM pattern is in app/services/checklist_optimizer.py.
The ChecklistOptimizer class is constructed and calls:
  self.llm = ChatOpenAI(model="gpt-4o", temperature=0.3, api_key=settings.OPENAI_API_KEY)
  response = await self.llm.ainvoke([SystemMessage(content="..."), HumanMessage(content="...")])
  text = response.content

The model relationships relevant here:
  AutonomousReviewJob.results  → list of AutonomousReviewResult (relationship name: "results")
  AutonomousReviewJob.project  → Project (relationship name: "project")
  AutonomousReviewJob.checklist → Checklist (relationship name: "checklist")
  Checklist.items              → list of ChecklistItem (relationship name: "items")

### Task

Add the following two endpoints to app/api/routes/reports.py.
Insert them at the END of the file, after all existing functions.

Also add these imports by merging into the existing import block (do not duplicate):
  from dataclasses import asdict
  from app.services.action_plan_generator import ActionPlanGenerator
  from app.api.routes.auth import get_current_user
  from langchain_openai import ChatOpenAI
  from langchain_core.messages import SystemMessage, HumanMessage

#### Endpoint 1: GET /api/autonomous-reviews/{job_id}/action-plan

  @router.get("/autonomous-reviews/{job_id}/action-plan")
  async def get_action_plan(
      job_id: int,
      db: AsyncSession = Depends(get_db),
      current_user: User = Depends(get_current_user)
  ):

  Logic:
  1. Load AutonomousReviewJob with eager loading:
       result = await db.execute(
           select(AutonomousReviewJob)
           .options(
               selectinload(AutonomousReviewJob.results),
               selectinload(AutonomousReviewJob.project),
               selectinload(AutonomousReviewJob.checklist)
                   .selectinload(Checklist.items)
           )
           .where(AutonomousReviewJob.id == job_id)
       )
       job = result.scalar_one_or_none()
  2. If job is None: raise HTTPException(status_code=404, detail="Job not found")
  3. If job.status != "completed": raise HTTPException(status_code=400, detail="Job is not completed")
  4. Build checklist_items dict:
       checklist_items = {item.id: item for item in job.checklist.items}
  5. Call:
       generator = ActionPlanGenerator()
       plan = generator.generate(
           job=job,
           results=job.results,
           checklist_items=checklist_items,
           project=job.project,
           checklist_name=job.checklist.name
       )
  6. Return: return asdict(plan)

  IMPORTANT: The route prefix is registered in main.py as "/api/autonomous-reviews" for
  routes from reports.py — verify this. If reports.py is registered under "/api/reports",
  then you must register the router again or check main.py. Do NOT change main.py —
  just note the correct URL in a comment above the endpoint.

#### Endpoint 2: POST /api/autonomous-reviews/{job_id}/action-plan/enhance

  @router.post("/autonomous-reviews/{job_id}/action-plan/enhance")
  async def enhance_action_plan(
      job_id: int,
      db: AsyncSession = Depends(get_db),
      current_user: User = Depends(get_current_user)
  ):

  Logic:
  1. Load job with .results eager loaded (same pattern as endpoint 1, but checklist.items too).
  2. If job is None: 404. If not completed: 400.
  3. Check idempotency:
       metadata = job.agent_metadata or {}
       if "action_plan_prompts" in metadata:
           return {"status": "already_enhanced"}
  4. Check LLM is configured:
       if not settings.OPENAI_API_KEY:
           raise HTTPException(status_code=400, detail="No LLM provider configured. Set ACTIVE_LLM_PROVIDER and the corresponding API key.")
  5. Instantiate LLM:
       llm = ChatOpenAI(model="gpt-4o", temperature=0.3, api_key=settings.OPENAI_API_KEY)
  6. Build checklist_items dict (same as endpoint 1).
  7. For each result in job.results where result.rag_status in ("red", "amber"):
       item = checklist_items.get(result.checklist_item_id)
       if item is None: continue
       Build base_prompt using ActionPlanGenerator()._build_prompt(result, item, job.project).generic
       Try:
         response = await llm.ainvoke([
             SystemMessage(content="You are a senior software engineer writing actionable remediation prompts for developers to paste into their AI IDE. Given the context below, produce an improved, specific, file-aware prompt that a developer can paste directly into Cursor, GitHub Copilot Chat, or Claude Code to fix the issue. Be specific: reference exact file paths, suggest the fix pattern, and include the acceptance criteria."),
             HumanMessage(content=base_prompt)
         ])
         improved = response.content
         metadata.setdefault("action_plan_prompts", {})[str(result.id)] = {
             "generic": improved,
             "cursor": "@workspace\n" + improved,
             "claude_code": "Task:\n" + improved + "\n\nAfter making changes, run the test suite to confirm the fix."
         }
       Except Exception as e:
         print(f"LLM enhance error for result {result.id}: {e}")
         continue
  8. Try:
       job.agent_metadata = metadata
       db.add(job)
       await db.commit()
     Except:
       await db.rollback()
       raise HTTPException(status_code=500, detail="Failed to save enhanced prompts")
  9. Return:
       prompts_count = len(metadata.get("action_plan_prompts", {}))
       return {"status": "enhanced", "prompts_generated": prompts_count}

### Requirements
- async def + await for all DB operations
- selectinload() for all relationship access — never access .results or .items without eager loading
- Merge new imports into the existing import block — do not create duplicate import lines
- Type hints on all function signatures
- Do NOT add docstrings or inline comments
- Do NOT change any existing function in reports.py
```

---

## Prompt 3 — Frontend: Action Plan Tab + CSS in `static/history.html`

```
You are an expert frontend developer (vanilla JS, no framework).
You are working on static/history.html in the ReviewBot project.

### What already exists in history.html

The details section HTML structure (simplified):

  <section id="details-section" style="display:none;">
    <div id="det-header">...</div>
    <div id="det-stats">...</div>

    <!-- filter bar -->
    <div style="display:flex; gap:8px; ...">
      <button ...>All</button>
      <button ...>🔴 Red</button>
      ...
      <button class="sort-btn" onclick="toggleSort()" id="sort-btn">↓ Code</button>
      <span class="results-summary" id="results-summary"></span>
    </div>

    <div class="items-container" id="det-items"></div>   ← EXISTING item grid
  </section>

The JS helper for authenticated API calls is:

  async function apiFetch(path, opts = {}) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), 20000);
    try {
      const res = await fetch(path, { ...opts, headers: { ...authHeader(), ...(opts.headers || {}) }, signal: controller.signal });
      clearTimeout(timer);
      if (res.status === 401) { if (!_logoutInProgress) logout(); return null; }
      if (!res.ok) throw new Error(await res.text());
      return await res.json();
    } catch (e) {
      clearTimeout(timer);
      if (e.name === 'AbortError') throw new Error('Request timed out');
      throw e;
    }
  }

Use apiFetch() for all new API calls — NOT fetch() directly.
escapeHtml(str) also already exists — use it for any user-supplied text.

The existing viewDetails() function signature:

  async function viewDetails(reportId, jobId, pushState = true) {
    currentReportId = reportId;
    currentJobId = jobId;
    ...
    document.getElementById('det-items').innerHTML = '';
    ...
    const data = await apiFetch(`/api/reports/${reportId}/details`);
    if (data === null) return;
    renderDetails(data);
  }

### Task — Part A: HTML changes

1. Wrap the existing `<div class="items-container" id="det-items"></div>` in a new outer div.
   Insert a tab bar BEFORE the items-container and add a new action plan container AFTER it.
   Replace this block in the HTML:

     <div class="items-container" id="det-items"></div>

   With:

     <div id="details-tabs" style="display:flex;gap:0;border-bottom:1px solid #334155;margin-bottom:16px;margin-top:16px;">
       <button class="dtab active" data-tab="items" onclick="switchDetailsTab('items')">Review Items</button>
       <button class="dtab" data-tab="action-plan" onclick="switchDetailsTab('action-plan')">Action Plan</button>
     </div>
     <div id="tab-items">
       <div class="items-container" id="det-items"></div>
     </div>
     <div id="tab-action-plan" style="display:none;"></div>

### Task — Part B: CSS to add

Add these rules inside the existing <style> block, just before the closing </style> tag:

  .dtab {
    background: none; border: none; color: #94a3b8;
    padding: 10px 18px; font-size: 13px; font-weight: 600;
    cursor: pointer; border-bottom: 2px solid transparent; transition: all 0.15s;
  }
  .dtab.active { color: #38bdf8; border-bottom-color: #38bdf8; }
  .dtab:hover:not(.active) { color: #e2e8f0; }

  .action-card {
    background: #1e293b; border: 1px solid #334155; border-radius: 10px;
    padding: 16px 20px; margin-bottom: 10px;
  }
  .action-card.priority-high  { border-left: 3px solid #ef4444; }
  .action-card.priority-medium { border-left: 3px solid #f59e0b; }

  .action-section-header {
    display: flex; align-items: center; gap: 10px;
    font-size: 14px; font-weight: 700; color: #e2e8f0;
    cursor: pointer; padding: 10px 0; user-select: none;
  }
  .action-section-header:hover { color: #38bdf8; }

  .prompt-block {
    display: none;
    background: #0f172a; border: 1px solid #334155; border-radius: 8px;
    padding: 12px 14px; font-size: 12px; color: #7dd3fc;
    white-space: pre-wrap; word-break: break-word; margin-top: 10px;
  }
  .prompt-block.visible { display: block; }

  .btn-copy-prompt {
    background: transparent; border: 1px solid #334155; color: #94a3b8;
    padding: 4px 10px; border-radius: 6px; font-size: 11px; cursor: pointer;
  }
  .btn-copy-prompt:hover { border-color: #38bdf8; color: #38bdf8; }

  .copied-badge {
    display: inline-block; background: #14532d; color: #4ade80;
    font-size: 11px; padding: 2px 8px; border-radius: 4px; margin-left: 6px;
    animation: fadeOut 1.5s forwards;
  }
  @keyframes fadeOut { 0% { opacity:1 } 80% { opacity:1 } 100% { opacity:0 } }

### Task — Part C: JS to add

Add the following JS functions inside the existing <script> block, just before the closing </script> tag.

  // ── Action Plan Tab ────────────────────────────────────────────────────

  let _actionPlanData = null;

  function switchDetailsTab(tab) {
    document.querySelectorAll('.dtab').forEach(b => b.classList.toggle('active', b.dataset.tab === tab));
    document.getElementById('tab-items').style.display        = tab === 'items'       ? '' : 'none';
    document.getElementById('tab-action-plan').style.display  = tab === 'action-plan' ? '' : 'none';
    if (tab === 'action-plan' && _actionPlanData === null) {
      loadActionPlan(currentJobId);
    }
  }

  async function loadActionPlan(jobId) {
    const container = document.getElementById('tab-action-plan');
    container.innerHTML = '<span class="spinner"></span>';
    const data = await apiFetch(`/api/autonomous-reviews/${jobId}/action-plan`);
    if (data === null) return;
    _actionPlanData = data;
    renderActionPlan();
  }

  function renderActionPlan() {
    const container = document.getElementById('tab-action-plan');
    if (!_actionPlanData) { container.innerHTML = '<p style="color:#94a3b8">No data.</p>'; return; }
    const d = _actionPlanData;
    const flavour = localStorage.getItem('reviewbot_ide_flavour') || 'generic';

    const toolbar = `
      <div style="display:flex;align-items:center;gap:12px;margin-bottom:16px;flex-wrap:wrap;">
        <label style="color:#94a3b8;font-size:13px;">IDE Flavour:
          <select id="ide-flavour" onchange="onFlavourChange(this.value)"
            style="margin-left:6px;background:#1e293b;color:#e2e8f0;border:1px solid #334155;border-radius:6px;padding:4px 8px;font-size:13px;">
            <option value="generic"    ${flavour==='generic'    ?'selected':''}>Generic</option>
            <option value="cursor"     ${flavour==='cursor'     ?'selected':''}>Cursor / Copilot</option>
            <option value="claude_code"${flavour==='claude_code'?'selected':''}>Claude Code</option>
          </select>
        </label>
        <button onclick="exportActionPlan()" class="btn-sm">Export MD</button>
        <button onclick="enhanceActionPlan(currentJobId)" class="btn-sm" id="btn-enhance">✨ Enhance with AI</button>
      </div>`;

    const sections = [
      { key: 'critical_blockers', label: '🔴 Critical Blockers', cards: d.critical_blockers },
      { key: 'advisories',        label: '🟡 Advisories',         cards: d.advisories },
      { key: 'sign_off_required', label: '🟣 Needs Sign-off',     cards: d.sign_off_required },
    ];

    const sectionsHtml = sections.map(s => {
      if (!s.cards.length) return '';
      const cardsHtml = s.cards.map((c, i) => renderActionCard(c, i, s.key, flavour)).join('');
      return `
        <div>
          <div class="action-section-header" onclick="toggleSection('sec-${s.key}')">
            ${escapeHtml(s.label)} (${s.cards.length})
            <span style="margin-left:auto;font-size:11px;color:#64748b" id="sec-${s.key}-arrow">▼</span>
          </div>
          <div id="sec-${s.key}">${cardsHtml}</div>
        </div>`;
    }).join('');

    const compliant = d.compliant_summary || [];
    const compliantHtml = compliant.length ? `
      <div>
        <div class="action-section-header" onclick="toggleSection('sec-compliant')">
          ✅ Already Compliant (${compliant.length})
          <span style="margin-left:auto;font-size:11px;color:#64748b" id="sec-compliant-arrow">▶</span>
        </div>
        <div id="sec-compliant" style="display:none;">
          ${compliant.map(c => `<div style="padding:6px 0;font-size:13px;color:#94a3b8;border-bottom:1px solid #1e293b;">
            <span style="color:#4ade80">${escapeHtml(c.item_code)}</span>
            <span style="margin-left:8px">${escapeHtml(c.area)}</span>
            <span style="margin-left:8px;color:#64748b">${escapeHtml(c.question)}</span>
          </div>`).join('')}
        </div>
      </div>` : '';

    container.innerHTML = toolbar + sectionsHtml + compliantHtml;
  }

  function renderActionCard(card, index, sectionKey, flavour) {
    const promptText = card.ai_prompt ? (card.ai_prompt[flavour] || card.ai_prompt.generic || '') : '';
    const cardId = `card-${sectionKey}-${index}`;
    const priorityClass = card.priority === 'High' ? 'priority-high' : 'priority-medium';
    return `
      <div class="action-card ${priorityClass}" id="${cardId}">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:8px;flex-wrap:wrap;">
          <span style="background:#0f172a;border:1px solid #334155;border-radius:6px;padding:2px 8px;font-size:11px;color:#94a3b8">${escapeHtml(card.area)}</span>
          <span style="background:${card.priority==='High'?'#7f1d1d':'#78350f'};color:${card.priority==='High'?'#fca5a5':'#fcd34d'};border-radius:6px;padding:2px 8px;font-size:11px;font-weight:700">${escapeHtml(card.priority)}</span>
          <span style="font-family:monospace;font-size:11px;color:#64748b">${escapeHtml(card.item_code)}</span>
        </div>
        <div style="font-size:13px;font-weight:600;color:#e2e8f0;margin-bottom:6px">${escapeHtml(card.question)}</div>
        <div style="font-size:12px;color:#94a3b8;margin-bottom:4px"><b style="color:#cbd5e1">What was found:</b> ${escapeHtml(card.what_was_found || '')}</div>
        <div style="font-size:12px;color:#94a3b8;margin-bottom:4px"><b style="color:#cbd5e1">What to fix:</b> ${escapeHtml(card.what_to_fix || '')}</div>
        <div style="font-size:12px;color:#94a3b8;margin-bottom:8px"><b style="color:#cbd5e1">Expected outcome:</b> ${escapeHtml(card.expected_outcome || 'Not specified')}</div>
        ${promptText ? `
          <button class="btn-copy-prompt" onclick="togglePrompt('${cardId}-prompt')">▶ Show AI Prompt</button>
          <pre class="prompt-block" id="${cardId}-prompt">${escapeHtml(promptText)}</pre>
          <div style="margin-top:6px;display:none" id="${cardId}-copy-row">
            <button class="btn-copy-prompt" onclick="copyPrompt('${cardId}-prompt', '${cardId}-copied')">📋 Copy</button>
            <span class="copied-badge" id="${cardId}-copied" style="display:none">Copied!</span>
          </div>` : ''}
      </div>`;
  }

  function toggleSection(id) {
    const el = document.getElementById(id);
    const arrow = document.getElementById(id + '-arrow');
    const hidden = el.style.display === 'none';
    el.style.display = hidden ? '' : 'none';
    if (arrow) arrow.textContent = hidden ? '▼' : '▶';
  }

  function togglePrompt(promptId) {
    const el = document.getElementById(promptId);
    const visible = el.classList.toggle('visible');
    const copyRow = document.getElementById(promptId.replace('-prompt', '-copy-row'));
    if (copyRow) copyRow.style.display = visible ? '' : 'none';
  }

  function copyPrompt(promptId, badgeId) {
    const text = document.getElementById(promptId).textContent;
    navigator.clipboard.writeText(text).then(() => {
      const badge = document.getElementById(badgeId);
      badge.style.display = 'inline-block';
      setTimeout(() => { badge.style.display = 'none'; }, 1600);
    });
  }

  function onFlavourChange(val) {
    localStorage.setItem('reviewbot_ide_flavour', val);
    renderActionPlan();
  }

  function exportActionPlan() {
    if (!_actionPlanData) return;
    const d = _actionPlanData;
    const flavour = localStorage.getItem('reviewbot_ide_flavour') || 'generic';
    const lines = [
      `# Action Plan — ${d.project} | ${d.checklist}`,
      `Generated: ${d.generated_at}`,
      `Compliance: ${d.summary.compliant}/${d.summary.total} items`,
      ''
    ];
    const sections = [
      { label: '## 🔴 Critical Blockers', cards: d.critical_blockers },
      { label: '## 🟡 Advisories',         cards: d.advisories },
      { label: '## 🟣 Needs Human Sign-off', cards: d.sign_off_required },
    ];
    sections.forEach(s => {
      if (!s.cards.length) return;
      lines.push(s.label, '');
      s.cards.forEach(c => {
        const prompt = c.ai_prompt ? (c.ai_prompt[flavour] || c.ai_prompt.generic || '') : '';
        lines.push(
          `### ${c.item_code} — ${c.area}`,
          `**${c.question}**`, '',
          `**What was found:** ${c.what_was_found}`,
          `**What to fix:** ${c.what_to_fix}`,
          `**Expected outcome:** ${c.expected_outcome || 'Not specified'}`, ''
        );
        if (prompt) {
          lines.push('**AI Prompt:**', '```', prompt, '```', '');
        }
        lines.push('---', '');
      });
    });
    const blob = new Blob([lines.join('\n')], { type: 'text/markdown' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = `action-plan-${currentJobId}.md`;
    a.click();
  }

  async function enhanceActionPlan(jobId) {
    const btn = document.getElementById('btn-enhance');
    if (btn) { btn.disabled = true; btn.textContent = '⏳ Enhancing…'; }
    const data = await apiFetch(`/api/autonomous-reviews/${jobId}/action-plan/enhance`, { method: 'POST' });
    if (data === null) { if (btn) { btn.disabled = false; btn.textContent = '✨ Enhance with AI'; } return; }
    _actionPlanData = null;
    await loadActionPlan(jobId);
  }

### Important rules
- Reset _actionPlanData = null inside viewDetails() when a new job is opened, so stale data
  from a previous job is not shown. Add this line inside viewDetails() right after
  `document.getElementById('det-items').innerHTML = '';`
  → Add: `_actionPlanData = null;`
  And also reset the tab to items:
  → Add: `switchDetailsTab('items');`
  But switchDetailsTab() uses _actionPlanData and DOM elements that may not be ready yet —
  so just set the tab state manually before the fetch:
      document.querySelectorAll('.dtab').forEach(b => b.classList.toggle('active', b.dataset.tab === 'items'));
      document.getElementById('tab-items').style.display = '';
      document.getElementById('tab-action-plan').style.display = 'none';

- The existing filter/sort bar (All, Red, Amber, Green, Compliance, Sort) is inside #tab-items
  already (it surrounds #det-items) — do NOT move it. If it is outside #tab-items in the
  current HTML, wrap both the filter bar and #det-items together inside #tab-items.

- Do NOT change any existing JS function behaviour.
- Do NOT add any new external script tags or CSS files.
- Vanilla JS only — no frameworks, no import/export.
```

---

## Prompt 4 — Integration Tests: `tests/test_action_plan_integration.py`

```
You are a Python testing expert working on the ReviewBot codebase (pytest + httpx AsyncClient).

### Existing test infrastructure in tests/conftest.py

  Fixtures available (all async, function-scoped unless noted):

  db_session — AsyncSession (function-scoped):
    async with TestingSessionLocal() as session:
        yield session
        # clears all table data after each test

  async_client — AsyncClient (function-scoped):
    Wraps the FastAPI app with get_db overridden to use db_session.
    Has NO default auth headers. Add auth headers per-request.

  create_test_user — factory fixture:
    Usage: user, headers = await create_test_user(role="admin")
    Returns (User ORM object, {"Authorization": "Bearer <token>"})

  project_factory — factory fixture:
    Usage: project = await project_factory(owner_id=user.id)
    Creates Project(name=..., domain="general", status="active", owner_id=owner_id)

  checklist_factory — factory fixture:
    Usage: chk = await checklist_factory(is_global=False, project_id=project.id)
    Creates Checklist(name="Test Checklist", type="delivery", version="1.0", ...)

  item_factory — factory fixture:
    Usage: item = await item_factory(checklist_id=chk.id, item_code="1.1", question="...", weight=1.0)
    Creates ChecklistItem(area="General", category="delivery", is_required=True, order=0)
    Does NOT set expected_evidence — set it manually on the item object then commit if needed.

### SQLAlchemy models for test setup

  AutonomousReviewJob (table: autonomous_review_jobs):
    id, project_id, checklist_id, source_path, status,
    total_items, completed_items, agent_metadata (JSON, nullable),
    created_by (nullable int)

  AutonomousReviewResult (table: autonomous_review_results):
    id, job_id, checklist_item_id,
    rag_status ("green"|"amber"|"red"|"na"|"skipped"),
    evidence (text), confidence (float),
    files_checked (JSON list), needs_human_sign_off (bool),
    evidence_hint (nullable text)

  Import both models:
    from app.models import AutonomousReviewJob, AutonomousReviewResult

### Task

Create tests/test_action_plan_integration.py — new file.

Add these exact imports at the top:

  import pytest
  import pytest_asyncio
  from httpx import AsyncClient
  from app.models import AutonomousReviewJob, AutonomousReviewResult

Do NOT import conftest fixtures — pytest discovers them automatically.

Add these four tests (all must use @pytest.mark.asyncio):

#### test_action_plan_groups_by_rag

  async def test_action_plan_groups_by_rag(async_client, db_session, create_test_user, project_factory, checklist_factory, item_factory):
    user, headers = await create_test_user(role="admin")
    project = await project_factory(owner_id=user.id)
    chk = await checklist_factory(is_global=False, project_id=project.id)

    item1 = await item_factory(chk.id, "1.1", "Is rate limiting configured?")
    item2 = await item_factory(chk.id, "1.2", "Is logging complete?")
    item3 = await item_factory(chk.id, "1.3", "Is JWT implemented?")
    item4 = await item_factory(chk.id, "1.4", "Is auth in place?")

    job = AutonomousReviewJob(
        project_id=project.id, checklist_id=chk.id,
        source_path="/tmp/test", status="completed",
        total_items=4, completed_items=4
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    results = [
        AutonomousReviewResult(job_id=job.id, checklist_item_id=item1.id, rag_status="red",   evidence="No rate limiting found",     needs_human_sign_off=False, files_checked=[], confidence=1.0),
        AutonomousReviewResult(job_id=job.id, checklist_item_id=item2.id, rag_status="amber", evidence="Partial logging",             needs_human_sign_off=False, files_checked=[], confidence=0.7),
        AutonomousReviewResult(job_id=job.id, checklist_item_id=item3.id, rag_status="green", evidence="JWT implemented",             needs_human_sign_off=False, files_checked=[], confidence=1.0),
        AutonomousReviewResult(job_id=job.id, checklist_item_id=item4.id, rag_status="red",   evidence="No authentication found",     needs_human_sign_off=True,  files_checked=[], confidence=0.5),
    ]
    for r in results:
        db_session.add(r)
    await db_session.commit()

    response = await async_client.get(f"/api/autonomous-reviews/{job.id}/action-plan", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert len(data["critical_blockers"]) == 1       # item1: red, no sign-off
    assert len(data["advisories"]) == 1               # item2: amber
    assert len(data["sign_off_required"]) == 1        # item4: red + needs_human_sign_off
    assert len(data["compliant_summary"]) == 1        # item3: green

    card = data["critical_blockers"][0]
    assert card["item_code"] == "1.1"
    assert card["priority"] == "High"
    assert card["what_was_found"] == "No rate limiting found"
    assert card["ai_prompt"]["generic"] != ""
    assert card["ai_prompt"]["cursor"].startswith("@workspace")
    assert card["ai_prompt"]["claude_code"].startswith("Task:")

#### test_action_plan_404_for_unknown_job

  async def test_action_plan_404_for_unknown_job(async_client, create_test_user):
    _, headers = await create_test_user()
    response = await async_client.get("/api/autonomous-reviews/99999/action-plan", headers=headers)
    assert response.status_code == 404

#### test_action_plan_400_for_non_completed_job

  async def test_action_plan_400_for_non_completed_job(async_client, db_session, create_test_user, project_factory, checklist_factory):
    user, headers = await create_test_user()
    project = await project_factory(owner_id=user.id)
    chk = await checklist_factory(is_global=False, project_id=project.id)
    job = AutonomousReviewJob(
        project_id=project.id, checklist_id=chk.id,
        source_path="/tmp/test", status="running",
        total_items=0, completed_items=0
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    response = await async_client.get(f"/api/autonomous-reviews/{job.id}/action-plan", headers=headers)
    assert response.status_code == 400

#### test_action_plan_prompt_contains_file_context

  async def test_action_plan_prompt_contains_file_context(async_client, db_session, create_test_user, project_factory, checklist_factory, item_factory):
    user, headers = await create_test_user()
    project = await project_factory(owner_id=user.id)
    chk = await checklist_factory(is_global=False, project_id=project.id)
    item = await item_factory(chk.id, "2.1", "Are JWT tokens validated with expiry?")

    # Set expected_evidence directly on the ORM object
    item.expected_evidence = "JWT tokens must be validated with expiry check"
    db_session.add(item)
    await db_session.commit()

    job = AutonomousReviewJob(
        project_id=project.id, checklist_id=chk.id,
        source_path="/tmp/test", status="completed",
        total_items=1, completed_items=1
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    r = AutonomousReviewResult(
        job_id=job.id, checklist_item_id=item.id,
        rag_status="red", evidence="No expiry validation found",
        needs_human_sign_off=False, confidence=1.0,
        files_checked=["src/auth.py", "src/middleware.py"]
    )
    db_session.add(r)
    await db_session.commit()

    response = await async_client.get(f"/api/autonomous-reviews/{job.id}/action-plan", headers=headers)
    assert response.status_code == 200
    data = response.json()

    assert len(data["critical_blockers"]) == 1
    prompt_generic = data["critical_blockers"][0]["ai_prompt"]["generic"]
    assert "src/auth.py" in prompt_generic
    assert "JWT tokens must be validated" in prompt_generic

### Requirements
- @pytest.mark.asyncio on every test function
- Do NOT define any fixtures in this file — use the ones from conftest.py
- All tests are independent — conftest clears all DB data between tests
- Type hints not required in test functions
```

---

## Prompt 5 — Verify Route Registration in `main.py`

```
You are reviewing the ReviewBot codebase to verify that two new API endpoints
are reachable at the correct URLs.

### What was added in Prompt 2

Two endpoints were added to app/api/routes/reports.py:

  GET  /api/autonomous-reviews/{job_id}/action-plan
  POST /api/autonomous-reviews/{job_id}/action-plan/enhance

The decorator paths in reports.py are:

  @router.get("/autonomous-reviews/{job_id}/action-plan")
  @router.post("/autonomous-reviews/{job_id}/action-plan/enhance")

### Task

Read main.py and find where app/api/routes/reports is registered:

  Look for:  app.include_router(reports.router, prefix="...")

Check what prefix is used. The final URLs will be:
  {prefix} + "/autonomous-reviews/{job_id}/action-plan"

If the prefix is "/api/reports", the final URL would be:
  /api/reports/autonomous-reviews/{job_id}/action-plan  ← WRONG

The frontend in history.html calls:
  /api/autonomous-reviews/{job_id}/action-plan

So the correct prefix for these two routes must result in "/api/autonomous-reviews/...".

### Fix options (choose the simplest):

Option A — Register the reports router with a second include_router call:
  In main.py, after the existing:
    app.include_router(reports.router, prefix="/api/reports", tags=["reports"])
  Add:
    app.include_router(reports.router, prefix="/api/autonomous-reviews", tags=["autonomous-reviews"])
  But this will double-register ALL endpoints in reports.py — avoid if reports.py has many routes.

Option B — Move only the two new action-plan endpoints to a new file:
  Create app/api/routes/action_plan.py with only the two endpoints.
  Register in main.py:
    from app.api.routes import action_plan
    app.include_router(action_plan.router, prefix="/api/autonomous-reviews", tags=["action-plan"])

Option C — Change the decorator paths in reports.py to include the full path:
  @router.get("/autonomous-reviews/{job_id}/action-plan")  ← keep as-is
  And register the router with prefix="/api":
    But this would break all existing /api/reports/* endpoints.

**Recommended: Use Option B.**

Create app/api/routes/action_plan.py by moving only the two new endpoints out of reports.py.
Register it in main.py. Keep reports.py unchanged for existing routes.

### What to produce

1. Create app/api/routes/action_plan.py with:
   - The same imports as reports.py (copy only what the two endpoints use)
   - router = APIRouter()
   - The GET and POST endpoints from Prompt 2 (verbatim, do not modify logic)

2. In main.py, add one line in the routers section:
   from app.api.routes import action_plan
   app.include_router(action_plan.router, prefix="/api/autonomous-reviews", tags=["action-plan"])

3. Remove the two endpoints from reports.py (keep all other routes intact).

If you are unsure about main.py structure, read it first before making changes.
```

---

## Prompt 6 — LLM Enrichment Refactor: `app/services/checklist_optimizer.py` pattern

```
You are a Python developer working on the ReviewBot codebase.

This prompt is OPTIONAL / Phase 2. Only implement this if Prompt 2's enhance endpoint
needs to support multiple LLM providers (not just OpenAI).

### Current pattern in app/services/checklist_optimizer.py

The ChecklistOptimizer class uses only OpenAI:

  class ChecklistOptimizer:
      def __init__(self):
          self.llm = None
          if settings.OPENAI_API_KEY:
              self.llm = ChatOpenAI(
                  model="gpt-4o",
                  temperature=0.3,
                  api_key=settings.OPENAI_API_KEY
              )
      ...
      async def _get_llm_recommendations(self, ...):
          response = await self.llm.ainvoke([system_message, user_message])
          return self._parse_llm_recommendations(response.content)

settings.ACTIVE_LLM_PROVIDER can be: "openai" | "anthropic" | "google" | "groq" | "qwen" | "azure"
The corresponding API key settings are: OPENAI_API_KEY, ANTHROPIC_API_KEY, GROQ_API_KEY, QWEN_API_KEY

### Task

Create a standalone helper function in a new file app/services/llm_client.py:

  from typing import Optional
  from langchain_core.messages import BaseMessage
  from app.core.config import settings

  def get_llm_client(temperature: float = 0.3):
      """
      Returns a LangChain chat model based on ACTIVE_LLM_PROVIDER setting.
      Returns None if no provider is configured.
      """
      provider = (settings.ACTIVE_LLM_PROVIDER or "openai").lower()

      if provider == "openai" and settings.OPENAI_API_KEY:
          from langchain_openai import ChatOpenAI
          return ChatOpenAI(model="gpt-4o", temperature=temperature, api_key=settings.OPENAI_API_KEY)

      if provider == "anthropic" and settings.ANTHROPIC_API_KEY:
          from langchain_anthropic import ChatAnthropic
          return ChatAnthropic(model="claude-3-5-sonnet-20241022", temperature=temperature, api_key=settings.ANTHROPIC_API_KEY)

      if provider == "groq" and settings.GROQ_API_KEY:
          from langchain_groq import ChatGroq
          return ChatGroq(model="llama-3.3-70b-versatile", temperature=temperature, api_key=settings.GROQ_API_KEY)

      if provider == "qwen" and settings.QWEN_API_KEY:
          from langchain_openai import ChatOpenAI
          return ChatOpenAI(
              model="qwen2.5-coder-32b-instruct",
              temperature=temperature,
              api_key=settings.QWEN_API_KEY,
              base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
          )

      # Fallback: try OpenAI if key is set
      if settings.OPENAI_API_KEY:
          from langchain_openai import ChatOpenAI
          return ChatOpenAI(model="gpt-4o", temperature=temperature, api_key=settings.OPENAI_API_KEY)

      return None

Then update the enhance endpoint in app/api/routes/action_plan.py (from Prompt 5) to use this:

  Replace:
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=400, detail="No LLM provider configured...")
    llm = ChatOpenAI(model="gpt-4o", temperature=0.3, api_key=settings.OPENAI_API_KEY)

  With:
    from app.services.llm_client import get_llm_client
    llm = get_llm_client()
    if llm is None:
        raise HTTPException(status_code=400, detail="No LLM provider configured. Set ACTIVE_LLM_PROVIDER and the corresponding API key.")

### Requirements
- Lazy imports inside each if-branch (avoids ImportError when a package is not installed)
- Do NOT modify checklist_optimizer.py — it continues to use ChatOpenAI directly
- Type hints on get_llm_client signature
- Do NOT add docstrings or comments
```
