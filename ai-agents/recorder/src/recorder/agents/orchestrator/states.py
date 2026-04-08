"""OrchestratorState TypedDict for the LangGraph orchestrator agent."""

from typing import TypedDict


class OrchestratorState(TypedDict):
    session_id: str
    project_id: str
    query: str
    query_domain: str | None         # classified domain
    target_persona_ids: list[str]    # routed to
    agent_responses: dict[str, str]  # persona_id → response
    conflicts: list[dict]            # ConflictRecord dicts detected
    synthesized_answer: str
    citations: list[str]
    health_alerts: list[dict]
