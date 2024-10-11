from fastapi import UploadFile, HTTPException, File


def validate_zip_file(file: UploadFile = File(...)):
    if not file.filename.lower().endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only ZIP files are allowed")

    return file