import React, { useEffect, useMemo, useState } from "react";
import "./style/budget.css";
import { Link } from "react-router-dom";
import T from "../i18n/T";
import { useLang } from "../i18n/LanguageContext";

const USER_ID = "1be32073-0b12-4a59-b9a1-77e0d3586a4c";

export default function Budgets() {
  const { lang } = useLang();


  const [isMobile400, setIsMobile400] = useState(window.innerWidth < 1000);
  useEffect(() => {
    const onResize = () => setIsMobile400(window.innerWidth < 1000);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);


  const formatMoney = (n) => Number(n || 0).toFixed(2);
  const getMonthName = (date, lang) =>
    date.toLocaleDateString(lang === "sk" ? "sk-SK" : "en-US", {
      month: "long",
      year: "numeric",
    });

  const monthKeyFromDate = (d) => d.toISOString().slice(0, 7);


  const [currentDate, setCurrentDate] = useState(() => {
    const params = new URLSearchParams(window.location.search);
    const m = params.get("month");
    return m ? new Date(m + "-01") : new Date();
  });

  const monthKey = useMemo(() => monthKeyFromDate(currentDate), [currentDate]);

  const [loading, setLoading] = useState(false);
  const [apiError, setApiError] = useState(null);

  const [monthData, setMonthData] = useState({
    incomes: [],
    expenses: [],
    planning: [
      { category: "Potreby", percent: 40 },
      { category: "Voľný čas", percent: 10 },
      { category: "Sporenie", percent: 40 },
      { category: "Investovanie", percent: 10 },
    ],
  });

  const totalIncome = useMemo(
    () => monthData.incomes.reduce((s, i) => s + Number(i.amount || 0), 0),
    [monthData.incomes]
  );
  const totalExpense = useMemo(
    () => monthData.expenses.reduce((s, e) => s + Number(e.amount || 0), 0),
    [monthData.expenses]
  );
  const balance = totalIncome - totalExpense;

    useEffect(() => {
    document.title = "BudgetApp · Rozpočet";
  }, []);


  useEffect(() => {
    let alive = true;

    async function loadMonthlyBudget() {
      setLoading(true);
      setApiError(null);

      try {
        const url = `/api/monthly-budget?month=${encodeURIComponent(monthKey)}`;

        const res = await fetch(url, {
          method: "GET",
          headers: {
            "Accept": "application/json",
          },
          credentials: "include",
        });

        const json = await res.json().catch(() => null);

        if (!alive) return;

        if (!res.ok) {
          const msg =
            json?.error?.message ||
            json?.data?.error ||
            `Request failed (${res.status})`;
          setApiError(msg);
          setMonthData((prev) => ({
            ...prev,
            incomes: [],
            expenses: [],
          }));
          return;
        }

        if (json?.error) {
          setApiError(json.error.message || "Unknown error");
          setMonthData((prev) => ({
            ...prev,
            incomes: [],
            expenses: [],
          }));
          return;
        }

        const payload = json?.data;
        if (!payload) {
          setApiError("Empty response from server");
          setMonthData((prev) => ({
            ...prev,
            incomes: [],
            expenses: [],
          }));
          return;
        }

        const incomesUi = (payload.incomes || []).map((inc) => ({
          id: inc.id,
          date: inc.income_date ?? inc.date ?? "",
          description: inc.description ?? "",
          amount: Number(inc.amount ?? 0),
        }));

        const expensesUi = (payload.expenses || []).map((rec) => ({
          id: rec.id,
          date: rec.issue_date ?? rec.date ?? "",
          category:
            rec.category ??
            rec.vendor ??
            rec.store_name ??
            rec.description ??
            "—",
          amount: Number(rec.total_amount ?? rec.amount ?? 0),
        }));

        setMonthData((prev) => ({
          ...prev,
          incomes: incomesUi,
          expenses: expensesUi,
        }));
      } catch (e) {
        if (!alive) return;
        setApiError(e?.message || "Network error");
        setMonthData((prev) => ({
          ...prev,
          incomes: [],
          expenses: [],
        }));
      } finally {
        if (!alive) return;
        setLoading(false);
      }
    }

    loadMonthlyBudget();

    return () => {
      alive = false;
    };
  }, [monthKey]);

  const changeMonth = (offset) => {
    const newDate = new Date(currentDate);
    newDate.setMonth(currentDate.getMonth() + offset);
    const newKey = monthKeyFromDate(newDate);
    setCurrentDate(newDate);
    window.history.replaceState({}, "", `?month=${newKey}`);
  };

  const handlePercentChange = (index, value) => {
    const updated = [...monthData.planning];
    updated[index].percent = parseFloat(value) || 0;
    setMonthData({ ...monthData, planning: updated });
  };

  return (
    <div className="wrap budget">
      <div className="page-header">
        <div className="month-nav">
          <button id="prev-month" onClick={() => changeMonth(-1)}>◀</button>
          <h2>{getMonthName(currentDate, lang)}</h2>
          <button id="next-month" onClick={() => changeMonth(1)}>▶</button>
        </div>

        <div className="export-btns">
          <Link className="btn" to="/comparison">
            {lang === "sk" ? "Porovnávať mesiace" : "Compare months"}
          </Link>
          <a className="btn" href="#">
            {lang === "sk" ? "Export do PDF" : "Export to PDF"}
          </a>
          <a className="btn" href="#">
            {lang === "sk" ? "Export do CSV" : "Export to CSV"}
          </a>
        </div>
      </div>

      {loading && (
        <div style={{ margin: "10px 0", opacity: 0.8 }}>
          {lang === "sk" ? "Načítavam údaje..." : "Loading data..."}
        </div>
      )}
      {apiError && (
        <div
          style={{
            margin: "10px 0",
            padding: "10px 12px",
            borderRadius: "10px",
            border: "1px solid #f0b4b4",
            background: "#fff5f5",
          }}
        >
          <strong style={{ marginRight: 8 }}>
            {lang === "sk" ? "Chyba:" : "Error:"}
          </strong>
          {apiError}
        </div>
      )}

      <div className="section-title">
        <T sk="Príjmy a Výdavky" en="Incomes and Expenses" />
      </div>

      <div className="tables">
        <div className="table-box incomes-table">
          <div
            className="table-header"
            style={{ borderTopLeftRadius: "12px", borderRight: "1px solid #bfc2c7" }}
          >
            <h3>📊 <T sk="Príjmy" en="Incomes" /></h3>
            <Link className="table-button" to="/incomes">
              {lang === "sk" ? "+ Pridať príjem" : "+ Add income"}
            </Link>
          </div>

          <table>
            <thead>
              <tr>
                <th style={{ textAlign: "left" }}><T sk="Dátum" en="Date" /></th>
                <th style={{ textAlign: "left" }}><T sk="Popis" en="Description" /></th>
                <th style={{ textAlign: "right" }}><T sk="Suma (€)" en="Amount (€)" /></th>
              </tr>
            </thead>

            <tbody>
              {monthData.incomes.map((i) => (
                <tr key={i.id ?? `${i.date}-${i.description}`}>
                  <td>{i.date}</td>
                  <td>{i.description}</td>
                  <td className="amount-inc" style={{ textAlign: "right" }}>
                    + {formatMoney(i.amount)}
                  </td>
                </tr>
              ))}
              {!loading && monthData.incomes.length === 0 && (
                <tr>
                  <td colSpan="3" style={{ opacity: 0.7, padding: "12px" }}>
                    {lang === "sk" ? "Žiadne príjmy pre tento mesiac" : "No incomes for this month"}
                  </td>
                </tr>
              )}
            </tbody>

            <tfoot>
              <tr>
                <td colSpan="2"><strong><T sk="Spolu príjmy" en="Total income" /></strong></td>
                <td className="amount-inc" style={{ textAlign: "right" }}>
                  <strong>{formatMoney(totalIncome)}</strong>
                </td>
              </tr>
            </tfoot>
          </table>
        </div>

        <div className="table-box expenses-table">
          <div className="table-header" style={{ borderTopRightRadius: "12px" }}>
            <h3>💸 <T sk="Výdavky" en="Expenses" /></h3>
            <Link className="table-button" to="/expenses">
              {lang === "sk" ? "+ Pridať výdavok" : "+ Add expense"}
            </Link>
          </div>

          <table>
            {isMobile400 ? (
              <>
                <thead>
                  <tr>
                    <th style={{ textAlign: "left" }}><T sk="Dátum" en="Date" /></th>
                    <th style={{ textAlign: "left" }}><T sk="Popis" en="Description" /></th>
                    <th style={{ textAlign: "right" }}><T sk="Suma (€)" en="Amount (€)" /></th>
                  </tr>
                </thead>

                <tbody>
                  {monthData.expenses.map((e) => (
                    <tr key={e.id ?? `${e.date}-${e.category}`}>
                      <td>{e.date}</td>
                      <td>{e.category}</td>
                      <td className="amount-exp" style={{ textAlign: "right" }}>
                        - {formatMoney(e.amount)}
                      </td>
                    </tr>
                  ))}
                  {!loading && monthData.expenses.length === 0 && (
                    <tr>
                      <td colSpan="3" style={{ opacity: 0.7, padding: "12px" }}>
                        {lang === "sk" ? "Žiadne výdavky pre tento mesiac" : "No expenses for this month"}
                      </td>
                    </tr>
                  )}
                </tbody>

                <tfoot>
                  <tr>
                    <td colSpan="2"><strong><T sk="Spolu výdavky" en="Total expenses" /></strong></td>
                    <td className="amount-exp" style={{ textAlign: "right" }}>
                      <strong>{formatMoney(totalExpense)}</strong>
                    </td>
                  </tr>
                </tfoot>
              </>
            ) : (
              <>
                <thead>
                  <tr>
                    <th style={{ textAlign: "left" }}><T sk="Suma (€)" en="Amount (€)" /></th>
                    <th style={{ textAlign: "left" }}><T sk="Popis" en="Description" /></th>
                    <th style={{ textAlign: "left" }}><T sk="Dátum" en="Date" /></th>
                  </tr>
                </thead>

                <tbody>
                  {monthData.expenses.map((e) => (
                    <tr key={e.id ?? `${e.date}-${e.category}`}>
                      <td className="amount-exp">- {formatMoney(e.amount)}</td>
                      <td>{e.category}</td>
                      <td>{e.date}</td>
                    </tr>
                  ))}
                  {!loading && monthData.expenses.length === 0 && (
                    <tr>
                      <td colSpan="3" style={{ opacity: 0.7, padding: "12px" }}>
                        {lang === "sk" ? "Žiadne výdavky pre tento mesiac" : "No expenses for this month"}
                      </td>
                    </tr>
                  )}
                </tbody>

                <tfoot>
                  <tr>
                    <td className="amount-exp">
                      <strong>{formatMoney(totalExpense)}</strong>
                    </td>
                    <td colSpan="2">
                      <strong><T sk="Spolu výdavky" en="Total expenses" /></strong>
                    </td>
                  </tr>
                </tfoot>
              </>
            )}
          </table>
        </div>

        <div className="balance-box">
          <T sk="Zostatok" en="Balance" />:{" "}
          <strong id="main-balance">{formatMoney(balance)}</strong> €
        </div>
      </div>

      <div className="section-title">
        <T sk="📋 Plánovanie rozpočtu" en="📋 Budget Planning" />
      </div>

      <div className="plan-box">
        <div className="plan-header">
          <h3>
            <T sk="Zostatok" en="Balance" />:{" "}
            <strong id="plan-balance">{formatMoney(balance)} €</strong>
          </h3>

          <button className="table-button" type="button">
            {lang === "sk" ? "+ Pridať kategóriu" : "+ Add category"}
          </button>
        </div>

        <table id="plan-table">
          <thead>
            <tr>
              <th><T sk="Kategória" en="Category" /></th>
              <th><T sk="Percento" en="Percentage" /></th>
              <th><T sk="Čiastka (€)" en="Amount (€)" /></th>
            </tr>
          </thead>

          <tbody>
            {monthData.planning.map((p, i) => {
              const amount = ((balance * p.percent) / 100).toFixed(2);
              return (
                <tr key={i}>
                  <td>{p.category}</td>
                  <td>
                    <input
                      type="number"
                      className="percent-input"
                      min="0"
                      max="100"
                      step="1"
                      value={p.percent}
                      onChange={(e) => handlePercentChange(i, e.target.value)}
                    />{" "}
                    %
                  </td>
                  <td className="plan-amount">{amount}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
