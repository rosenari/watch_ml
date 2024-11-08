from typing import List
from fastapi import UploadFile, Depends
from app.config import DATASET_DIRECTORY
from app.database import get_redis, get_session
from app.repositories.dataset_repository import DatasetRepository
from app.util import transactional
from app.entity import Status
import os


class DataSetService:
    def __init__(self, redis, session, dir=DATASET_DIRECTORY):
        self.redis = redis
        self.session = session
        self.dir = dir
        self.repository = DatasetRepository(db=session)

    @transactional
    async def upload_file(self, file: UploadFile) -> int:
        """파일을 업로드하고 식별자를 반환합니다."""
        content = await file.read()
        file_path = os.path.join(self.dir, file.filename)
        dataset = await self.repository.save_file(file_path, content)

        return dataset.id

    @transactional
    async def delete_file(self, dataset_id: int) -> bool:
        """파일을 삭제합니다 (is_delete 플래그를 설정)."""
        await self.repository.delete_file(dataset_id=dataset_id)
        return True

    async def get_file_list(self) -> List[dict]:
        """디렉터리 내 모든 파일 목록을 반환합니다."""
        datasets = await self.repository.list_files_with_filemeta()
        return [dataset.serialize() for dataset in datasets]

    async def get_file_status(self) -> List[dict]:
        """디렉터리 내 파일들의 상태를 반환합니다 (디렉터리 제외)."""
        datasets = await self.repository.list_files()
        return [
            {"id": dataset.id, "file_name": dataset.filename, "status": dataset.status.value}
            for dataset in datasets
        ]
    
    async def get_dataset_by_id(self, id: int) -> dict:
        dataset = await self.repository.get_dataset_by_id(id)
        return dataset.serialize()

    @transactional
    async def update_status(self, dataset_id: int, status: str) -> bool:
        """파일 상태를 업데이트합니다."""
        new_status = Status[status.upper()]
        await self.repository.update_status(dataset_id=dataset_id, new_status=new_status)
        return True


async def get_dataset_service(redis=Depends(get_redis), session=Depends(get_session)):
    """DataSetService 인스턴스를 반환합니다."""
    yield DataSetService(redis, session)
