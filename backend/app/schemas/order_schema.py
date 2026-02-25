from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class OrderCreate(BaseModel):
    customer_id: int
    medicine_name: str
    quantity: int


class OrderResponse(BaseModel):
    status: str
    order_id: Optional[int] = None
    reason: Optional[str] = None


class OrderItemSummary(BaseModel):
    medicine_name: str
    quantity: int


class OrderSummary(BaseModel):
    id: int
    status: str
    created_at: datetime
    items: list[OrderItemSummary]

    class Config:
        orm_mode = True

