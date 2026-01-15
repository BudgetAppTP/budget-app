import React, {useEffect, useMemo, useState} from "react";
import "./style/incomes.css";
import { useLang } from "../i18n/LanguageContext";
import T from "../i18n/T";


const API_BASE = "/api";
const USER_ID = "1be32073-0b12-4a59-b9a1-77e0d3586a4c";

export default function Incomes() {
  const { lang } = useLang();

  useEffect(() => {
    document.title = "BudgetApp · Príjmy";
  }, []);

  const [incomes, setIncomes] = useState([]);
  const [newIncome, setNewIncome] = useState({
    date: "",
    description: "",
    tag: "",
    amount: "",
  });

  const [tagsIncome, setTagsIncome] = useState([]);
  const [selectedTagId, setSelectedTagId] = useState("");
  const [addingNew, setAddingNew] = useState(false);
  const [newCatValue, setNewCatValue] = useState("");

  const [error, setError] = useState("");
  const [editingId, setEditingId] = useState(null);
  const [editBuffer, setEditBuffer] = useState({});
  const [sortOrder, setSortOrder] = useState({
    date: "asc",
    amount: "asc",
  });

  const total = incomes.reduce((sum, i) => sum + (i.amount || 0), 0);

  const fetchIncomes = async (sortField = "income_date", order = "desc", dateForQuery = currentDate) => {
  try {
    const year = dateForQuery.getFullYear();
    const month = dateForQuery.getMonth() + 1; // 1..12

    const params = new URLSearchParams({
      sort: sortField,
      order,
      year: String(year),
      month: String(month),
    });

    const res = await fetch(`${API_BASE}/incomes?${params.toString()}`);
    const json = await res.json();

    const data = json.data ?? json;
    const list = Array.isArray(data.incomes) ? data.incomes : [];

    const mapped = list.map((i) => ({
      id: i.id,
      date: i.income_date || "",
      description: i.description || "",
      tag: i.tag || "",
      tag_id: i.tag_id || null,
      amount:
        typeof i.amount === "number"
          ? i.amount
          : parseFloat(i.amount || 0) || 0,
    }));

    setIncomes(mapped);
    setError("");
  } catch (err) {
    console.error(err);
    setError(lang === "sk" ? "Chyba pri načítaní príjmov" : "Failed to load incomes");
  }
};


  const fetchIncomeById = async (id) => {
    const res = await fetch(`${API_BASE}/incomes/${id}`);
    const json = await res.json();

    if (!res.ok) {
      const msg =
        json?.data?.error ||
        (lang === "sk" ? "Nepodarilo sa načítať príjem" : "Failed to load income");
      throw new Error(msg);
    }

    const r = json.data ?? json;

    return {
      id: r.id,
      date: r.income_date || "",
      description: r.description || "",
      tag: r.tag || "unclassified",
      amount:
        typeof r.amount === "number"
          ? r.amount
          : parseFloat(r.amount || 0) || 0,
    };
  };


  const fetchIncomeTags = async () => {
  try {
    const res = await fetch(`${API_BASE}/tags/income`);
    const json = await res.json();
    const data = json?.data ?? json;
    const list = Array.isArray(data?.tags) ? data.tags : [];
    setTagsIncome(list);
  } catch (e) {
    console.error(e);
  }
};

const createIncomeTag = async (name) => {
  const payload = {
    user_id: USER_ID,
    name: name.trim(),
    type: "income",
  };

  const res = await fetch(`${API_BASE}/tags`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const json = await res.json();

  if (!res.ok) {
    const msg =
      json?.data?.error ||
      json?.error?.message ||
      (lang === "sk" ? "Nepodarilo sa vytvoriť tag" : "Failed to create tag");
    throw new Error(msg);
  }

  const createdId = json?.data?.id;
  return createdId;
};


const [currentDate, setCurrentDate] = useState(() => {
     const params = new URLSearchParams(window.location.search);
     const m = params.get("month");
     return m ? new Date(m + "-01") : new Date();
  });


    const monthKeyFromDate = (d) => d.toISOString().slice(0, 7);

    const pad2 = (n) => String(n).padStart(2, "0");

const monthBounds = (d) => {
  const y = d.getFullYear();
  const m = d.getMonth(); // 0..11
  const first = `${y}-${pad2(m + 1)}-01`;
  const lastDay = new Date(y, m + 1, 0).getDate(); // последний день месяца
  const last = `${y}-${pad2(m + 1)}-${pad2(lastDay)}`;
  return { first, last };
};

const { first: minDate, last: maxDate } = monthBounds(currentDate);


    const changeMonth = (offset) => {
  const newDate = new Date(currentDate);
  newDate.setMonth(newDate.getMonth() + offset);

  const newKey = monthKeyFromDate(newDate);
  setCurrentDate(newDate);
  window.history.replaceState({}, "", `?month=${newKey}`);

  setNewIncome((prev) => ({ ...prev, date: "" }));
  setError("");
};


    const getMonthName = (date, lang) =>
      date.toLocaleDateString(lang === "sk" ? "sk-SK" : "en-US", {
        month: "long",
        year: "numeric",
      });













  useEffect(() => {
  fetchIncomeTags();
}, [lang]);

useEffect(() => {
  fetchIncomes("income_date", "desc", currentDate);
}, [currentDate, lang]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    const { date, description, tag, amount } = newIncome;

    if (!date || !description || !amount || !selectedTagId) {
      setError(
        lang === "sk"
          ? "Všetky polia musia byť vyplnené!"
          : "All fields must be filled!"
      );
      return;
    }

    setError("");

    if (date < minDate || date > maxDate) {
  setError(
    lang === "sk"
      ? "Dátum musí byť v aktuálnom mesiaci."
      : "Date must be within the current month."
  );
  return;
}

    const payload = {
      user_id: USER_ID,
      income_date: date,
      description: description.trim(),
      amount: parseFloat(amount),
      tag_id: selectedTagId || null,
      extra_metadata: null,
    };

    try {
      const res = await fetch(`${API_BASE}/incomes`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const json = await res.json();

      if (!res.ok) {
        setError(
          json?.data?.error ||
            json?.error?.message ||
            (lang === "sk"
              ? "Nepodarilo sa vytvoriť záznam"
              : "Failed to create income")
        );
        return;
      }

      const createdId = json?.data?.id;
      let newRow;

      if (createdId) {
        try {
          newRow = await fetchIncomeById(createdId);
          newRow = { ...newRow, tag: tag || newRow.tag };
        } catch (err) {
          console.error("Failed to refetch created income:", err);
          newRow = {
            id: createdId,
            date,
            description: description.trim(),
            tag,
            amount: parseFloat(amount),
          };
        }
      } else {
        const fallbackId =
          (typeof crypto !== "undefined" && crypto.randomUUID) ||
          Date.now().toString();
        newRow = {
          id: fallbackId,
          date,
          description: description.trim(),
          tag,
          amount: parseFloat(amount),
        };
      }

      setIncomes((prev) => [...prev, newRow]);
      setNewIncome({ date: "", description: "", tag: "", amount: "" });
    } catch (err) {
      console.error(err);
      setError(
        lang === "sk"
          ? "Chyba pri komunikácii so serverom"
          : "Server communication error"
      );
    }
  };

  const handleDelete = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/incomes/${id}`, {
        method: "DELETE",
      });

      const json = await res.json();

      if (!res.ok) {
        setError(
          json?.data?.error ||
            (lang === "sk"
              ? "Nepodarilo sa vymazať záznam"
              : "Failed to delete income")
        );
        return;
      }

      setIncomes((prev) => prev.filter((i) => i.id !== id));
    } catch (err) {
      console.error(err);
      setError(
        lang === "sk"
          ? "Chyba pri komunikácii so serverom"
          : "Server communication error"
      );
    }
  };

  const handleEditToggle = async (id) => {
    const isEditing = editingId === id;

    if (isEditing) {
      const { date, description, tag, amount } = editBuffer;

      if (!date || !description || !amount) {
        setError(
          lang === "sk"
            ? "Všetky polia musia byť vyplnené!"
            : "All fields must be filled!"
        );
        return;
      }

      const payload = {
        income_date: date,
        description: description.trim(),
        amount: parseFloat(amount),
        extra_metadata: null,
      };

      try {
        const res = await fetch(`${API_BASE}/incomes/${id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });

        const json = await res.json();

        if (!res.ok) {
          setError(
            json?.data?.error ||
              (lang === "sk"
                ? "Nepodarilo sa upraviť záznam"
                : "Failed to update income")
          );
          return;
        }

        let updatedRow;
        try {
          updatedRow = await fetchIncomeById(id);
          updatedRow = { ...updatedRow, tag: tag || updatedRow.tag };
        } catch (err) {
          console.error("Failed to refetch updated income:", err);
          updatedRow = {
            ...editBuffer,
            id,
            amount: parseFloat(amount),
          };
        }

        setIncomes((prev) =>
          prev.map((i) => (i.id === id ? updatedRow : i))
        );
        setEditingId(null);
        setEditBuffer({});
        setError("");
      } catch (err) {
        console.error(err);
        setError(
          lang === "sk"
            ? "Chyba pri komunikácii so serverom"
            : "Server communication error"
        );
      }
    } else {
      const inc = incomes.find((e) => e.id === id);
      setEditBuffer({ ...inc });
      setEditingId(id);
      setError("");
    }
  };







  const handleSort = (field) => {
    const order = sortOrder[field] === "asc" ? "desc" : "asc";
    setSortOrder({ ...sortOrder, [field]: order });

    const sorted = [...incomes].sort((a, b) => {
      if (field === "amount")
        return order === "asc" ? a.amount - b.amount : b.amount - a.amount;
      return order === "asc"
        ? a.date.localeCompare(b.date)
        : b.date.localeCompare(a.date);
    });

    setIncomes(sorted);
  };

  return (
    <div className="wrap incomes">
      <div className="page-title">
        📊 <T sk="Príjmy" en="Incomes" />
      </div>




      <div className="page-header">



        <div className="month-nav">
          <button id="prev-month" onClick={() => changeMonth(-1)}>◀</button>
          <h2>{getMonthName(currentDate,lang)}</h2>
          <button id="next-month" onClick={() => changeMonth(1)}>▶</button>
        </div>

        <div className="summary">
        <span>
          <T sk="Spolu tento mesiac" en="Total this month" />:
        </span>
        <span className="value">
          {total.toFixed(2).replace(".", ",")} €
        </span>
      </div>



      </div>

      <div className="table-card">
        <table>
          <thead>
            <tr>
              <th className="sortable" onClick={() => handleSort("date")}>
                <T sk="Dátum" en="Date" />
              </th>
              <th>
                <T sk="Popis" en="Description" />
              </th>
              <th style={{ textAlign: "center" }}>
                <T sk="Organizácia" en="Organisation" />
              </th>
              <th
                className="sortable"
                onClick={() => handleSort("amount")}
                style={{ textAlign: "right" }}
              >
                <T sk="Suma" en="Amount" />
              </th>
              <th style={{ textAlign: "center" }}>
                <T sk="Akcia" en="Action" />
              </th>
            </tr>
          </thead>
          <tbody>
          {incomes.length === 0 ? (
    <tr>
      <td colSpan={5} className="empty-row" style={{ opacity: 0.7, padding: "12px" }}>
        {lang === "sk"
          ? "Žiadne príjmy pre tento mesiac"
          : "No incomes for this month"}
      </td>
    </tr>
  ) : (incomes.map((inc) => {
              const isEditing = editingId === inc.id;
              const data = isEditing ? editBuffer : inc;

              const rowStyle = isEditing
                ? {
                    backgroundColor: "#fff8e1",
                    boxShadow: "inset 0 0 0 2px #d4a017",
                    transition: "background-color 0.3s ease",
                  }
                : {};

              return (
                <tr
                  key={inc.id}
                  style={rowStyle}
                  className={isEditing ? "editing" : ""}
                >
                  <td>
                    {isEditing ? (
                      <input
  type="date"
  min={minDate}
  max={maxDate}
  value={data.date}
  onChange={(e) => {
    const v = e.target.value;

    if (v && (v < minDate || v > maxDate)) {
      setError(
        lang === "sk"
          ? "Dátum musí byť v aktuálnom mesiaci"
          : "Date must be within the current month"
      );
      return;
    }

    setError("");
    setEditBuffer({
      ...editBuffer,
      date: v,
    });
  }}
/>
                    ) : (
                      inc.date
                    )}
                  </td>
                  <td>
                    {isEditing ? (
                      <textarea
                        value={data.description}
                        onChange={(e) => {
                          const el = e.target;
                          el.style.height = "auto";
                          el.style.height = el.scrollHeight + "px";
                          setEditBuffer({
                            ...editBuffer,
                            description: el.value,
                          });
                        }}
                        rows={1}
                      />
                    ) : (
                      inc.description
                    )}
                  </td>
                  <td style={{ textAlign: "center" }}>
                    {inc.tag}
                  </td>
                  <td style={{ textAlign: "right" }}>
                    {isEditing ? (
                      <input
                        type="number"
                        step="0.01"
                        value={data.amount}
                        onChange={(e) =>
                          setEditBuffer({
                            ...editBuffer,
                            amount: parseFloat(e.target.value || 0),
                          })
                        }
                      />
                    ) : (
                      inc.amount.toFixed(2)
                    )}
                  </td>
                  <td>
                    <div className="actions">
                      {!isEditing && (
                        <span
                          className="action-icon delete"
                          onClick={() => handleDelete(inc.id)}
                          title={
                            lang === "sk" ? "Vymazať" : "Delete"
                          }
                        >
                          🗑️
                        </span>
                      )}

                      <span
                        className="action-icon edit"
                        onClick={() => handleEditToggle(inc.id)}
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
                    </div>
                  </td>
                </tr>
              );
            })
  )}
</tbody>
          <tfoot>
            <tr>
              <td colSpan="3">
                <T sk="Spolu" en="Total" />
              </td>
              <td className="amount">{total.toFixed(2)}</td>
              <td></td>
            </tr>
          </tfoot>
        </table>
      </div>

      {}
      <form onSubmit={handleSubmit} className="incomes-form">
        <table className="input-table">
          <tbody>
            <tr>
              <td style={{ width: "15%" }}>
                <input
  type="date"
  min={minDate}
  max={maxDate}
  value={newIncome.date}
  onChange={(e) => {
    const v = e.target.value;

    if (v && (v < minDate || v > maxDate)) {
      setError(
        lang === "sk"
          ? "Dátum musí byť v aktuálnom mesiaci"
          : "Date must be within the current month"
      );
      return;
    }

    setError("");
    setNewIncome({ ...newIncome, date: v });
  }}
/>
              </td>

              <td style={{ width: "30%" }}>
                <input
                  type="text"
                  placeholder={lang === "sk" ? "Popis" : "Description"}
                  value={newIncome.description}
                  onChange={(e) =>
                    setNewIncome({
                      ...newIncome,
                      description: e.target.value,
                    })
                  }
                />
              </td>

              <td style={{ width: "20%" }}>
                {!addingNew ? (
                  <select
                    className="organisation-wrapper"
                    value={selectedTagId}
                    onChange={(e) => {
                      const val = e.target.value;

                      if (val === "add-new") {
                        setAddingNew(true);
                      } else {
                        setSelectedTagId(val);
                      }
                    }}
                  >
                    <option value="" disabled>
                      <T sk="Organizácia" en="Organization" />
                    </option>

                    {tagsIncome.map((t) => (
                      <option key={t.id} value={t.id}>
                        {t.name}
                      </option>
                    ))}
                    <option value="add-new">
                      <T
                        sk="➕ Pridať novú kategóriu"
                        en="➕ Add new tag"
                      />
                    </option>
                  </select>
                ) : (
                  <div style={{ display: "flex", gap: "6px" }}>
                    <input
                      type="text"
                      className="organisation-wrapper"
                      placeholder={
                        lang === "sk"
                          ? "Nová kategória"
                          : "New category"
                      }
                      value={newCatValue}
                      onChange={(e) => setNewCatValue(e.target.value)}
                    />

                    <button
                        className="organisation_button"
                        type="button"
                        onClick={async () => {
                          const name = (newCatValue || "").trim();
                          if (!name) return;

                          try {
                            const createdId = await createIncomeTag(name);
                            const createdTag = {
                              id: createdId,
                              user_id: USER_ID,
                              name,
                              type: "income",
                              counter: 0,
                            };

                            setTagsIncome((prev) => [...prev, createdTag]);

                            setSelectedTagId(createdId);

                            setAddingNew(false);
                            setNewCatValue("");
                            setError("");
                          } catch (err) {
                            console.error(err);
                            setError(err.message);
                          }
                        }}
                      >
                        ✔
                      </button>

                  </div>
                )}
              </td>

              <td style={{ width: "15%" }}>
                <input
                  type="number"
                  step="0.01"
                  placeholder={
                    lang === "sk" ? "Suma (€)" : "Amount (€)"
                  }
                  value={newIncome.amount}
                  onChange={(e) =>
                    setNewIncome({
                      ...newIncome,
                      amount: e.target.value,
                    })
                  }
                />
              </td>

              <td style={{ width: "20%", textAlign: "center" }}>
                <button type="submit" className="btn">
                  <T sk="+ Pridať záznam" en="+ Add record" />
                </button>
              </td>
            </tr>
          </tbody>
        </table>
      </form>

      {error && <div className="error-text">{error}</div>}
    </div>
  );
}
