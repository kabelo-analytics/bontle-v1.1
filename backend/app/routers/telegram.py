# backend/app/routers/telegram.py
from __future__ import annotations

from fastapi import APIRouter, Request, Header, HTTPException
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

router = APIRouter(prefix="/telegram", tags=["telegram"])


# -----------------------------
# Minimal handlers (sanity check)
# -----------------------------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="✅ Bontle is live. Send a message.",
        )


async def text_msg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat and update.effective_message and update.effective_message.text:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"✅ Received: {update.effective_message.text}",
        )


def build_ptb_application(bot_token: str) -> Application:
    app = Application.builder().token(bot_token).build()
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_msg))
    return app


# -----------------------------
# Webhook endpoint
# -----------------------------
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
