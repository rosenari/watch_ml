#!/bin/bash

# 모델 정보 출력

TRITON_SERVER_URL="localhost:8000"

curl -X POST "${TRITON_SERVER_URL}/v2/repository/index" \
     -H "Content-Type: application/json" \
     -d '{"ready": true}' \
     -w "\n"