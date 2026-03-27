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
    """Initialize database — run Alembic migrations then create any missing tables."""
    import subprocess, sys, logging
    log = logging.getLogger(__name__)

    # Run migrations synchronously before the async app starts serving requests
    try:
        result = subprocess.run(
            [sys.executable, "-m", "alembic", "upgrade", "head"],
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            log.warning("Alembic migration warning:\n%s", result.stderr)
        else:
            log.info("Alembic migrations applied:\n%s", result.stdout or "(none pending)")
    except Exception as exc:
        log.warning("Could not run Alembic migrations: %s", exc)

    # create_all as safety net for any model not covered by migrations
    from app.models import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
