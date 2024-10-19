from app.database import Base, async_engine
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Float
from sqlalchemy.sql import func


class CommonFields:
    id = Column(Integer, primary_key=True)
    filepath = Column(String, nullable=False)  # 파일 경로
    creation_time = Column(DateTime(timezone=True), default=func.now())
    is_delete = Column(Boolean, default=False)


class FileMeta(CommonFields, Base):
    __tablename__ = 'files'
    
    filename = Column(String, unique=True, nullable=False)
    filesize = Column(Integer, nullable=False)


class AiModel(CommonFields, Base):
    __tablename__ = 'ai'

    modelname = Column(String, unique=True, nullable=False)
    map50 = Column(Float, nullable=True)        
    map50_95 = Column(Float, nullable=True)     
    precision = Column(Float, nullable=True)   
    recall = Column(Float, nullable=True)       
    is_deploy = Column(Boolean, default=False)


async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)