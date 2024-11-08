#!/bin/bash

INFERENCE_ID=$1
MODEL_ID=$2

curl -X POST "http://localhost:5000/inference/generate" \
-H "Content-Type: application/json" \
-d "{'inference_file_id': $INFERENCE_ID, 'm_id': $MODEL_ID}"