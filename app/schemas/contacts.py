from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class ContactCreate(BaseModel):
    campaign_id: Optional[str] = None
    full_name: str
    email: str
    linkedin_url: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    tags: Optional[List[str]] = None


class ContactUpdate(BaseModel):
    full_name: Optional[str] = None
    linkedin_url: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    tags: Optional[List[str]] = None


class ContactOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    campaign_id: Optional[str] = None
    full_name: str
    email: str
    linkedin_url: Optional[str] = None
    company: Optional[str] = None
    title: Optional[str] = None
    tags: List[str] = []
    last_interaction_at: Optional[datetime] = None
    created_at: datetime
