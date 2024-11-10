import os
import zipfile
import yaml
import shutil
import tempfile
import random
import math
import hashlib
import logging
from app.logger import LOGGER_NAME


logger = logging.getLogger(LOGGER_NAME)


# 병합 디렉터리 생성 (images와 labels 디렉터리 아래에 train, val, test 생성)
def create_output_dirs(output_dir):
    dirs = {
        'images': {
            'train': os.path.join(output_dir, 'images', 'train'),
            'val': os.path.join(output_dir, 'images', 'val'),
            'test': os.path.join(output_dir, 'images', 'test')
        },
        'labels': {
            'train': os.path.join(output_dir, 'labels', 'train'),
            'val': os.path.join(output_dir, 'labels', 'val'),
            'test': os.path.join(output_dir, 'labels', 'test')
        }
    }
    for d in dirs['images'].values():
        os.makedirs(d, exist_ok=True)
    for d in dirs['labels'].values():
        os.makedirs(d, exist_ok=True)
    return dirs


# 임시 폴더로 zip 파일 해제
def extract_zip_to_temp(zip_file):
    temp_dir = tempfile.TemporaryDirectory()
    with zipfile.ZipFile(zip_file, 'r') as zip_ref:
        zip_ref.extractall(temp_dir.name)
    return temp_dir


# data.yaml 경로 찾기
def find_yaml_path(temp_dir):
    for root, _, files in os.walk(temp_dir):
        if 'data.yaml' in files:
            return os.path.join(root, 'data.yaml')
    return None


