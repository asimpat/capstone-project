from datetime import datetime, timezone
from cuid2 import cuid_wrapper
from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

generate_cuid = cuid_wrapper()
class UserRole(Base):
    __tablename__ = "user_roles"

    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True
    )

    role_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True
    )

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    assigned_by: Mapped[str | None] = mapped_column(
        String,
        nullable=True
    )

    user = relationship(
        "User",
        back_populates="user_roles"
    )

    role = relationship(
        "Role",
        back_populates="user_roles"
    )
