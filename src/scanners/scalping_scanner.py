import sys
from pathlib import Path
import os

# ==========================================
# 🚀 [핵심 1] 단독 실행을 위한 루트 경로 탐지
# ==========================================
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

import time
from datetime import datetime, timedelta
from math import ceil, log10

# 💡 Level 1 & 2 공통 모듈 임포트
from src.utils import kiwoom_utils
from src.utils.logger import log_error, log_info
from src.database.db_manager import DBManager
from src.database.models import RecommendationHistory
from src.core.event_bus import EventBus
from src.engine.signal_radar import SniperRadar
from src.engine.scalping.watch_budget import (
    GENERAL_SCALPING,
    OPENING_ROTATION,
    RISING_MISSED,
    classify_owner as classify_watch_budget_owner,
    limits as watch_budget_limits,
)
from src.engine.scalping.opening_rotation import EntryConfig as OpeningRotationConfig
from src.engine.sniper_time import (
    SCALPING_BUY_WINDOWS,
    describe_scalping_buy_windows,
    is_scalping_buy_time_allowed,
)
from src.utils.constants import TRADING_RULES
from src.utils.pipeline_event_logger import emit_pipeline_event
from sqlalchemy import func, or_

SCANNER_RISING_START_SOURCE_FAMILY = "scalping_scanner_rising_start_source_v1"
LOW_REBOUND_RISING_MISSED_SOURCE = "LOW_REBOUND_RISING_MISSED"
LOW_REBOUND_RISING_MISSED_SOURCE_FAMILY = "rising_missed_low_rebound_source_v1"
LOW_REBOUND_RISING_MISSED_ROLE = "rising_missed_low_rebound_candidate"
LOW_REBOUND_RISING_MISSED_LINEAGE = "low_rebound_from_intraday_low"
HIGH_PROXIMITY_CONFIRMATION_SOURCE = "HIGH_PROXIMITY_CONFIRMATION"
NEW_HIGH_CONFIRMATION_SOURCE = "NEW_HIGH_CONFIRMATION"
BREAKOUT_CONFIRMATION_SOURCES = {
    HIGH_PROXIMITY_CONFIRMATION_SOURCE,
    NEW_HIGH_CONFIRMATION_SOURCE,
}
RANK_CHANGE_SIGN_AUTHORITY_DEFAULT = "raw_unverified_not_decision_input"
SCANNER_PROMOTION_POLICY_VERSION = (
    "scanner_priority_v6_20260709_breakout_confirmation_enrichment"
)
SCANNER_UNDER_10000_PRIORITY_PRICE_CEILING = 10000
SCANNER_UNDER_10000_VOLUME_SURGE_RANK_PCT_DEFAULT = 0.40
SCANNER_UNDER_10000_VOLUME_SURGE_RANK_MIN_COUNT_DEFAULT = 10
SCANNER_SOURCE_IDENTITY_QUARANTINE_SEC_DEFAULT = 300
PRIMARY_RISING_START_SOURCES = {
    "REALTIME_RANK_START",
    "PRICE_JUMP_START",
    "VOLUME_SURGE_POSITIVE",
    "BID_IMBALANCE_SURGE",
}
LOW_REBOUND_BASE_SOURCES = {"VOLUME_SURGE_RAW", "VALUE_TOP", "REALTIME_RANK_START"}
LOW_REBOUND_PREFETCH_EXCLUDED_NAME_KEYWORDS = (
    "스팩",
    "ETF",
    "ETN",
    "TIGER",
    "KBSTAR",
    "KODEX",
    "KINDEX",
    "ARIRANG",
    "KOSEF",
    "리츠",
    "HANARO",
    "SOL ",
    "ACE ",
    "RISE ",
    "PLUS ",
    "TIMEFOLIO",
    "KIWOOM ",
    "선물",
    "레버리지",
    "블룸버그",
    "VIX",
    "인버스",
)


def _resolve_scan_interval_sec(now_time):
    """장 초반/후반에는 더 자주 돌리고, 점심/NXT 구간은 약간 완화합니다."""
    hhmm = now_time.hour * 100 + now_time.minute
    if 905 <= hhmm < 1030:
        return 60
    if 1400 <= hhmm <= 1500:
        return 60
    return 90


def _parse_scan_time_env(env_name, default_value):
    raw_value = os.getenv(env_name, default_value)
    try:
        return datetime.strptime(str(raw_value), "%H:%M:%S").time()
    except (TypeError, ValueError):
        log_error(
            f"⚠️ {env_name} 값이 잘못되어 기본값을 사용합니다: {raw_value} -> {default_value}"
        )
        return datetime.strptime(default_value, "%H:%M:%S").time()


def _resolve_scanner_discovery_window():
    """Compatibility view for logs; discovery itself follows SCALPING_BUY_WINDOWS."""
    market_open = min(start for start, _end in SCALPING_BUY_WINDOWS)
    market_close = max(end for _start, end in SCALPING_BUY_WINDOWS)
    return market_open, market_close


def _is_scanner_discovery_time(now_time):
    return is_scalping_buy_time_allowed(now_time)


def _time_in_window(now_time, start, end):
    return (
        start <= now_time <= end
        if start <= end
        else now_time >= start or now_time <= end
    )


def _active_scalping_buy_window(now_dt):
    now_time = now_dt.time()
    for index, (start, end) in enumerate(SCALPING_BUY_WINDOWS):
        if _time_in_window(now_time, start, end):
            return index, start, end
    return None


def _window_start_epoch(now_dt, start):
    start_dt = datetime.combine(now_dt.date(), start)
    if start > now_dt.time():
        start_dt -= timedelta(days=1)
    return start_dt.timestamp()


def _scalping_watching_max_active():
    raw = os.getenv("KORSTOCKSCAN_SCALPING_WATCHING_MAX_ACTIVE", "")
    try:
        value = int(str(raw).strip()) if str(raw).strip() else 16
    except (TypeError, ValueError):
        value = 16
    return max(1, min(value, 80))


def _scanner_watch_budget_reallocation_enabled():
    raw = os.getenv("KORSTOCKSCAN_SCANNER_WATCH_BUDGET_REALLOCATION_ENABLED", "")
    if not str(raw).strip():
        return True
    return str(raw).strip().lower() in {"1", "true", "yes", "y", "on"}


def _scanner_watch_budget_opening_config():
    def _rule_value(name, default):
        return getattr(TRADING_RULES, name, default)

    def _opening_time(env_name, default, hard_default):
        raw = str(os.getenv(env_name, default) or "").strip()
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(raw, fmt).time()
            except (TypeError, ValueError):
                continue
        log_error(
            f"⚠️ {env_name} 값이 잘못되어 기본값을 사용합니다: {raw} -> {default}"
        )
        for fmt in ("%H:%M:%S", "%H:%M"):
            try:
                return datetime.strptime(str(default), fmt).time()
            except (TypeError, ValueError):
                continue
        return datetime.strptime(hard_default, "%H:%M:%S").time()

    enabled_raw = os.getenv(
        "KORSTOCKSCAN_OPENING_ROTATION_1PCT_ENABLED",
        str(_rule_value("OPENING_ROTATION_1PCT_ENABLED", True)),
    )
    enabled = (
        enabled_raw
        if isinstance(enabled_raw, bool)
        else str(enabled_raw).strip().lower() in {"1", "true", "yes", "y", "on"}
    )

    observe_default = str(_rule_value("OPENING_ROTATION_1PCT_OBSERVE_START", "09:01"))
    entry_end_default = str(_rule_value("OPENING_ROTATION_1PCT_ENTRY_END", "15:00"))
    return OpeningRotationConfig(
        enabled=enabled,
        observe_start=_opening_time(
            "KORSTOCKSCAN_OPENING_ROTATION_1PCT_OBSERVE_START",
            observe_default,
            "09:01:00",
        ),
        entry_end=_opening_time(
            "KORSTOCKSCAN_OPENING_ROTATION_1PCT_ENTRY_END",
            entry_end_default,
            "15:00:00",
        ),
        min_day_change_pct=_safe_float(
            os.getenv(
                "KORSTOCKSCAN_OPENING_ROTATION_1PCT_MIN_DAY_CHANGE_PCT",
                _rule_value("OPENING_ROTATION_1PCT_MIN_DAY_CHANGE_PCT", 1.5),
            ),
            1.5,
        ),
        max_day_change_pct=_safe_float(
            os.getenv(
                "KORSTOCKSCAN_OPENING_ROTATION_1PCT_MAX_DAY_CHANGE_PCT",
                _rule_value("OPENING_ROTATION_1PCT_MAX_DAY_CHANGE_PCT", 8.0),
            ),
            8.0,
        ),
    )


def _low_rebound_reserve_slots():
    raw = os.getenv("KORSTOCKSCAN_SCALP_SCANNER_LOW_REBOUND_RESERVE_SLOTS", "")
    try:
        value = int(str(raw).strip()) if str(raw).strip() else 2
    except (TypeError, ValueError):
        value = 2
    return max(0, min(value, 10))


def _low_rebound_active_floor():
    raw = os.getenv("KORSTOCKSCAN_SCALP_SCANNER_LOW_REBOUND_ACTIVE_FLOOR", "")
    try:
        value = int(str(raw).strip()) if str(raw).strip() else 2
    except (TypeError, ValueError):
        value = 2
    return max(0, min(value, 10))


def _low_rebound_floor_replacement_max_per_loop():
    raw = os.getenv(
        "KORSTOCKSCAN_SCALP_SCANNER_LOW_REBOUND_FLOOR_REPLACE_MAX_PER_LOOP", ""
    )
    try:
        value = int(str(raw).strip()) if str(raw).strip() else 2
    except (TypeError, ValueError):
        value = 2
    return max(0, min(value, 5))


def _scanner_after_buy_window_cap_release_enabled():
    raw = os.getenv("KORSTOCKSCAN_SCANNER_AFTER_BUY_WINDOW_CAP_RELEASE_ENABLED", "")
    text = str(raw).strip().lower()
    if not text:
        return True
    return text in {"1", "true", "yes", "y", "on"}


def _scanner_after_buy_window_cap_release_start_time():
    raw = os.getenv(
        "KORSTOCKSCAN_SCANNER_AFTER_BUY_WINDOW_CAP_RELEASE_START_TIME", ""
    ) or os.getenv(
        "KORSTOCKSCAN_SCANNER_AFTER_BUY_WINDOW_SOURCE_QUALITY_EVICTION_START_TIME", ""
    )
    if not str(raw).strip():
        return None
    try:
        return datetime.strptime(str(raw).strip(), "%H:%M:%S").time()
    except (TypeError, ValueError):
        log_error(
            f"⚠️ KORSTOCKSCAN_SCANNER_AFTER_BUY_WINDOW_CAP_RELEASE_START_TIME 값이 잘못되었습니다: {raw}"
        )
        return None


def _scanner_after_buy_window_cap_release_min_age_sec():
    raw = os.getenv("KORSTOCKSCAN_SCANNER_AFTER_BUY_WINDOW_CAP_RELEASE_MIN_AGE_SEC", "")
    try:
        value = float(str(raw).strip()) if str(raw).strip() else 60.0
    except (TypeError, ValueError):
        value = 60.0
    return max(10.0, min(value, 900.0))


def _scanner_after_buy_window_cap_release_max_per_loop():
    raw = os.getenv(
        "KORSTOCKSCAN_SCANNER_AFTER_BUY_WINDOW_CAP_RELEASE_MAX_PER_LOOP", ""
    )
    try:
        value = int(str(raw).strip()) if str(raw).strip() else 4
    except (TypeError, ValueError):
        value = 4
    return max(0, min(value, 20))


def _expire_after_buy_window_scanner_watching(db, now_ts):
    if not _scanner_after_buy_window_cap_release_enabled():
        return 0
    start_time = _scanner_after_buy_window_cap_release_start_time()
    if start_time is None or datetime.fromtimestamp(float(now_ts)).time() < start_time:
        return 0
    max_per_loop = _scanner_after_buy_window_cap_release_max_per_loop()
    if max_per_loop <= 0:
        return 0
    min_age_sec = _scanner_after_buy_window_cap_release_min_age_sec()
    expired_codes = _expire_scanner_watching_records(
        db,
        now_ts,
        max_per_loop=max_per_loop,
        min_age_sec=min_age_sec,
        position_tag="SCANNER",
        reason="after_window_cap_release",
    )
    if expired_codes:
        log_info(
            "[SCALPING_SCANNER_AFTER_WINDOW_CAP_RELEASE] "
            f"expired={len(expired_codes)} codes={','.join(code for code in expired_codes if code)} "
            f"start_time={start_time.isoformat()} min_age_sec={min_age_sec} max_per_loop={max_per_loop}"
        )
    return len(expired_codes)


def _expire_scanner_watching_records(
    db,
    now_ts,
    *,
    max_per_loop=None,
    min_age_sec=0.0,
    armed_before_epoch=None,
    position_tag=None,
    reason="buy_window_reset",
):
    expired_codes = []
    try:
        with db.get_session() as session:
            if hasattr(session, "query"):
                records = (
                    session.query(RecommendationHistory)
                    .filter(
                        RecommendationHistory.rec_date == datetime.now().date(),
                        RecommendationHistory.status == "WATCHING",
                        RecommendationHistory.strategy == "SCALPING",
                        RecommendationHistory.buy_time.is_(None),
                        RecommendationHistory.buy_qty == 0,
                    )
                    .all()
                )
            else:
                records = list(getattr(session, "records", []))
            candidates = []
            for record in records:
                if getattr(record, "status", None) != "WATCHING":
                    continue
                if getattr(record, "strategy", None) != "SCALPING":
                    continue
                if (
                    position_tag is not None
                    and getattr(record, "position_tag", None) != position_tag
                ):
                    continue
                if getattr(record, "buy_time", None) is not None:
                    continue
                if int(getattr(record, "buy_qty", 0) or 0) != 0:
                    continue
                armed_ts = _safe_float(
                    getattr(record, "entry_armed_at_epoch", 0.0), 0.0
                )
                age_sec = (
                    max(0.0, float(now_ts) - armed_ts) if armed_ts > 0 else min_age_sec
                )
                if age_sec < min_age_sec:
                    continue
                if armed_before_epoch is not None and armed_ts >= float(
                    armed_before_epoch
                ):
                    continue
                candidates.append((armed_ts or 0.0, record))
            ordered = sorted(candidates, key=lambda item: item[0])
            if max_per_loop is not None:
                ordered = ordered[: int(max_per_loop)]
            for _armed_ts, record in ordered:
                record.status = "EXPIRED"
                expired_codes.append(
                    str(getattr(record, "stock_code", "") or "").strip()[:6]
                )
    except Exception as exc:
        log_error(f"⚠️ [SCALPING 스캐너] watch reset 실패 reason={reason}: {exc}")
        return []
    return expired_codes


def _recent_low_rebound_codes(recent_picks, low_rebound_targets=None):
    codes = {
        str((target or {}).get("Code") or "").strip()[:6]
        for target in (low_rebound_targets or [])
        if str((target or {}).get("Code") or "").strip()
    }
    for code, meta in (recent_picks or {}).items():
        sources = set((meta or {}).get("last_source_signature") or [])
        if LOW_REBOUND_RISING_MISSED_SOURCE in sources:
            recent_target = {
                "Price": (meta or {}).get("last_price")
                or (meta or {}).get("first_price"),
                "SourceSet": sources,
                "VolumeSurgeMatched": (meta or {}).get("last_volume_surge_matched"),
                "VolumeSurgeRank": (meta or {}).get("last_volume_surge_rank"),
                "VolumeSurgeRankPct": (meta or {}).get("last_volume_surge_rank_pct"),
                "VolumeSurgeUniverseSize": (meta or {}).get(
                    "last_volume_surge_universe_size"
                ),
            }
            if _under_10000_runtime_priority_rank(recent_target) > 0:
                continue
            norm_code = str(code or "").strip()[:6]
            if norm_code:
                codes.add(norm_code)
    return codes


def _active_scanner_watching_codes(db, codes):
    codes = {
        str(code or "").strip()[:6] for code in (codes or []) if str(code or "").strip()
    }
    if not codes:
        return set()
    try:
        with db.get_session() as session:
            if hasattr(session, "query"):
                rows = (
                    session.query(RecommendationHistory.stock_code)
                    .filter(
                        RecommendationHistory.rec_date == datetime.now().date(),
                        RecommendationHistory.status == "WATCHING",
                        RecommendationHistory.strategy == "SCALPING",
                        RecommendationHistory.position_tag == "SCANNER",
                        RecommendationHistory.buy_time.is_(None),
                        RecommendationHistory.buy_qty == 0,
                        RecommendationHistory.stock_code.in_(sorted(codes)),
                    )
                    .all()
                )
                return {
                    str(row[0] if isinstance(row, tuple) else row.stock_code).strip()[
                        :6
                    ]
                    for row in rows
                }
            records = getattr(session, "records", [])
            return {
                str(getattr(record, "stock_code", "") or "").strip()[:6]
                for record in records
                if str(getattr(record, "stock_code", "") or "").strip()[:6] in codes
                and getattr(record, "status", None) == "WATCHING"
                and getattr(record, "strategy", None) == "SCALPING"
                and getattr(record, "position_tag", None) == "SCANNER"
                and getattr(record, "buy_time", None) is None
                and int(getattr(record, "buy_qty", 0) or 0) == 0
            }
    except Exception as exc:
        log_error(f"⚠️ [SCALPING 스캐너] LOW_REBOUND active 코드 확인 실패: {exc}")
        return set()


def _expire_scanner_watching_for_low_rebound_floor(
    db, now_ts, *, max_to_expire, protected_codes=None
):
    protected_codes = {
        str(code or "").strip()[:6]
        for code in (protected_codes or set())
        if str(code or "").strip()
    }
    if int(max_to_expire or 0) <= 0:
        return []
    expired_codes = []
    try:
        with db.get_session() as session:
            if hasattr(session, "query"):
                records = (
                    session.query(RecommendationHistory)
                    .filter(
                        RecommendationHistory.rec_date == datetime.now().date(),
                        RecommendationHistory.status == "WATCHING",
                        RecommendationHistory.strategy == "SCALPING",
                        RecommendationHistory.position_tag == "SCANNER",
                        RecommendationHistory.buy_time.is_(None),
                        RecommendationHistory.buy_qty == 0,
                    )
                    .all()
                )
            else:
                records = list(getattr(session, "records", []))
            candidates = []
            for record in records:
                code = str(getattr(record, "stock_code", "") or "").strip()[:6]
                if not code or code in protected_codes:
                    continue
                if getattr(record, "status", None) != "WATCHING":
                    continue
                if getattr(record, "strategy", None) != "SCALPING":
                    continue
                if getattr(record, "position_tag", None) != "SCANNER":
                    continue
                if getattr(record, "buy_time", None) is not None:
                    continue
                if int(getattr(record, "buy_qty", 0) or 0) != 0:
                    continue
                armed_ts = _safe_float(
                    getattr(record, "entry_armed_at_epoch", 0.0), 0.0
                )
                candidates.append((armed_ts or 0.0, record))
            for _armed_ts, record in sorted(candidates, key=lambda item: item[0])[
                : int(max_to_expire)
            ]:
                record.status = "EXPIRED"
                expired_codes.append(
                    str(getattr(record, "stock_code", "") or "").strip()[:6]
                )
    except Exception as exc:
        log_error(f"⚠️ [SCALPING 스캐너] LOW_REBOUND floor 슬롯 교체 실패: {exc}")
        return []
    return expired_codes


