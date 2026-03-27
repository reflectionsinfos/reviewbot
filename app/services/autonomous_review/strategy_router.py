"""
Strategy Router
Maps each checklist item (area + question) to the best analysis strategy
and provides configuration for the chosen analyzer.
"""
from __future__ import annotations
import re
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class StrategyConfig:
    strategy: str   # file_presence | pattern_scan | llm_analysis | metadata_check | human_required | ai_and_human

    # FILE_PRESENCE config
    file_patterns: list[str] = field(default_factory=list)
    dir_patterns: list[str] = field(default_factory=list)

    # PATTERN_SCAN config
    scan_patterns: list[str] = field(default_factory=list)   # regex list
    scan_extensions: Optional[list[str]] = None
    invert_match: bool = False          # True → GREEN if pattern NOT found

    # LLM_ANALYSIS config
    context_keywords: list[str] = field(default_factory=list)
    focus_prompt: str = ""

    # METADATA_CHECK config
    metadata_files: list[str] = field(default_factory=list)
    metadata_check: str = ""           # "dependencies_scanned" | "deprecated" | "license"

    # HUMAN_REQUIRED config
    skip_reason: str = ""
    evidence_hint: str = ""

    # AI_AND_HUMAN config
    needs_human_sign_off: bool = False  # Run AI analyzer but flag result for human confirmation


# ── Human-required detection ─────────────────────────────────────────────────

_HUMAN_AREAS = {
    "financial health",
    "customer success & growth",
    "ai adoption",
    "ai usage",
    "ai practices",
}

_HUMAN_QUESTION_PATTERNS = [
    # Interview / survey phrasing — these can never be answered by scanning files
    r"how are you (currently )?using",
    r"what steps do you take",
    r"how has (ai|automation|tooling).*impacted",
    r"are you aware of and following",
    r"do you use ai to support",
    r"how do you (currently )?use ai",
    r"what (ai|llm|copilot|genai|generative) tools",
    r"guidelines or restrictions for using",
    r"morale",
    r"csat",
    r"\bnps\b",
    r"billing",
    r"\bbudget\b",
    r"margins?",
    r"utilization",
    r"governance cadence",
    r"steering committee",
    r"stakeholder communications timely",
    r"backlog refinement.*demo",
    r"customer escalations",
    r"attrition",
    r"upsell",
    r"cross.?sell",
    r"building references",
    r"mandatory training",
    r"right mix of skills",
    r"succession.*critical roles",
    r"single points? of failure",
    r"scope.*change.*decision.*commercial",
    r"scope.*sow.*baseline",
    r"decision logs.*action items",
    r"issues resolved within.*sla",
    r"stakeholder.*sign.?off",
]
_HUMAN_COMPILED = [re.compile(p, re.IGNORECASE) for p in _HUMAN_QUESTION_PATTERNS]


def _is_human_required(area: str, question: str) -> Optional[StrategyConfig]:
    if area.lower() in _HUMAN_AREAS:
        hint = _build_evidence_hint(area, question)
        return StrategyConfig(
            strategy="human_required",
            skip_reason=f"Area '{area}' requires human/organisational data — interview or survey team members",
            evidence_hint=hint,
        )
    combined = f"{area} {question}"
    for pattern in _HUMAN_COMPILED:
        if pattern.search(combined):
            return StrategyConfig(
                strategy="human_required",
                skip_reason="Requires process, people, or organisational data",
                evidence_hint=_build_evidence_hint(area, question),
            )
    return None


def _build_evidence_hint(area: str, question: str) -> str:
    q = question.lower()
    if "ai" in area.lower() or any(w in q for w in ("ai tool", "copilot", "llm", "generative", "chatgpt")):
        return "Provide: team survey results, AI tool usage policy, or interview notes from developers"
    if "budget" in q or "billing" in q or "margins" in q:
        return "Provide: actuals vs budget report, billing records, or finance dashboard"
    if "csat" in q or "nps" in q or "feedback" in q:
        return "Provide: CSAT survey results, NPS scores, or customer feedback log"
    if "morale" in q or "collaboration" in q:
        return "Provide: team pulse survey results or manager assessment"
    if "attrition" in q or "capacity" in q or "skills" in q:
        return "Provide: team capacity plan, skills matrix, or staffing sheet"
    if "escalation" in q:
        return "Provide: escalation log, stakeholder communication records"
    if "upsell" in q or "growth" in q:
        return "Provide: account plan, pipeline report, or commercial opportunities log"
    if "governance" in q or "cadence" in q:
        return "Provide: meeting minutes, status reports, or governance log"
    return "Provide supporting documentation or organisational records"


