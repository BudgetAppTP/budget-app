import {GoogleLogin} from "@react-oauth/google";
import React, { useEffect, useMemo, useState } from "react";
import "./style/signup.css";
import { Link } from "react-router-dom";
import T from "../i18n/T";
import { useLang } from "../i18n/LanguageContext";
import { useNavigate } from "react-router-dom";

export default function Signup() {
  const { lang } = useLang();
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
    password2: ""
  });

  const [showPass1, setShowPass1] = useState(false);
  const [showPass2, setShowPass2] = useState(false);
  const [error, setError] = useState(null);
  const [nameError, setNameError] = useState(null);
  const [password2Error, setPassword2Error] = useState(null);
  const [passwordProblems, setPasswordProblems] = useState([]);
  const [step, setStep] = useState("signup");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const [verifyCode, setVerifyCode] = useState("");
  const [verifyError, setVerifyError] = useState(null);

  const canSubmit = useMemo(() => {
    if (!form.firstName.trim()) return false;
    if (!form.lastName.trim()) return false;
    if (!form.email.trim()) return false;
    if (!form.password.trim()) return false;
    if (!form.password2.trim()) return false;
    if (form.password !== form.password2) return false;
    return true;
  }, [form]);


  const getPasswordProblems = (password) => {
    const p = (password || "").trim();
    const problems = [];

    if (p.length < 8) problems.push("len");
    if (!/[a-z]/.test(p)) problems.push("lower");
    if (!/[A-Z]/.test(p)) problems.push("upper");
    if (!/[0-9]/.test(p)) problems.push("digit");

    return problems;
  };

  const onChange = (key, value) => {
    setForm((p) => ({ ...p, [key]: value }));

    if (key === "firstName" || key === "lastName") {
      setNameError(null);
    }

    if (key === "password" || key === "password2") {
      setPassword2Error(null);
    }

    if (key === "password") {
      setPasswordProblems([]);
    }
    setError(null);
  };


  const fakeRegisterApi = (payload) =>
    new Promise((resolve) => {
      setTimeout(() => {
        resolve({ ok: true });
      }, 450);
    });

  const submit = async (e) => {
    e.preventDefault();
    if (isSubmitting) return;


    const hasFirst = !!form.firstName.trim();
    const hasLast = !!form.lastName.trim();

    if (!hasFirst && !hasLast) setNameError("both");
    else if (!hasFirst) setNameError("first");
    else if (!hasLast) setNameError("last");
    else setNameError(null);


    const p1 = form.password.trim();
    const p2 = form.password2.trim();

    if (!p1 && !p2) setPassword2Error("bothEmpty");
    else if (!p1 && p2) setPassword2Error("passwordMissing");
    else if (p1 && !p2) setPassword2Error("repeatMissing");
    else if (p1 && p2 && p1 !== p2) setPassword2Error("mismatch");
    else setPassword2Error(null);


    const probs = getPasswordProblems(form.password);
    setPasswordProblems(probs);

    if (!canSubmit || probs.length > 0) {
      setError(
        lang === "sk"
          ? "Skontrolujte povinné polia, heslá a súhlas."
          : "Check required fields, passwords, and consent."
      );
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);

      const payload = {
        firstName: form.firstName.trim(),
        lastName: form.lastName.trim(),
        email: form.email.trim(),
        password: form.password,
      };

      const res = await fakeRegisterApi(payload);

      if (!res.ok) {
        setError(lang === "sk" ? "Registrácia zlyhala." : "Registration failed.");
        return;
      }

      setStep("verify");
      setVerifyCode("");
      setVerifyError(null);
    } finally {
      setIsSubmitting(false);
    }
  };

  const onVerifyChange = (value) => {
    setVerifyCode(value);
    setVerifyError(null);
  };

  const verifySubmit = (e) => {
    e.preventDefault();

    const code = verifyCode.trim();

    if (!code) {
      setVerifyError("required");
      return;
    }

       if (code === "12345") {
      navigate("/");
      return;
    }

    setVerifyError("invalid");
  };

  const handleGoogleSignupSuccess = async (credentialResponse) => {
  try {
    setError(null);

    console.log("Google credential response:", credentialResponse);

    const credential = credentialResponse?.credential;

    if (!credential) {
      setError(
        lang === "sk"
          ? "Google registrácia zlyhala."
          : "Google sign up failed."
      );
      return;
    }

    console.log("Google ID token:", credential);


    /*
    const res = await fetch("/api/auth/google/signup", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      credentials: "include",
      body: JSON.stringify({
        credential,
      }),
    });

    const json = await res.json().catch(() => null);

    if (!res.ok) {
      throw new Error(
        json?.error?.message ||
        (lang === "sk"
          ? "Google registrácia zlyhala."
          : "Google sign up failed.")
      );
    }
    */

    navigate("/");
  } catch (e) {
    console.error(e);
    setError(
      e?.message ||
        (lang === "sk"
          ? "Google registrácia zlyhala"
          : "Google sign up failed")
    );
  }
};

