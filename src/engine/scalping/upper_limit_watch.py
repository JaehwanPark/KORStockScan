"""Previous-limit-up rotating observer and bounded normal-scanner handoff.

The lane owns one conditional slot inside the existing rising budget.  It never
submits an order.  A validated prior-date policy may only create a normal
scalping scanner candidate after ordered two-tick trigger and fresh BBO checks.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime
import json
import os
from pathlib import Path
import threading
import time
from typing import Any, Callable

import pandas as pd
from sqlalchemy import text

from src.engine.scalping.limit_down_watch import (
    _atomic_write_json,
    _canonical_hash,
    _krx_session_phase,
    _pct,
    _safe_float,
    _safe_int,
    _safe_price,
    _top_of_book,
    price_band,
)
from src.utils import kiwoom_utils
from src.utils.pipeline_event_logger import emit_pipeline_event

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
CANDIDATE_DIR = DATA_DIR / "report" / "upper_limit_watch_candidate_source"
RUNTIME_DIR = DATA_DIR / "runtime"
LIVE_POLICY_DIR = DATA_DIR / "threshold_cycle" / "bounded_live_candidates"

UPPER_LIMIT_LIVE_RECLAIM_SOURCE = "UPPER_LIMIT_LIVE_RECLAIM"
UPPER_LIMIT_LIVE_POLICY_VERSION = "upper_limit_ordered_reclaim_live_auto_v1"
METRIC_ROLE = "diagnostic"
DECISION_AUTHORITY = "upper_limit_source_observation_only"
WINDOW_POLICY = "same_symbol_same_krx_session_ordered_0b_trade_and_0d_quote"
SAMPLE_FLOOR = "not_applicable_source_observation"
PRIMARY_DECISION_METRIC = "ordered_gap_pullback_reclaim_breakout_path_capture_rate"
SOURCE_QUALITY_GATE = "official_ka10017_previous_limit_up_and_ka10081_db_ohlc_match"
FORBIDDEN_USES = (
    "direct_real_order,buy_analysis_from_observer,threshold_change,provider_route_change,"
    "order_price_or_quantity_change,cap_change,broker_guard_change,bot_restart_authority"
)


def _truthy(value: Any) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def feature_enabled() -> bool:
    return _truthy(os.getenv("KORSTOCKSCAN_UPPER_LIMIT_WATCH_ENABLED", "false"))


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
class UpperLimitCandidate:
    code: str
    name: str
    source_trade_date: str
    limit_up_close: int
    source_open: int
    source_high: int
    source_low: int
    consecutive_count: int
    cohort: str
    price_band: str
    volume: int
    source_api: str = "ka10017"
    source_quality: str = "pass"


def _candidate_priority(candidate: UpperLimitCandidate) -> tuple[int, int, int, str]:
    return (
        0 if candidate.consecutive_count >= 2 else 1,
        1 if candidate.cohort == "single_limit_up_one_price_locked" else 0,
        -candidate.volume,
        candidate.code,
    )


def _latest_completed_date(db: Any, target_date: date) -> date | None:
    query = text(
        "SELECT MAX(quote_date) FROM daily_stock_quotes WHERE quote_date < :target_date"
    )
    with db.get_session() as session:
        row = session.execute(query, {"target_date": target_date}).fetchone()
    value = row[0] if row else None
    return value.date() if isinstance(value, datetime) else value


def _completed_db_ohlc(
    db: Any, code: str, source_date: date
) -> tuple[int, int, int, int, str]:
    query = text("""
        SELECT open_price, high_price, low_price, close_price, stock_name
        FROM daily_stock_quotes
        WHERE stock_code = :code AND quote_date = :source_date
        LIMIT 1
        """)
    with db.get_session() as session:
        row = session.execute(
            query, {"code": code, "source_date": source_date}
        ).fetchone()
    if not row:
        return 0, 0, 0, 0, ""
    return (*(_safe_price(row[index]) for index in range(4)), str(row[4] or ""))


def build_candidate_source(
    token: str,
    db: Any,
    *,
    target_date: date | None = None,
    fetch_previous: (
        Callable[[str], tuple[list[dict[str, Any]], dict[str, Any]]] | None
    ) = None,
    fetch_daily: Callable[[str, str], Any] | None = None,
    latest_date_loader: Callable[[Any, date], date | None] | None = None,
    db_ohlc_loader: (
        Callable[[Any, str, date], tuple[int, int, int, int, str]] | None
    ) = None,
) -> tuple[list[UpperLimitCandidate], dict[str, Any]]:
    """Build a fail-closed official previous-limit-up candidate artifact."""

    target_date = target_date or datetime.now().date()
    fetch_previous = fetch_previous or kiwoom_utils.get_previous_limit_up_stocks_ka10017
    fetch_daily = fetch_daily or kiwoom_utils.get_daily_ohlcv_ka10081_df
    latest_date_loader = latest_date_loader or _latest_completed_date
    db_ohlc_loader = db_ohlc_loader or _completed_db_ohlc
    raw_rows, source_meta = fetch_previous(token)
    expected_date = latest_date_loader(db, target_date)
    candidates: list[UpperLimitCandidate] = []
    blocked: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    seen: dict[str, str] = {}

    for raw in raw_rows or []:
        code = kiwoom_utils.normalize_stock_code((raw or {}).get("Code"))
        name = str((raw or {}).get("Name") or "").strip()
        raw_count = str((raw or {}).get("ConsecutiveCountRaw") or "").strip()
        if not code or not code.isdigit() or len(code) != 6:
            blocked.append({"code": code or "-", "reason": "invalid_stock_code"})
            continue
        if not raw_count.isdigit() or int(raw_count) <= 0:
            blocked.append({"code": code, "reason": "invalid_consecutive_count"})
            continue
        if code in seen:
            target = excluded if seen[code] == raw_count else blocked
            target.append(
                {
                    "code": code,
                    "reason": (
                        "duplicate_source_row"
                        if target is excluded
                        else "duplicate_consecutive_count_conflict"
                    ),
                }
            )
            continue
        seen[code] = raw_count
        if not kiwoom_utils.is_valid_stock(code, name, token=None):
            excluded.append({"code": code, "reason": "excluded_existing_stock_filter"})
            continue
        daily = fetch_daily(token, code)
        if daily is None or getattr(daily, "empty", True):
            blocked.append({"code": code, "reason": "ka10081_missing"})
            continue
        try:
            parsed = pd.to_datetime(daily.index, errors="coerce")
            valid = parsed.notna()
            normalized = daily.loc[valid].copy()
            normalized.index = parsed[valid]
        except (AttributeError, TypeError, ValueError):
            blocked.append({"code": code, "reason": "ka10081_invalid_date_index"})
            continue
        eligible = normalized[normalized.index.date < target_date]
        if eligible.empty:
            blocked.append({"code": code, "reason": "completed_daily_row_missing"})
            continue
        source_index = eligible.index.max()
        source_date = source_index.date()
        if expected_date is None or source_date != expected_date:
            blocked.append(
                {
                    "code": code,
                    "reason": "completed_daily_date_stale_or_mismatch",
                    "source_trade_date": source_date.isoformat(),
                }
            )
            continue
        source_row = eligible.loc[source_index]
        official_ohlc = tuple(
            _safe_price(source_row.get(field))
            for field in ("Open", "High", "Low", "Close")
        )
        db_open, db_high, db_low, db_close, db_name = db_ohlc_loader(
            db, code, source_date
        )
        db_ohlc = (db_open, db_high, db_low, db_close)
        if any(value <= 0 for value in official_ohlc) or official_ohlc != db_ohlc:
            blocked.append(
                {
                    "code": code,
                    "reason": "ka10081_db_ohlc_mismatch",
                    "source_trade_date": source_date.isoformat(),
                }
            )
            continue
        source_open, source_high, source_low, source_close = official_ohlc
        if source_close != source_high:
            blocked.append({"code": code, "reason": "source_close_not_daily_high"})
            continue
        count = int(raw_count)
        if count >= 2:
            cohort = "consecutive_limit_up_2plus"
        elif source_open == source_high == source_low == source_close:
            cohort = "single_limit_up_one_price_locked"
        else:
            cohort = "single_limit_up_intraday_traded_close_locked"
        candidates.append(
            UpperLimitCandidate(
                code=code,
                name=name or db_name or code,
                source_trade_date=source_date.isoformat(),
                limit_up_close=source_close,
                source_open=source_open,
                source_high=source_high,
                source_low=source_low,
                consecutive_count=count,
                cohort=cohort,
                price_band=price_band(source_close),
                volume=_safe_int((raw or {}).get("Volume")),
            )
        )

    candidates.sort(key=_candidate_priority)
    artifact = {
        "schema_version": 1,
        "report_type": "upper_limit_watch_candidate_source",
        "target_date": target_date.isoformat(),
        "expected_source_trade_date": (
            expected_date.isoformat() if expected_date else None
        ),
        "generated_at": datetime.now().isoformat(),
        "status": (
            "blocked"
            if blocked and not candidates
            else "partial" if blocked else "pass"
        ),
        "candidate_source_mode": "official_previous_limit_up",
        "source_meta": source_meta,
        "request_response_hash": _canonical_hash(
            {"rows": raw_rows, "source_meta": source_meta}
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
        / f"upper_limit_watch_candidate_source_{target_date.isoformat()}.json",
        artifact,
    )
    return candidates, artifact


class UpperLimitObservationRegistry:
    """Thread-safe one-code raw market-data sink and signal isolation registry."""

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

    def active_code(self) -> str:
        with self._lock:
            return self._code

    def is_observation_only(self, code: str) -> bool:
        normalized = kiwoom_utils.normalize_stock_code(code)
        with self._lock:
            return bool(normalized and normalized == self._code)

    def observe_raw_market_data(
        self,
        code: str,
        data: dict[str, Any],
        received_epoch: float | None = None,
        *,
        realtime_type: str = "0B",
    ) -> None:
        normalized = kiwoom_utils.normalize_stock_code(code)
        with self._lock:
            sink = self._sink if normalized and normalized == self._code else None
        if sink is None:
            return
        payload = dict(data or {})
        payload["_upper_limit_realtime_type"] = str(realtime_type or "").strip()
        sink(normalized, payload, received_epoch or time.time())


UPPER_LIMIT_OBSERVATION_REGISTRY = UpperLimitObservationRegistry()


class UpperLimitWatchManager:
    """Own one rising-budget observation symbol without creating a trade row."""

    def __init__(self, token: str, db: Any, event_bus: Any) -> None:
        self.token = token
        self.db = db
        self.event_bus = event_bus
        self.candidates: list[UpperLimitCandidate] = []
        self.active: UpperLimitCandidate | None = None
        self.state: dict[str, Any] = {}
        self.activity: dict[str, dict[str, Any]] = {}
        self.last_visit: dict[str, float] = {}
        self.loaded_date = ""
        self.next_retry_epoch = 0.0
        self.last_snapshot_epoch = 0.0
        self.last_quote_snapshot_epoch = 0.0
        self.live_policy_by_key: dict[str, dict[str, Any]] = {}
        self.live_policy_source_date = ""
        self.live_policy_max_entry_spread_pct = 0.0
        self.last_release: dict[str, Any] | None = None
        self._lock = threading.RLock()

    @property
    def state_path(self) -> Path:
        return RUNTIME_DIR / f"upper_limit_watch_state_{datetime.now().date()}.json"

    def active_slot_count(self) -> int:
        return 1 if feature_enabled() and self.active is not None else 0

    def _emit(self, stage: str, **fields: Any) -> None:
        candidate = self.active
        emit_pipeline_event(
            "UPPER_LIMIT_WATCH",
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
            "budget_owner": "rising_missed_conditional_reservation",
            "global_watch_budget_expansion": False,
            "active_candidate": asdict(self.active) if self.active else None,
            "pool_hash": _canonical_hash([asdict(item) for item in self.candidates]),
            "state": self.state,
            "candidate_activity": self.activity,
            "active_live_policy_keys": sorted(self.live_policy_by_key),
            "live_policy_source_date": self.live_policy_source_date,
            "live_policy_version": UPPER_LIMIT_LIVE_POLICY_VERSION,
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
                "upper_limit_watch_source_blocked",
                reason=f"candidate_source_exception:{type(exc).__name__}",
            )
            return
        if artifact.get("status") == "blocked":
            self.candidates = []
            self.next_retry_epoch = now_epoch + 300.0
            self._emit(
                "upper_limit_watch_source_blocked",
                reason="candidate_source_quality_blocked",
                source_hash=artifact.get("request_response_hash"),
            )
            return
        self.loaded_date = today.isoformat()
        self.next_retry_epoch = 0.0
        self._load_live_policy(today)
        self._emit(
            "upper_limit_watch_source_loaded",
            candidate_count=len(self.candidates),
            source_status=artifact.get("status"),
            source_hash=artifact.get("request_response_hash"),
            active_live_policy_count=len(self.live_policy_by_key),
            live_policy_source_date=self.live_policy_source_date,
        )

    def _load_live_policy(self, target_date: date) -> None:
        dated: list[tuple[date, Path]] = []
        for path in LIVE_POLICY_DIR.glob(
            "upper_limit_watch_bounded_live_candidate_*.json"
        ):
            try:
                policy_date = date.fromisoformat(
                    path.stem.removeprefix("upper_limit_watch_bounded_live_candidate_")
                )
            except ValueError:
                continue
            if policy_date < target_date:
                dated.append((policy_date, path))
        self.live_policy_by_key = {}
        self.live_policy_source_date = ""
        self.live_policy_max_entry_spread_pct = 0.0
        if not dated:
            return
        policy_date, path = max(dated)
        expected_source_dates = {
            candidate.source_trade_date for candidate in self.candidates
        }
        if expected_source_dates != {policy_date.isoformat()}:
            return
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        policies = payload.get("candidates") if isinstance(payload, dict) else []
        risk = payload.get("risk_contract") if isinstance(payload, dict) else {}
        policies = policies if isinstance(policies, list) else []
        risk = risk if isinstance(risk, dict) else {}
        valid = bool(
            payload.get("schema_version") == 1
            and payload.get("report_type") == "upper_limit_watch_bounded_live_candidate"
            and payload.get("target_date") == policy_date.isoformat()
            and payload.get("status") == "live_auto_apply_ready"
            and payload.get("decision_authority")
            == "upper_limit_live_auto_eligibility_candidate"
            and payload.get("operator_approval_required") is False
            and payload.get("activation_mode")
            == "latest_valid_prior_date_policy_auto_loaded"
            and payload.get("allowed_runtime_apply") is True
            and payload.get("runtime_effect") is False
            and payload.get("actual_order_submitted") is False
            and payload.get("broker_order_forbidden") is True
            and payload.get("ready_candidate_count") == len(policies)
            and risk.get("max_concurrent_positions") == 1
            and risk.get("max_daily_entries") == 1
            and risk.get("scale_in_allowed") is False
            and risk.get("same_day_reentry_allowed") is False
            and risk.get("overnight_allowed") is False
            and risk.get("normal_scalping_ai_and_submit_guards_required") is True
            and risk.get("upper_limit_entry_proximity_guard_required") is True
            and 0.0 < _safe_float(risk.get("max_entry_spread_pct")) <= 1.5
        )
        if not valid:
            return
        by_key = {
            str(row.get("policy_key")): dict(row)
            for row in policies
            if isinstance(row, dict)
            and str(row.get("policy_key") or "")
            == f"{row.get('cohort')}|{row.get('price_band')}|{row.get('trigger_type')}"
            and _safe_int(row.get("sample_count")) >= 1
            and _safe_float(row.get("source_quality_adjusted_ev_pct")) > 0.0
            and _safe_float(row.get("downside_p10_pct"), -999.0) > 0.0
            and _safe_float(row.get("mae_p10_pct"), -999.0) >= -5.0
            and _safe_float(row.get("entry_bbo_coverage_pct")) >= 100.0
        }
        if not by_key or len(by_key) != len(policies):
            return
        self.live_policy_by_key = by_key
        self.live_policy_source_date = policy_date.isoformat()
        self.live_policy_max_entry_spread_pct = _safe_float(
            risk.get("max_entry_spread_pct")
        )

    def _pick(
        self, active_codes: set[str], now_epoch: float
    ) -> UpperLimitCandidate | None:
        available = [
            candidate
            for candidate in self.candidates
            if candidate.code not in active_codes
            and now_epoch - self.last_visit.get(candidate.code, 0.0) >= 300.0
        ]
        if not available:
            return None

        def has_live_policy(candidate: UpperLimitCandidate) -> bool:
            prefix = f"{candidate.cohort}|{candidate.price_band}|"
            return any(key.startswith(prefix) for key in self.live_policy_by_key)

        return min(
            available,
            key=lambda candidate: (
                0 if has_live_policy(candidate) else 1,
                (
                    0
                    if _safe_int(
                        self.activity.get(candidate.code, {}).get("visit_count")
                    )
                    <= 0
                    else 1
                ),
                _safe_int(self.activity.get(candidate.code, {}).get("visit_count")),
                *_candidate_priority(candidate),
            ),
        )

    def prepare_candidates(self, *, now_epoch: float | None = None) -> None:
        """Load the daily pool without issuing REG, so capacity can be reclaimed first."""

        now_epoch = time.time() if now_epoch is None else float(now_epoch)
        with self._lock:
            if feature_enabled() and _krx_session_phase(now_epoch) == "OPEN":
                self._load_candidates(now_epoch)

    def has_available_candidate(
        self, *, active_codes: set[str] | None = None, now_epoch: float | None = None
    ) -> bool:
        now_epoch = time.time() if now_epoch is None else float(now_epoch)
        normalized = {
            kiwoom_utils.normalize_stock_code(code) for code in (active_codes or set())
        }
        with self._lock:
            if not feature_enabled():
                return False
            return (
                self.active is not None or self._pick(normalized, now_epoch) is not None
            )

    def _activate(self, candidate: UpperLimitCandidate, now_epoch: float) -> None:
        info = kiwoom_utils.get_basic_info_ka10001(self.token, candidate.code) or {}
        current_upper = _safe_price(info.get("UpperLimitPrice"))
        if current_upper <= 0:
            self.last_visit[candidate.code] = now_epoch
            self.next_retry_epoch = now_epoch + 300.0
            self._emit(
                "upper_limit_watch_source_blocked",
                reason="current_upper_limit_price_missing",
                candidate_code=candidate.code,
            )
            return
        self.active = candidate
        activity = self.activity.setdefault(candidate.code, {})
        activity["visit_count"] = _safe_int(activity.get("visit_count")) + 1
        self.last_snapshot_epoch = 0.0
        self.last_quote_snapshot_epoch = 0.0
        self.state = {
            "phase": "WAITING_FIRST_TICK",
            "registered_epoch": now_epoch,
            "last_transition_epoch": now_epoch,
            "prior_limit_up_close": candidate.limit_up_close,
            "current_upper_limit_price": current_upper,
            "open_price": 0,
            "high_price": 0,
            "low_price": 0,
            "current_price": 0,
            "first_tick_epoch": 0.0,
            "last_tick_epoch": 0.0,
            "first_quote_epoch": 0.0,
            "last_quote_epoch": 0.0,
            "tick_count": 0,
            "quote_count": 0,
            "transition_count": 0,
            "prior_close_broken_observed": False,
            "current_limit_lock_count": 0,
            "current_limit_unlock_count": 0,
            "consecutive_reclaim_tick_count": 0,
            "consecutive_gap_hold_tick_count": 0,
            "trigger_confirmed_epoch": 0.0,
            "trigger_type": "",
            "required_realtime_types": ["0B", "0D"],
            "last_reg_request_epoch": 0.0,
            "reg_request_count": 0,
        }
        UPPER_LIMIT_OBSERVATION_REGISTRY.activate(
            candidate.code, self.on_raw_market_data
        )
        self._request_registration(now_epoch, reason="initial")
        self._emit(
            "upper_limit_watch_registered",
            cohort=candidate.cohort,
            price_band=candidate.price_band,
            consecutive_count=candidate.consecutive_count,
            prior_limit_up_close=candidate.limit_up_close,
            current_upper_limit_price=current_upper,
            validated_live_type_priority=any(
                key.startswith(f"{candidate.cohort}|{candidate.price_band}|")
                for key in self.live_policy_by_key
            ),
        )
        self._write_state()

    def _request_registration(self, now_epoch: float, *, reason: str) -> None:
        if self.active is None:
            return
        self.event_bus.publish(
            "COMMAND_WS_REG",
            {
                "codes": [self.active.code],
                "source": "upper_limit_watch_observation",
                "reason": reason,
                "required_realtime_types": ("0B", "0D"),
            },
        )
        self.state["last_reg_request_epoch"] = now_epoch
        self.state["reg_request_count"] = (
            _safe_int(self.state.get("reg_request_count")) + 1
        )
        self._emit(
            "upper_limit_watch_reg_requested",
            reason=reason,
            reg_request_count=self.state["reg_request_count"],
        )

    def release(self, *, reason: str, keep_ws: bool = False) -> None:
        with self._lock:
            candidate = self.active
            if candidate is None:
                return
            released = time.time()
            previous_phase = str(self.state.get("phase") or "WAITING_FIRST_TICK")
            terminal = (
                "SESSION_ENDED"
                if reason in {"session_ended", "feature_disabled"}
                else "ROTATED"
            )
            self.state["phase"] = terminal
            self._emit(
                "upper_limit_watch_state_transition",
                previous_phase=previous_phase,
                phase=terminal,
                reason=reason,
            )
            UPPER_LIMIT_OBSERVATION_REGISTRY.release(candidate.code)
            if not keep_ws:
                self.event_bus.publish(
                    "COMMAND_WS_UNREG",
                    {
                        "codes": [candidate.code],
                        "source": "upper_limit_watch_observation",
                        "reason": reason,
                    },
                )
            self.last_visit[candidate.code] = released
            self._emit("upper_limit_watch_released", reason=reason, keep_ws=keep_ws)
            self.last_release = {
                "candidate": asdict(candidate),
                "released_epoch": released,
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

    def reconcile(
        self,
        *,
        active_codes: set[str] | None = None,
        now_epoch: float | None = None,
        allow_activation: bool = True,
    ) -> None:
        now_epoch = time.time() if now_epoch is None else float(now_epoch)
        active_codes = {
            kiwoom_utils.normalize_stock_code(code) for code in (active_codes or set())
        }
        with self._lock:
            if not feature_enabled():
                self.release(reason="feature_disabled")
                self._write_state()
                return
            self._load_candidates(now_epoch)
            phase = _krx_session_phase(now_epoch)
            if phase != "OPEN":
                if self.active is not None:
                    self.release(
                        reason="session_ended" if phase == "ENDED" else "preopen_wait"
                    )
                self._write_state()
                return
            if self.active and self.active.code in active_codes:
                self.release(reason="active_trade_target_conflict", keep_ws=True)
            if self.active:
                registered = _safe_float(self.state.get("registered_epoch"), now_epoch)
                last_transition = _safe_float(
                    self.state.get("last_transition_epoch"), registered
                )
                trigger_confirmed = _safe_float(
                    self.state.get("trigger_confirmed_epoch")
                )
                dwell = now_epoch - registered
                unchanged = now_epoch - last_transition
                label_capture_pending = bool(
                    trigger_confirmed > 0.0 and now_epoch - trigger_confirmed < 245.0
                )
                if (
                    len(self.candidates) > 1
                    and not label_capture_pending
                    and (
                        trigger_confirmed > 0.0
                        or dwell >= 600.0
                        or (dwell >= 180.0 and unchanged >= 180.0)
                    )
                ):
                    self.release(reason="rotation_due")
                elif (
                    self.active is not None
                    and _safe_float(self.state.get("first_tick_epoch")) <= 0.0
                    and now_epoch
                    - _safe_float(self.state.get("last_reg_request_epoch"), registered)
                    >= 15.0
                ):
                    self._request_registration(now_epoch, reason="first_tick_pending")
            if self.active is None and allow_activation:
                candidate = self._pick(active_codes, now_epoch)
                if candidate is not None:
                    self._activate(candidate, now_epoch)
            self._write_state()

    def _on_quote(self, data: dict[str, Any], received_epoch: float) -> None:
        if received_epoch <= _safe_float(self.state.get("last_quote_epoch")):
            return
        best_ask, best_bid = _top_of_book(data)
        if best_ask <= 0 and best_bid <= 0:
            return
        self.state["first_quote_epoch"] = (
            self.state.get("first_quote_epoch") or received_epoch
        )
        self.state["last_quote_epoch"] = received_epoch
        self.state["quote_count"] = _safe_int(self.state.get("quote_count")) + 1
        self.state["best_ask"] = best_ask
        self.state["best_bid"] = best_bid
        self.state["spread"] = (
            max(0, best_ask - best_bid) if best_ask > 0 and best_bid > 0 else None
        )
        self.state["actual_ws_item"] = str(data.get("last_ws_item") or "")
        self.state["actual_ws_route"] = str(
            data.get("last_ws_market_route") or "unknown"
        )
        if received_epoch - self.last_quote_snapshot_epoch >= 5.0:
            self.last_quote_snapshot_epoch = received_epoch
            self._emit(
                "upper_limit_watch_quote_snapshot",
                phase=self.state.get("phase"),
                best_ask=best_ask,
                best_bid=best_bid,
                spread=self.state.get("spread"),
                quote_count=self.state.get("quote_count"),
                current_price=self.state.get("current_price"),
                last_quote_epoch=received_epoch,
                quote_age_sec=0.0,
                snapshot_source="raw_0d_callback_event_time",
                actual_ws_item=self.state.get("actual_ws_item"),
                actual_ws_route=self.state.get("actual_ws_route"),
            )

    def on_raw_market_data(
        self, code: str, data: dict[str, Any], received_epoch: float
    ) -> None:
        with self._lock:
            if self.active is None or code != self.active.code:
                return
            if str(data.get("_upper_limit_realtime_type") or "0B") == "0D":
                self._on_quote(data, received_epoch)
                return
            if received_epoch <= _safe_float(self.state.get("last_tick_epoch")):
                return
            current = _safe_price(
                data.get("curr") or data.get("current_price") or data.get("cur_prc")
            )
            if current <= 0:
                return
            open_price = _safe_price(data.get("open") or data.get("open_price"))
            high_price = _safe_price(data.get("high") or data.get("high_price"))
            low_price = _safe_price(data.get("low") or data.get("low_price"))
            best_ask, best_bid = _top_of_book(data)
            self.state["first_tick_epoch"] = (
                self.state.get("first_tick_epoch") or received_epoch
            )
            self.state["last_tick_epoch"] = received_epoch
            self.state["tick_count"] = _safe_int(self.state.get("tick_count")) + 1
            self.state["current_price"] = current
            if open_price > 0:
                self.state["open_price"] = self.state.get("open_price") or open_price
            self.state["high_price"] = max(
                _safe_int(self.state.get("high_price")), high_price, current
            )
            lows = [
                value
                for value in (
                    _safe_int(self.state.get("low_price")),
                    low_price,
                    current,
                )
                if value > 0
            ]
            self.state["low_price"] = min(lows) if lows else 0
            if best_ask > 0 or best_bid > 0:
                self.state["best_ask"] = best_ask
                self.state["best_bid"] = best_bid
                self.state["spread"] = (
                    max(0, best_ask - best_bid)
                    if best_ask > 0 and best_bid > 0
                    else None
                )

            source_close = _safe_int(self.state.get("prior_limit_up_close"))
            current_upper = _safe_int(self.state.get("current_upper_limit_price"))
            previous_phase = str(self.state.get("phase") or "WAITING_FIRST_TICK")
            locked = current >= current_upper > 0
            below_source = current < source_close
            if locked:
                new_phase = "CURRENT_LIMIT_LOCKED"
                if previous_phase != new_phase:
                    self.state["current_limit_lock_count"] = (
                        _safe_int(self.state.get("current_limit_lock_count")) + 1
                    )
                self.state["consecutive_reclaim_tick_count"] = 0
                self.state["consecutive_gap_hold_tick_count"] = 0
                self.state["trigger_confirmed_epoch"] = 0.0
                self.state["trigger_type"] = ""
            elif previous_phase == "CURRENT_LIMIT_LOCKED":
                new_phase = "CURRENT_LIMIT_UNLOCKED"
                self.state["current_limit_unlock_count"] = (
                    _safe_int(self.state.get("current_limit_unlock_count")) + 1
                )
            elif below_source:
                new_phase = "BELOW_PRIOR_LIMIT_CLOSE"
                self.state["prior_close_broken_observed"] = True
                self.state["consecutive_reclaim_tick_count"] = 0
                self.state["consecutive_gap_hold_tick_count"] = 0
                self.state["trigger_confirmed_epoch"] = 0.0
                self.state["trigger_type"] = ""
            elif self.state.get("prior_close_broken_observed"):
                new_phase = "RECLAIMED_PRIOR_LIMIT_CLOSE"
                self.state["consecutive_reclaim_tick_count"] = (
                    _safe_int(self.state.get("consecutive_reclaim_tick_count")) + 1
                )
                self.state["consecutive_gap_hold_tick_count"] = 0
            else:
                new_phase = "ABOVE_PRIOR_LIMIT_CLOSE"
                if current >= max(
                    source_close, _safe_int(self.state.get("open_price"))
                ):
                    self.state["consecutive_gap_hold_tick_count"] = (
                        _safe_int(self.state.get("consecutive_gap_hold_tick_count")) + 1
                    )

            if new_phase != previous_phase:
                self.state["phase"] = new_phase
                self.state["last_transition_epoch"] = received_epoch
                self.state["transition_count"] = (
                    _safe_int(self.state.get("transition_count")) + 1
                )
                self._emit(
                    "upper_limit_watch_state_transition",
                    previous_phase=previous_phase,
                    phase=new_phase,
                    current_price=current,
                    prior_limit_up_close=source_close,
                    current_upper_limit_price=current_upper,
                )

            trigger_type = ""
            if (
                not locked
                and _safe_int(self.state.get("consecutive_reclaim_tick_count")) >= 2
            ):
                trigger_type = "pullback_reclaim"
            elif (
                not locked
                and _safe_int(self.state.get("consecutive_gap_hold_tick_count")) >= 2
            ):
                trigger_type = "gap_hold_breakout"
            if (
                trigger_type
                and _safe_float(self.state.get("trigger_confirmed_epoch")) <= 0.0
            ):
                self.state["trigger_confirmed_epoch"] = received_epoch
                self.state["trigger_type"] = trigger_type
                trigger_best_ask = _safe_int(self.state.get("best_ask"))
                trigger_best_bid = _safe_int(self.state.get("best_bid"))
                last_quote_epoch = _safe_float(self.state.get("last_quote_epoch"))
                self._emit(
                    "upper_limit_watch_trigger_confirmed",
                    trigger_type=trigger_type,
                    phase=self.state.get("phase"),
                    cohort=self.active.cohort,
                    price_band=self.active.price_band,
                    current_price=current,
                    prior_limit_up_close=source_close,
                    open_price=self.state.get("open_price"),
                    low_price=self.state.get("low_price"),
                    best_ask=trigger_best_ask,
                    best_bid=trigger_best_bid,
                    last_quote_epoch=last_quote_epoch,
                    quote_age_sec=(
                        round(received_epoch - last_quote_epoch, 6)
                        if 0.0 <= received_epoch - last_quote_epoch <= 3600.0
                        else None
                    ),
                    confirmation_tick_count=2,
                )

            self.state.update(
                {
                    "high_vs_prior_limit_close_pct": _pct(
                        _safe_int(self.state.get("high_price")), source_close
                    ),
                    "low_vs_prior_limit_close_pct": _pct(
                        _safe_int(self.state.get("low_price")), source_close
                    ),
                    "open_gap_pct": _pct(
                        _safe_int(self.state.get("open_price")), source_close
                    ),
                    "low_to_high_range_pct": _pct(
                        _safe_int(self.state.get("high_price")),
                        _safe_int(self.state.get("low_price")),
                    ),
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
                    "actual_ws_item": str(
                        data.get("last_ws_item")
                        or self.state.get("actual_ws_item")
                        or ""
                    ),
                    "actual_ws_route": str(
                        data.get("last_ws_market_route")
                        or self.state.get("actual_ws_route")
                        or "unknown"
                    ),
                }
            )
            activity = self.activity.setdefault(code, {})
            activity["tick_count"] = _safe_int(activity.get("tick_count")) + 1
            activity["last_tick_epoch"] = received_epoch
            activity["trade_value"] = max(
                _safe_int(activity.get("trade_value")),
                _safe_int(self.state.get("trade_value")),
            )
            if received_epoch - self.last_snapshot_epoch >= 5.0:
                self.last_snapshot_epoch = received_epoch
                self._emit(
                    "upper_limit_watch_snapshot",
                    phase=self.state.get("phase"),
                    cohort=self.active.cohort,
                    price_band=self.active.price_band,
                    trigger_type=self.state.get("trigger_type"),
                    trigger_confirmed_epoch=self.state.get("trigger_confirmed_epoch"),
                    open_gap_pct=self.state.get("open_gap_pct"),
                    high_vs_prior_limit_close_pct=self.state.get(
                        "high_vs_prior_limit_close_pct"
                    ),
                    low_vs_prior_limit_close_pct=self.state.get(
                        "low_vs_prior_limit_close_pct"
                    ),
                    low_to_high_range_pct=self.state.get("low_to_high_range_pct"),
                    current_limit_lock_count=self.state.get("current_limit_lock_count"),
                    current_limit_unlock_count=self.state.get(
                        "current_limit_unlock_count"
                    ),
                    first_tick_epoch=self.state.get("first_tick_epoch"),
                    last_tick_epoch=self.state.get("last_tick_epoch"),
                    open_price=self.state.get("open_price"),
                    high_price=self.state.get("high_price"),
                    low_price=self.state.get("low_price"),
                    current_price=current,
                    volume=self.state.get("volume"),
                    trade_value=self.state.get("trade_value"),
                    best_ask=self.state.get("best_ask"),
                    best_bid=self.state.get("best_bid"),
                    spread=self.state.get("spread"),
                    actual_ws_item=self.state.get("actual_ws_item"),
                    actual_ws_route=self.state.get("actual_ws_route"),
                )
                self._write_state()

    def live_promotion_target(
        self, *, now_epoch: float | None = None, daily_promotion_count: int = 0
    ) -> dict[str, Any] | None:
        """Return one bounded normal-scanner handoff; never submit directly."""

        now_epoch = time.time() if now_epoch is None else float(now_epoch)
        with self._lock:
            candidate = self.active
            if candidate is None or int(daily_promotion_count or 0) >= 1:
                return None
            trigger_type = str(self.state.get("trigger_type") or "")
            key = f"{candidate.cohort}|{candidate.price_band}|{trigger_type}"
            policy = self.live_policy_by_key.get(key)
            current = _safe_int(self.state.get("current_price"))
            source_close = _safe_int(self.state.get("prior_limit_up_close"))
            current_upper = _safe_int(self.state.get("current_upper_limit_price"))
            best_ask = _safe_int(self.state.get("best_ask"))
            best_bid = _safe_int(self.state.get("best_bid"))
            last_tick = _safe_float(self.state.get("last_tick_epoch"))
            last_quote = _safe_float(self.state.get("last_quote_epoch"))
            confirmed = _safe_float(self.state.get("trigger_confirmed_epoch"))
            if not (
                policy
                and trigger_type in {"pullback_reclaim", "gap_hold_breakout"}
                and confirmed > 0.0
                and 0.0 <= now_epoch - last_tick <= 5.0
                and 0.0 <= now_epoch - last_quote <= 5.0
                and source_close <= current < current_upper
                and best_ask >= current > 0
                and best_ask >= best_bid > 0
            ):
                return None
            spread_pct = (best_ask - best_bid) / best_ask * 100.0
            if not (
                0.0 < self.live_policy_max_entry_spread_pct <= 1.5
                and spread_pct <= self.live_policy_max_entry_spread_pct
            ):
                return None
            return {
                "Code": candidate.code,
                "Name": candidate.name,
                "Price": current,
                "FluRate": _pct(current, source_close) or 0.0,
                "TradeValue": _safe_int(self.state.get("trade_value")),
                "Volume": _safe_int(self.state.get("volume")),
                "PriorityScore": 215.0,
                "ScannerWatchBudgetOwner": "rising_missed",
                "UpperLimitLivePolicyKey": key,
                "UpperLimitLivePolicyMatched": True,
                "UpperLimitLivePolicySourceDate": self.live_policy_source_date,
                "UpperLimitLivePolicyVersion": UPPER_LIMIT_LIVE_POLICY_VERSION,
                "UpperLimitLivePolicySampleCount": _safe_int(
                    policy.get("sample_count")
                ),
                "UpperLimitLiveTriggerType": trigger_type,
                "UpperLimitTriggerConfirmedEpoch": confirmed,
                "UpperLimitLastTickEpoch": last_tick,
                "UpperLimitLastQuoteEpoch": last_quote,
                "UpperLimitPriorClose": source_close,
                "UpperLimitCurrentLimitPrice": current_upper,
                "UpperLimitBestAsk": best_ask,
                "UpperLimitBestBid": best_bid,
                "UpperLimitEntrySpreadPct": round(spread_pct, 6),
                "UpperLimitMaxEntrySpreadPct": self.live_policy_max_entry_spread_pct,
                "UpperLimitCohort": candidate.cohort,
                "UpperLimitPriceBand": candidate.price_band,
                "UpperLimitConsecutiveCount": candidate.consecutive_count,
                "UpperLimitRiskMaxDailyEntries": 1,
                "UpperLimitScaleInAllowed": False,
                "UpperLimitSameDayReentryAllowed": False,
                "UpperLimitOvernightAllowed": False,
                "UpperLimitNormalScalpingGuardsRequired": True,
                "UpperLimitEntryProximityGuardRequired": True,
            }
