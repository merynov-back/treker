"""Ендпоінти цілком: HTTP → роутер → сервіс → БД"""
import pytest
from fastapi import FastAPI
from pydantic import ValidationError
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
from starlette.testclient import TestClient

from src.config import settings
from src.exceptions import register_exception_handlers, NotFoundError
from src.main import app
from src.models import User, Category
from src.schemas.user import UserRead
from src.services.category_service import CategoryService
from tests.conftest import TEST_PASSWORD


class TestHealthCheck:

    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestAuth:

    def test_register_and_login(self, client):
        response = client.post("/auth/register", json={"name": "Іван", "email": "ivan@example.com", "password": "StrongPass1!"})
        assert response.status_code == 201
        assert "password" not in response.json()

        response = client.post("/auth/token", data={"username": "ivan@example.com", "password": "StrongPass1!"})
        assert response.status_code == 200
        assert "access_token" in response.json()

    def test_register_creates_default_categories(self, client):
        client.post("/auth/register", json={"name": "Іван", "email": "ivan@example.com", "password": "StrongPass1!"})
        token = client.post("/auth/token", data={"username": "ivan@example.com", "password": "StrongPass1!"}).json()["access_token"]

        response = client.get("/categories", headers={"Authorization": f"Bearer {token}"})
        types = {c["type"] for c in response.json()}
        assert len(response.json()) == 10
        assert types == {"income", "expense"}

    def test_register_duplicate_returns_409(self, client, user):
        response = client.post("/auth/register", json={"name": "Дубль", "email": user.email, "password": "StrongPass1!"})
        assert response.status_code == 409

    def test_wrong_password_returns_401(self, client, user):
        response = client.post("/auth/token", data={"username": user.email, "password": "wrong-password"})
        assert response.status_code == 401

    def test_me_requires_token(self, client):
        assert client.get("/auth/me").status_code == 401

    def test_me(self, client, auth_headers, user):
        response = client.get("/auth/me", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["email"] == user.email

    def test_logout_kills_token(self, client, auth_headers):
        assert client.post("/auth/logout", headers=auth_headers).status_code == 200
        assert client.get("/auth/me", headers=auth_headers).status_code == 401

    def test_refresh(self, client, user):
        tokens = client.post("/auth/token", data={"username": user.email, "password": TEST_PASSWORD}).json()
        response = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
        assert response.status_code == 200


class TestCategories:

    def test_create_and_list(self, client, auth_headers):
        response = client.post("/categories", json={"name": "Кафе", "type": "expense"}, headers=auth_headers)
        assert response.status_code == 201

        response = client.get("/categories?type=expense", headers=auth_headers)
        assert [c["name"] for c in response.json()] == ["Кафе"]

    def test_duplicate_returns_409(self, client, auth_headers, categories):
        response = client.post("/categories", json={"name": "Продукти", "type": "expense"}, headers=auth_headers)
        assert response.status_code == 409

    def test_duplicate_ignores_case_and_spaces(self, client, auth_headers, categories):
        response = client.post("/categories", json={"name": "  ПРОДУКТИ ", "type": "expense"}, headers=auth_headers)
        assert response.status_code == 409

    def test_same_name_allowed_for_other_type(self, client, auth_headers, categories):
        response = client.post("/categories", json={"name": "Продукти", "type": "income"}, headers=auth_headers)
        assert response.status_code == 201

    def test_rename_only_case(self, client, auth_headers, categories):
        response = client.patch(f"/categories/{categories['food'].id}", json={"name": "продукти"}, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["name"] == "продукти"

    def test_delete_with_transactions_returns_409(self, client, auth_headers, categories, transactions):
        response = client.delete(f"/categories/{categories['food'].id}", headers=auth_headers)
        assert response.status_code == 409

    def test_delete_empty_category(self, client, auth_headers, categories):
        response = client.delete(f"/categories/{categories['transport'].id}", headers=auth_headers)
        assert response.status_code == 204


class TestTransactions:

    def test_crud(self, client, auth_headers, categories):
        response = client.post("/transactions", json={
            "category_id": categories["food"].id,
            "amount": "250.50",
            "date": "2026-10-19",
            "description": "Сільпо",
        }, headers=auth_headers)
        assert response.status_code == 201
        created = response.json()
        assert created["type"] == "expense"
        assert created["amount"] == "250.50"

        response = client.patch(f"/transactions/{created['id']}", json={"amount": "300"}, headers=auth_headers)
        assert response.json()["amount"] == "300.00"

        assert client.delete(f"/transactions/{created['id']}", headers=auth_headers).status_code == 204
        assert client.get(f"/transactions/{created['id']}", headers=auth_headers).status_code == 404

    def test_unknown_category_returns_404(self, client, auth_headers):
        response = client.post("/transactions", json={"category_id": 999, "amount": "10"}, headers=auth_headers)
        assert response.status_code == 404

    def test_filter_by_period(self, client, auth_headers, transactions):
        response = client.get("/transactions?date_from=2026-10-01&date_to=2026-10-31", headers=auth_headers)
        assert len(response.json()) == 4

    def test_edit_amount_description_and_category(self, client, auth_headers, categories, transactions):
        transaction_id = transactions[1].id
        response = client.patch(f"/transactions/{transaction_id}", json={
            "amount": "777.70",
            "description": "Новий опис",
            "category_id": categories["transport"].id,
        }, headers=auth_headers)

        data = response.json()
        assert data["amount"] == "777.70"
        assert data["description"] == "Новий опис"
        assert data["category_id"] == categories["transport"].id

    def test_search_by_description(self, client, auth_headers, categories):
        client.post("/transactions", json={"category_id": categories["food"].id, "amount": "10", "description": "Silpo market"}, headers=auth_headers)
        client.post("/transactions", json={"category_id": categories["food"].id, "amount": "20", "description": "ATB"}, headers=auth_headers)

        # lower() у SQLite не знає кирилиці, тому латиниця
        response = client.get("/transactions?search=silpo", headers=auth_headers)
        assert [t["description"] for t in response.json()] == ["Silpo market"]

    def test_search_by_category_name(self, client, auth_headers, transactions):
        response = client.get("/transactions?search=Транс", headers=auth_headers)
        assert len(response.json()) == 1

    def test_search_escapes_wildcards(self, client, auth_headers, transactions):
        response = client.get("/transactions?search=%25", headers=auth_headers)
        assert response.json() == []

    def test_invalid_period_returns_400(self, client, auth_headers):
        response = client.get("/transactions?date_from=2026-10-31&date_to=2026-10-01", headers=auth_headers)
        assert response.status_code == 400


class TestBudgetsAndAnalytics:

    def test_budget_status(self, client, auth_headers, categories, transactions):
        client.post("/budgets", json={"category_id": categories["food"].id, "amount": "1800", "year": 2026, "month": 10}, headers=auth_headers)

        response = client.get("/budgets/status?year=2026&month=10", headers=auth_headers)
        status = response.json()[0]
        assert status["spent"] == "2000.00"
        assert status["is_exceeded"] is True

    def test_summary(self, client, auth_headers, transactions):
        response = client.get("/analytics/summary?date_from=2026-10-01&date_to=2026-10-31", headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["balance"] == "27000.00"

    def test_by_category(self, client, auth_headers, transactions):
        response = client.get("/analytics/by-category?date_from=2026-10-01&date_to=2026-10-31&type=expense", headers=auth_headers)
        assert response.json()[0]["category_name"] == "Продукти"

    def test_daily_grouping_too_long_returns_400(self, client, auth_headers):
        response = client.get("/analytics/by-period?date_from=2024-01-01&date_to=2026-01-01&group_by=day", headers=auth_headers)
        assert response.status_code == 400


class TestSecurityAndConsistency:

    def test_parallel_refresh_with_same_token(self, client, user):
        tokens = client.post("/auth/token", data={"username": user.email, "password": TEST_PASSWORD}).json()

        first = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})
        second = client.post("/auth/refresh", json={"refresh_token": tokens["refresh_token"]})

        assert first.status_code == 200
        assert second.status_code == 401

    def test_login_blocked_after_failed_attempts(self, client, user):
        for _ in range(settings.LOGIN_MAX_ATTEMPTS):
            client.post("/auth/token", data={"username": user.email, "password": "wrong-password"})

        # Навіть правильний пароль не пускає, поки діє блок
        response = client.post("/auth/token", data={"username": user.email, "password": TEST_PASSWORD})
        assert response.status_code == 429
        assert int(response.headers["Retry-After"]) > 0

    def test_successful_login_resets_attempts(self, client, user):
        for _ in range(settings.LOGIN_MAX_ATTEMPTS - 1):
            client.post("/auth/token", data={"username": user.email, "password": "wrong-password"})
        client.post("/auth/token", data={"username": user.email, "password": TEST_PASSWORD})

        response = client.post("/auth/token", data={"username": user.email, "password": "wrong-password"})
        assert response.status_code == 401

    def test_register_is_atomic(self, client, db_session, monkeypatch):
        def broken(*args, **kwargs):
            raise RuntimeError("db is down")
        monkeypatch.setattr(CategoryService, "create_default_categories", broken)

        with TestClient(app, raise_server_exceptions=False) as raw_client:
            response = raw_client.post("/auth/register", json={"name": "Іван", "email": "atomic@example.com", "password": "StrongPass1!"})
        assert response.status_code == 500

        # get_db у проді закриває сесію з rollback
        db_session.rollback()
        assert db_session.scalar(select(func.count(User.id))) == 0

    def test_too_long_password_for_bcrypt(self, client):
        response = client.post("/auth/register", json={"name": "Іван", "email": "long@example.com", "password": "ж" * 40})
        assert response.status_code == 422

    def test_total_count_header(self, client, auth_headers, transactions):
        response = client.get("/transactions?limit=2", headers=auth_headers)

        assert len(response.json()) == 2
        assert response.headers["X-Total-Count"] == "5"

    def test_cors_allows_only_configured_origins(self, client):
        allowed = client.get("/", headers={"Origin": "http://localhost:5173"})
        evil = client.get("/", headers={"Origin": "https://evil.example"})

        assert allowed.headers.get("access-control-allow-origin") == "http://localhost:5173"
        assert "access-control-allow-origin" not in evil.headers

    def test_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "database": "ok", "redis": "ok"}

    def test_category_unique_ignores_case_in_db(self, db_session, user):
        db_session.add(Category(user_id=user.id, name="Cafe", type="expense"))
        db_session.commit()
        db_session.add(Category(user_id=user.id, name="cafe", type="expense"))

        with pytest.raises(IntegrityError):
            db_session.commit()


