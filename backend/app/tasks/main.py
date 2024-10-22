from celery import Celery
from app.config import CELERY_BROKER_URL, CELERY_ARCHIVE_PATH, CELERY_ML_RUNS_PATH, DATASET_DIRECTORY, MODEL_DIRECTORY
from app.tasks.valid.valid_archive import parse_and_verify_zip
from app.tasks.train.merge_archive import merge_archive_files
from app.tasks.train.create_ml_model import create_yolo_model
from app.services.dataset_service import DataSetService
from app.services.ml_service import MlService
from app.database import get_redis, get_session
import os
import asyncio
import redis
from datetime import datetime


redis_url = CELERY_BROKER_URL
app = Celery('tasks', broker=redis_url)


# set redis key value
def redis_status_handler(ri_key, status):
    ri = redis.from_url(redis_url)
    ri.set(ri_key, status)
    ri.close()   


async def with_service(service_class, file_directory, func, *args, **kwargs):
    async for redis_instance in get_redis():
        async for session_instance in get_session():
            service = service_class(redis=redis_instance, session=session_instance, file_directory=file_directory)
            return await func(service, *args, **kwargs)


# Dataset Task 상태 갱신
async def dataset_status_handler(file_name: str, status: str):
    async def update_status(service: DataSetService):
        await service.update_status(file_name, status)

    await with_service(DataSetService, DATASET_DIRECTORY, update_status)


# Ml Task 상태 갱신
async def ml_status_handler(model_name: str, status: str):
    file_name = f"{model_name}.onnx"

    async def update_status(service: MlService):
        await service.update_status(file_name, status)

    await with_service(MlService, MODEL_DIRECTORY, update_status)


# 생성된 모델을 db에 등록
async def register_model(model_info: dict):
    async def register_model_fn(service: MlService):
        await service.register_model(**model_info)

    await with_service(MlService, MODEL_DIRECTORY, register_model_fn)


# 모델 버전 가져오기
async def get_model_version(file_name: str) -> int:
    async def get_version_fn(service: MlService):
        model = await service.get_model_by_name(file_name)
        return model['version']

    return await with_service(MlService, MODEL_DIRECTORY, get_version_fn)


# 특정 패턴의 키를 redis 에서 삭제
def clear_redis_keys_sync(key_pattern: str):
    ri = redis.from_url(redis_url)
    
    cursor = "0"
    while cursor != 0:
        cursor, keys = ri.scan(cursor=cursor, match=key_pattern, count=100)
        if keys:
            ri.delete(*keys)

    ri.close()


@app.task
def valid_archive_task(file_name):
    return asyncio.run(valid_archive(file_name))


# 아카이브 검사 (디렉터리 및 yaml 내용 체크)
async def valid_archive(file_name):
    zip_path = f"{CELERY_ARCHIVE_PATH}/{file_name}"    
    await dataset_status_handler(file_name, 'running')

    result = parse_and_verify_zip(zip_path)
    status = "complete" if result else "failed"

    await dataset_status_handler(file_name, status)

    return result


@app.task
def create_model_task(model_name: str, zip_files: list[str]):
    return asyncio.run(create_model(model_name, zip_files))


# zip_files를 기반으로 학습하고 생성된 모델 저장
async def create_model(model_name: str, zip_files: list[str]):
    file_name = f"{model_name}.onnx"
    datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")
    output_dir = os.path.join(CELERY_ML_RUNS_PATH, f"{model_name}_{datetime_str}")
    zip_files = [os.path.join(CELERY_ARCHIVE_PATH, zip_file) for zip_file in zip_files]

    if not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    else:
        await ml_status_handler(model_name, 'failed')
        return False

    if not merge_archive_files(zip_files, output_dir):  # 아카이브 병합
        await ml_status_handler(model_name, 'failed')
        return False

    version = await get_model_version(file_name)
    new_version = version + 1
    create_result, model_info = create_yolo_model(  # Yolo 학습 및 모델 생성
        model_name=model_name, 
        version=new_version, 
        output_dir=output_dir, 
        ml_runs_path=CELERY_ML_RUNS_PATH, 
        status_handler=redis_status_handler
        )
    if not create_result:
        await ml_status_handler(model_name, 'failed')
        return False
    
    await register_model(model_info)  # 모델 정보를 등록합니다.
    await ml_status_handler(model_name, 'complete')  # Task 완료 처리 (db)
    
    clear_redis_keys_sync(f"train:{file_name}")  # Progress 제거 (redis)
    return True