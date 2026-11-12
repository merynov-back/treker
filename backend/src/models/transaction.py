import datetime
from decimal import Decimal
from sqlalchemy import String, Integer, Numeric, Date, DateTime, ForeignKey, func
from sqlalchemy.orm import mapped_column, Mapped, relationship
from src.models.base import Base
from src.models.category import Category


class Transaction(Base):
    __tablename__ = "transactions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    # RESTRICT — категорію з транзакціями видалити не можна
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id", ondelete="RESTRICT"), index=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    description: Mapped[str | None] = mapped_column(String(255), nullable=True, default=None)
    date: Mapped[datetime.date] = mapped_column(Date, index=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    category: Mapped[Category] = relationship(lazy="joined")

    @property
    def type(self) -> str:
        """Тип транзакції (дохід/витрата) береться з категорії"""
        return self.category.type
