from redis.asyncio import from_url


async def get_redis():
    redis = await from_url("redis://redis:6379/0")
    redis.exists
    try:
        yield redis
    finally:
        await redis.aclose()