import os
import pytest
import zipfile
from io import BytesIO
from app.tasks.valid_archive import parse_and_verify_zip, verify_yolo_dataset, check_yolo_format


# 가상의 이미지 파일과 txt 파일 목록
image_files = ['image1.jpg', 'image2.png']
txt_files = ['image1.txt', 'image2.txt']
yolo_format = "0 0.5 0.5 0.1 0.1\n"  # 가상 YOLO 형식 데이터


# 가상 ZIP 파일 생성
@pytest.fixture
def mock_zip_file(tmpdir):
    train_images_dir = tmpdir.mkdir("train_images")
    train_labels_dir = tmpdir.mkdir("train_labels")

    # 가상의 이미지와 라벨 파일 추가
    for image_file in image_files:
        train_images_dir.join(image_file).write('dummy image data')
    
    for txt_file in txt_files:
        train_labels_dir.join(txt_file).write(yolo_format)

    # 가상의 ZIP 파일을 생성 (메모리 내에서)
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as mock_zip:
        # 가상의 data.yaml 파일 추가
        yaml_content = f"""
        train: 'train_images'
        val: 'train_images'  # 여기서 val/test도 train처럼 가정
        test: 'train_images'
        names: ['class1', 'class2']
        """
        mock_zip.writestr('data.yaml', yaml_content)

        # 이미지 및 라벨 파일을 ZIP에 추가
        for directory in [train_images_dir, train_labels_dir]:
            for file_path in directory.listdir():
                mock_zip.write(file_path, arcname=os.path.relpath(file_path, tmpdir))
    
    zip_buffer.seek(0)  # ZIP 파일 포인터를 처음으로 이동
    return zip_buffer


# ZIP 파일 파싱 및 검증 테스트
def test_parse_and_verify_zip(mock_zip_file):
    # ZIP 파일을 BytesIO 객체에서 읽어서 테스트
    result = parse_and_verify_zip(mock_zip_file)
    
    # 검증
    assert result == True


def test_parse_and_verify_zip_with_realfile():
    current_dir = os.path.dirname(__file__)
    zip_file_path = os.path.join(current_dir, 'mock', 'datasets.zip')

    result = parse_and_verify_zip(zip_file_path)

    assert result == True