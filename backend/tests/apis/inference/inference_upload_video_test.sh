#!/bin/bash

# FastAPI 서버 URL
UPLOAD_URL="http://localhost:5000/inference/upload"

# 상위 디렉터리의 mock 디렉터리에 있는 runway.mp4 파일 경로
MP4_FILE="../mock/runway.mp4"

# 현재 경로 출력 (확인용)
echo "현재 경로: $(pwd)"
echo "업로드할 파일: $MP4_FILE"

# MIME 타입 확인 (file 명령어로 MIME 타입 검사)
MIME_TYPE=$(file --mime-type -b "$MP4_FILE")

# MIME 타입 출력 (디버깅용)
echo "파일의 MIME 타입: $MIME_TYPE"

# MIME 타입 검사 (mp4인지 확인)
if [ "$MIME_TYPE" != "video/mp4" ]; then
  echo "MIME 타입이 올바르지 않습니다. 현재 타입: $MIME_TYPE"
  exit 1
fi

# curl로 파일 업로드
curl -X POST "$UPLOAD_URL" -F "file=@$MP4_FILE"

# 업로드 상태 출력
if [ $? -eq 0 ]; then
  echo "파일 업로드 성공"
else
  echo "파일 업로드 실패"
fi
