import React, { useState, useEffect } from "react";
import { NavLink } from "react-router-dom";
import { useLocation } from "react-router-dom";
import "./Navbar.css";
import logo from "../assets/logo.png";
import { useLang } from "../i18n/LanguageContext";
import T from "../i18n/T";

export default function Navbar() {
  const { lang, setLang } = useLang();
  const [today, setToday] = useState("");
  const [isLangMenuOpen, setIsLangMenuOpen] = useState(false);


   const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const [isWide, setIsWide] = useState(window.innerWidth > 1600);
  const [isMedium, setIsMedium] = useState(window.innerWidth <= 1600 && window.innerWidth > 1300);
  const [isSmall, setIsSmall] = useState(window.innerWidth <= 1300);

  const updateDate = () => {
    const now = new Date();
    const locale = lang === "sk" ? "sk-SK" : "en-US";

    if (window.innerWidth > 1600) {
      setToday(
        now.toLocaleDateString(locale, {
          year: "numeric",
          month: "long",
          day: "2-digit",
        })
      );
    } else {
      setToday(
        now.toLocaleDateString(locale)
      );
    }
  };

    useEffect(() => {
    updateDate();
  }, [lang]);


  useEffect(() => {
    const handleResize = () => {
      const w = window.innerWidth;

      setIsWide(w > 1600);
      setIsMedium(w <= 1600 && w > 1300);
      setIsSmall(w <= 1300);

      updateDate();
    };

    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, []);

  const closeMobileMenu = () => setIsMobileMenuOpen(false);

  const location = useLocation();

    useEffect(() => {
      setIsMobileMenuOpen(false);
    }, [location.pathname]);


  return (
      <>
    <nav className="navbar" aria-label="Top Navigation">
      <div className="nav-inner">
        <div className="brand">
          <div className="logo" aria-hidden="true">
            <img src={logo} alt="Logo" />
          </div>
          <span>BudgetApp</span>
        </div>

            {!isSmall && (
            <div className="nav-links" role="navigation">
              <NavLink to="/" end><T sk="Domov" en="Home" /></NavLink>
              <NavLink to="/incomes" onClick={closeMobileMenu}><T sk="Príjmy" en="Incomes" /></NavLink>
              <NavLink to="/expenses" onClick={closeMobileMenu}><T sk="Výdavky" en="Expenses" /></NavLink>
              <NavLink to="/budgets" onClick={closeMobileMenu}><T sk="Rozpočty" en="Budgets" /></NavLink>
              <NavLink to="/savings" onClick={closeMobileMenu}><T sk="Úspory" en="Savings" /></NavLink>
              <NavLink to="/needs" onClick={closeMobileMenu}><T sk="Potreby" en="Needs" /></NavLink>
              <NavLink to="/organisation" onClick={closeMobileMenu}><T sk="Organizácia" en="Organisation" /></NavLink>
            </div>
          )}



        <div className="right-bar">
                  <div className="date-badge" title={lang === "sk" ? "Dátum" : "Date"}>
          <svg
            width="18"
            height="18"
            viewBox="0 0 24 24"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
          >
            <path
              d="M7 2v3M17 2v3M3.5 9.5h17M4 6.5h16a1.5 1.5 0 0 1 1.5 1.5v11A1.5 1.5 0 0 1 20 20.5H4A1.5 1.5 0 0 1 2.5 19V8A1.5 1.5 0 0 1 4 6.5Z"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="round"
            />
          </svg>
          <span>{today}</span>
        </div>



 <div className="language">

            {isWide && (
                <>
                  <button className={`flag-btn ${lang === "sk" ? "active" : ""}`} onClick={() => setLang("sk")}>
                    <img src="/slovak.png" alt="SK" />
                  </button>

                  <button className={`flag-btn ${lang === "en" ? "active" : ""}`} onClick={() => setLang("en")}>
                    <img src="/english.png" alt="EN" />
                  </button>
                </>
              )}

              {isMedium && (
                <>
                  <button className="lang-trigger flag-btn" onClick={() => setIsLangMenuOpen((p) => !p)}>
                    <img src="/language.png" alt="lang" />
                  </button>

                  {isLangMenuOpen && (
                    <div className="lang-menu">
                  <button className={`flag-btn ${lang === "sk" ? "active" : ""}`} onClick={() => setLang("sk")}>
                    <img src="/slovak.png" alt="SK" />
                  </button>

                  <button className={`flag-btn ${lang === "en" ? "active" : ""}`} onClick={() => setLang("en")}>
                    <img src="/english.png" alt="EN" />
                  </button>
                    </div>
                  )}
                </>
              )}

              {isSmall && (
                <button className="burger-btn" onClick={() => setIsMobileMenuOpen(true)}>
                    <img src="/burger.png" alt="SK" />
                </button>
              )}

            </div>
          </div>
        </div>
      </nav>
{isSmall && (
        <div className={`mobile-menu ${isMobileMenuOpen ? "open" : ""}`}>

          <div className="nav-links-mobile" role="navigation">

              <NavLink to="/" end><T sk="Domov" en="Home" /></NavLink>
              <NavLink to="/incomes"><T sk="Príjmy" en="Incomes" /></NavLink>
              <NavLink to="/expenses"><T sk="Výdavky" en="Expenses" /></NavLink>
              <NavLink to="/budgets"><T sk="Rozpočty" en="Budgets" /></NavLink>
              <NavLink to="/savings"><T sk="Úspory" en="Savings" /></NavLink>
              <NavLink to="/needs"><T sk="Potreby" en="Needs" /></NavLink>
              <NavLink to="/organisation"><T sk="Organizácia" en="Organisation" /></NavLink>
            <NavLink to="#" className="close-btn"  onClick={(e) => {e.preventDefault();
             closeMobileMenu();
             }}
             > ←  Back
            </NavLink>
          </div>
          <div className="language" >
                  <button className={`flag-btn ${lang === "sk" ? "active" : ""}`} onClick={() => setLang("sk")}>
                    <img src="/slovak.png" alt="SK" />
                  </button>

                  <button className={`flag-btn ${lang === "en" ? "active" : ""}`} onClick={() => setLang("en")}>
                    <img src="/english.png" alt="EN" />
                  </button>
          </div>
        </div>
      )}
    </>
  );
}
