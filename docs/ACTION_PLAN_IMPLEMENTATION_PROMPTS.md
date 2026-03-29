# Action Plan and LLM-First Review — Implementation Prompts

This document replaces the older action-plan prompt set.

The previous design assumed:
- cheap non-LLM analyzers could answer a large share of checklist questions well
- action-plan prompts could be generated from `question + evidence + expected_evidence`
- “file present” or regex evidence would be strong enough input for remediation

The generated reports show that those assumptions do not hold for many technical checklist items.

## Why the old design was weak

The current prompt output is shallow because the input evidence is shallow:
- `file_presence` often produces only “No matching files or directories found”
- `pattern_scan` often produces isolated matches without explaining intent, scope, or remediation path
- `metadata_check` often answers a narrow proxy question, not the real checklist requirement
- the action-plan builder then converts that thin evidence into generic prompts like “Fix the above gap” or “Implement: Yes”

That is not enough context for an LLM IDE assistant to produce a reliable fix.

## Revised Product Direction

Use this model going forward:

1. Every checklist item is analyzed by LLM by default.
2. The reviewer can override an item to:
   - `human_required`
   - `ai_and_human`
3. Legacy strategies like `file_presence`, `pattern_scan`, and `metadata_check` remain available only as explicit/manual strategies, not as the default routing approach.
4. The LLM analyzer must return remediation-ready findings, not only RAG and a one-line evidence note.
5. The action plan must be generated from richer review output and must include ownership guidance, likely files/artifacts, validation steps, and better task framing.

## Expected End State

After these changes:
- the review result itself is richer and more faithful to the checklist intent
- the action plan becomes implementation-ready instead of template-like
- client-owned / externally-owned controls are handled as “document the boundary and evidence” instead of fake code implementation
- sign-off items are separated cleanly from direct remediation items

---

## Prompt 1 — Replace Auto Routing with LLM-First Default

```text
You are an expert Python backend engineer working in the ReviewBot codebase.

Goal:
Change the autonomous review routing model so that every checklist item is analyzed with `llm_analysis` by default.

New routing rules:
1. Reviewer override from DB has highest priority.
2. If reviewer sets `human_required`, skip AI analysis.
3. If reviewer sets `ai_and_human`, run LLM analysis and mark `needs_human_sign_off=True`.
4. Otherwise default to `llm_analysis` for every checklist item.
5. Do not auto-route to `file_presence`, `pattern_scan`, or `metadata_check` during normal review execution.

Implementation requirements:
- Update `app/services/autonomous_review/strategy_router.py`
- Preserve compatibility for existing strategy names so old/manual overrides still work
- Keep keyword extraction for building LLM context keywords
- Remove dependence on “strategy classification” as the primary control plane
- Make the code and comments clearly communicate that the product is now LLM-first by default

Acceptance criteria:
- A normal checklist item with no override routes to `llm_analysis`
- A DB rule for `human_required` still skips analysis
- A DB rule for `ai_and_human` still runs AI and requires sign-off
- No automatic fallback chooses `file_presence`, `pattern_scan`, or `metadata_check`
```

---

## Prompt 2 — Upgrade the LLM Analyzer to Return Remediation-Ready Findings

```text
You are an expert Python + LLM integration engineer working in ReviewBot.

Goal:
Upgrade the LLM analyzer so the review result is rich enough to generate actionable remediation prompts.

Files:
- `app/services/autonomous_review/analyzers/llm_analyzer.py`
- any shared LLM client helper you need under `app/services/autonomous_review/connectors/`

Current problem:
The analyzer mainly returns a short evidence sentence. The action plan then has too little context.

Required changes:
1. Improve file selection:
   - inspect more relevant files per item (not just 3)
   - add sensible fallback files like README, manifests, Docker/CI files when relevance is weak
2. Strengthen the system prompt so the model returns JSON with:
   - `rag`
   - `evidence`
   - `root_cause`
   - `recommended_actions`
   - `validation_steps`
   - `confidence`
3. Convert that structured output into a repository-specific evidence block stored in `AutonomousReviewResult.evidence`
4. The evidence text must mention:
   - what exists
   - what is missing
   - likely remediation direction
   - how to validate the fix
5. If the requirement appears externally owned, the analyzer should explicitly say so and recommend documenting the ownership boundary in the repo

Constraints:
- Keep the persisted schema unchanged unless absolutely necessary
- Reuse a shared provider-aware LLM client helper if one does not already exist
- Handle non-JSON responses and provider errors safely

Acceptance criteria:
- Review evidence is no longer a one-line pass/fail comment
- Evidence contains concrete remediation guidance
- The analyzer still returns `AnalysisResult`
- The implementation works with the active configured provider
```

---

## Prompt 3 — Rebuild ActionPlanGenerator Around Richer Prompts

