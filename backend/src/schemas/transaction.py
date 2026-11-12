from datetime import date as Date, datetime
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field
from src.models.category import CategoryType
from src.schemas.common import Money
from src.utils.periods import today


class TransactionCreate(BaseModel):
    """Нова транзакція"""
    category_id: int
    amount: Money
    date: Date = Field(default_factory=today, examples=["2026-10-19"])
    description: Optional[str] = Field(None, max_length=255, examples=["Сільпо"])

class TransactionUpdate(BaseModel):
    """Часткове оновлення транзакції"""
    category_id: Optional[int] = None
    amount: Optional[Money] = None
    date: Optional[Date] = None
    description: Optional[str] = Field(None, max_length=255)

class TransactionRead(BaseModel):
    id: int
    category_id: int
    type: CategoryType
    amount: Decimal
    date: Date
    description: Optional[str]
    created_at: datetime
    model_config = {"from_attributes": True}
