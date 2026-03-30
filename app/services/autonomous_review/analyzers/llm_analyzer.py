"""
LLM Analyzer
Uses the configured LLM to read the most relevant project files and
assess a checklist item qualitatively, returning a RAG + evidence.
"""
from __future__ import annotations

import json
import logging
from typing import Any, List

from .base import AnalysisResult
from ..connectors.llm import get_llm_client, pick_model
from ..connectors.local_folder import FileIndex
from app.agents.strategy_router_agent import StrategyConfig

logger = logging.getLogger(__name__)

MAX_CHARS_PER_FILE = 4000
MAX_FILES_PER_ITEM = 6
FALLBACK_FILES = [
    "README.md",
    "requirements.txt",
    "pyproject.toml",
    "package.json",
    "docker-compose.yml",
    "Dockerfile",
]

SYSTEM_PROMPT = """\
You are a senior technical reviewer performing an autonomous repository review.
You must evaluate a checklist requirement using only the repository context provided.

Return ONLY valid JSON in this exact shape:
{
  "rag": "green" | "amber" | "red" | "na",
  "evidence": "2-4 sentences explaining what exists, what is missing, and citing specific files when possible",
  "root_cause": "One concise sentence",
  "recommended_actions": ["action 1", "action 2", "action 3"],
  "validation_steps": ["validation 1", "validation 2"],
  "confidence": 0.0
}

Rules:
- Prefer repository-specific reasoning over generic best practices.
- If the repository lacks enough evidence, say that clearly and explain what evidence is missing.
- If a requirement appears externally owned, say so and recommend documenting the boundary in-repo.
- Recommended actions must be implementation-ready and specific enough to drive remediation prompts.
"""


class LLMAnalyzer:
    """Reads project files and asks the LLM to assess the checklist item."""

    def __init__(self) -> None:
        self._client = None

    async def _get_client(self):
        if self._client is None:
            self._client = await get_llm_client()
        return self._client

    async def analyze(
        self,
        item: Any,
        file_index: FileIndex,
        config: StrategyConfig,
    ) -> AnalysisResult:
        keywords = config.context_keywords or []
        question = item.question or ""
        area = item.area or ""

        relevant_files = self._select_relevant_files(file_index, keywords)
        if not relevant_files:
            return AnalysisResult(
                rag_status="na",
                evidence="No readable repository files were selected for this checklist item.",
                confidence=0.0,
                files_checked=[],
            )

        file_sections: List[str] = []
        for rel_path in relevant_files:
            content = file_index.get_content(rel_path)
            if content:
                snippet = content[:MAX_CHARS_PER_FILE]
                file_sections.append(f"--- {rel_path} ---\n{snippet}\n")

        if not file_sections:
            return AnalysisResult(
                rag_status="na",
                evidence="Selected files could not be read.",
                confidence=0.0,
                files_checked=relevant_files,
            )

        user_prompt = (
            f"Checklist area: {area}\n"
            f"Checklist question: {question}\n"
            f"Expected evidence: {item.expected_evidence or 'Not specified'}\n"
            f"Routing focus: {config.focus_prompt or question}\n\n"
            "Repository files:\n\n"
            + "\n".join(file_sections)
        )

        try:
            client = await self._get_client()
            response = await client.chat.completions.create(
                model=await pick_model(),
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=700,
                response_format={"type": "json_object"},
            )

            raw = response.choices[0].message.content or "{}"
            
            # Increment usage
            from ..connectors.llm import increment_llm_usage
            await increment_llm_usage(tokens=response.usage.total_tokens)
            
            data = json.loads(raw)

            rag = data.get("rag", "na")
            if rag not in {"green", "amber", "red", "na"}:
                rag = "na"

            evidence = self._compose_evidence(data)
            confidence = float(data.get("confidence", 0.7))
            confidence = max(0.0, min(1.0, confidence))

            return AnalysisResult(
                rag_status=rag,
                evidence=evidence,
                confidence=confidence,
                files_checked=relevant_files,
            )

        except json.JSONDecodeError as exc:
            logger.warning("LLM returned non-JSON for item %s: %s", item.item_code, exc)
            return AnalysisResult(
                rag_status="na",
                evidence="LLM response could not be parsed.",
                confidence=0.0,
                files_checked=relevant_files,
            )
        except Exception as exc:
            logger.error("LLM analysis failed for item %s: %s", item.item_code, exc)
            return AnalysisResult(
                rag_status="na",
                evidence=f"LLM analysis error: {exc}",
                confidence=0.0,
                files_checked=relevant_files,
            )

    def _select_relevant_files(self, file_index: FileIndex, keywords: list[str]) -> list[str]:
        ranked = file_index.get_relevant_files(keywords, max_files=MAX_FILES_PER_ITEM)
        selected: list[str] = list(ranked)

        if len(selected) < 3:
            for fallback in file_index.find_files(FALLBACK_FILES):
                if fallback not in selected:
                    selected.append(fallback)
                if len(selected) >= MAX_FILES_PER_ITEM:
                    break

        if not selected:
            selected = [fi.rel_path for fi in file_index.files if fi.is_text][:MAX_FILES_PER_ITEM]

        return selected[:MAX_FILES_PER_ITEM]

    def _compose_evidence(self, data: dict) -> str:
        parts: list[str] = []
        evidence = (data.get("evidence") or "").strip()
        root_cause = (data.get("root_cause") or "").strip()
        actions = [str(action).strip() for action in data.get("recommended_actions", []) if str(action).strip()]
        validations = [str(step).strip() for step in data.get("validation_steps", []) if str(step).strip()]

        if evidence:
            parts.append(evidence)
        if root_cause:
            parts.append(f"Root cause: {root_cause}")
        if actions:
            parts.append("Recommended actions:\n" + "\n".join(f"- {action}" for action in actions[:4]))
        if validations:
            parts.append("Validation:\n" + "\n".join(f"- {step}" for step in validations[:3]))

        return "\n\n".join(parts) if parts else "LLM returned no evidence."
