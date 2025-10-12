from pydantic import BaseModel

class SystemStatus(BaseModel):
    cpu_percent: float
    mem_total_gb: float
    mem_used_gb: float
    mem_percent: float