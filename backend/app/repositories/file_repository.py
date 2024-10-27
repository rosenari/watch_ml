import os
import aiofiles

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.entity import FileMeta



class FileRepository:
    def __init__(self, db: AsyncSession = None):
        self.db = db

    async def save_file(self, file_path: str, content: bytes) -> FileMeta:
        file_meta = await self._get_existing_file_meta(file_path)

        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)

        file_size = os.path.getsize(file_path)

        if file_meta:
            file_meta.filesize = file_size
        else:
            file_meta = FileMeta(
                filepath=file_path,
                filesize=file_size
            )
            self.db.add(file_meta)

        await self.db.flush()
        return file_meta

    async def register_file(self, file_path: str) -> FileMeta:
        file_size = os.path.getsize(file_path)
        file_meta = await self._get_existing_file_meta(file_path)

        if file_meta:
            file_meta.filesize = file_size
        else:
            file_meta = FileMeta(
                filepath=file_path,
                filesize=file_size
            )
            self.db.add(file_meta)

        await self.db.flush()
        return file_meta

    async def get_file(self, file_path: str) -> FileMeta:
        result = await self.db.execute(select(FileMeta).filter(FileMeta.filepath == file_path))
        file_meta = result.scalars().first()

        if not file_meta:
            raise FileNotFoundError(f"File {file_path} not found in database.")

        return file_meta
    
    async def _get_existing_file_meta(self, file_path: str) -> FileMeta:
        result = await self.db.execute(select(FileMeta).filter(FileMeta.filepath == file_path))
        return result.scalars().first()