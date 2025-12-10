// Comparison.jsx
import React, { useEffect, useRef, useState } from "react";
import { Chart, ArcElement, Tooltip, Legend } from "chart.js";
import "./style/comparison.css";
import T from "../i18n/T";
import { useLang } from "../i18n/LanguageContext";

Chart.register(ArcElement, Tooltip, Legend);

const DATA = {

  "2025-01": {
    label: "Január 2025",
    incomes: [
      { date: "2025-01-01", desc: "Výplata", amount: 1200, category: "Práca" },
      { date: "2025-01-10", desc: "Darček od babky", amount: 150, category: "Dar" },
      { date: "2025-01-15", desc: "Predaj starého telefónu", amount: 180, category: "Predaj" },
    ],
    expenses: [
      { date: "2025-01-03", desc: "Nájom", amount: 400, category: "Bývanie" },
      { date: "2025-01-05", desc: "Potraviny", amount: 220, category: "Jedlo" },
      { date: "2025-01-11", desc: "MHD karta", amount: 30, category: "Doprava" },
      { date: "2025-01-14", desc: "Internet", amount: 20, category: "Bývanie" },
      { date: "2025-01-18", desc: "Kino", amount: 18, category: "Voľný čas" },
    ],
    needs: [
      { date: "2025-01-02", desc: "Nájom", amount: 400, sub: "Bývanie" },
      { date: "2025-01-05", desc: "Potraviny", amount: 220, sub: "Jedlo" },
      { date: "2025-01-11", desc: "MHD karta", amount: 30, sub: "Doprava" },
      { date: "2025-01-20", desc: "Lekáreň", amount: 25, sub: "Zdravie" },
    ],
    goals: [
      { name: "Mesačný limit na jedlo", type: "monthly", target: 250, actual: 220 },
      { name: "Ročné sporenie 2000 €", type: "yearly", target: 2000, progressYTD: 150 },
    ],
    savings: [{ date: "2025-01-07", desc: "Vklad na sporiaci účet", amount: 150 }],
    savingsAlloc: [
      { label: "Núdzový fond", amount: 80 },
      { label: "Investície", amount: 50 },
      { label: "Dovolenka", amount: 20 },
    ],
  },

  "2025-02": {
    label: "Február 2025",
    incomes: [
      { date: "2025-02-01", desc: "Výplata", amount: 1300, category: "Práca" },
      { date: "2025-02-05", desc: "Darček od babky", amount: 200, category: "Dar" },
      { date: "2025-02-10", desc: "Predaj starého bicykla", amount: 350, category: "Predaj" },
    ],
    expenses: [
      { date: "2025-02-03", desc: "Nájom", amount: 400, category: "Bývanie" },
      { date: "2025-02-06", desc: "Potraviny", amount: 260, category: "Jedlo" },
      { date: "2025-02-10", desc: "Taxi", amount: 20, category: "Doprava" },
      { date: "2025-02-14", desc: "Internet", amount: 20, category: "Bývanie" },
      { date: "2025-02-17", desc: "Divadlo", amount: 35, category: "Voľný čas" },
    ],
    needs: [
      { date: "2025-02-03", desc: "Nájom", amount: 400, sub: "Bývanie" },
      { date: "2025-02-06", desc: "Potraviny", amount: 260, sub: "Jedlo" },
      { date: "2025-02-10", desc: "Taxi", amount: 20, sub: "Doprava" },
    ],
    goals: [
      { name: "Mesačný limit na jedlo", type: "monthly", target: 250, actual: 260 },
      { name: "Ročné sporenie 2000 €", type: "yearly", target: 2000, progressYTD: 350 },
    ],
    savings: [{ date: "2025-02-08", desc: "Vklad na sporiaci účet", amount: 200 }],
    savingsAlloc: [
      { label: "Núdzový fond", amount: 100 },
      { label: "Investície", amount: 70 },
      { label: "Dovolenka", amount: 30 },
    ],
  },

  "2025-03": {
    label: "Marec 2025",
    incomes: [{ date: "2025-03-01", desc: "Výplata", amount: 1200, category: "Práca" }],
    expenses: [{ date: "2025-03-05", desc: "Potraviny", amount: 230, category: "Jedlo" }],
    needs: [{ date: "2025-03-05", desc: "Potraviny", amount: 230, sub: "Jedlo" }],
    goals: [
      { name: "Mesačný limit na jedlo", type: "monthly", target: 250, actual: 230 },
      { name: "Ročné sporenie 2000 €", type: "yearly", target: 2000, progressYTD: 500 },
    ],
    savings: [{ date: "2025-03-12", desc: "Vklad na sporiaci účet", amount: 150 }],
    savingsAlloc: [
      { label: "Núdzový fond", amount: 90 },
      { label: "Investície", amount: 40 },
      { label: "Dovolenka", amount: 20 },
    ],
  },
};


