from app.database import Base, async_engine
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func


class FileMeta(Base):
    __tablename__ = 'files'
    
    id = Column(Integer, primary_key=True)
    filename = Column(String, unique=True, nullable=False)
    filepath = Column(String, nullable=False)
    filesize = Column(Integer, nullable=False)
    creation_time = Column(DateTime(timezone=True), default=func.now())  # 파일 생성 시간
    is_delete = Column(Boolean, default=False)  # 논리적 삭제 여부


async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)