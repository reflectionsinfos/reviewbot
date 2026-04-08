"""Incremental Sync (PB-4).

Keeps the Project Brain current without full re-indexing.

Code sync (git-based):
  git diff HEAD~1 --name-only → re-summarise + re-embed changed files

Document sync (continuous):
  Watchdog monitors docs_folder → re-chunk + re-embed modified files

Pre-session freshness prompt:
  "Last indexed N days ago. X files changed. Re-index now?"

Stale file detection during meetings:
  If chunk.last_modified < actual file modification time → append stale warning
"""

# Implementation: Phase 2
# Skeleton only.


async def detect_changed_files(repo_path: str, since_commit: str) -> list[str]:
    """Return list of changed file paths since the given git commit.
    Phase 2 implementation.
    """
    raise NotImplementedError("Incremental sync — Phase 2")


def is_chunk_stale(chunk_last_modified: float, actual_file_mtime: float) -> bool:
    """Return True if the indexed chunk is older than the actual file."""
    return chunk_last_modified < actual_file_mtime


STALE_WARNING = (
    "[Note: this file was modified after my last index. "
    "My knowledge of it may be outdated.]"
)
