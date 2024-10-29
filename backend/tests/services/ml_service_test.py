import os
import pytest
import pytest_asyncio
from app.database import get_redis
from app.services.ml_service import MlService, AiModelDTO
from app.exceptions import ForbiddenException
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
def temp_model(temp_directory):
    model_name = 'temp_model'
    temp_model_path = os.path.join(temp_directory, f"{model_name}.pt")
    with open(temp_model_path, "wb") as tmp_model:
        tmp_model.write(b"dummy model content")
    yield temp_model_path, model_name


@pytest.fixture
def ml_service(redis, session) -> MlService:
    service = MlService(redis, session)
    return service


@pytest.mark.asyncio
async def test_init_model(ml_service: MlService):
    model_name = 'temp_init_model'
    base_model_name = 'yolov10s'  # 앱 실행 시 자동등록되는 모델

    await ml_service.init_model(model_name=model_name, base_model_name=base_model_name)
    model = await ml_service.get_model_by_name(model_name=model_name)
    
    assert model_name == model['model_name'], f"Model {model_name} was not registered."
    assert model['base_model']['model_name'] == 'yolov10s', f"Base Model {base_model_name} was not registered."
    assert model['base_model']['model_file']['filepath'] == f"{base_model_name}.pt", f"Base Model Path {base_model_name}.pt was not registered."


@pytest.mark.asyncio
async def test_register_model(ml_service: MlService, temp_model: str):
    model_path, model_name = temp_model
    classes = ['bus', 'truck']

    await ml_service.register_model(AiModelDTO(
        model_name=model_name,
        model_path=model_path,
        classes=classes
    ))

    model = await ml_service.get_model_by_name(model_name=model_name)

    assert model_name == model['model_name'], f"Model {model_name} was not registered."
    assert model['base_model'] == None, f"Base Model was registered."
    assert model['model_file']['filepath'] == model_path, f"Model Path {model_path} was not registered."


@pytest.mark.asyncio
async def test_register_model_error(ml_service: MlService, temp_model: str):
    model_path, model_name = temp_model
    classes = ['bus', 'truck']

    await ml_service.register_model(AiModelDTO(
        model_name='base_model',
    ))

    with pytest.raises(ForbiddenException):
        await ml_service.register_model(AiModelDTO(
            model_name=model_name,
            model_path=model_path,
            base_model_name='base_model',
            classes=classes
        ))

    model = await ml_service.get_model_by_name(model_name=model_name)

    assert model == None,  f"Model {model_name} was registered."


@pytest.mark.asyncio
async def test_get_model_by_name(ml_service: MlService, temp_model: str):
    model_path, model_name = temp_model
    version = 1
    map50 = 0.75
    map50_95 = 0.65
    precision = 0.8
    recall = 0.9
    classes = ['car']

    await ml_service.register_model(AiModelDTO(
        model_name=model_name,
        model_path=model_path,
        version=version,
        map50=map50,
        map50_95=map50_95,
        precision=precision,
        recall=recall,
        classes=classes
    ))
    model = await ml_service.get_model_by_name(model_name)

    assert model is not None, f"Model {model_name} was not found."
    assert model["model_name"] == model_name, f"Expected {model_name}, got {model['model_name']}."
    assert model["version"] == version, f"Expected {version}, got {model['version']}."
    assert model["model_file"]["filepath"] == model_path, f"Expected {model_path}, got {model['model_file']['filepath']}."
    assert model["map50"] == map50, f"Expected {map50}, got {model['map50']}."
    assert model["map50_95"] == map50_95, f"Expected {map50_95}, got {model['map50_95']}."
    assert model["precision"] == precision, f"Expected {precision}, got {model['precision']}."
    assert model["recall"] == recall, f"Expected {recall}, got {model['recall']}."
    assert model["classes"] == classes, f"Expected {classes}, got {model['classes']}."
    assert model["status"] == "pending", f"Expected status 'ready', got {model['status']}."  # model 등록시 최초 pending 상태로 초기화됨.


