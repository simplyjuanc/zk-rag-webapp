from sqlalchemy.orm import Mapped, mapped_column
from uuid import uuid4

from libs.storage.tables.base import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(
        primary_key=True, index=True, default=lambda: uuid4().hex
    )
    file_path: Mapped[str] = mapped_column(
        nullable=False,
        unique=True,
    )
    file_name: Mapped[str] = mapped_column(
        nullable=False,
        index=False,
    )
    raw_content: Mapped[str] = mapped_column(
        nullable=True,
    )
    last_name: Mapped[str] = mapped_column(
        nullable=True,
    )
    
