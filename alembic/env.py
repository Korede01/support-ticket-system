# migrations/env.py
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from sqlalchemy.engine import Connection

from alembic import context

# ------------------------------------------------------------------------------
# 1. Import your application’s settings and metadata
# ------------------------------------------------------------------------------
import app.models    # noqa: F401  (so that Base.metadata includes all tables)
from app.core.config import settings
from app.db.session import Base

# ------------------------------------------------------------------------------
# 2. Alembic Config object (reads alembic.ini)
# ------------------------------------------------------------------------------
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ------------------------------------------------------------------------------
# 3. Tell Alembic which Metadata to use for 'autogenerate'
# ------------------------------------------------------------------------------
target_metadata = Base.metadata

# ------------------------------------------------------------------------------
# 4. Convert your async URL → sync URL, and also normalize "postgres://" → "postgresql://"
# ------------------------------------------------------------------------------
def get_sync_url() -> str:
    """
    - If settings.DATABASE_URL starts with "postgresql+asyncpg://", strip "+asyncpg" off.
    - If it starts with "postgres://", replace with "postgresql://".
    - Otherwise, assume it is already a valid sync URL.
    """
    async_url: str = settings.DATABASE_URL

    if async_url.startswith("postgresql+asyncpg://"):
        return async_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    if async_url.startswith("postgres://"):
        return async_url.replace("postgres://", "postgresql://", 1)

    return async_url


# Override the sqlalchemy.url in alembic.ini
config.set_main_option("sqlalchemy.url", get_sync_url())


# ------------------------------------------------------------------------------
# 5. Offline mode: generate SQL without connecting
# ------------------------------------------------------------------------------
def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


# ------------------------------------------------------------------------------
# 6. Online mode: create a synchronous Engine and run migrations
# ------------------------------------------------------------------------------
def run_migrations_online() -> None:
    """
    In 'online' mode we construct a synchronous Engine and run migrations
    directly without any asyncio.
    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
        future=True
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# ------------------------------------------------------------------------------
# 7. Check offline vs. online
# ------------------------------------------------------------------------------
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
