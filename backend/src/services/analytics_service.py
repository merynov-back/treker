from collections import defaultdict
from datetime import date
from decimal import Decimal
from operator import methodcaller
from typing import List, Optional
from pydantic import TypeAdapter
from sqlalchemy.orm import Session
from src.exceptions import BadRequestError
from src.models.category import CategoryType
from src.repositories.transaction_repository import TransactionRepository
from src.schemas.analytics import Summary, CategoryTotal, PeriodTotal, GroupBy
from src.services.redis_service import RedisService
from src.utils.money import to_money, percent
from src.utils.periods import resolve_period, iter_days, iter_months

summary_adapter = TypeAdapter(Summary)
category_totals_adapter = TypeAdapter(List[CategoryTotal])
period_totals_adapter = TypeAdapter(List[PeriodTotal])

# Захист від надто великих графіків по днях
MAX_DAYS_FOR_DAILY_GROUPING = 366


class AnalyticsService:
    """Звіти кешуються в Redis до наступної зміни даних користувача"""

    def __init__(self, transaction_repository: TransactionRepository, redis_service: RedisService):
        self.transaction_repository = transaction_repository
        self.redis_service = redis_service

    def get_summary(
            self,
            db: Session,
            user_id: int,
            date_from: Optional[date] = None,
            date_to: Optional[date] = None,
    ) -> Summary:
        date_from, date_to = resolve_period(date_from, date_to)

        def compute() -> Summary:
            totals = {CategoryType.INCOME: to_money(0), CategoryType.EXPENSE: to_money(0)}
            count = 0
            for type_, total, type_count in self.transaction_repository.totals_by_type(db, user_id, date_from, date_to):
                totals[CategoryType(type_)] = to_money(total)
                count += type_count

            return Summary(
                date_from=date_from,
                date_to=date_to,
                income=totals[CategoryType.INCOME],
                expense=totals[CategoryType.EXPENSE],
                balance=totals[CategoryType.INCOME] - totals[CategoryType.EXPENSE],
                transactions_count=count,
            )

        return self.redis_service.get_or_compute(
            user_id, f"summary:{date_from}:{date_to}", summary_adapter, compute
        )

    def get_by_category(
            self,
            db: Session,
            user_id: int,
            date_from: Optional[date] = None,
            date_to: Optional[date] = None,
            type: Optional[CategoryType] = None,
    ) -> List[CategoryTotal]:
        date_from, date_to = resolve_period(date_from, date_to)

        def compute() -> List[CategoryTotal]:
            rows = self.transaction_repository.totals_by_category(db, user_id, date_from, date_to, type)

            # Відсоток рахуємо в межах свого типу: витрати окремо, доходи окремо
            type_totals: dict[str, Decimal] = defaultdict(lambda: to_money(0))
            for _, _, type_, total, _ in rows:
                type_totals[type_] += to_money(total)

            return [
                CategoryTotal(
                    category_id=category_id,
                    category_name=name,
                    type=type_,
                    total=to_money(total),
                    percent=percent(to_money(total), type_totals[type_]),
                    transactions_count=count,
                )
                for category_id, name, type_, total, count in rows
            ]

        return self.redis_service.get_or_compute(
            user_id, f"by-category:{date_from}:{date_to}:{type or 'all'}", category_totals_adapter, compute
        )

    def get_by_period(
            self,
            db: Session,
            user_id: int,
            date_from: Optional[date] = None,
            date_to: Optional[date] = None,
            group_by: GroupBy = GroupBy.DAY,
    ) -> List[PeriodTotal]:
        date_from, date_to = resolve_period(date_from, date_to)

        if group_by == GroupBy.DAY and (date_to - date_from).days >= MAX_DAYS_FOR_DAILY_GROUPING:
            raise BadRequestError("Для періоду довше року використовуйте group_by=month")

        def compute() -> List[PeriodTotal]:
            if group_by == GroupBy.DAY:
                periods = [day.isoformat() for day in iter_days(date_from, date_to)]
                period_of = methodcaller("isoformat")
            else:
                periods = [f"{year}-{month:02d}" for year, month in iter_months(date_from, date_to)]
                period_of = methodcaller("strftime", "%Y-%m")

            # Заповнюємо нулями, щоб на графіку не було дірок
            buckets = {p: {CategoryType.INCOME: to_money(0), CategoryType.EXPENSE: to_money(0)} for p in periods}
            for day, type_, total in self.transaction_repository.totals_by_date(db, user_id, date_from, date_to):
                buckets[period_of(day)][CategoryType(type_)] += to_money(total)

            return [
                PeriodTotal(
                    period=p,
                    income=values[CategoryType.INCOME],
                    expense=values[CategoryType.EXPENSE],
                    balance=values[CategoryType.INCOME] - values[CategoryType.EXPENSE],
                )
                for p, values in buckets.items()
            ]

        return self.redis_service.get_or_compute(
            user_id, f"by-period:{date_from}:{date_to}:{group_by}", period_totals_adapter, compute
        )
