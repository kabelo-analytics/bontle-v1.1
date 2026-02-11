from sqlmodel import Session, text

VIEWS_SQL = [
"""
DROP VIEW IF EXISTS v_daily_store_ops;
CREATE VIEW v_daily_store_ops AS
SELECT store_id,
       DATE(scheduled_start_at) AS day,
       COUNT(*) AS bookings,
       SUM(CASE WHEN status='COMPLETED' THEN 1 ELSE 0 END) AS completed,
       SUM(CASE WHEN status='NO_SHOW' THEN 1 ELSE 0 END) AS no_show,
       SUM(CASE WHEN status='CANCELLED' THEN 1 ELSE 0 END) AS cancelled
FROM booking
GROUP BY store_id, DATE(scheduled_start_at);
""",
"""
DROP VIEW IF EXISTS v_peak_hours;
CREATE VIEW v_peak_hours AS
SELECT store_id,
       EXTRACT(HOUR FROM scheduled_start_at) AS hour,
       COUNT(*) AS bookings
FROM booking
GROUP BY store_id, EXTRACT(HOUR FROM scheduled_start_at);
""",
"""
DROP VIEW IF EXISTS v_service_mix;
CREATE VIEW v_service_mix AS
SELECT b.store_id,
       s.category,
       s.name AS service_name,
       COUNT(*) AS bookings,
       SUM(s.price_cents) AS value_cents
FROM booking b
JOIN service s ON s.id = b.service_id
GROUP BY b.store_id, s.category, s.name;
""",
"""
DROP VIEW IF EXISTS v_consultant_performance;
CREATE VIEW v_consultant_performance AS
SELECT store_id,
       consultant_id,
       DATE(scheduled_start_at) AS day,
       COUNT(*) AS bookings,
       SUM(CASE WHEN status='COMPLETED' THEN 1 ELSE 0 END) AS completed,
       SUM(CASE WHEN status='NO_SHOW' THEN 1 ELSE 0 END) AS no_show
FROM booking
GROUP BY store_id, consultant_id, DATE(scheduled_start_at);
""",
"""
DROP VIEW IF EXISTS v_incident_rates;
CREATE VIEW v_incident_rates AS
SELECT b.store_id,
       DATE(i.created_at) AS day,
       COUNT(i.id) AS incidents,
       COUNT(DISTINCT b.id) AS bookings,
       ROUND(
           (COUNT(i.id)::decimal / NULLIF(COUNT(DISTINCT b.id),0)) * 100,
           2
       ) AS incidents_per_100
FROM incident i
JOIN booking b ON b.id = i.booking_id
GROUP BY b.store_id, DATE(i.created_at);
"""
]

def ensure_views(session: Session):
    for sql in VIEWS_SQL:
        session.exec(text(sql))
    session.commit()
