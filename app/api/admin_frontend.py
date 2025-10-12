from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse

from app.api.deps import get_current_active_superuser, get_db
from app.main import templates
from app.models.user_model import User
from app.models.service_model import Service
from app.models.ticket import Ticket
from sqlalchemy.orm import Session

router = APIRouter(
    prefix="/admin",
    tags=["admin_frontend"],
    dependencies=[Depends(get_current_active_superuser)]
)

@router.get("/dashboard", response_class=HTMLResponse)
async def get_admin_dashboard(request: Request, db: Session = Depends(get_db), user: User = Depends(get_current_active_superuser)):
    total_users = db.query(User).count()
    total_services = db.query(Service).count()
    total_tickets = db.query(Ticket).count()

    stats = {
        "total_users": total_users,
        "total_services": total_services,
        "total_tickets": total_tickets
    }

    return templates.TemplateResponse("admin/dashboard.html", {"request": request, "user": user, "stats": stats})

@router.get("/tickets", response_class=HTMLResponse)
async def get_admin_tickets_page(request: Request, db: Session = Depends(get_db)):
    tickets = db.query(Ticket).order_by(Ticket.created_at.desc()).all()
    return templates.TemplateResponse("admin/tickets.html", {"request": request, "tickets": tickets})

@router.get("/announcements", response_class=HTMLResponse)
async def get_admin_announcements_page(request: Request, db: Session = Depends(get_db)):
    announcements = db.query(Announcement).order_by(Announcement.created_at.desc()).all()
    return templates.TemplateResponse("admin/announcements.html", {"request": request, "announcements": announcements})

@router.post("/announcements")
async def handle_create_announcement(
    request: Request,
    content: str = Form(...),
    is_active: bool = Form(True)
):
    cookies = request.cookies
    api_url = f"{get_api_base_url(request)}/api/v1/announcements/"
    async with httpx.AsyncClient() as client:
        await client.post(
            api_url,
            json={"content": content, "is_active": is_active},
            cookies=cookies,
        )
    return RedirectResponse(url="/admin/announcements", status_code=303)

@router.post("/announcements/{announcement_id}/delete")
async def handle_delete_announcement(request: Request, announcement_id: str):
    cookies = request.cookies
    api_url = f"{get_api_base_url(request)}/api/v1/announcements/{announcement_id}"
    async with httpx.AsyncClient() as client:
        await client.delete(api_url, cookies=cookies)
    return RedirectResponse(url="/admin/announcements", status_code=303)

@router.get("/plans", response_class=HTMLResponse)
async def get_admin_plans_page(request: Request, db: Session = Depends(get_db)):
    plans = db.query(Plan).all()
    return templates.TemplateResponse("admin/plans.html", {"request": request, "plans": plans})

@router.post("/plans")
async def handle_create_plan(
    name: str = Form(...),
    price: float = Form(...),
    stripe_price_id: str = Form(...),
    ram_mb: int = Form(...),
    cpu_vcore: float = Form(...),
    disk_gb: int = Form(...),
    max_services: int = Form(...)
):
    # Reusing the script logic is a good way to keep things consistent
    from scripts.manage_plans import create_plan as create_plan_logic
    import argparse

    args = argparse.Namespace(
        name=name, price=price, stripe_price_id=stripe_price_id,
        ram_mb=ram_mb, cpu_vcore=cpu_vcore, disk_gb=disk_gb, max_services=max_services
    )
    create_plan_logic(args)

    return RedirectResponse(url="/admin/plans", status_code=303)