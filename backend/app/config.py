from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / ".env"

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)

# Absolute default SQLite path — resolves correctly regardless of CWD.
_DEFAULT_DB_URL = f"sqlite:///{BASE_DIR / 'database' / 'pharmacy.db'}"


@dataclass
class Settings:
    OPENAI_API_KEY: str | None = os.getenv("OPENAI_API_KEY")
    LANGFUSE_PUBLIC_KEY: str | None = os.getenv("LANGFUSE_PUBLIC_KEY")
    LANGFUSE_SECRET_KEY: str | None = os.getenv("LANGFUSE_SECRET_KEY")
    DATABASE_URL: str = os.getenv("DATABASE_URL", _DEFAULT_DB_URL)
    WAREHOUSE_WEBHOOK_URL: str | None = os.getenv("WAREHOUSE_WEBHOOK_URL")


settings = Settings()

