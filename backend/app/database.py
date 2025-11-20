"""
Database connection and session management.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings

# Async PostgreSQL engine
# postgresql+asyncpg://user:password@host:port/database
DATABASE_URL = getattr(settings, 'DATABASE_URL', 'postgresql+asyncpg://localhost/kurz_studio')

engine = create_async_engine(
    DATABASE_URL,
    echo=True if settings.ENV == "dev" else False,  # SQL 로깅
    pool_size=20,  # 동시 접속 제한
    max_overflow=10,
    pool_pre_ping=True,  # 연결 상태 확인
)

# Async session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)

# Base class for ORM models
Base = declarative_base()


async def get_db():
    """
    FastAPI dependency for DB session.

    Usage:
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Create all tables (for development only)."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
