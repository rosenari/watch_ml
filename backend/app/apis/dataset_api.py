from fastapi import APIRouter, UploadFile, HTTPException, Depends
from typing import List
from app.apis.models import FileValidationRequest
from app.validation import validate_zip_file
from app.tasks.main import valid_archive_task
from app.services.dataset_service import get_dataset_service, DataSetService


router = APIRouter()


# 파일 업로드
@router.post("/upload", response_model=dict)
async def upload_file(file: UploadFile = Depends(validate_zip_file), dataset_service: DataSetService = Depends(get_dataset_service)):
    try:
        file_name = await dataset_service.upload_file(file)
        return {"file_name": file_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 파일 삭제
@router.delete("/{file_name}", response_model=dict)
async def delete_file(file_name: str, dataset_service: DataSetService = Depends(get_dataset_service)):
    try:
        await dataset_service.delete_file(file_name)
        return {"file_name": file_name}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 파일 목록
@router.get("/list", response_model=List[dict])
async def get_file_list(dataset_service: DataSetService = Depends(get_dataset_service)):
    try:
        return await dataset_service.get_file_list()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/validation', response_model=dict)
async def valid_file(request: FileValidationRequest, dataset_service: DataSetService = Depends(get_dataset_service)):
    try:
        await dataset_service.update_status(request.file_name, 'pending')
        valid_archive_task.delay(request.file_name)

        return { 'result': True }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get('/validation', response_model=List[dict])
async def get_valid_files(dataset_service: DataSetService = Depends(get_dataset_service)):
    try:
        return await dataset_service.get_file_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))