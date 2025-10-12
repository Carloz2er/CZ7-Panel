from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import APIRouter, HTTPException, status
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.core.config import settings

router = APIRouter()

oauth = OAuth()
oauth.register(
    name='discord',
    client_id=settings.DISCORD_CLIENT_ID,
    client_secret=settings.DISCORD_CLIENT_SECRET,
    authorize_url='https://discord.com/api/oauth2/authorize',
    access_token_url='https://discord.com/api/oauth2/token',
    scope='identify email guilds',
    client_kwargs={'scope': 'identify email guilds'},
)

@router.get('/login')
async def login(request: Request):
    """Redirects the user to Discord for authentication."""
    redirect_uri = request.url_for('auth_callback')
    return await oauth.discord.authorize_redirect(request, redirect_uri)

@router.get('/auth', name='auth_callback')
async def auth_callback(request: Request):
    """
    Callback endpoint for Discord OAuth.
    Exchanges the authorization code for an access token and stores it in the session.
    """
    try:
        token = await oauth.discord.authorize_access_token(request)
    except OAuthError as error:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"OAuth error: {error.error}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    request.session['user'] = dict(token)

    # Here you would typically fetch user info from discord and store it in your DB
    # or update existing user info. For now, we'll just redirect to a profile page.

    return RedirectResponse(url='/api/v1/users/me')

@router.get('/logout')
async def logout(request: Request):
    """Logs the user out by clearing the session."""
    request.session.pop('user', None)
    return {"message": "Successfully logged out"}