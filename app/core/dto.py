from dataclasses import dataclass
from decimal import Decimal
from typing import Optional, Dict
from .domain import Section, TransactionKind


@dataclass
class TransactionFilter:
    month: Optional[str] = None
    category: Optional[str] = None
    section: Optional[Section] = None
    kind: Optional[TransactionKind] = None
    search: Optional[str] = None


@dataclass
class MonthlyTotals:
    month: str
    incomes: Decimal
    expenses: Decimal


@dataclass
class SectionTotals:
    month: str
    by_section: Dict[Section, Decimal]
