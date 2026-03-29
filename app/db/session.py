"""
Database Session and Connection Management
"""
import logging

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.core.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


async def get_db() -> AsyncSession:
    """Dependency for getting async database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables and apply any pending column additions."""
    from app.models import Base
    log = logging.getLogger(__name__)

    async with engine.begin() as conn:
        # Create all tables that don't exist yet
        await conn.run_sync(Base.metadata.create_all)

        # ── Incremental column additions (safe: IF NOT EXISTS) ────────────────
        # These cover cases where the table already existed before the column
        # was added to the model, since create_all never alters existing tables.
        migrations = [
            # 005 — checklist_routing_rules (whole table, handled by create_all)
            # 006 — needs_human_sign_off on autonomous_review_results
            """ALTER TABLE autonomous_review_results
               ADD COLUMN IF NOT EXISTS needs_human_sign_off BOOLEAN NOT NULL DEFAULT FALSE""",
            # 007a — agent_metadata on autonomous_review_jobs
            """ALTER TABLE autonomous_review_jobs
               ADD COLUMN IF NOT EXISTS agent_metadata JSONB""",
            # 007b — source_checklist_id on checklists (FK added by alembic on fresh DBs;
            #         here we just ensure the column exists on pre-existing databases)
            """ALTER TABLE checklists
               ADD COLUMN IF NOT EXISTS source_checklist_id INTEGER""",
            # 007c — autonomous_review_job_id on reports (links a report to an autonomous job)
            """ALTER TABLE reports
               ADD COLUMN IF NOT EXISTS autonomous_review_job_id INTEGER""",
            # 008 — area_codes on checklists (JSON mapping: area name → code)
            """ALTER TABLE checklists
               ADD COLUMN IF NOT EXISTS area_codes JSONB""",
            # 009 — summary scores on autonomous_review_jobs
            """ALTER TABLE autonomous_review_jobs
               ADD COLUMN IF NOT EXISTS green_count INTEGER DEFAULT 0""",
            """ALTER TABLE autonomous_review_jobs
               ADD COLUMN IF NOT EXISTS amber_count INTEGER DEFAULT 0""",
            """ALTER TABLE autonomous_review_jobs
               ADD COLUMN IF NOT EXISTS red_count INTEGER DEFAULT 0""",
            """ALTER TABLE autonomous_review_jobs
               ADD COLUMN IF NOT EXISTS skipped_count INTEGER DEFAULT 0""",
            """ALTER TABLE autonomous_review_jobs
               ADD COLUMN IF NOT EXISTS na_count INTEGER DEFAULT 0""",
            """ALTER TABLE autonomous_review_jobs
               ADD COLUMN IF NOT EXISTS compliance_score FLOAT DEFAULT 0.0""",
        ]
        for sql in migrations:
            try:
                await conn.execute(sa.text(sql))
                log.info("Migration applied: %s", sql[:60])
            except Exception as exc:
                log.warning("Migration skipped (%s): %s", type(exc).__name__, sql[:60])

        await _migrate_checklist_item_review_flag(conn, log)


async def _migrate_checklist_item_review_flag(conn, log: logging.Logger) -> None:
    """Rename checklist_items.is_required to checklist_items.is_review_mandatory."""
    table_names = await conn.run_sync(lambda sync_conn: sa.inspect(sync_conn).get_table_names())
    if "checklist_items" not in table_names:
        return

    columns = set(
        await conn.run_sync(
            lambda sync_conn: [col["name"] for col in sa.inspect(sync_conn).get_columns("checklist_items")]
        )
    )
    if "is_required" not in columns:
        return

    dialect = conn.dialect.name

    if "is_review_mandatory" not in columns:
        await conn.execute(
            sa.text(
                "ALTER TABLE checklist_items "
                "ADD COLUMN is_review_mandatory BOOLEAN NOT NULL DEFAULT TRUE"
            )
        )
        await conn.execute(
            sa.text(
                "UPDATE checklist_items "
                "SET is_review_mandatory = COALESCE(is_required, TRUE)"
            )
        )
        log.info("Copied checklist_items.is_required into is_review_mandatory")

    drop_sql = (
        "ALTER TABLE checklist_items DROP COLUMN IF EXISTS is_required"
        if dialect == "postgresql"
        else "ALTER TABLE checklist_items DROP COLUMN is_required"
    )
    try:
        await conn.execute(sa.text(drop_sql))
        log.info("Dropped legacy checklist_items.is_required column")
    except Exception as exc:
        log.warning("Could not drop legacy checklist_items.is_required column: %s", exc)
