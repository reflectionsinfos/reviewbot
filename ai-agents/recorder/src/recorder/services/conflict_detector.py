"""Inter-agent conflict detection.

Compares agent responses on the same topic after each synthesis call.
Conflicts are recorded and surfaced — NEVER silently resolved.

ConflictRecord fields:
  - conflict_id, session_id, timestamp_in_meeting
  - topic, agents_involved, agent_positions (agent_id → position)
  - conflict_type: contradiction | unacknowledged_dependency | risk_gap
  - resolution_status: unresolved | resolved | deferred
"""

# Implementation: Phase 4
# Skeleton only.


def detect_conflicts(agent_responses: dict[str, str], topic: str) -> list[dict]:
    """Compare agent responses on the same topic and return ConflictRecord dicts.

    agent_responses: {persona_id: response_text}
    Phase 4 implementation.
    """
    raise NotImplementedError("Conflict detection — Phase 4")
