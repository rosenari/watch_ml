#!/bin/bash

curl -X POST "http://localhost:5000/ml/create" \
-H "Content-Type: application/json" \
-d '{
    "m_name": "hello_model",
    "b_m_name": "example_model"
    "zip_files": ["night.zip", "sunset.zip"]
}'