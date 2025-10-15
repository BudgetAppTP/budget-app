import os
import uuid
from typing import List, Optional, Dict, Iterable
from decimal import Decimal
from datetime import datetime
from collections import defaultdict
from app.core.domain import Transaction, MonthlyBudget, Goal, User, Section, TransactionKind, Money
from app.core.dto import TransactionFilter
from .repositories import TransactionsRepository, BudgetsRepository, GoalsRepository, UsersRepository

try:
    import pandas as pd
except Exception:
    pd = None


def _month_of(d: datetime) -> str:
    return d.strftime("%Y-%m")


def _parse_decimal_mixed(v) -> Decimal:
    if v is None:
        return Decimal("0.00")
    s = str(v).strip()
    s = s.replace(" ", "")
    if "," in s and "." not in s:
        s = s.replace(",", ".")
    return Decimal(s)


def _coalesce(*vals):
    for v in vals:
        if v is not None:
            return v
    return None


class InMemoryTransactionsRepository(TransactionsRepository):
    def __init__(self, initial: Optional[List[Transaction]] = None):
        self._items: List[Transaction] = list(initial or [])

    def all(self) -> List[Transaction]:
        return list(self._items)

    def query(self, flt: TransactionFilter) -> List[Transaction]:
        res = self._items
        if flt.month:
            res = [t for t in res if _month_of(t.date) == flt.month]
        if flt.kind:
            res = [t for t in res if t.kind == flt.kind]
        if flt.category:
            res = [t for t in res if t.category == flt.category]
        if flt.section:
            res = [t for t in res if _section_of(t.category) == flt.section]
        if flt.search:
            q = flt.search.lower()
            res = [t for t in res if (t.item or "").lower().find(q) >= 0 or (t.note or "").lower().find(q) >= 0]
        return res

    def add(self, tx: Transaction) -> None:
        self._items.append(tx)

    def categories(self) -> Iterable[str]:
        return sorted({t.category for t in self._items})

    def totals_by_section(self, month: str) -> Dict[Section, Decimal]:
        acc: Dict[Section, Decimal] = defaultdict(lambda: Decimal("0.00"))
        for t in self._items:
            if _month_of(t.date) != month:
                continue
            s = _section_of(t.category)
            v = t.total_with_vat()
            if t.kind == TransactionKind.expense:
                acc[s] += v
        return dict(acc)

    def totals_by_category(self, month: str, kind: Optional[TransactionKind] = None) -> Dict[str, Decimal]:
        acc: Dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))
        for t in self._items:
            if _month_of(t.date) != month:
                continue
            if kind and t.kind != kind:
                continue
            v = t.total_with_vat()
            if t.kind == TransactionKind.expense:
                acc[t.category] += v
            else:
                acc[t.category] += v
        return dict(acc)


class InMemoryBudgetsRepository(BudgetsRepository):
    def __init__(self, initial: Optional[List[MonthlyBudget]] = None):
        self._items: List[MonthlyBudget] = list(initial or [])

    def by_month(self, month: str) -> List[MonthlyBudget]:
        return [b for b in self._items if b.month == month]

    def upsert(self, mb: MonthlyBudget) -> None:
        self._items = [b for b in self._items if not (b.id == mb.id)]
        self._items.append(mb)

    def sections(self) -> List[Section]:
        return [Section.POTREBY, Section.VOLNY_CAS, Section.SPORENIE, Section.INVESTOVANIE]


class InMemoryGoalsRepository(GoalsRepository):
    def __init__(self, initial: Optional[List[Goal]] = None):
        self._items: List[Goal] = list(initial or [])

    def all(self) -> List[Goal]:
        return list(self._items)

    def upsert(self, g: Goal) -> None:
        self._items = [x for x in self._items if x.id != g.id]
        self._items.append(g)

    def by_section(self, section: Optional[Section]) -> List[Goal]:
        if section is None:
            return list(self._items)
        return [g for g in self._items if g.section == section]


class InMemoryUsersRepository(UsersRepository):
    def __init__(self, initial: Optional[List[User]] = None):
        self._items: List[User] = list(initial or [])

    def get_by_email(self, email: str) -> Optional[User]:
        for u in self._items:
            if u.email.lower() == email.lower():
                return u
        return None

    def add(self, user: User) -> None:
        self._items.append(user)


def _section_of(category: str) -> Section:
    c = category.lower()
    if c in {"byvanie", "jedlo", "obliekanie", "lieky", "cistiace prostriedky", "mobil", "streaming", "doprava", "alt tools", "google"}:
        return Section.POTREBY
    if c in {"volny cas", "zabava", "hry", "kino", "restauracia"}:
        return Section.VOLNY_CAS
    if c in {"sporenie", "rezerva"}:
        return Section.SPORENIE
    if c in {"investovanie", "akcie", "krypto"}:
        return Section.INVESTOVANIE
    return Section.POTREBY


