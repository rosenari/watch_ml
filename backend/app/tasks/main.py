from celery import Celery
from app.config import CELERY_BROKER_URL, CELERY_ARCHIVE_PATH, CELERY_ML_RUNS_PATH, DATASET_DIRECTORY, MODEL_DIRECTORY, MODEL_REPOSITORY
from app.tasks.valid.valid_archive import parse_and_verify_zip
from app.tasks.train.merge_archive import merge_archive_files
from app.tasks.train.create_ml_model import create_yolo_model
from app.tasks.deploy.deploy_ml_model import deploy_to_triton
from app.services.dataset_service import DataSetService
from app.services.ml_service import MlService
from app.database import get_redis, get_session
import os
import asyncio
import redis
from datetime import datetime
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


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
            await session_instance.begin()
            service = service_class(redis=redis_instance, session=session_instance, file_directory=file_directory)
            try:
                result = await func(service, *args, **kwargs)
                await session_instance.commit()  
                return result
            except Exception as e:
                await session_instance.rollback()
                raise e  
            finally:
                await session_instance.close()


# 특정 패턴의 키를 redis 에서 삭제
def clear_redis_keys_sync(key_pattern: str):
    ri = redis.from_url(redis_url)
    
    cursor = "0"
    while cursor != 0:
        cursor, keys = ri.scan(cursor=cursor, match=key_pattern, count=100)
        if keys:
            ri.delete(*keys)

    ri.close()

def get_event_loop():
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop


@app.task
def valid_archive_task(file_name):
    loop = get_event_loop()
    return loop.run_until_complete(with_service(DataSetService, DATASET_DIRECTORY, valid_archive, file_name=file_name))


# 아카이브 검사 (디렉터리 및 yaml 내용 체크)
async def valid_archive(dataset_service: DataSetService, file_name: str):
    try: 
        zip_path = f"{CELERY_ARCHIVE_PATH}/{file_name}"   
        await dataset_service.update_status(file_name, 'running') 

        result = parse_and_verify_zip(zip_path)
        status = "complete" if result else "failed"

        await dataset_service.update_status(file_name, status) 

        return result
    except Exception as e:
        logging.error(f"Unexpected Error in valid_archive task: {e}")
        return False


@app.task
def create_model_task(model_name: str, model_type: str, version: int, zip_files: list[str]):
    loop = get_event_loop()
    return loop.run_until_complete(with_service(MlService, MODEL_DIRECTORY, create_model, model_name=model_name, model_type=model_type, version=version, zip_files=zip_files))


# zip_files를 기반으로 학습하고 생성된 모델 저장
async def create_model(ml_service: MlService, model_name: str, model_type: str, version: int, zip_files: list[str]):
    try:
        file_name = f"{model_name}.{model_type}"
        datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")
        output_dir = os.path.join(CELERY_ML_RUNS_PATH, f"{model_name}_{datetime_str}")
        zip_files = [os.path.join(CELERY_ARCHIVE_PATH, zip_file) for zip_file in zip_files]
        await ml_service.update_status(file_name, 'running')
        await ml_service.session.commit()  # 중간 상태 커밋

        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        else:
            await ml_service.update_status(file_name, 'failed')
            return False

        if not merge_archive_files(zip_files, output_dir):  # 아카이브 병합
            await ml_service.update_status(file_name, 'failed')
            return False

        create_result, model_info = create_yolo_model(  # Yolo 학습 및 모델 생성
            model_name=model_name,
            file_name=file_name,
            version=version, 
            output_dir=output_dir, 
            ml_runs_path=CELERY_ML_RUNS_PATH, 
            status_handler=redis_status_handler
            )
        if not create_result:
            await ml_service.update_status(file_name, 'failed')
            return False
        
        await ml_service.update_model(**model_info)
        await ml_service.update_status(file_name, 'complete')  # Task 완료 처리 (db)
        
        clear_redis_keys_sync(f"train:{file_name}")  # Progress 제거 (redis)
        return True
    except Exception as e:
        logging.error(f"Unexpected Error in create_model task: {e}")
        return False


@app.task
def deploy_model_task(model_name: str, model_type: str):
    loop = get_event_loop()
    return loop.run_until_complete(with_service(MlService, MODEL_DIRECTORY, deploy_model, model_name=model_name, model_type=model_type))


async def deploy_model(ml_service: MlService, model_name: str, model_type: str):
    try:
        file_name = f"{model_name}.{model_type}"

        await ml_service.update_status(file_name, 'running')
        await ml_service.session.commit()  # 중간 상태 커밋

        model = await ml_service.get_model_by_name(file_name)
        file_path = model['file_path']
        version = model['version']

        if deploy_to_triton(model_name, version, file_path, MODEL_REPOSITORY) is False:
            await ml_service.update_status(file_name, 'failed')
            return False

        await ml_service.deploy_model(file_name)  # deploy 표시
        await ml_service.update_model(file_name, 'complete')  # 완료 표시

        return True
    except Exception as e:
        logging.error(f"Unexpected Error in deploy_model task: {e}")
        return False