"""Project Setup Wizard (PB-1).

Conversational LangGraph interview that collects project sources and triggers indexing.
Run once per project before the first meeting.

States:
  awaiting_project_info → awaiting_codebase → awaiting_docs
  → awaiting_exclusions → awaiting_integrations
  → trigger_indexing → review_profile_card → complete
"""

# Implementation: Phase 2
# Skeleton only — state machine and LangGraph graph to be implemented.

from recorder.agents.onboarding.states import OnboardingState


WIZARD_QUESTIONS = {
    "awaiting_project_info": "What is this project and what is it trying to achieve?",
    "awaiting_codebase": "Where is the codebase? Local folder path or git URL?",
    "awaiting_docs": "Where are the project documents? Local folder, Confluence, or SharePoint?",
    "awaiting_exclusions": (
        "Are there any directories or files to never index? "
        "(e.g. credentials, generated files)"
    ),
    "awaiting_integrations": "Do you use Jira, GitHub Issues, or Confluence for project tracking?",
}


STATE_TRANSITIONS = [
    "awaiting_project_info",
    "awaiting_codebase",
    "awaiting_docs",
    "awaiting_exclusions",
    "awaiting_integrations",
    "trigger_indexing",
    "review_profile_card",
    "complete",
]
