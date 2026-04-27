# Architecture & Design Guidelines

## 1. Service Layer Pattern for Database Operations

**Guideline:** 
Do not execute raw database queries (`db.execute()`, `db.add()`, etc.) directly inside FastAPI router endpoint functions. Instead, delegate these operations to a dedicated Service layer.

**Rationale:**
- **Separation of Concerns:** Routers should only handle HTTP concerns (request parsing, path/query validation, response formatting, authentication, and HTTP status codes). Business logic and data access belong in a dedicated Service or Repository layer.
- **Reusability:** Database queries and data retrieval logic can be reused across different endpoints, background tasks, or CLI scripts without duplicating SQLAlchemy code.
- **Testability:** Service methods can be unit-tested directly by passing a database session mock, without the need for an HTTP client or testing the entire FastAPI dependency tree.

**Implementation Pattern:**
1. Create a service class/module in the `app/services/` directory (e.g., `app/services/checklist_service.py`).
2. Encapsulate the database queries in static methods or class methods within the service.
3. Inject the `AsyncSession` into the FastAPI router via `Depends(get_db)` and pass it down to the service layer.

**Example:**
```python
# Route implementation
@router.get("/")
async def list_items(db: AsyncSession = Depends(get_db)):
    return await ItemService.list_all(db)
```

---

## 2. Organization Scoping Pattern

**Guideline:**
Pass `current_user.organization_id` into service methods whenever the result set must respect org visibility. Apply the org filter inside the service, not in the route handler.

**Rule:** `organization_id = NULL` → platform-wide (visible to all users). `organization_id = X` → visible only to users with matching `organization_id`.

```python
# Service — apply org filter
from sqlalchemy import or_

async def get_global_templates(db, type=None, organization_id=None):
    query = select(Checklist).where(Checklist.is_global == True)
    query = query.where(or_(
        Checklist.organization_id == None,
        Checklist.organization_id == organization_id,
    ))
    ...

# Route — inject current user and pass org_id
@router.get("/templates/global")
async def list_global_templates(
    type: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await ChecklistService.get_global_templates(
        db, type, organization_id=current_user.organization_id
    )
```

---

## 3. Database Migration Pattern

**Guideline:**
Add schema changes as SQL strings in the `migrations` array inside `app/db/session.py:init_db()`. Always use `IF NOT EXISTS` / `IF EXISTS` for idempotency. Do **not** use Alembic.

```python
migrations = [
    # existing entries...
    "ALTER TABLE my_table ADD COLUMN IF NOT EXISTS new_col VARCHAR(200)",
    "CREATE INDEX IF NOT EXISTS idx_my_table_col ON my_table(new_col)",
]
```

---

## 4. Checklist Item Metadata

**Guideline:**
`ChecklistItem` carries three optional metadata fields for the external review workflow. Always expose them in item create/update/list APIs and the `/globals` UI:

| Field | Type | Purpose |
|-------|------|---------|
| `team_category` | string (nullable) | Structural ownership: Development, QA, DevOps, Delivery, etc. |
| `guidance` | text (nullable) | 1–2 sentences explaining what a good answer contains |
| `applicability_tags` | JSON array (nullable) | Optional filters: project type, phase, domain, platform |

---

## 5. Global Checklist Type — Free Form

**Guideline:**
`GlobalChecklistCreate.type` accepts **any string**, not `Literal["delivery", "technical"]`. The planned master-checklist model uses `type = "master"`. Do not revert to the Literal constraint.

---

## 6. AsyncSession + selectinload Rule

**Guideline:**
Any SQLAlchemy relationship accessed in an async context **must** be eagerly loaded with `selectinload()`. Lazy loading raises `MissingGreenlet` at runtime.

```python
# ✅ Always add selectinload for relationship access
result = await db.execute(
    select(Checklist)
    .options(selectinload(Checklist.items))
    .where(Checklist.id == checklist_id)
)
checklist = result.scalar_one_or_none()
# Now checklist.items is safe to access
```