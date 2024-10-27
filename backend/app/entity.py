from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base, async_engine
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, Enum
from sqlalchemy.sql import func
import enum


class Status(enum.Enum):
    READY = "ready"
    PENDING = "pending"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"


class FileType(enum.Enum):
    PHOTO = "photo"
    VIDEO = "video"


class FileMeta(Base):
    __tablename__ = 'file_meta'

    id = Column(Integer, primary_key=True)
    filepath = Column(String, nullable=False)
    filesize = Column(Integer, nullable=False)
    creation_time = Column(DateTime(timezone=True), default=func.now())

    dataset = relationship("DataSet", uselist=False, back_populates="file_meta")
    ai_model_file = relationship("AiModel", foreign_keys="[AiModel.model_file_id]", back_populates="model_file")
    ai_deploy_file = relationship("AiModel", foreign_keys="[AiModel.deploy_file_id]", back_populates="deploy_file")
    inference_file_original = relationship("InferenceFile", foreign_keys="[InferenceFile.original_file_id]", back_populates="original_file")
    inference_file_generated = relationship("InferenceFile", foreign_keys="[InferenceFile.generated_file_id]", back_populates="generated_file")

    def serialize(self) -> dict:
        return {
            "id": self.id,
            "filepath": self.filepath,
            "filesize": self.filesize,
            "creation_time": self.creation_time.strftime('%Y-%m-%d %H:%M:%S') if self.creation_time else None,
        }


class DataSet(Base):
    __tablename__ = 'dataset'

    id = Column(Integer, primary_key=True)
    filename = Column(String, unique=True, nullable=False)
    status = Column(Enum(Status), nullable=False, default=Status.READY)
    is_delete = Column(Boolean, default=False)

    file_meta_id = Column(Integer, ForeignKey('file_meta.id'), nullable=False)
    file_meta = relationship("FileMeta", back_populates="dataset")

    def serialize(self) -> dict:
        return {
            "id": self.id,
            "filename": self.filename,
            "status": self.status.value,
            "is_delete": self.is_delete,
            "file_meta": self.file_meta.serialize() if self.file_meta else None,
        }


class AiModel(Base):
    __tablename__ = 'ai_model'

    id = Column(Integer, primary_key=True)
    modelname = Column(String, unique=True, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    map50 = Column(Float, nullable=True)        
    map50_95 = Column(Float, nullable=True)     
    precision = Column(Float, nullable=True)   
    recall = Column(Float, nullable=True)     
    classes = Column(String, nullable=True)
    status = Column(Enum(Status), nullable=False, default=Status.READY)
    is_delete = Column(Boolean, default=False)
    is_deploy = Column(Boolean, default=False)

    base_model_id = Column(Integer, ForeignKey('ai_model.id'), nullable=True)  # 자기참조 외래 키
    base_model = relationship("AiModel", remote_side=[id], backref="derived_models")

    model_file_id = Column(Integer, ForeignKey('file_meta.id'), nullable=True)
    model_file = relationship("FileMeta", foreign_keys=[model_file_id], back_populates="ai_model_file")  # 모델 생성 시

    deploy_file_id = Column(Integer, ForeignKey('file_meta.id'), nullable=True)
    deploy_file = relationship("FileMeta", foreign_keys=[deploy_file_id], back_populates="ai_deploy_file")

    def serialize(self) -> dict:
        return {
            "id": self.id,
            "modelname": self.modelname,
            "version": self.version,
            "map50": self.map50,
            "map50_95": self.map50_95,
            "precision": self.precision,
            "recall": self.recall,
            "classes": self.classes.split(',') if self.classes else None,
            "status": self.status.value,
            "is_delete": self.is_delete,
            "is_deploy": self.is_deploy,
            "base_model": self.base_model.serialize() if self.base_model else None,
            "model_file": self.model_file.serialize() if self.model_file else None,
            "deploy_file": self.deploy_file.serialize() if self.deploy_file else None,
        }


class InferenceFile(Base):
    __tablename__ = 'inference_files'

    id = Column(Integer, primary_key=True)

    original_file_name = Column(String, nullable=True)
    generated_file_name = Column(String, nullable=True)
    file_type = Column(Enum(FileType), nullable=False, default=FileType.PHOTO)
    is_delete = Column(Boolean, default=False)

    original_file_id = Column(Integer, ForeignKey('file_meta.id'), nullable=True)
    original_file = relationship("FileMeta", foreign_keys=[original_file_id], back_populates="inference_file_original")

    generated_file_id = Column(Integer, ForeignKey('file_meta.id'), nullable=True)
    generated_file = relationship("FileMeta", foreign_keys=[generated_file_id], back_populates="inference_file_generated")

    status = Column(Enum(Status), nullable=False, default=Status.READY)

    def serialize(self) -> dict:
        return {
            "id": self.id,
            "original_file_name": self.original_file_name,
            "generated_file_name": self.generated_file_name,
            "file_type": self.file_type.value,
            "is_delete": self.is_delete,
            "status": self.status.value,
            "original_file": self.original_file.serialize() if self.original_file else None,
            "generated_file": self.generated_file.serialize() if self.generated_file else None,
        }


async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
