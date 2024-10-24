#!/bin/bash

curl -X POST "http://localhost:5000/ml/create" \
-H "Content-Type: application/json" \
-d '{
    "m_name": "example_model",
    "m_type": "onnx",
    "zip_files": ["night.zip"]
}'