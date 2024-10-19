from typing import List
from fastapi import UploadFile, Depends
from app.database import get_redis, get_session
from app.repositories.file_repository import FileRepository
from app.util import transactional


class FileService:
    def __init__(self, repository: FileRepository, redis):
        self.repository = repository
        self.redis = redis

    @transactional
    async def upload_file(self, file: UploadFile) -> str:
        content = await file.read()
        return await self.repository.save_file(file.filename, content)

    @transactional
    async def delete_file(self, file_name: str) -> None:
        return await self.repository.delete_file(file_name)

    async def get_file_list(self) -> List[dict]:
        return await self.repository.list_files()
    
    async def get_valid_file_list(self) -> List[str]:
        prefix = "valid:"
        return await get_valid_file_list_from_redis(self.redis, prefix)
    

async def get_file_service(redis = Depends(get_redis), database = Depends(get_session)):
    yield FileService(FileRepository(db=database), redis)


async def get_valid_file_list_from_redis(redis, prefix: str = "valid:") -> list:
    cursor = "0"
    result = []

    while cursor != 0:
        cursor, keys = await redis.scan(cursor=cursor, match=f"{prefix}*", count=100)
        if keys:
            decoded_keys = [key.decode('utf-8') for key in keys]
            values = await redis.mget(*keys)

            for key, value in zip(decoded_keys, values):
                    result.append({ 'file_name': key.replace("valid:", ""), 'status': value.decode('utf-8') if value else None })

    return result