# ── FILE_PRESENCE rules ───────────────────────────────────────────────────────

_FILE_PRESENCE_RULES: list[tuple[list[str], StrategyConfig]] = [
    # Architecture
    (["architecture.*documented", "target architecture", "context.*container.*component"],
     StrategyConfig(
         strategy="file_presence",
         file_patterns=["ARCHITECTURE.md", "architecture.md", "*.drawio", "*.puml", "*.erd"],
         dir_patterns=["docs/arch*", "docs/architecture*", "architecture/"],
         context_keywords=["architecture", "design", "diagrams"],
     )),
    # HLD / LLD
    (["hld.*lld", "high.level.*low.level", "hld and lld", "lld.*hld"],
     StrategyConfig(
         strategy="file_presence",
         file_patterns=["HLD*", "LLD*", "high-level*", "low-level*", "hld.*", "lld.*"],
         dir_patterns=["docs/design*", "design/"],
         context_keywords=["HLD", "LLD", "design document"],
     )),
    # ADR / architectural decisions
    (["architectural decisions", "trade-offs documented", "adr"],
     StrategyConfig(
         strategy="file_presence",
         file_patterns=["ADR-*.md", "adr-*.md", "*.adr.md"],
         dir_patterns=["docs/adr*", "adr/", "docs/decisions*", "decisions/"],
         context_keywords=["ADR", "architectural decision", "decision record"],
     )),
    # API documentation
    (["api documentation", "swagger", "openapi", "postman", "asyncapi"],
     StrategyConfig(
         strategy="file_presence",
         file_patterns=["swagger.json", "swagger.yaml", "openapi.json", "openapi.yaml",
                        "openapi.yml", "swagger.yml", "*.postman_collection.json"],
         dir_patterns=["api-docs/", "docs/api/", "swagger/", "openapi/"],
         context_keywords=["swagger", "openapi", "API documentation"],
     )),
    # Developer onboarding / contributing
    (["developer onboarding", "local setup.*coding standards", "onboarding documentation"],
     StrategyConfig(
         strategy="file_presence",
         file_patterns=["CONTRIBUTING.md", "SETUP.md", "ONBOARDING.md",
                        "contributing.md", "setup.md", "onboarding.md"],
         dir_patterns=["docs/dev/", "docs/contributing/"],
         context_keywords=["onboarding", "setup", "contributing"],
     )),
    # Install / deployment docs
    (["installation.*deployment.*configuration.*documented",
      "deployment.*configuration steps.*documented",
      "clean environment"],
     StrategyConfig(
         strategy="file_presence",
         file_patterns=["README.md", "INSTALL.md", "DEPLOY.md", "DEPLOYMENT.md",
                        "install.md", "deploy.md"],
         dir_patterns=["docs/deployment/", "deploy/", "docs/install/"],
         context_keywords=["installation", "deployment", "setup"],
     )),
    # Test strategy
    (["documented test strategy", "test strategy.*covering"],
     StrategyConfig(
         strategy="file_presence",
         file_patterns=["TEST_STRATEGY.md", "TESTING.md", "test-strategy.md",
                        "test_strategy.md", "test-plan*", "test_plan*"],
         dir_patterns=["docs/test*", "test-docs/"],
         context_keywords=["test strategy", "testing plan"],
     )),
    # CI/CD pipeline
    (["ci/cd pipeline.*implemented", "ci.*cd.*pipeline"],
     StrategyConfig(
         strategy="file_presence",
         file_patterns=["Jenkinsfile", "*.jenkins", "azure-pipelines.yml",
                        "circle.yml", ".travis.yml", "bitbucket-pipelines.yml"],
         dir_patterns=[".github/workflows/", ".github/", ".circleci/", ".gitlab-ci*"],
         context_keywords=["CI", "CD", "pipeline", "GitHub Actions"],
     )),
    # IaC
    (["infrastructure.as.code", "\\biac\\b", "terraform", "ansible", "helm"],
     StrategyConfig(
         strategy="file_presence",
         file_patterns=["*.tf", "*.hcl", "*.tfvars", "playbook*.yml",
                        "Chart.yaml", "chart.yaml"],
         dir_patterns=["terraform/", "ansible/", "k8s/", "kubernetes/", "helm/",
                       "infra/", "infrastructure/", "cloudformation/"],
         context_keywords=["Terraform", "IaC", "infrastructure"],
     )),
    # On-call / runbooks
    (["on.call model", "runbook", "escalation matrix.*production", "support.*sop"],
     StrategyConfig(
         strategy="file_presence",
         file_patterns=["RUNBOOK.md", "runbook.md", "RUNBOOKS.md", "ON_CALL.md",
                        "on-call.md", "SOP*.md", "OPERATIONS.md"],
         dir_patterns=["runbooks/", "docs/runbooks/", "docs/operations/", "ops/"],
         context_keywords=["runbook", "on-call", "operations"],
     )),
    # LICENSE / third-party
    (["licensing requirements", "third.party.*licens", "licens.*third.party"],
     StrategyConfig(
         strategy="file_presence",
         file_patterns=["LICENSE", "LICENSE.txt", "LICENSE.md", "NOTICE", "NOTICE.txt"],
         dir_patterns=["licenses/"],
         context_keywords=["license", "licensing"],
     )),
    # Backup / DR
    (["backup.*restore.*strateg", "backup.*documented", "dr runbook"],
     StrategyConfig(
         strategy="file_presence",
         file_patterns=["BACKUP*.md", "DR.md", "DISASTER_RECOVERY*.md",
                        "backup*.sh", "restore*.sh", "backup*.py"],
         dir_patterns=["backup/", "dr/", "docs/backup/"],
         context_keywords=["backup", "disaster recovery", "restore"],
     )),
    # Data models / ER diagrams
    (["data models.*er diagram", "er diagram", "integration contracts"],
     StrategyConfig(
         strategy="file_presence",
         file_patterns=["*.erd", "ER*.png", "ER*.svg", "data-model*",
                        "schema*.sql", "schema*.md"],
         dir_patterns=["docs/data/", "docs/db/", "docs/schema/"],
         context_keywords=["ER diagram", "data model", "schema"],
     )),
    # Go-live checklist
    (["go.live.*checklist", "operational readiness checklist"],
     StrategyConfig(
         strategy="file_presence",
         file_patterns=["GO_LIVE*.md", "RELEASE_CHECKLIST*.md", "LAUNCH*.md",
                        "go-live*.md"],
         dir_patterns=["docs/release/", "release/"],
         context_keywords=["go-live", "release checklist", "launch"],
     )),
]

