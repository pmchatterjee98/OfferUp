from __future__ import annotations

from functools import lru_cache
from typing import Any, Dict, Optional

from authlib.integrations.starlette_client import OAuth
from google.auth.transport.requests import Request as GoogleRequest
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.oauth_token import OAuthToken


@lru_cache(maxsize=1)
def _oauth_cached(
    client_id: str,
    client_secret: str,
    scopes: str,
) -> OAuth:
    oauth = OAuth()
    oauth.register(
        name="google",
        client_id=client_id,
        client_secret=client_secret,
        server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
        client_kwargs={"scope": scopes},
    )
    return oauth


def get_google_oauth(settings: Settings) -> OAuth:
    if not settings.google_client_id or not settings.google_client_secret:
        raise RuntimeError("Google OAuth not configured")
    return _oauth_cached(settings.google_client_id, settings.google_client_secret, settings.google_scopes)


def get_google_token(db: Session, user_id: str) -> Optional[OAuthToken]:
    return (
        db.query(OAuthToken)
        .filter(OAuthToken.user_id == user_id, OAuthToken.provider == "google")
        .one_or_none()
    )


def upsert_google_token(db: Session, user_id: str, provider_token: Dict[str, Any]) -> OAuthToken:
    record = get_google_token(db, user_id=user_id)
    if record is None:
        record = OAuthToken(user_id=user_id, provider="google", access_token="placeholder")
        db.add(record)

    record.access_token = str(provider_token.get("access_token") or "")
    if provider_token.get("refresh_token"):
        record.refresh_token = provider_token.get("refresh_token")
    record.token_type = provider_token.get("token_type")
    scope = provider_token.get("scope")
    if isinstance(scope, list):
        scope = " ".join(scope)
    record.scope = scope
    expires_at = provider_token.get("expires_at")
    if expires_at is not None:
        try:
            record.expires_at = int(expires_at)
        except (TypeError, ValueError):
            record.expires_at = None
    record.id_token = provider_token.get("id_token")

    db.add(record)
    db.flush()
    return record


def build_google_credentials(settings: Settings, token: OAuthToken) -> Credentials:
    if not settings.google_client_id or not settings.google_client_secret:
        raise RuntimeError("Google OAuth not configured")

    scopes = (token.scope.split() if token.scope else settings.google_scopes.split()) or None
    creds = Credentials(
        token=token.access_token,
        refresh_token=token.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.google_client_id,
        client_secret=settings.google_client_secret,
        scopes=scopes,
    )
    if token.expires_at:
        # google-auth uses datetime for expiry; assigning is safe.
        import datetime as _dt

        creds.expiry = _dt.datetime.fromtimestamp(token.expires_at, tz=_dt.timezone.utc)
    return creds


def refresh_token_if_needed(db: Session, token_row: OAuthToken, creds: Credentials) -> None:
    if not creds.expired:
        return
    if not creds.refresh_token:
        return

    creds.refresh(GoogleRequest())
    token_row.access_token = creds.token
    if creds.expiry:
        token_row.expires_at = int(creds.expiry.timestamp())
    db.add(token_row)
    db.flush()


def build_gmail_service(creds: Credentials):
    return build("gmail", "v1", credentials=creds, cache_discovery=False)


def build_calendar_service(creds: Credentials):
    return build("calendar", "v3", credentials=creds, cache_discovery=False)
