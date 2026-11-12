from typing import Optional, List
from sqlalchemy import select, exists
from sqlalchemy.orm import Session
from src.models.category import Category
from src.models.transaction import Transaction
from src.repositories.base_repository import UserOwnedRepository


class CategoryRepository(UserOwnedRepository[Category]):
    def __init__(self):
        super().__init__(Category)

    def get_all_for_user(self, db: Session, user_id: int, type: Optional[str] = None) -> List[Category]:
        stmt = select(Category).where(Category.user_id == user_id)
        if type:
            stmt = stmt.where(Category.type == type)
        return list(db.scalars(stmt.order_by(Category.type, Category.name)).all())

    def get_by_name(self, db: Session, user_id: int, name: str, type: str) -> Optional[Category]:
        # Без урахування регістру. Порівнюємо в Python: lower() в SQLite не знає кирилиці
        key = name.casefold()
        return next(
            (category for category in self.get_all_for_user(db, user_id, type) if category.name.casefold() == key),
            None,
        )

    def has_transactions(self, db: Session, category_id: int) -> bool:
        stmt = select(exists().where(Transaction.category_id == category_id))
        return bool(db.scalar(stmt))
