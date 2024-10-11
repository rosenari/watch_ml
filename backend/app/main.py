from fastapi import FastAPI
from app.apis import file_api

app = FastAPI()

# 파일 관련 API 라우터 등록
app.include_router(file_api.router, prefix="/files")