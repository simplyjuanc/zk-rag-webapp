from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from libs.storage.models.base import Base

db = create_engine(
    "sqlite:///:memory:",
    echo=True,
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(
    bind=db, autoflush=True, autocommit=False, expire_on_commit=False
)


def get_db_session() -> Generator[Session, None, None]:
    """
    Creates a new SQLAlchemy session for each request and
    closes it when the request is finished.
    """
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


def init_db() -> None:
    Base.metadata.create_all(db)
