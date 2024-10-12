from celery import Celery
import os
import importlib

module_name = os.getenv('VALID_ARCHIVE_MODULE_PATH', "app.tasks.valid_archive")
module = importlib.import_module(module_name)
parse_and_verify_zip = getattr(module, "parse_and_verify_zip")

redis_url = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0')
app = Celery('tasks', broker=redis_url)


@app.task
def valid_archive(file_name):
    archive_path = os.environ.get('CELERY_ARCHIVE_PATH', '/app/dataset_archive')
    zip_path = f"{archive_path}/{file_name}"
    return parse_and_verify_zip(zip_path)