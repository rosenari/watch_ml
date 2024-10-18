from celery import Celery
from app.config import CELERY_BROKER_URL, CELERY_ARCHIVE_PATH
from backend.app.tasks.valid.valid_archive import parse_and_verify_zip
import redis


redis_url = CELERY_BROKER_URL
app = Celery('tasks', broker=redis_url)


@app.task
def valid_archive(file_name):
    archive_path = CELERY_ARCHIVE_PATH
    zip_path = f"{archive_path}/{file_name}"

    ri = redis.from_url(redis_url)
    ri.set(f"valid:{file_name}", "running")

    result = parse_and_verify_zip(zip_path)

    ri.set(f"valid:{file_name}", "complete" if result is True else "failed")
    ri.close()

    return result