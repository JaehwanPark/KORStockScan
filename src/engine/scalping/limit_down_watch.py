"""Source-only rotating observation lane for prior KRX limit-down stocks."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import threading
import time
from dataclasses import asdict, dataclass
from datetime import date, datetime
from pathlib import Path
from typing import Any, Callable

from sqlalchemy import text

from src.utils import kiwoom_utils
from src.utils.pipeline_event_logger import emit_pipeline_event

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
RUNTIME_DIR = DATA_DIR / "runtime"
CANDIDATE_DIR = DATA_DIR / "report" / "limit_down_watch_candidate_source"

DECISION_AUTHORITY = "limit_down_source_observation_only"
METRIC_ROLE = "diagnostic"
WINDOW_POLICY = "same_symbol_same_krx_session_ordered_raw_tick"
SAMPLE_FLOOR = "not_applicable_source_observation"
PRIMARY_DECISION_METRIC = "ordered_intraday_path_capture_rate"
SOURCE_QUALITY_GATE = "official_ka10017_and_completed_ka10081_db_close_match"
FORBIDDEN_USES = (
    "real_order,buy_analysis,threshold_change,provider_route_change,"
    "order_price_or_quantity_change,cap_change,broker_guard_change,bot_restart_authority"
)


def _truthy(value: Any) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def feature_enabled() -> bool:
    return _truthy(os.getenv("KORSTOCKSCAN_LIMIT_DOWN_WATCH_ENABLED", "false"))


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value).replace(",", "").replace("+", "").strip()))
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


def _candidate_priority(candidate: LimitDownCandidate) -> tuple[int, int, str]:
    return (
        0 if candidate.consecutive_count >= 2 else 1,
        -candidate.volume,
        candidate.code,
    )


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
    raw_rows, source_meta = fetch_previous(token)
    candidates: list[LimitDownCandidate] = []
    blocked: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    expected_source_date = latest_completed_date_loader(db, target_date)
    seen_counts: dict[str, str] = {}

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
        eligible = daily[daily.index.date < target_date]
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

    candidates.sort(key=_candidate_priority)
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
        "status": "pass" if not blocked else ("partial" if candidates else "blocked"),
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
        / f"limit_down_watch_candidate_source_{target_date.isoformat()}.json",
        artifact,
    )
    return candidates, artifact


class LimitDownObservationRegistry:
    """Thread-safe single-code raw-tick sink and trading-signal isolation registry."""

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

    def observe_raw_tick(
        self, code: str, data: dict[str, Any], received_epoch: float | None = None
    ) -> None:
        with self._lock:
            if not self._code:
                return
            normalized = kiwoom_utils.normalize_stock_code(code)
            sink = self._sink if normalized and normalized == self._code else None
        if sink is not None:
            sink(normalized, dict(data or {}), received_epoch or time.time())


LIMIT_DOWN_OBSERVATION_REGISTRY = LimitDownObservationRegistry()


def is_observation_only_code(code: str) -> bool:
    return LIMIT_DOWN_OBSERVATION_REGISTRY.is_observation_only(code)


def observe_raw_tick(code: str, data: dict[str, Any], received_epoch=None) -> None:
    LIMIT_DOWN_OBSERVATION_REGISTRY.observe_raw_tick(code, data, received_epoch)


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
        self.activity: dict[str, dict[str, Any]] = {}
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
        self._emit(
            "limit_down_watch_source_loaded",
            candidate_count=len(self.candidates),
            source_status=artifact.get("status"),
            source_hash=artifact.get("request_response_hash"),
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

        def priority(item: LimitDownCandidate) -> tuple[Any, ...]:
            activity = self.activity.get(item.code, {})
            tick_count = _safe_int(activity.get("tick_count"))
            unlock_count = _safe_int(activity.get("unlock_count"))
            trade_value = _safe_int(activity.get("trade_value"))
            last_tick_epoch = float(activity.get("last_tick_epoch") or 0.0)
            fresh_tick = last_tick_epoch > 0 and now_epoch - last_tick_epoch <= 30.0
            return (
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
        if lower_limit <= 0:
            self.next_retry_epoch = now_epoch + 300.0
            self.last_visit[candidate.code] = now_epoch
            self._emit(
                "limit_down_watch_source_blocked",
                reason="current_lower_limit_price_missing",
                candidate_code=candidate.code,
            )
            return
        self.active = candidate
        self.last_snapshot_epoch = 0.0
        self.state = {
            "phase": "WAITING_FIRST_TICK",
            "registered_epoch": now_epoch,
            "last_transition_epoch": now_epoch,
            "lower_limit_price": lower_limit,
            "open_price": 0,
            "high_price": 0,
            "low_price": 0,
            "current_price": 0,
            "first_tick_epoch": 0.0,
            "last_tick_epoch": 0.0,
            "unlock_count": 0,
            "relock_count": 0,
            "tick_count": 0,
            "transition_count": 0,
            "first_unlock_epoch": 0.0,
            "first_relock_epoch": 0.0,
            "requested_ws_route": "krx_regular_or_effective_integrated",
            "requested_ws_code_count": 1,
            "requested_ws_item_count_max": 1,
            "last_reg_request_epoch": 0.0,
            "reg_request_count": 0,
        }
        LIMIT_DOWN_OBSERVATION_REGISTRY.activate(candidate.code, self.on_raw_tick)
        self._request_registration(now_epoch, reason="initial")
        self._emit(
            "limit_down_watch_registered",
            cohort=candidate.cohort,
            price_band=candidate.price_band,
            consecutive_count=candidate.consecutive_count,
            lower_limit_price=lower_limit,
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
                return
            self._load_candidates(now_epoch)
            if self.active and self.active.code in active_codes:
                self.release(reason="active_trade_target_conflict", keep_ws=True)
            if self.active:
                registered = float(self.state.get("registered_epoch") or now_epoch)
                last_transition = float(
                    self.state.get("last_transition_epoch") or registered
                )
                first_tick = float(self.state.get("first_tick_epoch") or 0.0)
                last_reg_request = float(
                    self.state.get("last_reg_request_epoch") or registered
                )
                phase = str(self.state.get("phase") or "")
                dwell = now_epoch - registered
                unchanged = now_epoch - last_transition
                should_rotate = dwell >= 600.0 or (
                    phase in {"WAITING_FIRST_TICK", "LIMIT_LOCKED"}
                    and dwell >= 180.0
                    and unchanged >= 180.0
                )
                if should_rotate and len(self.candidates) > 1:
                    self.release(reason="rotation_due")
                elif (
                    self.active is not None
                    and first_tick <= 0
                    and now_epoch - last_reg_request >= 15.0
                ):
                    self._request_registration(now_epoch, reason="first_tick_pending")
            if self.active is None:
                candidate = self._pick(active_codes, now_epoch)
                if candidate is not None:
                    self._activate(candidate, now_epoch)
            if self.active:
                self._write_state()

    def on_raw_tick(
        self, code: str, data: dict[str, Any], received_epoch: float
    ) -> None:
        with self._lock:
            if self.active is None or code != self.active.code:
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
            self.state["first_tick_epoch"] = (
                self.state.get("first_tick_epoch") or received_epoch
            )
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
            locked = current <= lower_limit
            if previous_phase == "WAITING_FIRST_TICK":
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

            reference = self.active.limit_down_close
            open_value = _safe_int(self.state.get("open_price"))
            high_value = _safe_int(self.state.get("high_price"))
            low_value = _safe_int(self.state.get("low_price"))
            best_ask, best_bid = _top_of_book(data)
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
                    first_tick_epoch=self.state.get("first_tick_epoch"),
                    last_tick_epoch=self.state.get("last_tick_epoch"),
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
