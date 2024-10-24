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
    async def register_model(self, file_name: str, version: int = 1, file_path: str = None, map50: float = None, map50_95: float = None, precision: float = None, recall: float = None) -> AiModel:
        result = await self.db.execute(select(AiModel).filter(AiModel.filename == file_name))
        model = result.scalars().first()
        file_meta = None

        if file_path is not None:
            file_meta = await self.file_repository.register_file(file_path)

        if model is not None:
            model.version = version
            model.map50 = map50
            model.map50_95 =  map50_95
            model.precision = precision
            model.recall = recall
            model.file_meta = file_meta
            model.status = Status.PENDING
        else:
            model = AiModel(
                filename=file_name,
                version=version,
                map50=map50,
                map50_95=map50_95,
                precision=precision,
                recall=recall,
                file_meta=file_meta,
                status=Status.PENDING
            )
            self.db.add(model)
        await self.db.flush()
        return model
    
    async def update_model(self, file_name: str, version: int = None, file_path: str = None, map50: float = None, map50_95: float = None, precision: float = None, recall: float = None, classes: list = None) -> AiModel:
        result = await self.db.execute(select(AiModel).filter(AiModel.filename == file_name))
        model = result.scalars().first()

        if not model:
            raise FileNotFoundError(f"Model {file_name} not found in database.")
        
        model.is_delete = False
        
        if version is not None:
            model.version = version
        
        if file_path is not None:
            file_meta = await self.file_repository.register_file(file_path)
            model.file_meta = file_meta
        
        if map50 is not None:
            model.map50 = map50
        
        if map50_95 is not None:
            model.map50_95 = map50_95
        
        if precision is not None:
            model.precision = precision
        
        if recall is not None:
            model.recall = recall

        if classes is not None and len(classes) > 0:
            model.classes = ','.join(classes)

        await self.db.flush()  # 데이터베이스에 변경 사항을 반영
        return model

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
    
    async def undeploy_model(self, file_name: str) -> AiModel:
        result = await self.db.execute(select(AiModel).filter(AiModel.filename == file_name))
        model = result.scalars().first()

        if model:
            model.is_deploy = False
            await self.db.flush()
        return model

    # 상태 업데이트
    async def update_status(self, file_name: str, new_status: Status) -> None:
        result = await self.db.execute(select(AiModel).filter(AiModel.filename == file_name))
        model = result.scalars().first()

        if not model:
            raise ValueError(f"Model {file_name} not found in database.")
        
        model.status = new_status
        await self.db.flush()