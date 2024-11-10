from typing import List, Optional
from sqlalchemy import desc, select
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
import os

from app.entity import DataSet, Status
from app.repositories.file_repository import FileRepository
from app.exceptions import NotFoundException


class DatasetRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.file_repo = FileRepository(db)
    async def save_file(self, file_path: str, content: bytes) -> DataSet:
        file_name = os.path.basename(file_path)
        file_meta = await self.file_repo.save_file(file_path, content)

        result = await self.db.execute(
            select(DataSet).filter_by(filename=file_name)
        )
        dataset = result.scalars().first()

        if dataset:
            dataset.is_delete = False
            dataset.file_meta = file_meta
            dataset.status = Status.READY
        else:
            dataset = DataSet(filename=file_name, file_meta=file_meta)
            self.db.add(dataset)

        await self.db.flush()
        return dataset

    async def delete_file(self, dataset_id: int) -> None:
        result = await self.db.execute(select(DataSet).filter_by(id=dataset_id))
        dataset = result.scalars().first()

        if not dataset:
            raise NotFoundException(f"DataSet with ID '{dataset_id}' not found in database.")
        
        dataset.is_delete = True
        await self.db.flush()

    async def list_files_with_filemeta(
        self,
        last_id: Optional[int] = None,
        limit: int = 10
    ) -> List[DataSet]:
        query = select(DataSet).options(joinedload(DataSet.file_meta)).filter_by(is_delete=False)
        
        if last_id is not None:
            query = query.filter(DataSet.id < last_id)
        
        query = query.order_by(desc(DataSet.id)).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def list_files(self) -> List[DataSet]:
        query = select(DataSet).filter_by(is_delete=False)

        result = await self.db.execute(query.order_by(desc(DataSet.id)))
        return result.scalars().all()
    
    async def get_dataset_by_id(self, id: int) -> DataSet:
        result = await self.db.execute(select(DataSet).options(joinedload(DataSet.file_meta)).filter_by(id=id))
        return result.scalars().first()

    async def update_status(self, dataset_id: int, new_status: Status) -> None:
        result = await self.db.execute(select(DataSet).filter_by(id=dataset_id))
        file_record = result.scalars().first()

        if not file_record:
            raise NotFoundException(f"Dataset with ID '{dataset_id}' not found in database.")
        
        file_record.status = new_status
        self.db.add(file_record)
        await self.db.flush()
