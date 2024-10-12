FROM python:3.9-slim

# 작업 디렉토리 설정
WORKDIR /app

# 파이썬 종속성 설치
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Celery 작업 복사
COPY *.py /app/

# Celery 워커 실행
CMD ["celery", "-A", "app.tasks", "worker", "--loglevel=info"]