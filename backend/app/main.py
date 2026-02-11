import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

from telegram import Bot

from .config import settings
from .db import init_db, engine
from .seed import seed_if_needed
from .views import ensure_views

from .routers import auth, catalog, availability, bookings, admin, analytics
from .routers.telegram import router as telegram_router
from .routers.telegram import build_ptb_application

logger = logging.getLogger(__name__)

app = FastAPI(title="Bontle V1.1 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    # --- DB startup ---
    init_db()
    with Session(engine) as session:
        seed_if_needed(session)
        ensure_views(session)

    # --- Telegram startup (webhook mode) ---
    token = settings.telegram_bot_token
    public_base_url = settings.public_base_url
    webhook_secret = settings.telegram_webhook_secret

    # Skip Telegram if not configured
    if not token or not public_base_url:
        logger.warning("Telegram not initialized (missing TELEGRAM_BOT_TOKEN or PUBLIC_BASE_URL).")
        return

    ptb_app = build_ptb_application(token)

    await ptb_app.initialize()
    await ptb_app.start()

    app.state.telegram_app = ptb_app
    app.state.telegram_webhook_secret = webhook_secret

    webhook_url = f"{public_base_url.rstrip('/')}/telegram/webhook"

    bot = Bot(token=token)
    await bot.set_webhook(
        url=webhook_url,
        secret_token=webhook_secret if webhook_secret else None,
        allowed_updates=["message", "edited_message", "callback_query"],
        drop_pending_updates=True,
    )

    logger.info("Telegram webhook set: %s", webhook_url)


@app.on_event("shutdown")
async def shutdown():
    ptb_app = getattr(app.state, "telegram_app", None)
    if ptb_app:
        await ptb_app.stop()
        await ptb_app.shutdown()


@app.get("/health")
def health():
    return {"ok": True, "name": "bontle", "version": "1.1"}


# Routers
app.include_router(auth.router)
app.include_router(catalog.router)
app.include_router(availability.router)
app.include_router(bookings.router)
app.include_router(admin.router)
app.include_router(analytics.router)
app.include_router(telegram_router)
