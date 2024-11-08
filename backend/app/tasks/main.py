from celery import Celery
from app.config import CELERY_BROKER_URL, CELERY_ML_RUNS_PATH, MODEL_REPOSITORY, TRITON_GRPC_URL
from app.tasks.valid.valid_archive import parse_and_verify_zip
from app.tasks.train.merge_archive import merge_archive_files
from app.tasks.train.create_ml_model import create_yolo_model
from app.tasks.deploy.deploy_ml_model import deploy_to_triton
from app.tasks.deploy.undeploy_ml_model import undeploy_from_triton
from app.tasks.inference.generate_inference_file import generate_inference_file
from app.services.dataset_service import DataSetService
from app.services.ml_service import MlService
from app.services.inference_service import InferenceService
from app.dto import AiModelDTO
from app.database import get_redis, get_session
from app.repositories.inference_repository import FileType
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


async def with_service(service_class, func, *args, **kwargs):
    async for redis_instance in get_redis():
        async for session_instance in get_session():
            await session_instance.begin()
            service = service_class(redis=redis_instance, session=session_instance)
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
def valid_archive_task(id):
    loop = get_event_loop()
    return loop.run_until_complete(with_service(DataSetService, valid_archive, id=id))


# 아카이브 검사 (디렉터리 및 yaml 내용 체크)
async def valid_archive(dataset_service: DataSetService, id: int):
    try: 
        dataset = await dataset_service.get_dataset_by_id(id)
        zip_path = dataset['file_meta']['filepath']
        file_name = os.path.basename(zip_path)
        await dataset_service.update_status(file_name, 'running')
        await dataset_service.session.commit()

        result = parse_and_verify_zip(zip_path)
        status = "complete" if result else "failed"

        await dataset_service.update_status(file_name, status) 

        return result
    except Exception as e:
        logging.error(f"Unexpected Error in valid_archive task: {e}")
        return False


@app.task
def create_model_task(model_id: str, model_ext: str, version: int, zip_file_paths: list[str]):
    loop = get_event_loop()
    return loop.run_until_complete(with_service(MlService, create_model, model_id=model_id, model_ext=model_ext, version=version, zip_file_paths=zip_file_paths))


# zip_files를 기반으로 학습하고 생성된 모델 저장
async def create_model(ml_service: MlService, model_id: int, model_ext: str, version: int, zip_file_paths: list[str]):
    try:
        datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")
        output_dir = os.path.join(CELERY_ML_RUNS_PATH, f"{model_id}_{datetime_str}")
        await ml_service.update_status(model_id, 'running')
        await ml_service.session.commit()  # 중간 상태 커밋

        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        else:
            await ml_service.update_status(model_id, 'failed')
            return False
        
        merged_result, total_classes = merge_archive_files(zip_file_paths, output_dir)
        if not merged_result:  # 아카이브 병합
            await ml_service.update_status(model_id, 'failed')
            return False

        ai_model = await ml_service.get_model_by_id(model_id)
        model_name = ai_model['model_name']
        base_model_path = ai_model['base_model']['model_file']['filepath']
        create_result, model_info = create_yolo_model(  # Yolo 학습 및 모델 생성
            model_name=model_name,
            model_ext=model_ext,
            base_model_path=base_model_path,
            version=version, 
            output_dir=output_dir,
            status_handler=redis_status_handler
            )
        if not create_result:
            await ml_service.update_status(model_id, 'failed')
            return False
        
        model_info['classes'] = total_classes
        await ml_service.update_model(AiModelDTO(**model_info))
        await ml_service.update_status(model_id, 'complete')  # Task 완료 처리 (db)
        
        clear_redis_keys_sync(f"train:{model_name}")  # Progress 제거 (redis)
        return True
    except Exception as e:
        logging.error(f"Unexpected Error in create_model task: {e}")
        return False


@app.task
def deploy_model_task(model_id: int):
    loop = get_event_loop()
    return loop.run_until_complete(with_service(MlService, deploy_model, model_id=model_id))


async def deploy_model(ml_service: MlService, model_id: int):
    try:
        await ml_service.update_status(model_id, 'running')
        await ml_service.session.commit()  # 중간 상태 커밋

        model = await ml_service.get_model_by_id(model_id)
        model_path = model['model_file']['filepath']
        model_name = model['model_name']
        version = model['version']

        deploy_result, deploy_path = deploy_to_triton(model_name, version, model_path, MODEL_REPOSITORY, TRITON_GRPC_URL)
        if deploy_result is False:
            await ml_service.update_status(model_id, 'failed')
            return False
        

        await ml_service.deploy_model(model_id, deploy_path)  # deploy 표시
        await ml_service.update_status(model_id, 'complete')  # 완료 표시

        return True
    except Exception as e:
        logging.error(f"Unexpected Error in deploy_model task: {e}")
        return False
    

@app.task
def undeploy_model_task(model_id: int):
    loop = get_event_loop()
    return loop.run_until_complete(with_service(MlService, undeploy_model, model_id=model_id))


async def undeploy_model(ml_service: MlService, model_id: int):
    try:
        model = await ml_service.get_model_by_id(model_id)
        model_name = model['model_name']
        await ml_service.update_status(model_id, 'running')
        await ml_service.session.commit()  # 중간 상태 커밋

        if undeploy_from_triton(model_name, MODEL_REPOSITORY, TRITON_GRPC_URL) is False:
            await ml_service.update_status(model_id, 'failed')
            return False

        await ml_service.undeploy_model(model_id)  # deploy 표시
        await ml_service.update_status(model_id, 'complete')  # 완료 표시

        return True
    except Exception as e:
        logging.error(f"Unexpected Error in undeploy_model task: {e}")
        return False
    

@app.task
def generate_inference_task(inference_file_id: int, model_name: str, classes: list[str]):
    loop = get_event_loop()
    return loop.run_until_complete(with_service(InferenceService, generate_inference, inference_file_id=inference_file_id, model_name=model_name, classes=classes))


async def generate_inference(inference_service: InferenceService, inference_file_id: int, model_name: str, classes: list[str]):
    try:
        await inference_service.update_status(inference_file_id, 'running')
        await inference_service.session.commit()  # 중간 상태 커밋

        file = await inference_service.get_file_by_id(inference_file_id)
        original_file_path = file['original_file']['filepath']
        file_type = file['file_type']
        generate_file_path = None

        if file_type == FileType.PHOTO or file_type == FileType.VIDEO:
            generate_file_path = generate_inference_file(file_type.value, original_file_path, model_name, classes)
        else:
            await inference_service.update_status(inference_file_id, 'failed')
            return False
        
        await inference_service.update_generated_file(inference_file_id, generate_file_path)
        await inference_service.update_status(inference_file_id, 'complete')  # 완료 표시

        return True
    except Exception as e:
        logging.error(f"Unexpected Error in generate_inference task: {e}")
        return False