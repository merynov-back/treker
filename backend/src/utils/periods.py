import calendar
from datetime import date, datetime, timedelta
from typing import Iterator, Optional
from zoneinfo import ZoneInfo
from src.config import settings
from src.exceptions import BadRequestError


def today() -> date:
    """Сьогодні в поясі застосунку, а не в UTC сервера"""
    return datetime.now(ZoneInfo(settings.APP_TIMEZONE)).date()


def month_bounds(year: int, month: int) -> tuple[date, date]:
    """Перший і останній день місяця"""
    last_day = calendar.monthrange(year, month)[1]
    return date(year, month, 1), date(year, month, last_day)


def resolve_period(date_from: Optional[date], date_to: Optional[date]) -> tuple[date, date]:
    """
    Підставити поточний місяць, якщо межі не передані.
    Кидає BadRequestError, якщо початок пізніше кінця
    """
    current = today()
    default_from, default_to = month_bounds(current.year, current.month)
    date_from = date_from or default_from
    date_to = date_to or default_to

    if date_from > date_to:
        raise BadRequestError("date_from не може бути пізніше за date_to")
    return date_from, date_to


def iter_days(date_from: date, date_to: date) -> Iterator[date]:
    current = date_from
    while current <= date_to:
        yield current
        current += timedelta(days=1)


def iter_months(date_from: date, date_to: date) -> Iterator[tuple[int, int]]:
    year, month = date_from.year, date_from.month
    while (year, month) <= (date_to.year, date_to.month):
        yield year, month
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
