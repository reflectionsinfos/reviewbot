"""
Security Scan Analyzer

Runs local, zero-credential security scanning tools to detect known CVEs and
dependency vulnerabilities in a project's source tree.

Tool preference order (auto-detected from PATH):
  1. Trivy       — comprehensive: deps, secrets, misconfigs, containers
  2. OSV Scanner — Google's OSV database, supports most ecosystems
  3. pip-audit   — Python requirements.txt / Pipfile.lock
  4. npm audit   — Node.js package-lock.json / yarn.lock

All tools produce structured JSON output that is parsed into a normalised
vulnerability list and mapped to a RAG status.

RAG mapping:
  red   — at least one CRITICAL or HIGH severity CVE
  amber — MEDIUM or LOW severities only
  green — no known vulnerabilities found
  na    — no supported tool found in PATH
"""
from __future__ import annotations

import asyncio
import json
import logging
import shutil
from typing import Optional

from .base import AnalysisResult
from ..connectors.local_folder import FileIndex
from app.agents.strategy_router_agent.strategy_router_agent import StrategyConfig

logger = logging.getLogger(__name__)

_SCAN_TIMEOUT = 90   # seconds — first trivy run downloads DB, can be slow


# ── RAG helpers ───────────────────────────────────────────────────────────────

def _rag_from_counts(critical: int, high: int, medium: int, low: int) -> str:
    if critical > 0 or high > 0:
        return "red"
    if medium > 0 or low > 0:
        return "amber"
    return "green"


def _summarise(vulns: list[dict]) -> str:
    total = len(vulns)
    if total == 0:
        return "✅ No known vulnerabilities found in dependencies."

    counts: dict[str, int] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
    for v in vulns:
        sev = v.get("severity", "UNKNOWN").upper()
        counts[sev] = counts.get(sev, 0) + 1

    lines = [f"🔒 {total} vulnerabilit{'y' if total == 1 else 'ies'} found:"]
    emoji_map = {"CRITICAL": "🔴", "HIGH": "🔴", "MEDIUM": "🟡", "LOW": "⚪"}
    for sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW"):
        if counts[sev]:
            lines.append(f"  {emoji_map[sev]} {sev}: {counts[sev]}")

    lines.append("\nTop findings:")
    for v in vulns[:8]:
        cve   = v.get("id", "?")
        pkg   = v.get("package", "?")
        ver   = v.get("installed_version", "")
        fix   = v.get("fixed_version", "")
        sev   = v.get("severity", "?")
        title = v.get("title", "")
        line  = f"  • {cve} [{sev}]  {pkg} {ver}"
        if fix:
            line += f"  →  fix: {fix}"
        if title:
            line += f"  —  {title[:80]}"
        lines.append(line)

    if total > 8:
        lines.append(f"  … and {total - 8} more.")

    return "\n".join(lines)


def _build_result(vulns: list[dict], tool: str) -> AnalysisResult:
    counts: dict[str, int] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "UNKNOWN": 0}
    for v in vulns:
        sev = v.get("severity", "UNKNOWN").upper()
        counts[sev] = counts.get(sev, 0) + 1

    rag = _rag_from_counts(counts["CRITICAL"], counts["HIGH"], counts["MEDIUM"], counts["LOW"])
    evidence = f"[{tool}]\n{_summarise(vulns)}"

    targets = list(dict.fromkeys(v.get("target", "") for v in vulns if v.get("target")))[:10]

    return AnalysisResult(
        rag_status=rag,
        evidence=evidence,
        confidence=0.95,
        files_checked=targets,
    )


# ── Subprocess runner ─────────────────────────────────────────────────────────

async def _run_cmd(
    cmd: list[str],
    cwd: Optional[str] = None,
    timeout: int = _SCAN_TIMEOUT,
) -> tuple[str, int]:
    """Run a command and return (stdout, returncode). Never raises on non-zero exit."""
    proc = await asyncio.create_subprocess_exec(
        *cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=cwd,
    )
    try:
        stdout_bytes, _ = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        logger.warning("Security scan timed out after %ds: %s", timeout, " ".join(cmd))
        return "", -1

    return stdout_bytes.decode("utf-8", errors="replace"), proc.returncode or 0


