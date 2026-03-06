from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class CampaignCreate(BaseModel):
    name: str
    target_company: Optional[str] = None
    target_role: Optional[str] = None
    resume_text: Optional[str] = None
    job_description_text: Optional[str] = None


class CampaignOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    target_company: Optional[str] = None
    target_role: Optional[str] = None
    resume_text: Optional[str] = None
    job_description_text: Optional[str] = None
    created_at: datetime

