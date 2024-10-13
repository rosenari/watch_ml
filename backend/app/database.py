import os
from redis.asyncio import from_url


async def get_redis():
    redis = await from_url(os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0'))

    try:
        yield redis
    finally:
        await redis.aclose()