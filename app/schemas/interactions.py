from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class InteractionCreate(BaseModel):
    direction: str = Field(description="inbound or outbound")
    occurred_at: Optional[datetime] = None
    subject: Optional[str] = None
    snippet: Optional[str] = None


class InteractionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source: str
    direction: str
    occurred_at: datetime
    subject: Optional[str] = None
    snippet: Optional[str] = None
    external_id: Optional[str] = None

