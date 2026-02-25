import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, Optional

import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import BASE_DIR
from app.database import SessionLocal
from app.models.customer import Customer
from app.models.medicine import Medicine
from app.models.order import Order
from app.models.order_item import OrderItem

logger = logging.getLogger(__name__)

if not logger.handlers:
    logging.basicConfig(level=logging.INFO)


DATA_DIR = BASE_DIR / "backend" / "data"
PRODUCTS_FILE = DATA_DIR / "products-export.xlsx"
HISTORY_FILE = DATA_DIR / "consumer-order-history.xlsx"


def _get_value(row: Dict[str, Any], aliases: Iterable[str], default: Any = None) -> Any:
    for alias in aliases:
        for key in row.keys():
            if key.lower() == alias.lower():
                return row.get(key, default)
    return default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return default
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_bool(value: Any, default: bool = False) -> bool:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"y", "yes", "true", "t", "1"}:
        return True
    if text in {"n", "no", "false", "f", "0"}:
        return False
    return default


def _to_datetime(value: Any) -> datetime:
    if isinstance(value, datetime):
        return value
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return datetime.utcnow()
    try:
        return pd.to_datetime(value).to_pydatetime()
    except (TypeError, ValueError):
        return datetime.utcnow()


def _load_dataframe(path: Path, label: str) -> Optional[pd.DataFrame]:
    if not path.exists():
        logger.info("Excel file not found for %s: %s", label, path)
        return None
    try:
        return pd.read_excel(path)
    except Exception as exc:  # noqa: BLE001
        logger.warning("Failed to read Excel file for %s from %s: %s", label, path, exc)
        return None


def _upsert_medicines(session: Session) -> None:
    df = _load_dataframe(PRODUCTS_FILE, "products")
    if df is None or df.empty:
        return

    inserted = 0
    updated = 0

    for row in df.to_dict(orient="records"):
        name = _get_value(row, ["name", "medicine_name", "product_name"])
        if not name:
            continue

        category = _get_value(row, ["category", "type"])
        unit = _get_value(row, ["unit", "uom"])
        stock = _to_int(_get_value(row, ["stock_quantity", "stock", "quantity"], 0), 0)
        prescription_required = _to_bool(
            _get_value(row, ["prescription_required", "requires_prescription", "rx_required"], False),
            False,
        )

        existing = (
            session.query(Medicine)
            .filter(func.lower(Medicine.name) == name.strip().lower())
            .first()
        )

        if existing:
            existing.category = category or existing.category
            existing.unit = unit or existing.unit
            if stock:
                existing.stock_quantity = stock
            existing.prescription_required = prescription_required
            updated += 1
        else:
            medicine = Medicine(
                name=name.strip(),
                category=category,
                unit=unit,
                stock_quantity=stock,
                prescription_required=prescription_required,
            )
            session.add(medicine)
            inserted += 1

    session.commit()
    logger.info(
        "Medicine import complete. Inserted=%s, Updated=%s from %s",
        inserted,
        updated,
        PRODUCTS_FILE,
    )


def _get_or_create_customer(session: Session, name: str, email: Optional[str]) -> Customer:
    query = session.query(Customer)
    if email:
        existing = query.filter(func.lower(Customer.email) == email.strip().lower()).first()
        if existing:
            return existing

    existing = (
        query.filter(func.lower(Customer.name) == name.strip().lower()).first()
        if name
        else None
    )
    if existing:
        if email and not existing.email:
            existing.email = email.strip()
        return existing

    customer = Customer(name=name.strip() if name else "Unknown", email=email.strip() if email else None)
    session.add(customer)
    session.flush()
    return customer


def _get_or_create_medicine(session: Session, name: str) -> Optional[Medicine]:
    if not name:
        return None
    existing = (
        session.query(Medicine)
        .filter(func.lower(Medicine.name) == name.strip().lower())
        .first()
    )
    if existing:
        return existing
    medicine = Medicine(
        name=name.strip(),
        stock_quantity=0,
        prescription_required=False,
    )
    session.add(medicine)
    session.flush()
    return medicine


def _load_order_history(session: Session) -> None:
    df = _load_dataframe(HISTORY_FILE, "order history")
    if df is None or df.empty:
        return

    created_items = 0

    for row in df.to_dict(orient="records"):
        customer_name = _get_value(row, ["customer_name", "name", "customer"])
        customer_email = _get_value(row, ["customer_email", "email"])
        medicine_name = _get_value(row, ["medicine_name", "product_name", "name"])
        quantity = _to_int(_get_value(row, ["quantity", "qty", "amount"], 0), 0)
        status = _get_value(row, ["status", "order_status"], "completed") or "completed"
        created_at_raw = _get_value(row, ["created_at", "order_date", "date"])
        created_at = _to_datetime(created_at_raw)

        if not medicine_name or quantity <= 0:
            continue

        customer = _get_or_create_customer(
            session,
            customer_name or "Unknown",
            customer_email,
        )
        medicine = _get_or_create_medicine(session, medicine_name)
        if medicine is None:
            continue

        existing_item = None
        try:
            existing_item = (
                session.query(OrderItem)
                .join(Order)
                .filter(
                    Order.customer_id == customer.id,
                    OrderItem.medicine_id == medicine.id,
                    OrderItem.quantity == quantity,
                    func.date_trunc("second", Order.created_at)
                    == func.date_trunc("second", created_at),
                )
                .first()
            )
        except Exception:  # noqa: BLE001
            # date_trunc is PostgreSQL-only; fall through to the SQLite fallback.
            session.rollback()
        # SQLite-compatible fallback when date_trunc is unavailable.
        if existing_item is None:
            existing_item = (
                session.query(OrderItem)
                .join(Order)
                .filter(
                    Order.customer_id == customer.id,
                    OrderItem.medicine_id == medicine.id,
                    OrderItem.quantity == quantity,
                    Order.created_at == created_at,
                )
                .first()
            )

        if existing_item:
            continue

        order = Order(
            customer_id=customer.id,
            status=status,
            created_at=created_at,
        )
        session.add(order)
        session.flush()

        order_item = OrderItem(
            order_id=order.id,
            medicine_id=medicine.id,
            quantity=quantity,
            created_at=created_at,
        )
        session.add(order_item)

        created_items += 1

    session.commit()
    logger.info(
        "Order history import complete. Created %s order items from %s",
        created_items,
        HISTORY_FILE,
    )


def load_initial_data() -> None:
    """
    Load initial data from Excel files into the database.

    This function is safe to call multiple times; it avoids creating
    duplicate records where possible.
    """
    session: Optional[Session] = None
    try:
        session = SessionLocal()
        _upsert_medicines(session)
        _load_order_history(session)
    except Exception:  # noqa: BLE001
        logger.exception("Error while loading initial data from Excel files.")
        if session is not None:
            session.rollback()
    finally:
        if session is not None:
            session.close()

