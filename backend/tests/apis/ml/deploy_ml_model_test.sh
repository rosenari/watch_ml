#!/bin/bash

API_URL="http://localhost:5000/ml/deploy"

MODEL_NAME="example_model"
MODEL_TYPE="onnx"

curl -X POST "$API_URL" \
     -H "Content-Type: application/json" \
     -d "{\"m_name\": \"$MODEL_NAME\", \"m_type\": \"$MODEL_TYPE\"}" \
     -w "\n"