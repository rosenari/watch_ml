from pydantic import BaseModel


class FileValidationRequest(BaseModel):
    file_name: str


class ModelCreateRequest(BaseModel):
    m_name: str  # model_name
    m_type: str  # model_type
    zip_files: list[str]

    @property
    def file_name(self) -> str:
        return f"{self.m_name}.{self.m_type}"
    

class ModelDeployRequest(BaseModel):
    m_name: str  # model_name
    m_type: str  # model_type

    @property
    def file_name(self) -> str:
        return f"{self.m_name}.{self.m_type}"