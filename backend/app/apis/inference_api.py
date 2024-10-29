from fastapi import APIRouter, UploadFile, Depends
from typing import List
from app.apis.models import InferenceGenerateRequest
from app.validation import validate_inference_file
from app.services.inference_service import get_inference_service, InferenceService
from app.tasks.main import generate_inference_task


router = APIRouter()


# 파일 업로드
@router.post("/upload", response_model=dict)
async def upload_file(file: UploadFile = Depends(validate_inference_file), inference_service: InferenceService = Depends(get_inference_service)):
    original_file_name = await inference_service.upload_file(file)
    return {"original_file_name": original_file_name}


@router.post("/generate", response_model=dict)
async def generate_inference_file(request: InferenceGenerateRequest):
    generate_inference_task.delay(request.original_file_name)
    return { 'result': True }


# 파일 삭제
@router.delete("/{original_file_name}", response_model=dict)
async def delete_file(original_file_name: str, inference_service: InferenceService = Depends(get_inference_service)):
    await inference_service.delete_file(original_file_name)
    return {"original_file_name": original_file_name}


# 파일 목록
@router.get("/list", response_model=List[dict])
async def get_file_list(inference_service: InferenceService = Depends(get_inference_service)):
    return await inference_service.get_file_list()


@router.get("/status", response_model=List[dict])
async def get_file_status(inference_service: InferenceService = Depends(get_inference_service)):
    return await inference_service.get_file_status()