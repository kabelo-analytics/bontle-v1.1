const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

export async function login(email: string, password: string) {
  const r = await fetch(`${API_BASE}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function me(token: string) {
  const r = await fetch(`${API_BASE}/auth/me`, { headers: { Authorization: `Bearer ${token}` } });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function stores() {
  const r = await fetch(`${API_BASE}/stores`);
  return r.json();
}

export async function queueToday(token: string, store_id: number) {
  const r = await fetch(`${API_BASE}/queue/today?store_id=${store_id}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function updateStatus(token: string, booking_id: string, status: string) {
  const r = await fetch(`${API_BASE}/bookings/${booking_id}/status`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
    body: JSON.stringify({ status }),
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}

export async function kpisDaily(token: string, store_id: number, date: string) {
  const r = await fetch(`${API_BASE}/analytics/daily?store_id=${store_id}&date_str=${date}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (!r.ok) throw new Error(await r.text());
  return r.json();
}
