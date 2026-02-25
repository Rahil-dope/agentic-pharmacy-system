"""
Configuration for the Agentic AI Pharmacy Assistant agent layer.

This module loads environment variables and exposes constants used by the agent
and tool functions.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
ENV_PATH = PROJECT_ROOT / ".env"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")

# Base URL for the FastAPI backend (Phase 2)
BACKEND_BASE_URL: str = os.getenv("BACKEND_BASE_URL", "http://localhost:8000/api")

# Default model for the agent (can be overridden via env if needed)
MODEL_NAME: str = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")

# Langfuse configuration
LANGFUSE_PUBLIC_KEY: str | None = os.getenv("LANGFUSE_PUBLIC_KEY")
LANGFUSE_SECRET_KEY: str | None = os.getenv("LANGFUSE_SECRET_KEY")

# Prefer LANGFUSE_HOST, fall back to LANGFUSE_BASE_URL, then default cloud host.
LANGFUSE_HOST: str = (
    os.getenv("LANGFUSE_HOST")
    or os.getenv("LANGFUSE_BASE_URL")
    or "https://cloud.langfuse.com"
)

# Ensure the Python SDK picks up the correct base URL.
os.environ.setdefault("LANGFUSE_BASE_URL", LANGFUSE_HOST)


