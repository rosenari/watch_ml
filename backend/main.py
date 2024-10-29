from fastapi import FastAPI, Request
from app.apis import dataset_api, ml_api, inference_api
from app.entity import create_tables
from app.exceptions import ForbiddenException, NotFoundException, BadRequestException
from app.repositories.ml_repository import create_base_model
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    await create_base_model()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 허용할 출처 목록
    allow_credentials=True,  # 자격 증명(쿠키 등) 허용 여부
    allow_methods=["*"],  # 모든 HTTP 메서드 허용 (GET, POST, PUT 등)
    allow_headers=["*"],  # 모든 헤더 허용
)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logging.error(exc.message)

    if isinstance(exc, NotFoundException):
        return JSONResponse(
            status_code=404,
            content={"message": exc.message},
        )
    elif isinstance(exc, ForbiddenException):
        return JSONResponse(
            status_code=403,
            content={"message": exc.message},
        )
    elif isinstance(exc, BadRequestException):
        return JSONResponse(
            status_code=400,
            content={"message": exc.message},
        )
    # 기타 예외는 500 상태 코드로 반환
    return JSONResponse(
        status_code=500,
        content={"message": "서버에서 알 수 없는 에러가 발생했습니다."},
    )


# 파일 관련 API 라우터 등록
app.include_router(dataset_api.router, prefix="/dataset")
app.include_router(ml_api.router, prefix="/ml")
app.include_router(inference_api.router, prefix="/inference")