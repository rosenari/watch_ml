# 로컬에서 실행하세요.
MSYS_NO_PATHCONV=1 docker exec -it backend bash -c "PYTHONPATH=/src python /src/app/scripts/delete_file_sync.py"
