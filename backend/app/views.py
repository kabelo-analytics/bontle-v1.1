from sqlmodel import Session, text

VIEWS_SQL = [
"""
CREATE VIEW IF NOT EXISTS v_daily_store_ops AS
SELECT store_id, date(scheduled_start_at) as day,
       COUNT(*) as bookings,
       SUM(CASE WHEN status='COMPLETED' THEN 1 ELSE 0 END) as completed,
       SUM(CASE WHEN status='NO_SHOW' THEN 1 ELSE 0 END) as no_show,
       SUM(CASE WHEN status='CANCELLED' THEN 1 ELSE 0 END) as cancelled
FROM booking
GROUP BY store_id, day;
""",
"""
CREATE VIEW IF NOT EXISTS v_peak_hours AS
SELECT store_id, strftime('%H', scheduled_start_at) as hour, COUNT(*) as bookings
FROM booking
GROUP BY store_id, hour;
""",
"""
CREATE VIEW IF NOT EXISTS v_service_mix AS
SELECT b.store_id, s.category, s.name as service_name,
       COUNT(*) as bookings, SUM(s.price_cents) as value_cents
FROM booking b JOIN service s ON s.id=b.service_id
GROUP BY b.store_id, s.category, s.name;
""",
"""
CREATE VIEW IF NOT EXISTS v_consultant_performance AS
SELECT store_id, consultant_id, date(scheduled_start_at) as day,
       COUNT(*) as bookings,
       SUM(CASE WHEN status='COMPLETED' THEN 1 ELSE 0 END) as completed,
       SUM(CASE WHEN status='NO_SHOW' THEN 1 ELSE 0 END) as no_show
FROM booking
GROUP BY store_id, consultant_id, day;
""",
"""
CREATE VIEW IF NOT EXISTS v_incident_rates AS
SELECT b.store_id, date(i.created_at) as day,
       COUNT(i.id) as incidents,
       COUNT(DISTINCT b.id) as bookings,
       ROUND((CAST(COUNT(i.id) AS FLOAT) / NULLIF(COUNT(DISTINCT b.id),0))*100.0, 2) as incidents_per_100
FROM incident i JOIN booking b ON b.id=i.booking_id
GROUP BY b.store_id, day;
"""
]

def ensure_views(session: Session):
    for sql in VIEWS_SQL:
        session.exec(text(sql))
    session.commit()
