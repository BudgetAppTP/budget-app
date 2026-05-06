import React, { useEffect, useState } from "react";
import "./style/dashboard.css";
import { Link } from "react-router-dom";
import { useLang } from "../i18n/LanguageContext";
import T from "../i18n/T";
import "../components/Navbar.jsx"
import Chart from "chart.js/auto";

const API_BASE = "/api";
const USER_ID = "1be32073-0b12-4a59-b9a1-77e0d3586a4c";

export default function Dashboard() {
  const { lang, setLang } = useLang();
      useEffect(() => {
    document.title = "BudgetApp · Dashboard";
  }, []);

  useEffect(() => {
    document.body.classList.add("dashboard-body");
    return () => document.body.classList.remove("dashboard-body");
    const grid = document.querySelector(".grid");
    if (!grid) return;
    let dragged = null;

    const restoreDragHandles = (grid) => {
      grid.querySelectorAll(".panel").forEach((p) => {
        const handle = p.querySelector(".drag-handle");
        if (!handle) return;
        handle.setAttribute("title", "Presuň sekciu");
      });
    };

    grid.querySelectorAll(".panel").forEach((panel) => {
      const handle = panel.querySelector(".drag-handle");
      if (!handle) return;

      handle.addEventListener("mousedown", () =>
        panel.setAttribute("draggable", "true")
      );
      handle.addEventListener("mouseup", () =>
        panel.removeAttribute("draggable")
      );

      panel.addEventListener("dragstart", (e) => {
        dragged = panel;
        panel.classList.add("dragging");
        e.dataTransfer.setData("text/plain", "panel");
        e.dataTransfer.effectAllowed = "move";
      });

      panel.addEventListener("dragend", () => {
        panel.classList.remove("dragging");
        dragged = null;
      });

      panel.addEventListener("dragover", (e) => e.preventDefault());

      panel.addEventListener("dragenter", (e) => {
        e.preventDefault();
        if (panel !== dragged) panel.classList.add("drop-target");
      });
      panel.addEventListener("dragleave", () =>
        panel.classList.remove("drop-target")
      );

      panel.addEventListener("drop", (e) => {
        e.preventDefault();
        const target = panel;
        if (!dragged || dragged === target) return;

        const temp = dragged.innerHTML;
        dragged.innerHTML = target.innerHTML;
        target.innerHTML = temp;

        restoreDragHandles(grid);

        target.classList.remove("drop-target");
        dragged.classList.remove("dragging");
        dragged = null;
      });
    });


    return () => {
      document.querySelectorAll(".panel").forEach((p) => {
        p.replaceWith(p.cloneNode(true));
      });
    };
  }, []);

  const [ekasaReceiptId, setEkasaReceiptId] = useState("");
  const [ekasaError, setEkasaError] = useState("");
  const [ekasaSuccess, setEkasaSuccess] = useState("");
  const [ekasaLoading, setEkasaLoading] = useState(false);

  const handleImportEkasa = async () => {
  const rid = (ekasaReceiptId || "").trim();

  if (!rid) {
    setEkasaError(
      lang === "sk" ? "Zadajte ID bločku." : "Please enter receipt ID."
    );
    return;
  }

  setEkasaError("");
  setEkasaLoading(true);

  try {
    const res = await fetch(`${API_BASE}/receipts/import-ekasa`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        receiptId: rid,
        user_id: USER_ID,
      }),
    });

    const json = await res.json();

    if (!res.ok || json?.error) {
      const backendMsg =
        json?.error?.message ||
        json?.error?.details?.error ||
        json?.data?.error ||
        (lang === "sk"
          ? "Import z eKasa zlyhal."
          : "Import from eKasa failed.");

      setEkasaError(backendMsg);
      return;
    }

    setEkasaReceiptId("");
    setEkasaError("");
    setEkasaSuccess(
      lang === "sk" ? "Bloček bol importovaný ✔" : "Receipt imported ✔"
    );
  } catch (err) {
    console.error(err);
    setEkasaError(
      lang === "sk"
        ? "Chyba spojenia so serverom."
        : "Server connection error."
    );
  } finally {
    setEkasaLoading(false);
  }
};

  useEffect(() => {
    if (!ekasaSuccess) return;
    const t = setTimeout(() => setEkasaSuccess(""), 2500); // 2.5s
    return () => clearTimeout(t);
  }, [ekasaSuccess]);

   const currentDate = new Date();
  const monthTitle = currentDate.toLocaleDateString(
  lang === "sk" ? "sk-SK" : "en-US",
  {
    month: "long",
    year: "numeric",
  }
);

const [analyticsData, setAnalyticsData] = useState({
  total_amount: 0,
  categories: [],
});

