from dataclasses import dataclass
from typing import List, Optional


@dataclass
class AiModelDTO:
    model_name: str
    base_model_name: str = None
    version: int = 1
    model_path: str = None
    deploy_path: str = None
    map50: Optional[float] = None
    map50_95: Optional[float] = None
    precision: Optional[float] = None
    recall: Optional[float] = None
    classes: Optional[List[str]] = None