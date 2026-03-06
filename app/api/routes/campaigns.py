from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import current_user_dep, db_dep
from app.models.campaign import Campaign
from app.models.user import User
from app.schemas.campaigns import CampaignCreate, CampaignOut

router = APIRouter()


@router.post("", response_model=CampaignOut)
def create_campaign(
    payload: CampaignCreate,
    db: Session = Depends(db_dep),
    user: User = Depends(current_user_dep),
) -> Campaign:
    campaign = Campaign(
        user_id=user.id,
        name=payload.name,
        target_company=payload.target_company,
        target_role=payload.target_role,
        resume_text=payload.resume_text,
        job_description_text=payload.job_description_text,
    )
    db.add(campaign)
    db.flush()
    return campaign


@router.get("", response_model=List[CampaignOut])
def list_campaigns(
    db: Session = Depends(db_dep),
    user: User = Depends(current_user_dep),
) -> List[Campaign]:
    return (
        db.query(Campaign)
        .filter(Campaign.user_id == user.id)
        .order_by(Campaign.created_at.desc())
        .all()
    )


@router.get("/{campaign_id}", response_model=CampaignOut)
def get_campaign(
    campaign_id: str,
    db: Session = Depends(db_dep),
    user: User = Depends(current_user_dep),
) -> Campaign:
    campaign = (
        db.query(Campaign).filter(Campaign.id == campaign_id, Campaign.user_id == user.id).one_or_none()
    )
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign
