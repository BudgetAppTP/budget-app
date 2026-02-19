import enum

from sqlalchemy.types import TypeDecorator, JSON as SA_JSON
from sqlalchemy.dialects.postgresql import JSONB


class JSONType(TypeDecorator):
    """ Choose the appropriate JSON column type for the database.

    Uses PostgreSQL's JSONB type if available, otherwise falls back to
    the generic JSON type. This allows models to work across different
    databases without changes.

    Attributes:
        impl: The underlying SQLAlchemy type used as the default (JSON).

    Example:
        extra_metadata: Mapped[dict] = mapped_column(JSONType())

    Notes:
        - PostgreSQL: JSONB is fast, indexable, and recommended for production.
        - Other databases (e.g., SQLite): JSON is used since JSONB is not supported.
        - No extra handling in Python code is needed; you can use the column
          as a normal dict regardless of the database.
    """
    impl = SA_JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(SA_JSON())


@enum.unique
class TagType(str, enum.Enum):
    """ Enum representing the types of tags in the system.

    Attributes:
        INCOME: (salary, payments).
        EXPENSE:  (receipts).
        BOTH: Tag can be used for both income and expenses.
    """
    INCOME = "income"
    EXPENSE = "expense"
    BOTH = "both"
