from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from enum import Enum
from typing import Optional


class TransactionKind(str, Enum):
    income = "income"
    expense = "expense"


class Section(str, Enum):
    POTREBY = "POTREBY"
    VOLNY_CAS = "VOLNY_CAS"
    SPORENIE = "SPORENIE"
    INVESTOVANIE = "INVESTOVANIE"


@dataclass(frozen=True)
class Money:
    amount: Decimal
    currency: str = "EUR"

    def quantized(self) -> "Money":
        q = self.amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return Money(q, self.currency)


@dataclass
class Transaction:
    id: str
    kind: TransactionKind
    date: date
    category: str
    subcategory: Optional[str]
    item: Optional[str]
    qty: Decimal
    unit_price: Decimal
    vat: Decimal
    seller: Optional[str]
    unit: Optional[str]
    note: Optional[str]
    source: Optional[str]

    def total_no_vat(self) -> Decimal:
        return (self.qty * self.unit_price).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def total_with_vat(self) -> Decimal:
        base = self.total_no_vat()
        vat_part = (base * self.vat).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return (base + vat_part).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


@dataclass
class MonthlyBudget:
    id: str
    month: str
    section: Section
    limit_amount: Decimal
    percent_target: Decimal = Decimal("0")


@dataclass
class Goal:
    id: str
    name: str
    type: str
    target_amount: Decimal
    section: Optional[Section]
    month_from: Optional[str]
    month_to: Optional[str]
    is_done: bool = False


@dataclass
class User:
    id: str
    email: str
    password_hash: str
