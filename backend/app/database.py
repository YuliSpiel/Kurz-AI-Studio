"""
Database connection and session management.
Uses lazy initialization to avoid import-time database connections.
This is critical for Celery workers which should not load async engines.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from app.config import settings

# Lazy-initialized engine and session maker
_engine = None
_async_session_maker = None
_sync_engine = None
_sync_session_maker = None

# Base class for ORM models (can be imported without triggering engine creation)
Base = declarative_base()


def _get_database_url():
    """Get DATABASE_URL with asyncpg driver."""
    url = getattr(settings, 'DATABASE_URL', 'postgresql+asyncpg://localhost/kurz_studio')
    # Ensure asyncpg driver is used
    if url.startswith('postgresql://') and '+asyncpg' not in url:
        url = url.replace('postgresql://', 'postgresql+asyncpg://', 1)
    return url


def get_engine():
    """Get or create the async engine (lazy initialization)."""
    global _engine
    if _engine is None:
        _engine = create_async_engine(
            _get_database_url(),
            echo=True if settings.ENV == "dev" else False,
            pool_size=20,
            max_overflow=10,
            pool_pre_ping=True,
        )
    return _engine


def get_async_session_maker():
    """Get or create the async session maker (lazy initialization)."""
    global _async_session_maker
    if _async_session_maker is None:
        _async_session_maker = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _async_session_maker


async def get_db():
    """
    FastAPI dependency for DB session.

    Usage:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    session_maker = get_async_session_maker()
    async with session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Create all tables (for development only)."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


def _get_sync_database_url():
    """Get DATABASE_URL with psycopg2 driver for sync operations."""
    url = getattr(settings, 'DATABASE_URL', 'postgresql://localhost/kurz_studio')
    # Use psycopg2 driver for sync
    if '+asyncpg' in url:
        url = url.replace('+asyncpg', '')
    return url


def get_sync_engine():
    """Get or create the sync engine for Celery tasks (lazy initialization)."""
    global _sync_engine
    if _sync_engine is None:
        _sync_engine = create_engine(
            _get_sync_database_url(),
            echo=True if settings.ENV == "dev" else False,
            pool_size=5,
            max_overflow=5,
            pool_pre_ping=True,
        )
    return _sync_engine


def get_sync_session_maker():
    """Get or create the sync session maker for Celery tasks."""
    global _sync_session_maker
    if _sync_session_maker is None:
        _sync_session_maker = sessionmaker(
            bind=get_sync_engine(),
            expire_on_commit=False,
            autoflush=False,
            autocommit=False,
        )
    return _sync_session_maker


# Alias for convenience in Celery tasks
SessionLocal = get_sync_session_maker
