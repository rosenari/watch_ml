from typing import List
from fastapi import UploadFile, Depends
from app.config import INFERENCE_DIRECTORY
from app.database import get_redis, get_session
from app.repositories.inference_repository import InferenceRepository
from app.util import transactional
from app.entity import Status
import os


class InferenceService:
    def __init__(self, redis, session, dir=INFERENCE_DIRECTORY):
        self.redis = redis
        self.session = session
        self.dir = dir
        self.repository = InferenceRepository(db=session)

    @transactional
    async def upload_file(self, file: UploadFile) -> str:
        """파일을 업로드하고 식별자를 반환합니다."""
        content = await file.read()
        file_path = os.path.join(self.dir, file.filename)
        inference_file = await self.repository.save_original_file(file_path, content)
        return { "original_file_name": inference_file.original_file_name, "id": inference_file.id }
    
    @transactional
    async def update_generated_file(self, inference_file_id: int, generated_file_path: str) -> dict:
        """생성된 파일을 저장하고 업데이트된 InferenceFile 객체를 반환합니다."""
        inference_file = await self.repository.update_generated_file(inference_file_id, generated_file_path)
        return inference_file.serialize()

    @transactional
    async def delete_file(self, inference_file_id: int) -> bool:
        """InferenceFile 객체를 삭제합니다."""
        await self.repository.delete_file(inference_file_id)
        return True
    
    async def get_file_by_id(self, inference_file_id: int) -> dict:
        """ID로 InferenceFile 객체를 조회합니다."""
        inference_file = await self.repository.get_inference_file_by_id(inference_file_id)
        return inference_file.serialize()

    async def get_file_list(self) -> List[dict]:
        """모든 InferenceFile 목록을 반환합니다."""
        inference_files = await self.repository.list_files_with_filemeta()
        return [inference_file.serialize() for inference_file in inference_files]
    
    async def get_file_status(self) -> List[dict]:
        """모든 InferenceFile의 상태를 반환합니다."""
        inference_files = await self.repository.list_files()
        return [
            {
                "id": inference_file.id,
                "original_file_name": inference_file.original_file_name,
                "status": inference_file.status.value
            }
            for inference_file in inference_files
        ]
    
    @transactional
    async def update_status(self, inference_file_id: int, status: str) -> bool:
        """InferenceFile 객체의 상태를 업데이트합니다."""
        new_status = Status[status.upper()]
        await self.repository.update_status(inference_file_id, new_status)
        return True
    
    async def get_file_path(self, file_id: int) -> str:
        """ID로 InferenceFile의 파일 경로를 반환합니다."""
        return await self.repository.get_file_path(file_id)
    

async def get_inference_service(redis=Depends(get_redis), session=Depends(get_session)):
    """InferenceService 인스턴스를 반환합니다."""
    yield InferenceService(redis, session)
