from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Contact(Base):
    __tablename__ = "contacts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), index=True)
    campaign_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("campaigns.id"),
        index=True,
        nullable=True,
    )

    full_name: Mapped[str] = mapped_column(String(200))
    email: Mapped[str] = mapped_column(String(320), index=True)
    linkedin_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    company: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    tags_json: Mapped[str] = mapped_column(Text, default="[]")
    last_interaction_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="contacts")
    campaign = relationship("Campaign", back_populates="contacts")
    interactions = relationship("Interaction", back_populates="contact", cascade="all, delete-orphan")
    followups = relationship("FollowUp", back_populates="contact", cascade="all, delete-orphan")

    def get_tags(self) -> List[str]:
        try:
            value = json.loads(self.tags_json or "[]")
        except json.JSONDecodeError:
            return []
        if not isinstance(value, list):
            return []
        return [str(item) for item in value]

    def set_tags(self, tags: List[str]) -> None:
        self.tags_json = json.dumps(tags)

    @property
    def tags(self) -> List[str]:
        return self.get_tags()

    @tags.setter
    def tags(self, value: List[str]) -> None:
        self.set_tags(value)