def _reset_scanner_watch_targets(
    db, event_bus, now_ts, *, reason, armed_before_epoch=None
):
    expired_codes = _expire_scanner_watching_records(
        db,
        now_ts,
        armed_before_epoch=armed_before_epoch,
        reason=reason,
    )
    unreg_codes = sorted({code for code in expired_codes if code})
    if unreg_codes:
        event_bus.publish(
            "COMMAND_WS_UNREG",
            {
                "codes": unreg_codes,
                "source": "scalping_scanner_buy_window_reset",
                "reason": reason,
            },
        )
        log_info(
            "[SCALPING_SCANNER_BUY_WINDOW_RESET] "
            f"reason={reason} expired={len(expired_codes)} unreg={','.join(unreg_codes)}"
        )
    return expired_codes


def _active_scanner_watching_count(db):
    try:
        with db.get_session() as session:
            if hasattr(session, "query"):
                return (
                    session.query(RecommendationHistory)
                    .filter(
                        RecommendationHistory.rec_date == datetime.now().date(),
                        RecommendationHistory.status == "WATCHING",
                        RecommendationHistory.strategy == "SCALPING",
                        RecommendationHistory.position_tag == "SCANNER",
                        RecommendationHistory.buy_time.is_(None),
                        RecommendationHistory.buy_qty == 0,
                    )
                    .count()
                )
            records = getattr(session, "records", [])
            return sum(
                1
                for record in records
                if getattr(record, "status", None) == "WATCHING"
                and getattr(record, "strategy", None) == "SCALPING"
                and getattr(record, "position_tag", None) == "SCANNER"
                and getattr(record, "buy_time", None) is None
                and int(getattr(record, "buy_qty", 0) or 0) == 0
            )
    except Exception as exc:
        log_error(f"⚠️ [SCALPING 스캐너] active WATCHING 수량 확인 실패: {exc}")
        return 0


def _has_active_non_scanner_scalping_watching_code(db, code):
    norm_code = str(code or "").strip()[:6]
    if not norm_code:
        return False
    try:
        with db.get_session() as session:
            if hasattr(session, "query"):
                return (
                    session.query(RecommendationHistory)
                    .filter(
                        RecommendationHistory.rec_date == datetime.now().date(),
                        RecommendationHistory.stock_code == norm_code,
                        RecommendationHistory.status == "WATCHING",
                        RecommendationHistory.strategy == "SCALPING",
                        or_(
                            RecommendationHistory.position_tag.is_(None),
                            RecommendationHistory.position_tag != "SCANNER",
                        ),
                        RecommendationHistory.buy_time.is_(None),
                        func.coalesce(RecommendationHistory.buy_qty, 0) == 0,
                    )
                    .count()
                    > 0
                )
            records = getattr(session, "records", [])
            return any(
                getattr(record, "status", None) == "WATCHING"
                and getattr(record, "strategy", None) == "SCALPING"
                and getattr(record, "position_tag", None) != "SCANNER"
                and str(getattr(record, "stock_code", "") or "").strip()[:6]
                == norm_code
                and getattr(record, "buy_time", None) is None
                and int(getattr(record, "buy_qty", 0) or 0) == 0
                for record in records
            )
    except Exception as exc:
        log_error(
            f"⚠️ [SCALPING 스캐너] active non-SCANNER 코드 확인 실패 ({norm_code}): {exc}"
        )
        return False


def _source_priority(source):
    """장중 신선도는 상승 시작 primary source를 시가/거래대금 보조 신호보다 앞세웁니다."""
    return {
        "REALTIME_RANK_START": 0,
        "PRICE_JUMP_START": 1,
        "VOLUME_SURGE_POSITIVE": 2,
        "BID_IMBALANCE_SURGE": 3,
        "VI_TRIGGERED": 4,
        NEW_HIGH_CONFIRMATION_SOURCE: 5,
        HIGH_PROXIMITY_CONFIRMATION_SOURCE: 6,
        "VI+VALUE": 7,
        "SUPERNOVA+VALUE": 8,
        "BOTH": 9,
        "SUPERNOVA": 10,
        LOW_REBOUND_RISING_MISSED_SOURCE: 11,
        "BOTH+VALUE": 12,
        "OPEN_TOP": 13,
        "VALUE_TOP": 14,
    }.get(str(source or "OPEN_TOP"), 14)


def _safe_float(value, default=0.0):
    if value in (None, ""):
        return default
    try:
        return float(str(value).replace(",", "").replace("+", "").strip())
    except (TypeError, ValueError):
        return default


def _safe_int(value, default=0):
    if value in (None, ""):
        return default
    try:
        clean_value = str(value).replace(",", "").replace("+", "").strip()
        if not clean_value:
            return default
        return int(float(clean_value))
    except (TypeError, ValueError):
        return default


def _rank_change_sign_event_diagnostics(target, source_signature):
    has_realtime_rank_source = "REALTIME_RANK_START" in set(_source_signature(target))
    has_realtime_rank_source = has_realtime_rank_source or "REALTIME_RANK_START" in str(
        source_signature or ""
    )
    has_rank_fields = any(
        key in target and target.get(key) not in (None, "")
        for key in (
            "RankChange",
            "RankChangeSign",
            "RankChangeSignState",
            "RankChangeSignConsistency",
        )
    )
    if not has_realtime_rank_source and not has_rank_fields:
        return {
            "RankChangeSignState": "not_applicable",
            "RankChangeSignConsistency": "not_applicable",
        }
    return kiwoom_utils.rank_change_sign_diagnostics(
        target.get("RankChangeSign"),
        _safe_int(target.get("RankChange")),
    )


ZERO_CONTEXT_FORBIDDEN_USES = (
    "threshold_mutation,provider_route_change,order_price_relaxation,"
    "quantity_or_cap_change,broker_guard_bypass,stale_quote_bypass,"
    "hard_safety_guard_bypass,real_execution_quality_approval"
)


def _zero_context_value_missing(value) -> bool:
    if value is None:
        return True
    text = str(value).strip().lower()
    return (
        text == ""
        or text in {"-", "none", "null", "nan", "nat", "not_evaluated"}
        or text.startswith("not_applicable")
    )


def _zero_context_value_state(
    value, *, missing: bool = False, not_applicable: bool = False
) -> str:
    numeric = _safe_float(value, 0.0)
    if abs(numeric) > 1e-12:
        return "non_zero"
    if not_applicable:
        return "not_applicable_zero"
    if missing or _zero_context_value_missing(value):
        return "missing_defaulted_zero"
    return "actual_zero"


def _zero_context_observation_fields(
    *, domain: str, blocker: str, states: dict
) -> dict:
    zero_states = {str(key): str(value) for key, value in (states or {}).items()}
    blocking_states = [
        value
        for value in zero_states.values()
        if value in {"missing_defaulted_zero", "stale_defaulted_zero"}
    ]
    return {
        "zero_context_observed": bool(zero_states),
        "zero_context_domain": str(domain or "unknown"),
        "zero_context_blocker": str(blocker or "unknown"),
        "zero_context_primary_state": (
            blocking_states[0]
            if blocking_states
            else (
                next(iter(zero_states.values()))
                if zero_states
                else "not_applicable_zero"
            )
        ),
        "zero_context_defaulted_zero_field_count": len(blocking_states),
        "zero_context_forbidden_uses": ZERO_CONTEXT_FORBIDDEN_USES,
        **{f"zero_context_{key}_state": value for key, value in zero_states.items()},
    }


def _safe_positive_int(value, default=0):
    parsed = _safe_int(value, default)
    if parsed is None:
        return default
    return abs(parsed)


def _candidate_priority_price(target):
    target = target or {}
    for key in ("Price", "CurrentPrice", "curr", "current_price", "buy_price"):
        price = _safe_positive_int(target.get(key))
        if price > 0:
            return price
    return 0


def _under_10000_volume_surge_rank_pct():
    raw_value = os.getenv(
        "KORSTOCKSCAN_SCALP_SCANNER_UNDER_10000_VOLUME_SURGE_RANK_PCT",
        str(SCANNER_UNDER_10000_VOLUME_SURGE_RANK_PCT_DEFAULT),
    )
    try:
        return min(1.0, max(0.0, float(raw_value)))
    except (TypeError, ValueError):
        log_error(
            "⚠️ KORSTOCKSCAN_SCALP_SCANNER_UNDER_10000_VOLUME_SURGE_RANK_PCT 값이 잘못되어 기본값을 사용합니다: "
            f"{raw_value} -> {SCANNER_UNDER_10000_VOLUME_SURGE_RANK_PCT_DEFAULT}"
        )
        return SCANNER_UNDER_10000_VOLUME_SURGE_RANK_PCT_DEFAULT


def _under_10000_volume_surge_rank_min_count():
    raw_value = os.getenv(
        "KORSTOCKSCAN_SCALP_SCANNER_UNDER_10000_VOLUME_SURGE_RANK_MIN_COUNT",
        str(SCANNER_UNDER_10000_VOLUME_SURGE_RANK_MIN_COUNT_DEFAULT),
    )
    try:
        return max(0, int(float(raw_value)))
    except (TypeError, ValueError):
        log_error(
            "⚠️ KORSTOCKSCAN_SCALP_SCANNER_UNDER_10000_VOLUME_SURGE_RANK_MIN_COUNT 값이 잘못되어 기본값을 사용합니다: "
            f"{raw_value} -> {SCANNER_UNDER_10000_VOLUME_SURGE_RANK_MIN_COUNT_DEFAULT}"
        )
        return SCANNER_UNDER_10000_VOLUME_SURGE_RANK_MIN_COUNT_DEFAULT


def _has_under_10000_volume_surge_rank_relief(target):
    if not bool((target or {}).get("VolumeSurgeMatched")):
        return False
    rank = _safe_positive_int((target or {}).get("VolumeSurgeRank"))
    if rank <= 0:
        return False
    universe_size = _safe_positive_int((target or {}).get("VolumeSurgeUniverseSize"))
    rank_pct_limit = _under_10000_volume_surge_rank_pct()
    min_count = _under_10000_volume_surge_rank_min_count()
    rank_limit = (
        max(min_count, int(ceil(universe_size * rank_pct_limit)))
        if universe_size > 0
        else min_count
    )
    if rank <= rank_limit:
        return True
    rank_pct = _safe_float((target or {}).get("VolumeSurgeRankPct"))
    return rank_pct > 0.0 and rank_pct <= rank_pct_limit


def _has_volume_surge_source_evidence(target, *, positive_only=False):
    target = target or {}
    source_set = set(_source_signature(target))
    if positive_only:
        if "VOLUME_SURGE_POSITIVE" not in source_set:
            return False
    elif not (
        {"VOLUME_SURGE_POSITIVE", "VOLUME_SURGE_RAW", LOW_REBOUND_RISING_MISSED_SOURCE}
        & source_set
        or bool(target.get("VolumeSurgeMatched"))
    ):
        return False
    if bool(target.get("VolumeSurgeMatched")):
        return True
    return (
        _safe_float(target.get("VolumeSurgeRate", target.get("SpikeRate"))) > 0.0
        or _safe_positive_int(target.get("VolumeSurgeQty", target.get("SurgeQty"))) > 0
        or _safe_positive_int(target.get("VolumeSurgeTradeQty", target.get("TradeQty")))
        > 0
    )


def _has_positive_volume_surge_source_evidence(target):
    return _has_volume_surge_source_evidence(target, positive_only=True)


def _has_under_10000_liquidity_relief(target):
    target = target or {}
    source_set = set(_source_signature(target))
    if "VALUE_TOP" in source_set:
        return True
    if _has_volume_surge_source_evidence(target):
        return True
    return _has_under_10000_volume_surge_rank_relief(target)


def _under_10000_runtime_priority_rank(target):
    price = _candidate_priority_price(target)
    if not 0 < price < SCANNER_UNDER_10000_PRIORITY_PRICE_CEILING:
        return 0
    return 0 if _has_under_10000_liquidity_relief(target) else 1


def _low_rebound_min_pct():
    return float(
        getattr(TRADING_RULES, "SCALP_SCANNER_LOW_REBOUND_MIN_PCT", 2.5) or 2.5
    )


def _low_rebound_max_distance_from_high_pct():
    return float(
        getattr(
            TRADING_RULES, "SCALP_SCANNER_LOW_REBOUND_MAX_DISTANCE_FROM_HIGH_PCT", -0.5
        )
        or -0.5
    )


def _low_rebound_candle_fetch_cap():
    return int(
        getattr(TRADING_RULES, "SCALP_SCANNER_LOW_REBOUND_CANDLE_FETCH_CAP", 20) or 20
    )


def _low_rebound_candle_limit():
    return int(
        getattr(TRADING_RULES, "SCALP_SCANNER_LOW_REBOUND_CANDLE_LIMIT", 420) or 420
    )


def _candidate_current_change_rate(target):
    for key in (
        "LowReboundDisplayChangeRate",
        "RealtimeRankFluRate",
        "VolumeSurgeFluRate",
        "HighProximityFluRate",
        "NewHighFluRate",
        "ValueFluRate",
        "FluRate",
        "flu_rate",
    ):
        value = (target or {}).get(key)
        if value not in (None, ""):
            return _safe_float(value), True
    return 0.0, False


def _low_rebound_price_from_candle(candle, *keys):
    for key in keys:
        price = _safe_positive_int((candle or {}).get(key))
        if price > 0:
            return price
    return 0


def _low_rebound_candle_source_date(candle):
    for key in ("source_timestamp", "cntr_tm", "체결시간"):
        text = str((candle or {}).get(key) or "").strip()
        if len(text) >= 8 and text[:8].isdigit():
            return text[:8]
    return ""


def _filter_low_rebound_intraday_candles(candles):
    rows = list(candles or [])
    source_dates = [_low_rebound_candle_source_date(row) for row in rows]
    dated = [date for date in source_dates if date]
    if not dated:
        return rows, {
            "intraday_date_filter_applied_count": 0,
            "intraday_date_filter_latest_date": "",
            "intraday_date_filter_unique_date_count": 0,
        }
    latest_date = max(dated)
    filtered = [
        row
        for row, source_date in zip(rows, source_dates, strict=False)
        if source_date == latest_date
    ]
    return filtered, {
        "intraday_date_filter_applied_count": max(0, len(rows) - len(filtered)),
        "intraday_date_filter_latest_date": latest_date,
        "intraday_date_filter_unique_date_count": len(set(dated)),
    }


def _bounded(value, low=0.0, high=9999.0):
    return max(low, min(high, float(value or 0.0)))


def _pick_first_present(payload, keys):
    for key in keys:
        if key in payload and payload.get(key) not in (None, ""):
            return payload.get(key)
    return None


def _extract_strength_value(payload):
    raw_value = _pick_first_present(
        payload or {},
        (
            "CntrStr",
            "cntr_str",
            "cntr_strg",
            "cntr_streng",
            "exec_strength",
            "v_pw",
        ),
    )
    if raw_value is None:
        return 0.0, False
    value = _safe_float(raw_value)
    return value, value > 0.0


def _format_strength_display(target):
    if not bool(target.get("CntrStrAvailable", False)):
        return "수신대기"
    return f"{_safe_float(target.get('CntrStr')):.1f}"


def _representative_source(source_set):
    sources = set(source_set or [])
    for source in (
        "REALTIME_RANK_START",
        "PRICE_JUMP_START",
        "VOLUME_SURGE_POSITIVE",
        "BID_IMBALANCE_SURGE",
        NEW_HIGH_CONFIRMATION_SOURCE,
        HIGH_PROXIMITY_CONFIRMATION_SOURCE,
    ):
        if source in sources:
            return source
    has_open = "OPEN_TOP" in sources
    has_supernova = "SUPERNOVA" in sources
    has_value = "VALUE_TOP" in sources
    has_vi = "VI_TRIGGERED" in sources

    if has_vi and has_value:
        return "VI+VALUE"
    if has_value and has_open and has_supernova:
        return "BOTH+VALUE"
    if has_value and has_supernova:
        return "SUPERNOVA+VALUE"
    if LOW_REBOUND_RISING_MISSED_SOURCE in sources:
        return LOW_REBOUND_RISING_MISSED_SOURCE
    if has_value:
        return "VALUE_TOP"
    if has_vi:
        return "VI_TRIGGERED"
    if has_open and has_supernova:
        return "BOTH"
    if has_supernova:
        return "SUPERNOVA"
    return "OPEN_TOP"


def _source_signature(target):
    return tuple(
        sorted(set(target.get("SourceSet") or [target.get("Source") or "OPEN_TOP"]))
    )


def _is_low_rebound_target(target):
    return LOW_REBOUND_RISING_MISSED_SOURCE in set(_source_signature(target or {}))


def _is_low_rebound_reserved_priority_target(target):
    return (
        _is_low_rebound_target(target)
        and _under_10000_runtime_priority_rank(target) == 0
    )


def _scanner_rate_from_field(target, field_name):
    if field_name in (target or {}) and target.get(field_name) not in (None, ""):
        return _safe_float(target.get(field_name)), True
    return 0.0, False


def _scanner_flu_metric(target):
    source_set = set(_source_signature(target))

    if LOW_REBOUND_RISING_MISSED_SOURCE in source_set:
        rate, has_rate = _scanner_rate_from_field(target, "LowReboundDisplayChangeRate")
        if has_rate:
            return (
                rate,
                "low_rebound_display_change_rate",
                LOW_REBOUND_RISING_MISSED_SOURCE,
            )

    if "REALTIME_RANK_START" in source_set:
        rate, has_rate = _scanner_rate_from_field(target, "RealtimeRankFluRate")
        if has_rate:
            return rate, "realtime_rank_base_comp_chgr", "REALTIME_RANK_START"

    if "PRICE_JUMP_START" in source_set:
        rate, has_rate = _scanner_rate_from_field(target, "PriceJumpFluRate")
        if has_rate:
            return rate, "price_jump_flu_rate", "PRICE_JUMP_START"

    if "VOLUME_SURGE_POSITIVE" in source_set:
        rate, has_rate = _scanner_rate_from_field(target, "VolumeSurgeFluRate")
        if has_rate:
            return rate, "volume_surge_flu_rate", "VOLUME_SURGE_POSITIVE"

    if "BID_IMBALANCE_SURGE" in source_set:
        rate, has_rate = _scanner_rate_from_field(target, "BidImbalanceFluRate")
        if has_rate:
            return rate, "bid_imbalance_flu_rate", "BID_IMBALANCE_SURGE"

    if NEW_HIGH_CONFIRMATION_SOURCE in source_set:
        rate, has_rate = _scanner_rate_from_field(target, "NewHighFluRate")
        if has_rate:
            return rate, "new_high_flu_rate", NEW_HIGH_CONFIRMATION_SOURCE

    if HIGH_PROXIMITY_CONFIRMATION_SOURCE in source_set:
        rate, has_rate = _scanner_rate_from_field(target, "HighProximityFluRate")
        if has_rate:
            return rate, "high_proximity_flu_rate", HIGH_PROXIMITY_CONFIRMATION_SOURCE

    if source_set and source_set.issubset({"OPEN_TOP", "VALUE_TOP"}):
        open_rate, has_open = _scanner_rate_from_field(target, "OpenFluRate")
        if has_open:
            return open_rate, "open_flu_rate", "OPEN_TOP"
        value_rate, has_value = _scanner_rate_from_field(target, "ValueFluRate")
        if source_set == {"VALUE_TOP"} and has_value:
            return value_rate, "day_flu_rate", "VALUE_TOP"

    if "VI_TRIGGERED" in source_set:
        vi_rate, has_vi = _scanner_rate_from_field(target, "ViFluRate")
        if has_vi:
            return (
                vi_rate,
                str(target.get("ViFluRateMetric") or "vi_open_flu_rate"),
                "VI_TRIGGERED",
            )

    if "SUPERNOVA" in source_set:
        supernova_rate, has_supernova = _scanner_rate_from_field(
            target, "SupernovaFluRate"
        )
        if has_supernova:
            return supernova_rate, "supernova_source_rate", "SUPERNOVA"

    value_rate, has_value = _scanner_rate_from_field(target, "ValueFluRate")
    if has_value:
        return value_rate, "day_flu_rate", "VALUE_TOP"

    legacy_rate = _safe_float(target.get("FluRate"))
    return legacy_rate, "legacy_flu_rate", str(target.get("Source") or "UNKNOWN")


