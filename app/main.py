from fastapi import FastAPI, Request
from starlette.middleware.sessions import SessionMiddleware

from app.api import auth
from app.core.config import settings

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

@app.get("/api/v1/users/me")
def read_user_me(request: Request):
    user = request.session.get('user')
    if not user:
        return {"error": "Not logged in"}
    # In a real app, you'd use the token to fetch fresh user data
    return {"message": "Successfully authenticated", "user_token_data": user}