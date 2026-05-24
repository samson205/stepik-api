from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Review, User
from app.schemas import ReviewCreate, ReviewUpdate
from app.services import ProductService


class ReviewService:
    db: AsyncSession
    product_service: ProductService

    def __init__(self, db: AsyncSession, product_service: ProductService) -> None:
        self.db = db
        self.product_service = product_service

    async def create_review(self, data: ReviewCreate, user_id: int) -> Review:
        await self.product_service.get_product_by_id(data.product_id)
        review = Review(**data.model_dump(), user_id=user_id)
        self.db.add(review)
        await self._update_product_rating(data.product_id)
        await self.db.commit()
        await self.db.refresh(review)
        return review
    
    async def get_all_reviews(self) -> list[Review]:
        result = await self.db.scalars(select(Review).where(Review.is_active == True))
        return list(result.all())
    
    async def get_reviews_by_product_id(self, product_id: int) -> list[Review]:
        await self.product_service.get_product_by_id(product_id)
        
        result = await self.db.scalars(
            select(Review).where(Review.product_id == product_id, Review.is_active == True)
        )
        return list(result.all())
    
    async def update_review(self, review_id, data: ReviewUpdate, buyer: User) -> Review:
        result = await self.db.scalars(select(Review).where(Review.id == review_id, Review.is_active == True))
        review = result.first()
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Review not found or inactive"
            )
        
        if buyer.id != review.user_id and buyer.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own reviews"
            )
        
        upd_data = data.model_dump(exclude_unset=True)
        for key, value in upd_data.items():
            setattr(review, key, value)
        await self._update_product_rating(review.product_id)
        await self.db.commit()
        await self.db.refresh(review)
        return review

    
    async def delete_review(self, review_id: int, buyer: User) -> None:
        result = await self.db.scalars(select(Review).where(Review.id == review_id, Review.is_active == True))
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
        await self._update_product_rating(review.product_id)
        await self.db.commit()
    
    async def _update_product_rating(self, product_id: int) -> None:
        result = await self.db.scalars(
            select(func.avg(Review.grade)).where(Review.product_id == product_id, Review.is_active == True)
        )
        avg_rating = result.first() or 0.0
        product = await self.product_service.get_product_by_id(product_id)
        product.rating = avg_rating
    