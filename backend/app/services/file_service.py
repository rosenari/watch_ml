from typing import List
from fastapi import UploadFile
from app.repositories.file_repository import FileRepository


class FileService:
    def __init__(self, repository: FileRepository):
        self.repository = repository

    async def upload_file(self, file: UploadFile) -> str:
        content = await file.read()
        return await self.repository.save_file(file.filename, content)

    def delete_file(self, file_name: str) -> None:
        return self.repository.delete_file(file_name)

    def get_file_list(self) -> List[dict]:
        return self.repository.list_files()