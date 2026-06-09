from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlmodel import SQLModel

from app.core.config import settings

# 创建异步引擎
async_engine = create_async_engine(settings.DATABASE_URL, echo=True)

# 创建异步会话工厂
async_session = async_sessionmaker(
    async_engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

async def get_async_session():
    async with async_session() as session:
        yield session
