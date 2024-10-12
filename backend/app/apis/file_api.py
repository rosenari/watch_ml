from fastapi import APIRouter, UploadFile, HTTPException, Depends
from typing import List
from app.services.file_service import FileService
from app.repositories.file_repository import FileRepository
from app.validation import validate_zip_file
from app.database import get_redis
from app.tasks.main import valid_archive


router = APIRouter()
file_service = FileService(FileRepository())


# 파일 업로드
@router.post("/upload", response_model=dict)
async def upload_file(file: UploadFile = Depends(validate_zip_file)):
    try:
        file_name = await file_service.upload_file(file)
        return {"file_name": file_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 파일 삭제
@router.delete("/{file_name}", response_model=dict)
async def delete_file(file_name: str):
    try:
        file_service.delete_file(file_name)
        return {"file_name": file_name}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# 파일 목록
@router.get("/list", response_model=List[dict])
async def get_file_list():
    try:
        return file_service.get_file_list()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post('/validation', response_model=dict)
async def valid_file(file_name: str, ri = Depends(get_redis)):
    try:
        key = f"valid:{file_name}"
        await ri.set(key, "pending")
        valid_archive.delay(file_name)

        return { 'result': True }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
