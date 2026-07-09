"""Runtime-only per-symbol microstructure estimator state."""

from __future__ import annotations

import math
import os
import threading
from dataclasses import dataclass
from typing import Any, Mapping


POLICY_VERSION = "micro_estimator_state_v1"
DEFAULT_HOT_TTL_SEC = 600.0
DEFAULT_WARM_TTL_SEC = 180.0
DEFAULT_MAX_HOT_SYMBOLS = 80
DEFAULT_MAX_WARM_SYMBOLS = 200
DEFAULT_HALF_LIFE_SEC = 60.0
DEFAULT_MIN_CONFIDENCE = 0.25
DEFAULT_MIN_OFI_NORM = 0.10
DEFAULT_MIN_PRESSURE = 55.0
FEATURE_ONLY_DECISION_AUTHORITY = "feature_only_micro_estimator_state"
FEATURE_ONLY_FORBIDDEN_USES = (
    "standalone_buy|standalone_scale_in|standalone_exit|hard_safety_bypass|"
    "broker_guard_bypass|threshold_mutation|provider_route_change|bot_restart|cap_release"
)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "-"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, "", "-"):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    text = str(value).strip().lower()
    if text in {"1", "true", "yes", "y", "on"}:
        return True
    if text in {"0", "false", "no", "n", "off"}:
        return False
    return default


def _env_float(name: str, default: float) -> float:
    return _safe_float(os.environ.get(name), default)


def _env_int(name: str, default: int) -> int:
    return _safe_int(os.environ.get(name), default)


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _decay_weight(age_sec: float, half_life_sec: float) -> float:
    if half_life_sec <= 0:
        return 0.0
    return math.pow(0.5, max(0.0, age_sec) / half_life_sec)


def _read_first_number(data: Mapping[str, Any], *keys: str) -> float:
    for key in keys:
        if key in data:
            value = _safe_float(data.get(key), 0.0)
            if value > 0:
                return value
    return 0.0


@dataclass
class MicroEstimatorConfig:
    max_hot_symbols: int = DEFAULT_MAX_HOT_SYMBOLS
    max_warm_symbols: int = DEFAULT_MAX_WARM_SYMBOLS
    hot_ttl_sec: float = DEFAULT_HOT_TTL_SEC
    warm_ttl_sec: float = DEFAULT_WARM_TTL_SEC
    half_life_sec: float = DEFAULT_HALF_LIFE_SEC
    min_confidence: float = DEFAULT_MIN_CONFIDENCE
    min_ofi_norm: float = DEFAULT_MIN_OFI_NORM
    min_pressure: float = DEFAULT_MIN_PRESSURE

    @classmethod
    def from_env(cls) -> "MicroEstimatorConfig":
        return cls(
            max_hot_symbols=max(1, _env_int("KORSTOCKSCAN_MICRO_ESTIMATOR_MAX_HOT_SYMBOLS", DEFAULT_MAX_HOT_SYMBOLS)),
            max_warm_symbols=max(
                0,
                _env_int("KORSTOCKSCAN_MICRO_ESTIMATOR_MAX_WARM_SYMBOLS", DEFAULT_MAX_WARM_SYMBOLS),
            ),
            hot_ttl_sec=max(1.0, _env_float("KORSTOCKSCAN_MICRO_ESTIMATOR_HOT_TTL_SEC", DEFAULT_HOT_TTL_SEC)),
            warm_ttl_sec=max(1.0, _env_float("KORSTOCKSCAN_MICRO_ESTIMATOR_WARM_TTL_SEC", DEFAULT_WARM_TTL_SEC)),
            half_life_sec=max(1.0, _env_float("KORSTOCKSCAN_MICRO_ESTIMATOR_HALF_LIFE_SEC", DEFAULT_HALF_LIFE_SEC)),
            min_confidence=max(0.0, _env_float("KORSTOCKSCAN_MICRO_ESTIMATOR_MIN_CONFIDENCE", DEFAULT_MIN_CONFIDENCE)),
            min_ofi_norm=_env_float("KORSTOCKSCAN_MICRO_ESTIMATOR_MIN_OFI_NORM", DEFAULT_MIN_OFI_NORM),
            min_pressure=_env_float("KORSTOCKSCAN_MICRO_ESTIMATOR_MIN_PRESSURE", DEFAULT_MIN_PRESSURE),
        )


