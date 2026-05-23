from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, HTTPException, Depends, status

from app.dependencies.db_depends import get_async_db
from app.security import get_current_admin
from app.models import Category, User
from app.schemas import CategoryRead, CategoryCreate

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=list[CategoryRead])
async def get_all_categories(db: AsyncSession = Depends(get_async_db)):
    result = await db.scalars(select(Category).where(Category.is_active == True))
    return result.all()


@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(get_async_db),
    admin: User = Depends(get_current_admin)
):
    if data.parent_id is not None:
        stmt = select(Category).where(
            Category.id == data.parent_id, Category.is_active == True
        )
        result = await db.scalars(stmt)
        parent = result.first()
        if parent is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent category not found",
            )

    new_category = Category(**data.model_dump())
    db.add(new_category)
    await db.commit()
    await db.refresh(new_category)
    return new_category


@router.put("/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: int, data: CategoryCreate,
    db: AsyncSession = Depends(get_async_db),
    admin: User = Depends(get_current_admin)
):
    stmt = select(Category).where(
        Category.id == category_id, Category.is_active == True
    )
    result = await db.scalars(stmt)
    category = result.first()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    if data.parent_id is not None:
        stmt = select(Category).where(
            Category.id == data.parent_id, Category.is_active == True
        )
        parent = await db.scalars(stmt)
        parent = result.first()
        if parent is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Parent category not found",
            )

    await db.execute(
        update(Category).where(Category.id == category_id).values(**data.model_dump(exclude_unset=True))
    )
    await db.commit()
    await db.refresh(category)
    return category


@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    db: AsyncSession = Depends(get_async_db),
    admin: User = Depends(get_current_admin)
):
    stmt = select(Category).where(
        Category.id == category_id, Category.is_active == True
    )
    result = await db.scalars(stmt)
    category = result.first()
    if category is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Category not found"
        )

    await db.execute(
        update(Category).where(Category.id == category_id).values(is_active=False)
    )
    await db.commit()

    return {"status": "success", "message": "Category marked as inactive"}
