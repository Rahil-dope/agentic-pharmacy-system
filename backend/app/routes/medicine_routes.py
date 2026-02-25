from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.medicine import Medicine
from app.schemas.medicine_schema import MedicineAvailability, MedicineOut

router = APIRouter(prefix="/medicines", tags=["medicines"])


@router.get("/", response_model=List[MedicineOut])
def list_medicines(db: Session = Depends(get_db)):
    medicines = db.query(Medicine).order_by(Medicine.name.asc()).all()
    return medicines


@router.get("/{medicine_name}", response_model=MedicineOut)
def get_medicine(medicine_name: str, db: Session = Depends(get_db)):
    medicine = (
        db.query(Medicine)
        .filter(func.lower(Medicine.name) == medicine_name.strip().lower())
        .first()
    )
    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found",
        )
    return medicine


@router.get("/{medicine_name}/availability", response_model=MedicineAvailability)
def check_medicine_availability(medicine_name: str, db: Session = Depends(get_db)):
    medicine = (
        db.query(Medicine)
        .filter(func.lower(Medicine.name) == medicine_name.strip().lower())
        .first()
    )
    if not medicine:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Medicine not found",
        )

    available = medicine.stock_quantity > 0
    return MedicineAvailability(
        available=available,
        stock_quantity=medicine.stock_quantity,
        prescription_required=medicine.prescription_required,
    )

