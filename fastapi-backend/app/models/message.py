from datetime import datetime, timezone

from cuid2 import cuid_wrapper
from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base

generate_cuid = cuid_wrapper()


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=generate_cuid
    )

    conversation_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    user_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    document_id: Mapped[str | None] = mapped_column(
        String,
        ForeignKey("documents.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="user"
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )

    conversation = relationship(
        "Conversation",
        back_populates="messages"
    )
