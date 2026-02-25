from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel

from .order_schema import OrderItemSummary


class CustomerOut(BaseModel):
    id: int
    name: str
    email: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True


class CustomerOrderHistoryItem(BaseModel):
    order_id: int
    status: str
    created_at: datetime
    items: List[OrderItemSummary]

    class Config:
        orm_mode = True

