# ReviewBot — Architecture & Design Guidelines

> CRITICAL: Follow these guidelines in all code you write for this project.
> Last updated: 2026-04-27

---

## 1. Service Layer Pattern for Database Operations

**Guideline:**
Do not execute raw database queries (`db.execute()`, `db.add()`, etc.) directly inside FastAPI router endpoint functions. Delegate to a dedicated Service layer.

**Rationale:**
- Routers handle only HTTP concerns (request parsing, auth, response formatting, status codes).
- Business logic and data access belong in `app/services/`.
- Service methods can be unit-tested by passing a DB session mock.

**Pattern:**
```python
# Route — delegates to service
@router.get("/")
async def list_items(db: AsyncSession = Depends(get_db)):
    return await ItemService.list_all(db)
```

---

## 2. Organization Scoping Pattern

**Guideline:**
Pass `current_user.organization_id` into service methods whenever the result set must respect org visibility. Apply the org filter inside the service, not in the route handler.

**Rule:** `organization_id = NULL` → platform-wide (visible to all). `organization_id = X` → visible only to users in that org.

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

## 4. ChecklistItem Metadata Fields

**Guideline:**
`ChecklistItem` carries three optional metadata fields. Always expose them in item create/update/list APIs and the `/globals` UI:

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

---

## 7. Dynamic Base URL — Never Hardcode `localhost`

**Guideline:**
Never use `settings.APP_BASE_URL` (which defaults to `http://localhost:8000`) when generating portal links, review URLs, or email links inside a request-scoped route handler. Always derive the base URL from the live HTTP request so the correct public domain is used in every environment (local, GCP Cloud Run, custom domain).

**Why this matters:**
`APP_BASE_URL` is a static config value. In GCP Cloud Run the app receives requests internally at `http://localhost:8000`, but the public-facing URL is entirely different. Hardcoding the default produces links like `http://localhost:8000/manual-review/…` in emails and the UI even in production.

**Implementation:**

Add a `_get_base_url` helper that reads the proxy headers injected by GCP / nginx:

```python
from fastapi import Request

def _get_base_url(http_request: Request) -> str:
    """Derive public base URL from request, honouring GCP/nginx proxy headers."""
    scheme = http_request.headers.get("x-forwarded-proto", http_request.url.scheme)
    host   = http_request.headers.get("host", http_request.url.netloc)
    return f"{scheme}://{host}"
```

Inject `http_request: Request` into every route that generates a shareable URL:

```python
@router.post("/manual")
async def create_manual_review(
    request: ManualReviewCreate,
    http_request: Request,           # ← add this
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    ...
    portal_url = f"{_get_base_url(http_request)}/manual-review/{review.id}?token={token}"
```

**Applies to:** every place a URL is returned to the client or embedded in an email — `portal_url`, `review_url`, `app_url` passed to email helpers, and any share-link list endpoints.

**`APP_BASE_URL` in config.py** may be kept as a fallback for non-request contexts (CLI scripts, background tasks), but must never be used inside a live HTTP route handler.

---

## 8. Button State After Async Form Submission

**Guideline:**
After a form button triggers an async API call, always restore the button to an interactive state on **both** success and failure paths. Never leave the button permanently disabled after a successful submission.

**The common mistake:**

```javascript
btn.disabled = true;
btn.textContent = 'Saving…';

try {
  await api('/endpoint', { … });
  btn.textContent = 'Done';          // ❌ button is still disabled
} catch (e) {
  btn.disabled = false;              // only re-enabled on error
  btn.textContent = 'Try Again';
}
```

**Correct pattern — success closes the modal:**

When the success state means the user is finished (review created, invitation sent, etc.), re-enable the button **and** redirect its `onclick` to close the modal so clicking "Done" dismisses it cleanly:

```javascript
btn.disabled = true;
btn.textContent = 'Saving…';

try {
  const result = await api('/endpoint', { … });
  showSuccessUI(result);
  btn.disabled = false;              // ✅ re-enable
  btn.onclick = closeMyModal;        // ✅ redirect click to close
  btn.textContent = 'Done';
} catch (e) {
  showError(e.message);
  btn.disabled = false;
  btn.textContent = 'Try Again';
}
```

**Rule:** Every `btn.disabled = true` that starts a submission must have a matching `btn.disabled = false` in **every** exit path of the try/catch block.
