from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import Settings
from app.models.base import Base

_ENGINE = None
_SESSION_FACTORY: Optional[sessionmaker] = None


def _ensure_sqlite_dir(database_url: str) -> None:
    if not database_url.startswith("sqlite:///"):
        return
    path = database_url[len("sqlite:///") :]
    dir_path = os.path.dirname(path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)


def create_db_engine(settings: Settings):
    _ensure_sqlite_dir(settings.database_url)
    connect_args = {}
    if settings.database_url.startswith("sqlite:///"):
        connect_args = {"check_same_thread": False}
    return create_engine(
        settings.database_url,
        pool_pre_ping=True,
        future=True,
        connect_args=connect_args,
    )


def init_db(settings: Settings) -> None:
    global _ENGINE, _SESSION_FACTORY
    if _ENGINE is None:
        _ENGINE = create_db_engine(settings)
        _SESSION_FACTORY = sessionmaker(autocommit=False, autoflush=False, bind=_ENGINE, class_=Session)
        Base.metadata.create_all(bind=_ENGINE)


def get_session_factory(settings: Settings):
    init_db(settings)
    assert _SESSION_FACTORY is not None
    return _SESSION_FACTORY


@contextmanager
def session_scope(session_factory) -> Generator[Session, None, None]:
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
