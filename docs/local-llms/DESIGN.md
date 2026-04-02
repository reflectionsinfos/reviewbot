# Hybrid LLM Feature — Technical Design

**Feature:** Hybrid LLM Routing with Local Model Support  
**Version:** 1.1  
**Status:** Approved — In Development  
**Created:** 2026-04-02  
**Updated:** 2026-04-02

---

## 1. Current State (Confirmed by Code Analysis)

`StrategyRouter._auto_route()` in `strategy_router_agent.py` returns `llm_analysis`
unconditionally. The code comment at lines 6–10 states this explicitly:

```python
# default every checklist item to LLM analysis
# let reviewers override specific items to human_required or ai_and_human
# keep legacy deterministic strategies available only when explicitly selected
```

Result: all 103 items call the cloud LLM. `file_presence`, `pattern_scan`,
`metadata_check` analyzers exist but are never reached without a manual DB rule.

---

## 2. Target Architecture

```
ChecklistItems (103)
       │
       ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 0: Deterministic Pre-filter                          │
│  strategy_router_agent.py — _keyword_route()                │
│  Zero LLM calls · < 100ms · ~25-35 items classified        │
└────────────┬────────────────────────────────────────────────┘
             │ remaining ~70 items
             ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 1: Planning LLM  (ONE call)                          │
│  agent_orchestrator.py — _build_routing_plan()              │
│  Input:  file tree + project desc + remaining items         │
│  Output: JSON plan { strategy, complexity, files } per item │
│  Model:  local Ollama preferred → cloud fallback            │
└────────────┬────────────────────────────────────────────────┘
             │ routing plan
             ▼
┌─────────────────────────────────────────────────────────────┐
│  PHASE 2: Parallel Execution                                │
│  agent_orchestrator.py — item loop                          │
│                                                             │
│  file_presence / pattern_scan / metadata_check              │
│      → No LLM · analyzers run directly                      │
│                                                             │
│  llm_analysis [complexity=simple]                           │
│      → Local Ollama (1-2 files, factual question)           │
│                                                             │
│  llm_analysis [complexity=complex]  ← locked areas always   │
│      → Cloud LLM priority chain                             │
│        [1] Primary → 429 → [2] Fallback → [3] Local        │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Database Changes

### 3.1 New columns — `llm_configs`

```sql
ALTER TABLE llm_configs
  ADD COLUMN role              VARCHAR(20)  DEFAULT 'primary',
  ADD COLUMN priority          INTEGER      DEFAULT 1,
  ADD COLUMN is_enabled        BOOLEAN      DEFAULT true,
  ADD COLUMN strategy_affinity JSON         DEFAULT NULL;
```

Migration behaviour: `is_enabled = is_active`, `priority = 1`, `role = 'primary'`
for all existing rows. `is_active` column is kept but no longer written to after migration.

### 3.2 New column — `autonomous_review_jobs`

```sql
ALTER TABLE autonomous_review_jobs
  ADD COLUMN routing_plan JSON DEFAULT NULL;
```

Stores the Phase 1 plan output for audit and optional re-use on repeat reviews.

### 3.3 Alembic migration

File: `alembic/versions/xxxx_hybrid_llm_routing.py`

```python
def upgrade():
    # llm_configs new columns
    op.add_column("llm_configs", sa.Column("role", sa.String(20), server_default="primary"))
    op.add_column("llm_configs", sa.Column("priority", sa.Integer(), server_default="1"))
    op.add_column("llm_configs", sa.Column("is_enabled", sa.Boolean(), server_default="true"))
    op.add_column("llm_configs", sa.Column("strategy_affinity", postgresql.JSON(), nullable=True))
    op.execute("UPDATE llm_configs SET is_enabled = is_active, priority = 1")

    # autonomous_review_jobs new column
    op.add_column("autonomous_review_jobs",
        sa.Column("routing_plan", postgresql.JSON(), nullable=True))

def downgrade():
    op.drop_column("llm_configs", "strategy_affinity")
    op.drop_column("llm_configs", "is_enabled")
    op.drop_column("llm_configs", "priority")
    op.drop_column("llm_configs", "role")
    op.drop_column("autonomous_review_jobs", "routing_plan")
