import os
import shutil
import tarfile
from pathlib import Path
from datetime import datetime

from app.core.file_manager import get_service_path

BASE_BACKUP_PATH = Path("/var/lib/cz7host/backups")

def get_backup_path(service_id: int, filename: str) -> Path:
    """
    Constructs the absolute path for a backup file.
    """
    return BASE_BACKUP_PATH / str(service_id) / filename

def create_backup(service_id: int) -> (str, int):
    """
    Creates a new backup for a service.
    Returns the filename and size of the backup.
    """
    service_path = get_service_path(service_id)
    if not service_path.exists() or not service_path.is_dir():
        raise ValueError("Service directory does not exist.")

    backup_dir = BASE_BACKUP_PATH / str(service_id)
    backup_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"backup_{timestamp}.tar.gz"
    backup_filepath = backup_dir / filename

    with tarfile.open(backup_filepath, "w:gz") as tar:
        tar.add(str(service_path), arcname=os.path.basename(service_path))

    size_bytes = backup_filepath.stat().st_size
    return filename, size_bytes

def restore_from_backup(service_id: int, filename: str):
    """
    Restores a service from a backup file.
    """
    service_path = get_service_path(service_id)
    backup_filepath = get_backup_path(service_id, filename)

    if not backup_filepath.exists():
        raise FileNotFoundError("Backup file not found.")

    # Clear the service directory before restoring
    if service_path.exists():
        shutil.rmtree(service_path)
    service_path.mkdir(parents=True)

    with tarfile.open(backup_filepath, "r:gz") as tar:
        # The archive contains a single top-level directory. We need to extract its contents.
        # This is a bit complex, so we'll do it carefully.
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            tar.extractall(path=tmpdir)

            # This assumes the archive was created with a single directory inside
            # named after the service path's basename.
            extracted_folder = Path(tmpdir) / service_path.name
            if extracted_folder.exists() and extracted_folder.is_dir():
                # Move contents from the extracted folder to the service path
                for item in extracted_folder.iterdir():
                    shutil.move(str(item), str(service_path))
            else:
                raise RuntimeError("Backup archive is not in the expected format.")

def delete_backup_file(service_id: int, filename: str):
    """
    Deletes a backup file from the filesystem.
    """
    backup_filepath = get_backup_path(service_id, filename)
    if backup_filepath.exists():
        backup_filepath.unlink()
    else:
        raise FileNotFoundError("Backup file not found.")