from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from pydantic import BaseModel

from src.core.config import get_auth_settings, get_jwt_settings
from src.core.security import create_access_token, decode_access_token, verify_password

class LoginRequest(BaseModel):
    username: str
    password: str

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(credentials: LoginRequest, response: Response):
    """
    Authenticate with username + password, set an httpOnly JWT cookie.
    """
    auth_settings = get_auth_settings()
    if (
        credentials.username != auth_settings.username
        or not verify_password(credentials.password, auth_settings.password_hash)
    ):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    jwt_settings = get_jwt_settings()
    token = create_access_token({"sub": credentials.username})
    response.set_cookie(
        key="access_token",
        value=token,
        httponly=True,
        samesite="lax",
        max_age=jwt_settings.expiry_hours * 3600,
    )
    return {"message": "logged in"}


@router.post("/logout")
async def logout(response: Response):
    """
    Clear the access token cookie.
    """
    response.delete_cookie("access_token")
    return {"message": "logged out"}


def get_current_user(access_token: str | None = Cookie(default=None)) -> str:
    if access_token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_access_token(access_token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload["sub"]


@router.get("/me")
async def me(username: str = Depends(get_current_user)):
    """
    Return the currently authenticated username.
    """
    return {"username": username}