@dataclass
class SymbolMicroEstimatorState:
    symbol: str
    tier: str = "warm"
    last_update_ts: float = 0.0
    last_rest_ts: float = 0.0
    last_ws_ts: float = 0.0
    last_probe_ts: float = 0.0
    ofi_ewma: float = 0.0
    true_ofi_ewma: float = 0.0
    depth_imbalance_ewma: float = 0.0
    last_ofi_event: float = 0.0
    pressure_ewma: float = 50.0
    top_depth_ratio: float = 0.0
    confidence: float = 0.0
    sample_count: int = 0
    true_ofi_sample_count: int = 0
    prev_best_bid_price: float = 0.0
    prev_best_bid_size: float = 0.0
    prev_best_ask_price: float = 0.0
    prev_best_ask_size: float = 0.0
    ofi_source: str = "default_prior"
    source_state: str = "default_prior"


def estimate_orderbook_pressure(orderbook: Mapping[str, Any] | None) -> dict[str, Any]:
    data = orderbook if isinstance(orderbook, Mapping) else {}
    best_bid_qty = _read_first_number(data, "best_bid_qty", "bid_qty_1", "bid1_qty", "bid_qty")
    best_ask_qty = _read_first_number(data, "best_ask_qty", "ask_qty_1", "ask1_qty", "ask_qty")
    bid_total = _read_first_number(data, "bid_tot", "bid_total", "total_bid_qty")
    ask_total = _read_first_number(data, "ask_tot", "ask_total", "total_ask_qty")
    bid_depth = bid_total if bid_total > 0 else best_bid_qty
    ask_depth = ask_total if ask_total > 0 else best_ask_qty
    total_depth = max(0.0, bid_depth + ask_depth)
    ofi_norm = ((bid_depth - ask_depth) / total_depth) if total_depth > 0 else 0.0
    pressure = _clamp(50.0 + (50.0 * ofi_norm), 0.0, 100.0)
    top_depth_ratio = (bid_depth / max(ask_depth, 1.0)) if bid_depth > 0 and ask_depth > 0 else 0.0
    return {
        "bid_depth": bid_depth,
        "ask_depth": ask_depth,
        "total_depth": total_depth,
        "ofi_norm": ofi_norm,
        "pressure": pressure,
        "top_depth_ratio": top_depth_ratio,
        "depth_source": "rest_total_depth" if bid_total > 0 and ask_total > 0 else "rest_best_level_qty",
    }


def _best_level_snapshot(orderbook: Mapping[str, Any] | None) -> dict[str, float]:
    data = orderbook if isinstance(orderbook, Mapping) else {}
    return {
        "bid_price": _read_first_number(data, "best_bid", "bid_price_1", "bid1_price", "bid_price"),
        "bid_size": _read_first_number(data, "best_bid_qty", "bid_qty_1", "bid1_qty", "bid_qty"),
        "ask_price": _read_first_number(data, "best_ask", "ask_price_1", "ask1_price", "ask_price"),
        "ask_size": _read_first_number(data, "best_ask_qty", "ask_qty_1", "ask1_qty", "ask_qty"),
    }


def _has_best_level(snapshot: Mapping[str, float]) -> bool:
    return bool(
        snapshot.get("bid_price", 0.0) > 0
        and snapshot.get("bid_size", 0.0) > 0
        and snapshot.get("ask_price", 0.0) > 0
        and snapshot.get("ask_size", 0.0) > 0
    )


