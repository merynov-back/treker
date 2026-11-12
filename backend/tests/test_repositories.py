"""Робота з БД без бізнес-логіки"""
from datetime import date

from src.models import User
from src.repositories.budget_repository import BudgetRepository
from src.repositories.category_repository import CategoryRepository
from src.repositories.transaction_repository import TransactionRepository
from src.repositories.user_repository import UserRepository


class TestUserRepository:

    def test_create_and_get_by_email(self, db_session):
        repo = UserRepository()
        created = repo.create(db_session, {"name": "Тест", "email": "repo@test.com", "password": "hash"})

        found = repo.get_by_email(db_session, "repo@test.com")
        assert found is not None
        assert found.id == created.id

    def test_get_by_email_missing(self, db_session):
        assert UserRepository().get_by_email(db_session, "nobody@test.com") is None


class TestOwnership:

    def test_foreign_category_is_invisible(self, db_session, categories):
        stranger = User(name="Чужий", email="stranger@test.com", password="hash")
        db_session.add(stranger)
        db_session.commit()

        found = CategoryRepository().get_by_id_for_user(db_session, categories["food"].id, stranger.id)
        assert found is None


class TestCategoryRepository:

    def test_filter_by_type(self, db_session, user, categories):
        expenses = CategoryRepository().get_all_for_user(db_session, user.id, "expense")
        assert {c.name for c in expenses} == {"Продукти", "Транспорт"}

    def test_has_transactions(self, db_session, categories, transactions):
        repo = CategoryRepository()
        assert repo.has_transactions(db_session, categories["food"].id) is True


class TestTransactionRepository:

    def test_filter_by_period_and_order(self, db_session, user, transactions):
        items = TransactionRepository().get_filtered(db_session, user.id, date_from=date(2026, 10, 1), date_to=date(2026, 10, 31))

        assert len(items) == 4
        # Від новіших до старіших
        assert items[0].date >= items[-1].date

    def test_filter_by_type(self, db_session, user, transactions):
        items = TransactionRepository().get_filtered(db_session, user.id, type="income")
        assert [t.type for t in items] == ["income"]


class TestBudgetRepository:

    def test_find_total_budget_with_null_category(self, db_session, user):
        repo = BudgetRepository()
        repo.create(db_session, {"user_id": user.id, "category_id": None, "amount": 5000, "year": 2026, "month": 10})

        assert repo.find(db_session, user.id, None, 2026, 10) is not None
        assert repo.find(db_session, user.id, None, 2026, 11) is None
