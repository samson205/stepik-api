from fastapi import APIRouter, Depends, status

from app.dependencies.services import get_product_service
from app.security import get_current_seller
from app.services import ProductService
from app.schemas import ProductCreate, ProductRead
from app.models import User

router = APIRouter(
    prefix="/products",
    tags=["products"]
)


@router.get("/", response_model=list[ProductRead])
async def get_all_products(service: ProductService = Depends(get_product_service)):
    result = await service.get_all_products()
    return result


@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    service: ProductService = Depends(get_product_service),
    seller: User = Depends(get_current_seller)
):
    result = await service.create_product(data, seller.id)
    return result


@router.get("/category/{category_id}", response_model=list[ProductRead])
async def get_products_by_category(
    category_id: int,
    service: ProductService = Depends(get_product_service)
):
    result = await service.get_products_by_category(category_id)
    return result


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(
    product_id: int,
    service: ProductService = Depends(get_product_service)
):
    result = await service.get_product_by_id(product_id)
    return result


@router.put("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int,
    data: ProductCreate,
    service: ProductService = Depends(get_product_service),
    seller: User = Depends(get_current_seller)
):
    result = await service.update_product(product_id, data, seller)
    return result


@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
    seller: User = Depends(get_current_seller)
):
    await service.delete_product(product_id, seller)
    return {"status": "success", "message": "Product marked as inactive"}
