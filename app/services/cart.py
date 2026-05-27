from fastapi import HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import CartItem
from app.schemas import CartItemCreate, CartItemUpdate
from app.services import ProductService


class CartService:
    db: AsyncSession
    product_service: ProductService

    def __init__(self, db: AsyncSession, product_service: ProductService) -> None:
        self.db = db
        self.product_service = product_service

    async def add_item_to_cart(self, data: CartItemCreate, user_id: int) -> CartItem:
        await self.product_service.get_product_by_id(data.product_id)
        cart_item = await self._get_cart_item(user_id, data.product_id)
        if cart_item:
            cart_item.quantity += data.quantity
        else:
            cart_item = CartItem(**data.model_dump(), user_id=user_id)
            self.db.add(cart_item)
        
        await self.db.commit()
        cart_item = await self._get_cart_item(user_id, data.product_id)
        if not cart_item:
            raise Exception
        return cart_item

    async def get_cart(self, user_id: int) -> list[CartItem]:
        result = await self.db.scalars(
            select(CartItem)
            .options(selectinload(CartItem.product))
            .where(CartItem.user_id == user_id)
            .order_by(CartItem.id)
        )
        return list(result.all())
    
    async def update_cart_item(self, data: CartItemUpdate, user_id: int, product_id: int) -> CartItem:
        cart_item = await self._get_cart_item(user_id, product_id)
        if not cart_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart item not found"
            )
        cart_item.quantity = data.quantity
        await self.db.commit()
        return cart_item
    
    async def remove_item_from_cart(self, user_id: int, product_id: int) -> None:
        cart_item = await self._get_cart_item(user_id, product_id)
        if not cart_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Cart item not found"
            )
        await self.db.delete(cart_item)
        await self.db.commit()

    async def clear_cart(self, user_id: int) -> None:
        await self.db.execute(
            delete(CartItem).where(CartItem.user_id == user_id)
        )
        await self.db.commit()

    async def _get_cart_item(self, user_id: int, product_id: int) -> CartItem | None:
        result = await self.db.scalars(
            select(CartItem)
            .options(selectinload(CartItem.product))
            .where(CartItem.user_id == user_id, CartItem.product_id == product_id)
        )
        return result.first()
    