def _rank_jump(target):
    rank_now = _safe_int(target.get("RankNow"))
    rank_prev = _safe_int(target.get("RankPrev"))
    if rank_now > 0 and rank_prev > rank_now:
        return rank_prev - rank_now
    return 0


def _scanner_candidate_role(target):
    source_set = set(_source_signature(target))
    if LOW_REBOUND_RISING_MISSED_SOURCE in source_set:
        return LOW_REBOUND_RISING_MISSED_ROLE
    if bool(getattr(TRADING_RULES, "SCALP_SCANNER_PRIORITY_TIERING_ENABLED", False)):
        if source_set == {"BID_IMBALANCE_SURGE"} and bool(
            getattr(
                TRADING_RULES, "SCALP_SCANNER_PRIORITY_DEMOTE_BID_IMBALANCE_ONLY", True
            )
        ):
            return "source_only"
        late_rank_sources = {"REALTIME_RANK_START", "VALUE_TOP", "OPEN_TOP"}
        if (
            source_set
            and source_set.issubset(late_rank_sources)
            and bool(
                getattr(
                    TRADING_RULES,
                    "SCALP_SCANNER_PRIORITY_DEMOTE_REALTIME_RANK_ONLY",
                    True,
                )
            )
        ):
            return "late_confirmation"
    if source_set & PRIMARY_RISING_START_SOURCES:
        return "early_discovery"
    if source_set & BREAKOUT_CONFIRMATION_SOURCES and source_set.issubset(
        BREAKOUT_CONFIRMATION_SOURCES | {"VALUE_TOP", "OPEN_TOP"}
    ):
        return "late_confirmation"
    if source_set == {"VALUE_TOP"}:
        return "liquidity_enrichment_only"
    if source_set in (
        {"VALUE_TOP"},
        {"OPEN_TOP"},
        {"OPEN_TOP", "VALUE_TOP"},
        {"VI_TRIGGERED"},
        {"VI_TRIGGERED", "VALUE_TOP"},
    ):
        return "late_confirmation"
    return "early_discovery"


def _rising_start_score(target):
    source_set = set(_source_signature(target))
    source_bias = {
        "REALTIME_RANK_START": 720.0,
        "PRICE_JUMP_START": 690.0,
        "VOLUME_SURGE_POSITIVE": 650.0,
        "BID_IMBALANCE_SURGE": 610.0,
        NEW_HIGH_CONFIRMATION_SOURCE: 560.0,
        HIGH_PROXIMITY_CONFIRMATION_SOURCE: 540.0,
        LOW_REBOUND_RISING_MISSED_SOURCE: 520.0,
        "VI_TRIGGERED": 360.0,
        "OPEN_TOP": 120.0,
        "VALUE_TOP": 20.0,
    }
    best_source_bias = max(
        (source_bias.get(source, 0.0) for source in source_set), default=0.0
    )
    flu_rate, flu_metric, _ = _scanner_flu_metric(target)
    flu_score = _bounded(flu_rate * 10.0, 0.0, 260.0)
    if flu_metric in {"vi_dynamic_disparity_rate", "vi_static_disparity_rate"}:
        flu_score = 0.0

    # rank_chg_sign is raw/unverified. Only the signed numeric rank delta may
    # contribute, and negative deltas must not reward a rising-start candidate.
    rank_change = max(0, _safe_int(target.get("RankChange")))
    rank_score = min(240.0, rank_change * 8.0)
    rank_jump_score = min(220.0, _rank_jump(target) * 4.0)
    jump_score = _bounded(target.get("JumpRate"), 0.0, 20.0) * 18.0
    volume_score = _bounded(
        target.get("VolumeSurgeRate", target.get("SpikeRate")), 0.0, 400.0
    )
    bid_score = _bounded(target.get("BidSurgeRate"), 0.0, 250.0)
    cntr_score = _bounded(target.get("CntrStr"), 0.0, 180.0)
    priority_score = _bounded(target.get("PriorityScore"), 0.0, 220.0)
    trade_value = _safe_positive_int(target.get("TradeValue"))
    trade_value_score = (
        min(160.0, log10(max(trade_value, 1)) * 22.0) if trade_value > 0 else 0.0
    )
    source_count_score = min(240.0, max(0, len(source_set) - 1) * 70.0)
    breakout_confirmation_score = 0.0
    if source_set & BREAKOUT_CONFIRMATION_SOURCES and source_set & {
        "PRICE_JUMP_START",
        "VOLUME_SURGE_POSITIVE",
    }:
        breakout_confirmation_score = 180.0

    return (
        best_source_bias
        + flu_score
        + rank_score
        + rank_jump_score
        + jump_score
        + volume_score
        + bid_score
        + cntr_score
        + priority_score
        + trade_value_score
        + source_count_score
        + breakout_confirmation_score
    )


def _scanner_priority_profile(target, previous=None):
    source_set = set(_source_signature(target))
    acceleration_reason = _acceleration_reason(target, previous)
    rank_jump = _rank_jump(target)
    spike_rate = _safe_float(target.get("SpikeRate"))
    jump_rate = _safe_float(target.get("JumpRate"))
    priority_score = _safe_float(target.get("PriorityScore"))
    cntr_str = _safe_float(target.get("CntrStr"))
    cntr_available = bool(target.get("CntrStrAvailable", False))
    min_rank_jump = int(
        getattr(TRADING_RULES, "SCALP_SCANNER_ACCEL_MIN_RANK_JUMP", 10) or 10
    )
    min_spike = float(
        getattr(TRADING_RULES, "SCALP_SCANNER_ACCEL_MIN_SPIKE_RATE", 80.0) or 80.0
    )
    min_priority = float(
        getattr(TRADING_RULES, "SCALP_SCANNER_ACCEL_MIN_PRIORITY_SCORE", 80.0) or 80.0
    )
    min_cntr = float(
        getattr(TRADING_RULES, "SCALP_SCANNER_ACCEL_MIN_CNTR_STR", 110.0) or 110.0
    )
    demote_bid_only = bool(
        getattr(TRADING_RULES, "SCALP_SCANNER_PRIORITY_DEMOTE_BID_IMBALANCE_ONLY", True)
    )
    demote_open_price_jump_without_volume = bool(
        getattr(
            TRADING_RULES, "SCALP_SCANNER_DEMOTE_OPEN_PRICE_JUMP_WITHOUT_VOLUME", False
        )
    )
    open_price_jump_without_volume = (
        "OPEN_TOP" in source_set
        and "PRICE_JUMP_START" in source_set
        and "VOLUME_SURGE_POSITIVE" not in source_set
    )

    strong_accel = acceleration_reason in {
        "price_jump_start_acceleration",
        "rank_jump_acceleration",
        "spike_rate_acceleration",
        "priority_score_acceleration",
        "execution_strength_acceleration",
    }
    strong_accel = strong_accel or rank_jump >= min_rank_jump
    strong_accel = strong_accel or spike_rate >= min_spike
    strong_accel = strong_accel or jump_rate >= max(0.3, min_spike / 200.0)
    strong_accel = strong_accel or priority_score >= min_priority
    strong_accel = strong_accel or (cntr_available and cntr_str >= min_cntr)
    price_jump_confirmed = "PRICE_JUMP_START" in source_set and bool(
        source_set & {"REALTIME_RANK_START", "VOLUME_SURGE_POSITIVE"}
    )
    price_jump_breakout_confirmed = (
        "PRICE_JUMP_START" in source_set
        and "VOLUME_SURGE_POSITIVE" in source_set
        and bool(source_set & BREAKOUT_CONFIRMATION_SOURCES)
    )
    price_jump_confirmed = price_jump_confirmed or price_jump_breakout_confirmed

    if LOW_REBOUND_RISING_MISSED_SOURCE in source_set:
        tier = "tier_c_volume_confirmation"
        reason = acceleration_reason or "low_rebound_rising_missed_candidate"
        base_score = 1800.0
        demoted_reason = ""
    elif source_set == {"BID_IMBALANCE_SURGE"} and demote_bid_only:
        tier = "tier_z_source_only"
        reason = "bid_imbalance_only_source_only"
        base_score = 0.0
        demoted_reason = "bid_imbalance_only_without_price_or_volume_confirmation"
    elif open_price_jump_without_volume and demote_open_price_jump_without_volume:
        tier = "tier_b_price_jump_candidate"
        reason = "open_price_jump_without_volume_demoted"
        base_score = 3000.0
        demoted_reason = "open_price_jump_requires_volume_or_followthrough"
    elif "PRICE_JUMP_START" in source_set and (strong_accel or price_jump_confirmed):
        tier = "tier_a_acceleration_confirmed"
        if jump_rate >= max(0.3, min_spike / 200.0):
            reason = "price_jump_start_acceleration"
        elif price_jump_breakout_confirmed:
            reason = "price_jump_breakout_confirmation"
        elif price_jump_confirmed:
            reason = "price_jump_multisource_confirmation"
        elif rank_jump >= min_rank_jump:
            reason = "rank_jump_acceleration"
        elif spike_rate >= min_spike:
            reason = "spike_rate_acceleration"
        elif priority_score >= min_priority:
            reason = "priority_score_acceleration"
        elif cntr_available and cntr_str >= min_cntr:
            reason = "execution_strength_acceleration"
        else:
            reason = acceleration_reason or "price_jump_multisource_confirmation"
        base_score = 4000.0
        demoted_reason = ""
    elif "PRICE_JUMP_START" in source_set:
        tier = "tier_b_price_jump_candidate"
        reason = acceleration_reason or "price_jump_source_present"
        base_score = 3000.0
        demoted_reason = ""
    elif "VOLUME_SURGE_POSITIVE" in source_set:
        tier = "tier_c_volume_confirmation"
        reason = acceleration_reason or "volume_surge_positive_source_present"
        base_score = 2200.0
        demoted_reason = ""
    elif source_set & BREAKOUT_CONFIRMATION_SOURCES and source_set.issubset(
        BREAKOUT_CONFIRMATION_SOURCES | {"VALUE_TOP", "OPEN_TOP"}
    ):
        tier = "tier_d_late_rank_only"
        reason = "breakout_confirmation_only_source"
        base_score = 1000.0
        demoted_reason = "breakout_confirmation_requires_price_or_volume_source"
    elif strong_accel:
        tier = "tier_a_acceleration_confirmed"
        if rank_jump >= min_rank_jump:
            reason = "rank_jump_acceleration"
        elif spike_rate >= min_spike:
            reason = "spike_rate_acceleration"
        elif priority_score >= min_priority:
            reason = "priority_score_acceleration"
        elif cntr_available and cntr_str >= min_cntr:
            reason = "execution_strength_acceleration"
        else:
            reason = acceleration_reason or "general_acceleration_confirmed"
        base_score = 4000.0
        demoted_reason = ""
    elif source_set and source_set.issubset(
        {"REALTIME_RANK_START", "VALUE_TOP", "OPEN_TOP"}
    ):
        tier = "tier_d_late_rank_only"
        reason = "late_rank_or_liquidity_only_source"
        base_score = 1000.0
        demoted_reason = "late_rank_only_requires_acceleration_confirmation"
    else:
        tier = "tier_d_late_rank_only"
        reason = acceleration_reason or "secondary_source_requires_confirmation"
        base_score = 1000.0
        demoted_reason = "secondary_source_requires_acceleration_confirmation"

    score = base_score + _freshness_score(target)
    return {
        "scanner_priority_tier": tier,
        "scanner_priority_score": score,
        "scanner_priority_reason": reason,
        "scanner_demoted_reason": demoted_reason,
        "scanner_promotion_policy_version": SCANNER_PROMOTION_POLICY_VERSION,
    }


def _price_delta_pct(first_price, current_price):
    first = _safe_positive_int(first_price)
    current = _safe_positive_int(current_price)
    if first <= 0 or current <= 0:
        return 0.0
    return ((current - first) / first) * 100.0


def _late_confirmation_probe_block_reason(
    *, probe_age, min_probe_sec, max_probe_sec, price_declined, flu_metric_changed=False
):
    if probe_age < min_probe_sec:
        return "late_confirmation_probe_waiting"
    if probe_age > max_probe_sec:
        return "late_confirmation_probe_expired"
    if price_declined:
        return "late_confirmation_price_declined"
    if flu_metric_changed:
        return "late_confirmation_flu_metric_changed"
    return "late_confirmation_probe_no_acceleration"


def _acceleration_reason(target, previous=None):
    source_set = set(_source_signature(target))
    previous_sources = set((previous or {}).get("last_source_signature") or [])
    if LOW_REBOUND_RISING_MISSED_SOURCE in source_set:
        return "low_rebound_rising_missed_candidate"
    for source in (
        "REALTIME_RANK_START",
        "PRICE_JUMP_START",
        "VOLUME_SURGE_POSITIVE",
        "BID_IMBALANCE_SURGE",
    ):
        if source in source_set and source not in previous_sources:
            return f"new_{source.lower()}_source"
    if "VI_TRIGGERED" in source_set and "VI_TRIGGERED" not in previous_sources:
        return "new_vi_triggered_source"
    if "SUPERNOVA" in source_set and "SUPERNOVA" not in previous_sources:
        return "new_supernova_source"

    rank_jump = _rank_jump(target)
    min_rank_jump = int(
        getattr(TRADING_RULES, "SCALP_SCANNER_ACCEL_MIN_RANK_JUMP", 10) or 10
    )
    if rank_jump >= min_rank_jump:
        return "rank_jump_acceleration"

    spike_rate = _safe_float(target.get("SpikeRate"))
    min_spike = float(
        getattr(TRADING_RULES, "SCALP_SCANNER_ACCEL_MIN_SPIKE_RATE", 80.0) or 80.0
    )
    if spike_rate >= min_spike:
        return "spike_rate_acceleration"

    jump_rate = _safe_float(target.get("JumpRate"))
    if jump_rate >= max(0.3, min_spike / 200.0):
        return "price_jump_start_acceleration"

    bid_surge_rate = _safe_float(target.get("BidSurgeRate"))
    if bid_surge_rate >= min_spike:
        return "bid_imbalance_surge_acceleration"

    priority_score = _safe_float(target.get("PriorityScore"))
    min_priority = float(
        getattr(TRADING_RULES, "SCALP_SCANNER_ACCEL_MIN_PRIORITY_SCORE", 80.0) or 80.0
    )
    if priority_score >= min_priority:
        return "priority_score_acceleration"

    cntr_str = _safe_float(target.get("CntrStr"))
    min_cntr = float(
        getattr(TRADING_RULES, "SCALP_SCANNER_ACCEL_MIN_CNTR_STR", 110.0) or 110.0
    )
    if bool(target.get("CntrStrAvailable", False)) and cntr_str >= min_cntr:
        return "execution_strength_acceleration"

    return ""


def _freshness_score(target):
    """
    `OPEN_TOP`은 하루 종일 순위가 고착되기 쉬워 보조 신호로만 쓰고,
    최근 거래량 급증/체결강도/등락률이 함께 살아난 종목을 앞세웁니다.
    """
    if set(_source_signature(target)) & PRIMARY_RISING_START_SOURCES:
        return _rising_start_score(target)

    source_bias = {
        "VI+VALUE": 650.0,
        "SUPERNOVA+VALUE": 620.0,
        "VI_TRIGGERED": 560.0,
        "BOTH": 520.0,
        "SUPERNOVA": 460.0,
        NEW_HIGH_CONFIRMATION_SOURCE: 420.0,
        HIGH_PROXIMITY_CONFIRMATION_SOURCE: 400.0,
        "BOTH+VALUE": 430.0,
        LOW_REBOUND_RISING_MISSED_SOURCE: 360.0,
        "VALUE_TOP": 180.0,
        "OPEN_TOP": 0.0,
    }.get(str(target.get("Source") or "OPEN_TOP"), 0.0)
    priority_score = _bounded(target.get("PriorityScore"), 0.0, 300.0)
    spike_rate = _bounded(target.get("SpikeRate"), 0.0, 350.0)
    flu_rate, flu_metric, _ = _scanner_flu_metric(target)
    cntr_str = _bounded(target.get("CntrStr"), 0.0, 180.0)
    trade_value = _safe_positive_int(target.get("TradeValue"))
    source_set = set(target.get("SourceSet") or [])

    trade_value_score = 0.0
    if trade_value > 0:
        trade_value_score = min(220.0, log10(max(trade_value, 1)) * 30.0)

    rank_jump_score = min(260.0, _rank_jump(target) * 5.0)

    vi_score = 0.0
    if "VI_TRIGGERED" in source_set:
        vi_score = (
            320.0 + min(_safe_positive_int(target.get("VIMotionCount")), 5) * 30.0
        )

    source_count_score = min(320.0, max(0, len(source_set) - 1) * 100.0)
    flu_score = _bounded(flu_rate * 8.0, 0.0, 220.0)
    if flu_metric in {"vi_dynamic_disparity_rate", "vi_static_disparity_rate"}:
        flu_score = 0.0

    return (
        source_bias
        + priority_score
        + spike_rate
        + flu_score
        + cntr_str
        + trade_value_score
        + rank_jump_score
        + vi_score
        + source_count_score
    )


def _merge_best_rank_metadata(current, raw_target, prefix):
    rank_key = f"{prefix}Rank"
    rank = _safe_positive_int((raw_target or {}).get(rank_key))
    if rank <= 0:
        return
    current_rank = _safe_positive_int((current or {}).get(rank_key))
    if current_rank > 0 and rank >= current_rank:
        return
    current[f"{prefix}Matched"] = bool((raw_target or {}).get(f"{prefix}Matched", True))
    current[rank_key] = rank
    current[f"{prefix}RankPct"] = _safe_float(
        (raw_target or {}).get(f"{prefix}RankPct")
    )
    current[f"{prefix}UniverseSize"] = _safe_positive_int(
        (raw_target or {}).get(f"{prefix}UniverseSize")
    )
    current[f"{prefix}SortType"] = str(
        (raw_target or {}).get(f"{prefix}SortType") or ""
    )


