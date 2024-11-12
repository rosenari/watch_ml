<h1 style="text-align: center;">YOLO STUDIO</h1>

YOLO STUDIO는 데이터셋 관리, 모델 생성 및 배포, 추론 기능을 제공하는 웹 기반 YOLO 파인튜닝 All-In-One 솔루션입니다.


## 개발 환경

### 사전 요구 사항
- CUDA 12.6을 지원하는 NVIDIA 그래픽 카드 및 드라이버 ( >= NVIDIA RTX 3000 Series)
- CUDA Toolkit
- WSL2
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

### 데이터 셋 관리
![데이터셋관리](https://github.com/user-attachments/assets/03b981b3-466b-4083-8772-0562269ab47a)
<img src="https://github.com/user-attachments/assets/11ebbe97-3ded-482a-bd8e-5cb49783dcc6">

- zip 파일 형태의 데이터 셋 아카이브를 업로드, 삭제하고 파일 정상 여부를 검사할 수 있습니다.
- 파일 검사의 경우 업로드된 아카이브 내 data.yaml, 디렉터리/파일 구조, 라벨 파일을 차례로 분석합니다.

### 무한 스크롤
![무한스크롤](https://github.com/user-attachments/assets/23f2c9f8-03ba-4981-9c2f-8ea867493263)
![image](https://github.com/user-attachments/assets/8fda0c91-d509-479a-867c-cf7dc5cacbc5)
- 커서 기반 페이지네이션에 기반한 무한스크롤이 가능합니다.

### 모델 학습
![모델생성](https://github.com/user-attachments/assets/f6bf8c9e-7589-42fd-9778-bd98989c695e)
<img src="https://github.com/user-attachments/assets/fa2faab6-fbd9-4259-83ce-2c359b7a9484">

- 여러 아카이브를 선택하고 base 모델을 기반으로 생성을 요청하면 병합하여 학습을 진행합니다.
- 학습 시 진행률이 실시간으로 표시되며 완료 시 배포가 가능해집니다.

### 모델 배포

![모델배포](https://github.com/user-attachments/assets/063c0ac7-acba-48f0-9340-9fe719a5d7e2)


### 추론

<img src="https://github.com/user-attachments/assets/040d0fa0-4b08-4789-b778-91e25bddd6f1">

- 검사, 학습, 배포, 추론 과정에서 폴링 모듈은 status 상태에 따라 요청을 반복할지 멈출지 결정합니다.

![추론](https://github.com/user-attachments/assets/68e43fef-7064-409d-9070-74bc685dfd6e)

- 이미지 또는 영상을 선택하고 배포된 모델을 선택하여 추론을 수행하면 결과 파일이 생성됩니다.

### 추론 결과 확인
<img src="https://github.com/user-attachments/assets/a80d4474-614f-4311-9aa3-9764c507e803">


### 모니터링
![image](https://github.com/user-attachments/assets/80c64c08-d75d-4f6e-a1b2-1e2979ea75b2)

- fluentd를 통해 fastapi와 celery worker의 로그를 수집하고, 이를 elastic search에 저장 kibana를 통해 대시보드를 구성하여 모니터링합니다.
