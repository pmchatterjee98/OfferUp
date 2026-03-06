from __future__ import annotations

from typing import Generator, Optional

from fastapi import Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import Settings, get_settings
from app.core.db import get_session_factory, session_scope
from app.models.user import User


def settings_dep() -> Settings:
    return get_settings()


def db_dep(settings: Settings = Depends(settings_dep)) -> Generator[Session, None, None]:
    session_factory = get_session_factory(settings)
    with session_scope(session_factory) as session:
        yield session


def current_user_dep(
    request: Request,
    db: Session = Depends(db_dep),
    settings: Settings = Depends(settings_dep),
    x_debug_user: Optional[str] = Header(default=None, alias="X-Debug-User"),
) -> User:
    if settings.environment == "dev" and x_debug_user:
        user = db.query(User).filter(User.email == x_debug_user).one_or_none()
        if user is None:
            user = User(email=x_debug_user)
            db.add(user)
            db.flush()
        return user

    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated. Connect Google first.")
    user = db.query(User).filter(User.id == user_id).one_or_none()
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid session. Connect Google again.")
    return user

