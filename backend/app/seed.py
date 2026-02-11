from __future__ import annotations
from datetime import time
from sqlmodel import Session, select
from .models import Store, Station, Service, StoreHours, StaffUser, Role
from .security import hash_password

GAUTENG_STORES = [
    {"region": "Gauteng", "name": "Mall of Africa", "city": "Midrand"},
    {"region": "Gauteng", "name": "Sandton City", "city": "Sandton"},
    {"region": "Gauteng", "name": "Rosebank Mall", "city": "Rosebank"},
]

SERVICES = [
    ("Makeup",     "Foundation Match",         30, 20000),
    ("Makeup",     "Makeup Consultation",      45, 30000),
    ("Makeup",     "Full Glam",                60, 45000),
    ("Skincare",   "Skin Analysis",            20, 15000),
    ("Skincare",   "Routine Consult",          30, 20000),
    ("Skincare",   "Hydration Boost Advice",   30, 18000),
    ("Fragrance",  "Scent Finder",             20, 12000),
    ("Fragrance",  "Fragrance Layering",       30, 17000),
    ("Makeup",     "Concealer Match",          20, 15000),
    ("Makeup",     "Brow Advice",              15,  9000),
    ("Skincare",   "SPF Consult",              20, 12000),
    ("Skincare",   "Acne Support Consult",     30, 20000),
    ("Makeup",     "Lip Shade Match",          15,  9000),
    ("Fragrance",  "Gift Scent Consult",       20, 12000),
    ("Makeup",     "Quick Touch-Up",           15,  8000),
]


def seed_if_needed(session: Session) -> None:
    # If any store already exists → assume DB is seeded
    if session.exec(select(Store)).first() is not None:
        return

    store_ids = []

    for store_data in GAUTENG_STORES:
        store = Store(**store_data)
        session.add(store)
        session.commit()
        session.refresh(store)
        store_ids.append(store.id)

        # Add two stations per store
        session.add(Station(store_id=store.id, name="Kiosk 1"))
        session.add(Station(store_id=store.id, name="Kiosk 2"))
        session.commit()

        # Add opening hours for all 7 days (Mon=0 ... Sun=6)
        for dow in range(7):
            session.add(
                StoreHours(
                    store_id=store.id,
                    day_of_week=dow,
                    open_time=time(9, 0),
                    close_time=time(18, 0),
                    active=True
                )
            )
        session.commit()

        # Add services for this store
        for category, name, duration, price_cents in SERVICES:
            session.add(
                Service(
                    store_id=store.id,
                    category=category,
                    name=name,
                    duration_minutes=duration,
                    price_cents=price_cents,
                    active=True
                )
            )
        session.commit()

    # ────────────────────────────────────────────────
    # Create default staff users (using first store)
    # ────────────────────────────────────────────────
    password_hash = hash_password("Password123!")

    default_store_id = store_ids[0]  # Mall of Africa

    # Manager → assigned to a store
    session.add(
        StaffUser(
            email="manager@demo.com",
            hashed_password=password_hash,
            role=Role.MANAGER,
            store_id=default_store_id,
            is_active=True
        )
    )

    # Consultant → assigned to a store
    session.add(
        StaffUser(
            email="consultant@demo.com",
            hashed_password=password_hash,
            role=Role.CONSULTANT,
            store_id=default_store_id,
            is_active=True
        )
    )

    # Head office admin → no store assigned
    session.add(
        StaffUser(
            email="headoffice@demo.com",
            hashed_password=password_hash,
            role=Role.HEAD_OFFICE_ADMIN,
            store_id=None,
            is_active=True
        )
    )

    session.commit()