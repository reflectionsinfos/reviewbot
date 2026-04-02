"""
Agent Scan Connector
Builds a FileIndex-compatible object from the metadata uploaded by the
reviewbot-cli CLI — no actual files on the server required.

File-presence and metadata-check strategies work fully.
Pattern-scan and LLM strategies are degraded: they check only the files
whose content the agent has explicitly uploaded via POST /file-content.
"""
import json
import re
import fnmatch
from dataclasses import dataclass, field
from typing import Optional, List

from app.services.autonomous_review.connectors.local_folder import (
    FileInfo, SearchMatch, TEXT_EXTENSIONS,
)


class AgentFileIndex:
    """
    Wraps agent-uploaded scan metadata to satisfy the FileIndex interface
    expected by all analyzers.

    Files whose content has been uploaded (via the file-content endpoint)
    are fully analysable; others support path-based checks only.
    """

    def __init__(self, metadata: dict, file_content_store: dict):
        """
        Args:
            metadata: Parsed scan_result dict from the agent upload payload.
            file_content_store: Dict keyed by rel_path → file content str.
                                Populated as the agent uploads individual files.
        """
        self.base_path = "__agent__"
        self._meta = metadata
        self._content_store = file_content_store  # rel_path → content

        # Build FileInfo list from metadata
        self.files: list[FileInfo] = []
        for f in metadata.get("files", []):
            ext = "." + f["path"].rsplit(".", 1)[-1].lower() if "." in f["path"] else ""
            is_text = ext in TEXT_EXTENSIONS
            self.files.append(FileInfo(
                rel_path=f["path"],
                abs_path=f["path"],  # not a real path
                extension=ext,
                size_bytes=f.get("size_bytes", 0),
                is_text=is_text,
            ))

    # ── FileIndex public API ──────────────────────────────────────────────────

    def find_files(self, patterns: list[str]) -> list[str]:
        """Return relative paths matching any of the given glob patterns."""
        matched = []
        for fi in self.files:
            for pat in patterns:
                pat_lower = pat.lower()
                rel_lower = fi.rel_path.lower()
                if fnmatch.fnmatch(rel_lower, pat_lower):
                    matched.append(fi.rel_path)
                    break
                fname = rel_lower.split("/")[-1]
                if fnmatch.fnmatch(fname, pat_lower):
                    matched.append(fi.rel_path)
                    break
        return matched

    def directory_exists(self, dir_pattern: str) -> bool:
        """True if any directory segment in any path matches the pattern."""
        pat = dir_pattern.lower().rstrip("/")
        for fi in self.files:
            parts = fi.rel_path.lower().split("/")
            for part in parts[:-1]:
                if fnmatch.fnmatch(part, pat):
                    return True
        return False

    def get_content(self, rel_path: str) -> Optional[str]:
        """Return uploaded file content, or None if not yet uploaded."""
        return self._content_store.get(rel_path)

    def search_content(self, pattern: str, extensions: Optional[list[str]] = None,
                       max_matches: int = 20) -> list[SearchMatch]:
        """
        Regex search across uploaded file contents only.
        Files not yet uploaded are silently skipped.
        """
        compiled = re.compile(pattern, re.IGNORECASE)
        matches: list[SearchMatch] = []

        for fi in self.files:
            if len(matches) >= max_matches:
                break
            if not fi.is_text:
                continue
            if extensions and fi.extension not in extensions:
                continue
            content = self._content_store.get(fi.rel_path)
            if not content:
                continue
            lines = content.splitlines()
            for lineno, line in enumerate(lines, 1):
                if compiled.search(line):
                    start = max(0, lineno - 3)
                    end = min(len(lines), lineno + 2)
                    ctx = "\n".join(lines[start:end])
                    matches.append(SearchMatch(
                        file_path=fi.rel_path,
                        line_number=lineno,
                        line_content=line.strip(),
                        context=ctx,
                    ))
                    if len(matches) >= max_matches:
                        break
        return matches

    def get_relevant_files(self, keywords: list[str], max_files: int = 3) -> list[str]:
        """
        Score uploaded files by keyword relevance; fall back to path-only
        scoring for files whose content isn't available yet.
        """
        keyword_lower = [k.lower() for k in keywords]
        scores: dict[str, float] = {}

        for fi in self.files:
            if not fi.is_text:
                continue
            score = 0.0
            path_lower = fi.rel_path.lower()

            for kw in keyword_lower:
                if kw in path_lower:
                    score += 3.0

            content = self._content_store.get(fi.rel_path)
            if content:
                peek = content[:3000].lower()
                for kw in keyword_lower:
                    score += peek.count(kw) * 0.5

            if score > 0:
                scores[fi.rel_path] = score

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [path for path, _ in ranked[:max_files]]

    def summary(self) -> dict:
        """Return a summary compatible with the LocalFolderConnector output."""
        ext_counts: dict[str, int] = {}
        for fi in self.files:
            ext_counts[fi.extension] = ext_counts.get(fi.extension, 0) + 1

        return {
            "base_path": "__agent__",
            "total_files": len(self.files),
            "text_files": sum(1 for f in self.files if f.is_text),
            "extensions": dict(sorted(ext_counts.items(), key=lambda x: x[1], reverse=True)[:20]),
            "has_git": any(
                fi.rel_path.startswith(".git") or "/.git/" in fi.rel_path
                for fi in self.files
            ),
            "agent_mode": True,
            "uploaded_content_files": len(self._content_store) if hasattr(self._content_store, "__len__") else 0,
        }
