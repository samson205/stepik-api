from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm

from app.services import UserService, AuthService
from app.models.users import User
from app.schemas import UserCreate, UserRead, UserUpdate, UserUpdateRole, RefreshTokenRequest
from app.dependencies.services import get_user_service, get_auth_service
from app.security import get_current_admin, get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: UserCreate,
    service: UserService = Depends(get_user_service)
):
    """Регистрация нового пользователя"""
    result = await service.create_user(data)
    return result


@router.put("/", response_model=UserRead)
async def update_current_user(
    data: UserUpdate,
    user: User = Depends(get_current_user),
    service: UserService = Depends(get_user_service)
):
    """Обновление данных пользователя (email, пароль)"""
    result = await service.update_user(user.id, data)
    return result


@router.get("/me", response_model=UserRead)
async def get_current_profile(
    user: User = Depends(get_current_user)
):
    """Получение текущего профиля пользователя"""
    return user


@router.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    service: AuthService = Depends(get_auth_service)
):
    """Получение access и refresh токенов"""
    result = await service.create_tokens(form_data.username, form_data.password)
    return result


@router.post("/access-token")
async def access_token(
    data: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service)
):
    """Обновление access токена по refresh токену"""
    result = await service.create_access_token(data.refresh_token)
    return result


@router.post("/refresh-token")
async def refresh_token(
    data: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service)
):
    """Обновление refresh токена по refresh токену"""
    result = await service.create_refresh_token(data.refresh_token)
    return result


@router.patch("/{user_id}/role", response_model=UserRead)
async def update_role(
    user_id: int,
    data: UserUpdateRole,
    admin: User = Depends(get_current_admin),
    service: UserService = Depends(get_user_service)
):
    """Обновление роли пользователя админом"""
    result = await service.update_user_role(user_id, admin.id, data)
    return result
