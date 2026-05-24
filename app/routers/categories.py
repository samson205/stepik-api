from fastapi import APIRouter, Depends, status

from app.dependencies.services import get_category_service
from app.security import get_current_admin
from app.services import CategoryService
from app.models import User
from app.schemas import CategoryRead, CategoryCreate

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=list[CategoryRead])
async def get_all_categories(service: CategoryService = Depends(get_category_service)):
    """Получение всех активных категорий"""
    result = await service.get_all_categories()
    return result


@router.post("/", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
    data: CategoryCreate,
    service: CategoryService = Depends(get_category_service),
    admin: User = Depends(get_current_admin)
):
    """Создание новой категории"""
    result = await service.create_category(data)
    return result


@router.put("/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: int,
    data: CategoryCreate,
    service: CategoryService = Depends(get_category_service),
    admin: User = Depends(get_current_admin)
):
    """Обновление активной категории"""
    result = await service.update_category(category_id, data)
    return result


@router.delete("/{category_id}")
async def delete_category(
    category_id: int,
    service: CategoryService = Depends(get_category_service),
    admin: User = Depends(get_current_admin)
):
    """Удаление категории (установка is_active = False)"""
    await service.delete_category(category_id)
    return {"status": "success", "message": "Category marked as inactive"}
