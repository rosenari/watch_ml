import pytest
import pytest_asyncio
from app.database import get_redis



@pytest_asyncio.fixture
async def redis():
    async for ri in get_redis('redis://localhost:6379/0'):
        yield ri


@pytest.mark.asyncio
async def test_get_redis(redis):
    # 레디스 작동 테스트

    await redis.set('test_key', 'test_value')

    assert await redis.get('test_key') == b'test_value'

    await redis.delete('test_key')

    assert await redis.exists('test_key') == 0