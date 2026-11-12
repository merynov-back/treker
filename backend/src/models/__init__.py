# Імпорт усіх моделей, щоб Alembic і create_all бачили таблиці
from src.models.user import User
from src.models.category import Category, CategoryType
from src.models.transaction import Transaction
from src.models.budget import Budget

__all__ = ["User", "Category", "CategoryType", "Transaction", "Budget"]