class TestErrorHandling:

    @staticmethod
    def make_client(error: Exception) -> TestClient:
        mini_app = FastAPI()
        register_exception_handlers(mini_app)

        @mini_app.get("/boom")
        def boom():
            raise error

        return TestClient(mini_app, raise_server_exceptions=False)

    def test_internal_validation_error_is_500_not_400(self):
        try:
            UserRead(id="not-int")
        except ValidationError as exc:
            error = exc

        response = self.make_client(error).get("/boom")
        assert response.status_code == 500

    def test_integrity_error_is_409(self):
        error = IntegrityError("INSERT ...", {}, Exception("duplicate key"))
        response = self.make_client(error).get("/boom")

        assert response.status_code == 409
        assert "duplicate" not in response.text

    def test_domain_error_status(self):
        assert self.make_client(NotFoundError("Немає")).get("/boom").status_code == 404


class TestProfile:

    def test_update_name(self, client, auth_headers):
        response = client.patch("/auth/me", json={"name": "Нове Ім'я"}, headers=auth_headers)
        assert response.status_code == 200
        assert response.json()["name"] == "Нове Ім'я"

    def test_change_password_revokes_other_sessions(self, client, user, auth_headers):
        other = client.post("/auth/token", data={"username": user.email, "password": TEST_PASSWORD}).json()
        other_headers = {"Authorization": f"Bearer {other['access_token']}"}

        response = client.post("/auth/change-password", json={
            "current_password": TEST_PASSWORD,
            "new_password": "BrandNewPass1!",
        }, headers=auth_headers)
        assert response.status_code == 200

        assert client.get("/auth/me", headers=auth_headers).status_code == 200
        assert client.get("/auth/me", headers=other_headers).status_code == 401
        login = client.post("/auth/token", data={"username": user.email, "password": "BrandNewPass1!"})
        assert login.status_code == 200

    def test_wrong_current_password_is_400(self, client, auth_headers):
        response = client.post("/auth/change-password", json={
            "current_password": "wrong-password",
            "new_password": "BrandNewPass1!",
        }, headers=auth_headers)
        assert response.status_code == 400


