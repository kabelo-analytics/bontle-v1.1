# Bontle V1.1 — Beauty Retail Booking & Consultation Platform (Telegram + Staff Ops + Power BI)

Bontle is a **Telegram-first** retail service booking platform inspired by enterprise systems (e.g., Zenoti) but built **lean** for mall-based beauty counters.

**Customer channel:** Telegram Bot  
**Staff UI:** Web dashboard (queue + booking details + status actions)  
**Analytics:** Power BI connects to the database (views + exports)

## What’s in this repo
- `/backend` — FastAPI API + Telegram bot + SQLModel database + auth + events + analytics views
- `/frontend` — React + Vite + Tailwind staff dashboard
- POPI-first data minimization (no phone numbers; minimal customer data)

## Key features (MVP)
- Telegram booking flow: **Store → Category → Service → (Optional) Consultant → Date → Time → Confirm**
- Service catalog is dynamic (loaded from DB; no hardcoding in bot)
- Booking status integrity with validated transitions:
  - `SCHEDULED → ARRIVED → IN_SERVICE → COMPLETED`
  - `SCHEDULED → NO_SHOW`
  - `ARRIVED → NO_SHOW` (allowed)
  - `* → CANCELLED` (MANAGER/HEAD_OFFICE_ADMIN only)
- **Event log is gold**: all meaningful actions write to `event_log`
- Staff auth (JWT access + refresh) + logout + RBAC (store-scoped for consultant/manager)
- POPI retention: `POST /admin/purge` (defaults to 90 days in examples)
- Power BI-friendly:
  - SQL views (daily ops, consultant performance, peak hours, service mix, incident rates)
  - CSV export endpoint

## POPI notes (summary)
- Customer data stored: `telegram_chat_id`, `display_first_name`, `booking_code`
- No phone numbers, IDs, addresses, birthdays.
- You can purge old records via `POST /admin/purge`.

---

# Local setup (Windows-friendly)

## 1) Backend
Open PowerShell in `backend/`

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `backend/.env`:
- `JWT_SECRET` set to a long random string
- `TELEGRAM_BOT_TOKEN` from BotFather (required for bot)
- Keep `DATABASE_URL` empty for SQLite local dev (defaults to `sqlite:///./bontle.db`)

Run API:

```powershell
uvicorn app.main:app --reload
```

Check:
- http://localhost:8000/health
- http://localhost:8000/docs

## 2) Run Telegram bot (polling) locally
In another terminal (still in `backend/` with venv activated):

```powershell
python run_polling.py
```

In Telegram, open your bot and type `/start`.

## 3) Frontend
In `frontend/`:

```bash
npm install
cp .env.example .env
npm run dev
```

Open: http://localhost:5173

### Seeded demo users (local dev)
Created by seed on backend startup:
- Manager: `manager@demo.local` / `Password123!`
- Consultant: `consultant@demo.local` / `Password123!`
- Head Office: `headoffice@demo.local` / `Password123!`

---

# Power BI (recommended approach)

## If Postgres (production)
Connect Power BI to Postgres and consume:
- tables: `booking`, `event_log`, `feedback`, `shift`, `service`, `store`, etc.
- views: `v_daily_store_ops`, `v_consultant_performance`, `v_peak_hours`, `v_service_mix`, `v_incident_rates`

## If SQLite (local)
Use a SQLite connector/ODBC, or pull CSV via:
- `GET /exports/bookings.csv?store_id=...&start=YYYY-MM-DD&end=YYYY-MM-DD`

