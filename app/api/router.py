from __future__ import annotations

from fastapi import APIRouter

from app.api.routes import actions, campaigns, contacts, health, messages
from app.api.routes.integrations_google import router as google_router

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(campaigns.router, prefix="/campaigns", tags=["campaigns"])
api_router.include_router(contacts.router, prefix="/contacts", tags=["contacts"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])
api_router.include_router(actions.router, prefix="/actions", tags=["actions"])
api_router.include_router(google_router, prefix="/integrations/google", tags=["integrations"])
