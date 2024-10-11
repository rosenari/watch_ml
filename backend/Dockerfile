FROM python:3.11-slim

WORKDIR /app

ARG ARCHIVE_PATH=/app/dataset_archive

COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r /app/requirements.txt

COPY ./app /app

RUN mkdir -p $ARCHIVE_PATH && chmod 777 $ARCHIVE_PATH

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
