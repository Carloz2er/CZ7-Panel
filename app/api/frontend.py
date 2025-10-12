from fastapi import APIRouter, Request, Depends, Form, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session
import httpx

from app.api.deps import get_db, get_current_user
from app.main import templates
from app.models.user_model import User
from app.models.service_model import Service, ServiceType
from app.core import docker_manager, libvirt_manager

router = APIRouter()

def get_api_base_url(request: Request) -> str:
    return f"{request.url.scheme}://{request.url.hostname}:{request.url.port}"

@router.get("/", response_class=HTMLResponse)
async def read_root(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    current_user = None
    if user_id:
        current_user = db.query(User).filter(User.id == user_id).first()
    return templates.TemplateResponse("index.html", {"request": request, "user": current_user, "announcements": request.state.announcements})

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
        "request": request, "user": user, "services": services,
        "service_status": service_status, "service_types": [e.value for e in ServiceType], "announcements": request.state.announcements
    })

@router.get("/tickets", response_class=HTMLResponse)
async def get_tickets_page(request: Request, user: User = Depends(get_current_user)):
    cookies = request.cookies
    api_url = f"{get_api_base_url(request)}/api/v1/tickets"
    async with httpx.AsyncClient() as client:
        response = await client.get(api_url, cookies=cookies)
        tickets_data = response.json() if response.status_code == 200 else []
    return templates.TemplateResponse("tickets.html", {"request": request, "user": user, "tickets": tickets_data, "announcements": request.state.announcements})

@router.post("/tickets")
async def handle_create_ticket(request: Request, title: str = Form(...), initial_message: str = Form(...)):
    cookies = request.cookies
    api_url = f"{get_api_base_url(request)}/api/v1/tickets/"
    async with httpx.AsyncClient() as client:
        response = await client.post(api_url, json={"title": title, "initial_message": initial_message}, cookies=cookies)
        new_ticket = response.json()
    return RedirectResponse(url=f"/tickets/{new_ticket['id']}", status_code=303)

@router.get("/tickets/{ticket_id}", response_class=HTMLResponse)
async def get_ticket_detail_page(request: Request, ticket_id: int, user: User = Depends(get_current_user)):
    cookies = request.cookies
    api_url = f"{get_api_base_url(request)}/api/v1/tickets/{ticket_id}"
    async with httpx.AsyncClient() as client:
        response = await client.get(api_url, cookies=cookies)
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail="Ticket not found or permission denied")
        ticket_data = response.json()
    return templates.TemplateResponse("ticket_detail.html", {"request": request, "user": user, "ticket": ticket_data, "announcements": request.state.announcements})

@router.post("/tickets/{ticket_id}/reply")
async def handle_ticket_reply(request: Request, ticket_id: int, content: str = Form(...)):
    cookies = request.cookies
    api_url = f"{get_api_base_url(request)}/api/v1/tickets/{ticket_id}/messages"
    async with httpx.AsyncClient() as client:
        await client.post(api_url, json={"content": content}, cookies=cookies)
    return RedirectResponse(url=f"/tickets/{ticket_id}", status_code=303)

@router.get("/services/{service_id}/files", response_class=HTMLResponse)
async def get_file_manager_page(request: Request, service_id: int, path: str = "/", user: User = Depends(get_current_user)):
    cookies = request.cookies
    api_url_files = f"{get_api_base_url(request)}/api/v1/services/{service_id}/files?path={path}"
    db = next(get_db())
    service = db.query(Service).filter(Service.id == service_id, Service.owner_id == user.id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found or permission denied")
    async with httpx.AsyncClient() as client:
        files_response = await client.get(api_url_files, cookies=cookies)
        files_data = files_response.json() if files_response.status_code == 200 else []
    return templates.TemplateResponse("file_manager.html", {"request": request, "user": user, "service": service, "files": files_data, "current_path": path, "announcements": request.state.announcements})

@router.post("/services/{service_id}/files/upload")
async def handle_upload_file(request: Request, service_id: int, path: str = "/", file: UploadFile = File(...)):
    cookies = request.cookies
    api_url = f"{get_api_base_url(request)}/api/v1/services/{service_id}/files/upload?path={path}"
    async with httpx.AsyncClient() as client:
        await client.post(api_url, files={'file': (file.filename, await file.read(), file.content_type)}, cookies=cookies)
    return RedirectResponse(url=f"/services/{service_id}/files?path={path}", status_code=303)

@router.post("/services/{service_id}/files/delete")
async def handle_delete_file(request: Request, service_id: int, path: str = "/"):
    cookies = request.cookies
    api_url = f"{get_api_base_url(request)}/api/v1/services/{service_id}/files?path={path}"
    async with httpx.AsyncClient() as client:
        await client.delete(api_url, cookies=cookies)
    parent_path = "/".join(path.split('/')[:-1]) or "/"
    return RedirectResponse(url=f"/services/{service_id}/files?path={parent_path}", status_code=303)

# --- Action Endpoints ---
@router.post("/actions/create-service")
async def action_create_service(request: Request, name: str = Form(...), service_type: str = Form(...)):
    cookies = request.cookies
    base_url = get_api_base_url(request)
    api_url = f"{base_url}/api/v1/services/"
    async with httpx.AsyncClient() as client:
        await client.post(api_url, json={"name": name, "service_type": service_type}, cookies=cookies)
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