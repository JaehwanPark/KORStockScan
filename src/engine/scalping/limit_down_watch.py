"""Rotating observation lane and bounded live-eligibility handoff."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
import time
from dataclasses import asdict, dataclass
from datetime import date, datetime, time as datetime_time
from pathlib import Path
from typing import Any, Callable

import pandas as pd
from sqlalchemy import text

from src.utils import kiwoom_utils
from src.utils.pipeline_event_logger import emit_pipeline_event

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
RUNTIME_DIR = DATA_DIR / "runtime"
CANDIDATE_DIR = DATA_DIR / "report" / "limit_down_watch_candidate_source"
SIM_POLICY_DIR = DATA_DIR / "threshold_cycle" / "scalp_sim_policies"
LIVE_AUTO_POLICY_DIR = DATA_DIR / "threshold_cycle" / "bounded_live_candidates"
LIMIT_DOWN_LIVE_UNLOCK_SOURCE = "LIMIT_DOWN_LIVE_UNLOCK"
LIMIT_DOWN_LIVE_POLICY_VERSION = "limit_down_single_verified_path_live_auto_v2"

DECISION_AUTHORITY = "limit_down_source_observation_only"
METRIC_ROLE = "diagnostic"
WINDOW_POLICY = "same_symbol_same_krx_session_ordered_0b_trade_and_0d_quote"
SAMPLE_FLOOR = "not_applicable_source_observation"
PRIMARY_DECISION_METRIC = "ordered_intraday_path_capture_rate"
SOURCE_QUALITY_GATE = (
    "official_ka10017_exact_or_completed_daily_near_limit_ka10081_db_match"
)
FORBIDDEN_USES = (
    "real_order,buy_analysis,threshold_change,provider_route_change,"
    "order_price_or_quantity_change,cap_change,broker_guard_change,bot_restart_authority"
)
NEAR_LIMIT_LOW_MIN_PCT = -29.5
NEAR_LIMIT_LOW_MAX_PCT = -27.0
NEAR_LIMIT_MIN_CLOSE_RECOVERY_PCT = 5.0
NEAR_LIMIT_MIN_DAILY_ROW_COUNT = 2_000
NEAR_LIMIT_LIVE_MIN_REBOUND_FROM_LOW_PCT = 1.0
EXACT_LIMIT_DOWN_COHORTS = {
    "consecutive_limit_down_2plus",
    "single_limit_down",
}
LIVE_AUTO_COHORTS = {*EXACT_LIMIT_DOWN_COHORTS, "near_limit_rebound"}


def _truthy(value: Any) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def feature_enabled() -> bool:
    return _truthy(os.getenv("KORSTOCKSCAN_LIMIT_DOWN_WATCH_ENABLED", "false"))


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value).replace(",", "").replace("+", "").strip()))
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return default


def _safe_price(value: Any, default: int = 0) -> int:
    return abs(_safe_int(value, default))


def _top_of_book(data: dict[str, Any]) -> tuple[int, int]:
    best_ask = _safe_price(data.get("best_ask") or data.get("ask"))
    best_bid = _safe_price(data.get("best_bid") or data.get("bid"))
    orderbook = data.get("orderbook")
    if isinstance(orderbook, dict):
        asks = orderbook.get("asks")
        bids = orderbook.get("bids")
        if best_ask <= 0 and isinstance(asks, list) and asks:
            best_ask = _safe_price((asks[0] or {}).get("price"))
        if best_bid <= 0 and isinstance(bids, list) and bids:
            best_bid = _safe_price((bids[0] or {}).get("price"))
    return best_ask, best_bid


def _pct(numerator: int, denominator: int) -> float | None:
    if numerator <= 0 or denominator <= 0:
        return None
    return round((numerator / denominator - 1.0) * 100.0, 6)


def price_band(price: int) -> str:
    if price < 1_000:
        return "under_1000"
    if price < 5_000:
        return "1000_4999"
    if price < 10_000:
        return "5000_9999"
    if price < 30_000:
        return "10000_29999"
    return "30000_plus"


def _canonical_hash(value: Any) -> str:
    raw = json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), default=str
    )
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with open(fd, "w", encoding="utf-8", closefd=True) as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, default=str)
            handle.flush()
        os.replace(temp_name, path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def _contract_fields() -> dict[str, Any]:
    return {
        "metric_role": METRIC_ROLE,
        "decision_authority": DECISION_AUTHORITY,
        "window_policy": WINDOW_POLICY,
        "sample_floor": SAMPLE_FLOOR,
        "primary_decision_metric": PRIMARY_DECISION_METRIC,
        "source_quality_gate": SOURCE_QUALITY_GATE,
        "forbidden_uses": FORBIDDEN_USES,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


@dataclass(frozen=True)
class LimitDownCandidate:
    code: str
    name: str
    source_trade_date: str
    limit_down_close: int
    consecutive_count: int
    cohort: str
    price_band: str
    volume: int
    source_api: str = "ka10017"
    source_quality: str = "pass"
    candidate_kind: str = "exact_limit_down"
    prior_close: int = 0
    trigger_low: int = 0
    trigger_low_change_pct: float | None = None
    close_recovery_from_low_pct: float | None = None


def _candidate_priority(candidate: LimitDownCandidate) -> tuple[int, int, str]:
    return (
        (
            0
            if candidate.consecutive_count >= 2
            else 1 if candidate.consecutive_count == 1 else 2
        ),
        -candidate.volume,
        candidate.code,
    )


def _db_near_limit_rebound_rows(
    db: Any, target_date: date
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Return a full-day DB prefilter; ka10081 remains row-level authority."""

    date_query = text("""
        SELECT quote_date, COUNT(*) AS row_count
        FROM daily_stock_quotes
        WHERE quote_date < :target_date
        GROUP BY quote_date
        ORDER BY quote_date DESC
        LIMIT 1
        """)
    with db.get_session() as session:
        source_row = session.execute(
            date_query, {"target_date": target_date}
        ).fetchone()
    if not source_row:
        return [], {"status": "blocked", "reason": "daily_source_date_missing"}
    source_date = (
        source_row[0].date() if isinstance(source_row[0], datetime) else source_row[0]
    )
    row_count = _safe_int(source_row[1])
    if not isinstance(source_date, date) or row_count < NEAR_LIMIT_MIN_DAILY_ROW_COUNT:
        return [], {
            "status": "blocked",
            "reason": "daily_source_incomplete",
            "source_trade_date": str(source_date or ""),
            "source_row_count": row_count,
            "required_row_count": NEAR_LIMIT_MIN_DAILY_ROW_COUNT,
        }

    candidate_query = text("""
        SELECT stock_code, stock_name, low_price, close_price, volume, daily_return
        FROM daily_stock_quotes
        WHERE quote_date = :source_date
          AND stock_code ~ '^[0-9]{6}$'
          AND low_price > 0
          AND close_price > 0
          AND daily_return IS NOT NULL
          AND (1.0 + daily_return) > 0
          AND ((low_price / (close_price / (1.0 + daily_return))) - 1.0) * 100.0
                BETWEEN :low_min_pct AND :low_max_pct
          AND ((close_price / low_price) - 1.0) * 100.0 >= :min_recovery_pct
        ORDER BY volume DESC NULLS LAST, stock_code
        """)
    params = {
        "source_date": source_date,
        "low_min_pct": NEAR_LIMIT_LOW_MIN_PCT,
        "low_max_pct": NEAR_LIMIT_LOW_MAX_PCT,
        "min_recovery_pct": NEAR_LIMIT_MIN_CLOSE_RECOVERY_PCT,
    }
    with db.get_session() as session:
        rows = session.execute(candidate_query, params).fetchall()
    normalized = []
    for row in rows:
        close_price = _safe_price(row[3])
        daily_return = _safe_float(row[5], -999.0)
        denominator = 1.0 + daily_return
        prior_close = round(close_price / denominator) if denominator > 0 else 0
        low_price = _safe_price(row[2])
        normalized.append(
            {
                "Code": str(row[0] or "").strip(),
                "Name": str(row[1] or "").strip(),
                "SourceTradeDate": source_date.isoformat(),
                "Low": low_price,
                "Close": close_price,
                "PreviousClose": prior_close,
                "Volume": _safe_int(row[4]),
                "LowChangePct": _pct(low_price, prior_close),
                "CloseRecoveryFromLowPct": _pct(close_price, low_price),
            }
        )
    return normalized, {
        "status": "pass",
        "source_trade_date": source_date.isoformat(),
        "source_row_count": row_count,
        "near_limit_candidate_count": len(normalized),
        "thresholds": {
            "low_change_pct_min": NEAR_LIMIT_LOW_MIN_PCT,
            "low_change_pct_max": NEAR_LIMIT_LOW_MAX_PCT,
            "close_recovery_from_low_pct_min": NEAR_LIMIT_MIN_CLOSE_RECOVERY_PCT,
        },
    }


