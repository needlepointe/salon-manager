from datetime import datetime
from sqlalchemy import (
    Integer, String, Boolean, Text, DateTime, Numeric,
    ForeignKey, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class InventoryProduct(Base):
    __tablename__ = "inventory_products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    sku: Mapped[str | None] = mapped_column(String(60), unique=True, nullable=True)
    category: Mapped[str] = mapped_column(String(60), nullable=False)  # extensions/tools/retail/color/care
    supplier_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    supplier_contact: Mapped[str | None] = mapped_column(String(255), nullable=True)
    unit_cost: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    retail_price: Mapped[float | None] = mapped_column(Numeric(8, 2), nullable=True)
    current_stock: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    stock_unit: Mapped[str] = mapped_column(String(20), default="units")  # units/grams/packs
    reorder_threshold: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    reorder_quantity: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    last_ordered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    last_restocked_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )

    # Relationships
    transactions: Mapped[list["InventoryTransaction"]] = relationship(
        "InventoryTransaction", back_populates="product", cascade="all, delete-orphan"
    )


class InventoryTransaction(Base):
    __tablename__ = "inventory_transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("inventory_products.id"), nullable=False
    )
    transaction_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # received/used/adjusted/sold/wasted
    quantity_change: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    quantity_after: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    appointment_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("appointments.id"), nullable=True
    )
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    product: Mapped["InventoryProduct"] = relationship(
        "InventoryProduct", back_populates="transactions"
    )
    appointment: Mapped["Appointment | None"] = relationship(  # type: ignore[name-defined]  # noqa
        "Appointment", back_populates="inventory_transactions"
    )


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    status: Mapped[str] = mapped_column(
        String(20), default="draft"
    )  # draft/sent/received/cancelled
    supplier_name: Mapped[str | None] = mapped_column(String(120), nullable=True)
    ai_generated: Mapped[bool] = mapped_column(Boolean, default=False)
    items_json: Mapped[str] = mapped_column(Text, nullable=False)  # JSON array
    total_cost: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    ordered_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    received_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
