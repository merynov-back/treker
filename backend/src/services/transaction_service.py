import csv
import io
from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session
from src.exceptions import NotFoundError, BadRequestError
from src.models.transaction import Transaction
from src.repositories.category_repository import CategoryRepository
from src.repositories.transaction_repository import TransactionRepository
from src.schemas.transaction import TransactionCreate, TransactionUpdate
from src.services.redis_service import RedisService


class TransactionService:
    def __init__(
            self,
            transaction_repository: TransactionRepository,
            category_repository: CategoryRepository,
            redis_service: RedisService,
    ):
        self.transaction_repository = transaction_repository
        self.category_repository = category_repository
        self.redis_service = redis_service

    def _ensure_category(self, db: Session, user_id: int, category_id: int) -> None:
        if self.category_repository.get_by_id_for_user(db, category_id, user_id) is None:
            raise NotFoundError("Категорію не знайдено")

    @staticmethod
    def _build_filters(
            date_from: Optional[date] = None,
            date_to: Optional[date] = None,
            category_id: Optional[int] = None,
            type: Optional[str] = None,
            search: Optional[str] = None,
    ) -> dict:
        if date_from and date_to and date_from > date_to:
            raise BadRequestError("date_from не може бути пізніше за date_to")

        return {
            "date_from": date_from,
            "date_to": date_to,
            "category_id": category_id,
            "type": type,
            "search": search.strip() if search else None,
        }

    def list_transactions(
            self,
            db: Session,
            user_id: int,
            skip: int = 0,
            limit: int = 100,
            **filters,
    ) -> tuple[List[Transaction], int]:
        """Сторінка транзакцій і загальна кількість під фільтром"""
        filters = self._build_filters(**filters)
        items = self.transaction_repository.get_filtered(db, user_id, skip=skip, limit=limit, **filters)
        total = self.transaction_repository.count_filtered(db, user_id, **filters)
        return items, total

    def export_csv(self, db: Session, user_id: int, **filters) -> str:
        """CSV під Excel з українською локаллю: роздільник «;», копійки через кому"""
        filters = self._build_filters(**filters)
        items = self.transaction_repository.get_filtered(db, user_id, skip=0, limit=None, **filters)

        output = io.StringIO()
        writer = csv.writer(output, delimiter=";")
        writer.writerow(["Дата", "Тип", "Категорія", "Сума", "Опис"])
        for t in items:
            writer.writerow([
                t.date.strftime("%d.%m.%Y"),
                "Дохід" if t.type == "income" else "Витрата",
                t.category.name,
                f"{t.amount:.2f}".replace(".", ","),
                t.description or "",
            ])

        # BOM — без нього Excel відкриє кирилицю кракозябрами
        return "\ufeff" + output.getvalue()

    def get_transaction(self, db: Session, user_id: int, transaction_id: int) -> Transaction:
        transaction = self.transaction_repository.get_by_id_for_user(db, transaction_id, user_id)
        if transaction is None:
            raise NotFoundError("Транзакцію не знайдено")
        return transaction

    def create_transaction(self, db: Session, user_id: int, data: TransactionCreate) -> Transaction:
        self._ensure_category(db, user_id, data.category_id)

        transaction = self.transaction_repository.create(db, {"user_id": user_id, **data.model_dump()})
        self.redis_service.invalidate_user_cache(user_id)
        return transaction

    def update_transaction(self, db: Session, user_id: int, transaction_id: int, data: TransactionUpdate) -> Transaction:
        transaction = self.get_transaction(db, user_id, transaction_id)

        # null можна передати лише для опису — щоб його очистити
        changes = {
            field: value
            for field, value in data.model_dump(exclude_unset=True).items()
            if value is not None or field == "description"
        }
        if "category_id" in changes:
            self._ensure_category(db, user_id, changes["category_id"])

        transaction = self.transaction_repository.update(db, transaction, changes)
        self.redis_service.invalidate_user_cache(user_id)
        return transaction

    def delete_transaction(self, db: Session, user_id: int, transaction_id: int) -> None:
        transaction = self.get_transaction(db, user_id, transaction_id)
        self.transaction_repository.delete(db, transaction.id)
        self.redis_service.invalidate_user_cache(user_id)
