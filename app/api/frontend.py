from fastapi import APIRouter, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
import httpx

from app.api.deps import get_db, get_current_user
from app.main import templates
from app.models.user_model import User
from app.models.service_model import Service, ServiceType
from app.core import docker_manager, libvirt_manager

router = APIRouter()

@router.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    services = db.query(Service).filter(Service.owner_id == user.id).all()

    service_status = {}
    for service in services:
        if service.service_type == ServiceType.VPS:
            status = libvirt_manager.get_vm_status(service.libvirt_domain_name)
        else:
            status = docker_manager.get_container_status(service.docker_container_id)
        service_status[service.id] = status

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "services": services,
        "service_status": service_status,
        "service_types": [e.value for e in ServiceType]
    })

# --- Action Endpoints ---

def get_api_base_url(request: Request) -> str:
    # Reconstruct base URL to make API calls from server-side
    return f"{request.url.scheme}://{request.url.hostname}:{request.url.port}"

@router.post("/actions/create-service")
async def action_create_service(
    request: Request,
    name: str = Form(...),
    service_type: str = Form(...)
):
    cookies = request.cookies
    base_url = get_api_base_url(request)
    api_url = f"{base_url}/api/v1/services/"

    async with httpx.AsyncClient() as client:
        await client.post(
            api_url,
            json={"name": name, "service_type": service_type},
            cookies=cookies
        )
    return RedirectResponse(url="/dashboard", status_code=303)

@router.post("/actions/start-service")
async def action_start_service(request: Request, service_id: int = Form(...)):
    cookies = request.cookies
    base_url = get_api_base_url(request)
    api_url = f"{base_url}/api/v1/services/{service_id}/start"
    async with httpx.AsyncClient() as client:
        await client.post(api_url, cookies=cookies)
    return RedirectResponse(url="/dashboard", status_code=303)

@router.post("/actions/stop-service")
async def action_stop_service(request: Request, service_id: int = Form(...)):
    cookies = request.cookies
    base_url = get_api_base_url(request)
    api_url = f"{base_url}/api/v1/services/{service_id}/stop"
    async with httpx.AsyncClient() as client:
        await client.post(api_url, cookies=cookies)
    return RedirectResponse(url="/dashboard", status_code=303)

@router.post("/actions/delete-service")
async def action_delete_service(request: Request, service_id: int = Form(...)):
    cookies = request.cookies
    base_url = get_api_base_url(request)
    api_url = f"{base_url}/api/v1/services/{service_id}"
    async with httpx.AsyncClient() as client:
        await client.delete(api_url, cookies=cookies)
    return RedirectResponse(url="/dashboard", status_code=303)