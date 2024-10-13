import pytest
import os
import pytest_asyncio
from app.database import get_redis



@pytest_asyncio.fixture
async def redis():
    os.environ['CELERY_BROKER_URL'] = 'redis://localhost:6379/0'

    async for ri in get_redis():
        yield ri


@pytest.mark.asyncio
async def test_get_redis(redis):
    # 레디스 작동 테스트

    await redis.set('test_key', 'test_value')

    assert await redis.get('test_key') == b'test_value'

    await redis.delete('test_key')

    assert await redis.exists('test_key') == 0