from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, nullable=True, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    orders = relationship("Order", back_populates="customer")

