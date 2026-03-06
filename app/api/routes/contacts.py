from __future__ import annotations

from typing import List, Optional

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import current_user_dep, db_dep
from app.models.contact import Contact
from app.models.interaction import Interaction
from app.models.user import User
from app.schemas.contacts import ContactCreate, ContactOut, ContactUpdate
from app.schemas.interactions import InteractionCreate, InteractionOut

router = APIRouter()


@router.post("", response_model=ContactOut)
def create_contact(
    payload: ContactCreate,
    db: Session = Depends(db_dep),
    user: User = Depends(current_user_dep),
) -> Contact:
    contact = Contact(
        user_id=user.id,
        campaign_id=payload.campaign_id,
        full_name=payload.full_name,
        email=payload.email,
        linkedin_url=payload.linkedin_url,
        company=payload.company,
        title=payload.title,
    )
    contact.tags = payload.tags or []
    db.add(contact)
    db.flush()
    return contact


@router.get("", response_model=List[ContactOut])
def list_contacts(
    campaign_id: Optional[str] = Query(default=None),
    db: Session = Depends(db_dep),
    user: User = Depends(current_user_dep),
) -> List[Contact]:
    query = db.query(Contact).filter(Contact.user_id == user.id)
    if campaign_id:
        query = query.filter(Contact.campaign_id == campaign_id)
    return query.order_by(Contact.created_at.desc()).all()


@router.patch("/{contact_id}", response_model=ContactOut)
def update_contact(
    contact_id: str,
    payload: ContactUpdate,
    db: Session = Depends(db_dep),
    user: User = Depends(current_user_dep),
) -> Contact:
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user.id).one_or_none()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    if payload.full_name is not None:
        contact.full_name = payload.full_name
    if payload.linkedin_url is not None:
        contact.linkedin_url = payload.linkedin_url
    if payload.company is not None:
        contact.company = payload.company
    if payload.title is not None:
        contact.title = payload.title
    if payload.tags is not None:
        contact.tags = payload.tags
    db.add(contact)
    db.flush()
    return contact


@router.get("/{contact_id}", response_model=ContactOut)
def get_contact(
    contact_id: str,
    db: Session = Depends(db_dep),
    user: User = Depends(current_user_dep),
) -> Contact:
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user.id).one_or_none()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact


@router.get("/{contact_id}/interactions", response_model=List[InteractionOut])
def list_interactions(
    contact_id: str,
    db: Session = Depends(db_dep),
    user: User = Depends(current_user_dep),
) -> List[Interaction]:
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user.id).one_or_none()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")
    return (
        db.query(Interaction)
        .filter(Interaction.user_id == user.id, Interaction.contact_id == contact.id)
        .order_by(Interaction.occurred_at.desc())
        .all()
    )


@router.post("/{contact_id}/interactions", response_model=InteractionOut)
def create_interaction(
    contact_id: str,
    payload: InteractionCreate,
    db: Session = Depends(db_dep),
    user: User = Depends(current_user_dep),
) -> Interaction:
    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user.id).one_or_none()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")

    direction = (payload.direction or "").lower().strip()
    if direction not in {"inbound", "outbound"}:
        raise HTTPException(status_code=400, detail="direction must be inbound or outbound")

    occurred_at = payload.occurred_at or datetime.now(timezone.utc)
    if occurred_at.tzinfo is None:
        occurred_at = occurred_at.replace(tzinfo=timezone.utc)

    interaction = Interaction(
        user_id=user.id,
        contact_id=contact.id,
        source="manual",
        direction=direction,
        occurred_at=occurred_at,
        subject=payload.subject,
        snippet=payload.snippet,
    )
    db.add(interaction)

    if contact.last_interaction_at is None or occurred_at > contact.last_interaction_at:
        contact.last_interaction_at = occurred_at
        db.add(contact)

    db.flush()
    return interaction
