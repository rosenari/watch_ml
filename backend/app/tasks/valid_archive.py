import os
import zipfile
import yaml


image_extensions = {'.jpg', '.jpeg', '.png', '.bmp'}


# YOLO 포맷 검증 함수
def check_yolo_format(txt_path, num_classes):
    with open(txt_path, 'r') as file:
        lines = file.readlines()
        for line in lines:
            elements = line.strip().split()
            if len(elements) != 5:
                print(f"Invalid YOLO format in file: {txt_path}")
                return False
            class_id = int(elements[0])
            if class_id < 0 or class_id >= num_classes:
                print(f"Invalid class ID {class_id} in file: {txt_path}")
                return False
            for value in elements[1:]:
                try:
                    float_value = float(value)
                    if not (0 <= float_value <= 1):
                        print(f"Invalid bounding box value {float_value} in file: {txt_path}")
                        return False
                except ValueError:
                    print(f"Invalid number {value} in file: {txt_path}")
                    return False
    return True

# 디렉토리 내 이미지와 대응하는 txt 파일 검증
def verify_files(directory, num_classes):
    all_files = os.listdir(directory)
    images = [f for f in all_files if os.path.splitext(f)[1].lower() in image_extensions]
    txt_files = [f for f in all_files if f.endswith('.txt')]

    for image in images:
        txt_file = os.path.splitext(image)[0] + '.txt'
        if txt_file not in txt_files:
            print(f"Missing txt file for image: {image} in directory: {directory}")
            return False

        txt_path = os.path.join(directory, txt_file)
        if not check_yolo_format(txt_path, num_classes):
            return False

    print(f"All files in {directory} verified successfully.")
    return True

# YOLO 데이터 세트 검증 (train/val/test 디렉토리 및 파일 구조)
def verify_yolo_dataset(data_yaml):
    # 클래스 개수 확인
    if 'names' not in data_yaml:
        print("No 'names' key found in data.yaml")
        return False

    num_classes = len(data_yaml['names'])

    for key in ['train', 'val', 'test']:
        if key in data_yaml:
            image_dir = data_yaml[key]
            label_dir = image_dir.replace('images', 'labels')

            if not os.path.isdir(image_dir):
                print(f"Image directory not found: {image_dir}")
                return False
            if not os.path.isdir(label_dir):
                print(f"Label directory not found: {label_dir}")
                return False

            if not verify_files(image_dir, num_classes):
                return False
            if not verify_files(label_dir, num_classes):
                return False

    return True


def parse_and_verify_zip(zip_path):
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        with zip_ref.open('data.yaml') as yaml_file:
            data_yaml = yaml.safe_load(yaml_file)
            if not verify_yolo_dataset(data_yaml):
                print("YOLO dataset verification failed.")
                return False
            print("YOLO dataset verified successfully.")
    return True