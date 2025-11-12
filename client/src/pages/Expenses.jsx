import React, {useEffect, useState} from "react";
import "./style/expenses.css";

export default function Expenses() {
      useEffect(() => {
    document.title = "BudgetApp · Vydavky";
  }, []);


  const [expenses, setExpenses] = useState([
    { id: 1, date: "2025-10-02", description: "TERNO real estate", amount: 45.2 },
    { id: 2, date: "2025-10-05", description: "Doprava", amount: 14.0 },
    { id: 3, date: "2025-10-07", description: "Byvanie", amount: 865.0 },
  ]);

  const [newExpense, setNewExpense] = useState({
    date: "",
    descripiton: "",
    amount: "",
  });

  const [error, setError] = useState("");
  const [editingId, setEditingId] = useState(null);
  const [editBuffer, setEditBuffer] = useState({});
  const [sortOrder, setSortOrder] = useState({ date: "asc", amount: "asc" });
  const total = expenses.reduce((sum, e) => sum + e.amount, 0);

    const handleSubmit = (e) => {
    e.preventDefault();
    const { date, description, amount } = newExpense;
    if (!date || !description || !amount) {
      setError("Všetky polia musia byť vyplnené!");
      return;
    }
     setError("");
    const id = expenses.length ? expenses[expenses.length - 1].id + 1 : 1;
    setExpenses([
      ...expenses,
      { id, date, description, amount: parseFloat(amount) },
    ]);
    setNewExpense({ date: "", description: "", amount: "" });
  };

  const handleDelete = (id) => {
    setExpenses(expenses.filter((e) => e.id !== id));
  };

  const handleEditToggle = (id) => {
    if (editingId === id) {
      const { date, description, amount } = editBuffer;
      if (!date || !description || !amount) {
        setError("Všetky polia musia byť vyplnené!");
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
        💸 Výdavky
      </div>

      <div className="summary">
        <span>Spolu tento mesiac:</span>
        <span className="value">{total.toFixed(2)} €</span>
      </div>

      <div className="table-card">
        <table>
          <thead>
          <tr>
            <th className="sortable" onClick={() => handleSort("date")}>
              Dátum
            </th>
            <th>Popis</th>
            <th className="sortable"  onClick={() => handleSort("amount")} style={{ textAlign: "right" }}>
              Suma (€)
            </th>
            <th style={{ textAlign: "center" }}>Akcie</th>
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

                       {!isEditing && (
                                                         <span
                                className="action-icon redirect"
                                title="Zobraziť na eKasa"
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
              <td colSpan="2">Spolu</td>
              <td className="amount">{total.toFixed(2)}</td>
              <td></td>
            </tr>
          </tfoot>
        </table>
      </div>

      <form className="form-row" onSubmit={handleSubmit}>
        <input
            type="date"
            value={newExpense.date}
            onChange={(e) =>
                setNewExpense({...newExpense, date: e.target.value})
            }
        />
        <input
          type="text"
          placeholder="Popis"
          value={newExpense.description}
          onChange={(e) =>
            setNewExpense({ ...newExpense, description: e.target.value })
          }
        />
          <input
          type="number"
          step="0.01"
          placeholder="Suma (€)"
          value={newExpense.amount}
          onChange={(e) =>
            setNewExpense({ ...newExpense, amount: e.target.value })
          }
        />
        <button className="btn" type="submit">
          + Pridať výdavok
        </button>
      </form>
       {error && <div className="error-text">{error}</div>}
    </div>
  );
}
