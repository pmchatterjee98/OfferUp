from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Interaction(Base):
    __tablename__ = "interactions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    contact_id: Mapped[str] = mapped_column(String(36), ForeignKey("contacts.id"), index=True)

    source: Mapped[str] = mapped_column(String(50), default="manual")  # gmail | manual
    direction: Mapped[str] = mapped_column(String(20))  # inbound | outbound
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)

    subject: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    snippet: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    external_id: Mapped[Optional[str]] = mapped_column(String(200), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    contact = relationship("Contact", back_populates="interactions")
