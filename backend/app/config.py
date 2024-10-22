import os


DATASET_DIRECTORY = os.environ.get('DATASET_DIRECTORY', '/src/dataset_archive')
VALID_ARCHIVE_MODULE_PATH = os.getenv('VALID_ARCHIVE_MODULE_PATH', 'app.tasks.valid_archive')
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_ARCHIVE_PATH = os.environ.get('CELERY_ARCHIVE_PATH', '/src/dataset_archive')
CELERY_ML_RUNS_PATH = os.environ.get('CELERY_ML_RUNS_PATH', '/src/runs')
MODEL_DIRECTORY = os.environ.get('MODEL_DIRECTORY', '/src/runs/model_repo')


DATABASE_USER = os.environ.get('DATABASE_USER', 'mluser')
DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD', 'devpassword')
DATABASE_HOST = os.environ.get('DATABASE_HOST', 'localhost')
DATABASE = os.environ.get('DATABASE', 'watchml')
SQLALCHEMY_DATABASE_URL = os.environ.get('DATABASE_URL', f"postgresql+asyncpg://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}/{DATABASE}")