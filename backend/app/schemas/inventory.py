from datetime import datetime
from pydantic import BaseModel


class ProductCreate(BaseModel):
    name: str
    sku: str | None = None
    category: str
    supplier_name: str | None = None
    supplier_contact: str | None = None
    unit_cost: float | None = None
    retail_price: float | None = None
    current_stock: float = 0.0
    stock_unit: str = "units"
    reorder_threshold: float
    reorder_quantity: float | None = None
    notes: str | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    sku: str | None = None
    category: str | None = None
    supplier_name: str | None = None
    supplier_contact: str | None = None
    unit_cost: float | None = None
    retail_price: float | None = None
    stock_unit: str | None = None
    reorder_threshold: float | None = None
    reorder_quantity: float | None = None
    notes: str | None = None
    is_active: bool | None = None


class ProductRead(BaseModel):
    id: int
    name: str
    sku: str | None
    category: str
    supplier_name: str | None
    supplier_contact: str | None
    unit_cost: float | None
    retail_price: float | None
    current_stock: float
    stock_unit: str
    reorder_threshold: float
    reorder_quantity: float | None
    last_ordered_at: datetime | None
    last_restocked_at: datetime | None
    notes: str | None
    is_active: bool
    is_low_stock: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StockAdjustment(BaseModel):
    transaction_type: str  # received/used/adjusted/sold/wasted
    quantity: float  # positive = add, negative = remove
    appointment_id: int | None = None
    note: str | None = None


class TransactionRead(BaseModel):
    id: int
    product_id: int
    transaction_type: str
    quantity_change: float
    quantity_after: float
    appointment_id: int | None
    note: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class PurchaseOrderCreate(BaseModel):
    supplier_name: str | None = None
    ai_generated: bool = False
    items_json: str  # JSON array: [{product_id, name, qty, cost}]
    total_cost: float | None = None
    notes: str | None = None


class PurchaseOrderRead(BaseModel):
    id: int
    status: str
    supplier_name: str | None
    ai_generated: bool
    items_json: str
    total_cost: float | None
    notes: str | None
    ordered_at: datetime | None
    received_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