# Pre-compile patterns
_FILE_RULES_COMPILED: list[tuple[list, StrategyConfig]] = [
    ([re.compile(p, re.IGNORECASE) for p in patterns], config)
    for patterns, config in _FILE_PRESENCE_RULES
]


# ── PATTERN_SCAN rules ────────────────────────────────────────────────────────

_PATTERN_SCAN_RULES: list[tuple[list[str], StrategyConfig]] = [
    # Hardcoded secrets / externalized credentials
    (["hardcoded.*credentials", "never hardcoded", "externalized.*config",
      "secrets.*vault.*never.*hardcoded", "secrets.*committed"],
     StrategyConfig(
         strategy="pattern_scan",
         scan_patterns=[
             r'(?i)(password|passwd|secret|api_key|apikey|token|access_key'
             r'|private_key|client_secret)\s*=\s*["\'][^"\']{6,}["\']',
             r'(?i)AWS_ACCESS_KEY_ID\s*=\s*["\'][A-Z0-9]{16,}',
             r'(?i)-----BEGIN (RSA |EC )?PRIVATE KEY-----',
         ],
         scan_extensions=[".py", ".js", ".ts", ".java", ".cs", ".go", ".rb",
                          ".yml", ".yaml", ".json", ".env", ".properties", ".cfg"],
         invert_match=True,  # GREEN = no matches found
     )),
    # Env vars in pipelines secured
    (["secrets.*pipeline.*secure", "credentials.*pipeline.*never.*embedded"],
     StrategyConfig(
         strategy="pattern_scan",
         scan_patterns=[
             r'(?i)(password|secret|api_key|token)\s*=\s*["\'][^"\'${}]{6,}',
         ],
         scan_extensions=[".yml", ".yaml", ".groovy"],
         invert_match=True,
     )),
    # HTTPS / TLS enforced
    (["https.*tls.*enforced", "https.*tls.*external.*internal",
      "http.*tls.*enforced"],
     StrategyConfig(
         strategy="pattern_scan",
         scan_patterns=[
             r'(?i)http://(?!localhost|127\.0\.0\.1|0\.0\.0\.0)',
         ],
         scan_extensions=[".py", ".js", ".ts", ".java", ".cs", ".go",
                          ".yml", ".yaml", ".json", ".env", ".conf", ".cfg"],
         invert_match=True,
     )),
    # Unit tests present / coverage
    (["unit tests present.*coverage", "unit test.*meaningful.*coverage"],
     StrategyConfig(
         strategy="pattern_scan",
         scan_patterns=[
             r'def test_',
             r'it\s*\(',
             r'@Test\b',
             r'describe\s*\(',
         ],
         scan_extensions=[".py", ".js", ".ts", ".java", ".cs", ".go", ".rb", ".spec.*"],
         invert_match=False,
     )),
    # Dead code / TODO/FIXME
    (["dead code.*cleaned", "unused configuration.*cleaned", "todo.*fixme"],
     StrategyConfig(
         strategy="pattern_scan",
         scan_patterns=[r'(?i)\b(TODO|FIXME|HACK|XXX|TEMP|TEMPORARY)\b'],
         invert_match=False,   # amber/red = many found; green = none
     )),
    # Caching used
    (["caching.*batching.*asynchronous", "caching.*used.*appropriately",
      "response.*caching"],
     StrategyConfig(
         strategy="pattern_scan",
         scan_patterns=[
             r'(?i)(redis|memcached|cache\.set|cache\.get|@cacheable|lru_cache)',
         ],
         invert_match=False,
     )),
    # Retry / circuit-breaker patterns
    (["retry", "circuit.?breaker", "bulkhead", "resiliency patterns"],
     StrategyConfig(
         strategy="pattern_scan",
         scan_patterns=[
             r'(?i)(retry|circuit.?breaker|tenacity|resilience4j|polly'
             r'|backoff|exponential|@retryable)',
         ],
         invert_match=False,
     )),
    # Static analysis / linter
    (["static analysis.*linter.*enabled", "static analysis.*free of critical"],
     StrategyConfig(
         strategy="pattern_scan",
         scan_patterns=[
             r'(?i)(flake8|pylint|eslint|sonarqube|sonar-scanner|checkstyle|rubocop)',
         ],
         scan_extensions=[".yml", ".yaml", ".cfg", ".ini", ".toml", ".json", ".sh"],
         invert_match=False,
     )),
    # Error handling
    (["error handling consistent", "meaningful.*messages.*no silent failures"],
     StrategyConfig(
         strategy="pattern_scan",
         scan_patterns=[
             r'(?i)except\s*:',          # bare except (Python bad pattern)
             r'catch\s*\(\s*\)',          # empty catch (JS/Java bad pattern)
             r'\.catch\s*\(\s*\)',        # empty .catch()
         ],
         invert_match=True,
     )),
]

