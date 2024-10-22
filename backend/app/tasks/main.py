from celery import Celery
from app.config import CELERY_BROKER_URL, CELERY_ARCHIVE_PATH, CELERY_ML_RUNS_PATH, DATASET_DIRECTORY
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


def redis_status_handler(ri_key, status):
    ri = redis.from_url(redis_url)
    ri.set(ri_key, status)
    ri.close()   


async def dataset_status_handler(file_name: str, status: str):
    async for redis_instance in get_redis():
        async for session_instance in get_session():
            dataset_service = DataSetService(redis=redis_instance, session=session_instance, file_directory=DATASET_DIRECTORY)
            await dataset_service.update_status(file_name, status)


async def ml_status_handler(model_name: str, status: str):
    file_name = f"{model_name}.onnx"
    async for redis_instance in get_redis():
        async for session_instance in get_session():
            ml_serivce = MlService(redis=redis_instance, session=session_instance)
            await ml_serivce.update_status(file_name, status)


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


async def create_model(model_name: str, zip_files: list[str]):
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

    create_result = create_yolo_model(model_name, output_dir, ml_runs_path=CELERY_ML_RUNS_PATH, status_handler=redis_status_handler)
    if not create_result:  # AI 모델 생성
        await ml_status_handler(model_name, 'failed')
        return False
    
    await ml_status_handler(model_name, 'complete')
    file_name = f"{model_name}.onnx"
    clear_redis_keys_sync(f"train:{file_name}")
    return True