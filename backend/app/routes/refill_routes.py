from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.customer import Customer
from app.services.refill_service import get_refill_alerts_for_customer

router = APIRouter(tags=["refill"])


@router.get("/customers/{customer_id}/refill-alerts")
def get_customer_refill_alerts(customer_id: int) -> List[Dict[str, Any]]:
    """
    Return refill alerts for a single customer.
    """
    return get_refill_alerts_for_customer(customer_id)


@router.get("/admin/refill-alerts")
def get_all_refill_alerts(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Return refill alerts across all customers.
    """
    customers = db.query(Customer.id).all()
    results: List[Dict[str, Any]] = []
    for (customer_id,) in customers:
        alerts = get_refill_alerts_for_customer(customer_id)
        for alert in alerts:
            enriched = dict(alert)
            enriched["customer_id"] = customer_id
            results.append(enriched)

    return results