def _true_ofi_event_norm(
    previous: Mapping[str, float],
    current: Mapping[str, float],
) -> tuple[float | None, float]:
    if not _has_best_level(previous) or not _has_best_level(current):
        return None, 0.0
    prev_bid_price = float(previous["bid_price"])
    prev_bid_size = float(previous["bid_size"])
    prev_ask_price = float(previous["ask_price"])
    prev_ask_size = float(previous["ask_size"])
    bid_price = float(current["bid_price"])
    bid_size = float(current["bid_size"])
    ask_price = float(current["ask_price"])
    ask_size = float(current["ask_size"])
    event = 0.0
    if bid_price >= prev_bid_price:
        event += bid_size
    if bid_price <= prev_bid_price:
        event -= prev_bid_size
    if ask_price <= prev_ask_price:
        event -= ask_size
    if ask_price >= prev_ask_price:
        event += prev_ask_size
    denominator = max(1.0, bid_size + ask_size + prev_bid_size + prev_ask_size)
    return _clamp(event / denominator, -1.0, 1.0), event


def feature_only_fields_from_snapshot(
    snapshot: Mapping[str, Any] | None,
    *,
    prefix: str = "micro_estimator",
    consumer_stage: str = "unspecified",
) -> dict[str, Any]:
    snap = snapshot if isinstance(snapshot, Mapping) else {}
    return {
        f"{prefix}_policy_version": snap.get("policy_version") or POLICY_VERSION,
        f"{prefix}_symbol": snap.get("symbol") or "",
        f"{prefix}_tier": snap.get("tier") or "cold",
        f"{prefix}_source_state": snap.get("source_state") or "default_prior",
        f"{prefix}_ofi_source": snap.get("ofi_source") or "default_prior",
        f"{prefix}_ofi_ewma": round(_safe_float(snap.get("ofi_ewma"), 0.0), 4),
        f"{prefix}_true_ofi_ewma": round(_safe_float(snap.get("true_ofi_ewma"), 0.0), 4),
        f"{prefix}_depth_imbalance_ewma": round(_safe_float(snap.get("depth_imbalance_ewma"), 0.0), 4),
        f"{prefix}_last_ofi_event": round(_safe_float(snap.get("last_ofi_event"), 0.0), 4),
        f"{prefix}_pressure_ewma": round(_safe_float(snap.get("pressure_ewma"), 50.0), 3),
        f"{prefix}_top_depth_ratio": round(_safe_float(snap.get("top_depth_ratio"), 0.0), 4),
        f"{prefix}_confidence": round(_safe_float(snap.get("confidence"), 0.0), 4),
        f"{prefix}_sample_count": _safe_int(snap.get("sample_count"), 0),
        f"{prefix}_true_ofi_sample_count": _safe_int(snap.get("true_ofi_sample_count"), 0),
        f"{prefix}_age_sec": round(_safe_float(snap.get("age_sec"), 0.0), 3),
        f"{prefix}_consumer_stage": consumer_stage or "unspecified",
        f"{prefix}_metric_role": "diagnostic",
        f"{prefix}_decision_authority": FEATURE_ONLY_DECISION_AUTHORITY,
        f"{prefix}_runtime_effect": False,
        f"{prefix}_allowed_runtime_apply": False,
        f"{prefix}_standalone_order_authority": False,
        f"{prefix}_forbidden_uses": FEATURE_ONLY_FORBIDDEN_USES,
    }


