#!/bin/bash

API_URL="http://localhost:5000/ml/undeploy"

MODEL_ID=$1

curl -X POST "$API_URL" \
     -H "Content-Type: application/json" \
     -d "{\"m_id\": \"$MODEL_ID\"}" \
     -w "\n"