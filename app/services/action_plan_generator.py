"""
Action Plan Generator Service

Generates structured action plans from autonomous review results.
Creates prioritized action cards with AI prompts for fixing identified gaps.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class AIPrompt:
    """AI-ready prompt in multiple formats."""
    generic: str       # plain instruction usable in any AI IDE
    cursor: str        # prefixed with @workspace for Cursor / GitHub Copilot Chat
    claude_code: str   # task-description style for Claude Code CLI


@dataclass
class ActionCard:
    """Actionable remediation card for a single review gap."""
    item_code: str
    area: str
    question: str
    priority: str           # "High" (red) | "Medium" (amber)
    rag_status: str
    what_was_found: str     # from AutonomousReviewResult.evidence
    what_to_fix: str        # derived sentence from expected_evidence gap
    expected_outcome: str   # ChecklistItem.expected_evidence (or empty string)
    assigned_to: str = "TBD"
    due_date: str = "TBD"
    ai_prompt: Optional[AIPrompt] = None


@dataclass
class ActionPlanResponse:
    """Complete action plan for a review job."""
    job_id: int
    project: str
    checklist: str
    generated_at: str       # ISO datetime
    summary: dict           # total, critical_blockers, advisories, sign_off_required, compliant
    critical_blockers: List[ActionCard]   # red items
    advisories: List[ActionCard]          # amber items
    sign_off_required: List[ActionCard]   # needs_human_sign_off=True (any rag_status)
    compliant_summary: List[dict]         # [{item_code, area, question}] for green items


class ActionPlanGenerator:
    """
    Generates action plans from autonomous review results.
    
    Usage:
        generator = ActionPlanGenerator()
        plan = generator.generate(job, results, checklist_items, project, checklist_name)
    """
    
    def generate(
        self,
        job,  # AutonomousReviewJob
        results: list,  # list of AutonomousReviewResult
        checklist_items: Dict[int, any],  # {checklist_item_id: ChecklistItem}
        project,  # Project
        checklist_name: str
    ) -> ActionPlanResponse:
        """
        Generate a complete action plan from review results.
        
        Args:
            job: The AutonomousReviewJob instance
            results: List of AutonomousReviewResult instances
            checklist_items: Dict mapping checklist_item_id to ChecklistItem
            project: The Project instance
            checklist_name: Name of the checklist used
            
        Returns:
            ActionPlanResponse with categorized action cards
        """
        critical_blockers: List[ActionCard] = []
        advisories: List[ActionCard] = []
        sign_off_required: List[ActionCard] = []
        compliant_summary: List[dict] = []
        
        # Process each result
        for result in results:
            item = checklist_items.get(result.checklist_item_id)
            if not item:
                continue
            
            # Build action card
            card = self._build_action_card(result, item, project)
            
            # Categorize by RAG status
            if result.rag_status == "red":
                critical_blockers.append(card)
            elif result.rag_status == "amber":
                advisories.append(card)
            
            # Track human sign-off items (any status)
            if result.needs_human_sign_off:
                sign_off_required.append(card)
            
            # Track compliant items
            if result.rag_status == "green":
                compliant_summary.append({
                    "item_code": item.item_code or "",
                    "area": item.area or "",
                    "question": item.question or ""
                })
        
        # Build summary
        summary = {
            "total": len(results),
            "critical_blockers": len(critical_blockers),
            "advisories": len(advisories),
            "sign_off_required": len(sign_off_required),
            "compliant": len(compliant_summary)
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
            compliant_summary=compliant_summary
        )
    
    def _build_action_card(
        self,
        result,  # AutonomousReviewResult
        item,    # ChecklistItem
        project  # Project
    ) -> ActionCard:
        """Build a single action card from a review result."""
        # Determine priority
        priority = "High" if result.rag_status == "red" else "Medium"
        
        # Derive what_to_fix
        if item.expected_evidence:
            what_to_fix = f"Implement: {item.expected_evidence}"
        else:
            what_to_fix = f"Address the following: {item.question}"
        
        # Build AI prompt
        ai_prompt = self._build_prompt(result, item, project)
        
        return ActionCard(
            item_code=item.item_code or "",
            area=item.area or "",
            question=item.question or "",
            priority=priority,
            rag_status=result.rag_status or "",
            what_was_found=result.evidence or "",
            what_to_fix=what_to_fix,
            expected_outcome=item.expected_evidence or "",
            ai_prompt=ai_prompt
        )
    
    def _build_prompt(
        self,
        result,  # AutonomousReviewResult
        item,    # ChecklistItem
        project  # Project
    ) -> AIPrompt:
        """
        Construct three prompt flavours from review context.
        
        Returns:
            AIPrompt with generic, cursor, and claude_code variants
        """
        # Build CONTEXT block
        tech_stack_str = ""
        if project.tech_stack and isinstance(project.tech_stack, list):
            tech_stack_str = ", ".join(str(t) for t in project.tech_stack)
        
        files_checked_str = ""
        if result.files_checked and isinstance(result.files_checked, list):
            files_checked_str = "\n".join(f"  - {f}" for f in result.files_checked[:20])
        
        context_block = f"""CONTEXT:
Project: {project.name or 'Unknown'}
Tech Stack: {tech_stack_str or 'Not specified'}
Files Checked:
{files_checked_str or '  None specified'}"""
        
        # Build FINDING block
        finding_block = f"""FINDING:
{result.evidence or 'No specific evidence provided'}"""
        
        # Build STANDARD EXPECTED block
        expected_block = f"""STANDARD EXPECTED:
{item.expected_evidence or 'Not specified'}"""
        
        # Build TASK block
        task_block = f"""TASK:
Fix the above gap. Ensure the solution satisfies: '{item.question}'"""
        
        # Build ACCEPTANCE CRITERIA
        acceptance = item.expected_evidence or item.question or ""
        acceptance_block = f"""ACCEPTANCE CRITERIA:
{acceptance}"""
        
        # Generic flavour: plain text, no special prefix
        generic = "\n\n".join([
            context_block,
            finding_block,
            expected_block,
            task_block,
            acceptance_block
        ])
        
        # Cursor flavour: prefix with @workspace and add search instruction
        cursor = f"@workspace {generic}\n\nSearch the workspace for related files before making changes."
        
        # Claude Code flavour: wrap in Task: prefix and add test instruction
        claude_code = f"""Task:
{generic}

Run tests after making changes."""
        
        return AIPrompt(
            generic=generic,
            cursor=cursor,
            claude_code=claude_code
        )
