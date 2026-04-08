# Persona Orchestration

## Use When

- implementing persona-agent logic
- implementing the orchestrator
- wiring query routing
- generating briefings or understanding docs

## Current Reality

- persona and orchestrator state shapes exist
- built-in persona templates exist
- live query routing is still placeholder-level in `sessions.py`
- most LangGraph execution code described in the docs is not implemented yet

## Design Intent

- each persona has its own role, relevance filter, and rolling summary
- orchestrator routes or synthesizes rather than acting as a hidden monolith
- Default Expert is always the fallback
- conflicts should be recorded and surfaced explicitly

## Main Files

- `src/recorder/agents/persona/states.py`
- `src/recorder/agents/orchestrator/states.py`
- `src/recorder/agents/templates/`
- `src/recorder/api/routes/sessions.py`
- `src/recorder/services/conflict_detector.py`
- `src/recorder/services/briefing_generator.py`
- `src/recorder/services/health_monitor.py`

## Build Order

1. Make direct single-agent query flow real.
2. Add orchestrator routing to one or more personas.
3. Add citations and conflict records.
4. Add post-meeting briefing and understanding-doc generation.

## Common Mistakes

- skipping the Default Expert fallback
- silently resolving disagreements instead of surfacing them
- mixing retrieval logic into route handlers
- assuming every persona should see the same code/document depth

## Minimum Validation

- test a direct query path end to end
- verify target persona selection behavior
- verify conflicts can be returned without breaking normal responses
