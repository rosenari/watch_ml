#!/bin/bash

UPLOAD_URL="http://localhost:5000/dataset/upload"

NIGHT_FILE="../mock/night.zip"
SUNSET_FILE="../mock/sunset.zip"

echo "현재 경로: $(pwd)"
echo "업로드할 zip 파일: $NIGHT_FILE, $SUNSET_FILE"

NIGHT_MIME_TYPE=$(file --mime-type -b "$NIGHT_FILE")
SUNSET_MIME_TYPE=$(file --mime-type -b "$SUNSET_FILE")

echo "NIGHT 파일의 MIME 타입: $NIGHT_MIME_TYPE"
echo "SUNSET 파일의 MIME 타입: $SUNSET_MIME_TYPE"

if [ "$NIGHT_MIME_TYPE" != "application/zip" ]; then
  echo "NIGHT 파일의 MIME 타입이 올바르지 않습니다. 현재 타입: $NIGHT_MIME_TYPE"
  exit 1
fi

if [ "$SUNSET_MIME_TYPE" != "application/zip" ]; then
  echo "SUNSET 파일의 MIME 타입이 올바르지 않습니다. 현재 타입: $SUNSET_MIME_TYPE"
  exit 1
fi

curl -X POST "$UPLOAD_URL" -F "file=@$NIGHT_FILE"
NIGHT_UPLOAD_STATUS=$?

curl -X POST "$UPLOAD_URL" -F "file=@$SUNSET_FILE"
SUNSET_UPLOAD_STATUS=$?

if [ $NIGHT_UPLOAD_STATUS -eq 0 ]; then
  echo "NIGHT 파일 업로드 성공"
else
  echo "NIGHT 파일 업로드 실패"
fi

if [ $SUNSET_UPLOAD_STATUS -eq 0 ]; then
  echo "SUNSET 파일 업로드 성공"
else
  echo "SUNSET 파일 업로드 실패"
fi
