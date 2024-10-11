import os
import pytest
import tempfile
from fastapi import UploadFile
from app.services.file_service import FileService
from app.repositories.file_repository import FileRepository


@pytest.fixture
def temp_directory():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def file_service(temp_directory):
    repository = FileRepository(file_directory=temp_directory)
    service = FileService(repository=repository)
    return service


@pytest.fixture
def temp_file_in_directory(temp_directory):
    temp_file_path = os.path.join(temp_directory, "temp_test_file.txt")
    with open(temp_file_path, "wb") as temp_file:
        yield temp_file_path


@pytest.mark.asyncio
async def test_upload_file(file_service, temp_directory, temp_file_in_directory):
    file_content = b"this is a test file"
    with open(temp_file_in_directory, "wb") as temp_file:
        temp_file.write(file_content)

    with open(temp_file_in_directory, "rb") as temp_file_for_upload:
        upload_file = UploadFile(filename="temp_test_file.txt", file=temp_file_for_upload)

        await file_service.upload_file(upload_file)

    uploaded_file_path = os.path.join(temp_directory, "temp_test_file.txt")
    assert os.path.exists(uploaded_file_path)

    with open(uploaded_file_path, "rb") as f:
        saved_content = f.read()
    assert saved_content == file_content


def test_delete_file(file_service, temp_directory, temp_file_in_directory):
    assert os.path.exists(temp_file_in_directory)

    file_service.delete_file(os.path.basename(temp_file_in_directory))

    assert not os.path.exists(temp_file_in_directory)


def test_get_file_list(file_service, temp_directory):
    file_names = ["file1.txt", "file2.txt", "file3.txt"]
    for file_name in file_names:
        with open(os.path.join(temp_directory, file_name), "w") as f:
            f.write("test content")

    file_list = file_service.get_file_list()

    assert sorted(file_list) == sorted(file_names)
