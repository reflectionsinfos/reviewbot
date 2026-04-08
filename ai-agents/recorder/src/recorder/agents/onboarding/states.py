"""OnboardingState TypedDict for the Role Onboarding Interview state machine."""

from typing import TypedDict


class OnboardingState(TypedDict):
    session_id: str
    current_state: str   # awaiting_role | awaiting_accountability | ...
    messages: list[dict] # conversation history

    # Captured fields
    role_title: str
    role_description: str
    accountability_areas: list[str]
    decision_domains: list[str]
    success_criteria: list[str]
    irrelevant_topics: list[str]
    prior_open_questions: list[str]
    is_complete: bool
