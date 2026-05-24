from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product, User
from app.schemas import ProductCreate
from app.services import CategoryService


class ProductService:
    db: AsyncSession
    category_service: CategoryService

    def __init__(self, db: AsyncSession, category_service: CategoryService) -> None:
        self.db = db
        self.category_service = category_service

    async def create_product(self, data: ProductCreate, seller_id: int) -> Product:
        category = await self.category_service.get_category_by_id(data.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found or inactive"
            )
            
        new_product = Product(**data.model_dump(), seller_id=seller_id)
        self.db.add(new_product)
        await self.db.commit()
        await self.db.refresh(new_product)
        return new_product

    async def get_all_products(self) -> list[Product]:
        result = await self.db.scalars(select(Product).where(Product.is_active == True))
        return list(result.all())
    
    async def get_products_by_category(self, category_id: int) -> list[Product]:
        category = await self.category_service.get_category_by_id(category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found or inactive"
            )

        result = await self.db.scalars(
            select(Product).where(Product.category_id == category_id, Product.is_active == True)
        )
        return list(result.all())
    
    async def get_product_by_id(self, product_id: int) -> Product:
        result = await self.db.scalars(
            select(Product).where(Product.id == product_id, Product.is_active == True)
        )
        product = result.first()
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Product not found or inactive"
            )
        
        category = await self.category_service.get_category_by_id(product.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found or inactive"
            )
        return product
    
    async def update_product(self, product_id: int, data: ProductCreate, seller: User) -> Product:
        product = await self.get_product_by_id(product_id)
        
        if product.seller_id != seller.id and seller.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only update your own products"
            )
        
        category = await self.category_service.get_category_by_id(data.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found or inactive"
            )
        
        upd_data = data.model_dump(exclude_unset=True)
        for key, value in upd_data.items():
            setattr(product, key, value)
        await self.db.commit()
        await self.db.refresh(product)
        return product
    
    async def delete_product(self, product_id: int, seller: User) -> None:
        product = await self.get_product_by_id(product_id)
        
        if product.seller_id != seller.id and seller.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only delete your own products"
            )
        
        product.is_active = False
        await self.db.commit()
