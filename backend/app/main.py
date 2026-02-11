from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session
from .config import settings
from .db import init_db, engine
from .seed import seed_if_needed
from .views import ensure_views
from .routers import auth, catalog, availability, bookings, admin, analytics

app = FastAPI(title="Bontle V1.1 API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()
    with Session(engine) as session:
        seed_if_needed(session)
        ensure_views(session)

@app.get("/health")
def health():
    return {"ok": True, "name": "bontle", "version": "1.1"}

app.include_router(auth.router)
app.include_router(catalog.router)
app.include_router(availability.router)
app.include_router(bookings.router)
app.include_router(admin.router)
app.include_router(analytics.router)
