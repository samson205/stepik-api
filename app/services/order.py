from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Order, OrderItem, User
from app.services import CartService


class OrderService:
    db: AsyncSession
    cart_service: CartService

    def __init__(self, db: AsyncSession, cart_service: CartService) -> None:
        self.db = db
        self.cart_service = cart_service

    async def checkout_order(self, user_id: int) -> Order:
        cart_items = await self.cart_service.get_cart(user_id)
        if not cart_items:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cart is empty"
            )
        
        order = Order(user_id=user_id)
        total_amount = Decimal("0")
        for cart_item in cart_items:
            product = cart_item.product
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product {cart_item.product_id} is unavailable"
                )
            if product.stock < cart_item.quantity:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Not enough stock for product {product.name}"
                )
            
            unit_price = product.price
            if unit_price is None:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Product {product.name} has no price set"
                )
            total_price = cart_item.quantity * unit_price
            total_amount += total_price

            order_item = OrderItem(
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                unit_price=unit_price,
                total_price=total_price
            )
            
            order.items.append(order_item)
            product.stock -= cart_item.quantity

        order.total_amount = total_amount
        self.db.add(order)

        await self.cart_service.clear_cart(user_id)
        await self.db.commit()

        created_order = await self._load_order_with_items(order.id)
        if not created_order:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to load created order"
            )
        return created_order
    
    async def get_all_user_orders(self, user_id: int, page: int, page_size: int) -> dict:
        total = await self.db.scalar(
            select(func.count(Order.id)).where(Order.user_id == user_id)
        )
        total = total or 0
        result = await self.db.scalars(
            select(Order)
            .options(selectinload(Order.items).selectinload(OrderItem.product))
            .where(Order.user_id == user_id)
            .order_by(Order.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        orders = result.all()
        return {
            "total": total,
            "orders": orders
        }
    
    async def get_order_by_id(self, order_id: int, user_id: int) -> Order:
        order = await self._load_order_with_items(order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found"
            )
        if order.user_id != user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only read your own order"
            )
        return order

    async def _load_order_with_items(self, order_id: int) -> Order | None:
        result = await self.db.scalars(
            select(Order)
            .options(selectinload(Order.items).selectinload(OrderItem.product))
            .where(Order.id == order_id)
        )
        return result.first()
    