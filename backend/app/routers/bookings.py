from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select, text
from datetime import datetime, date, timedelta
import csv, io

from ..deps import get_session, get_current_user
from ..models import Booking, BookingStatus, StaffUser, Role, EventType, ActorType, Incident
from ..logic import validate_transition, log_event

router = APIRouter(tags=["bookings"])

@router.get("/queue/today")
def queue_today(store_id: int, session: Session = Depends(get_session), user: StaffUser = Depends(get_current_user)):
    if user.role != Role.HEAD_OFFICE_ADMIN and user.store_id != store_id:
        raise HTTPException(403, "Forbidden")
    today = datetime.utcnow().date()
    start = datetime.combine(today, datetime.min.time())
    end = start + timedelta(days=1)
    stmt = select(Booking).where(Booking.store_id==store_id, Booking.scheduled_start_at>=start, Booking.scheduled_start_at<end).order_by(Booking.scheduled_start_at)
    return session.exec(stmt).all()

class StatusIn(BaseModel):
    status: BookingStatus

@router.patch("/bookings/{booking_id}/status")
def update_status(booking_id: str, payload: StatusIn, session: Session = Depends(get_session), user: StaffUser = Depends(get_current_user)):
    booking = session.get(Booking, booking_id)
    if not booking:
        raise HTTPException(404, "Not found")
    if user.role != Role.HEAD_OFFICE_ADMIN and user.store_id != booking.store_id:
        raise HTTPException(403, "Forbidden")

    is_manager = user.role in (Role.MANAGER, Role.HEAD_OFFICE_ADMIN)
    try:
        validate_transition(booking.status, payload.status, is_manager=is_manager)
    except ValueError as e:
        raise HTTPException(400, str(e))

    booking.status = payload.status
    booking.updated_at = datetime.utcnow()
    session.add(booking); session.commit()

    mapping = {
        BookingStatus.ARRIVED: EventType.ARRIVED,
        BookingStatus.IN_SERVICE: EventType.IN_SERVICE,
        BookingStatus.COMPLETED: EventType.COMPLETED,
        BookingStatus.NO_SHOW: EventType.NO_SHOW,
        BookingStatus.CANCELLED: EventType.CANCELLED,
    }
    ev = mapping.get(payload.status)
    if ev:
        log_event(session, booking_id=booking.id, store_id=booking.store_id, event_type=ev, actor_type=ActorType.STAFF, actor_staff_user_id=user.id)
    return {"ok": True, "status": booking.status}

class IncidentIn(BaseModel):
    booking_id: str
    severity: str
    category: str
    note: str

@router.post("/incidents")
def incidents(payload: IncidentIn, session: Session = Depends(get_session), user: StaffUser = Depends(get_current_user)):
    booking = session.get(Booking, payload.booking_id)
    if not booking:
        raise HTTPException(404, "Not found")
    if user.role != Role.HEAD_OFFICE_ADMIN and user.store_id != booking.store_id:
        raise HTTPException(403, "Forbidden")
    inc = Incident(booking_id=payload.booking_id, staff_user_id=user.id, severity=payload.severity, category=payload.category, note=payload.note)
    session.add(inc); session.commit()
    log_event(session, booking_id=booking.id, store_id=booking.store_id, event_type=EventType.INCIDENT_LOGGED, actor_type=ActorType.STAFF, actor_staff_user_id=user.id)
    return {"ok": True, "id": inc.id}
