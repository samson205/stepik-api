from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db_depends import get_async_db
from app.services import UserService, AuthService, CategoryService, ProductService, ReviewService


async def get_user_service(db: AsyncSession = Depends(get_async_db)):
    return UserService(db)


async def get_auth_service(
    db: AsyncSession = Depends(get_async_db),
    user_service: UserService = Depends(get_user_service)
):
    return AuthService(db, user_service)


async def get_category_service(db: AsyncSession = Depends(get_async_db)):
    return CategoryService(db)


async def get_product_service(
    db: AsyncSession = Depends(get_async_db),
    category_service: CategoryService = Depends(get_category_service)
):
    return ProductService(db, category_service)


async def get_review_service(
        db: AsyncSession = Depends(get_async_db),
        product_service: ProductService = Depends(get_product_service)
):
    return ReviewService(db, product_service)
