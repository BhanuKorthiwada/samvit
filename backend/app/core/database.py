"""Database configuration and session management."""

from collections.abc import AsyncGenerator
from contextvars import ContextVar

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# Context variable to store current tenant ID
current_tenant_id: ContextVar[str | None] = ContextVar(
    "current_tenant_id", default=None
)

# Create async engine with appropriate settings based on database type
engine_kwargs = {
    "echo": settings.debug,
}

# SQLite doesn't support pool_size and max_overflow
if not settings.database_url.startswith("sqlite"):
    engine_kwargs.update(
        {
            "pool_pre_ping": True,
            "pool_size": settings.db_pool_size,
            "max_overflow": settings.db_pool_max_overflow,
            "pool_timeout": settings.db_pool_timeout,
            "pool_recycle": settings.db_pool_recycle,
        }
    )

engine = create_async_engine(settings.database_url, **engine_kwargs)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Alias for easier imports
AsyncSessionLocal = async_session_maker


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency to get async database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