def _db_completed_close(db: Any, code: str, quote_date: date) -> tuple[int, str]:
    query = text("""
        SELECT close_price, stock_name
        FROM daily_stock_quotes
        WHERE stock_code = :code AND quote_date = :quote_date
        LIMIT 1
        """)
    with db.get_session() as session:
        row = session.execute(
            query, {"code": code, "quote_date": quote_date}
        ).fetchone()
    if not row:
        return 0, ""
    return _safe_int(row[0]), str(row[1] or "").strip()


def _db_latest_completed_date(db: Any, target_date: date) -> date | None:
    query = text("""
        SELECT MAX(quote_date)
        FROM daily_stock_quotes
        WHERE quote_date < :target_date
        """)
    with db.get_session() as session:
        row = session.execute(query, {"target_date": target_date}).fetchone()
    value = row[0] if row else None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return datetime.fromisoformat(str(value)).date() if value else None
    except (TypeError, ValueError):
        return None


def build_candidate_source(
    token: str,
    db: Any,
    *,
    target_date: date | None = None,
    fetch_previous: (
        Callable[[str], tuple[list[dict[str, Any]], dict[str, Any]]] | None
    ) = None,
    fetch_daily: Callable[[str, str], Any] | None = None,
    db_close_loader: Callable[[Any, str, date], tuple[int, str]] | None = None,
    latest_completed_date_loader: Callable[[Any, date], date | None] | None = None,
    near_limit_loader: (
        Callable[[Any, date], tuple[list[dict[str, Any]], dict[str, Any]]] | None
    ) = None,
    near_eligibility_loader: (
        Callable[[str, list[str]], tuple[dict[str, dict[str, Any]], dict[str, Any]]]
        | None
    ) = None,
) -> tuple[list[LimitDownCandidate], dict[str, Any]]:
    """Build a fail-closed candidate source from official Kiwoom data."""

    target_date = target_date or datetime.now().date()
    fetch_previous = (
        fetch_previous or kiwoom_utils.get_previous_limit_down_stocks_ka10017
    )
    fetch_daily = fetch_daily or kiwoom_utils.get_daily_ohlcv_ka10081_df
    db_close_loader = db_close_loader or _db_completed_close
    latest_completed_date_loader = (
        latest_completed_date_loader or _db_latest_completed_date
    )
    near_limit_loader = near_limit_loader or _db_near_limit_rebound_rows
    near_eligibility_loader = (
        near_eligibility_loader or kiwoom_utils.get_stock_eligibility_map_ka10099
    )
    raw_rows, source_meta = fetch_previous(token)
    candidates: list[LimitDownCandidate] = []
    blocked: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    expected_source_date = latest_completed_date_loader(db, target_date)
    seen_counts: dict[str, str] = {}
    near_rows: list[dict[str, Any]] = []
    near_source_meta: dict[str, Any] = {
        "status": "not_requested_exact_candidates_present"
    }

    for raw in raw_rows or []:
        code = kiwoom_utils.normalize_stock_code((raw or {}).get("Code"))
        name = str((raw or {}).get("Name") or "").strip()
        raw_count = str((raw or {}).get("ConsecutiveCountRaw") or "").strip()
        if not code or not code.isdigit() or len(code) != 6:
            blocked.append({"code": code or "-", "reason": "invalid_stock_code"})
            continue
        if not raw_count.isdigit() or int(raw_count) <= 0:
            blocked.append({"code": code or "-", "reason": "invalid_consecutive_count"})
            continue
        if code in seen_counts:
            if seen_counts[code] == raw_count:
                excluded.append({"code": code, "reason": "duplicate_source_row"})
            else:
                blocked.append(
                    {
                        "code": code,
                        "reason": "duplicate_consecutive_count_conflict",
                    }
                )
            continue
        seen_counts[code] = raw_count
        if not kiwoom_utils.is_valid_stock(code, name, token=None):
            excluded.append({"code": code, "reason": "excluded_existing_stock_filter"})
            continue

        daily = fetch_daily(token, code)
        if daily is None or getattr(daily, "empty", True):
            blocked.append({"code": code, "reason": "ka10081_missing"})
            continue
        # A malformed ka10081 row can leave ``NaT`` in the DataFrame index.
        # Do not let it abort the whole source load (and hide otherwise valid
        # candidates); only completed, parseable daily rows may establish the
        # prior-limit-down close.
        try:
            parsed_index = pd.to_datetime(daily.index, errors="coerce")
            valid_index = parsed_index.notna()
            normalized_daily = daily.loc[valid_index].copy()
            normalized_daily.index = parsed_index[valid_index]
        except (AttributeError, TypeError, ValueError):
            blocked.append({"code": code, "reason": "ka10081_invalid_date_index"})
            continue
        if normalized_daily.empty:
            blocked.append({"code": code, "reason": "ka10081_no_valid_completed_dates"})
            continue
        eligible = normalized_daily[normalized_daily.index.date < target_date]
        if eligible.empty:
            blocked.append({"code": code, "reason": "completed_daily_row_missing"})
            continue
        latest_index = eligible.index.max()
        latest_row = eligible.loc[latest_index]
        completed_close = _safe_int(latest_row.get("Close"))
        source_date = latest_index.date()
        if expected_source_date is None or source_date != expected_source_date:
            blocked.append(
                {
                    "code": code,
                    "reason": "completed_daily_date_stale_or_mismatch",
                    "source_trade_date": source_date.isoformat(),
                    "expected_source_trade_date": (
                        expected_source_date.isoformat()
                        if expected_source_date is not None
                        else None
                    ),
                }
            )
            continue
        db_close, db_name = db_close_loader(db, code, source_date)
        if completed_close <= 0 or db_close <= 0 or completed_close != db_close:
            blocked.append(
                {
                    "code": code,
                    "reason": "ka10081_db_close_mismatch",
                    "source_trade_date": source_date.isoformat(),
                }
            )
            continue
        count = int(raw_count)
        candidates.append(
            LimitDownCandidate(
                code=code,
                name=name or db_name or code,
                source_trade_date=source_date.isoformat(),
                limit_down_close=completed_close,
                consecutive_count=count,
                cohort=(
                    "consecutive_limit_down_2plus"
                    if count >= 2
                    else "single_limit_down"
                ),
                price_band=price_band(completed_close),
                volume=_safe_int((raw or {}).get("Volume")),
            )
        )

    # The fallback is deliberately narrower than a generic shock scanner and
    # only runs when the official exact previous-limit-down source is empty.
    # A malformed or filtered exact row must not be hidden by the fallback.
    if not (raw_rows or []) and not blocked:
        near_rows, near_source_meta = near_limit_loader(db, target_date)
        if near_source_meta.get("status") == "pass":
            try:
                eligibility_by_code, eligibility_meta = near_eligibility_loader(
                    token,
                    [str((row or {}).get("Code") or "") for row in near_rows],
                )
            except Exception as exc:
                eligibility_by_code = {}
                eligibility_meta = {
                    "status": "blocked",
                    "reason": f"ka10099_exception:{type(exc).__name__}",
                }
            near_source_meta = {
                **near_source_meta,
                "official_eligibility_source": eligibility_meta,
            }
            for raw in near_rows:
                code = kiwoom_utils.normalize_stock_code((raw or {}).get("Code"))
                name = str((raw or {}).get("Name") or "").strip()
                if not code or not code.isdigit() or len(code) != 6:
                    blocked.append(
                        {"code": code or "-", "reason": "near_invalid_stock_code"}
                    )
                    continue
                if not kiwoom_utils.is_valid_stock(code, name, token=None):
                    excluded.append(
                        {"code": code, "reason": "near_excluded_existing_stock_filter"}
                    )
                    continue
                eligibility = eligibility_by_code.get(code)
                if not isinstance(eligibility, dict):
                    blocked.append(
                        {"code": code, "reason": "near_ka10099_eligibility_missing"}
                    )
                    continue
                if eligibility.get("eligible") is not True:
                    reasons = [
                        str(value)
                        for value in (eligibility.get("blocked_reasons") or [])
                    ]
                    known_exclusion = bool(
                        reasons
                        and all(
                            value
                            in {
                                "audit_info_excluded",
                                "management_state_excluded",
                                "order_warning_excluded",
                            }
                            for value in reasons
                        )
                    )
                    target = excluded if known_exclusion else blocked
                    target.append(
                        {
                            "code": code,
                            "reason": (
                                "near_ka10099_official_exclusion"
                                if known_exclusion
                                else "near_ka10099_eligibility_unknown"
                            ),
                            "eligibility_reasons": reasons,
                        }
                    )
                    continue
                try:
                    source_date = date.fromisoformat(
                        str((raw or {}).get("SourceTradeDate") or "")
                    )
                except ValueError:
                    blocked.append(
                        {"code": code, "reason": "near_source_trade_date_invalid"}
                    )
                    continue
                low_price = _safe_price((raw or {}).get("Low"))
                close_price = _safe_price((raw or {}).get("Close"))
                previous_close = _safe_price((raw or {}).get("PreviousClose"))
                low_change_pct = _pct(low_price, previous_close)
                recovery_pct = _pct(close_price, low_price)
                if not (
                    low_price > 0
                    and close_price > 0
                    and previous_close > 0
                    and low_change_pct is not None
                    and NEAR_LIMIT_LOW_MIN_PCT
                    <= low_change_pct
                    <= NEAR_LIMIT_LOW_MAX_PCT
                    and recovery_pct is not None
                    and recovery_pct >= NEAR_LIMIT_MIN_CLOSE_RECOVERY_PCT
                ):
                    blocked.append(
                        {"code": code, "reason": "near_threshold_contract_invalid"}
                    )
                    continue
                daily = fetch_daily(token, code)
                if daily is None or getattr(daily, "empty", True):
                    blocked.append({"code": code, "reason": "near_ka10081_missing"})
                    continue
                try:
                    parsed_index = pd.to_datetime(daily.index, errors="coerce")
                    valid_index = parsed_index.notna()
                    normalized_daily = daily.loc[valid_index].copy()
                    normalized_daily.index = parsed_index[valid_index]
                    completed = normalized_daily[
                        normalized_daily.index.date <= source_date
                    ].sort_index(ascending=False)
                except (AttributeError, TypeError, ValueError):
                    blocked.append(
                        {"code": code, "reason": "near_ka10081_invalid_date_index"}
                    )
                    continue
                source_rows = completed[completed.index.date == source_date]
                prior_rows = completed[completed.index.date < source_date]
                if source_rows.empty or prior_rows.empty:
                    blocked.append(
                        {"code": code, "reason": "near_ka10081_completed_rows_missing"}
                    )
                    continue
                official_source = source_rows.iloc[0]
                official_prior = prior_rows.iloc[0]
                official_low = _safe_price(official_source.get("Low"))
                official_close = _safe_price(official_source.get("Close"))
                official_previous_close = _safe_price(official_prior.get("Close"))
                db_close, db_name = db_close_loader(db, code, source_date)
                if not (
                    official_low == low_price
                    and official_close == close_price == db_close
                    and official_previous_close == previous_close
                ):
                    blocked.append(
                        {
                            "code": code,
                            "reason": "near_ka10081_db_ohlc_mismatch",
                            "source_trade_date": source_date.isoformat(),
                        }
                    )
                    continue
                candidates.append(
                    LimitDownCandidate(
                        code=code,
                        name=name or db_name or code,
                        source_trade_date=source_date.isoformat(),
                        limit_down_close=close_price,
                        consecutive_count=0,
                        cohort="near_limit_rebound",
                        price_band=price_band(close_price),
                        volume=_safe_int((raw or {}).get("Volume")),
                        source_api="daily_stock_quotes+ka10081",
                        candidate_kind="near_limit_rebound",
                        prior_close=previous_close,
                        trigger_low=low_price,
                        trigger_low_change_pct=low_change_pct,
                        close_recovery_from_low_pct=recovery_pct,
                    )
                )

    candidates.sort(key=_candidate_priority)
    fallback_source_blocked = bool(
        not (raw_rows or []) and near_source_meta.get("status") != "pass"
    )
    artifact = {
        "schema_version": 1,
        "report_type": "limit_down_watch_candidate_source",
        "target_date": target_date.isoformat(),
        "expected_source_trade_date": (
            expected_source_date.isoformat()
            if expected_source_date is not None
            else None
        ),
        "generated_at": datetime.now().isoformat(),
        "status": (
            "blocked"
            if blocked and not candidates
            else "partial" if blocked or fallback_source_blocked else "pass"
        ),
        "candidate_source_mode": (
            "official_exact_limit_down"
            if raw_rows
            else "exact_empty_near_limit_rebound_fallback"
        ),
        "source_meta": source_meta,
        "near_limit_source_meta": near_source_meta,
        "request_response_hash": _canonical_hash(
            {"rows": raw_rows, "source_meta": source_meta}
        ),
        "near_limit_source_hash": _canonical_hash(
            {"rows": near_rows, "source_meta": near_source_meta}
        ),
        "candidate_count": len(candidates),
        "blocked_count": len(blocked),
        "excluded_count": len(excluded),
        "candidates": [asdict(candidate) for candidate in candidates],
        "blocked_rows": blocked,
        "excluded_rows": excluded,
        **_contract_fields(),
    }
    _atomic_write_json(
        CANDIDATE_DIR
        / f"limit_down_watch_candidate_source_{target_date.isoformat()}.json",
        artifact,
    )
    return candidates, artifact


