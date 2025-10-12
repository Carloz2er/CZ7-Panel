import psutil
from fastapi import APIRouter

from app.schemas.status import SystemStatus

router = APIRouter()

@router.get("/", response_model=SystemStatus)
def get_system_status():
    """
    Get the current system status (CPU and Memory).
    """
    cpu_percent = psutil.cpu_percent(interval=1)

    mem = psutil.virtual_memory()
    mem_total_gb = round(mem.total / (1024**3), 2)
    mem_used_gb = round(mem.used / (1024**3), 2)

    return {
        "cpu_percent": cpu_percent,
        "mem_total_gb": mem_total_gb,
        "mem_used_gb": mem_used_gb,
        "mem_percent": mem.percent,
    }