def _merge_candidate(candidate_pool, raw_target, source):
    code = kiwoom_utils.normalize_stock_code(
        raw_target.get("Code", raw_target.get("code", ""))
    )
    if not code:
        return

    name = raw_target.get("Name", raw_target.get("name", ""))
    current = candidate_pool.setdefault(
        code,
        {
            "Code": code,
            "Name": name,
            "FluRate": 0.0,
            "LegacyMaxFluRate": 0.0,
            "CntrStr": 0.0,
            "Price": 0,
            "Source": source,
            "SourceSet": set(),
            "PriorityScore": 0.0,
            "SpikeRate": 0.0,
            "TradeValue": 0,
            "RankNow": 0,
            "RankPrev": 0,
            "VIMotionCount": 0,
            "VIReleaseTime": "",
            "CntrStrAvailable": False,
            "SourceFamily": SCANNER_RISING_START_SOURCE_FAMILY,
        },
    )

    current["SourceSet"].add(source)
    if name:
        current["Name"] = name

    raw_flu_value = raw_target.get("FluRate", raw_target.get("flu_rate"))
    raw_flu_present = raw_flu_value not in (None, "")
    raw_flu_rate = _safe_float(raw_flu_value)
    current["LegacyMaxFluRate"] = max(
        current.get("LegacyMaxFluRate", 0.0), raw_flu_rate
    )
    if source == "OPEN_TOP":
        open_flu_value = raw_target.get("OpenFluRate", raw_flu_value)
        if open_flu_value not in (None, ""):
            current["OpenFluRate"] = _safe_float(open_flu_value)
        if "DayFluRate" in raw_target:
            current["DayFluRate"] = _safe_float(raw_target.get("DayFluRate"))
        if "OpenPrice" in raw_target:
            current["OpenPrice"] = _safe_positive_int(raw_target.get("OpenPrice"))
    elif source == "VALUE_TOP":
        if raw_flu_present:
            current["ValueFluRate"] = raw_flu_rate
            current.setdefault("DayFluRate", raw_flu_rate)
    elif source == "REALTIME_RANK_START":
        if raw_target.get("RealtimeRankFluRate") not in (None, ""):
            current["RealtimeRankFluRate"] = _safe_float(
                raw_target.get("RealtimeRankFluRate")
            )
        elif raw_flu_present:
            current["RealtimeRankFluRate"] = raw_flu_rate
        current["RealtimePrevBaseChange"] = _safe_float(
            raw_target.get("RealtimePrevBaseChange")
        )
        current["RankChange"] = _safe_int(raw_target.get("RankChange"))
        current["RankChangeSign"] = str(raw_target.get("RankChangeSign") or "").strip()
        current["RankChangeSignAuthority"] = (
            str(
                raw_target.get("RankChangeSignAuthority")
                or RANK_CHANGE_SIGN_AUTHORITY_DEFAULT
            ).strip()
            or RANK_CHANGE_SIGN_AUTHORITY_DEFAULT
        )
        sign_diagnostics = kiwoom_utils.rank_change_sign_diagnostics(
            current.get("RankChangeSign"),
            current.get("RankChange"),
        )
        current["RankChangeSignState"] = str(
            raw_target.get("RankChangeSignState")
            or sign_diagnostics["RankChangeSignState"]
        ).strip()
        current["RankChangeSignConsistency"] = str(
            raw_target.get("RankChangeSignConsistency")
            or sign_diagnostics["RankChangeSignConsistency"]
        ).strip()
        current["RealtimeRankWindow"] = str(raw_target.get("RealtimeRankWindow") or "")
    elif source == "PRICE_JUMP_START":
        if raw_flu_present:
            current["PriceJumpFluRate"] = raw_flu_rate
        current["JumpRate"] = max(
            current.get("JumpRate", 0.0), _safe_float(raw_target.get("JumpRate"))
        )
        current["PriceJumpTradeQty"] = max(
            current.get("PriceJumpTradeQty", 0),
            _safe_positive_int(raw_target.get("TradeQty")),
        )
        current["PreSig"] = raw_target.get("PreSig", current.get("PreSig", ""))
        _merge_best_rank_metadata(current, raw_target, "PriceJump")
    elif source == "VOLUME_SURGE_POSITIVE":
        if raw_flu_present:
            current["VolumeSurgeFluRate"] = raw_flu_rate
        current["VolumeSurgeRate"] = max(
            current.get("VolumeSurgeRate", 0.0),
            _safe_float(
                raw_target.get(
                    "VolumeSurgeRate",
                    raw_target.get("SpikeRate", raw_target.get("spike_rate")),
                )
            ),
        )
        current["VolumeSurgeQty"] = max(
            current.get("VolumeSurgeQty", 0),
            _safe_positive_int(raw_target.get("SurgeQty")),
        )
        current["PreSig"] = raw_target.get("PreSig", current.get("PreSig", ""))
    elif source == "BID_IMBALANCE_SURGE":
        if raw_flu_present:
            current["BidImbalanceFluRate"] = raw_flu_rate
        current["BidSurgeRate"] = max(
            current.get("BidSurgeRate", 0.0),
            _safe_float(raw_target.get("BidSurgeRate")),
        )
        current["BidSurgeQty"] = max(
            current.get("BidSurgeQty", 0),
            _safe_positive_int(raw_target.get("BidSurgeQty")),
        )
        current["TotalBuyQty"] = max(
            current.get("TotalBuyQty", 0),
            _safe_positive_int(raw_target.get("TotalBuyQty")),
        )
        current["PreSig"] = raw_target.get("PreSig", current.get("PreSig", ""))
    elif source == "VI_TRIGGERED":
        if raw_flu_present:
            current["ViFluRate"] = raw_flu_rate
        if raw_target.get("ViOpenFluRate") not in (None, ""):
            current["ViOpenFluRate"] = _safe_float(raw_target.get("ViOpenFluRate"))
        if raw_target.get("ViDynamicDisparityRate") not in (None, ""):
            current["ViDynamicDisparityRate"] = _safe_float(
                raw_target.get("ViDynamicDisparityRate")
            )
        if raw_target.get("ViStaticDisparityRate") not in (None, ""):
            current["ViStaticDisparityRate"] = _safe_float(
                raw_target.get("ViStaticDisparityRate")
            )
        if raw_target.get("ViFluRateMetric"):
            current["ViFluRateMetric"] = str(raw_target.get("ViFluRateMetric"))
        if "ViFluRate" not in current:
            if "ViOpenFluRate" in current:
                current["ViFluRate"] = current["ViOpenFluRate"]
                current.setdefault("ViFluRateMetric", "vi_open_flu_rate")
            elif "ViDynamicDisparityRate" in current:
                current["ViFluRate"] = current["ViDynamicDisparityRate"]
                current.setdefault("ViFluRateMetric", "vi_dynamic_disparity_rate")
            elif "ViStaticDisparityRate" in current:
                current["ViFluRate"] = current["ViStaticDisparityRate"]
                current.setdefault("ViFluRateMetric", "vi_static_disparity_rate")
    elif source == HIGH_PROXIMITY_CONFIRMATION_SOURCE:
        if raw_flu_present:
            current["HighProximityFluRate"] = raw_flu_rate
        current["HighProximityTradeQty"] = max(
            current.get("HighProximityTradeQty", 0),
            _safe_positive_int(raw_target.get("TradeQty")),
        )
        current["TodayHighPrice"] = max(
            current.get("TodayHighPrice", 0),
            _safe_positive_int(raw_target.get("TodayHighPrice")),
        )
        current["TodayLowPrice"] = max(
            current.get("TodayLowPrice", 0),
            _safe_positive_int(raw_target.get("TodayLowPrice")),
        )
        if raw_target.get("HighProximityDistancePct") not in (None, ""):
            current["HighProximityDistancePct"] = _safe_float(
                raw_target.get("HighProximityDistancePct")
            )
        current["PreSig"] = raw_target.get("PreSig", current.get("PreSig", ""))
        _merge_best_rank_metadata(current, raw_target, "HighProximity")
    elif source == NEW_HIGH_CONFIRMATION_SOURCE:
        if raw_flu_present:
            current["NewHighFluRate"] = raw_flu_rate
        current["NewHighTradeQty"] = max(
            current.get("NewHighTradeQty", 0),
            _safe_positive_int(raw_target.get("TradeQty")),
        )
        current["NewHighPrevTradeQtyRatio"] = max(
            current.get("NewHighPrevTradeQtyRatio", 0.0),
            _safe_float(raw_target.get("PrevTradeQtyRatio")),
        )
        current["NewHighPrice"] = max(
            current.get("NewHighPrice", 0),
            _safe_positive_int(raw_target.get("NewHighPrice")),
        )
        current["NewLowPrice"] = max(
            current.get("NewLowPrice", 0),
            _safe_positive_int(raw_target.get("NewLowPrice")),
        )
        current["NewHighPeriodDays"] = max(
            current.get("NewHighPeriodDays", 0),
            _safe_positive_int(raw_target.get("NewHighPeriodDays")),
        )
        current["PreSig"] = raw_target.get("PreSig", current.get("PreSig", ""))
        _merge_best_rank_metadata(current, raw_target, "NewHigh")
    elif source == LOW_REBOUND_RISING_MISSED_SOURCE:
        current["SourceFamily"] = LOW_REBOUND_RISING_MISSED_SOURCE_FAMILY
        current["RisingMissedLineage"] = (
            raw_target.get("RisingMissedLineage") or LOW_REBOUND_RISING_MISSED_LINEAGE
        )
        current["LowReboundPct"] = _safe_float(raw_target.get("LowReboundPct"))
        current["IntradayLowPrice"] = _safe_positive_int(
            raw_target.get("IntradayLowPrice")
        )
        current["IntradayHighPrice"] = _safe_positive_int(
            raw_target.get("IntradayHighPrice")
        )
        current["DistanceFromIntradayHighPct"] = _safe_float(
            raw_target.get("DistanceFromIntradayHighPct")
        )
        current["NegativeDisplayRebound"] = bool(
            raw_target.get("NegativeDisplayRebound")
        )
        current["LowReboundBaseSourceSignature"] = str(
            raw_target.get("LowReboundBaseSourceSignature") or ""
        )
        current["LowReboundCandleLimit"] = _safe_positive_int(
            raw_target.get("LowReboundCandleLimit")
        )
        if raw_target.get("LowReboundDisplayChangeRate") not in (None, ""):
            current["LowReboundDisplayChangeRate"] = _safe_float(
                raw_target.get("LowReboundDisplayChangeRate")
            )
    elif source == "SUPERNOVA":
        if raw_flu_present:
            current["SupernovaFluRate"] = raw_flu_rate
    strength_value, strength_available = _extract_strength_value(raw_target)
    if strength_available:
        current["CntrStr"] = max(current.get("CntrStr", 0.0), strength_value)
        current["CntrStrAvailable"] = True
    current["PriorityScore"] = max(
        current.get("PriorityScore", 0.0),
        _safe_float(raw_target.get("PriorityScore", raw_target.get("priority_score"))),
    )
    current["SpikeRate"] = max(
        current.get("SpikeRate", 0.0),
        _safe_float(raw_target.get("SpikeRate", raw_target.get("spike_rate"))),
    )
    current["TradeValue"] = max(
        current.get("TradeValue", 0),
        _safe_positive_int(raw_target.get("TradeValue", raw_target.get("trade_value"))),
    )
    volume_surge_rank = _safe_positive_int(raw_target.get("VolumeSurgeRank"))
    if volume_surge_rank > 0 and (
        _safe_positive_int(current.get("VolumeSurgeRank")) <= 0
        or volume_surge_rank < _safe_positive_int(current.get("VolumeSurgeRank"))
    ):
        current["VolumeSurgeMatched"] = True
        current["VolumeSurgeRank"] = volume_surge_rank
        current["VolumeSurgeRankPct"] = _safe_float(
            raw_target.get("VolumeSurgeRankPct")
        )
        current["VolumeSurgeUniverseSize"] = _safe_positive_int(
            raw_target.get("VolumeSurgeUniverseSize")
        )
        current["VolumeSurgeSortType"] = str(
            raw_target.get("VolumeSurgeSortType") or ""
        )
    _merge_best_rank_metadata(current, raw_target, "PriceJump")
    _merge_best_rank_metadata(current, raw_target, "HighProximity")
    _merge_best_rank_metadata(current, raw_target, "NewHigh")
    current["VIMotionCount"] = max(
        current.get("VIMotionCount", 0),
        _safe_positive_int(raw_target.get("VIMotionCount")),
    )

    price = _safe_positive_int(raw_target.get("Price", raw_target.get("cur_prc")))
    if price > 0:
        current["Price"] = price
    if "OPEN_TOP" in current["SourceSet"]:
        open_price = _safe_positive_int(current.get("OpenPrice"))
        current_price = _safe_positive_int(current.get("Price"))
        if open_price > 0 and current_price > 0:
            current["OpenFluRate"] = round(
                ((current_price - open_price) / open_price) * 100.0, 2
            )

    rank_now = _safe_int(raw_target.get("RankNow"))
    rank_prev = _safe_int(raw_target.get("RankPrev"))
    if rank_now > 0:
        current["RankNow"] = rank_now
    if rank_prev > 0:
        current["RankPrev"] = rank_prev
    vi_release_time = str(raw_target.get("VIReleaseTime") or "").strip()
    if vi_release_time:
        current["VIReleaseTime"] = max(
            str(current.get("VIReleaseTime") or ""), vi_release_time
        )

    current["Source"] = _representative_source(current["SourceSet"])
    scanner_flu_rate, scanner_flu_metric, scanner_flu_source = _scanner_flu_metric(
        current
    )
    current["FluRate"] = scanner_flu_rate
    current["ScannerFluRate"] = scanner_flu_rate
    current["ScannerFluRateMetric"] = scanner_flu_metric
    current["ScannerFluRateSource"] = scanner_flu_source
    current["SourceRole"] = _scanner_candidate_role(current)
    current["RisingStartScore"] = _rising_start_score(current)


def build_candidate_pool(
    realtime_rank_targets=None,
    price_jump_targets=None,
    volume_surge_targets=None,
    bid_imbalance_targets=None,
    high_proximity_targets=None,
    new_high_targets=None,
    soaring_targets=None,
    supernova_targets=None,
    value_targets=None,
    vi_targets=None,
    low_rebound_targets=None,
):
    candidate_pool = {}
    for target in realtime_rank_targets or []:
        _merge_candidate(candidate_pool, target, "REALTIME_RANK_START")
    for target in price_jump_targets or []:
        _merge_candidate(candidate_pool, target, "PRICE_JUMP_START")
    for target in volume_surge_targets or []:
        _merge_candidate(candidate_pool, target, "VOLUME_SURGE_POSITIVE")
    for target in bid_imbalance_targets or []:
        _merge_candidate(candidate_pool, target, "BID_IMBALANCE_SURGE")
    for target in high_proximity_targets or []:
        _merge_candidate(candidate_pool, target, HIGH_PROXIMITY_CONFIRMATION_SOURCE)
    for target in new_high_targets or []:
        _merge_candidate(candidate_pool, target, NEW_HIGH_CONFIRMATION_SOURCE)
    for target in soaring_targets or []:
        _merge_candidate(candidate_pool, target, "OPEN_TOP")
    for target in supernova_targets or []:
        _merge_candidate(candidate_pool, target, "SUPERNOVA")
    for target in value_targets or []:
        _merge_candidate(candidate_pool, target, "VALUE_TOP")
    for target in vi_targets or []:
        _merge_candidate(candidate_pool, target, "VI_TRIGGERED")
    for target in low_rebound_targets or []:
        _merge_candidate(candidate_pool, target, LOW_REBOUND_RISING_MISSED_SOURCE)
    return candidate_pool


def rank_candidates(candidate_pool):
    if bool(getattr(TRADING_RULES, "SCALP_SCANNER_PRIORITY_TIERING_ENABLED", False)):
        tier_rank = {
            "tier_a_acceleration_confirmed": 0,
            "tier_b_price_jump_candidate": 1,
            "tier_c_volume_confirmation": 2,
            "tier_d_late_rank_only": 3,
            "tier_z_source_only": 9,
        }
        return sorted(
            candidate_pool.values(),
            key=lambda item: (
                _under_10000_runtime_priority_rank(item),
                tier_rank.get(
                    _scanner_priority_profile(item).get("scanner_priority_tier"), 8
                ),
                -_scanner_priority_profile(item).get("scanner_priority_score", 0.0),
                _source_priority(item.get("Source")),
                -_safe_float(item.get("FluRate")),
            ),
        )
    return sorted(
        candidate_pool.values(),
        key=lambda item: (
            _under_10000_runtime_priority_rank(item),
            _source_priority(item.get("Source")),
            -_rising_start_score(item),
            -_freshness_score(item),
            -_safe_float(item.get("FluRate")),
        ),
    )


def _scanner_candidate_pre_filter_reason(target):
    price = _safe_positive_int(target.get("Price"))
    if price <= 0:
        return "invalid_or_stale_price"
    source_set = set(_source_signature(target))
    if LOW_REBOUND_RISING_MISSED_SOURCE in source_set:
        low_rebound_pct = _safe_float(target.get("LowReboundPct"))
        intraday_low = _safe_positive_int(target.get("IntradayLowPrice"))
        intraday_high = _safe_positive_int(target.get("IntradayHighPrice"))
        distance_from_high_pct = _safe_float(target.get("DistanceFromIntradayHighPct"))
        if intraday_low <= 0 or intraday_high <= 0 or price <= intraday_low:
            return "low_rebound_invalid_intraday_price"
        if low_rebound_pct < _low_rebound_min_pct():
            return "low_rebound_below_threshold"
        if distance_from_high_pct > _low_rebound_max_distance_from_high_pct():
            return "low_rebound_chase_risk"
        if not str(target.get("LowReboundBaseSourceSignature") or "").strip():
            return "low_rebound_base_source_missing"
        return ""
    flu_rate, _, _ = _scanner_flu_metric(target)
    if source_set == {"VALUE_TOP"}:
        if flu_rate <= 0:
            return "non_positive_liquidity_only_source"
        return "liquidity_only_source_not_seed"
    if source_set & BREAKOUT_CONFIRMATION_SOURCES and source_set.issubset(
        BREAKOUT_CONFIRMATION_SOURCES | {"VALUE_TOP", "OPEN_TOP"}
    ):
        return "breakout_confirmation_only_source_not_seed"
    if source_set in ({"VI_TRIGGERED"}, {"VI_TRIGGERED", "VALUE_TOP"}):
        return "vi_secondary_confirmation_only"
    if flu_rate <= 0:
        return "non_positive_rising_start"
    return ""


def _filter_picks_within_cooldown(recent_picks, now_ts, reentry_cooldown_sec):
    max_probe_sec = int(
        getattr(TRADING_RULES, "SCALP_SCANNER_PROBE_MAX_SEC", 300) or 300
    )
    return {
        code: meta
        for code, meta in (recent_picks or {}).items()
        if (
            (now_ts - float(meta.get("last_promoted_at", 0.0) or 0.0))
            < reentry_cooldown_sec
            or (
                str(meta.get("scanner_probe_state") or "") == "first_seen_probe"
                and (now_ts - float(meta.get("first_seen_at", 0.0) or 0.0))
                <= max_probe_sec
            )
        )
    }


def _scanner_identity_name(value):
    text = str(value or "").strip().upper()
    if text in {"", "-", "UNKNOWN", "NONE"}:
        return ""
    return "".join(char for char in text if char.isalnum())


def _scanner_anchor_reset_context(target, previous):
    previous = previous if isinstance(previous, dict) else {}
    current_name = _scanner_identity_name((target or {}).get("Name"))
    previous_name = _scanner_identity_name(previous.get("identity_name"))
    current_price = _safe_positive_int((target or {}).get("Price"))
    previous_price = _safe_positive_int(
        previous.get("last_price") or previous.get("first_price")
    )
    price_ratio = (
        current_price / previous_price
        if current_price > 0 and previous_price > 0
        else 0.0
    )
    name_changed = bool(
        current_name and previous_name and current_name != previous_name
    )
    price_discontinuous = bool(
        price_ratio >= 2.0 or (price_ratio > 0.0 and price_ratio <= 0.5)
    )
    reason = (
        "scanner_identity_name_changed"
        if name_changed
        else (
            "scanner_identity_price_discontinuity"
            if price_discontinuous
            else "not_applicable"
        )
    )
    return {
        "reset": bool(name_changed or price_discontinuous),
        "reason": reason,
        "previous_name": previous_name or "-",
        "current_name": current_name or "-",
        "previous_price": previous_price or "-",
        "current_price": current_price or "-",
        "price_ratio": round(price_ratio, 6) if price_ratio > 0 else "-",
    }


