from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.security import hash_password
from app.models import User
from app.schemas import UserCreate, UserUpdate, UserUpdateRole


class UserService:
    db: AsyncSession

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_user(self, data: UserCreate):
        result = await self.db.scalars(select(User).where(User.email == data.email, User.is_active == True))
        if result.first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        new_user = User(
            email=data.email,
            hashed_password=hash_password(data.password),
            role=data.role
        )

        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        return new_user

    async def update_user_role(self, user_id: int, admin_id: int, data: UserUpdateRole) -> User:
        if user_id == admin_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin cannot change his role"
            )

        result = await self.db.scalars(select(User).where(User.id == user_id, User.is_active == True))
        user = result.first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.role = data.role
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_user(self, user_id: int, data: UserUpdate) -> User:
        user = await self.get_user_by_id(user_id)

        upd_data = data.model_dump(exclude_unset=True)
        if "password" in upd_data:
            upd_data["hashed_password"] = hash_password(upd_data.pop("password"))

        if "email" in upd_data:
            await self._check_email_exists(user_id, upd_data["email"])
            
        for key, value in upd_data.items():
            setattr(user, key, value)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def get_user_by_email(self, email: str) -> User:
        result = await self.db.scalars(
            select(User).where(User.email == email, User.is_active == True)
        )
        user = result.first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user
    
    async def get_user_by_id(self, user_id: int) -> User:
        result = await self.db.scalars(
            select(User).where(User.id == user_id, User.is_active == True)
        )
        user = result.first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        return user

    async def _check_email_exists(self, user_id: int, email: str):
        existing = await self.db.scalars(
            select(User).where(User.id != user_id, User.email == email, User.is_active == True)
        )
        if existing.first():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
