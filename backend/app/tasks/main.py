from celery import Celery
from app.config import CELERY_BROKER_URL, CELERY_ARCHIVE_PATH
from backend.app.tasks.valid.valid_archive import parse_and_verify_zip
from backend.app.tasks.train.merge_archive import merge_archive_files
from backend.app.tasks.train.create_ml_model import create_yolo_model
import redis
import os
from datetime import datetime


redis_url = CELERY_BROKER_URL
app = Celery('tasks', broker=redis_url)


@app.task
def valid_archive(file_name):
    archive_path = CELERY_ARCHIVE_PATH
    zip_path = f"{archive_path}/{file_name}"
    ri_key = f"valid:{file_name}"

    ri = redis.from_url(redis_url)
    
    try:
        ri.set(ri_key, "running")

        result = parse_and_verify_zip(zip_path)
        status = "complete" if result else "failed"

        ri.set(ri_key, status)

        return result

    finally:
        ri.close()


def redis_status_handler(ri_key, status):
    ri = redis.from_url(redis_url)
    ri.set(ri_key, status)
    ri.close()


@app.task
def create_model(model_name: str, zip_files: list[str]):
    datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")
    output_dir = f"{model_name}_{datetime_str}"
    ri_key = f"model:{model_name}"

    ri = redis.from_url(redis_url)

    try:
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        else:
            ri.set(ri_key, "failed")
            return False
    
        if not merge_archive_files(zip_files, output_dir):  # 아카이브 병합
            ri.set(ri_key, "failed")
            return False

        if not create_yolo_model(model_name, output_dir, status_handler=redis_status_handler):  # AI 모델 생성
            ri.set(ri_key, "failed")
            return False

        ri.set(ri_key, "complete")
        return True

    finally:
        ri.close()