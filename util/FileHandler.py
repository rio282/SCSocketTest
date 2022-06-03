import os
import subprocess


def read_chunks(file_path: str, buffer: int = 1024):
    file_size = os.path.getsize(file_path)
    content = []
    with open(file=file_path, mode="rb") as file:
        chunk = 0
        while chunk * buffer < file_size:
            file.seek(chunk * buffer)
            data = file.read(buffer)
            if data:
                content.append(data)
            chunk += 1
    return content


def open_file(file_path: str) -> None:
    subprocess.call(file_path)
