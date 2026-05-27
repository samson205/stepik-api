from decimal import Decimal

from fastapi import APIRouter, Depends, Response, status

from app.schemas import CartRead, CartItemRead, CartItemCreate, CartItemUpdate
from app.models import User
from app.security import get_current_user
from app.services import CartService
from app.dependencies.services import get_cart_service

router = APIRouter(prefix="/cart", tags=["cart"])


@router.get("/", response_model=CartRead)
async def get_cart(
    user: User = Depends(get_current_user),
    service: CartService = Depends(get_cart_service)
):
    items = await service.get_cart(user.id)
    total_quantity = sum(item.quantity for item in items)
    price_items = (
        Decimal(item.quantity) *
        (item.product.price if item.product.price is not None else Decimal("0"))
        for item in items
    )
    total_price = sum(price_items, Decimal("0"))

    return CartRead(
        user_id=user.id,
        total_quantity=total_quantity,
        total_price=total_price,
        items=items # type: ignore
    )


@router.post("/items", response_model=CartItemRead, status_code=status.HTTP_201_CREATED)
async def add_item_to_cart(
    data: CartItemCreate,
    user: User = Depends(get_current_user),
    service: CartService = Depends(get_cart_service)
):
    cart_item = await service.add_item_to_cart(data, user.id)
    return cart_item


@router.put("/items/{product_id}", response_model=CartItemRead)
async def update_cart_item(
    product_id: int,
    data: CartItemUpdate,
    user: User = Depends(get_current_user),
    service: CartService = Depends(get_cart_service)
):
    cart_item = await service.update_cart_item(data, user.id, product_id)
    return cart_item


@router.delete("/items/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item_from_cart(
    product_id: int,
    user: User = Depends(get_current_user),
    service: CartService = Depends(get_cart_service)
):
    await service.remove_item_from_cart(user.id, product_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
async def clear_cart(
    user: User = Depends(get_current_user),
    service: CartService = Depends(get_cart_service)
):
    await service.clear_cart(user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