_PATTERN_RULES_COMPILED: list[tuple[list, StrategyConfig]] = [
    ([re.compile(p, re.IGNORECASE) for p in patterns], config)
    for patterns, config in _PATTERN_SCAN_RULES
]


# ── METADATA_CHECK rules ──────────────────────────────────────────────────────

_METADATA_RULES: list[tuple[list[str], StrategyConfig]] = [
    (["third.party.*scan", "container images.*scan", "dependabot", "snyk",
      "software composition analysis"],
     StrategyConfig(
         strategy="metadata_check",
         metadata_check="dependencies_scanned",
         metadata_files=["package.json", "requirements.txt", ".github/dependabot.yml",
                         ".snyk", "snyk.yml"],
     )),
    (["deprecated.*component", "legacy.*migration plan"],
     StrategyConfig(
         strategy="metadata_check",
         metadata_check="deprecated",
         metadata_files=["requirements.txt", "package.json", "pom.xml", "build.gradle"],
     )),
    (["coverage.*measured.*minimum thresholds", "test coverage.*thresholds"],
     StrategyConfig(
         strategy="metadata_check",
         metadata_check="coverage_thresholds",
         metadata_files=[".coveragerc", "codecov.yml", "jest.config.js",
                         "jest.config.ts", "pyproject.toml"],
     )),
]

_META_RULES_COMPILED: list[tuple[list, StrategyConfig]] = [
    ([re.compile(p, re.IGNORECASE) for p in patterns], config)
    for patterns, config in _METADATA_RULES
]


# ── LLM keyword extraction ───────────────────────────────────────────────────

