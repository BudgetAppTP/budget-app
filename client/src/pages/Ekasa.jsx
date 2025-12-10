import React, { useEffect } from "react";
import "./style/ekasa.css";
import T from "../i18n/T";
import { useLang } from "../i18n/LanguageContext";

export default function Ekasa() {
   const {lang} = useLang();
  useEffect(() => {
    const DATA = [
      {
        opd: "O-30D7CD84F6",
        date: "27.09.2025",
        items: [
          {
            category: "Jedlo",
            item: "Rožok štandard",
            qnt: 3,
            price: 0.36,
            vat: "5%",
            seller: "TERNO real estate",
            unit: "Hálova",
            sellerUnit: "Hálova",
          },
          {
            category: "Jedlo",
            item: "Kaiserka cereal",
            qnt: 2,
            price: 0.38,
            vat: "19%",
            seller: "TERNO real estate",
            unit: "Hálova",
            sellerUnit: "Hálova",
          },
          {
            category: "Jedlo",
            item: "Hruštínske nite",
            qnt: 1,
            price: 4.79,
            vat: "19%",
            seller: "TERNO real estate",
            unit: "Hálova",
            sellerUnit: "Hálova",
          },
        ],
      },
      {
        opd: "O-4D55DB20D1",
        date: "18.09.2025",
        items: [
          {
            category: "Jedlo",
            item: "#Lipánek MAXI",
            qnt: 1,
            price: 0.76,
            vat: "19%",
            seller: "TERNO real estate",
            unit: "Hálova",
            sellerUnit: "Hálova",
          },
          {
            category: "Jedlo",
            item: "Uhorka šalátová",
            qnt: 1,
            price: 0.99,
            vat: "5%",
            seller: "TERNO real estate",
            unit: "Hálova",
            sellerUnit: "Hálova",
          },
        ],
      },
    ];

      const ekasaRoot = document.querySelector(".ekasa");
      if (!ekasaRoot) return;

      const table = ekasaRoot.querySelector("#data-table");
      if (!table) return;

      const tbody = table.querySelector("tbody");
      const CATEGORIES = ["📌 Bývanie", "📌 Jedlo", "Doprava", "Lieky", "Ostatné"];

      function renderCategorySelect(selected) {
        return `<select class="category">
          ${CATEGORIES.map(
            (c) =>
              `<option${c.includes("📌") ? ' class="pinned"' : ""} ${
                c.replace("📌 ", "") == selected ? "selected" : ""
              }>${c}</option>`
          ).join("")}
        </select>`;
      }

      function renderTable() {
        tbody.innerHTML = "";
        let total = 0;
        DATA.forEach((block) => {
          block.items.forEach((it) => {
            const tr = document.createElement("tr");
            total += it.price;
            tr.innerHTML = `
              <td>${block.opd}</td>
              <td>${block.date}</td>
              <td>${renderCategorySelect(it.category)}</td>
              <td>${it.item}</td>
              <td class="quantity">${it.qnt}</td>
              <td class="amount">${it.price.toFixed(2)}</td>
              <td>${it.vat}</td>
              <td>${it.seller}</td>
              <td>${it.unit}</td>
              <td>${it.sellerUnit}</td>
            `;
            tbody.appendChild(tr);
          });
        });
      }

      let sortState = {};

      table.querySelectorAll("th.sortable").forEach((th) => {
        th.addEventListener("click", () => {
          const index = Array.from(th.parentNode.children).indexOf(th);
          const isPrice = th.classList.contains("price-col");
          const type = isPrice ? "num" : "date";
          const asc = sortState[index] !== "asc";
          sortState = { [index]: asc ? "asc" : "desc" };

          table
            .querySelectorAll("th")
            .forEach((t) => t.classList.remove("sorted-asc", "sorted-desc"));

          th.classList.add(asc ? "sorted-asc" : "sorted-desc");
          sortRows(index, type, asc);
        });
      });

      function sortRows(index, type, asc) {
        const rows = Array.from(tbody.rows);
        rows.sort((a, b) => {
          let av = a.cells[index].innerText.trim();
          let bv = b.cells[index].innerText.trim();
          if (type === "num") {
            av = parseFloat(av.replace(/[^\d.,-]/g, "").replace(",", "."));
            bv = parseFloat(bv.replace(/[^\d.,-]/g, "").replace(",", "."));
            return asc ? av - bv : bv - av;
          } else {
            const [da, ma, ya] = av.split(".");
            const [db, mb, yb] = bv.split(".");
            const d1 = new Date(`${ya}-${ma}-${da}`);
            const d2 = new Date(`${yb}-${mb}-${db}`);
            return asc ? d1 - d2 : d2 - d1;
          }
        });
        rows.forEach((r) => tbody.appendChild(r));
      }

      renderTable();

      return () => {};

    }, [lang]);

  return (
    <div className="wrap ekasa">
      <div className="page-title">
        🧾 <T sk="eKasa" en="eKasa" />
      </div>

      <div className="table-card">
        <table id="data-table">
          <thead>
            <tr>
            <th>OPD</th>
                          <th className="sortable price-col">

              <T sk="DÁTUM" en="DATE" />
            </th>

            <th>
              <T sk="KATEGÓRIA" en="CATEGORY" />
            </th>
            <th>
              <T sk="POLOŽKA" en="ITEM" />
            </th>
            <th>
              <T sk="MNOŽSTVO" en="QUANTITY" />
            </th>
            <th className="sortable price-col">
              <T sk="CENA (€)" en="PRICE (€)" />
            </th>
            <th>VAT</th>
            <th>
              <T sk="PREDAJCA" en="SELLER" />
            </th>
            <th>
              <T sk="UNIT" en="UNIT" />
            </th>
            <th>
              <T sk="SELLER-UNIT" en="SELLER-UNIT" />
            </th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>

      <div className="page-title" style={{ marginTop: "30px" }}>
        📂 <T sk="Import eKasa" en="Import eKasa" /><div className="gold-line"></div>
      </div>

    <div className="panel">
      <div className="import-boxes">

        <div className="import-card" draggable="true">
          <strong>
            <T sk="Nahrať eKasa / PDF" en="Upload eKasa / PDF" />
          </strong>

          <p>
            <T sk="Podporované: .ekd, .json, .pdf"
               en="Supported: .ekd, .json, .pdf" />
          </p>

          <button>
            <T sk="Vybrať súbor" en="Choose file" />
          </button>
        </div>

      </div>
    </div>
  </div>
  );
}
