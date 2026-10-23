from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from app.config import settings

engine = create_engine(
    settings.sync_database_url,
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy declarative models"""
    pass


def get_db() -> Generator[Session, None, None]:
    """Dependency for providing database session to FastAPI routes"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
