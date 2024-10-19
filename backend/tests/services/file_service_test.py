import os
import pytest
import tempfile
import pytest_asyncio
from app.database import get_redis
from fastapi import UploadFile
from app.services.file_service import FileService
from app.database import get_session, async_engine


@pytest_asyncio.fixture
async def session():
    async for s in get_session():
        await s.begin()
        try:
            yield s
        except Exception as e:
            await s.rollback()
            raise e
        finally:
            await s.rollback()

    await async_engine.dispose()


@pytest_asyncio.fixture
async def redis():
    async for ri in get_redis('redis://localhost:6379/0'):
        yield ri


@pytest.fixture
def temp_directory():
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def temp_file_in_directory(temp_directory):
    temp_file_path = os.path.join(temp_directory, "temp_test_file.txt")
    with open(temp_file_path, "wb") as temp_file:
        temp_file.write(b'test file')
    yield temp_file_path


@pytest.fixture
def file_service(temp_directory, redis, session) -> FileService:
    service = FileService(redis, session, temp_directory)
    return service


@pytest.mark.asyncio
async def test_upload_file(file_service: FileService, temp_directory, temp_file_in_directory):
    with open(temp_file_in_directory, "rb") as temp_file_for_upload:
        upload_file = UploadFile(filename="temp_test_file.txt", file=temp_file_for_upload)

        await file_service.upload_file(upload_file)

    uploaded_file_path = os.path.join(temp_directory, "temp_test_file.txt")
    assert os.path.exists(uploaded_file_path)

    file_list = await file_service.get_file_list()
    file_names = [file['file_name'] for file in file_list]

    assert "temp_test_file.txt" in file_names, "데이터베이스에 등록 되지않았습니다."



@pytest.mark.asyncio
async def test_delete_file(file_service: FileService, temp_file_in_directory):
    with open(temp_file_in_directory, "rb") as temp_file_for_upload:
        upload_file = UploadFile(filename="temp_test_file.txt", file=temp_file_for_upload)

        await file_service.upload_file(upload_file)

    assert os.path.exists(temp_file_in_directory)

    await file_service.delete_file(os.path.basename(temp_file_in_directory))

    file_list = await file_service.get_file_list()
    file_names = [file['file_name'] for file in file_list]

    assert "temp_test_file.txt" not in file_names, "삭제된 파일이 목록에 표시됩니다."


@pytest.mark.asyncio
async def test_get_file_list(file_service: FileService, temp_directory):
    file_names = ["file1.txt", "file2.txt", "file3.txt"]
    for file_name in file_names:
        temp_file_path = os.path.join(temp_directory, file_name)
        
        with open(temp_file_path, "w") as f:
            f.write("test content")
        
        with open(temp_file_path, "rb") as temp_file_for_upload:
            upload_file = UploadFile(filename=file_name, file=temp_file_for_upload)
            await file_service.upload_file(upload_file)

    file_list = await file_service.get_file_list()
    file_list = [file['file_name'] for file in file_list]

    for file_name in file_names:
        assert file_name in file_list, f"{file_name}이(가) 파일 목록에 없습니다."


@pytest.mark.asyncio
async def test_get_valid_file_list(file_service: FileService):
    ri = file_service.redis

    await ri.set('valid:file1', 'success')
    await ri.set('valid:file2', 'pending')

    result = await file_service.get_valid_file_list()

    assert {'file_name': 'file1', 'status': 'success'} in result
    assert {'file_name': 'file2', 'status': 'pending'} in result

    await ri.delete('valid:file1')
    await ri.delete('valid:file2')
    
    result_after_delete = await file_service.get_valid_file_list()
    assert {'file_name': 'file1', 'status': 'success'} not in result_after_delete
    assert {'file_name': 'file2', 'status': 'pending'} not in result_after_delete