# data.yaml 파일 로드
def load_data_yaml(yaml_path):
    with open(yaml_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


# 라벨 디렉터리 경로 추출
def get_label_dirs(temp_dir, data):
    return {
        'train': os.path.join(temp_dir, data['train'].replace('images', 'labels')),
        'val': os.path.join(temp_dir, data['val'].replace('images', 'labels')),
        'test': os.path.join(temp_dir, data['test'].replace('images', 'labels')) if 'test' in data else None
    }


# 파일 복사
def copy_files(source_dir: str, dest_dir: str, file_prefix: str):
    if not os.path.exists(source_dir):
        return
    
    for item in os.listdir(source_dir):
        source_file_path = os.path.join(source_dir, item)

        if not os.path.isfile(source_file_path):
            continue

        new_file_name = f"{file_prefix}_{item}"
        shutil.copy(source_file_path, os.path.join(dest_dir, new_file_name))


# data.yaml로 부터 클래스 정보 얻어오기
def get_classes_from_yaml(data):
    if 'names' in data:
        return data['names']
    return []


# classes.txt 생성 (각각의 train, val, test에 따로 생성)
def write_merged_classes(output_dir, total_classes):
    for split in ['train', 'val', 'test']:
        merged_classes_txt_path = os.path.join(output_dir, 'labels', split, 'classes.txt')
        with open(merged_classes_txt_path, 'w') as f:
            f.write('\n'.join(total_classes))

    return total_classes


# 병합된 data.yaml 생성
def write_merged_data_yaml(output_dir, merged_data, total_classes):
    merged_data_yaml_path = os.path.join(output_dir, 'data.yaml')
    train = os.path.relpath(merged_data['train'], output_dir).replace('\\', '/')
    val = os.path.relpath(merged_data['val'], output_dir).replace('\\', '/')
    test = os.path.relpath(merged_data['test'], output_dir).replace('\\', '/')
    nc = len(total_classes)
    names = total_classes

    with open(merged_data_yaml_path, 'w', encoding='utf-8') as f:
        f.write(f'train: {train}\n')
        f.write(f'val: {val}\n')
        f.write(f'test: {test}\n')
        f.write('\n')  # 빈 줄 추가
        f.write(f'nc: {nc}\n')
        names_list = ', '.join(f"'{name}'" for name in names)
        f.write(f"names: [{names_list}]\n")


# train 데이터에서 일부 추출하여 test 데이터로 생성
def split_train_to_test(merged_dirs):
    train_images_dir = merged_dirs['images']['train']
    test_images_dir = merged_dirs['images']['test']
    train_labels_dir = merged_dirs['labels']['train']
    test_labels_dir = merged_dirs['labels']['test']
        
    train_images = [f for f in os.listdir(train_images_dir) if os.path.isfile(os.path.join(train_images_dir, f))]
    num_test_samples = math.ceil(len(train_images) * 0.1)
    test_images = random.sample(train_images, num_test_samples)

    for image in test_images:
        src_image = os.path.join(train_images_dir, image)
        dest_image = os.path.join(test_images_dir, image)
        shutil.move(src_image, dest_image)

        label_name = os.path.splitext(image)[0] + '.txt'
        src_label = os.path.join(train_labels_dir, label_name)
        dest_label = os.path.join(test_labels_dir, label_name)
        if os.path.exists(src_label):
            shutil.move(src_label, dest_label)


def update_label(src_label_file, dest_label_file, class_mapping):
    """
    라벨 파일의 인덱스를 입력된 class_mapping에 따라 매핑하여 저장
    class_mapping: index_to_class || class_to_index
    """
    new_lines = []
    
    with open(src_label_file, 'r') as f:
        lines = f.readlines()
        for line in lines:
            parts = line.strip().split()
            if len(parts) > 0:
                source = parts[0]
                dest = class_mapping.get(source)
                parts[0] = dest
                new_lines.append(' '.join(parts))
    
    with open(dest_label_file, 'w') as f:
        f.write('\n'.join(new_lines))


# 아카이브 파일 병합
def merge_archive_files(zip_files, output_dir):
    logging.info("start merge_archive_files")
    result = True
    total_classes = set()

    try:
        merged_dirs = create_output_dirs(output_dir)
        merged_data_store_path = {
            'train': merged_dirs['images']['train'],
            'val': merged_dirs['images']['val'],
            'test': merged_dirs['images']['test']
        }

        for zip_file in zip_files:
            temp_dir = None
            try:
                temp_dir = extract_zip_to_temp(zip_file)  # 임시 폴더에 압축 해제
                yaml_path = find_yaml_path(temp_dir.name)  # data.yaml 경로 얻기
                hash = hashlib.md5(temp_dir.name.encode()).hexdigest()

                if yaml_path:
                    data = load_data_yaml(yaml_path)
                    
                    classes = get_classes_from_yaml(data)
                    total_classes.update(classes)

                    index_to_class = {str(i): class_name for i, class_name in enumerate(classes)}
 
                    for key in ['train', 'val', 'test']:
                        if key not in data:
                            continue

                        # 이미지 복사
                        source_image_dir = os.path.join(temp_dir.name, data[key])

                        if len(os.listdir(source_image_dir)) == 0:
                            continue

                        logger.info(f"[Copy files] source: {source_image_dir}, dest: {merged_dirs['images'][key]}")
                        copy_files(source_image_dir, merged_dirs['images'][key], file_prefix=hash)

                        source_label_dir = os.path.join(temp_dir.name, data[key].replace('images', 'labels'))

                        # 라벨 파일의 인덱스 정보를 클래스 이름으로 변환하여 dest에 저장
                        for label_file in os.listdir(source_label_dir):
                            src_label_file = os.path.join(source_label_dir, label_file)

                            if label_file == 'classes.txt':
                                continue
                            
                            dest_label_file = os.path.join(merged_dirs['labels'][key], f"{hash}_{label_file}")
                            update_label(src_label_file, dest_label_file, index_to_class)  # index to class
            finally:
                if temp_dir is not None:
                    temp_dir.cleanup()

        if len(os.listdir(merged_data_store_path['test'])) == 0:  # test 데이터가 없다면 train에서 일부를 test로 분리
            logger.warning("Because test data does not exist, part of the train data is extracted.")
            split_train_to_test(merged_dirs)

        total_classes = write_merged_classes(output_dir, total_classes)
        logger.info("classes.txt has been created.")

        class_to_index = {class_name: str(i) for i, class_name in enumerate(total_classes)}

        logger.info("Start updating the label from class to index.")
        for key in ['train', 'val', 'test']:
            for label_file in os.listdir(merged_dirs['labels'][key]):
                if label_file == 'classes.txt':
                    continue
                
                dest_label_file = os.path.join(merged_dirs['labels'][key], label_file)
                update_label(dest_label_file, dest_label_file, class_to_index)  # class to index

        write_merged_data_yaml(output_dir, merged_data_store_path, total_classes) 
        logger.info("data.yaml has been created.")

        logger.info(f'Merged data.yaml and classes.txt have been created in {output_dir}')
    except Exception:
        result = False
        logger.error(f"Unexpected Error occurred", exc_info=True)
    finally:
        return result, total_classes