def _scanner_candidate_identity_decision(db, target):
    code = str((target or {}).get("Code") or "").strip()[:6]
    payload_name = str((target or {}).get("Name") or "").strip()
    fields = {
        "scanner_source_identity_guard_applied": False,
        "scanner_source_identity_guard_reason": "authoritative_name_unavailable",
        "scanner_source_identity_payload_name": payload_name or "-",
        "scanner_source_identity_authoritative_name": "-",
    }
    getter = getattr(db, "get_latest_stock_name", None)
    if not callable(getter) or not code:
        return {"blocked": False, "reason": "authoritative_name_unavailable", **fields}
    try:
        authoritative_name = str(getter(code) or "").strip()
    except Exception as exc:
        log_error(
            f"[SCANNER_SOURCE_IDENTITY_GUARD] latest name lookup failed ({code}): {exc}"
        )
        return {
            "blocked": False,
            "reason": "authoritative_name_lookup_failed",
            **fields,
        }
    fields.update(
        {
            "scanner_source_identity_guard_applied": bool(authoritative_name),
            "scanner_source_identity_guard_reason": "scanner_identity_ok",
            "scanner_source_identity_authoritative_name": authoritative_name or "-",
        }
    )
    payload_name_norm = _scanner_identity_name(payload_name)
    authoritative_name_norm = _scanner_identity_name(authoritative_name)
    if (
        payload_name
        and not payload_name.isascii()
        and payload_name_norm
        and authoritative_name_norm
        and payload_name_norm != authoritative_name_norm
    ):
        fields["scanner_source_identity_guard_reason"] = (
            "scanner_identity_name_mismatch"
        )
        return {"blocked": True, "reason": "scanner_identity_name_mismatch", **fields}
    return {"blocked": False, "reason": "scanner_identity_ok", **fields}


def _scanner_source_identity_quarantine_sec():
    raw_value = os.getenv(
        "KORSTOCKSCAN_SCANNER_SOURCE_IDENTITY_QUARANTINE_SEC",
        str(SCANNER_SOURCE_IDENTITY_QUARANTINE_SEC_DEFAULT),
    )
    try:
        return max(0, int(float(raw_value)))
    except (TypeError, ValueError):
        return SCANNER_SOURCE_IDENTITY_QUARANTINE_SEC_DEFAULT


def _should_promote_candidate(target, recent_picks, now_ts, reentry_cooldown_sec):
    code = target.get("Code")
    previous = (recent_picks or {}).get(code)
    if not previous:
        return True
    if _scanner_anchor_reset_context(target, previous)["reset"]:
        return True
    if str(previous.get("scanner_probe_state") or "") == "first_seen_probe":
        return True
    if (
        now_ts - float(previous.get("last_promoted_at", 0.0) or 0.0)
    ) >= reentry_cooldown_sec:
        return True

    current_sources = set(_source_signature(target))
    previous_sources = set(previous.get("last_source_signature") or [])
    if len(current_sources) > len(previous_sources):
        return True
    if "VALUE_TOP" in current_sources and "VALUE_TOP" not in previous_sources:
        return True
    if "VI_TRIGGERED" in current_sources and "VI_TRIGGERED" not in previous_sources:
        return True

    current_score = _freshness_score(target)
    previous_score = float(previous.get("last_score", 0.0) or 0.0)
    return previous_score > 0 and current_score >= previous_score * 1.2


def _scanner_real_source_guard_decision(target, recent_picks, now_ts):
    source_signature = _source_signature(target)
    raw_previous = (recent_picks or {}).get(target.get("Code")) or {}
    anchor_reset = _scanner_anchor_reset_context(target, raw_previous)
    previous = {} if anchor_reset["reset"] else raw_previous
    quarantine_sec = _scanner_source_identity_quarantine_sec()
    last_guard_reason = str(previous.get("last_guard_block_reason") or "")
    last_guard_blocked_at = _safe_float(previous.get("last_guard_blocked_at"), 0.0)
    quarantine_age_sec = (
        max(0.0, now_ts - last_guard_blocked_at) if last_guard_blocked_at > 0 else 0.0
    )
    if (
        quarantine_sec > 0
        and last_guard_reason == "scanner_identity_name_mismatch"
        and last_guard_blocked_at > 0
        and quarantine_age_sec < quarantine_sec
    ):
        return {
            "blocked": True,
            "reason": "scanner_identity_name_mismatch_quarantine",
            "candidate_role": _scanner_candidate_role(target),
            "source_signature": ",".join(source_signature),
            "scanner_source_identity_quarantine_sec": quarantine_sec,
            "scanner_source_identity_quarantine_age_sec": round(quarantine_age_sec, 3),
            "scanner_source_identity_quarantine_remaining_sec": round(
                quarantine_sec - quarantine_age_sec, 3
            ),
            "scanner_source_identity_quarantine_basis": "first_identity_mismatch_for_same_anchor",
        }
    if not bool(
        getattr(TRADING_RULES, "SCALP_SCANNER_REAL_SOURCE_GUARD_ENABLED", False)
    ):
        return {"blocked": False, "reason": "guard_disabled"}

    source_set = set(source_signature)
    candidate_role = _scanner_candidate_role(target)
    acceleration_reason = _acceleration_reason(target, previous)
    priority_profile = _scanner_priority_profile(target, previous)
    priority_tiering_enabled = bool(
        getattr(TRADING_RULES, "SCALP_SCANNER_PRIORITY_TIERING_ENABLED", False)
    )
    open_price_jump_without_volume_demoted = (
        priority_tiering_enabled
        and priority_profile.get("scanner_priority_reason")
        == "open_price_jump_without_volume_demoted"
    )
    previous_sources = set(previous.get("last_source_signature") or [])
    open_price_jump_volume_followup_confirmed = (
        priority_tiering_enabled
        and "OPEN_TOP" in previous_sources
        and "PRICE_JUMP_START" in previous_sources
        and "VOLUME_SURGE_POSITIVE" not in previous_sources
        and "OPEN_TOP" in source_set
        and "PRICE_JUMP_START" in source_set
        and "VOLUME_SURGE_POSITIVE" in source_set
    )
    if (
        priority_tiering_enabled
        and priority_profile.get("scanner_priority_tier") == "tier_d_late_rank_only"
    ):
        candidate_role = "late_confirmation"
        if acceleration_reason in {"new_realtime_rank_start_source"}:
            acceleration_reason = ""
    if open_price_jump_without_volume_demoted:
        candidate_role = "late_confirmation"
        acceleration_reason = ""
    if (
        priority_tiering_enabled
        and priority_profile.get("scanner_priority_tier") == "tier_z_source_only"
    ):
        candidate_role = "source_only"
        acceleration_reason = ""
    if (
        priority_tiering_enabled
        and priority_profile.get("scanner_priority_tier")
        == "tier_a_acceleration_confirmed"
    ):
        acceleration_reason = str(
            priority_profile.get("scanner_priority_reason") or acceleration_reason
        )
    first_price = _safe_positive_int(previous.get("first_price"))
    current_price = _safe_positive_int(target.get("Price"))
    current_flu, current_flu_metric, current_flu_source = _scanner_flu_metric(target)
    legacy_unknown_flu_anchor = (
        bool(previous)
        and previous.get("first_flu_rate") not in (None, "")
        and (
            not previous.get("first_flu_rate_metric")
            or not previous.get("first_flu_rate_source")
        )
    )
    previous_flu_metric = str(
        previous.get("first_flu_rate_metric")
        or (
            "legacy_unknown_flu_rate"
            if legacy_unknown_flu_anchor
            else current_flu_metric
        )
    )
    previous_flu_source = str(
        previous.get("first_flu_rate_source")
        or ("legacy_unknown" if legacy_unknown_flu_anchor else current_flu_source)
    )
    first_flu = _safe_float(previous.get("first_flu_rate"), current_flu)
    flu_metric_changed = bool(previous) and (
        previous_flu_metric != current_flu_metric
        or previous_flu_source != current_flu_source
    )
    price_delta = _price_delta_pct(first_price, current_price)
    flu_delta = current_flu - first_flu
    comparable_flu_delta = 0.0 if flu_metric_changed else flu_delta
    observed_context = {
        "first_seen_flu_rate": f"{first_flu:.2f}",
        "current_flu_rate": f"{current_flu:.2f}",
        "first_flu_rate_metric": previous_flu_metric,
        "current_flu_rate_metric": current_flu_metric,
        "first_flu_rate_source": previous_flu_source,
        "current_flu_rate_source": current_flu_source,
        "flu_metric_changed": flu_metric_changed,
        "first_price": str(first_price or current_price or "-"),
        "current_price": str(current_price or "-"),
        "price_delta_since_first_seen_pct": f"{price_delta:.2f}",
        "flu_delta_since_first_seen": f"{flu_delta:.2f}",
        "comparable_flu_delta_since_first_seen": f"{comparable_flu_delta:.2f}",
        "last_promoted_at": str(previous.get("last_promoted_at") or "-"),
        "scanner_anchor_reset_applied": bool(anchor_reset["reset"]),
        "scanner_anchor_reset_reason": anchor_reset["reason"],
        "scanner_anchor_previous_name": anchor_reset["previous_name"],
        "scanner_anchor_current_name": anchor_reset["current_name"],
        "scanner_anchor_previous_price": anchor_reset["previous_price"],
        "scanner_anchor_current_price": anchor_reset["current_price"],
        "scanner_anchor_price_ratio": anchor_reset["price_ratio"],
        **priority_profile,
    }
    first_seen_at = float(previous.get("first_seen_at", 0.0) or 0.0)
    probe_age = max(0.0, now_ts - first_seen_at) if first_seen_at > 0 else 0.0
    price_declined = (
        first_price > 0 and current_price > 0 and current_price < first_price
    )
    if previous:
        observed_context["probe_age_sec"] = f"{probe_age:.1f}"

    if (
        priority_tiering_enabled
        and priority_profile.get("scanner_priority_tier") == "tier_z_source_only"
    ):
        return {
            "blocked": True,
            "reason": "scanner_priority_source_only",
            "candidate_role": candidate_role,
            "source_signature": ",".join(source_signature),
            **observed_context,
        }

    if open_price_jump_volume_followup_confirmed:
        if price_declined:
            return {
                "blocked": True,
                "reason": "late_confirmation_price_declined",
                "candidate_role": candidate_role,
                "source_signature": ",".join(source_signature),
                **observed_context,
            }
        return {
            "blocked": False,
            "reason": "open_price_jump_volume_confirmed",
            "candidate_role": candidate_role,
            "acceleration_reason": "open_price_jump_volume_confirmed",
            "source_signature": ",".join(source_signature),
            **observed_context,
        }

    if candidate_role == "early_discovery":
        return {
            "blocked": False,
            "reason": acceleration_reason or "early_discovery_source_present",
            "candidate_role": candidate_role,
            "acceleration_reason": acceleration_reason,
            "source_signature": ",".join(source_signature),
            **observed_context,
        }

    if acceleration_reason:
        return {
            "blocked": False,
            "reason": acceleration_reason,
            "candidate_role": candidate_role,
            "acceleration_reason": acceleration_reason,
            "source_signature": ",".join(source_signature),
            **observed_context,
        }

    if not bool(
        getattr(
            TRADING_RULES, "SCALP_SCANNER_REAL_SOURCE_GUARD_BLOCK_LATE_FIRST_SEEN", True
        )
    ):
        return {
            "blocked": False,
            "reason": "late_first_seen_guard_disabled",
            "candidate_role": candidate_role,
            "source_signature": ",".join(source_signature),
            **observed_context,
        }

    min_probe_sec = int(getattr(TRADING_RULES, "SCALP_SCANNER_PROBE_MIN_SEC", 30) or 30)
    max_probe_sec = int(
        getattr(TRADING_RULES, "SCALP_SCANNER_PROBE_MAX_SEC", 300) or 300
    )
    min_price_delta = float(
        getattr(TRADING_RULES, "SCALP_SCANNER_PROBE_MIN_PRICE_DELTA_PCT", 0.15) or 0.15
    )
    min_flu_delta = float(
        getattr(TRADING_RULES, "SCALP_SCANNER_PROBE_MIN_FLU_DELTA_PCT", 0.30) or 0.30
    )

    if not previous:
        first_seen_reason = (
            "open_price_jump_requires_volume_or_followthrough"
            if open_price_jump_without_volume_demoted
            else "late_confirmation_first_seen_probe"
        )
        return {
            "blocked": True,
            "reason": first_seen_reason,
            "candidate_role": candidate_role,
            "source_signature": ",".join(source_signature),
            **priority_profile,
            "first_seen_flu_rate": f"{current_flu:.2f}",
            "current_flu_rate": f"{current_flu:.2f}",
            "first_flu_rate_metric": current_flu_metric,
            "current_flu_rate_metric": current_flu_metric,
            "first_flu_rate_source": current_flu_source,
            "current_flu_rate_source": current_flu_source,
            "flu_metric_changed": False,
            "first_price": str(current_price or "-"),
            "current_price": str(current_price or "-"),
            "price_delta_since_first_seen_pct": "0.00",
            "flu_delta_since_first_seen": "0.00",
            "comparable_flu_delta_since_first_seen": "0.00",
            "probe_age_sec": "0.0",
            "last_promoted_at": "-",
        }

    probe_confirmed = (
        min_probe_sec <= probe_age <= max_probe_sec
        and not price_declined
        and (price_delta >= min_price_delta or comparable_flu_delta >= min_flu_delta)
    )
    if probe_confirmed:
        return {
            "blocked": False,
            "reason": "probe_acceleration_confirmed",
            "candidate_role": candidate_role,
            "source_signature": ",".join(source_signature),
            **observed_context,
        }

    if source_set != {"VALUE_TOP"}:
        reason = _late_confirmation_probe_block_reason(
            probe_age=probe_age,
            min_probe_sec=min_probe_sec,
            max_probe_sec=max_probe_sec,
            price_declined=price_declined,
            flu_metric_changed=flu_metric_changed,
        )
        return {
            "blocked": True,
            "reason": reason,
            "candidate_role": candidate_role,
            "source_signature": ",".join(source_signature),
            **observed_context,
        }

    if not bool(
        getattr(
            TRADING_RULES, "SCALP_SCANNER_REAL_SOURCE_GUARD_BLOCK_VALUE_TOP_ONLY", True
        )
    ):
        return {
            "blocked": False,
            "reason": "value_top_only_guard_disabled",
            "candidate_role": candidate_role,
            "source_signature": ",".join(source_signature),
            **observed_context,
        }
    if bool(target.get("CntrStrAvailable", False)):
        return {
            "blocked": False,
            "reason": "strength_available",
            "candidate_role": candidate_role,
            "source_signature": ",".join(source_signature),
            **observed_context,
        }

    max_decline = float(
        getattr(TRADING_RULES, "SCALP_SCANNER_REAL_SOURCE_GUARD_MAX_DECLINE_PCT", 0.0)
        or 0.0
    )
    flu_declined = (
        False if flu_metric_changed else current_flu < (first_flu - max_decline)
    )

    price_declined = (
        first_price > 0 and current_price > 0 and current_price < first_price
    )

    previous_signature = tuple(previous.get("last_source_signature") or ())
    same_source_family = previous_signature == source_signature

    if same_source_family and (flu_declined or price_declined):
        return {
            "blocked": True,
            "reason": "value_top_only_repeat_deteriorating_without_strength",
            "source_signature": ",".join(source_signature),
            "first_seen_flu_rate": f"{first_flu:.2f}",
            "current_flu_rate": f"{current_flu:.2f}",
            "first_flu_rate_metric": previous_flu_metric,
            "current_flu_rate_metric": current_flu_metric,
            "first_flu_rate_source": previous_flu_source,
            "current_flu_rate_source": current_flu_source,
            "flu_metric_changed": flu_metric_changed,
            "first_price": str(first_price or "-"),
            "current_price": str(current_price or "-"),
            "price_delta_since_first_seen_pct": f"{price_delta:.2f}",
            "flu_delta_since_first_seen": f"{flu_delta:.2f}",
            "comparable_flu_delta_since_first_seen": f"{comparable_flu_delta:.2f}",
            "last_promoted_at": str(previous.get("last_promoted_at") or "-"),
        }

    reason = _late_confirmation_probe_block_reason(
        probe_age=probe_age,
        min_probe_sec=min_probe_sec,
        max_probe_sec=max_probe_sec,
        price_declined=price_declined,
        flu_metric_changed=flu_metric_changed,
    )
    return {
        "blocked": True,
        "reason": reason,
        "candidate_role": candidate_role,
        "source_signature": ",".join(source_signature),
        **observed_context,
    }


def _remember_pick(recent_picks, target, now_ts):
    raw_previous = recent_picks.get(target["Code"]) or {}
    previous = (
        {}
        if _scanner_anchor_reset_context(target, raw_previous)["reset"]
        else raw_previous
    )
    current_flu, current_flu_metric, current_flu_source = _scanner_flu_metric(target)
    recent_picks[target["Code"]] = {
        "last_promoted_at": now_ts,
        "last_source_signature": _source_signature(target),
        "last_score": _freshness_score(target),
        "first_seen_at": previous.get("first_seen_at", now_ts),
        "first_flu_rate": previous.get("first_flu_rate", current_flu),
        "first_flu_rate_metric": previous.get(
            "first_flu_rate_metric", current_flu_metric
        ),
        "first_flu_rate_source": previous.get(
            "first_flu_rate_source", current_flu_source
        ),
        "first_price": previous.get(
            "first_price", _safe_positive_int(target.get("Price"))
        ),
        "last_flu_rate": current_flu,
        "last_flu_rate_metric": current_flu_metric,
        "last_flu_rate_source": current_flu_source,
        "last_price": _safe_positive_int(target.get("Price")),
        "identity_name": str(target.get("Name") or "").strip(),
        "last_volume_surge_matched": bool(target.get("VolumeSurgeMatched")),
        "last_volume_surge_rank": _safe_positive_int(target.get("VolumeSurgeRank")),
        "last_volume_surge_rank_pct": _safe_float(target.get("VolumeSurgeRankPct")),
        "last_volume_surge_universe_size": _safe_positive_int(
            target.get("VolumeSurgeUniverseSize")
        ),
        "scanner_probe_state": "promoted",
        **_scanner_priority_profile(target, previous),
    }


