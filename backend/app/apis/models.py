from pydantic import BaseModel
from typing import Optional, List


class FileValidationRequest(BaseModel):
    file_name: str


class ModelDeployRequest(BaseModel):
    m_name: str  # model_name


class ModelCreateRequest(ModelDeployRequest):
    m_ext: Optional[str] = 'pt' # model_ext
    b_m_name: Optional[str] = None  # base_model_name
    zip_files: List[str]

    @property
    def file_name(self) -> str:
        return f"{self.m_name}.{self.m_ext}"