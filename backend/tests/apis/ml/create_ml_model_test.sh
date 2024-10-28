#!/bin/bash

curl -X POST "http://localhost:5000/ml/create" \
-H "Content-Type: application/json" \
-d '{
    "m_name": "example_model",
    "b_m_name": "yolov10n"
    "zip_files": ["night.zip"]
}'

# yolov10n, yolov10s