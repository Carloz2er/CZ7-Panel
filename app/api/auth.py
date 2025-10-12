from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import select
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.api.deps import get_db
from app.core.config import settings
from app.models.user_model import User
from app.models.subscription import Plan, Subscription, SubscriptionStatus
from datetime import datetime, timedelta

router = APIRouter()

oauth = OAuth()
oauth.register(
    name='discord',
    client_id=settings.DISCORD_CLIENT_ID,
    client_secret=settings.DISCORD_CLIENT_SECRET,
    authorize_url='https://discord.com/api/oauth2/authorize',
    access_token_url='https://discord.com/api/oauth2/token',
    scope='identify email',
    client_kwargs={'scope': 'identify email'},
)

@router.get('/login')
async def login(request: Request):
    """Redirects the user to Discord for authentication."""
    redirect_uri = request.url_for('auth_callback')
    return await oauth.discord.authorize_redirect(request, redirect_uri)

@router.get('/auth', name='auth_callback')
async def auth_callback(request: Request, db: Session = Depends(get_db)):
    """
    Callback endpoint for Discord OAuth.
    Exchanges the authorization code for an access token, fetches user info,
    creates or updates the user in the DB, and stores user ID in the session.
    """
    try:
        token = await oauth.discord.authorize_access_token(request)
        resp = await oauth.discord.get('users/@me', token=token)
        resp.raise_for_status()
        profile = resp.json()
    except (OAuthError, Exception) as error:
        return HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"OAuth/Discord API error: {error}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    discord_id = profile['id']

    # Check if user exists
    statement = select(User).where(User.discord_id == discord_id)
    db_user = db.execute(statement).scalars().first()

    if db_user:
        # Update existing user
        db_user.username = profile['username']
        db_user.email = profile['email']
        db_user.avatar = profile.get('avatar')
    else:
        # Create new user
        db_user = User(
            discord_id=discord_id,
            username=profile['username'],
            email=profile['email'],
            avatar=profile.get('avatar'),
        )
        db.add(db_user)
        db.flush() # Flush to get the user ID

        # Assign free plan on registration
        free_plan = db.query(Plan).filter(Plan.name == "Free").first()
        if free_plan:
            new_subscription = Subscription(
                user_id=db_user.id,
                plan_id=free_plan.id,
                stripe_subscription_id=f"free_{db_user.id}", # Placeholder for free tier
                status=SubscriptionStatus.ACTIVE,
                current_period_end=datetime.utcnow() + timedelta(days=9999) # Effectively forever
            )
            db.add(new_subscription)

    db.commit()
    db.refresh(db_user)

    # Store our internal user ID in the session
    request.session['user_id'] = db_user.id

    return RedirectResponse(url='/api/v1/users/me')

@router.get('/logout')
async def logout(request: Request):
    """Logs the user out by clearing the session."""
    request.session.pop('user_id', None)
    return {"message": "Successfully logged out"}