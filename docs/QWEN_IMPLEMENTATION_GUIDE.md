# ReviewBot Downloads Page — Qwen Code Implementation Guide

> **Purpose:** Add a Downloads page to the ReviewBot web app (hosted on GCP Cloud Run)
> so users can download the VSCode extension (.vsix) and CLI agent (.whl) directly from the site.

---

## Context You Must Understand First

### Project Structure
```
c:\projects\reviewbot\          ← main FastAPI web app (GCP Cloud Run)
c:\projects\reviewbot-vscode\   ← VSCode extension (TypeScript)
c:\projects\reviewbot-agent\    ← Python CLI agent
```

### Tech Stack (reviewbot)
- **Backend:** FastAPI + Uvicorn (async Python)
- **Frontend:** Plain HTML files in `static/` directory — NO React/Vue/Webpack
- **Routing:** Routes defined in `main.py`, each returns a `FileResponse` pointing to an HTML file
- **Static files:** Mounted at `/static` via `StaticFiles(directory=_static_dir)`
- **Deployment:** Docker → GCP Cloud Run (stateless container; files must be baked into the image)

### Existing routes in main.py:
```
GET /          → static/home.html
GET /ui        → static/index.html
GET /history   → static/history.html
GET /projects-ui → static/project.html
GET /globals   → static/globals.html
GET /dashboard → static/home.html (alias)
/static/*      → StaticFiles mount
```

### Distributable Artifacts
| Tool | File | Source project |
|------|------|----------------|
| VSCode Extension | `reviewbot-vscode-0.0.1.vsix` | `c:\projects\reviewbot-vscode\` |
| CLI Agent | `reviewbot_agent-0.1.0-py3-none-any.whl` | `c:\projects\reviewbot-agent\` |

---

## What Needs to Be Built

### Task 1 — Copy artifacts into reviewbot project

Place distributable files inside `static/downloads/` so they are baked into the Docker image:

```
static/
  downloads/
    reviewbot-vscode-0.0.1.vsix      ← copy from c:\projects\reviewbot-vscode\
    reviewbot_agent-0.1.0-py3-none-any.whl   ← build from c:\projects\reviewbot-agent\
    checksums.txt                    ← SHA256 of both files (optional but recommended)
```

**To build the CLI wheel** (run this in `c:\projects\reviewbot-agent\`):
```bash
pip install build
python -m build --wheel
# Output: dist/reviewbot_agent-0.1.0-py3-none-any.whl
```

---

### Task 2 — Add `/downloads` route to `main.py`

Open `c:\projects\reviewbot\main.py`.

**After the existing route block** (around line 106, after the `/globals` route), add:

```python
@app.get("/downloads", include_in_schema=False)
async def serve_downloads():
    """Serve the Downloads page for VSCode extension and CLI agent"""
    return FileResponse(os.path.join(_static_dir, "downloads.html"))
```

No other changes to `main.py` are needed. The files in `static/downloads/` are already
served automatically by the `/static` StaticFiles mount as `/static/downloads/<filename>`.

---

### Task 3 — Create `static/downloads.html`

Create the file `c:\projects\reviewbot\static\downloads.html`.

**Design requirements** (match existing pages):
- Same dark theme as `home.html`: background `#0f172a`, accent `#38bdf8`, font `Segoe UI`
- Same `<header>` with logo "ReviewBot" and nav links: Dashboard, Downloads (active)
- No JavaScript frameworks — plain HTML + inline CSS + minimal vanilla JS
- No authentication required — downloads must be publicly accessible (no JWT check)

**Page layout:**

```
Header (same as home.html)
│
├── Hero section
│     Title: "ReviewBot Tooling"
│     Subtitle: "Extend your workflow with the VSCode extension or CLI agent"
│
├── Download Cards (2 cards side by side, stack on mobile)
│   │
│   ├── Card 1 — VSCode Extension
│   │     Icon: VSCode logo SVG (inline, blue #007ACC)
│   │     Title: "VSCode Extension"
│   │     Version: v0.0.1
│   │     Description: "Run ReviewBot reviews directly inside VS Code.
│   │                   Supports project scanning, review sessions, and
│   │                   inline checklist management."
│   │     Download button → /static/downloads/reviewbot-vscode-0.0.1.vsix
│   │     Install instructions (collapsible <details>):
│   │       1. Download the .vsix file
│   │       2. Open VS Code → Extensions (Ctrl+Shift+X)
│   │       3. Click ⋯ menu → "Install from VSIX..."
│   │       4. Select the downloaded file
│   │       5. Configure: Settings → reviewbot.serverUrl → your ReviewBot server URL
│   │
│   └── Card 2 — CLI Agent
│         Icon: terminal SVG (inline, green #22c55e)
│         Title: "CLI Agent"
│         Version: v0.1.0
│         Description: "Command-line tool to run project scans and reviews
│                       from your terminal or CI/CD pipeline."
│         Download button → /static/downloads/reviewbot_agent-0.1.0-py3-none-any.whl
│         Install instructions (collapsible <details>):
│           1. Download the .whl file
│           2. pip install reviewbot_agent-0.1.0-py3-none-any.whl
│           3. reviewbot login --server https://your-reviewbot-url.run.app
│           4. reviewbot review --project-id 1
│           Or install directly: pip install reviewbot_agent-0.1.0-py3-none-any.whl
│
└── Configuration section
      Title: "Connecting to Your ReviewBot Server"
      Show the server URL format:
        https://<your-cloud-run-service>.run.app
      Note: Both tools default to http://localhost:8000 — update to your deployed URL.
```

