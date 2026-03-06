from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CalendarFollowUpCreate(BaseModel):
    due_at: datetime
    duration_minutes: int = Field(default=15, ge=5, le=180)
    summary: Optional[str] = None
    description: Optional[str] = None

