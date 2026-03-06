from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class NextActionOut(BaseModel):
    contact_id: str
    contact_name: str
    contact_email: str
    action: str  # outreach | follow_up | schedule_call
    reason: str
    due_at: Optional[datetime] = None
    relationship_strength: float = 0.0