class MicroEstimatorStore:
    """Bounded runtime-only state for hot and warm symbols."""

    def __init__(self, config: MicroEstimatorConfig | None = None):
        self.config = config or MicroEstimatorConfig.from_env()
        self._states: dict[str, SymbolMicroEstimatorState] = {}
        self._lock = threading.RLock()

    def clear(self) -> None:
        with self._lock:
            self._states.clear()

    def __len__(self) -> int:
        with self._lock:
            return len(self._states)

    def state_count_by_tier(self) -> dict[str, int]:
        with self._lock:
            counts = {"hot": 0, "warm": 0}
            for state in self._states.values():
                counts[state.tier] = counts.get(state.tier, 0) + 1
            return counts

    def mark_candidate(
        self,
        symbol: str,
        *,
        tier: str = "warm",
        now_ts: float,
        reason: str = "candidate",
    ) -> SymbolMicroEstimatorState:
        with self._lock:
            symbol_key = str(symbol or "").strip()
            if not symbol_key:
                raise ValueError("symbol is required")
            self.prune(now_ts)
            resolved_tier = "hot" if str(tier).lower() == "hot" else "warm"
            state = self._states.get(symbol_key)
            if state is None:
                state = SymbolMicroEstimatorState(symbol=symbol_key, tier=resolved_tier)
                self._states[symbol_key] = state
            elif state.tier != "hot" or resolved_tier == "hot":
                state.tier = resolved_tier
            if state.last_update_ts <= 0:
                state.last_update_ts = float(now_ts)
                state.source_state = "default_prior"
            self._enforce_limits(now_ts)
            return state

    def update_from_rest_orderbook(
        self,
        symbol: str,
        orderbook: Mapping[str, Any] | None,
        *,
        now_ts: float,
        tier: str = "hot",
    ) -> SymbolMicroEstimatorState:
        with self._lock:
            state = self.mark_candidate(symbol, tier=tier, now_ts=now_ts, reason="rest_orderbook")
            depth = estimate_orderbook_pressure(orderbook)
            if depth["total_depth"] <= 0:
                return state
            current_best = _best_level_snapshot(orderbook)
            true_ofi_norm, raw_ofi_event = self._calculate_true_ofi(state, current_best)
            confidence = 0.72
            self._apply_observation(
                state,
                now_ts=now_ts,
                ofi_norm=true_ofi_norm if true_ofi_norm is not None else float(depth["ofi_norm"]),
                depth_imbalance=float(depth["ofi_norm"]),
                true_ofi_norm=true_ofi_norm,
                raw_ofi_event=raw_ofi_event,
                pressure=float(depth["pressure"]),
                top_depth_ratio=float(depth["top_depth_ratio"]),
                confidence=confidence,
                source_state="rest_orderbook_delta_estimate" if true_ofi_norm is not None else "rest_anchored_estimate",
                ofi_source="rest_orderbook_delta" if true_ofi_norm is not None else "depth_imbalance_proxy",
                current_best=current_best,
            )
            if confidence > 0:
                state.last_rest_ts = float(now_ts)
            return state

    def update_from_ws_quote(
        self,
        symbol: str,
        ws_quote: Mapping[str, Any] | None,
        *,
        now_ts: float,
        tier: str = "warm",
    ) -> SymbolMicroEstimatorState:
        with self._lock:
            state = self.mark_candidate(symbol, tier=tier, now_ts=now_ts, reason="ws_quote")
            data = ws_quote if isinstance(ws_quote, Mapping) else {}
            depth = estimate_orderbook_pressure(data)
            if depth["total_depth"] <= 0:
                return state
            current_best = _best_level_snapshot(data)
            true_ofi_norm, raw_ofi_event = self._calculate_true_ofi(state, current_best)
            quote_age_ms = _safe_float(data.get("quote_age_ms"), 0.0)
            stale = str(data.get("source_quality_state") or "").lower().find("stale") >= 0
            stale = stale or str(data.get("quote_stale") or "").strip().lower() in {"1", "true", "stale"}
            fresh = bool(depth["total_depth"] > 0 and (quote_age_ms <= 3000.0 or quote_age_ms <= 0) and not stale)
            confidence = 0.85 if fresh else 0.15 if depth["total_depth"] > 0 else 0.0
            self._apply_observation(
                state,
                now_ts=now_ts,
                ofi_norm=true_ofi_norm if true_ofi_norm is not None else float(depth["ofi_norm"]),
                depth_imbalance=float(depth["ofi_norm"]),
                true_ofi_norm=true_ofi_norm,
                raw_ofi_event=raw_ofi_event,
                pressure=float(depth["pressure"]),
                top_depth_ratio=float(depth["top_depth_ratio"]),
                confidence=confidence,
                source_state=(
                    "fresh_ws_order_flow_delta"
                    if fresh and true_ofi_norm is not None
                    else "fresh_ws_estimate"
                    if fresh
                    else "decayed_ws_order_flow_delta"
                    if true_ofi_norm is not None
                    else "decayed_ws_estimate"
                ),
                ofi_source="ws_order_flow_delta" if true_ofi_norm is not None else "depth_imbalance_proxy",
                current_best=current_best,
            )
            if confidence > 0:
                state.last_ws_ts = float(now_ts)
            return state

    def update_from_feature_probe(
        self,
        symbol: str,
        probe: Mapping[str, Any] | None,
        source_quality: Mapping[str, Any] | None = None,
        *,
        now_ts: float,
        observed_ts: float | None = None,
        max_age_sec: float = 120.0,
        tier: str = "hot",
    ) -> SymbolMicroEstimatorState:
        with self._lock:
            state = self.mark_candidate(symbol, tier=tier, now_ts=now_ts, reason="feature_probe")
            probe_data = probe if isinstance(probe, Mapping) else {}
            quality_data = source_quality if isinstance(source_quality, Mapping) else {}
            pressure = _safe_float(
                probe_data.get("buy_pressure_10t")
                or probe_data.get("late_entry_buy_pressure_10t")
                or quality_data.get("buy_pressure_10t")
                or quality_data.get("late_entry_buy_pressure_10t"),
                50.0,
            )
            delta = _safe_float(
                probe_data.get("net_aggressive_delta_10t") or quality_data.get("net_aggressive_delta_10t"),
                0.0,
            )
            observed = _safe_float(observed_ts, 0.0)
            age_sec = max(0.0, float(now_ts) - observed) if observed > 0 else max_age_sec
            age_confidence = _clamp(1.0 - (age_sec / max(1.0, max_age_sec)), 0.0, 1.0)
            decayed_pressure = 50.0 + ((_clamp(pressure, 0.0, 100.0) - 50.0) * age_confidence)
            ofi_hint = _clamp(delta / max(abs(delta), 1000.0), -1.0, 1.0) if delta else 0.0
            confidence = 0.40 * age_confidence if observed > 0 else 0.0
            self._apply_observation(
                state,
                now_ts=now_ts,
                ofi_norm=ofi_hint,
                depth_imbalance=ofi_hint,
                true_ofi_norm=None,
                raw_ofi_event=0.0,
                pressure=decayed_pressure,
                top_depth_ratio=state.top_depth_ratio,
                confidence=confidence,
                source_state="smoothed_probe_estimate" if confidence > 0 else "default_prior",
                ofi_source="feature_probe_delta_hint",
                current_best=None,
            )
            if confidence > 0:
                state.last_probe_ts = observed
            return state

    def snapshot(self, symbol: str, *, now_ts: float) -> dict[str, Any]:
        with self._lock:
            symbol_key = str(symbol or "").strip()
            state = self._states.get(symbol_key)
            if state is None:
                return self._default_snapshot(symbol_key, now_ts=now_ts)
            age_sec = max(0.0, float(now_ts) - float(state.last_update_ts or now_ts))
            ttl_sec = self.config.hot_ttl_sec if state.tier == "hot" else self.config.warm_ttl_sec
            decay = _decay_weight(age_sec, self.config.half_life_sec)
            confidence = _clamp(state.confidence * decay, 0.0, 1.0)
            source_state = state.source_state
            if age_sec > ttl_sec:
                source_state = "unusable"
                confidence = 0.0
            elif confidence <= 0.0:
                source_state = "default_prior"
            elif age_sec > self.config.half_life_sec:
                source_state = "decayed_estimate"
            return {
            "policy_version": POLICY_VERSION,
            "symbol": symbol_key,
            "tier": state.tier,
            "source_state": source_state,
            "ofi_source": state.ofi_source,
            "ofi_ewma": state.ofi_ewma,
            "true_ofi_ewma": state.true_ofi_ewma,
            "depth_imbalance_ewma": state.depth_imbalance_ewma,
            "last_ofi_event": state.last_ofi_event,
            "pressure_ewma": state.pressure_ewma,
            "top_depth_ratio": state.top_depth_ratio,
            "confidence": confidence,
            "sample_count": state.sample_count,
            "true_ofi_sample_count": state.true_ofi_sample_count,
            "age_sec": age_sec,
            "last_update_ts": state.last_update_ts,
            "last_rest_ts": state.last_rest_ts,
            "last_ws_ts": state.last_ws_ts,
            "last_probe_ts": state.last_probe_ts,
            "prev_best_bid_price": state.prev_best_bid_price,
            "prev_best_bid_size": state.prev_best_bid_size,
            "prev_best_ask_price": state.prev_best_ask_price,
            "prev_best_ask_size": state.prev_best_ask_size,
            "min_confidence": self.config.min_confidence,
            "min_ofi_norm": self.config.min_ofi_norm,
            "min_pressure": self.config.min_pressure,
            }

    def prune(self, now_ts: float) -> int:
        with self._lock:
            remove: list[str] = []
            for symbol, state in self._states.items():
                ttl_sec = self.config.hot_ttl_sec if state.tier == "hot" else self.config.warm_ttl_sec
                age_sec = max(0.0, float(now_ts) - float(state.last_update_ts or now_ts))
                if age_sec > ttl_sec:
                    remove.append(symbol)
            for symbol in remove:
                self._states.pop(symbol, None)
            return len(remove)

    def _calculate_true_ofi(
        self,
        state: SymbolMicroEstimatorState,
        current_best: Mapping[str, float],
    ) -> tuple[float | None, float]:
        previous = {
            "bid_price": state.prev_best_bid_price,
            "bid_size": state.prev_best_bid_size,
            "ask_price": state.prev_best_ask_price,
            "ask_size": state.prev_best_ask_size,
        }
        return _true_ofi_event_norm(previous, current_best)

    def _apply_observation(
        self,
        state: SymbolMicroEstimatorState,
        *,
        now_ts: float,
        ofi_norm: float,
        depth_imbalance: float,
        true_ofi_norm: float | None,
        raw_ofi_event: float,
        pressure: float,
        top_depth_ratio: float,
        confidence: float,
        source_state: str,
        ofi_source: str,
        current_best: Mapping[str, float] | None,
    ) -> None:
        prev_ts = state.last_update_ts or now_ts
        elapsed = max(0.0, float(now_ts) - float(prev_ts))
        alpha = 1.0 if state.sample_count <= 0 else _clamp(1.0 - _decay_weight(elapsed, self.config.half_life_sec), 0.20, 0.80)
        state.depth_imbalance_ewma = ((1.0 - alpha) * state.depth_imbalance_ewma) + (
            alpha * _clamp(depth_imbalance, -1.0, 1.0)
        )
        if true_ofi_norm is not None:
            state.true_ofi_ewma = ((1.0 - alpha) * state.true_ofi_ewma) + (
                alpha * _clamp(true_ofi_norm, -1.0, 1.0)
            )
            state.true_ofi_sample_count += 1
            state.last_ofi_event = float(raw_ofi_event)
            state.ofi_ewma = state.true_ofi_ewma
            effective_ofi_source = ofi_source
        elif state.true_ofi_sample_count > 0:
            state.ofi_ewma = state.true_ofi_ewma
            effective_ofi_source = "previous_true_ofi"
        elif state.true_ofi_sample_count <= 0:
            state.ofi_ewma = ((1.0 - alpha) * state.ofi_ewma) + (alpha * _clamp(ofi_norm, -1.0, 1.0))
            effective_ofi_source = ofi_source
        state.pressure_ewma = ((1.0 - alpha) * state.pressure_ewma) + (alpha * _clamp(pressure, 0.0, 100.0))
        state.top_depth_ratio = max(0.0, top_depth_ratio)
        state.confidence = max(state.confidence * _decay_weight(elapsed, self.config.half_life_sec), _clamp(confidence, 0.0, 1.0))
        state.sample_count += 1
        state.last_update_ts = float(now_ts)
        state.ofi_source = effective_ofi_source
        state.source_state = source_state
        if current_best is not None and _has_best_level(current_best):
            state.prev_best_bid_price = float(current_best["bid_price"])
            state.prev_best_bid_size = float(current_best["bid_size"])
            state.prev_best_ask_price = float(current_best["ask_price"])
            state.prev_best_ask_size = float(current_best["ask_size"])
        self._enforce_limits(now_ts)

    def _enforce_limits(self, now_ts: float) -> None:
        self.prune(now_ts)
        hot = [item for item in self._states.values() if item.tier == "hot"]
        warm = [item for item in self._states.values() if item.tier != "hot"]
        hot.sort(key=lambda item: item.last_update_ts)
        warm.sort(key=lambda item: item.last_update_ts)
        while len(hot) > self.config.max_hot_symbols:
            demote = hot.pop(0)
            demote.tier = "warm"
            warm.append(demote)
            warm.sort(key=lambda item: item.last_update_ts)
        while len(warm) > self.config.max_warm_symbols:
            evict = warm.pop(0)
            self._states.pop(evict.symbol, None)

    def _default_snapshot(self, symbol: str, *, now_ts: float) -> dict[str, Any]:
        return {
            "policy_version": POLICY_VERSION,
            "symbol": symbol,
            "tier": "cold",
            "source_state": "default_prior",
            "ofi_source": "default_prior",
            "ofi_ewma": 0.0,
            "true_ofi_ewma": 0.0,
            "depth_imbalance_ewma": 0.0,
            "last_ofi_event": 0.0,
            "pressure_ewma": 50.0,
            "top_depth_ratio": 0.0,
            "confidence": 0.0,
            "sample_count": 0,
            "true_ofi_sample_count": 0,
            "age_sec": 0.0,
            "last_update_ts": 0.0,
            "last_rest_ts": 0.0,
            "last_ws_ts": 0.0,
            "last_probe_ts": 0.0,
            "prev_best_bid_price": 0.0,
            "prev_best_bid_size": 0.0,
            "prev_best_ask_price": 0.0,
            "prev_best_ask_size": 0.0,
            "min_confidence": self.config.min_confidence,
            "min_ofi_norm": self.config.min_ofi_norm,
            "min_pressure": self.config.min_pressure,
        }