```

---

## 4. Model Changes — `app/models.py`

```python
class LLMConfig(Base):
    __tablename__ = "llm_configs"
    # ... existing columns unchanged ...

    # New columns
    role              = Column(String(20), default="primary")   # primary|fallback|local
    priority          = Column(Integer, default=1)               # 1 = highest
    is_enabled        = Column(Boolean, default=True)            # replaces is_active mutex
    strategy_affinity = Column(JSON, nullable=True)              # None = all strategies


class AutonomousReviewJob(Base):
    __tablename__ = "autonomous_review_jobs"
    # ... existing columns unchanged ...

    # New column
    routing_plan = Column(JSON, nullable=True)   # Phase 1 plan output
```

---

## 5. Phase 0 — Deterministic Pre-filter

### 5.1 Location

`app/agents/strategy_router_agent/strategy_router_agent.py`

Replace the `_auto_route()` method body. Current code returns `llm_analysis`
unconditionally. New code applies keyword rules first.

### 5.2 Rule Table

```python
# Ordered — first match wins
_KEYWORD_RULES = [
    # file_presence — existence questions
    {
        "triggers": ["is there a", "does the repo", "does the project have",
                     "is there an", "exists", "present in the repo"],
        "file_nouns": ["readme", "dockerfile", "docker", "ci", "pipeline",
                       "gitignore", "changelog", "license", "makefile",
                       "contributing", "helm", "kubernetes", "k8s"],
        "strategy": "file_presence",
    },
    # metadata_check — dependency/config questions
    {
        "areas": ["dependencies", "dependency management", "package management"],
        "triggers": ["package", "library", "dependency", "dependencies",
                     "version pinned", "lock file", "requirements"],
        "strategy": "metadata_check",
    },
    # pattern_scan — secret/credential detection
    {
        "triggers": ["hardcoded", "secret", "api key", "credential",
                     "password in code", "token in source"],
        "strategy": "pattern_scan",
        "patterns": [
            r'(?i)(password|secret|api_key|token)\s*=\s*["\'][^"\']{4,}',
            r'sk-[a-zA-Z0-9]{20,}',
            r'(?i)Authorization:\s*Bearer\s+[^\s"\']+',
        ],
    },
    # pattern_scan — test existence
    {
        "triggers": ["unit test", "test coverage", "are there tests",
                     "test suite", "automated test", "test file"],
        "strategy": "pattern_scan",
        "patterns": [
            r"import pytest", r"def test_", r"@Test", r"describe\(", r"it\(",
            r"import unittest", r"@pytest", r"spec\.rb",
        ],
    },
    # human_required — governance/process items
    {
        "areas": ["governance", "ownership", "financial", "legal",
                  "compliance", "sign-off", "approval", "stakeholder",
                  "architecture and design"],
        "triggers": ["who is responsible", "who owns", "named person",
                     "approved by", "sign off", "budget", "legal review"],
        "strategy": "human_required",
    },
]
```

### 5.3 Updated `_auto_route()` logic

```python
def _auto_route(self, item: ChecklistItem) -> StrategyConfig:
    question_lower = (item.question or "").lower()
    area_lower = (item.area or "").lower()

    for rule in _KEYWORD_RULES:
        area_match = any(a in area_lower for a in rule.get("areas", []))
        trigger_match = any(t in question_lower for t in rule.get("triggers", []))
        file_noun_match = any(f in question_lower for f in rule.get("file_nouns", []))

        if area_match or trigger_match or (
            rule["strategy"] == "file_presence" and trigger_match and file_noun_match
        ):
            return StrategyConfig(
                strategy=rule["strategy"],
                context_keywords=_extract_keywords(item.area, item.question),
                focus_prompt=item.question,
                patterns=rule.get("patterns"),
            )

    # Default: needs planning LLM to decide
    return StrategyConfig(
        strategy="llm_analysis",
        context_keywords=_extract_keywords(item.area, item.question),
        focus_prompt=item.question,
    )
