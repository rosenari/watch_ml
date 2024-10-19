import os
import aiofiles
from typing import List, Dict

from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.config import FILE_DIRECTORY
from app.entity import FileMeta
from app.util import format_file_size



class FileRepository:
    def __init__(self, file_directory: str = FILE_DIRECTORY, db: AsyncSession = None):
        self.file_directory = file_directory
        self.db = db

    async def save_file(self, file_name: str, content: bytes) -> str:
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
        await self.db.commit()
        return file_name

    async def delete_file(self, file_name: str) -> None:
        result = await self.db.execute(select(FileMeta).filter(FileMeta.filename == file_name))
        file_record = result.scalars().first()
        
        if not file_record:
            raise FileNotFoundError("File not found in database.")
        
        file_record.is_delete = True
        await self.db.commit()

    async def list_files(self) -> List[Dict[str, str]]:
        file_list = []

        result = await self.db.execute(select(FileMeta).filter(FileMeta.is_delete == False).order_by(desc(FileMeta.creation_time)).limit(100))  # 100개 제한
        files = result.scalars().all()
        
        for file in files:
            formatted_size = format_file_size(file.filesize)

            file_list.append({
                "file_name": file.filename,
                "creation_date": file.creation_time.strftime('%Y-%m-%d %H:%M:%S'),
                "file_size": formatted_size
            })
        return file_list
