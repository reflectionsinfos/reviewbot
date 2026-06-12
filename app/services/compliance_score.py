"""
Weighted compliance score calculation for manual and offline reviews.
"""
from typing import Dict, List, Tuple

RAG_SCORES = {"green": 100, "amber": 50, "red": 0}


def calculate_compliance_score(
    rag_entries: List[Tuple[str, float]],
) -> Tuple[float, str, Dict[str, int]]:
    """
    Calculate weighted compliance score, overall RAG status, and rag_counts.

    Each entry in rag_entries is a (rag_status, weight) tuple.
    Items with rag_status 'na' are excluded from scoring (score remains None).
    """
    rag_counts: Dict[str, int] = {"green": 0, "amber": 0, "red": 0, "na": 0}
    total_weight = 0.0
    weighted_score = 0.0

    for rag, weight in rag_entries:
        rag = rag.lower()
        rag_counts[rag] = rag_counts.get(rag, 0) + 1

        score = RAG_SCORES.get(rag)
        if score is not None:
            weighted_score += score * weight
            total_weight += weight

    compliance_score = (weighted_score / total_weight) if total_weight else 0.0

    overall_rag = (
        "green" if compliance_score >= 75
        else "amber" if compliance_score >= 50
        else "red"
    ) if rag_counts["green"] or rag_counts["amber"] or rag_counts["red"] else "na"

    return compliance_score, overall_rag, rag_counts
