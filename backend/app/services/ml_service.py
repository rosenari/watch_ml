from typing import List
from fastapi import Depends
from app.database import get_redis, get_session
from app.repositories.ml_repository import MlRepository
from app.util import transactional
from app.entity import Status


class MlService:
    def __init__(self, redis, session):
        self.redis = redis
        self.session = session
        self.repository = MlRepository(db=session)

    @transactional
    async def register_model(self, modelname: str, filepath: str, map50: float = None, map50_95: float = None, precision: float = None, recall: float = None) -> str:
        new_model = await self.repository.register_model(
            modelname=modelname,
            filepath=filepath,
            map50=map50,
            map50_95=map50_95,
            precision=precision,
            recall=recall
        )
        return new_model.modelname

    async def get_model_by_name(self, modelname: str) -> dict:
        model = await self.repository.get_model_by_name(modelname)
        return {
            "model_name": model.modelname, 
            "map50": model.map50, 
            "map50_95": model.map50_95, 
            "precision": model.precision, 
            "recall": model.recall,
            "status": model.status.value
            }

    async def get_all_models(self) -> List[dict]:
        models = await self.repository.get_all_models()
        return [{
            "model_name": model.modelname,
            "map50": model.map50, 
            "map50_95": model.map50_95, 
            "precision": model.precision, 
            "recall": model.recall,
            "status": model.status.value
            } for model in models]

    @transactional
    async def delete_model(self, model_id: int) -> None:
        return await self.repository.delete_model(model_id)

    @transactional
    async def deploy_model(self, model_id: int) -> str:
        model = await self.repository.deploy_model(model_id)
        return model.modelname
    
    # training 중인 model 리스트 출력 (pending, running)
    async def get_train_model_list(self) -> List[dict]:
        return []
    
    @transactional
    async def update_status(self, model_name: str, status: str):
        try:
            new_status = Status[status.upper()]
        except KeyError:
            raise ValueError(f"Invalid status: {status}")

        return await self.repository.update_status(model_name, new_status)
        

async def get_ml_service(redis=Depends(get_redis), session=Depends(get_session)):
    yield MlService(redis, session)