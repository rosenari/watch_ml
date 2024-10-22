from typing import List
from fastapi import Depends
from app.database import get_redis, get_session
from app.repositories.ml_repository import MlRepository
from app.util import transactional
from app.config import MODEL_DIRECTORY
from app.entity import Status


class MlService:
    def __init__(self, redis, session, file_directory=MODEL_DIRECTORY):
        self.redis = redis
        self.session = session
        self.repository = MlRepository(file_directory=file_directory, db=session)


    @transactional
    async def init_model(self, model_name: str) -> int:
        file_name = f"{model_name}.onnx"
        model = await self.get_model_by_name(file_name)
        version = 1 if model is None else model['version'] + 1
        await self.register_model(file_name, version)

        return version


    @transactional
    async def register_model(self, file_name: str, version: int = 1, file_path: str = None, map50: float = None, map50_95: float = None, precision: float = None, recall: float = None) -> str:
        new_model = await self.repository.register_model(
            file_name=file_name,
            version=version,
            file_path=file_path,
            map50=map50,
            map50_95=map50_95,
            precision=precision,
            recall=recall
        )
        return new_model.filename
    
    @transactional
    async def update_model(self, file_name: str, version: int = None, file_path: str = None, map50: float = None, map50_95: float = None, precision: float = None, recall: float = None) -> str:
        update_model = await self.repository.update_model(
            file_name=file_name,
            version=version,
            file_path=file_path,
            map50=map50,
            map50_95=map50_95,
            precision=precision,
            recall=recall
        )
        return update_model.filename

    async def get_model_by_name(self, file_name: str) -> dict:
        model = await self.repository.get_model_by_name_with_filemeta(file_name)

        if model is None:
            return model

        return {
            "file_name": model.filename, 
            "version": model.version,
            "file_path": model.file_meta.filepath,
            "map50": model.map50, 
            "map50_95": model.map50_95, 
            "precision": model.precision, 
            "recall": model.recall,
            "status": model.status.value
            }

    async def get_model_list(self) -> List[dict]:
        models = await self.repository.get_all_models_with_filemeta()
        return [{
            "file_name": model.filename,
            "version": model.version,
            "file_path": model.file_meta.filepath,
            "file_size": model.file_meta.filesize,
            "map50": model.map50, 
            "map50_95": model.map50_95, 
            "precision": model.precision, 
            "recall": model.recall,
            "status": model.status.value,
            "creation_date": model.file_meta.creation_time.strftime('%Y-%m-%d %H:%M:%S')
            } for model in models]
    
    async def get_model_status(self) -> List[dict]:
        result = []
        redis_models = await get_running_model_list_from_redis(self.redis, prefix="train:")
        models = await self.repository.get_all_models()

        redis_status_map = {model['file_name']: model['status'] for model in redis_models}

        for model in models:
            status = redis_status_map.get(model.filename, model.status.value)

            result.append({
                "file_name": model.filename,
                "status": status
            })

        return result


    @transactional
    async def delete_model(self, file_name: str) -> None:
        return await self.repository.delete_model(file_name)

    @transactional
    async def deploy_model(self, file_name: str) -> str:
        model = await self.repository.deploy_model(file_name)
        return model.filename
    
    @transactional
    async def update_status(self, file_name: str, status: str):
        try:
            new_status = Status[status.upper()]
        except KeyError:
            raise ValueError(f"Invalid status: {status}")

        return await self.repository.update_status(file_name, new_status)
        

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
                    result.append({ 'file_name': key.replace(prefix, ""), 'status': value.decode('utf-8') if value else None })

    return result