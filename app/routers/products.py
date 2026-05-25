from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status, Query

from app.dependencies.services import get_product_service
from app.security import get_current_seller
from app.services import ProductService
from app.schemas import ProductCreate, ProductRead, ProductList
from app.models import User

router = APIRouter(
    prefix="/products",
    tags=["products"]
)


@router.get("/", response_model=ProductList)
async def get_all_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category_id: int | None = Query(None, description="ID категории для фильтрации"),
    start_date: date | None = Query(None, description="Мин. дата создания"),
    end_date: date | None = Query(None, description="Макс. дата создания"),
    min_price: float | None = Query(None, ge=0, description="Мин. цена товара"),
    max_price: float | None = Query(None, ge=0, description="Макс. цена товара"),
    in_stock: bool | None = Query(None, description="Наличие товаров"),
    seller_id: int | None = Query(None, description="ID продавца для фильтрации"),
    service: ProductService = Depends(get_product_service)
):
    """Получение всех активных товаров"""
    if (min_price is not None) and (max_price is not None) and (min_price > max_price):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="min_price cannot be greater than max_price"
        )
    
    if (start_date is not None) and (end_date is not None) and (start_date > end_date):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="start_date cannot be greater than end_date"
        )
    
    # if (start_date is not None) and (start_date > date.today()):
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="start_date cannot be greated than today"
    #     )
    
    # if (end_date is not None) and (end_date > date.today()):
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="end_date cannot be greated than today"
    #     )

    result = await service.get_all_products(
        page, page_size,
        category_id = category_id,
        start_date=start_date, end_date=end_date,
        min_price=min_price, max_price=max_price,
        in_stock=in_stock,
        seller_id=seller_id
    )
    return {
        "total": result["total"],
        "page": page,
        "page_size": page_size,
        "items": result["items"]
    }


@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    service: ProductService = Depends(get_product_service),
    seller: User = Depends(get_current_seller)
):
    """Создание нового товара"""
    result = await service.create_product(data, seller.id)
    return result


@router.get("/category/{category_id}", response_model=list[ProductRead])
async def get_products_by_category(
    category_id: int,
    service: ProductService = Depends(get_product_service)
):
    """Получение активных товаров, относящихся к какой-либо активной категории"""
    result = await service.get_products_by_category(category_id)
    return result


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(
    product_id: int,
    service: ProductService = Depends(get_product_service)
):
    """Получение активного товара по ID"""
    result = await service.get_product_by_id(product_id)
    return result


@router.put("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int,
    data: ProductCreate,
    service: ProductService = Depends(get_product_service),
    seller: User = Depends(get_current_seller)
):
    """Обновление информации о товаре"""
    result = await service.update_product(product_id, data, seller)
    return result


@router.delete("/{product_id}")
async def delete_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
    seller: User = Depends(get_current_seller)
):
    """Удаление товара (установка is_active = False)"""
    await service.delete_product(product_id, seller)
    return {"status": "success", "message": "Product marked as inactive"}
