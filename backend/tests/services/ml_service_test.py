import os
import pytest
import pytest_asyncio
from app.database import get_redis
from app.services.ml_service import MlService
from app.database import get_session, async_engine
import tempfile


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
def temp_file(temp_directory):
    temp_file_path = os.path.join(temp_directory, "temp_test_model.onnx")
    with open(temp_file_path, "wb") as tmp_file:
        tmp_file.write(b"dummy model content")
    yield temp_file_path


@pytest.fixture
def ml_service(redis, session, temp_directory) -> MlService:
    service = MlService(redis, session, file_directory=temp_directory)
    return service


@pytest.mark.asyncio
async def test_register_model(ml_service: MlService, temp_file: str):
    file_name = os.path.basename(temp_file)
    version = 1
    map50 = 0.75
    map50_95 = 0.65
    precision = 0.8
    recall = 0.9

    await ml_service.register_model(file_name, version, temp_file, map50, map50_95, precision, recall)

    model_list = await ml_service.get_model_list()
    model_names = [model['file_name'] for model in model_list]

    assert file_name in model_names, f"Model {file_name} was not registered."


@pytest.mark.asyncio
async def test_get_model_by_name(ml_service: MlService, temp_file: str):
    file_name = os.path.basename(temp_file)
    version = 1
    map50 = 0.75
    map50_95 = 0.65
    precision = 0.8
    recall = 0.9

    await ml_service.register_model(file_name, version, temp_file, map50, map50_95, precision, recall)

    model = await ml_service.get_model_by_name(file_name)

    assert model is not None, f"Model {file_name} was not found."
    assert model["file_name"] == file_name, f"Expected {file_name}, got {model['file_name']}."
    assert model["version"] == version, f"Expected {version}, got {model['version']}."
    assert model["file_path"] == temp_file, f"Expected {temp_file}, got {model['file_path']}."
    assert model["map50"] == map50, f"Expected {map50}, got {model['map50']}."
    assert model["map50_95"] == map50_95, f"Expected {map50_95}, got {model['map50_95']}."
    assert model["precision"] == precision, f"Expected {precision}, got {model['precision']}."
    assert model["recall"] == recall, f"Expected {recall}, got {model['recall']}."
    assert model["status"] == "pending", f"Expected status 'ready', got {model['status']}."  # model 등록시 최초 pending 상태로 초기화됨.


@pytest.mark.asyncio
async def test_delete_model(ml_service: MlService, temp_file: str):
    file_name = os.path.basename(temp_file)
    version = 1
    map50 = 0.75
    map50_95 = 0.65
    precision = 0.8
    recall = 0.9

    await ml_service.register_model(file_name, version, temp_file, map50, map50_95, precision, recall)
    await ml_service.delete_model(file_name)

    model_list = await ml_service.get_model_list()
    model_names = [model['file_name'] for model in model_list]

    assert file_name not in model_names, f"Model {file_name} was not deleted."


@pytest.mark.asyncio
async def test_get_model_list(ml_service: MlService, temp_directory):
    model_files = [
        ("model1.onnx", 0.7, 0.6, 0.8, 0.9),
        ("model2.onnx", 0.8, 0.7, 0.85, 0.95),
        ("model3.onnx", 0.75, 0.65, 0.82, 0.92)
    ]

    for file_name, map50, map50_95, precision, recall in model_files:
        temp_file_path = os.path.join(temp_directory, file_name)
        with open(temp_file_path, "wb") as f:
            f.write(b"dummy model content")
        
        await ml_service.register_model(file_name, 1, temp_file_path, map50, map50_95, precision, recall)

    model_list = await ml_service.get_model_list()
    model_names = [model['file_name'] for model in model_list]

    for file_name, *_ in model_files:
        assert file_name in model_names, f"{file_name} is not listed."


@pytest.mark.asyncio
async def test_update_model_status(ml_service: MlService, temp_file: str):
    file_name = os.path.basename(temp_file)
    version = 1
    map50 = 0.75
    map50_95 = 0.65
    precision = 0.8
    recall = 0.9

    await ml_service.register_model(file_name, version, temp_file, map50, map50_95, precision, recall)
    await ml_service.update_status(file_name, "running")

    model_list = await ml_service.get_model_status()
    updated_model_status = next((model for model in model_list if model['file_name'] == file_name), None)

    assert updated_model_status is not None, "Updated model is not found in the list."
    assert updated_model_status["status"] == "running", "Model status was not updated to 'running'."
