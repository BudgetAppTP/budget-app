import React, { useEffect, useState } from "react";
import "./style/expenses.css";
import T from "../i18n/T";
import { useLang } from "../i18n/LanguageContext";

const API_BASE_URL = "";
const USER_ID = "1be32073-0b12-4a59-b9a1-77e0d3586a4c";

export default function Expenses() {
  const { lang, t } = useLang();

  useEffect(() => {
    document.title = "BudgetApp · Vydavky";
  }, []);

  const [expenses, setExpenses] = useState([]);
  const [newExpense, setNewExpense] = useState({
    date: "",
    description: "",
    amount: "",
  });

  const [tagsExpense, setTagsExpense] = useState([]);
  const [selectedTagId, setSelectedTagId] = useState("");
  const [addingNew, setAddingNew] = useState(false);
  const [newCatValue, setNewCatValue] = useState("");

  const [error, setError] = useState("");
  const [editingId, setEditingId] = useState(null);
  const [editBuffer, setEditBuffer] = useState({});
  const [sortOrder, setSortOrder] = useState({ date: "asc", amount: "asc" });

  const [isLoading, setIsLoading] = useState(true);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [savingId, setSavingId] = useState(null);
  const [deletingId, setDeletingId] = useState(null);
  const total = expenses.reduce((sum, e) => sum + (e.amount || 0), 0);


  const fetchExpenseTags = async () => {
  try {
    const res = await fetch(`/api/tags/expense`);
    const json = await res.json();
    const data = json?.data ?? json;
    const list = Array.isArray(data?.tags) ? data.tags : [];
    setTagsExpense(list);
  } catch (e) {
    console.error(e);
  }
};

  const createExpenseTag = async (name) => {
  const payload = {
    user_id: USER_ID,
    name: name.trim(),
    type: "expense",
  };

  const res = await fetch(`/api/tags`, {
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

  return json?.data?.id;
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
      const lastDay = new Date(y, m + 1, 0).getDate();
      const last = `${y}-${pad2(m + 1)}-${pad2(lastDay)}`;
      return { first, last };
    };

    const { first: minDate, last: maxDate } = monthBounds(currentDate);


    const changeMonth = (offset) => {
      const newDate = new Date(currentDate);
      newDate.setMonth(currentDate.getMonth() + offset);

      const newKey = monthKeyFromDate(newDate);
      setCurrentDate(newDate);
      window.history.replaceState({}, "", `?month=${newKey}`);

      setNewExpense((prev) => ({ ...prev, date: "" }));
      setError("");
    };


    const getMonthName = (date, lang) =>
      date.toLocaleDateString(lang === "sk" ? "sk-SK" : "en-US", {
        month: "long",
        year: "numeric",
      });





  useEffect(() => {
  fetchExpenseTags();
  }, [lang]);

  useEffect(() => {
  fetchReceipts("issue_date", "desc", currentDate);
  }, [currentDate, lang]);

  const fetchReceipts = async (sortField = "issue_date", order = "desc", dateForQuery = currentDate) => {
        try {
          setIsLoading(true);
          setError("");

          const year = dateForQuery.getFullYear();
          const month = dateForQuery.getMonth() + 1; // 1..12

          const params = new URLSearchParams({
            sort: sortField,
            order,
            year: String(year),
            month: String(month),
          });

          const res = await fetch(`${API_BASE_URL}/api/receipts?${params.toString()}`);
          const json = await res.json();

          const list = Array.isArray(json?.data)
            ? json.data
            : Array.isArray(json)
            ? json
            : [];

          const mapped = list.map((r) => ({
            id: r.id,
            date: r.issue_date || "",
            description: r.description || "",
            amount:
              typeof r.total_amount === "number"
                ? r.total_amount
                : parseFloat(r.total_amount || 0) || 0,
            tag: r.tag || "unclassified",
            tag_id: r.tag_id || null,
          }));

          setExpenses(mapped);
        } catch (err) {
          console.error(err);
          setError(
            lang === "sk"
              ? "Nepodarilo sa načítať výdavky."
              : "Failed to load expenses."
          );
        } finally {
          setIsLoading(false);
        }
      };

  async function fetchReceiptById(id) {
  const res = await fetch(`${API_BASE_URL}/api/receipts/${id}`);
  const json = await res.json();

  const r = json?.data ?? json;

  return {
    id: r.id,
    date: r.issue_date || "",
    description: r.description || "",
    amount:
      typeof r.total_amount === "number"
        ? r.total_amount
        : parseFloat(r.total_amount || 0) || 0,
    tag: r.tag || "unclassified",
    tag_id: r.tag_id || null,
  };
}






  const handleSubmit = async (e) => {
    e.preventDefault();
    const { date, description, amount } = newExpense;

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


    setIsSubmitting(true);

    try {
      const payload = {
      user_id: USER_ID,
      issue_date: date,
      description: description.trim(),
      currency: "EUR",
      total_amount: parseFloat(amount),
      tag_id: selectedTagId || null,
    };

      const res = await fetch(`${API_BASE_URL}/api/receipts`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(payload),
      });

      const json = await res.json();

      if (!res.ok || json.error) {
        const backendMsg =
          json.error?.message ||
          json.data?.error ||
          (lang === "sk"
            ? "Nepodarilo sa vytvoriť výdavok."
            : "Failed to create expense.");
        setError(backendMsg);
        return;
      }

      const createdId = json?.data?.id;

      const selectedTagName =
  tagsExpense.find((t) => t.id === selectedTagId)?.name || "unclassified";
let newRow;

if (createdId) {
  try {
    newRow = await fetchReceiptById(createdId);
    newRow = { ...newRow, tag: selectedTagName, tag_id: selectedTagId };
  } catch (e) {
    console.error("Failed to fetch created receipt by id", e);
    newRow = {
      id: createdId,
      date,
      description: description.trim(),
      tag: selectedTagName,
      tag_id: selectedTagId,
      amount: parseFloat(amount),
    };
  }
} else {
  newRow = {
    id: crypto.randomUUID(),
    date,
    description: description.trim(),
    tag: selectedTagName,
    tag_id: selectedTagId,
    amount: parseFloat(amount),
  };
}

setExpenses([...expenses, newRow]);


      setNewExpense({ date: "", description: "",  amount: "" });
      setSelectedTagId("");
      setAddingNew(false);
      setNewCatValue("");
    } catch (err) {
      console.error(err);
      setError(
        lang === "sk"
          ? "Chyba spojenia so serverom. Skúste znova."
          : "Connection error. Please try again."
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    setError("");
    setDeletingId(id);

    try {
      const res = await fetch(`${API_BASE_URL}/api/receipts/${id}`, {
        method: "DELETE",
      });

      const json = await res.json();

      if (!res.ok || json.error) {
        const backendMsg =
          json.error?.message ||
          json.data?.error ||
          (lang === "sk"
            ? "Nepodarilo sa vymazať výdavok."
            : "Failed to delete expense.");
        setError(backendMsg);
        return;
      }

      setExpenses(expenses.filter((e) => e.id !== id));
    } catch (err) {
      console.error(err);
      setError(
        lang === "sk"
          ? "Chyba spojenia so serverom pri mazaní."
          : "Connection error while deleting."
      );
    } finally {
      setDeletingId(null);
    }
  };

  const handleEditToggle = async (id) => {
    if (editingId === id) {
      const { date, description, amount, tag } = editBuffer;

      if (!date || !description || amount === "" || amount === null) {
        setError(
          lang === "sk"
            ? "Všetky polia musia byť vyplnené!"
            : "All fields must be filled!"
        );
        return;
      }

      if (date < minDate || date > maxDate) {
        setError(
          lang === "sk"
            ? "Dátum musí byť v aktuálnom mesiaci."
            : "Date must be within the current month."
        );
        return;
      }

      setError("");
      setSavingId(id);

      try {
        const payload = {
          issue_date: date,
          description: description.trim(),
          total_amount: parseFloat(amount),
        };

        const res = await fetch(`${API_BASE_URL}/api/receipts/${id}`, {
          method: "PUT",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(payload),
        });

        const json = await res.json();

        if (!res.ok || json.error) {
          const backendMsg =
            json.error?.message ||
            json.data?.error ||
            (lang === "sk"
              ? "Nepodarilo sa upraviť výdavok."
              : "Failed to update expense.");
          setError(backendMsg);
          return;
        }

        setExpenses(
          expenses.map((e) =>
            e.id === id
              ? {
                  ...e,
                  date,
                  description: description.trim(),
                  amount: parseFloat(amount),
                  tag: tag ?? e.tag,
                }
              : e
          )
        );


        setEditingId(null);
        setEditBuffer({});
      } catch (err) {
        console.error(err);
        setError(
          lang === "sk"
            ? "Chyba spojenia so serverom pri úprave."
            : "Connection error while updating."
        );
      } finally {
        setSavingId(null);
      }
    } else {
      const exp = expenses.find((e) => e.id === id);
      if (!exp) return;
      setEditBuffer({
        id: exp.id,
        date: exp.date,
        description: exp.description,
        amount: exp.amount,
        tag: exp.tag,
      });
      setEditingId(id);
      setError("");
    }
  };

  const handleEkasaRedirect = () => {
    alert("Presmerovanie na eKasa (demo)");
  };









  const handleSort = (field) => {
    const order = sortOrder[field] === "asc" ? "desc" : "asc";
    setSortOrder({ ...sortOrder, [field]: order });
    const sorted = [...expenses].sort((a, b) => {
      if (field === "amount")
        return order === "asc" ? a.amount - b.amount : b.amount - a.amount;
      return order === "asc"
        ? a.date.localeCompare(b.date)
        : b.date.localeCompare(a.date);
    });
    setExpenses(sorted);
  };

  return (
    <div className="wrap expenses">
      <div className="page-title">
        <T sk="💸 Výdavky" en="💸 Expenses" />
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

      {isLoading ? (
        <div className="loading">
          {lang === "sk" ? "Načítavam výdavky..." : "Loading expenses..."}
        </div>
      ) : (
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
                  <T sk="Organizácia" en="Organization" />
                </th>
                <th
                  className="sortable"
                  onClick={() => handleSort("amount")}
                  style={{ textAlign: "right" }}
                >
                  <T sk="Suma (€)" en="Amount (€)" />
                </th>
                <th style={{ textAlign: "center" }}>
                  <T sk="Akcie" en="Actions" />
                </th>
              </tr>
            </thead>
            <tbody>
            {expenses.length === 0 ? (
    <tr>
      <td colSpan={5} className="empty-row" style={{ opacity: 0.7, padding: "12px" }}>
        {lang === "sk"
          ? "Žiadne výdavky pre tento mesiac"
          : "No expenses for this month"}
      </td>
    </tr>
  ) : (expenses.map((exp) => {
                const isEditing = editingId === exp.id;
                const data = isEditing ? editBuffer : exp;

                const rowStyle = isEditing
                  ? {
                      backgroundColor: "#fff8e1",
                      transition: "background-color 0.3s ease",
                    }
                  : {};

                return (
                  <tr
                    key={exp.id}
                    style={rowStyle}
                    className={isEditing ? "editing" : ""}
                  >
                    <td>
                      {isEditing ? (
                          <input
                            type="date"
                            min={minDate}
                            max={maxDate}
                            value={data.date || ""}
                            onChange={(e) => {
                              const v = e.target.value;

                              if (v && (v < minDate || v > maxDate)) {
                                setError(
                                  lang === "sk"
                                    ? "Dátum musí byť v aktuálnom mesiaci."
                                    : "Date must be within the current month."
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
                          exp.date
                        )}
                    </td>
                    <td>
                      {isEditing ? (
                        <textarea
                          value={data.description || ""}
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
                        exp.description
                      )}
                    </td>
                    <td style={{ textAlign: "center" }}>
                      {exp.tag}
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
                        (exp.amount ?? 0).toFixed(2)
                      )}
                    </td>
                    <td>
                      <div className="actions">
                        {!isEditing && (
                          <span
                            className="action-icon delete"
                            onClick={() => handleDelete(exp.id)}
                            title={
                              lang === "sk" ? "Vymazať" : "Delete"
                            }
                            style={{
                              opacity: deletingId === exp.id ? 0.4 : 1,
                              pointerEvents:
                                deletingId === exp.id ? "none" : "auto",
                            }}
                          >
                            🗑️
                          </span>
                        )}

                        <span
                          className="action-icon edit"
                          onClick={() => handleEditToggle(exp.id)}
                          title={
                            isEditing
                              ? lang === "sk"
                                ? "Uložiť zmeny"
                                : "Save changes"
                              : lang === "sk"
                              ? "Upraviť"
                              : "Edit"
                          }
                          style={{
                            opacity: savingId === exp.id ? 0.5 : 1,
                          }}
                        >
                          {isEditing ? "✔" : "✏️"}
                        </span>

                        {!isEditing && (
                          <span
                            className="action-icon redirect"
                            title={
                              lang === "sk"
                                ? "Zobraziť na eKasa"
                                : "View on eKasa"
                            }
                            onClick={handleEkasaRedirect}
                          >
                            ➜
                          </span>
                        )}
                      </div>
                    </td>
                  </tr>
                 );
    })
  )}
</tbody>
            <tfoot>
              <tr>
                <td colSpan={3}>
                  <T sk="Spolu" en="Total" />
                </td>
                <td className="amount">{total.toFixed(2)}</td>
                <td></td>
              </tr>
            </tfoot>
          </table>
        </div>
      )}

      {}
      <form onSubmit={handleSubmit} className="expense-form">
        <table className="expense-table">
          <tbody>
            <tr>
              <td style={{ width: "15%" }}>
                <input
                  type="date"
                  min={minDate}
                  max={maxDate}
                  value={newExpense.date}
                  onChange={(e) => {
                    const v = e.target.value;

                    if (v && (v < minDate || v > maxDate)) {
                      setError(
                        lang === "sk"
                          ? "Dátum musí byť v aktuálnom mesiaci."
                          : "Date must be within the current month."
                      );
                      return;
                    }

                    setError("");
                    setNewExpense({ ...newExpense, date: v });
                  }}
                />

              </td>

              <td style={{ width: "30%" }}>
                <input
                  type="text"
                  placeholder={
                    lang === "sk" ? "Popis" : "Description"
                  }
                  value={newExpense.description}
                  onChange={(e) =>
                    setNewExpense({
                      ...newExpense,
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
                        if (val === "add-new") setAddingNew(true);
                        else setSelectedTagId(val);
                      }}
                    >
                      <option value="" disabled>
                        {lang === "sk" ? "Organizácia" : "Organization"}
                      </option>

                      {tagsExpense.map((t) => (
                        <option key={t.id} value={t.id}>
                          {t.name}
                        </option>
                      ))}

                      <option value="add-new">
                        {lang === "sk" ? "➕ Pridať nový tag" : "➕ Add new tag"}
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
                      onChange={(e) =>
                        setNewCatValue(e.target.value)
                      }
                    />

                    <button
                          className="organisation_button"
                          type="button"
                          onClick={async () => {
                            const name = (newCatValue || "").trim();
                            if (!name) return;

                            try {
                              const createdId = await createExpenseTag(name);

                              const createdTag = {
                                id: createdId,
                                user_id: USER_ID,
                                name,
                                type: "expense",
                                counter: 0,
                              };

                              setTagsExpense((prev) => [...prev, createdTag]);
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
                  value={newExpense.amount}
                  onChange={(e) =>
                    setNewExpense({
                      ...newExpense,
                      amount: e.target.value,
                    })
                  }
                />
              </td>

              <td style={{ width: "20%", textAlign: "center" }}>
                <button
                  type="submit"
                  className="btn"
                  disabled={isSubmitting}
                >
                  {isSubmitting
                    ? lang === "sk"
                      ? "Ukladám..."
                      : "Saving..."
                    : lang === "sk"
                    ? "+ Pridať záznam"
                    : "+ Add entry"}
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
