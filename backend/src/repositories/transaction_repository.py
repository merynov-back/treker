from datetime import date
from typing import Optional, List
from sqlalchemy import select, func, or_, Row, Select
from sqlalchemy.orm import Session
from src.models.category import Category
from src.models.transaction import Transaction
from src.repositories.base_repository import UserOwnedRepository


class TransactionRepository(UserOwnedRepository[Transaction]):
    def __init__(self):
        super().__init__(Transaction)

    def get_filtered(
            self,
            db: Session,
            user_id: int,
            skip: int = 0,
            limit: Optional[int] = 100,
            **filters,
    ) -> List[Transaction]:
        stmt = self._filtered_stmt(user_id, **filters)
        stmt = stmt.order_by(Transaction.date.desc(), Transaction.id.desc()).offset(skip).limit(limit)
        return list(db.scalars(stmt).all())

    def count_filtered(self, db: Session, user_id: int, **filters) -> int:
        stmt = self._filtered_stmt(user_id, **filters).with_only_columns(func.count(Transaction.id))
        return db.scalar(stmt)

    @staticmethod
    def _filtered_stmt(
            user_id: int,
            date_from: Optional[date] = None,
            date_to: Optional[date] = None,
            category_id: Optional[int] = None,
            type: Optional[str] = None,
            search: Optional[str] = None,
    ) -> Select:
        stmt = select(Transaction).join(Transaction.category).where(Transaction.user_id == user_id)

        if search:
            # autoescape — щоб % і _ з пошуку не працювали як шаблон LIKE
            stmt = stmt.where(or_(
                Transaction.description.icontains(search, autoescape=True),
                Category.name.icontains(search, autoescape=True),
            ))

        if date_from:
            stmt = stmt.where(Transaction.date >= date_from)
        if date_to:
            stmt = stmt.where(Transaction.date <= date_to)
        if category_id:
            stmt = stmt.where(Transaction.category_id == category_id)
        if type:
            stmt = stmt.where(Category.type == type)
        return stmt

    def totals_by_type(self, db: Session, user_id: int, date_from: date, date_to: date) -> List[Row]:
        # (type, total, count)
        stmt = (
            select(Category.type, func.sum(Transaction.amount), func.count(Transaction.id))
            .join(Transaction.category)
            .where(
                Transaction.user_id == user_id,
                Transaction.date.between(date_from, date_to),
            )
            .group_by(Category.type)
        )
        return list(db.execute(stmt).all())

    def totals_by_category(
            self,
            db: Session,
            user_id: int,
            date_from: date,
            date_to: date,
            type: Optional[str] = None,
    ) -> List[Row]:
        # (category_id, name, type, total, count), від більшої суми
        total = func.sum(Transaction.amount)
        stmt = (
            select(Category.id, Category.name, Category.type, total, func.count(Transaction.id))
            .join(Transaction.category)
            .where(
                Transaction.user_id == user_id,
                Transaction.date.between(date_from, date_to),
            )
            .group_by(Category.id, Category.name, Category.type)
            .order_by(total.desc())
        )
        if type:
            stmt = stmt.where(Category.type == type)
        return list(db.execute(stmt).all())

    def totals_by_date(self, db: Session, user_id: int, date_from: date, date_to: date) -> List[Row]:
        # (date, type, total)
        stmt = (
            select(Transaction.date, Category.type, func.sum(Transaction.amount))
            .join(Transaction.category)
            .where(
                Transaction.user_id == user_id,
                Transaction.date.between(date_from, date_to),
            )
            .group_by(Transaction.date, Category.type)
        )
        return list(db.execute(stmt).all())
