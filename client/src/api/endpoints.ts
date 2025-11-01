import { http, unwrap } from "./http";

export type LoginBody = { email: string; password: string };
export type RegisterBody = { email: string; password: string };

export const authApi = {
  login: (body: LoginBody) => unwrap(http.post("/auth/login", body)),
  register: (body: RegisterBody) => unwrap(http.post("/auth/register", body)),
  logout: () => unwrap(http.post("/auth/logout"))
};

export type Transaction = {
  id: number | string;
  date: string;
  kind: "income" | "expense";
  amount: number;
  description?: string;
  category?: string;
};

export const transactionsApi = {
  list: (q?: { month?: string; kind?: string; category?: string; search?: string }) =>
    unwrap<{ items: Transaction[]; count: number }>(http.get("/transactions", { params: q })),
  create: (body: Partial<Transaction> & { kind: "income" | "expense" }) =>
    unwrap<Transaction>(http.post("/transactions", body))
};

export type BudgetItem = {
  id: string;
  month: string;
  section: string;
  limit_amount: number;
  percent_target: number;
  spent: number;
};

export const budgetsApi = {
  get: (month: string) => unwrap<{ month: string; items: BudgetItem[]; left: number }>(http.get("/budgets", { params: { month } })),
  upsert: (month: string, items: Array<Pick<BudgetItem, "id" | "section" | "limit_amount" | "percent_target">>) =>
    unwrap(http.put(`/budgets/${month}`, { items }))
};

export type Goal = {
  id: string;
  name: string;
  type: string;
  target_amount: number;
  section?: string | null;
  month_from?: string | null;
  month_to?: string | null;
  is_done: boolean;
};

export const goalsApi = {
  list: (section?: string) =>
    unwrap<{ items: Goal[]; count: number }>(http.get("/goals", { params: section ? { section } : {} })),
  create: (g: Partial<Goal>) => unwrap<{ id: string }>(http.post("/goals", g)),
  update: (id: string, g: Partial<Goal>) => unwrap(http.put(`/goals/${id}`, g))
};

export const importQrApi = {
  preview: (payload: unknown) => unwrap<{ items: any[]; count: number }>(http.post("/import-qr/preview", { payload })),
  confirm: (items: unknown[]) => unwrap<{ created: number }>(http.post("/import-qr/confirm", { items }))
};

export const dashboardApi = {
  get: (month: string) =>
    unwrap<{
      month: string;
      total_exp: number;
      total_inc: number;
      sections: Record<string, number>;
      cats_exp: Record<string, number>;
      months: string[];
      series_inc: number[];
      series_exp: number[];
    }>(http.get("/dashboard", { params: { month } }))
};