```

---

## 6. Phase 1 — Planning LLM

### 6.1 Location

New function `_build_routing_plan()` in `agent_orchestrator.py`

### 6.2 Input construction

```python
async def _build_routing_plan(
    job: AutonomousReviewJob,
    items: list,           # items that survived Phase 0 (strategy == llm_analysis)
    file_index: AgentFileIndex,
    db: AsyncSession,
) -> dict[int, PlanEntry]:
    """
    Makes one LLM call to produce a per-item routing plan.
    Returns dict keyed by checklist_item_id.
    """
    fs = file_index.summary()
    file_tree = _format_file_tree(fs)          # paths + sizes, no content
    stack = _detect_stack(fs["extensions"])    # e.g. "Python, FastAPI"

    item_list = [
        {"id": item.id, "area": item.area, "question": item.question}
        for item in items
    ]

    prompt = PLANNING_PROMPT_TEMPLATE.format(
        project_name=job.project.name,
        description=job.project.description or "No description provided",
        stack=stack,
        file_tree=file_tree,
        items_json=json.dumps(item_list, indent=2),
    )
```

### 6.3 Planning prompt template

```
PLANNING_PROMPT_TEMPLATE = """
You are a technical review planner. Given a project's file structure and a list of
checklist items, assign the most efficient analysis strategy to each item.

PROJECT: {project_name}
DESCRIPTION: {description}
STACK: {stack}

FILE TREE:
{file_tree}

CHECKLIST ITEMS TO PLAN:
{items_json}

For each item, output a JSON array. Each entry MUST be one of:

1. Pattern scan (no LLM needed):
   {{"item_id": N, "strategy": "pattern_scan",
     "patterns": ["regex1", "regex2"],
     "files_scope": ["*.py"],
     "rationale": "one line"}}

2. File presence (no LLM needed):
   {{"item_id": N, "strategy": "file_presence",
     "file_patterns": ["Dockerfile", "*.yml"],
     "rationale": "one line"}}

3. LLM analysis — simple (answerable from 1-2 files, factual):
   {{"item_id": N, "strategy": "llm_analysis", "complexity": "simple",
     "files_to_read": ["src/auth.py"],
     "rationale": "one line"}}

4. LLM analysis — complex (cross-file reasoning, design quality):
   {{"item_id": N, "strategy": "llm_analysis", "complexity": "complex",
     "files_to_read": ["src/auth.py", "src/middleware.py"],
     "rationale": "one line"}}

Rules:
- Only reference files that exist in the FILE TREE above
- Prefer pattern_scan and file_presence over llm_analysis where possible
- Mark as complex if the question asks about quality, design, architecture, security posture
- Mark as simple if the question asks about presence, configuration, or a specific fact
- Output ONLY the JSON array, no other text
"""
```

### 6.4 Planning LLM selection

```python
# Try local Ollama first (free, no rate limit)
planning_client, planning_config = await _get_planning_client(db)

response = await planning_client.chat.completions.create(
    model=planning_config.model_name,
    messages=[
        {"role": "system", "content": "You are a JSON-only technical review planner."},
        {"role": "user",   "content": prompt},
    ],
    temperature=0.0,          # deterministic
    max_tokens=4000,          # enough for 70-item plan
    response_format={"type": "json_object"},  # if supported
)

async def _get_planning_client(db) -> tuple[AsyncOpenAI, LLMConfig]:
    """Prefer local Ollama for planning — simple task, free, no rate limit."""
    chain = await get_config_chain(db)
    local = [c for c in chain if c.provider == "ollama"]
    if local:
        return build_client(local[0]), local[0]
    # Fall back to lowest-priority cloud config (save quota)
    return build_client(chain[-1]), chain[-1]
```

### 6.5 Plan validation and storage

```python
def _validate_plan(raw_plan: list, items: list, file_index) -> dict[int, PlanEntry]:
    valid_paths = set(file_index.all_paths())
    item_ids = {i.id for i in items}
    result = {}

    for entry in raw_plan:
        item_id = entry.get("item_id")
        if item_id not in item_ids:
            continue

        # Validate file paths
        files = entry.get("files_to_read") or entry.get("file_patterns") or []
        valid_files = [f for f in files if f in valid_paths or "*" in f]

        result[item_id] = PlanEntry(
            strategy=entry.get("strategy", "llm_analysis"),
            complexity=entry.get("complexity", "complex"),
            files=valid_files,
            patterns=entry.get("patterns", []),
            rationale=entry.get("rationale", ""),
        )

    # Items missing from plan → complex llm_analysis (safe default)
    for item in items:
        if item.id not in result:
            result[item.id] = PlanEntry(strategy="llm_analysis", complexity="complex")

    return result

