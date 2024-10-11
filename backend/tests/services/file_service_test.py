import os
import pytest
import tempfile
from fastapi import UploadFile
from app.services.file_service import FileService
from app.repositories.file_repository import FileRepository


@pytest.fixture
def temp_directory():
    # 임시 디렉터리 생성
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir
    # 테스트 후 임시 디렉터리 및 파일 자동 삭제


@pytest.fixture
def file_service(temp_directory):
    # 임시 디렉터리 기반으로 FileRepository 및 FileService 생성
    repository = FileRepository(file_directory=temp_directory)
    service = FileService(repository=repository)
    return service


@pytest.fixture
def temp_file_in_directory(temp_directory):
    # 임시 디렉터리 안에 임시 파일 생성
    temp_file_path = os.path.join(temp_directory, "temp_test_file.txt")
    with open(temp_file_path, "wb") as temp_file:
        yield temp_file_path  # 파일 경로를 테스트에서 사용
    # 임시 디렉터리에서 모든 파일이 자동 삭제됨 (별도 파일 삭제 필요 없음)


@pytest.mark.asyncio
async def test_upload_file(file_service, temp_directory, temp_file_in_directory):
    # 테스트용 임시 파일 내용 작성
    file_content = b"this is a test file"
    with open(temp_file_in_directory, "wb") as temp_file:
        temp_file.write(file_content)

    # UploadFile로 임시 파일 래핑
    with open(temp_file_in_directory, "rb") as temp_file_for_upload:
        upload_file = UploadFile(filename="temp_test_file.txt", file=temp_file_for_upload)

        # 파일 업로드 테스트
        await file_service.upload_file(upload_file)

    # 업로드된 파일 경로 확인
    uploaded_file_path = os.path.join(temp_directory, "temp_test_file.txt")
    assert os.path.exists(uploaded_file_path)

    # 업로드된 파일 내용 확인
    with open(uploaded_file_path, "rb") as f:
        saved_content = f.read()
    assert saved_content == file_content


def test_delete_file(file_service, temp_directory, temp_file_in_directory):
    # 임시 파일이 존재하는지 확인
    assert os.path.exists(temp_file_in_directory)

    # 파일 삭제
    file_service.delete_file(os.path.basename(temp_file_in_directory))

    # 파일 삭제 확인
    assert not os.path.exists(temp_file_in_directory)


def test_get_file_list(file_service, temp_directory):
    # 테스트용 파일 여러 개 생성
    file_names = ["file1.txt", "file2.txt", "file3.txt"]
    for file_name in file_names:
        with open(os.path.join(temp_directory, file_name), "w") as f:
            f.write("test content")

    # 파일 목록 조회
    file_list = file_service.get_file_list()

    # 파일 목록이 예상과 일치하는지 확인
    assert sorted(file_list) == sorted(file_names)
