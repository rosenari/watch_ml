import os
import pytest
import tempfile
import pytest_asyncio
from fastapi import UploadFile
from app.database import get_redis, get_session, async_engine
from app.services.dataset_service import DataSetService


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
def dataset_service(temp_directory, redis, session) -> DataSetService:
    service = DataSetService(redis, session, temp_directory)
    return service


@pytest.mark.asyncio
async def test_upload_file(dataset_service: DataSetService, temp_directory, temp_file_in_directory):
    with open(temp_file_in_directory, "rb") as temp_file_for_upload:
        upload_file = UploadFile(filename="temp_test_file.txt", file=temp_file_for_upload)

        await dataset_service.upload_file(upload_file)

    uploaded_file_path = os.path.join(temp_directory, "temp_test_file.txt")
    assert os.path.exists(uploaded_file_path)  # 파일 존재 여부

    file_list = await dataset_service.get_file_list()
    file_names = [file['file_name'] for file in file_list]

    assert "temp_test_file.txt" in file_names, "데이터베이스에 등록 되지않았습니다."



@pytest.mark.asyncio
async def test_delete_file(dataset_service: DataSetService, temp_file_in_directory):
    dataset_id = None
    with open(temp_file_in_directory, "rb") as temp_file_for_upload:
        upload_file = UploadFile(filename="temp_test_file.txt", file=temp_file_for_upload)

        dataset_id = await dataset_service.upload_file(upload_file)

    assert os.path.exists(temp_file_in_directory)

    await dataset_service.delete_file(dataset_id)

    file_list = await dataset_service.get_file_list()
    file_names = [file['file_name'] for file in file_list]

    assert "temp_test_file.txt" not in file_names, "삭제된 파일이 목록에 표시됩니다."


@pytest.mark.asyncio
async def test_get_file_list(dataset_service: DataSetService, temp_directory):
    file_names = ["file1.txt", "file2.txt", "file3.txt"]
    for file_name in file_names:
        temp_file_path = os.path.join(temp_directory, file_name)
        
        with open(temp_file_path, "w") as f:
            f.write("test content")
        
        with open(temp_file_path, "rb") as temp_file_for_upload:
            upload_file = UploadFile(filename=file_name, file=temp_file_for_upload)
            await dataset_service.upload_file(upload_file)

    file_list = await dataset_service.get_file_list()
    file_list = [file['file_name'] for file in file_list]

    for file_name in file_names:
        assert file_name in file_list, f"{file_name}이(가) 파일 목록에 없습니다."


@pytest.mark.asyncio
async def test_update_status(dataset_service: DataSetService, temp_file_in_directory):
    with open(temp_file_in_directory, "rb") as temp_file_for_upload:
        upload_file = UploadFile(filename="temp_test_file.txt", file=temp_file_for_upload)
        dataset_id = await dataset_service.upload_file(upload_file)

        await dataset_service.update_status(dataset_id, "running")

    # 파일 상태를 조회
    file_status_list = await dataset_service.get_file_status()
    updated_file_status = next((file for file in file_status_list if file['file_name'] == "temp_test_file.txt"), None)

    assert updated_file_status is not None, "업데이트된 파일이 목록에 없습니다."
    assert updated_file_status["status"] == "running", "파일 상태가 'running'으로 업데이트되지 않았습니다."


@pytest.mark.asyncio
async def test_get_file_status(dataset_service: DataSetService, temp_directory):
    file_names = ["file1.txt", "file2.txt", "file3.txt"]
    statuses = ["ready", "running", "complete"]

    for file_name, status in zip(file_names, statuses):
        temp_file_path = os.path.join(temp_directory, file_name)
        
        with open(temp_file_path, "w") as f:
            f.write("test content")
        
        with open(temp_file_path, "rb") as temp_file_for_upload:
            upload_file = UploadFile(filename=file_name, file=temp_file_for_upload)
            dataset_id = await dataset_service.upload_file(upload_file)

            await dataset_service.update_status(dataset_id, status)

    file_status_list = await dataset_service.get_file_status()

    for file_name, status in zip(file_names, statuses):
        file_status = next((file for file in file_status_list if file['file_name'] == file_name), None)
        assert file_status is not None, f"{file_name}의 상태가 조회되지 않습니다."
        assert file_status["status"] == status, f"{file_name}의 상태가 {status}로 업데이트되지 않았습니다."
