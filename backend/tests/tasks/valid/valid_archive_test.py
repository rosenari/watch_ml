import os
import pytest
import zipfile
from io import BytesIO
from app.tasks.valid.valid_archive import parse_and_verify_zip


image_files = ['image1.jpg', 'image2.png']
txt_files = ['image1.txt', 'image2.txt']
yolo_format = "0 0.5 0.5 0.1 0.1\n" 


# 가상 ZIP 파일 생성
@pytest.fixture
def mock_zip_file(tmpdir):
    train_images_dir = tmpdir.mkdir("train_images")
    train_labels_dir = tmpdir.mkdir("train_labels")

    for image_file in image_files:
        train_images_dir.join(image_file).write('dummy image data')
    
    for txt_file in txt_files:
        train_labels_dir.join(txt_file).write(yolo_format)

    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w') as mock_zip:
        yaml_content = f"""
        train: 'train_images'
        val: 'train_images'
        test: 'train_images'
        names: ['class1', 'class2']
        """
        mock_zip.writestr('data.yaml', yaml_content)

        for directory in [train_images_dir, train_labels_dir]:
            for file_path in directory.listdir():
                mock_zip.write(file_path, arcname=os.path.relpath(file_path, tmpdir))
    
    zip_buffer.seek(0) 
    return zip_buffer


def test_parse_and_verify_zip(mock_zip_file):
    result = parse_and_verify_zip(mock_zip_file)

    assert result == True


def test_parse_and_verify_zip_with_realfile():
    current_dir = os.path.dirname(__file__)
    zip_file_path = os.path.join(current_dir, 'mock', 'datasets.zip')

    result = parse_and_verify_zip(zip_file_path)

    assert result == True