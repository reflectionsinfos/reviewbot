"""Role-filtered retrieval helpers for all vector store namespaces.

Implements the 7-step retrieval stack for persona agents:
  1. project.profile_card          (injected, not retrieved here)
  2. session.preloaded_context     (injected, not retrieved here)
  3. agent.rolling_summary         (injected, not retrieved here)
  4. session_transcript_{id}       ← retrieved here
  5. project_brain_{id}            ← retrieved here
  6. project_code_{id}             ← retrieved here (role-filtered)
  7. persona_domain_{id}           ← retrieved here
"""

from __future__ import annotations

from functools import lru_cache

import structlog

from recorder.core.config import settings
from recorder.vector_store.client import get_chroma_client
from recorder.vector_store import namespaces

logger = structlog.get_logger()

# Role-based code access level filters (from design F6)
ROLE_CODE_FILTERS: dict[str, dict] = {
    "Solutions Architect": {"level": {"$in": ["module", "class", "endpoint"]}},
    "Security Engineer": {"$and": [
        {"level": {"$in": ["module", "class", "endpoint", "schema"]}},
    ]},
    "Data Engineer": {"level": {"$in": ["schema", "module", "class"]}},
    "DevOps / SRE": {"level": {"$eq": "module"}},
    "Product Manager": {"level": {"$eq": "module"}},
    "Business Analyst": {"level": {"$eq": "module"}},
    "Default Expert": {},  # no filter — all levels
}


def _get_or_create_collection(name: str):  # type: ignore[return]
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


def retrieve_session_transcript(
    session_id: str,
    query: str,
    persona_id: str,
    n_results: int = 5,
    min_relevance: float = 0.4,
) -> list[str]:
    collection = _get_or_create_collection(namespaces.session_transcript(session_id))
    try:
        results = collection.query(
            query_texts=[query],
            n_results=n_results,
            where={f"relevance_score_{persona_id}": {"$gte": min_relevance}},
            include=["documents"],
        )
        return results["documents"][0] if results["documents"] else []
    except Exception:
        return []


def retrieve_project_brain(
    project_id: str,
    query: str,
    n_results: int = 5,
) -> list[str]:
    collection = _get_or_create_collection(namespaces.project_brain(project_id))
    try:
        results = collection.query(query_texts=[query], n_results=n_results, include=["documents"])
        return results["documents"][0] if results["documents"] else []
    except Exception:
        return []


def retrieve_project_code(
    project_id: str,
    query: str,
    role_title: str,
    n_results: int = 5,
) -> list[str]:
    collection = _get_or_create_collection(namespaces.project_code(project_id))
    where_filter = ROLE_CODE_FILTERS.get(role_title, {})
    try:
        kwargs: dict = {"query_texts": [query], "n_results": n_results, "include": ["documents"]}
        if where_filter:
            kwargs["where"] = where_filter
        results = collection.query(**kwargs)
        return results["documents"][0] if results["documents"] else []
    except Exception:
        return []


def retrieve_persona_domain(
    persona_id: str,
    query: str,
    n_results: int = 5,
) -> list[str]:
    collection = _get_or_create_collection(namespaces.persona_domain(persona_id))
    try:
        results = collection.query(query_texts=[query], n_results=n_results, include=["documents"])
        return results["documents"][0] if results["documents"] else []
    except Exception:
        return []
