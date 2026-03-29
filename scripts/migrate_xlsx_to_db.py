"""
ReviewBot - Excel Data Migration Script
Reads all .xlsx files from data/projects/ and data/templates/
and migrates them fully into the database.

What gets created:
  - Global templates  (data/templates/*.xlsx)
  - Projects          (one per sub-folder in data/projects/)
  - Checklists        (one per .xlsx file, linked to the project)
  - ChecklistItems    (one per question row)
  - Review            (one per project checklist representing the captured review)
  - ReviewResponses   (from "Inputs from Delivery", "Reviewer Comments", "RAG" columns)
"""

import sys
import re
from pathlib import Path
from datetime import datetime

import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor

# ─── Config ────────────────────────────────────────────────────────────────────
DB = dict(host="127.0.0.1", port=5435, dbname="reviews_db",
          user="review_user", password="review_password_change_me")

BASE_DIR   = Path(__file__).parent.parent          # project root
TEMPLATES  = BASE_DIR / "data" / "templates"
PROJECTS   = BASE_DIR / "data" / "projects"

# Bcrypt hash of "Admin@123" (pre-computed — no bcrypt dependency needed)
ADMIN_HASH = "$2b$12$1YEK5YKoxFGQcYTmG0.XiuWCC5B1an1sOocu8ivfnAohRPv9e9jyG"

# Human-readable project names keyed by folder name
PROJECT_META = {
    "aaa-pdh":  {"name": "AAA PDH",          "domain": "enterprise"},
    "neumoney": {"name": "NeUMoney Platform", "domain": "fintech"},
}

# ─── RAG normaliser ────────────────────────────────────────────────────────────
_GREEN = {"green", "g", "yes", "done", "good", "complete", "completed",
          "ok", "ok.", "pass", "passed"}
_AMBER = {"amber", "a", "partial", "in progress", "wip", "ongoing",
          "need to check", "check", "review", "tbd", "pending"}
_RED   = {"red", "r", "no", "not done", "missing", "fail", "failed",
          "not started", "overdue"}

def normalise_rag(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "na"
    txt = str(value).strip().lower()
    if not txt or txt == "nan":
        return "na"
    for kw in _GREEN:
        if kw in txt:
            return "green"
    for kw in _RED:
        if kw in txt:
            return "red"
    for kw in _AMBER:
        if kw in txt:
            return "amber"
    return "na"

def clean(value) -> str | None:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return None
    s = str(value).strip()
    return s if s and s.lower() != "nan" else None

# ─── Excel parser ──────────────────────────────────────────────────────────────
def parse_sheet(df: pd.DataFrame, checklist_type: str) -> list[dict]:
    """
    Parse one Excel sheet into a list of item dicts.
    Handles merged cells by inheriting the last non-empty area value.
    Returns all columns: item_code, area, question, expected_evidence,
                          reviewer_comment, rag_status, weight, order_idx
    """
    items = []
    area_col  = "Area" if checklist_type == "delivery" else "Technical Area"
    code_col  = "SNO"  if checklist_type == "delivery" else "#"
    current_area = "General"

    for idx, row in df.iterrows():
        # Inherit merged area
        raw_area = clean(row.get(area_col))
        if raw_area:
            current_area = raw_area

        question = clean(row.get("Key Review Question"))
        if not question:
            continue

        # item code – float 1.1 → "1.1"
        raw_code = row.get(code_col)
        if raw_code is not None and not (isinstance(raw_code, float) and pd.isna(raw_code)):
            item_code = str(raw_code).rstrip("0").rstrip(".") if "." in str(raw_code) else str(raw_code)
            # keep decimal format  e.g. "1.10" or "1.1"
            item_code = str(raw_code)
            if item_code.endswith(".0"):
                item_code = item_code[:-2]
        else:
            item_code = str(idx + 1)

        evidence   = clean(row.get("Inputs from Delivery"))
        rev_comment = clean(row.get("Reviewer Comments"))

        # aaa-pdh technical has an extra unnamed column with notes
        extra_note = None
        for col in df.columns:
            if col.startswith("Unnamed"):
                extra_note = clean(row.get(col))
                break

        if extra_note and rev_comment:
            rev_comment = f"{rev_comment} | {extra_note}"
        elif extra_note:
            rev_comment = extra_note

        rag_raw = row.get("RAG")
        rag_status = normalise_rag(rag_raw)
        # If RAG is na but we have evidence that is a clear yes/no, derive it
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
            "weight":            1.0,
            "is_review_mandatory":       True,
            "order_idx":         len(items),
        })

    return items


