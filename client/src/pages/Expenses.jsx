import React, {useEffect, useState} from "react";
import "./style/expenses.css";
import T from "../i18n/T";
import { useLang } from "../i18n/LanguageContext";

export default function Expenses() {
   const { lang, setLang, t } = useLang();
      useEffect(() => {
    document.title = "BudgetApp · Vydavky";
  }, []);


  const [expenses, setExpenses] = useState([
    { id: 1, date: "2025-10-02", description: "unclassified",tag: "TERNO real estate" ,amount: 45.2 },
    { id: 2, date: "2025-10-05", description: "Doprava", tag:"unclassified",amount: 14.0 },
    { id: 3, date: "2025-10-07", description: "Byvanie",tag:"unclassified", amount: 865.0 },
  ]);

  const [newExpense, setNewExpense] = useState({
    date: "",
    descripiton: "",
    tag:"",
    amount: "",
  });

const STATIC_CATEGORIES = ["TERNO", "BILLA", "LIDL"];
const [categories, setCategories] = useState(STATIC_CATEGORIES);
const [addingNew, setAddingNew] = useState(false);
const [newCatValue, setNewCatValue] = useState("");


  const [error, setError] = useState("");
  const [editingId, setEditingId] = useState(null);
  const [editBuffer, setEditBuffer] = useState({});
  const [sortOrder, setSortOrder] = useState({ date: "asc", amount: "asc" });
  const total = expenses.reduce((sum, e) => sum + e.amount, 0);

    const handleSubmit = (e) => {
    e.preventDefault();
    const { date, description, tag, amount } = newExpense;
    if (!date || !description ||!tag || !amount) {
      setError(lang === "sk" ? "Všetky polia musia byť vyplnené!" : "All fields must be filled!");
      return;
    }
     setError("");
    const id = expenses.length ? expenses[expenses.length - 1].id + 1 : 1;
    setExpenses([
      ...expenses,
      { id, date, description,tag, amount: parseFloat(amount) },
    ]);
    setNewExpense({ date: "", description: "",tag:"", amount: "" });
  };

  const handleDelete = (id) => {
    setExpenses(expenses.filter((e) => e.id !== id));
  };

  const handleEditToggle = (id) => {
    if (editingId === id) {
      const { date, description, amount } = editBuffer;
      if (!date || !description || !amount) {
        setError(lang === "sk" ? "Všetky polia musia byť vyplnené!" : "All fields must be filled!");
        return;
      }

      setError("");
      setExpenses(
        expenses.map((e) => (e.id === id ? { ...e, ...editBuffer, amount: parseFloat(amount) } : e))
      );
      setEditingId(null);
      setEditBuffer({});
    } else {
      const exp = expenses.find((e) => e.id === id);
      setEditBuffer({ ...exp });
      setEditingId(id);
      setError("");
    }
  };

  const handleEkasaRedirect = () => {
    alert("➡ Presmerovanie na eKasa (demo)");
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

      <div className="summary">
        <span><T sk="Spolu tento mesiac:" en="Total this month:" /></span>
        <span className="value">{total.toFixed(2)} €</span>
      </div>

      <div className="table-card">
        <table>
          <thead>
          <tr>
            <th className="sortable" onClick={() => handleSort("date")}>
              <T sk="Dátum" en="Date" />
            </th>
            <th><T sk="Popis" en="Description" /></th>
             <th style={{ textAlign: "center" }}><T sk="Organizácia" en="Organization" /></th>
            <th className="sortable"  onClick={() => handleSort("amount")} style={{ textAlign: "right" }}>
              <T sk="Suma (€)" en="Amount (€)" />
            </th>
            <th style={{ textAlign: "center" }}><T sk="Akcie" en="Actions" /></th>
          </tr>
          </thead>
          <tbody>
            {expenses.map((exp, i) => {
              const isEditing = editingId === exp.id;
              const data = isEditing ? editBuffer : exp;

              const rowStyle = isEditing
                ? {
                    backgroundColor: "#fff8e1",
                    transition: "background-color 0.3s ease",
                  }
                : {};

              return (
                <tr key={exp.id} style={rowStyle} className={isEditing ? "editing" : ""}>
                  <td>
                    {isEditing ? (
                      <input
                        type="date"
                        value={data.date}
                        onChange={(e) =>
                          setEditBuffer({ ...editBuffer, date: e.target.value })
                        }
                      />
                    ) : (
                      exp.date
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
                    exp.description
                  )}
                  </td>
                                                      <td style={{ textAlign: "center" }}>
                   {isEditing ? (
                                      <textarea
                    value={data.tag}
                    onChange={(e) => {
                      const el = e.target;
                      el.style.height = "auto";
                      el.style.height = el.scrollHeight + "px";
                      setEditBuffer({
                        ...editBuffer,
                        tag: el.value,
                      });
                    }}
                    rows={1}
                  />
                  ) : (
                    exp.tag
                  )}
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
                      exp.amount.toFixed(2)
                    )}
                  </td>
                  <td>
                    <div className="actions">
                        {!isEditing && (
                            <>

                              <span
                                className="action-icon delete"
                                onClick={() => handleDelete(exp.id)}
                                title={lang === "sk" ? "Vymazať" : "Delete"}
                              >
                                🗑️
                              </span>
                            </>
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
                          >
                            {isEditing ? "✔" : "✏️"}
                          </span>

                       {!isEditing && (
                                                         <span
                                className="action-icon redirect"
                                title={
                          lang === "sk" ? "Zobraziť na eKasa" : "View on eKasa"
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
            })}
          </tbody>
          <tfoot>
            <tr>
              <td colSpan="3"> <T sk="Spolu" en="Total" /></td>
              <td className="amount">{total.toFixed(2)}</td>
              <td></td>
            </tr>
          </tfoot>
        </table>
      </div>



      <form onSubmit={handleSubmit} className="expense-form">
  <table className="expense-table">
    <tbody>
      <tr>
        <td style={{ width: "15%" }}>
          <input
            type="date"
            value={newExpense.date}
            onChange={(e) =>
              setNewExpense({ ...newExpense, date: e.target.value })
            }
          />
        </td>

        <td style={{ width: "30%" }}>
          <input
            type="text"
             placeholder={lang === "sk" ? "Popis" : "Description"}
            value={newExpense.description}
            onChange={(e) =>
              setNewExpense({ ...newExpense, description: e.target.value })
            }
          />
        </td>

        <td style={{ width: "20%" }}>
         {!addingNew ? (
  <select
    className="organisation-wrapper"
    value={newExpense.tag}
    onChange={(e) => {
      const val = e.target.value;

      if (val === "add-new") {
        setAddingNew(true);
      } else {
        setNewExpense({ ...newExpense, tag: val });
      }
    }}
  >
    <option value="" disabled>
      {lang === "sk" ? "Organizácia" : "Organization"}
    </option>

    {categories.map((c, i) => (
      <option key={i} value={c}>
        {c}
      </option>
    ))}

    <option value="add-new">{lang === "sk"
                      ? "➕ Pridať nový tag"
                      : "➕ Add new tag"}</option>
  </select>
) : (
  <div style={{ display: "flex", gap: "6px" }}>
    <input
      type="text"
      className="organisation-wrapper"
      placeholder={
                      lang === "sk" ? "Nová kategória" : "New category"
                    }
      value={newCatValue}
      onChange={(e) => setNewCatValue(e.target.value)}
    />

    <button className="organisation_button"
      type="button"
      onClick={() => {
        if (!newCatValue.trim()) return;

        const updated = [...categories, newCatValue.trim()];
        setCategories(updated);
        setNewIncome({ ...newIncome, tag: newCatValue.trim() });

        setAddingNew(false);
        setNewCatValue("");
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
            placeholder={lang === "sk" ? "Suma (€)" : "Amount (€)"}
            value={newExpense.amount}
            onChange={(e) =>
              setNewExpense({ ...newExpense, amount: e.target.value })
            }
          />
        </td>

        <td style={{ width: "20%", textAlign: "center" }}>
          <button type="submit" className="btn">
             {lang === "sk" ? "+ Pridať záznam" : "+ Add entry"}
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
