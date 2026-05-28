import uuid
from datetime import datetime
from pathlib import Path

from fastapi import HTTPException, UploadFile, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Product, User
from app.schemas import ProductCreate
from app.services import CategoryService

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MEDIA_ROOT = BASE_DIR / "media" / "products"
MEDIA_ROOT.mkdir(parents=True, exist_ok=True)
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
MAX_IMAGE_SIZE = 2 * 1024 * 1024


class ProductService:
    db: AsyncSession
    category_service: CategoryService

    def __init__(self, db: AsyncSession, category_service: CategoryService) -> None:
        self.db = db
        self.category_service = category_service

    async def create_product(self, data: ProductCreate, image: UploadFile | None, seller_id: int) -> Product:
        category = await self.category_service.get_category_by_id(data.category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Category not found or inactive"
            )
            
        image_url = await self._save_product_image(image) if image else None
        new_product = Product(**data.model_dump(), seller_id=seller_id, image_url=image_url)
        self.db.add(new_product)
        await self.db.commit()
        await self.db.refresh(new_product)
        return new_product

    async def get_all_products(self, page: int, page_size: int, **kwargs) -> dict:
        filters = self._build_filters(**kwargs)
        result = await self.db.scalars(
            select(Product)
            .where(*filters)
            .order_by(Product.id)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return {
            "total": await self._get_products_count(filters),
            "items": list(result.all()) 
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
    
    async def update_product(self, product_id: int, data: ProductCreate,
                             image: UploadFile | None, seller: User) -> Product:
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
        if image:
            self._remove_product_image(product.image_url)
            product.image_url = await self._save_product_image(image)

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
        
        self._remove_product_image(product.image_url)
        product.is_active = False
        product.image_url = None
        await self.db.commit()

    @staticmethod
    async def _save_product_image(file: UploadFile) -> str:
        if file.content_type not in ALLOWED_IMAGE_TYPES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only JPG, PNG or WebP images are allowed"
            )
        
        content = await file.read()
        if len(content) > MAX_IMAGE_SIZE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Image is too large"
            )
        
        extension = Path(file.filename or "").suffix.lower() or ".jpg"
        file_name = f"{uuid.uuid4()}{extension}"
        file_path = MEDIA_ROOT / file_name
        file_path.write_bytes(content)

        return f"/media/products/{file_name}"

    @staticmethod
    def _remove_product_image(url: str | None) -> None:
        if not url:
            return
        relative_path = url.lstrip("/")
        file_path = BASE_DIR / relative_path
        if file_path.exists():
            file_path.unlink()

    async def _get_products_count(self, filters: list) -> int:
        result = await self.db.scalar(
            select(func.count(Product.id)).where(*filters)
        )
        return result or 0

    def _build_filters(self, **kwargs) -> list:
        filters = [Product.is_active == True]

        if kwargs.get("category_id"):
            filters.append(Product.category_id == kwargs["category_id"])
        if kwargs.get("search"):
            search_value = kwargs["search"].strip()
            if search_value:
                filters.append(func.lower(Product.name).like(f"%{search_value.lower()}%"))
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

        return filters