class TestExport:

    def test_csv_export(self, client, auth_headers, transactions):
        response = client.get("/transactions/export?date_from=2026-10-01&date_to=2026-10-31", headers=auth_headers)

        assert response.status_code == 200
        assert response.headers["content-type"].startswith("text/csv")
        lines = response.content.decode("utf-8-sig").strip().splitlines()
        assert lines[0] == "Дата;Тип;Категорія;Сума;Опис"
        assert len(lines) == 5
        assert "30000,00" in response.content.decode("utf-8-sig")


class TestCopyBudgets:

    def test_copy_from_previous_month(self, client, auth_headers, categories):
        client.post("/budgets", json={"category_id": categories["food"].id, "amount": "5000", "year": 2026, "month": 9}, headers=auth_headers)
        client.post("/budgets", json={"amount": "20000", "year": 2026, "month": 9}, headers=auth_headers)
        client.post("/budgets", json={"amount": "25000", "year": 2026, "month": 10}, headers=auth_headers)

        response = client.post("/budgets/copy-previous?year=2026&month=10", headers=auth_headers)

        # Загальний ліміт на жовтень уже був — переноситься лише ліміт на продукти
        assert response.status_code == 200
        assert [b["category_id"] for b in response.json()] == [categories["food"].id]

    def test_copy_across_year(self, client, auth_headers):
        client.post("/budgets", json={"amount": "1000", "year": 2025, "month": 12}, headers=auth_headers)
        response = client.post("/budgets/copy-previous?year=2026&month=1", headers=auth_headers)
        assert len(response.json()) == 1
