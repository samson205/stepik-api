from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category
from app.schemas import CategoryCreate


class CategoryService:
    db: AsyncSession

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_all_categories(self) -> list[Category]:
        result = await self.db.scalars(select(Category).where(Category.is_active == True))
        return list(result.all())
    
    async def create_category(self, data: CategoryCreate) -> Category:
        if data.parent_id is not None:
            parent = await self._get_category_by_id(data.parent_id)
            if parent is None:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent category not found",
                )

        new_category = Category(**data.model_dump())
        self.db.add(new_category)
        await self.db.commit()
        await self.db.refresh(new_category)
        return new_category
    
    async def update_category(self, category_id: int, data: CategoryCreate) -> Category:
        category = await self._get_category_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

        if data.parent_id is not None:
            parent = await self._get_category_by_id(data.parent_id)
            if not parent:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Parent category not found",
                )

        upd_data = data.model_dump(exclude_unset=True)
        for key, value in upd_data.items():
            setattr(category, key, value)
        await self.db.commit()
        await self.db.refresh(category)
        return category
    
    async def delete_category(self, category_id: int) -> None:
        category = await self._get_category_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found"
            )

        category.is_active = False
        await self.db.commit()

    async def _get_category_by_id(self, category_id: int) -> Category | None:
        result = await self.db.scalars(
            select(Category).where(Category.id == category_id, Category.is_active == True)
        )
        return result.first()
    