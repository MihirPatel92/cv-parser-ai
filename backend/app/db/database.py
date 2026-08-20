from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from ..core.config import settings

# Use async_database_url property which auto-converts postgresql:// → postgresql+asyncpg://
# This makes it work both locally and on Render.com (which injects a plain postgresql:// URL)
engine = create_async_engine(
    settings.async_database_url,
    echo=False,
    pool_pre_ping=True,       # Reconnect if DB connection dropped (important for cloud)
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


async def get_db():
    async with SessionLocal() as session:
        yield session
