"""Relevance scoring of transcript chunks against persona domains.

Uses sentence-transformers/all-MiniLM-L6-v2 — fast, runs on CPU.
Runs in parallel across all active agents for each chunk.
"""

from __future__ import annotations

import asyncio
from functools import lru_cache
from typing import NamedTuple

import structlog

from recorder.core.config import settings

logger = structlog.get_logger()

DEEP_THRESHOLD = 0.7
LIGHT_THRESHOLD = 0.4


class RelevanceScore(NamedTuple):
    chunk_id: str
    persona_id: str
    score: float
    routing_tier: str  # deep | light | skip


@lru_cache(maxsize=1)
def _get_model() -> "sentence_transformers.SentenceTransformer":  # type: ignore[name-defined]
    from sentence_transformers import SentenceTransformer  # type: ignore[import]
    logger.info("loading_relevance_model", model=settings.embedding_model)
    return SentenceTransformer(settings.embedding_model)


def _score_sync(chunk_text: str, domain_description: str) -> float:
    from sentence_transformers import util  # type: ignore[import]
    model = _get_model()
    emb_chunk = model.encode(chunk_text, convert_to_tensor=True)
    emb_domain = model.encode(domain_description, convert_to_tensor=True)
    score: float = float(util.cos_sim(emb_chunk, emb_domain).item())
    return score


async def score_chunk_for_personas(
    chunk_id: str,
    chunk_text: str,
    personas: list[dict],  # list of {persona_id, role_description, irrelevant_topics}
) -> list[RelevanceScore]:
    """Score one chunk against all active personas in parallel."""
    loop = asyncio.get_event_loop()

    async def _score_one(persona: dict) -> RelevanceScore:
        domain = persona.get("role_description", "")
        score = await loop.run_in_executor(None, _score_sync, chunk_text, domain)
        if score >= DEEP_THRESHOLD:
            tier = "deep"
        elif score >= LIGHT_THRESHOLD:
            tier = "light"
        else:
            tier = "skip"
        return RelevanceScore(chunk_id=chunk_id, persona_id=persona["persona_id"], score=score, routing_tier=tier)

    results = await asyncio.gather(*[_score_one(p) for p in personas])
    return list(results)
