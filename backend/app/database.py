import os
from redis.asyncio import from_url
from app.config import CELERY_BROKER_URL


async def get_redis(url=None):
    if url is None:
        url = CELERY_BROKER_URL

    redis = await from_url(url)

    try:
        yield redis
    finally:
        await redis.aclose()