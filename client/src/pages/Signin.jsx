import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import "./style/signin.css";
import { Link, useNavigate } from "react-router-dom";
import T from "../i18n/T";
import { useLang } from "../i18n/LanguageContext";
import { authApi } from "../api/endpoints";
import { useAuth } from "../auth/AuthContext";

// Google client ID for OAuth. Provided via VITE_GOOGLE_CLIENT_ID.
const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

export default function Signin() {
  const { lang } = useLang();
  const { refreshAuth } = useAuth();

  const navigate = useNavigate();

  useEffect(() => {
    document.title = lang === "sk" ? "BudgetApp · Registrácia" : "BudgetApp · Registration";
  }, [lang]);

  const [isNarrow, setIsNarrow] = useState(
    typeof window !== "undefined" ? window.innerWidth < 980 : false
  );

  useEffect(() => {
    const onResize = () => setIsNarrow(window.innerWidth < 980);
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  const [form, setForm] = useState({
    firstName: "",
    lastName: "",
    email: "",
    password: "",
    password2: "",
    agree: false,
  });

  const [showPass1, setShowPass1] = useState(false);
  const [showPass2, setShowPass2] = useState(false);
  const [error, setError] = useState(null);
  const [step, setStep] = useState("signup");
  const [verifyCode, setVerifyCode] = useState("");
  const [verifyError, setVerifyError] = useState(null);
  const registeredCreds = useRef({ email: "", password: "" });

  const handleCredentialResponse = useCallback((response) => {
    const idToken = response.credential;
    if (!idToken) {
      setError(lang === "sk" ? "Google prihlásenie zlyhalo." : "Google sign-in failed.");
      return;
    }
    authApi
      .googleLogin({ token: idToken })
      .then(async () => {
        await refreshAuth();
        navigate("/");
      })
      .catch((err) => {
        setError(err.message || (lang === "sk" ? "Chyba prihlásenia." : "Login error."));
      });
  }, [lang, refreshAuth, navigate]);

  useEffect(() => {
    if (typeof window === "undefined" || !window.google || !GOOGLE_CLIENT_ID) return;
    try {
      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: handleCredentialResponse,
      });
    } catch (_) {}
  }, [handleCredentialResponse]);

  const canSubmit = useMemo(() => {
    if (!form.firstName.trim()) return false;
    if (!form.lastName.trim()) return false;
    if (!form.email.trim()) return false;
    if (!form.password.trim()) return false;
    if (!form.password2.trim()) return false;
    if (form.password !== form.password2) return false;
    return true;
  }, [form]);

  const onChange = (key, value) => setForm((p) => ({ ...p, [key]: value }));

  const submit = (e) => {
    e.preventDefault();
    setError(null);

    if (!canSubmit) {
      setError(
        lang === "sk"
          ? "Skontrolujte povinné polia, heslá a súhlas."
          : "Check required fields, passwords, and consent."
      );
      return;
    }

    const email = form.email.trim();
    const password = form.password;

    authApi
      .register({ email, password })
      .then(() => {
        registeredCreds.current = { email, password };
        setVerifyCode("");
        setVerifyError(null);
        setStep("verify");
      })
      .catch((err) => {
        setError(err.message || (lang === "sk" ? "Chyba registrácie." : "Registration error."));
      });
  };

  const verifySubmit = (e) => {
    e.preventDefault();
    setVerifyError(null);

    const code = verifyCode.trim();
    if (!code) {
      setVerifyError(lang === "sk" ? "Zadajte overovací kód." : "Enter the verification code.");
      return;
    }

    const { email, password } = registeredCreds.current;

    authApi
      .verify({ email, code })
      .then(() => authApi.login({ email, password }))
      .then(async () => {
        await refreshAuth();
        navigate("/");
      })
      .catch((err) => {
        setVerifyError(err.message || (lang === "sk" ? "Neplatný kód." : "Invalid code."));
      });
  };

  const onGoogleClick = () => {
    if (typeof window === "undefined" || !window.google || !GOOGLE_CLIENT_ID) {
      setError(lang === "sk" ? "Google prihlásenie nie je dostupné." : "Google sign-in is not available.");
      return;
    }
    try {
      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: handleCredentialResponse,
      });
      window.google.accounts.id.prompt();
    } catch (_) {
      setError(lang === "sk" ? "Google prihlásenie zlyhalo." : "Google sign-in failed.");
    }
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
            d="M10.6 10.6A3 3 0 0 0 12 15a3 3 0 0 0 2.4-4.4"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          />
          <path
            d="M6.6 6.6C4.1 8.4 2 12 2 12s3.5 7 10 7c2 0 3.7-.7 5.1-1.6"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
          />
          <path
            d="M14.2 5.4C17.6 6.5 20.1 9.6 22 12c0 0-3.5 7-10 7"
            fill="none"
            stroke="currentColor"
            strokeWidth="0"
            opacity="0"
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

              <div className="signin-card signin-left">
                <h2 className="signin-title">
                  <T sk="Maj financie pod kontrolou" en="Keep your finances under control"/>
                </h2>
                <p className="signin-subtitle">
                  <T
                      sk="Prihlás sa do BudgetAppa a sleduj príjmy, výdavky a ciele"
                      en="Sign in to BudgetApp and track income, expenses, and goals"
                  />
                </p>

                <div className="signin-features">
                  <div className="signin-feature">
                    <span className="signin-feature-ico ok">✅</span>
                    <span><T sk="Prehľad po mesiacoch" en="Monthly overview"/></span>
                  </div>

                  <div className="signin-feature">
                    <span className="signin-feature-ico chart">📊</span>
                    <span><T sk="Štatistiky a grafy" en="Statistics and charts"/></span>
                  </div>

                  <div className="signin-feature">
                    <span className="signin-feature-ico goal">🎯</span>
                    <span><T sk="Finančné ciele" en="Financial goals"/></span>
                  </div>

                  <div className="signin-feature">
                    <span className="signin-feature-ico doc">📄</span>
                    <span><T sk="Import eKasa" en="eKasa import"/></span>
                  </div>
                </div>
              </div>


              <div className="signin-card signin-right">
                {step === "signup" ? (
                  <>
                    <h2 className="signin-form-title">
                      <T sk="Registrácia" en="Registration"/>
                    </h2>

                    <form onSubmit={submit} className="signin-form">
                      <div className={isNarrow ? "signin-row one" : "signin-row two"}>
                        <div className="signin-field">
                          <label><T sk="Meno" en="First name"/></label>
                          <input
                              value={form.firstName}
                              onChange={(e) => onChange("firstName", e.target.value)}
                              placeholder={lang === "sk" ? "Valeria" : "Valeria"}
                              autoComplete="given-name"
                          />
                        </div>

                        <div className="signin-field">
                          <label><T sk="Priezvisko" en="Last name"/></label>
                          <input
                              value={form.lastName}
                              onChange={(e) => onChange("lastName", e.target.value)}
                              placeholder={lang === "sk" ? "M." : "M."}
                              autoComplete="family-name"
                          />
                        </div>
                      </div>

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
                        <label><T sk="Heslo" en="Password"/></label>
                        <div className="signin-input-icon">
                          <input
                              type={showPass1 ? "text" : "password"}
                              value={form.password}
                              onChange={(e) => onChange("password", e.target.value)}
                              placeholder="••••••••"
                              autoComplete="new-password"
                          />
                          <button
                              type="button"
                              className="signin-eye"
                              onClick={() => setShowPass1((v) => !v)}
                              aria-label={showPass1 ? "Hide password" : "Show password"}
                          >
                            <EyeIcon open={showPass1}/>
                          </button>
                        </div>
                        <div className="signin-hint">
                          <T
                              sk="Min. 8 znakov, odporúčané: veľké písmeno a číslo."
                              en="Min. 8 characters, recommended: uppercase letter and number."
                          />
                        </div>
                      </div>

                      <div className="signin-field">
                        <label><T sk="Zopakovať heslo" en="Repeat password"/></label>
                        <div className="signin-input-icon">
                          <input
                              type={showPass2 ? "text" : "password"}
                              value={form.password2}
                              onChange={(e) => onChange("password2", e.target.value)}
                              placeholder="••••••••"
                              autoComplete="new-password"
                          />
                          <button
                              type="button"
                              className="signin-eye"
                              onClick={() => setShowPass2((v) => !v)}
                              aria-label={showPass2 ? "Hide password" : "Show password"}
                          >
                            <EyeIcon open={showPass2}/>
                          </button>
                        </div>
                      </div>

                      {error && <div className="signin-error">{error}</div>}

                      <button className="signin-primary" type="submit">
                        <T sk="Vytvoriť účet" en="Create account"/>
                      </button>

                      <div className="login-or">
                        <span className="line" />
                        <span className="text"><T sk="alebo" en="or" /></span>
                        <span className="line" />
                      </div>

                      <button type="button" className="login-google" onClick={onGoogleClick}>
                        <svg className="google-icon" viewBox="0 0 48 48">
                          <path fill="#EA4335" d="M24 9.5c3.54 0 6.34 1.46 8.25 3.22l6.16-6.16C34.64 2.52 29.74 0 24 0 14.62 0 6.44 5.38 2.56 13.22l7.18 5.58C11.5 13.06 17.23 9.5 24 9.5z"/>
                          <path fill="#4285F4" d="M46.5 24c0-1.64-.15-3.22-.43-4.74H24v9h12.7c-.55 2.96-2.22 5.47-4.73 7.15l7.27 5.64C43.73 36.88 46.5 30.95 46.5 24z"/>
                          <path fill="#FBBC05" d="M9.74 28.8a14.5 14.5 0 010-9.6l-7.18-5.58a23.98 23.98 0 000 20.76l7.18-5.58z"/>
                          <path fill="#34A853" d="M24 48c6.48 0 11.93-2.13 15.9-5.77l-7.27-5.64c-2.02 1.36-4.6 2.16-8.63 2.16-6.77 0-12.5-4.56-14.26-10.74l-7.18 5.58C6.44 42.62 14.62 48 24 48z"/>
                        </svg>
                        <span>Google</span>
                      </button>

                      <div className="signin-divider">
                        <span className="line"/>
                        <span className="text">
                          <T sk="Máš účet?" en="Already have an account?"/>{" "}
                          <Link to="/login">
                            <T sk="Prihlásiť sa" en="Sign in"/> <span aria-hidden="true">›</span>
                          </Link>
                        </span>
                        <span className="line"/>
                      </div>
                    </form>
                  </>
                ) : (
                  <>
                    <h2 className="signin-form-title">
                      <T sk="Overte email" en="Verify your email"/>
                    </h2>
                    <p className="signin-subtitle">
                      <T
                        sk="Poslali sme vám overovací kód. Skontrolujte email a zadajte ho nižšie."
                        en="We sent a verification code. Check your email and enter it below."
                      />
                    </p>

                    <form onSubmit={verifySubmit} className="signin-form">
                      <div className="signin-field">
                        <label><T sk="Overovací kód" en="Verification code"/></label>
                        <input
                          value={verifyCode}
                          onChange={(e) => setVerifyCode(e.target.value)}
                          placeholder="123456"
                          inputMode="numeric"
                          autoComplete="one-time-code"
                          autoFocus
                        />
                      </div>

                      {verifyError && <div className="signin-error">{verifyError}</div>}

                      <button className="signin-primary" type="submit">
                        <T sk="Potvrdiť kód" en="Confirm code"/>
                      </button>

                      <div className="signin-divider">
                        <span className="line"/>
                        <span className="text">
                          <button
                            type="button"
                            style={{ background: "none", border: "none", cursor: "pointer", color: "var(--gold-dark)", fontWeight: 800, fontSize: 14 }}
                            onClick={() => { setStep("signup"); setVerifyCode(""); setVerifyError(null); setError(null); }}
                          >
                            <T sk="← Späť" en="← Back"/>
                          </button>
                        </span>
                        <span className="line"/>
                      </div>
                    </form>
                  </>
                )}
              </div>
            </div>
          </div>

        <div className="login-footer-wrap">
          <footer className="login-footer">© BudgetApp</footer>
        </div>


        </div>

      </div>
  );
}
