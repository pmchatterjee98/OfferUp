from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Campaign(Base):
    __tablename__ = "campaigns"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)

    name: Mapped[str] = mapped_column(String(200))
    target_company: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    target_role: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    resume_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    job_description_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="campaigns")
    contacts = relationship("Contact", back_populates="campaign", cascade="all, delete-orphan")
