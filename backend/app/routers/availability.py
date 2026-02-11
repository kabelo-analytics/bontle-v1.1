from fastapi import APIRouter, Depends
from sqlmodel import Session
from datetime import date
from ..deps import get_session
from ..availability import list_available_start_times

router = APIRouter(tags=["availability"])

@router.get("/availability/times")
def availability_times(store_id: int, service_id: int, date_str: str, consultant_id: int | None = None, session: Session = Depends(get_session)):
    d = date.fromisoformat(date_str)
    return {"date": date_str, "times": list_available_start_times(session, store_id=store_id, service_id=service_id, d=d, consultant_id=consultant_id)}
