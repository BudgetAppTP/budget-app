import React, { useState, useEffect } from "react";
import Chart from "chart.js/auto";
import "./style/needs.css";
import T from "../i18n/T";
import { useLang } from "../i18n/LanguageContext";

const API_BASE = "/api";
const USER_ID = "1be32073-0b12-4a59-b9a1-77e0d3586a4c";

export default function Needs() {
  const { lang } = useLang();

  useEffect(() => {
    document.title = "BudgetApp · Potreby";
  }, []);

  const [categories, setCategories] = useState([]);
  const [newCategory, setNewCategory] = useState("");
  const [error, setError] = useState("");
  const [editingId, setEditingId] = useState(null);
  const [editBuffer, setEditBuffer] = useState({});

  const [currentDate, setCurrentDate] = useState(() => new Date());
  const [analyticsData, setAnalyticsData] = useState({
    year: null,
    month: null,
    total_amount: 0,
    categories: [],
    tags_by_category: {},
  });

  const fetchCategories = async () => {
    try {
      const res = await fetch(`${API_BASE}/categories`);
      const json = await res.json();

      const data = json?.categories ? json : json?.data ?? json;
      const list = Array.isArray(data?.categories) ? data.categories : [];

      const mapped = list.map((cat) => ({
        id: cat.id,
        name: cat.name || "",
        pinned: !!cat.is_pinned,
        count:
          typeof cat.count === "number"
            ? cat.count
            : parseInt(cat.count || 0, 10) || 0,
        user_id: cat.user_id || USER_ID,
        parent_id: cat.parent_id || null,
        created_at: cat.created_at || null,
      }));

      setCategories(mapped);
      setError("");
    } catch (err) {
      console.error(err);
      setError(
        lang === "sk"
          ? "Chyba pri načítaní kategórií"
          : "Failed to load categories"
      );
    }
  };

  const fetchCategoryById = async (id) => {
    const res = await fetch(`${API_BASE}/categories`);
    const json = await res.json();

    const data = json?.categories ? json : json?.data ?? json;
    const list = Array.isArray(data?.categories) ? data.categories : [];
    const cat = list.find((item) => item.id === id);

    if (!cat) {
      throw new Error(
        lang === "sk"
          ? "Nepodarilo sa načítať kategóriu"
          : "Failed to load category"
      );
    }

    return {
      id: cat.id,
      name: cat.name || "",
      pinned: !!cat.is_pinned,
      count:
        typeof cat.count === "number"
          ? cat.count
          : parseInt(cat.count || 0, 10) || 0,
      user_id: cat.user_id || USER_ID,
      parent_id: cat.parent_id || null,
      created_at: cat.created_at || null,
    };
  };

  const createCategory = async (name) => {
    const payload = {
      user_id: USER_ID,
      parent_id: null,
      name: name.trim(),
      count: 0,
      is_pinned: false,
    };

    const res = await fetch(`${API_BASE}/categories`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const json = await res.json();

    if (!res.ok) {
      const msg =
        json?.data?.error ||
        json?.error ||
        (lang === "sk"
          ? "Nepodarilo sa vytvoriť kategóriu"
          : "Failed to create category");
      throw new Error(msg);
    }

    return json?.id || json?.data?.id;
  };

  const updateCategory = async (id, payload) => {
    const res = await fetch(`${API_BASE}/categories/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const json = await res.json();

    if (!res.ok) {
      const msg =
        json?.data?.error ||
        json?.error ||
        (lang === "sk"
          ? "Nepodarilo sa upraviť kategóriu"
          : "Failed to update category");
      throw new Error(msg);
    }

    return json;
  };

  const deleteCategory = async (id) => {
    const res = await fetch(`${API_BASE}/categories/${id}`, {
      method: "DELETE",
    });

    const json = await res.json();

    if (!res.ok) {
      const msg =
        json?.data?.error ||
        json?.error ||
        (lang === "sk"
          ? "Nepodarilo sa vymazať kategóriu"
          : "Failed to delete category");
      throw new Error(msg);
    }

    return json;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!newCategory.trim()) {
      setError(
        lang === "sk" ? "Zadajte názov potreby!" : "Enter the need name!"
      );
      return;
    }

    try {
      setError("");

      const createdId = await createCategory(newCategory);
      let newRow;

      if (createdId) {
        try {
          newRow = await fetchCategoryById(createdId);
        } catch (err) {
          console.error("Failed to refetch created category:", err);
          newRow = {
            id: createdId,
            name: newCategory.trim(),
            pinned: false,
            count: 0,
            user_id: USER_ID,
            parent_id: null,
            created_at: null,
          };
        }
      } else {
        newRow = {
          id:
            (typeof crypto !== "undefined" && crypto.randomUUID?.()) ||
            Date.now().toString(),
          name: newCategory.trim(),
          pinned: false,
          count: 0,
          user_id: USER_ID,
          parent_id: null,
          created_at: null,
        };
      }

      setCategories((prev) => [...prev, newRow]);
      setNewCategory("");
    } catch (err) {
      console.error(err);
      setError(err.message);
    }
  };

  const handleDelete = async (id) => {
    try {
      await deleteCategory(id);
      setCategories((prev) => prev.filter((c) => c.id !== id));
    } catch (err) {
      console.error(err);
      setError(err.message);
    }
  };

  const handleEditToggle = async (id) => {
    const isEditing = editingId === id;

    if (isEditing) {
      const name = (editBuffer.name || "").trim();

      if (!name) {
        setError(
          lang === "sk"
            ? "Názov potreby nesmie byť prázdny!"
            : "Needs name cannot be empty!"
        );
        return;
      }

      try {
        await updateCategory(id, { name });

        let updatedRow;
        try {
          updatedRow = await fetchCategoryById(id);
        } catch (err) {
          console.error("Failed to refetch updated category:", err);
          updatedRow = {
            ...editBuffer,
            id,
            name,
          };
        }

        setCategories((prev) =>
          prev.map((c) => (c.id === id ? updatedRow : c))
        );

        setEditingId(null);
        setEditBuffer({});
        setError("");
      } catch (err) {
        console.error(err);
        setError(err.message);
      }
    } else {
      const cat = categories.find((c) => c.id === id);
      if (!cat) return;

      setEditBuffer({ ...cat });
      setEditingId(id);
      setError("");
    }
  };

  const handlePin = async (id) => {
    const current = categories.find((c) => c.id === id);
    if (!current) return;

    const newPinned = !current.pinned;

    try {
      await updateCategory(id, { is_pinned: newPinned });

      setCategories((prev) => {
        const updated = prev.map((c) =>
          c.id === id ? { ...c, pinned: newPinned } : c
        );

        const pinned = updated.filter((c) => c.pinned);
        const unpinned = updated.filter((c) => !c.pinned);

        return [...pinned, ...unpinned];
      });

      setError("");
    } catch (err) {
      console.error(err);
      setError(err.message);
    }
  };

  const changeMonth = (offset) => {
    const newDate = new Date(currentDate);
    newDate.setMonth(currentDate.getMonth() + offset);
    setCurrentDate(newDate);
  };

  const getMonthLabel = (date) =>
    date.toLocaleDateString(lang === "sk" ? "sk-SK" : "en-US", {
      month: "long",
      year: "numeric",
    });

  const formatDate = (isoDate) => {
    if (!isoDate) return "";
    const [year, month, day] = isoDate.split("-");
    return `${day}.${month}.${year}`;
  };

  const fetchDonutAnalytics = async (dateForQuery = currentDate) => {
    try {
      setError("");

      const year = dateForQuery.getFullYear();
      const month = dateForQuery.getMonth() + 1;

      const params = new URLSearchParams({
        year: String(year),
        month: String(month),
      });

      const res = await fetch(
        `${API_BASE}/analytics/donut?${params.toString()}`
      );
      const json = await res.json();
      const data = json?.data ?? json;

      if (!res.ok) {
        const backendMsg =
          data?.error ||
          (lang === "sk"
            ? "Nepodarilo sa načítať analytiku."
            : "Failed to load analytics.");
        setError(backendMsg);
        setAnalyticsData({
          year,
          month,
          total_amount: 0,
          categories: [],
          tags_by_category: {},
        });
        return;
      }

      setAnalyticsData({
        year: data?.year ?? year,
        month: data?.month ?? month,
        total_amount:
          typeof data?.total_amount === "number"
            ? data.total_amount
            : parseFloat(data?.total_amount || 0) || 0,
        categories: Array.isArray(data?.categories) ? data.categories : [],
        tags_by_category: data?.tags_by_category || {},
      });
    } catch (err) {
      console.error(err);
      setError(
        lang === "sk"
          ? "Chyba spojenia so serverom pri načítaní analytiky."
          : "Connection error while loading analytics."
      );
      setAnalyticsData({
        year: null,
        month: null,
        total_amount: 0,
        categories: [],
        tags_by_category: {},
      });
    }
  };

  useEffect(() => {
    fetchCategories();
  }, [lang]);

  useEffect(() => {
    fetchDonutAnalytics(currentDate);
  }, [currentDate, lang]);

  useEffect(() => {
    const ctx = document.getElementById("donutChart");
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

    const monthLabel = document.getElementById("monthLabel");
    const monthSum = document.getElementById("monthSum");
    const detBox = document.getElementById("details");
    const txBox = document.getElementById("transactions");

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

    function showCategoryShares() {
      if (!txBox) return;

      if (!monthInfo.labels.length) {
        txBox.innerHTML = `
          <div class="summary-line">
            ${
              lang === "sk"
                ? "Za zvolený mesiac nie sú dostupné žiadne údaje"
                : "No data available for the selected month"
            }
          </div>
        `;
        return;
      }

      let html = monthInfo.labels
        .map((cat, i) => {
          const percent = monthInfo.data[i] || 0;
          const amount = monthInfo.amounts[i] || 0;
          return `
            <div class="transaction-item">
              <span><span class="color-dot" style="background:${
                colors[i % colors.length]
              }"></span>${cat}</span>
              <span>${percent.toFixed(1)}% | ${amount.toFixed(2)} €</span>
            </div>`;
        })
        .join("");

      html += `<div class="summary-line">${
        lang === "sk" ? "Celkovo" : "Total"
      }: ${monthInfo.sum.toFixed(2)} €</div>`;
      txBox.innerHTML = html;
    }

    function showDetails(category) {
      const details = analyticsData?.tags_by_category?.[category];
      if (!detBox || !txBox) return;

      if (!details) {
        detBox.querySelector("h3").textContent = category;
        detBox.querySelector(".details-total").textContent = `0.00 €`;
        txBox.innerHTML = `
          <div class="summary-line">
            ${
              lang === "sk"
                ? "Pre túto kategóriu nie sú dostupné detaily."
                : "No details available for this category."
            }
          </div>
        `;
        return;
      }

      const transactions = [];
      let total = 0;

      Object.entries(details).forEach(([tagName, datesObj]) => {
        Object.entries(datesObj || {}).forEach(([issueDate, amount]) => {
          const parsedAmount =
            typeof amount === "number" ? amount : parseFloat(amount || 0) || 0;
          total += parsedAmount;

          transactions.push({
            name: tagName,
            date: formatDate(issueDate),
            amount: -parsedAmount,
          });
        });
      });

      transactions.sort((a, b) => {
        const [da, ma, ya] = a.date.split(".");
        const [db, mb, yb] = b.date.split(".");
        return new Date(`${yb}-${mb}-${db}`) - new Date(`${ya}-${ma}-${da}`);
      });

      detBox.querySelector("h3").textContent = category;
      detBox.querySelector(".details-total").textContent = `${total.toFixed(
        2
      )} €`;

      txBox.innerHTML = transactions.length
        ? transactions
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
            .join("")
        : `<div class="summary-line">${
            lang === "sk"
              ? "Pre túto kategóriu nie sú dostupné detaily."
              : "No details available for this category."
          }</div>`;
    }

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
          if (!hasDonutData) return;

          if (elements.length > 0) {
            const i = elements[0].index;
            const category = data.labels[i];
            showDetails(category);
          }
        },
      },
    });

    if (monthLabel) monthLabel.textContent = getMonthLabel(currentDate);
    if (monthSum) monthSum.textContent = `${monthInfo.sum.toFixed(2)} €`;

    if (detBox) {
      detBox.querySelector("h3").textContent =
        lang === "sk" ? "Podiel potrieb" : "Share of needs";
      detBox.querySelector(".details-total").textContent = "";
    }

    showCategoryShares();

    return () => {
      if (chart) chart.destroy();
    };
  }, [analyticsData, currentDate, lang]);

  return (
    <div className="wrap needs">
      <div>
        <div className="page-title">
          <T sk="📦 Potreby" en="📦 Needs" />
        </div>

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>
                  <T sk="KATEGÓRIA" en="CATEGORY" />
                </th>
                <th style={{ textAlign: "center" }}>
                  <T sk="AKCIE" en="ACTIONS" />
                </th>
              </tr>
            </thead>
            <tbody>
              {categories.map((cat) => {
                const isEditing = editingId === cat.id;
                const data = isEditing ? editBuffer : cat;

                return (
                  <tr
                    key={cat.id}
                    className={`${cat.pinned ? "pinned" : ""} ${
                      isEditing ? "editing" : ""
                    }`}
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
                          <span
                            className={`action-icon ${
                              cat.pinned ? "pinned" : "unpinned"
                            }`}
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
                          <span
                            className="action-icon delete"
                            onClick={() => handleDelete(cat.id)}
                            title={lang === "sk" ? "Vymazať" : "Delete"}
                          >
                            🗑️
                          </span>
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
                    placeholder={
                      lang === "sk" ? "Nová kategória" : "New category"
                    }
                  />
                </td>
                <td style={{ width: "30%" }}>
                  <button className="btn" type="submit">
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
        <div className="page-title">
          <T
            sk="📊 Mesačná štatistika výdavkov"
            en="📊 Monthly expense statistics"
          />
        </div>

        <div className="chart-section">
          <div className="chart-container">
            <div className="month-nav">
              <span
                className="arrow"
                id="prevMonth"
                onClick={() => changeMonth(-1)}
              >
                ◀
              </span>
              <span id="monthLabel">{getMonthLabel(currentDate)}</span> :
              <span className="gold" id="monthSum">
                {(analyticsData?.total_amount || 0).toFixed(2)} €
              </span>
              <span
                className="arrow"
                id="nextMonth"
                onClick={() => changeMonth(1)}
              >
                ▶
              </span>
            </div>

            <div className="chart-canvas-wrapper">
              <canvas id="donutChart"></canvas>
            </div>
          </div>

          <div className="details-container" id="details">
            <h3>
              <T sk="Podiel potrieb" en="Share of needs" />
            </h3>
            <div className="details-total"></div>
            <div className="transactions" id="transactions"></div>
          </div>
        </div>
      </div>
    </div>
  );
}