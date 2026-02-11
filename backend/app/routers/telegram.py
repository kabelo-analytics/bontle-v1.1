# backend/app/routers/telegram.py
from __future__ import annotations

from fastapi import APIRouter, Request, Header, HTTPException
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

# Your real bot logic (store/category/service/date/time/confirm -> booking)
from ..telegram_bot import start, on_callback, on_text

router = APIRouter(prefix="/telegram", tags=["telegram"])


def build_ptb_application(bot_token: str) -> Application:
    app = Application.builder().token(bot_token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    return app


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    ptb_app: Application | None = getattr(request.app.state, "telegram_app", None)
    expected_secret: str | None = getattr(request.app.state, "telegram_webhook_secret", None)

    if ptb_app is None:
        raise HTTPException(status_code=503, detail="Telegram app not initialized")

    # Enforce secret token if configured
    if expected_secret:
        if (not x_telegram_bot_api_secret_token) or (x_telegram_bot_api_secret_token != expected_secret):
            raise HTTPException(status_code=401, detail="Invalid Telegram secret token")

    payload = await request.json()
    update = Update.de_json(payload, ptb_app.bot)

    await ptb_app.process_update(update)
    return {"ok": True}
