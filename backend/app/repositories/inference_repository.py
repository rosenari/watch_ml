from typing import List, Union

from sqlalchemy import desc, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.entity import InferenceFile, Status, FileType
from app.repositories.file_repository import FileRepository
from app.exceptions import NotFoundException
import os



class InferenceRepository:
    def __init__(self, db: AsyncSession = None):
        self.db = db
        self.file_repo = FileRepository(db)

    async def save_original_file(self, file_path: str, content: bytes) -> InferenceFile:
        file_name = os.path.basename(file_path)
        file_type = get_file_type(file_name)
        file_meta = await self.file_repo.save_file(file_path, content)
        result = await self.db.execute(select(InferenceFile).filter(InferenceFile.original_file_name == file_name))
        inference_file = result.scalars().first()

        if inference_file:
            inference_file.is_delete = False
            inference_file.file_type = file_type
            inference_file.original_file = file_meta
            inference_file.generated_file_name = None
            inference_file.generated_file = None
            inference_file.status = Status.READY
        else:
            inference_file = InferenceFile(
                original_file_name=file_name,
                original_file=file_meta,
                file_type=file_type
            )
            self.db.add(inference_file)

        await self.db.flush()
        return inference_file
    
    async def update_generated_file(self, original_file_name: str, generated_file_path: str) -> InferenceFile:
        generated_file_name = os.path.basename(generated_file_path)
        result = await self.db.execute(select(InferenceFile).filter(InferenceFile.original_file_name == original_file_name))
        inference_file = result.scalars().first()

        if not inference_file:
            raise NotFoundException(f"InferenceFile {original_file_name} not found in database.")
        
        inference_file.generated_file_name = generated_file_name
        inference_file.generated_file = await self.file_repo.register_file(generated_file_path)
        await self.db.flush()

        return inference_file

    async def delete_file(self, original_file_name: str) -> None:
        result = await self.db.execute(select(InferenceFile).filter(InferenceFile.original_file_name == original_file_name))
        inference_file = result.scalars().first()
        
        if not inference_file:
            raise NotFoundException(f"InferenceFile {original_file_name} not found in database.")
        
        inference_file.is_delete = True
        await self.db.flush()

    async def get_inference_file_by_name(self, original_file_name) -> InferenceFile:
        result = await self.db.execute(select(InferenceFile).filter(InferenceFile.original_file_name == original_file_name))
        inference_file = result.scalars().first()

        if not inference_file:
            raise NotFoundException(f"InferenceFile {original_file_name} not found in database.")
        
        return inference_file

    # FileMeta Join
    async def list_files_with_filemeta(self) -> List[InferenceFile]:
        result = await self.db.execute(
            select(InferenceFile)
                .options(
                    selectinload(InferenceFile.original_file),
                    selectinload(InferenceFile.generated_file)
                )
                .filter(and_(InferenceFile.is_delete == False))
                .order_by(desc(InferenceFile.id))
        )
        files = result.scalars().all()

        return files
    
    async def list_files(self) -> List[InferenceFile]:
        result = await self.db.execute(
            select(InferenceFile)
            .filter(InferenceFile.is_delete == False)
            .order_by(desc(InferenceFile.id))
        )
        files = result.scalars().all()

        return files

    # 상태 업데이트
    async def update_status(self, original_file_name: str, new_status: Status) -> None:
        result = await self.db.execute(select(InferenceFile).filter(InferenceFile.original_file_name == original_file_name))
        inference_file = result.scalars().first()

        if not inference_file:
            raise FileNotFoundError(f"InferenceFile {original_file_name} not found in database.")
        
        inference_file.status = new_status
        self.db.add(inference_file)
        await self.db.flush()


def get_file_type(file_name: str) -> Union[FileType, None]:
    photo_extensions = {'jpg', 'jpeg', 'png'}
    video_extensions = {'mov', 'mp4', 'avi', 'mkv'}

    extension = os.path.splitext(file_name)[1][1:].lower()

    if extension in photo_extensions:
        return FileType.PHOTO
    elif extension in video_extensions:
        return FileType.VIDEO
    
    raise NotFoundException(f"The file type for '{file_name}' is not supported. Supported types are: {photo_extensions | video_extensions}.")
