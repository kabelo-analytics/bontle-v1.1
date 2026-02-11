from __future__ import annotations
from datetime import datetime
from sqlmodel import Session
from .models import BookingStatus, EventLog, EventType, ActorType
import json

VALID_TRANSITIONS = {
    BookingStatus.SCHEDULED: {BookingStatus.ARRIVED, BookingStatus.NO_SHOW},
    BookingStatus.ARRIVED: {BookingStatus.IN_SERVICE, BookingStatus.NO_SHOW},
    BookingStatus.IN_SERVICE: {BookingStatus.COMPLETED},
    BookingStatus.COMPLETED: set(),
    BookingStatus.NO_SHOW: set(),
    BookingStatus.CANCELLED: set(),
}

def validate_transition(current: BookingStatus, target: BookingStatus, is_manager: bool) -> None:
    if target == BookingStatus.CANCELLED:
        if not is_manager:
            raise ValueError("Only manager/head office can cancel")
        return
    if target not in VALID_TRANSITIONS.get(current, set()):
        raise ValueError(f"Invalid transition {current} -> {target}")

def log_event(session: Session, *, booking_id: str | None, store_id: int | None, event_type: EventType, actor_type: ActorType, actor_staff_user_id: int | None = None, metadata: dict | None = None) -> None:
    ev = EventLog(
        booking_id=booking_id,
        store_id=store_id,
        event_type=event_type,
        actor_type=actor_type,
        actor_staff_user_id=actor_staff_user_id,
        occurred_at=datetime.utcnow(),
        metadata_json=json.dumps(metadata) if metadata else None,
    )
    session.add(ev)
    session.commit()
