"""
Local Folder Connector
Walks a local directory tree and builds a searchable file index.
"""
import os
import re
import fnmatch
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional

# Directories to always skip
SKIP_DIRS = {
    ".git", "__pycache__", "node_modules", "venv", ".venv", "env",
    "dist", "build", ".next", ".nuxt", "coverage", "htmlcov",
    ".pytest_cache", ".mypy_cache", ".tox", "eggs", ".eggs",
    "*.egg-info", "target", "out", "bin", "obj", ".idea", ".vscode",
    "chroma_db", "uploads", "reports",
}

# File extensions considered source/text (readable)
TEXT_EXTENSIONS = {
    ".py", ".js", ".ts", ".jsx", ".tsx", ".java", ".cs", ".go", ".rb",
    ".php", ".cpp", ".c", ".h", ".rs", ".scala", ".kt", ".swift",
    ".md", ".txt", ".rst", ".yaml", ".yml", ".json", ".toml", ".ini",
    ".cfg", ".conf", ".env", ".sh", ".bash", ".ps1", ".sql",
    ".html", ".css", ".scss", ".less", ".xml", ".gradle", ".tf",
    ".hcl", ".dockerfile", ".Dockerfile", ".makefile", ".Makefile",
    ".properties", ".gitignore", ".eslintrc", ".prettierrc",
}

MAX_FILE_SIZE_BYTES = 80_000   # 80KB cap for reading
MAX_FILES_SCAN = 2000          # Stop indexing if folder is huge


@dataclass
class FileInfo:
    rel_path: str          # relative to base_path, always forward slashes
    abs_path: str
    extension: str
    size_bytes: int
    is_text: bool


@dataclass
class SearchMatch:
    file_path: str
    line_number: int
    line_content: str
    context: str           # surrounding lines


class FileIndex:
    """Lazily-loaded, searchable index of a project folder."""

    def __init__(self, base_path: str):
        self.base_path = Path(base_path).resolve()
        self.files: list[FileInfo] = []
        self._content_cache: dict[str, str] = {}

    # ── Public API ────────────────────────────────────────────────────────────

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
                # Also match just the filename part
                fname = rel_lower.split("/")[-1]
                if fnmatch.fnmatch(fname, pat_lower):
                    matched.append(fi.rel_path)
                    break
        return matched

    def directory_exists(self, dir_pattern: str) -> bool:
        """True if any directory in the tree matches the pattern."""
        pat = dir_pattern.lower().rstrip("/")
        for fi in self.files:
            parts = fi.rel_path.lower().split("/")
            for part in parts[:-1]:  # directories only
                if fnmatch.fnmatch(part, pat):
                    return True
        return False

    def get_content(self, rel_path: str) -> Optional[str]:
        """Read file content (cached). Returns None if not readable."""
        if rel_path in self._content_cache:
            return self._content_cache[rel_path]

        abs_path = self.base_path / rel_path
        try:
            if not abs_path.exists() or not abs_path.is_file():
                return None
            stat = abs_path.stat()
            if stat.st_size > MAX_FILE_SIZE_BYTES:
                # Return truncated head
                with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read(MAX_FILE_SIZE_BYTES)
                content += "\n... [truncated]"
            else:
                with open(abs_path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read()
            self._content_cache[rel_path] = content
            return content
        except Exception:
            return None

    def search_content(self, pattern: str, extensions: Optional[list[str]] = None,
                       max_matches: int = 20) -> list[SearchMatch]:
        """Regex search across all text files. Returns up to max_matches hits."""
        compiled = re.compile(pattern, re.IGNORECASE)
        matches: list[SearchMatch] = []

        candidates = [
            fi for fi in self.files
            if fi.is_text and (extensions is None or fi.extension in extensions)
        ]

        for fi in candidates:
            if len(matches) >= max_matches:
                break
            content = self.get_content(fi.rel_path)
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
        Score all text files by keyword relevance (path + content peek),
        return top max_files by score.
        """
        keyword_lower = [k.lower() for k in keywords]
        scores: dict[str, float] = {}

        for fi in self.files:
            if not fi.is_text:
                continue
            score = 0.0
            path_lower = fi.rel_path.lower()

            # Path matching (high weight)
            for kw in keyword_lower:
                if kw in path_lower:
                    score += 3.0

            # Content peek (first 3KB only to keep it fast)
            content_peek = self.get_content(fi.rel_path)
            if content_peek:
                peek = content_peek[:3000].lower()
                for kw in keyword_lower:
                    score += peek.count(kw) * 0.5

            if score > 0:
                scores[fi.rel_path] = score

        ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return [path for path, _ in ranked[:max_files]]

    def summary(self) -> dict:
        """Return a summary of the scanned project."""
        ext_counts: dict[str, int] = {}
        for fi in self.files:
            ext_counts[fi.extension] = ext_counts.get(fi.extension, 0) + 1

        return {
            "base_path": str(self.base_path),
            "total_files": len(self.files),
            "text_files": sum(1 for f in self.files if f.is_text),
            "extensions": dict(sorted(ext_counts.items(), key=lambda x: x[1], reverse=True)[:20]),
            "has_git": any(fi.rel_path.startswith(".git") for fi in self.files)
                       or (self.base_path / ".git").exists(),
        }


class LocalFolderConnector:
    """Scans a local filesystem folder and returns a FileIndex."""

    def __init__(self, path: str):
        self.path = path

    def scan(self) -> FileIndex:
        base = Path(self.path).resolve()
        if not base.exists():
            raise FileNotFoundError(f"Source path does not exist: {base}")
        if not base.is_dir():
            raise NotADirectoryError(f"Source path is not a directory: {base}")

        index = FileIndex(str(base))
        count = 0

        for root, dirs, files in os.walk(base):
            # Prune skip dirs in-place so os.walk won't descend into them
            dirs[:] = [
                d for d in dirs
                if d not in SKIP_DIRS
                and not any(fnmatch.fnmatch(d, pat) for pat in SKIP_DIRS)
            ]

            for filename in files:
                if count >= MAX_FILES_SCAN:
                    break
                abs_path = Path(root) / filename
                try:
                    size = abs_path.stat().st_size
                except OSError:
                    continue

                ext = abs_path.suffix.lower()
                rel_path = abs_path.relative_to(base).as_posix()

                is_text = ext in TEXT_EXTENSIONS or filename in {
                    "Dockerfile", "Makefile", "Procfile", "Pipfile",
                    ".env", ".env.example", ".env.docker", "Jenkinsfile",
                }

                index.files.append(FileInfo(
                    rel_path=rel_path,
                    abs_path=str(abs_path),
                    extension=ext,
                    size_bytes=size,
                    is_text=is_text,
                ))
                count += 1

        return index