DEFAULT_STORE = MicroEstimatorStore()


def mark_candidate(symbol: str, *, tier: str = "warm", now_ts: float, reason: str = "candidate"):
    return DEFAULT_STORE.mark_candidate(symbol, tier=tier, now_ts=now_ts, reason=reason)


def update_from_ws_quote(symbol: str, ws_quote: Mapping[str, Any] | None, *, now_ts: float, tier: str = "warm"):
    return DEFAULT_STORE.update_from_ws_quote(symbol, ws_quote, now_ts=now_ts, tier=tier)


def update_from_rest_orderbook(symbol: str, orderbook: Mapping[str, Any] | None, *, now_ts: float, tier: str = "hot"):
    return DEFAULT_STORE.update_from_rest_orderbook(symbol, orderbook, now_ts=now_ts, tier=tier)


def update_from_feature_probe(
    symbol: str,
    probe: Mapping[str, Any] | None,
    source_quality: Mapping[str, Any] | None = None,
    *,
    now_ts: float,
    observed_ts: float | None = None,
    max_age_sec: float = 120.0,
    tier: str = "hot",
):
    return DEFAULT_STORE.update_from_feature_probe(
        symbol,
        probe,
        source_quality,
        now_ts=now_ts,
        observed_ts=observed_ts,
        max_age_sec=max_age_sec,
        tier=tier,
    )


def snapshot(symbol: str, *, now_ts: float) -> dict[str, Any]:
    return DEFAULT_STORE.snapshot(symbol, now_ts=now_ts)


def feature_only_fields(
    symbol: str,
    *,
    now_ts: float,
    prefix: str = "micro_estimator",
    consumer_stage: str = "unspecified",
) -> dict[str, Any]:
    return feature_only_fields_from_snapshot(
        DEFAULT_STORE.snapshot(symbol, now_ts=now_ts),
        prefix=prefix,
        consumer_stage=consumer_stage,
    )


def prune(now_ts: float) -> int:
    return DEFAULT_STORE.prune(now_ts)
