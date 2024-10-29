from fastapi import UploadFile, File
from app.config import PHOTO_EXTENSIONS, VIDEO_EXTENSIONS
from app.exceptions import BadRequestException


def validate_zip_file(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".zip"):
        raise BadRequestException("Only ZIP files are allowed")

    return file


def validate_inference_file(file: UploadFile = File(...)):
    # 파일 확장자 추출
    extension = file.filename.rsplit(".")[-1].lower()

    # 이미지 또는 비디오 확장자인지 확인
    if extension not in PHOTO_EXTENSIONS and extension not in VIDEO_EXTENSIONS:
        raise BadRequestException("Only image (jpg, jpeg, png) and video (mov, mp4, avi, mkv) files are allowed")

    return file