from celery import Celery
from app.config import CELERY_BROKER_URL, CELERY_ARCHIVE_PATH, CELERY_ML_RUNS_PATH
from app.tasks.valid.valid_archive import parse_and_verify_zip
from app.tasks.train.merge_archive import merge_archive_files
from app.tasks.train.create_ml_model import create_yolo_model
import redis
import os
import shutil
from datetime import datetime


redis_url = CELERY_BROKER_URL
app = Celery('tasks', broker=redis_url)


def redis_status_handler(ri_key, status):
    ri = redis.from_url(redis_url)
    ri.set(ri_key, status)
    ri.close()   


@app.task
def valid_archive(file_name):
    zip_path = f"{CELERY_ARCHIVE_PATH}/{file_name}"
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


@app.task
def create_model(model_name: str, zip_files: list[str]):
    datetime_str = datetime.now().strftime("%Y%m%d%H%M%S")
    output_dir = os.path.join(CELERY_ML_RUNS_PATH, f"{model_name}_{datetime_str}")
    ri_key = f"model:{model_name}"
    zip_files = [os.path.join(CELERY_ARCHIVE_PATH, zip_file) for zip_file in zip_files]

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

        create_result = create_yolo_model(model_name, output_dir, ml_runs_path=CELERY_ML_RUNS_PATH, status_handler=redis_status_handler)
        if not create_result:  # AI 모델 생성
            ri.set(ri_key, "failed")
            return False
        
        ri.set(ri_key, "complete")
        return True

    finally:
        ri.close()