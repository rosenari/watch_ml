import os
import aiofiles
from typing import List, Dict
from app.config import FILE_DIRECTORY
from datetime import datetime, timezone, timedelta


class FileRepository:
    def __init__(self, file_directory: str = None):
        if file_directory is None:
            file_directory = FILE_DIRECTORY

        self.file_directory = file_directory

    async def save_file(self, file_name: str, content: bytes) -> str:
        file_path = os.path.join(self.file_directory, file_name)
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        return file_name

    def delete_file(self, file_name: str) -> None:
        file_path = os.path.join(self.file_directory, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)

    def list_files(self) -> List[Dict[str, str]]:
        """파일 이름과 생성 날짜를 딕셔너리 형태로 반환 (한국 시간대로 변환)"""
        file_list = []
        # 한국 시간대(KST)는 UTC +9
        kst = timezone(timedelta(hours=9))

        for file_name in os.listdir(self.file_directory):
            file_path = os.path.join(self.file_directory, file_name)
            creation_time = os.path.getctime(file_path)

            # 한국 시간대로 변환
            creation_date = datetime.fromtimestamp(creation_time, tz=kst).strftime('%Y-%m-%d %H:%M:%S')

            file_list.append({
                "file_name": file_name,
                "creation_date": creation_date
            })
        return file_list
