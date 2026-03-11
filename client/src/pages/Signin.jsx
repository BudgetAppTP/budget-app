import React, { useEffect, useState } from "react";
import "./style/signin.css";
import { Link } from "react-router-dom";
import T from "../i18n/T";
import { useLang } from "../i18n/LanguageContext";

export default function Signin() {
  const { lang } = useLang();

  useEffect(() => {
    document.title = lang === "sk" ? "BudgetApp · Prihlásiť sa" : "BudgetApp · Sign in";
  }, [lang]);

  const [form, setForm] = useState({
    email: "",
    password: "",
    remember: false,
  });

  const [showPass, setShowPass] = useState(false);
  const [error, setError] = useState(null);

  const onChange = (key, value) => setForm((p) => ({ ...p, [key]: value }));

  const submit = (e) => {
    e.preventDefault();
    setError(null);

    if (!form.email.trim() || !form.password.trim()) {
      setError(lang === "sk" ? "Vyplňte email a heslo." : "Please enter email and password");
      return;
    }


    alert(lang === "sk" ? "Prihlásenie (demo)." : "Signin (demo).");
  };

  const EyeIcon = ({ open }) => (
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true">
      {open ? (
        <>
          <path
            d="M12 5c6.5 0 10 7 10 7s-3.5 7-10 7S2 12 2 12s3.5-7 10-7Z"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          />
          <circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" strokeWidth="2" />
        </>
      ) : (
        <>
          <path
            d="M3 3l18 18"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
          />
          <path
            d="M6.6 6.6C4.1 8.4 2 12 2 12s3.5 7 10 7c2 0 3.7-.7 5.1-1.6"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          />
          <path
            d="M10.7 10.7A3 3 0 0 0 12 15a3 3 0 0 0 2.3-4.3"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          />
        </>
      )}
    </svg>
  );

  return (
    <div className="wrap signin">
      <div className="signin-bg">

        <div className="signin-shell">
          <div className="signin-grid">

            <div className="signin-left">
              <h2 className="signin-title">
                <T sk="Vitaj späť v BudgetApp!" en="Welcome back to BudgetApp!" />
              </h2>
              <p className="signin-subtitle">
                <T
                  sk="Prihláste sa a majte svoje financie pod kontrolou"
                  en="Sign in and keep your finances under control"
                />
              </p>
            </div>

            <div className="signin-card">
              <h2 className="signin-card-title">
                <T sk="Prihlásiť sa" en="Sign in" />
              </h2>
              <p className="signin-card-sub">
                <T sk="Zadaj svoje údaje pre vstup do aplikácie" en="Enter your details to access the app" />
              </p>

              <form onSubmit={submit} className="signin-form">
                <div className="signin-field">
                  <label>Email</label>
                  <input
                    value={form.email}
                    onChange={(e) => onChange("email", e.target.value)}
                    placeholder={lang === "sk" ? "napr. valeria@email.com" : "e.g. valeria@email.com"}
                    autoComplete="email"
                  />
                </div>

                <div className="signin-field">
                  <label><T sk="Heslo" en="Password" /></label>
                  <div className="signin-input-icon">
                    <input
                      type={showPass ? "text" : "password"}
                      value={form.password}
                      onChange={(e) => onChange("password", e.target.value)}
                      placeholder="••••••••"
                      autoComplete="current-password"
                    />
                    <button
                      type="button"
                      className="signin-eye"
                      onClick={() => setShowPass((v) => !v)}
                      aria-label={showPass ? "Hide password" : "Show password"}
                    >
                      <EyeIcon open={showPass} />
                    </button>
                  </div>

                  <div className="signin-row-mini">
                      <label className="signin-remember">
                      <input
                        type="checkbox"
                        checked={form.remember}
                        onChange={(e) => onChange("remember", e.target.checked)}
                      />
                      <span className="checkmark" aria-hidden="true"></span>
                      <span className="remember-text">
                        <T sk="Zapamätať si ma" en="Remember me" />
                      </span>
                    </label>

                      <Link className="signin-forgot" to="/forgot">
                        <T sk="Zabudli ste heslo?" en="Forgot your password?" />
                      </Link>
                    </div>
                </div>

                {error && <div className="signin-error">{error}</div>}

                <button className="signin-primary" type="submit">
                  <T sk="Prihlásiť sa" en="Sign in" />
                </button>

                <div className="signin-or">
                  <span className="line" />
                  <span className="text"><T sk="alebo" en="or" /></span>
                  <span className="line" />
                </div>

               <button type="button" className="signin-google">
  <svg className="google-icon" viewBox="0 0 48 48">
    <path fill="#EA4335" d="M24 9.5c3.54 0 6.34 1.46 8.25 3.22l6.16-6.16C34.64 2.52 29.74 0 24 0 14.62 0 6.44 5.38 2.56 13.22l7.18 5.58C11.5 13.06 17.23 9.5 24 9.5z"/>
    <path fill="#4285F4" d="M46.5 24c0-1.64-.15-3.22-.43-4.74H24v9h12.7c-.55 2.96-2.22 5.47-4.73 7.15l7.27 5.64C43.73 36.88 46.5 30.95 46.5 24z"/>
    <path fill="#FBBC05" d="M9.74 28.8a14.5 14.5 0 010-9.6l-7.18-5.58a23.98 23.98 0 000 20.76l7.18-5.58z"/>
    <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.9-5.77l-7.27-5.64c-2.02 1.36-4.6 2.16-8.63 2.16-6.77 0-12.5-4.56-14.26-10.74l-7.18 5.58C6.44 42.62 14.62 48 24 48z"/>
  </svg>
  <span>Google</span>
</button>

                <div className="signin-bottom">
                  <span className="line" />
                  <span className="text">
                    <T sk="Nemáš účet?" en="Don’t have an account?" />{" "}
                    <Link to="/signup">
                      <T sk="Vytvoriť účet" en="Create account" /> <span aria-hidden="true">›</span>
                    </Link>
                  </span>
                  <span className="line" />
                </div>
              </form>
            </div>
          </div>
        </div>

        <div className="signin-footer-wrap">
          <footer className="signin-footer">© BudgetApp</footer>
        </div>
      </div>
    </div>
  );
}