import json
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from app.database import get_db
from app.models.inventory import InventoryProduct, InventoryTransaction, PurchaseOrder
from app.schemas.inventory import (
    ProductCreate, ProductUpdate, ProductRead,
    StockAdjustment, TransactionRead,
    PurchaseOrderCreate, PurchaseOrderRead,
)
from app.services.ai.reorder_advisor import get_reorder_recommendations

router = APIRouter(prefix="/inventory", tags=["inventory"])


@router.get("/alerts")
async def get_stock_alerts(db: AsyncSession = Depends(get_db)):
    """Return products that are at or below reorder threshold."""
    result = await db.execute(
        select(InventoryProduct)
        .where(
            and_(
                InventoryProduct.is_active == True,  # noqa: E712
                InventoryProduct.current_stock <= InventoryProduct.reorder_threshold,
            )
        )
        .order_by(InventoryProduct.current_stock.asc())
    )
    products = result.scalars().all()
    return [
        {
            "id": p.id,
            "name": p.name,
            "sku": p.sku,
            "current_stock": float(p.current_stock),
            "reorder_threshold": float(p.reorder_threshold),
            "stock_unit": p.stock_unit,
            "category": p.category,
            "is_critical": float(p.current_stock) == 0,
        }
        for p in products
    ]


@router.post("/reorder-advice")
async def get_reorder_advice(db: AsyncSession = Depends(get_db)):
    """AI-powered reorder recommendations."""
    from app.models.appointment import Appointment
    from datetime import date

    # Get low stock items
    low_stock_result = await db.execute(
        select(InventoryProduct)
        .where(
            and_(
                InventoryProduct.is_active == True,  # noqa: E712
                InventoryProduct.current_stock <= InventoryProduct.reorder_threshold,
            )
        )
    )
    low_stock = low_stock_result.scalars().all()

    # Get all active products
    all_result = await db.execute(
        select(InventoryProduct).where(InventoryProduct.is_active == True)  # noqa: E712
    )
    all_products = all_result.scalars().all()

    # Compute average weekly usage for each product (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    usage_result = await db.execute(
        select(
            InventoryTransaction.product_id,
            func.sum(func.abs(InventoryTransaction.quantity_change))
        )
        .where(
            and_(
                InventoryTransaction.transaction_type.in_(["used", "sold"]),
                InventoryTransaction.created_at >= thirty_days_ago,
            )
        )
        .group_by(InventoryTransaction.product_id)
    )
    usage_data = {row[0]: float(row[1]) / 4.3 for row in usage_result.all()}  # /4.3 weeks

    # Get upcoming service types
    upcoming_result = await db.execute(
        select(Appointment.service_type)
        .where(
            and_(
                Appointment.status == "scheduled",
                Appointment.start_datetime >= datetime.now(),
                Appointment.start_datetime <= datetime.now() + timedelta(days=14),
            )
        )
    )
    upcoming_services = [row[0] for row in upcoming_result.all()]

    inventory_context = {
        "low_stock_items": [
            {
                "id": p.id,
                "name": p.name,
                "current_stock": float(p.current_stock),
                "stock_unit": p.stock_unit,
                "reorder_threshold": float(p.reorder_threshold),
                "last_ordered_at": p.last_ordered_at.isoformat() if p.last_ordered_at else None,
            }
            for p in low_stock
        ],
        "recent_usage": usage_data,
        "upcoming_services": upcoming_services,
        "all_products": [
            {
                "id": p.id,
                "name": p.name,
                "current_stock": float(p.current_stock),
                "weekly_usage": usage_data.get(p.id, 0),
            }
            for p in all_products
        ],
    }

    return await get_reorder_recommendations(inventory_context)


@router.get("/products", response_model=list[ProductRead])
async def list_products(
    category: str | None = None,
    low_stock_only: bool = False,
    db: AsyncSession = Depends(get_db),
):
    query = select(InventoryProduct).where(InventoryProduct.is_active == True)  # noqa: E712
    if category:
        query = query.where(InventoryProduct.category == category)
    if low_stock_only:
        query = query.where(InventoryProduct.current_stock <= InventoryProduct.reorder_threshold)
    query = query.order_by(InventoryProduct.category, InventoryProduct.name)
    result = await db.execute(query)
    products = result.scalars().all()
    return [
        {
            **{c.key: getattr(p, c.key) for c in p.__table__.columns},
            "current_stock": float(p.current_stock),
            "reorder_threshold": float(p.reorder_threshold),
            "unit_cost": float(p.unit_cost) if p.unit_cost else None,
            "retail_price": float(p.retail_price) if p.retail_price else None,
            "reorder_quantity": float(p.reorder_quantity) if p.reorder_quantity else None,
            "is_low_stock": float(p.current_stock) <= float(p.reorder_threshold),
        }
        for p in products
    ]


