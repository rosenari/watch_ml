#!/bin/bash

curl -X POST "http://localhost:5000/ml/create" \
-H "Content-Type: application/json" \
-d '{
    "name": "example_model",
    "zip_files": ["night.zip", "sunset.zip"]
}'