def parse_xlsx(path: Path) -> dict[str, list[dict]]:
    """Return {checklist_type: [items]} for every recognised sheet."""
    xl = pd.ExcelFile(path)
    result = {}
    for sheet in xl.sheet_names:
        if "Delivery" in sheet:
            df = pd.read_excel(path, sheet_name=sheet)
            result["delivery"] = parse_sheet(df, "delivery")
        elif "Technical" in sheet:
            df = pd.read_excel(path, sheet_name=sheet)
            result["technical"] = parse_sheet(df, "technical")
    return result

# ─── DB helpers ────────────────────────────────────────────────────────────────
def upsert_user(cur, email, full_name, role="admin") -> int:
    cur.execute("""
        INSERT INTO users (email, full_name, hashed_password, role, is_active, created_at)
        VALUES (%s, %s, %s, %s, TRUE, NOW())
        ON CONFLICT (email) DO UPDATE SET full_name = EXCLUDED.full_name
        RETURNING id
    """, (email, full_name, ADMIN_HASH, role))
    return cur.fetchone()[0]


def upsert_project(cur, name, domain, owner_id) -> int:
    cur.execute("""
        INSERT INTO projects (name, domain, status, owner_id, created_at)
        VALUES (%s, %s, 'active', %s, NOW())
        ON CONFLICT DO NOTHING
        RETURNING id
    """, (name, domain, owner_id))
    row = cur.fetchone()
    if row:
        return row[0]
    cur.execute("SELECT id FROM projects WHERE name = %s", (name,))
    return cur.fetchone()[0]


def insert_checklist(cur, name, cl_type, version, project_id, is_global) -> int:
    cur.execute("""
        INSERT INTO checklists (name, type, version, project_id, is_global, created_at)
        VALUES (%s, %s, %s, %s, %s, NOW())
        RETURNING id
    """, (name, cl_type, version, project_id, is_global))
    return cur.fetchone()[0]


def insert_items(cur, checklist_id, items) -> list[int]:
    ids = []
    for item in items:
        cur.execute("""
            INSERT INTO checklist_items
                (checklist_id, item_code, area, question, category,
                 weight, is_review_mandatory, expected_evidence, "order", created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            RETURNING id
        """, (
            checklist_id,
            item["item_code"],
            item["area"],
            item["question"],
            item["category"],
            item["weight"],
            item["is_review_mandatory"],
            item["expected_evidence"],
            item["order_idx"],
        ))
        ids.append(cur.fetchone()[0])
    return ids


def insert_review(cur, project_id, checklist_id, title, reviewer_id) -> int:
    cur.execute("""
        INSERT INTO reviews
            (project_id, checklist_id, title, status, conducted_by,
             voice_enabled, review_date, created_at, completed_at)
        VALUES (%s, %s, %s, 'completed', %s, FALSE, NOW(), NOW(), NOW())
        RETURNING id
    """, (project_id, checklist_id, title, reviewer_id))
    return cur.fetchone()[0]


def insert_responses(cur, review_id, item_ids, items):
    for item_id, item in zip(item_ids, items):
        answer = item.get("expected_evidence") or ""
        cur.execute("""
            INSERT INTO review_responses
                (review_id, checklist_item_id, answer, comments,
                 rag_status, created_at)
            VALUES (%s, %s, %s, %s, %s, NOW())
        """, (
            review_id,
            item_id,
            answer[:255] if answer else "",
            item.get("reviewer_comment"),
            item["rag_status"],
        ))


def insert_report(cur, review_id, items) -> int:
    total   = len(items)
    greens  = sum(1 for i in items if i["rag_status"] == "green")
    ambers  = sum(1 for i in items if i["rag_status"] == "amber")
    reds    = sum(1 for i in items if i["rag_status"] == "red")
    score   = round((greens / total * 100), 2) if total else 0.0

    if score >= 75:
        overall = "green"
    elif score >= 50:
        overall = "amber"
    else:
        overall = "red"

    areas_followed  = list({i["area"] for i in items if i["rag_status"] == "green"})
    gaps_identified = [
        {"area": i["area"], "question": i["question"][:120], "rag": i["rag_status"]}
        for i in items if i["rag_status"] in ("red", "amber")
    ]
    summary = (
        f"Review completed. {greens} green / {ambers} amber / {reds} red "
        f"out of {total} items. Compliance score: {score}%%."
    )

    import json
    cur.execute("""
        INSERT INTO reports
            (review_id, summary, overall_rag_status, compliance_score,
             areas_followed, gaps_identified, recommendations, action_items,
             approval_status, requires_approval, created_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending', TRUE, NOW())
        RETURNING id
    """, (
        review_id, summary, overall, score,
        json.dumps(areas_followed),
        json.dumps(gaps_identified),
        json.dumps([]),
        json.dumps([]),
    ))
    return cur.fetchone()[0]


