from decimal import Decimal
from typing import Annotated
from pydantic import Field

# Сума завжди додатна, а дохід це чи витрата — визначає категорія
Money = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2, examples=["1250.50"])]