_AREA_KEYWORD_MAP: dict[str, list[str]] = {
    "architecture & design": ["architecture", "design", "diagram", "pattern", "ARCHITECTURE"],
    "technical documentation": ["docs", "documentation", "readme", "wiki"],
    "data & storage design": ["database", "schema", "model", "migration", "query"],
    "security architecture": ["security", "auth", "jwt", "oauth", "token", "encryption"],
    "code quality & standards": ["source", "code", "lint", "style", "test"],
    "testing & coverage": ["test", "spec", "coverage", "pytest", "jest"],
    "devsecops": ["pipeline", "ci", "cd", "deploy", "Dockerfile", "workflow"],
    "environments & infrastructure": ["docker", "compose", "config", "env", "infra"],
    "operational readiness & reliability": ["logging", "monitoring", "alert", "metrics"],
    "compliance & governance": ["license", "compliance", "audit", "gdpr", "policy"],
    "performance, scalability & resilience": ["performance", "cache", "async", "retry"],
    "apis, integrations & messaging": ["api", "integration", "swagger", "queue", "message"],
    "user experience & accessibility": ["frontend", "ui", "css", "html", "component"],
    "ai adoption": ["ai", "copilot", "chatgpt", "llm", "automation"],
    "scope, planning & governance": ["roadmap", "milestone", "plan", "scope"],
    "delivery health": ["release", "sprint", "milestone", "changelog"],
    "requirements & customer alignment": ["requirements", "user story", "acceptance"],
    "risks, issues & escalations": ["risk", "issue", "mitigation", "escalation"],
    "quality & testing": ["test", "defect", "coverage", "qa"],
    "compliance & security": ["security", "gdpr", "compliance", "audit"],
    "continuous improvement & knowledge management": ["retrospective", "lessons", "wiki", "docs"],
}


def _extract_keywords(area: str, question: str) -> list[str]:
    area_lower = area.lower()
    keywords = []
    for key, words in _AREA_KEYWORD_MAP.items():
        if key in area_lower:
            keywords.extend(words)
            break
    # Pull nouns from question (simple heuristic: 4+ char words not common stop words)
    stop = {"with", "that", "this", "from", "have", "been", "will", "should",
            "where", "used", "what", "your", "their", "each", "they", "into",
            "more", "some", "such", "about", "when", "also", "whether"}
    words = re.findall(r'\b[A-Za-z]{4,}\b', question)
    keywords.extend([w for w in words if w.lower() not in stop][:8])
    return list(dict.fromkeys(keywords))  # deduplicate, preserve order


# ── Main Router ───────────────────────────────────────────────────────────────

class StrategyRouter:
    """Routes a ChecklistItem to the best StrategyConfig.

    Accepts an optional dict of DB-defined rules keyed by checklist_item_id.
    DB rules are checked first, before any hard-coded logic.
    """

    def __init__(self, db_rules: dict[int, "StrategyConfig"] | None = None):
        # db_rules: {checklist_item_id: StrategyConfig}
        self._db_rules = db_rules or {}

    def route(self, item) -> StrategyConfig:
        # 0. DB rule — highest priority (admin/PM override)
        if item.id in self._db_rules:
            db_rule = self._db_rules[item.id]
            if db_rule.strategy == "ai_and_human":
                # Run normal auto-routing but flag result for human sign-off
                config = self._auto_route(item)
                config.needs_human_sign_off = True
                return config
            return db_rule

        return self._auto_route(item)

    def _auto_route(self, item) -> StrategyConfig:
        """Hard-coded routing logic — no DB rules applied."""
        area = (item.area or "").strip()
        question = (item.question or "").strip()

        # 1. Hard-coded human-required check
        human = _is_human_required(area, question)
        if human:
            return human

        combined = f"{area} {question}"

        # 2. Pattern scan
        for compiled_patterns, config in _PATTERN_RULES_COMPILED:
            if any(p.search(combined) for p in compiled_patterns):
                return config

        # 3. File presence
        for compiled_patterns, config in _FILE_RULES_COMPILED:
            if any(p.search(combined) for p in compiled_patterns):
                return config

        # 4. Metadata check
        for compiled_patterns, config in _META_RULES_COMPILED:
            if any(p.search(combined) for p in compiled_patterns):
                return config

        # 5. Default → LLM analysis
        keywords = _extract_keywords(area, question)
        return StrategyConfig(
            strategy="llm_analysis",
            context_keywords=keywords,
            focus_prompt=question,
        )


def build_strategy_config_from_db(rule) -> StrategyConfig:
    """Convert a ChecklistRoutingRule DB row to a StrategyConfig."""
    return StrategyConfig(
        strategy=rule.strategy,
        skip_reason=rule.skip_reason or "Marked as human-required by reviewer",
        evidence_hint=rule.evidence_hint or "",
    )
