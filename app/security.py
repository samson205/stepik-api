from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from passlib.context import CryptContext

from app.models.users import User
from app.config import SECRET_KEY, ALGORITHM
from app.dependencies.db_depends import get_async_db

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ACCESS_TOKEN_EXPIRE_MINUTES = 30
REFRESH_TOKEN_EXPIRE_DAYS = 7
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/token")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_token(data: dict, token_type: str):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        if token_type == "access"
        else timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    )
    to_encode.update({"exp": expire, "token_type": token_type})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str, token_type: str) -> dict:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"}
    )

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str | None = payload.get("sub")
        decoded_token_type: str | None = payload.get("token_type")
        if not email or decoded_token_type != token_type:
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise credentials_exception
    except jwt.PyJWTError:
        raise credentials_exception
    
    return payload

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str | None = payload.get("sub")
        token_type: str | None = payload.get("token_type")
        if not email or token_type != "access":
            raise credentials_exception
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.PyJWTError:
        raise credentials_exception

    result = await db.scalars(
        select(User).where(User.email == email, User.is_active == True)
    )
    user = result.first()
    if not User:
        raise credentials_exception

    return user


async def get_current_seller(user: User = Depends(get_current_user)):
    if user.role not in ("seller", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only sellers can perform this action",
        )
    return user


async def get_current_buyer(user: User = Depends(get_current_user)):
    if user.role not in ("buyer", "admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only buyers can perform this action",
        )
    return user


async def get_current_admin(user: User = Depends(get_current_user)):
    if user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can perform this action",
        )
    return user
