from sqlalchemy import desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.exc import NoResultFound
from app.entity import AiModel, Status


class MlRepository:
    def __init__(self, db: AsyncSession = None):
        self.db = db

    # AI 모델 등록
    async def register_model(self, model_name: str, file_path: str, map50: float = None, map50_95: float = None, precision: float = None, recall: float = None) -> AiModel:
        stmt = select(AiModel).where(AiModel.modelname == model_name).order_by(desc(AiModel.version))
        existing_model = await self.db.execute(stmt)
        latest_model = existing_model.scalars().first()

        new_version = latest_model.version + 1 if latest_model else 1

        new_model = AiModel(
            modelname=model_name,
            version=new_version,
            filepath=file_path,
            map50=map50,
            map50_95=map50_95,
            precision=precision,
            recall=recall
        )

        self.db.add(new_model)
        return new_model

    async def get_model_by_name(self, model_name: str) -> AiModel:
        try:
            result = await self.db.execute(select(AiModel).filter(AiModel.modelname == model_name))
            model = result.scalars().one()
            return model
        except NoResultFound:
            return None

    async def get_all_models(self) -> list[AiModel]:
        result = await self.db.execute(select(AiModel).filter(AiModel.is_delete == False).order_by(desc(AiModel.creation_time)).limit(100))
        models = result.scalars().all()
        return models

    async def delete_model(self, model_id: int) -> bool:
        model = await self.db.get(AiModel, model_id)
        if not model:
            raise FileNotFoundError("AiModel not found in database.")

        model.is_delete = True

    # 모델을 배포 상태로 변경
    async def deploy_model(self, model_id: int) -> AiModel:
        model = await self.db.get(AiModel, model_id)
        if model:
            model.is_deploy = True
        return model

    # 상태 업데이트
    async def update_status(self, model_name: str, new_status: Status) -> None:
        result = await self.db.execute(select(AiModel).filter(AiModel.modelname == model_name))
        ai_model = result.scalars().first()

        if not ai_model:
            raise ValueError(f"Model {model_name} not found in database.")
        
        ai_model.status = new_status
        self.db.add(ai_model)