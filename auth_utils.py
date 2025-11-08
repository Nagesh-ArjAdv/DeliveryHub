from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlmodel import Session, select
from passlib.context import CryptContext
import jwt
from models import User
from database import get_session


SECRET_KEY = "AdvikaArjun@143"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


# ---------------- Password Utilities ----------------
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# ---------------- JWT Token Utilities ----------------
def create_access_token(data: dict, expire_days: Optional[int] = ACCESS_TOKEN_EXPIRE_DAYS):
    to_encode = data.copy()
    expire = datetime.now(tz=timezone.utc) + timedelta(days=expire_days)
    expire = expire.replace(hour=23, minute=59, second=59, microsecond=999999)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


# ---------------- FastAPI Dependency ----------------
def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security),session: Session = Depends(get_session)):
    token = credentials.credentials
    payload = decode_token(token)
    email = payload.get("sub")

    if not email:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user
