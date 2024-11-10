from fastapi import APIRouter, UploadFile, Depends, Query
from typing import List, Optional
from app.apis.models import FileValidationRequest
from app.validation import validate_zip_file
from app.tasks.main import valid_archive_task
from app.services.dataset_service import get_dataset_service, DataSetService


router = APIRouter()


# 파일 업로드
@router.post("/upload", response_model=dict)
async def upload_file(
    file: UploadFile = Depends(validate_zip_file), 
    dataset_service: DataSetService = Depends(get_dataset_service)
):
    return await dataset_service.upload_file(file)


# 파일 삭제
@router.delete("/{dataset_id}", response_model=dict)
async def delete_file(
    dataset_id: int,
    dataset_service: DataSetService = Depends(get_dataset_service)
):
    result = await dataset_service.delete_file(dataset_id)
    return {"result": result}


# 파일 목록
@router.get("/list", response_model=List[dict])
async def get_file_list(
    last_id: Optional[int] = Query(None),
    dataset_service: DataSetService = Depends(get_dataset_service)
):
    return await dataset_service.get_file_list(last_id=last_id)


# 파일 유효성 검사 시작
@router.post('/validation', response_model=dict)
async def valid_file(
    request: FileValidationRequest, 
    dataset_service: DataSetService = Depends(get_dataset_service)
):
    await dataset_service.update_status(request.dataset_id, 'pending')
    valid_archive_task.delay(request.dataset_id)
    return {'result': True}
    

# 파일 상태 확인
@router.get('/status', response_model=List[dict])
async def get_valid_files(
    dataset_service: DataSetService = Depends(get_dataset_service)
):
    return await dataset_service.get_file_status()
