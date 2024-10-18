from fastapi import APIRouter, UploadFile, HTTPException, Depends
from typing import List
from app.apis.models import FileValidationRequest
from app.validation import validate_zip_file
from app.database import get_redis
from app.tasks.main import valid_archive
from app.services.file_service import get_file_service, FileService


router = APIRouter()


# 파일 업로드
@router.post("/upload", response_model=dict)
async def upload_file(file: UploadFile = Depends(validate_zip_file), file_service: FileService = Depends(get_file_service)):
    try:
        file_name = await file_service.upload_file(file)
        return {"file_name": file_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 파일 삭제
@router.delete("/{file_name}", response_model=dict)
async def delete_file(file_name: str, file_service: FileService = Depends(get_file_service)):
    try:
        file_service.delete_file(file_name)
        return {"file_name": file_name}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 파일 목록
@router.get("/list", response_model=List[dict])
async def get_file_list(file_service: FileService = Depends(get_file_service)):
    try:
        return file_service.get_file_list()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/validation', response_model=dict)
async def valid_file(request: FileValidationRequest, ri = Depends(get_redis)):
    try:
        key = f"valid:{request.file_name}"
        await ri.set(key, "pending")
        valid_archive.delay(request.file_name)

        return { 'result': True }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get('/validation', response_model=List[dict])
async def get_valid_files(file_service: FileService = Depends(get_file_service)):
    try:
        return await file_service.get_valid_file_list()
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail=str(e))