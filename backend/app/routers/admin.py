from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select
from datetime import datetime, timedelta
from ..deps import get_session, get_current_user
from ..models import StaffUser, Role, Booking, EventLog, Feedback, Incident, EventType, ActorType
from ..logic import log_event

router = APIRouter(tags=["admin"])

class PurgeIn(BaseModel):
    older_than_days: int = 90

@router.post("/admin/purge")
def purge(payload: PurgeIn, session: Session = Depends(get_session), user: StaffUser = Depends(get_current_user)):
    if user.role != Role.HEAD_OFFICE_ADMIN:
        raise HTTPException(403, "Forbidden")
    cutoff = datetime.utcnow() - timedelta(days=payload.older_than_days)

    for fb in session.exec(select(Feedback).where(Feedback.created_at < cutoff)).all():
        session.delete(fb)
    for inc in session.exec(select(Incident).where(Incident.created_at < cutoff)).all():
        session.delete(inc)
    for ev in session.exec(select(EventLog).where(EventLog.occurred_at < cutoff)).all():
        session.delete(ev)

    old_bookings = session.exec(select(Booking).where(Booking.created_at < cutoff)).all()
    deleted = len(old_bookings)
    for b in old_bookings:
        session.delete(b)

    session.commit()
    log_event(session, booking_id=None, store_id=None, event_type=EventType.PURGE, actor_type=ActorType.STAFF, actor_staff_user_id=user.id, metadata={"older_than_days": payload.older_than_days, "deleted_bookings": deleted})
    return {"ok": True, "deleted_bookings": deleted}
