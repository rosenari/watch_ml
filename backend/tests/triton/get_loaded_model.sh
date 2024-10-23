#!/bin/bash

TRITON_SERVER_URL="localhost:8000"

curl -X POST "${TRITON_SERVER_URL}/v2/repository/index" \
     -H "Content-Type: application/json" \
     -d '{"ready": true}' \
     -w "\n"