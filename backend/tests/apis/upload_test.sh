#!/bin/bash

# 임시 디렉터리 생성
TEMP_DIR=$(mktemp -d)

# 임시 zip 파일 생성 경로
TEMP_FILE=$(mktemp -u "$(pwd)/tempfileXXXXXX.zip")

# 임시 디렉터리에 임시 텍스트 파일 생성 (ZIP 파일에 포함될 파일)
echo "Temporary file content" > "$TEMP_DIR/temp.txt"

# zip 파일 생성 (임시 디렉터리 안의 파일 압축)
zip -j "$TEMP_FILE" "$TEMP_DIR/temp.txt" > /dev/null

# FastAPI 서버 URL
UPLOAD_URL="http://localhost:8000/files/upload"

# 현재 경로 출력 (확인용)
echo "현재 경로: $(pwd)"
echo "임시 zip 파일 생성: $TEMP_FILE"

# MIME 타입 확인 (file 명령어로 MIME 타입 검사)
MIME_TYPE=$(file --mime-type -b "$TEMP_FILE")

# MIME 타입 출력 (디버깅용)
echo "생성된 파일의 MIME 타입: $MIME_TYPE"

# MIME 타입 검사 (application/zip인지 확인)
if [ "$MIME_TYPE" != "application/zip" ]; then
  echo "MIME 타입이 올바르지 않습니다. 현재 타입: $MIME_TYPE"
  rm -rf "$TEMP_DIR"
  rm -f "$TEMP_FILE"
  exit 1
fi

# curl로 파일 업로드
curl -X POST "$UPLOAD_URL" -F "file=@$TEMP_FILE"

# 파일 업로드 후 임시 파일과 디렉터리 삭제
rm -rf "$TEMP_DIR"
rm -f "$TEMP_FILE"

# 업로드 상태 출력
if [ $? -eq 0 ]; then
  echo "파일 업로드 성공"
else
  echo "파일 업로드 실패"
fi
