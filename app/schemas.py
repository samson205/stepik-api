from typing import Annotated
from decimal import Decimal
from datetime import datetime

from fastapi import Form
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
    stock: Annotated[int, Field(..., ge=0, description="Количество товара на складе")]
    category_id: Annotated[
        int, Field(..., description="ID категори, к которой относится товар")
    ]

    @classmethod
    def as_form(
        cls,
        name: Annotated[str, Form(...)],
        price: Annotated[Decimal, Form(...)],
        stock: Annotated[int, Form(...)],
        category_id: Annotated[int, Form(...)],
        description: Annotated[str | None, Form()] = None
    ) -> "ProductCreate":
        return cls(
            name=name,
            description=description,
            price=price,
            stock=stock,
            category_id=category_id
        )


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
    created_at: Annotated[datetime, Field(..., description="Дата создания товара")]
    updated_at: Annotated[datetime, Field(..., description="Дата обновления товара")]
    category_id: Annotated[
        int, Field(..., description="ID категори, к которой относится товар")
    ]
    seller_id: Annotated[int, Field(..., description="Уникальный идентификатор продавца")]
    is_active: Annotated[bool, Field(..., description="Активность товара")]

    model_config = ConfigDict(from_attributes=True)


class ProductList(BaseModel):
    total: Annotated[int, Field(..., ge=0, description="Общее кол-во товаров")]
    page: Annotated[int, Field(..., ge=1, description="Номер текущей страницы")]
    page_size: Annotated[int, Field(..., ge=1, description="Кол-во элементов на странице")]
    items: Annotated[list["ProductRead"], Field(default_factory=list, description="Товары для текущей страницы")]

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


class CartItemBase(BaseModel):
    product_id: Annotated[int, Field(..., description="ID товара")]
    quantity: Annotated[int, Field(..., ge=1, description="Количество товара")]


class CartItemCreate(CartItemBase):
    pass


class CartItemUpdate(BaseModel):
    quantity: Annotated[int, Field(..., ge=1, description="Новое количество товара")]


class CartItemRead(BaseModel):
    id: Annotated[int, Field(..., description="ID позиции корзины")]
    quantity: Annotated[int, Field(..., description="Количество товара")]
    product: Annotated[ProductRead, Field(..., description="Информация о товаре")]

    model_config = ConfigDict(from_attributes=True)


class CartRead(BaseModel):
    user_id: Annotated[int, Field(..., description="ID пользователя")]
    total_quantity: Annotated[int, Field(..., ge=0, description="Общее количество товаров")]
    total_price: Annotated[Decimal, Field(..., ge=0, description="Общая стоимость товаров")]
    items: Annotated[list["CartItemRead"], Field(default_factory=list, description="Содержимое корзины")]

    model_config = ConfigDict(from_attributes=True)


class OrderItemRead(BaseModel):
    id: Annotated[int, Field(..., description="ID позиции заказа")]
    product_id: Annotated[int, Field(..., description="ID товара")]
    quantity: Annotated[int, Field(..., ge=1, description="Количество товара")]
    unit_price: Annotated[Decimal, Field(..., ge=0, description="Цена за единицу товара на момент покупки")]
    total_price: Annotated[Decimal, Field(..., ge=0, description="Сумма по позиции")]
    product: Annotated[ProductRead | None, Field(..., description="Полная информация о товаре")]

    model_config = ConfigDict(from_attributes=True)


class OrderRead(BaseModel):
    id: Annotated[int, Field(..., description="ID заказа")]
    user_id: Annotated[int, Field(..., description="ID пользователя")]
    status: Annotated[str, Field(..., description="Текущий статус заказа")]
    total_amount: Annotated[Decimal, Field(..., ge=0, description="общая стоимость")]
    created_at: Annotated[datetime, Field(..., description="Когда был создан заказ")]
    updated_at: Annotated[datetime, Field(..., description="Когда последний раз обновлялся")]
    items: Annotated[list["OrderItemRead"], Field(default_factory=list, description="Список позиций")]

    model_config = ConfigDict(from_attributes=True)


class OrderList(BaseModel):
    total: Annotated[int, Field(..., ge=0, description="Общее количество заказов")]
    page: Annotated[int, Field(..., ge=1, description="Текущая страница")]
    page_size: Annotated[int, Field(..., ge=1, description="Размер страницы")]
    items: Annotated[list["OrderRead"], Field(..., description="Заказы на текущей странице")]

    model_config = ConfigDict(from_attributes=True)
