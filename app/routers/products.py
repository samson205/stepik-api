from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies.db_depends import get_async_db
from app.security import get_current_seller
from app.schemas import ProductCreate, ProductRead
from app.models import Product, Category, User

router = APIRouter(
    prefix="/products",
    tags=["products"]
)


@router.get("/", response_model=list[ProductRead])
async def get_all_products(db: AsyncSession = Depends(get_async_db)):
    result = await db.scalars(select(Product).where(Product.is_active == True))
    return result.all()


@router.post("/", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_async_db),
    seller: User = Depends(get_current_seller)
):
    result = await db.scalars(select(Category).where(Category.id == data.category_id, Category.is_active == True))
    if not result.first():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found or inactive"
        )
        
    new_product = Product(**data.model_dump(), seller_id=seller.id)
    db.add(new_product)
    await db.commit()
    await db.refresh(new_product)
    return new_product


@router.get("/category/{category_id}", response_model=list[ProductRead])
async def get_products_by_category(category_id: int, db: AsyncSession = Depends(get_async_db)):
    result = await db.scalars(select(Category).where(Category.id == category_id, Category.is_active == True))
    category = result.first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found or inactive"
        )

    result = await db.scalars(select(Product).where(Product.category_id == category_id, Product.is_active == True))
    return result.all()


@router.get("/{product_id}", response_model=ProductRead)
async def get_product(product_id: int, db: AsyncSession = Depends(get_async_db)):
    result = await db.scalars(select(Product).where(Product.id == product_id, Product.is_active == True))
    product = result.first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or inactive"
        )
    
    result = await db.scalars(select(Category).where(Category.id == product.category_id, Category.is_active == True))
    category = result.first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found or inactive"
        )
    return product


@router.put("/{product_id}", response_model=ProductRead)
async def update_product(
    product_id: int,
    data: ProductCreate,
    db: AsyncSession = Depends(get_async_db),
    seller: User = Depends(get_current_seller)
):
    result = await db.scalars(select(Product).where(Product.id == product_id, Product.is_active == True))
    product = result.first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or inactive"
        )
    
    if product.seller_id != seller.id and seller.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own products"
        )
    
    result = await db.scalars(select(Category).where(Category.id == product.category_id, Category.is_active == True))
    category = result.first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found or inactive"
        )
    
    await db.execute(
        update(Product).where(Product.id == product_id).values(**data.model_dump())
    )
    await db.commit()
    await db.refresh(product)
    return product


@router.delete("/{product_id}", response_model=ProductRead)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_async_db),
    seller: User = Depends(get_current_seller)
):
    result = await db.scalars(select(Product).where(Product.id == product_id, Product.is_active == True))
    product = result.first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found or inactive"
        )
    
    if product.seller_id != seller.id and seller.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only delte your own products"
        )
    
    product.is_active = False
    await db.commit()
    await db.refresh(product)
    return product
