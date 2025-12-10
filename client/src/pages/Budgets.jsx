import React, { useEffect,useState } from "react";
import "./style/budget.css";
import { Link } from "react-router-dom";
import T from "../i18n/T";
import { useLang } from "../i18n/LanguageContext";

export default function Budgets() {
  const {lang} = useLang();
  const [isMobile400, setIsMobile400] = useState(window.innerWidth < 1000);

  useEffect(() => {
    const onResize = () => setIsMobile400(window.innerWidth < 1000);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);
  const demoData = {
    "2025-01": {
      incomes: [
        { id: 1, date: "2025-01-05", description: "Výplata", amount: 1000.0 },
        { id: 2, date: "2025-01-12", description: "Bonus", amount: 200.0 },
      ],
      expenses: [
        { id: 1, date: "2025-01-08", category: "Jedlo", amount: 90.0 },
        { id: 2, date: "2025-01-15", category: "Byvanie", amount: 700.0 },
      ],
      planning: [
        { category: "Potreby", percent: 40 },
        { category: "Voľný čas", percent: 10 },
        { category: "Sporenie", percent: 40 },
        { category: "Investovanie", percent: 10 },
      ],
    },
    "2025-10": {
      incomes: [
        { id: 1, date: "2025-10-01", description: "Výplata", amount: 1200.0 },
        { id: 2, date: "2025-10-10", description: "Darček", amount: 100.0 },
        { id: 3, date: "2025-10-15", description: "Predaj bicykla", amount: 350.0 },
      ],
      expenses: [
        { id: 1, date: "2025-10-02", category: "TERNO real estate", amount: 45.2 },
        { id: 2, date: "2025-10-07", category: "Byvanie", amount: 865.0 },
      ],
      planning: [
        { category: "Potreby", percent: 40 },
        { category: "Voľný čas", percent: 10 },
        { category: "Sporenie", percent: 40 },
        { category: "Investovanie", percent: 10 },
      ],
    },
    "2025-11": {
      incomes: [{ id: 1, date: "2025-11-01", description: "Výplata", amount: 1300.0 }],
      expenses: [
        { id: 1, date: "2025-11-05", category: "Jedlo", amount: 120.0 },
        { id: 2, date: "2025-11-09", category: "Byvanie", amount: 600.0 },
      ],
      planning: [
        { category: "Potreby", percent: 40 },
        { category: "Voľný čas", percent: 10 },
        { category: "Sporenie", percent: 40 },
        { category: "Investovanie", percent: 10 },
      ],
    },
  };

  const formatMoney = (n) => n.toFixed(2);
  const getMonthName = (date) =>
    date.toLocaleDateString("sk-SK", { month: "long", year: "numeric" });

  const [currentDate, setCurrentDate] = useState(() => {
    const params = new URLSearchParams(window.location.search);
    const m = params.get("month");
    return m ? new Date(m + "-01") : new Date("2025-10-01");
  });

  const monthKey = currentDate.toISOString().slice(0, 7);
  const [monthData, setMonthData] = useState(demoData[monthKey]);

  const totalIncome = monthData.incomes.reduce((s, i) => s + i.amount, 0);
  const totalExpense = monthData.expenses.reduce((s, e) => s + e.amount, 0);
  const balance = totalIncome - totalExpense;

  useEffect(() => {
    document.title = `BudgetApp · Rozpočet (${getMonthName(currentDate)})`;
  }, [currentDate]);


  const changeMonth = (offset) => {
    const newDate = new Date(currentDate);
    newDate.setMonth(currentDate.getMonth() + offset);
    const newKey = newDate.toISOString().slice(0, 7);
    setCurrentDate(newDate);
    setMonthData(demoData[newKey] || demoData["2025-10"]);
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
          <h2>{getMonthName(currentDate)}</h2>
          <button id="next-month" onClick={() => changeMonth(1)}>▶</button>
        </div>

        <div className="export-btns">
          <Link className="btn" to="/comparison">
     {lang === "sk" ? "Porovnávať mesiace" : "Compare months"}
         </Link>
          <a className="btn" href="#">  {lang === "sk" ? "Export do PDF" : "Export to PDF"}</a>
          <a className="btn" href="#"> {lang === "sk" ? "Export do CSV" : "Export to CSV"}</a>
        </div>
      </div>

      <div className="section-title">  <T sk="Príjmy a Výdavky" en="Incomes and Expenses" /></div>


      <div className="tables">
        <div className="table-box incomes-table" >
          <div className="table-header" style={{borderTopLeftRadius: "12px",borderRight: "1px solid #bfc2c7"}}>
               <h3>📊 <T sk="Príjmy" en="Incomes" /></h3>
             <Link className="table-button" to="/incomes">
        {lang === "sk" ? "+ Pridať príjem" : "+ Add income"}
         </Link>
          </div>
          <table>
            <thead>

              <tr>
              <th style={{ textAlign: "left" }}>
                <T sk="Dátum" en="Date" />
              </th>
              <th style={{ textAlign: "left" }}>
                <T sk="Popis" en="Description" />
              </th>
              <th style={{ textAlign: "right" }}>
                <T sk="Suma (€)" en="Amount (€)" />
              </th>
              </tr>
            </thead>
            <tbody>
              {monthData.incomes.map((i) => (
                <tr key={i.id}>
                  <td>{i.date}</td>
                  <td>{i.description}</td>
                  <td className="amount-inc" style={{textAlign:"right"}}>+ {formatMoney(i.amount)}</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <td colSpan="2"><strong> <T sk="Spolu príjmy" en="Total income" /></strong></td>
                <td className="amount-inc" style={{textAlign:"right"}}>
                  <strong >{formatMoney(totalIncome)}</strong>
                </td>
              </tr>
            </tfoot>
          </table>

        </div>

        <div className="table-box expenses-table">
<div className="table-header" style={{borderTopRightRadius: "12px"}}>
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
                    <th style={{ textAlign: "left" }}>
                      <T sk="Dátum" en="Date" />
                    </th>

                    <th style={{ textAlign: "left" }}>
                      <T sk="Popis" en="Description" />
                    </th>

                    <th style={{ textAlign: "right" }}>
                      <T sk="Suma (€)" en="Amount (€)" />
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {monthData.expenses.map((e) => (
                    <tr key={e.id}>
                      <td>{e.date}</td>
                      <td>{e.category}</td>
                      <td className="amount-exp" style={{ textAlign: "right" }}>
                        - {formatMoney(e.amount)}
                      </td>
                    </tr>
                  ))}
                </tbody>

                <tfoot>
                  <tr>
                    <td colSpan="2">
                      <strong><T sk="Spolu výdavky" en="Total expenses" /></strong>
                    </td>
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
                    <th style={{ textAlign: "left" }}>
                      <T sk="Suma (€)" en="Amount (€)" />
                    </th>

                    <th style={{ textAlign: "left" }}>
                      <T sk="Popis" en="Description" />
                    </th>

                    <th style={{ textAlign: "left" }}>
                      <T sk="Dátum" en="Date" />
                    </th>
                  </tr>
                </thead>

                <tbody>
                  {monthData.expenses.map((e) => (
                    <tr key={e.id}>
                      <td className="amount-exp">- {formatMoney(e.amount)}</td>
                      <td>{e.category}</td>
                      <td>{e.date}</td>
                    </tr>
                  ))}
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

      <div className="section-title"><T sk="📋 Plánovanie rozpočtu" en="📋 Budget Planning" /></div>
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
              const amount = (balance * p.percent / 100).toFixed(2);
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
                    /> %
                  </td>
                  <td className=" plan-amount">{amount}</td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}