@pytest.mark.asyncio
async def test_update_model(ml_service: MlService, temp_model: str):
    model_path, model_name = temp_model
    version = 1
    map50 = 0.75
    map50_95 = 0.65
    precision = 0.8
    recall = 0.9

    await ml_service.register_model(AiModelDTO(
        model_name=model_name,
        version=version,
        model_path=model_path,
        map50=map50,
        map50_95=map50_95,
        precision=precision,
        recall=recall
    ))

    new_version = 2
    classes = ['car']

    await ml_service.update_model(AiModelDTO(
        model_name=model_name,
        version=new_version,
        classes=classes
    ))
    model = await ml_service.get_model_by_name(model_name)

    assert model is not None, f"Model {model_name} was not found."
    assert model["model_name"] == model_name, f"Expected {model_name}, got {model['model_name']}."
    assert model["version"] == new_version, f"Expected {new_version}, got {model['version']}."
    assert model["model_file"]["filepath"] == model_path, f"Expected {model_path}, got {model['model_file']['filepath']}."
    assert model["map50"] == map50, f"Expected {map50}, got {model['map50']}."
    assert model["map50_95"] == map50_95, f"Expected {map50_95}, got {model['map50_95']}."
    assert model["precision"] == precision, f"Expected {precision}, got {model['precision']}."
    assert model["recall"] == recall, f"Expected {recall}, got {model['recall']}."
    assert model["classes"] == classes, f"Expected {classes}, got {model['classes']}."
    assert model["status"] == "pending", f"Expected status 'ready', got {model['status']}."  # model 등록시 최초 pending 상태로 초기화됨.


@pytest.mark.asyncio
async def test_delete_model(ml_service: MlService, temp_model: str):
    model_path, model_name = temp_model
    version = 1
    map50 = 0.75
    map50_95 = 0.65
    precision = 0.8
    recall = 0.9

    await ml_service.register_model(AiModelDTO(
        model_name=model_name,
        version=version,
        model_path=model_path,
        map50=map50,
        map50_95=map50_95,
        precision=precision,
        recall=recall
    ))
    await ml_service.delete_model(model_name)

    model_list = await ml_service.get_model_list()
    model_names = [model['model_name'] for model in model_list]

    assert model_name not in model_names, f"Model {model_name} was not deleted."


@pytest.mark.asyncio
async def test_get_model_list(ml_service: MlService, temp_directory): # 여기부터 ~
    model_files = [
        ("model1", 0.7, 0.6, 0.8, 0.9),
        ("model2", 0.8, 0.7, 0.85, 0.95),
        ("model3", 0.75, 0.65, 0.82, 0.92)
    ]

    for model_name, map50, map50_95, precision, recall in model_files:
        model_file_path = os.path.join(temp_directory, f"{model_name}.pt")
        with open(model_file_path, "wb") as f:
            f.write(b"dummy model content")
        
        await ml_service.register_model(AiModelDTO(
            model_name=model_name,
            map50=map50,
            map50_95=map50_95,
            precision=precision,
            recall=recall
        ))

    model_list = await ml_service.get_model_list()
    model_names = [model['model_name'] for model in model_list]

    for model_name, *_ in model_files:
        assert model_name in model_names, f"{model_name} is not listed."


@pytest.mark.asyncio
async def test_get_model_classes(ml_service: MlService):
    model_name = 'test_model'
    classes = ['truck', 'bus']
    await ml_service.register_model(AiModelDTO(
        model_name=model_name,
        classes=classes
    ))

    model_classes = await ml_service.get_model_classes(model_name)

    assert classes == model_classes, f"Model classes was not registered to {classes}."


@pytest.mark.asyncio
async def test_update_status(ml_service: MlService):
    model_name = 'temp_model'

    await ml_service.register_model(AiModelDTO(
        model_name=model_name
    ))
    await ml_service.update_status(model_name, "running")

    model_list = await ml_service.get_model_status()
    updated_model = next((model for model in model_list if model['model_name'] == model_name), None)

    assert updated_model is not None, "Updated model is not found in the list."
    assert updated_model["status"] == "running", "Model status was not updated to 'running'."
