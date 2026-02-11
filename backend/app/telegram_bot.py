from __future__ import annotations
from datetime import datetime, timedelta, date
from typing import Optional
import random, string

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters
from sqlmodel import Session, select

from .db import engine
from .models import Store, Service, StaffUser, Customer, Booking, BookingStatus, EventType, ActorType, Feedback
from .availability import list_available_start_times
from .logic import log_event

def _code(prefix="BO"):
    return f"{prefix}-" + "".join(random.choices(string.digits, k=4))

def _with_session(fn):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        with Session(engine) as session:
            return await fn(update, context, session)
    return wrapper

async def start_app(token: str):
    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    return app

@_with_session
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE, session: Session):
    context.user_data.clear()
    stores = session.exec(select(Store).where(Store.is_active==True).order_by(Store.name)).all()
    kb = [[InlineKeyboardButton(s.name, callback_data=f"store:{s.id}")] for s in stores]
    await update.message.reply_text("Welcome to Bontle ✨\nChoose a store:", reply_markup=InlineKeyboardMarkup(kb))

@_with_session
async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE, session: Session):
    store_id = context.user_data.get("store_id")
    if not store_id:
        await update.message.reply_text("Type /start to begin.")
        return
    qtxt = (update.message.text or "").strip()
    services = session.exec(select(Service).where(Service.store_id==store_id, Service.active==True, Service.name.ilike(f"%{qtxt}%")).limit(10)).all()
    if not services:
        await update.message.reply_text("No matching services. Tap Back.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅ Back", callback_data="back:category")]]))
        return
    kb = [[InlineKeyboardButton(f"{s.name} • R{(s.price_cents/100):.0f} • {s.duration_minutes}m", callback_data=f"service:{s.id}")] for s in services]
    kb.append([InlineKeyboardButton("⬅ Back", callback_data="back:category")])
    await update.message.reply_text("Select a service:", reply_markup=InlineKeyboardMarkup(kb))

