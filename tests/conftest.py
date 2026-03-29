import pytest
import pytest_asyncio
import os
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from httpx import AsyncClient, ASGITransport

# ── Patch passlib + bcrypt >= 4.1 incompatibility ─────────────────────────
# passlib 1.7.4 is unmaintained and its bcrypt wrap-bug detection passes an
# 80-byte secret that bcrypt >= 4.1 rejects.  Monkey-patch before any import
# that triggers passlib initialisation.
import bcrypt as _bcrypt

_original_hashpw = _bcrypt.hashpw

def _patched_hashpw(password, salt):
    if isinstance(password, str):
        password = password.encode("utf-8")
    if len(password) > 72:
        password = password[:72]
    return _original_hashpw(password, salt)

_bcrypt.hashpw = _patched_hashpw
# ──────────────────────────────────────────────────────────────────────────

TEST_DATABASE_URL = "postgresql+asyncpg://review_user:review_password@localhost:5432/test_reviews_db"

# Force the application to boot against PostgreSQL during tests before importing main.
os.environ["DATABASE_URL"] = TEST_DATABASE_URL
os.environ.setdefault("DEBUG", "false")

from main import app
from app.db.session import get_db
from app.models import Base, User, Project, Checklist, ChecklistItem
from app.api.routes.auth import get_password_hash, create_access_token

engine = create_async_engine(TEST_DATABASE_URL, pool_pre_ping=True)
TestingSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

@pytest_asyncio.fixture(scope="session")
async def db_engine():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db_session(db_engine):
    async with TestingSessionLocal() as session:
        yield session
        # Clear data between tests to ensure isolation
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()

@pytest_asyncio.fixture
async def async_client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def create_test_user(db_session):
    """Creates a user with the requested role and returns (User, Headers)"""
    async def _create_user(role="admin", email=None):
        email = email or f"test_{uuid4().hex[:6]}@example.com"
        user = User(
            email=email,
            full_name="Test User",
            hashed_password=get_password_hash("password123"),
            role=role,
            is_active=True
        )
        db_session.add(user)
        await db_session.commit()
        await db_session.refresh(user)
        
        token = create_access_token(data={"sub": user.email, "role": user.role})
        headers = {"Authorization": f"Bearer {token}"}
        return user, headers
        
    return _create_user


@pytest_asyncio.fixture
async def project_factory(db_session):
    """Creates a sample project"""
    async def _create_project(owner_id, name=None):
        name = name or f"Test Project {uuid4().hex[:6]}"
        project = Project(
            name=name,
            domain="general",
            description="Integration test project",
            status="active",
            owner_id=owner_id
        )
        db_session.add(project)
        await db_session.commit()
        await db_session.refresh(project)
        return project
        
    return _create_project


@pytest_asyncio.fixture
async def checklist_factory(db_session):
    """Creates a checklist template or project checklist instance"""
    async def _create_checklist(is_global=True, project_id=None, name="Test Checklist", source_checklist_id=None):
        chk = Checklist(
            name=name,
            type="delivery",
            version="1.0",
            project_id=project_id,
            is_global=is_global,
            source_checklist_id=source_checklist_id
        )
        db_session.add(chk)
        await db_session.commit()
        await db_session.refresh(chk)
        return chk
        
    return _create_checklist


@pytest_asyncio.fixture
async def item_factory(db_session):
    """Creates a checklist item tied to a checklist"""
    async def _create_item(checklist_id, item_code, question="Is this a test?", weight=1.0):
        item = ChecklistItem(
            checklist_id=checklist_id,
            item_code=item_code,
            area="General",
            question=question,
            category="delivery",
            weight=weight,
            is_review_mandatory=True,
            order=0
        )
        db_session.add(item)
        await db_session.commit()
        await db_session.refresh(item)
        return item
        
    return _create_item