def _seed_transactions() -> List[Transaction]:
    from datetime import date
    return [
        Transaction(str(uuid.uuid4()), TransactionKind.income, date.today().replace(day=1), "Prijmy", None, "Vyplata", Decimal("1"), Decimal("2284.91"), Decimal("0.0"), "Firma", None, None, "seed"),
        Transaction(str(uuid.uuid4()), TransactionKind.expense, date.today().replace(day=2), "Jedlo", "Potraviny", "Nakup", Decimal("1"), Decimal("32.40"), Decimal("0.2"), "Hala", "ks", None, "seed"),
        Transaction(str(uuid.uuid4()), TransactionKind.expense, date.today().replace(day=3), "Byvanie", None, "Najom", Decimal("1"), Decimal("800.00"), Decimal("0.0"), "Prenajimatel", None, None, "seed"),
        Transaction(str(uuid.uuid4()), TransactionKind.expense, date.today().replace(day=4), "Investovanie", "ETF", "Nákup", Decimal("1"), Decimal("200.00"), Decimal("0.0"), "Broker", None, None, "seed"),
    ]


def _seed_budgets(month: str) -> List[MonthlyBudget]:
    return [
        MonthlyBudget(str(uuid.uuid4()), month, Section.POTREBY, Decimal("800.00"), Decimal("40")),
        MonthlyBudget(str(uuid.uuid4()), month, Section.VOLNY_CAS, Decimal("200.00"), Decimal("10")),
        MonthlyBudget(str(uuid.uuid4()), month, Section.SPORENIE, Decimal("800.00"), Decimal("40")),
        MonthlyBudget(str(uuid.uuid4()), month, Section.INVESTOVANIE, Decimal("0.00"), Decimal("10")),
    ]


def _seed_goals(month: str) -> List[Goal]:
    return [
        Goal(str(uuid.uuid4()), "Rezerva", "monthly", Decimal("300.00"), Section.SPORENIE, month, month, False),
        Goal(str(uuid.uuid4()), "ETF dlhodobo", "longterm", Decimal("5000.00"), Section.INVESTOVANIE, None, None, False),
    ]


def try_import_from_xlsx(path: str) -> List[Transaction]:
    if not path or not os.path.exists(path):
        return []
    if pd is None:
        return []
    try:
        df = pd.read_excel(path)
    except Exception:
        return []
    cols = {c.lower(): c for c in df.columns}
    def col(name):
        return cols.get(name, None)
    out: List[Transaction] = []
    for _, r in df.iterrows():
        try:
            dt_raw = _coalesce(r.get(col("date")), r.get(col("datum")), r.get(col("dátum")))
            if isinstance(dt_raw, str):
                dt = datetime.fromisoformat(dt_raw)
            else:
                dt = pd.to_datetime(dt_raw).to_pydatetime()
            kind = TransactionKind.expense
            cat = str(_coalesce(r.get(col("category")), r.get(col("kategoria")), r.get(col("category "))) or "Jedlo")
            sub = _coalesce(r.get(col("subcategory")), r.get(col("podkategoria")))
            item = _coalesce(r.get(col("item")), r.get(col("polozka")))
            qty = _parse_decimal_mixed(_coalesce(r.get(col("qnt")), r.get(col("qty")), 1))
            price = _parse_decimal_mixed(_coalesce(r.get(col("price")), r.get(col("cena")), 0))
            vat = _parse_decimal_mixed(_coalesce(r.get(col("vat")), r.get(col("dph")), 0))
            seller = _coalesce(r.get(col("seller")), r.get(col("predajca")))
            unit = _coalesce(r.get(col("unit")), r.get(col("jednotka")))
            note = _coalesce(r.get(col("note")), None)
            out.append(Transaction(str(uuid.uuid4()), kind, dt.date(), cat, sub, item, qty, price, vat, seller, unit, note, "xlsx"))
        except Exception:
            continue
    return out


class ServicesContainer:
    def __init__(self, tx_repo: TransactionsRepository, b_repo: BudgetsRepository, g_repo: GoalsRepository, u_repo: UsersRepository):
        self.transactions = tx_repo
        self.budgets = b_repo
        self.goals = g_repo
        self.users = u_repo


def build_services(import_path: Optional[str], default_currency: str, test_user_email: Optional[str], test_user_password_hash: Optional[str]) -> ServicesContainer:
    from datetime import date
    month = date.today().strftime("%Y-%m")
    imported = try_import_from_xlsx(import_path)
    tx_repo = InMemoryTransactionsRepository(_seed_transactions() + imported)
    b_repo = InMemoryBudgetsRepository(_seed_budgets(month))
    g_repo = InMemoryGoalsRepository(_seed_goals(month))
    users = []
    if test_user_email and test_user_password_hash:
        users.append(User(str(uuid.uuid4()), test_user_email, test_user_password_hash))
    u_repo = InMemoryUsersRepository(users)
    return ServicesContainer(tx_repo, b_repo, g_repo, u_repo)
