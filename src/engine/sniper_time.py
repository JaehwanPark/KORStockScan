"""Trading time rules for the sniper engine."""

from datetime import datetime, time as dt_time, timedelta, timezone

from src.utils.constants import TRADING_RULES

DEFAULT_SCALPING_BUY_WINDOWS = "08:01:00-08:40:00,09:01:00-15:00:00,16:00:00-19:45:00"
KST = timezone(timedelta(hours=9))


def _rule_time(rule_name, default_value):
    raw = getattr(TRADING_RULES, rule_name, default_value)
    if isinstance(raw, dt_time):
        return raw
    try:
        return datetime.strptime(str(raw), "%H:%M:%S").time()
    except Exception:
        return datetime.strptime(default_value, "%H:%M:%S").time()


def _in_time_window(now_value, start, end):
    return (
        (start <= now_value <= end)
        if start <= end
        else (now_value >= start or now_value <= end)
    )


def _parse_time_value(value):
    if isinstance(value, dt_time):
        return value
    return datetime.strptime(str(value), "%H:%M:%S").time()


def _rule_time_windows(rule_name, default_value):
    raw = getattr(TRADING_RULES, rule_name, default_value)
    for candidate in (raw, default_value):
        try:
            windows = []
            for token in str(candidate or "").split(","):
                token = token.strip()
                if not token:
                    continue
                start_raw, end_raw = token.split("-", 1)
                windows.append(
                    (
                        _parse_time_value(start_raw.strip()),
                        _parse_time_value(end_raw.strip()),
                    )
                )
            if windows:
                return tuple(windows)
        except Exception:
            continue
    return ((_parse_time_value("09:01:00"), _parse_time_value("15:00:00")),)


def _coerce_time(value):
    if value is None:
        return datetime.now().time()
    if isinstance(value, datetime):
        return value.time()
    if isinstance(value, dt_time):
        return value
    return _parse_time_value(value)


def describe_scalping_buy_windows(windows=None):
    active_windows = windows if windows is not None else SCALPING_BUY_WINDOWS
    return ",".join(
        f"{start.isoformat()}-{end.isoformat()}" for start, end in active_windows
    )


def is_scalping_buy_time_allowed(now_value=None):
    now_t = _coerce_time(now_value)
    return any(
        _in_time_window(now_t, start, end) for start, end in SCALPING_BUY_WINDOWS
    )


def scalping_buy_time_block_reason(now_value=None):
    now_t = _coerce_time(now_value)
    first_start = min(start for start, _end in SCALPING_BUY_WINDOWS)
    last_end = max(end for _start, end in SCALPING_BUY_WINDOWS)
    if now_t < first_start:
        return "before_strategy_start"
    if now_t > last_end:
        return "scalping_new_buy_cutoff"
    return "outside_scalping_buy_window"


def scalping_session_venue_provenance(now_value=None):
    """Resolve the scalping observation cohort without inferring broker route."""

    if now_value is None:
        now_t = datetime.now(tz=KST).time()
    elif isinstance(now_value, (int, float)):
        now_t = datetime.fromtimestamp(float(now_value), tz=KST).time()
    elif isinstance(now_value, datetime) and now_value.tzinfo is not None:
        now_t = now_value.astimezone(KST).time()
    else:
        now_t = _coerce_time(now_value)
    if dt_time(hour=8) <= now_t < dt_time(hour=9):
        venue = "PREMARKET_KRX_LIKE"
        session_bucket = "krx_like_premarket"
    elif dt_time(hour=9) <= now_t < dt_time(hour=15, minute=30):
        venue = "KRX"
        session_bucket = "krx_regular"
    elif dt_time(hour=16) <= now_t < dt_time(hour=20):
        venue = "NXT"
        session_bucket = "nxt"
    else:
        venue = "UNKNOWN"
        session_bucket = "outside_supported_session"
    return {
        "venue": venue,
        "effective_venue": venue,
        "venue_resolution": f"scanner_session_clock:{session_bucket}",
        "market_session_bucket": session_bucket,
    }


TIME_07_00 = _rule_time("PREMARKET_START_TIME", "07:00:00")
TIME_09_00 = _rule_time("MARKET_OPEN_TIME", "09:00:00")
TIME_09_03 = _rule_time("SCALPING_EARLIEST_BUY_TIME", "09:01:00")
TIME_09_05 = _rule_time("SWING_EARLIEST_BUY_TIME", "09:05:00")
TIME_09_10 = _rule_time("MORNING_BATCH_END_TIME", "09:10:00")
TIME_10_30 = _rule_time("MORNING_SCALPING_END_TIME", "10:30:00")
TIME_11_00 = _rule_time("MIDDAY_SCALPING_END_TIME", "11:00:00")
SCALPING_BUY_WINDOWS = _rule_time_windows(
    "SCALPING_BUY_WINDOWS", DEFAULT_SCALPING_BUY_WINDOWS
)
TIME_SCALPING_NEW_BUY_CUTOFF = _rule_time("SCALPING_NEW_BUY_CUTOFF", "19:45:00")
TIME_SCALPING_OVERNIGHT_DECISION = _rule_time(
    "SCALPING_OVERNIGHT_DECISION_TIME", "15:10:00"
)
TIME_MARKET_CLOSE = _rule_time("MARKET_CLOSE_TIME", "15:30:00")
TIME_15_30 = TIME_MARKET_CLOSE
TIME_20_00 = _rule_time("SYSTEM_SHUTDOWN_TIME", "20:00:00")
TIME_23_59 = _rule_time("SYSTEM_DAY_END_TIME", "23:59:59")
