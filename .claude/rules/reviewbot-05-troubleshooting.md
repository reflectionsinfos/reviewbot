# ReviewBot — Troubleshooting Reference

> Common issues and solutions.
> Last updated: 2026-04-27

---

## Database Issues

### MissingGreenlet on relationship access
**Cause:** SQLAlchemy relationship accessed without `selectinload()` in async context.
**Fix:** Add `.options(selectinload(Model.relationship))` to every query that accesses related objects.

### DB port conflict (Docker)
**Cause:** Docker PostgreSQL runs on host port `5435` (not 5432) to avoid conflict with a locally-installed PostgreSQL.
**Fix:** Use port `5435` in DBeaver and `.env` `DATABASE_URL`.

### Migration not applied
**Cause:** New column/index added in code but not in `init_db` migrations array.
**Fix:** Add `ALTER TABLE ... ADD COLUMN IF NOT EXISTS ...` to the `migrations` list in `app/db/session.py`. Restart the app — `init_db()` runs on startup.

---

## URL / Link Issues

### Portal links showing `localhost` in production emails
**Cause:** Route handler using `settings.APP_BASE_URL` (which defaults to `http://localhost:8000`) instead of deriving the URL from the live request.
**Fix:** Use `_get_base_url(http_request)` helper in the route. See design guideline #7.

---

## Authentication Issues

### 401 — Could not validate credentials
- Check token format: `Authorization: Bearer <token>`
- Token may have expired (default 8 hours)
- Ensure `SECRET_KEY` in `.env` matches what was used when the token was issued

### Can't login
- Default demo user: `admin@example.com` / `admin123`
- Verify bcrypt hash: `from passlib.context import CryptContext; CryptContext(schemes=['bcrypt']).verify(plain, hashed)`

---

## LLM / OpenAI Issues

### 401 — Invalid API key
- Verify key in `.env`: `OPENAI_API_KEY=sk-...` (no quotes, no extra spaces)
- Restart server after changing `.env`
- Check credits: platform.openai.com/account/usage

### Rate limit exceeded
- Wait and retry; GPT-4 limit is 3 RPM on free tier
- Implement retry with exponential backoff (`tenacity` library)

---

## Report Generation

### PDF generation fails — `ImportError: No module named 'reportlab'`
```bash
pip install reportlab
```

### `Heading` class error in ReportLab
**Cause:** `Heading` is not a valid ReportLab platypus class.
**Fix:** Use `Paragraph(text, styles['Heading1'])` instead.

---

## Checklist Parsing (Excel)

### Sheet not found
**Cause:** Excel file has wrong sheet names.
**Expected:** "Delivery Check List V 1.0" and "Technical Check List V 1.0" (exact).
**Diagnosis:**
```python
import pandas as pd
xl = pd.ExcelFile("file.xlsx")
print(xl.sheet_names)
```

---

## File Upload Issues

### `FileNotFoundError` on upload
```bash
mkdir -p uploads
```

---

## Deployment

### `ModuleNotFoundError: No module named 'app'`
```bash
export PYTHONPATH=/path/to/reviewbot:$PYTHONPATH
```

### Environment variables not loaded
- `.env` must be in project root
- No quotes around values: `OPENAI_API_KEY=sk-...` not `OPENAI_API_KEY="sk-..."`

### CORS errors in browser
Check `main.py` CORS middleware — ensure frontend origin is in `allow_origins`.

---

## Debugging Tips

```bash
# Syntax check key files
python -c "
import ast, sys
for f in ['app/models.py', 'app/db/session.py', 'main.py']:
    try:
        ast.parse(open(f).read())
        print('OK ', f)
    except SyntaxError as e:
        print('ERR', f, e); sys.exit(1)
"

# Start with debug logging
uvicorn main:app --log-level debug

# Health check
curl http://localhost:8000/health

# Run Docker
docker-compose up --build
```
