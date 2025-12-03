"""Shared test fixtures and configuration."""

import asyncio
import os
import shutil
from collections.abc import AsyncGenerator, Generator
from datetime import datetime, timezone
from pathlib import Path

# Set mock API key before importing app modules
os.environ.setdefault("OPENAI_API_KEY", "sk-test-key-for-testing")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base, get_async_session
from app.core.security import create_access_token, get_password_hash
from app.main import app
from app.modules.auth.models import User, UserStatus
from app.modules.tenants.models import Tenant, TenantStatus

# Base domain for multi-tenancy
BASE_DOMAIN = "samvit.bhanu.dev"

# Fixed test tenant ID - prevents accumulation of test data
TEST_TENANT_ID = "00000000-0000-0000-0000-000000000001"
TEST_USER_ID = "00000000-0000-0000-0000-000000000002"
TEST_ADMIN_ID = "00000000-0000-0000-0000-000000000003"

# Directories for test data
POLICIES_DIR = Path("data/policies")
CHROMA_DIR = Path("data/chroma")


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db_path(tmp_path: Path):
    """Create a temporary database file path."""
    db_path = tmp_path / "test.db"
    yield db_path
    # Cleanup handled by tmp_path fixture


@pytest_asyncio.fixture(scope="function")
async def test_engine(test_db_path: Path):
    """Create a test database engine using file-based SQLite."""
    # Use file-based SQLite so the middleware can access the same database
    db_url = f"sqlite+aiosqlite:///{test_db_path}"
    engine = create_async_engine(
        db_url,
        connect_args={"check_same_thread": False},
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def session_maker(test_engine):
    """Create a shared session maker for both fixtures and app."""
    maker = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )
    return maker


@pytest_asyncio.fixture(scope="function")
async def test_session(session_maker) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session."""
    async with session_maker() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def client(
    test_engine,  # noqa: ARG001
    session_maker,
    monkeypatch,
) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with overridden database dependency."""
    import app.core.database as db_module
    import app.core.tenancy as tenancy_module

    # Create a session maker that we can override
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    # Override the FastAPI dependency
    app.dependency_overrides[get_async_session] = override_get_db

    # Also patch the session maker used by the TenantMiddleware
    monkeypatch.setattr(tenancy_module, "async_session_maker", session_maker)
    monkeypatch.setattr(db_module, "async_session_maker", session_maker)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def test_tenant(test_session: AsyncSession) -> Tenant:
    """Create a test tenant with fixed ID for consistent test data location."""
    tenant = Tenant(
        id=TEST_TENANT_ID,
        name="Test Company",
        domain=f"test.{BASE_DOMAIN}",
        email="test@example.com",
        status=TenantStatus.ACTIVE.value,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    test_session.add(tenant)
    await test_session.commit()
    await test_session.refresh(tenant)
    return tenant


def cleanup_test_tenant_data() -> None:
    """Clean up test tenant data. Can be called manually if needed."""
    # Clean policy files
    tenant_policy_dir = POLICIES_DIR / TEST_TENANT_ID
    if tenant_policy_dir.exists():
        shutil.rmtree(tenant_policy_dir, ignore_errors=True)

    # Clean chroma collection
    try:
        from app.ai.rag.vectorstore import PolicyVectorStore

        store = PolicyVectorStore(TEST_TENANT_ID)
        store.clear()
    except Exception:
        pass  # Ignore errors during cleanup


@pytest_asyncio.fixture(scope="function")
async def test_user(test_session: AsyncSession, test_tenant: Tenant) -> User:
    """Create a test user with fixed ID."""
    user = User(
        id=TEST_USER_ID,
        tenant_id=test_tenant.id,
        email="testuser@example.com",
        password_hash=get_password_hash("Test@12345"),
        first_name="Test",
        last_name="User",
        status=UserStatus.ACTIVE.value,
        is_active=True,
        email_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


@pytest_asyncio.fixture(scope="function")
async def admin_user(test_session: AsyncSession, test_tenant: Tenant) -> User:
    """Create an admin test user with fixed ID."""
    user = User(
        id=TEST_ADMIN_ID,
        tenant_id=test_tenant.id,
        email="admin@example.com",
        password_hash=get_password_hash("Admin@12345"),
        first_name="Admin",
        last_name="User",
        status=UserStatus.ACTIVE.value,
        is_active=True,
        email_verified=True,
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    test_session.add(user)
    await test_session.commit()
    await test_session.refresh(user)
    return user


def get_auth_headers(user: User, tenant: Tenant) -> dict[str, str]:
    """Generate authentication headers for a user."""
    token = create_access_token(
        data={"sub": user.id, "tenant_id": tenant.id},
    )
    return {
        "Authorization": f"Bearer {token}",
        "Host": tenant.domain,
    }


def get_tenant_headers(tenant: Tenant) -> dict[str, str]:
    """Generate headers with tenant context only (no auth)."""
    return {
        "Host": tenant.domain,
    }
