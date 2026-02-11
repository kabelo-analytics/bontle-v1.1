from __future__ import annotations
from datetime import datetime, date, time, timedelta
from sqlmodel import Session, select
from .models import StoreHours, Booking, Service

SLOT_MINUTES = 30

def list_available_start_times(session: Session, *, store_id: int, service_id: int, d: date, consultant_id: int | None = None) -> list[str]:
    dow = d.weekday()
    hours = session.exec(select(StoreHours).where(StoreHours.store_id==store_id, StoreHours.day_of_week==dow, StoreHours.active==True)).first()
    if not hours:
        return []
    svc = session.get(Service, service_id)
    if not svc or not svc.active:
        return []
    dur = svc.duration_minutes

    start = datetime.combine(d, hours.open_time)
    end_limit = datetime.combine(d, hours.close_time)

    stmt = select(Booking).where(Booking.store_id==store_id, Booking.scheduled_start_at>=start, Booking.scheduled_start_at<end_limit)
    if consultant_id:
        stmt = stmt.where(Booking.consultant_id==consultant_id)
    existing = session.exec(stmt).all()

    def conflicts(s: datetime, e: datetime) -> bool:
        for b in existing:
            if b.status == "CANCELLED":
                continue
            if s < b.scheduled_end_at and e > b.scheduled_start_at:
                return True
        return False

    out = []
    cur = start
    step = timedelta(minutes=SLOT_MINUTES)
    while True:
        slot_end = cur + timedelta(minutes=dur)
        if slot_end > end_limit:
            break
        if not conflicts(cur, slot_end):
            out.append(cur.strftime("%H:%M"))
        cur += step
    return out
