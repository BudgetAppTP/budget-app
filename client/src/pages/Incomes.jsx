import React, { useEffect,useState } from "react";
import "./style/incomes.css";

export default function Incomes() {

    useEffect(() => {
    document.title = "BudgetApp · Príjmy";
  }, []);

  const [incomes, setIncomes] = useState([
    { id: 1, date: "2025-10-01", description: "Výplata", amount: 1200.0 },
    { id: 2, date: "2025-10-05", description: "Darček od babky", amount: 200.0 },
    { id: 3, date: "2025-10-10", description: "Predaj starého bicykla", amount: 350.0 },
  ]);

  const [newIncome, setNewIncome] = useState({
    date: "",
    description: "",
    amount: "",
  });

  const [error, setError] = useState("");
  const [editingId, setEditingId] = useState(null);
  const [editBuffer, setEditBuffer] = useState({});
  const [sortOrder, setSortOrder] = useState({ date: "asc", amount: "asc" });

  const total = incomes.reduce((sum, i) => sum + i.amount, 0);

    const handleSubmit = (e) => {
    e.preventDefault();
    const { date, description, amount } = newIncome;
    if (!date || !description || !amount) {
      setError("Všetky polia musia byť vyplnené!");
      return;
    }
     setError("");
    const id = incomes.length ? incomes[incomes.length - 1].id + 1 : 1;
    setIncomes([
      ...incomes,
      { id, date, description, amount: parseFloat(amount) },
    ]);
    setNewIncome({ date: "", description: "", amount: "" });
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
      <div className="page-title">📊 Príjmy</div>

      <div className="summary">
        <span>Spolu tento mesiac:</span>
        <span className="value">
          {total.toFixed(2).replace(".", ",")} €
        </span>
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
                                title="Vymazať"
                              >
                                🗑️
                              </span>
                            </>
                          )}

                          <span
                            className="action-icon edit"
                            onClick={() => handleEditToggle(inc.id)}
                            title={isEditing ? "Uložiť zmeny" : "Upraviť"}
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
            <td colSpan="2">Spolu</td>
            <td className="amount">{total.toFixed(2)}</td>
            <td></td>
          </tr>
        </tfoot>
      </table>
    </div>



      <form onSubmit={handleSubmit} className="form-row">
        <input
            type="date"
            value={newIncome.date}
            onChange={(e) =>
                setNewIncome({...newIncome, date: e.target.value})
            }
        />
        <input
          type="text"
          placeholder="Popis"
          value={newIncome.description}
          onChange={(e) =>
            setNewIncome({ ...newIncome, description: e.target.value })
          }
        />
          <input
          type="number"
          step="0.01"
          placeholder="Suma (€)"
          value={newIncome.amount}
          onChange={(e) =>
            setNewIncome({ ...newIncome, amount: e.target.value })
          }
        />
        <button type="submit" className="btn">
          + Pridať záznam
        </button>
      </form>
       {error && <div className="error-text">{error}</div>}
    </div>
  );
}
