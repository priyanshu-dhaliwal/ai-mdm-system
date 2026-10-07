from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi import HTTPException, Depends, status
from fastapi.security import OAuth2PasswordBearer
import secrets

SECRET_KEY     = secrets.token_hex(32)
ALGORITHM      = "HS256"
DEVICE_SECRET  = secrets.token_hex(16)

pwd_context   = CryptContext(schemes=["bcrypt"])
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

ADMIN_USERS = {
    "admin": pwd_context.hash("mdm_admin_2024")
}

def create_token(data: dict, expires_delta: timedelta = timedelta(hours=8)) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + expires_delta
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_device_token(device_id: str) -> str:
    return create_token({"sub": device_id, "type": "device"},
                        expires_delta=timedelta(days=365))

def verify_token(token: str = Depends(oauth2_scheme)) -> dict:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Invalid token")

def verify_admin(payload: dict = Depends(verify_token)) -> dict:
    if payload.get("type") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return payload
