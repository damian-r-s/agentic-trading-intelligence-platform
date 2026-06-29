from fastapi import APIRouter, Cookie, Depends, HTTPException, Response
from pydantic import BaseModel

from src.core.config import get_jwt_settings
from src.core.security import create_access_token, decode_access_token, verify_password
from src.core.databases.repositories.users_repo import get_user_by_username, set_binance_credentials

class LoginRequest(BaseModel):
    username: str
    password: str

class BinanceCredentialsRequest(BaseModel):
    api_key: str
    api_secret: str

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def login(credentials: LoginRequest, response: Response):
    """
    Authenticate with username + password, set an httpOnly JWT cookie.
    """
    user = get_user_by_username(credentials.username)
    if user is None or not verify_password(credentials.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    jwt_settings = get_jwt_settings()
    token = create_access_token({"sub": str(user["id"]), "username": user["username"]})
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


def get_current_user(access_token: str | None = Cookie(default=None)) -> dict:
    if access_token is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = decode_access_token(access_token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return {"id": int(payload["sub"]), "username": payload["username"]}


@router.get("/me")
async def me(user: dict = Depends(get_current_user)):
    """
    Return the currently authenticated username.
    """
    return {"username": user["username"]}


@router.put("/me/binance-credentials")
async def update_binance_credentials(
    credentials: BinanceCredentialsRequest, user: dict = Depends(get_current_user)
):
    """
    Set or overwrite the current user's Binance API key/secret (encrypted at rest).
    """
    set_binance_credentials(user["id"], credentials.api_key, credentials.api_secret)
    return {"message": "credentials saved"}
