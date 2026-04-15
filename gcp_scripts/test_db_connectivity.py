"""
test_db_connectivity.py — Diagnose Cloud SQL connectivity for ReviewBot

Usage:
    # From the reviewbot project root:
    python scripts/test_db_connectivity.py

    # Override the connection mode:
    python scripts/test_db_connectivity.py --mode proxy   # Cloud SQL Auth Proxy on localhost
    python scripts/test_db_connectivity.py --mode socket  # Unix socket (Cloud Run style)
    python scripts/test_db_connectivity.py --mode url     # Use DATABASE_URL as-is from .env

Reads credentials from  gcp_scripts/.env  (DB_USER, DB_PASS, DB_NAME,
GCP_PROJECT, GCP_REGION, DB_INSTANCE_NAME).

Exit codes:
    0 — all tests passed
    1 — at least one test failed
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Parse .env
# ---------------------------------------------------------------------------

def load_env(env_file: Path) -> dict:
    """Parse a key=value .env file; skip comments and blank lines."""
    if not env_file.exists():
        print(f"ERROR: .env not found at {env_file}")
        sys.exit(1)

    result = {}
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        eq = line.find("=")
        if eq <= 0:
            continue
        key = line[:eq].strip()
        val = line[eq + 1:].strip().strip('"').strip("'")
        # Strip inline comments (e.g. value  # comment)
        if " #" in val:
            val = val[:val.index(" #")].strip()
        result[key] = val
    return result


# ---------------------------------------------------------------------------
# Build connection strings
# ---------------------------------------------------------------------------

def build_dsn(env: dict, mode: str) -> str:
    """
    Build an asyncpg DSN based on the chosen connection mode.

    mode='proxy'  — Cloud SQL Auth Proxy running on 127.0.0.1:5432
    mode='socket' — Unix socket at /cloudsql/<project>:<region>:<instance>
    mode='url'    — return DATABASE_URL from env verbatim
    """
    from urllib.parse import quote as _quote

    user = env.get("DB_USER", "review_user")
    # Percent-encode the password so special chars like '@' don't break the URL
    password = _quote(env.get("DB_PASS", ""), safe="")
    db = env.get("DB_NAME", "reviews_db")
    project = env.get("GCP_PROJECT", "")
    region = env.get("GCP_REGION", "us-central1")
    instance = env.get("DB_INSTANCE_NAME", "reviewbot-db")
    instance_connection = f"{project}:{region}:{instance}"

    if mode == "url":
        url = env.get("DATABASE_URL", "")
        if not url:
            print("ERROR: DATABASE_URL not found in .env")
            sys.exit(1)
        return url

    if mode == "socket":
        # asyncpg host= syntax for Unix sockets:
        socket_dir = f"/cloudsql/{instance_connection}"
        return f"postgresql+asyncpg://{user}:{password}@/{db}?host={socket_dir}"

    # default: proxy
    return f"postgresql+asyncpg://{user}:{password}@127.0.0.1:5432/{db}"


# ---------------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------------

PASS = "\033[32mPASS\033[0m"
FAIL = "\033[31mFAIL\033[0m"
SKIP = "\033[33mSKIP\033[0m"

results: list[tuple[str, bool, str]] = []


def record(label: str, ok: bool, detail: str = ""):
    results.append((label, ok, detail))
    status = PASS if ok else FAIL
    print(f"  [{status}] {label}")
    if detail:
        indent = "         "
        for line in detail.splitlines():
            print(f"{indent}{line}")


async def test_asyncpg_direct(dsn_asyncpg: str) -> bool:
    """Connect with raw asyncpg (no SQLAlchemy)."""
    try:
        import asyncpg  # type: ignore
    except ImportError:
        record("asyncpg direct connect", False, "asyncpg not installed — run: pip install asyncpg")
        return False

    try:
        conn = await asyncpg.connect(dsn=dsn_asyncpg, timeout=10)
        version = await conn.fetchval("SELECT version()")
        await conn.close()
        record("asyncpg direct connect", True, version.split(",")[0])
        return True
    except Exception as exc:
        record("asyncpg direct connect", False, f"{type(exc).__name__}: {exc}")
        _print_remediation(exc)
        return False


async def test_sqlalchemy_engine(dsn_sa: str) -> bool:
    """Connect via SQLAlchemy async engine — same code path as init_db()."""
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        import sqlalchemy as sa
    except ImportError:
        record("SQLAlchemy engine connect", False, "sqlalchemy not installed")
        return False

    try:
        engine = create_async_engine(dsn_sa, echo=False, future=True)
        async with engine.begin() as conn:
            result = await conn.execute(sa.text("SELECT current_database(), current_user"))
            row = result.fetchone()
        await engine.dispose()
        record("SQLAlchemy engine connect", True, f"database={row[0]}, user={row[1]}")
        return True
    except Exception as exc:
        record("SQLAlchemy engine connect", False, f"{type(exc).__name__}: {exc}")
        _print_remediation(exc)
        return False


async def test_table_access(dsn_sa: str) -> bool:
    """Check that the users table exists (basic schema sanity check)."""
    try:
        from sqlalchemy.ext.asyncio import create_async_engine
        import sqlalchemy as sa
    except ImportError:
        return False

    try:
        engine = create_async_engine(dsn_sa, echo=False, future=True)
        async with engine.begin() as conn:
            result = await conn.execute(
                sa.text(
                    "SELECT count(*) FROM information_schema.tables "
                    "WHERE table_schema = 'public' AND table_name = 'users'"
                )
            )
            count = result.scalar()
        await engine.dispose()
        if count:
            record("users table exists", True)
        else:
            record("users table exists", False, "Table not found — run init_db() or alembic upgrade head")
        return bool(count)
    except Exception as exc:
        record("users table exists", False, f"{type(exc).__name__}: {exc}")
        return False


# ---------------------------------------------------------------------------
# Remediation hints
# ---------------------------------------------------------------------------

def _print_remediation(exc: Exception):
    msg = str(exc).lower()
    name = type(exc).__name__.lower()

    if "password" in name or "password" in msg or "authentication" in msg:
        print()
        print("  HINT — Password mismatch. Reset the Cloud SQL user password:")
        print("    gcloud sql users set-password review_user \\")
        print("      --instance=reviewbot-db \\")
        print("      --project=reviewbot-493320 \\")
        print("      --password='<DB_PASS from .env>'")
        print()
        print("  Then re-sync the secret and redeploy:")
        print("    cd gcp_scripts && .\\05_deploy_app.ps1")

    elif "connect" in msg or "refused" in msg or "timeout" in msg:
        print()
        print("  HINT — Cannot reach the database server.")
        print("  For local testing, start the Cloud SQL Auth Proxy first:")
        print("    cloud-sql-proxy reviewbot-493320:us-central1:reviewbot-db --port=5432")
        print("  Or install it: https://cloud.google.com/sql/docs/postgres/sql-proxy")

    elif "does not exist" in msg or "unknown database" in msg:
        print()
        print("  HINT — Database/user not found.")
        print("  Re-run: gcp_scripts\\04_create_db.ps1")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def run(mode: str, env: dict):
    print()
    print("=" * 60)
    print("  ReviewBot — Database Connectivity Test")
    print("=" * 60)

    user = env.get("DB_USER", "?")
    db   = env.get("DB_NAME", "?")
    inst = f"{env.get('GCP_PROJECT','?')}:{env.get('GCP_REGION','?')}:{env.get('DB_INSTANCE_NAME','?')}"

    print(f"  User:     {user}")
    print(f"  Database: {db}")
    print(f"  Instance: {inst}")
    print(f"  Mode:     {mode}")
    print()

    # Build the two DSN flavours
    if mode == "url":
        dsn_sa = env.get("DATABASE_URL", "")
        # asyncpg wants no driver prefix
        dsn_asyncpg = dsn_sa.replace("postgresql+asyncpg://", "postgresql://", 1)
    else:
        dsn_sa = build_dsn(env, mode)
        dsn_asyncpg = dsn_sa.replace("postgresql+asyncpg://", "postgresql://", 1)

    print(f"  DSN: {_redact(dsn_sa)}")
    print()

    print("Tests:")
    ok1 = await test_asyncpg_direct(dsn_asyncpg)
    ok2 = await test_sqlalchemy_engine(dsn_sa)
    ok3 = await test_table_access(dsn_sa) if ok2 else False

    print()
    print("=" * 60)
    passed = sum(1 for _, ok, _ in results if ok)
    total  = len(results)
    print(f"  Result: {passed}/{total} tests passed")
    print("=" * 60)
    print()

    if not (ok1 and ok2):
        print("Next steps:")
        print("  1. Confirm DB_PASS in gcp_scripts/.env matches the Cloud SQL user password.")
        print("  2. Re-run gcp_scripts/04_create_db.ps1 to reset the password + update the secret.")
        print("  3. Re-run gcp_scripts/05_deploy_app.ps1 to redeploy with the corrected secret.")
        print()

    return 0 if (ok1 and ok2) else 1


def _redact(dsn: str) -> str:
    """Hide the password portion of a DSN for display."""
    import re
    return re.sub(r"(://[^:]+:)[^@]+(@)", r"\1***\2", dsn)


def main():
    parser = argparse.ArgumentParser(description="Test Cloud SQL connectivity for ReviewBot")
    parser.add_argument(
        "--mode",
        choices=["proxy", "socket", "url"],
        default="proxy",
        help=(
            "proxy  = Cloud SQL Auth Proxy on 127.0.0.1:5432 (default, for local testing)\n"
            "socket = Unix socket /cloudsql/... (matches Cloud Run environment)\n"
            "url    = use DATABASE_URL from .env verbatim"
        ),
    )
    args = parser.parse_args()

    # Locate gcp_scripts/.env relative to this script
    script_dir = Path(__file__).resolve().parent
    env_file = script_dir / ".env"

    env = load_env(env_file)

    sys.exit(asyncio.run(run(args.mode, env)))


if __name__ == "__main__":
    main()
