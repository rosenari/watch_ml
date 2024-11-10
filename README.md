<h1 style="text-align: center;">YOLO STUDIO</h1>

YOLO STUDIO는 YOLO 사전 학습 모델을 기반으로 데이터셋을 학습하여 새로운 모델을 생성, 보관하고, Triton Inference Server를 통해 실시간 추론을 수행해 결과 파일을 제공합니다.


## 개발 환경

### 사전 요구 사항
- CUDA 12.6을 지원하는 NVIDIA 그래픽 카드 및 드라이버 ( >= NVIDIA RTX 3000 Series)
- docker
- docker-compose
- Nodejs

### 개발 환경 구성
#### backend
```bash
docker-compose up -d
```

#### dashboard
```bash
cd dashboard

yarn install

npm run start
```


## 시스템 아키텍처

![system](https://github.com/user-attachments/assets/24b166ec-adbf-4b17-b982-52c1038933a3)

- **uvicorn(FastAPI)**: 클라이언트 요청에 따라 postgresql에 데이터를 저장하고 task queue에 task를 적재합니다. (비동기 데이터베이스 드라이버를 기반으로 postgresql와 통신)
- **postgrsql**: 모델, 데이터셋, 추론파일에 대한 정보를 저장합니다. 
- **redis**: celery task queue로 활용되며, 모델 학습 시 진행률을 저장합니다.
- **celery worker**: 파일 검사, 모델 학습/배포, 추론을 수행합니다. (추론 및 배포시 triton server와 grpc 통신)
- **triton inference server**: 실시간 추론 서버입니다.
- **fluentd**: fastapi와 celery worker 컨테이너에서 전달하는 로그를 필터링하여, elastic search에 전달합니다.
- **elastic search**: 전달된 로그를 저장 및 검색하는 검색 엔진입니다.
- **kibana**: elastic search에 저장된 데이터를 시각화하고 대시보드를 구성하는 도구입니다.

## ERD
<p align="center">
  <img src="https://github.com/user-attachments/assets/dc85adc8-b0ae-4d50-9427-963f261e99eb" width="70%">
</p>

## 기술 스택
### backend
- python 3.11
- postgresql 14
- redis 7.4
- tritonserver 24.08
- fastapi 0.115
- celery 5.4
- SQLAlchemy 2.0.36
- opencv-python
- ultralytics 8.3.8
- torch 2.4.1

### dashboard
- react 18.3.1
- antd 5.21.3
- jotai 2.10.1

## 기능 설명

### 데이터 셋 아카이브 업로드
![datasetupload](https://github.com/user-attachments/assets/65e289c7-efe6-4e40-9bbd-5fac9ecdbb91)
> zip 파일 형태의 데이터 셋 아카이브를 업로드 할 수 있습니다.

### 데이터 셋 파일 검사
<p align="center">
  <img src="https://github.com/user-attachments/assets/11ebbe97-3ded-482a-bd8e-5cb49783dcc6">
</p>
> 업로드된 아카이브 내 data.yaml, 디렉터리/파일 구조, 라벨 파일을 차례로 분석합니다.

![valid](https://github.com/user-attachments/assets/418e55d1-f51d-4f09-b9f9-5436462c164f)
> 검사 중에는 스피너가 돌며 완료 시 체크 표시가 노출됩니다.

### 모델 학습 및 배포
<p align="center">
  <img src="https://github.com/user-attachments/assets/fa2faab6-fbd9-4259-83ce-2c359b7a9484">
</p>
> 여러 아카이브를 선택하고 base 모델을 기반으로 생성을 요청하면 병합하여 학습을 진행합니다.

![train](https://github.com/user-attachments/assets/7df59e72-0d92-4d49-9589-e8473edfe368)
> 학습 시 진행률이 실시간으로 표시되며 완료 시 배포가 가능해집니다.

### 이미지/영상 파일 업로드
![fileupload](https://github.com/user-attachments/assets/e3fa9c35-3fd5-4bd0-b988-b2d44f9aa925)
> 추론을 위한 이미지/영상 파일을 업로드 할 수 있습니다.

### 추론
<p align="center">
  <img src="https://github.com/user-attachments/assets/040d0fa0-4b08-4789-b778-91e25bddd6f1">
</p>
> 검사, 학습, 배포, 추론 과정에서 폴링 모듈은 status 상태에 따라 요청을 반복할지 멈출지 결정합니다.

![inference](https://github.com/user-attachments/assets/55e6dd2f-75b9-42e3-9853-467bbab0dfd6)
> 이미지 또는 영상을 선택하고 배포된 모델을 선택하여 추론을 수행하면 결과 파일이 생성됩니다.

### 추론 결과 확인
<p align="center">
<img src="https://github.com/user-attachments/assets/a80d4474-614f-4311-9aa3-9764c507e803">
</p>
