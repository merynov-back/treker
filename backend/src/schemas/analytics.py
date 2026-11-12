from datetime import date
from decimal import Decimal
from enum import StrEnum
from pydantic import BaseModel
from src.models.category import CategoryType


class GroupBy(StrEnum):
    DAY = "day"
    MONTH = "month"


class Summary(BaseModel):
    """Підсумок за період"""
    date_from: date
    date_to: date
    income: Decimal
    expense: Decimal
    balance: Decimal
    transactions_count: int

class CategoryTotal(BaseModel):
    """Сума по категорії та її частка серед категорій того ж типу"""
    category_id: int
    category_name: str
    type: CategoryType
    total: Decimal
    percent: float
    transactions_count: int

class PeriodTotal(BaseModel):
    """Точка для графіка: день (YYYY-MM-DD) або місяць (YYYY-MM)"""
    period: str
    income: Decimal
    expense: Decimal
    balance: Decimal
