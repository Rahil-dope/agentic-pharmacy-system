from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Medicine(Base):
    __tablename__ = "medicines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False, unique=True)
    category = Column(String, nullable=True)
    unit = Column(String, nullable=True)
    stock_quantity = Column(Integer, nullable=False, default=0)
    prescription_required = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    order_items = relationship("OrderItem", back_populates="medicine")

