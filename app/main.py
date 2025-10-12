from fastapi import FastAPI, Depends
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

from app.api import auth, tickets, announcements, status, services
from app.core.config import settings
from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.user import User as UserSchema
from app.core.libvirt_manager import close_connection as close_libvirt_connection

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION
)

@app.on_event("shutdown")
def shutdown_event():
    close_libvirt_connection()

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET,
    max_age=60 * 60 * 24 * 7  # one week
)

# Include the routers
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(tickets.router, prefix="/api/v1/tickets", tags=["tickets"])
app.include_router(announcements.router, prefix="/api/v1/announcements", tags=["announcements"])
app.include_router(status.router, prefix="/api/v1/status", tags=["status"])
app.include_router(services.router, prefix="/api/v1/services", tags=["services"])

@app.get("/")
def read_root():
    return {"message": f"Bem-vindo à API da {settings.PROJECT_NAME}"}

@app.get("/api/v1/users/me", response_model=UserSchema)
def read_user_me(current_user: User = Depends(get_current_user)):
    """
    Get current user details.
    """
    return current_user