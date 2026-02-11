import React, { useEffect, useState } from "react";
import { login, me, stores, queueToday, updateStatus, kpisDaily } from "./api";

function todayISO() {
  const d = new Date();
  const y = d.getFullYear();
  const m = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");
  return `${y}-${m}-${day}`;
}

export function App() {
  const [token, setToken] = useState<string | null>(null);
  const [user, setUser] = useState<any | null>(null);
  const [email, setEmail] = useState("manager@demo.local");
  const [password, setPassword] = useState("Password123!");
  const [err, setErr] = useState<string | null>(null);

  const [storeList, setStoreList] = useState<any[]>([]);
  const [storeId, setStoreId] = useState<number | null>(null);
  const [queue, setQueue] = useState<any[]>([]);
  const [selected, setSelected] = useState<any | null>(null);
  const [kpis, setKpis] = useState<any | null>(null);

  useEffect(() => { stores().then(setStoreList).catch(()=>{}); }, []);

  async function doLogin(e: React.FormEvent) {
    e.preventDefault();
    setErr(null);
    try {
      const t = await login(email.trim().toLowerCase(), password);
      setToken(t.access_token);
      const u = await me(t.access_token);
      setUser(u);
      setStoreId(u.store_id ?? (storeList[0]?.id ?? null));
    } catch (ex: any) {
      setErr(String(ex?.message ?? ex));
    }
  }

  async function refreshAll() {
    if (!token || !storeId) return;
    const q = await queueToday(token, storeId);
    setQueue(q);
    if (selected) {
      const latest = q.find((b: any) => b.id === selected.id);
      if (latest) setSelected(latest);
    }
    const k = await kpisDaily(token, storeId, todayISO());
    setKpis(k);
  }

  useEffect(() => {
    if (!token || !storeId) return;
    refreshAll().catch(()=>{});
    const i = setInterval(() => refreshAll().catch(()=>{}), 10000);
    return () => clearInterval(i);
  }, [token, storeId]);

  async function setStatus(status: string) {
    if (!token || !selected) return;
    await updateStatus(token, selected.id, status);
    await refreshAll();
  }

  if (!token) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6">
        <div className="w-full max-w-md bg-white shadow-sm rounded-2xl border border-slate-200 p-6">
          <div className="text-xl font-semibold">Bontle Staff</div>
          <div className="text-slate-500 mt-1">Sign in to manage today’s queue.</div>
          <form className="mt-6 space-y-3" onSubmit={doLogin}>
            <div>
              <label className="text-sm text-slate-600">Email</label>
              <input className="mt-1 w-full rounded-xl border border-slate-200 p-3" value={email} onChange={e=>setEmail(e.target.value)} />
            </div>
            <div>
              <label className="text-sm text-slate-600">Password</label>
              <input type="password" className="mt-1 w-full rounded-xl border border-slate-200 p-3" value={password} onChange={e=>setPassword(e.target.value)} />
            </div>
            {err && <div className="text-sm text-red-600 whitespace-pre-wrap">{err}</div>}
            <button className="w-full rounded-xl bg-slate-900 text-white py-3 font-medium">Login</button>
            <div className="text-xs text-slate-500 mt-2">Demo: manager@demo.local / Password123!</div>
          </form>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen">
      <div className="sticky top-0 z-10 bg-white border-b border-slate-200">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div>
            <div className="text-lg font-semibold">Bontle — Queue</div>
            <div className="text-xs text-slate-500">{user?.email} • {user?.role}</div>
          </div>
          <div className="flex items-center gap-2">
            <select className="rounded-xl border border-slate-200 px-3 py-2 text-sm" value={storeId ?? ""} onChange={e=>setStoreId(Number(e.target.value))}>
              {storeList.map((s) => <option key={s.id} value={s.id}>{s.name} ({s.city})</option>)}
            </select>
            <button className="rounded-xl border border-slate-200 px-3 py-2 text-sm" onClick={()=>{ setToken(null); setUser(null); }}>Logout</button>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto p-4">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <Kpi label="Bookings" value={kpis?.bookings ?? "—"} />
          <Kpi label="Completed" value={kpis?.completed ?? "—"} />
          <Kpi label="No-show" value={kpis?.no_show ?? "—"} />
          <Kpi label="Cancelled" value={kpis?.cancelled ?? "—"} />
        </div>

        <div className="grid grid-cols-1 md:grid-cols-5 gap-4">
          <div className="md:col-span-2 bg-white border border-slate-200 rounded-2xl shadow-sm overflow-hidden">
            <div className="px-4 py-3 border-b border-slate-100 flex justify-between items-center">
              <div className="font-semibold">Today’s Queue</div>
              <button className="text-sm text-slate-600" onClick={()=>refreshAll().catch(()=>{})}>Refresh</button>
            </div>
            <div className="divide-y divide-slate-100">
              {queue.length===0 ? (
                <div className="p-6 text-slate-500 text-sm">No bookings yet.</div>
              ) : queue.map(b => (
                <button key={b.id} className={"w-full text-left p-4 hover:bg-slate-50 " + (selected?.id===b.id ? "bg-slate-50":"")} onClick={()=>setSelected(b)}>
                  <div className="flex items-center justify-between">
                    <div className="font-medium">{new Date(b.scheduled_start_at).toLocaleTimeString([], {hour:"2-digit", minute:"2-digit"})}</div>
                    <Pill status={b.status} />
                  </div>
                  <div className="text-xs text-slate-500 mt-1">{b.booking_code}</div>
                </button>
              ))}
            </div>
          </div>

          <div className="md:col-span-3 bg-white border border-slate-200 rounded-2xl shadow-sm">
            {!selected ? (
              <div className="p-8 text-slate-500">Select a booking to view details.</div>
            ) : (
              <div className="p-5">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <div className="text-sm text-slate-500">Booking</div>
                    <div className="text-xl font-semibold">{selected.booking_code}</div>
                    <div className="text-sm text-slate-600 mt-1">{new Date(selected.scheduled_start_at).toLocaleString()}</div>
                  </div>
                  <Pill status={selected.status} />
                </div>

                <div className="grid grid-cols-2 gap-3 mt-5">
                  <Info label="Store ID" value={String(selected.store_id)} />
                  <Info label="Service ID" value={String(selected.service_id)} />
                  <Info label="Consultant ID" value={selected.consultant_id ? String(selected.consultant_id) : "Auto"} />
                  <Info label="Channel" value={selected.source_channel} />
                </div>

                <div className="mt-6">
                  <div className="text-sm font-semibold mb-2">Actions</div>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-2">
                    <Act onClick={()=>setStatus("ARRIVED")} text="Arrived" />
                    <Act onClick={()=>setStatus("IN_SERVICE")} text="In Service" />
                    <Act onClick={()=>setStatus("COMPLETED")} text="Completed" />
                    <Act onClick={()=>setStatus("NO_SHOW")} text="No-show" />
                    <Act onClick={()=>setStatus("CANCELLED")} text="Cancel" danger />
                  </div>
                  <div className="text-xs text-slate-500 mt-2">Status transitions are validated server-side.</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function Kpi({label, value}:{label:string; value:any}) {
  return (
    <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-4">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="text-2xl font-semibold mt-1">{value}</div>
    </div>
  );
}

function Pill({status}:{status:string}) {
  const map: Record<string,string> = {
    SCHEDULED: "bg-blue-50 text-blue-700",
    ARRIVED: "bg-emerald-50 text-emerald-700",
    IN_SERVICE: "bg-amber-50 text-amber-700",
    COMPLETED: "bg-slate-100 text-slate-700",
    NO_SHOW: "bg-rose-50 text-rose-700",
    CANCELLED: "bg-slate-200 text-slate-800",
  };
  return <span className={`text-xs px-2 py-1 rounded-full ${map[status] ?? "bg-slate-100"}`}>{status}</span>;
}

function Info({label, value}:{label:string; value:string}) {
  return (
    <div className="rounded-xl border border-slate-200 p-3">
      <div className="text-xs text-slate-500">{label}</div>
      <div className="text-sm font-medium mt-1">{value}</div>
    </div>
  );
}

function Act({onClick, text, danger}:{onClick:()=>void; text:string; danger?:boolean}) {
  const cls = danger ? "bg-rose-600 hover:bg-rose-700" : "bg-slate-900 hover:bg-slate-800";
  return <button onClick={onClick} className={`rounded-xl py-3 text-sm font-medium text-white ${cls}`}>{text}</button>;
}
