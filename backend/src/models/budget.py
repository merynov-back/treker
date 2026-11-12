from decimal import Decimal
from sqlalchemy import Integer, Numeric, ForeignKey, UniqueConstraint
from sqlalchemy.orm import mapped_column, Mapped, relationship
from src.models.base import Base
from src.models.category import Category


class Budget(Base):
    """Ліміт витрат на місяць. category_id = None — загальний ліміт"""
    __tablename__ = "budgets"
    # Без NULLS NOT DISTINCT Postgres пропустить два загальні ліміти на місяць
    __table_args__ = (
        UniqueConstraint(
            "user_id", "category_id", "year", "month",
            name="uq_budgets_user_category_period",
            postgresql_nulls_not_distinct=True,
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id", ondelete="CASCADE"), nullable=True, default=None)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    year: Mapped[int] = mapped_column(Integer)
    month: Mapped[int] = mapped_column(Integer)

    category: Mapped[Category | None] = relationship(lazy="joined")
