import os
import zipfile
import yaml
import shutil
import tempfile


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
    with open(yaml_path, 'r') as f:
        return yaml.safe_load(f)


# 라벨 디렉터리 경로 추출
def get_label_dirs(temp_dir, data):
    return {
        'train': os.path.join(temp_dir, data['train'].replace('images', 'labels')),
        'val': os.path.join(temp_dir, data['val'].replace('images', 'labels')),
        'test': os.path.join(temp_dir, data['test'].replace('images', 'labels'))
    }


# 이미지 및 라벨 파일 복사
def copy_files(src_dir, label_dir, dst_dirs, zip_file):
    if os.path.exists(src_dir):
        for item in os.listdir(src_dir):
            src_image_path = os.path.join(src_dir, item)
            if os.path.isfile(src_image_path):
                ext = os.path.splitext(item)[1].lower()
                if ext in ['.jpg', '.jpeg', '.png', '.bmp']:
                    new_image_name = f"{os.path.basename(zip_file).replace('.zip', '')}_{item}"
                    shutil.copy(src_image_path, os.path.join(dst_dirs['images'], new_image_name))

                    label_name = os.path.splitext(item)[0] + '.txt'
                    src_label_path = os.path.join(label_dir, label_name)
                    if os.path.exists(src_label_path):
                        new_label_name = f"{os.path.basename(zip_file).replace('.zip', '')}_{label_name}"
                        shutil.copy(src_label_path, os.path.join(dst_dirs['labels'], new_label_name))


# classes.txt 병합 (train, val, test 각각의 디렉터리에서 classes.txt를 병합)
def merge_classes_per_split(classes_txt_path, merged_classes):
    if os.path.exists(classes_txt_path):
        with open(classes_txt_path, 'r') as f:
            classes = f.read().splitlines()
            merged_classes.update(classes)


# 병합된 classes.txt 생성 (각각의 train, val, test에 따로 생성)
def write_merged_classes(output_dir, merged_classes_per_split):
    for split in ['train', 'val', 'test']:
        merged_classes_txt_path = os.path.join(output_dir, 'labels', split, 'classes.txt')
        with open(merged_classes_txt_path, 'w') as f:
            f.write('\n'.join(merged_classes_per_split[split]))


# 병합된 data.yaml 생성
def write_merged_data_yaml(output_dir, merged_data, merged_classes):
    merged_data_yaml_path = os.path.join(output_dir, 'data.yaml')
    merged_data['nc'] = len(merged_classes)  
    merged_data['names'] = list(merged_classes) 
    with open(merged_data_yaml_path, 'w') as f:
        yaml.dump(merged_data, f)


# 아카이브 파일 병합
def merge_archive_files(zip_files, output_dir):
    merged_dirs = create_output_dirs(output_dir)
    merged_classes_per_split = {
        'train': set(),
        'val': set(),
        'test': set()
    }
    merged_data = {
        'train': merged_dirs['images']['train'],
        'val': merged_dirs['images']['val'],
        'test': merged_dirs['images']['test']
    }

    for zip_file in zip_files:
        temp_dir = extract_zip_to_temp(zip_file)
        yaml_path = find_yaml_path(temp_dir.name)

        if yaml_path:
            data = load_data_yaml(yaml_path)
            label_dirs = get_label_dirs(temp_dir.name, data)

            for key in ['train', 'val', 'test']:
                copy_files(os.path.join(temp_dir.name, data[key]), label_dirs[key], {
                    'images': merged_dirs['images'][key],
                    'labels': merged_dirs['labels'][key]
                }, zip_file)

                merge_classes_per_split(os.path.join(os.path.dirname(yaml_path), 'labels', key, 'classes.txt'),
                                        merged_classes_per_split[key])

        temp_dir.cleanup()

    write_merged_classes(output_dir, merged_classes_per_split)
    write_merged_data_yaml(output_dir, merged_data, {cls for split in merged_classes_per_split.values() for cls in split})

    print(f'Merged data.yaml and classes.txt have been created in {output_dir}')


# 예시 사용법
"""
zip_files = ['dataset1.zip', 'dataset2.zip']  # 병합할 zip 파일 리스트
output_dir = 'merged_dataset'  # 결과 저장 디렉터리
merge_archive_files(zip_files, output_dir)
"""
