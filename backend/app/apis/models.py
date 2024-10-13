from pydantic import BaseModel


class FileValidationRequest(BaseModel):
    file_name: str