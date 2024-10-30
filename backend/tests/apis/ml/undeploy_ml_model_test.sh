#!/bin/bash

API_URL="http://localhost:5000/ml/undeploy"

MODEL_NAME="fashion_model"

curl -X POST "$API_URL" \
     -H "Content-Type: application/json" \
     -d "{\"m_name\": \"$MODEL_NAME\"}" \
     -w "\n"