import os
import aiofiles
from typing import List

from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.config import FILE_DIRECTORY
from app.entity import FileMeta, Status



class FileRepository:
    def __init__(self, file_directory: str = FILE_DIRECTORY, db: AsyncSession = None):
        self.file_directory = file_directory
        self.db = db

    async def save_file(self, file_name: str, content: bytes) -> FileMeta:
        file_path = os.path.join(self.file_directory, file_name)
        
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        
        file_size = os.path.getsize(file_path)
        
        file_record = FileMeta(
            filename=file_name,
            filepath=file_path,
            filesize=file_size
        )
        self.db.add(file_record)
        return file_record

    async def delete_file(self, file_name: str) -> None:
        result = await self.db.execute(select(FileMeta).filter(FileMeta.filename == file_name))
        file_record = result.scalars().first()
        
        if not file_record:
            raise FileNotFoundError(f"File {file_name} not found in database.")
        
        file_record.is_delete = True

    async def list_files(self) -> List[FileMeta]:
        result = await self.db.execute(select(FileMeta).filter(FileMeta.is_delete == False).order_by(desc(FileMeta.creation_time)).limit(100))  # 100개 제한
        files = result.scalars().all()

        return files

    # 상태 업데이트
    async def update_status(self, file_name: str, new_status: Status) -> None:
        result = await self.db.execute(select(FileMeta).filter(FileMeta.filename == file_name))
        file_record = result.scalars().first()

        if not file_record:
            raise FileNotFoundError(f"File {file_name} not found in database.")
        
        file_record.status = new_status
        self.db.add(file_record)