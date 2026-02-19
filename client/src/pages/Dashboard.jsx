import React, { useEffect, useState } from "react";
import "./style/dashboard.css";
import { Link } from "react-router-dom";
import { useLang } from "../i18n/LanguageContext";
import T from "../i18n/T";

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



  return (
    <main className="wrap dashboard">
      <div className="section-title">
        <span className="marker"></span>
        <div>
           <T sk="Mesačný prehľad" en="Monthly Overview" /> ·{" "}
          <span id="monthTitle">Október 2025</span>
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
          <div className="panel" draggable="true">
            <div className="drag-handle" title="Presuň sekciu"></div>
            <header>
              <h3> <T sk="Rozloženie výdavkov" en="Expense Distribution" /></h3>
            </header>

            <div className="donut-wrap">
              <div
                className="donut"
                role="img"
                aria-label="Donut chart: Bývanie 45%, Jedlo 25%, Lieky 20%, Oblečenie 10%"
              >
                <div className="donut-center">€ 1 840</div>
              </div>
              <div className="legend">
                <div className="row">
                  <div className="dot" style={{ background: "var(--gold)" }}></div>
                  <div className="label">Bývanie</div>
                  <strong>45%</strong>
                </div>
                <div className="row">
                  <div className="dot" style={{ background: "#9ca3af" }}></div>
                  <div className="label">Jedlo</div>
                  <strong>25%</strong>
                </div>
                <div className="row">
                  <div className="dot" style={{ background: "#60a5fa" }}></div>
                  <div className="label">Lieky</div>
                  <strong>20%</strong>
                </div>
                <div className="row">
                  <div className="dot" style={{ background: "#34d399" }}></div>
                  <div className="label">Oblečenie</div>
                  <strong>10%</strong>
                </div>
              </div>
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
