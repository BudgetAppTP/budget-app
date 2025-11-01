import React from "react";
import { goalsApi, type Goal } from "../api/endpoints";

export default function Goals() {
  const [rows, setRows] = React.useState<Goal[]>([]);
  const [err, setErr] = React.useState<string | null>(null);
  const [form, setForm] = React.useState<Partial<Goal>>({ name: "", type: "save", target_amount: 0, is_done: false });

  const load = React.useCallback(async () => {
    setErr(null);
    try {
      const d = await goalsApi.list();
      setRows(d.items);
    } catch (e: any) {
      setErr(String(e.message || e));
    }
  }, []);

  React.useEffect(() => { load(); }, [load]);

  const create = async () => {
    setErr(null);
    try {
      await goalsApi.create(form);
      setForm({ name: "", type: "save", target_amount: 0, is_done: false });
      await load();
    } catch (e: any) {
      setErr(String(e.message || e));
    }
  };

  return (
    <div>
      <h2>Goals</h2>
      {err && <div style={{ color: "crimson" }}>{err}</div>}
      <div style={{ display: "grid", gridTemplateColumns: "200px 140px 140px 140px 100px 100px", gap: 8, marginBottom: 12 }}>
        <input placeholder="name" value={form.name || ""} onChange={e => setForm({ ...form, name: e.target.value })} />
        <input placeholder="type" value={form.type || ""} onChange={e => setForm({ ...form, type: e.target.value })} />
        <input placeholder="target_amount" value={form.target_amount || 0} onChange={e => setForm({ ...form, target_amount: Number(e.target.value) })} />
        <input placeholder="section" value={form.section || ""} onChange={e => setForm({ ...form, section: e.target.value })} />
        <input placeholder="from YYYY-MM" value={form.month_from || ""} onChange={e => setForm({ ...form, month_from: e.target.value })} />
        <input placeholder="to YYYY-MM" value={form.month_to || ""} onChange={e => setForm({ ...form, month_to: e.target.value })} />
      </div>
      <button onClick={create}>Create</button>

      <table style={{ width: "100%", borderCollapse: "collapse", marginTop: 12 }}>
        <thead>
          <tr>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>Name</th>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>Type</th>
            <th style={{ textAlign: "right", borderBottom: "1px solid #ddd" }}>Target</th>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>Section</th>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>Period</th>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>Done</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(g => (
            <tr key={g.id}>
              <td>{g.name}</td>
              <td>{g.type}</td>
              <td style={{ textAlign: "right" }}>{g.target_amount}</td>
              <td>{g.section || ""}</td>
              <td>{[g.month_from, g.month_to].filter(Boolean).join(" — ")}</td>
              <td>{g.is_done ? "yes" : "no"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
