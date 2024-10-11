import os
import aiofiles
from typing import List


class FileRepository:
    def __init__(self, file_directory: str):
        if file_directory is None:
            file_directory = os.environ.get("FILE_DIRECTORY")

        self.file_directory = file_directory

    async def save_file(self, file_name: str, content: bytes) -> str:
        file_path = os.path.join(self.file_directory, file_name)
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)
        return file_path

    def delete_file(self, file_name: str) -> None:
        file_path = os.path.join(self.file_directory, file_name)
        if os.path.exists(file_path):
            os.remove(file_path)

    def list_files(self) -> List[str]:
        return os.listdir(self.file_directory)


def get_file_repository() -> FileRepository:
    file_directory = os.environ.get("FILE_DIRECTORY")
    return FileRepository(file_directory)