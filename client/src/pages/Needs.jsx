import React, { useState, useEffect } from "react";
import Chart from "chart.js/auto";
import "./style/needs.css";
import T from "../i18n/T";
import { useLang } from "../i18n/LanguageContext";

export default function Needs() {
     const {lang} = useLang();

        useEffect(() => {
    document.title = "BudgetApp · Potreby";
  }, []);
        const [categories, setCategories] = useState([
    { id: 1, name: "Jedlo", pinned: false },
    { id: 2, name: "Bývanie", pinned: false },
    { id: 3, name: "Doprava", pinned: false },
  ]);

const [newCategory, setNewCategory] = useState("");
const [error, setError] = useState("");
const [editingId, setEditingId] = useState(null);
const [editBuffer, setEditBuffer] = useState({});

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!newCategory.trim()) {
            setError(lang === "sk"
  ? "Zadajte názov organizácie!"
  : "Enter the organization name!"
);

      return;
    }
    setError("");
    const id = categories.length
      ? categories[categories.length - 1].id + 1
      : 1;

    setCategories([...categories, { id, name: newCategory, pinned: false }]);
    setNewCategory("");
  };

  const handleDelete = (id) => {
    setCategories(categories.filter((c) => c.id !== id));
  };

const handleEditToggle = (id) => {
  if (editingId === id) {
    const name = (editBuffer.name || "").trim();
    if (!name) {
          setError(lang === "sk"
  ? "Názov kategórie nesmie byť prázdny!"
  : "Category name cannot be empty!"
);
      return;
    }

    setCategories(
      categories.map((c) => (c.id === id ? { ...c, name } : c))
    );

    setEditingId(null);
    setEditBuffer({});
    setError("");
  } else {
    const cat = categories.find((c) => c.id === id);
    if (!cat) return;

    setEditBuffer({ ...cat });
    setEditingId(id);
    setError("");
  }
};

const handlePin = (id) => {
  setCategories((prev) => {
    const updated = prev.map((c) =>
      c.id === id ? { ...c, pinned: !c.pinned } : c
    );

    const current = updated.find((c) => c.id === id);

    if (current.pinned) {
      const without = updated.filter((c) => c.id !== id);
      return [current, ...without];
    }

    else {
      const without = updated.filter((c) => c.id !== id);
      return [...without, current];
    }
  });
};

