from __future__ import annotations

import logging
from typing import Any, Dict

import requests

from app.config import settings

logger = logging.getLogger(__name__)


def send_mock_webhook(order_id: int, payload: Dict[str, Any]) -> None:
    """
    Send a mock webhook to the configured warehouse endpoint.

    This function must never raise an exception; failures are logged only.
    """
    url = settings.WAREHOUSE_WEBHOOK_URL
    if not url:
        logger.info("WAREHOUSE_WEBHOOK_URL not set; skipping warehouse webhook for order %s", order_id)
        return

    body = {
        "order_id": order_id,
        "payload": payload,
    }

    try:
        response = requests.post(url, json=body, timeout=5)
        logger.info(
            "Warehouse webhook sent for order %s, status_code=%s",
            order_id,
            response.status_code,
        )
    except requests.RequestException as exc:
        logger.warning(
            "Warehouse webhook failed for order %s: %s",
            order_id,
            exc,
        )


def send_mock_confirmation_email(customer_email: str | None, order_details: Dict[str, Any]) -> None:
    """
    Simulate sending an order confirmation email.

    For this prototype, the function only logs the action.
    """
    if not customer_email:
        return

    logger.info(
        "Mock confirmation email to %s for order: %s",
        customer_email,
        order_details,
    )

