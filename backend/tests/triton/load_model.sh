#!/bin/bash

# 모델 수동 로드

TRITON_SERVER_URL="localhost:8000"
MODEL_NAME="example_model"

curl -X POST "${TRITON_SERVER_URL}/v2/repository/models/${MODEL_NAME}/load" \
     -H "Content-Type: application/json"