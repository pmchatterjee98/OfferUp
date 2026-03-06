from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.api.deps import current_user_dep, db_dep, settings_dep
from app.models.contact import Contact
from app.models.followup import FollowUp
from app.models.interaction import Interaction
from app.models.user import User
from app.schemas.integrations import CalendarFollowUpCreate
from app.services.google import (
    build_calendar_service,
    build_gmail_service,
    build_google_credentials,
    get_google_oauth,
    get_google_token,
    refresh_token_if_needed,
    upsert_google_token,
)

router = APIRouter()


@router.get("/connect")
async def connect_google(request: Request, settings=Depends(settings_dep)):
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=400, detail="Google OAuth not configured")
    oauth = get_google_oauth(settings)
    return await oauth.google.authorize_redirect(request, settings.google_redirect_uri)


@router.get("/callback")
async def google_callback(
    request: Request,
    db: Session = Depends(db_dep),
    settings=Depends(settings_dep),
) -> Dict[str, Any]:
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=400, detail="Google OAuth not configured")

    oauth = get_google_oauth(settings)
    token: Dict[str, Any] = await oauth.google.authorize_access_token(request)

    # Pull user identity from OIDC userinfo.
    resp = await oauth.google.get("https://openidconnect.googleapis.com/v1/userinfo", token=token)
    resp.raise_for_status()
    userinfo = resp.json()

    email = userinfo.get("email")
    if not email:
        raise HTTPException(status_code=400, detail="Google userinfo missing email")

    user = db.query(User).filter(User.email == email).one_or_none()
    if user is None:
        user = User(email=email, full_name=userinfo.get("name"))
        db.add(user)
        db.flush()

    upsert_google_token(db, user_id=user.id, provider_token=token)
    request.session["user_id"] = user.id

    return {"connected": True, "email": email}


@router.get("/status")
def google_status(
    db: Session = Depends(db_dep),
    user: User = Depends(current_user_dep),
) -> Dict[str, Any]:
    token = get_google_token(db, user_id=user.id)
    return {"connected": token is not None}


@router.post("/gmail/sync/contact/{contact_id}")
def sync_gmail_for_contact(
    contact_id: str,
    db: Session = Depends(db_dep),
    user: User = Depends(current_user_dep),
    settings=Depends(settings_dep),
    max_results: int = 20,
) -> Dict[str, Any]:
    token = get_google_token(db, user_id=user.id)
    if token is None:
        raise HTTPException(status_code=400, detail="Google not connected")

    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user.id).one_or_none()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")

    creds = build_google_credentials(settings, token)
    refresh_token_if_needed(db, token, creds)
    gmail = build_gmail_service(creds)

    query = f"from:{contact.email} OR to:{contact.email}"
    results = gmail.users().messages().list(userId="me", q=query, maxResults=max_results).execute()
    messages = results.get("messages") or []

    added = 0
    newest: Optional[datetime] = contact.last_interaction_at

    for item in messages:
        msg_id = item.get("id")
        if not msg_id:
            continue

        existing = (
            db.query(Interaction.id)
            .filter(
                Interaction.user_id == user.id,
                Interaction.contact_id == contact.id,
                Interaction.external_id == msg_id,
            )
            .first()
        )
        if existing:
            continue

        msg = (
            gmail.users()
            .messages()
            .get(
                userId="me",
                id=msg_id,
                format="metadata",
                metadataHeaders=["From", "To", "Subject", "Date"],
            )
            .execute()
        )

        headers = {h["name"].lower(): h.get("value") for h in (msg.get("payload", {}).get("headers") or [])}
        from_header = headers.get("from", "")
        direction = "outbound" if user.email.lower() in from_header.lower() else "inbound"
        internal_ms = int(msg.get("internalDate") or "0")
        occurred_at = datetime.fromtimestamp(internal_ms / 1000.0, tz=timezone.utc)

        db.add(
            Interaction(
                user_id=user.id,
                contact_id=contact.id,
                source="gmail",
                direction=direction,
                occurred_at=occurred_at,
                subject=headers.get("subject"),
                snippet=msg.get("snippet"),
                external_id=msg_id,
            )
        )
        added += 1
        if newest is None or occurred_at > newest:
            newest = occurred_at

    if newest and (contact.last_interaction_at is None or newest > contact.last_interaction_at):
        contact.last_interaction_at = newest
        db.add(contact)

    db.flush()
    return {"added": added}


@router.post("/calendar/followup/{contact_id}")
def schedule_followup(
    contact_id: str,
    payload: CalendarFollowUpCreate,
    db: Session = Depends(db_dep),
    user: User = Depends(current_user_dep),
    settings=Depends(settings_dep),
) -> Dict[str, Any]:
    token = get_google_token(db, user_id=user.id)
    if token is None:
        raise HTTPException(status_code=400, detail="Google not connected")

    contact = db.query(Contact).filter(Contact.id == contact_id, Contact.user_id == user.id).one_or_none()
    if contact is None:
        raise HTTPException(status_code=404, detail="Contact not found")

    creds = build_google_credentials(settings, token)
    refresh_token_if_needed(db, token, creds)
    calendar = build_calendar_service(creds)

    start = payload.due_at
    if start.tzinfo is None:
        start = start.replace(tzinfo=timezone.utc)
    start = start.astimezone(timezone.utc)
    end = start + timedelta(minutes=payload.duration_minutes)

    summary = payload.summary or f"Follow up: {contact.full_name}"
    body = {
        "summary": summary,
        "description": payload.description,
        "start": {"dateTime": start.isoformat()},
        "end": {"dateTime": end.isoformat()},
    }
    event = calendar.events().insert(calendarId="primary", body=body).execute()

    followup = FollowUp(
        user_id=user.id,
        contact_id=contact.id,
        due_at=start,
        status="pending",
        calendar_event_id=event.get("id"),
    )
    db.add(followup)
    db.flush()

    return {"created": True, "event_id": followup.calendar_event_id}
