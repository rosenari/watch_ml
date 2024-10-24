from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base, async_engine
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float, UniqueConstraint, Enum
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
    ai_model = relationship("AiModel", uselist=False, back_populates="file_meta")
    inference_file_original = relationship("InferenceFile", foreign_keys="[InferenceFile.original_file_id]", back_populates="original_file")
    inference_file_generated = relationship("InferenceFile", foreign_keys="[InferenceFile.generated_file_id]", back_populates="generated_file")


class DataSet(Base):
    __tablename__ = 'dataset'

    id = Column(Integer, primary_key=True)
    filename = Column(String, unique=True, nullable=False)
    status = Column(Enum(Status), nullable=False, default=Status.READY)
    is_delete = Column(Boolean, default=False)

    file_meta_id = Column(Integer, ForeignKey('file_meta.id'), nullable=False)
    file_meta = relationship("FileMeta", back_populates="dataset", cascade="all, delete")


class AiModel(Base):
    __tablename__ = 'ai_model'

    id = Column(Integer, primary_key=True)
    filename = Column(String, unique=True, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    map50 = Column(Float, nullable=True)        
    map50_95 = Column(Float, nullable=True)     
    precision = Column(Float, nullable=True)   
    recall = Column(Float, nullable=True)     
    classes = Column(String, nullable=True)  
    is_deploy = Column(Boolean, default=False)
    status = Column(Enum(Status), nullable=False, default=Status.READY)
    is_delete = Column(Boolean, default=False)

    file_meta_id = Column(Integer, ForeignKey('file_meta.id'), nullable=True)
    file_meta = relationship("FileMeta", back_populates="ai_model", cascade="all, delete")


class InferenceFile(Base):
    __tablename__ = 'inference_files'

    id = Column(Integer, primary_key=True)

    original_file_name = Column(String, nullable=True)
    generated_file_name = Column(String, nullable=True)
    original_file_id = Column(Integer, ForeignKey('file_meta.id'), nullable=True)
    generated_file_id = Column(Integer, ForeignKey('file_meta.id'), nullable=True)
    file_type = Column(Enum(FileType), nullable=False, default=FileType.PHOTO)
    is_delete = Column(Boolean, default=False)

    original_file = relationship("FileMeta", foreign_keys=[original_file_id], back_populates="inference_file_original")
    generated_file = relationship("FileMeta", foreign_keys=[generated_file_id], back_populates="inference_file_generated")

    status = Column(Enum(Status), nullable=False, default=Status.READY)


async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
