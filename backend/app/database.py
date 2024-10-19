from redis.asyncio import from_url
from app.config import CELERY_BROKER_URL
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession
from app.config import SQLALCHEMY_DATABASE_URL


async def get_redis(url=None):
    if url is None:
        url = CELERY_BROKER_URL

    redis = await from_url(url)

    try:
        yield redis
    finally:
        await redis.aclose()


async_engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)
session_factory = async_sessionmaker(async_engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


# Depends로 여러번 주입해도 동일한 세션 객체가 호출됨. (의존성 캐싱)
async def get_session():
    async with session_factory() as session:
        yield session