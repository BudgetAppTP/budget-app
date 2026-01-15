import React, { useEffect, useMemo, useState } from "react";
import "./style/ekasa.css";
import T from "../i18n/T";
import { useLang } from "../i18n/LanguageContext";

const API_BASE = "/api";
const USER_ID = "1be32073-0b12-4a59-b9a1-77e0d3586a4c";


const CATEGORIES = ["📌 Bývanie", "📌 Jedlo", "Doprava", "Lieky", "Ostatné"];

export default function Ekasa() {
  const { lang } = useLang();

  const [currentDate, setCurrentDate] = useState(() => {
    const params = new URLSearchParams(window.location.search);
    const m = params.get("month"); // YYYY-MM
    return m ? new Date(m + "-01") : new Date();
  });

  const monthKeyFromDate = (d) => d.toISOString().slice(0, 7);

  const changeMonth = (offset) => {
    const newDate = new Date(currentDate);
    newDate.setMonth(currentDate.getMonth() + offset);
    const newKey = monthKeyFromDate(newDate);

    setCurrentDate(newDate);
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

  const safeNum = (v) => (Number.isFinite(Number(v)) ? Number(v) : 0);

  const formatDate = (iso) => {
    if (!iso) return "";
    const [y, m, d] = String(iso).split("-");
    if (!y || !m || !d) return String(iso);
    return `${d}.${m}.${y}`;
  };

  const receiptOrgTitle = (check) =>
    check?.tag || check?.description || (lang === "sk" ? "Neznáme" : "Unknown");

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
            ? "Nepodarilo sa načítať eKasa bločky."
            : "Failed to load eKasa checks.");
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

            const meta = it?.extra_metadata || {};
            const raw = meta.category || meta.Category || meta.cat || "";
            const cleaned =
              typeof raw === "string" && raw.trim() ? raw.trim() : "Jedlo";

            next[id] = cleaned.replace("📌 ", "");
          }
        }
        return next;
      });
    } catch (e) {
      console.error(e);
      setError(
        lang === "sk"
          ? "Chyba spojenia so serverom."
          : "Server connection error."
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




  const handleCategoryChange = (itemId, valueWithPin) => {
    const v = (valueWithPin || "").replace("📌 ", "");
    setItemCategory((prev) => ({ ...prev, [itemId]: v }));
  };

      const [ekasaReceiptId, setEkasaReceiptId] = useState("");
      const [ekasaError, setEkasaError] = useState("");
      const [ekasaSuccess, setEkasaSuccess] = useState("");
      const [ekasaLoading, setEkasaLoading] = useState(false);

      const handleImportEkasa = async () => {
      const rid = (ekasaReceiptId || "").trim();

      if (!rid) {
        setEkasaError(
          lang === "sk" ? "Zadajte ID bločku." : "Please enter receipt ID."
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
              ? "Import z eKasa zlyhal."
              : "Import from eKasa failed.");

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
            ? "Chyba spojenia so serverom."
            : "Server connection error."
        );
      } finally {
        setEkasaLoading(false);
      }
    };

      useEffect(() => {
        if (!ekasaSuccess) return;
        const t = setTimeout(() => setEkasaSuccess(""), 2500); // 2.5s
        return () => clearTimeout(t);
      }, [ekasaSuccess]);

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

      {!isLoading && error && <div className="error-text">{error}</div>}

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
            const total = safeNum(check.total_amount);

            return (
              <React.Fragment key={check.receipt_id || check.external_uid || idx}>
                {idx !== 0 && <div className="gold-line"></div>}

                <div className="table-card receipt-card">
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

                      <span className="receipt-id" title="external_uid / receiptId">
                        receiptId: {check.external_uid || "-"}
                      </span>
                    </div>
                  </div>


                  <div className="table-card">
                    <table>
                      <thead>
                        <tr>
                          <th style={{ textAlign: "left" }}><T sk="POLOŽKA" en="ITEM" /></th>
                          <th><T sk="KATEGÓRIA" en="CATEGORY" /></th>
                          <th className="price-col"><T sk="CENA/KS (€)" en="UNIT PRICE (€)" /></th>
                          <th><T sk="MNOŽSTVO" en="QUANTITY" /></th>
                          <th>VAT %</th>
                          <th className="price-col" style={{ textAlign: "right" }} ><T sk="SPOLU (€)" en="TOTAL (€)" /></th>
                        </tr>
                      </thead>

                      <tbody>
                        {items.length === 0 ? (
                          <tr>
                            <td colSpan={6} className="empty-row">
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

                            const selected = itemCategory[it.id] || "Jedlo";

                            return (
                              <tr key={it.id}>
                                <td className="item">{it.name || "-"}</td>

                                <td>
                                  <select
                                    className="category"
                                    value={
                                      CATEGORIES.find((c) => c.replace("📌 ", "") === selected) ||
                                      "📌 Jedlo"
                                    }
                                    onChange={(e) => handleCategoryChange(it.id, e.target.value)}
                                  >
                                    {CATEGORIES.map((c) => (
                                      <option
                                        key={c}
                                        value={c}
                                        className={c.includes("📌") ? "pinned" : ""}
                                      >
                                        {c.replace("📌 ", "")}
                                      </option>
                                    ))}
                                  </select>
                                </td>

                                <td className="amount">{unitPrice.toFixed(2)}</td>
                                <td className="quantity">{qty || "-"}</td>
                                <td className="vat">{vat}</td>
                                <td className="amount">{totalPrice.toFixed(2)}</td>
                              </tr>
                            );
                          })
                        )}
                      </tbody>
                        <tfoot>
                          <tr className="total-row">

                            <td colSpan={5} className="total-label">
                              <T sk="Spolu" en="Total" />
                            </td>

                            <td className="total-value">
                              {total.toFixed(2)}
                            </td>
                          </tr>
                        </tfoot>



                    </table>
                  </div>





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
                  <strong> <T sk="QR kód eKasa" en="QR Code eKasa" /></strong>
                  <p>

                    <T sk="Naskenujte QR kód z bločku"
                          en="Scan the QR code from your receipt"/>

                  </p>
                  <button><T sk="Nahrať QR" en="Upload QR" /></button>
                </div>
                <div className="import-card" draggable="true">
                  <strong><T sk="PDF alebo JSON" en="PDF or JSON" /></strong>
                  <p><T sk="Importujte súbor z eKasa"
                          en="Import an eKasa file"
                    /></p>
                  <button> <T sk="Vybrať súbor" en="Choose File" /></button>
                </div>

                <div className="import-card import-ekasa">
      <strong>
        <T sk="Import z eKasa" en="Import from eKasa" />
      </strong>

      <p>
        <T
          sk="Zadajte ID bločku (receiptId) z eKasa a importujte výdavok."
          en="Enter eKasa receipt ID (receiptId) to import an expense."
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
        placeholder={lang === "sk" ? "ID bločku (receiptId)" : "Receipt ID (receiptId)"}
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
