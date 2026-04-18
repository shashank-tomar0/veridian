from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from backend.config import settings

# Engine configuration with SQLite thread-safety checks
connect_args = {"check_same_thread": False} if "sqlite" in settings.database_url else {}
engine = create_async_engine(settings.database_url, echo=False, connect_args=connect_args)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(AsyncAttrs, DeclarativeBase):
    pass

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

async def init_models():
    """Auto-create tables for Zero-Config mode."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
