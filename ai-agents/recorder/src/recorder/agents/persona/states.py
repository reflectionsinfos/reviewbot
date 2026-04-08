"""PersonaAgentState TypedDict for LangGraph persona agents."""

from typing import TypedDict


class PersonaAgentState(TypedDict):
    persona_id: str
    session_id: str
    project_id: str
    role_title: str
    role_description: str
    accountability_areas: list[str]
    irrelevant_topics: list[str]

    # Always-present context (no retrieval)
    profile_card: str              # project.profile_card
    preloaded_context: str         # session.preloaded_context
    rolling_summary: str           # agent.rolling_summary

    # Current query context
    query: str
    retrieved_transcript: list[str]
    retrieved_project_brain: list[str]
    retrieved_code: list[str]
    retrieved_domain: list[str]

    # Response
    answer: str
    citations: list[str]
    confidence: str                # high | medium | low
    domain_alignment: str          # in-domain | partial | out-of-domain
