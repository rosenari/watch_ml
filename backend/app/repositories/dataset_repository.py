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

    async def get_parent_dataset(self, parent_id: Optional[int]) -> Optional[DataSet]:
        if parent_id is not None:
            result = await self.db.execute(select(DataSet).filter_by(id=parent_id))
            parent_dir = result.scalars().first()
            if not parent_dir:
                raise NotFoundException(f"Parent directory with ID '{parent_id}' not found.")
            return parent_dir
        return None

    async def create_dir(self, dir_name: str, parent_id: Optional[int] = None) -> DataSet:
        parent_dir = await self.get_parent_dataset(parent_id)
        dataset = DataSet(filename=dir_name, parent_dataset=parent_dir)

        self.db.add(dataset)
        await self.db.flush()
        return dataset

    async def save_file(self, file_path: str, content: bytes, parent_id: Optional[int] = None) -> DataSet:
        file_name = os.path.basename(file_path)
        file_meta = await self.file_repo.save_file(file_path, content)
        parent_dir = await self.get_parent_dataset(parent_id)

        result = await self.db.execute(
            select(DataSet).filter_by(filename=file_name, parent_dataset_id=parent_dir.id if parent_dir else None)
        )
        dataset = result.scalars().first()

        if dataset:
            dataset.is_delete = False
            dataset.file_meta = file_meta
            dataset.status = Status.READY
        else:
            dataset = DataSet(filename=file_name, file_meta=file_meta, parent_dataset=parent_dir)
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

    async def list_files_with_filemeta(self, parent_id: Optional[int] = None) -> List[DataSet]:
        query = select(DataSet).options(joinedload(DataSet.file_meta)).filter_by(is_delete=False)

        if parent_id is not None:
            query = query.filter_by(parent_dataset_id=parent_id)
        else:
            query = query.filter_by(parent_dataset_id=None)

        result = await self.db.execute(query.order_by(desc(DataSet.id)))
        return result.scalars().all()

    async def list_files(self, parent_id: Optional[int] = None) -> List[DataSet]:
        query = select(DataSet).filter_by(is_delete=False)

        if parent_id is not None:
            query = query.filter_by(parent_dataset_id=parent_id)
        else:
            query = query.filter_by(parent_dataset_id=None)

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
