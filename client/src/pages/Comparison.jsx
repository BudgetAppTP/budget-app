import React, { useEffect, useMemo, useRef, useState } from "react";
import "./style/comparison.css";
import T from "../i18n/T";
import { useLang } from "../i18n/LanguageContext";

import { Chart, ArcElement, Tooltip, Legend } from "chart.js";
Chart.register(ArcElement, Tooltip, Legend);

const API_BASE = "/api";


const chartColors = ["#e6c975", "#ccb8a3", "#b1bfd0", "#c0cfad", "#d6b7c6", "#a9d1c7"];

const pad2 = (n) => String(n).padStart(2, "0");
const monthKeyFromYM = (y, m) => `${y}-${pad2(m)}`;

function buildMonthKeys(count = 12) {
  const now = new Date();
  const keys = [];
  for (let i = 0; i < count; i++) {
    const d = new Date(now.getFullYear(), now.getMonth() - (count - 1 - i), 1);
    keys.push(monthKeyFromYM(d.getFullYear(), d.getMonth() + 1));
  }
  return keys;
}

function parseMonthKey(key) {
  const [y, m] = key.split("-");
  return { year: Number(y), month: Number(m) };
}

function monthLabel(key, lang) {
  const { year, month } = parseMonthKey(key);
  const d = new Date(year, month - 1, 1);
  return d.toLocaleDateString(lang === "sk" ? "sk-SK" : "en-US", {
    month: "long",
    year: "numeric",
  });
}

