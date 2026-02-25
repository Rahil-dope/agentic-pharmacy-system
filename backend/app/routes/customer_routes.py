from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.customer import Customer
from app.models.order import Order
from app.schemas.customer_schema import (
    CustomerOrderHistoryItem,
    CustomerOut,
)
from app.schemas.order_schema import OrderItemSummary

router = APIRouter(prefix="/customers", tags=["customers"])


@router.get("/", response_model=List[CustomerOut])
def list_customers(db: Session = Depends(get_db)):
    customers = db.query(Customer).order_by(Customer.created_at.desc()).all()
    return customers


@router.get("/{customer_id}/history", response_model=List[CustomerOrderHistoryItem])
def get_customer_history(customer_id: int, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == customer_id).first()
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer not found",
        )

    orders = (
        db.query(Order)
        .filter(Order.customer_id == customer_id)
        .order_by(Order.created_at.desc())
        .all()
    )

    history: List[CustomerOrderHistoryItem] = []
    for order in orders:
        items = [
            OrderItemSummary(
                medicine_name=item.medicine.name if item.medicine else "",
                quantity=item.quantity,
            )
            for item in order.items
        ]
        history.append(
            CustomerOrderHistoryItem(
                order_id=order.id,
                status=order.status,
                created_at=order.created_at,
                items=items,
            )
        )

    return history

