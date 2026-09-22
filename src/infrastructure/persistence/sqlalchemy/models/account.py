from datetime import datetime

from sqlalchemy import String, Enum
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.enums import AccountStatus
from src.infrastructure.persistence.sqlalchemy.models.base import Base


class Account(Base):
    __tablename__ = "account"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    public_id: Mapped[str] = mapped_column(unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    status: Mapped[AccountStatus] = mapped_column(
        Enum(AccountStatus, native_enum=True, name="account_status"),
        default=AccountStatus.ACTIVE,
    )
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(nullable=False)
    updated_at: Mapped[datetime] = mapped_column(nullable=False)
