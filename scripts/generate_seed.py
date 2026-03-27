"""
ReviewBot - Generate seed_data.sql from xlsx files
Run: python scripts/generate_seed.py
Output: scripts/seed_data.sql  (safe to re-run, uses ON CONFLICT DO NOTHING / DO UPDATE)
"""
import json
import re
from pathlib import Path
from datetime import datetime

import pandas as pd

BASE_DIR  = Path(__file__).parent.parent
TEMPLATES = BASE_DIR / "data" / "templates"
PROJECTS  = BASE_DIR / "data" / "projects"
OUT_FILE  = Path(__file__).parent / "seed_data.sql"

# Bcrypt hash of "Admin@123"
ADMIN_HASH = "$2b$12$1YEK5YKoxFGQcYTmG0.XiuWCC5B1an1sOocu8ivfnAohRPv9e9jyG"

PROJECT_META = {
    "aaa-pdh":  {"name": "AAA PDH",           "domain": "enterprise"},
    "neumoney": {"name": "NeUMoney Platform",  "domain": "fintech"},
}

_GREEN = {"green","g","yes","done","good","complete","completed","ok","ok.","pass","passed"}
_AMBER = {"amber","a","partial","in progress","wip","ongoing","need to check","check","review","tbd","pending"}
_RED   = {"red","r","no","not done","missing","fail","failed","not started","overdue"}


