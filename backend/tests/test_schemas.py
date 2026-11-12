"""Валідація вхідних даних"""
from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from src.schemas.budget import BudgetCreate
from src.schemas.category import CategoryCreate
from src.schemas.transaction import TransactionCreate
from src.schemas.user import UserCreate


class TestUserCreate:

    def test_valid(self):
        user = UserCreate(name="Іван Петренко", email="ivan@example.com", password="StrongPass1!")
        assert user.name == "Іван Петренко"

    def test_short_password(self):
        with pytest.raises(ValidationError):
            UserCreate(name="Іван", email="ivan@example.com", password="short")

    def test_invalid_email(self):
        with pytest.raises(ValidationError):
            UserCreate(name="Іван", email="not-an-email", password="StrongPass1!")


class TestCategoryCreate:

    def test_unknown_type(self):
        with pytest.raises(ValidationError):
            CategoryCreate(name="Щось", type="savings")


class TestTransactionCreate:

    def test_date_defaults_to_today(self):
        transaction = TransactionCreate(category_id=1, amount=Decimal("10"))
        assert transaction.date == date.today()

    @pytest.mark.parametrize("amount", ["0", "-5", "10.555", "12345678901.00"])
    def test_invalid_amount(self, amount):
        with pytest.raises(ValidationError):
            TransactionCreate(category_id=1, amount=Decimal(amount))


class TestBudgetCreate:

    def test_month_out_of_range(self):
        with pytest.raises(ValidationError):
            BudgetCreate(amount=Decimal("100"), year=2026, month=13)
