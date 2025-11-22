import React, { useState, useEffect } from "react";
import { NavLink } from "react-router-dom";
import "./Navbar.css";
import logo from "../assets/logo.png";

export default function Navbar() {
  const [today, setToday] = useState("");

  useEffect(() => {
    const now = new Date();
    const formatted = now.toLocaleDateString("sk-SK", {
      year: "numeric",
      month: "long",
      day: "2-digit",
    });
    setToday(formatted);
  }, []);

  return (
    <nav className="navbar" aria-label="Top Navigation">
      <div className="nav-inner">
        <div className="brand">
          <div className="logo" aria-hidden="true">
            <img src={logo} alt="Logo" />
          </div>
          <span>BudgetApp</span>
        </div>

        <div className="nav-links" role="navigation">
          <NavLink to="/" end>
            Domov
          </NavLink>
          <NavLink to="/incomes">Príjmy</NavLink>
          <NavLink to="/expenses">Výdavky</NavLink>
          <NavLink to="/budgets">Mesačný rozpočet</NavLink>
          <NavLink to="/savings">Planovanie</NavLink>
          <NavLink to="/needs">Potreby</NavLink>
        </div>

        <div className="date-badge" title="Dátum">
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
          >
            <path
              d="M7 2v3M17 2v3M3.5 9.5h17M4 6.5h16a1.5 1.5 0 0 1 1.5 1.5v11A1.5 1.5 0 0 1 20 20.5H4A1.5 1.5 0 0 1 2.5 19V8A1.5 1.5 0 0 1 4 6.5Z"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
          <span>{today}</span>
        </div>
      </div>
    </nav>
  );
}
