from typing import Annotated, Optional
from pydantic import BaseModel, BeforeValidator, Field
from src.models.category import CategoryType


def _normalize_name(value):
    # «  Кафе   та  ресторани » → «Кафе та ресторани»
    return " ".join(value.split()) if isinstance(value, str) else value

CategoryName = Annotated[str, BeforeValidator(_normalize_name), Field(min_length=1, max_length=50, examples=["Продукти"])]


class CategoryCreate(BaseModel):
    """Нова категорія доходу або витрати"""
    name: CategoryName
    type: CategoryType = Field(..., examples=["expense"])

class CategoryUpdate(BaseModel):
    """Перейменування категорії. Тип змінити не можна — зламається історія транзакцій"""
    name: Optional[CategoryName] = None

class CategoryRead(BaseModel):
    id: int
    name: str
    type: CategoryType
    model_config = {"from_attributes": True}
