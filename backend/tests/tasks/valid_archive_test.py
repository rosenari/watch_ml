import pytest
import zipfile
from io import BytesIO
from app.tasks.valid_archive import parse_and_verify_zip, verify_yolo_dataset, check_yolo_format


# 가상의 이미지 파일과 txt 파일 목록
image_files = ['image1.jpg', 'image2.png']
txt_files = ['image1.txt', 'image2.txt']
yolo_format = "0 0.5 0.5 0.1 0.1\n"  # 가상 YOLO 형식 데이터

# 가상 디렉토리와 파일 생성
@pytest.fixture
def mock_directories_and_files(tmpdir):
    # 가상의 train 디렉토리 생성
    train_images_dir = tmpdir.mkdir("train_images")
    train_labels_dir = tmpdir.mkdir("train_labels")

    # 이미지 파일 생성
    for image_file in image_files:
        train_images_dir.join(image_file).write('dummy image data')

    # 라벨 파일 생성 (YOLO 포맷)
    for txt_file in txt_files:
        train_labels_dir.join(txt_file).write(yolo_format)

    return str(train_images_dir), str(train_labels_dir)

# 가상 ZIP 파일 생성
@pytest.fixture
def mock_zip_file():
    # 가상의 ZIP 파일을 생성 (메모리 내에서)
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as mock_zip:
        # 가상의 data.yaml 파일 추가
        yaml_content = """
        train: ./train_images
        val: ./val_images
        test: ./test_images
        names: ['class1', 'class2']
        """
        mock_zip.writestr('data.yaml', yaml_content)
    
    zip_buffer.seek(0)  # ZIP 파일 포인터를 처음으로 이동
    return zip_buffer

# YOLO 포맷 검증 테스트
def test_check_yolo_format(tmpdir):
    # 가상의 txt 파일 생성
    txt_file = tmpdir.join("image1.txt")
    txt_file.write(yolo_format)

    # YOLO 포맷 검증
    assert check_yolo_format(str(txt_file), num_classes=2) == True

    # 잘못된 형식 테스트
    txt_file.write("invalid_format")
    assert check_yolo_format(str(txt_file), num_classes=2) == False

# 디렉토리 및 파일 구조 검증 테스트
def test_verify_yolo_dataset(mock_directories_and_files):
    train_images_dir, train_labels_dir = mock_directories_and_files

    # 가상 YAML 데이터 생성
    data_yaml = {
        'train': train_images_dir,
        'val': train_images_dir,  # val과 test도 동일한 구조로 가정
        'test': train_images_dir,
        'names': ['class1', 'class2']
    }

    # 검증 함수 호출
    assert verify_yolo_dataset(data_yaml) == True


def test_parse_and_verify_zip(mock_zip_file):
    # ZIP 파일을 BytesIO 객체에서 읽어서 테스트
    result = parse_and_verify_zip(mock_zip_file)
    
    # 검증
    assert result == True