# ── Output parsers ────────────────────────────────────────────────────────────

def _parse_trivy(raw: str) -> list[dict]:
    """Flatten Trivy fs JSON into a normalised vulnerability list."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []

    vulns: list[dict] = []
    for result in data.get("Results") or []:
        target = result.get("Target", "")
        for v in result.get("Vulnerabilities") or []:
            vulns.append({
                "id":                v.get("VulnerabilityID", "?"),
                "package":           v.get("PkgName", "?"),
                "installed_version": v.get("InstalledVersion", ""),
                "fixed_version":     v.get("FixedVersion", ""),
                "severity":          (v.get("Severity") or "UNKNOWN").upper(),
                "title":             v.get("Title", ""),
                "target":            target,
            })
    return vulns


def _parse_osv(raw: str) -> list[dict]:
    """Flatten OSV Scanner JSON into a normalised vulnerability list."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []

    vulns: list[dict] = []
    for result in data.get("results") or []:
        for pkg in result.get("packages") or []:
            pkg_info = pkg.get("package", {})
            for v in pkg.get("vulnerabilities") or []:
                aliases = v.get("aliases") or []
                cve_id  = next((a for a in aliases if a.startswith("CVE-")), v.get("id", "?"))
                db      = v.get("database_specific") or {}
                sev     = (db.get("severity") or "UNKNOWN").upper()
                vulns.append({
                    "id":                cve_id,
                    "package":           pkg_info.get("name", "?"),
                    "installed_version": pkg_info.get("version", ""),
                    "fixed_version":     "",
                    "severity":          sev if sev in ("CRITICAL", "HIGH", "MEDIUM", "LOW") else "UNKNOWN",
                    "title":             v.get("summary", ""),
                    "target":            pkg_info.get("ecosystem", ""),
                })
    return vulns