const handleGoogleSignupError = () => {
  setError(
    lang === "sk"
      ? "Google registrácia zlyhala"
      : "Google sign up failed"
  );
};



  const verifyErrorText =
    verifyError === "required"
      ? lang === "sk"
        ? "Zadaj overovací kód."
        : "Verification code is required."
      : verifyError === "invalid"
      ? lang === "sk"
        ? "Nesprávny kód. Skús znova."
        : "Invalid code. Try again."
      : "";


  const nameErrorText =
    nameError === "both"
      ? lang === "sk"
        ? "Zadaj meno a priezvisko"
        : "First name and last name are required"
      : nameError === "first"
      ? lang === "sk"
        ? "Zadaj meno"
        : "First name is required"
      : nameError === "last"
      ? lang === "sk"
        ? "Zadaj priezvisko"
        : "Last name is required"
      : "";

  const password2ErrorText =
    password2Error === "bothEmpty"
      ? lang === "sk"
        ? "Zadaj heslo a zopakuj ho"
        : "Passwords are required"
      : password2Error === "passwordMissing"
      ? lang === "sk"
        ? "Najprv zadaj heslo"
        : "Enter password first"
      : password2Error === "repeatMissing"
      ? lang === "sk"
        ? "Zopakuj heslo"
        : "Repeat password is required"
      : password2Error === "mismatch"
      ? lang === "sk"
        ? "Heslá sa nezhodujú"
        : "Passwords do not match"
      : "";

  const passwordRuleText = (code) => {
    const sk = {
      len: "aspoň 8 znakov",
      lower: "aspoň jedno malé písmeno",
      upper: "aspoň jedno veľké písmeno",
      digit: "aspoň jedno číslo",
    };
    const en = {
      len: "at least 8 characters",
      lower: "at least one lowercase letter",
      upper: "at least one uppercase letter",
      digit: "at least one number",
    };
    return (lang === "sk" ? sk : en)[code];
  };


  const passwordHintText = useMemo(() => {
    if (!passwordProblems.length) {
      return lang === "sk"
        ? "Min. 8 znakov, veľké, malé písmeno a číslo sú povinné"
        : "Min. 8 characters, upper, lower case letters and number are required";
    }
    return passwordProblems.map((c) => `• ${passwordRuleText(c)}`).join("\n");
  }, [passwordProblems, lang]);


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

  const isValidEmail = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email);

  return (
      <div className="wrap signup">
        <div className="signup-bg">
          <div className="signup-shell">
            <div className="signup-grid">

              <div className="signup-card signup-left">
                <h2 className="signup-title">
                  <T sk="Maj financie pod kontrolou" en="Keep your finances under control"/>
                </h2>
                <p className="signup-subtitle">
                  <T
                      sk="Prihlás sa do BudgetAppa a sleduj príjmy, výdavky a ciele"
                      en="Sign in to BudgetApp and track income, expenses, and goals"
                  />
                </p>

                <div className="signup-features">
                  <div className="signup-feature">
                    <span className="signup-feature-ico ok">✅</span>
                    <span><T sk="Prehľad po mesiacoch" en="Monthly overview"/></span>
                  </div>

                  <div className="signup-feature">
                    <span className="signup-feature-ico chart">📊</span>
                    <span><T sk="Štatistiky a grafy" en="Statistics and charts"/></span>
                  </div>

                  <div className="signup-feature">
                    <span className="signup-feature-ico goal">🎯</span>
                    <span><T sk="Finančné ciele" en="Financial goals"/></span>
                  </div>

                  <div className="signup-feature">
                    <span className="signup-feature-ico doc">📄</span>
                    <span><T sk="Import eKasa" en="eKasa import"/></span>
                  </div>
                </div>
              </div>

<div className={`signup-right-inner ${step === "verify" ? "is-verify" : "is-signup"}`}>
           <div className="signup-card signup-right">
              {step === "signup" ? (
                <>
                  <h2 className="signup-form-title">
                    <T sk="Registrácia" en="Registration" />
                  </h2>

                  <form onSubmit={submit} className="signup-form">
                    <div className="signup-name">
                      <div className={isNarrow ? "signup-row one" : "signup-row two"}>
                        <div className="signup-field">
                          <label>
                            <T sk="Meno" en="First name" />
                          </label>
                          <input
                            value={form.firstName}
                            onChange={(e) => onChange("firstName", e.target.value)}
                            placeholder={lang === "sk" ? "Valeria" : "Valeria"}
                            autoComplete="given-name"
                          />
                        </div>

                        <div className="signup-field">
                          <label>
                            <T sk="Priezvisko" en="Last name" />
                          </label>
                          <input
                            value={form.lastName}
                            onChange={(e) => onChange("lastName", e.target.value)}
                            placeholder={lang === "sk" ? "M." : "M."}
                            autoComplete="family-name"
                          />
                        </div>
                      </div>

                      {nameErrorText && (
                        <div className="signup-error" id="checkpassword-name">
                          {nameErrorText}
                        </div>
                      )}
                    </div>

                    <div className="signup-field">
                      <label>Email</label>

                      <input
                        type="email"
                        className="email-input"
                        value={form.email}
                        onChange={(e) => onChange("email", e.target.value)}
                        placeholder={lang === "sk"
                          ? "napr. valeria@email.com"
                          : "e.g. valeria@email.com"}
                        autoComplete="email"
                      />


                      {!form.email.trim() && error && (
                        <div className="signup-error">
                          {lang === "sk" ? "Zadaj email." : "Email is required"}
                        </div>
                      )}

                      {form.email.trim() && !isValidEmail && (
                        <div className="signup-error">
                          {lang === "sk"
                            ? "Neplatný formát emailu"
                            : "Invalid email format"}
                        </div>
                      )}
                    </div>

                    <div className="signup-field">
                      <label>
                        <T sk="Heslo" en="Password" />
                      </label>
                      <div className="signup-input-icon">
                        <input
                          type={showPass1 ? "text" : "password"}
                          value={form.password}
                          onChange={(e) => onChange("password", e.target.value)}
                          placeholder="••••••••"
                          autoComplete="new-password"
                        />
                        <button
                          type="button"
                          className="signup-eye"
                          onClick={() => setShowPass1((v) => !v)}
                          aria-label={showPass1 ? "Hide password" : "Show password"}
                        >
                          <EyeIcon open={showPass1} />
                        </button>
                      </div>

                      <div className={passwordProblems.length ? "signup-error" : "signup-hint"}>
                        <span style={{ whiteSpace: "pre-line" }}>{passwordHintText}</span>
                      </div>
                    </div>

                    <div className="signup-field">
                      <label>
                        <T sk="Zopakovať heslo" en="Repeat password" />
                      </label>
                      <div className="signup-input-icon">
                        <input
                          type={showPass2 ? "text" : "password"}
                          value={form.password2}
                          onChange={(e) => onChange("password2", e.target.value)}
                          placeholder="••••••••"
                          autoComplete="new-password"
                        />
                        <button
                          type="button"
                          className="signup-eye"
                          onClick={() => setShowPass2((v) => !v)}
                          aria-label={showPass2 ? "Hide password" : "Show password"}
                        >
                          <EyeIcon open={showPass2} />
                        </button>
                      </div>

                      {password2Error && <div className="signup-error">{password2ErrorText}</div>}
                    </div>


                    <button className="signup-primary" type="submit" disabled={isSubmitting}>
                      {isSubmitting ? (lang === "sk" ? "Odosielam..." : "Submitting...") : <T sk="Vytvoriť účet" en="Create account" />}
                    </button>

                    <div className="login-or">
                      <span className="line" />
                      <span className="text">
                        <T sk="alebo" en="or" />
                      </span>
                      <span className="line" />
                    </div>

                    <div className="login-google">
                    <GoogleLogin
                      onSuccess={handleGoogleSignupSuccess}
                      onError={handleGoogleSignupError}
                      text="signup_with"
                      shape="rectangular"
                      theme="outline"
                      size="large"
                      width="100%"
                      locale={lang === "sk" ? "sk" : "en"}
                      auto_select={true}
                    />
                  </div>



                    <div className="signup-divider">
                      <span className="line" />
                      <span className="text">
                        <T sk="Máš účet?" en="Already have an account?" />{" "}
                        <Link to="/signin">
                          <T sk="Prihlásiť sa" en="Sign in" /> <span aria-hidden="true">›</span>
                        </Link>
                      </span>
                      <span className="line" />
                    </div>
                  </form>
                </>
              ) : (
                <>
                  <h2 className="signup-form-title">
                    <T sk="Over si email" en="Verify your email address" />
                  </h2>

                  <p className="signup-subtitle" style={{ marginTop: 6 }}>
                    <T
                      sk="Poslali sme overovací kód na tvoj email"
                      en="We have sent a verification code to your email"
                    />
                  </p>

                  <form onSubmit={verifySubmit} className="signup-form">
                    <div className="signup-field">
                      <label>
                        <T sk="Overovací kód" en="Verification code" />
                      </label>

                      <input
                        value={verifyCode}
                        onChange={(e) => onVerifyChange(e.target.value)}
                        placeholder="12345"
                        inputMode="numeric"
                        autoComplete="one-time-code"
                      />

                      <div className="verify-help">
                        <span className="verify-help-icon">i</span>
                        <span>
                          <T
                            sk="Máte problém? "
                            en="Having trouble? "
                          />
                          <button
                            type="button"
                            className="verify-link"
                            onClick={() => {
                              console.log("resend code");
                            }}
                          >
                            <T
                              sk="Poslať nový kód"
                              en="Send a new code"
                            />
                          </button>
                        </span>
                      </div>


                      {verifyErrorText && <div className="signup-error">{verifyErrorText}</div>}
                    </div>

                    <button className="signup-primary" type="submit">
                      <T sk="Overiť email" en="Verify email address" />
                    </button>

                  </form>
                </>
              )}
            </div>
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