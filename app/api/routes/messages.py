from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.deps import current_user_dep, db_dep, settings_dep
from app.models.campaign import Campaign
from app.models.contact import Contact
from app.models.user import User
from app.schemas.messages import (
    DraftRequest,
    DraftResponse,
    InfoInterviewPrepRequest,
    InfoInterviewPrepResponse,
)
from app.services.llm import get_llm_client

router = APIRouter()


@router.post("/draft", response_model=DraftResponse)
def draft_message(
    payload: DraftRequest,
    db: Session = Depends(db_dep),
    user: User = Depends(current_user_dep),
    settings=Depends(settings_dep),
) -> DraftResponse:
    campaign = (
        db.query(Campaign)
        .filter(Campaign.id == payload.campaign_id, Campaign.user_id == user.id)
        .one_or_none()
    )
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    contact = (
        db.query(Contact)
        .filter(Contact.id == payload.contact_id, Contact.user_id == user.id)
        .one_or_none()
    )
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")

    llm = get_llm_client(settings)
    draft = llm.draft_outreach(
        user_email=user.email,
        campaign_name=campaign.name,
        target_company=campaign.target_company,
        target_role=campaign.target_role,
        resume_text=campaign.resume_text,
        job_description_text=campaign.job_description_text,
        contact_name=contact.full_name,
        contact_company=contact.company,
        contact_title=contact.title,
        style=payload.style,
        ask=payload.ask,
    )
    return DraftResponse(text=draft)


@router.post("/info-interview-prep", response_model=InfoInterviewPrepResponse)
def info_interview_prep(
    payload: InfoInterviewPrepRequest,
    db: Session = Depends(db_dep),
    user: User = Depends(current_user_dep),
    settings=Depends(settings_dep),
) -> InfoInterviewPrepResponse:
    campaign = (
        db.query(Campaign)
        .filter(Campaign.id == payload.campaign_id, Campaign.user_id == user.id)
        .one_or_none()
    )
    if campaign is None:
        raise HTTPException(status_code=404, detail="Campaign not found")
    contact = (
        db.query(Contact)
        .filter(Contact.id == payload.contact_id, Contact.user_id == user.id)
        .one_or_none()
    )
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")

    llm = get_llm_client(settings)
    markdown = llm.prepare_info_interview(
        campaign_name=campaign.name,
        target_company=campaign.target_company,
        target_role=campaign.target_role,
        resume_text=campaign.resume_text,
        job_description_text=campaign.job_description_text,
        contact_name=contact.full_name,
        contact_company=contact.company,
        contact_title=contact.title,
        meeting_length_minutes=payload.meeting_length_minutes,
        goal=payload.goal,
    )
    return InfoInterviewPrepResponse(markdown=markdown)
