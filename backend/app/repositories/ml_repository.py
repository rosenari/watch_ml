from sqlalchemy import desc, and_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
from app.database import get_session
from app.entity import AiModel, Status, FileMeta
from app.repositories.file_repository import FileRepository
from app.dto import AiModelDTO
from typing import Optional
from app.config import YOLO_CLASS_LIST, MODEL_DIRECTORY, FASHION_MODEL_CLASS_LIST


class MlRepository:
    def __init__(self, db: AsyncSession = None):
        self.db = db
        self.file_repo = FileRepository(db)

    # AI 모델 등록
    async def register_model(self, ai_model_dto: AiModelDTO) -> AiModel:
        model = await self.get_model_by_name(ai_model_dto.model_name)

        base_model = await self.get_model_by_name(ai_model_dto.base_model_name) if ai_model_dto.base_model_name else None
        model_file = await self.file_repo.register_file(ai_model_dto.model_path) if ai_model_dto.model_path else None
        deploy_file = await self.file_repo.register_file(ai_model_dto.deploy_path) if ai_model_dto.deploy_path else None
        
        if model is None:
            # 새로운 모델 생성
            model = AiModel(modelname=ai_model_dto.model_name, status=Status.PENDING)
            self.db.add(model)

        await self._update_model_attributes(model, ai_model_dto, base_model, model_file, deploy_file)
        await self.db.flush()
        return model
    
    # AI 모델 업데이트
    async def update_model(self, ai_model_dto: AiModelDTO) -> AiModel:
        model = await self.get_model_by_name(ai_model_dto.model_name)
        if model is None:
            raise FileNotFoundError(f"Model {ai_model_dto.model_name} not found in database.")

        model.is_delete = False
        model.is_deploy = False
        base_model = await self.get_model_by_name(ai_model_dto.base_model_name) if ai_model_dto.base_model_name else None
        model_file = await self.file_repo.register_file(ai_model_dto.model_path) if ai_model_dto.model_path else None
        deploy_file = await self.file_repo.register_file(ai_model_dto.deploy_path) if ai_model_dto.deploy_path else None

        await self._update_model_attributes(model, ai_model_dto, base_model, model_file, deploy_file)
        await self.db.flush()
        return model
    
    async def _update_model_attributes(self, model: AiModel, ai_model_dto: AiModelDTO, base_model: AiModel = None, model_file: Optional[FileMeta] = None, deploy_file: Optional[FileMeta] = None):
        model.version = ai_model_dto.version or model.version
        model.map50 = ai_model_dto.map50 or model.map50
        model.map50_95 = ai_model_dto.map50_95 or model.map50_95
        model.precision = ai_model_dto.precision or model.precision
        model.recall = ai_model_dto.recall or model.recall
        model.classes = ','.join(ai_model_dto.classes) if ai_model_dto.classes else model.classes
        model.base_model = base_model
        model.is_deploy = False
        model.is_delete = False
        model.status = Status.PENDING

        if model_file is not None:
            model.model_file = model_file
        if deploy_file is not None:
            model.deploy_file = deploy_file

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
                    selectinload(AiModel.base_model).selectinload(AiModel.model_file),
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
            selectinload(AiModel.base_model).selectinload(AiModel.model_file)
        )
        .filter(AiModel.is_delete == False)
        .order_by(desc(AiModel.id))
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
    async def deploy_model(self, model_name: str, deploy_path: str) -> AiModel:
        result = await self.db.execute(select(AiModel).filter(AiModel.modelname == model_name))
        model = result.scalars().first()

        if model:
            deploy_file = await self.file_repo.register_file(deploy_path)
            model.is_deploy = True
            model.deploy_file = deploy_file
            await self.db.flush()
        return model
    
    # 모델을 미배포 상태로 변경
    async def undeploy_model(self, model_name: str) -> AiModel:
        result = await self.db.execute(select(AiModel).filter(AiModel.modelname == model_name))
        model = result.scalars().first()

        if model:
            model.is_deploy = False
            model.deploy_file = None
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


async def create_base_model():
    async for session_instance in get_session():
        try:
            ml_repo = MlRepository(session_instance)
            base_model_list = [
                {
                    "model_name": "yolov10s",
                    "model_path": "yolov10s.pt",
                    "classes": YOLO_CLASS_LIST,
                },
                {
                    "model_name": "yolov10n",
                    "model_path": "yolov10n.pt",
                    "classes": YOLO_CLASS_LIST,
                },
                {
                    "model_name": "fashion_model",
                    "model_path": f"{MODEL_DIRECTORY}/fashion_model/1/best.pt",
                    "classes": FASHION_MODEL_CLASS_LIST
                }
            ]
            for base_model in base_model_list:
                await ml_repo.register_model(AiModelDTO(
                    model_name=base_model['model_name'],
                    version=1,
                    model_path=base_model['model_path'],
                    classes=base_model['classes']
                ))
            await session_instance.commit()
        except Exception as e:
            await session_instance.rollback()
            raise e  
        finally:
            await session_instance.close()