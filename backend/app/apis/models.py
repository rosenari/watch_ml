from pydantic import BaseModel


class FileValidationRequest(BaseModel):
    file_name: str


class ModelCreateRequest(BaseModel):
    name: str
    zip_files: list[str]