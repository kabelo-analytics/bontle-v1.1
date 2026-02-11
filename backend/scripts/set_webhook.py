import os, sys
import httpx

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
BASE_URL = os.getenv("PUBLIC_BASE_URL")
if not TOKEN or not BASE_URL:
    print("Set TELEGRAM_BOT_TOKEN and PUBLIC_BASE_URL")
    sys.exit(1)

url = f"https://api.telegram.org/bot{TOKEN}/setWebhook"
webhook_url = f"{BASE_URL.rstrip('/')}/telegram/webhook"
r = httpx.post(url, json={"url": webhook_url})
print(r.status_code, r.text)
