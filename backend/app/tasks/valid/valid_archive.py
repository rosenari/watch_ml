import os
import zipfile
import yaml
import logging
from app.logger import LOGGER_NAME



logger = logging.getLogger(LOGGER_NAME)
image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}

# YOLO 포맷 검증 함수
def check_yolo_format(txt_path, num_classes, zip_ref):
    with zip_ref.open(txt_path) as file:
        lines = file.readlines()
        for line in lines:
            elements = line.decode('utf-8').strip().split()
            if len(elements) != 5:
                logger.error(f"Invalid YOLO format in file: {txt_path}")
                return False
            class_id = int(elements[0])
            if class_id < 0 or class_id >= num_classes:
                logger.error(f"Invalid class ID {class_id} in file: {txt_path}")
                return False
            for value in elements[1:]:
                try:
                    float_value = float(value)
                    if not (0 <= float_value <= 1):
                        logger.error(f"Invalid bounding box value {float_value} in file: {txt_path}")
                        return False
                except ValueError:
                    logger.error(f"Invalid number {value} in file: {txt_path}", exc_info=True)
                    return False
    return True

# 이미지와 라벨이 다른 디렉토리에 있는 경우, 각각을 비교하는 함수
def verify_files(image_dir, label_dir, num_classes, zip_ref):
    images = [f for f in zip_ref.namelist() if f.startswith(image_dir) and os.path.splitext(f)[1].lower() in image_extensions]

    for image in images:
        # 라벨 파일은 이미지 디렉토리에서 라벨 디렉토리로 대응시켜서 추정
        label_file = image.replace(image_dir, label_dir).replace('.jpg', '.txt').replace('.png', '.txt')  
        logger.info(f"Verifying label: {label_file}")

        if label_file not in zip_ref.namelist():
            logger.warning(f"Warning: Missing label file for image: {image}. Continuing without label.")
            continue

        # YOLO 포맷 검증
        if not check_yolo_format(label_file, num_classes, zip_ref):
            logger.error("Failed YOLO format validation")
            return False

    logger.info(f"All files in {image_dir} and corresponding labels verified successfully.")
    return True

# YOLO 데이터 세트 검증 (train/val/test 디렉토리 및 파일 구조)
def verify_yolo_dataset(data_yaml, zip_ref):
    # 클래스 개수 확인
    if 'names' not in data_yaml:
        logger.error("No 'names' key found in data.yaml")
        return False

    num_classes = len(data_yaml['names'])

    # train, val, test 디렉토리 검증
    for key in ['train', 'val', 'test']:
        if key in data_yaml:
            image_dir = data_yaml[key]  # 압축 파일 내의 상대 경로 그대로 사용
            label_dir = image_dir.replace('images', 'labels')  # 라벨 경로는 이미지 경로와 대응

            # 압축 파일 내부 경로가 유효한지 확인
            if not any(f.startswith(image_dir) for f in zip_ref.namelist()):
                logger.error(f"Image directory not found: {image_dir} inside the zip")
                return False
            if not any(f.startswith(label_dir) for f in zip_ref.namelist()):
                logger.error(f"Label directory not found: {label_dir} inside the zip")
                return False

            # 이미지와 라벨 파일 검증
            if not verify_files(image_dir, label_dir, num_classes, zip_ref):
                return False

    return True


def parse_and_verify_zip(zip_path):
    result = True

    try:        
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            with zip_ref.open('data.yaml') as yaml_file:
                data_yaml = yaml.safe_load(yaml_file)
                if not verify_yolo_dataset(data_yaml, zip_ref):
                    logger.error("YOLO dataset verification failed.")
                    result = False
                logger.info("YOLO dataset verified successfully.")
    except Exception:
        logger.error(f"Unexpected Error occurred", exc_info=True)
        result = False
    finally:
        return result