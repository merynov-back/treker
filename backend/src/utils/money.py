from decimal import Decimal

CENTS = Decimal("0.01")


def to_money(value) -> Decimal:
    """Привести суму з БД (Decimal, float, None) до Decimal з двома знаками"""
    if value is None:
        return Decimal("0.00")
    return Decimal(str(value)).quantize(CENTS)


def percent(part: Decimal, whole: Decimal) -> float:
    """Частка у відсотках, округлена до сотих"""
    if not whole:
        return 0.0
    return round(float(part / whole * 100), 2)
