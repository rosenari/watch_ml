from fastapi import APIRouter, HTTPException, Depends
from app.services.ml_service import get_ml_service, MlService
from app.apis.models import ModelCreateRequest
from app.tasks.main import create_model_task


router = APIRouter()


@router.post('/create', response_model=dict)
async def create_ml_model(request: ModelCreateRequest, ml_service: MlService = Depends(get_ml_service)):
    try:
        version = await ml_service.init_model(request.name)
        create_model_task.delay(request.name, version, request.zip_files)

        return { 'result': True }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))