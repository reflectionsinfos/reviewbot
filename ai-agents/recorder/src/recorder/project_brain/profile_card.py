"""Project Profile Card (PB-6).

A short structured text block (< 500 tokens) injected verbatim into every
agent's system prompt for every session. Never retrieved — always present.
This eliminates cold-start latency for core project facts.
"""

PROFILE_CARD_TEMPLATE = """\
## Project: {name}
**Goal:** {description}
**Stack:** {tech_stack}
**Team:** {team_description}
**Current focus:** {current_focus}
**Key open risks:**
{risks}
**Architecture style:** {architecture_style}
**Key decisions in effect:**
{key_decisions}
**Last updated:** {last_updated}
"""


def render_profile_card(project: dict) -> str:
    """Render the profile card from project metadata.

    The rendered card is injected verbatim into every agent system prompt.
    It must never exceed 500 tokens (~375 words).
    """
    risks = "\n".join(f"  - {r}" for r in project.get("key_risks", []))
    decisions = "\n".join(f"  - {d}" for d in project.get("key_decisions", []))
    return PROFILE_CARD_TEMPLATE.format(
        name=project.get("name", "Unnamed"),
        description=project.get("description", ""),
        tech_stack=project.get("tech_stack", "Not specified"),
        team_description=project.get("team_description", "Not specified"),
        current_focus=project.get("current_focus", "Not specified"),
        risks=risks or "  - None recorded",
        architecture_style=project.get("architecture_style", "Not specified"),
        key_decisions=decisions or "  - None recorded",
        last_updated=project.get("last_updated", "Unknown"),
    )
