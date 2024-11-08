from pydantic import BaseModel
from typing import Optional, List


class FileValidationRequest(BaseModel):
    dataset_id: int


class ModelDeployRequest(BaseModel):
    m_id: str  # 모델 이름


class ModelCreateRequest(BaseModel):
    m_ext: Optional[str] = 'pt'  # 모델 확장자
    m_name: str
    b_m_name: Optional[str] = None  # 베이스 모델 이름
    zip_files: List[int]

    @property
    def file_name(self) -> str:
        return f"{self.m_name}.{self.m_ext}"
    

class InferenceGenerateRequest(BaseModel):
    inference_file_id: int  # InferenceFile ID
    m_id: int 