from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.sql import func
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db_depends import get_async_db
from app.models import Review, User, Product
from app.schemas import ReviewRead, ReviewCreate
from app.security import get_current_buyer

router = APIRouter(tags=["reviews"])


@router.get("/reviews", response_model=list[ReviewRead])
async def get_all_reviews(
    db: AsyncSession = Depends(get_async_db)
):
    result = await db.scalars(select(Review).where(Review.is_active == True))
    return result.all()


@router.post("/reviews", response_model=ReviewRead)
async def create_review(
    data: ReviewCreate,
    db: AsyncSession = Depends(get_async_db),
    buyer: User = Depends(get_current_buyer)
):
    result = await db.scalars(
        select(Product).where(Product.id == data.product_id, Product.is_active == True)
    )
    if not result.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    review = Review(**data.model_dump(), user_id=buyer.id)
    db.add(review)
    await db.commit()
    await db.refresh(review)
    await update_product_rating(db, review.product_id)
    return review


@router.get("/products/{product_id}/reviews", response_model=list[ReviewRead])
async def get_reviews_by_product(
    product_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    result = await db.scalars(
        select(Product).where(Product.id == product_id, Product.is_active == True)
    )
    if not result.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    result = await db.scalars(
        select(Review).where(Review.product_id == product_id, Review.is_active == True)
    )
    return result.all()


@router.delete("/reviews/{review_id}")
async def delete_review(
    review_id: int,
    db: AsyncSession = Depends(get_async_db),
    buyer: User = Depends(get_current_buyer)
):
    result = await db.scalars(select(Review).where(Review.id == review_id, Review.is_active == True))
    review = result.first()
    if not review:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Review not found or inactive"
        )
    
    if buyer.id != review.user_id and buyer.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delete your own reviews"
        )
    
    review.is_active = False
    await update_product_rating(db, review.product_id)
    await db.commit()
    return {"message": "Review deleted!"}


async def update_product_rating(
    db: AsyncSession,
    product_id: int
):
    result = await db.scalars(
        select(func.avg(Review.grade)).where(Review.product_id == product_id, Review.is_active == True)
    )
    avg_rating = result.first() or 0.0
    product = await db.get(Product, product_id)
    product.rating = avg_rating # type: ignore
    await db.commit()
