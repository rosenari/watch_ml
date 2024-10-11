from fastapi import APIRouter, UploadFile, HTTPException, Depends
from typing import List
from app.services.file_service import FileService

router = APIRouter()
file_service = FileService()


@router.post("/upload", response_model=str)
async def upload_file(file: UploadFile):
    try:
        file_path = await file_service.upload_file(file)
        return file_path
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/delete/{file_name}")
async def delete_file(file_name: str):
    try:
        file_service.delete_file(file_name)
        return {"message": f"File '{file_name}' deleted successfully"}
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/files", response_model=List[str])
async def get_file_list():
    try:
        return file_service.get_file_list()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