useEffect(() => {
  const table = document.getElementById("category-table");
  const form = document.getElementById("add-form");
  const input = document.getElementById("new-category");

  if (form && input && table) {
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const name = input.value.trim();
      if (!name) return;

      const row = document.createElement("tr");
      row.innerHTML = `
        <td>${name}</td>
        <td>
           <div className="actions">
            {!isEditing && (
                <>

                  <span
                    className="action-icon delete"
                    onClick={() => handleDelete(exp.id)}
                    title="Vymazať"
                  >
                    🗑️
                  </span>
                </>
              )}

              <span
                className="action-icon edit"
                onClick={() => handleEditToggle(exp.id)}
                title={isEditing ? "Uložiť zmeny" : "Upraviť"}
              >
                {isEditing ? "✔" : "✏️"}
              </span>
           </div>
        </td>
      `;
      table.appendChild(row);
      input.value = "";
    });
  }

  const ctx = document.getElementById("donutChart");
  if (!ctx) return;

  const monthlyData = {
    "September 2025": {
      sum: 820.5,
      labels: ["Jedlo", "Bývanie", "Doprava", "Voľný čas"],
      data: [35, 30, 15, 20],
    },
    "Október 2025": {
      sum: 924.2,
      labels: ["Jedlo", "Bývanie", "Doprava", "Voľný čas"],
      data: [45, 25, 10, 20],
    },
    "November 2025": {
      sum: 1032.6,
      labels: ["Jedlo", "Bývanie", "Doprava", "Voľný čas"],
      data: [40, 28, 18, 14],
    },
  };

  const colors = ["#e6c975", "#ccb8a3", "#b1bfd0", "#c0cfad"];
  let monthKeys = Object.keys(monthlyData);
  let currentMonthIndex = 1;

  const monthLabel = document.getElementById("monthLabel");
  const monthSum = document.getElementById("monthSum");
  const detBox = document.getElementById("details");
  const txBox = document.getElementById("transactions");

  function showCategoryShares(month) {
    const monthInfo = monthlyData[month];
    if (!monthInfo || !txBox) return;

    const total = monthInfo.sum;
    const categories = monthInfo.labels;
    const values = monthInfo.data;

    let html = categories
      .map((cat, i) => {
        const percent = values[i];
        const amount = total * (percent / 100);
        return `
          <div class="transaction-item">
            <span><span class="color-dot" style="background:${colors[i]}"></span>${cat}</span>
            <span>${percent.toFixed(1)}% | ${amount.toFixed(2)} €</span>
          </div>`;
      })
      .join("");

    html += `<div class="summary-line">${lang === "sk" ? "Celkovo" : "Total"}: ${total.toFixed(2)} €</div>`;
    txBox.innerHTML = html;
  }

  const data = {
    labels: monthlyData[monthKeys[currentMonthIndex]].labels,
    datasets: [
      {
        data: monthlyData[monthKeys[currentMonthIndex]].data,
        backgroundColor: colors,
        hoverOffset: 15,
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
          position: "right",
          labels: {
            color: "#333",
            usePointStyle: true,
            boxWidth: 10,
            padding: 15,
          },
        },
        tooltip: {
          backgroundColor: "#333",
          titleColor: "#fff",
          callbacks: {
            label: (ctx) => `${ctx.label}: ${ctx.parsed}%`,
          },
        },
      },
      onClick: (evt, elements) => {
        if (elements.length > 0) {
          const i = elements[0].index;
          const category = data.labels[i];
          showDetails(category);
        }
      },
    },
  });

  const categoryData = {
    Jedlo: {
      total: "415.90",
      transactions: [
        { name: "BILLA Bratislava", date: "22.10.2025", amount: -3.99 },
        { name: "DELIKOMAT SK 12448", date: "22.10.2025", amount: -1.7 },
        { name: "LIDL nákup", date: "15.10.2025", amount: -24.3 },
      ],
    },
    Bývanie: {
      total: "230.50",
      transactions: [
        { name: "Nájom", date: "01.10.2025", amount: -200.0 },
        { name: "Elektrina", date: "10.10.2025", amount: -30.5 },
      ],
    },
    Doprava: {
      total: "92.80",
      transactions: [
        { name: "MHD karta", date: "05.10.2025", amount: -25.0 },
        { name: "Taxi služba", date: "11.10.2025", amount: -15.0 },
        { name: "Benzín", date: "20.10.2025", amount: -52.8 },
      ],
    },
    "Voľný čas": {
      total: "185.00",
      transactions: [
        { name: "Fitko", date: "03.10.2025", amount: -40.0 },
        { name: "Kino", date: "08.10.2025", amount: -25.0 },
        { name: "Výlet", date: "17.10.2025", amount: -120.0 },
      ],
    },
  };

  function showDetails(category) {
    const data = categoryData[category];
    if (!data || !detBox || !txBox) return;

    detBox.querySelector("h3").textContent = category;
    detBox.querySelector(".details-total").textContent = `${data.total} €`;

    txBox.innerHTML = data.transactions
      .map(
        (tx) => `
      <div class="transaction-item">
        <div class="left">
          <span>${tx.name}</span>
          <small>${tx.date}</small>
        </div>
        <div class="right">${tx.amount.toFixed(2)} €</div>
      </div>`
      )
      .join("");
  }

  showCategoryShares("Október 2025");

  const prevBtn = document.getElementById("prevMonth");
  const nextBtn = document.getElementById("nextMonth");

  if (prevBtn && nextBtn) {
    prevBtn.addEventListener("click", () => {
      currentMonthIndex =
        (currentMonthIndex - 1 + monthKeys.length) % monthKeys.length;
      updateChart(monthKeys[currentMonthIndex]);
    });

    nextBtn.addEventListener("click", () => {
      currentMonthIndex = (currentMonthIndex + 1) % monthKeys.length;
      updateChart(monthKeys[currentMonthIndex]);
    });
  }

  function updateChart(month) {
    const monthInfo = monthlyData[month];
    if (!monthInfo || !chart) return;

    chart.data.labels = monthInfo.labels;
    chart.data.datasets[0].data = monthInfo.data;
    chart.update();

    if (monthLabel) monthLabel.textContent = month;
    if (monthSum) monthSum.textContent = `${monthInfo.sum.toFixed(2)} €`;

    if (detBox)
      detBox.querySelector("h3").textContent = `Podiel potreb za ${month}`;
    if (detBox)
      detBox.querySelector(".details-total").textContent = "";

    showCategoryShares(month);
  } return () => {
    if (chart) chart.destroy();
  };

}, [lang]);


  return (
    <div className="wrap needs">
      <div>
        <div className="page-title"><T sk="📦 Potreby" en="📦 Needs" /></div>

        <div className="table-wrap">
 <table>
            <thead>
              <tr>
                <th><T sk="KATEGÓRIA" en="CATEGORY" /></th>
                <th style={{ textAlign: "center" }}><T sk="AKCIE" en="ACTIONS" /></th>
              </tr>
            </thead>
            <tbody>
              {categories.map((cat) => {
                const isEditing = editingId === cat.id;
                const data = isEditing ? editBuffer : cat;

                return (
                  <tr
                    key={cat.id}
                    className={`${cat.pinned ? "pinned" : ""} ${isEditing ? "editing" : ""}`}
                    style={
                      isEditing
                        ? {
                            backgroundColor: "#fff8e1",
                            transition: "background-color 0.3s ease",
                          }
                        : {}
                    }
                  >
                    <td>
                      {isEditing ? (
                        <input
                          type="text"
                          value={data.name}
                          onChange={(e) =>
                            setEditBuffer({
                              ...editBuffer,
                              name: e.target.value,
                            })
                          }
                        />
                      ) : (
                        cat.name
                      )}
                    </td>
                    <td>
                      <div className="actions">
                                 {!isEditing && (
                            <>
                              <span
                                className={`action-icon ${cat.pinned ? "pinned" : "unpinned"}`}
                                onClick={() => handlePin(cat.id)}
                                title={
                            cat.pinned
                              ? lang === "sk"
                                ? "Odkotviť kategóriu"
                                : "Unpin category"
                              : lang === "sk"
                              ? "Pripnúť kategóriu"
                              : "Pin category"
                          }
                              >
                                📌
                              </span>
                            </>
                          )}






                          <span
                            className="action-icon edit"
                            onClick={() => handleEditToggle(cat.id)}
                            title={
                          isEditing
                            ? lang === "sk"
                              ? "Uložiť zmeny"
                              : "Save changes"
                            : lang === "sk"
                            ? "Upraviť"
                            : "Edit"
                        }
                          >
                            {isEditing ? "✔" : "✏️"}
                          </span>

                                                {!isEditing && (
                            <>

                              <span
                                className="action-icon delete"
                                onClick={() => handleDelete(cat.id)}
                                title={lang === "sk" ? "Vymazať" : "Delete"}
                              >
                                🗑️
                              </span>
                            </>
                          )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        <form onSubmit={handleSubmit} className="needs-form">
          <table className="needs-table">
             <tbody>
              <tr>
          <td style={{ width: "70%" }}>
          <input
            type="text"
            value={newCategory}
            onChange={(e) => setNewCategory(e.target.value)}
            placeholder={lang === "sk" ? "Nová kategória" : "New category"}
          />
          </td>
            <td style={{ width: "30%" }}>
          <button
            className="btn"
            type="submit"
          >
            {lang === "sk" ? "+ Pridať potreby" : "+ Add need"}
          </button>
                   </td>
                   </tr>
             </tbody>
          </table>
        </form>
        {error && <div className="error-text">{error}</div>}
      </div>





      <div className="statistic">
        <div className="page-title"> <T sk="📊 Mesačná štatistika výdavkov" en="📊 Monthly expense statistics" /></div>

        <div className="chart-section">
          <div className="chart-container">
            <div className="month-nav">
              <span className="arrow" id="prevMonth">◀</span>
              <span id="monthLabel">Október 2025</span> :
              <span className="gold" id="monthSum">924.20 €</span>
              <span className="arrow" id="nextMonth">▶</span>
            </div>

            <div className="chart-canvas-wrapper">
              <canvas id="donutChart"></canvas>
            </div>
          </div>

          <div className="details-container" id="details">
            <h3><T sk="Podiel potreb" en="Share of needs" /></h3>
            <div className="details-total"></div>
            <div className="transactions" id="transactions"></div>
          </div>
        </div>
      </div>
    </div>
  );
}
