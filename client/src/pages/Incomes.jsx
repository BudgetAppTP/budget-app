import React, { useEffect,useState } from "react";
import "./style/incomes.css";
import { useLang } from "../i18n/LanguageContext";
import T from "../i18n/T";

export default function Incomes() {
   const { lang, setLang } = useLang();

    useEffect(() => {
    document.title = "BudgetApp · Príjmy";
  }, []);

  // === Demo dáta ===
  const [incomes, setIncomes] = useState([
    { id: 1, date: "2025-10-01", description: "Výplata",tag:"unclassified", amount: 1200.0 },
    { id: 2, date: "2025-10-05", description: "Darček od babky",tag:"unclassified", amount: 200.0 },
    { id: 3, date: "2025-10-10", description: "Predaj starého bicykla",tag:"unclassified", amount: 350.0 },
    { id: 4, date: "2025-10-10", description: "mzda",tag:"STU", amount: 350.0 },
  ]);

  const [newIncome, setNewIncome] = useState({
    date: "",
    description: "",
    tag:"",
    amount: "",
  });

const STATIC_CATEGORIES = ["FEI"];
const [categories, setCategories] = useState(STATIC_CATEGORIES);
const [addingNew, setAddingNew] = useState(false);
const [newCatValue, setNewCatValue] = useState("");


  const [error, setError] = useState("");
  const [editingId, setEditingId] = useState(null);
  const [editBuffer, setEditBuffer] = useState({});
  const [sortOrder, setSortOrder] = useState({ date: "asc", amount: "asc" });

  const total = incomes.reduce((sum, i) => sum + i.amount, 0);

    const handleSubmit = (e) => {
    e.preventDefault();
    const { date, description, tag, amount } = newIncome;
    if (!date || !description||!tag || !amount) {
      setError(lang === "sk" ? "Všetky polia musia byť vyplnené!" : "All fields must be filled!");
      return;
    }
     setError("");
    const id = incomes.length ? incomes[incomes.length - 1].id + 1 : 1;
    setIncomes([
      ...incomes,
      { id, date, description,tag, amount: parseFloat(amount) },
    ]);
    setNewIncome({ date: "", description: "",tag:"", amount: "" });
  };

  const handleDelete = (id) => {
    setIncomes(incomes.filter((i) => i.id !== id));
  };

  const handleEditToggle = (id) => {
    if (editingId === id) {
      const { date, description, amount } = editBuffer;
      if (!date || !description || !amount) {
        setError("Všetky polia musia byť vyplnené!");
        return;
      }

      setError("");
      setIncomes(
        incomes.map((e) => (e.id === id ? { ...e, ...editBuffer, amount: parseFloat(amount) } : e))
      );
      setEditingId(null);
      setEditBuffer({});
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
      <div className="page-title">📊 <T sk="Príjmy" en="Incomes" /></div>

      <div className="summary">
        <span><T sk="Spolu tento mesiac" en="Total this month" />:</span>
        <span className="value">
          {total.toFixed(2).replace(".", ",")} €
        </span>
      </div>

      <div className="table-card">
      <table>
        <thead>
          <tr>
            <th className="sortable" onClick={() => handleSort("date")}>
              <T sk="Dátum" en="Date" />
            </th>
            <th><T sk="Popis" en="Description" /></th>
             <th style={{ textAlign: "center" }}><T sk="Organizácia" en="Organisation" /></th>
            <th className="sortable"  onClick={() => handleSort("amount")} style={{ textAlign: "right" }}>
                <T sk="Suma" en="Amount" />
            </th>
            <th style={{ textAlign: "center" }}><T sk="Akcia" en="Action" /></th>
          </tr>
        </thead>
        <tbody>
          {incomes.map((inc) => {
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
                <tr key={inc.id} style={rowStyle} className={isEditing ? "editing" : ""}>
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
                    inc.tag
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
                      inc.amount.toFixed(2)
                    )}
                  </td>
                  <td>
                    <div className="actions">
                        {!isEditing && (
                            <>
                              <span
                                className="action-icon delete"
                                onClick={() => handleDelete(inc.id)}
                                title={lang === "sk" ? "Vymazať" : "Delete"}
                              >
                                🗑️
                              </span>
                            </>
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
          })}
        </tbody>
        <tfoot>
          <tr>
            <td colSpan="3"><T sk="Spolu" en="Total" /></td>
            <td className="amount">{total.toFixed(2)}</td>
            <td></td>
          </tr>
        </tfoot>
      </table>
    </div>



      <form onSubmit={handleSubmit} className="incomes-form">
  <table className="input-table">
    <tbody>
      <tr>
        <td style={{ width: "15%" }}>
          <input
            type="date"
            value={newIncome.date}
            onChange={(e) =>
              setNewIncome({ ...newIncome, date: e.target.value })
            }
          />
        </td>

        <td style={{ width: "30%" }}>
          <input
            type="text"
            placeholder={lang === "sk" ? "Popis" : "Description"}
            value={newIncome.description}
            onChange={(e) =>
              setNewIncome({ ...newIncome, description: e.target.value })
            }
          />
        </td>

        <td style={{ width: "20%" }}>
         {!addingNew ? (
  <select
    className="organisation-wrapper"
    value={newIncome.tag}
    onChange={(e) => {
      const val = e.target.value;

      if (val === "add-new") {
        setAddingNew(true);
      } else {
        setNewIncome({ ...newIncome, tag: val });
      }
    }}
  >
    <option value="" disabled>
     <T sk="Organizácia" en="Organization" />
    </option>

    {categories.map((c, i) => (
      <option key={i} value={c}>
        {c}
      </option>
    ))}
    <option value="add-new"><T sk="➕ Pridať novú kategóriu" en="➕ Add new tag" /></option>
  </select>
) : (
  <div style={{ display: "flex", gap: "6px" }}>
    <input
      type="text"
      className="organisation-wrapper"
      placeholder={lang === "sk" ? "Nová kategória" : "New category"}
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
            value={newIncome.amount}
            onChange={(e) =>
              setNewIncome({ ...newIncome, amount: e.target.value })
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
