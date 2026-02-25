from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MedicineBase(BaseModel):
    name: str
    category: Optional[str] = None
    unit: Optional[str] = None
    stock_quantity: int
    prescription_required: bool

    class Config:
        orm_mode = True


class MedicineOut(MedicineBase):
    id: int
    created_at: datetime


class MedicineAvailability(BaseModel):
    available: bool
    stock_quantity: int
    prescription_required: bool

