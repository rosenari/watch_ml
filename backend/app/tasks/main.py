from celery import Celery
from app.config import CELERY_BROKER_URL, CELERY_ARCHIVE_PATH
from app.tasks.valid_archive import parse_and_verify_zip
import redis


redis_url = CELERY_BROKER_URL
app = Celery('tasks', broker=redis_url)


def redis_status_handler(file_name, status):
    ri = redis.from_url(redis_url)
    ri.set(f"valid:{file_name}", status)
    ri.close()


@app.task
def valid_archive(file_name):
    archive_path = CELERY_ARCHIVE_PATH
    zip_path = f"{archive_path}/{file_name}"
    return parse_and_verify_zip(zip_path, redis_status_handler)