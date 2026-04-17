"""
Action Plan Generator Service

Generates structured action plans from autonomous review results.
Creates prioritized action cards with implementation-ready AI prompts.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


_CLIENT_OWNED_MARKERS = (
    "maintained by clients",
    "maintained by client",
    "client controlled",
    "client-owned",
    "client owned",
    "na, maintained by clients",
    "not applicable",
)

_DOCUMENTATION_HINTS = (
    "document",
    "documentation",
    "diagram",
    "runbook",
    "checklist",
    "onboarding",
    "backup",
    "restore",
    "retention",
    "policy",
    "plan",
)

_PIPELINE_HINTS = (
    "pipeline",
    "ci/cd",
    "cicd",
    "workflow",
    "scan",
    "dependabot",
    "sast",
    "dast",
    "coverage",
    "linter",
    "iac",
)

_GOVERNANCE_HINTS = (
    "who is responsible",
    "who owns",
    "who is accountable",
    "raci",
    "named architect",
    "named owner",
    "accountability chain",
    "org chart",
)

_BOOLEAN_EXPECTATIONS = {"yes", "no", "true", "false", "y", "n"}

_VALID_MODES = {"governance", "documentation", "pipeline", "client_owned", "implementation"}

_LLM_MODE_SYSTEM_PROMPT = """\
You are classifying checklist review findings to determine the correct remediation category.

CATEGORIES (choose exactly one per item):
- governance: Requires identifying real people, teams, owners, or accountability structures \
(e.g. "who is responsible", RACI, named architect, org chart, accountability chain)
- documentation: Requires creating or updating documents, diagrams, runbooks, policies, or plans
- pipeline: Requires CI/CD workflow, build automation, scanning, linting, or deployment configuration
- client_owned: The control is owned externally by the client or a platform team, not this repository
- implementation: Requires writing or changing code, configuration, tests, or infrastructure in the repo