```text
You are an expert Python / FastAPI developer working in ReviewBot.

Goal:
Rewrite the action-plan prompt generation so each action card is detailed enough for Cursor, Copilot, Claude Code, or ChatGPT to act on directly.

Files:
- `app/services/action_plan_generator.py`

Current problem:
The generated prompts are too generic because they mostly restate:
- project name
- question
- evidence
- expected evidence

Required prompt design:
Each generated prompt should include these sections:

1. ROLE
   - tell the model it is a senior engineer working in this repo

2. CHECKLIST GAP
   - item code
   - area
   - question
   - priority
   - review status
   - whether human sign-off is required

3. REPOSITORY CONTEXT
   - project
   - tech stack
   - files already inspected

4. CURRENT FINDING
   - full evidence from the review result

5. TARGET STANDARD
   - expected evidence, or fallback to the checklist question

6. LIKELY ARTIFACTS TO TOUCH
   - infer likely code/config/docs/pipeline locations from the finding and the checklist theme

7. OWNERSHIP AND DECISION GUIDANCE
   - if client-owned, instruct the model to document the boundary and required external evidence
   - if sign-off is required, instruct the model to prepare a human validation pack

8. WORK TO PERFORM
   - concrete numbered tasks

9. VALIDATION
   - explicit repo-facing validation steps

10. EXPECTED DELIVERABLE
   - files changed
   - tests/checks updated
   - assumptions documented

11. ACCEPTANCE CRITERIA
   - expected evidence or checklist question

Additional requirements:
- Do not put sign-off items in both `critical_blockers` and `sign_off_required`
- If enhanced prompts already exist in `job.agent_metadata["action_plan_prompts"]`, use them instead of rebuilding a weaker base prompt
- Improve `what_to_fix` so it does not emit useless phrases like `Implement: Yes`
- Recognize client-controlled expectations such as “Maintained by Clients” and convert them into documentation / ownership-boundary tasks instead of fake implementation tasks

Acceptance criteria:
- Base prompts are much richer even without the optional enhance endpoint
- Sign-off items are separated properly
- Client-owned items get sane guidance
- Enhanced prompts are surfaced when available
```

---

## Prompt 4 — Fix the Action Plan API Contract

```text
You are an expert FastAPI developer working in ReviewBot.

Goal:
Make the action-plan endpoints reflect the richer design and actually return enhanced prompts after enrichment.

Files:
- `app/api/routes/autonomous_reviews.py`

Required changes:
1. `GET /api/autonomous-reviews/{job_id}/action-plan`
   - load results in stable order
   - load any stored prompt overrides from `job.agent_metadata["action_plan_prompts"]`
   - pass stored prompts into the action-plan generator so the response reflects enhanced prompts

2. `POST /api/autonomous-reviews/{job_id}/action-plan/enhance`
   - return `already_enhanced` with count if prompts already exist
   - fail with HTTP 400 if no LLM provider is configured
   - build enhancement input from the upgraded base prompt
   - ask the LLM to rewrite that prompt into a more specific repository-aware remediation prompt
   - store final `generic`, `cursor`, and `claude_code` strings directly
   - keep processing sequential to avoid rate-limit problems
   - commit once at the end

Do not:
- store placeholder prompts like `Fix: <question>`
- store an “enhanced” JSON blob that the UI never uses

Acceptance criteria:
- After calling `/enhance`, a subsequent GET `/action-plan` returns the improved prompts
- Prompt enhancement is idempotent
- The endpoint gives a useful 400 when no provider is configured
```

---

## Prompt 5 — Update the History UI to Reflect the New Prompt Quality

```text
You are an expert frontend engineer working in `static/history.html`.

Goal:
Make the Action Plan tab clearly show that prompts are implementation-ready and can be enhanced.

Changes:
1. Keep the two-tab layout (Review Items / Action Plan)
2. In each action card:
   - show richer `what_to_fix`
   - continue supporting IDE flavour switching
   - use the enhanced prompt automatically when the backend returns it
3. Improve copy/export fidelity so Markdown export includes the richer prompt text
4. Show success feedback when enhanced prompts are already cached vs newly generated
5. Preserve the existing dark theme and avoid disruptive layout changes

Acceptance criteria:
- A user can switch to Action Plan and copy a prompt that already contains task framing, likely artifacts, and validation guidance
- Exported Markdown is substantially more useful than the old generic report
- Enhancing the plan changes what the user sees on refresh
```

---

## Prompt 6 — Add Regression Tests for the New Design

```text
You are an expert Python testing engineer working in ReviewBot.

Goal:
Add tests that lock the new LLM-first and richer action-plan behaviour.

Create or update tests covering:

1. Strategy router defaults to `llm_analysis`
2. Reviewer overrides still win over the default
3. Sign-off items do not also appear in critical blockers
4. Action-plan prompts contain rich sections like:
   - `ROLE`
   - `WORK TO PERFORM`
   - `VALIDATION`
   - `ACCEPTANCE CRITERIA`
5. Stored enhanced prompts override the base generated prompts in GET `/action-plan`
6. GET `/action-plan` still returns 404 for unknown jobs and 400 for incomplete jobs

Use:
- existing pytest + AsyncClient setup in `tests/conftest.py`
- direct model creation via `db_session`

Acceptance criteria:
- tests fail against the old design
- tests pass against the revised implementation
```

---

## Implementation Notes

This redesign intentionally changes the philosophy:
- old model: “pick the cheapest analyzer first, then generate prompts”
- new model: “generate higher-quality review understanding first, then generate remediation prompts from that understanding”

That is the right trade-off for checklist questions whose wording and intent are nuanced.

## Reviewer Workflow After This Change

Expected reviewer flow:
1. Run review
2. By default every item gets LLM analysis
3. If a reviewer disagrees with the automation strategy for a specific item:
   - switch it to `human_required`, or
   - switch it to `ai_and_human`
4. Re-run review
5. Use the richer Action Plan output to drive remediation

This is the intended control model going forward.
