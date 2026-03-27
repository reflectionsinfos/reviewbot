"""
LLM Analyzer
Uses the configured LLM to read the most relevant project files and
assess a checklist item qualitatively, returning a RAG + evidence.
"""
import json
import logging
from .base import AnalysisResult
from ..connectors.local_folder import FileIndex
from ..strategy_router import StrategyConfig

logger = logging.getLogger(__name__)

MAX_TOKENS_PER_FILE = 2500    # ~2000 chars per file sent to LLM
MAX_FILES_PER_ITEM = 3        # Top-N files selected per item

SYSTEM_PROMPT = """\
You are a senior technical reviewer performing an autonomous code review.
You will be given a checklist question and the relevant project files.
Assess whether the project satisfies the checklist requirement.

Respond ONLY with a valid JSON object in this exact format:
{
  "rag": "green" | "amber" | "red" | "na",
  "evidence": "<1-3 sentence explanation with specific file references>",
  "confidence": <float 0.0 to 1.0>
}

RAG definitions:
- green:  Fully satisfied, clear evidence found
- amber:  Partially satisfied or unclear — needs attention
- red:    Not satisfied or critical gaps found
- na:     Cannot assess from the provided files (insufficient context)
"""


class LLMAnalyzer:
    """Reads top-N project files and asks LLM to rate the checklist item."""

    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            from app.core.config import settings
            from openai import AsyncOpenAI
            self._client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        return self._client

    async def analyze(self, item, file_index: FileIndex,
                      config: StrategyConfig) -> AnalysisResult:
        keywords = config.context_keywords or []
        question = item.question or ""
        area = item.area or ""

        # Select most relevant files
        relevant_files = file_index.get_relevant_files(keywords, max_files=MAX_FILES_PER_ITEM)

        if not relevant_files:
            return AnalysisResult(
                rag_status="na",
                evidence="No relevant source files found in the project to assess this item.",
                confidence=0.0,
                files_checked=[],
            )

        # Build file context
        file_sections: list[str] = []
        for rel_path in relevant_files:
            content = file_index.get_content(rel_path)
            if content:
                snippet = content[:MAX_TOKENS_PER_FILE]
                file_sections.append(f"--- {rel_path} ---\n{snippet}\n")

        if not file_sections:
            return AnalysisResult(
                rag_status="na",
                evidence="Selected files could not be read.",
                confidence=0.0,
                files_checked=relevant_files,
            )

        user_prompt = (
            f"Area: {area}\n"
            f"Checklist Question: {question}\n\n"
            f"Project files:\n\n"
            + "\n".join(file_sections)
        )

        try:
            client = self._get_client()
            from app.core.config import settings

            model = _pick_model(settings)
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=300,
                response_format={"type": "json_object"},
            )

            raw = response.choices[0].message.content or "{}"
            data = json.loads(raw)

            rag = data.get("rag", "na")
            if rag not in ("green", "amber", "red", "na"):
                rag = "na"

            return AnalysisResult(
                rag_status=rag,
                evidence=data.get("evidence", "LLM returned no evidence."),
                confidence=float(data.get("confidence", 0.7)),
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


def _pick_model(settings) -> str:
    """Choose LLM model based on active provider."""
    provider = getattr(settings, "ACTIVE_LLM_PROVIDER", "openai").lower()
    if provider == "openai":
        return "gpt-4o-mini"   # cost-effective for bulk item analysis
    return "gpt-4o-mini"