def _parse_pip_audit(raw: str) -> list[dict]:
    """Flatten pip-audit JSON into a normalised vulnerability list."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []

    vulns: list[dict] = []
    deps = data.get("dependencies") if isinstance(data, dict) else data
    if not isinstance(deps, list):
        return []

    for dep in deps:
        for v in dep.get("vulns") or []:
            aliases     = v.get("aliases") or []
            cve_id      = next((a for a in aliases if a.startswith("CVE-")), v.get("id", "?"))
            fix_vers    = v.get("fix_versions") or []
            vulns.append({
                "id":                cve_id,
                "package":           dep.get("name", "?"),
                "installed_version": dep.get("version", ""),
                "fixed_version":     fix_vers[0] if fix_vers else "",
                "severity":          "UNKNOWN",   # pip-audit doesn't report severity
                "title":             (v.get("description") or "")[:120],
                "target":            "pip",
            })
    return vulns


def _parse_npm_audit(raw: str) -> list[dict]:
    """Flatten npm audit v2 JSON into a normalised vulnerability list."""
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []

    sev_map = {"critical": "CRITICAL", "high": "HIGH", "moderate": "MEDIUM", "low": "LOW"}
    vulns: list[dict] = []
    for pkg_name, info in (data.get("vulnerabilities") or {}).items():
        sev = sev_map.get((info.get("severity") or "").lower(), "UNKNOWN")
        vulns.append({
            "id":                pkg_name,
            "package":           pkg_name,
            "installed_version": info.get("range", ""),
            "fixed_version":     "",
            "severity":          sev,
            "title":             f"{info.get('severity', '').title()} severity vulnerability",
            "target":            "npm",
        })
    return vulns


# ── Analyzer ──────────────────────────────────────────────────────────────────

class SecurityScanAnalyzer:
    """
    Auto-detects available security scanning tools and runs the best one found.
    Returns a single AnalysisResult covering all dependency vulnerabilities.
    """

    async def analyze(
        self,
        item,
        file_index: FileIndex,
        config: StrategyConfig,
        audit_context=None,
    ) -> AnalysisResult:
        source_path = str(file_index.base_path)

        result = await self._try_trivy(source_path)
        if result is not None:
            return result

        result = await self._try_osv_scanner(source_path)
        if result is not None:
            return result

        result = await self._try_pip_audit(source_path, file_index)
        if result is not None:
            return result

        result = await self._try_npm_audit(source_path, file_index)
        if result is not None:
            return result

        return AnalysisResult(
            rag_status="na",
            evidence=(
                "No security scanning tools found in PATH. Install one of:\n"
                "  • trivy        — https://aquasecurity.github.io/trivy/latest/getting-started/installation/\n"
                "  • osv-scanner  — https://google.github.io/osv-scanner/\n"
                "  • pip-audit    — pip install pip-audit\n"
                "  • npm audit    — built into npm ≥ 6"
            ),
            confidence=0.0,
            evidence_hint="Trivy is recommended: one binary covers all ecosystems including containers and IaC.",
        )

    # ── Tool runners ──────────────────────────────────────────────────────────

    async def _try_trivy(self, source_path: str) -> Optional[AnalysisResult]:
        if not shutil.which("trivy"):
            return None
        logger.info("SecurityScan: running trivy fs on %s", source_path)
        try:
            stdout, _ = await _run_cmd(
                ["trivy", "fs", "--format", "json", "--quiet", source_path],
            )
            if not stdout.strip():
                return None
            vulns = _parse_trivy(stdout)
            return _build_result(vulns, tool="trivy")
        except Exception as exc:
            logger.warning("trivy scan error: %s", exc)
            return None

    async def _try_osv_scanner(self, source_path: str) -> Optional[AnalysisResult]:
        if not shutil.which("osv-scanner"):
            return None
        logger.info("SecurityScan: running osv-scanner on %s", source_path)
        try:
            stdout, _ = await _run_cmd(
                ["osv-scanner", "--format", "json", source_path],
            )
            if not stdout.strip():
                return None
            vulns = _parse_osv(stdout)
            return _build_result(vulns, tool="osv-scanner")
        except Exception as exc:
            logger.warning("osv-scanner error: %s", exc)
            return None

    async def _try_pip_audit(self, source_path: str, file_index: FileIndex) -> Optional[AnalysisResult]:
        if not shutil.which("pip-audit"):
            return None

        req_files = [
            f.abs_path for f in file_index.files
            if (
                f.rel_path.lower().startswith("requirements")
                and f.rel_path.lower().endswith(".txt")
            )
        ]
        if not req_files:
            return None

        logger.info("SecurityScan: running pip-audit on %d requirements file(s)", len(req_files))
        all_vulns: list[dict] = []
        for req_file in req_files[:3]:
            try:
                stdout, _ = await _run_cmd(
                    ["pip-audit", "--format", "json", "-r", req_file],
                )
                if stdout.strip():
                    all_vulns.extend(_parse_pip_audit(stdout))
            except Exception as exc:
                logger.warning("pip-audit error for %s: %s", req_file, exc)

        return _build_result(all_vulns, tool="pip-audit")

    async def _try_npm_audit(self, source_path: str, file_index: FileIndex) -> Optional[AnalysisResult]:
        if not shutil.which("npm"):
            return None

        has_lockfile = any(
            f.rel_path in ("package-lock.json", "yarn.lock")
            for f in file_index.files
        )
        if not has_lockfile:
            return None

        logger.info("SecurityScan: running npm audit on %s", source_path)
        try:
            stdout, _ = await _run_cmd(
                ["npm", "audit", "--json"],
                cwd=source_path,
            )
            if not stdout.strip():
                return None
            vulns = _parse_npm_audit(stdout)
            return _build_result(vulns, tool="npm-audit")
        except Exception as exc:
            logger.warning("npm audit error: %s", exc)
            return None
