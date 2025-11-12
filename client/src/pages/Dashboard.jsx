import React, { useEffect } from "react";
import "./style/dashboard.css";
import { Link } from "react-router-dom";
export default function Dashboard() {
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

  return (
    <main className="wrap dashboard">
      <div className="section-title">
        <span className="marker"></span>
        <div>
          Mesačný prehľad · <span id="monthTitle">Október 2025</span>
        </div>
      </div>

      <section className="summary" aria-label="Monthly KPIs">
        <article className="card compact">
          <div className="kpi">
            <div className="icon" aria-hidden="true">💶</div>
            <div>
              <small>Celkové príjmy</small>
              <div className="value" id="kpiIncome">€ 2 350</div>
            </div>
          </div>
        </article>

        <article className="card compact">
          <div className="kpi">
            <div className="icon" aria-hidden="true">💳</div>
            <div>
              <small>Celkové výdavky</small>
              <div className="value" id="kpiExpense">€ 1 840</div>
            </div>
          </div>
        </article>

        <article className="card compact">
          <div className="kpi">
            <div className="icon" aria-hidden="true">🧾</div>
            <div>
              <small>Zostatok</small>
              <div className="value" id="kpiBalance">€ 510</div>
            </div>
          </div>
        </article>

        <article className="card compact">
          <div className="kpi">
            <div className="icon" aria-hidden="true">🎯</div>
            <div>
              <small>Plnenie cieľov</small>
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
              <h3>Rozdelenie výdavkov tento mesiac</h3>
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
              <h2>Finančné ciele</h2>
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
              <strong>Naskenovať QR</strong>
              <p>Otvoriť kameru a naskenovať kód z účtenky</p>
              <button>Spustiť skener</button>
            </div>
            <div className="import-card" draggable="true">
              <strong>Nahrať eKasa / PDF</strong>
              <p>Podporované: .ekd, .json, .pdf</p>
              <button>Vybrať súbor</button>
            </div>
           <Link
              to="/Ekasa"
              className="btn"
              style={{ textDecoration: "none", textAlign: "center" }}>
              Prehľad eKasy
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
