from typing import Annotated
from decimal import Decimal
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict, EmailStr


class CategoryCreate(BaseModel):
    name: Annotated[
        str, Field(..., min_length=3, max_length=50, description="Название категории")
    ]
    parent_id: Annotated[
        int | None,
        Field(default=None, description="ID родительской категории, если есть"),
    ]


class CategoryRead(BaseModel):
    id: Annotated[int, Field(..., description="Уникальный идентификатор категории")]
    name: Annotated[str, Field(..., description="Название категории")]
    parent_id: Annotated[
        int | None,
        Field(default=None, description="ID родительской категории, если есть"),
    ]
    is_active: Annotated[bool, Field(..., description="Активность категории")]

    model_config = ConfigDict(from_attributes=True)


class ProductCreate(BaseModel):
    name: Annotated[
        str, Field(..., min_length=3, max_length=100, description="Название товара")
    ]
    description: Annotated[
        str | None, Field(default=None, max_length=500, description="Описание товара")
    ]
    price: Annotated[Decimal, Field(..., gt=0, description="Цена товара")]
    image_url: Annotated[
        str | None,
        Field(default=None, max_length=200, description="URL изображения товара"),
    ]
    stock: Annotated[int, Field(..., ge=0, description="Количество товара на складе")]
    category_id: Annotated[
        int, Field(..., description="ID категори, к которой относится товар")
    ]


class ProductRead(BaseModel):
    id: Annotated[int, Field(..., description="Уникальный идентификатор товара")]
    name: Annotated[str, Field(..., description="Название товара")]
    description: Annotated[
        str | None, Field(default=None, description="Описание товара")
    ]
    price: Annotated[Decimal, Field(..., description="Цена товара")]
    image_url: Annotated[
        str | None, Field(default=None, description="URL изображения товара")
    ]
    stock: Annotated[int, Field(..., description="Количество товара на складе")]
    rating: Annotated[float, Field(..., description="Средний рейтинг товара")]
    category_id: Annotated[
        int, Field(..., description="ID категори, к которой относится товар")
    ]
    seller_id: Annotated[int, Field(..., description="Уникальный идентификатор продавца")]
    is_active: Annotated[bool, Field(..., description="Активность товара")]

    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    email: Annotated[
        EmailStr,
        Field(..., description="Email пользователя")
    ]
    password: Annotated[
        str,
        Field(..., min_length=8, description="Пароль")
    ]
    role: Annotated[
        str,
        Field(default="buyer", pattern="^(buyer|seller)$", description="Роль: 'buyer' или 'seller'")
    ]


class UserUpdate(BaseModel):
    email: Annotated[
        EmailStr | None,
        Field(None, description="Новый email пользователя")
    ]
    password: Annotated[
        str | None,
        Field(None, min_length=8, description="Новый пароль")
    ]


class UserRead(BaseModel):
    id: int
    email: EmailStr
    is_active: bool
    role: str

    model_config = ConfigDict(from_attributes=True)


class UserUpdateRole(BaseModel):
    role: Annotated[
        str,
        Field(default="buyer", pattern="^(buyer|seller|admin)$", description="Роль: 'buyer', 'seller' или 'admin'")
    ]


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class ReviewRead(BaseModel):
    id: Annotated[int, Field(..., description="Уникальный идентификатор отзыва")]
    user_id: Annotated[int, Field(..., description="Уникальный идентификатор пользователя, которому принадлежит отзыв")]
    product_id: Annotated[int, Field(..., description="Уникальный идентификатор товара, к которому написан отзыв")]
    comment: Annotated[str | None, Field(None, description="Комментарий отзыва")]
    comment_date: Annotated[datetime, Field(..., description="Дата и время написания отзыва")]
    grade: Annotated[int, Field(..., description="Оценка")]
    is_active: Annotated[bool, Field(..., description="Активность отзыва")]

    model_config = ConfigDict(from_attributes=True)


class ReviewCreate(BaseModel):
    product_id: Annotated[int, Field(..., description="Уникальный идентификатор товара, к которому написан отзыв")]
    comment: Annotated[str | None, Field(None, description="Комментарий отзыва")]
    grade: Annotated[int, Field(..., ge=1, le=5, description="Оценка")]


class ReviewUpdate(BaseModel):
    comment: str | None
    grade: Annotated[int | None, Field(None, ge=1, le=5)]
