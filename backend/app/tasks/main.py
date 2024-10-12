from celery import Celery
from .valid_archive import parse_and_verify_zip

app = Celery('tasks', broker='redis://redis:6379/0')


@app.task
def valid_archive(zip_path):
    return parse_and_verify_zip(zip_path)