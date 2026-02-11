from __future__ import annotations
from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime, date, time
import uuid
from enum import Enum

class Role(str, Enum):
    CONSULTANT = "CONSULTANT"
    MANAGER = "MANAGER"
    HEAD_OFFICE_ADMIN = "HEAD_OFFICE_ADMIN"

class BookingStatus(str, Enum):
    SCHEDULED = "SCHEDULED"
    ARRIVED = "ARRIVED"
    IN_SERVICE = "IN_SERVICE"
    COMPLETED = "COMPLETED"
    NO_SHOW = "NO_SHOW"
    CANCELLED = "CANCELLED"

class ActorType(str, Enum):
    SYSTEM = "system"
    STAFF = "staff"
    CUSTOMER = "customer"

class Store(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    brand: Optional[str] = Field(default="Bontle Beauty", index=True)
    region: str = Field(index=True)
    name: str = Field(index=True)
    city: str = Field(index=True, default="Gauteng")
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Station(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    store_id: int = Field(foreign_key="store.id", index=True)
    name: str = Field(index=True)
    is_active: bool = Field(default=True)

class Service(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    store_id: int = Field(foreign_key="store.id", index=True)
    category: str = Field(index=True)
    name: str = Field(index=True)
    duration_minutes: int
    price_cents: int
    active: bool = Field(default=True)

class StoreHours(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    store_id: int = Field(foreign_key="store.id", index=True)
    day_of_week: int = Field(index=True)  # 0=Mon
    open_time: time
    close_time: time
    active: bool = Field(default=True)

class Customer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    telegram_chat_id: str = Field(index=True, unique=True)
    display_first_name: Optional[str] = Field(default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class StaffUser(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    role: Role = Field(index=True)
    store_id: Optional[int] = Field(default=None, foreign_key="store.id", index=True)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class RefreshToken(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    staff_user_id: int = Field(foreign_key="staffuser.id", index=True)
    token_jti: str = Field(index=True, unique=True)
    expires_at: datetime
    is_revoked: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)

class Booking(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    booking_code: str = Field(index=True, unique=True)
    store_id: int = Field(foreign_key="store.id", index=True)
    station_id: Optional[int] = Field(default=None, foreign_key="station.id", index=True)
    service_id: int = Field(foreign_key="service.id", index=True)
    consultant_id: Optional[int] = Field(default=None, foreign_key="staffuser.id", index=True)
    customer_id: int = Field(foreign_key="customer.id", index=True)

    scheduled_start_at: datetime = Field(index=True)
    scheduled_end_at: datetime = Field(index=True)
    status: BookingStatus = Field(index=True, default=BookingStatus.SCHEDULED)
    source_channel: str = Field(default="TELEGRAM", index=True)

    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class EventType(str, Enum):
    BOOKED = "BOOKED"
    RESCHEDULED = "RESCHEDULED"
    CANCELLED = "CANCELLED"
    ARRIVED = "ARRIVED"
    IN_SERVICE = "IN_SERVICE"
    COMPLETED = "COMPLETED"
    NO_SHOW = "NO_SHOW"
    ASSIGNED = "ASSIGNED"
    INCIDENT_LOGGED = "INCIDENT_LOGGED"
    FEEDBACK_RECEIVED = "FEEDBACK_RECEIVED"
    PURGE = "PURGE"

class EventLog(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    booking_id: Optional[str] = Field(default=None, foreign_key="booking.id", index=True)
    store_id: Optional[int] = Field(default=None, foreign_key="store.id", index=True)
    event_type: EventType = Field(index=True)
    actor_type: ActorType = Field(index=True)
    actor_staff_user_id: Optional[int] = Field(default=None, foreign_key="staffuser.id", index=True)
    occurred_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    metadata_json: Optional[str] = Field(default=None)

class Feedback(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    booking_id: str = Field(foreign_key="booking.id", index=True)
    rating_1_5: int = Field(index=True)
    comment: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
    store_id: int = Field(index=True)
    service_id: int = Field(index=True)
    consultant_id: Optional[int] = Field(default=None, index=True)

class Incident(SQLModel, table=True):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), primary_key=True)
    booking_id: str = Field(foreign_key="booking.id", index=True)
    staff_user_id: Optional[int] = Field(default=None, foreign_key="staffuser.id", index=True)
    category: str = Field(index=True)
    severity: str = Field(index=True)
    note: str
    created_at: datetime = Field(default_factory=datetime.utcnow, index=True)
