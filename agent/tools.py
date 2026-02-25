"""
Tool definitions for the Agentic AI Pharmacy Assistant System.

These functions are the only way the agent interacts with the backend.
They wrap HTTP calls to the FastAPI API and always return structured
JSON-like dictionaries without raising exceptions.
"""

from __future__ import annotations

from typing import Any, Dict, List

import requests

from config import BACKEND_BASE_URL


def _build_url(path: str) -> str:
    return f"{BACKEND_BASE_URL.rstrip('/')}/{path.lstrip('/')}"


def check_medicine_availability(medicine_name: str) -> Dict[str, Any]:
    """
    Check availability, stock quantity, and prescription requirement for a medicine.

    Returns a dictionary:
    {
        "available": bool,
        "stock_quantity": int,
        "prescription_required": bool,
        "error": Optional[str]
    }
    """
    url = _build_url(f"medicines/{medicine_name}/availability")
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 404:
            return {
                "available": False,
                "stock_quantity": 0,
                "prescription_required": False,
                "error": "Medicine not found",
            }

        response.raise_for_status()
        data = response.json()
        return {
            "available": bool(data.get("available", False)),
            "stock_quantity": int(data.get("stock_quantity", 0) or 0),
            "prescription_required": bool(data.get("prescription_required", False)),
            "error": None,
        }
    except requests.RequestException as exc:
        return {
            "available": False,
            "stock_quantity": 0,
            "prescription_required": False,
            "error": f"Request error: {exc}",
        }
    except ValueError:
        return {
            "available": False,
            "stock_quantity": 0,
            "prescription_required": False,
            "error": "Invalid JSON response from backend",
        }


def create_order(customer_id: int, medicine_name: str, quantity: int) -> Dict[str, Any]:
    """
    Create an order for a specific customer, medicine, and quantity.

    Returns a dictionary:
    {
        "status": "approved" | "pending" | "rejected",
        "order_id": Optional[int],
        "reason": Optional[str],
        "error": Optional[str]
    }
    """
    url = _build_url("orders")
    payload = {
        "customer_id": customer_id,
        "medicine_name": medicine_name,
        "quantity": quantity,
    }
    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        data = response.json()
        return {
            "status": data.get("status", "rejected"),
            "order_id": data.get("order_id"),
            "reason": data.get("reason"),
            "error": None,
        }
    except requests.RequestException as exc:
        return {
            "status": "rejected",
            "order_id": None,
            "reason": "Failed to contact backend service",
            "error": f"Request error: {exc}",
        }
    except ValueError:
        return {
            "status": "rejected",
            "order_id": None,
            "reason": "Invalid response from backend service",
            "error": "Invalid JSON response from backend",
        }


def get_customer_history(customer_id: int) -> Dict[str, Any]:
    """
    Retrieve the order history for a specific customer.

    Returns a dictionary:
    {
        "history": List[dict],
        "error": Optional[str]
    }
    """
    url = _build_url(f"customers/{customer_id}/history")
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 404:
            return {"history": [], "error": "Customer not found"}

        response.raise_for_status()
        data = response.json()
        history: List[Dict[str, Any]] = list(data) if isinstance(data, list) else []
        return {"history": history, "error": None}
    except requests.RequestException as exc:
        return {"history": [], "error": f"Request error: {exc}"}
    except ValueError:
        return {"history": [], "error": "Invalid JSON response from backend"}


def get_refill_alerts(customer_id: int) -> Dict[str, Any]:
    """
    Retrieve predicted refill alerts for a specific customer.

    Returns a dictionary:
    {
        "alerts": List[dict],
        "error": Optional[str]
    }
    """
    url = _build_url(f"customers/{customer_id}/refill-alerts")
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 404:
            # Customer endpoint itself does not return 404 here, but we guard anyway.
            return {"alerts": [], "error": "Customer not found"}

        response.raise_for_status()
        data = response.json()
        alerts: List[Dict[str, Any]] = list(data) if isinstance(data, list) else []
        return {"alerts": alerts, "error": None}
    except requests.RequestException as exc:
        return {"alerts": [], "error": f"Request error: {exc}"}
    except ValueError:
        return {"alerts": [], "error": "Invalid JSON response from backend"}