@_with_session
async def on_callback(update: Update, context: ContextTypes.DEFAULT_TYPE, session: Session):
    cq = update.callback_query
    await cq.answer()
    data = cq.data or ""

    if data.startswith("store:"):
        store_id = int(data.split(":")[1])
        context.user_data["store_id"] = store_id
        cats = session.exec(select(Service.category).where(Service.store_id==store_id, Service.active==True).distinct()).all()
        cats = [c[0] if isinstance(c, tuple) else c for c in cats]
        kb = [[InlineKeyboardButton(c, callback_data=f"cat:{c}")] for c in sorted(cats)]
        kb.append([InlineKeyboardButton("Search service 🔎", callback_data="search:service")])
        await cq.edit_message_text("Choose a category:", reply_markup=InlineKeyboardMarkup(kb))
        return

    if data.startswith("cat:"):
        cat = data.split(":",1)[1]
        context.user_data["category"] = cat
        store_id = context.user_data["store_id"]
        services = session.exec(select(Service).where(Service.store_id==store_id, Service.category==cat, Service.active==True).order_by(Service.name).limit(12)).all()
        kb = [[InlineKeyboardButton(f"{s.name} • R{(s.price_cents/100):.0f} • {s.duration_minutes}m", callback_data=f"service:{s.id}")] for s in services]
        kb.append([InlineKeyboardButton("Search service 🔎", callback_data="search:service")])
        kb.append([InlineKeyboardButton("⬅ Back", callback_data="back:store")])
        await cq.edit_message_text("Select a service:", reply_markup=InlineKeyboardMarkup(kb))
        return

    if data == "search:service":
        await cq.edit_message_text("Type part of the service name to search (e.g. 'foundation')", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅ Back", callback_data="back:category")]]))
        return

    if data.startswith("service:"):
        service_id = int(data.split(":")[1])
        context.user_data["service_id"] = service_id
        store_id = context.user_data["store_id"]
        consultants = session.exec(select(StaffUser).where(StaffUser.store_id==store_id, StaffUser.role=="CONSULTANT", StaffUser.is_active==True)).all()
        kb = [[InlineKeyboardButton("Skip (auto-assign)", callback_data="consultant:skip")]]
        kb += [[InlineKeyboardButton(c.email.split("@")[0], callback_data=f"consultant:{c.id}")] for c in consultants[:10]]
        kb.append([InlineKeyboardButton("⬅ Back", callback_data="back:category")])
        await cq.edit_message_text("Choose a consultant (optional):", reply_markup=InlineKeyboardMarkup(kb))
        return

    if data.startswith("consultant:"):
        val = data.split(":")[1]
        context.user_data["consultant_id"] = None if val=="skip" else int(val)
        today = datetime.utcnow().date()
        kb = [[InlineKeyboardButton((today+timedelta(days=i)).strftime("%a %d %b"), callback_data=f"date:{(today+timedelta(days=i)).isoformat()}")] for i in range(0,7)]
        kb.append([InlineKeyboardButton("⬅ Back", callback_data="back:service")])
        await cq.edit_message_text("Choose a date:", reply_markup=InlineKeyboardMarkup(kb))
        return

    if data.startswith("date:"):
        ds = data.split(":")[1]
        context.user_data["date_str"] = ds
        store_id = context.user_data["store_id"]
        service_id = context.user_data["service_id"]
        consultant_id = context.user_data.get("consultant_id")
        times = list_available_start_times(session, store_id=store_id, service_id=service_id, d=date.fromisoformat(ds), consultant_id=consultant_id)
        if not times:
            await cq.edit_message_text("No slots available. Choose another date.", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅ Back", callback_data="back:consultant")]]))
            return
        kb = [[InlineKeyboardButton(t, callback_data=f"time:{t}")] for t in times[:12]]
        kb.append([InlineKeyboardButton("⬅ Back", callback_data="back:consultant")])
        await cq.edit_message_text("Choose a time:", reply_markup=InlineKeyboardMarkup(kb))
        return

    if data.startswith("time:"):
        t = data.split(":")[1]
        store = session.get(Store, context.user_data["store_id"])
        svc = session.get(Service, context.user_data["service_id"])
        ds = context.user_data["date_str"]
        consultant_id = context.user_data.get("consultant_id")
        msg = f"Confirm booking:\nStore: {store.name}\nService: {svc.name} (R{svc.price_cents/100:.0f}, {svc.duration_minutes}m)\nDate: {ds} {t}\n"
        if consultant_id:
            c = session.get(StaffUser, consultant_id)
            msg += f"Consultant: {c.email.split('@')[0]}\n"
        kb = [[InlineKeyboardButton("✅ Confirm", callback_data=f"confirm:{t}")],[InlineKeyboardButton("⬅ Back", callback_data="back:date")]]
        await cq.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(kb))
        return

    if data.startswith("confirm:"):
        t = data.split(":")[1]
        store_id = context.user_data["store_id"]
        service_id = context.user_data["service_id"]
        consultant_id = context.user_data.get("consultant_id")
        ds = context.user_data["date_str"]
        dt_start = datetime.fromisoformat(f"{ds}T{t}:00")
        svc = session.get(Service, service_id)
        dt_end = dt_start + timedelta(minutes=svc.duration_minutes)

        chat_id = str(update.effective_chat.id)
        first_name = update.effective_user.first_name if update.effective_user else None
        cust = session.exec(select(Customer).where(Customer.telegram_chat_id==chat_id)).first()
        if not cust:
            cust = Customer(telegram_chat_id=chat_id, display_first_name=first_name)
            session.add(cust); session.commit(); session.refresh(cust)

        booking = Booking(
            booking_code=_code(),
            store_id=store_id,
            service_id=service_id,
            consultant_id=consultant_id,
            customer_id=cust.id,
            scheduled_start_at=dt_start,
            scheduled_end_at=dt_end,
            status=BookingStatus.SCHEDULED,
        )
        session.add(booking); session.commit(); session.refresh(booking)
        log_event(session, booking_id=booking.id, store_id=store_id, event_type=EventType.BOOKED, actor_type=ActorType.CUSTOMER, metadata={"channel":"telegram"})

        await cq.edit_message_text(f"Booked ✅\nBooking code: {booking.booking_code}\nSee you at {ds} {t}.")
        return

    if data.startswith("back:"):
        dest = data.split(":")[1]
        if dest=="store":
            stores = session.exec(select(Store).where(Store.is_active==True).order_by(Store.name)).all()
            kb = [[InlineKeyboardButton(s.name, callback_data=f"store:{s.id}")] for s in stores]
            await cq.edit_message_text("Choose a store:", reply_markup=InlineKeyboardMarkup(kb))
        else:
            await cq.edit_message_text("Type /start to begin.")
