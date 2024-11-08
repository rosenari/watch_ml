#!/bin/bash

DATASET_ID=$1

curl -X POST "http://localhost:5000/dataset/validation" \
-H "Content-Type: application/json" \
-d "{'dataset_id': $DATASET_ID}"