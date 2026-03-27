"""
File Presence Analyzer
Checks whether expected files or directories exist in the project.
"""
from .base import AnalysisResult
from ..connectors.local_folder import FileIndex
from ..strategy_router import StrategyConfig


class FilePresenceAnalyzer:
    """Checks for the presence of specific files/directories."""

    async def analyze(self, item, file_index: FileIndex,
                      config: StrategyConfig) -> AnalysisResult:
        found_files: list[str] = []
        found_dirs: list[str] = []
        checked: list[str] = []

        # Check file patterns
        for pattern in config.file_patterns:
            matches = file_index.find_files([pattern])
            checked.append(pattern)
            found_files.extend(matches)

        # Check directory patterns
        for dir_pat in config.dir_patterns:
            if file_index.directory_exists(dir_pat.rstrip("/")):
                found_dirs.append(dir_pat)
            checked.append(dir_pat)

        all_found = found_files + found_dirs

        if all_found:
            evidence = (
                f"Found {len(all_found)} matching artifact(s):\n"
                + "\n".join(f"  • {f}" for f in all_found[:10])
            )
            rag = "green"
        else:
            expected = (config.file_patterns + config.dir_patterns)[:5]
            evidence = (
                f"No matching files or directories found.\n"
                f"Expected (examples): {', '.join(expected)}"
            )
            rag = "red"

        return AnalysisResult(
            rag_status=rag,
            evidence=evidence,
            confidence=1.0,
            files_checked=all_found[:20],
        )
