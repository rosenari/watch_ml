from typing import List
from fastapi import UploadFile, Depends
from app.config import FILE_DIRECTORY
from app.database import get_redis, get_session
from app.repositories.file_repository import FileRepository
from app.util import transactional, format_file_size
from app.entity import Status


class FileService:
    def __init__(self, redis, session, file_directory=FILE_DIRECTORY):
        self.redis = redis
        self.session = session
        self.repository = FileRepository(file_directory=file_directory, db=session)

    @transactional
    async def upload_file(self, file: UploadFile) -> str:
        content = await file.read()
        file_record = await self.repository.save_file(file.filename, content)
        return file_record.filename

    @transactional
    async def delete_file(self, file_name: str) -> None:
        return await self.repository.delete_file(file_name)

    async def get_file_list(self) -> List[dict]:
        file_list = []
        files = await self.repository.list_files()
        for file in files:
            formatted_size = format_file_size(file.filesize)

            file_list.append({
                "file_name": file.filename,
                "creation_date": file.creation_time.strftime('%Y-%m-%d %H:%M:%S'),
                "file_size": formatted_size,
                "status": file.status.value
            })
        return file_list
    
    async def get_valid_file_list(self) -> List[dict]:
        prefix = "valid:"
        return await get_valid_file_list_from_redis(self.redis, prefix)
    
    @transactional
    async def update_status(self, file_name: str, status: str):
        try:
            new_status = Status[status.upper()]
        except KeyError:
            raise ValueError(f"Invalid status: {status}")

        return await self.repository.update_status(file_name, new_status)
    

async def get_file_service(redis = Depends(get_redis), session = Depends(get_session)):
    yield FileService(redis, session)


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