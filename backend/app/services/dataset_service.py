from typing import List
from fastapi import UploadFile, Depends
from app.config import DATASET_DIRECTORY
from app.database import get_redis, get_session
from app.repositories.dataset_repository import DatasetRepository
from app.util import transactional, format_file_size
from app.entity import Status


class DataSetService:
    def __init__(self, redis, session, file_directory=DATASET_DIRECTORY):
        self.redis = redis
        self.session = session
        self.repository = DatasetRepository(file_directory=file_directory, db=session)

    @transactional
    async def upload_file(self, file: UploadFile) -> str:
        content = await file.read()
        dataset = await self.repository.save_file(file.filename, content)
        return dataset.filename

    @transactional
    async def delete_file(self, file_name: str) -> None:
        return await self.repository.delete_file(file_name)

    async def get_file_list(self) -> List[dict]:
        result = []
        datasets = await self.repository.list_files_with_filemeta()
        for dataset in datasets:
            formatted_size = format_file_size(dataset.file_meta.filesize)

            result.append({
                "file_name": dataset.filename,
                "creation_date": dataset.file_meta.creation_time.strftime('%Y-%m-%d %H:%M:%S'),
                "file_size": formatted_size,
                "status": dataset.status.value
            })
        return result
    
    async def get_file_status(self) -> List[dict]:
        result = []
        datasets = await self.repository.list_files()
        for dataset in datasets:

            result.append({
                "file_name": dataset.filename,
                "status": dataset.status.value
            })

        return result
    
    @transactional
    async def update_status(self, file_name: str, status: str):
        try:
            new_status = Status[status.upper()]
        except KeyError:
            raise ValueError(f"Invalid status: {status}")

        return await self.repository.update_status(file_name, new_status)
    

async def get_dataset_service(redis = Depends(get_redis), session = Depends(get_session)):
    yield DataSetService(redis, session)
