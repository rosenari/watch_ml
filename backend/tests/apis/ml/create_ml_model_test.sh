#!/bin/bash

curl -X POST "http://localhost:5000/ml/create" \
-H "Content-Type: application/json" \
-d '{
    "model_name": "example_model",
    "model_type": "onnx",
    "zip_files": ["night.zip", "sunset.zip"]
}'