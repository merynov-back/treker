"""Бізнес-логіка сервісів: SQLite + fakeredis"""
from datetime import date
from decimal import Decimal

import pytest

from src.config import settings
from src.exceptions import AuthError, BadRequestError, ConflictError, NotFoundError
from src.schemas.analytics import GroupBy
from src.schemas.budget import BudgetCreate
from src.schemas.user import UserCreate
from src.services.auth_service import AuthService
from tests.conftest import TEST_PASSWORD


class TestPasswordHashing:

    def test_hash_differs_from_password(self):
        assert AuthService.hash_password("MyPassword123!") != "MyPassword123!"

    def test_verify_correct_and_wrong_password(self):
        hashed = AuthService.hash_password("MyPassword123!")
        assert AuthService.verify_password("MyPassword123!", hashed) is True
        assert AuthService.verify_password("wrong", hashed) is False


class TestAuthService:

    def test_register_lowercases_email(self, db_session, auth_service):
        user = auth_service.register_user(db_session, UserCreate(name="Іван", email="Ivan@Example.com", password="StrongPass1!"))
        assert user.email == "ivan@example.com"

    def test_register_duplicate_email(self, db_session, auth_service, user):
        with pytest.raises(ConflictError):
            auth_service.register_user(db_session, UserCreate(name="Дубль", email=user.email, password="StrongPass1!"))

    def test_login_creates_session(self, db_session, auth_service, redis_service, user):
        tokens = auth_service.login(db_session, user.email, TEST_PASSWORD)

        token_data = auth_service.decode_token(tokens.access_token)
        assert token_data.user_id == user.id
        assert redis_service.get_session_user_id(token_data.session_id) == user.id

    def test_login_wrong_password(self, db_session, auth_service, user):
        with pytest.raises(AuthError):
            auth_service.login(db_session, user.email, "wrong-password")

    def test_refresh_token_cannot_be_used_as_access(self, db_session, auth_service, user):
        tokens = auth_service.login(db_session, user.email, TEST_PASSWORD)
        with pytest.raises(AuthError):
            auth_service.decode_token(tokens.refresh_token, expected_type="access")

    def test_refresh_rotates_session(self, db_session, auth_service, user):
        old = auth_service.login(db_session, user.email, TEST_PASSWORD)
        new = auth_service.refresh_tokens(db_session, old.refresh_token)

        assert new.refresh_token != old.refresh_token
        # Старий refresh після ротації вже не працює
        with pytest.raises(AuthError):
            auth_service.refresh_tokens(db_session, old.refresh_token)

    def test_logout_invalidates_access_token(self, db_session, auth_service, user):
        tokens = auth_service.login(db_session, user.email, TEST_PASSWORD)
        session_id = auth_service.decode_token(tokens.access_token).session_id

        auth_service.logout(session_id)

        with pytest.raises(AuthError):
            auth_service.get_user_by_access_token(db_session, tokens.access_token)


class TestAnalyticsService:

    def test_summary(self, db_session, analytics_service, user, transactions):
        summary = analytics_service.get_summary(db_session, user.id, date(2026, 10, 1), date(2026, 10, 31))

        assert summary.income == Decimal("30000.00")
        assert summary.expense == Decimal("3000.00")
        assert summary.balance == Decimal("27000.00")
        assert summary.transactions_count == 4

    def test_by_category_percent_within_type(self, db_session, analytics_service, user, transactions):
        totals = analytics_service.get_by_category(db_session, user.id, date(2026, 10, 1), date(2026, 10, 31), "expense")

        assert [t.category_name for t in totals] == ["Продукти", "Транспорт"]
        assert totals[0].total == Decimal("2000.00")
        assert totals[0].percent == pytest.approx(66.67)
        assert totals[1].percent == pytest.approx(33.33)

    def test_by_period_fills_empty_days(self, db_session, analytics_service, user, transactions):
        points = analytics_service.get_by_period(db_session, user.id, date(2026, 10, 1), date(2026, 10, 3), GroupBy.DAY)

        assert [p.period for p in points] == ["2026-10-01", "2026-10-02", "2026-10-03"]
        assert points[2].income == points[2].expense == Decimal("0.00")

    def test_by_period_months(self, db_session, analytics_service, user, transactions):
        points = analytics_service.get_by_period(db_session, user.id, date(2026, 9, 1), date(2026, 10, 31), GroupBy.MONTH)

        assert [p.period for p in points] == ["2026-09", "2026-10"]
        assert points[0].expense == Decimal("999.00")
        assert points[1].balance == Decimal("27000.00")

    def test_invalid_period(self, db_session, analytics_service, user):
        with pytest.raises(BadRequestError):
            analytics_service.get_summary(db_session, user.id, date(2026, 10, 31), date(2026, 10, 1))


class TestBudgetService:

    def test_status_for_category_and_total(self, db_session, budget_service, user, categories, transactions):
        budget_service.create_budget(db_session, user.id, BudgetCreate(category_id=categories["food"].id, amount=Decimal("1800"), year=2026, month=10))
        budget_service.create_budget(db_session, user.id, BudgetCreate(amount=Decimal("5000"), year=2026, month=10))

        statuses = {s.category_name: s for s in budget_service.get_budget_status(db_session, user.id, 2026, 10)}

        assert statuses["Продукти"].spent == Decimal("2000.00")
        assert statuses["Продукти"].is_exceeded is True
        assert statuses["Усі витрати"].spent == Decimal("3000.00")
        assert statuses["Усі витрати"].remaining == Decimal("2000.00")

    def test_budget_on_income_category_rejected(self, db_session, budget_service, user, categories):
        with pytest.raises(BadRequestError):
            budget_service.create_budget(db_session, user.id, BudgetCreate(category_id=categories["salary"].id, amount=Decimal("100"), year=2026, month=10))

    def test_duplicate_total_budget(self, db_session, budget_service, user):
        data = BudgetCreate(amount=Decimal("5000"), year=2026, month=10)
        budget_service.create_budget(db_session, user.id, data)
        with pytest.raises(ConflictError):
            budget_service.create_budget(db_session, user.id, data)

    def test_foreign_category_not_found(self, db_session, budget_service, user):
        with pytest.raises(NotFoundError):
            budget_service.create_budget(db_session, user.id, BudgetCreate(category_id=999, amount=Decimal("100"), year=2026, month=10))

    def test_changes_invalidate_cache(self, db_session, budget_service, user, categories, transactions):
        budget_service.create_budget(db_session, user.id, BudgetCreate(category_id=categories["food"].id, amount=Decimal("5000"), year=2026, month=10))
        before = budget_service.get_budget_status(db_session, user.id, 2026, 10)

        # Новий ліміт скидає кеш — у статусі одразу два бюджети, а не закешований один
        budget_service.create_budget(db_session, user.id, BudgetCreate(amount=Decimal("9000"), year=2026, month=10))
        after = budget_service.get_budget_status(db_session, user.id, 2026, 10)

        assert len(before) == 1
        assert len(after) == 2


class TestTimezone:

    def test_today_uses_app_timezone(self, monkeypatch):
        from src.utils.periods import today

        # UTC+14 і UTC-11: дати відрізняються завжди
        monkeypatch.setattr(settings, "APP_TIMEZONE", "Pacific/Kiritimati")
        ahead = today()
        monkeypatch.setattr(settings, "APP_TIMEZONE", "Pacific/Pago_Pago")
        behind = today()

        assert ahead > behind