def _remember_guard_block(recent_picks, target, now_ts, reason):
    raw_previous = recent_picks.get(target["Code"]) or {}
    previous = (
        {}
        if _scanner_anchor_reset_context(target, raw_previous)["reset"]
        else raw_previous
    )
    current_flu, current_flu_metric, current_flu_source = _scanner_flu_metric(target)
    reset_probe_anchor = reason == "late_confirmation_flu_metric_changed"
    first_seen_at = (
        now_ts if reset_probe_anchor else previous.get("first_seen_at", now_ts)
    )
    first_flu_rate = (
        current_flu
        if reset_probe_anchor
        else previous.get("first_flu_rate", current_flu)
    )
    first_flu_metric = (
        current_flu_metric
        if reset_probe_anchor
        else previous.get("first_flu_rate_metric", current_flu_metric)
    )
    first_flu_source = (
        current_flu_source
        if reset_probe_anchor
        else previous.get("first_flu_rate_source", current_flu_source)
    )
    first_price = (
        _safe_positive_int(target.get("Price"))
        if reset_probe_anchor
        else previous.get("first_price", _safe_positive_int(target.get("Price")))
    )
    recent_picks[target["Code"]] = {
        **previous,
        "last_guard_blocked_at": now_ts,
        "last_guard_block_reason": reason,
        "last_source_signature": _source_signature(target),
        "last_score": _freshness_score(target),
        "first_seen_at": first_seen_at,
        "first_flu_rate": first_flu_rate,
        "first_flu_rate_metric": first_flu_metric,
        "first_flu_rate_source": first_flu_source,
        "first_price": first_price,
        "last_flu_rate": current_flu,
        "last_flu_rate_metric": current_flu_metric,
        "last_flu_rate_source": current_flu_source,
        "last_price": _safe_positive_int(target.get("Price")),
        "identity_name": str(target.get("Name") or "").strip(),
        "last_volume_surge_matched": bool(target.get("VolumeSurgeMatched")),
        "last_volume_surge_rank": _safe_positive_int(target.get("VolumeSurgeRank")),
        "last_volume_surge_rank_pct": _safe_float(target.get("VolumeSurgeRankPct")),
        "last_volume_surge_universe_size": _safe_positive_int(
            target.get("VolumeSurgeUniverseSize")
        ),
        "scanner_probe_state": "first_seen_probe",
        "last_observed_at": now_ts,
        **_scanner_priority_profile(target, previous),
    }


def _scanner_source_guard_requires_first_seen_provenance(reason):
    reason_text = str(reason or "")
    if reason_text == "value_top_only_repeat_deteriorating_without_strength":
        return True
    return False


def _scanner_zero_context_fields(
    target, source_guard, current_flu, source_guard_context
):
    cntr_str_available = bool(target.get("CntrStrAvailable", False))
    first_seen_not_applicable = source_guard_context == "first_seen_not_applicable"
    return _zero_context_observation_fields(
        domain="scanner_source_guard",
        blocker=source_guard.get("reason") or "candidate_observed",
        states={
            "current_flu_rate": _zero_context_value_state(current_flu),
            "rank_jump": _zero_context_value_state(_rank_jump(target)),
            "spike_rate": _zero_context_value_state(target.get("SpikeRate")),
            "cntr_str": _zero_context_value_state(
                target.get("CntrStr"),
                missing=not cntr_str_available,
            ),
            "price_delta_since_first_seen_pct": _zero_context_value_state(
                source_guard.get("price_delta_since_first_seen_pct"),
                not_applicable=first_seen_not_applicable,
            ),
        },
    )


def _scanner_event_fields(target, source_guard=None):
    source_guard = source_guard or {}
    source_signature = source_guard.get("source_signature") or ",".join(
        _source_signature(target)
    )
    first_price = source_guard.get("first_price")
    current_price = source_guard.get("current_price") or str(
        _safe_positive_int(target.get("Price")) or "-"
    )
    first_flu = source_guard.get("first_seen_flu_rate")
    current_flu_value, current_flu_metric, current_flu_source = _scanner_flu_metric(
        target
    )
    current_flu = source_guard.get("current_flu_rate") or f"{current_flu_value:.2f}"
    priority_profile = _scanner_priority_profile(target)
    guard_reason = str(source_guard.get("reason") or "")
    last_promoted_at = source_guard.get("last_promoted_at")
    first_seen_missing = first_flu in (None, "", "-")
    last_promoted_missing = last_promoted_at in (None, "", "-")
    if guard_reason in {
        "late_confirmation_first_seen_probe",
        "open_price_jump_requires_volume_or_followthrough",
    }:
        source_guard_context = "normal_first_seen_block"
    elif _scanner_source_guard_requires_first_seen_provenance(guard_reason):
        source_guard_context = "repeat_guard_with_provenance"
    elif first_seen_missing or last_promoted_missing:
        source_guard_context = "first_seen_not_applicable"
    else:
        source_guard_context = "repeat_guard_with_provenance"
    rank_sign_diagnostics = _rank_change_sign_event_diagnostics(
        target, source_signature
    )
    is_low_rebound_source = LOW_REBOUND_RISING_MISSED_SOURCE in set(
        _source_signature(target)
    )
    return {
        "metric_role": "source_quality_gate",
        "decision_authority": "real_scalping_scanner_source_guard_only",
        "source_quality_gate": "scalping_scanner_real_source_guard",
        "window_policy": "intraday_operational_guard",
        "sample_floor": "not_applicable_runtime_guard",
        "primary_decision_metric": "funnel_count",
        "forbidden_uses": (
            "score_threshold_change,provider_route_change,order_price_change,"
            "quantity_or_cap_change,broker_guard_change,bot_restart_authority,"
            "ai_score_smoothing_live_gate,real_execution_quality_approval"
        ),
        "runtime_effect": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "source_signature": source_signature,
        "scanner_source_family": target.get("SourceFamily")
        or SCANNER_RISING_START_SOURCE_FAMILY,
        "scanner_source_role": target.get("SourceRole")
        or _scanner_candidate_role(target),
        "rising_start_score": _safe_float(
            target.get("RisingStartScore", _rising_start_score(target))
        ),
        "rank_change": _safe_int(target.get("RankChange")),
        "rank_change_sign": target.get("RankChangeSign"),
        "rank_change_sign_authority": (
            str(
                target.get("RankChangeSignAuthority")
                or RANK_CHANGE_SIGN_AUTHORITY_DEFAULT
            ).strip()
            or RANK_CHANGE_SIGN_AUTHORITY_DEFAULT
        ),
        "rank_change_sign_state": target.get("RankChangeSignState")
        or rank_sign_diagnostics["RankChangeSignState"],
        "rank_change_sign_consistency": target.get("RankChangeSignConsistency")
        or rank_sign_diagnostics["RankChangeSignConsistency"],
        "rank_change_score_input": max(0, _safe_int(target.get("RankChange"))),
        "rank_change_score_policy": "positive_signed_rank_delta_only_raw_rank_sign_unverified",
        "jump_rate": _safe_float(target.get("JumpRate")),
        "volume_surge_rate": _safe_float(
            target.get("VolumeSurgeRate", target.get("SpikeRate"))
        ),
        "bid_surge_rate": _safe_float(target.get("BidSurgeRate")),
        "scanner_filter_reason": (
            source_guard.get("reason") if source_guard.get("blocked") else ""
        ),
        "scanner_candidate_role": source_guard.get("candidate_role")
        or _scanner_candidate_role(target),
        "scanner_watch_budget_owner": target.get("ScannerWatchBudgetOwner")
        or source_guard.get("scanner_watch_budget_owner")
        or GENERAL_SCALPING,
        "scanner_watch_budget_policy": "general1_opening3_rising_residual_v1",
        "scanner_watch_budget_owner_source": "scanner_candidate_classification",
        "scanner_block_reason": (
            source_guard.get("reason") if source_guard.get("blocked") else ""
        ),
        "scanner_source_guard_context": source_guard_context,
        "scanner_source_guard_first_seen_required": source_guard_context
        == "repeat_guard_with_provenance",
        "scanner_promotion_reason": (
            "" if source_guard.get("blocked") else source_guard.get("reason")
        ),
        "scanner_promotion_id": source_guard.get("scanner_promotion_id") or "",
        "scanner_promotion_emitted_epoch": source_guard.get(
            "scanner_promotion_emitted_epoch"
        )
        or "",
        "scanner_priority_tier": source_guard.get("scanner_priority_tier")
        or priority_profile.get("scanner_priority_tier"),
        "scanner_priority_score": _safe_float(
            source_guard.get("scanner_priority_score")
            if source_guard.get("scanner_priority_score") is not None
            else priority_profile.get("scanner_priority_score")
        ),
        "scanner_priority_reason": source_guard.get("scanner_priority_reason")
        or priority_profile.get("scanner_priority_reason"),
        "scanner_demoted_reason": source_guard.get("scanner_demoted_reason")
        or priority_profile.get("scanner_demoted_reason"),
        "scanner_promotion_policy_version": source_guard.get(
            "scanner_promotion_policy_version"
        )
        or priority_profile.get("scanner_promotion_policy_version"),
        "first_seen_price": first_price,
        "current_price": current_price,
        "price_delta_since_first_seen_pct": source_guard.get(
            "price_delta_since_first_seen_pct"
        ),
        "first_seen_flu_rate": first_flu,
        "current_flu_rate": current_flu,
        "first_flu_rate_metric": source_guard.get("first_flu_rate_metric"),
        "current_flu_rate_metric": source_guard.get("current_flu_rate_metric")
        or current_flu_metric,
        "first_flu_rate_source": source_guard.get("first_flu_rate_source"),
        "current_flu_rate_source": source_guard.get("current_flu_rate_source")
        or current_flu_source,
        "flu_metric_changed": source_guard.get("flu_metric_changed"),
        "flu_delta_since_first_seen": source_guard.get("flu_delta_since_first_seen"),
        "comparable_flu_delta_since_first_seen": source_guard.get(
            "comparable_flu_delta_since_first_seen"
        ),
        "probe_age_sec": source_guard.get("probe_age_sec"),
        "last_promoted_at": last_promoted_at,
        "rank_jump": _rank_jump(target),
        "spike_rate": _safe_float(target.get("SpikeRate")),
        "priority_score": _safe_float(target.get("PriorityScore")),
        "cntr_str_available": bool(target.get("CntrStrAvailable", False)),
        "cntr_str": _safe_float(target.get("CntrStr")),
        "current_price_observed": _safe_positive_int(target.get("Price")),
        "current_source": target.get("Source"),
        "rising_missed_lineage": target.get("RisingMissedLineage")
        or (LOW_REBOUND_RISING_MISSED_LINEAGE if is_low_rebound_source else ""),
        "low_rebound_pct": (
            _safe_float(target.get("LowReboundPct")) if is_low_rebound_source else ""
        ),
        "intraday_low_price": (
            _safe_positive_int(target.get("IntradayLowPrice"))
            if is_low_rebound_source
            else ""
        ),
        "intraday_high_price": (
            _safe_positive_int(target.get("IntradayHighPrice"))
            if is_low_rebound_source
            else ""
        ),
        "distance_from_intraday_high_pct": (
            _safe_float(target.get("DistanceFromIntradayHighPct"))
            if is_low_rebound_source
            else ""
        ),
        "negative_display_rebound": (
            bool(target.get("NegativeDisplayRebound")) if is_low_rebound_source else ""
        ),
        "low_rebound_base_source_signature": target.get("LowReboundBaseSourceSignature")
        or "",
        "scanner_source_identity_guard_applied": source_guard.get(
            "scanner_source_identity_guard_applied", "not_evaluated"
        ),
        "scanner_source_identity_guard_reason": source_guard.get(
            "scanner_source_identity_guard_reason", "not_evaluated"
        ),
        "scanner_source_identity_payload_name": source_guard.get(
            "scanner_source_identity_payload_name", "not_evaluated"
        ),
        "scanner_source_identity_authoritative_name": source_guard.get(
            "scanner_source_identity_authoritative_name", "not_evaluated"
        ),
        **_scanner_zero_context_fields(
            target, source_guard, current_flu, source_guard_context
        ),
    }


def _log_scanner_candidate_event(stage, target, source_guard=None):
    emit_pipeline_event(
        "ENTRY_PIPELINE",
        str(target.get("Name") or "-"),
        str(target.get("Code") or ""),
        stage,
        fields=_scanner_event_fields(target, source_guard),
    )


def _log_scanner_real_source_guard_block(target, source_guard, now_ts):
    emit_pipeline_event(
        "ENTRY_PIPELINE",
        str(target.get("Name") or "-"),
        str(target.get("Code") or ""),
        "scalping_scanner_real_source_guard_block",
        fields={
            **_scanner_event_fields(target, {**source_guard, "blocked": True}),
            "scanner_real_source_guard_applied": True,
            "scanner_real_source_guard_skip_reason": source_guard.get("reason"),
            "scanner_real_source_guard_block_event_emitted": True,
            "last_promoted_at": source_guard.get("last_promoted_at"),
            "current_cntr_str_available": bool(target.get("CntrStrAvailable", False)),
            "guard_blocked_at_ts": now_ts,
        },
    )


