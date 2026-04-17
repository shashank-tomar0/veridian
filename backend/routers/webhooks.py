"""Webhook routers — mounts WhatsApp and Telegram handlers."""

from __future__ import annotations

from fastapi import APIRouter

from bot.whatsapp import router as whatsapp_router

router = APIRouter(tags=["webhooks"])

# Mount the WhatsApp webhook routes
router.include_router(whatsapp_router)
