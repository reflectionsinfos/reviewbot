# Recorder Agent Notes

## Purpose

This package is the backend foundation for the Nexus AI meeting recorder. The intended product is a local, async Python system that:

- watches OBS mp4 segments
- transcribes them incrementally
- grounds answers in a per-project "Project Brain"
- supports multiple persona agents plus an orchestrator
- answers questions by chat now and voice later

## Current Reality

Treat this codebase as a strong scaffold, not a finished product.

Implemented today:

- FastAPI app wiring in `src/recorder/main.py`
- async SQLAlchemy setup and ORM models in `src/recorder/db/`
- project, session, persona, transcript, conflict, and understanding-doc schemas/routes
- session state transitions in `src/recorder/services/session_manager.py`
- Chroma client and basic retrieval helpers in `src/recorder/vector_store/`
- OBS segment watcher debounce logic in `src/recorder/pipeline/file_watcher.py`
- built-in persona template data in `src/recorder/agents/templates/`

Still mostly stubbed or phase-marked:

- document indexing
- code indexing
- incremental sync
- setup wizard orchestration
- LangGraph orchestrator/persona execution
- live query answering beyond placeholder responses
- STT/TTS implementation
- briefing generation, exports, health monitor, most connector logic

## Start Here

When picking up work in this package:

1. Read `README.md`, `CLAUDE.md`, and this file.
2. Trust the source code over the docs if they disagree.
3. Check the targeted subsystem file before assuming a feature exists.
4. Use the local guides in `.agent/skills/` for the relevant workstream.

## Working Commands

From `reviewbot/ai-agents/recorder`:

- `pip install -e ".[dev]"`
- `uvicorn recorder.main:app --reload --port 8100`
- `pytest`

Database notes:

- `src/recorder/db/session.py` creates tables on startup for development.
- The docs mention Alembic, but migrations are not present in this package yet.
- The live defaults use port `5436`, while some docs still mention `5432`.

## Architecture Map

- `src/recorder/main.py`: app startup, router registration, CORS, db init
- `src/recorder/core/`: settings, logging, exceptions
- `src/recorder/db/`: async engine and ORM models
- `src/recorder/schemas/`: request/response contracts
- `src/recorder/api/routes/`: CRUD-ish HTTP layer
- `src/recorder/api/websockets/`: live chat transport
- `src/recorder/project_brain/`: setup, indexing, sync, context injection
- `src/recorder/pipeline/`: file watcher, audio extraction, transcription, chunking, relevance
- `src/recorder/agents/`: persona/orchestrator state definitions and templates
- `src/recorder/services/`: session lifecycle, conflicts, briefings, exports
- `src/recorder/vector_store/`: Chroma namespaces and retrieval
- `src/recorder/voice/`: wake word, STT, TTS, audio routing

## Non-Negotiables

These design rules appear repeatedly across the docs and code. Preserve them unless the product direction changes explicitly.

- All runtime config must come from `settings`, never hardcoded values.
- Keep I/O async. Routes, db work, LLM calls, and file/network access should remain async-first.
- In async SQLAlchemy code, eager load relationships before access. Avoid lazy-loading surprises.
- The Project Profile Card is injected directly into prompts. It is not a retrieved vector-store document.
- Raw code must not be embedded into Chroma. Only generated summaries belong in the code index.
- Respect exclusion rules before indexing code or docs.
- TTS must target an explicit headset/output device, never a default speaker path.
- Agent disagreements are a feature. Surface conflicts; do not silently merge them away.
- Prefer phase-consistent work. Do not pretend Phase 3/4 features are implemented if the current route/service is still MVP-only.

## Known Drift To Remember

- `README.md` references `docs/implementation_plan.md`, but that file is missing.
- `README.md` shows `uvicorn src.recorder.main:app`; with the current `src` layout, `uvicorn recorder.main:app` is the safer target after editable install.
- `.env.example` contains Azure OpenAI variables, but `src/recorder/core/config.py` does not currently expose them.
- Several docs describe richer LangGraph flows than the present code actually implements.

## Good First Checks Before Editing

- If you touch routes, verify the matching schema and ORM model together.
- If you touch session logic, check allowed transitions in `services/session_manager.py`.
- If you touch retrieval or Project Brain code, re-check the "profile card injected / raw code not embedded" rules.
- If you touch audio, re-check output-device isolation and OBS bleed constraints.
- If you touch docs, prefer updating both `README.md` and `CLAUDE.md` when behavior changes.

## Validation Expectations

Use the smallest useful validation that matches the change:

- route/schema changes: import or smoke-test the endpoint flow
- model changes: ensure table shape and response models still align
- watcher/pipeline changes: exercise the debounce and queue path
- retrieval changes: verify namespace/filter behavior
- doc-only changes: re-read for consistency against current code

This package currently has little or no committed test coverage, so do not claim broad verification unless you actually add and run tests.