def normalise_rag(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "na"
    txt = str(value).strip().lower()
    if not txt or txt == "nan":
        return "na"
    for kw in _GREEN:
        if kw in txt: return "green"
    for kw in _RED:
        if kw in txt: return "red"
    for kw in _AMBER:
        if kw in txt: return "amber"
    return "na"


def clean(value):
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip()
    return s if s and s.lower() != "nan" else None


def sq(value) -> str:
    """Escape a value for SQL single-quoted string. Returns NULL if None."""
    if value is None:
        return "NULL"
    return "'" + str(value).replace("'", "''") + "'"


def parse_sheet(df: pd.DataFrame, checklist_type: str) -> list[dict]:
    items = []
    area_col = "Area" if checklist_type == "delivery" else "Technical Area"
    code_col = "SNO"  if checklist_type == "delivery" else "#"
    current_area = "General"

    for idx, row in df.iterrows():
        raw_area = clean(row.get(area_col))
        if raw_area:
            current_area = raw_area

        question = clean(row.get("Key Review Question"))
        if not question:
            continue

        raw_code = row.get(code_col)
        if raw_code is not None and not (isinstance(raw_code, float) and pd.isna(raw_code)):
            item_code = str(raw_code)
            if item_code.endswith(".0"):
                item_code = item_code[:-2]
        else:
            item_code = str(idx + 1)

        evidence    = clean(row.get("Inputs from Delivery"))
        rev_comment = clean(row.get("Reviewer Comments"))

        extra_note = None
        for col in df.columns:
            if col.startswith("Unnamed"):
                extra_note = clean(row.get(col))
                break
        if extra_note and rev_comment:
            rev_comment = f"{rev_comment} | {extra_note}"
        elif extra_note:
            rev_comment = extra_note

        rag_raw    = row.get("RAG")
        rag_status = normalise_rag(rag_raw)
        if rag_status == "na" and evidence:
            rag_status = normalise_rag(evidence)

        items.append({
            "item_code":         item_code,
            "area":              current_area,
            "question":          question,
            "category":          checklist_type,
            "expected_evidence": evidence,
            "reviewer_comment":  rev_comment,
            "rag_status":        rag_status,
        })
    return items


def parse_xlsx(path: Path) -> dict:
    xl  = pd.ExcelFile(path)
    out = {}
    for sheet in xl.sheet_names:
        if "Delivery" in sheet:
            out["delivery"] = parse_sheet(pd.read_excel(path, sheet_name=sheet), "delivery")
        elif "Technical" in sheet:
            out["technical"] = parse_sheet(pd.read_excel(path, sheet_name=sheet), "technical")
    return out


def generate():
    lines = []
    ts = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")

    lines += [
        f"-- ============================================================",
        f"-- ReviewBot seed data  (generated {ts})",
        f"-- Run in DBeaver or: psql -U review_user -d reviews_db -f seed_data.sql",
        f"-- Safe to re-run: users/projects use ON CONFLICT; checklists are",
        f"-- skipped if a same-name entry already exists.",
        f"-- ============================================================",
        "",
        "BEGIN;",
        "",
    ]

    # ── 1. Users ──────────────────────────────────────────────────────────────
    lines += [
        "-- ── Users ──────────────────────────────────────────────────────────",
        "INSERT INTO users (email, full_name, hashed_password, role, is_active, created_at)",
        "VALUES",
        f"  ('admin@reviewbot.com',    'Admin User',     '{ADMIN_HASH}', 'admin',    TRUE, NOW()),",
        f"  ('reviewer@reviewbot.com', 'Tech Reviewer',  '{ADMIN_HASH}', 'reviewer', TRUE, NOW())",
        "ON CONFLICT (email) DO UPDATE",
        "  SET full_name = EXCLUDED.full_name,",
        "      hashed_password = EXCLUDED.hashed_password;",
        "",
    ]

    # ── 2. Global templates ───────────────────────────────────────────────────
    lines += [
        "-- ── Global template checklists ─────────────────────────────────────",
    ]

    all_data = {}  # store parsed items for later use in projects

    for xlsx in sorted(TEMPLATES.glob("*.xlsx")):
        data = parse_xlsx(xlsx)
        for cl_type, items in data.items():
            cl_name = f"Standard {cl_type.title()} Checklist"
            lines += [
                f"-- {cl_name} ({len(items)} items)",
                "DO $$ DECLARE cl_id INT;",
                "BEGIN",
                f"  IF NOT EXISTS (SELECT 1 FROM checklists WHERE name={sq(cl_name)} AND is_global=TRUE) THEN",
                f"    INSERT INTO checklists (name, type, version, project_id, is_global, created_at)",
                f"    VALUES ({sq(cl_name)}, {sq(cl_type)}, '1.0', NULL, TRUE, NOW())",
                f"    RETURNING id INTO cl_id;",
            ]
            for i, item in enumerate(items):
                lines.append(
                    f"    INSERT INTO checklist_items "
                    f"(checklist_id, item_code, area, question, category, weight, is_required, expected_evidence, \"order\", created_at) "
                    f"VALUES (cl_id, {sq(item['item_code'])}, {sq(item['area'])}, {sq(item['question'])}, "
                    f"{sq(item['category'])}, 1.0, TRUE, {sq(item['expected_evidence'])}, {i}, NOW());"
                )
            lines += [
                "  END IF;",
                "END $$;",
                "",
            ]
        all_data[xlsx.stem] = data

    # ── 3. Projects + project checklists + reviews + reports ──────────────────
    lines += [
        "-- ── Projects ───────────────────────────────────────────────────────",
    ]

    for proj_dir in sorted(PROJECTS.iterdir()):
        if not proj_dir.is_dir():
            continue

        meta     = PROJECT_META.get(proj_dir.name, {"name": proj_dir.name.title(), "domain": "general"})
        proj_var = re.sub(r'[^a-z0-9]', '_', proj_dir.name.lower())

        lines += [
            f"-- Project: {meta['name']}",
            "DO $$ DECLARE",
            f"  proj_id   INT;",
            f"  admin_id  INT;",
            f"  rvwr_id   INT;",
        ]

        # declare vars for each checklist
        xlsx_files = sorted(proj_dir.glob("*.xlsx"))
        cl_vars = []
        rv_vars = []
        for xlsx in xlsx_files:
            data = parse_xlsx(xlsx)
            for cl_type in data:
                v = f"{cl_type[:3]}_cl"
                r = f"{cl_type[:3]}_rv"
                cl_vars.append((v, cl_type, data[cl_type]))
                rv_vars.append(r)

        for v, _, _ in cl_vars:
            lines.append(f"  {v}_id  INT;")
        for r in rv_vars:
            lines.append(f"  {r}_id  INT;")
            lines.append(f"  {r}_rpt_id INT;")

        lines += [
            "BEGIN",
            "  SELECT id INTO admin_id FROM users WHERE email='admin@reviewbot.com';",
            "  SELECT id INTO rvwr_id  FROM users WHERE email='reviewer@reviewbot.com';",
            "",
            f"  -- upsert project",
            f"  INSERT INTO projects (name, domain, status, owner_id, created_at)",
            f"  VALUES ({sq(meta['name'])}, {sq(meta['domain'])}, 'active', admin_id, NOW())",
            f"  ON CONFLICT DO NOTHING;",
            f"  SELECT id INTO proj_id FROM projects WHERE name={sq(meta['name'])};",
            "",
        ]

        for v, cl_type, items in cl_vars:
            cl_name = f"{meta['name']} — {cl_type.title()} Checklist"
            rev_title = f"{meta['name']} {cl_type.title()} Review"
            rv = f"{cl_type[:3]}_rv"

            greens = sum(1 for i in items if i["rag_status"] == "green")
            ambers = sum(1 for i in items if i["rag_status"] == "amber")
            reds   = sum(1 for i in items if i["rag_status"] == "red")
            score  = round(greens / len(items) * 100, 2) if items else 0
            overall = "green" if score >= 75 else "amber" if score >= 50 else "red"

            areas_followed  = list({i["area"] for i in items if i["rag_status"] == "green"})
            gaps_identified = [{"area": i["area"], "question": i["question"][:120], "rag": i["rag_status"]}
                               for i in items if i["rag_status"] in ("red", "amber")]
            summary_txt = (f"Review completed. {greens} green / {ambers} amber / {reds} red "
                           f"out of {len(items)} items. Compliance score: {score}%.")

            lines += [
                f"  -- Checklist: {cl_name}",
                f"  INSERT INTO checklists (name, type, version, project_id, is_global, created_at)",
                f"  VALUES ({sq(cl_name)}, {sq(cl_type)}, '1.0', proj_id, FALSE, NOW())",
                f"  RETURNING id INTO {v}_id;",
                "",
            ]

            for i, item in enumerate(items):
                lines.append(
                    f"  INSERT INTO checklist_items "
                    f"(checklist_id, item_code, area, question, category, weight, is_required, expected_evidence, \"order\", created_at) "
                    f"VALUES ({v}_id, {sq(item['item_code'])}, {sq(item['area'])}, {sq(item['question'])}, "
                    f"{sq(item['category'])}, 1.0, TRUE, {sq(item['expected_evidence'])}, {i}, NOW());"
                )

            lines += [
                "",
                f"  -- Review + responses",
                f"  INSERT INTO reviews (project_id, checklist_id, title, status, conducted_by, voice_enabled, review_date, created_at, completed_at)",
                f"  VALUES (proj_id, {v}_id, {sq(rev_title)}, 'completed', rvwr_id, FALSE, NOW(), NOW(), NOW())",
                f"  RETURNING id INTO {rv}_id;",
                "",
            ]

            for i, item in enumerate(items):
                answer = (item.get("expected_evidence") or "")[:255]
                lines.append(
                    f"  INSERT INTO review_responses (review_id, checklist_item_id, answer, comments, rag_status, created_at) "
                    f"SELECT {rv}_id, id, {sq(answer)}, {sq(item.get('reviewer_comment'))}, {sq(item['rag_status'])}, NOW() "
                    f"FROM checklist_items WHERE checklist_id={v}_id AND \"order\"={i};"
                )

            lines += [
                "",
                f"  -- Report",
                f"  INSERT INTO reports (review_id, summary, overall_rag_status, compliance_score,",
                f"      areas_followed, gaps_identified, recommendations, action_items,",
                f"      approval_status, requires_approval, created_at)",
                f"  VALUES ({rv}_id,",
                f"    {sq(summary_txt)},",
                f"    {sq(overall)},",
                f"    {score},",
                f"    {sq(json.dumps(areas_followed))},",
                f"    {sq(json.dumps(gaps_identified))},",
                f"    '[]', '[]', 'pending', TRUE, NOW())",
                f"  RETURNING id INTO {rv}_rpt_id;",
                "",
            ]

        lines += ["END $$;", ""]

    lines += ["COMMIT;", "", "-- Done! Verify:", "SELECT table_name, (xpath('/row/c/text()', query_to_xml(format('SELECT count(*) AS c FROM %I', table_name), FALSE, TRUE, '')))[1]::text::int AS rows FROM information_schema.tables WHERE table_schema='public' AND table_type='BASE TABLE' ORDER BY table_name;"]

    sql = "\n".join(lines)
    OUT_FILE.write_text(sql, encoding="utf-8")
    print(f"Generated: {OUT_FILE}  ({len(lines)} lines)")
    print("Run in DBeaver or:")
    print("  psql -h localhost -p 5435 -U review_user -d reviews_db -f scripts/seed_data.sql")


if __name__ == "__main__":
    generate()
