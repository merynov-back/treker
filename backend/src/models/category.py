from enum import StrEnum
from sqlalchemy import String, Integer, ForeignKey, Index, func
from sqlalchemy.orm import mapped_column, Mapped
from src.models.base import Base


class CategoryType(StrEnum):
    INCOME = "income"
    EXPENSE = "expense"


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(50))
    type: Mapped[str] = mapped_column(String(10))


# Одна назва в межах типу для кожного користувача, без урахування регістру: «Кафе» = «кафе»
Index(
    "uq_categories_user_lower_name_type",
    Category.user_id, func.lower(Category.name), Category.type,
    unique=True,
)
