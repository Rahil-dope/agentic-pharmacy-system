from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

from sqlalchemy import asc
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.models.medicine import Medicine
from app.models.order import Order
from app.models.order_item import OrderItem


def _compute_alerts_for_medicine(
    dates: List[datetime],
    medicine_name: str,
) -> Dict[str, Any] | None:
    """
    Given a sorted list of purchase datetimes for a single medicine, compute
    whether a refill is due and, if so, return an alert dictionary.
    """
    if not dates:
        return None

    dates = sorted(dates)
    last_purchase = dates[-1]

    if len(dates) == 1:
        avg_interval_days = 30.0
    else:
        deltas = []
        for i in range(1, len(dates)):
            delta_days = (dates[i].date() - dates[i - 1].date()).days
            if delta_days > 0:
                deltas.append(delta_days)
        avg_interval_days = sum(deltas) / len(deltas) if deltas else 30.0

    today = datetime.utcnow().date()
    estimated_due_date = last_purchase.date() + timedelta(days=avg_interval_days)

    if today <= estimated_due_date:
        return None

    days_overdue = (today - estimated_due_date).days

    return {
        "medicine_name": medicine_name,
        "last_purchase_date": last_purchase.isoformat(),
        "estimated_refill_due_date": estimated_due_date.isoformat(),
        "days_overdue": int(days_overdue),
    }


def get_refill_alerts_for_customer(customer_id: int) -> List[Dict[str, Any]]:
    """
    Compute refill alerts for a single customer based on historical orders.

    The logic is:
    - For each medicine the customer has ordered:
      - Sort orders by date.
      - Compute average days between purchases.
      - If last_purchase_date + avg_interval < today => refill is due.
      - If there is only one purchase, use a fixed interval of 30 days.

    Returns a list of alert dictionaries and never raises an exception.
    """
    session: Session | None = None
    try:
        session = SessionLocal()
        rows = (
            session.query(
                Medicine.id,
                Medicine.name,
                Order.created_at,
            )
            .join(OrderItem, OrderItem.medicine_id == Medicine.id)
            .join(Order, OrderItem.order_id == Order.id)
            .filter(Order.customer_id == customer_id)
            .order_by(asc(Medicine.id), asc(Order.created_at))
            .all()
        )

        if not rows:
            return []

        purchases: Dict[int, Dict[str, Any]] = {}
        for med_id, med_name, created_at in rows:
            record = purchases.setdefault(
                med_id,
                {"name": med_name, "dates": []},
            )
            if isinstance(created_at, datetime):
                record["dates"].append(created_at)

        alerts: List[Dict[str, Any]] = []
        for med_id, info in purchases.items():
            alert = _compute_alerts_for_medicine(
                dates=info["dates"],
                medicine_name=info["name"],
            )
            if alert:
                alerts.append(alert)

        alerts.sort(key=lambda a: a["days_overdue"], reverse=True)
        return alerts
    except Exception:
        # Fail-safe: never propagate errors to the API layer.
        return []
    finally:
        if session is not None:
            session.close()

