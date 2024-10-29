from typing import List
from fastapi import UploadFile, Depends
from app.config import INFERENCE_DIRECTORY
from app.database import get_redis, get_session
from app.repositories.inference_repository import InferenceRepository
from app.util import transactional
from app.entity import Status
import os


class InferenceService:
    def __init__(self, redis, session, dir = INFERENCE_DIRECTORY):
        self.redis = redis
        self.session = session
        self.dir = dir
        self.repository = InferenceRepository(db=session)

    @transactional
    async def upload_file(self, file: UploadFile) -> str:
        content = await file.read()
        file_path = os.path.join(self.dir, file.filename)
        inference_file = await self.repository.save_original_file(file_path, content)
        return inference_file.original_file_name

    @transactional
    async def delete_file(self, original_file_name: str) -> None:
        return await self.repository.delete_file(original_file_name)

    async def get_file_list(self) -> List[dict]:
        result = []
        inference_files = await self.repository.list_files_with_filemeta()
        for inference_file in inference_files:
            result.append(inference_file.serialize())
        return result
    
    async def get_file_status(self) -> List[dict]:
        result = []
        inference_files = await self.repository.list_files()
        for inference_file in inference_files:
            result.append({
                "original_file_name": inference_file.original_file_name,
                "status": inference_file.status.value
            })

        return result
    
    @transactional
    async def update_status(self, original_file_name: str, status: str):
        new_status = Status[status.upper()]

        return await self.repository.update_status(original_file_name, new_status)
    

async def get_inference_service(redis = Depends(get_redis), session = Depends(get_session)):
    yield InferenceService(redis, session)
