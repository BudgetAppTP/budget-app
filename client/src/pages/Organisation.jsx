import React, { useEffect, useMemo, useState } from "react";
import "./style/organisation.css";
import T from "../i18n/T";
import { useLang } from "../i18n/LanguageContext";


const API_BASE = "/api";
const USER_ID = "1be32073-0b12-4a59-b9a1-77e0d3586a4c";

async function apiFetch(path, { method = "GET", body } = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: {
      Accept: "application/json",
      ...(body ? { "Content-Type": "application/json" } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
    credentials: "include",
  });

  let json = null;
  try {
    json = await res.json();
  } catch {
  }

  const data = json?.data ?? null;
  const err = json?.error ?? null;


  if (!res.ok) {
    const message =
      err?.message ||
      data?.error ||
      json?.message ||
      `Request failed (${res.status})`;
    return { ok: false, status: res.status, data, error: { message } };
  }


  if (err) {
    const message = err?.message || data?.error || "Unknown error";
    return { ok: false, status: res.status, data, error: { message } };
  }

  return { ok: true, status: res.status, data, error: null };
}

export default function Needs() {
  const { lang } = useLang();

  useEffect(() => {
    document.title = "BudgetApp · Organizácie";
  }, []);

  const [selectedCategory, setSelectedCategory] = useState("prijmy");


  const [incomeCategories, setIncomeCategories] = useState([]);
  const [expenseCategories, setExpenseCategories] = useState([]);


  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [newCategory, setNewCategory] = useState("");

  const [editingId, setEditingId] = useState(null);
  const [editBuffer, setEditBuffer] = useState({});

  const categories = useMemo(() => {
    return selectedCategory === "prijmy" ? incomeCategories : expenseCategories;
  }, [selectedCategory, incomeCategories, expenseCategories]);


  const currentTypeForApi = selectedCategory === "prijmy" ? "income" : "expense";

  const emptyRowText = useMemo(() => {
    if (lang === "sk") {
      return selectedCategory === "prijmy"
        ? "Žiadne organizácie (tagy) pre príjmy"
        : "Žiadne organizácie (tagy) pre výdavky";
    }
    return selectedCategory === "prijmy"
      ? "No income organizations (tags)"
      : "No expense organizations (tags)";
  }, [lang, selectedCategory]);

  const reloadLists = async () => {
    setLoading(true);
    setError("");

    const inc = await apiFetch("/tags/income");
    if (inc.ok) setIncomeCategories(inc.data?.tags || []);

    const exp = await apiFetch("/tags/expense");
    if (exp.ok) setExpenseCategories(exp.data?.tags || []);

    if (!inc.ok || !exp.ok) {
      setError(
        inc.error?.message ||
          exp.error?.message ||
          (lang === "sk" ? "Chyba pri načítaní tagov." : "Error loading tags.")
      );
    }

    setLoading(false);
  };

  useEffect(() => {
    let alive = true;
    (async () => {
      setLoading(true);
      setError("");

      const inc = await apiFetch("/tags/income");
      if (!alive) return;
      if (!inc.ok) {
        setError(inc.error?.message || (lang === "sk" ? "Nepodarilo sa načítať príjmové tagy." : "Failed to load income tags."));
        setLoading(false);
        return;
      }
      setIncomeCategories(inc.data?.tags || []);

      const exp = await apiFetch("/tags/expense");
      if (!alive) return;
      if (!exp.ok) {
        setError(exp.error?.message || (lang === "sk" ? "Nepodarilo sa načítať výdavkové tagy." : "Failed to load expense tags."));
        setLoading(false);
        return;
      }
      setExpenseCategories(exp.data?.tags || []);
      setLoading(false);
    })();

    return () => {
      alive = false;
    };
  }, []);
  const handleSubmit = async (e) => {
    e.preventDefault();

    const name = (newCategory || "").trim();
    if (!name) {
      setError(
        lang === "sk" ? "Zadajte názov organizácie!" : "Enter the organization name!"
      );
      return;
    }

    setError("");

    const resp = await apiFetch("/tags", {
      method: "POST",
      body: {
        user_id: USER_ID,
        name,
        type: currentTypeForApi,
      },
    });

    if (!resp.ok) {
      setError(resp.error?.message || (lang === "sk" ? "Nepodarilo sa vytvoriť tag." : "Failed to create tag."));
      return;
    }

    setNewCategory("");
    await reloadLists();
  };


  const handleDelete = async (id) => {
    setError("");

    const resp = await apiFetch(`/tags/${id}`, { method: "DELETE" });
    if (!resp.ok) {
      setError(resp.error?.message || (lang === "sk" ? "Nepodarilo sa vymazať tag." : "Failed to delete tag."));
      return;
    }


    if (selectedCategory === "prijmy") {
      setIncomeCategories((prev) => prev.filter((c) => c.id !== id));
    } else {
      setExpenseCategories((prev) => prev.filter((c) => c.id !== id));
    }
  };


  const handleEditToggle = async (id) => {
    setError("");


    if (editingId === id) {
      const name = (editBuffer.name || "").trim();
      if (!name) {
        setError(
          lang === "sk"
            ? "Názov kategórie nesmie byť prázdny!"
            : "Category name cannot be empty!"
        );
        return;
      }

      const resp = await apiFetch(`/tags/${id}`, {
        method: "PUT",
        body: { name },
      });

      if (!resp.ok) {
        setError(resp.error?.message || (lang === "sk" ? "Nepodarilo sa uložiť zmeny." : "Failed to save changes."));
        return;
      }

      if (selectedCategory === "prijmy") {
        setIncomeCategories((prev) =>
          prev.map((c) => (c.id === id ? { ...c, name } : c))
        );
      } else {
        setExpenseCategories((prev) =>
          prev.map((c) => (c.id === id ? { ...c, name } : c))
        );
      }

      setEditingId(null);
      setEditBuffer({});
      return;
    }


    const cat = categories.find((c) => c.id === id);
    if (!cat) return;

    setEditingId(id);
    setEditBuffer({ ...cat });
  };

  const handleCategorySwitch = (e) => {
    setSelectedCategory(e.target.value);
    setEditingId(null);
    setEditBuffer({});
    setError("");
  };

  return (
    <div className="wrap organisation">
      <div>
        <div className="page-title">
          <T sk="🏛️ Organizácie" en="🏛️ Organizations" />
        </div>

        <div className="choice-box">
          <p>
            <T sk="Zobraziť organizácie:" en="Show organizations:" />
          </p>

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

        {loading && (
          <div style={{ margin: "10px 0", opacity: 0.8 }}>
            {lang === "sk" ? "Načítavam..." : "Loading..."}
          </div>
        )}

        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>
                  <T sk="ORGANIZÁCIA" en="ORGANIZATION" />
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
                          value={data.name || ""}
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

              {!loading && categories.length === 0 && (
                <tr>
                  <td colSpan={2} style={{ opacity: 0.75, padding: "12px" }}>
                    {emptyRowText}
                  </td>
                </tr>
              )}
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
                    placeholder={lang === "sk" ? "Nová organizácia" : "New organization"}
                  />
                </td>
                <td style={{ width: "30%" }}>
                  <button className="btn" type="submit" disabled={loading}>
                    {lang === "sk" ? "+ Pridať organizáciu" : "+ Add organization"}
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
