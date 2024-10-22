import pytest
import os
import zipfile
import tempfile
import yaml
from app.tasks.train.merge_archive import (extract_zip_to_temp, get_label_dirs, copy_files, merge_classes_per_split, 
                         split_train_to_test, get_class_mapper, update_label, merge_archive_files, find_yaml_path, load_data_yaml,
                         create_output_dirs)

@pytest.fixture
def sample_zip_file():
    temp_zip = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)  # delete=False로 자동 삭제 방지
    with zipfile.ZipFile(temp_zip, 'w') as zipf:
        zipf.writestr('data.yaml', yaml.dump({
            'train': 'images/train',
            'val': 'images/val',
            'test': 'images/test',
            'names': ['class1', 'class2'],
            'nc': 2
        }))
        zipf.writestr('images/train/sample_image_1.jpg', '')
        zipf.writestr('labels/train/sample_image_1.txt', '0 0.5 0.5 1 1')
        zipf.writestr('images/val/sample_image_2.jpg', '')
        zipf.writestr('labels/val/sample_image_2.txt', '1 0.5 0.5 1 1')
        zipf.writestr('images/test/sample_image_3.jpg', '')
        zipf.writestr('labels/test/sample_image_3.txt', '0 0.5 0.5 1 1')

        zipf.writestr('labels/train/classes.txt', 'class1\nclass2\n')
        zipf.writestr('labels/val/classes.txt', 'class1\nclass2\n')
        zipf.writestr('labels/test/classes.txt', 'class1\nclass2\n')

    temp_zip.close()
    yield temp_zip.name

    os.remove(temp_zip.name)


def test_extract_zip_to_temp(sample_zip_file):
    temp_dir = extract_zip_to_temp(sample_zip_file)
    assert os.path.exists(temp_dir.name)
    temp_dir.cleanup()


def test_get_label_dirs(sample_zip_file):
    temp_dir = extract_zip_to_temp(sample_zip_file)
    yaml_path = find_yaml_path(temp_dir.name)
    data = load_data_yaml(yaml_path)
    label_dirs = get_label_dirs(temp_dir.name, data)
    assert 'train' in label_dirs
    assert 'val' in label_dirs
    assert 'test' in label_dirs
    temp_dir.cleanup()


def test_copy_files(sample_zip_file, tmpdir):
    temp_dir = extract_zip_to_temp(sample_zip_file)
    yaml_path = find_yaml_path(temp_dir.name)
    data = load_data_yaml(yaml_path)

    merged_dirs = create_output_dirs(tmpdir)

    copy_files(os.path.join(temp_dir.name, data['train']), merged_dirs['images']['train'], "test_prefix")

    copied_image_path = os.path.join(merged_dirs['images']['train'], "test_prefix_sample_image_1.jpg")
    assert os.path.exists(copied_image_path), "Image file was not copied correctly."

    temp_dir.cleanup()


def test_merge_classes_per_split(sample_zip_file):
    temp_dir = extract_zip_to_temp(sample_zip_file)
    yaml_path = find_yaml_path(temp_dir.name)
    data = load_data_yaml(yaml_path)

    merged_classes = set()
    label_dir = os.path.join(temp_dir.name, data['train'].replace('images', 'labels'))
    
    print(os.path.exists(label_dir))
    merged_classes = merge_classes_per_split(os.path.join(label_dir, 'classes.txt'), merged_classes)
    
    assert 'class1' in merged_classes
    assert 'class2' in merged_classes
    
    temp_dir.cleanup()


def test_split_train_to_test(tmpdir):
    merged_dirs = create_output_dirs(tmpdir)

    for i in range(10):
        with open(os.path.join(merged_dirs['images']['train'], f'image_{i}.jpg'), 'w') as f:
            f.write('fake image content')

    split_train_to_test(merged_dirs)

    assert len(os.listdir(merged_dirs['images']['test'])) == 1
    assert len(os.listdir(merged_dirs['images']['train'])) == 9


def test_get_class_mapper(sample_zip_file):
    temp_dir = extract_zip_to_temp(sample_zip_file)
    yaml_path = find_yaml_path(temp_dir.name)
    data = load_data_yaml(yaml_path)

    label_dir = os.path.join(temp_dir.name, data['train'].replace('images', 'labels'))
    class_mapper = get_class_mapper(label_dir)

    assert class_mapper['0'] == 'class1'
    assert class_mapper['1'] == 'class2'

    temp_dir.cleanup()


def test_update_label(sample_zip_file, tmpdir):
    temp_dir = extract_zip_to_temp(sample_zip_file)
    yaml_path = find_yaml_path(temp_dir.name)
    data = load_data_yaml(yaml_path)

    label_dir = os.path.join(temp_dir.name, data['train'].replace('images', 'labels'))
    class_mapper = get_class_mapper(label_dir)


    src_label_file = os.path.join(label_dir, 'sample_image_1.txt')
    dest_label_file = os.path.join(tmpdir, 'sample_image_1.txt')

    update_label(src_label_file, dest_label_file, class_mapper)

    with open(dest_label_file, 'r') as f:
        lines = f.readlines()
        assert lines[0].startswith('class1'), "Class index was not updated to class name"

    temp_dir.cleanup()


def test_merge_archive_files(sample_zip_file, tmpdir):
    merge_archive_files([sample_zip_file], tmpdir)

    assert os.path.exists(os.path.join(tmpdir, 'data.yaml'))
    for split in ['train', 'val', 'test']:
        assert os.path.exists(os.path.join(tmpdir, 'labels', split, 'classes.txt'))



if __name__ == '__main__':
    current_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(current_dir, 'merged_output')

    zip_dir = os.path.join(current_dir, 'mock')
    zip_files = [os.path.join(zip_dir, file) for file in os.listdir(zip_dir) if file.endswith('.zip')]

    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    merge_archive_files(zip_files, output_dir)

    print(f"Files merged into {output_dir}")
