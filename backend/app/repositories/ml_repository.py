from sqlalchemy import desc, and_
from sqlalchemy.orm import contains_eager
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
from app.entity import AiModel, Status, FileMeta
from app.config import MODEL_DIRECTORY
from app.repositories.file_repository import FileRepository


class MlRepository:
    def __init__(self, file_directory: str = MODEL_DIRECTORY, db: AsyncSession = None):
        self.db = db
        self.file_repository = FileRepository(file_directory, db)

    # AI 모델 등록
    async def register_model(self, file_name: str, version: int, file_path: str, map50: float = None, map50_95: float = None, precision: float = None, recall: float = None) -> AiModel:
        result = await self.db.execute(select(AiModel).filter(AiModel.filename == file_name, AiModel.version == version))
        existing_model = result.scalars().first()
        file_meta = await self.file_repository.register_file(file_path)

        if existing_model:
            existing_model.map50 = map50
            existing_model.map50_95 = map50_95
            existing_model.precision = precision
            existing_model.recall = recall
            existing_model.is_delete = False
            existing_model.file_meta = file_meta
            await self.db.flush()
            return existing_model
        else:
            new_model = AiModel(
                filename=file_name,
                version=version,
                map50=map50,
                map50_95=map50_95,
                precision=precision,
                recall=recall,
                file_meta=file_meta
            )

            self.db.add(new_model)
            await self.db.flush()
            return new_model

    async def get_model_by_name(self, file_name: str) -> AiModel:
        try:
            result = await self.db.execute(select(AiModel).filter(AiModel.filename == file_name))
            model = result.scalars().one()
            return model
        except NoResultFound:
            return None
        
    async def get_model_by_name_with_filemeta(self, file_name: str) -> AiModel:
        try:
            result = await self.db.execute(
                select(AiModel)
                .join(AiModel.file_meta)
                .options(contains_eager(AiModel.file_meta))
                .filter(and_(AiModel.is_delete == False, AiModel.filename == file_name)))
            model = result.scalars().one()
            return model
        except NoResultFound:
            return None

    async def get_all_models_with_filemeta(self) -> list[AiModel]:
        result = await self.db.execute(
            select(AiModel)
            .join(AiModel.file_meta) 
            .options(contains_eager(AiModel.file_meta))
            .filter(AiModel.is_delete == False)
            .order_by(desc(FileMeta.creation_time))
        )
        models = result.scalars().all()

        return models
    
    async def get_all_models(self) -> list[AiModel]:
        result = await self.db.execute(select(AiModel).filter(AiModel.is_delete == False))
        models = result.scalars().all()

        return models

    async def delete_model(self, file_name: str) -> bool:
        result = await self.db.execute(select(AiModel).filter(AiModel.filename == file_name))
        model = result.scalars().first()
        
        if not model:
            raise FileNotFoundError(f"Model {file_name} not found in database.")
        
        model.is_delete = True
        await self.db.flush()

    # 모델을 배포 상태로 변경
    async def deploy_model(self, file_name: str) -> AiModel:
        result = await self.db.execute(select(AiModel).filter(AiModel.filename == file_name))
        model = result.scalars().first()

        if model:
            model.is_deploy = True
            await self.db.flush()
        return model

    # 상태 업데이트
    async def update_status(self, file_name: str, new_status: Status) -> None:
        result = await self.db.execute(select(AiModel).filter(AiModel.filename == file_name))
        model = result.scalars().first()

        if not model:
            raise ValueError(f"Model {file_name} not found in database.")
        
        model.status = new_status
        self.db.add(model)
        await self.db.flush()