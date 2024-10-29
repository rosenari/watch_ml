from fastapi import APIRouter, Depends
from app.services.ml_service import get_ml_service, MlService
from app.apis.models import ModelCreateRequest, ModelDeployRequest
from app.tasks.main import create_model_task, deploy_model_task, undeploy_model_task


router = APIRouter()


@router.post('/create', response_model=dict)
async def create_ml_model(request: ModelCreateRequest, ml_service: MlService = Depends(get_ml_service)):
    version = await ml_service.init_model(request.m_name, request.b_m_name)
    create_model_task.delay(request.m_name, request.m_ext, version, request.zip_files)

    return { 'result': True }
    

@router.post('/deploy', response_model=dict)
async def deploy_ml_model(request: ModelDeployRequest):
    deploy_model_task.delay(request.m_name)

    return { 'result': True }
    

@router.post('/undeploy', response_model=dict)
async def deploy_ml_model(request: ModelDeployRequest):
    undeploy_model_task.delay(request.m_name)

    return { 'result': True }