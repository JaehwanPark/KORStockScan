from __future__ import annotations

from datetime import date, timedelta


def get_krx_trading_day_status(target: date) -> tuple[bool, str]:
    if target.weekday() >= 5:
        return False, "weekend"

    try:
        import holidays  # type: ignore

        kr_holidays = holidays.KR(years=[target.year, target.year + 1])
        if target in kr_holidays:
            return False, f"holiday:{kr_holidays.get(target)}"
    except Exception:
        pass

    if target.month == 5 and target.day == 1:
        return False, "market_holiday:workers_day"
    if target.month == 12 and target.day == 31:
        return False, "market_holiday:year_end_close"

    return True, "trading_day"


def is_krx_trading_day(target: date) -> bool:
    return get_krx_trading_day_status(target)[0]


def count_krx_trading_days(start_exclusive: date, end_inclusive: date) -> int:
    """Count KRX trading days in ``(start_exclusive, end_inclusive]``."""
    if end_inclusive <= start_exclusive:
        return 0
    current = start_exclusive + timedelta(days=1)
    count = 0
    while current <= end_inclusive:
        if is_krx_trading_day(current):
            count += 1
        current += timedelta(days=1)
    return count
