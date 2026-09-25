from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from cuid2 import cuid_wrapper
from app.database.session import Base

generate_cuid = cuid_wrapper()
class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("roles.id", ondelete="CASCADE"),
        primary_key=True
    )

    permission_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("permissions.id", ondelete="CASCADE"),
        primary_key=True
    )

    role = relationship(
        "Role",
        back_populates="role_permissions"
    )

    permission = relationship(
        "Permission",
        back_populates="role_permissions"
    )
