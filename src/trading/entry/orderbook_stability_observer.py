from __future__ import annotations

import json
import os
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from math import sqrt
from pathlib import Path
from statistics import median
from typing import Any

from src.trading.order.tick_utils import get_tick_size


DEFAULT_WINDOW_SEC = 10.0
DEFAULT_FR_THRESHOLD = 5
DEFAULT_AGE_P90_THRESHOLD_MS = 400.0
DEFAULT_ALIGNMENT_THRESHOLD = 0.90
DEFAULT_MICRO_LAMBDA = 0.3
DEFAULT_MICRO_WINDOW_SEC = 60.0
DEFAULT_MICRO_MAX_SAMPLES = 300
DEFAULT_MICRO_Z_MIN_SAMPLES = 20
DEFAULT_WIDE_MICRO_WINDOWS_SEC = (180, 300, 600)
DEFAULT_OFI_BULL_THRESHOLD = 1.2
DEFAULT_OFI_BEAR_THRESHOLD = -1.0
DEFAULT_QI_BULL_THRESHOLD = 0.55
DEFAULT_QI_BEAR_THRESHOLD = 0.48
DEFAULT_BUCKET_MANIFEST_PATH = Path("data/config/ofi_bucket_threshold_manifest.json")


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(str(value).replace(",", "").strip()))
    except Exception:
        return default


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(str(value).replace(",", "").strip())
    except Exception:
        return default


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "y", "on"}


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return round(float(ordered[0]), 3)
    rank = (len(ordered) - 1) * percentile
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    weight = rank - lower
    return round(float(ordered[lower] * (1.0 - weight) + ordered[upper] * weight), 3)


@dataclass
class _PendingReversion:
    side: str
    price: int
    changed_at: float
    counted: bool = False


@dataclass
class _SymbolState:
    quotes: deque[dict[str, Any]] = field(default_factory=deque)
    trades: deque[dict[str, Any]] = field(default_factory=deque)
    micro_samples: deque[dict[str, Any]] = field(default_factory=deque)
    wide_micro_samples: deque[dict[str, Any]] = field(default_factory=deque)
    pending_reversions: deque[_PendingReversion] = field(default_factory=deque)
    flicker_count: int = 0
    last_bid: int = 0
    last_ask: int = 0
    last_bid_qty: int = 0
    last_ask_qty: int = 0
    last_quote_ts: float = 0.0
    ofi_ewma: float = 0.0
    qi_ewma: float | None = None
    depth_ewma: float = 1.0
    last_ofi_instant: float = 0.0
    last_ofi_norm: float = 0.0
    last_ofi_z: float | None = None
    last_qi: float | None = None
    last_bid_depth: int = 0
    last_ask_depth: int = 0
    last_trade_ts: float = 0.0


