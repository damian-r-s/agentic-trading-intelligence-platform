from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext

from src.core.config import get_jwt_settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
_settings = get_jwt_settings()
ALGORITHM = "HS256"

def hash_password(password: str) -> str:
    return _pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return _pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(hours=_settings.expiry_hours))
    to_encode = data.copy()
    to_encode["exp"] = expire
    return jwt.encode(to_encode, _settings.secret_key, algorithm=ALGORITHM)

def decode_access_token(token: str) -> dict | None:
    try: 
        return jwt.decode(token, _settings.secret_key, algorithms=[ALGORITHM])
    except JWTError: 
        return None