# ─── Main migration ────────────────────────────────────────────────────────────
def migrate():
    conn = psycopg2.connect(**DB)
    cur  = conn.cursor()

    print("\n" + "="*65)
    print("  ReviewBot - Excel to Database Migration")
    print("="*65)

    # ── 1. Admin user ──────────────────────────────────────────────
    print("\n[1/4] Creating admin user ...")
    admin_id = upsert_user(cur, "admin@reviewbot.com", "Admin User", "admin")
    reviewer_id = upsert_user(cur, "reviewer@reviewbot.com", "Tech Reviewer", "reviewer")
    conn.commit()
    print(f"      admin id={admin_id}  reviewer id={reviewer_id}")

    # ── 2. Global templates ────────────────────────────────────────
    print("\n[2/4] Loading global templates ...")
    for xlsx in sorted(TEMPLATES.glob("*.xlsx")):
        data = parse_xlsx(xlsx)
        for cl_type, items in data.items():
            cl_name = f"Standard {cl_type.title()} Checklist"
            # Skip if already loaded
            cur.execute(
                "SELECT id FROM checklists WHERE name=%s AND is_global=TRUE",
                (cl_name,)
            )
            if cur.fetchone():
                print(f"      SKIP  {cl_name} (already exists)")
                continue
            cl_id = insert_checklist(cur, cl_name, cl_type, "1.0", None, True)
            insert_items(cur, cl_id, items)
            conn.commit()
            print(f"      OK    {cl_name}  ({len(items)} items)")

    # ── 3. Projects + checklists + reviews ─────────────────────────
    print("\n[3/4] Migrating project data ...")
    for proj_dir in sorted(PROJECTS.iterdir()):
        if not proj_dir.is_dir():
            continue

        meta   = PROJECT_META.get(proj_dir.name,
                                  {"name": proj_dir.name.title(), "domain": "general"})
        proj_id = upsert_project(cur, meta["name"], meta["domain"], admin_id)
        conn.commit()
        print(f"\n  Project: {meta['name']}  (id={proj_id}  domain={meta['domain']})")

        for xlsx in sorted(proj_dir.glob("*.xlsx")):
            data = parse_xlsx(xlsx)
            for cl_type, items in data.items():
                cl_name = f"{meta['name']} — {cl_type.title()} Checklist"
                cl_id   = insert_checklist(cur, cl_name, cl_type, "1.0", proj_id, False)
                item_ids = insert_items(cur, cl_id, items)

                # Review + responses
                rev_title  = f"{meta['name']} {cl_type.title()} Review"
                review_id  = insert_review(cur, proj_id, cl_id, rev_title, reviewer_id)
                insert_responses(cur, review_id, item_ids, items)

                # Report
                rpt_id = insert_report(cur, review_id, items)

                conn.commit()

                greens = sum(1 for i in items if i["rag_status"] == "green")
                ambers = sum(1 for i in items if i["rag_status"] == "amber")
                reds   = sum(1 for i in items if i["rag_status"] == "red")
                nas    = sum(1 for i in items if i["rag_status"] == "na")
                score  = round(greens / len(items) * 100, 1) if items else 0
                print(f"    [{cl_type:9}] {len(items):3} items | "
                      f"G={greens} A={ambers} R={reds} N/A={nas} | "
                      f"score={score}%%  checklist={cl_id} review={review_id} report={rpt_id}")

    # ── 4. Summary query ───────────────────────────────────────────
    print("\n[4/4] Database summary ...")
    for table in ("users","projects","checklists","checklist_items",
                  "reviews","review_responses","reports"):
        cur.execute(f"SELECT COUNT(*) FROM {table}")
        print(f"      {table:22} {cur.fetchone()[0]:>5} rows")

    cur.close()
    conn.close()
    print("\n" + "="*65)
    print("  Migration complete!")
    print("="*65 + "\n")


if __name__ == "__main__":
    migrate()

