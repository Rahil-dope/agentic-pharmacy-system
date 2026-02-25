from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.customer import Customer
from app.models.medicine import Medicine
from app.models.order import Order
from app.models.order_item import OrderItem
from app.schemas.order_schema import OrderCreate, OrderResponse
from app.utils.webhook import send_mock_confirmation_email, send_mock_webhook

router = APIRouter(prefix="/orders", tags=["orders"])


def trigger_warehouse_webhook(order: Order, medicine: Medicine, quantity: int, customer: Customer) -> None:
    """
    Trigger downstream automation (warehouse webhook and confirmation email).

    This helper must never raise exceptions; any failures are logged only.
    """
    payload = {
        "customer_id": customer.id,
        "customer_email": customer.email,
        "medicine_name": medicine.name,
        "quantity": quantity,
        "order_status": order.status,
        "order_id": order.id,
    }

    try:
        send_mock_webhook(order.id, payload)
        send_mock_confirmation_email(customer.email, payload)
    except Exception:
        # Swallow all exceptions to avoid impacting order creation.
        return


@router.post("/", response_model=OrderResponse)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    customer = db.query(Customer).filter(Customer.id == payload.customer_id).first()
    if not customer:
        return OrderResponse(status="rejected", reason="Customer not found")

    medicine = (
        db.query(Medicine)
        .filter(func.lower(Medicine.name) == payload.medicine_name.strip().lower())
        .first()
    )
    if not medicine:
        return OrderResponse(status="rejected", reason="Medicine not found")

    if payload.quantity <= 0:
        return OrderResponse(status="rejected", reason="Quantity must be greater than zero")

    if medicine.stock_quantity < payload.quantity:
        return OrderResponse(status="rejected", reason="Insufficient stock")

    status_value = "approved"
    if medicine.prescription_required:
        status_value = "pending"

    order = Order(
        customer_id=customer.id,
        status=status_value,
    )
    db.add(order)
    db.flush()

    order_item = OrderItem(
        order_id=order.id,
        medicine_id=medicine.id,
        quantity=payload.quantity,
    )
    db.add(order_item)

    medicine.stock_quantity -= payload.quantity

    db.commit()
    db.refresh(order)

    # Fire-and-forget warehouse webhook and confirmation email.
    trigger_warehouse_webhook(order, medicine, payload.quantity, customer)

    return OrderResponse(status=status_value, order_id=order.id)