@router.post("/products", response_model=ProductRead, status_code=201)
async def create_product(data: ProductCreate, db: AsyncSession = Depends(get_db)):
    product = InventoryProduct(**data.model_dump())
    db.add(product)
    await db.flush()
    await db.refresh(product)
    result_dict = {**{c.key: getattr(product, c.key) for c in product.__table__.columns},
                   "current_stock": float(product.current_stock),
                   "reorder_threshold": float(product.reorder_threshold),
                   "is_low_stock": float(product.current_stock) <= float(product.reorder_threshold)}
    return result_dict


@router.get("/products/{product_id}")
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(InventoryProduct).where(InventoryProduct.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Get recent transactions
    tx_result = await db.execute(
        select(InventoryTransaction)
        .where(InventoryTransaction.product_id == product_id)
        .order_by(InventoryTransaction.created_at.desc())
        .limit(20)
    )
    transactions = tx_result.scalars().all()

    return {
        "product": {
            **{c.key: getattr(product, c.key) for c in product.__table__.columns},
            "current_stock": float(product.current_stock),
            "reorder_threshold": float(product.reorder_threshold),
            "is_low_stock": float(product.current_stock) <= float(product.reorder_threshold),
        },
        "recent_transactions": [
            {**{c.key: getattr(t, c.key) for c in t.__table__.columns},
             "quantity_change": float(t.quantity_change),
             "quantity_after": float(t.quantity_after)}
            for t in transactions
        ],
    }


@router.put("/products/{product_id}", response_model=ProductRead)
async def update_product(product_id: int, data: ProductUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(InventoryProduct).where(InventoryProduct.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(product, field, value)
    await db.flush()
    await db.refresh(product)
    return {**{c.key: getattr(product, c.key) for c in product.__table__.columns},
            "current_stock": float(product.current_stock),
            "reorder_threshold": float(product.reorder_threshold),
            "is_low_stock": float(product.current_stock) <= float(product.reorder_threshold)}


@router.post("/products/{product_id}/adjust")
async def adjust_stock(
    product_id: int,
    data: StockAdjustment,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(InventoryProduct).where(InventoryProduct.id == product_id))
    product = result.scalar_one_or_none()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    new_stock = float(product.current_stock) + data.quantity
    if new_stock < 0:
        raise HTTPException(status_code=400, detail="Stock cannot go below zero")

    transaction = InventoryTransaction(
        product_id=product_id,
        transaction_type=data.transaction_type,
        quantity_change=data.quantity,
        quantity_after=new_stock,
        appointment_id=data.appointment_id,
        note=data.note,
    )
    db.add(transaction)
    product.current_stock = new_stock

    if data.transaction_type == "received":
        product.last_restocked_at = datetime.now()

    await db.commit()
    return {"message": "Stock adjusted", "new_stock": new_stock}


@router.get("/purchase-orders", response_model=list[PurchaseOrderRead])
async def list_purchase_orders(db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(PurchaseOrder).order_by(PurchaseOrder.created_at.desc())
    )
    return result.scalars().all()


@router.post("/purchase-orders", response_model=PurchaseOrderRead, status_code=201)
async def create_purchase_order(data: PurchaseOrderCreate, db: AsyncSession = Depends(get_db)):
    po = PurchaseOrder(**data.model_dump())
    db.add(po)
    await db.flush()
    await db.refresh(po)
    return po


@router.put("/purchase-orders/{po_id}")
async def update_purchase_order(
    po_id: int,
    status: str,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(PurchaseOrder).where(PurchaseOrder.id == po_id))
    po = result.scalar_one_or_none()
    if not po:
        raise HTTPException(status_code=404, detail="Purchase order not found")
    po.status = status
    if status == "sent":
        po.ordered_at = datetime.now()
    if status == "received":
        po.received_at = datetime.now()
        # Update stock for each item in the order
        try:
            items = json.loads(po.items_json)
            for item in items:
                product_result = await db.execute(
                    select(InventoryProduct).where(InventoryProduct.id == item["product_id"])
                )
                product = product_result.scalar_one_or_none()
                if product:
                    qty = float(item.get("qty", 0))
                    new_stock = float(product.current_stock) + qty
                    db.add(InventoryTransaction(
                        product_id=product.id,
                        transaction_type="received",
                        quantity_change=qty,
                        quantity_after=new_stock,
                        note=f"Purchase order #{po_id}",
                    ))
                    product.current_stock = new_stock
                    product.last_ordered_at = po.ordered_at
                    product.last_restocked_at = datetime.now()
        except Exception as e:
            print(f"Error updating stock from PO: {e}")
    await db.commit()
    return {"message": f"Purchase order updated to {status}"}
