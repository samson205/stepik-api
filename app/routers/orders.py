from fastapi import APIRouter, Depends, status, Query

from app.dependencies.services import get_order_service
from app.security import get_current_buyer
from app.models import User
from app.services import OrderService
from app.schemas import OrderList, OrderRead

router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("/checkout", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
async def checkout_order(
    user: User = Depends(get_current_buyer),
    service: OrderService = Depends(get_order_service)
):
    result = await service.checkout_order(user.id)
    return result


@router.get("/", response_model=OrderList)
async def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    user: User = Depends(get_current_buyer),
    service: OrderService = Depends(get_order_service)
):
    result = await service.get_all_user_orders(user.id, page, page_size)
    return OrderList(
        total=result["total"],
        page=page,
        page_size=page_size,
        items=result["orders"]
    )


@router.get("/{order_id}", response_model=OrderRead)
async def get_order(
    order_id: int,
    user: User = Depends(get_current_buyer),
    service: OrderService = Depends(get_order_service)
):
    result = await service.get_order_by_id(order_id, user.id)
    return result
