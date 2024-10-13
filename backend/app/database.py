import os
from redis.asyncio import from_url


async def get_redis(url=None):
    if url is None:
        url = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0')

    redis = await from_url(url)

    try:
        yield redis
    finally:
        await redis.aclose()