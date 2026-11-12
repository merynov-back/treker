from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import Session
from src.models.budget import Budget
from src.repositories.base_repository import UserOwnedRepository


class BudgetRepository(UserOwnedRepository[Budget]):
    def __init__(self):
        super().__init__(Budget)

    def get_for_period(self, db: Session, user_id: int, year: int, month: int) -> List[Budget]:
        stmt = (
            select(Budget)
            .where(Budget.user_id == user_id, Budget.year == year, Budget.month == month)
            .order_by(Budget.category_id.is_not(None), Budget.id)
        )
        return list(db.scalars(stmt).all())

    def find(self, db: Session, user_id: int, category_id: Optional[int], year: int, month: int) -> Optional[Budget]:
        # NULL не рівний NULL в SQL, тому для загального ліміту окрема умова
        category_clause = Budget.category_id.is_(None) if category_id is None else Budget.category_id == category_id
        stmt = select(Budget).where(
            Budget.user_id == user_id,
            category_clause,
            Budget.year == year,
            Budget.month == month,
        )
        return db.execute(stmt).scalar_one_or_none()
