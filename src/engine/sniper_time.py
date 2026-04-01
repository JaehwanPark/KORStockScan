"""Trading time rules for the sniper engine."""

from datetime import datetime, time as dt_time

from src.utils.constants import TRADING_RULES


def _rule_time(rule_name, default_value):
    raw = getattr(TRADING_RULES, rule_name, default_value)
    if isinstance(raw, dt_time):
        return raw
    try:
        return datetime.strptime(str(raw), "%H:%M:%S").time()
    except Exception:
        return datetime.strptime(default_value, "%H:%M:%S").time()


def _in_time_window(now_value, start, end):
    return (start <= now_value <= end) if start <= end else (now_value >= start or now_value <= end)


TIME_07_00 = _rule_time("PREMARKET_START_TIME", "07:00:00")
TIME_09_00 = _rule_time("MARKET_OPEN_TIME", "09:00:00")
TIME_09_03 = _rule_time("SCALPING_EARLIEST_BUY_TIME", "09:03:00")
TIME_09_05 = _rule_time("SWING_EARLIEST_BUY_TIME", "09:05:00")
TIME_09_10 = _rule_time("MORNING_BATCH_END_TIME", "09:10:00")
TIME_10_30 = _rule_time("MORNING_SCALPING_END_TIME", "10:30:00")
TIME_11_00 = _rule_time("MIDDAY_SCALPING_END_TIME", "11:00:00")
TIME_SCALPING_NEW_BUY_CUTOFF = _rule_time("SCALPING_NEW_BUY_CUTOFF", "15:00:00")
TIME_SCALPING_OVERNIGHT_DECISION = _rule_time("SCALPING_OVERNIGHT_DECISION_TIME", "15:15:00")
TIME_MARKET_CLOSE = _rule_time("MARKET_CLOSE_TIME", "15:30:00")
TIME_15_30 = TIME_MARKET_CLOSE
TIME_20_00 = _rule_time("SYSTEM_SHUTDOWN_TIME", "20:00:00")
TIME_23_59 = _rule_time("SYSTEM_DAY_END_TIME", "23:59:59")
