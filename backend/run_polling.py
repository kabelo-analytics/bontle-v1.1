import asyncio
from app.config import settings
from app.telegram_bot import start_app

async def main():
    if not settings.telegram_bot_token:
        raise SystemExit("Set TELEGRAM_BOT_TOKEN in backend/.env")
    app = await start_app(settings.telegram_bot_token)
    print("Telegram bot polling started...")
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
