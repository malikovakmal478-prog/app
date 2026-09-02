import os
import datetime
from passlib.context import CryptContext
from jose import jwt, JWTError
from fastapi import HTTPException, Depends, Header
from sqlalchemy.orm import Session

from .database import get_db
from .models import User

SECRET_KEY = os.environ.get("JWT_SECRET", "CHANGE_THIS_IN_PRODUCTION")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24 * 7

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(user_id: int) -> str:
    expire = datetime.datetime.utcnow() + datetime.timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {"sub": str(user_id), "exp": expire}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)) -> User:
    """Dashboard (login qilingan foydalanuvchi) uchun - API key bilan ARALASHTIRMASLIK kerak."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Login qiling")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=401, detail="Token yaroqsiz")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="Foydalanuvchi topilmadi")
    return user