const [analyticsError, setAnalyticsError] = useState("");

  const fetchDonutAnalytics = async (dateForQuery = currentDate) => {
  try {
    setAnalyticsError("");

    const year = dateForQuery.getFullYear();
    const month = dateForQuery.getMonth() + 1;

    const params = new URLSearchParams({
      year: String(year),
      month: String(month),
    });

    const res = await fetch(`${API_BASE}/analytics/donut?${params.toString()}`);
    const json = await res.json();
    const data = json?.data ?? json;

    if (!res.ok) {
      setAnalyticsError(
        lang === "sk"
          ? "Nepodarilo sa načítať analytiku."
          : "Failed to load analytics."
      );

      setAnalyticsData({
        total_amount: 0,
        categories: [],
      });

      return;
    }

    setAnalyticsData({
      total_amount: parseFloat(data?.total_amount || 0) || 0,
      categories: Array.isArray(data?.categories) ? data.categories : [],
    });
  } catch (err) {
    console.error(err);

    setAnalyticsError(
      lang === "sk"
        ? "Chyba spojenia so serverom pri načítaní analytiky."
        : "Connection error while loading analytics."
    );

    setAnalyticsData({
      total_amount: 0,
      categories: [],
    });
  }
};

  useEffect(() => {
  fetchDonutAnalytics(currentDate);
}, [lang]);


  useEffect(() => {
  const ctx = document.getElementById("dashboardDonutChart");
  if (!ctx) return;

  const colors = [
    "#e6c975",
    "#ccb8a3",
    "#b1bfd0",
    "#c0cfad",
    "#d9b3c9",
    "#a8d5ba",
    "#f2b880",
    "#b9c0ff",
  ];

  const monthInfo = {
    sum: analyticsData?.total_amount || 0,
    labels: (analyticsData?.categories || []).map((c) => c.category),
    data: (analyticsData?.categories || []).map((c) =>
      typeof c.percentage === "number"
        ? c.percentage
        : parseFloat(c.percentage || 0) || 0
    ),
    amounts: (analyticsData?.categories || []).map((c) =>
      typeof c.amount === "number"
        ? c.amount
        : parseFloat(c.amount || 0) || 0
    ),
  };

  const hasDonutData = monthInfo.sum > 0 && monthInfo.labels.length > 0;

  const data = {
    labels: hasDonutData
      ? monthInfo.labels
      : [lang === "sk" ? "Žiadne výdavky" : "No expenses"],
    datasets: [
      {
        data: hasDonutData ? monthInfo.data : [100],
        backgroundColor: hasDonutData
          ? monthInfo.labels.map((_, i) => colors[i % colors.length])
          : ["#e5e7eb"],
        hoverOffset: hasDonutData ? 15 : 0,
        borderColor: "#ffffff",
        borderWidth: 2,
      },
    ],
  };

  const chart = new Chart(ctx, {
    type: "doughnut",
    data: data,
    options: {
      responsive: true,
      cutout: "68%",
      plugins: {
        legend: {
          display: false,
        },
        tooltip: {
          enabled: true,
          backgroundColor: "#333",
          titleColor: "#fff",
          bodyColor: "#fff",
          callbacks: {
            label: (ctx) => {
              const percent = Number(ctx.parsed || 0);
              const amount = monthInfo.amounts[ctx.dataIndex] || 0;

              return `${ctx.label}: ${percent.toFixed(1)}% | ${amount.toFixed(2)} €`;
            },
          },
        },
      },
    },
  });

  return () => {
    if (chart) chart.destroy();
  };
}, [analyticsData, lang]);

  return (
    <main className="wrap dashboard">
      <div className="section-title">
        <span className="marker"></span>
        <div>
           <h2 className="month-title">
  <T sk="Mesačný prehľad" en="Monthly Overview" /> · {monthTitle}
</h2>
        </div>
      </div>

      <section className="summary" aria-label="Monthly KPIs">
        <article className="card compact">
          <div className="kpi">
            <div className="icon" aria-hidden="true">💶</div>
            <div>
              <small> <T sk="Príjmy" en="Incomes" /></small>
              <div className="value" id="kpiIncome">€ 2 350</div>
            </div>
          </div>
        </article>

        <article className="card compact">
          <div className="kpi">
            <div className="icon" aria-hidden="true">💳</div>
            <div>
              <small><T sk="Výdavky" en="Expenses" /></small>
              <div className="value" id="kpiExpense">€ 1 840</div>
            </div>
          </div>
        </article>

        <article className="card compact">
          <div className="kpi">
            <div className="icon" aria-hidden="true">🧾</div>
            <div>
              <small> <T sk="Zostatok" en="Balance" /></small>
              <div className="value" id="kpiBalance">€ 510</div>
            </div>
          </div>
        </article>

        <article className="card compact">
          <div className="kpi">
            <div className="icon" aria-hidden="true">🎯</div>
            <div>
              <small><T sk="Ciele" en="Goals" /></small>
              <div className="value" id="kpiGoals">73%</div>
            </div>
          </div>
        </article>
      </section>

      <section className="grid" aria-label="Detail & rýchly prístup">
        <div>
          <div className="panel">
            <div className="drag-handle" title="Presuň sekciu"></div>
            <header>
              <h2> <T sk="Rozloženie výdavkov" en="Expense Distribution" /></h2>
            </header>

            <div className="donut-wrap">
        <div className="chart-canvas-wrapper">
          <canvas id="dashboardDonutChart"></canvas>
          <div className="donut-center">
            € {(analyticsData.total_amount || 0).toFixed(2)}
          </div>
        </div>

        <div className="legend">
          {analyticsData.categories.length > 0 ? (
            analyticsData.categories.map((cat, i) => (
              <div className="row" key={cat.category}>
                <div
                  className="dot"
                  style={{
                    background: [
                      "#e6c975",
                      "#ccb8a3",
                      "#b1bfd0",
                      "#c0cfad",
                      "#d9b3c9",
                      "#a8d5ba",
                      "#f2b880",
                      "#b9c0ff",
                    ][i % 8],
                  }}
                ></div>

                <div className="label">{cat.category}</div>

                <strong>
                  {(parseFloat(cat.percentage || 0) || 0).toFixed(1)}%
                </strong>
              </div>
            ))
          ) : (
            <div className="row">
              <div className="label">
                <T
                  sk="Za tento mesiac nie sú dostupné žiadne údaje"
                  en="No data available for this month"
                />
              </div>
            </div>
          )}
        </div>

        {analyticsError && (
          <div className="error-text">
            {analyticsError}
          </div>
        )}
      </div>




          </div>

          <div id="goals" className="panel" draggable="true" style={{ marginTop: "16px" }}>
            <div className="drag-handle" title="Presuň sekciu"></div>
            <header>
              <h2><T sk="Finančné ciele" en="Financial Goals" /></h2>
            </header>

            <div className="goals-container" id="goalList">
              <div className="goal-box" draggable="true">
                <div className="goal-title">Šporiť 300 € mesačne</div>
                <div className="goal-info">Ušetrené: <b>220 €</b> / 300 €</div>
                <div className="progress"><span style={{ width: "73%" }}></span></div>
              </div>

              <div className="goal-box" draggable="true">
                <div className="goal-title">Jedlo: limit 250 €</div>
                <div className="goal-info">Vynaložené: <b>190 €</b> / 250 €</div>
                <div className="progress"><span style={{ width: "76%" }}></span></div>
              </div>

              <div className="goal-box" draggable="true">
                <div className="goal-title">Investície 100 €</div>
                <div className="goal-info">Investované: <b>60 €</b> / 100 €</div>
                <div className="progress"><span style={{ width: "60%" }}></span></div>
              </div>
            </div>
          </div>
        </div>

        <div className="panel" draggable="true" id="importSection">
          <div className="drag-handle" title="Presuň sekciu"></div>
          <header>
            <h2>Import eKasa</h2>
          </header>
          <div className="import-boxes">
            <div className="import-card" draggable="true">
              <strong> <T sk="QR kód eKasa" en="QR Code eKasa" /></strong>
              <p>

                <T sk="Naskenujte QR kód z bločku"
	                  en="Scan the QR code from your receipt"/>

              </p>
              <button><T sk="Nahrať QR" en="Upload QR" /></button>
            </div>
            <div className="import-card" draggable="true">
              <strong><T sk="PDF alebo JSON" en="PDF or JSON" /></strong>
              <p><T sk="Importujte súbor z eKasa"
	                  en="Import an eKasa file"
                /></p>
              <button> <T sk="Vybrať súbor" en="Choose File" /></button>
            </div>

            <div className="import-card import-ekasa">
  <strong>
    <T sk="Import z eKasa" en="Import from eKasa" />
  </strong>

  <p>
    <T
      sk="Zadajte ID bločku (receiptId) z eKasa a importujte výdavok."
      en="Enter eKasa receipt ID (receiptId) to import an expense."
    />
  </p>

  <input
    type="text"
    value={ekasaReceiptId}
    onChange={(e) => {
      setEkasaReceiptId(e.target.value);
      setEkasaError("");
      setEkasaSuccess("");
    }}
    placeholder={lang === "sk" ? "ID bločku (receiptId)" : "Receipt ID (receiptId)"}
    style={{
      border: ekasaError ? "1px solid #e53935" : "1px solid #d0d0d0",
    }}
  />


  <button
    type="button"
    onClick={handleImportEkasa}
    disabled={ekasaLoading}
    style={{
      cursor: ekasaLoading ? "not-allowed" : "pointer",
      opacity: ekasaLoading ? 0.7 : 1,
    }}
  >
    {ekasaLoading
      ? lang === "sk"
        ? "Importujem..."
        : "Importing..."
      : lang === "sk"
      ? "Importovať"
      : "Import"}
  </button>

  {ekasaError && (
    <div style={{ marginTop: "8px", color: "#e53935", fontSize: "13px" }}>
      {ekasaError}
    </div>
  )}

  {ekasaSuccess && (
  <div style={{ marginTop: "8px", color: "#2e7d32", fontSize: "13px" }}>
    {ekasaSuccess}
  </div>
)}
</div>


           <Link
              to="/Ekasa"
              className="btn"
              style={{ textDecoration: "none", textAlign: "center" }}>
              <T sk="Otvoriť eKasa" en="Open eKasa" />
           </Link>
          </div>
        </div>
      </section>

      <footer>
        <div className="foot-inner">
          <span>© BudgetApp</span>
        </div>
      </footer>
    </main>
  );
}
