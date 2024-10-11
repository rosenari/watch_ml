from fastapi import UploadFile, HTTPException, File


def validate_zip_mime_type(file: UploadFile = File(...)):
    if file.content_type != "application/zip":
        raise HTTPException(status_code=400, detail="Only ZIP files are allowed")

    return file