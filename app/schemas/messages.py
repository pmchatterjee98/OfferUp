from __future__ import annotations

from typing import Optional

from pydantic import BaseModel


class DraftRequest(BaseModel):
    campaign_id: str
    contact_id: str
    style: str = "warm"
    ask: Optional[str] = None


class DraftResponse(BaseModel):
    text: str


class InfoInterviewPrepRequest(BaseModel):
    campaign_id: str
    contact_id: str
    meeting_length_minutes: int = 20
    goal: Optional[str] = None


class InfoInterviewPrepResponse(BaseModel):
    markdown: str
