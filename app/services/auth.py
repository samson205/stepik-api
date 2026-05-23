from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.security import verify_password, create_token, decode_token
from app.services.user import UserService
from app.models import User


class AuthService:
    db: AsyncSession
    user_service: UserService

    def __init__(self, db: AsyncSession, user_service: UserService) -> None:
        self.db = db
        self.user_service = user_service

    async def create_tokens(self, email: str, password: str) -> dict:
        user = await self.user_service.get_user_by_email(email)
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrent email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        access_token = create_token({"sub": user.email, "role": user.role, "id": user.id}, "access")
        refresh_token = create_token({"sub": user.email, "role": user.role, "id": user.id}, "refresh")
        return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}
    
    async def create_access_token(self, refresh_token: str) -> dict:
        user = await self._validate_refresh_token(refresh_token)
        new_access_token = create_token({"sub": user.email, "role": user.role, "id": user.id}, "access")
        return {"access_token": new_access_token, "token_type": "bearer"}
    
    async def create_refresh_token(self, refresh_token: str) -> dict:
        user = await self._validate_refresh_token(refresh_token)
        new_refresh_token = create_token({"sub": user.email, "role": user.role, "id": user.id}, "refresh")
        return {"refresh_token": new_refresh_token, "token_type": "bearer"}
    
    async def _validate_refresh_token(self, refresh_token: str) -> User:
        creds_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate refresh token",
            headers={"WWW-Authenticate": "Bearer"}
        )
        payload = decode_token(refresh_token, "refresh")
        email: str | None = payload.get("sub")
        if not email:
            raise creds_exception
        user = await self.user_service.get_user_by_email(email)
        
        if not user:
            raise creds_exception
        
        return user
