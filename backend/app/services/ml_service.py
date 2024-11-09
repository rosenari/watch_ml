from typing import List
from fastapi import Depends
from app.database import get_redis, get_session
from app.repositories.ml_repository import MlRepository
from app.dto import AiModelDTO
from app.util import transactional
from app.entity import Status
from app.exceptions import ForbiddenException


class MlService:
    def __init__(self, redis, session):
        self.redis = redis
        self.session = session
        self.repository = MlRepository(db=session)

    @transactional
    async def init_model(self, model_name: str, base_model_name: str = None) -> int:
        model = await self.repository.get_model_by_name(model_name)
        version = 1 if model is None else (model.version if model.status == Status.FAILED else model.version + 1)
        id = await self.register_model(AiModelDTO(
            model_name=model_name, version=version, base_model_name=base_model_name
        ))

        return version

    @transactional
    async def register_model(self, ai_model_dto: AiModelDTO) -> int:
        if ai_model_dto.base_model_name is not None:
            base_model = await self.repository.get_model_by_name(ai_model_dto.base_model_name)
            if base_model.status != Status.COMPLETE:
                raise ForbiddenException(f"Base model '{ai_model_dto.base_model_name}' is not complete and cannot be used.")
        
        new_model = await self.repository.register_model(ai_model_dto)
        return new_model.id
    
    @transactional
    async def update_model(self, ai_model_dto: AiModelDTO) -> str:
        update_model = await self.repository.update_model(ai_model_dto)
        return update_model.modelname

    async def get_model_by_id(self, model_id: int) -> dict:
        model = await self.repository.get_model_by_id_with_filemeta(model_id)

        if model is None:
            return model

        return model.serialize()
    
    async def get_model_by_name(self, model_name: str) -> dict:
        model = await self.repository.get_model_by_name_with_filemeta(model_name)

        if model is None:
            return model

        return model.serialize()

    async def get_model_list(self, last_id: int = None) -> List[dict]:
        models = await self.repository.get_all_models_with_filemeta(last_id=last_id)
        return [model.serialize() for model in models]
    
    async def get_model_status(self) -> List[dict]:
        result = []
        redis_models = await get_running_model_list_from_redis(self.redis, prefix="train:")
        models = await self.repository.get_all_models()

        redis_status_map = {model['model_name']: model['status'] for model in redis_models}

        for model in models:
            status = redis_status_map.get(model.modelname, model.status.value)

            result.append({
                "id": model.id,
                "model_name": model.modelname,
                "status": status
            })

        return result
    
    async def get_model_classes(self, model_id: int) -> List[str]:
        model = await self.repository.get_model_by_id(model_id)
        return model.classes.split(',') if model and model.classes else None

    @transactional
    async def delete_model(self, model_id: int) -> None:
        return await self.repository.delete_model(model_id=model_id)

    @transactional
    async def deploy_model(self, model_id: int, deploy_path: str) -> str:
        model = await self.repository.deploy_model(model_id, deploy_path)
        return model.modelname
    
    @transactional
    async def undeploy_model(self, model_id: int) -> str:
        model = await self.repository.undeploy_model(model_id)
        return model.modelname
    
    @transactional
    async def update_status(self, model_id: str, status: str):
        new_status = Status[status.upper()]

        return await self.repository.update_status(model_id, new_status)
        

async def get_ml_service(redis=Depends(get_redis), session=Depends(get_session)):
    yield MlService(redis, session)


async def get_running_model_list_from_redis(redis, prefix: str = "train:") -> list:
    cursor = "0"
    result = []

    while cursor != 0:
        cursor, keys = await redis.scan(cursor=cursor, match=f"{prefix}*", count=100)
        if keys:
            decoded_keys = [key.decode('utf-8') for key in keys]
            values = await redis.mget(*keys)

            for key, value in zip(decoded_keys, values):
                    result.append({ 'model_name': key.replace(prefix, ""), 'status': value.decode('utf-8') if value else None })

    return result