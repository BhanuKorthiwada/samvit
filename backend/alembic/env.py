"""Alembic environment configuration for async SQLAlchemy."""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config

from app.core.config import settings

# Import Base and all models for autogenerate support
from app.core.database import Base  # noqa: F401

# Import all models to ensure they're registered with Base.metadata
from app.modules.auth.models import User  # noqa: F401
from app.modules.employees.models import Department, Employee, Position  # noqa: F401
from app.modules.attendance.models import AttendanceRecord, Shift  # noqa: F401
from app.modules.leave.models import (  # noqa: F401
    Holiday,
    LeaveBalance,
    LeavePolicy,
    LeaveRequest,
)
from app.modules.payroll.models import (  # noqa: F401
    PayrollPeriod,
    Payslip,
    SalaryComponent,
    SalaryStructure,
    SalaryStructureComponent,
)
from app.modules.tenants.models import Tenant  # noqa: F401

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Set the database URL from settings
config.set_main_option("sqlalchemy.url", settings.database_url)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# The target metadata for autogenerate support
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """Run migrations with the given connection."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Run migrations in 'online' mode with async engine."""
    # Handle SQLite differently - it doesn't support async the same way
    db_url = config.get_main_option("sqlalchemy.url")

    if db_url and db_url.startswith("sqlite"):
        # For SQLite, use synchronous approach
        from sqlalchemy import create_engine

        sync_url = db_url.replace("+aiosqlite", "")
        connectable = create_engine(sync_url, poolclass=pool.NullPool)
        with connectable.connect() as connection:
            do_run_migrations(connection)
        connectable.dispose()
    else:
        # For PostgreSQL and other async-capable databases
        connectable = async_engine_from_config(
            config.get_section(config.config_ini_section, {}),
            prefix="sqlalchemy.",
            poolclass=pool.NullPool,
        )

        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)

        await connectable.dispose()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
