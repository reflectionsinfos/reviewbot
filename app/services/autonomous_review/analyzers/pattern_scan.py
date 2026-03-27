"""
Pattern Scan Analyzer
Performs regex searches across source files. Objective, no LLM needed.
"""
from .base import AnalysisResult
from ..connectors.local_folder import FileIndex
from ..strategy_router import StrategyConfig


class PatternScanAnalyzer:
    """Scans source files for regex patterns and derives RAG from match count."""

    async def analyze(self, item, file_index: FileIndex,
                      config: StrategyConfig) -> AnalysisResult:
        all_matches = []
        checked_files: set[str] = set()

        for pattern in config.scan_patterns:
            matches = file_index.search_content(
                pattern,
                extensions=config.scan_extensions,
                max_matches=15,
            )
            all_matches.extend(matches)
            for m in matches:
                checked_files.add(m.file_path)

        total = len(all_matches)

        if config.invert_match:
            # GREEN = pattern not found (e.g. no hardcoded secrets)
            if total == 0:
                rag = "green"
                evidence = "No problematic patterns detected across scanned files."
            elif total <= 3:
                rag = "amber"
                evidence = (
                    f"⚠️  {total} potential issue(s) found — review manually:\n"
                    + _format_matches(all_matches[:5])
                )
            else:
                rag = "red"
                evidence = (
                    f"❌  {total} pattern matches found — immediate attention needed:\n"
                    + _format_matches(all_matches[:8])
                )
        else:
            # GREEN = pattern found (e.g. test functions exist, retry logic present)
            if total == 0:
                rag = "red"
                evidence = "Pattern not found — feature appears to be missing."
            elif total <= 5:
                rag = "amber"
                evidence = (
                    f"⚠️  Only {total} occurrence(s) found — may be insufficient:\n"
                    + _format_matches(all_matches[:5])
                )
            else:
                rag = "green"
                evidence = (
                    f"✅  {total} occurrence(s) found across {len(checked_files)} file(s):\n"
                    + _format_matches(all_matches[:5])
                )

        return AnalysisResult(
            rag_status=rag,
            evidence=evidence,
            confidence=0.9,
            files_checked=list(checked_files)[:20],
        )


def _format_matches(matches) -> str:
    lines = []
    for m in matches:
        lines.append(f"  {m.file_path}:{m.line_number} → {m.line_content[:120]}")
    return "\n".join(lines)
