"""Pure policy and durable runtime ledger for early scalp partial take-profit."""

from __future__ import annotations

import json
import math
import os
import tempfile
import threading
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from src.engine.trade_profit import get_trade_cost_rate
from src.utils import kiwoom_utils
from src.utils.constants import DATA_DIR

POLICY_VERSION = "early_volatility_partial_tp_v1"
RUNTIME_FAMILY = "scalp_early_volatility_partial_tp"
DEFAULT_LEDGER_PATH = (
    Path(DATA_DIR) / "runtime" / "early_volatility_partial_tp_state.json"
)
TERMINAL_STATES = {"FILLED_RUNNER", "CANCELLED", "FAILED_RECONCILIATION"}


@dataclass(frozen=True)
class EarlyVolatilityTPContext:
    position_cycle_id: str
    venue: str
    entry_lineage: str
    average_price: float
    holding_qty: int
    entry_bundle_complete: bool
    pending_entry: bool
    pending_add: bool
    quote_fresh: bool
    quote_conflict: bool
    direction_state: str
    observed_prices: tuple[int, ...]
    observation_span_sec: float
    tick_sample_count: int
    partial_already_filled: bool = False
    target_net_profit_pct: float = 0.60
    partial_ratio: float = 0.30
    ttl_sec: int = 180
    min_range_pct: float = 0.60
    min_tick_samples: int = 3
    min_observation_span_sec: float = 2.0
    trade_cost_rate: float | None = None


@dataclass(frozen=True)
class EarlyVolatilityTPDecision:
    policy_version: str
    eligible: bool
    reason: str
    position_cycle_id: str
    venue: str
    entry_lineage: str
    partial_qty: int
    runner_qty: int
    limit_price: int
    target_net_profit_pct: float
    target_gross_profit_pct: float
    partial_ratio: float
    ttl_sec: int
    observed_range_pct: float
    observation_span_sec: float
    tick_sample_count: int

    def as_fields(self) -> dict[str, Any]:
        return asdict(self)


def _ceil_sell_tick(price: float) -> int:
    raw = max(0, int(math.ceil(float(price or 0))))
    if raw <= 0:
        return 0
    tick = max(1, int(kiwoom_utils.get_tick_size(raw) or 1))
    return int(math.ceil(raw / tick) * tick)


def _observed_range_pct(prices: tuple[int, ...]) -> float:
    clean = [int(value) for value in prices if int(value or 0) > 0]
    if len(clean) < 2:
        return 0.0
    low = min(clean)
    return ((max(clean) - low) / low) * 100.0 if low > 0 else 0.0