Return a JSON array only — no prose, no markdown fences.
Example: [{"id": 1, "mode": "governance"}, {"id": 2, "mode": "pipeline"}]
"""


@dataclass
class AIPrompt:
    """AI-ready prompt in multiple formats."""

    generic: str
    cursor: str
    claude_code: str


@dataclass
class ActionCard:
    """Actionable remediation card for a single review gap."""

    item_code: str
    area: str
    question: str
    priority: str
    rag_status: str
    what_was_found: str
    what_to_fix: str
    expected_outcome: str
    assigned_to: str = "TBD"
    due_date: str = "TBD"
    ai_prompt: Optional[AIPrompt] = None


@dataclass
class ActionPlanResponse:
    """Complete action plan for a review job."""

    job_id: int
    project: str
    checklist: str
    generated_at: str
    summary: dict
    critical_blockers: List[ActionCard]
    advisories: List[ActionCard]
    sign_off_required: List[ActionCard]
    compliant_summary: List[dict]


class ActionPlanGenerator:
    """
    Generates action plans from autonomous review results.

    The generator intentionally produces richer prompts than the raw checklist
    question so developers can act without having to reinterpret the review.
    """

    async def _classify_modes_with_llm(
        self,
        pairs: List[Tuple[Any, Any]],  # [(result, item), ...]
    ) -> Dict[int, str]:
        """
        Batch-classify resolution modes for all non-compliant items using LLM.

        Sends one prompt containing all items and parses a JSON array back.
        Returns {sequential_index → mode_string}.  Falls back to {} on any
        failure so keyword matching in _resolution_mode() takes over per item.
        """
        if not pairs:
            return {}

        items_text = "\n".join(
            f"{i + 1}. Area: {item.area or 'Unknown'}\n"
            f"   Question: {item.question or ''}\n"
            f"   Expected: {(item.expected_evidence or '')[:120]}"
            for i, (_result, item) in enumerate(pairs[:60])
        )
        user_prompt = (
            f"{items_text}\n\n"
            "Return JSON array: "
            '[{"id": 1, "mode": "..."}, {"id": 2, "mode": "..."}, ...]'
        )

        try:
            from app.services.autonomous_review.connectors.llm import (  # noqa: PLC0415
                get_llm_client,
                pick_model,
            )

            client = await get_llm_client()
            model = await pick_model()
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": _LLM_MODE_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=500,
            )
            raw = (response.choices[0].message.content or "").strip()
            # Strip accidental markdown fences
            if raw.startswith("```"):
                raw = raw.split("```")[1].lstrip("json").strip()
            classifications = json.loads(raw)
            return {
                int(c["id"]): c["mode"]
                for c in classifications
                if "id" in c and c.get("mode") in _VALID_MODES
            }
        except Exception as exc:
            logger.warning("LLM mode classification failed (%s) — falling back to keyword matching", exc)
            return {}

    async def generate(
        self,
        job: Any,
        results: list,
        checklist_items: Dict[int, Any],
        project: Any,
        checklist_name: str,
        enhanced_prompts: Optional[Dict[str, Dict[str, str]]] = None,
    ) -> ActionPlanResponse:
        critical_blockers: List[ActionCard] = []
        advisories: List[ActionCard] = []
        sign_off_required: List[ActionCard] = []
        compliant_summary: List[dict] = []
        enhanced_prompts = enhanced_prompts or {}

        # Collect all non-compliant items for a single batched LLM classification
        actionable_pairs: List[Tuple[Any, Any]] = []
        for result in results:
            item = checklist_items.get(result.checklist_item_id)
            if item and (result.rag_status in ("red", "amber") or result.needs_human_sign_off):
                actionable_pairs.append((result, item))

        # One LLM call for all items; {1-based index → mode}
        llm_modes = await self._classify_modes_with_llm(actionable_pairs)
        # Build a lookup keyed by checklist_item_id for fast access inside the loop
        pair_index = {result.checklist_item_id: idx + 1 for idx, (result, _) in enumerate(actionable_pairs)}

        for result in results:
            item = checklist_items.get(result.checklist_item_id)
            if not item:
                continue

            llm_mode = llm_modes.get(pair_index.get(result.checklist_item_id, -1))
            card = self._build_action_card(result, item, project, enhanced_prompts, llm_mode=llm_mode)

            if result.needs_human_sign_off:
                sign_off_required.append(card)
            elif result.rag_status == "red":
                critical_blockers.append(card)
            elif result.rag_status == "amber":
                advisories.append(card)

            if result.rag_status == "green":
                compliant_summary.append(
                    {
                        "item_code": item.item_code or "",
                        "area": item.area or "",
                        "question": item.question or "",
                    }
                )

        summary = {
            "total": len(results),
            "critical_blockers": len(critical_blockers),
            "advisories": len(advisories),
            "sign_off_required": len(sign_off_required),
            "compliant": len(compliant_summary),
        }

        return ActionPlanResponse(
            job_id=job.id,
            project=project.name or "",
            checklist=checklist_name,
            generated_at=datetime.utcnow().isoformat() + "Z",
            summary=summary,
            critical_blockers=critical_blockers,
            advisories=advisories,
            sign_off_required=sign_off_required,
            compliant_summary=compliant_summary,
        )

    def _build_action_card(
        self,
        result: Any,
        item: Any,
        project: Any,
        enhanced_prompts: Dict[str, Dict[str, str]],
        llm_mode: Optional[str] = None,
    ) -> ActionCard:
        priority = "High" if result.rag_status == "red" else "Medium"
        what_to_fix = self._derive_fix_statement(item)
        expected_outcome = self._effective_expected_outcome(item)
        ai_prompt = self._build_prompt(result, item, project, llm_mode=llm_mode)

        stored_prompt = enhanced_prompts.get(str(result.id))
        if stored_prompt:
            ai_prompt = AIPrompt(
                generic=stored_prompt.get("generic", ai_prompt.generic),
                cursor=stored_prompt.get("cursor", ai_prompt.cursor),
                claude_code=stored_prompt.get("claude_code", ai_prompt.claude_code),
            )

        return ActionCard(
            item_code=item.item_code or "",
            area=item.area or "",
            question=item.question or "",
            priority=priority,
            rag_status=result.rag_status or "",
            what_was_found=result.evidence or "",
            what_to_fix=what_to_fix,
            expected_outcome=expected_outcome,
            ai_prompt=ai_prompt,
        )

    def _derive_fix_statement(self, item: Any) -> str:
        expected = self._effective_expected_outcome(item)
        question = (item.question or "").strip()
        lower_expected = expected.lower()

        if expected:
            if any(marker in lower_expected for marker in _CLIENT_OWNED_MARKERS):
                return (
                    "Document the ownership boundary, required external evidence, "
                    "and repository-side integration assumptions for this client-controlled requirement."
                )
            return f"Implement or document the missing evidence so the repository clearly satisfies: {expected}"

        if any(hint in question.lower() for hint in _DOCUMENTATION_HINTS):
            return f"Create or update the supporting documentation needed to satisfy: {question}"

        return f"Address the gap and leave the codebase, configuration, or docs in a state that satisfies: {question}"

    def _build_prompt(self, result: Any, item: Any, project: Any, llm_mode: Optional[str] = None) -> AIPrompt:
        mode = self._resolution_mode(item, result, llm_mode=llm_mode)
        expected_outcome = self._effective_expected_outcome(item)
        tech_stack = self._format_tech_stack(project)
        files_checked = self._format_files(result.files_checked)
        artifact_hints = self._artifact_hints(item, result)
        validation_steps = self._validation_steps(item, result, mode)
        ownership_guidance = self._ownership_guidance(mode, result)
        task_list = self._task_list(mode, item, result)

        prompt_body = "\n\n".join(
            [
                "ROLE:\nYou are a senior engineer working inside this repository. Produce a concrete fix, not a generic suggestion.",
                (
                    "CHECKLIST GAP:\n"
                    f"Item: {item.item_code or 'Unknown'}\n"
                    f"Area: {item.area or 'Unknown'}\n"
                    f"Question: {item.question or 'Unknown'}\n"
                    f"Priority: {'High' if result.rag_status == 'red' else 'Medium'}\n"
                    f"Current review status: {result.rag_status or 'unknown'}\n"
                    f"Human sign-off required: {'Yes' if getattr(result, 'needs_human_sign_off', False) else 'No'}"
                ),
                (
                    "REPOSITORY CONTEXT:\n"
                    f"Project: {project.name or 'Unknown'}\n"
                    f"Tech Stack: {tech_stack}\n"
                    "Files already inspected:\n"
                    f"{files_checked}"
                ),
                (
                    "CURRENT FINDING:\n"
                    f"{(result.evidence or 'No specific evidence provided').strip()}"
                ),
                (
                    "TARGET STANDARD:\n"
                    f"{expected_outcome or (item.question or 'Not specified').strip()}"
                ),
                (
                    "LIKELY ARTIFACTS TO TOUCH:\n"
                    f"{artifact_hints}"
                ),
                (
                    "OWNERSHIP AND DECISION GUIDANCE:\n"
                    f"{ownership_guidance}"
                ),
                (
                    "WORK TO PERFORM:\n"
                    f"{task_list}"
                ),
                (
                    "VALIDATION:\n"
                    f"{validation_steps}"
                ),
                (
                    "EXPECTED DELIVERABLE:\n"
                    "- Update the relevant code, configuration, pipeline, or documentation.\n"
                    "- Keep changes aligned with existing project conventions.\n"
                    "- Summarize the root cause and the files changed.\n"
                    "- Add or update tests/checks when the requirement is repository-owned.\n"
                    "- If something is truly external, document the dependency clearly instead of inventing fake controls."
                ),
                (
                    "ACCEPTANCE CRITERIA:\n"
                    f"{expected_outcome or (item.question or 'Not specified').strip()}"
                ),
            ]
        )

        cursor = (
            "@workspace\n"
            + prompt_body
            + "\n\nSearch the workspace for the most relevant implementation points before making changes."
        )
        claude_code = (
            "Task:\n"
            + prompt_body
            + "\n\nAfter making changes, run the relevant tests or verification commands and summarize the outcome."
        )

        return AIPrompt(generic=prompt_body, cursor=cursor, claude_code=claude_code)

    def _resolution_mode(self, item: Any, result: Any, llm_mode: Optional[str] = None) -> str:
        # LLM classification takes priority when available and valid
        if llm_mode in _VALID_MODES:
            return llm_mode

        # Keyword fallback — used when LLM call failed or was skipped
        expected = self._effective_expected_outcome(item).lower()
        question = (item.question or "").lower()

        if any(marker in expected for marker in _CLIENT_OWNED_MARKERS):
            return "client_owned"
        if any(hint in question or hint in expected for hint in _GOVERNANCE_HINTS):
            return "governance"
        if any(hint in question for hint in _DOCUMENTATION_HINTS):
            return "documentation"
        if any(hint in question or hint in expected for hint in _PIPELINE_HINTS):
            return "pipeline"
        if getattr(result, "needs_human_sign_off", False):
            return "sign_off"
        return "implementation"

    def _format_tech_stack(self, project: Any) -> str:
        tech_stack = getattr(project, "tech_stack", None)
        if isinstance(tech_stack, list) and tech_stack:
            return ", ".join(str(item) for item in tech_stack)
        return "Not specified"

    def _format_files(self, files_checked: Any) -> str:
        if isinstance(files_checked, list) and files_checked:
            return "\n".join(f"- {path}" for path in files_checked[:12])
        return "- No specific files were captured by the review result"

    def _artifact_hints(self, item: Any, result: Any) -> str:
        hints: List[str] = []
        question = (item.question or "").lower()
        evidence = (result.evidence or "").lower()
        files_checked = result.files_checked if isinstance(result.files_checked, list) else []

        for path in files_checked[:8]:
            hints.append(f"- Inspect or update {path}")

        if any(token in question for token in _DOCUMENTATION_HINTS):
            hints.append("- Add or revise the relevant documentation under docs/ or the closest existing documentation location")
        if any(token in question for token in _PIPELINE_HINTS) or any(token in evidence for token in _PIPELINE_HINTS):
            hints.append("- Review CI/CD workflow files, dependency manifests, and container build definitions")
        if "security" in question or "security" in evidence:
            hints.append("- Review auth, middleware, configuration, and deployment edges that enforce security controls")
        if "database" in question or "data" in question:
            hints.append("- Review schema docs, migration scripts, data-access code, and operational runbooks")
        if not hints:
            hints.append("- Start from the modules referenced in the finding and the files already inspected by the review")

        return "\n".join(dict.fromkeys(hints))

    def _ownership_guidance(self, mode: str, result: Any) -> str:
        if mode == "client_owned":
            return (
                "This requirement is marked as client-controlled or externally owned. "
                "Do not fabricate infrastructure controls in this repository. "
                "Instead, document the dependency, expected evidence from the client, and any repository-side safeguards or assumptions."
            )
        if mode == "governance":
            return (
                "This requirement identifies real people, teams, or accountability structures. "
                "Create the documentation skeleton where useful, but do not fabricate names, roles, or org structures. "
                "Leave explicit gaps for project stakeholders to fill in."
            )
        if mode == "sign_off":
            return (
                "Implement repository changes where possible, then leave a concise sign-off package "
                "so a human reviewer can verify the non-code or high-risk parts."
            )
        if getattr(result, "needs_human_sign_off", False):
            return "A reviewer must still confirm the result after the repository changes are prepared."
        return "Assume this is repository-owned unless the codebase clearly shows the control is handled elsewhere."

    def _task_list(self, mode: str, item: Any, result: Any) -> str:
        base_tasks = [
            "1. Re-check the repository and confirm whether the finding still holds in the current codebase.",
        ]

        if mode == "governance":
            base_tasks.extend(
                [
                    "2. This question identifies real people, roles, or accountability — you cannot invent names or org structures.",
                    "3. Create the documentation skeleton (e.g., docs/ARCHITECTURE_OWNERS.md or a RACI template) if nothing exists.",
                    "4. Leave owner/name fields as [TO BE CONFIRMED BY PROJECT LEAD] — never populate with placeholder data.",
                    "5. Add a clear TODO comment so the right stakeholder knows what to fill in.",
                ]
            )
        elif mode == "client_owned":
            base_tasks.extend(
                [
                    "2. Add or update repository documentation that explains who owns this control and what evidence is expected from the client or platform team.",
                    "3. Record any repository-side integration points, assumptions, handoffs, or prerequisites that must remain true.",
                    "4. If there is a small repository safeguard that supports this control, add it; otherwise leave clear documentation instead of fake implementation.",
                ]
            )
        elif mode == "documentation":
            base_tasks.extend(
                [
                    "2. Identify the most relevant existing documentation location and extend it instead of creating disconnected placeholder files.",
                    "3. Write project-specific documentation that reflects the actual modules, flows, environments, and responsibilities in this repository.",
                    "4. Cross-link related documents or code paths so future reviewers can trace the evidence quickly.",
                ]
            )
        elif mode == "pipeline":
            base_tasks.extend(
                [
                    "2. Review existing build, test, and deployment workflows before adding new automation.",
                    "3. Implement the missing pipeline, scan, threshold, or policy in the repo's current CI/CD style.",
                    "4. Make gating behaviour explicit so the requirement is objectively verifiable in future reviews.",
                ]
            )
        else:
            base_tasks.extend(
                [
                    "2. Implement the missing code, configuration, documentation, or tests needed to satisfy the checklist requirement.",
                    "3. Follow the project's existing patterns and update adjacent artifacts when the control spans multiple layers.",
                    "4. Remove ambiguity: future reviewers should be able to find direct evidence in the repository.",
                ]
            )

        if getattr(result, "needs_human_sign_off", False):
            base_tasks.append(
                "5. Leave a short sign-off note or evidence checklist describing what a human reviewer still needs to confirm."
            )

        return "\n".join(base_tasks)

    def _validation_steps(self, item: Any, result: Any, mode: str = "") -> str:
        expected_outcome = self._effective_expected_outcome(item)
        steps = [
            "- Ensure the repository contains explicit evidence for the checklist requirement, not just intent.",
            f"- Verify the final state satisfies: {expected_outcome or (item.question or 'Not specified').strip()}",
        ]

        if mode == "governance":
            steps.append(
                "- Confirm that owner/responsible fields contain real names or are explicitly marked as requiring stakeholder input — not placeholder text."
            )

        question = (item.question or "").lower()
        if any(token in question for token in _DOCUMENTATION_HINTS):
            steps.append("- Confirm the updated documentation references real modules, environments, owners, and operational steps.")
        if any(token in question for token in _PIPELINE_HINTS):
            steps.append("- Confirm the workflow or scan is version-controlled and fails or warns in the intended conditions.")
        if "test" in question or "coverage" in question:
            steps.append("- Run or describe the relevant automated verification and capture the threshold or expected output.")
        if getattr(result, "needs_human_sign_off", False):
            steps.append("- Capture the remaining human review checkpoint explicitly.")

        return "\n".join(steps)

    def _effective_expected_outcome(self, item: Any) -> str:
        expected = (item.expected_evidence or "").strip()
        if expected and expected.lower() not in _BOOLEAN_EXPECTATIONS:
            return expected
        return (item.question or "").strip()
