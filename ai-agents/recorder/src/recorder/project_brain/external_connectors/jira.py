"""Jira connector (PB-5).

Fetches: open issues, current sprint, epics, recent comments.
Processing: LLM summarises each issue → embed in project_brain_{id}.
Refresh: before each session (delta sync — only changed issues).
"""

# Implementation: Phase 6
# Skeleton only.


async def sync_jira(project_id: str, jira_project_key: str) -> int:
    """Sync Jira issues into project_brain_{project_id}.
    Returns number of issues indexed.
    Phase 6 implementation.
    """
    raise NotImplementedError("Jira connector — Phase 6")
