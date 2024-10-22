from typing import List

from sqlalchemy import desc
from sqlalchemy.orm import contains_eager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.config import DATASET_DIRECTORY
from app.entity import DataSet, Status, FileMeta
from app.repositories.file_repository import FileRepository



class DatasetRepository:
    def __init__(self, file_directory: str = DATASET_DIRECTORY, db: AsyncSession = None):
        self.db = db
        self.file_repository = FileRepository(file_directory, db)

    async def save_file(self, file_name: str, content: bytes) -> DataSet:
        file_meta = await self.file_repository.save_file(file_name, content)
        
        dataset = DataSet(
            filename=file_name,
            file_meta=file_meta
        )
        self.db.add(dataset)
        await self.db.flush()
        return dataset

    async def delete_file(self, file_name: str) -> None:
        result = await self.db.execute(select(DataSet).filter(DataSet.filename == file_name))
        dataset = result.scalars().first()
        
        if not dataset:
            raise FileNotFoundError(f"DataSet {file_name} not found in database.")
        
        dataset.is_delete = True
        await self.db.flush()

    # FileMeta Join
    async def list_files_with_filemeta(self) -> List[DataSet]:
        result = await self.db.execute(
            select(DataSet)
            .join(DataSet.file_meta) 
            .options(contains_eager(DataSet.file_meta))
            .filter(DataSet.is_delete == False)
            .order_by(desc(FileMeta.creation_time))
        )
        files = result.scalars().all()

        return files
    
    async def list_files(self) -> List[DataSet]:
        result = await self.db.execute(select(DataSet).filter(DataSet.is_delete == False))
        files = result.scalars().all()

        return files

    # 상태 업데이트
    async def update_status(self, file_name: str, new_status: Status) -> None:
        result = await self.db.execute(select(DataSet).filter(DataSet.filename == file_name))
        file_record = result.scalars().first()

        if not file_record:
            raise FileNotFoundError(f"Dataset {file_name} not found in database.")
        
        file_record.status = new_status
        self.db.add(file_record)
        await self.db.flush()