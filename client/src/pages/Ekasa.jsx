import React, { useEffect, useMemo, useState } from "react";
import "./style/ekasa.css";
import T from "../i18n/T";
import { useLang } from "../i18n/LanguageContext";

const API_BASE = "/api";
const USER_ID = "1be32073-0b12-4a59-b9a1-77e0d3586a4c";

export default function Ekasa() {
  const { lang } = useLang();

  const [highlightedExpenseId, setHighlightedExpenseId] = useState(() => {
    const params = new URLSearchParams(window.location.search);
    return params.get("expenseId");
  });

  const [currentDate, setCurrentDate] = useState(() => {
    const params = new URLSearchParams(window.location.search);
    const m = params.get("month");
    return m ? new Date(m + "-01") : new Date();
  });

  const monthKeyFromDate = (d) => d.toISOString().slice(0, 7);

  const changeMonth = (offset) => {
    const newDate = new Date(currentDate);
    newDate.setMonth(currentDate.getMonth() + offset);
    const newKey = monthKeyFromDate(newDate);

    setCurrentDate(newDate);
    setHighlightedExpenseId("");
    window.history.replaceState({}, "", `?month=${newKey}`);
  };

  const getMonthName = (date, lang) =>
    date.toLocaleDateString(lang === "sk" ? "sk-SK" : "en-US", {
      month: "long",
      year: "numeric",
    });

  const [checks, setChecks] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const [sortChecksBy, setSortChecksBy] = useState({
    field: "issue_date",
    order: "desc",
  });

  const [itemCategory, setItemCategory] = useState({});

const [editingReceiptId, setEditingReceiptId] = useState(null);

const [editingItemId, setEditingItemId] = useState(null);
const [itemEditBuffer, setItemEditBuffer] = useState({});

const [savingItemId, setSavingItemId] = useState(null);
const [deletingItemId, setDeletingItemId] = useState(null);

const [newItemReceiptId, setNewItemReceiptId] = useState(null);
const [newItem, setNewItem] = useState({
  name: "",
  category_id: "",
  quantity: 1,
  unit_price: "",
});
const [manualValidationError, setManualValidationError] = useState("");
const [addingItemReceiptId, setAddingItemReceiptId] = useState(null);

  const safeNum = (v) => (Number.isFinite(Number(v)) ? Number(v) : 0);

    const calculateReceiptTotal = (items) => {
    return (items || []).reduce((sum, it) => {
      const qty = safeNum(it.quantity);
      const unitPrice = safeNum(it.unit_price);
      const totalPrice = safeNum(it.total_price) || qty * unitPrice;

      return sum + totalPrice;
    }, 0);
  };

  const updateReceiptTotal = async (receiptId, newTotal) => {
    const res = await fetch(`${API_BASE}/receipts/${receiptId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        total_amount: newTotal,
      }),
    });

    const json = await res.json();

    if (!res.ok || json?.error) {
      throw new Error("Failed to update receipt total");
    }
  };

  const formatDate = (iso) => {
    if (!iso) return "";
    const [y, m, d] = String(iso).split("-");
    if (!y || !m || !d) return String(iso);
    return `${d}.${m}.${y}`;
  };

  const receiptOrgTitle = (check) =>
    check?.tag || check?.description || (lang === "sk" ? "Neznáme" : "Unknown");

  const isManualReceipt = (check) =>
    check?.extra_metadata?.manual === true ||
    check?.extra_metadata?.manual === "true";

  const fetchEkasaItems = async (dateForQuery = currentDate) => {
    setIsLoading(true);
    setError("");


    try {
      const year = dateForQuery.getFullYear();
      const month = dateForQuery.getMonth() + 1;

      const params = new URLSearchParams({
        year: String(year),
        month: String(month),
        user_id: USER_ID,
      });

      const res = await fetch(
        `${API_BASE}/receipts/ekasa-items?${params.toString()}`
      );
      const json = await res.json();

      if (!res.ok || json?.error) {
        const msg =
          json?.error?.message ||
          json?.data?.error ||
          (lang === "sk"
            ? "Nepodarilo sa načítať eKasa bločky"
            : "Failed to load eKasa checks");
        setError(msg);
        setChecks([]);
        return;
      }

      const data = json?.data ?? json;
      const list = Array.isArray(data?.checks) ? data.checks : [];
      setChecks(list);

      setItemCategory((prev) => {
        const next = { ...prev };

        for (const ch of list) {
          const items = Array.isArray(ch.items) ? ch.items : [];

          for (const it of items) {
            const id = it?.id;
            if (!id || next[id]) continue;

            next[id] = it?.category_id || "";
          }
        }

        return next;
      });
    } catch (e) {
      console.error(e);
      setError(
        lang === "sk"
          ? "Chyba spojenia so serverom"
          : "Server connection error"
      );
      setChecks([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    document.title = "BudgetApp · eKasa";
  }, []);

  useEffect(() => {
    fetchEkasaItems(currentDate);
  }, [currentDate, lang]);

  const [categories, setCategories] = useState([]);

  const fetchCategories = async () => {
    try {
      const res = await fetch(`/api/categories`);
      const json = await res.json();

      const data = json.data ?? json;
      const list = Array.isArray(data?.categories) ? data.categories : [];

      setCategories(
        list.map((c) => ({
          id: c.id,
          name: c.name,
          pinned: c.is_pinned === true || c.is_pinned === "true",
        }))
      );
    } catch (e) {
      console.error("Failed to load categories", e);
    }
  };

  useEffect(() => {
    fetchCategories();
  }, []);

  const sortedChecks = useMemo(() => {
    const list = [...checks];
    const { field, order } = sortChecksBy;
    const asc = order === "asc";

    list.sort((a, b) => {
      const av = (a?.[field] || "").toString();
      const bv = (b?.[field] || "").toString();
      return asc ? av.localeCompare(bv) : bv.localeCompare(av);
    });

    return list;
  }, [checks, sortChecksBy]);

  const totalMonth = useMemo(() => {
    return sortedChecks.reduce((sum, c) => sum + safeNum(c.total_amount), 0);
  }, [sortedChecks]);

  const handleCategoryChange = async (receiptId, itemId, categoryId) => {
    setItemCategory((prev) => ({ ...prev, [itemId]: categoryId }));

    try {
      const res = await fetch(`/api/receipts/${receiptId}/items/${itemId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          category_id: categoryId,
        }),
      });

      const data = await res.json();

      if (!res.ok) {
        console.error("Failed to update category", data);
      }
    } catch (err) {
      console.error("Failed to update category", err);
    }
  };

  const handleReceiptEditToggle = (check) => {
  const receiptId = check.receipt_id;

  if (editingReceiptId === receiptId) {
    setEditingReceiptId(null);
    setEditingItemId(null);
    setItemEditBuffer({});
    setNewItemReceiptId(null);
    setNewItem({
      name: "",
      category_id: "",
      quantity: 1,
      unit_price: "",
    });
    setError("");
    setManualValidationError("");
    return;
  }

  setEditingReceiptId(receiptId);
  setEditingItemId(null);
  setItemEditBuffer({});

  const defaultCategoryId =
    categories.find((c) => c.pinned)?.id || categories[0]?.id || "";

  setNewItemReceiptId(receiptId);
  setNewItem({
    name: "",
    category_id: defaultCategoryId,
    quantity: 1,
    unit_price: "",
  });

  setError("");
  setManualValidationError("");
};

  const handleManualItemEditToggle = (it) => {
  if (editingItemId === it.id) {
    setEditingItemId(null);
    setItemEditBuffer({});
    setError("");
    setManualValidationError("");
    return;
  }

  setEditingItemId(it.id);
  setItemEditBuffer({
    name: it.name || "",
    category_id: it.category_id || "",
    quantity: safeNum(it.quantity) || 1,
    unit_price: safeNum(it.unit_price),
  });
  setError("");
  setManualValidationError("");
};


  const handleManualItemSave = async (receiptId, itemId) => {
  const item = itemEditBuffer;

  if (!item?.name?.trim()) {
    setManualValidationError(
      lang === "sk"
        ? "Názov položky musí byť vyplnený"
        : "Item name must be filled"
    );
    return;
  }

  if (!item.category_id) {
    setManualValidationError(
      lang === "sk"
        ? "Kategória musí byť vybraná"
        : "Category must be selected"
    );
    return;
  }

  const quantity = safeNum(item.quantity);
  const unitPrice = safeNum(item.unit_price);

  if (quantity <= 0) {
    setManualValidationError(
      lang === "sk"
        ? "Množstvo musí byť väčšie ako 0"
        : "Quantity must be greater than 0"
    );
    return;
  }

  if (unitPrice < 0) {
    setManualValidationError(
      lang === "sk"
        ? "Cena nemôže byť záporná"
        : "Price cannot be negative"
    );
    return;
  }

  const totalPrice = quantity * unitPrice;

  setSavingItemId(itemId);

  setManualValidationError("");
  setError("");

  try {
    const res = await fetch(`${API_BASE}/receipts/${receiptId}/items/${itemId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        name: item.name.trim(),
        category_id: item.category_id,
        quantity,
        unit_price: unitPrice,
        total_price: totalPrice,
      }),
    });

    const json = await res.json();

    if (!res.ok || json?.error) {
      setError(
        lang === "sk"
          ? "Nepodarilo sa upraviť položku"
          : "Failed to update item"
      );
      return;
    }

    const currentReceipt = checks.find((c) => c.receipt_id === receiptId);

    const updatedItems = (currentReceipt?.items || []).map((it) =>
      it.id === itemId
        ? {
            ...it,
            name: item.name.trim(),
            category_id: item.category_id,
            quantity,
            unit_price: unitPrice,
            total_price: totalPrice,
          }
        : it
    );

    const newReceiptTotal = calculateReceiptTotal(updatedItems);

    await updateReceiptTotal(receiptId, newReceiptTotal);

    setChecks((prev) =>
      prev.map((c) =>
        c.receipt_id === receiptId
          ? {
              ...c,
              total_amount: newReceiptTotal,
              items: updatedItems,
            }
          : c
      )
    );

    setItemCategory((prev) => ({
      ...prev,
      [itemId]: item.category_id,
    }));

    setEditingItemId(null);
    setItemEditBuffer({});
  } catch (err) {
    console.error(err);
    setError(
      lang === "sk"
        ? "Chyba spojenia pri úprave položky"
        : "Connection error while updating item"
    );
  } finally {
    setSavingItemId(null);
  }
};

  const handleManualItemDelete = async (receiptId, itemId) => {
  setDeletingItemId(itemId);
  setError("");

  try {
    const currentReceipt = checks.find((c) => c.receipt_id === receiptId);
    const remainingItems = (currentReceipt?.items || []).filter(
      (it) => it.id !== itemId
    );

    const res = await fetch(`${API_BASE}/receipts/${receiptId}/items/${itemId}`, {
      method: "DELETE",
    });

    const json = await res.json();

    if (!res.ok || json?.error) {
      setError(
        lang === "sk"
          ? "Nepodarilo sa vymazať položku"
          : "Failed to delete item"
      );
      return;
    }

    if (remainingItems.length === 0) {
      const receiptRes = await fetch(`${API_BASE}/receipts/${receiptId}`, {
        method: "DELETE",
      });

      const receiptJson = await receiptRes.json();

      if (!receiptRes.ok || receiptJson?.error) {
        setError(
          lang === "sk"
            ? "Položka bola vymazaná, ale nepodarilo sa vymazať prázdny výdavok"
            : "Item was deleted, but failed to delete empty expense"
        );
        return;
      }

      setChecks((prev) => prev.filter((c) => c.receipt_id !== receiptId));

      setEditingReceiptId(null);
      setEditingItemId(null);
      setItemEditBuffer({});
      setNewItemReceiptId(null);
      setNewItem({
        name: "",
        category_id: "",
        quantity: 1,
        unit_price: "",
      });

      return;
    }

    const newReceiptTotal = calculateReceiptTotal(remainingItems);

await updateReceiptTotal(receiptId, newReceiptTotal);

    setChecks((prev) =>
      prev.map((c) =>
        c.receipt_id === receiptId
          ? {
              ...c,
              total_amount: newReceiptTotal,
              items: remainingItems,
            }
          : c
      )
    );

    if (editingItemId === itemId) {
      setEditingItemId(null);
      setItemEditBuffer({});
    }
  } catch (err) {
    console.error(err);
    setError(
      lang === "sk"
        ? "Chyba spojenia pri mazaní položky"
        : "Connection error while deleting item"
    );
  } finally {
    setDeletingItemId(null);
  }
};

  const handleManualItemAdd = async (receiptId) => {
  const name = newItem.name.trim();
  const categoryId = newItem.category_id;

  const quantityRaw = newItem.quantity;
  const unitPriceRaw = newItem.unit_price;

  const quantity = safeNum(quantityRaw);
  const unitPrice = safeNum(unitPriceRaw);

  // name + quantity + price must be filled
  if (!name || quantityRaw === "" || unitPriceRaw === "") {
    setManualValidationError(
      lang === "sk"
        ? "Všetky polia musia byť vyplnené!"
        : "All fields must be filled"
    );
    return;
  }

  // category separately
  if (!categoryId) {
    setManualValidationError(
      lang === "sk"
        ? "Kategória musí byť vybraná"
        : "Category must be selected"
    );
    return;
  }

  // quantity cannot be negative / zero
  if (quantity <= 0) {
    setManualValidationError(
      lang === "sk"
        ? "Množstvo musí byť väčšie ako 0"
        : "Quantity must be greater than 0"
    );
    return;
  }

  // price cannot be negative
  if (unitPrice < 0) {
    setManualValidationError(
      lang === "sk"
        ? "Cena nesmie byť záporná"
        : "Price cannot be negative"
    );
    return;
  }

  const totalPrice = quantity * unitPrice;

  setAddingItemReceiptId(receiptId);
  setManualValidationError("");
  setError("");

  try {
    const res = await fetch(`${API_BASE}/receipts/${receiptId}/items`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        name,
        category_id: categoryId,
        quantity,
        unit_price: unitPrice,
        total_price: totalPrice,
      }),
    });

    const json = await res.json();

    if (!res.ok || json?.error) {
      setError(
        lang === "sk"
          ? "Nepodarilo sa pridať položku"
          : "Failed to add item"
      );
      return;
    }

    const currentReceipt = checks.find((c) => c.receipt_id === receiptId);

      const updatedItems = [
        ...(currentReceipt?.items || []),
        {
          name,
          category_id: categoryId,
          quantity,
          unit_price: unitPrice,
          total_price: totalPrice,
        },
      ];

      const newReceiptTotal = calculateReceiptTotal(updatedItems);

      await updateReceiptTotal(receiptId, newReceiptTotal);


    await fetchEkasaItems(currentDate);

    const defaultCategoryId =
      categories.find((c) => c.pinned)?.id || categories[0]?.id || "";

    setNewItem({
      name: "",
      category_id: defaultCategoryId,
      quantity: 1,
      unit_price: "",
    });
  } catch (err) {
    console.error(err);
    setError(
      lang === "sk"
        ? "Chyba spojenia pri pridávaní položky"
        : "Connection error while adding item"
    );
  } finally {
    setAddingItemReceiptId(null);
  }
};

  const [ekasaReceiptId, setEkasaReceiptId] = useState("");
  const [ekasaError, setEkasaError] = useState("");
  const [ekasaSuccess, setEkasaSuccess] = useState("");
  const [ekasaLoading, setEkasaLoading] = useState(false);

  const handleImportEkasa = async () => {
    const rid = (ekasaReceiptId || "").trim();

    if (!rid) {
      setEkasaError(
        lang === "sk" ? "Zadajte ID bločku" : "Please enter receipt ID"
      );
      return;
    }

    setEkasaError("");
    setEkasaLoading(true);

    try {
      const res = await fetch(`${API_BASE}/receipts/import-ekasa`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          receiptId: rid,
          user_id: USER_ID,
        }),
      });

      const json = await res.json();

      if (!res.ok || json?.error) {
        const backendMsg =
          json?.error?.message ||
          json?.error?.details?.error ||
          json?.data?.error ||
          (lang === "sk"
            ? "Import z eKasa zlyhal"
            : "Import from eKasa failed");

        setEkasaError(backendMsg);
        return;
      }

      setEkasaReceiptId("");
      setEkasaError("");
      setEkasaSuccess(
        lang === "sk" ? "Bloček bol importovaný ✔" : "Receipt imported ✔"
      );
    } catch (err) {
      console.error(err);
      setEkasaError(
        lang === "sk"
          ? "Chyba spojenia so serverom"
          : "Server connection error"
      );
    } finally {
      setEkasaLoading(false);
    }
  };

  useEffect(() => {
    if (!ekasaSuccess) return;
    const t = setTimeout(() => setEkasaSuccess(""), 2500);
    return () => clearTimeout(t);
  }, [ekasaSuccess]);

  useEffect(() => {
    if (!highlightedExpenseId || isLoading || checks.length === 0) return;

    const el = document.getElementById(`receipt-${highlightedExpenseId}`);

    if (el) {
      setTimeout(() => {
        el.scrollIntoView({
          behavior: "smooth",
          block: "center",
        });
      }, 100);
    }
  }, [highlightedExpenseId, isLoading, checks]);

  return (
    <div className="wrap ekasa">
      <div className="page-title">
        🧾 <T sk="eKasa" en="eKasa" />
        <div className="gold-line"></div>
      </div>

      <div className="page-header">
        <div className="month-nav">
          <button id="prev-month" onClick={() => changeMonth(-1)}>
            ◀
          </button>
          <h2>{getMonthName(currentDate, lang)}</h2>
          <button id="next-month" onClick={() => changeMonth(1)}>
            ▶
          </button>
        </div>

        <div className="summary">
          <span>
            <T sk="Spolu tento mesiac" en="Total this month" />:
          </span>
          <span className="value">
            {totalMonth.toFixed(2).replace(".", ",")} €
          </span>
        </div>
      </div>

      {isLoading && (
        <div className="loading">
          {lang === "sk" ? "Načítavam eKasa..." : "Loading eKasa..."}
        </div>
      )}



      {!isLoading && !error && sortedChecks.length === 0 && (
        <div className="empty-row">
          {lang === "sk"
            ? "Žiadne eKasa bločky pre tento mesiac"
            : "No eKasa checks for this month"}
        </div>
      )}

      {!isLoading && !error && sortedChecks.length > 0 && (
        <div className="ekasa-checks">
          {sortedChecks.map((check, idx) => {
            const items = Array.isArray(check.items) ? check.items : [];
            const org = receiptOrgTitle(check);
            const dateText = formatDate(check.issue_date);
            const itemsCount = items.length;
            const total =
              items.length > 0
                ? items.reduce(
                    (sum, it) =>
                      sum +
                      (safeNum(it.total_price) ||
                        safeNum(it.unit_price) * safeNum(it.quantity)),
                    0
                  )
                : safeNum(check.total_amount);

            const isManual = isManualReceipt(check);
            const isEditingManual =
              isManual && editingReceiptId === check.receipt_id;

            return (
              <React.Fragment key={check.receipt_id || check.external_uid || idx}>
                {idx !== 0 && <div className="gold-line"></div>}

                <div
                  id={`receipt-${check.receipt_id}`}
                  className={`table-card receipt-card ${
                    highlightedExpenseId &&
                    String(highlightedExpenseId) === String(check.receipt_id)
                      ? "highlighted-receipt"
                      : ""
                  } ${isEditingManual ? "manual-editing" : ""}`}
                >
                  <div className="receipt-header">
                    <div className="receipt-org">{org}</div>

                    <div className="receipt-meta">
                      <span className="receipt-pill">
                        <span className="receipt-pill-label">
                          <T sk="Dátum" en="Date" />:
                        </span>
                        <b>{dateText || "-"}</b>
                      </span>

                      <span className="receipt-pill">
                        <span className="receipt-pill-label">
                          <T sk="Položky" en="Items" />:
                        </span>
                        <b>{itemsCount}</b>
                      </span>


                         <div className="receipt-actions-right">
                      <span className="receipt-id" title="external_uid / receiptId">
                        {isManual ? "manual" : `receiptId: ${check.external_uid || "-"}`}
                      </span>

                        {isManual && (
                            <span
                              className="edit-button manual-edit-btn"
                              onClick={() => handleReceiptEditToggle(check)}
                              style={{ cursor: "pointer" }}
                            >
                              {isEditingManual
                                ? lang === "sk"
                                  ? "✔ Hotovo"
                                  : "✔ Done"
                                : lang === "sk"
                                ? "✏️ Upraviť"
                                : "✏️ Edit"}
                            </span>
                          )}
                       </div>

                    </div>
                  </div>

                  <div className="table-card">
                    <table>
                     <thead>
                      <tr>
                        <th style={{ textAlign: "left" }}>
                          <T sk="POLOŽKA" en="ITEM" />
                        </th>

                        <th>
                          <T sk="KATEGÓRIA" en="CATEGORY" />
                        </th>

                        <th className="price-col">
                          <T sk="CENA/KS (€)" en="UNIT PRICE (€)" />
                        </th>

                        <th>
                          <T sk="MNOŽSTVO" en="QUANTITY" />
                        </th>


                        {isEditingManual ? (
                          <th className="actions-col" style={{ textAlign: "center" }}>
                            <T sk="AKCIE" en="ACTIONS" />
                          </th>
                        ) : (
                          <>
                            <th>VAT %</th>
                            <th className="price-col" style={{ textAlign: "right" }}>
                              <T sk="SPOLU (€)" en="TOTAL (€)" />
                            </th>
                          </>
                        )}
                      </tr>
                    </thead>

                      <tbody>
                        {items.length === 0 ? (
                          <tr>
                            <td
                              colSpan={6}
                              className="empty-row"
                            >
                              {lang === "sk"
                                ? "Žiadne položky v tomto bločku."
                                : "No items in this check."}
                            </td>
                          </tr>
                        ) : (
                          items.map((it) => {
                            const meta = it?.extra_metadata || {};
                            const vat =
                              meta.vat ||
                              meta.VAT ||
                              meta.vat_percent ||
                              meta.vatPercent ||
                              "-";

                            const qty = safeNum(it.quantity);
                            const unitPrice = safeNum(it.unit_price);
                            const totalPrice =
                              safeNum(it.total_price) || unitPrice * qty;

                            const defaultCategoryId =
                              categories.find((c) => c.pinned)?.id ||
                              categories[0]?.id ||
                              "";
                            const selected = itemCategory[it.id] || defaultCategoryId;

                           const isEditingItem = editingItemId === it.id;
                           const itemData = isEditingItem ? itemEditBuffer : it;

                           const rowStyle = isEditingItem
                            ? {
                                backgroundColor: "#fff8e1",
                                transition: "background-color 0.3s ease",
                              }
                            : {};

                            const editedQty = safeNum(itemData.quantity) || 1;
                            const editedUnitPrice = safeNum(itemData.unit_price);
                            const editedTotal = editedQty * editedUnitPrice;

                            return (
                              <tr
                                  key={it.id}
                              style={rowStyle}
                              className={isEditingItem ? "editing" : ""}
                              >
                              <td>
                                {isEditingItem ? (
                                  <textarea
                                    value={itemData.name || ""}
                                    onChange={(e) => {
                                      const el = e.target;
                                      el.style.height = "auto";
                                      el.style.height = el.scrollHeight + "px";

                                      setItemEditBuffer({
                                        ...itemEditBuffer,
                                        name: el.value,
                                      });
                                    }}
                                    rows={1}
                                  />
                                ) : (
                                  it.name || "-"
                                )}
                              </td>

                              <td >
                                <select
                                  className="category"
                                  value={isEditingItem ? itemData.category_id || "" : selected}
                                  onChange={(e) => {
                                    if (isEditingItem) {
                                      setItemEditBuffer({
                                        ...itemEditBuffer,
                                        category_id: e.target.value,
                                      });
                                    } else {
                                      handleCategoryChange(check.receipt_id, it.id, e.target.value);
                                    }
                                  }}
                                >
                                  <option value="" disabled>
                                    {lang === "sk" ? "Kategória" : "Category"}
                                  </option>

                                  {categories.map((c) => (
                                    <option key={c.id} value={c.id}>
                                      {c.pinned ? "📌 " : ""}
                                      {c.name}
                                    </option>
                                  ))}
                                </select>
                              </td>

                              <td style={{ textAlign: "center" }}>
                                {isEditingItem ? (
                                  <input
                                    type="number"
                                    step="0.01"
                                    value={itemData.unit_price ?? ""}
                                    onChange={(e) =>
                                      setItemEditBuffer({
                                        ...itemEditBuffer,
                                        unit_price: e.target.value,
                                      })
                                    }
                                  />
                                ) : (
                                  unitPrice.toFixed(2)
                                )}
                              </td>

                              <td style={{ textAlign: "center" }}>
                                {isEditingItem ? (
                                  <input
                                    type="number"
                                    step="1"
                                    value={itemData.quantity ?? 1}
                                    onChange={(e) =>
                                      setItemEditBuffer({
                                        ...itemEditBuffer,
                                        quantity: e.target.value,
                                      })
                                    }
                                  />
                                ) : (
                                  qty || "-"
                                )}
                              </td>


                              {isEditingManual ? (
                              <td>
                                <div className="actions">
                                  {!isEditingItem && (
                                    <span
                                      className="action-icon delete"
                                      onClick={() => handleManualItemDelete(check.receipt_id, it.id)}
                                      title={lang === "sk" ? "Vymazať" : "Delete"}
                                      style={{
                                        opacity: deletingItemId === it.id ? 0.4 : 1,
                                        pointerEvents: deletingItemId === it.id ? "none" : "auto",
                                      }}
                                    >
                                      🗑️
                                    </span>
                                  )}

                                  <span
                                    className="action-icon edit"
                                    onClick={() =>
                                      isEditingItem
                                        ? handleManualItemSave(check.receipt_id, it.id)
                                        : handleManualItemEditToggle(it)
                                    }
                                    title={
                                      isEditingItem
                                        ? lang === "sk"
                                          ? "Uložiť položku"
                                          : "Save item"
                                        : lang === "sk"
                                        ? "Upraviť položku"
                                        : "Edit item"
                                    }
                                    style={{
                                      opacity: savingItemId === it.id ? 0.5 : 1,
                                    }}
                                  >
                                    {isEditingItem ? "✔" : "✏️"}
                                  </span>
                                </div>
                              </td>
                            ) : (
                              <>
                                <td className="vat">{vat}</td>
                                <td className="amount">{totalPrice.toFixed(2)}</td>
                              </>
                            )}




                            </tr>
                            );
                          })
                        )}
                      </tbody>

                      <tfoot>
                        <tr className="total-row">
                          <td colSpan={isEditingManual ? 4 : 5} className="total-label">
                              <T sk="Spolu" en="Total" />
                            </td>

                            <td className="total-value">{total.toFixed(2)}</td>
                        </tr>
                      </tfoot>
                    </table>


                  </div>
                    {isEditingManual && (
  <form
    className="ekasa-item-form"
    onSubmit={(e) => {
      e.preventDefault();
      handleManualItemAdd(check.receipt_id);
    }}
  >
    <table className="expense-table">
      <tbody>
        <tr>
          <td style={{ width: "30%" }}>
            <input
              type="text"
              placeholder={lang === "sk" ? "Názov položky" : "Item name"}
              value={newItemReceiptId === check.receipt_id ? newItem.name : ""}
              onChange={(e) =>
                setNewItem({
                  ...newItem,
                  name: e.target.value,
                })
              }
            />
          </td>

          <td style={{ width: "25%" }}>
            <select
              className="category"
              value={
                newItemReceiptId === check.receipt_id
                  ? newItem.category_id
                  : ""
              }
              onChange={(e) =>
                setNewItem({
                  ...newItem,
                  category_id: e.target.value,
                })
              }
            >
              <option value="" disabled>
                {lang === "sk" ? "Kategória" : "Category"}
              </option>

              {categories.map((c) => (
                <option key={c.id} value={c.id}>
                  {c.pinned ? "📌 " : ""}
                  {c.name}
                </option>
              ))}
            </select>
          </td>

          <td style={{ width: "16%" }}>
            <input
              type="number"
              step="0.01"
              placeholder={lang === "sk" ? "Cena/ks" : "Unit price"}
              value={
                newItemReceiptId === check.receipt_id
                  ? newItem.unit_price
                  : ""
              }
              onChange={(e) =>
                setNewItem({
                  ...newItem,
                  unit_price: e.target.value,
                })
              }
            />
          </td>

          <td style={{ width: "14%" }}>
            <input
              type="number"
              step="1"
              min="1"
              placeholder={lang === "sk" ? "Množstvo" : "Quantity"}
              value={
                newItemReceiptId === check.receipt_id
                  ? newItem.quantity
                  : 1
              }
              onChange={(e) =>
                setNewItem({
                  ...newItem,
                  quantity: e.target.value,
                })
              }
            />
          </td>

          <td style={{ width: "15%", textAlign: "center" }}>
            <button
              type="submit"
              className="btn"
              disabled={addingItemReceiptId === check.receipt_id}
            >
              {addingItemReceiptId === check.receipt_id
                ? lang === "sk"
                  ? "Pridávam..."
                  : "Adding..."
                : lang === "sk"
                ? "+ Pridať položku"
                : "+ Add item"}
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </form>
)}
                    {isEditingManual && manualValidationError && (
  <div className="error-text">
    {manualValidationError}
  </div>
)}
                </div>
              </React.Fragment>
            );
          })}
        </div>
      )}

      <div className="page-title" style={{ marginTop: "30px" }}>
        📂 <T sk="Import eKasa" en="Import eKasa" />
        <div className="gold-line"></div>
      </div>

      <div className="panel">
        <div className="import-card" draggable="true">
          <strong>
            <T sk="QR kód eKasa" en="QR Code eKasa" />
          </strong>
          <p>
            <T
              sk="Naskenujte QR kód z bločku"
              en="Scan the QR code from your receipt"
            />
          </p>
          <button>
            <T sk="Nahrať QR" en="Upload QR" />
          </button>
        </div>

        <div className="import-card" draggable="true">
          <strong>
            <T sk="PDF alebo JSON" en="PDF or JSON" />
          </strong>
          <p>
            <T sk="Importujte súbor z eKasa" en="Import an eKasa file" />
          </p>
          <button>
            <T sk="Vybrať súbor" en="Choose File" />
          </button>
        </div>

        <div className="import-card import-ekasa">
          <strong>
            <T sk="Import z eKasa" en="Import from eKasa" />
          </strong>

          <p>
            <T
              sk="Zadajte ID bločku (receiptId) z eKasa a importujte výdavok"
              en="Enter eKasa receipt ID (receiptId) to import an expense"
            />
          </p>

          <input
            type="text"
            value={ekasaReceiptId}
            onChange={(e) => {
              setEkasaReceiptId(e.target.value);
              setEkasaError("");
              setEkasaSuccess("");
            }}
            placeholder={
              lang === "sk" ? "ID bločku (receiptId)" : "Receipt ID (receiptId)"
            }
            style={{
              border: ekasaError ? "1px solid #e53935" : "1px solid #d0d0d0",
            }}
          />

          <button
            type="button"
            onClick={handleImportEkasa}
            disabled={ekasaLoading}
            style={{
              cursor: ekasaLoading ? "not-allowed" : "pointer",
              opacity: ekasaLoading ? 0.7 : 1,
            }}
          >
            {ekasaLoading
              ? lang === "sk"
                ? "Importujem..."
                : "Importing..."
              : lang === "sk"
              ? "Importovať"
              : "Import"}
          </button>

          {ekasaError && (
            <div style={{ marginTop: "8px", color: "#e53935", fontSize: "13px" }}>
              {ekasaError}
            </div>
          )}

          {ekasaSuccess && (
            <div style={{ marginTop: "8px", color: "#2e7d32", fontSize: "13px" }}>
              {ekasaSuccess}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}