import os

# Тестам не потрібні ні .env, ні Postgres — задаємо мінімум до імпорту застосунку
os.environ.setdefault("BASE_URL", "sqlite:///:memory:")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-key")
os.environ.setdefault("CORS_ORIGINS", '["http://localhost:5173"]')

from datetime import date
from decimal import Decimal
import fakeredis
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from starlette.testclient import TestClient

from src.main import app
from src.models import User, Category, Transaction
from src.models.base import Base
from src.dependencies.database import get_db
from src.dependencies.redis import get_redis_service
from src.repositories.budget_repository import BudgetRepository
from src.repositories.category_repository import CategoryRepository
from src.repositories.transaction_repository import TransactionRepository
from src.repositories.user_repository import UserRepository
from src.services.analytics_service import AnalyticsService
from src.services.auth_service import AuthService
from src.services.budget_service import BudgetService
from src.services.redis_service import RedisService


TEST_DATABASE_URL = "sqlite:///:memory:"
TEST_PASSWORD = "TestPass123!"


@pytest.fixture(scope="function")
def db_session() -> Session:
    """Чиста SQLite БД в пам'яті на кожен тест"""
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)

    session = sessionmaker(autoflush=False, bind=engine)()
    yield session

    session.close()
    engine.dispose()


@pytest.fixture(scope="function")
def redis_service() -> RedisService:
    """RedisService поверх fakeredis — сервер Redis не потрібен"""
    return RedisService(fakeredis.FakeRedis(decode_responses=True))


@pytest.fixture(scope="function")
def auth_service(redis_service) -> AuthService:
    return AuthService(UserRepository(), redis_service)


@pytest.fixture(scope="function")
def analytics_service(redis_service) -> AnalyticsService:
    return AnalyticsService(TransactionRepository(), redis_service)


@pytest.fixture(scope="function")
def budget_service(redis_service) -> BudgetService:
    return BudgetService(BudgetRepository(), CategoryRepository(), TransactionRepository(), redis_service)


@pytest.fixture(scope="function")
def client(db_session, redis_service):
    """HTTP-клієнт з підміненими залежностями БД і Redis"""
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_redis_service] = lambda: redis_service

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def user(db_session) -> User:
    """Активний користувач прямо в БД, минаючи HTTP"""
    user = User(
        name="Test User",
        email="test@example.com",
        password=AuthService.hash_password(TEST_PASSWORD),
        role="user",
        is_active=True,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_headers(client, user) -> dict:
    response = client.post("/auth/token", data={"username": user.email, "password": TEST_PASSWORD})
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture(scope="function")
def categories(db_session, user) -> dict[str, Category]:
    """Набір категорій: зарплата (дохід), продукти й транспорт (витрати)"""
    items = {
        "salary": Category(user_id=user.id, name="Зарплата", type="income"),
        "food": Category(user_id=user.id, name="Продукти", type="expense"),
        "transport": Category(user_id=user.id, name="Транспорт", type="expense"),
    }
    db_session.add_all(items.values())
    db_session.commit()
    return items


@pytest.fixture(scope="function")
def transactions(db_session, user, categories) -> list[Transaction]:
    """Жовтень 2026: дохід 30000, витрати 1500 + 500 + 1000 = 3000"""
    items = [
        Transaction(user_id=user.id, category_id=categories["salary"].id, amount=Decimal("30000"), date=date(2026, 10, 1)),
        Transaction(user_id=user.id, category_id=categories["food"].id, amount=Decimal("1500"), date=date(2026, 10, 2)),
        Transaction(user_id=user.id, category_id=categories["food"].id, amount=Decimal("500"), date=date(2026, 10, 15)),
        Transaction(user_id=user.id, category_id=categories["transport"].id, amount=Decimal("1000"), date=date(2026, 10, 15)),
        # Інший місяць — не має потрапляти у жовтневі звіти
        Transaction(user_id=user.id, category_id=categories["food"].id, amount=Decimal("999"), date=date(2026, 9, 30)),
    ]
    db_session.add_all(items)
    db_session.commit()
    return items
