import os


FILE_DIRECTORY = os.environ.get("FILE_DIRECTORY")
VALID_ARCHIVE_MODULE_PATH = os.getenv('VALID_ARCHIVE_MODULE_PATH', "app.tasks.valid_archive")
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_ARCHIVE_PATH = os.environ.get('CELERY_ARCHIVE_PATH', '/src/dataset_archive')
CELERY_ML_RUNS_PATH = os.environ.get('CELERY_ML_RUNS_PATH', '/src/runs')