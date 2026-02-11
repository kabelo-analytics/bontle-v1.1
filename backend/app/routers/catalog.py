from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from ..deps import get_session
from ..models import Store, Service, StaffUser

router = APIRouter(tags=["catalog"])

@router.get("/stores")
def stores(session: Session = Depends(get_session)):
    return session.exec(select(Store).where(Store.is_active==True).order_by(Store.name)).all()

@router.get("/service-categories")
def categories(store_id: int, session: Session = Depends(get_session)):
    rows = session.exec(select(Service.category).where(Service.store_id==store_id, Service.active==True).distinct()).all()
    cats = [r[0] if isinstance(r, tuple) else r for r in rows]
    return sorted(cats)

@router.get("/services")
def services(store_id: int, category: str | None = None, q: str | None = None, limit: int = 25, offset: int = 0, session: Session = Depends(get_session)):
    stmt = select(Service).where(Service.store_id==store_id, Service.active==True)
    if category:
        stmt = stmt.where(Service.category==category)
    if q:
        stmt = stmt.where(Service.name.ilike(f"%{q}%"))
    return session.exec(stmt.order_by(Service.name).offset(offset).limit(limit)).all()

@router.get("/consultants")
def consultants(store_id: int, session: Session = Depends(get_session)):
    stmt = select(StaffUser).where(StaffUser.store_id==store_id, StaffUser.role=="CONSULTANT", StaffUser.is_active==True)
    return session.exec(stmt).all()
