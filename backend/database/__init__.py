"""SQLAlchemy database setup."""
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from contextlib import contextmanager

from core.config import settings


class VaultBase(DeclarativeBase):
    pass


DSN = f"sqlite:///{os.path.join(settings.VAULTSHIFT_DATA_DIR, 'vaultshift.db')}"
engine = create_engine(DSN, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_db():
    """Create all tables."""
    os.makedirs(settings.VAULTSHIFT_DATA_DIR, exist_ok=True)
    VaultBase.metadata.create_all(bind=engine)


@contextmanager
def get_session() -> Session:
    """Get a database session as context manager."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


async def get_db():
    """FastAPI dependency for DB sessions."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
