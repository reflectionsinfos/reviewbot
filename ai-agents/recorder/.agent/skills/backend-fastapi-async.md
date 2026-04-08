# Backend FastAPI Async

## Use When

- adding or changing HTTP routes
- updating Pydantic schemas
- changing ORM models
- working on session/project/persona CRUD

## Current Reality

- FastAPI route wiring is present.
- ORM models and schemas are real and usable.
- Most route handlers are thin and phase-light.
- Startup uses `init_db()` and creates tables directly in development.

## Rules

- Keep handlers async.
- Route contracts live in `src/recorder/schemas/`.
- DB state lives in `src/recorder/db/models.py`.
- Shared db/session behavior lives in `src/recorder/db/session.py`.
- Prefer service-layer logic for non-trivial transitions or orchestration.
- In async SQLAlchemy flows, eager load related data before access.
- Roll back on errors through the existing session dependency pattern.

## Files To Check Together

- `src/recorder/api/routes/projects.py`
- `src/recorder/api/routes/sessions.py`
- `src/recorder/api/routes/personas.py`
- `src/recorder/api/routes/chat.py`
- `src/recorder/schemas/project.py`
- `src/recorder/schemas/session.py`
- `src/recorder/schemas/persona.py`
- `src/recorder/db/models.py`

## Common Mistakes

- changing a response model without updating the route return shape
- adding relationship access without eager loading
- baking product logic into the route instead of a service/helper
- assuming the documented endpoint behavior is already implemented

## Minimum Validation

- import the affected route module
- run the relevant endpoint locally if dependencies are available
- verify schema fields still match ORM attributes
