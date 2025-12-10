import React, { useState, useEffect } from "react";
import Chart from "chart.js/auto";
import "./style/organisation.css";
import T from "../i18n/T";
import { useLang } from "../i18n/LanguageContext";

export default function Needs() {
   const {lang} = useLang();
        useEffect(() => {
    document.title = "BudgetApp · Organizácie";
  }, []);
const [selectedCategory, setSelectedCategory] = useState("prijmy");

const [incomeCategories, setIncomeCategories] = useState([
 { id: 1, name: "STU" }
]);

const [expenseCategories, setExpenseCategories] = useState([

      { id: 1, name: "Billa" },
  { id: 2, name: "Lidl"},
  { id: 3, name: "Tesco"},
]);


const [categories, setCategories] = useState(incomeCategories);

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

const handleCategorySwitch = (e) => {
  const value = e.target.value;
  setSelectedCategory(value);

  if (value === "prijmy") {
    setCategories(incomeCategories);
  } else {
    setCategories(expenseCategories);
  }
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

}, []);


  return (
    <div className="wrap organisation">
      <div>
        <div className="page-title"><T sk="🏛️ Organizácie" en="🏛️ Organizations" /></div>
          <div className="choice-box">
                <p><T sk="Zobraziť organizácie:" en="Show organizations:" /></p>
              <form>
                  <label>
                          <input
                              type="radio"
                              name="category"
                              value="prijmy"
                              checked={selectedCategory === "prijmy"}
                              onChange={handleCategorySwitch}
                            />
                        {lang === "sk" ? "📊 Príjmov" : "📊 Incomes"}
                  </label>
                  <label>
                          <input
                              type="radio"
                              name="category"
                              value="vydavky"
                              checked={selectedCategory === "vydavky"}
                              onChange={handleCategorySwitch}
                            />
                     {lang === "sk" ? "💸 Výdavkov" : "💸 Expenses"}
                  </label>
              </form>


          </div>
          <div className="table-wrap">
              <table>
                  <thead>
                  <tr>
                       <th><T sk="ORGANIZÁCIA" en="ORGANIZATION" /></th>
                      <th style={{textAlign: "center"}}> <T sk="AKCIE" en="ACTIONS" /></th>
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

        <form onSubmit={handleSubmit} className="organisation-form">
         <table className="organisation-table">
           <tbody>
            <tr>
           <td style={{ width: "70%" }}>
          <input
            type="text"
            value={newCategory}
            onChange={(e) => setNewCategory(e.target.value)}
           placeholder={
                    lang === "sk"
                      ? "Nová organizácia"
                      : "New organization"
                  }
          />
         </td>
         <td style={{ width: "30%" }}>
          <button
            className="btn"
            type="submit"
          >
           {lang === "sk"
                    ? "+ Pridať organizáciu"
                    : "+ Add organization"}
          </button>
            </td>
            </tr>
           </tbody>
           </table>
        </form>



        {error && <div className="error-text">{error}</div>}
      </div>
    </div>
  );
}