const fmt = (n, lang) =>
  Number(n || 0).toLocaleString(lang === "sk" ? "sk-SK" : "en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });

function unwrap(payload) {
  if (payload && typeof payload === "object" && "data" in payload) return payload.data;
  return payload;
}

function normalize(kind, raw) {
  const data = unwrap(raw);

  if (kind === "incomes") {
    const incomes = data?.incomes && Array.isArray(data.incomes) ? data.incomes : [];
    const total = Number(data?.total_amount ?? 0);
    return { rows: incomes, total };
  }

  const list = Array.isArray(data) ? data : Array.isArray(data?.receipts) ? data.receipts : [];
  const total = list.reduce((s, r) => s + Number(r?.total_amount ?? r?.amount ?? 0), 0);
  return { rows: list, total };
}

function normalizeNeeds(raw) {
  const data = unwrap(raw);

  const categories = Array.isArray(data?.categories) ? data.categories : [];

  return {
    total: Number(data?.total_amount ?? 0),
    labels: categories.map((c) => c.category),
    data: categories.map((c) => Number(c.amount ?? 0)),
  };
}

function mapRow(kind, r) {
  if (kind === "incomes") {
    return {
      date: r.income_date ?? r.date ?? null,
      desc: r.description ?? r.desc ?? "—",
      org:  r.tag ?? r.category ?? "—",
      amount: Number(r.amount ?? 0),
    };
  }

  return {
    date: r.issue_date ?? r.date ?? null,
    desc: r.description ?? "—",
    org: r.tag ??  "—",
    amount: Number(r.total_amount ?? 0),
  };
}


async function fetchMonthData(activeTab, year, month) {
  let endpoint = "receipts";

  if (activeTab === "incomes") endpoint = "incomes";
  if (activeTab === "needs") endpoint = "analytics/donut";

  const url = new URL(`${API_BASE}/${endpoint}`, window.location.origin);
  url.searchParams.set("year", String(year));
  url.searchParams.set("month", String(month));

  if (activeTab === "incomes") {
    url.searchParams.set("sort", "income_date");
    url.searchParams.set("order", "desc");
  }

  if (activeTab === "expenses") {
    url.searchParams.set("sort", "issue_date");
    url.searchParams.set("order", "desc");
  }

  const res = await fetch(url.toString(), { credentials: "include" });
  const json = await res.json().catch(() => ({}));

  if (!res.ok) {
    const msg =
      json?.data?.error || json?.error || json?.message || "Request failed";
    throw new Error(msg);
  }

  return json;
}

function groupNeedsBySub(arr) {
  const result = {};
  for (const r of arr || []) {
    if (!r?.sub) continue;
    result[r.sub] = (result[r.sub] || 0) + Number(r.amount || 0);
  }
  return result;
}

export default function Comparison() {
  const { lang } = useLang();

  const [activeTab, setActiveTab] = useState("incomes");

  const MONTH_KEYS = useMemo(() => buildMonthKeys(12), []);
  const currentIndex = MONTH_KEYS.length - 1;

  const [indices, setIndices] = useState(() => ({
    left: currentIndex,
    right: currentIndex,
  }));

  const leftKey = MONTH_KEYS[indices.left];
  const rightKey = MONTH_KEYS[indices.right];

  const [cache, setCache] = useState(() => ({
    incomes: {},
    expenses: {},
    needs: {},
  }));

  const [loading, setLoading] = useState({ left: false, right: false });
  const [error, setError] = useState({ left: "", right: "" });

  const leftCanvasRef = useRef(null);
  const rightCanvasRef = useRef(null);
  const leftDetailsRef = useRef(null);
  const rightDetailsRef = useRef(null);
  const leftChartRef = useRef(null);
  const rightChartRef = useRef(null);

  const isNeeds = activeTab === "needs";
  const showCharts = isNeeds;
  const showTables = activeTab === "incomes" || activeTab === "expenses";
  const showSummary = showTables;

  const handleArrowClick = (side, dir) => {
    const step = Number(dir);
    const len = MONTH_KEYS.length;
    setIndices((prev) => ({
      ...prev,
      [side]: Math.min(Math.max(0, prev[side] + step), len - 1),
    }));
  };

  useEffect(() => {
      if (!showTables && !isNeeds) return;

    let cancelled = false;

    const run = async (side, monthKey) => {
      if (cache[activeTab][monthKey]) return;

      const { year, month } = parseMonthKey(monthKey);

      setLoading((p) => ({ ...p, [side]: true }));
      setError((p) => ({ ...p, [side]: "" }));

      try {
        const payload = await fetchMonthData(activeTab, year, month);
        if (cancelled) return;

        let value;

        if (activeTab === "needs") {
          value = normalizeNeeds(payload);
        } else {
          const kind = activeTab === "incomes" ? "incomes" : "receipts";
          const norm = normalize(kind, payload);
          const mapped = norm.rows.map((r) => mapRow(kind, r));
          value = { rows: mapped, total: norm.total };
        }

        setCache((prev) => ({
          ...prev,
          [activeTab]: { ...prev[activeTab], [monthKey]: value },
        }));
      } catch (e) {
        if (cancelled) return;
        setError((p) => ({ ...p, [side]: String(e?.message || "Error") }));
      } finally {
        if (cancelled) return;
        setLoading((p) => ({ ...p, [side]: false }));
      }
    };

    run("left", leftKey);
    run("right", rightKey);

    return () => {
      cancelled = true;
    };

  }, [activeTab, leftKey, rightKey, showTables]);


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

      const leftNeeds = cache.needs[leftKey] || { labels: [], data: [], total: 0 };
      const rightNeeds = cache.needs[rightKey] || { labels: [], data: [], total: 0 };

      const labelsL = leftNeeds.labels;
      const labelsR = rightNeeds.labels;
      const dataL = leftNeeds.data;
      const dataR = rightNeeds.data;

      if (leftChartRef.current) leftChartRef.current.destroy();
      if (rightChartRef.current) rightChartRef.current.destroy();

      const makeChart = (canvas, labels, data) => {
  const hasData = data.reduce((a, b) => a + b, 0) > 0 && labels.length > 0;

        return new Chart(canvas, {
          type: "doughnut",
          data: {
            labels: hasData
              ? labels
              : [lang === "sk" ? "Žiadne výdavky" : "No expenses"],
            datasets: [
              {
                data: hasData ? data : [100],
                backgroundColor: hasData
                  ? chartColors.slice(0, labels.length)
                  : ["#e5e7eb"],
                hoverOffset: hasData ? 10 : 0,
                borderColor: "#ffffff",
                borderWidth: 2,
              },
            ],
          },
          options: {
            cutout: "65%",
            plugins: {
              legend: { display: false },
              tooltip: {
                enabled: hasData,
                backgroundColor: "#333",
                titleColor: "#fff",
                callbacks: {
                  label: (ctx) => `${ctx.label}: ${fmt(ctx.parsed, lang)} €`,
                },
              },
            },
          },
        });
      };

      leftChartRef.current = makeChart(leftCanvasRef.current, labelsL, dataL);
      rightChartRef.current = makeChart(rightCanvasRef.current, labelsR, dataR);

      const renderDetailsHTML = (labels, data) => {
        const total = data.reduce((a, b) => a + b, 0);
        if (!labels.length || total <= 0) {
        return `<div class="summary">${
          lang === "sk" ? "Žiadne dáta pre tento mesiac" : "No data for this month"
        }</div>`;
      }
        let html = labels
          .map((label, i) => {
            const percent = total > 0 ? ((data[i] / total) * 100).toFixed(1) : 0;
            return `
              <div class="item">
                <span><span class="color-dot" style="background:${chartColors[i]}"></span>${label}</span>
                <span>${percent}% | ${fmt(data[i], lang)} €</span>
              </div>`;
          })
          .join("");
        html += `<div class="summary">${lang === "sk" ? "Celkovo" : "Total"}: ${fmt(total, lang)} €</div>`;
        return html;
      };

      if (leftDetailsRef.current) leftDetailsRef.current.innerHTML = renderDetailsHTML(labelsL, dataL);
      if (rightDetailsRef.current) rightDetailsRef.current.innerHTML = renderDetailsHTML(labelsR, dataR);
    };

    if (isNeeds) renderNeedsCharts();
    else destroyCharts();

  }, [isNeeds, leftKey, rightKey, lang]);

  const leftData = showTables ? cache[activeTab][leftKey] || { rows: [], total: 0 } : { rows: [], total: 0 };
  const rightData = showTables ? cache[activeTab][rightKey] || { rows: [], total: 0 } : { rows: [], total: 0 };

  const leftRows = leftData.rows;
  const rightRows = rightData.rows;

  const leftTotalValue = leftData.total;
  const rightTotalValue = rightData.total;

  const diffT = leftTotalValue - rightTotalValue;
  let tIcon = <span className="trend-flat">➖</span>;
  if (diffT > 1) tIcon = <span className="trend-up">🔼</span>;
  else if (diffT < -1) tIcon = <span className="trend-down">🔽</span>;

  const summaryRow = {
    totalL: fmt(leftTotalValue, lang),
    totalR: fmt(rightTotalValue, lang),
    diff: `${diffT > 0 ? "+" : ""}${fmt(diffT, lang)}`,
    icon: tIcon,
  };

  const tabs = [
    { id: "incomes", label: <T sk="Príjmy" en="Incomes" /> },
    { id: "expenses", label: <T sk="Výdavky" en="Expenses" /> },
    { id: "needs", label: <T sk="Potreby" en="Needs" /> },
  ];

  const prefix = activeTab === "incomes" ? "+ " : "- ";

  return (
    <div className="wrap comparison">
      <div className="page-title">
        📈<T sk=" Porovnanie mesiacov" en=" Monthly comparison" />
      </div>

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
          <div className="grid">
            <div className="panel" id="leftPanel">
              <div className="month-picker" id="pickerLeft">
              <button className="arrow-btn" onClick={() => handleArrowClick("left", -1)}>
                <span className="arrow left"></span>
              </button>
              <div className="month-label" id="labelLeft">{monthLabel(leftKey, lang)}</div>
              <button className="arrow-btn" onClick={() => handleArrowClick("left", 1)}>
                <span className="arrow right"></span>
              </button>
            </div>
              <div className="chart-container" style={{ display: showCharts ? "flex" : "none" }}>
                <canvas ref={leftCanvasRef}></canvas>
                <div className="chart-details" ref={leftDetailsRef}></div>
              </div>

              {showTables && (
                <div className="card">
                  <div className="table-card">
                    {loading.left && <div className="mini-loading"><T sk="Načítavam..." en="Loading..." /></div>}
                    {!!error.left && <div className="mini-error">{error.left}</div>}

                    <table id="leftTable">
                      <thead>
                        <tr>
                          <th><T sk="DÁTUM" en="DATE" /></th>
                          <th><T sk="POPIS" en="DESCRIPTION" /></th>
                          <th><T sk="ORGANIZÁCIA" en="ORGANIZATION" /></th>
                          <th className="right"><T sk="SUMA (€)" en="AMOUNT (€)" /></th>
                        </tr>
                      </thead>
                      <tbody>
                        {leftRows.map((r, i) => (
                          <tr key={i}>
                            <td>{r.date || "—"}</td>
                            <td>{r.desc}</td>
                            <td>{r.org || "—"}</td>
                            <td className="right">{prefix}{fmt(r.amount, lang)}</td>
                          </tr>
                        ))}
                        {!loading.left && !error.left && leftRows.length === 0 && (
                          <tr>
                            <td colSpan={4} style={{ opacity: 0.7 }}>
                              <T sk="Žiadne dáta pre tento mesiac" en="No data for this month" />
                            </td>
                          </tr>
                        )}
                      </tbody>
                      <tfoot>
                        <tr>
                          <td colSpan="3"><T sk="Spolu" en="Total" /></td>
                          <td className="right">{fmt(leftTotalValue, lang)}</td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                </div>
              )}
            </div>

            <div className="panel" id="rightPanel">
               <div className="month-picker" id="pickerRight">
              <button className="arrow-btn" onClick={() => handleArrowClick("right", -1)}>
                <span className="arrow left"></span>
              </button>
              <div className="month-label" id="labelRight">{monthLabel(rightKey, lang)}</div>
              <button className="arrow-btn" onClick={() => handleArrowClick("right", 1)}>
                <span className="arrow right"></span>
              </button>
            </div>
              <div className="chart-container" style={{ display: showCharts ? "flex" : "none" }}>
                <canvas ref={rightCanvasRef}></canvas>
                <div className="chart-details" ref={rightDetailsRef}></div>
              </div>

              {showTables && (
                <div className="card">
                  <div className="table-card">
                    {loading.right && <div className="mini-loading"><T sk="Načítavam..." en="Loading..." /></div>}
                    {!!error.right && <div className="mini-error">{error.right}</div>}

                    <table id="rightTable">
                      <thead>
                        <tr>
                          <th><T sk="DÁTUM" en="DATE" /></th>
                          <th><T sk="POPIS" en="DESCRIPTION" /></th>
                          <th><T sk="ORGANIZÁCIA" en="ORGANIZATION" /></th>
                          <th className="right"><T sk="SUMA (€)" en="AMOUNT (€)" /></th>
                        </tr>
                      </thead>
                      <tbody>
                        {rightRows.map((r, i) => (
                          <tr key={i}>
                            <td>{r.date || "—"}</td>
                            <td>{r.desc}</td>
                            <td>{r.org || "—"}</td>
                            <td className="right">{prefix}{fmt(r.amount, lang)}</td>
                          </tr>
                        ))}
                        {!loading.right && !error.right && rightRows.length === 0 && (
                          <tr>
                            <td colSpan={4} style={{ opacity: 0.7 }}>
                              <T sk="Žiadne dáta pre tento mesiac" en="No data for this month" />
                            </td>
                          </tr>
                        )}
                      </tbody>
                      <tfoot>
                        <tr>
                          <td colSpan="3"><T sk="Spolu" en="Total" /></td>
                          <td className="right">{fmt(rightTotalValue, lang)}</td>
                        </tr>
                      </tfoot>
                    </table>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {showSummary && (
          <div className="panel summary-card" id="summaryPanel">
            <div className="section-title">
              <T sk="Súhrn porovnania" en="Comparison summary" />
            </div>
            <div className="card table-card">
              <table id="summaryTable">
                <thead>
                  <tr>
                    <th>{`${monthLabel(leftKey, lang)} (€)`}</th>
                    <th>{`${monthLabel(rightKey, lang)} (€)`}</th>
                    <th><T sk="Rozdiel (ľavý − pravý)" en="Difference (left − right)" /></th>
                    <th><T sk="Trend" en="Trend" /></th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>{summaryRow.totalL}</td>
                    <td>{summaryRow.totalR}</td>
                    <td>{summaryRow.diff}</td>
                    <td>{summaryRow.icon}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
