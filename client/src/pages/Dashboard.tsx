import React from "react";
import { dashboardApi } from "../api/endpoints";

export default function Dashboard() {
  const [month, setMonth] = React.useState<string>(new Date().toISOString().slice(0, 7));
  const [data, setData] = React.useState<any | null>(null);
  const [err, setErr] = React.useState<string | null>(null);
  const load = React.useCallback(async () => {
    setErr(null);
    try {
      const d = await dashboardApi.get(month);
      setData(d);
    } catch (e: any) {
      setErr(String(e.message || e));
    }
  }, [month]);
  React.useEffect(() => { load(); }, [load]);

  return (
    <div>
      <h2>Dashboard</h2>
      <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 12 }}>
        <input type="month" value={month} onChange={e => setMonth(e.target.value)} />
        <button onClick={load}>Reload</button>
      </div>
      {err && <div style={{ color: "crimson" }}>{err}</div>}
      {data && (
        <pre style={{ background: "#f7f7f7", padding: 12, borderRadius: 6 }}>{JSON.stringify(data, null, 2)}</pre>
      )}
    </div>
  );
}
