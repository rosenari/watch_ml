from typing import List, Union
from sqlalchemy import desc
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.entity import InferenceFile, Status, FileType
from app.repositories.file_repository import FileRepository
from app.exceptions import NotFoundException
from app.config import PHOTO_EXTENSIONS, VIDEO_EXTENSIONS
import os


class InferenceRepository:
    def __init__(self, db: AsyncSession = None):
        self.db = db
        self.file_repo = FileRepository(db)

    async def save_original_file(self, file_path: str, content: bytes) -> InferenceFile:
        """원본 파일을 저장하고 InferenceFile 객체를 반환합니다."""
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

    async def update_generated_file(self, inference_file_id: int, generated_file_path: str) -> InferenceFile:
        """생성된 파일을 저장하고 InferenceFile 객체를 업데이트합니다."""
        generated_file_name = os.path.basename(generated_file_path)
        
        result = await self.db.execute(
            select(InferenceFile)
            .options(
                joinedload(InferenceFile.original_file),
                joinedload(InferenceFile.generated_file)
            )
            .filter(InferenceFile.id == inference_file_id)
        )
        inference_file = result.scalars().first()

        if not inference_file:
            raise NotFoundException(f"InferenceFile with ID '{inference_file_id}' not found in database.")
        
        inference_file.generated_file_name = generated_file_name
        inference_file.generated_file = await self.file_repo.register_file(generated_file_path)
        await self.db.flush()

        return inference_file

    async def delete_file(self, inference_file_id: int) -> None:
        """InferenceFile 객체를 삭제합니다 (is_delete 플래그 설정)."""
        result = await self.db.execute(select(InferenceFile).filter(InferenceFile.id == inference_file_id))
        inference_file = result.scalars().first()
        
        if not inference_file:
            raise NotFoundException(f"InferenceFile with ID '{inference_file_id}' not found in database.")
        
        inference_file.is_delete = True
        await self.db.flush()

    async def get_inference_file_by_id(self, inference_file_id: int) -> InferenceFile:
        """InferenceFile 객체를 ID로 조회합니다."""
        result = await self.db.execute(
            select(InferenceFile)
            .options(
                joinedload(InferenceFile.original_file),
                joinedload(InferenceFile.generated_file)
            )
            .filter(InferenceFile.id == inference_file_id)
        )
        inference_file = result.scalars().first()

        if not inference_file:
            raise NotFoundException(f"InferenceFile with ID '{inference_file_id}' not found in database.")
        
        return inference_file

    # FileMeta Join
    async def list_files_with_filemeta(self) -> List[InferenceFile]:
        """file_meta 정보를 포함한 InferenceFile 목록을 반환합니다."""
        result = await self.db.execute(
            select(InferenceFile)
            .options(
                joinedload(InferenceFile.original_file),
                joinedload(InferenceFile.generated_file)
            )
            .filter(InferenceFile.is_delete == False)
            .order_by(desc(InferenceFile.id))
        )
        return result.scalars().all()
    
    async def list_files(self) -> List[InferenceFile]:
        """삭제되지 않은 InferenceFile 목록을 반환합니다."""
        result = await self.db.execute(
            select(InferenceFile)
            .filter(InferenceFile.is_delete == False)
            .order_by(desc(InferenceFile.id))
        )
        return result.scalars().all()

    async def update_status(self, inference_file_id: int, new_status: Status) -> None:
        """InferenceFile 객체의 상태를 업데이트합니다."""
        result = await self.db.execute(select(InferenceFile).filter(InferenceFile.id == inference_file_id))
        inference_file = result.scalars().first()

        if not inference_file:
            raise NotFoundException(f"InferenceFile with ID '{inference_file_id}' not found in database.")
        
        inference_file.status = new_status
        await self.db.flush()

    async def get_file_path(self, file_id: int) -> str:
        result = await self.db.execute(
            select(InferenceFile)
            .options(
                joinedload(InferenceFile.original_file),
                joinedload(InferenceFile.generated_file)
            )
            .where(
                (InferenceFile.original_file_id == file_id) |
                (InferenceFile.generated_file_id == file_id)
            )
        )
        inference_file = result.scalars().first()

        if inference_file:
            if inference_file.original_file and inference_file.original_file.id == file_id:
                return inference_file.original_file.filepath
            elif inference_file.generated_file and inference_file.generated_file.id == file_id:
                return inference_file.generated_file.filepath

        raise NotFoundException(f"File with id {file_id} not found in both original and generated files.")



def get_file_type(file_name: str) -> Union[FileType, None]:
    """파일 확장자를 기반으로 파일 유형을 반환합니다."""
    photo_extensions = PHOTO_EXTENSIONS
    video_extensions = VIDEO_EXTENSIONS

    extension = file_name.rsplit(".", 1)[-1].lower()

    if extension in photo_extensions:
        return FileType.PHOTO
    elif extension in video_extensions:
        return FileType.VIDEO
    
    raise NotFoundException(f"The file type for '{file_name}' is not supported. Supported types are: {photo_extensions | video_extensions}.")
