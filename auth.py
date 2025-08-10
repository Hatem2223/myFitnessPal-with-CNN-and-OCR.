from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext
import jwt, os
from datetime import datetime, timedelta
from sqlmodel import Session, select
from models import User
from db import get_session

SECRET = os.getenv("JWT_SECRET", "devsecret")
ALGO = "HS256"
oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")
pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(pw: str) -> str:
    return pwd.hash(pw)

def verify_password(pw: str, hashed: str) -> bool:
    return pwd.verify(pw, hashed)

def create_token(sub: str) -> str:
    exp = datetime.utcnow() + timedelta(days=7)
    return jwt.encode({"sub": sub, "exp": exp}, SECRET, algorithm=ALGO)

def get_current_user(session: Session = Depends(get_session), token: str = Depends(oauth2)) -> User:
    try:
        payload = jwt.decode(token, SECRET, algorithms=[ALGO])
        email = payload.get("sub")
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = session.exec(select(User).where(User.email == email)).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user