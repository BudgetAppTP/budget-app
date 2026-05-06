import React, { useEffect, useMemo, useState } from "react";
import "./style/savings.css";
import { useLang } from "../i18n/LanguageContext";
import T from "../i18n/T";

export default function Savings() {
  const { lang } = useLang();

  useEffect(() => {
    document.title = lang === "sk" ? "BudgetApp · Úspory" : "BudgetApp · Savings";
  }, [lang]);

  const [accountBalance, setAccountBalance] = useState(1500);

  const [funds, setFunds] = useState([
    {
      id: 1,
      title: "Vacation in Spain",
      description:
        "Main goal. Inside it, money is distributed across flights, accommodation, entertainment and insurance.",
      target: 3000,
      contribution: 250,
      balance: 900,
      completed: false,
      history: [
        { label: "Fund top-up", date: "14.03.2026", amount: 600 },
        { label: "Monthly contribution", date: "01.03.2026", amount: 250 },
        { label: "Reallocation from balance", date: "22.02.2026", amount: 300 },
      ],
      goals: [
        {
          id: 101,
          title: "Tickets",
          description: "Round-trip flights for two.",
          target: 800,
          allocated: 300,
          completed: false,
        },
        {
          id: 102,
          title: "Insurance",
          description: "Medical insurance and reserve.",
          target: 200,
          allocated: 0,
          completed: false,
        },
      ],
    },
    {
      id: 2,
      title: "New laptop",
      description: "Fund for a major tech purchase.",
      target: 2200,
      contribution: 180,
      balance: 520,
      completed: false,
      history: [
        { label: "Initial funding", date: "28.02.2026", amount: 400 },
        { label: "Contribution", date: "10.03.2026", amount: 120 },
      ],
      goals: [
        {
          id: 201,
          title: "Laptop",
          description: "Main device cost.",
          target: 1800,
          allocated: 420,
          completed: false,
        },
        {
          id: 202,
          title: "Accessories",
          description: "Case, mouse and adapters.",
          target: 250,
          allocated: 0,
          completed: false,
        },
      ],
    },
    {
      id: 3,
      title: "Emergency fund",
      description: "Reserve for unexpected expenses.",
      target: 5000,
      contribution: 300,
      balance: 1600,
      completed: false,
      history: [
        { label: "Regular contribution", date: "05.03.2026", amount: 300 },
        { label: "Regular contribution", date: "05.02.2026", amount: 300 },
      ],
      goals: [
        {
          id: 301,
          title: "1-month reserve",
          description: "Minimum safety net.",
          target: 1500,
          allocated: 700,
          completed: false,
        },
        {
          id: 302,
          title: "3-month reserve",
          description: "Comfortable buffer.",
          target: 3500,
          allocated: 400,
          completed: false,
        },
      ],
    },
  ]);

  const [currentFundId, setCurrentFundId] = useState(1);
  const [fundActionAmount, setFundActionAmount] = useState("100");
  const [goalInputs, setGoalInputs] = useState({});
  const [showHistoryPanel, setShowHistoryPanel] = useState(false);

  const [editingFundId, setEditingFundId] = useState(null);
  const [editingGoalId, setEditingGoalId] = useState(null);

  const [fundEditorOpen, setFundEditorOpen] = useState(false);
  const [goalEditorOpen, setGoalEditorOpen] = useState(false);

  const [fundForm, setFundForm] = useState({
    title: "",
    target: "",
    contribution: "",
    description: "",
  });

  const [goalForm, setGoalForm] = useState({
    title: "",
    target: "",
    description: "",
  });

  const [fundFormErrors, setFundFormErrors] = useState({});
  const [goalFormErrors, setGoalFormErrors] = useState({});
  const [pageError, setPageError] = useState("");
  const [footerMessage, setFooterMessage] = useState("");

  const formatMoney = (value) =>
    `${Number(value || 0).toLocaleString(lang === "sk" ? "sk-SK" : "en-US")} €`;

  const today = () =>
    new Date().toLocaleDateString(lang === "sk" ? "sk-SK" : "en-US");

  const orderedFunds = useMemo(() => {
    return [...funds].sort((a, b) => {
      if (a.completed !== b.completed) return Number(a.completed) - Number(b.completed);
      return a.id - b.id;
    });
  }, [funds]);

  useEffect(() => {
    if (!orderedFunds.length) return;
    const exists = orderedFunds.some((fund) => fund.id === currentFundId);
    if (!exists) setCurrentFundId(orderedFunds[0].id);
  }, [orderedFunds, currentFundId]);

  const currentFund = orderedFunds.find((fund) => fund.id === currentFundId) || null;

  const orderedGoals = useMemo(() => {
    if (!currentFund) return [];
    return [...currentFund.goals].sort((a, b) => {
      if (a.completed !== b.completed) return Number(a.completed) - Number(b.completed);
      return a.id - b.id;
    });
  }, [currentFund]);

  const totalFundsBalance = useMemo(
    () => funds.reduce((sum, fund) => sum + (fund.balance || 0), 0),
    [funds]
  );

  const unallocatedInFund = (fund) =>
    Math.max(
      0,
      (fund.balance || 0) -
        fund.goals.reduce((sum, goal) => sum + (goal.allocated || 0), 0)
    );

  const totalUnallocated = useMemo(
    () => funds.reduce((sum, fund) => sum + unallocatedInFund(fund), 0),
    [funds]
  );

  const currentPercent = currentFund
    ? Math.min(100, Math.round((currentFund.balance / Math.max(1, currentFund.target)) * 100))
    : 0;

  const resetMessages = () => {
    setPageError("");
    setFooterMessage("");
  };

  const guardCompletedFund = () => {
    if (!currentFund?.completed) return false;
    setFooterMessage(
      lang === "sk"
        ? "Tento fond je označený ako splnený. Úpravy a presuny sú momentálne zablokované"
        : "This fund is marked as completed. Editing and transfers are currently locked"
    );
    return true;
  };

  const changeFund = (offset) => {
    if (!orderedFunds.length || !currentFund) return;
    const currentIndex = orderedFunds.findIndex((f) => f.id === currentFund.id);
    const nextIndex = (currentIndex + offset + orderedFunds.length) % orderedFunds.length;
    setCurrentFundId(orderedFunds[nextIndex].id);
    setFundEditorOpen(false);
    setGoalEditorOpen(false);
    setEditingFundId(null);
    setEditingGoalId(null);
    setShowHistoryPanel(false);
    resetMessages();
  };

  const getGoalInputValue = (goalId) => goalInputs[goalId] ?? "100";

  const validateFundForm = () => {
    const errors = {};

    if (!fundForm.title.trim()) {
      errors.title =
        lang === "sk" ? "Názov fondu je povinný" : "Fund name is required";
    }

    if (fundForm.target === "" || Number(fundForm.target) <= 0) {
      errors.target =
        lang === "sk"
          ? "Cieľová suma musí byť väčšia ako 0"
          : "Target amount must be greater than 0";
    }

    if (fundForm.contribution === "" || Number(fundForm.contribution) < 0) {
      errors.contribution =
        lang === "sk"
          ? "Príspevok musí byť 0 alebo viac"
          : "Contribution must be 0 or more";
    }

    if (!fundForm.description.trim()) {
      errors.description =
        lang === "sk" ? "Popis fondu je povinný" : "Fund description is required";
    }

    setFundFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const validateGoalForm = () => {
    const errors = {};

    if (!goalForm.title.trim()) {
      errors.title =
        lang === "sk" ? "Názov cieľa je povinný" : "Goal name is required";
    }

    if (goalForm.target === "" || Number(goalForm.target) <= 0) {
      errors.target =
        lang === "sk"
          ? "Cieľová suma musí byť väčšia ako 0"
          : "Target amount must be greater than 0";
    }

    if (!goalForm.description.trim()) {
      errors.description =
        lang === "sk" ? "Popis cieľa je povinný" : "Goal description is required";
    }

    setGoalFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const openAddFundCard = () => {
    resetMessages();
    setEditingFundId(null);
    setFundFormErrors({});
    setFundForm({
      title: "",
      target: "",
      contribution: "",
      description: "",
    });
    setFundEditorOpen(true);
  };

  const openEditFundCard = () => {
    if (!currentFund) return;
    if (guardCompletedFund()) return;

    resetMessages();
    setEditingFundId(currentFund.id);
    setFundFormErrors({});
    setFundForm({
      title: currentFund.title || "",
      target: currentFund.target ?? "",
      contribution: currentFund.contribution ?? "",
      description: currentFund.description || "",
    });
    setFundEditorOpen(true);
  };

  const cancelFundEditor = () => {
    setFundEditorOpen(false);
    setEditingFundId(null);
    setFundFormErrors({});
  };

  const saveFund = () => {
    if (!validateFundForm()) return;

    const payload = {
      title: fundForm.title.trim(),
      target: parseFloat(fundForm.target),
      contribution: parseFloat(fundForm.contribution),
      description: fundForm.description.trim(),
    };

    if (editingFundId) {
      setFunds((prev) =>
        prev.map((fund) =>
          fund.id === editingFundId
            ? {
                ...fund,
                ...payload,
              }
            : fund
        )
      );
    } else {
      const newId = Date.now();
      const newFund = {
        id: newId,
        ...payload,
        balance: 0,
        completed: false,
        history: [],
        goals: [],
      };

      setFunds((prev) => [...prev, newFund]);
      setCurrentFundId(newId);
    }

    setFundEditorOpen(false);
    setEditingFundId(null);
    setFundFormErrors({});
  };

  const openGoalCard = (goalId = null) => {
    if (!currentFund) return;
    if (guardCompletedFund()) return;

    resetMessages();
    setEditingGoalId(goalId);
    setGoalFormErrors({});

    if (goalId) {
      const goal = currentFund.goals.find((g) => g.id === goalId);
      setGoalForm({
        title: goal?.title || "",
        target: goal?.target ?? "",
        description: goal?.description || "",
      });
    } else {
      setGoalForm({
        title: "",
        target: "",
        description: "",
      });
    }

    setGoalEditorOpen(true);
    setShowHistoryPanel(false);
  };

  const cancelGoalEditor = () => {
    setGoalEditorOpen(false);
    setEditingGoalId(null);
    setGoalFormErrors({});
  };

  const saveGoal = () => {
    if (!currentFund) return;
    if (!validateGoalForm()) return;

    const payload = {
      title: goalForm.title.trim(),
      target: parseFloat(goalForm.target),
      description: goalForm.description.trim(),
    };

    setFunds((prev) =>
      prev.map((fund) => {
        if (fund.id !== currentFund.id) return fund;

        if (editingGoalId) {
          return {
            ...fund,
            goals: fund.goals.map((goal) => {
              if (goal.id !== editingGoalId) return goal;

              const nextCompleted = goal.allocated >= payload.target;

              return {
                ...goal,
                ...payload,
                completed: nextCompleted,
              };
            }),
          };
        }

        return {
          ...fund,
          goals: [
            ...fund.goals,
            {
              id: Date.now(),
              ...payload,
              allocated: 0,
              completed: false,
            },
          ],
        };
      })
    );

    setGoalEditorOpen(false);
    setEditingGoalId(null);
    setGoalFormErrors({});
  };

  const handleFundBalanceAdjust = (sign) => {
    if (!currentFund) return;
    if (guardCompletedFund()) return;

    const amount = parseFloat(fundActionAmount || 0);
    if (!amount || amount <= 0) {
      setFooterMessage(
        lang === "sk"
          ? "Zadajte platnú sumu väčšiu ako 0."
          : "Enter a valid amount greater than 0."
      );
      return;
    }

    if (sign > 0) {
      if (amount > accountBalance) {
        setFooterMessage(
          lang === "sk"
            ? "Na hlavnom zostatku nie je dostatok peňazí."
            : "There is not enough money in the main balance."
        );
        return;
      }

      setFunds((prev) =>
        prev.map((fund) =>
          fund.id === currentFund.id
            ? {
                ...fund,
                balance: fund.balance + amount,
                history: [
                  {
                    label:
                      lang === "sk"
                        ? "Doplnenie fondu z hlavného zostatku"
                        : "Fund top-up from main balance",
                    date: today(),
                    amount,
                  },
                  ...fund.history,
                ],
              }
            : fund
        )
      );

      setAccountBalance((prev) => prev - amount);
    } else {
      const availableToReturn = unallocatedInFund(currentFund);

      if (amount > availableToReturn) {
        setFooterMessage(
          lang === "sk"
            ? "Späť môžete vrátiť iba nerozdelenú časť fondu."
            : "You can only return the unallocated part of the fund."
        );
        return;
      }

      setFunds((prev) =>
        prev.map((fund) =>
          fund.id === currentFund.id
            ? {
                ...fund,
                balance: Math.max(0, fund.balance - amount),
                history: [
                  {
                    label:
                      lang === "sk"
                        ? "Vrátenie do hlavného zostatku"
                        : "Return to main balance",
                    date: today(),
                    amount: -amount,
                  },
                  ...fund.history,
                ],
              }
            : fund
        )
      );

      setAccountBalance((prev) => prev + amount);
    }

    resetMessages();
  };

  const handleAllocateToGoal = (goalId, sign) => {
    if (!currentFund) return;
    if (guardCompletedFund()) return;

    const amount = parseFloat(getGoalInputValue(goalId) || 0);
    if (!amount || amount <= 0) {
      setFooterMessage(
        lang === "sk"
          ? "Zadajte platnú sumu väčšiu ako 0."
          : "Enter a valid amount greater than 0."
      );
      return;
    }

    const targetGoal = currentFund.goals.find((g) => g.id === goalId);
    if (!targetGoal) return;

    const available = unallocatedInFund(currentFund);

    if (sign > 0) {
      if (targetGoal.completed || targetGoal.allocated >= targetGoal.target) {
        setFooterMessage(
          lang === "sk"
            ? "Tento cieľ je už splnený. Ďalšie pridanie peňazí nie je možné."
            : "This goal is already completed. You cannot add more money."
        );
        return;
      }

      const remainingToTarget = Math.max(0, targetGoal.target - targetGoal.allocated);

      if (amount > available) {
        setFooterMessage(
          lang === "sk"
            ? "V tomto fonde nie je dostatok dostupných peňazí."
            : "There isn't enough available cash in this fund."
        );
        return;
      }

      if (amount > remainingToTarget) {
        setFooterMessage(
          lang === "sk"
            ? "Nemôžete pridať viac než zostáva do splnenia cieľa."
            : "You cannot add more than the remaining amount to the goal."
        );
        return;
      }
    }

    if (sign < 0 && amount > targetGoal.allocated) {
      setFooterMessage(
        lang === "sk"
          ? "Nemôžete odobrať viac, než je v cieli alokované."
          : "You cannot remove more than is allocated to the goal."
      );
      return;
    }

    setFunds((prev) =>
      prev.map((fund) => {
        if (fund.id !== currentFund.id) return fund;

        return {
          ...fund,
          goals: fund.goals.map((goal) => {
            if (goal.id !== goalId) return goal;

            const nextAllocated =
              sign > 0
                ? goal.allocated + amount
                : Math.max(0, goal.allocated - amount);

            return {
              ...goal,
              allocated: nextAllocated,
              completed: nextAllocated >= goal.target,
            };
          }),
          history: [
            {
              label:
                sign > 0
                  ? `${lang === "sk" ? "Presun do cieľa" : "Transfer to goal"}: ${targetGoal.title}`
                  : `${lang === "sk" ? "Návrat z cieľa" : "Return from goal"}: ${targetGoal.title}`,
              date: today(),
              amount: sign > 0 ? amount : -amount,
            },
            ...fund.history,
          ],
        };
      })
    );

    resetMessages();
  };

  const toggleGoalComplete = (goalId) => {
    if (!currentFund) return;
    if (guardCompletedFund()) return;

    setFunds((prev) =>
      prev.map((fund) => {
        if (fund.id !== currentFund.id) return fund;

        const currentGoal = fund.goals.find((g) => g.id === goalId);
        if (!currentGoal) return fund;

        if (currentGoal.allocated < currentGoal.target && !currentGoal.completed) {
          setFooterMessage(
            lang === "sk"
              ? "Cieľ nie je možné označiť ako splnený skôr, než dosiahne cieľovú sumu."
              : "A goal cannot be marked as completed before it reaches its target amount."
          );
          return fund;
        }

        return {
          ...fund,
          goals: fund.goals.map((goal) =>
            goal.id === goalId ? { ...goal, completed: !goal.completed } : goal
          ),
          history: [
            {
              label: `${
                currentGoal.completed
                  ? lang === "sk"
                    ? "Cieľ znovu otvorený"
                    : "Goal reopened"
                  : lang === "sk"
                  ? "Cieľ splnený"
                  : "Goal completed"
              }: ${currentGoal.title}`,
              date: today(),
              amount: 0,
            },
            ...fund.history,
          ],
        };
      })
    );
  };

  const toggleFundComplete = () => {
    if (!currentFund) return;

    setFunds((prev) =>
      prev.map((fund) =>
        fund.id === currentFund.id
          ? {
              ...fund,
              completed: !fund.completed,
              history: [
                {
                  label: fund.completed
                    ? lang === "sk"
                      ? "Fond bol znovu otvorený"
                      : "Fund reopened"
                    : lang === "sk"
                    ? "Fond bol označený ako splnený"
                    : "Fund marked as completed",
                  date: today(),
                  amount: 0,
                },
                ...fund.history,
              ],
            }
          : fund
      )
    );

    setFooterMessage(
      currentFund.completed
        ? ""
        : lang === "sk"
        ? "Fond bol označený ako splnený. Väčšina akcií je teraz zablokovaná."
        : "The fund was marked as completed. Most actions are now locked."
    );
  };

  const deleteGoal = (goalId) => {
    if (!currentFund) return;
    if (guardCompletedFund()) return;

    const goal = currentFund.goals.find((g) => g.id === goalId);

    if (goal && goal.allocated > 0) {
      setFooterMessage(
        lang === "sk"
          ? "Cieľ môžete odstrániť iba vtedy, keď má alokáciu 0."
          : "You can delete the goal only when its allocation is 0."
      );
      return;
    }

    setFunds((prev) =>
      prev.map((fund) =>
        fund.id === currentFund.id
          ? {
              ...fund,
              goals: fund.goals.filter((g) => g.id !== goalId),
            }
          : fund
      )
    );

    resetMessages();
  };

  const deleteFund = () => {
    if (!currentFund) return;
    if (guardCompletedFund()) return;

    if (funds.length === 1) {
      setPageError(
        lang === "sk"
          ? "Nemôžete odstrániť jediný fond."
          : "You cannot delete the only fund."
      );
      return;
    }

    if (currentFund.balance > 0) {
      setPageError(
        lang === "sk"
          ? "Pred odstránením fondu najprv presuňte alebo vráťte jeho peniaze."
          : "Before deleting the fund, first move or return its money."
      );
      return;
    }

    const remaining = orderedFunds.filter((f) => f.id !== currentFund.id);
    setFunds((prev) => prev.filter((f) => f.id !== currentFund.id));

    if (remaining.length) {
      setCurrentFundId(remaining[0].id);
    }

    resetMessages();
  };

  const stats = [
    {
      label: lang === "sk" ? "Aktuálny zostatok" : "Current balance",
      value: formatMoney(accountBalance),
      sub:
        lang === "sk"
          ? "K dispozícii na nové presuny"
          : "Available for new allocations",
    },
    {
      label: lang === "sk" ? "Spolu vo fondoch" : "Total in funds",
      value: formatMoney(totalFundsBalance),
      sub:
        lang === "sk"
          ? "Peniaze už rozdelené do fondov"
          : "Money already distributed to funds",
    },
    {
      label: lang === "sk" ? "Počet fondov" : "Number of funds",
      value: String(funds.length),
      sub:
        lang === "sk" ? "Aktuálny počet fondov" : "Current number of funds",
    },
    {
      label: lang === "sk" ? "Nerozdelené vo fondoch" : "Unallocated inside funds",
      value: formatMoney(totalUnallocated),
      sub:
        lang === "sk"
          ? "Peniaze ešte nerozdelené medzi ciele"
          : "Money not yet distributed across goals",
    },
  ];

  return (
    <div className="wrap savings">
      <div className="page-title">
        🎯 <T sk="Úspory" en="Savings" />
      </div>

      <div className="content-width">
        <div className="savings-stats">
          {stats.map((card, index) => (
            <div className="stat-card" key={index}>
              <div className="stat-label">{card.label}</div>
              <div className="stat-value">{card.value}</div>
              <div className="stat-sub">{card.sub}</div>
            </div>
          ))}
        </div>

        {fundEditorOpen && (
  <section className="editor-card fund-editor-card">
    <div className="editor-card-head">
      <h3>
        {editingFundId ? (
          <T sk="Upraviť fond" en="Edit fund" />
        ) : (
          <T sk="Pridať fond" en="Add fund" />
        )}
      </h3>
      <p>
        <T
          sk="Vyplňte základné údaje fondu."
          en="Fill in the basic fund details."
        />
      </p>
    </div>

    <div className="fund-editor-form-box">
      <div className="fund-editor-top-row">
        <div className="editor-form-block">
          <label>
            <span><T sk="Názov fondu" en="Fund name" /></span>
            <input
              type="text"
              value={fundForm.title}
              onChange={(e) =>
                setFundForm((prev) => ({ ...prev, title: e.target.value }))
              }
            />
            {fundFormErrors.title && (
              <div className="field-error">{fundFormErrors.title}</div>
            )}
          </label>
        </div>
      </div>

      <div className="fund-editor-description editor-form-block">
        <label>
          <span><T sk="Popis" en="Description" /></span>
          <textarea
            rows={4}
            value={fundForm.description}
            onChange={(e) =>
              setFundForm((prev) => ({ ...prev, description: e.target.value }))
            }
          />
          {fundFormErrors.description && (
            <div className="field-error">{fundFormErrors.description}</div>
          )}
        </label>
      </div>

      <div className="fund-editor-bottom-fields">
        <div className="editor-side-fields fund-editor-field">
          <label>
            <span><T sk="Cieľová suma" en="Target amount" /></span>
            <input
              type="number"
              min="0"
              step="50"
              value={fundForm.target}
              onChange={(e) =>
                setFundForm((prev) => ({ ...prev, target: e.target.value }))
              }
            />
            {fundFormErrors.target && (
              <div className="field-error">{fundFormErrors.target}</div>
            )}
          </label>
        </div>

        <div className="editor-side-fields fund-editor-field">
          <label>
            <span><T sk="Príspevok / mesiac" en="Contribution / month" /></span>
            <input
              type="number"
              min="0"
              step="10"
              value={fundForm.contribution}
              onChange={(e) =>
                setFundForm((prev) => ({ ...prev, contribution: e.target.value }))
              }
            />
            {fundFormErrors.contribution && (
              <div className="field-error">{fundFormErrors.contribution}</div>
            )}
          </label>
        </div>
      </div>

      <div className="fund-editor-bottom-bar">
        <div className="goal-editor-icon-actions">
          <button
            className="goal-editor-icon-btn cancel"
            type="button"
            onClick={cancelFundEditor}
            title={lang === "sk" ? "Zrušiť" : "Cancel"}
          >
            ✕
          </button>

          <button
            className="goal-editor-icon-btn confirm"
            type="button"
            onClick={saveFund}
            title={lang === "sk" ? "Uložiť fond" : "Save fund"}
          >
            ✓
          </button>
        </div>
      </div>
    </div>
  </section>
)}

        {!fundEditorOpen && (
  <div className="fund-stage">
    <div className="fund-stage-arrow fund-stage-arrow-left">
      <button
        className="side-arrow-box"
        type="button"
        onClick={() => changeFund(-1)}
        title={lang === "sk" ? "Predchádzajúci fond" : "Previous fund"}
      >
        <div className="triangle left"></div>
      </button>
    </div>

    <div className="fund-stage-center">
      {currentFund && (
        <section className={`fund-shell ${currentFund.completed ? "completed-fund" : ""}`}>
          <div className="fund-topbar">
            <div className="fund-topbar-actions">
              <button
                className="icon-btn"
                type="button"
                onClick={openEditFundCard}
                title={lang === "sk" ? "Upraviť fond" : "Edit fund"}
                disabled={currentFund.completed}
              >
                ✎
              </button>

              <button
                className={`icon-btn history-icon-btn ${showHistoryPanel ? "soft" : ""}`}
                type="button"
                onClick={() => {
                  setShowHistoryPanel((prev) => !prev);
                  setGoalEditorOpen(false);
                  resetMessages();
                }}
                title={lang === "sk" ? "Prepnúť históriu" : "Toggle history"}
              >
                <span className="history-sticker">🕘</span>
              </button>

              <button
                className="icon-btn danger"
                type="button"
                onClick={deleteFund}
                title={lang === "sk" ? "Odstrániť fond" : "Delete fund"}
                disabled={currentFund.completed}
              >
                🗑
              </button>

              <button
                className={`icon-btn ${currentFund.completed ? "done-on" : "done-off"}`}
                type="button"
                onClick={toggleFundComplete}
                title={lang === "sk" ? "Stav fondu" : "Fund status"}
              >
                {currentFund.completed ? "✓" : "◻"}
              </button>

              <button className="btn soft" type="button" onClick={openAddFundCard}>
                <T sk="+ Pridať fond" en="+ Add fund" />
              </button>
            </div>
          </div>

          <div className="fund-main-layout">
            <div className="fund-main-left">
              <div className="fund-title">
                <h2>{currentFund.title}</h2>
                <p>{currentFund.description}</p>
              </div>
            </div>

            <div className={`fund-money-side ${currentFund.completed ? "is-disabled-row" : ""}`}>
              <div className="fund-action-input">
                <label>
                  <T sk="Suma pre fond" en="Amount for fund" />
                </label>
                <input
                  type="number"
                  min="0"
                  step="50"
                  value={fundActionAmount}
                  onChange={(e) => setFundActionAmount(e.target.value)}
                  disabled={currentFund.completed}
                />
              </div>

              <div className="fund-action-buttons">
                <button
                  className="mini-action soft"
                  type="button"
                  onClick={() => handleFundBalanceAdjust(1)}
                  title={lang === "sk" ? "Pridať do fondu" : "Add to fund"}
                  disabled={currentFund.completed}
                >
                  +
                </button>

                <button
                  className="mini-action"
                  type="button"
                  onClick={() => handleFundBalanceAdjust(-1)}
                  title={lang === "sk" ? "Vrátiť z fondu" : "Return from fund"}
                  disabled={currentFund.completed}
                >
                  −
                </button>
              </div>
            </div>
          </div>

          <div className="fund-grid">
            <div className="mini-card">
              <div className="mini-top">
                <span><T sk="Spolu" en="Total" /></span>
              </div>
              <div className="mini-value">{formatMoney(currentFund.balance)}</div>
              <div className="mini-note">
                <T
                  sk="Koľko peňazí je momentálne vo fonde."
                  en="How much money is currently in this fund."
                />
              </div>
            </div>

            <div className="mini-card">
              <div className="mini-top">
                <span><T sk="Cieľová suma" en="Target amount" /></span>
              </div>
              <div className="mini-value">{formatMoney(currentFund.target)}</div>
              <div className="mini-note">
                <T
                  sk="Celková cieľová suma pre aktuálny fond."
                  en="Total target amount for the current fund."
                />
              </div>
            </div>

            <div className="mini-card">
              <div className="mini-top">
                <span><T sk="Príspevok" en="Contribution" /></span>
              </div>
              <div className="mini-value">{formatMoney(currentFund.contribution)}</div>
              <div className="mini-note">
                <T
                  sk="Koľko plánujete pridávať mesačne."
                  en="How much you plan to add monthly."
                />
              </div>
            </div>

            <div className="mini-card">
              <div className="mini-top">
                <span><T sk="Nerozdelené" en="Unallocated" /></span>
              </div>
              <div className="mini-value">{formatMoney(unallocatedInFund(currentFund))}</div>
              <div className="mini-note">
                <T
                  sk="Táto časť sa ešte dá rozdeliť medzi ciele alebo vrátiť späť."
                  en="This part can still be distributed to goals or returned back."
                />
              </div>
            </div>
          </div>

          <div className="progress-card">
            <div className="progress-row">
              <div className="progress-title">
                <T sk="Priebeh plnenia" en="Progress" />
              </div>
              <div className="progress-meta">
                {currentPercent}% <T sk="z cieľa" en="of target" />
              </div>
            </div>

            <div className="progress-bar">
              <div className="progress-fill" style={{ width: `${currentPercent}%` }}></div>
            </div>

            <div className="progress-foot">
              <span>
                <T sk="Spolu" en="Total" />: {formatMoney(currentFund.balance)}
              </span>
              <span>
                <T sk="Zostáva do cieľa" en="Remaining to target" />{" "}
                {formatMoney(Math.max(0, currentFund.target - currentFund.balance))}
              </span>
            </div>
          </div>

          <div className="goals-panel">
            <div className="goals-head">
              <h3>
                {showHistoryPanel ? (
                  <T sk="História fondu" en="Fund history" />
                ) : (
                  <T sk="Ciele" en="Goals" />
                )}
              </h3>

              <div className="goals-head-actions">
                {!showHistoryPanel && (
                  <button
                    className="btn soft small"
                    type="button"
                    onClick={() => openGoalCard()}
                    disabled={currentFund.completed}
                  >
                    <T sk="+ Pridať cieľ" en="+ Add goal" />
                  </button>
                )}
              </div>
            </div>

            {!showHistoryPanel && goalEditorOpen && (
              <div className="inline-goal-editor">
                <div className="goal-row editor-goal-row">
                  <div className="goal-editor-top-row">
                    <div className="goal-title editor-form-block">
                      <label>
                        <span><T sk="Názov cieľa" en="Goal name" /></span>
                        <input
                          type="text"
                          value={goalForm.title}
                          onChange={(e) =>
                            setGoalForm((prev) => ({ ...prev, title: e.target.value }))
                          }
                        />
                        {goalFormErrors.title && (
                          <div className="field-error">{goalFormErrors.title}</div>
                        )}
                      </label>
                    </div>

                    <div className="editor-side-fields compact goal-editor-target">
                      <label>
                        <span><T sk="Cieľová suma" en="Target amount" /></span>
                        <input
                          type="number"
                          min="0"
                          step="50"
                          value={goalForm.target}
                          onChange={(e) =>
                            setGoalForm((prev) => ({ ...prev, target: e.target.value }))
                          }
                        />
                        {goalFormErrors.target && (
                          <div className="field-error">{goalFormErrors.target}</div>
                        )}
                      </label>
                    </div>
                  </div>

                  <div className="goal-editor-description editor-form-block">
                    <label>
                      <span><T sk="Popis" en="Description" /></span>
                      <textarea
                        rows={4}
                        value={goalForm.description}
                        onChange={(e) =>
                          setGoalForm((prev) => ({
                            ...prev,
                            description: e.target.value,
                          }))
                        }
                      />
                      {goalFormErrors.description && (
                        <div className="field-error">{goalFormErrors.description}</div>
                      )}
                    </label>
                  </div>

                  <div className="goal-editor-bottom-bar">
                    <div className="goal-editor-icon-actions">
                      <button
                        className="goal-editor-icon-btn cancel"
                        type="button"
                        onClick={cancelGoalEditor}
                        title={lang === "sk" ? "Zrušiť" : "Cancel"}
                      >
                        ✕
                      </button>

                      <button
                        className="goal-editor-icon-btn confirm"
                        type="button"
                        onClick={saveGoal}
                        title={lang === "sk" ? "Uložiť cieľ" : "Save goal"}
                      >
                        ✓
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {showHistoryPanel ? (
              <div className="history-list inside-panel">
                {currentFund.history.length === 0 ? (
                  <div className="empty-note">
                    {lang === "sk"
                      ? "Sekcia histórie je momentálne prázdna."
                      : "The history section is currently empty."}
                  </div>
                ) : (
                  currentFund.history.map((item, index) => (
                    <div className="history-item" key={index}>
                      <div>
                        <strong>{item.label}</strong>
                        <span>{item.date}</span>
                      </div>
                      <div className={Number(item.amount) < 0 ? "minus" : "plus"}>
                        {Number(item.amount) > 0 ? "+" : ""}
                        {formatMoney(item.amount)}
                      </div>
                    </div>
                  ))
                )}
              </div>
            ) : (
              <div className="goal-list">
                {orderedGoals.length === 0 ? (
                  <div className="empty-note">
                    {lang === "sk"
                      ? "Tento fond zatiaľ nemá žiadne ciele."
                      : "This fund does not yet have any goals."}
                  </div>
                ) : (
                  orderedGoals.map((goal) => {
                      if (goalEditorOpen && editingGoalId === goal.id) {
                        return null;
                      }

                    const goalPercent = Math.min(
                      100,
                      Math.round((goal.allocated / Math.max(1, goal.target)) * 100)
                    );

                    const goalPlusDisabled =
                      currentFund.completed || goal.completed || goal.allocated >= goal.target;

                    return (
                      <div
                        className={`goal-row ${goal.completed ? "goal-completed" : ""}`}
                        key={goal.id}
                      >
                        <div className="goal-main-row">
                          <div className="goal-title">
                            <strong>{goal.title}</strong>
                            <span>{goal.description}</span>
                          </div>

                          <div className="goal-meta">
                            <b>
                              {formatMoney(goal.allocated)} {lang === "sk" ? "z" : "of"}{" "}
                              {formatMoney(goal.target)}
                            </b>
                            <div>
                              {goalPercent}% {lang === "sk" ? "splnené" : "completed"}
                            </div>
                          </div>

                          <div className="goal-money-tools">
                            <input
                              type="number"
                              step="50"
                              value={getGoalInputValue(goal.id)}
                              onChange={(e) =>
                                setGoalInputs((prev) => ({
                                  ...prev,
                                  [goal.id]: e.target.value,
                                }))
                              }
                            />
                            <button
                              className="mini-action soft"
                              type="button"
                              onClick={() => handleAllocateToGoal(goal.id, 1)}
                              title={lang === "sk" ? "Pridať do cieľa" : "Add to goal"}
                              disabled={goalPlusDisabled}
                            >
                              +
                            </button>
                            <button
                              className="mini-action"
                              type="button"
                              onClick={() => handleAllocateToGoal(goal.id, -1)}
                              title={lang === "sk" ? "Odobrať z cieľa" : "Remove from goal"}
                              disabled={currentFund.completed}
                            >
                              −
                            </button>
                          </div>
                        </div>

                        <div className="goal-bottom-row">
                          <button
                            className="mini-action"
                            type="button"
                            onClick={() => openGoalCard(goal.id)}
                            title={lang === "sk" ? "Upraviť cieľ" : "Edit goal"}
                            disabled={currentFund.completed}
                          >
                            ✎
                          </button>
                          <button
                            className="mini-action danger"
                            type="button"
                            onClick={() => deleteGoal(goal.id)}
                            title={lang === "sk" ? "Vymazať cieľ" : "Delete goal"}
                            disabled={currentFund.completed}
                          >
                            🗑
                          </button>
                          <button
                            className={`mini-action ${goal.completed ? "done-on" : "done-off"}`}
                            type="button"
                            onClick={() => toggleGoalComplete(goal.id)}
                            title={lang === "sk" ? "Označiť ako splnené" : "Mark as complete"}
                            disabled={currentFund.completed}
                          >
                            {goal.completed ? "✓" : "◻"}
                          </button>
                        </div>
                      </div>
                    );
                  })
                )}
              </div>
            )}

            <div className="goal-footer">
              {footerMessage ? (
                <span className="footer-warning">{footerMessage}</span>
              ) : (
                <>
                  <T
                    sk="Vo fonde je momentálne k dispozícii na ďalšie rozdelenie:"
                    en="Currently available inside this fund for further distribution:"
                  />{" "}
                  <strong>{formatMoney(unallocatedInFund(currentFund))}</strong>
                </>
              )}
            </div>
          </div>
        </section>
      )}
    </div>

    <div className="fund-stage-arrow fund-stage-arrow-right">
      <button
        className="side-arrow-box"
        type="button"
        onClick={() => changeFund(1)}
        title={lang === "sk" ? "Ďalší fond" : "Next fund"}
      >
        <div className="triangle right"></div>
      </button>
    </div>
  </div>
)}


        {pageError && <div className="error-text">{pageError}</div>}
      </div>
    </div>
  );
}