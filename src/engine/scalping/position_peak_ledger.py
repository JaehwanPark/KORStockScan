"""Durable peak-price state for real scalping position cycles."""

from __future__ import annotations

import json
import math
import os
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

from src.utils.constants import DATA_DIR

SCHEMA_VERSION = 1
DEFAULT_LEDGER_PATH = Path(DATA_DIR) / "runtime" / "scalp_position_peak_state.json"


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "-", "None", "none", "null"):
            return float(default)
        return float(value)
    except (TypeError, ValueError):
        return float(default)


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, "", "-", "None", "none", "null"):
            return int(default)
        return int(float(value))
    except (TypeError, ValueError):
        return int(default)


def _time_token(value: Any) -> str:
    if isinstance(value, datetime):
        return f"{value.timestamp():.6f}"
    numeric = _safe_float(value, float("nan"))
    if math.isfinite(numeric):
        return f"{numeric:.6f}"
    raw = str(value or "").strip()
    if raw:
        try:
            return f"{datetime.fromisoformat(raw).timestamp():.6f}"
        except ValueError:
            return raw
    return "0.000000"


def position_cycle_id(stock: dict[str, Any]) -> str:
    """Return a stable id that cannot leak a prior position's peak."""

    existing = str(stock.get("position_peak_cycle_id") or "").strip()
    if existing:
        return existing
    target_id = _safe_int(stock.get("id"), 0)
    code = str(stock.get("code") or stock.get("stock_code") or "").strip()[:6]
    if target_id > 0:
        return f"target:{target_id}:{code}"
    buy_time = stock.get("buy_time") or stock.get("holding_started_at")
    return f"legacy:{code}:{_time_token(buy_time)}"


class PositionPeakRuntimeLedger:
    """Atomic JSON ledger keyed by one immutable position cycle."""

    def __init__(self, path: str | Path = DEFAULT_LEDGER_PATH):
        self.path = Path(path)
        self._lock = threading.RLock()

    def load(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            try:
                payload = json.loads(self.path.read_text(encoding="utf-8"))
            except (FileNotFoundError, json.JSONDecodeError, OSError):
                return {}
            positions = payload.get("positions") if isinstance(payload, dict) else None
            return dict(positions) if isinstance(positions, dict) else {}

    def get_for_stock(self, stock: dict[str, Any]) -> dict[str, Any] | None:
        row = self.load().get(position_cycle_id(stock))
        return dict(row) if isinstance(row, dict) else None

    def record(
        self,
        stock: dict[str, Any],
        *,
        peak_price: int,
        observed_at: float,
        reason: str,
        allow_decrease: bool = False,
    ) -> dict[str, Any] | None:
        peak = _safe_int(peak_price, 0)
        average_price = _safe_float(stock.get("buy_price"), 0.0)
        code = str(stock.get("code") or stock.get("stock_code") or "").strip()[:6]
        if peak <= 0 or average_price <= 0 or not code:
            return None
        cycle_id = position_cycle_id(stock)
        with self._lock:
            rows = self.load()
            previous = dict(rows.get(cycle_id) or {})
            previous_peak = _safe_int(previous.get("peak_price"), 0)
            resolved_peak = peak if allow_decrease else max(previous_peak, peak)
            holding_qty = _safe_int(stock.get("buy_qty"), 0)
            if (
                previous_peak == resolved_peak
                and abs(_safe_float(previous.get("average_price"), 0.0) - average_price)
                <= 0.01
                and _safe_int(previous.get("holding_qty"), 0) == holding_qty
            ):
                return dict(previous)
            row = {
                "position_cycle_id": cycle_id,
                "target_id": _safe_int(stock.get("id"), 0),
                "code": code,
                "average_price": round(average_price, 6),
                "holding_qty": holding_qty,
                "peak_price": resolved_peak,
                "updated_at_epoch": float(observed_at),
                "update_reason": str(reason or "peak_update"),
            }
            if row == previous:
                return dict(row)
            rows[cycle_id] = row
            self._write(rows)
            return dict(row)

    def restore_peak(self, stock: dict[str, Any]) -> tuple[int, str]:
        row = self.get_for_stock(stock)
        if not row:
            return 0, "ledger_row_missing"
        code = str(stock.get("code") or stock.get("stock_code") or "").strip()[:6]
        if str(row.get("code") or "").strip()[:6] != code:
            return 0, "ledger_code_mismatch"
        current_average = _safe_float(stock.get("buy_price"), 0.0)
        ledger_average = _safe_float(row.get("average_price"), 0.0)
        if (
            current_average <= 0
            or ledger_average <= 0
            or abs(current_average - ledger_average) > 0.01
        ):
            return 0, "ledger_average_price_mismatch"
        peak = _safe_int(row.get("peak_price"), 0)
        if peak < current_average:
            return 0, "ledger_peak_below_average"
        return peak, "ledger_peak_restored"

    def remove_for_stock(self, stock: dict[str, Any]) -> bool:
        cycle_id = position_cycle_id(stock)
        with self._lock:
            rows = self.load()
            if cycle_id not in rows:
                return False
            rows.pop(cycle_id, None)
            self._write(rows)
            return True

    def _write(self, rows: dict[str, dict[str, Any]]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema_version": SCHEMA_VERSION,
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


POSITION_PEAK_LEDGER = PositionPeakRuntimeLedger()
