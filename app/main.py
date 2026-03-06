from __future__ import annotations

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.db import init_db


def create_app() -> FastAPI:
    settings = get_settings()
    init_db(settings)

    app = FastAPI(title="AI Networking Copilot", version="0.1.0")
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret_key,
        session_cookie=settings.session_cookie_name,
        https_only=settings.environment == "prod",
    )

    app.include_router(api_router)
    return app


app = create_app()