def _scanner_runtime_target_payload(
    target, source_guard, record_id=None, *, now_ts=None
):
    fields = _scanner_event_fields(target, source_guard)
    return {
        "record_id": record_id,
        "code": str(target.get("Code") or "").strip()[:6],
        "name": str(target.get("Name") or ""),
        "strategy": "SCALPING",
        "trade_type": "SCALP",
        "status": "WATCHING",
        "position_tag": "SCANNER",
        "buy_price": _safe_positive_int(target.get("Price")),
        "added_time": float(now_ts or time.time()),
        "entry_armed_at_epoch": float(now_ts or time.time()),
        "scanner_promotion_id": fields.get("scanner_promotion_id") or "",
        "scanner_promotion_reason": fields.get("scanner_promotion_reason") or "",
        "scanner_promotion_emitted_epoch": fields.get("scanner_promotion_emitted_epoch")
        or "",
        "source_signature": fields.get("source_signature") or "",
        "current_price_observed": fields.get("current_price_observed"),
        "price_delta_since_first_seen_pct": fields.get(
            "price_delta_since_first_seen_pct"
        ),
        "scanner_source_family": fields.get("scanner_source_family"),
        "scanner_source_role": fields.get("scanner_source_role"),
        "rank_change": fields.get("rank_change"),
        "rank_change_sign": fields.get("rank_change_sign"),
        "rank_change_sign_authority": fields.get("rank_change_sign_authority"),
        "rank_change_sign_state": fields.get("rank_change_sign_state"),
        "rank_change_sign_consistency": fields.get("rank_change_sign_consistency"),
        "rank_change_score_input": fields.get("rank_change_score_input"),
        "rank_change_score_policy": fields.get("rank_change_score_policy"),
        "rising_missed_lineage": fields.get("rising_missed_lineage") or "",
        "scanner_watch_budget_owner": fields.get("scanner_watch_budget_owner")
        or GENERAL_SCALPING,
        "scanner_watch_budget_policy": fields.get("scanner_watch_budget_policy"),
        "scanner_watch_budget_owner_source": fields.get(
            "scanner_watch_budget_owner_source"
        ),
        "low_rebound_pct": fields.get("low_rebound_pct"),
        "intraday_low_price": fields.get("intraday_low_price"),
        "intraday_high_price": fields.get("intraday_high_price"),
        "distance_from_intraday_high_pct": fields.get(
            "distance_from_intraday_high_pct"
        ),
        "negative_display_rebound": bool(fields.get("negative_display_rebound")),
        "runtime_effect": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def promote_candidates(
    db,
    event_bus,
    ranked_targets,
    recent_picks,
    *,
    max_new_codes,
    reentry_cooldown_sec,
    token=None,
    now_ts=None,
):
    now_ts = time.time() if now_ts is None else now_ts
    new_codes_found = []
    promoted_target_payloads = []
    recent_picks = _filter_picks_within_cooldown(
        recent_picks, now_ts, reentry_cooldown_sec
    )
    watch_budget_enabled = _scanner_watch_budget_reallocation_enabled()
    now_dt = datetime.fromtimestamp(now_ts)
    opening_config = _scanner_watch_budget_opening_config()
    for target in ranked_targets:
        owner = classify_watch_budget_owner(
            source_signature=_source_signature(target),
            rising_missed_lineage=target.get("RisingMissedLineage"),
            position_tag="SCANNER",
            day_change_pct=_candidate_current_change_rate(target)[0],
            now_dt=now_dt,
            explicit_owner=target.get("ScannerWatchBudgetOwner"),
            opening_config=opening_config,
        )
        target["ScannerWatchBudgetOwner"] = owner
    owner_priority = {
        OPENING_ROTATION: 0,
        RISING_MISSED: 1,
        GENERAL_SCALPING: 2,
    }
    if watch_budget_enabled:
        ranked_targets = sorted(
            ranked_targets,
            key=lambda target: owner_priority.get(
                target.get("ScannerWatchBudgetOwner"), 3
            ),
        )
    max_active = _scalping_watching_max_active()
    _expire_after_buy_window_scanner_watching(db, now_ts)
    active_count = _active_scanner_watching_count(db)
    low_rebound_targets = [
        target
        for target in ranked_targets
        if _is_low_rebound_reserved_priority_target(target)
    ]
    low_rebound_candidates_present = bool(low_rebound_targets)
    low_rebound_active_floor = _low_rebound_active_floor()
    protected_low_rebound_codes = _recent_low_rebound_codes(
        recent_picks, low_rebound_targets
    )
    active_low_rebound_codes = _active_scanner_watching_codes(
        db, protected_low_rebound_codes
    )
    active_low_rebound_count = len(active_low_rebound_codes)
    low_rebound_floor_shortfall = max(
        0, low_rebound_active_floor - active_low_rebound_count
    )
    if low_rebound_candidates_present and low_rebound_floor_shortfall > 0:
        open_slots = max(0, max_active - active_count)
        replacement_needed = max(0, low_rebound_floor_shortfall - open_slots)
        replacement_needed = min(
            replacement_needed,
            len(low_rebound_targets),
            _low_rebound_floor_replacement_max_per_loop(),
        )
        expired_for_low_rebound = _expire_scanner_watching_for_low_rebound_floor(
            db,
            now_ts,
            max_to_expire=replacement_needed,
            protected_codes=protected_low_rebound_codes,
        )
        if expired_for_low_rebound:
            active_count = max(0, active_count - len(expired_for_low_rebound))
            event_bus.publish(
                "COMMAND_WS_UNREG",
                {
                    "codes": sorted({code for code in expired_for_low_rebound if code}),
                    "source": "scalping_scanner_low_rebound_floor_replace",
                    "reason": "low_rebound_active_floor",
                },
            )
            log_info(
                "[SCALPING_SCANNER_LOW_REBOUND_FLOOR_REPLACE] "
                f"expired={len(expired_for_low_rebound)} "
                f"codes={','.join(code for code in expired_for_low_rebound if code)} "
                f"floor={low_rebound_active_floor} active_low_rebound={active_low_rebound_count}"
            )
    max_new_limit = max(0, int(max_new_codes or 0))
    open_slots = max(0, max_active - active_count)
    replacement_probe_slots = 0
    replacement_probe_mode = False
    if (
        open_slots == 0
        and watch_budget_enabled
        and any(
            target.get("ScannerWatchBudgetOwner") in {OPENING_ROTATION, RISING_MISSED}
            for target in ranked_targets
        )
    ):
        replacement_probe_slots = min(4, max_new_limit)
        replacement_probe_mode = replacement_probe_slots > 0
        ranked_targets = ranked_targets[:replacement_probe_slots]
    remaining_slots = min(
        max_new_limit,
        open_slots + replacement_probe_slots,
    )
    if remaining_slots <= 0:
        print(
            "🧯 [SCALPING 스캐너 cap] 신규 후보 등록 생략 "
            f"active={active_count} max_active={max_active} max_new_codes={max_new_codes}"
        )
        return [], recent_picks
    low_rebound_reserved_slots = 0
    if low_rebound_candidates_present:
        low_rebound_reserved_slots = min(
            remaining_slots,
            max(_low_rebound_reserve_slots(), low_rebound_floor_shortfall),
        )
    general_slot_limit = (
        remaining_slots - low_rebound_reserved_slots
        if low_rebound_reserved_slots > 0
        else remaining_slots
    )
    low_rebound_promoted_count = 0
    general_promoted_count = 0
    owner_promoted_counts = {
        GENERAL_SCALPING: 0,
        OPENING_ROTATION: 0,
        RISING_MISSED: 0,
    }
    promotion_policy = watch_budget_limits(
        max_new_limit,
        opening_window_active=True,
    )

    for target in ranked_targets:
        code = target["Code"]
        if _has_active_non_scanner_scalping_watching_code(db, code):
            continue
        is_low_rebound_target = _is_low_rebound_target(target)
        is_low_rebound_reserved_priority_target = (
            _is_low_rebound_reserved_priority_target(target)
        )
        uses_low_rebound_reserved_slot = (
            is_low_rebound_reserved_priority_target
            and low_rebound_reserved_slots > 0
            and low_rebound_promoted_count < low_rebound_reserved_slots
        )
        if (
            not uses_low_rebound_reserved_slot
            and general_promoted_count >= general_slot_limit
        ):
            continue
        watch_owner = target.get("ScannerWatchBudgetOwner") or GENERAL_SCALPING
        if replacement_probe_mode and watch_owner == GENERAL_SCALPING:
            continue
        if watch_owner == GENERAL_SCALPING:
            owner_limit = promotion_policy.general_max
        elif watch_owner == OPENING_ROTATION:
            owner_limit = promotion_policy.opening_protected
        else:
            # The general slot is never borrowed.  Unused opening slots are
            # available to rising candidates after the opening-first pass.
            owner_limit = min(
                promotion_policy.rising_max_with_borrow,
                promotion_policy.rising_guaranteed
                + max(
                    0,
                    promotion_policy.opening_protected
                    - owner_promoted_counts[OPENING_ROTATION],
                ),
            )
        pre_filter_reason = _scanner_candidate_pre_filter_reason(target)
        if pre_filter_reason:
            source_guard = {
                "blocked": True,
                "reason": pre_filter_reason,
                "candidate_role": _scanner_candidate_role(target),
                "source_signature": ",".join(_source_signature(target)),
            }
            _log_scanner_candidate_event(
                "scalping_scanner_candidate_observed", target, source_guard
            )
            _log_scanner_real_source_guard_block(target, source_guard, now_ts)
            _remember_guard_block(recent_picks, target, now_ts, pre_filter_reason)
            continue
        if not _should_promote_candidate(
            target, recent_picks, now_ts, reentry_cooldown_sec
        ):
            continue

        source_guard = _scanner_real_source_guard_decision(target, recent_picks, now_ts)
        if source_guard.get("blocked"):
            _log_scanner_candidate_event(
                "scalping_scanner_candidate_observed",
                target,
                {**source_guard, "blocked": True},
            )
            _log_scanner_real_source_guard_block(target, source_guard, now_ts)
            print(
                "🧯 [SCALPING 스캐너 guard] "
                f"{target['Name']}({code}) real WATCHING 승격 차단 "
                f"reason={source_guard.get('reason')} "
                f"source_signature={source_guard.get('source_signature')} "
                f"first_flu={source_guard.get('first_seen_flu_rate')} "
                f"current_flu={source_guard.get('current_flu_rate')} "
                f"flu_delta={source_guard.get('flu_delta_since_first_seen')} "
                f"flu_metric={source_guard.get('current_flu_rate_metric')} "
                f"flu_source={source_guard.get('current_flu_rate_source')} "
                f"price_delta={source_guard.get('price_delta_since_first_seen_pct')} "
                f"probe_age={source_guard.get('probe_age_sec')} "
                f"last_promoted_at={source_guard.get('last_promoted_at')}"
            )
            if (
                source_guard.get("reason")
                != "scanner_identity_name_mismatch_quarantine"
            ):
                _remember_guard_block(
                    recent_picks, target, now_ts, source_guard.get("reason")
                )
            continue

        curr_p = float(target.get("Price", 0))
        if not kiwoom_utils.is_valid_stock(
            code, target["Name"], token=token, current_price=curr_p
        ):
            source_guard = {
                "blocked": True,
                "reason": "invalid_stock_filter",
                "candidate_role": _scanner_candidate_role(target),
                "source_signature": ",".join(_source_signature(target)),
            }
            _log_scanner_candidate_event(
                "scalping_scanner_candidate_observed", target, source_guard
            )
            _log_scanner_real_source_guard_block(target, source_guard, now_ts)
            _remember_guard_block(recent_picks, target, now_ts, "invalid_stock_filter")
            continue

        identity_decision = _scanner_candidate_identity_decision(db, target)
        if identity_decision.get("blocked"):
            source_guard = {
                **source_guard,
                **identity_decision,
                "candidate_role": _scanner_candidate_role(target),
                "source_signature": ",".join(_source_signature(target)),
            }
            _log_scanner_candidate_event(
                "scalping_scanner_candidate_observed",
                target,
                {**source_guard, "blocked": True},
            )
            _log_scanner_real_source_guard_block(target, source_guard, now_ts)
            log_error(
                "[SCANNER_SOURCE_IDENTITY_GUARD] candidate rejected "
                f"code={code} payload_name={identity_decision.get('scanner_source_identity_payload_name')} "
                "authoritative_name="
                f"{identity_decision.get('scanner_source_identity_authoritative_name')}"
            )
            _remember_guard_block(
                recent_picks,
                target,
                now_ts,
                "scanner_identity_name_mismatch",
            )
            continue
        source_guard = {
            **source_guard,
            **{
                key: value
                for key, value in identity_decision.items()
                if key.startswith("scanner_source_identity_")
            },
        }

        if watch_budget_enabled and owner_promoted_counts[watch_owner] >= owner_limit:
            continue

        score = _freshness_score(target)
        source_sig = ",".join(_source_signature(target))
        display_flu, display_flu_metric, display_flu_source = _scanner_flu_metric(
            target
        )
        print(
            f"🎯 [타겟 포착] {target['Name']} "
            f"(등락률: {display_flu:+.2f}% [{display_flu_metric}/{display_flu_source}], "
            f"체결강도: {_format_strength_display(target)}, "
            f"신선도점수: {score:.1f} | 출처: {target['Source']} [{source_sig}])"
        )
        try:
            with db.get_session() as session:
                today_date = datetime.now().date()

                record = db.find_reusable_watching_record(
                    session,
                    rec_date=today_date,
                    stock_code=code,
                    strategy="SCALPING",
                    position_tag="SCANNER",
                )

                if record:
                    record.stock_name = target["Name"]
                    if record.status in ("WATCHING", "COMPLETED", "EXPIRED"):
                        record.strategy = "SCALPING"
                        record.buy_price = curr_p
                        record.entry_armed_at_epoch = now_ts
                        record.status = "WATCHING"
                        record.position_tag = "SCANNER"
                else:
                    new_record = RecommendationHistory(
                        rec_date=today_date,
                        stock_code=code,
                        stock_name=target["Name"],
                        buy_price=curr_p,
                        trade_type="SCALP",
                        strategy="SCALPING",
                        status="WATCHING",
                        position_tag="SCANNER",
                        entry_armed_at_epoch=now_ts,
                    )
                    session.add(new_record)
                    record = new_record

                if hasattr(session, "flush"):
                    session.flush()
                record_id = getattr(record, "id", None)
        except Exception as e:
            log_error(f"⚠️ DB 저장 실패 ({code}): {e}")
            continue

        source_guard = {
            **source_guard,
            "scanner_promotion_id": f"SCANPROM-{code}-{int(float(now_ts or 0.0) * 1000)}",
            "scanner_promotion_emitted_epoch": f"{float(now_ts or 0.0):.3f}",
            "scanner_low_rebound_reserved_slots": low_rebound_reserved_slots,
            "scanner_low_rebound_reserved_promotion": uses_low_rebound_reserved_slot,
            "scanner_low_rebound_active_floor": low_rebound_active_floor,
            "scanner_low_rebound_active_count": active_low_rebound_count,
            "scanner_low_rebound_floor_shortfall": low_rebound_floor_shortfall,
            "scanner_watch_budget_owner": watch_owner,
            "scanner_watch_budget_owner_limit": owner_limit,
            "scanner_watch_budget_total_limit": remaining_slots,
        }
        if bool(
            getattr(TRADING_RULES, "SCALP_SCANNER_REAL_SOURCE_GUARD_ENABLED", False)
        ):
            _log_scanner_candidate_event(
                "scalping_scanner_candidate_promoted", target, source_guard
            )
        _remember_pick(recent_picks, target, now_ts)
        new_codes_found.append(code)
        owner_promoted_counts[watch_owner] += 1
        if uses_low_rebound_reserved_slot:
            low_rebound_promoted_count += 1
        else:
            general_promoted_count += 1
        promoted_target_payloads.append(
            _scanner_runtime_target_payload(
                target, source_guard, record_id=record_id, now_ts=now_ts
            )
        )

        if len(new_codes_found) >= remaining_slots:
            break
        if (
            low_rebound_reserved_slots <= 0
            or low_rebound_promoted_count >= low_rebound_reserved_slots
        ) and general_promoted_count >= general_slot_limit:
            break

    if new_codes_found:
        event_bus.publish(
            "COMMAND_WS_REG",
            {"codes": new_codes_found, "source": "scalping_scanner_promote"},
        )
        for payload in promoted_target_payloads:
            event_bus.publish("SCALPING_SCANNER_PROMOTED_TARGET", payload)
        print(f"📡 웹소켓 감시 등록 요청 완료: {len(new_codes_found)} 종목")

    return new_codes_found, recent_picks


def _fetch_scan_source(source_name, fetcher, *args, **kwargs):
    try:
        return fetcher(*args, **kwargs) or []
    except Exception as exc:
        log_error(f"🚨 [SCALPING 스캐너] {source_name} 조회 실패: {exc}")
        return []


def _positive_volume_surge_from_raw(raw_targets, limit=60):
    positive = []
    for item in raw_targets or []:
        if _safe_float((item or {}).get("FluRate", (item or {}).get("flu_rate"))) <= 0:
            continue
        pre_sig = (item or {}).get("PreSig")
        if pre_sig not in (None, "") and str(pre_sig or "").strip() not in {
            "1",
            "2",
            "+",
            "상한",
            "상승",
        }:
            continue
        positive.append({**item, "Source": "VOLUME_SURGE_POSITIVE"})
        if len(positive) >= int(limit or 60):
            break
    return positive


def _annotate_source_rank(raw_targets, *, prefix, sort_type):
    targets = [dict(item or {}) for item in (raw_targets or []) if item]
    universe_size = len(targets)
    annotated = []
    for index, item in enumerate(targets, start=1):
        item[f"{prefix}Matched"] = True
        item[f"{prefix}Rank"] = index
        item[f"{prefix}RankPct"] = (
            round(index / universe_size, 6) if universe_size > 0 else 0.0
        )
        item[f"{prefix}UniverseSize"] = universe_size
        item[f"{prefix}SortType"] = sort_type
        annotated.append(item)
    return annotated


def _annotate_volume_surge_rank(raw_targets):
    return _annotate_source_rank(
        raw_targets,
        prefix="VolumeSurge",
        sort_type="ka10023_sort_tp_1_surge_qty_desc",
    )


def _merge_low_rebound_universe(universe, targets, source):
    for raw_target in targets or []:
        code = kiwoom_utils.normalize_stock_code(
            (raw_target or {}).get("Code", (raw_target or {}).get("code", ""))
        )
        if not code:
            continue
        if source not in LOW_REBOUND_BASE_SOURCES and code not in universe:
            continue
        current = universe.setdefault(
            code,
            {
                "Code": code,
                "Name": (raw_target or {}).get(
                    "Name", (raw_target or {}).get("name", "")
                ),
                "Price": _safe_positive_int(
                    (raw_target or {}).get("Price", (raw_target or {}).get("cur_prc"))
                ),
                "SourceSet": set(),
                "BaseTargets": [],
                "PriorityScore": 0.0,
                "TradeValue": 0,
                "SpikeRate": 0.0,
            },
        )
        current["SourceSet"].add(source)
        current["BaseTargets"].append(raw_target)
        if (raw_target or {}).get("Name") or (raw_target or {}).get("name"):
            current["Name"] = (raw_target or {}).get(
                "Name", (raw_target or {}).get("name", "")
            )
        price = _safe_positive_int(
            (raw_target or {}).get("Price", (raw_target or {}).get("cur_prc"))
        )
        if price > 0:
            current["Price"] = price
        change_rate, has_change_rate = _candidate_current_change_rate(raw_target)
        if has_change_rate and source in LOW_REBOUND_BASE_SOURCES:
            current["LowReboundDisplayChangeRate"] = change_rate
        current["PriorityScore"] = max(
            _safe_float(current.get("PriorityScore")),
            _safe_float(
                (raw_target or {}).get(
                    "PriorityScore", (raw_target or {}).get("priority_score")
                )
            ),
        )
        current["TradeValue"] = max(
            _safe_positive_int(current.get("TradeValue")),
            _safe_positive_int(
                (raw_target or {}).get(
                    "TradeValue", (raw_target or {}).get("trade_value")
                )
            ),
        )
        current["SpikeRate"] = max(
            _safe_float(current.get("SpikeRate")),
            _safe_float(
                (raw_target or {}).get(
                    "SpikeRate", (raw_target or {}).get("spike_rate")
                )
            ),
        )
        volume_surge_rank = _safe_positive_int(
            (raw_target or {}).get("VolumeSurgeRank")
        )
        if volume_surge_rank > 0 and (
            _safe_positive_int(current.get("VolumeSurgeRank")) <= 0
            or volume_surge_rank < _safe_positive_int(current.get("VolumeSurgeRank"))
        ):
            current["VolumeSurgeMatched"] = True
            current["VolumeSurgeRank"] = volume_surge_rank
            current["VolumeSurgeRankPct"] = _safe_float(
                (raw_target or {}).get("VolumeSurgeRankPct")
            )
            current["VolumeSurgeUniverseSize"] = _safe_positive_int(
                (raw_target or {}).get("VolumeSurgeUniverseSize")
            )
            current["VolumeSurgeSortType"] = str(
                (raw_target or {}).get("VolumeSurgeSortType") or ""
            )
        _merge_best_rank_metadata(current, raw_target, "PriceJump")
        _merge_best_rank_metadata(current, raw_target, "HighProximity")
        _merge_best_rank_metadata(current, raw_target, "NewHigh")
        if source == HIGH_PROXIMITY_CONFIRMATION_SOURCE:
            current["HighProximityFluRate"] = _safe_float(
                (raw_target or {}).get("FluRate")
            )
            current["HighProximityDistancePct"] = _safe_float(
                (raw_target or {}).get("HighProximityDistancePct")
            )
            current["TodayHighPrice"] = _safe_positive_int(
                (raw_target or {}).get("TodayHighPrice")
            )
            current["TodayLowPrice"] = _safe_positive_int(
                (raw_target or {}).get("TodayLowPrice")
            )
        elif source == NEW_HIGH_CONFIRMATION_SOURCE:
            current["NewHighFluRate"] = _safe_float((raw_target or {}).get("FluRate"))
            current["NewHighPrice"] = _safe_positive_int(
                (raw_target or {}).get("NewHighPrice")
            )
            current["NewLowPrice"] = _safe_positive_int(
                (raw_target or {}).get("NewLowPrice")
            )
            current["NewHighPeriodDays"] = _safe_positive_int(
                (raw_target or {}).get("NewHighPeriodDays")
            )


def _is_low_rebound_prefetch_product_allowed(target):
    name = str((target or {}).get("Name") or "").upper()
    if any(keyword in name for keyword in LOW_REBOUND_PREFETCH_EXCLUDED_NAME_KEYWORDS):
        return False
    price = _safe_positive_int((target or {}).get("Price"))
    min_price = _safe_positive_int(getattr(TRADING_RULES, "MIN_PRICE", 0))
    if (
        min_price > 0
        and 0 < price < min_price
        and not _has_volume_surge_source_evidence(target)
    ):
        return False
    return True


def _low_rebound_prefetch_rank_key(target):
    source_set = set((target or {}).get("SourceSet") or [])
    change_rate, has_change_rate = _candidate_current_change_rate(target or {})
    eligible_change = has_change_rate and change_rate <= 0.5
    negative_or_flat = has_change_rate and change_rate <= 0.0
    pullback_band = has_change_rate and -6.0 <= change_rate <= 0.5
    multi_source = len(LOW_REBOUND_BASE_SOURCES & source_set)
    raw_volume = "VOLUME_SURGE_RAW" in source_set
    value_top = "VALUE_TOP" in source_set
    realtime_rank = "REALTIME_RANK_START" in source_set
    product_allowed = _is_low_rebound_prefetch_product_allowed(target or {})
    return (
        0 if product_allowed else 1,
        0 if eligible_change else 1,
        0 if negative_or_flat else 1,
        0 if pullback_band else 1,
        -multi_source,
        0 if raw_volume and value_top else 1,
        0 if raw_volume else 1,
        0 if realtime_rank else 1,
        -_safe_float((target or {}).get("SpikeRate")),
        -min(_safe_float((target or {}).get("TradeValue")), 50_000_000_000.0),
        str((target or {}).get("Code") or ""),
    )


def _build_low_rebound_universe(
    realtime_rank_targets=None,
    raw_volume_surge_targets=None,
    value_targets=None,
    price_jump_targets=None,
    high_proximity_targets=None,
    new_high_targets=None,
):
    universe = {}
    _merge_low_rebound_universe(universe, raw_volume_surge_targets, "VOLUME_SURGE_RAW")
    _merge_low_rebound_universe(universe, value_targets, "VALUE_TOP")
    _merge_low_rebound_universe(universe, realtime_rank_targets, "REALTIME_RANK_START")
    _merge_low_rebound_universe(universe, price_jump_targets, "PRICE_JUMP_START")
    _merge_low_rebound_universe(
        universe, high_proximity_targets, HIGH_PROXIMITY_CONFIRMATION_SOURCE
    )
    _merge_low_rebound_universe(
        universe, new_high_targets, NEW_HIGH_CONFIRMATION_SOURCE
    )
    return sorted(
        universe.values(),
        key=_low_rebound_prefetch_rank_key,
    )


def _select_low_rebound_prefetch_targets(universe, fetch_cap):
    selected = []
    stats = {
        "prefilter_eligible_count": 0,
        "prefilter_product_filtered_count": 0,
        "prefilter_change_rate_filtered_count": 0,
        "prefilter_base_source_missing_count": 0,
    }
    selection_reasons = []
    for target in universe:
        code = str((target or {}).get("Code") or "").strip()
        source_set = set((target or {}).get("SourceSet") or [])
        if not code or not (LOW_REBOUND_BASE_SOURCES & source_set):
            stats["prefilter_base_source_missing_count"] += 1
            continue
        if not _is_low_rebound_prefetch_product_allowed(target):
            stats["prefilter_product_filtered_count"] += 1
            continue
        change_rate, has_change_rate = _candidate_current_change_rate(target)
        if not has_change_rate or change_rate > 0.5:
            stats["prefilter_change_rate_filtered_count"] += 1
            continue
        stats["prefilter_eligible_count"] += 1
        if len(selected) >= int(fetch_cap or 0):
            continue
        reasons = []
        if change_rate < 0:
            reasons.append("negative_display")
        else:
            reasons.append("weak_display")
        if "VOLUME_SURGE_RAW" in source_set:
            reasons.append("volume_raw")
        if "VALUE_TOP" in source_set:
            reasons.append("value_top")
        if "REALTIME_RANK_START" in source_set:
            reasons.append("realtime_rank")
        if len(LOW_REBOUND_BASE_SOURCES & source_set) >= 2:
            reasons.append("multi_source")
        selected.append(target)
        selection_reasons.append(f"{code}:{'+'.join(reasons)}")
    return selected, stats, selection_reasons


def _build_low_rebound_rising_missed_targets(
    token,
    *,
    realtime_rank_targets=None,
    raw_volume_surge_targets=None,
    value_targets=None,
    price_jump_targets=None,
    high_proximity_targets=None,
    new_high_targets=None,
    emit_observation=False,
):
    candidates = []
    min_rebound_pct = _low_rebound_min_pct()
    chase_distance_pct = _low_rebound_max_distance_from_high_pct()
    candle_limit = _low_rebound_candle_limit()
    universe = _build_low_rebound_universe(
        realtime_rank_targets=realtime_rank_targets,
        raw_volume_surge_targets=raw_volume_surge_targets,
        value_targets=value_targets,
        price_jump_targets=price_jump_targets,
        high_proximity_targets=high_proximity_targets,
        new_high_targets=new_high_targets,
    )
    fetch_cap = _low_rebound_candle_fetch_cap()
    prefetch_targets, prefetch_stats, selection_reasons = (
        _select_low_rebound_prefetch_targets(universe, fetch_cap)
    )
    stats = {
        "universe_count": len(universe),
        "candidate_scan_cap": fetch_cap,
        "scanned_count": 0,
        "base_source_missing_count": 0,
        "change_rate_filtered_count": 0,
        "candle_fetch_attempted_count": 0,
        "candle_fetch_failed_count": 0,
        "missing_candle_count": 0,
        "invalid_candle_price_count": 0,
        "invalid_intraday_price_count": 0,
        "intraday_date_filter_applied_count": 0,
        "intraday_date_filter_unique_date_count": 0,
        "intraday_date_filter_latest_date": "",
        "below_rebound_threshold_count": 0,
        "chase_risk_filtered_count": 0,
        "passed_count": 0,
        "negative_display_candidate_count": 0,
        **prefetch_stats,
    }
    sampled_codes = []
    passed_codes = []
    for target in prefetch_targets:
        stats["scanned_count"] += 1
        code = str(target.get("Code") or "").strip()
        if code and len(sampled_codes) < fetch_cap:
            sampled_codes.append(code)
        if not code or not (
            LOW_REBOUND_BASE_SOURCES & set(target.get("SourceSet") or [])
        ):
            stats["base_source_missing_count"] += 1
            continue
        current_change_rate, has_change_rate = _candidate_current_change_rate(target)
        if not has_change_rate or current_change_rate > 0.5:
            stats["change_rate_filtered_count"] += 1
            continue
        stats["candle_fetch_attempted_count"] += 1
        try:
            candles = (
                kiwoom_utils.get_minute_candles_ka10080(token, code, limit=candle_limit)
                or []
            )
        except Exception as exc:
            stats["candle_fetch_failed_count"] += 1
            log_error(
                f"🚨 [SCALPING 스캐너] ka10080 저가반등 조회 실패 [{code}]: {exc}"
            )
            continue
        if not candles:
            stats["missing_candle_count"] += 1
            continue
        candles, date_filter_stats = _filter_low_rebound_intraday_candles(candles)
        stats["intraday_date_filter_applied_count"] += int(
            date_filter_stats.get("intraday_date_filter_applied_count") or 0
        )
        stats["intraday_date_filter_unique_date_count"] = max(
            int(stats.get("intraday_date_filter_unique_date_count") or 0),
            int(date_filter_stats.get("intraday_date_filter_unique_date_count") or 0),
        )
        latest_filter_date = str(
            date_filter_stats.get("intraday_date_filter_latest_date") or ""
        )
        if latest_filter_date:
            stats["intraday_date_filter_latest_date"] = latest_filter_date
        if not candles:
            stats["missing_candle_count"] += 1
            continue
        lows = [
            _low_rebound_price_from_candle(row, "저가", "Low", "low") for row in candles
        ]
        highs = [
            _low_rebound_price_from_candle(row, "고가", "High", "high")
            for row in candles
        ]
        lows = [price for price in lows if price > 0]
        highs = [price for price in highs if price > 0]
        if not lows or not highs:
            stats["invalid_candle_price_count"] += 1
            continue
        latest_current = _low_rebound_price_from_candle(
            candles[-1], "현재가", "Close", "close", "cur_prc"
        )
        current_price = latest_current or _safe_positive_int(target.get("Price"))
        intraday_low = min(lows)
        intraday_high = max(highs)
        if (
            current_price <= 0
            or intraday_low <= 0
            or current_price <= intraday_low
            or intraday_high <= 0
        ):
            stats["invalid_intraday_price_count"] += 1
            continue
        low_rebound_pct = round(
            ((current_price - intraday_low) / intraday_low) * 100.0, 2
        )
        if low_rebound_pct < min_rebound_pct:
            stats["below_rebound_threshold_count"] += 1
            continue
        distance_from_high_pct = round(
            ((current_price - intraday_high) / intraday_high) * 100.0, 2
        )
        if distance_from_high_pct > chase_distance_pct:
            stats["chase_risk_filtered_count"] += 1
            continue
        source_signature = sorted(set(target.get("SourceSet") or []))
        stats["passed_count"] += 1
        if current_change_rate < 0:
            stats["negative_display_candidate_count"] += 1
        passed_codes.append(code)
        candidates.append(
            {
                "Code": code,
                "Name": target.get("Name") or "",
                "Price": current_price,
                "FluRate": current_change_rate,
                "LowReboundDisplayChangeRate": current_change_rate,
                "LowReboundPct": low_rebound_pct,
                "IntradayLowPrice": intraday_low,
                "IntradayHighPrice": intraday_high,
                "DistanceFromIntradayHighPct": distance_from_high_pct,
                "NegativeDisplayRebound": current_change_rate < 0,
                "LowReboundBaseSourceSignature": ",".join(source_signature),
                "LowReboundCandleLimit": candle_limit,
                "RisingMissedLineage": LOW_REBOUND_RISING_MISSED_LINEAGE,
                "Source": LOW_REBOUND_RISING_MISSED_SOURCE,
                "SourceFamily": LOW_REBOUND_RISING_MISSED_SOURCE_FAMILY,
                "SourceRole": LOW_REBOUND_RISING_MISSED_ROLE,
                "PriorityScore": _safe_float(target.get("PriorityScore")),
                "TradeValue": _safe_positive_int(target.get("TradeValue")),
                "SpikeRate": _safe_float(target.get("SpikeRate")),
                "VolumeSurgeMatched": bool(target.get("VolumeSurgeMatched")),
                "VolumeSurgeRank": _safe_positive_int(target.get("VolumeSurgeRank")),
                "VolumeSurgeRankPct": _safe_float(target.get("VolumeSurgeRankPct")),
                "VolumeSurgeUniverseSize": _safe_positive_int(
                    target.get("VolumeSurgeUniverseSize")
                ),
                "VolumeSurgeSortType": str(target.get("VolumeSurgeSortType") or ""),
                "PriceJumpMatched": bool(target.get("PriceJumpMatched")),
                "PriceJumpRank": _safe_positive_int(target.get("PriceJumpRank")),
                "PriceJumpRankPct": _safe_float(target.get("PriceJumpRankPct")),
                "PriceJumpUniverseSize": _safe_positive_int(
                    target.get("PriceJumpUniverseSize")
                ),
                "PriceJumpSortType": str(target.get("PriceJumpSortType") or ""),
                "HighProximityMatched": bool(target.get("HighProximityMatched")),
                "HighProximityRank": _safe_positive_int(
                    target.get("HighProximityRank")
                ),
                "HighProximityRankPct": _safe_float(target.get("HighProximityRankPct")),
                "HighProximityUniverseSize": _safe_positive_int(
                    target.get("HighProximityUniverseSize")
                ),
                "HighProximitySortType": str(target.get("HighProximitySortType") or ""),
                "HighProximityFluRate": _safe_float(target.get("HighProximityFluRate")),
                "HighProximityDistancePct": _safe_float(
                    target.get("HighProximityDistancePct")
                ),
                "TodayHighPrice": _safe_positive_int(target.get("TodayHighPrice")),
                "TodayLowPrice": _safe_positive_int(target.get("TodayLowPrice")),
                "NewHighMatched": bool(target.get("NewHighMatched")),
                "NewHighRank": _safe_positive_int(target.get("NewHighRank")),
                "NewHighRankPct": _safe_float(target.get("NewHighRankPct")),
                "NewHighUniverseSize": _safe_positive_int(
                    target.get("NewHighUniverseSize")
                ),
                "NewHighSortType": str(target.get("NewHighSortType") or ""),
                "NewHighFluRate": _safe_float(target.get("NewHighFluRate")),
                "NewHighPrice": _safe_positive_int(target.get("NewHighPrice")),
                "NewLowPrice": _safe_positive_int(target.get("NewLowPrice")),
                "NewHighPeriodDays": _safe_positive_int(
                    target.get("NewHighPeriodDays")
                ),
            }
        )
    if emit_observation:
        _log_low_rebound_source_observation(
            stats,
            sampled_codes=sampled_codes,
            passed_codes=passed_codes,
            min_rebound_pct=min_rebound_pct,
            chase_distance_pct=chase_distance_pct,
            candle_limit=candle_limit,
            selection_reasons=selection_reasons,
        )
    return candidates


def _log_low_rebound_source_observation(
    stats,
    *,
    sampled_codes,
    passed_codes,
    min_rebound_pct,
    chase_distance_pct,
    candle_limit,
    selection_reasons,
):
    emit_pipeline_event(
        "ENTRY_PIPELINE",
        LOW_REBOUND_RISING_MISSED_SOURCE,
        "",
        "scalping_scanner_low_rebound_source_observed",
        fields={
            "metric_role": "funnel_count",
            "decision_authority": "scalping_scanner_source_only_low_rebound_observation",
            "source_quality_gate": "scalping_scanner_low_rebound_source_observation_contract",
            "window_policy": "intraday_runtime_source_observation",
            "sample_floor": "not_applicable_source_observation",
            "primary_decision_metric": "funnel_count",
            "forbidden_uses": (
                "score_threshold_change,provider_route_change,order_price_change,"
                "quantity_or_cap_change,broker_guard_change,bot_restart_authority,"
                "real_execution_quality_approval"
            ),
            "runtime_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "source_signature": LOW_REBOUND_RISING_MISSED_SOURCE,
            "scanner_source_family": LOW_REBOUND_RISING_MISSED_SOURCE_FAMILY,
            "scanner_source_role": LOW_REBOUND_RISING_MISSED_ROLE,
            "rising_missed_lineage": LOW_REBOUND_RISING_MISSED_LINEAGE,
            "low_rebound_min_pct": min_rebound_pct,
            "low_rebound_chase_distance_pct": chase_distance_pct,
            "low_rebound_candle_limit": candle_limit,
            "low_rebound_sampled_codes": ",".join(sampled_codes),
            "low_rebound_passed_codes": ",".join(passed_codes),
            "low_rebound_fetch_selection_reason": ",".join(selection_reasons),
            **{f"low_rebound_{key}": value for key, value in stats.items()},
        },
    )


def run_scalper_iteration(
    *,
    token,
    radar,
    db,
    event_bus,
    recent_picks,
    reentry_cooldown_sec,
    max_new_codes,
    open_top_limit,
    supernova_limit,
):
    realtime_rank_targets = _fetch_scan_source(
        "ka00198 실시간종목조회순위(30초)",
        kiwoom_utils.get_realtime_item_rank_ka00198,
        token,
        qry_tp="5",
        limit=60,
    )
    price_jump_targets = _fetch_scan_source(
        "ka10019 가격급등락",
        kiwoom_utils.get_price_jump_ka10019,
        token,
        mrkt_tp="000",
        minutes=3,
        limit=60,
    )
    price_jump_targets = _annotate_source_rank(
        price_jump_targets,
        prefix="PriceJump",
        sort_type="ka10019_flu_tp_1_recent_jump_desc",
    )
    raw_volume_surge_targets = _fetch_scan_source(
        "ka10023 거래량급증 raw",
        kiwoom_utils.scan_volume_spike_ka10023,
        token,
        mrkt_tp="000",
    )
    raw_volume_surge_targets = _annotate_volume_surge_rank(raw_volume_surge_targets)
    volume_surge_targets = _positive_volume_surge_from_raw(
        raw_volume_surge_targets, limit=supernova_limit
    )
    bid_imbalance_targets = _fetch_scan_source(
        "ka10021 호가잔량급증",
        kiwoom_utils.get_bid_balance_surge_ka10021,
        token,
        mrkt_tp="000",
        minutes=3,
        limit=60,
    )
    high_proximity_targets = _fetch_scan_source(
        "ka10018 고가근접",
        kiwoom_utils.get_high_price_proximity_ka10018,
        token,
        mrkt_tp="000",
        proximity="10",
        limit=60,
    )
    high_proximity_targets = _annotate_source_rank(
        high_proximity_targets,
        prefix="HighProximity",
        sort_type="ka10018_high_low_tp_1_alacc_rt_10_return_order",
    )
    new_high_targets = _fetch_scan_source(
        "ka10016 신고가",
        kiwoom_utils.get_new_high_ka10016,
        token,
        mrkt_tp="000",
        period_days=20,
        limit=60,
    )
    new_high_targets = _annotate_source_rank(
        new_high_targets,
        prefix="NewHigh",
        sort_type="ka10016_ntl_tp_1_dt_20_return_order",
    )
    soaring_targets = _fetch_scan_source(
        "ka10028 시가대비 상위",
        kiwoom_utils.get_top_open_fluctuation_ka10028,
        token,
        mrkt_tp="000",
        limit=open_top_limit,
    )
    value_targets = _fetch_scan_source(
        "ka10032 거래대금 상위",
        kiwoom_utils.get_value_top_ka10032,
        token,
        mrkt_tp="000",
        limit=60,
    )
    vi_targets = _fetch_scan_source(
        "ka10054 VI 발동",
        kiwoom_utils.get_vi_triggered_ka10054,
        token,
        mrkt_tp="000",
        limit=60,
    )
    low_rebound_targets = _build_low_rebound_rising_missed_targets(
        token,
        realtime_rank_targets=realtime_rank_targets,
        raw_volume_surge_targets=raw_volume_surge_targets,
        value_targets=value_targets,
        price_jump_targets=price_jump_targets,
        high_proximity_targets=high_proximity_targets,
        new_high_targets=new_high_targets,
        emit_observation=True,
    )

    candidate_pool = build_candidate_pool(
        realtime_rank_targets=realtime_rank_targets,
        price_jump_targets=price_jump_targets,
        volume_surge_targets=volume_surge_targets,
        bid_imbalance_targets=bid_imbalance_targets,
        high_proximity_targets=high_proximity_targets,
        new_high_targets=new_high_targets,
        soaring_targets=soaring_targets,
        value_targets=value_targets,
        vi_targets=vi_targets,
        low_rebound_targets=low_rebound_targets,
    )
    ranked_targets = rank_candidates(candidate_pool)
    return promote_candidates(
        db,
        event_bus,
        ranked_targets,
        recent_picks,
        max_new_codes=max_new_codes,
        reentry_cooldown_sec=reentry_cooldown_sec,
        token=token,
    )


# ==========================================
# 🦅 스캘핑 스캐너 (전방 탐색조)
# ==========================================
def run_scalper(is_test_mode=False):
    """
    [역할]
    90~120초 주기로 시장을 스캔하여 당일 수급이 폭발하거나 급등 전조가 보이는
    '초단타(Scalping)' 타겟을 발굴합니다.

    [아키텍처 흐름]
    1. 데이터 수집: kiwoom_utils/signal_radar(REST API)를 호출하여 등락률 상위 및 거래량 급증 종목을 가져옵니다.
    2. 필터링: is_valid_stock을 통해 동전주, ETF, 스팩주 등의 불순물을 걸러냅니다.
    3. DB 저장: 발굴된 종목을 SQLAlchemy ORM을 사용하여 안전하게 Upsert(삽입/업데이트) 합니다.
    4. 이벤트 발행: 'COMMAND_WS_REG' 이벤트를 EventBus에 쏘아, 웹소켓 모듈이 해당 종목의 실시간 틱 데이터 감시를 즉각 시작하도록 지시합니다.
    """
    print(
        "⚡ [SCALPING 스캐너] 초단타 감시 엔진 가동 (장초반/후반 60초, 그 외 90초 주기)..."
    )
    db = DBManager()
    event_bus = EventBus()  # 💡 전역 싱글톤 이벤트 버스

    # 같은 종목을 하루 종일 영구 제외하면 초반에 잡힌 이름만 오래 남게 됩니다.
    # 그래서 `already_picked` 대신 재등록 cooldown을 둬서, 한동안은 쉬게 하되
    # 다시 거래가 살아난 종목은 같은 날에도 재포착할 수 있게 만듭니다.
    recent_picks = {}
    last_closed_msg_time = 0  # 💡 장 마감 도배 방지용 타이머 추가
    last_active_window_key = None
    last_outside_reset_key = None
    reentry_cooldown_sec = 25 * 60
    max_new_codes = 12
    open_top_limit = 60
    supernova_limit = 60

    # 💡 무한 루프 밖에서 토큰과 레이더를 한 번만 초기화하여 부하 감소
    # (실제 운영 시에는 토큰 만료를 대비한 갱신 로직이 추가로 필요할 수 있음)

    token = kiwoom_utils.get_kiwoom_token()

    if not token:
        log_error("❌ 키움 토큰 발급 실패. 스캐너를 종료합니다.")
        return

    radar = SniperRadar(token)

    while True:
        now = datetime.now()
        now_time = now.time()
        now_ts = time.time()

        from src.engine.error_detectors.process_health import write_heartbeat as _sc_whb

        _sc_whb("scalping_scanner")

        active_window = _active_scalping_buy_window(now)
        if active_window:
            window_index, window_start, _window_end = active_window
            window_key = (now.date().isoformat(), window_index)
            if window_key != last_active_window_key:
                _reset_scanner_watch_targets(
                    db,
                    event_bus,
                    now_ts,
                    reason=f"buy_window_start:{window_index}",
                    armed_before_epoch=_window_start_epoch(now, window_start),
                )
                recent_picks = {}
                last_active_window_key = window_key
                last_outside_reset_key = None

        # 신규 후보 발굴은 실제 scalping BUY window와 동일하게 맞춘다.
        # 보유/청산 감시와 downstream hard/broker/order guards는 별도 유지한다.
        if not is_test_mode and active_window is None:
            reset_key = (
                ("after_buy_window", last_active_window_key)
                if last_active_window_key
                else (
                    "outside_buy_window_startup",
                    now.date().isoformat(),
                )
            )
            if reset_key != last_outside_reset_key:
                _reset_scanner_watch_targets(
                    db,
                    event_bus,
                    now_ts,
                    reason=str(reset_key[0]),
                )
                recent_picks = {}
                last_outside_reset_key = reset_key
            if time.time() - last_closed_msg_time > 3600:
                print(
                    "🌙 신규 스캘핑 후보 발굴 시간이 아닙니다. "
                    f"(buy_windows={describe_scalping_buy_windows()}) 보유/청산 감시는 계속됩니다."
                )
                last_closed_msg_time = time.time()
            time.sleep(60)
            continue

        scan_interval_sec = _resolve_scan_interval_sec(now_time)
        _, recent_picks = run_scalper_iteration(
            token=token,
            radar=radar,
            db=db,
            event_bus=event_bus,
            recent_picks=recent_picks,
            reentry_cooldown_sec=reentry_cooldown_sec,
            max_new_codes=max_new_codes,
            open_top_limit=open_top_limit,
            supernova_limit=supernova_limit,
        )

        time.sleep(scan_interval_sec)


if __name__ == "__main__":
    run_scalper(is_test_mode=True)
