from sqlalchemy import desc, and_
from sqlalchemy.orm import contains_eager, selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
from app.entity import AiModel, Status, FileMeta
from app.config import MODEL_DIRECTORY
from app.repositories.file_repository import FileRepository
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class ModelInfo:
    model_name: str
    base_model_name: str = None
    version: int = 1
    model_path: str = None
    deploy_path: str = None
    map50: Optional[float] = None
    map50_95: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    classes: Optional[List[str]] = None


class MlRepository:
    def __init__(self, file_directory: str = MODEL_DIRECTORY, db: AsyncSession = None):
        self.db = db
        self.file_repository = FileRepository(file_directory, db)

    # AI 모델 등록
    async def register_model(self, model_info: ModelInfo) -> AiModel:
        model = await self.get_model_by_name(model_info.model_name)

        base_model = await self.get_model_by_name(model_info.base_model_name) if model_info.base_model_name else None
        model_file = await self.file_repository.register_file(model_info.model_path) if model_info.model_path else None
        deploy_file = await self.file_repository.register_file(model_info.deploy_path) if model_info.deploy_path else None
        
        if model is None:
            # 새로운 모델 생성
            model = AiModel(modelname=model_info.model_name, status=Status.PENDING)
            self.db.add(model)

        await self._update_model_attributes(model, model_info, base_model, model_file, deploy_file)
        await self.db.flush()
        return model
    
    # AI 모델 업데이트
    async def update_model(self, model_info: ModelInfo) -> AiModel:
        model = await self.get_model_by_name(model_info.model_name)
        if model is None:
            raise FileNotFoundError(f"Model {model_info.model_name} not found in database.")

        model.is_delete = False
        model.is_deploy = False
        base_model = await self.get_model_by_name(model_info.base_model_name) if model_info.base_model_name else None
        model_file = await self.file_repository.register_file(model_info.model_path) if model_info.model_path else None
        deploy_file = await self.file_repository.register_file(model_info.deploy_path) if model_info.deploy_path else None

        await self._update_model_attributes(model, model_info, base_model, model_file, deploy_file)
        await self.db.flush()
        return model
    
    async def _update_model_attributes(self, model: AiModel, model_info: ModelInfo, base_model: AiModel, model_file: Optional[FileMeta] = None, deploy_file: Optional[FileMeta] = None):
        model.version = model_info.version or model.version
        model.map50 = model_info.map50 or model.map50
        model.map50_95 = model_info.map50_95 or model.map50_95
        model.precision = model_info.precision or model.precision
        model.recall = model_info.recall or model.recall
        model.classes = ','.join(model_info.classes) if model_info.classes else model.classes
        model.base_model = base_model
        model.model_file = model_file or model.model_file
        model.deploy_file = deploy_file or model.deploy_file
        model.is_deploy = False
        model.is_delete = False
        model.status = Status.PENDING

    # 모델 정보 가져오기
    async def get_model_by_name(self, model_name: str) -> AiModel:
        try:
            result = await self.db.execute(select(AiModel).filter(AiModel.modelname == model_name))
            model = result.scalars().one()
            return model
        except NoResultFound:
            return None
        
    # 모델 정보 가져오기 (연관 테이블도)
    async def get_model_by_name_with_filemeta(self, model_name: str) -> AiModel:
        try:
            result = await self.db.execute(
                select(AiModel)
                .options(
                    selectinload(AiModel.model_file),
                    selectinload(AiModel.deploy_file),
                    selectinload(AiModel.base_model),
                )
                .filter(and_(AiModel.is_delete == False, AiModel.modelname == model_name))
            )
            model = result.scalars().one()
            return model
        except NoResultFound:
            return None
        
    # 모든 모델 정보 가져오기 
    async def get_all_models(self) -> list[AiModel]:
        result = await self.db.execute(select(AiModel).filter(AiModel.is_delete == False))
        models = result.scalars().all()

        return models

    # 모든 모델 정보 가져오기 (연관 테이블도)
    async def get_all_models_with_filemeta(self) -> list[AiModel]:
        result = await self.db.execute(
        select(AiModel)
        .options(
            selectinload(AiModel.model_file),
            selectinload(AiModel.deploy_file),
            selectinload(AiModel.base_model)
        )
        .filter(AiModel.is_delete == False)
        .order_by(desc(FileMeta.creation_time))
        )
        models = result.scalars().all()

        return models

    # 모델 삭제
    async def delete_model(self, model_name: str) -> bool:
        result = await self.db.execute(select(AiModel).filter(AiModel.modelname == model_name))
        model = result.scalars().first()
        
        if not model:
            raise FileNotFoundError(f"Model {model_name} not found in database.")
        
        model.is_delete = True
        await self.db.flush()

    # 모델을 배포 상태로 변경
    async def deploy_model(self, model_name: str) -> AiModel:
        result = await self.db.execute(select(AiModel).filter(AiModel.modelname == model_name))
        model = result.scalars().first()

        if model:
            model.is_deploy = True
            await self.db.flush()
        return model
    
    # 모델을 미배포 상태로 변경
    async def undeploy_model(self, model_name: str) -> AiModel:
        result = await self.db.execute(select(AiModel).filter(AiModel.modelname == model_name))
        model = result.scalars().first()

        if model:
            model.is_deploy = False
            await self.db.flush()
        return model

    # 모델 상태 업데이트
    async def update_status(self, model_name: str, new_status: Status) -> None:
        result = await self.db.execute(select(AiModel).filter(AiModel.modelname == model_name))
        model = result.scalars().first()

        if not model:
            raise ValueError(f"Model {model_name} not found in database.")
        
        model.status = new_status
        await self.db.flush()