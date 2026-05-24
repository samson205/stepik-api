from fastapi import APIRouter, Depends, status

from app.dependencies.services import get_review_service
from app.services import ReviewService
from app.models import User
from app.schemas import ReviewRead, ReviewCreate
from app.security import get_current_buyer

router = APIRouter(tags=["reviews"])


@router.get("/reviews", response_model=list[ReviewRead])
async def get_all_reviews(
    service: ReviewService = Depends(get_review_service)
):
    result = await service.get_all_reviews()
    return result


@router.post("/reviews", response_model=ReviewRead, status_code=status.HTTP_201_CREATED)
async def create_review(
    data: ReviewCreate,
    service: ReviewService = Depends(get_review_service),
    buyer: User = Depends(get_current_buyer)
):
    result = await service.create_review(data, buyer.id)
    return result


@router.get("/products/{product_id}/reviews", response_model=list[ReviewRead])
async def get_reviews_by_product(
    product_id: int,
    service: ReviewService = Depends(get_review_service)
):
    result = await service.get_reviews_by_product_id(product_id)
    return result


@router.delete("/reviews/{review_id}")
async def delete_review(
    review_id: int,
    service: ReviewService = Depends(get_review_service),
    buyer: User = Depends(get_current_buyer)
):
    await service.delete_review(review_id, buyer)
    return {"message": "Review deleted!"}
