curl -X POST "http://localhost:5000/inference/generate" \
-H "Content-Type: application/json" \
-d '{"original_file_name": "runway.mp4", "m_name": "fashion_model"}'