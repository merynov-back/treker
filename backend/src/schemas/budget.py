from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field
from src.schemas.common import Money


class BudgetCreate(BaseModel):
    """Ліміт витрат на місяць. Без category_id — загальний ліміт на всі витрати"""
    category_id: Optional[int] = None
    amount: Money
    year: int = Field(..., ge=2000, le=2100, examples=[2026])
    month: int = Field(..., ge=1, le=12, examples=[10])

class BudgetUpdate(BaseModel):
    """Змінити суму ліміту"""
    amount: Money

class BudgetRead(BaseModel):
    id: int
    category_id: Optional[int]
    amount: Decimal
    year: int
    month: int
    model_config = {"from_attributes": True}

class BudgetStatus(BaseModel):
    """Скільки витрачено з ліміту за місяць"""
    budget_id: int
    category_id: Optional[int]
    category_name: str
    limit: Decimal
    spent: Decimal
    remaining: Decimal
    percent_used: float
    is_exceeded: bool