class LimitDownObservationRegistry:
    """Thread-safe single-code raw market-data sink and signal isolation registry."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._code = ""
        self._sink: Callable[[str, dict[str, Any], float], None] | None = None

    def activate(
        self, code: str, sink: Callable[[str, dict[str, Any], float], None]
    ) -> None:
        with self._lock:
            self._code = kiwoom_utils.normalize_stock_code(code)
            self._sink = sink

    def release(self, code: str = "") -> bool:
        normalized = kiwoom_utils.normalize_stock_code(code)
        with self._lock:
            if normalized and normalized != self._code:
                return False
            changed = bool(self._code)
            self._code = ""
            self._sink = None
            return changed

    def is_observation_only(self, code: str) -> bool:
        normalized = kiwoom_utils.normalize_stock_code(code)
        with self._lock:
            return bool(normalized and normalized == self._code)

    def active_code(self) -> str:
        with self._lock:
            return self._code

    def observe_raw_market_data(
        self,
        code: str,
        data: dict[str, Any],
        received_epoch: float | None = None,
        *,
        realtime_type: str = "0B",
    ) -> None:
        with self._lock:
            if not self._code:
                return
            normalized = kiwoom_utils.normalize_stock_code(code)
            sink = self._sink if normalized and normalized == self._code else None
        if sink is not None:
            payload = dict(data or {})
            payload["_limit_down_realtime_type"] = str(realtime_type or "").strip()
            sink(normalized, payload, received_epoch or time.time())

    def observe_raw_tick(
        self, code: str, data: dict[str, Any], received_epoch: float | None = None
    ) -> None:
        self.observe_raw_market_data(code, data, received_epoch, realtime_type="0B")


LIMIT_DOWN_OBSERVATION_REGISTRY = LimitDownObservationRegistry()


def is_observation_only_code(code: str) -> bool:
    return LIMIT_DOWN_OBSERVATION_REGISTRY.is_observation_only(code)


def observe_raw_tick(code: str, data: dict[str, Any], received_epoch=None) -> None:
    LIMIT_DOWN_OBSERVATION_REGISTRY.observe_raw_tick(code, data, received_epoch)


def observe_raw_market_data(
    code: str,
    data: dict[str, Any],
    received_epoch=None,
    *,
    realtime_type: str = "0B",
) -> None:
    LIMIT_DOWN_OBSERVATION_REGISTRY.observe_raw_market_data(
        code, data, received_epoch, realtime_type=realtime_type
    )


def _krx_session_phase(now_epoch: float) -> str:
    current_time = datetime.fromtimestamp(now_epoch).time()
    if current_time < datetime_time(9, 0):
        return "PREOPEN"
    if current_time <= datetime_time(15, 30):
        return "OPEN"
    return "ENDED"


class LimitDownWatchManager:
    """Own one rotating WS observation symbol without creating a trade target."""

    def __init__(self, token: str, db: Any, event_bus: Any) -> None:
        self.token = token
        self.db = db
        self.event_bus = event_bus
        self.candidates: list[LimitDownCandidate] = []
        self.active: LimitDownCandidate | None = None
        self.state: dict[str, Any] = {}
        self.last_visit: dict[str, float] = {}
        self.loaded_date = ""
        self.next_retry_epoch = 0.0
        self.last_snapshot_epoch = 0.0
        self.last_quote_snapshot_epoch = 0.0
        self.activity: dict[str, dict[str, Any]] = {}
        self.cell_visit_counts: dict[str, int] = {}
        self.active_sim_policy_keys: set[str] = set()
        self.sim_policy_source_date = ""
        self.active_live_policy_keys: set[str] = set()
        self.live_policy_by_key: dict[str, dict[str, Any]] = {}
        self.live_policy_source_date = ""
        self.live_policy_max_entry_spread_pct = 0.0
        self.last_release: dict[str, Any] | None = None
        self._lock = threading.RLock()

    @property
    def state_path(self) -> Path:
        return RUNTIME_DIR / f"limit_down_watch_state_{datetime.now().date()}.json"

    def active_slot_count(self) -> int:
        return 1 if feature_enabled() and self.active is not None else 0

    def _emit(self, stage: str, **fields: Any) -> None:
        candidate = self.active
        emit_pipeline_event(
            "LIMIT_DOWN_WATCH",
            candidate.name if candidate else "-",
            candidate.code if candidate else "-",
            stage,
            fields={**_contract_fields(), **fields},
        )

    def _write_state(self) -> None:
        payload = {
            "schema_version": 1,
            "target_date": datetime.now().date().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "heartbeat_epoch": time.time(),
            "enabled": feature_enabled(),
            "active_slot_count": self.active_slot_count(),
            "active_candidate": asdict(self.active) if self.active else None,
            "pool_hash": _canonical_hash([asdict(item) for item in self.candidates]),
            "state": self.state,
            "selection_policy": "coverage_first_then_evidence_weighted_v2",
            "candidate_activity": self.activity,
            "cell_visit_counts": self.cell_visit_counts,
            "active_sim_policy_keys": sorted(self.active_sim_policy_keys),
            "sim_policy_source_date": self.sim_policy_source_date,
            "active_live_policy_keys": sorted(self.active_live_policy_keys),
            "live_policy_source_date": self.live_policy_source_date,
            "live_policy_version": LIMIT_DOWN_LIVE_POLICY_VERSION,
            "live_policy_max_entry_spread_pct": self.live_policy_max_entry_spread_pct,
            "last_release": self.last_release,
            **_contract_fields(),
        }
        _atomic_write_json(self.state_path, payload)

    def _load_candidates(self, now_epoch: float) -> None:
        today = datetime.fromtimestamp(now_epoch).date()
        if self.loaded_date == today.isoformat() or now_epoch < self.next_retry_epoch:
            return
        try:
            self.candidates, artifact = build_candidate_source(
                self.token, self.db, target_date=today
            )
        except Exception as exc:
            self.candidates = []
            self.next_retry_epoch = now_epoch + 300.0
            self._emit(
                "limit_down_watch_source_blocked",
                reason=f"candidate_source_exception:{type(exc).__name__}",
            )
            return
        if artifact.get("status") == "blocked":
            self.candidates = []
            self.next_retry_epoch = now_epoch + 300.0
            self._emit(
                "limit_down_watch_source_blocked",
                reason="candidate_source_quality_blocked",
                source_hash=artifact.get("request_response_hash"),
                blocked_count=artifact.get("blocked_count"),
            )
            return
        self.loaded_date = today.isoformat()
        self.next_retry_epoch = 0.0
        self._load_sim_policy(today)
        self._load_live_policy(today)
        self._emit(
            "limit_down_watch_source_loaded",
            candidate_count=len(self.candidates),
            source_status=artifact.get("status"),
            source_hash=artifact.get("request_response_hash"),
            active_sim_policy_count=len(self.active_sim_policy_keys),
            sim_policy_source_date=self.sim_policy_source_date,
            active_live_policy_count=len(self.active_live_policy_keys),
            live_policy_source_date=self.live_policy_source_date,
        )

    def _load_sim_policy(self, target_date: date) -> None:
        candidates: list[tuple[date, Path]] = []
        for path in SIM_POLICY_DIR.glob("limit_down_watch_sim_policy_catalog_*.json"):
            suffix = path.stem.removeprefix("limit_down_watch_sim_policy_catalog_")
            try:
                policy_date = date.fromisoformat(suffix)
            except ValueError:
                continue
            if policy_date < target_date:
                candidates.append((policy_date, path))
        self.active_sim_policy_keys = set()
        self.sim_policy_source_date = ""
        if not candidates:
            return
        policy_date, path = max(candidates)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        policies = (
            payload.get("active_policies")
            if isinstance(payload, dict)
            and isinstance(payload.get("active_policies"), list)
            else []
        )
        valid = bool(
            payload.get("schema_version") == 1
            and payload.get("report_type") == "limit_down_watch_sim_policy_catalog"
            and payload.get("target_date") == policy_date.isoformat()
            and payload.get("status") == "pass"
            and payload.get("allowed_sim_apply") is True
            and payload.get("runtime_effect") is False
            and payload.get("actual_order_submitted") is False
            and payload.get("broker_order_forbidden") is True
            and payload.get("allowed_runtime_apply") is False
            and payload.get("active_policy_count") == len(policies)
        )
        if not valid:
            return
        self.active_sim_policy_keys = {
            str(row.get("policy_key"))
            for row in policies
            if isinstance(row, dict)
            and str(row.get("cohort") or "") in LIVE_AUTO_COHORTS
            and str(row.get("policy_key") or "")
            == f"{row.get('cohort')}|{row.get('price_band')}"
        }
        self.sim_policy_source_date = policy_date.isoformat()

    def _load_live_policy(self, target_date: date) -> None:
        candidates: list[tuple[date, Path]] = []
        for path in LIVE_AUTO_POLICY_DIR.glob(
            "limit_down_watch_bounded_live_candidate_*.json"
        ):
            suffix = path.stem.removeprefix("limit_down_watch_bounded_live_candidate_")
            try:
                policy_date = date.fromisoformat(suffix)
            except ValueError:
                continue
            if policy_date < target_date:
                candidates.append((policy_date, path))
        self.active_live_policy_keys = set()
        self.live_policy_by_key = {}
        self.live_policy_source_date = ""
        self.live_policy_max_entry_spread_pct = 0.0
        if not candidates:
            return
        policy_date, path = max(candidates)
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        policies = (
            payload.get("candidates")
            if isinstance(payload, dict) and isinstance(payload.get("candidates"), list)
            else []
        )
        risk = payload.get("risk_contract") if isinstance(payload, dict) else {}
        risk = risk if isinstance(risk, dict) else {}
        has_near_policy = any(
            isinstance(row, dict) and row.get("cohort") == "near_limit_rebound"
            for row in policies
        )
        valid = bool(
            payload.get("schema_version") == 1
            and payload.get("report_type") == "limit_down_watch_bounded_live_candidate"
            and payload.get("target_date") == policy_date.isoformat()
            and payload.get("status") == "live_auto_apply_ready"
            and payload.get("decision_authority")
            == "limit_down_live_auto_eligibility_candidate"
            and payload.get("operator_approval_required") is False
            and payload.get("preopen_consumer_implemented") is True
            and payload.get("activation_mode")
            == "latest_valid_prior_date_policy_auto_loaded"
            and payload.get("sample_floor")
            == "1_verified_ordered_path_per_cohort_price_band"
            and payload.get("runtime_effect") is False
            and payload.get("actual_order_submitted") is False
            and payload.get("broker_order_forbidden") is True
            and payload.get("allowed_runtime_apply") is True
            and payload.get("ready_candidate_count") == len(policies)
            and risk.get("max_concurrent_positions") == 1
            and risk.get("max_daily_entries") == 1
            and risk.get("quantity_owner") == "position_sizing_dynamic_formula"
            and risk.get("requested_quantity_override") is None
            and risk.get("scale_in_allowed") is False
            and risk.get("same_day_reentry_allowed") is False
            and risk.get("overnight_allowed") is False
            and risk.get("entry_requires_two_ordered_unlocked_ticks") is True
            and (
                risk.get("entry_requires_two_ordered_trigger_ticks") is True
                or (
                    not has_near_policy
                    and risk.get("entry_requires_two_ordered_trigger_ticks") is None
                )
            )
            and (
                not has_near_policy
                or (
                    risk.get("near_rebound_requires_session_open_recovery") is True
                    and _safe_float(risk.get("near_rebound_min_from_low_pct"))
                    == NEAR_LIMIT_LIVE_MIN_REBOUND_FROM_LOW_PCT
                )
            )
            and risk.get("entry_requires_fresh_quote_and_bbo") is True
            and risk.get("relock_or_stale_cancels_unfilled_entry") is True
            and 0.0 < _safe_float(risk.get("max_entry_spread_pct")) <= 1.5
            and risk.get("normal_scalping_ai_and_submit_guards_required") is True
            and risk.get("hard_safety_priority") == "unchanged_and_unbypassable"
        )
        if not valid:
            return
        policy_by_key = {
            str(row.get("policy_key")): dict(row)
            for row in policies
            if isinstance(row, dict)
            and str(row.get("cohort") or "") in LIVE_AUTO_COHORTS
            and str(row.get("policy_key") or "")
            == f"{row.get('cohort')}|{row.get('price_band')}"
            and _safe_int(row.get("sample_count")) >= 1
            and _safe_float(row.get("source_quality_adjusted_ev_pct")) > 0.0
            and _safe_float(row.get("downside_p10_pct")) > 0.0
            and _safe_float(row.get("mae_p10_pct"), -999.0) >= -5.0
            and _safe_float(row.get("relock_rate_pct"), 999.0) <= 0.0
            and _safe_float(row.get("entry_bbo_coverage_pct")) >= 100.0
            and row.get("evidence_mode") == "single_verified_ordered_path_allowed"
        }
        if len(policy_by_key) != len(policies) or not policy_by_key:
            return
        self.live_policy_by_key = policy_by_key
        self.active_live_policy_keys = set(policy_by_key)
        self.live_policy_source_date = policy_date.isoformat()
        self.live_policy_max_entry_spread_pct = _safe_float(
            risk.get("max_entry_spread_pct")
        )

    def _pick(
        self, active_codes: set[str], now_epoch: float
    ) -> LimitDownCandidate | None:
        cooldown = 300.0
        available = [
            item
            for item in self.candidates
            if item.code not in active_codes
            and now_epoch - self.last_visit.get(item.code, 0.0) >= cooldown
        ]
        if not available:
            return None

        # Exploration debt is paid before evidence-weighted exploitation. This
        # prevents a previously active/unlocked symbol (or a dense 2+ cohort)
        # from starving unseen candidates and price bands. Once every candidate
        # has one visit and every observed cell has two visits, the original
        # cohort/liquidity/activity preference resumes.
        unseen_exists = any(
            _safe_int(self.activity.get(item.code, {}).get("visit_count")) <= 0
            for item in available
        )

        def priority(item: LimitDownCandidate) -> tuple[Any, ...]:
            activity = self.activity.get(item.code, {})
            visit_count = _safe_int(activity.get("visit_count"))
            cell_key = f"{item.cohort}|{item.price_band}"
            cell_visit_count = _safe_int(self.cell_visit_counts.get(cell_key))
            tick_count = _safe_int(activity.get("tick_count"))
            unlock_count = _safe_int(activity.get("unlock_count"))
            trade_value = _safe_int(activity.get("trade_value"))
            last_tick_epoch = float(activity.get("last_tick_epoch") or 0.0)
            fresh_tick = last_tick_epoch > 0 and now_epoch - last_tick_epoch <= 30.0
            live_policy_rank = 0 if cell_key in self.active_live_policy_keys else 1
            if unseen_exists:
                return (
                    live_policy_rank,
                    0 if visit_count <= 0 else 1,
                    cell_visit_count,
                    0 if item.consecutive_count >= 2 else 1,
                    -item.volume,
                    item.code,
                )
            return (
                live_policy_rank,
                0 if cell_visit_count < 2 else 1,
                cell_visit_count if cell_visit_count < 2 else 0,
                visit_count if cell_visit_count < 2 else 0,
                0 if cell_key in self.active_sim_policy_keys else 1,
                0 if item.consecutive_count >= 2 else 1,
                0 if fresh_tick or unlock_count > 0 or tick_count > 0 else 1,
                -unlock_count,
                -trade_value,
                -tick_count,
                -item.volume,
                item.code,
            )

        return min(available, key=priority)

    def _activate(self, candidate: LimitDownCandidate, now_epoch: float) -> None:
        info = kiwoom_utils.get_basic_info_ka10001(self.token, candidate.code) or {}
        lower_limit = _safe_price(info.get("LowerLimitPrice"))
        if lower_limit <= 0 and candidate.cohort in EXACT_LIMIT_DOWN_COHORTS:
            self.next_retry_epoch = now_epoch + 300.0
            self.last_visit[candidate.code] = now_epoch
            self._emit(
                "limit_down_watch_source_blocked",
                reason="current_lower_limit_price_missing",
                candidate_code=candidate.code,
            )
            return
        self.active = candidate
        cell_key = f"{candidate.cohort}|{candidate.price_band}"
        activity = self.activity.setdefault(candidate.code, {})
        activity["visit_count"] = _safe_int(activity.get("visit_count")) + 1
        activity["last_selected_epoch"] = now_epoch
        self.cell_visit_counts[cell_key] = (
            _safe_int(self.cell_visit_counts.get(cell_key)) + 1
        )
        self.last_snapshot_epoch = 0.0
        self.last_quote_snapshot_epoch = 0.0
        self.state = {
            "phase": (
                "WAITING_FIRST_TRADE"
                if candidate.cohort == "near_limit_rebound"
                else "WAITING_FIRST_TICK"
            ),
            "registered_epoch": now_epoch,
            "last_transition_epoch": now_epoch,
            "lower_limit_price": lower_limit,
            "open_price": 0,
            "high_price": 0,
            "low_price": 0,
            "current_price": 0,
            "first_tick_epoch": 0.0,
            "last_tick_epoch": 0.0,
            "first_quote_epoch": 0.0,
            "last_quote_epoch": 0.0,
            "first_market_data_epoch": 0.0,
            "last_market_data_epoch": 0.0,
            "quote_count": 0,
            "trade_tick_count": 0,
            "unlock_count": 0,
            "relock_count": 0,
            "tick_count": 0,
            "transition_count": 0,
            "first_unlock_epoch": 0.0,
            "first_relock_epoch": 0.0,
            "consecutive_unlocked_tick_count": 0,
            "unlock_confirmed_epoch": 0.0,
            "consecutive_rebound_tick_count": 0,
            "rebound_confirmed_epoch": 0.0,
            "rebound_from_low_pct": None,
            "live_promotion_eligible_emitted": False,
            "requested_ws_route": "krx_regular_or_effective_integrated",
            "requested_ws_code_count": 1,
            "requested_ws_item_count_max": 1,
            "required_realtime_types": ["0D"],
            "last_reg_request_epoch": 0.0,
            "reg_request_count": 0,
            "selection_policy": "coverage_first_then_evidence_weighted_v2",
            "candidate_visit_count": activity["visit_count"],
            "cell_key": cell_key,
            "cell_visit_count": self.cell_visit_counts[cell_key],
            "sim_policy_key": cell_key,
            "sim_policy_matched": cell_key in self.active_sim_policy_keys,
            "sim_policy_source_date": self.sim_policy_source_date,
            "live_policy_key": cell_key,
            "live_policy_matched": cell_key in self.active_live_policy_keys,
            "live_policy_source_date": self.live_policy_source_date,
            "candidate_kind": candidate.candidate_kind,
            "trigger_low_change_pct": candidate.trigger_low_change_pct,
            "close_recovery_from_low_pct": candidate.close_recovery_from_low_pct,
        }
        LIMIT_DOWN_OBSERVATION_REGISTRY.activate(candidate.code, self.on_raw_tick)
        self._request_registration(now_epoch, reason="initial")
        self._emit(
            "limit_down_watch_registered",
            cohort=candidate.cohort,
            price_band=candidate.price_band,
            consecutive_count=candidate.consecutive_count,
            candidate_kind=candidate.candidate_kind,
            lower_limit_price=lower_limit,
            trigger_low_change_pct=candidate.trigger_low_change_pct,
            close_recovery_from_low_pct=candidate.close_recovery_from_low_pct,
            sim_policy_key=cell_key,
            sim_policy_matched=cell_key in self.active_sim_policy_keys,
            sim_policy_source_date=self.sim_policy_source_date,
            live_policy_key=cell_key,
            live_policy_matched=cell_key in self.active_live_policy_keys,
            live_policy_source_date=self.live_policy_source_date,
        )
        self._write_state()

    def _request_registration(self, now_epoch: float, *, reason: str) -> None:
        if self.active is None:
            return
        self.event_bus.publish(
            "COMMAND_WS_REG",
            {
                "codes": [self.active.code],
                "source": "limit_down_watch_observation",
                "reason": reason,
                "required_realtime_types": ("0D",),
            },
        )
        self.state["last_reg_request_epoch"] = now_epoch
        self.state["reg_request_count"] = (
            _safe_int(self.state.get("reg_request_count")) + 1
        )
        self._emit(
            "limit_down_watch_reg_requested",
            reason=reason,
            reg_request_count=self.state["reg_request_count"],
        )

    def release(self, *, reason: str, keep_ws: bool = False) -> None:
        with self._lock:
            candidate = self.active
            if candidate is None:
                return
            previous_phase = str(self.state.get("phase") or "WAITING_FIRST_TICK")
            terminal_phase = (
                "SESSION_ENDED"
                if reason in {"session_ended", "feature_disabled"}
                else "ROTATED"
            )
            released_epoch = time.time()
            self.state["phase"] = terminal_phase
            self.state["last_transition_epoch"] = released_epoch
            self.state["transition_count"] = (
                _safe_int(self.state.get("transition_count")) + 1
            )
            self._emit(
                "limit_down_watch_state_transition",
                previous_phase=previous_phase,
                phase=terminal_phase,
                reason=reason,
            )
            LIMIT_DOWN_OBSERVATION_REGISTRY.release(candidate.code)
            if not keep_ws:
                self.event_bus.publish(
                    "COMMAND_WS_UNREG",
                    {
                        "codes": [candidate.code],
                        "source": "limit_down_watch_observation",
                        "reason": reason,
                    },
                )
            self.last_visit[candidate.code] = released_epoch
            self._emit("limit_down_watch_released", reason=reason, keep_ws=keep_ws)
            self.last_release = {
                "candidate": asdict(candidate),
                "released_epoch": released_epoch,
                "reason": reason,
                "keep_ws": keep_ws,
                "state": dict(self.state),
            }
            self.active = None
            self.state = {}
            self._write_state()

    def relinquish_for_trading(self, code: str) -> bool:
        if self.active and self.active.code == kiwoom_utils.normalize_stock_code(code):
            self.release(reason="normal_scanner_claimed", keep_ws=True)
            return True
        return False

    def live_promotion_target(
        self,
        *,
        now_epoch: float | None = None,
        daily_promotion_count: int = 0,
    ) -> dict[str, Any] | None:
        """Return one guarded normal-scanner handoff; never submit an order."""

        now_epoch = time.time() if now_epoch is None else float(now_epoch)
        with self._lock:
            candidate = self.active
            if candidate is None or int(daily_promotion_count or 0) >= 1:
                return None
            if candidate.cohort not in LIVE_AUTO_COHORTS:
                return None
            cell_key = f"{candidate.cohort}|{candidate.price_band}"
            policy = self.live_policy_by_key.get(cell_key)
            if not policy:
                return None
            phase = str(self.state.get("phase") or "")
            last_tick_epoch = _safe_float(self.state.get("last_tick_epoch"))
            current = _safe_int(self.state.get("current_price"))
            lower_limit = _safe_int(self.state.get("lower_limit_price"))
            best_ask = _safe_int(self.state.get("best_ask"))
            best_bid = _safe_int(self.state.get("best_bid"))
            confirmed_epoch = _safe_float(self.state.get("unlock_confirmed_epoch"))
            rebound_confirmed_epoch = _safe_float(
                self.state.get("rebound_confirmed_epoch")
            )
            open_price = _safe_int(self.state.get("open_price"))
            low_price = _safe_int(self.state.get("low_price"))
            rebound_from_low_pct = _pct(current, low_price)
            exact_trigger = bool(
                candidate.cohort in EXACT_LIMIT_DOWN_COHORTS
                and phase in {"UNLOCKED", "UNLOCKED_AGAIN"}
                and confirmed_epoch > 0.0
                and _safe_int(self.state.get("consecutive_unlocked_tick_count")) >= 2
                and current > lower_limit > 0
            )
            near_trigger = bool(
                candidate.cohort == "near_limit_rebound"
                and phase == "NEAR_REBOUND_OBSERVING"
                and rebound_confirmed_epoch > 0.0
                and _safe_int(self.state.get("consecutive_rebound_tick_count")) >= 2
                and current >= open_price > 0
                and current > low_price > 0
                and rebound_from_low_pct is not None
                and rebound_from_low_pct >= NEAR_LIMIT_LIVE_MIN_REBOUND_FROM_LOW_PCT
            )
            if not (
                (exact_trigger or near_trigger)
                and 0.0 <= now_epoch - last_tick_epoch <= 5.0
                and best_ask >= best_bid > 0
                and best_ask >= current > 0
            ):
                return None
            spread_pct = (best_ask - best_bid) / best_ask * 100.0
            max_spread_pct = self.live_policy_max_entry_spread_pct
            if max_spread_pct <= 0.0:
                return None
            if spread_pct > max_spread_pct:
                return None
            unlock_from_lower_pct = _pct(current, lower_limit) or 0.0
            trigger_type = "exact_unlock" if exact_trigger else "near_rebound"
            return {
                "Code": candidate.code,
                "Name": candidate.name,
                "Price": current,
                "FluRate": (
                    unlock_from_lower_pct
                    if exact_trigger
                    else (_pct(current, candidate.limit_down_close) or 0.0)
                ),
                "TradeValue": _safe_int(self.state.get("trade_value")),
                "Volume": _safe_int(self.state.get("volume")),
                "PriorityScore": 220.0,
                "ScannerWatchBudgetOwner": "limit_down_rotation",
                "LimitDownLivePolicyKey": cell_key,
                "LimitDownLivePolicyMatched": True,
                "LimitDownLivePolicySourceDate": self.live_policy_source_date,
                "LimitDownLivePolicyVersion": LIMIT_DOWN_LIVE_POLICY_VERSION,
                "LimitDownLivePolicySampleCount": _safe_int(policy.get("sample_count")),
                "LimitDownLiveTriggerType": trigger_type,
                "LimitDownUnlockConfirmed": exact_trigger,
                "LimitDownUnlockConfirmedEpoch": confirmed_epoch,
                "LimitDownReboundConfirmed": near_trigger,
                "LimitDownReboundConfirmedEpoch": rebound_confirmed_epoch,
                "LimitDownLastTickEpoch": last_tick_epoch,
                "LimitDownLowerLimitPrice": lower_limit,
                "LimitDownBestAsk": best_ask,
                "LimitDownBestBid": best_bid,
                "LimitDownEntrySpreadPct": round(spread_pct, 6),
                "LimitDownMaxEntrySpreadPct": max_spread_pct,
                "LimitDownUnlockFromLowerPct": unlock_from_lower_pct,
                "LimitDownSessionOpenPrice": open_price,
                "LimitDownSessionLowPrice": low_price,
                "LimitDownReboundFromLowPct": rebound_from_low_pct,
                "LimitDownMinReboundFromLowPct": (
                    NEAR_LIMIT_LIVE_MIN_REBOUND_FROM_LOW_PCT
                ),
                "LimitDownCohort": candidate.cohort,
                "LimitDownPriceBand": candidate.price_band,
                "LimitDownConsecutiveCount": candidate.consecutive_count,
                "LimitDownRiskMaxDailyEntries": 1,
                "LimitDownScaleInAllowed": False,
                "LimitDownSameDayReentryAllowed": False,
                "LimitDownOvernightAllowed": False,
                "LimitDownNormalScalpingGuardsRequired": True,
            }

    def reconcile(
        self, *, active_codes: set[str] | None = None, now_epoch: float | None = None
    ) -> None:
        now_epoch = now_epoch or time.time()
        active_codes = {
            kiwoom_utils.normalize_stock_code(code) for code in (active_codes or set())
        }
        with self._lock:
            if not feature_enabled():
                self.release(reason="feature_disabled")
                self._write_state()
                return
            self._load_candidates(now_epoch)
            session_phase = _krx_session_phase(now_epoch)
            if session_phase != "OPEN":
                if self.active is not None:
                    self.release(
                        reason=(
                            "session_ended"
                            if session_phase == "ENDED"
                            else "preopen_wait"
                        )
                    )
                self._write_state()
                return
            if self.active and self.active.code in active_codes:
                self.release(reason="active_trade_target_conflict", keep_ws=True)
            if self.active:
                registered = float(self.state.get("registered_epoch") or now_epoch)
                last_transition = float(
                    self.state.get("last_transition_epoch") or registered
                )
                first_market_data = float(
                    self.state.get("first_market_data_epoch") or 0.0
                )
                last_reg_request = float(
                    self.state.get("last_reg_request_epoch") or registered
                )
                phase = str(self.state.get("phase") or "")
                dwell = now_epoch - registered
                unchanged = now_epoch - last_transition
                should_rotate = dwell >= 600.0 or (
                    phase
                    in {"WAITING_FIRST_TICK", "WAITING_FIRST_TRADE", "LIMIT_LOCKED"}
                    and dwell >= 180.0
                    and unchanged >= 180.0
                )
                if should_rotate and len(self.candidates) > 1:
                    self.release(reason="rotation_due")
                elif (
                    self.active is not None
                    and first_market_data <= 0
                    and now_epoch - last_reg_request >= 15.0
                ):
                    self._request_registration(
                        now_epoch, reason="first_market_data_pending"
                    )
            if self.active is None:
                candidate = self._pick(active_codes, now_epoch)
                if candidate is not None:
                    self._activate(candidate, now_epoch)
            self._write_state()

    def _on_raw_quote(
        self, code: str, data: dict[str, Any], received_epoch: float
    ) -> None:
        last_quote_epoch = float(self.state.get("last_quote_epoch") or 0.0)
        if received_epoch <= last_quote_epoch:
            return
        best_ask, best_bid = _top_of_book(data)
        if best_ask <= 0 and best_bid <= 0:
            return
        first_quote = float(self.state.get("first_quote_epoch") or 0.0) <= 0.0
        self.state["first_quote_epoch"] = (
            self.state.get("first_quote_epoch") or received_epoch
        )
        self.state["last_quote_epoch"] = received_epoch
        self.state["first_market_data_epoch"] = (
            self.state.get("first_market_data_epoch") or received_epoch
        )
        self.state["last_market_data_epoch"] = received_epoch
        self.state["quote_count"] = _safe_int(self.state.get("quote_count")) + 1
        self.state["best_ask"] = best_ask
        self.state["best_bid"] = best_bid
        self.state["spread"] = (
            max(0, best_ask - best_bid) if best_ask > 0 and best_bid > 0 else None
        )
        actual_ws_item = str(data.get("last_ws_item") or "")
        actual_ws_route = str(data.get("last_ws_market_route") or "unknown")
        self.state["actual_ws_item"] = actual_ws_item
        self.state["actual_ws_route"] = actual_ws_route
        self.state["actual_ws_item_count"] = 1 if actual_ws_item else 0
        activity = self.activity.setdefault(code, {})
        activity["quote_count"] = _safe_int(activity.get("quote_count")) + 1
        activity["last_quote_epoch"] = received_epoch
        if first_quote:
            self._emit(
                "limit_down_watch_quote_observed",
                phase=self.state.get("phase"),
                cohort=self.active.cohort if self.active else "unknown",
                price_band=self.active.price_band if self.active else "unknown",
                best_ask=best_ask,
                best_bid=best_bid,
                actual_ws_item=actual_ws_item,
                actual_ws_route=actual_ws_route,
                registration_latency_sec=round(
                    max(
                        0.0,
                        received_epoch
                        - _safe_float(self.state.get("registered_epoch")),
                    ),
                    6,
                ),
            )
        if received_epoch - self.last_quote_snapshot_epoch >= 5.0:
            self.last_quote_snapshot_epoch = received_epoch
            self._emit(
                "limit_down_watch_quote_snapshot",
                phase=self.state.get("phase"),
                cohort=self.active.cohort if self.active else "unknown",
                price_band=self.active.price_band if self.active else "unknown",
                market_data_type="0D",
                quote_count=self.state.get("quote_count"),
                trade_tick_count=self.state.get("trade_tick_count"),
                first_quote_epoch=self.state.get("first_quote_epoch"),
                last_quote_epoch=self.state.get("last_quote_epoch"),
                first_tick_epoch=self.state.get("first_tick_epoch"),
                last_tick_epoch=self.state.get("last_tick_epoch"),
                current_price=self.state.get("current_price"),
                best_ask=best_ask,
                best_bid=best_bid,
                spread=self.state.get("spread"),
                actual_ws_item=actual_ws_item,
                actual_ws_route=actual_ws_route,
                actual_ws_item_count=self.state.get("actual_ws_item_count"),
            )
            self._write_state()

    def on_raw_tick(
        self, code: str, data: dict[str, Any], received_epoch: float
    ) -> None:
        with self._lock:
            if self.active is None or code != self.active.code:
                return
            if str(data.get("_limit_down_realtime_type") or "0B") == "0D":
                self._on_raw_quote(code, data, received_epoch)
                return
            last_epoch = float(self.state.get("last_tick_epoch") or 0.0)
            if received_epoch <= last_epoch:
                return
            current = _safe_price(
                data.get("curr") or data.get("current_price") or data.get("cur_prc")
            )
            if current <= 0:
                return
            open_price = _safe_price(data.get("open") or data.get("open_price"))
            high_price = _safe_price(data.get("high") or data.get("high_price"))
            low_price = _safe_price(data.get("low") or data.get("low_price"))
            self.state["last_tick_epoch"] = received_epoch
            self.state["tick_count"] = _safe_int(self.state.get("tick_count")) + 1
            self.state["trade_tick_count"] = (
                _safe_int(self.state.get("trade_tick_count")) + 1
            )
            self.state["first_tick_epoch"] = (
                self.state.get("first_tick_epoch") or received_epoch
            )
            self.state["first_market_data_epoch"] = (
                self.state.get("first_market_data_epoch") or received_epoch
            )
            self.state["last_market_data_epoch"] = received_epoch
            self.state["current_price"] = current
            if open_price > 0:
                self.state["open_price"] = self.state.get("open_price") or open_price
            self.state["high_price"] = max(
                _safe_int(self.state.get("high_price")), high_price, current
            )
            existing_low = _safe_int(self.state.get("low_price"))
            positive_lows = [
                value for value in (existing_low, low_price, current) if value > 0
            ]
            self.state["low_price"] = min(positive_lows) if positive_lows else 0

            lower_limit = _safe_int(self.state.get("lower_limit_price"))
            previous_phase = str(self.state.get("phase") or "WAITING_FIRST_TICK")
            exact_candidate = self.active.cohort in EXACT_LIMIT_DOWN_COHORTS
            locked = bool(exact_candidate and current <= lower_limit)
            best_ask, best_bid = _top_of_book(data)
            if not exact_candidate:
                self.state["consecutive_unlocked_tick_count"] = 0
                self.state["unlock_confirmed_epoch"] = 0.0
            elif locked:
                self.state["consecutive_unlocked_tick_count"] = 0
                self.state["unlock_confirmed_epoch"] = 0.0
                self.state["live_promotion_eligible_emitted"] = False
            else:
                self.state["consecutive_unlocked_tick_count"] = (
                    _safe_int(self.state.get("consecutive_unlocked_tick_count")) + 1
                )
            near_candidate = self.active.cohort == "near_limit_rebound"
            session_open = _safe_int(self.state.get("open_price"))
            session_low = _safe_int(self.state.get("low_price"))
            rebound_from_low_pct = _pct(current, session_low)
            rebound_tick = bool(
                near_candidate
                and current >= session_open > 0
                and current > session_low > 0
                and rebound_from_low_pct is not None
                and rebound_from_low_pct >= NEAR_LIMIT_LIVE_MIN_REBOUND_FROM_LOW_PCT
            )
            if rebound_tick:
                self.state["consecutive_rebound_tick_count"] = (
                    _safe_int(self.state.get("consecutive_rebound_tick_count")) + 1
                )
            else:
                self.state["consecutive_rebound_tick_count"] = 0
                if near_candidate:
                    self.state["rebound_confirmed_epoch"] = 0.0
                    self.state["live_promotion_eligible_emitted"] = False
            self.state["rebound_from_low_pct"] = rebound_from_low_pct
            if not exact_candidate and previous_phase == "WAITING_FIRST_TRADE":
                new_phase = "NEAR_REBOUND_OBSERVING"
            elif previous_phase == "WAITING_FIRST_TICK":
                new_phase = "LIMIT_LOCKED" if locked else "UNLOCKED"
                if not locked:
                    self.state["unlock_count"] = 1
            elif locked and previous_phase in {"UNLOCKED", "UNLOCKED_AGAIN"}:
                new_phase = "RELOCKED"
                self.state["relock_count"] = (
                    _safe_int(self.state.get("relock_count")) + 1
                )
            elif not locked and previous_phase in {"LIMIT_LOCKED", "RELOCKED"}:
                new_phase = (
                    "UNLOCKED_AGAIN"
                    if _safe_int(self.state.get("unlock_count")) > 0
                    else "UNLOCKED"
                )
                self.state["unlock_count"] = (
                    _safe_int(self.state.get("unlock_count")) + 1
                )
            else:
                new_phase = previous_phase

            if new_phase != previous_phase:
                self.state["phase"] = new_phase
                self.state["last_transition_epoch"] = received_epoch
                self.state["transition_count"] = (
                    _safe_int(self.state.get("transition_count")) + 1
                )
                if new_phase in {"UNLOCKED", "UNLOCKED_AGAIN"}:
                    self.state["first_unlock_epoch"] = (
                        self.state.get("first_unlock_epoch") or received_epoch
                    )
                if new_phase == "RELOCKED":
                    self.state["first_relock_epoch"] = (
                        self.state.get("first_relock_epoch") or received_epoch
                    )
                self._emit(
                    "limit_down_watch_state_transition",
                    previous_phase=previous_phase,
                    phase=new_phase,
                    current_price=current,
                    lower_limit_price=lower_limit,
                    unlock_count=self.state.get("unlock_count"),
                    relock_count=self.state.get("relock_count"),
                    tick_count=self.state.get("tick_count"),
                )

            if (
                near_candidate
                and rebound_tick
                and _safe_int(self.state.get("consecutive_rebound_tick_count")) >= 2
                and _safe_float(self.state.get("rebound_confirmed_epoch")) <= 0.0
            ):
                self.state["rebound_confirmed_epoch"] = received_epoch
                self._emit(
                    "limit_down_watch_rebound_confirmed",
                    phase=self.state.get("phase"),
                    cohort=self.active.cohort,
                    price_band=self.active.price_band,
                    current_price=current,
                    open_price=session_open,
                    low_price=session_low,
                    rebound_from_low_pct=rebound_from_low_pct,
                    min_rebound_from_low_pct=NEAR_LIMIT_LIVE_MIN_REBOUND_FROM_LOW_PCT,
                    best_ask=best_ask,
                    best_bid=best_bid,
                    confirmation_tick_count=self.state.get(
                        "consecutive_rebound_tick_count"
                    ),
                    tick_count=self.state.get("tick_count"),
                )
                if (
                    f"{self.active.cohort}|{self.active.price_band}"
                    in self.active_live_policy_keys
                    and not self.state.get("live_promotion_eligible_emitted")
                ):
                    self.state["live_promotion_eligible_emitted"] = True
                    self._emit(
                        "limit_down_live_auto_eligibility_observed",
                        policy_key=f"{self.active.cohort}|{self.active.price_band}",
                        policy_source_date=self.live_policy_source_date,
                        trigger_type="near_rebound",
                        current_price=current,
                        open_price=session_open,
                        low_price=session_low,
                        rebound_from_low_pct=rebound_from_low_pct,
                        best_ask=best_ask,
                        best_bid=best_bid,
                        normal_scalping_guards_required=True,
                        direct_order_submitted=False,
                    )
            if (
                exact_candidate
                and not locked
                and _safe_int(self.state.get("consecutive_unlocked_tick_count")) >= 2
                and float(self.state.get("unlock_confirmed_epoch") or 0.0) <= 0.0
            ):
                self.state["unlock_confirmed_epoch"] = received_epoch
                self._emit(
                    "limit_down_watch_unlock_confirmed",
                    phase=self.state.get("phase"),
                    cohort=self.active.cohort,
                    price_band=self.active.price_band,
                    current_price=current,
                    lower_limit_price=lower_limit,
                    best_ask=best_ask,
                    best_bid=best_bid,
                    spread=(
                        max(0, best_ask - best_bid)
                        if best_ask > 0 and best_bid > 0
                        else None
                    ),
                    confirmation_tick_count=self.state.get(
                        "consecutive_unlocked_tick_count"
                    ),
                    tick_count=self.state.get("tick_count"),
                )
                if (
                    f"{self.active.cohort}|{self.active.price_band}"
                    in self.active_live_policy_keys
                    and not self.state.get("live_promotion_eligible_emitted")
                ):
                    self.state["live_promotion_eligible_emitted"] = True
                    self._emit(
                        "limit_down_live_auto_eligibility_observed",
                        policy_key=f"{self.active.cohort}|{self.active.price_band}",
                        policy_source_date=self.live_policy_source_date,
                        current_price=current,
                        lower_limit_price=lower_limit,
                        best_ask=best_ask,
                        best_bid=best_bid,
                        normal_scalping_guards_required=True,
                        direct_order_submitted=False,
                    )

            reference = self.active.limit_down_close
            open_value = _safe_int(self.state.get("open_price"))
            high_value = _safe_int(self.state.get("high_price"))
            low_value = _safe_int(self.state.get("low_price"))
            vi_observation_available = bool(
                self.state.get("vi_observation_available") or "vi_triggered" in data
            )
            actual_ws_item = str(
                data.get("last_ws_item") or self.state.get("actual_ws_item") or ""
            )
            actual_ws_route = str(
                data.get("last_ws_market_route")
                or self.state.get("actual_ws_route")
                or "unknown"
            )
            self.state.update(
                {
                    "high_vs_limit_down_close_pct": _pct(high_value, reference),
                    "low_vs_limit_down_close_pct": _pct(low_value, reference),
                    "open_to_high_pct": _pct(high_value, open_value),
                    "open_to_low_pct": _pct(low_value, open_value),
                    "low_to_high_range_pct": _pct(high_value, low_value),
                    "volume": max(
                        _safe_int(self.state.get("volume")),
                        _safe_int(data.get("volume") or data.get("acc_volume")),
                    ),
                    "trade_value": max(
                        _safe_int(self.state.get("trade_value")),
                        _safe_int(
                            data.get("trade_value")
                            or data.get("acc_trade_value")
                            or data.get("cum_trade_value")
                        ),
                    ),
                    "best_ask": best_ask,
                    "best_bid": best_bid,
                    "spread": (
                        max(0, best_ask - best_bid)
                        if best_ask > 0 and best_bid > 0
                        else None
                    ),
                    "vi_observation_available": vi_observation_available,
                    "vi_triggered": (
                        _truthy(data.get("vi_triggered"))
                        if "vi_triggered" in data
                        else self.state.get("vi_triggered")
                    ),
                    "actual_ws_item": actual_ws_item,
                    "actual_ws_route": actual_ws_route,
                    "actual_ws_item_count": 1 if actual_ws_item else 0,
                }
            )
            activity = self.activity.setdefault(code, {})
            activity.update(
                {
                    "tick_count": _safe_int(activity.get("tick_count")) + 1,
                    "trade_tick_count": _safe_int(activity.get("trade_tick_count")) + 1,
                    "unlock_count": _safe_int(self.state.get("unlock_count")),
                    "trade_value": max(
                        _safe_int(activity.get("trade_value")),
                        _safe_int(self.state.get("trade_value")),
                    ),
                    "last_tick_epoch": received_epoch,
                }
            )
            if received_epoch - self.last_snapshot_epoch >= 5.0:
                self.last_snapshot_epoch = received_epoch
                self._emit(
                    "limit_down_watch_snapshot",
                    phase=self.state.get("phase"),
                    cohort=self.active.cohort,
                    price_band=self.active.price_band,
                    market_data_type="0B",
                    quote_count=self.state.get("quote_count"),
                    trade_tick_count=self.state.get("trade_tick_count"),
                    high_vs_limit_down_close_pct=self.state.get(
                        "high_vs_limit_down_close_pct"
                    ),
                    low_vs_limit_down_close_pct=self.state.get(
                        "low_vs_limit_down_close_pct"
                    ),
                    open_to_high_pct=self.state.get("open_to_high_pct"),
                    open_to_low_pct=self.state.get("open_to_low_pct"),
                    low_to_high_range_pct=self.state.get("low_to_high_range_pct"),
                    unlock_count=self.state.get("unlock_count"),
                    relock_count=self.state.get("relock_count"),
                    first_unlock_epoch=self.state.get("first_unlock_epoch"),
                    first_relock_epoch=self.state.get("first_relock_epoch"),
                    consecutive_unlocked_tick_count=self.state.get(
                        "consecutive_unlocked_tick_count"
                    ),
                    unlock_confirmed_epoch=self.state.get("unlock_confirmed_epoch"),
                    consecutive_rebound_tick_count=self.state.get(
                        "consecutive_rebound_tick_count"
                    ),
                    rebound_confirmed_epoch=self.state.get("rebound_confirmed_epoch"),
                    rebound_from_low_pct=self.state.get("rebound_from_low_pct"),
                    first_tick_epoch=self.state.get("first_tick_epoch"),
                    last_tick_epoch=self.state.get("last_tick_epoch"),
                    first_quote_epoch=self.state.get("first_quote_epoch"),
                    last_quote_epoch=self.state.get("last_quote_epoch"),
                    open_price=self.state.get("open_price"),
                    high_price=self.state.get("high_price"),
                    low_price=self.state.get("low_price"),
                    current_price=self.state.get("current_price"),
                    volume=self.state.get("volume"),
                    trade_value=self.state.get("trade_value"),
                    best_ask=self.state.get("best_ask"),
                    best_bid=self.state.get("best_bid"),
                    spread=self.state.get("spread"),
                    vi_triggered=self.state.get("vi_triggered"),
                    vi_observation_available=self.state.get("vi_observation_available"),
                    actual_ws_item=self.state.get("actual_ws_item"),
                    actual_ws_route=self.state.get("actual_ws_route"),
                    actual_ws_item_count=self.state.get("actual_ws_item_count"),
                )
                self._write_state()