def resolve_early_volatility_tp(
    context: EarlyVolatilityTPContext,
) -> EarlyVolatilityTPDecision:
    """Resolve one resting partial-profit order without any broker side effect."""

    observed_range_pct = _observed_range_pct(context.observed_prices)
    partial_qty = 0
    runner_qty = max(0, int(context.holding_qty or 0))
    limit_price = 0
    reason = "eligible"

    venue = str(context.venue or "").strip().upper()
    direction = str(context.direction_state or "").strip().upper()
    if venue != "KRX":
        reason = "venue_not_krx"
    elif not str(context.position_cycle_id or "").strip():
        reason = "position_cycle_missing"
    elif float(context.average_price or 0) <= 0:
        reason = "average_price_missing"
    elif int(context.holding_qty or 0) < 2:
        reason = "runner_minimum_not_met"
    elif not context.entry_bundle_complete or context.pending_entry:
        reason = "entry_bundle_not_terminal"
    elif context.pending_add:
        reason = "pending_add_order"
    elif context.partial_already_filled:
        reason = "single_partial_already_filled"
    elif not context.quote_fresh or context.quote_conflict:
        reason = "quote_source_unusable"
    elif direction in {"HARD_NEGATIVE", "UNKNOWN", "", "-"}:
        reason = "direction_unusable"
    elif int(context.tick_sample_count or 0) < max(1, context.min_tick_samples):
        reason = "tick_sample_floor_not_met"
    elif float(context.observation_span_sec or 0) < max(
        0.0, context.min_observation_span_sec
    ):
        reason = "observation_span_not_met"
    elif observed_range_pct < max(0.0, context.min_range_pct):
        reason = "volatility_range_not_met"

    eligible = reason == "eligible"
    cost_rate = get_trade_cost_rate(context.trade_cost_rate)
    target_net = max(0.0, float(context.target_net_profit_pct or 0.0))
    target_sell = (
        float(context.average_price)
        * (1.0 + (target_net / 100.0))
        / max(1e-9, 1.0 - cost_rate)
    )
    target_gross = (
        ((target_sell - float(context.average_price)) / float(context.average_price))
        * 100.0
        if float(context.average_price or 0) > 0
        else 0.0
    )
    if eligible:
        ratio = min(0.90, max(0.01, float(context.partial_ratio or 0.0)))
        partial_qty = min(
            int(context.holding_qty) - 1,
            max(1, int(math.floor(int(context.holding_qty) * ratio))),
        )
        runner_qty = int(context.holding_qty) - partial_qty
        limit_price = _ceil_sell_tick(target_sell)
        if partial_qty <= 0 or runner_qty <= 0 or limit_price <= 0:
            eligible = False
            reason = "resolved_order_invalid"
            partial_qty = 0
            runner_qty = int(context.holding_qty)
            limit_price = 0

    return EarlyVolatilityTPDecision(
        policy_version=POLICY_VERSION,
        eligible=eligible,
        reason=reason,
        position_cycle_id=str(context.position_cycle_id or ""),
        venue=venue or "UNKNOWN",
        entry_lineage=str(context.entry_lineage or "-") or "-",
        partial_qty=partial_qty,
        runner_qty=runner_qty,
        limit_price=limit_price,
        target_net_profit_pct=round(target_net, 6),
        target_gross_profit_pct=round(target_gross, 6),
        partial_ratio=round(float(context.partial_ratio or 0.0), 6),
        ttl_sec=max(1, int(context.ttl_sec or 1)),
        observed_range_pct=round(observed_range_pct, 6),
        observation_span_sec=round(float(context.observation_span_sec or 0.0), 6),
        tick_sample_count=max(0, int(context.tick_sample_count or 0)),
    )


class EarlyTPRuntimeLedger:
    """Small atomic JSON ledger for open resting partial-profit orders."""

    def __init__(self, path: str | Path = DEFAULT_LEDGER_PATH):
        self.path = Path(path)
        self._lock = threading.RLock()

    def load(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            try:
                raw = json.loads(self.path.read_text(encoding="utf-8"))
            except (FileNotFoundError, json.JSONDecodeError, OSError):
                return {}
            rows = raw.get("positions") if isinstance(raw, dict) else None
            return dict(rows) if isinstance(rows, dict) else {}

    def get(self, position_cycle_id: str) -> dict[str, Any] | None:
        row = self.load().get(str(position_cycle_id or ""))
        return dict(row) if isinstance(row, dict) else None

    def upsert(self, position_cycle_id: str, **fields: Any) -> dict[str, Any]:
        key = str(position_cycle_id or "").strip()
        if not key:
            raise ValueError("position_cycle_id is required")
        with self._lock:
            rows = self.load()
            row = dict(rows.get(key) or {})
            row.update(fields)
            row["position_cycle_id"] = key
            rows[key] = row
            self._write(rows)
            return dict(row)

    def _write(self, rows: dict[str, dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": 1,
            "policy_version": POLICY_VERSION,
            "positions": rows,
        }
        fd, tmp_name = tempfile.mkstemp(
            prefix=f".{self.path.name}.", dir=str(self.path.parent), text=True
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as handle:
                json.dump(payload, handle, ensure_ascii=False, sort_keys=True, indent=2)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_name, self.path)
        finally:
            try:
                os.unlink(tmp_name)
            except FileNotFoundError:
                pass
