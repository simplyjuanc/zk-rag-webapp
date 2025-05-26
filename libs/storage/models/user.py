from sqlalchemy.orm import Mapped, mapped_column
from uuid import uuid4

from libs.storage.models.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        primary_key=True, index=True, default=lambda: uuid4().hex
    )
    username: Mapped[str] = mapped_column(
        nullable=False,
        unique=True,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        nullable=False,
        unique=True,
    )
    first_name: Mapped[str] = mapped_column(
        nullable=True,
    )
    last_name: Mapped[str] = mapped_column(
        nullable=True,
    )
