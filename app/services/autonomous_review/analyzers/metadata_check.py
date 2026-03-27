"""
Metadata Check Analyzer
Reads structured config files (requirements.txt, package.json, etc.)
to make objective assertions without LLM.
"""
import re
import json
from .base import AnalysisResult
from ..connectors.local_folder import FileIndex
from ..strategy_router import StrategyConfig

# Known deprecated/EOL packages (extend as needed)
DEPRECATED_PYTHON = {
    "flask-script", "django-south", "pika<1", "boto", "python-dateutil<2",
    "beautifulsoup4<4.9", "requests<2.20", "sqlalchemy<1.4", "celery<5",
}
DEPRECATED_NPM = {
    "request", "node-uuid", "jade", "less-middleware", "grunt",
}


class MetadataCheckAnalyzer:

    async def analyze(self, item, file_index: FileIndex,
                      config: StrategyConfig) -> AnalysisResult:
        check = config.metadata_check

        if check == "dependencies_scanned":
            return self._check_dep_scanning(file_index, config)
        elif check == "deprecated":
            return self._check_deprecated(file_index, config)
        elif check == "coverage_thresholds":
            return self._check_coverage_thresholds(file_index, config)
        else:
            return AnalysisResult(
                rag_status="na",
                evidence=f"Unknown metadata check: {check}",
                confidence=0.0,
            )

    # ── Dependency scanning ───────────────────────────────────────────────────

    def _check_dep_scanning(self, file_index: FileIndex,
                            config: StrategyConfig) -> AnalysisResult:
        indicators = [
            ".github/dependabot.yml",
            ".github/dependabot.yaml",
            ".snyk",
            "snyk.yml",
            ".whitesource",
            "renovate.json",
            ".renovaterc",
        ]
        found = file_index.find_files(indicators)

        # Also check CI for safety / snyk / dependabot mentions
        ci_matches = file_index.search_content(
            r'(?i)(snyk|dependabot|trivy|safety|pip-audit|npm audit|yarn audit)',
            extensions=[".yml", ".yaml", ".sh"],
            max_matches=5,
        )

        checked = found + [m.file_path for m in ci_matches]

        if found:
            return AnalysisResult(
                rag_status="green",
                evidence=f"Dependency scanning configured: {', '.join(found)}",
                confidence=0.95,
                files_checked=checked,
            )
        if ci_matches:
            return AnalysisResult(
                rag_status="amber",
                evidence=(
                    f"Dependency scanning referenced in CI but no dedicated config file found.\n"
                    f"References: {ci_matches[0].file_path}:{ci_matches[0].line_number}"
                ),
                confidence=0.8,
                files_checked=checked,
            )
        return AnalysisResult(
            rag_status="red",
            evidence="No dependency scanning configured (no Dependabot, Snyk, Renovate, or audit commands found).",
            confidence=0.9,
            files_checked=[],
        )

    # ── Deprecated components ─────────────────────────────────────────────────

    def _check_deprecated(self, file_index: FileIndex,
                          config: StrategyConfig) -> AnalysisResult:
        found_deprecated: list[str] = []
        checked: list[str] = []

        # Python
        req_files = file_index.find_files(["requirements*.txt", "Pipfile"])
        for rf in req_files:
            content = file_index.get_content(rf)
            if content:
                checked.append(rf)
                for pkg in DEPRECATED_PYTHON:
                    if pkg.lower() in content.lower():
                        found_deprecated.append(f"{rf}: {pkg}")

        # Node
        pkg_files = file_index.find_files(["package.json"])
        for pf in pkg_files:
            content = file_index.get_content(pf)
            if content:
                checked.append(pf)
                try:
                    data = json.loads(content)
                    all_deps = {
                        **data.get("dependencies", {}),
                        **data.get("devDependencies", {}),
                    }
                    for dep in DEPRECATED_NPM:
                        if dep in all_deps:
                            found_deprecated.append(f"{pf}: {dep}")
                except json.JSONDecodeError:
                    pass

        if not checked:
            return AnalysisResult(
                rag_status="na",
                evidence="No dependency files found (requirements.txt, package.json).",
                confidence=0.5,
                files_checked=[],
            )
        if found_deprecated:
            return AnalysisResult(
                rag_status="amber",
                evidence=(
                    f"⚠️  Deprecated packages detected:\n"
                    + "\n".join(f"  • {d}" for d in found_deprecated)
                ),
                confidence=0.85,
                files_checked=checked,
            )
        return AnalysisResult(
            rag_status="green",
            evidence=f"No known deprecated packages detected in {', '.join(checked)}.",
            confidence=0.8,
            files_checked=checked,
        )

    # ── Coverage thresholds ───────────────────────────────────────────────────

    def _check_coverage_thresholds(self, file_index: FileIndex,
                                   config: StrategyConfig) -> AnalysisResult:
        threshold_patterns = [
            r'(?i)(fail_under|threshold|coverageThreshold)\s*[=:]\s*(\d+)',
            r'(?i)minimum_coverage\s*[=:]\s*(\d+)',
        ]
        found_thresholds: list[str] = []
        checked: list[str] = []

        candidates = file_index.find_files(config.metadata_files)
        for fp in candidates:
            content = file_index.get_content(fp)
            if not content:
                continue
            checked.append(fp)
            for pat in threshold_patterns:
                for match in re.finditer(pat, content):
                    found_thresholds.append(f"{fp}: {match.group(0).strip()}")

        if found_thresholds:
            return AnalysisResult(
                rag_status="green",
                evidence=(
                    "Coverage thresholds defined:\n"
                    + "\n".join(f"  • {t}" for t in found_thresholds[:5])
                ),
                confidence=0.95,
                files_checked=checked,
            )
        if checked:
            return AnalysisResult(
                rag_status="amber",
                evidence=f"Coverage config files found ({', '.join(checked)}) but no threshold values detected.",
                confidence=0.75,
                files_checked=checked,
            )
        return AnalysisResult(
            rag_status="red",
            evidence="No coverage threshold configuration found (.coveragerc, codecov.yml, jest.config.*, etc.).",
            confidence=0.9,
            files_checked=[],
        )