# Store plan on job for audit/re-use
job.routing_plan = [e.to_dict() for e in result.values()]
await db.commit()
```

---

## 7. Phase 2 — Execution Split

### 7.1 LLM complexity routing

```python
# Locked areas — always cloud LLM regardless of plan
CLOUD_LOCKED_AREAS = {
    "architecture", "architecture & design", "architecture and design",
    "security", "security architecture", "security design",
    "governance", "compliance", "sign-off",
}

def _effective_complexity(item, plan_entry: PlanEntry) -> str:
    """Override plan complexity for locked areas."""
    area = (item.area or "").lower()
    if any(locked in area for locked in CLOUD_LOCKED_AREAS):
        return "complex"
    return plan_entry.complexity
```

### 7.2 Updated item execution loop

```python
for idx, item in enumerate(items):
    plan_entry = routing_plan.get(item.id, PlanEntry(strategy="llm_analysis", complexity="complex"))
    strategy = plan_entry.strategy

    if strategy == "human_required":
        analysis = _skipped("Human review required", plan_entry.rationale)

    elif strategy == "file_presence":
        analysis = await file_presence_analyzer.analyze(item, file_index,
                       StrategyConfig(strategy="file_presence",
                                      file_patterns=plan_entry.files))

    elif strategy == "pattern_scan":
        analysis = await pattern_scan_analyzer.analyze(item, file_index,
                       StrategyConfig(strategy="pattern_scan",
                                      patterns=plan_entry.patterns))

    elif strategy == "metadata_check":
        analysis = await metadata_analyzer.analyze(item, file_index,
                       StrategyConfig(strategy="metadata_check"))

    else:  # llm_analysis
        complexity = _effective_complexity(item, plan_entry)

        if complexity == "simple":
            # Local Ollama — simple factual check
            client, cfg = await get_local_or_fallback(config_chain)
        else:
            # Cloud LLM priority chain
            client, cfg = await get_cloud_or_fallback(config_chain)

        try:
            analysis = await llm_analyzer.analyze(
                item, file_index,
                StrategyConfig(strategy="llm_analysis",
                               context_keywords=plan_entry.files),
                client=client,
                model=cfg.model_name,
            )
        except RateLimitError:
            # Try next in chain
            client, cfg = await get_next_in_chain(config_chain, cfg)
            analysis = await llm_analyzer.analyze(item, file_index, ...,
                                                   client=client, model=cfg.model_name)
        except LLMChainExhaustedError:
            analysis = AnalysisResult(rag_status="na",
                                      evidence="All LLM providers exhausted")
```

### 7.3 Config chain helpers

New functions in `connectors/llm.py`:

```python
async def get_config_chain(db, strategy=None) -> list[LLMConfig]:
    """Enabled configs ordered by priority, optionally filtered by strategy."""
    result = await db.execute(
        select(LLMConfig).where(LLMConfig.is_enabled == True)
                         .order_by(LLMConfig.priority)
    )
    configs = result.scalars().all()
    if strategy:
        configs = [c for c in configs
                   if c.strategy_affinity is None
                   or strategy in (c.strategy_affinity or [])]
    return configs


def build_client(config: LLMConfig) -> AsyncOpenAI:
    PROVIDER_BASE_URLS = {
        "groq":    "https://api.groq.com/openai/v1",
        "google":  "https://generativelanguage.googleapis.com/v1beta/openai/",
        "ollama":  "http://localhost:11434/v1",
    }
    base_url = config.base_url or PROVIDER_BASE_URLS.get(config.provider)
    return AsyncOpenAI(api_key=config.api_key, base_url=base_url)


async def get_local_or_fallback(chain: list[LLMConfig]) -> tuple[AsyncOpenAI, LLMConfig]:
    """Prefer local Ollama; fall back to lowest-priority cloud config."""
    local = [c for c in chain if c.provider == "ollama"]
    target = local[0] if local else chain[-1]
    return build_client(target), target


