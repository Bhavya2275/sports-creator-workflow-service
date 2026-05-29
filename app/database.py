from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text
from app.config import get_settings

settings = get_settings()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("ALTER TABLE qualification_jobs ADD COLUMN IF NOT EXISTS prompt_tokens INTEGER"))
        await conn.execute(text("ALTER TABLE qualification_jobs ADD COLUMN IF NOT EXISTS completion_tokens INTEGER"))
        await conn.execute(text("ALTER TABLE qualification_jobs ADD COLUMN IF NOT EXISTS total_tokens INTEGER"))


async def drop_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
