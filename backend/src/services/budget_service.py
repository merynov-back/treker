from typing import List
from pydantic import TypeAdapter
from sqlalchemy.orm import Session
from src.exceptions import NotFoundError, ConflictError, BadRequestError
from src.models.budget import Budget
from src.models.category import CategoryType
from src.repositories.budget_repository import BudgetRepository
from src.repositories.category_repository import CategoryRepository
from src.repositories.transaction_repository import TransactionRepository
from src.schemas.budget import BudgetCreate, BudgetUpdate, BudgetStatus
from src.services.redis_service import RedisService
from src.utils.money import to_money, percent
from src.utils.periods import month_bounds

budget_status_adapter = TypeAdapter(List[BudgetStatus])


class BudgetService:
    def __init__(
            self,
            budget_repository: BudgetRepository,
            category_repository: CategoryRepository,
            transaction_repository: TransactionRepository,
            redis_service: RedisService,
    ):
        self.budget_repository = budget_repository
        self.category_repository = category_repository
        self.transaction_repository = transaction_repository
        self.redis_service = redis_service

    def list_budgets(self, db: Session, user_id: int, year: int, month: int) -> List[Budget]:
        return self.budget_repository.get_for_period(db, user_id, year, month)

    def get_budget(self, db: Session, user_id: int, budget_id: int) -> Budget:
        budget = self.budget_repository.get_by_id_for_user(db, budget_id, user_id)
        if budget is None:
            raise NotFoundError("Бюджет не знайдено")
        return budget

    def create_budget(self, db: Session, user_id: int, data: BudgetCreate) -> Budget:
        if data.category_id is not None:
            category = self.category_repository.get_by_id_for_user(db, data.category_id, user_id)
            if category is None:
                raise NotFoundError("Категорію не знайдено")
            if category.type != CategoryType.EXPENSE:
                raise BadRequestError("Ліміт можна встановити тільки на категорію витрат")

        if self.budget_repository.find(db, user_id, data.category_id, data.year, data.month):
            raise ConflictError("Бюджет на цей місяць для цієї категорії вже існує")

        budget = self.budget_repository.create(db, {"user_id": user_id, **data.model_dump()})
        self.redis_service.invalidate_user_cache(user_id)
        return budget

    def update_budget(self, db: Session, user_id: int, budget_id: int, data: BudgetUpdate) -> Budget:
        budget = self.get_budget(db, user_id, budget_id)
        budget = self.budget_repository.update(db, budget, data.model_dump())
        self.redis_service.invalidate_user_cache(user_id)
        return budget

    def delete_budget(self, db: Session, user_id: int, budget_id: int) -> None:
        budget = self.get_budget(db, user_id, budget_id)
        self.budget_repository.delete(db, budget.id)
        self.redis_service.invalidate_user_cache(user_id)

    def copy_from_previous_month(self, db: Session, user_id: int, year: int, month: int) -> List[Budget]:
        """Перенести ліміти з минулого місяця, яких ще немає в поточному"""
        prev_year, prev_month = (year - 1, 12) if month == 1 else (year, month - 1)
        existing = {b.category_id for b in self.budget_repository.get_for_period(db, user_id, year, month)}

        to_create = [
            {"user_id": user_id, "category_id": b.category_id, "amount": b.amount, "year": year, "month": month}
            for b in self.budget_repository.get_for_period(db, user_id, prev_year, prev_month)
            if b.category_id not in existing
        ]
        if not to_create:
            return []

        created = self.budget_repository.create_many(db, to_create)
        self.redis_service.invalidate_user_cache(user_id)
        return created

    def get_budget_status(self, db: Session, user_id: int, year: int, month: int) -> List[BudgetStatus]:
        return self.redis_service.get_or_compute(
            user_id,
            f"budgets:{year}-{month:02d}",
            budget_status_adapter,
            lambda: self._calculate_status(db, user_id, year, month),
        )

    def _calculate_status(self, db: Session, user_id: int, year: int, month: int) -> List[BudgetStatus]:
        budgets = self.budget_repository.get_for_period(db, user_id, year, month)
        if not budgets:
            return []

        date_from, date_to = month_bounds(year, month)
        rows = self.transaction_repository.totals_by_category(
            db, user_id, date_from, date_to, type=CategoryType.EXPENSE
        )
        spent_by_category = {row[0]: to_money(row[3]) for row in rows}
        total_spent = sum(spent_by_category.values(), to_money(0))

        result = []
        for budget in budgets:
            limit = to_money(budget.amount)
            if budget.category_id is None:
                spent, name = total_spent, "Усі витрати"
            else:
                spent, name = spent_by_category.get(budget.category_id, to_money(0)), budget.category.name

            result.append(BudgetStatus(
                budget_id=budget.id,
                category_id=budget.category_id,
                category_name=name,
                limit=limit,
                spent=spent,
                remaining=limit - spent,
                percent_used=percent(spent, limit),
                is_exceeded=spent > limit,
            ))
        return result
