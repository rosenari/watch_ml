from fastapi import APIRouter, HTTPException, Depends
from app.apis.models import ModelCreateRequest
from app.database import get_redis
from app.tasks.main import create_model


router = APIRouter()


@router.post('', response_model=dict)
async def create_ml_model(request: ModelCreateRequest, ri = Depends(get_redis)):
    try:
        key = f"model:{request.name}"
        await ri.set(key, "pending")
        create_model.delay(request.name, request.zip_files)

        return { 'result': True }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))