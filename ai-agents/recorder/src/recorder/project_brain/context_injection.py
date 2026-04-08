"""Meeting-Specific Context Injection (PB-7).

When a session is created, the agent asks what the meeting focuses on and
pre-retrieves relevant Project Brain content before the meeting starts.

Effect: the very first question gets a project-grounded answer with zero
retrieval cold-start latency.
"""

# Implementation: Phase 3
# Skeleton only.


async def preload_meeting_context(
    project_id: str,
    meeting_focus: str,
    components_mentioned: list[str],
    n_results: int = 10,
) -> str:
    """Pre-retrieve and combine top-K project brain results for this meeting topic.

    Returns a concatenated string to be stored as session.preloaded_context.
    Phase 3 implementation.
    """
    raise NotImplementedError("Meeting context injection — Phase 3")
