from fastapi import APIRouter, Depends
from app.services.ml_service import get_ml_service, MlService
from app.services.dataset_service import get_dataset_service, DataSetService
from app.apis.models import ModelCreateRequest, ModelDeployRequest
from app.tasks.main import create_model_task, deploy_model_task, undeploy_model_task
from typing import List


router = APIRouter()


@router.post('/create', response_model=dict)
async def create_ml_model(request: ModelCreateRequest, ml_service: MlService = Depends(get_ml_service), dataset_service: DataSetService = Depends(get_dataset_service)):
    version = await ml_service.init_model(request.m_name, request.b_m_name)
    zip_files = [await dataset_service.get_dataset_by_id(zip_file_id) for zip_file_id in request.zip_files]
    zip_file_paths = [zip_file['file_meta']['filepath'] for zip_file in zip_files]
    create_model_task.delay(request.m_name, request.m_ext, version, zip_file_paths)

    return { 'result': True }
    

@router.post('/deploy', response_model=dict)
async def deploy_ml_model(request: ModelDeployRequest, ml_service: MlService = Depends(get_ml_service)):
    await ml_service.update_status(request.m_id, 'pending')
    deploy_model_task.delay(request.m_id)

    return { 'result': True }
    

@router.post('/undeploy', response_model=dict)
async def undeploy_ml_model(request: ModelDeployRequest, ml_service: MlService = Depends(get_ml_service)):
    await ml_service.update_status(request.m_id, 'pending')
    undeploy_model_task.delay(request.m_id)

    return { 'result': True }


@router.get('/status', response_model=List[dict])
async def get_ml_status(ml_service: MlService = Depends(get_ml_service)):
    ml_status_list = await ml_service.get_model_status()
    
    return ml_status_list


@router.get('/list', response_model=List[dict])
async def get_ml_status(ml_service: MlService = Depends(get_ml_service)):
    ml_list = await ml_service.get_model_list()
    
    return ml_list