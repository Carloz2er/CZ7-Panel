from pydantic import BaseModel
from app.models.service import ServiceType

class ServiceBase(BaseModel):
    name: str
    service_type: ServiceType

class ServiceCreate(ServiceBase):
    pass

class Service(ServiceBase):
    id: int
    owner_id: int
    docker_container_id: str | None = None

    class Config:
        from_attributes = True