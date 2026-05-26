from decimal import Decimal
from datetime import datetime

from sqlalchemy import Integer, Float, String, Boolean, Numeric, ForeignKey, DateTime, func, Computed, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import TSVECTOR

from app.database import Base


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        Index("ix_products_tsv_gin", "tsv", postgresql_using="gin"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    image_url: Mapped[str] = mapped_column(String(200), nullable=True)
    stock: Mapped[int] = mapped_column(Integer, nullable=False)
    rating: Mapped[float] = mapped_column(Float, server_default="0.0")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), server_onupdate=func.now())
    
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    category: Mapped["Category"] = relationship("Category", back_populates="products") # type: ignore

    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    seller: Mapped["User"] = relationship("User", back_populates="products") # type: ignore

    reviews: Mapped[list["Review"]] = relationship("Review", back_populates="product") # type: ignore

    tsv: Mapped[TSVECTOR] = mapped_column(
        TSVECTOR,
        Computed(
            """
            setweight(to_tsvector('english', coalesce(name, '')), 'A')
            ||
            setweight(to_tsvector('english', coalesce(description, '')), 'B')
            """,
            persisted=True
        ),
        nullable=False
    )

    cart_items: Mapped[list["CartItem"]] = relationship("CartItem", back_populates="product", # type: ignore
                                                        cascade="all, delete-orphan")
    
