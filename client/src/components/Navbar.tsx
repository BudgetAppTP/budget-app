import React from "react";
import { NavLink } from "react-router-dom";

const linkStyle: React.CSSProperties = { display: "block", padding: "8px 12px", textDecoration: "none", color: "#222" };
const activeStyle: React.CSSProperties = { fontWeight: 700, color: "#0b57d0" };

export default function Navbar() {
  return (
    <aside style={{ width: 220, borderRight: "1px solid #eee", padding: 12 }}>
      <div style={{ fontWeight: 700, marginBottom: 12 }}>BudgetApp</div>
      <nav style={{ display: "grid", gap: 6 }}>
        <NavLink to="/" style={({ isActive }) => ({ ...linkStyle, ...(isActive ? activeStyle : {}) })}>Dashboard</NavLink>
        <NavLink to="/transactions" style={({ isActive }) => ({ ...linkStyle, ...(isActive ? activeStyle : {}) })}>Transactions</NavLink>
        <NavLink to="/budgets" style={({ isActive }) => ({ ...linkStyle, ...(isActive ? activeStyle : {}) })}>Budgets</NavLink>
        <NavLink to="/goals" style={({ isActive }) => ({ ...linkStyle, ...(isActive ? activeStyle : {}) })}>Goals</NavLink>
        <NavLink to="/import-qr" style={({ isActive }) => ({ ...linkStyle, ...(isActive ? activeStyle : {}) })}>Import QR</NavLink>
      </nav>
    </aside>
  );
}