**HTML/CSS rules:**
- Cards: background `#1e293b`, border `1px solid #334155`, border-radius `12px`, padding `28px`
- Download button: class `btn btn-primary` (same style as home.html)
- File size shown next to button (VSCode: ~113 KB, CLI: ~30 KB)
- `<details><summary>Installation Instructions</summary>...</details>` for collapsible steps
- Responsive: use CSS Grid `grid-template-columns: repeat(auto-fit, minmax(320px, 1fr))`

---

### Task 4 — Add "Downloads" nav link to `home.html`

Open `c:\projects\reviewbot\static\home.html`.

Find the `<header>` nav section. It contains anchor tags like:

```html
<header nav a href="/ui">Reviews</header nav a>
```

Add a Downloads link to the nav (exact position: after whatever the last nav link is):

```html
<a href="/downloads">Downloads</a>
```

The existing CSS already styles `header nav a` with hover effects — no new CSS needed.

---

### Task 5 — Update `Dockerfile` (important for GCP Cloud Run)

Open `c:\projects\reviewbot\Dockerfile`.

The `COPY` command that copies static files must include the new `static/downloads/` directory.
If the Dockerfile already does `COPY . .` or `COPY static/ ./static/`, **no change is needed**.

If it copies selectively, add:
```dockerfile
COPY static/downloads/ ./static/downloads/
```

Verify the Dockerfile copies the full `static/` directory.

---

## What NOT to Do

- Do NOT add authentication/JWT checks to the `/downloads` route — downloads must be public
- Do NOT create a new Python router file — just add the route directly to `main.py`
- Do NOT use React, Vue, or any JS framework — plain HTML only
- Do NOT create a separate file server endpoint — the existing `/static` StaticFiles mount already serves files from the `static/` directory
- Do NOT change the Docker base image or requirements.txt — no new dependencies needed
- Do NOT modify any existing HTML files except adding the nav link to `home.html`

---

## Verification Checklist

After implementation, verify:
- [ ] `GET /downloads` returns HTTP 200 with the downloads page
- [ ] `GET /static/downloads/reviewbot-vscode-0.0.1.vsix` returns the file with content-type `application/octet-stream`
- [ ] `GET /static/downloads/reviewbot_agent-0.1.0-py3-none-any.whl` returns the file
- [ ] Downloads page nav link is visible and active on `/downloads`
- [ ] Page looks consistent with `home.html` (same header, same color scheme)
- [ ] `docker build` succeeds and files are present inside the image

---

## VSCode Marketplace Publishing — Background Info

> This is NOT part of the Qwen implementation task above. This is context for the project owner.

The VSCode extension (`c:\projects\reviewbot-vscode\`) is already configured for marketplace publishing:
- **Publisher ID:** `reflections-info-systems` (set in `package.json`)
- **Extension name:** `reviewbot-vscode`

**To publish to VS Code Marketplace (one-time setup):**
1. Register publisher at https://marketplace.visualstudio.com/manage
2. Create a Personal Access Token in Azure DevOps (scope: Marketplace → Manage)
3. Run: `npx @vscode/vsce login reflections-info-systems`
4. Run: `npx @vscode/vsce publish`

**Assessment: Very easy.** The `package.json` already has all required fields (`publisher`, `repository`, `license`, `icon`). The main prerequisite is registering the publisher account — the tooling is already set up.

**Recommendation:** Publish to marketplace for better user experience (one-click install, auto-updates). Keep the `.vsix` download on the site as a fallback for air-gapped environments.

---

## Summary of Files to Create/Modify

| Action | File |
|--------|------|
| CREATE | `static/downloads/reviewbot-vscode-0.0.1.vsix` (copy from reviewbot-vscode project) |
| CREATE | `static/downloads/reviewbot_agent-0.1.0-py3-none-any.whl` (build from reviewbot-agent project) |
| CREATE | `static/downloads.html` (new page) |
| MODIFY | `main.py` (add one route: `/downloads`) |
| MODIFY | `static/home.html` (add one nav link) |
| VERIFY | `Dockerfile` (confirm static/ is fully copied) |
