from sqlalchemy.orm import Mapped, mapped_column
from uuid import uuid4

from libs.storage.models.base import Base
from enum import Enum


class UserStatus(str, Enum):
    UNVERIFIED = "unverified"
    ACTIVE = "active"
    INACTIVE = "inactive"


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        primary_key=True, index=True, default=lambda: uuid4().hex
    )
    email: Mapped[str] = mapped_column(
        nullable=False,
        unique=True,
    )
    password: Mapped[str] = mapped_column(
        nullable=False,
        index=False,
    )
    first_name: Mapped[str] = mapped_column(
        nullable=True,
    )
    last_name: Mapped[str] = mapped_column(
        nullable=True,
    )
    status: Mapped[UserStatus] = mapped_column(
        nullable=False,
        default=UserStatus.UNVERIFIED,
    )
