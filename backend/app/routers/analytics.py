from fastapi import APIRouter, Depends, HTTPException, Response
from sqlmodel import Session, text
from datetime import date, datetime, timedelta
import csv, io
from ..deps import get_session, get_current_user
from ..models import StaffUser, Role

router = APIRouter(tags=["analytics"])

def _enforce(user: StaffUser, store_id: int):
    if user.role != Role.HEAD_OFFICE_ADMIN and user.store_id != store_id:
        raise HTTPException(403, "Forbidden")

@router.get("/analytics/daily")
def daily(store_id: int, date_str: str, session: Session = Depends(get_session), user: StaffUser = Depends(get_current_user)):
    _enforce(user, store_id)
    d = date.fromisoformat(date_str)
    start = datetime.combine(d, datetime.min.time())
    end = start + timedelta(days=1)
    q = text("""
    SELECT COUNT(*) as bookings,
           SUM(CASE WHEN status='COMPLETED' THEN 1 ELSE 0 END) as completed,
           SUM(CASE WHEN status='NO_SHOW' THEN 1 ELSE 0 END) as no_show,
           SUM(CASE WHEN status='CANCELLED' THEN 1 ELSE 0 END) as cancelled
    FROM booking
    WHERE store_id=:store_id AND scheduled_start_at>=:start AND scheduled_start_at<:end
    """)
    row = session.exec(q, params={"store_id": store_id, "start": start, "end": end}).one()
    return {"store_id": store_id, "date": date_str, **dict(row._mapping)}

@router.get("/exports/bookings.csv")
def export_bookings_csv(store_id: int, start: str, end: str, session: Session = Depends(get_session), user: StaffUser = Depends(get_current_user)):
    _enforce(user, store_id)
    q = text("""
    SELECT id as booking_id, booking_code, store_id, service_id, consultant_id,
           scheduled_start_at, scheduled_end_at, status, source_channel, created_at
    FROM booking
    WHERE store_id=:store_id AND date(scheduled_start_at) BETWEEN :start AND :end
    ORDER BY scheduled_start_at
    """)
    rows = session.exec(q, params={"store_id": store_id, "start": start, "end": end}).all()
    output = io.StringIO()
    headers = list(rows[0]._mapping.keys()) if rows else ["booking_id"]
    writer = csv.DictWriter(output, fieldnames=headers)
    writer.writeheader()
    for r in rows:
        writer.writerow(dict(r._mapping))
    return Response(content=output.getvalue(), media_type="text/csv")
