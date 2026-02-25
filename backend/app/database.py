from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings


DATABASE_URL = settings.DATABASE_URL

connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    """
    Initialize database tables.

    Imports all model modules so that SQLAlchemy is aware of them,
    then creates tables based on the metadata.
    """
    # Local imports to avoid circular dependencies at import time.
    from app.models import medicine, customer, order, order_item  # noqa: F401

    Base.metadata.create_all(bind=engine)

