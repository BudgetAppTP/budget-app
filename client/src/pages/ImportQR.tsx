import React from "react";
import { importQrApi } from "../api/endpoints";

type Row = {
  valid: boolean;
  opd: string;
  date: string;
  category: string;
  item: string;
  qnt: string;
  price: string;
  vat: string;
  seller: string;
  unit: string;
};

export default function ImportQR() {
  const [raw, setRaw] = React.useState<string>("");
  const [rows, setRows] = React.useState<Row[]>([]);
  const [err, setErr] = React.useState<string | null>(null);
  const [created, setCreated] = React.useState<number | null>(null);

  const preview = async () => {
    setErr(null);
    setCreated(null);
    try {
      const res = await importQrApi.preview(raw);
      setRows(res.items as Row[]);
    } catch (e: any) {
      setErr(String(e.message || e));
    }
  };

  const confirm = async () => {
    setErr(null);
    try {
      const res = await importQrApi.confirm(rows);
      setCreated(res.created);
    } catch (e: any) {
      setErr(String(e.message || e));
    }
  };

  return (
    <div>
      <h2>Import QR</h2>
      <textarea
        placeholder="Paste QR/eKasa payload or JSON array"
        value={raw}
        onChange={e => setRaw(e.target.value)}
        style={{ width: "100%", height: 120 }}
      />
      <div style={{ display: "flex", gap: 8, margin: "8px 0" }}>
        <button onClick={preview}>Preview</button>
        <button onClick={confirm} disabled={rows.length === 0}>Confirm</button>
      </div>
      {err && <div style={{ color: "crimson" }}>{err}</div>}
      {created !== null && <div>Created: {created}</div>}
      {rows.length > 0 && (
        <table style={{ width: "100%", borderCollapse: "collapse" }}>
          <thead>
            <tr>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>Valid</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>Date</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>Category</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>Item</th>
              <th style={{ textAlign: "right", borderBottom: "1px solid #ddd" }}>Qty</th>
              <th style={{ textAlign: "right", borderBottom: "1px solid #ddd" }}>Price</th>
              <th style={{ textAlign: "right", borderBottom: "1px solid #ddd" }}>VAT</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>Seller</th>
              <th style={{ textAlign: "left", borderBottom: "1px solid #ddd" }}>Unit</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r, i) => (
              <tr key={i}>
                <td>{r.valid ? "yes" : "no"}</td>
                <td>{r.date}</td>
                <td>{r.category}</td>
                <td>{r.item}</td>
                <td style={{ textAlign: "right" }}>{r.qnt}</td>
                <td style={{ textAlign: "right" }}>{r.price}</td>
                <td style={{ textAlign: "right" }}>{r.vat}</td>
                <td>{r.seller}</td>
                <td>{r.unit}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
