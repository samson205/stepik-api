from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select, func, desc
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

    async def get_all_products(self, page: int, page_size: int, **kwargs) -> dict:
        dict_filters = self._build_filters(**kwargs)
        filters = dict_filters.get("filters")
        if not filters:
            raise Exception
        rank_col = dict_filters.get("rank_col")
        if rank_col is not None:
            products_stmt = (
                select(Product, rank_col)
                .where(*filters)
                .order_by(desc(rank_col), Product.id)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            result = await self.db.execute(products_stmt)
            rows = result.all()
            items = [row[0] for row in rows]
        else:
            products_stmt = (
                select(Product)
                .where(*filters)
                .order_by(Product.id)
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
            items = (await self.db.scalars(products_stmt)).all()
        return {
            "total": await self._get_products_count(filters),
            "items": list(items) 
        }
    
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

    async def _get_products_count(self, filters: list) -> int:
        result = await self.db.scalar(
            select(func.count(Product.id)).where(*filters)
        )
        return result or 0

    def _build_filters(self, **kwargs) -> dict:
        filters = [Product.is_active == True]
        rank_col = None

        if kwargs.get("category_id"):
            filters.append(Product.category_id == kwargs["category_id"])
        if kwargs.get("search"):
            search_value = kwargs["search"].strip()
            if search_value:
                ts_query = func.websearch_to_tsquery('english', search_value)
                filters.append(Product.tsv.op('@@')(ts_query))
                rank_col = func.ts_rank_cd(Product.tsv, ts_query).label("rank")
        if kwargs.get("start_date"):
            start_date = kwargs["start_date"]
            start_datetime = datetime(start_date.year, start_date.month, start_date.day, 0, 0, 0)
            filters.append(Product.created_at >= start_datetime)
        if kwargs.get("end_date"):
            end_date = kwargs["end_date"]
            end_datetime = datetime(end_date.year, end_date.month, end_date.day, 23, 59, 59)
            filters.append(Product.created_at <= end_datetime)
        if kwargs.get("min_price"):
            filters.append(Product.price >= kwargs["min_price"])
        if kwargs.get("max_price"):
            filters.append(Product.price <= kwargs["max_price"])
        if kwargs.get("in_stock"):
            filters.append(Product.stock > 0 if kwargs["in_stock"] else Product.stock == 0)
        if kwargs.get("seller_id"):
            filters.append(Product.seller_id == kwargs["seller_id"])

        return {
            "filters": filters,
            "rank_col": rank_col
        }
