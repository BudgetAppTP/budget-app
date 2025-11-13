import React from "react";
import { transactionsApi, type Transaction } from "../api/endpoints";

export default function Transactions() {
  const [q, setQ] = React.useState({ month: "", kind: "", category: "", search: "" });
  const [rows, setRows] = React.useState<Transaction[]>([]);
  const [count, setCount] = React.useState(0);
  const [err, setErr] = React.useState<string | null>(null);

  const load = React.useCallback(async () => {
    setErr(null);
    try {
      const d = await transactionsApi.list(q);
      setRows(d.items);
      setCount(d.count);
    } catch (e: any) {
      setErr(String(e.message || e));
    }
  }, [q]);

  React.useEffect(() => { load(); }, [load]);

  return (
    <div>
      <h2>Transactions</h2>
      <div style={{ display: "grid", gap: 8, gridTemplateColumns: "repeat(4, 1fr) 120px", marginBottom: 12 }}>
        <input placeholder="YYYY-MM" value={q.month} onChange={e => setQ({ ...q, month: e.target.value })} />
        <select value={q.kind} onChange={e => setQ({ ...q, kind: e.target.value })}>
          <option value="">all</option>
          <option value="income">income</option>
          <option value="expense">expense</option>
        </select>
        <input placeholder="category" value={q.category} onChange={e => setQ({ ...q, category: e.target.value })} />
        <input placeholder="search" value={q.search} onChange={e => setQ({ ...q, search: e.target.value })} />
        <button onClick={load}>Search</button>
      </div>
      {err && <div style={{ color: "crimson" }}>{err}</div>}
      <div>Count: {count}</div>
      <table style={{ width: "100%", borderCollapse: "collapse" }}>
        <thead>
          <tr>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>Date</th>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>Kind</th>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>Category</th>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>Description</th>
            <th style={{ textAlign: "right", borderBottom: "1px solid #ddd" }}>Amount</th>
          </tr>
        </thead>
        <tbody>
          {rows.map(r => (
            <tr key={`${r.kind}-${r.id}`}>
              <td>{r.date}</td>
              <td>{r.kind}</td>
              <td>{r.category || ""}</td>
              <td>{r.description || ""}</td>
              <td style={{ textAlign: "right" }}>{r.amount?.toFixed ? r.amount.toFixed(2) : r.amount}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
