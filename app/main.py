from fastapi import FastAPI, Request, Depends
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session

from app.api import auth
from app.core.config import settings
from app.api.deps import get_db
from app.models.user import User
from app.schemas.user import User as UserSchema

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.PROJECT_VERSION
)

# Add session middleware
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SESSION_SECRET,
    max_age=60 * 60 * 24 * 7  # one week
)

# Include the auth router
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])

@app.get("/")
def read_root():
    return {"message": f"Bem-vindo à API da {settings.PROJECT_NAME}"}

@app.get("/api/v1/users/me", response_model=UserSchema)
def read_user_me(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get('user_id')
    if not user_id:
        return {"error": "Not logged in"}

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        # This case should not happen if session is managed correctly
        return {"error": "User not found"}

    return user