class OrderbookStabilityObserver:
    """Observe short-window quote stability without affecting entry decisions."""

    def __init__(
        self,
        *,
        window_sec: float = DEFAULT_WINDOW_SEC,
        micro_window_sec: float = DEFAULT_MICRO_WINDOW_SEC,
        micro_max_samples: int = DEFAULT_MICRO_MAX_SAMPLES,
        micro_z_min_samples: int = DEFAULT_MICRO_Z_MIN_SAMPLES,
        wide_micro_windows_sec: tuple[int, ...] | None = None,
        micro_lambda: float = DEFAULT_MICRO_LAMBDA,
        bucket_calibration_enabled: bool | None = None,
        threshold_manifest_path: str | Path | None = None,
        threshold_manifest: dict[str, Any] | None = None,
    ) -> None:
        self.window_sec = float(window_sec)
        self.micro_window_sec = float(micro_window_sec)
        self.micro_max_samples = int(micro_max_samples)
        self.micro_z_min_samples = int(micro_z_min_samples)
        self.wide_micro_windows_sec = tuple(
            int(window)
            for window in (wide_micro_windows_sec or DEFAULT_WIDE_MICRO_WINDOWS_SEC)
            if int(window) > 0
        )
        self.micro_lambda = max(0.0, min(1.0, float(micro_lambda)))
        self.bucket_calibration_enabled = (
            _env_bool("KORSTOCKSCAN_SCALPING_ENTRY_PRICE_ORDERBOOK_MICRO_BUCKET_CALIBRATION_ENABLED", False)
            if bucket_calibration_enabled is None
            else bool(bucket_calibration_enabled)
        )
        self.threshold_manifest_path = Path(threshold_manifest_path or DEFAULT_BUCKET_MANIFEST_PATH)
        self._threshold_manifest_override = threshold_manifest
        self._states: dict[str, _SymbolState] = {}
        self._lock = threading.RLock()

    def reset(self) -> None:
        with self._lock:
            self._states.clear()

    def record_quote(
        self,
        code: str,
        *,
        best_bid: int,
        best_ask: int,
        best_bid_qty: int = 0,
        best_ask_qty: int = 0,
        bid_depth_l: int = 0,
        ask_depth_l: int = 0,
        ts: float | None = None,
    ) -> None:
        safe_code = str(code or "").strip()[:6]
        if not safe_code:
            return
        now = float(ts if ts is not None else time.time())
        bid = _safe_int(best_bid)
        ask = _safe_int(best_ask)
        bid_qty = _safe_int(best_bid_qty)
        ask_qty = _safe_int(best_ask_qty)
        bid_depth = _safe_int(bid_depth_l) or bid_qty
        ask_depth = _safe_int(ask_depth_l) or ask_qty
        if bid <= 0 and ask <= 0:
            return
        with self._lock:
            state = self._states.setdefault(safe_code, _SymbolState())
            self._prune(state, now)
            previous_bid = state.last_bid
            previous_ask = state.last_ask
            if previous_bid > 0 and bid > 0 and bid != previous_bid:
                state.pending_reversions.append(_PendingReversion("bid", previous_bid, now))
            if previous_ask > 0 and ask > 0 and ask != previous_ask:
                state.pending_reversions.append(_PendingReversion("ask", previous_ask, now))

            state.last_bid = bid or previous_bid
            state.last_ask = ask or previous_ask
            self._update_orderbook_micro(
                state,
                now=now,
                bid=state.last_bid,
                ask=state.last_ask,
                bid_qty=bid_qty,
                ask_qty=ask_qty,
                bid_depth=bid_depth,
                ask_depth=ask_depth,
                previous_bid=previous_bid,
                previous_ask=previous_ask,
            )
            state.last_quote_ts = now
            state.quotes.append({"ts": now, "best_bid": state.last_bid, "best_ask": state.last_ask})
            self._mark_reversions(state, now)

    def record_trade(self, code: str, *, price: int, ts: float | None = None) -> None:
        safe_code = str(code or "").strip()[:6]
        if not safe_code:
            return
        now = float(ts if ts is not None else time.time())
        trade_price = _safe_int(price)
        if trade_price <= 0:
            return
        with self._lock:
            state = self._states.setdefault(safe_code, _SymbolState())
            self._prune(state, now)
            age_ms = None
            if state.last_quote_ts > 0:
                age_ms = max(0.0, (now - state.last_quote_ts) * 1000.0)
            aligned = self._is_aligned(trade_price, state.last_bid, state.last_ask)
            state.trades.append(
                {
                    "ts": now,
                    "price": trade_price,
                    "best_bid": state.last_bid,
                    "best_ask": state.last_ask,
                    "quote_age_ms": age_ms,
                    "aligned": aligned,
                }
            )
            state.last_trade_ts = now

    def snapshot(self, code: str, *, now: float | None = None) -> dict[str, Any]:
        safe_code = str(code or "").strip()[:6]
        current = float(now if now is not None else time.time())
        with self._lock:
            state = self._states.setdefault(safe_code, _SymbolState())
            self._prune(state, current)
            ages = [float(t["quote_age_ms"]) for t in state.trades if t.get("quote_age_ms") is not None]
            aligned_values = [bool(t.get("aligned")) for t in state.trades if t.get("aligned") is not None]
            alignment = None
            if aligned_values:
                alignment = round(sum(1 for item in aligned_values if item) / len(aligned_values), 6)
            p50 = round(float(median(ages)), 3) if ages else None
            p90 = _percentile(ages, 0.90)
            reasons: list[str] = []
            if state.flicker_count > DEFAULT_FR_THRESHOLD:
                reasons.append("fr_10s")
            if p90 is not None and p90 > DEFAULT_AGE_P90_THRESHOLD_MS:
                reasons.append("quote_age_p90")
            if alignment is not None and alignment < DEFAULT_ALIGNMENT_THRESHOLD:
                reasons.append("print_quote_alignment")
            last_quote_age_ms = (
                round(max(0.0, (current - state.last_quote_ts) * 1000.0), 3)
                if state.last_quote_ts > 0
                else None
            )
            last_trade_age_ms = (
                round(max(0.0, (current - state.last_trade_ts) * 1000.0), 3)
                if state.last_trade_ts > 0
                else None
            )
            observer_missing_reason = self._observer_missing_reason(state)
            return {
                "captured_at_ms": int(round(current * 1000)),
                "snapshot_age_ms": 0,
                "observer_healthy": observer_missing_reason == "ok",
                "observer_missing_reason": observer_missing_reason,
                "observer_last_quote_age_ms": last_quote_age_ms,
                "observer_last_trade_age_ms": last_trade_age_ms,
                "fr_10s": int(state.flicker_count),
                "quote_age_p50_ms": p50,
                "quote_age_p90_ms": p90,
                "print_quote_alignment": alignment,
                "unstable_quote_observed": bool(reasons),
                "unstable_reasons": ",".join(reasons),
                "best_bid": int(state.last_bid or 0),
                "best_ask": int(state.last_ask or 0),
                "sample_trade_count": len(state.trades),
                "sample_quote_count": len(state.quotes),
                "orderbook_micro": self._micro_snapshot(state, now=current),
            }

    def _prune(self, state: _SymbolState, now: float) -> None:
        cutoff = now - self.window_sec
        while state.quotes and float(state.quotes[0].get("ts", 0.0)) < cutoff:
            state.quotes.popleft()
        while state.trades and float(state.trades[0].get("ts", 0.0)) < cutoff:
            state.trades.popleft()
        while state.pending_reversions and state.pending_reversions[0].changed_at < cutoff:
            old = state.pending_reversions.popleft()
            if old.counted and state.flicker_count > 0:
                state.flicker_count -= 1
        micro_cutoff = now - self.micro_window_sec
        while state.micro_samples and float(state.micro_samples[0].get("ts", 0.0)) < micro_cutoff:
            state.micro_samples.popleft()
        while len(state.micro_samples) > self.micro_max_samples:
            state.micro_samples.popleft()
        max_wide_window = max(self.wide_micro_windows_sec or (0,))
        if max_wide_window > 0:
            wide_cutoff = now - float(max_wide_window)
            while state.wide_micro_samples and float(state.wide_micro_samples[0].get("ts", 0.0)) < wide_cutoff:
                state.wide_micro_samples.popleft()

    def _mark_reversions(self, state: _SymbolState, now: float) -> None:
        for item in state.pending_reversions:
            if item.counted:
                continue
            if now - item.changed_at > self.window_sec:
                continue
            current_price = state.last_bid if item.side == "bid" else state.last_ask
            if current_price == item.price:
                item.counted = True
                state.flicker_count += 1

    @staticmethod
    def _is_aligned(price: int, best_bid: int, best_ask: int) -> bool | None:
        if price <= 0 or best_bid <= 0 or best_ask <= 0:
            return None
        lower = min(best_bid, best_ask)
        upper = max(best_bid, best_ask)
        if lower <= price <= upper:
            return True
        mid = (best_bid + best_ask) / 2.0
        return abs(price - mid) <= get_tick_size(price)

    def _update_orderbook_micro(
        self,
        state: _SymbolState,
        *,
        now: float,
        bid: int,
        ask: int,
        bid_qty: int,
        ask_qty: int,
        bid_depth: int,
        ask_depth: int,
        previous_bid: int,
        previous_ask: int,
    ) -> None:
        previous_bid_qty = state.last_bid_qty
        previous_ask_qty = state.last_ask_qty
        has_previous = previous_bid > 0 and previous_ask > 0

        ofi_instant = 0.0
        if has_previous:
            if bid > previous_bid:
                ofi_instant += bid_qty
            elif bid < previous_bid:
                ofi_instant -= previous_bid_qty
            else:
                ofi_instant += bid_qty - previous_bid_qty

            if ask < previous_ask:
                ofi_instant -= ask_qty
            elif ask > previous_ask:
                ofi_instant += previous_ask_qty
            else:
                ofi_instant += previous_ask_qty - ask_qty

        depth_total = max(int(bid_depth) + int(ask_depth), 1)
        lam = self.micro_lambda
        first_micro_sample = len(state.micro_samples) == 0
        if first_micro_sample:
            state.ofi_ewma = float(ofi_instant)
            state.depth_ewma = float(depth_total)
        else:
            state.ofi_ewma = lam * ofi_instant + (1.0 - lam) * state.ofi_ewma
            state.depth_ewma = lam * depth_total + (1.0 - lam) * max(state.depth_ewma, 1.0)

        qi_denominator = bid_qty + ask_qty
        qi = (bid_qty / qi_denominator) if qi_denominator > 0 else None
        if qi is not None:
            state.qi_ewma = qi if state.qi_ewma is None else lam * qi + (1.0 - lam) * state.qi_ewma

        ofi_norm = state.ofi_ewma / sqrt(max(state.depth_ewma, 1.0))
        state.micro_samples.append({"ts": now, "ofi_norm": ofi_norm})
        state.last_ofi_instant = float(ofi_instant)
        state.last_ofi_norm = float(ofi_norm)
        state.last_ofi_z = self._ofi_z(state)
        state.last_qi = qi
        state.wide_micro_samples.append(
            {
                "ts": now,
                "ofi_norm": float(ofi_norm),
                "ofi_z": state.last_ofi_z,
                "qi": qi,
                "qi_ewma": state.qi_ewma,
            }
        )
        state.last_bid_qty = bid_qty
        state.last_ask_qty = ask_qty
        state.last_bid_depth = bid_depth
        state.last_ask_depth = ask_depth

    def _ofi_z(self, state: _SymbolState) -> float | None:
        values = [float(item.get("ofi_norm", 0.0)) for item in state.micro_samples]
        if len(values) < self.micro_z_min_samples:
            return None
        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        std = sqrt(variance)
        if std <= 1e-9:
            return 0.0
        return (state.last_ofi_norm - mean) / std

    def _observer_missing_reason(self, state: _SymbolState) -> str:
        if state.last_quote_ts <= 0 and state.last_trade_ts <= 0:
            return "missing_quote_and_trade"
        if state.last_quote_ts <= 0:
            return "missing_quote"
        if state.last_trade_ts <= 0:
            return "missing_trade"
        return "ok"

    @staticmethod
    def _price_bucket(price: int) -> str:
        if price <= 0:
            return "not_available_no_price"
        if price < 10_000:
            return "low"
        if price <= 50_000:
            return "mid"
        return "high"

    @staticmethod
    def _depth_bucket(depth_total: int) -> str:
        if depth_total <= 0:
            return "not_available_no_depth"
        if depth_total < 1_000:
            return "thin"
        if depth_total < 10_000:
            return "normal"
        return "thick"

    @staticmethod
    def _spread_bucket(bid: int, ask: int) -> str:
        if bid <= 0 or ask <= 0:
            return "not_available_no_bid_ask"
        tick_size = max(1, int(get_tick_size(max(bid, ask)) or 1))
        spread_ticks = max(0, int(round((ask - bid) / tick_size)))
        if spread_ticks <= 1:
            return "tight"
        if spread_ticks <= 3:
            return "normal"
        return "wide"

    def _sample_bucket(self, sample_count: int) -> str:
        if sample_count < self.micro_z_min_samples:
            return "insufficient"
        if sample_count >= max(self.micro_z_min_samples * 3, 60):
            return "rich"
        return "normal"

    def _bucket_key(self, state: _SymbolState, sample_count: int) -> str:
        depth_total = int(state.last_bid_depth or 0) + int(state.last_ask_depth or 0)
        parts = {
            "spread": self._spread_bucket(int(state.last_bid or 0), int(state.last_ask or 0)),
            "price": self._price_bucket(int(state.last_bid or state.last_ask or 0)),
            "depth": self._depth_bucket(depth_total),
            "sample": self._sample_bucket(sample_count),
        }
        return "|".join(f"{key}={value}" for key, value in parts.items())

    def _load_threshold_manifest(self) -> dict[str, Any] | None:
        if self._threshold_manifest_override is not None:
            return self._threshold_manifest_override
        try:
            if not self.threshold_manifest_path.exists():
                return None
            with self.threshold_manifest_path.open("r", encoding="utf-8") as handle:
                payload = json.load(handle)
            return payload if isinstance(payload, dict) else None
        except Exception:
            return None

    def _resolve_thresholds(self, *, bucket_key: str, sample_count: int) -> dict[str, Any]:
        thresholds = {
            "ofi_bull_threshold": DEFAULT_OFI_BULL_THRESHOLD,
            "ofi_bear_threshold": DEFAULT_OFI_BEAR_THRESHOLD,
            "qi_bull_threshold": DEFAULT_QI_BULL_THRESHOLD,
            "qi_bear_threshold": DEFAULT_QI_BEAR_THRESHOLD,
            "ofi_threshold_source": "global",
            "ofi_threshold_bucket_key": bucket_key,
            "ofi_threshold_manifest_id": "",
            "ofi_threshold_manifest_version": "",
            "ofi_threshold_fallback_reason": "",
            "ofi_bucket_sample_count": 0,
        }
        if not self.bucket_calibration_enabled:
            return thresholds

        manifest = self._load_threshold_manifest()
        if not manifest:
            thresholds["ofi_threshold_source"] = "fallback"
            thresholds["ofi_threshold_fallback_reason"] = "manifest_missing_or_invalid"
            return thresholds
        thresholds["ofi_threshold_manifest_id"] = str(manifest.get("manifest_id") or "")
        thresholds["ofi_threshold_manifest_version"] = str(manifest.get("version") or "")
        if not bool(manifest.get("enabled", False)):
            thresholds["ofi_threshold_source"] = "fallback"
            thresholds["ofi_threshold_fallback_reason"] = "manifest_disabled"
            return thresholds
        min_symbol_samples = _safe_int(manifest.get("min_symbol_samples"), 0)
        if min_symbol_samples > 0 and sample_count < min_symbol_samples:
            thresholds["ofi_threshold_source"] = "fallback"
            thresholds["ofi_threshold_fallback_reason"] = "insufficient_symbol_samples"
            return thresholds

        bucket_thresholds = manifest.get("bucket_thresholds") or {}
        if not isinstance(bucket_thresholds, dict) or bucket_key not in bucket_thresholds:
            thresholds["ofi_threshold_source"] = "fallback"
            thresholds["ofi_threshold_fallback_reason"] = "bucket_missing"
            return thresholds

        min_bucket_samples = _safe_int(manifest.get("min_bucket_samples"), 0)
        item = bucket_thresholds.get(bucket_key) or {}
        if not isinstance(item, dict):
            thresholds["ofi_threshold_source"] = "fallback"
            thresholds["ofi_threshold_fallback_reason"] = "bucket_invalid"
            return thresholds
        bucket_samples = _safe_int(item.get("bucket_sample_count", item.get("sample_count")), sample_count)
        thresholds["ofi_bucket_sample_count"] = bucket_samples
        if min_bucket_samples > 0 and bucket_samples < min_bucket_samples:
            thresholds["ofi_threshold_source"] = "fallback"
            thresholds["ofi_threshold_fallback_reason"] = "insufficient_bucket_samples"
            return thresholds

        for key in ("ofi_bull_threshold", "ofi_bear_threshold", "qi_bull_threshold", "qi_bear_threshold"):
            if key in item:
                thresholds[key] = _safe_float(item.get(key), thresholds[key])
        thresholds["ofi_threshold_source"] = "bucket"
        return thresholds

    @staticmethod
    def _avg(values: list[float]) -> float | None:
        if not values:
            return None
        return round(sum(values) / len(values), 6)

    def _wide_micro_window_summary(
        self,
        state: _SymbolState,
        *,
        now: float,
        threshold_meta: dict[str, Any],
    ) -> dict[str, Any]:
        summaries: dict[str, Any] = {}
        windows: dict[str, Any] = {}
        for window_sec in self.wide_micro_windows_sec:
            label = f"{int(window_sec)}s"
            samples = [
                sample
                for sample in state.wide_micro_samples
                if float(sample.get("ts", 0.0)) >= now - float(window_sec)
            ]
            ready_samples = [
                sample
                for sample in samples
                if sample.get("ofi_z") is not None and sample.get("qi_ewma") is not None
            ]
            state_counts = {"bullish": 0, "bearish": 0, "neutral": 0}
            ofi_values: list[float] = []
            qi_values: list[float] = []
            for sample in ready_samples:
                ofi_z = float(sample.get("ofi_z") or 0.0)
                qi_ewma = float(sample.get("qi_ewma") or 0.0)
                ofi_values.append(ofi_z)
                qi_values.append(qi_ewma)
                if (
                    ofi_z >= float(threshold_meta["ofi_bull_threshold"])
                    and qi_ewma >= float(threshold_meta["qi_bull_threshold"])
                ):
                    state_counts["bullish"] += 1
                elif (
                    ofi_z <= float(threshold_meta["ofi_bear_threshold"])
                    and qi_ewma < float(threshold_meta["qi_bear_threshold"])
                ):
                    state_counts["bearish"] += 1
                else:
                    state_counts["neutral"] += 1

            ready_count = len(ready_samples)
            bullish_ratio = round(state_counts["bullish"] / ready_count, 6) if ready_count else 0.0
            bearish_ratio = round(state_counts["bearish"] / ready_count, 6) if ready_count else 0.0
            if ready_count < self.micro_z_min_samples:
                dominant_state = "insufficient"
            elif bullish_ratio >= 0.60 and state_counts["bullish"] >= max(3, self.micro_z_min_samples // 2):
                dominant_state = "persistent_bullish"
            elif bearish_ratio >= 0.60 and state_counts["bearish"] >= max(3, self.micro_z_min_samples // 2):
                dominant_state = "persistent_bearish"
            elif state_counts["bullish"] > 0 and state_counts["bearish"] > 0:
                dominant_state = "mixed"
            else:
                dominant_state = "neutral"

            prefix = f"wide_{int(window_sec)}s"
            window_summary = {
                "window_sec": int(window_sec),
                "sample_count": len(samples),
                "ready_sample_count": ready_count,
                "bullish_count": state_counts["bullish"],
                "bearish_count": state_counts["bearish"],
                "neutral_count": state_counts["neutral"],
                "bullish_ratio": bullish_ratio,
                "bearish_ratio": bearish_ratio,
                "avg_ofi_z": self._avg(ofi_values),
                "avg_qi_ewma": self._avg(qi_values),
                "dominant_state": dominant_state,
            }
            windows[label] = window_summary
            summaries[f"{prefix}_state"] = dominant_state
            summaries[f"{prefix}_sample_count"] = len(samples)
            summaries[f"{prefix}_ready_sample_count"] = ready_count
            summaries[f"{prefix}_bullish_ratio"] = bullish_ratio
            summaries[f"{prefix}_bearish_ratio"] = bearish_ratio
            summaries[f"{prefix}_avg_ofi_z"] = window_summary["avg_ofi_z"]
            summaries[f"{prefix}_avg_qi_ewma"] = window_summary["avg_qi_ewma"]
        summaries["wide_windows"] = windows
        return summaries

    def _micro_snapshot(self, state: _SymbolState, *, now: float) -> dict[str, Any]:
        sample_count = len(state.micro_samples)
        reason = ""
        ready = True
        if state.last_qi is None or state.qi_ewma is None:
            ready = False
            reason = "missing_best_qty"
        elif sample_count < self.micro_z_min_samples or state.last_ofi_z is None:
            ready = False
            reason = "insufficient_samples"

        bucket_key = self._bucket_key(state, sample_count)
        threshold_meta = self._resolve_thresholds(bucket_key=bucket_key, sample_count=sample_count)
        micro_state = "insufficient"
        if ready:
            ofi_z = float(state.last_ofi_z or 0.0)
            qi_ewma = float(state.qi_ewma or 0.0)
            if (
                ofi_z >= float(threshold_meta["ofi_bull_threshold"])
                and qi_ewma >= float(threshold_meta["qi_bull_threshold"])
            ):
                micro_state = "bullish"
            elif (
                ofi_z <= float(threshold_meta["ofi_bear_threshold"])
                and qi_ewma < float(threshold_meta["qi_bear_threshold"])
            ):
                micro_state = "bearish"
            else:
                micro_state = "neutral"

        quote_age_ms = (
            round(max(0.0, (now - state.last_quote_ts) * 1000.0), 3)
            if state.last_quote_ts > 0
            else None
        )
        trade_age_ms = (
            round(max(0.0, (now - state.last_trade_ts) * 1000.0), 3)
            if state.last_trade_ts > 0
            else None
        )
        calibration_warning = ""
        if sample_count < self.micro_z_min_samples:
            calibration_warning = "insufficient_symbol_samples"
        elif threshold_meta["ofi_threshold_source"] == "fallback":
            calibration_warning = str(threshold_meta["ofi_threshold_fallback_reason"] or "threshold_fallback")
        wide_summary = self._wide_micro_window_summary(state, now=now, threshold_meta=threshold_meta)

        return {
            "captured_at_ms": int(round(now * 1000)),
            "snapshot_age_ms": 0,
            "observer_healthy": self._observer_missing_reason(state) == "ok",
            "observer_missing_reason": self._observer_missing_reason(state),
            "observer_last_quote_age_ms": quote_age_ms,
            "observer_last_trade_age_ms": trade_age_ms,
            "micro_window_sec": round(float(self.micro_window_sec), 3),
            "micro_z_min_samples": int(self.micro_z_min_samples),
            "micro_lambda": round(float(self.micro_lambda), 6),
            "ready": bool(ready),
            "reason": reason or "ready",
            "qi": round(float(state.last_qi), 6) if state.last_qi is not None else None,
            "qi_ewma": round(float(state.qi_ewma), 6) if state.qi_ewma is not None else None,
            "ofi_instant": round(float(state.last_ofi_instant), 6),
            "ofi_ewma": round(float(state.ofi_ewma), 6),
            "ofi_norm": round(float(state.last_ofi_norm), 6),
            "ofi_z": round(float(state.last_ofi_z), 6) if state.last_ofi_z is not None else None,
            "depth_ewma": round(float(state.depth_ewma), 6),
            "micro_state": micro_state,
            "sample_quote_count": sample_count,
            "bid_depth_l": int(state.last_bid_depth or 0),
            "ask_depth_l": int(state.last_ask_depth or 0),
            **threshold_meta,
            "ofi_calibration_bucket": bucket_key,
            "ofi_bucket_key": bucket_key,
            "ofi_symbol_sample_count": sample_count,
            "ofi_bucket_sample_count": _safe_int(threshold_meta.get("ofi_bucket_sample_count"), 0),
            "ofi_symbol_bearish_rate": None,
            "ofi_bucket_bearish_rate": None,
            "ofi_symbol_bullish_rate": None,
            "ofi_bucket_bullish_rate": None,
            "ofi_symbol_bucket_deviation": None,
            "ofi_calibration_warning": calibration_warning,
            **wide_summary,
        }


ORDERBOOK_STABILITY_OBSERVER = OrderbookStabilityObserver()
