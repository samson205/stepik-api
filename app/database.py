from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession 

from app.config import DATABASE_URL

if DATABASE_URL is None:
    raise ValueError("DATABASE_URL is not set in environment variables")

async_engine = create_async_engine(DATABASE_URL, echo=True)
async_session_maker = async_sessionmaker(async_engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    pass
