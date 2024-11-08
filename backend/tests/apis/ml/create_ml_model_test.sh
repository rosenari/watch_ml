#!/bin/bash

ZIP_FILE_ID=$1

curl -X POST "http://localhost:5000/ml/create" \
-H "Content-Type: application/json" \
-d "{
    'm_name': 'example_model',
    'b_m_name': 'yolov10n',
    'zip_files': [$ZIP_FILE_ID]
}"

# yolov10n, yolov10s