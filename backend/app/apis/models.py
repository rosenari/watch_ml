from pydantic import BaseModel


class FileValidationRequest(BaseModel):
    file_name: str


class ModelCreateRequest(BaseModel):
    model_name: str  # model_name
    model_type: str  # model_type
    zip_files: list[str]

    @property
    def file_name(self) -> str:
        return f"{self.model_name}.{self.model_type}"