async def get_cloud_or_fallback(chain: list[LLMConfig]) -> tuple[AsyncOpenAI, LLMConfig]:
    """Use highest-priority non-local config."""
    cloud = [c for c in chain if c.provider != "ollama"]
    if not cloud:
        raise LLMChainExhaustedError("No cloud LLM configured")
    return build_client(cloud[0]), cloud[0]


class LLMChainExhaustedError(Exception):
    pass
```

---

## 8. New API Endpoints — `llm_configs.py`

### `GET /api/llm-configs/chain`
Returns enabled configs in priority order for the chain visualizer.

### `POST /api/llm-configs/test-ollama`
Pings `GET {base_url}/api/tags` to verify model is pulled:
```json
Request:  {"base_url": "http://localhost:11434/v1", "model_name": "qwen2.5-coder:7b"}
Response: {"success": true, "message": "Model 'qwen2.5-coder:7b' is available"}
```

### Updated `PATCH /api/llm-configs/{id}`
Accepts new fields: `role`, `priority`, `is_enabled`, `strategy_affinity`.
On priority change, shifts other configs to avoid conflicts.

---

## 9. UI Changes — `system_config.html`

### Provider dropdown — add Ollama
```
OpenAI | Anthropic | Groq | Azure OpenAI | Ollama (Local) | Custom
```
When Ollama selected: auto-fill Base URL, API Key, Role=local.

### Form — new fields
- **Role**: radio buttons (Primary / Fallback / Local)
- **Priority**: number input (1 = highest)
- **Strategy Affinity**: checkboxes (All / llm_analysis / pattern_scan / metadata_check / file_presence)

### Card redesign
```
#1  [PRIMARY]  [CLOUD]  [ENABLED]
GPT-4o Production · openai · gpt-4o
Handles: All strategies
1,240 requests · 892K tokens
[↑][↓]  [Edit]  [Disable]  [Delete]
```

### Fallback Chain Visualizer
```
Active Chain
[1] GPT-4o Primary ──429──▶ [2] Groq Backup ──429──▶ [3] Ollama Local
    cloud                       cloud                      local
```

---

## 10. Implementation Order

| Step | Task | Files | Risk |
|---|---|---|---|
| 1 | Alembic migration | `alembic/versions/` | Low |
| 2 | Model update | `models.py` | Low |
| 3 | Connector refactor | `connectors/llm.py` | Medium |
| 4 | Phase 0 — keyword rules in router | `strategy_router_agent.py` | Low |
| 5 | Phase 1 — planning LLM | `agent_orchestrator.py` | Medium |
| 6 | Phase 2 — execution split | `agent_orchestrator.py` | Medium |
| 7 | New/updated API routes | `llm_configs.py` | Low |
| 8 | UI form + cards + chain visualizer | `system_config.html` | Low |
| 9 | Test with sample projects via Ollama | — | Validation |

---

## 11. Configuration Scenarios

### Scenario A: Cloud only (existing behaviour, no changes)
```
Config #1: GPT-4o · priority=1 · is_enabled=true · affinity=null
```
Phase 0 still runs and saves ~30 items. Planning LLM uses GPT-4o.

### Scenario B: Ollama for planning + simple; cloud for complex
```
Config #1: GPT-4o  · priority=1 · role=primary · affinity=null
Config #2: Ollama  · priority=2 · role=local   · affinity=null
```
Planning → Ollama. Simple llm_analysis → Ollama. Complex → GPT-4o.

### Scenario C: Full hybrid with middle-tier fallback
```
Config #1: GPT-4o  · priority=1 · role=primary  · affinity=null
Config #2: Groq    · priority=2 · role=fallback  · affinity=["llm_analysis"]
Config #3: Ollama  · priority=3 · role=local     · affinity=null
```
GPT-4o → 429 → Groq → 429 → Ollama. Planning uses Ollama (local preferred).

### Scenario D: Local-only development (no cloud keys)
```
Config #1: Ollama · priority=1 · role=local · affinity=null
```
All phases use Ollama. Slow on CPU but zero cost. Good for testing sample projects.
