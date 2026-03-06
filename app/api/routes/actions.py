from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy import and_, func
from sqlalchemy.orm import Session

from app.api.deps import current_user_dep, db_dep
from app.models.contact import Contact
from app.models.followup import FollowUp
from app.models.interaction import Interaction
from app.models.user import User
from app.schemas.actions import NextActionOut
from app.services.recommendations import Heuristics, compute_relationship_strength

router = APIRouter()


@router.get("/next", response_model=List[NextActionOut])
def next_actions(
    db: Session = Depends(db_dep),
    user: User = Depends(current_user_dep),
) -> List[NextActionOut]:
    now = datetime.now(timezone.utc)
    heuristics = Heuristics()

    contacts = db.query(Contact).filter(Contact.user_id == user.id).all()
    if not contacts:
        return []

    contact_ids = [c.id for c in contacts]

    # Latest interaction per contact (single query).
    latest_subq = (
        db.query(
            Interaction.contact_id.label("contact_id"),
            func.max(Interaction.occurred_at).label("max_occurred_at"),
        )
        .filter(Interaction.user_id == user.id, Interaction.contact_id.in_(contact_ids))
        .group_by(Interaction.contact_id)
        .subquery()
    )
    latest_rows = (
        db.query(Interaction.contact_id, Interaction.occurred_at, Interaction.direction)
        .join(
            latest_subq,
            and_(
                Interaction.contact_id == latest_subq.c.contact_id,
                Interaction.occurred_at == latest_subq.c.max_occurred_at,
            ),
        )
        .all()
    )
    latest_by_contact = {row.contact_id: row for row in latest_rows}

    counts_rows = (
        db.query(Interaction.contact_id, func.count(Interaction.id))
        .filter(Interaction.user_id == user.id, Interaction.contact_id.in_(contact_ids))
        .group_by(Interaction.contact_id)
        .all()
    )
    counts_by_contact = {contact_id: int(count) for contact_id, count in counts_rows}

    followup_rows = (
        db.query(FollowUp.contact_id, func.min(FollowUp.due_at))
        .filter(
            FollowUp.user_id == user.id,
            FollowUp.contact_id.in_(contact_ids),
            FollowUp.status == "pending",
        )
        .group_by(FollowUp.contact_id)
        .all()
    )
    next_followup_by_contact = {contact_id: due_at for contact_id, due_at in followup_rows}

    actions: List[NextActionOut] = []
    for contact in contacts:
        last = latest_by_contact.get(contact.id)
        interaction_count = counts_by_contact.get(contact.id, 0)
        next_followup_due = next_followup_by_contact.get(contact.id)

        strength = compute_relationship_strength(
            last_interaction_at=(last.occurred_at if last else None),
            interaction_count=interaction_count,
            now=now,
        )

        # 1) If a follow-up is already due, do that first.
        if next_followup_due is not None and next_followup_due <= now:
            actions.append(
                NextActionOut(
                    contact_id=contact.id,
                    contact_name=contact.full_name,
                    contact_email=contact.email,
                    action="follow_up",
                    reason="Follow-up reminder is due",
                    due_at=next_followup_due,
                    relationship_strength=strength,
                )
            )
            continue

        # 2) Otherwise pick the next best action.
        if last is None:
            actions.append(
                NextActionOut(
                    contact_id=contact.id,
                    contact_name=contact.full_name,
                    contact_email=contact.email,
                    action="outreach",
                    reason="No email history yet",
                    due_at=now,
                    relationship_strength=strength,
                )
            )
            continue

        if last.direction == "inbound":
            actions.append(
                NextActionOut(
                    contact_id=contact.id,
                    contact_name=contact.full_name,
                    contact_email=contact.email,
                    action="schedule_call",
                    reason="They replied recently",
                    due_at=now + timedelta(days=1),
                    relationship_strength=strength,
                )
            )
            continue

        followup_due = last.occurred_at + timedelta(days=heuristics.follow_up_days)
        if followup_due <= now:
            actions.append(
                NextActionOut(
                    contact_id=contact.id,
                    contact_name=contact.full_name,
                    contact_email=contact.email,
                    action="follow_up",
                    reason=f"No reply after {heuristics.follow_up_days} days",
                    due_at=followup_due,
                    relationship_strength=strength,
                )
            )

    actions.sort(key=lambda a: (a.due_at is None, a.due_at))
    return actions
