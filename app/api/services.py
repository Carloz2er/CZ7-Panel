from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.service import Service, ServiceType
from app.schemas.service import Service as ServiceSchema, ServiceCreate
from app.core import docker_manager, libvirt_manager

router = APIRouter()

IMAGE_MAP = {
    ServiceType.MINECRAFT_PAPER: "itzg/minecraft-server",
    # We can add other images here later
}

@router.post("/", response_model=ServiceSchema, status_code=status.HTTP_201_CREATED)
def create_service(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    service_in: ServiceCreate
):
    """
    Create a new service for the current user.
    """
    # Create service in DB first
    new_service = Service(
        name=service_in.name,
        service_type=service_in.service_type,
        owner_id=current_user.id
    )
    db.add(new_service)
    db.commit()
    db.refresh(new_service)

    try:
        if service_in.service_type == ServiceType.VPS:
            # Handle VPS creation
            domain_name = f"cz7host-vps-{new_service.id}"
            libvirt_manager.create_vm(domain_name)
            new_service.libvirt_domain_name = domain_name
        else:
            # Handle Docker container creation
            image_name = IMAGE_MAP.get(service_in.service_type)
            if not image_name:
                raise HTTPException(status_code=400, detail="Unsupported service type")

            container_name = f"cz7host-container-{new_service.id}"
            environment = {}
            if service_in.service_type in [ServiceType.MINECRAFT_PAPER, ServiceType.MINECRAFT_FORGE, ServiceType.MINECRAFT_VANILLA]:
                environment["EULA"] = "TRUE"

            container = docker_manager.create_container(
                service_id=new_service.id, image=image_name, name=container_name, environment=environment
            )
            new_service.docker_container_id = container.id

        db.commit()
        db.refresh(new_service)
    except RuntimeError as e:
        db.delete(new_service)
        db.commit()
        raise HTTPException(status_code=500, detail=f"Failed to create service backend: {e}")

    return new_service

@router.get("/", response_model=List[ServiceSchema])
def list_services(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List services for the current user.
    """
    return db.query(Service).filter(Service.owner_id == current_user.id).all()

@router.post("/{service_id}/start", response_model=ServiceSchema)
def start_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Start a specific service.
    """
    service = db.query(Service).filter(Service.id == service_id, Service.owner_id == current_user.id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    if service.service_type == ServiceType.VPS:
        libvirt_manager.start_vm(service.libvirt_domain_name)
    else:
        docker_manager.start_container(service.docker_container_id)

    return service

@router.post("/{service_id}/stop", response_model=ServiceSchema)
def stop_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = db.query(Service).filter(Service.id == service_id, Service.owner_id == current_user.id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    if service.service_type == ServiceType.VPS:
        libvirt_manager.stop_vm(service.libvirt_domain_name)
    else:
        docker_manager.stop_container(service.docker_container_id)

    return service

@router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_service(
    service_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = db.query(Service).filter(Service.id == service_id, Service.owner_id == current_user.id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    if service.service_type == ServiceType.VPS:
        libvirt_manager.remove_vm(service.libvirt_domain_name)
    else:
        docker_manager.remove_container(service.docker_container_id)

    db.delete(service)
    db.commit()
    return