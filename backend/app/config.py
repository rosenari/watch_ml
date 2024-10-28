import os


DATASET_DIRECTORY = os.environ.get('DATASET_DIRECTORY', '/src/dataset_archive')
MODEL_DIRECTORY = os.environ.get('MODEL_DIRECTORY', '/src/runs/model_repo')
MODEL_REPOSITORY = os.environ.get('MODEL_REPOSITORY', '/src/runs/triton_repo') # triton repo

VALID_ARCHIVE_MODULE_PATH = os.getenv('VALID_ARCHIVE_MODULE_PATH', 'app.tasks.valid_archive')
CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0')
CELERY_ARCHIVE_PATH = os.environ.get('CELERY_ARCHIVE_PATH', '/src/dataset_archive')
CELERY_ML_RUNS_PATH = os.environ.get('CELERY_ML_RUNS_PATH', '/src/runs')


DATABASE_USER = os.environ.get('DATABASE_USER', 'mluser')
DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD', 'devpassword')
DATABASE_HOST = os.environ.get('DATABASE_HOST', 'localhost')
DATABASE = os.environ.get('DATABASE', 'watchml')
SQLALCHEMY_DATABASE_URL = os.environ.get('DATABASE_URL', f"postgresql+asyncpg://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_HOST}/{DATABASE}")

TRITON_GRPC_URL = os.environ.get('TRITON_GRPC_URL', 'triton:8001')
YOLO_CLASS_LIST = ["person", "bicycle", "car", "motorcycle", "airplane",
"bus", "train", "truck", "boat", "traffic light",
"fire hydrant", "stop sign", "parking meter", "bench", "bird",
"cat", "dog", "horse", "sheep", "cow", "elephant",
"bear", "zebra", "giraffe", "backpack", "umbrella",
"handbag", "tie", "suitcase", "frisbee", "skis",
"snowboard", "sports ball", "kite", "baseball bat",
"baseball glove", "skateboard", "surfboard", "tennis racket",
"bottle", "wine glass", "cup", "fork", "knife",
"spoon", "bowl", "banana", "apple", "sandwich",
"orange", "broccoli", "carrot", "hot dog", "pizza",
"donut", "cake", "chair", "couch", "potted plant",
"bed", "dining table", "toilet", "tv", "laptop",
"mouse", "remote", "keyboard", "cell phone", "microwave",
"oven", "toaster", "sink", "refrigerator", "book",
"clock", "vase", "scissors", "teddy bear", "hair dryer",
"toothbrush"]
FASHION_MODEL_CLASS_LIST =  ["short_sleeved_shirt","long_sleeved_shirt","short_sleeved_outwear","long_sleeved_outwear","vest","sling","shorts","trousers","skirt","short_sleeved_dress","long_sleeved_dress","vest_dress","sling_dress"]