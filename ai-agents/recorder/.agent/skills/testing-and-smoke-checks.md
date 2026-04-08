# Testing And Smoke Checks

## Use When

- finishing any code change
- deciding what "verified" means for this package
- adding the first real tests around a subsystem

## Current Reality

- `pyproject.toml` is set up for `pytest`, `pytest-asyncio`, `ruff`, and `mypy`
- committed tests do not appear to exist yet in this package
- many higher-level features are still scaffolds, so targeted smoke checks matter more than broad claims

## Default Approach

- validate the narrowest affected path first
- prefer one real end-to-end smoke check over several vague claims
- if a subsystem is still stubbed, say so clearly instead of faking completeness

## Useful Targets

- app startup and `/api/health`
- project/session/persona CRUD flows
- session state transitions
- Chroma client initialization and retrieval helper behavior
- file watcher debounce behavior

## Good Additions

- route tests with async clients
- service tests for transition and conflict logic
- unit tests around chunking, stale detection, and filters

## Common Mistakes

- claiming `pytest` passed without a test suite
- skipping validation because a change is "just docs" when docs encode wrong commands
- changing models/routes without a quick startup or import smoke test
