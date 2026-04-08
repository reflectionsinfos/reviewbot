"""Role-specific post-meeting briefing generator.

Generates personalised briefings per persona in parallel after the meeting ends.

Briefing sections (per design F8):
  - what_matters_to_you
  - your_action_items
  - decisions_in_your_domain
  - risks_in_your_area
  - open_questions_for_you
  - safe_to_ignore
  - cross_role_dependencies
  - expert_commentary
  - conflicts_involving_you
"""

# Implementation: Phase 5
# Skeleton only.


async def generate_briefing(persona_id: str, session_id: str) -> dict:
    """Generate role-specific briefing for a persona after the meeting.

    Returns PersonaBriefing JSON (matching design.md schema).
    Phase 5 implementation.
    """
    raise NotImplementedError("Briefing generator — Phase 5")


async def generate_all_briefings(session_id: str, persona_ids: list[str]) -> dict[str, dict]:
    """Generate briefings for all personas in parallel.
    Phase 5 implementation.
    """
    raise NotImplementedError("Parallel briefing generation — Phase 5")
