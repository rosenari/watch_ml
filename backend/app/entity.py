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


class CommonFields:
    id = Column(Integer, primary_key=True)
    filepath = Column(String, nullable=False)  # 파일 경로
    creation_time = Column(DateTime(timezone=True), default=func.now())
    is_delete = Column(Boolean, default=False)
    status = Column(Enum(Status), nullable=False, default=Status.READY)


class FileMeta(CommonFields, Base):
    __tablename__ = 'files'
    
    filename = Column(String, unique=True, nullable=False)
    filesize = Column(Integer, nullable=False)


class AiModel(CommonFields, Base):
    __tablename__ = 'ai'

    modelname = Column(String, nullable=False)
    version = Column(Integer, nullable=False, default=1)
    map50 = Column(Float, nullable=True)        
    map50_95 = Column(Float, nullable=True)     
    precision = Column(Float, nullable=True)   
    recall = Column(Float, nullable=True)       
    is_deploy = Column(Boolean, default=False)

    __table_args__ = (UniqueConstraint('modelname', 'version', name='_modelname_version_uc'),)


async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)