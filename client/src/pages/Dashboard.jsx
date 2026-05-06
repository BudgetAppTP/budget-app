import React, { useEffect, useRef, useState } from "react";
import "./style/dashboard.css";
import { Link } from "react-router-dom";
import { Html5Qrcode } from "html5-qrcode";
import { useLang } from "../i18n/LanguageContext";
import T from "../i18n/T";

const API_BASE = "/api";
const USER_ID = "1be32073-0b12-4a59-b9a1-77e0d3586a4c";

export default function Dashboard() {
  const { lang, setLang } = useLang();
  const scannerRef = useRef(null);

  useEffect(() => {
    document.title = "BudgetApp · Dashboard";
  }, []);

  useEffect(() => {
    document.body.classList.add("dashboard-body");
    return () => document.body.classList.remove("dashboard-body");
  }, []);

  const [ekasaReceiptId, setEkasaReceiptId] = useState("");
  const [ekasaError, setEkasaError] = useState("");
  const [ekasaSuccess, setEkasaSuccess] = useState("");
  const [ekasaLoading, setEkasaLoading] = useState(false);

  const [qrFile, setQrFile] = useState(null);
  const [qrLoading, setQrLoading] = useState(false);
  const [qrError, setQrError] = useState("");
  const [qrSuccess, setQrSuccess] = useState("");

  const [scannerOpen, setScannerOpen] = useState(false);
  const [scannerLoading, setScannerLoading] = useState(false);
  const [lastScanned, setLastScanned] = useState("");

  const importReceiptById = async (receiptId) => {
    setQrLoading(true);
    setQrError("");
    setQrSuccess("");

    try {
      const importRes = await fetch(`${API_BASE}/receipts/import-ekasa`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          receiptId,
          user_id: USER_ID,
        }),
      });

      const importJson = await importRes.json();

      if (!importRes.ok || importJson?.error) {
        const errorMsg =
          importJson?.error?.message ||
          importJson?.error ||
          (lang === "sk" ? "Import zlyhal." : "Import failed.");
        setQrError(errorMsg);
        return false;
      }

      setQrSuccess(
        lang === "sk"
          ? "Bloček bol úspešne importovaný ✓"
          : "Receipt imported successfully ✓"
      );
      return true;
    } catch (err) {
      console.error(err);
      setQrError(lang === "sk" ? "Chyba spojenia." : "Connection error.");
      return false;
    } finally {
      setQrLoading(false);
    }
  };

  const handleQrFileChange = (e) => {
    setQrFile(e.target.files[0]);
    setQrError("");
    setQrSuccess("");
  };

  const handleQrImport = async () => {
    if (!qrFile) {
      setQrError(
        lang === "sk" ? "Vyberte obrázok QR kódu." : "Select a QR code image."
      );
      return;
    }

    setQrLoading(true);
    setQrError("");
    setQrSuccess("");

    const formData = new FormData();
    formData.append("image", qrFile);

    try {
      const extractRes = await fetch(`${API_BASE}/import-qr/extract-id`, {
        method: "POST",
        body: formData,
      });

      const extractJson = await extractRes.json();

      if (!extractRes.ok || extractJson?.error) {
        setQrError(
          extractJson?.error ||
            (lang === "sk"
              ? "Nepodarilo sa extrahovať ID."
              : "Failed to extract ID.")
        );
        return;
      }

      const receiptId = extractJson.data.receiptId;
      const ok = await importReceiptById(receiptId);

      if (ok) {
        setQrFile(null);
        const fileInput = document.querySelector('input[type="file"]');
        if (fileInput) fileInput.value = null;
      }
    } catch (err) {
      console.error(err);
      setQrError(lang === "sk" ? "Chyba spojenia." : "Connection error.");
    } finally {
      setQrLoading(false);
    }
  };

  const stopScanner = async () => {
    if (!scannerRef.current) return;

    try {
      const state = scannerRef.current.getState?.();
      if (state === 2 || state === 3) {
        await scannerRef.current.stop();
      }
    } catch (err) {
      console.warn("Scanner stop warning:", err);
    }

    try {
      await scannerRef.current.clear();
    } catch (err) {
      console.warn("Scanner clear warning:", err);
    }

    scannerRef.current = null;
  };

  const startScanner = async () => {
    setQrError("");
    setQrSuccess("");
    setScannerLoading(true);

    try {
      const scanner = new Html5Qrcode("qr-reader");
      scannerRef.current = scanner;

      await scanner.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: 220 },
        async (decodedText) => {
          const scannedValue = decodedText.trim();

          if (!scannedValue || scannedValue === lastScanned) return;
          setLastScanned(scannedValue);

          setQrLoading(true);
          setQrError("");
          setQrSuccess("");

          const ok = await importReceiptById(scannedValue);

          setQrLoading(false);

          if (ok) {
            await stopScanner();
            setScannerOpen(false);
          } else {
            setQrError(
              lang === "sk"
                ? "QR neobsahuje platný identifikátor dokladu."
                : "QR does not contain a valid receipt identifier."
            );

            setTimeout(() => {
              setLastScanned("");
            }, 1500);
          }
        },
        () => {}
      );
    } catch (err) {
      console.error(err);
      setQrError(
        lang === "sk"
          ? "Nepodarilo sa spustiť kameru."
          : "Unable to start the camera."
      );
      setScannerOpen(false);
    } finally {
      setScannerLoading(false);
    }
  };

  const toggleScanner = async () => {
    if (scannerOpen) {
      await stopScanner();
      setScannerOpen(false);
    } else {
      setScannerOpen(true);
    }
  };

  useEffect(() => {
    if (scannerOpen) {
      startScanner();
    } else {
      stopScanner();
    }

    return () => {
      stopScanner();
    };
  }, [scannerOpen]);

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
    const t = setTimeout(() => setEkasaSuccess(""), 2500);
    return () => clearTimeout(t);
  }, [ekasaSuccess]);

  useEffect(() => {
    if (!qrSuccess) return;
    const t = setTimeout(() => setQrSuccess(""), 2500);
    return () => clearTimeout(t);
  }, [qrSuccess]);

  return (
    <main className="wrap dashboard">
      <div className="section-title">
        <span className="marker"></span>
        <div>
          <T sk="Mesačný prehľad" en="Monthly Overview" /> ·{" "}
          <span id="monthTitle">Október 2025</span>
        </div>
      </div>

      <section className="summary" aria-label="Monthly KPIs">
        <article className="card compact">
          <div className="kpi">
            <div className="icon" aria-hidden="true">💶</div>
            <div>
              <small><T sk="Príjmy" en="Incomes" /></small>
              <div className="value" id="kpiIncome">€ 2 350</div>
            </div>
          </div>
        </article>

        <article className="card compact">
          <div className="kpi">
            <div className="icon" aria-hidden="true">💳</div>
            <div>
              <small><T sk="Výdavky" en="Expenses" /></small>
              <div className="value" id="kpiExpense">€ 1 840</div>
            </div>
          </div>
        </article>

        <article className="card compact">
          <div className="kpi">
            <div className="icon" aria-hidden="true">🧾</div>
            <div>
              <small><T sk="Zostatok" en="Balance" /></small>
              <div className="value" id="kpiBalance">€ 510</div>
            </div>
          </div>
        </article>

        <article className="card compact">
          <div className="kpi">
            <div className="icon" aria-hidden="true">🎯</div>
            <div>
              <small><T sk="Ciele" en="Goals" /></small>
              <div className="value" id="kpiGoals">73%</div>
            </div>
          </div>
        </article>
      </section>

      <section className="grid" aria-label="Detail & rýchly prístup">
        <div>
          <div className="panel" draggable="true">
            <div className="drag-handle" title="Presuň sekciu"></div>
            <header>
              <h3><T sk="Rozloženie výdavkov" en="Expense Distribution" /></h3>
            </header>

            <div className="donut-wrap">
              <div
                className="donut"
                role="img"
                aria-label="Donut chart: Bývanie 45%, Jedlo 25%, Lieky 20%, Oblečenie 10%"
              >
                <div className="donut-center">€ 1 840</div>
              </div>
              <div className="legend">
                <div className="row">
                  <div className="dot" style={{ background: "var(--gold)" }}></div>
                  <div className="label">Bývanie</div>
                  <strong>45%</strong>
                </div>
                <div className="row">
                  <div className="dot" style={{ background: "#9ca3af" }}></div>
                  <div className="label">Jedlo</div>
                  <strong>25%</strong>
                </div>
                <div className="row">
                  <div className="dot" style={{ background: "#60a5fa" }}></div>
                  <div className="label">Lieky</div>
                  <strong>20%</strong>
                </div>
                <div className="row">
                  <div className="dot" style={{ background: "#34d399" }}></div>
                  <div className="label">Oblečenie</div>
                  <strong>10%</strong>
                </div>
              </div>
            </div>
          </div>

          <div id="goals" className="panel" draggable="true" style={{ marginTop: "16px" }}>
            <div className="drag-handle" title="Presuň sekciu"></div>
            <header>
              <h2><T sk="Finančné ciele" en="Financial Goals" /></h2>
            </header>

            <div className="goals-container" id="goalList">
              <div className="goal-box" draggable="true">
                <div className="goal-title">Šporiť 300 € mesačne</div>
                <div className="goal-info">Ušetrené: <b>220 €</b> / 300 €</div>
                <div className="progress"><span style={{ width: "73%" }}></span></div>
              </div>

              <div className="goal-box" draggable="true">
                <div className="goal-title">Jedlo: limit 250 €</div>
                <div className="goal-info">Vynaložené: <b>190 €</b> / 250 €</div>
                <div className="progress"><span style={{ width: "76%" }}></span></div>
              </div>

              <div className="goal-box" draggable="true">
                <div className="goal-title">Investície 100 €</div>
                <div className="goal-info">Investované: <b>60 €</b> / 100 €</div>
                <div className="progress"><span style={{ width: "60%" }}></span></div>
              </div>
            </div>
          </div>
        </div>

        <div className="panel" draggable="true" id="importSection">
          <div className="drag-handle" title="Presuň sekciu"></div>
          <header>
            <h2>Import eKasa</h2>
          </header>

          <div className="import-boxes">
            <div className="import-card" draggable="true">
              <strong><T sk="QR kód eKasa" en="QR Code eKasa" /></strong>
              <p>
                <T
                  sk="Naskenujte QR kód z bločku"
                  en="Scan the QR code from your receipt"
                />
              </p>

              <input
                type="file"
                accept="image/*"
                onChange={handleQrFileChange}
                style={{ marginBottom: "8px" }}
              />

              <button
                type="button"
                onClick={handleQrImport}
                disabled={qrLoading}
                style={{
                  cursor: qrLoading ? "not-allowed" : "pointer",
                  opacity: qrLoading ? 0.7 : 1,
                  width: "100%",
                }}
              >
                {qrLoading
                  ? lang === "sk"
                    ? "Spracovávam..."
                    : "Processing..."
                  : lang === "sk"
                  ? "Importovať z QR"
                  : "Import from QR"}
              </button>

              <button
                type="button"
                onClick={toggleScanner}
                disabled={scannerLoading}
                style={{
                  marginTop: "10px",
                  cursor: scannerLoading ? "not-allowed" : "pointer",
                  opacity: scannerLoading ? 0.7 : 1,
                  width: "100%",
                }}
              >
                {scannerOpen
                  ? lang === "sk"
                    ? "Zavrieť kameru"
                    : "Close camera"
                  : lang === "sk"
                  ? "Skenovať kamerou"
                  : "Scan with camera"}
              </button>

              {scannerOpen && (
                <div
                  id="qr-reader"
                  style={{
                    width: "100%",
                    minHeight: "260px",
                    marginTop: "12px",
                    border: "2px dashed #e4d5a3",
                    borderRadius: "16px",
                    overflow: "hidden",
                    background: "#fffaf0",
                  }}
                />
              )}

              {qrSuccess && (
                <div style={{ marginTop: "8px", color: "#2e7d32", fontSize: "13px" }}>
                  {qrSuccess}
                </div>
              )}

              {qrError && (
                <div style={{ marginTop: "8px", color: "#e53935", fontSize: "13px" }}>
                  {qrError}
                </div>
              )}
            </div>

            <div className="import-card" draggable="true">
              <strong><T sk="PDF alebo JSON" en="PDF or JSON" /></strong>
              <p>
                <T
                  sk="Importujte súbor z eKasa"
                  en="Import an eKasa file"
                />
              </p>
              <button><T sk="Vybrať súbor" en="Choose File" /></button>
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

            <Link
              to="/Ekasa"
              className="btn"
              style={{ textDecoration: "none", textAlign: "center" }}
            >
              <T sk="Otvoriť eKasa" en="Open eKasa" />
            </Link>
          </div>
        </div>
      </section>

      <footer>
        <div className="foot-inner">
          <span>© BudgetApp</span>
        </div>
      </footer>
    </main>
  );
}