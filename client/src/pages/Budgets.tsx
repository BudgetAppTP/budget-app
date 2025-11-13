import React from "react";
import { budgetsApi, type BudgetItem } from "../api/endpoints";

export default function Budgets() {
  const [month, setMonth] = React.useState<string>(new Date().toISOString().slice(0, 7));
  const [items, setItems] = React.useState<BudgetItem[]>([]);
  const [left, setLeft] = React.useState<number>(0);
  const [err, setErr] = React.useState<string | null>(null);

  const load = React.useCallback(async () => {
    setErr(null);
    try {
      const d = await budgetsApi.get(month);
      setItems(d.items);
      setLeft(d.left);
    } catch (e: any) {
      setErr(String(e.message || e));
    }
  }, [month]);

  React.useEffect(() => { load(); }, [load]);

  const save = async () => {
    try {
      await budgetsApi.upsert(month, items.map(i => ({
        id: i.id,
        section: i.section,
        limit_amount: i.limit_amount,
        percent_target: i.percent_target
      })));
      await load();
    } catch (e: any) {
      setErr(String(e.message || e));
    }
  };

  const setField = (idx: number, field: keyof BudgetItem, value: any) => {
    setItems(prev => prev.map((x, i) => i === idx ? { ...x, [field]: value } : x));
  };

  return (
    <div>
      <h2>Budgets</h2>
      <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 12 }}>
        <input type="month" value={month} onChange={e => setMonth(e.target.value)} />
        <button onClick={load}>Reload</button>
        <button onClick={save}>Save</button>
      </div>
      {err && <div style={{ color: "crimson" }}>{err}</div>}
      <div>Total left: {left}</div>
      <table style={{ width: "100%", borderCollapse: "collapse", marginTop: 8 }}>
        <thead>
          <tr>
            <th style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>Section</th>
            <th style={{ textAlign: "right", borderBottom: "1px solid #ddd" }}>Limit</th>
            <th style={{ textAlign: "right", borderBottom: "1px solid #ddd" }}>% Target</th>
            <th style={{ textAlign: "right", borderBottom: "1px solid #ddd" }}>Spent</th>
          </tr>
        </thead>
        <tbody>
          {items.map((i, idx) => (
            <tr key={i.id}>
              <td>{i.section}</td>
              <td style={{ textAlign: "right" }}>
                <input
                  value={i.limit_amount}
                  onChange={e => setField(idx, "limit_amount", Number(e.target.value))}
                  style={{ width: 100, textAlign: "right" }}
                />
              </td>
              <td style={{ textAlign: "right" }}>
                <input
                  value={i.percent_target}
                  onChange={e => setField(idx, "percent_target", Number(e.target.value))}
                  style={{ width: 80, textAlign: "right" }}
                />
              </td>
              <td style={{ textAlign: "right" }}>{i.spent}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
