import os
import shutil
from pathlib import Path
from typing import List

from app.schemas.file import FileItem

BASE_SERVICE_PATH = Path("/var/lib/cz7host/services")

def _get_safe_path(service_id: int, relative_path: str) -> Path:
    """
    Constructs a safe, absolute path within a service's directory and prevents traversal.
    """
    service_base_path = BASE_SERVICE_PATH / str(service_id)

    # Ensure the base directory for the service exists
    service_base_path.mkdir(parents=True, exist_ok=True)

    # Normalize the relative path to prevent '..' traversal
    # os.path.normpath is used here to resolve path components like '.' or '..'
    # before joining, but the final check is the most important.
    safe_relative_path = os.path.normpath(relative_path.lstrip('/'))

    absolute_path = (service_base_path / safe_relative_path).resolve()

    # Security check: Ensure the resolved path is within the service's directory
    if not str(absolute_path).startswith(str(service_base_path.resolve())):
        raise PermissionError("Access denied: Path is outside the service directory.")

    return absolute_path

def list_files(service_id: int, path: str) -> List[FileItem]:
    """
    Lists files and directories in a given path for a service.
    """
    target_path = _get_safe_path(service_id, path)
    if not target_path.is_dir():
        raise ValueError("Path is not a directory.")

    items = []
    for entry in target_path.iterdir():
        stat = entry.stat()
        items.append(
            FileItem(
                name=entry.name,
                path=str(entry.relative_to(BASE_SERVICE_PATH / str(service_id))),
                is_dir=entry.is_dir(),
                size_bytes=stat.st_size,
                modified_at=stat.st_mtime,
            )
        )
    return items

def read_file(service_id: int, path: str) -> bytes:
    """
    Reads the content of a file for a service.
    """
    file_path = _get_safe_path(service_id, path)
    if not file_path.is_file():
        raise ValueError("Path is not a file.")
    return file_path.read_bytes()

def write_file(service_id: int, path: str, content: bytes):
    """
    Writes content to a file for a service.
    """
    file_path = _get_safe_path(service_id, path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_bytes(content)

def delete_file(service_id: int, path: str):
    """
    Deletes a file or directory for a service.
    """
    file_path = _get_safe_path(service_id, path)
    if file_path.is_dir():
        shutil.rmtree(file_path)
    else:
        file_path.unlink()