export default function Comparison() {
  const {lang} = useLang();
  const [activeTab, setActiveTab] = useState("incomes");

  const [indices, setIndices] = useState(() => {
    const len = MONTH_KEYS.length;
    return {
      left: Math.max(0, len - 2),
      right: Math.max(1, len - 1),
    };
  });

  const leftKey = MONTH_KEYS[indices.left];
  const rightKey = MONTH_KEYS[indices.right];
  const leftMonth = DATA[leftKey];
  const rightMonth = DATA[rightKey];

  const leftCanvasRef = useRef(null);
  const rightCanvasRef = useRef(null);
  const leftDetailsRef = useRef(null);
  const rightDetailsRef = useRef(null);
  const leftChartRef = useRef(null);
  const rightChartRef = useRef(null);

  const isNeeds = activeTab === "needs";
  const isGoals = activeTab === "goals";
  const isSavings = activeTab === "savings";
  const showSummary = !isNeeds && !isGoals && !isSavings;
  const showCharts = isNeeds || isSavings;
  const showCards = !isGoals;
  const showTables = activeTab === "incomes" || activeTab === "expenses";

  const handleArrowClick = (side, dir) => {
    const step = parseInt(dir, 10);
    const len = MONTH_KEYS.length;

    setIndices((prev) => {
      let left = prev.left;
      let right = prev.right;

      if (side === "left") {
        left = Math.min(Math.max(0, left + step), len - 1);
        if (left === right) {
          if (step > 0 && right < len - 1) right++;
          else if (step < 0 && right > 0) right--;
        }
      } else {
        right = Math.min(Math.max(0, right + step), len - 1);
        if (right === left) {
          if (step > 0 && left < len - 1) left++;
          else if (step < 0 && left > 0) left--;
        }
      }
      return { left, right };
    });
  };


  useEffect(() => {
    const destroyCharts = () => {
      if (leftChartRef.current) {
        leftChartRef.current.destroy();
        leftChartRef.current = null;
      }
      if (rightChartRef.current) {
        rightChartRef.current.destroy();
        rightChartRef.current = null;
      }
      if (leftDetailsRef.current) leftDetailsRef.current.innerHTML = "";
      if (rightDetailsRef.current) rightDetailsRef.current.innerHTML = "";
    };

    const renderNeedsCharts = () => {
      if (!leftCanvasRef.current || !rightCanvasRef.current) return;

      const leftData = DATA[leftKey].needs || [];
      const rightData = DATA[rightKey].needs || [];

      const groupBySub = (arr) => {
        const result = {};
        for (const r of arr) {
          if (!r.sub) continue;
          result[r.sub] = (result[r.sub] || 0) + (r.amount || 0);
        }
        return result;
      };

      const leftGrouped = groupBySub(leftData);
      const rightGrouped = groupBySub(rightData);

      const labelsL = Object.keys(leftGrouped);
      const labelsR = Object.keys(rightGrouped);
      const dataL = Object.values(leftGrouped);
      const dataR = Object.values(rightGrouped);

      if (leftChartRef.current) leftChartRef.current.destroy();
      if (rightChartRef.current) rightChartRef.current.destroy();

      const makeChart = (canvas, labels, data) =>
        new Chart(canvas, {
          type: "doughnut",
          data: {
            labels,
            datasets: [
              {
                data,
                backgroundColor: chartColors.slice(0, labels.length),
                hoverOffset: 10,
              },
            ],
          },
          options: {
            cutout: "65%",
            plugins: {
              legend: { display: false },
              tooltip: {
                backgroundColor: "#333",
                titleColor: "#fff",
                callbacks: {
                  label: (ctx) => `${ctx.label}: ${fmt(ctx.parsed)} €`,
                },
              },
            },
          },
        });

      leftChartRef.current = makeChart(leftCanvasRef.current, labelsL, dataL);
      rightChartRef.current = makeChart(rightCanvasRef.current, labelsR, dataR);

      const renderDetailsHTML = (labels, data) => {
        const total = data.reduce((a, b) => a + b, 0);
        let html = labels
          .map((label, i) => {
            const percent = total > 0 ? ((data[i] / total) * 100).toFixed(1) : 0;
            return `
              <div class="item">
                <span><span class="color-dot" style="background:${chartColors[i]}"></span>${label}</span>
                <span>${percent}% | ${fmt(data[i])} €</span>
              </div>`;
          })
          .join("");
        html += `<div class="summary">${lang === "sk" ? "Celkovo" : "Total"}: ${fmt(total)} €</div>`;
        return html;
      };

      if (leftDetailsRef.current) {
        leftDetailsRef.current.innerHTML = renderDetailsHTML(labelsL, dataL);
      }
      if (rightDetailsRef.current) {
        rightDetailsRef.current.innerHTML = renderDetailsHTML(labelsR, dataR);
      }
    };

    const renderSavingsCharts = () => {
      if (!leftCanvasRef.current || !rightCanvasRef.current) return;

      const leftInfo = computeSavings(leftKey);
      const rightInfo = computeSavings(rightKey);

      if (leftChartRef.current) leftChartRef.current.destroy();
      if (rightChartRef.current) rightChartRef.current.destroy();

      const makeChart = (canvas, labels, data, saved) =>
        new Chart(canvas, {
          type: "doughnut",
          data: {
            labels,
            datasets: [
              {
                data,
                backgroundColor: chartColors.slice(0, labels.length),
                hoverOffset: 10,
              },
            ],
          },
          options: {
            cutout: "70%",
            plugins: {
              legend: { display: false },
              tooltip: {
                backgroundColor: "#333",
                titleColor: "#fff",
                callbacks: {
                  label: (t) => `${t.label}: ${fmt(t.parsed)} €`,
                },
              },
            },
          },
        });

      leftChartRef.current = makeChart(
        leftCanvasRef.current,
        leftInfo.labels,
        leftInfo.data,
        leftInfo.saved
      );
      rightChartRef.current = makeChart(
        rightCanvasRef.current,
        rightInfo.labels,
        rightInfo.data,
        rightInfo.saved
      );

      const renderDetailsHTML = (labels, data) => {
        const total = data.reduce((a, b) => a + b, 0);
        let html = labels
          .map((label, i) => {
            const pct = total > 0 ? ((data[i] / total) * 100).toFixed(1) : 0;
            return `
              <div class="item">
                <span><span class="color-dot" style="background:${chartColors[i]}"></span>${label}</span>
                <span>${pct}% | ${fmt(data[i])} €</span>
              </div>`;
          })
          .join("");
        html += `<div class="summary">${lang === "sk" ? "Celkovo" : "Total"}:${fmt(total)} €</div>`;
        return html;
      };

      if (leftDetailsRef.current) {
        leftDetailsRef.current.innerHTML = renderDetailsHTML(leftInfo.labels, leftInfo.data);
      }
      if (rightDetailsRef.current) {
        rightDetailsRef.current.innerHTML = renderDetailsHTML(rightInfo.labels, rightInfo.data);
      }
    };

    if (activeTab === "needs") {
      renderNeedsCharts();
    } else if (activeTab === "savings") {
      renderSavingsCharts();
    } else {
      destroyCharts();
    }
  }, [activeTab, leftKey, rightKey, lang]);

  // (incomes/expenses)
  const leftRows = showTables ? byTab(leftKey, activeTab) : [];
  const rightRows = showTables ? byTab(rightKey, activeTab) : [];

  const leftTotalValue = showTables ? sum(leftRows) : 0;
  const rightTotalValue = showTables ? sum(rightRows) : 0;

  let summaryRow = null;
  if (showSummary) {
    const L = byTab(leftKey, activeTab);
    const R = byTab(rightKey, activeTab);
    const totalL = sum(L);
    const totalR = sum(R);
    const diffT = totalR - totalL;
    let tIcon = <span className="trend-flat">➖</span>;
    if (diffT > 1) tIcon = <span className="trend-up">🔼</span>;
    else if (diffT < -1) tIcon = <span className="trend-down">🔽</span>;

    summaryRow = {
      totalL: fmt(totalL),
      totalR: fmt(totalR),
      diff: `${diffT > 0 ? "+" : ""}${fmt(diffT)}`,
      icon: tIcon,
    };
  }

  const tabs = [
    { id: "incomes", label: <T sk="Príjmy" en="Incomes" /> },
    { id: "expenses", label: <T sk="Výdavky" en="Expenses" /> },
    { id: "needs", label: <T sk="Potreby" en="Needs" /> },
    { id: "goals", label: <T sk="Ciele" en="Goals" /> },
    { id: "savings", label: <T sk="Sporenie" en="Savings" /> },
  ];

  return (
    <div className="wrap comparison">
      <div className="page-title">📈<T sk=" Porovnanie mesiacov" en=" Monthly comparison" /></div>

      <div className="main_box">
        <div className="tabs" id="tabs">
          {tabs.map((t) => (
            <button
              key={t.id}
              className={`tab ${activeTab === t.id ? "active" : ""}`}
              data-tab={t.id}
              onClick={() => setActiveTab(t.id)}
            >
              {t.label}
            </button>
          ))}
        </div>

        <div className="main_table">
          <div className="controls">
            <div className="month-picker" id="pickerLeft">
              <button
                className="arrow-btn"
                data-side="left"
                data-dir="-1"
                aria-label="predchádzajúci mesiac"
                onClick={() => handleArrowClick("left", -1)}
              >
                <span className="arrow left"></span>
              </button>
              <div className="month-label" id="labelLeft">
                {leftMonth?.label ?? "—"}
              </div>
              <button
                className="arrow-btn"
                data-side="left"
                data-dir="1"
                aria-label="ďalší mesiac"
                onClick={() => handleArrowClick("left", 1)}
              >
                <span className="arrow right"></span>
              </button>
            </div>

            <div className="month-picker" id="pickerRight">
              <button
                className="arrow-btn"
                data-side="right"
                data-dir="-1"
                aria-label="predchádzajúci mesiac"
                onClick={() => handleArrowClick("right", -1)}
              >
                <span className="arrow left"></span>
              </button>
              <div className="month-label" id="labelRight">
                {rightMonth?.label ?? "—"}
              </div>
              <button
                className="arrow-btn"
                data-side="right"
                data-dir="1"
                aria-label="ďalší mesiac"
                onClick={() => handleArrowClick("right", 1)}
              >
                <span className="arrow right"></span>
              </button>
            </div>
          </div>

          <div className="grid">

            <div className="panel" id="leftPanel">
              <div
                className="chart-container"
                id="leftChartContainer"
                style={{ display: showCharts ? "flex" : "none" }}
              >
                <canvas id="leftDonutChart" ref={leftCanvasRef}></canvas>
                <div
                  className="chart-details"
                  id="leftChartDetails"
                  ref={leftDetailsRef}
                ></div>
              </div>

              <div
                className="card"
                style={{ display: showCards ? "block" : "none" }}
              >
                <div className="table-card">
                  <table
                    id="leftTable"
                    style={{ display: showTables ? "table" : "none" }}
                  >
                    <thead>
                      <tr>
                        <th><T sk="DÁTUM" en="DATE" /></th>
                        <th><T sk="POPIS" en="DESCRIPTION" /></th>
                        <th className="right"><T sk="SUMA (€)" en="AMOUNT (€)" /></th>
                      </tr>
                    </thead>
                    <tbody>
                      {showTables &&
                        leftRows.map((r, i) => {
                          let prefix = "";
                          if (activeTab === "incomes") prefix = "+ ";
                          else if (activeTab === "expenses") prefix = "- ";
                          return (
                            <tr key={i}>
                              <td>{r.date || "—"}</td>
                              <td>{r.desc}</td>
                              <td className="right">
                                {prefix}
                                {fmt(r.amount || 0)}
                              </td>
                            </tr>
                          );
                        })}
                    </tbody>
                    <tfoot>
                      <tr>
                        <td colSpan="2"><T sk="Spolu" en="Total" /></td>
                        <td className="right" id="leftTotal">
                          {showTables ? fmt(leftTotalValue) : fmt(0)}
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>

              {isGoals && <GoalsTable month={leftMonth} />}
            </div>

            <div className="panel" id="rightPanel">
              <div
                className="chart-container"
                id="rightChartContainer"
                style={{ display: showCharts ? "flex" : "none" }}
              >
                <canvas id="rightDonutChart" ref={rightCanvasRef}></canvas>
                <div
                  className="chart-details"
                  id="rightChartDetails"
                  ref={rightDetailsRef}
                ></div>
              </div>

              <div
                className="card"
                style={{ display: showCards ? "block" : "none" }}
              >
                <div className="table-card">
                  <table
                    id="rightTable"
                    style={{ display: showTables ? "table" : "none" }}
                  >
                    <thead>
                      <tr>
                        <th>DÁTUM</th>
                        <th>POPIS</th>
                        <th className="right">SUMA (€)</th>
                      </tr>
                    </thead>
                    <tbody>
                      {showTables &&
                        rightRows.map((r, i) => {
                          let prefix = "";
                          if (activeTab === "incomes") prefix = "+ ";
                          else if (activeTab === "expenses") prefix = "- ";
                          return (
                            <tr key={i}>
                              <td>{r.date || "—"}</td>
                              <td>{r.desc}</td>
                              <td className="right">
                                {prefix}
                                {fmt(r.amount || 0)}
                              </td>
                            </tr>
                          );
                        })}
                    </tbody>
                    <tfoot>
                      <tr>
                        <td colSpan="2">Spolu</td>
                        <td className="right" id="rightTotal">
                          {showTables ? fmt(rightTotalValue) : fmt(0)}
                        </td>
                      </tr>
                    </tfoot>
                  </table>
                </div>
              </div>

              {isGoals && <GoalsTable month={rightMonth} />}
            </div>
          </div>
        </div>

        <div
          className="panel summary-card"
          id="summaryPanel"
          style={{ display: showSummary ? "block" : "none" }}
        >
          <div className="section-title"> <T sk="Súhrn porovnania" en="Comparison summary" /></div>
          <div className="card table-card">
            <table id="summaryTable">
              <thead>
                <tr>
                  <th id="thL">
                    {leftMonth ? `${leftMonth.label} (€)` : (lang === "sk" ? "Ľavý mesiac (€)" : "Left month (€)")}
                  </th>
                  <th id="thR">
                    {rightMonth ? `${rightMonth.label} (€)` : (lang === "sk" ? "Pravý mesiac (€)" : "Right month (€)")}
                  </th>
                  <th><T sk="Rozdiel (€)" en="Difference (€)" /></th>
                  <th><T sk="Trend" en="Trend" /></th>
                </tr>
              </thead>
              <tbody>
                {summaryRow && (
                  <tr>
                    <td>{summaryRow.totalL}</td>
                    <td>{summaryRow.totalR}</td>
                    <td>{summaryRow.diff}</td>
                    <td>{summaryRow.icon}</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}


const MONTH_KEYS = Object.keys(DATA).sort();
const chartColors = ["#e6c975", "#ccb8a3", "#b1bfd0", "#c0cfad"];

const fmt = (n) =>
  n.toLocaleString("sk-SK", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

const sum = (arr) => arr.reduce((a, b) => a + (b.amount || 0), 0);

const byTab = (monthKey, tab) => {
  const d = DATA[monthKey];
  if (!d) return [];
  if (tab === "incomes") return d.incomes || [];
  if (tab === "expenses") return d.expenses || [];
  if (tab === "needs") return d.needs || [];
  if (tab === "goals") return d.goals || [];
  if (tab === "savings") return d.savings || [];
  return [];
};

const computeSavings = (monthKey) => {
  const d = DATA[monthKey] || {};
  const inc = (d.incomes || []).reduce((s, r) => s + (r.amount || 0), 0);
  const exp = (d.expenses || []).reduce((s, r) => s + (r.amount || 0), 0);
  const fromList = (d.savings || []).reduce((s, r) => s + (r.amount || 0), 0);

  const saved = fromList > 0 ? fromList : Math.max(inc - exp, 0);
  const savedPctOfIncome = inc > 0 ? (saved / inc) * 100 : 0;

  const alloc = Array.isArray(d.savingsAlloc)
    ? d.savingsAlloc
    : [{ label: "Sporenie", amount: saved }];
  const labels = alloc.map((a) => a.label);
  const data = alloc.map((a) => a.amount);

  return { saved, savedPctOfIncome, labels, data };
};

function GoalsTable({ month }) {
  if (!month) return null;

  const monthly = (month.goals || []).filter((g) => g.type === "monthly");
  const yearly = (month.goals || []).filter((g) => g.type === "yearly");

  const pct = (a, b) => (b ? (a / b) * 100 : 0);

  return (
    <div className="goals-table">
      <table className="goals-layout">
        <thead>
          <tr>
            <th><T sk="Popis" en="Description" /></th>
          <th><T sk="Cieľ (€)" en="Goal (€)" /></th>
          <th><T sk="Realita (€)" en="Actual (€)" /></th>
          <th><T sk="Splnené (%)" en="Completed (%)" /></th>
          <th><T sk="Stav" en="Status" /></th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <td colSpan="5" className="section-title">
              <T sk="Mesačné ciele" en="Monthly goals" />
            </td>
          </tr>
          {monthly.map((g, i) => {
            const p = pct(g.actual, g.target);
            const pRounded = p.toFixed(0);
            const done = p >= 100;
            return (
              <tr key={`m-${i}`}>
                <td>{g.name}</td>
                <td>{fmt(g.target)}</td>
                <td>{fmt(g.actual)}</td>
                <td>{pRounded} %</td>
                <td>
                  <span className={`status-icon ${done ? "done" : "fail"}`}>
                    {done ? "✔" : "✖"}
                  </span>
                </td>
              </tr>
            );
          })}
          <tr>
            <td colSpan="5" className="section-title">
             <T sk="Ročné ciele" en="Yearly goals" />
            </td>
          </tr>
          {yearly.map((g, i) => {
            const p = pct(g.progressYTD, g.target).toFixed(0);
            return (
              <tr key={`y-${i}`}>
                <td>{g.name}</td>
                <td>{fmt(g.target)}</td>
                <td>{fmt(g.progressYTD)}</td>
                <td>{p} %</td>
                <td>
                  <span className="status-icon progress">⏳</span>
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
