"""
Database Session and Connection Management
"""
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
    import logging
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
        ]
        for sql in migrations:
            try:
                await conn.execute(__import__('sqlalchemy').text(sql))
                log.info("Migration applied: %s", sql[:60])
            except Exception as exc:
                log.warning("Migration skipped (%s): %s", type(exc).__name__, sql[:60])
