"""Report-only panic sell defense attribution.

The report detects intraday panic sell clusters, separates real exits from
sim/probe observations, and routes recovery evidence to future canary
candidates. It never mutates runtime thresholds or order behavior.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from src.engine.panic_sell_state_detector import summarize_microstructure_detector_from_events
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import read_jsonl


SCHEMA_VERSION = 1
REPORT_DIRNAME = "panic_sell_defense"
PANIC_WINDOW_MIN = 30
PANIC_STOP_LOSS_RATIO_FLOOR_PCT = 70.0
PANIC_AVG_EXIT_PROFIT_CEILING_PCT = -2.0
MICRO_MARKET_BREADTH_SYMBOL_FLOOR = 20
MICRO_RISK_OFF_RATIO_FLOOR_PCT = 20.0
RECOVERY_WATCH_ACTIVE_AVG_FLOOR_PCT = 0.5
RECOVERY_WATCH_REBOUND_ABOVE_SELL_FLOOR_PCT = 50.0
RECOVERY_CONFIRMED_ACTIVE_AVG_FLOOR_PCT = 0.8
RECOVERY_CONFIRMED_ACTIVE_WIN_RATE_FLOOR_PCT = 60.0
RECOVERY_CONFIRMED_REBOUND_ABOVE_BUY_FLOOR_PCT = 35.0

PANIC_STATES = ("NORMAL", "PANIC_SELL", "RECOVERY_WATCH", "RECOVERY_CONFIRMED")
HOLDING_EXIT_STAGES = {"exit_signal", "swing_probe_exit_signal", "scalp_sim_exit_signal"}
PANIC_STOP_LOSS_COUNT_QUANTILE = 0.95
PANIC_STOP_LOSS_QUANTILE_SAMPLE_FLOOR = 3
PANIC_STOP_LOSS_RATIO_QUANTILE = 0.95
PANIC_AVG_EXIT_PROFIT_QUANTILE = 0.05
MICRO_RISK_OFF_RATIO_QUANTILE = 0.95
RECOVERY_ACTIVE_AVG_QUANTILE = 0.75
RECOVERY_ACTIVE_WIN_RATE_QUANTILE = 0.75
RECOVERY_REBOUND_QUANTILE = 0.75
HARD_PROTECT_EMERGENCY_RULE_MARKERS = (
    "emergency",
    "protect_hard_stop",
    "scalp_hard_stop_pct",
    "scalp_preset_hard_stop_pct",
    "hard_stop",
)
CONFIRMATION_ELIGIBLE_RULE_MARKERS = (
    "soft_stop",
    "trailing",
    "holding_flow",
    "flow_override",
)
STOP_LOSS_MARKERS = (
    "stop_loss",
    "hard_stop",
    "soft_stop",
    "protect_hard_stop",
    "loss",
    "손절",
    "방어선",
)
FORBIDDEN_AUTOMATIONS = [
    "live_threshold_runtime_mutation",
    "score_threshold_relaxation",
    "stop_loss_relaxation",
    "auto_sell",
    "bot_restart",
    "swing_real_order_enable",
]


def _pipeline_events_path(target_date: str) -> Path:
    return DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"


def _report_dir() -> Path:
    return DATA_DIR / "report" / REPORT_DIRNAME


def _json_report_path(dirname: str, target_date: str) -> Path:
    return DATA_DIR / "report" / dirname / f"{dirname}_{target_date}.json"


def _market_regime_path() -> Path:
    return DATA_DIR / "cache" / "market_regime_snapshot.json"


def _market_panic_breadth_path(target_date: str) -> Path:
    return DATA_DIR / "report" / "market_panic_breadth" / f"market_panic_breadth_{target_date}.json"


def _post_sell_feedback_path(target_date: str) -> Path:
    return DATA_DIR / "report" / "monitor_snapshots" / f"post_sell_feedback_{target_date}.json"


def _swing_probe_state_path() -> Path:
    return DATA_DIR / "runtime" / "swing_intraday_probe_state.json"


def _scalp_sim_state_path() -> Path:
    return DATA_DIR / "runtime" / "scalp_live_simulator_state.json"


def _safe_str(value: Any) -> str:
    return str(value if value is not None else "").strip()


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value in (None, "", "-", "None"):
            return default
        numeric = float(str(value).replace("%", "").replace("+", "").replace(",", "").strip())
        return numeric if math.isfinite(numeric) else default
    except (TypeError, ValueError):
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    numeric = _safe_float(value)
    return int(numeric) if numeric is not None else default


def _parse_dt(value: Any) -> datetime | None:
    text = _safe_str(value)
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _avg(values: list[float]) -> float | None:
    return round(sum(values) / len(values), 4) if values else None


def _quantile(values: list[int], q: float) -> int | None:
    if not values:
        return None
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, math.ceil(len(ordered) * q) - 1))
    return ordered[idx]


def _quantile_float(values: list[float], q: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    idx = min(len(ordered) - 1, max(0, math.ceil(len(ordered) * q) - 1))
    return round(ordered[idx], 4)


def _threshold_contract(
    *,
    name: str,
    static_fallback_value: Any,
    dynamic_threshold_value: Any,
    sample_count: int,
    sample_floor: int,
    threshold_source: str,
    threshold_mode: str | None = None,
) -> dict[str, Any]:
    sample_ready = sample_count >= sample_floor
    mode = threshold_mode or ("dynamic_quantile" if sample_ready and dynamic_threshold_value is not None else "insufficient_sample")
    return {
        "name": name,
        "static_fallback_value": static_fallback_value,
        "dynamic_threshold_value": dynamic_threshold_value,
        "sample_count": sample_count,
        "sample_floor": sample_floor,
        "sample_ready": sample_ready,
        "threshold_source": threshold_source,
        "threshold_mode": mode,
    }


def _ratio(numerator: int, denominator: int) -> float:
    return round((numerator / denominator) * 100.0, 1) if denominator else 0.0


def _truthy(value: Any) -> bool:
    return _safe_str(value).lower() in {"1", "true", "yes", "y"}


def _falsey(value: Any) -> bool:
    return _safe_str(value).lower() in {"0", "false", "no", "n"}


def _load_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    return read_jsonl(path)


def _event_fields(row: dict[str, Any]) -> dict[str, Any]:
    fields = row.get("fields")
    return fields if isinstance(fields, dict) else {}


def _is_non_real_observation(row: dict[str, Any]) -> bool:
    fields = _event_fields(row)
    stage = _safe_str(row.get("stage"))
    if _falsey(fields.get("actual_order_submitted")):
        return True
    if _truthy(fields.get("broker_order_forbidden")):
        return True
    if _truthy(fields.get("simulated_order")):
        return True
    if fields.get("simulation_book") or fields.get("simulation_owner"):
        return True
    if _truthy(fields.get("swing_intraday_probe")):
        return True
    if fields.get("probe_id") or fields.get("probe_origin_stage"):
        return True
    return "sim_" in stage or "_probe_" in stage or stage.startswith("swing_probe_")


def _has_real_exit_provenance(row: dict[str, Any]) -> bool:
    fields = _event_fields(row)
    if _truthy(fields.get("actual_order_submitted")):
        return True
    for key in (
        "order_no",
        "sell_order_no",
        "kiwoom_order_no",
        "broker_order_no",
        "broker_order_id",
        "actual_order_id",
    ):
        if _safe_str(fields.get(key)):
            return True
    return False


def _attempt_key(row: dict[str, Any]) -> str:
    fields = _event_fields(row)
    record_id = row.get("record_id")
    if record_id in (None, "", 0):
        record_id = fields.get("id")
    if _safe_str(record_id):
        return f"id:{_safe_str(record_id)}"
    stock_code = _safe_str(row.get("stock_code"))[:6]
    if stock_code:
        return f"code:{stock_code}"
    return f"name:{_safe_str(row.get('stock_name'))}"


def _non_real_attempt_keys(events: list[dict[str, Any]]) -> set[str]:
    """Propagate probe/sim provenance to sparse sibling exit_signal rows."""
    return {
        _attempt_key(row)
        for row in events
        if _attempt_key(row) and _is_non_real_observation(row)
    }


def _exit_rule_text(row: dict[str, Any]) -> str:
    fields = _event_fields(row)
    parts = [
        row.get("stage"),
        fields.get("exit_rule"),
        fields.get("sell_reason_type"),
        fields.get("exit_decision_source"),
        fields.get("reason"),
    ]
    return " ".join(_safe_str(part).lower() for part in parts if _safe_str(part))


def is_hard_protect_emergency_exit(row: dict[str, Any]) -> bool:
    text = _exit_rule_text(row)
    return any(marker in text for marker in HARD_PROTECT_EMERGENCY_RULE_MARKERS)


def is_confirmation_eligible_exit(row: dict[str, Any]) -> bool:
    text = _exit_rule_text(row)
    if is_hard_protect_emergency_exit(row):
        return False
    return any(marker in text for marker in CONFIRMATION_ELIGIBLE_RULE_MARKERS)


def _is_stop_loss_exit(row: dict[str, Any]) -> bool:
    text = _exit_rule_text(row)
    return any(marker in text for marker in STOP_LOSS_MARKERS)


def _is_holding_exit_signal(row: dict[str, Any]) -> bool:
    return _safe_str(row.get("pipeline")) == "HOLDING_PIPELINE" and _safe_str(row.get("stage")) in HOLDING_EXIT_STAGES


def _profit_rate(row: dict[str, Any]) -> float | None:
    fields = _event_fields(row)
    return _safe_float(
        fields.get("profit_rate")
        or fields.get("realized_profit_rate")
        or fields.get("return_pct")
        or fields.get("profit_pct")
    )


def _max_rolling_stop_count(events: list[dict[str, Any]], *, window_min: int) -> int:
    counts = _rolling_stop_counts(events, window_min=window_min)
    return max(counts) if counts else 0


def _rolling_stop_counts(events: list[dict[str, Any]], *, window_min: int) -> list[int]:
    stop_times = sorted(
        dt
        for row in events
        if _is_stop_loss_exit(row)
        for dt in [_parse_dt(row.get("emitted_at"))]
        if dt is not None
    )
    if not stop_times:
        return []
    counts: list[int] = []
    right = 0
    for left, start in enumerate(stop_times):
        while right < len(stop_times) and stop_times[right] <= start + timedelta(minutes=window_min):
            right += 1
        counts.append(right - left)
    return counts


def _summarize_exit_metrics(events: list[dict[str, Any]], *, as_of: datetime | None) -> dict[str, Any]:
    exit_events = [row for row in events if _is_holding_exit_signal(row)]
    holding_events = [row for row in events if _safe_str(row.get("pipeline")) == "HOLDING_PIPELINE"]
    non_real_keys = _non_real_attempt_keys(holding_events)
    real_exits = [
        row
        for row in exit_events
        if _has_real_exit_provenance(row)
        and _attempt_key(row) not in non_real_keys
        and not _is_non_real_observation(row)
    ]
    non_real_exits = [
        row
        for row in exit_events
        if row not in real_exits
    ]
    unproven_exits = [
        row
        for row in exit_events
        if not _has_real_exit_provenance(row) and not _is_non_real_observation(row)
    ]
    stop_loss_real = [row for row in real_exits if _is_stop_loss_exit(row)]
    profits = [value for row in real_exits for value in [_profit_rate(row)] if value is not None]
    stop_profits = [value for row in stop_loss_real for value in [_profit_rate(row)] if value is not None]
    current_window_start = as_of - timedelta(minutes=PANIC_WINDOW_MIN) if as_of else None
    current_window_stop_loss = [
        row
        for row in stop_loss_real
        if current_window_start is not None
        for dt in [_parse_dt(row.get("emitted_at"))]
        if dt is not None and current_window_start <= dt <= as_of
    ]
    exit_rule_counts = Counter(_safe_str(_event_fields(row).get("exit_rule") or "-") for row in real_exits)
    eligible = [row for row in real_exits if is_confirmation_eligible_exit(row)]
    never_delay = [row for row in real_exits if is_hard_protect_emergency_exit(row)]
    max_rolling_stop_loss = _max_rolling_stop_count(real_exits, window_min=PANIC_WINDOW_MIN)
    rolling_stop_counts = _rolling_stop_counts(real_exits, window_min=PANIC_WINDOW_MIN)
    stop_loss_count_quantile_threshold = _quantile(rolling_stop_counts, PANIC_STOP_LOSS_COUNT_QUANTILE)
    quantile_sample_ready = len(rolling_stop_counts) >= PANIC_STOP_LOSS_QUANTILE_SAMPLE_FLOOR
    stop_loss_ratio = _ratio(len(stop_loss_real), len(real_exits))
    avg_exit_profit = _avg(profits)
    stop_loss_ratio_samples = [100.0 if _is_stop_loss_exit(row) else 0.0 for row in real_exits]
    stop_loss_ratio_threshold = _quantile_float(stop_loss_ratio_samples, PANIC_STOP_LOSS_RATIO_QUANTILE)
    if stop_loss_ratio_threshold is not None:
        stop_loss_ratio_threshold = max(stop_loss_ratio_threshold, PANIC_STOP_LOSS_RATIO_FLOOR_PCT)
    avg_exit_profit_threshold = _quantile_float(profits, PANIC_AVG_EXIT_PROFIT_QUANTILE)
    if avg_exit_profit_threshold is not None:
        avg_exit_profit_threshold = min(avg_exit_profit_threshold, PANIC_AVG_EXIT_PROFIT_CEILING_PCT)
    count_contract = _threshold_contract(
        name="rolling_30m_stop_loss_count",
        static_fallback_value=None,
        dynamic_threshold_value=stop_loss_count_quantile_threshold,
        sample_count=len(rolling_stop_counts),
        sample_floor=PANIC_STOP_LOSS_QUANTILE_SAMPLE_FLOOR,
        threshold_source="same_day_real_exit_rolling_30m_p95",
    )
    ratio_contract = _threshold_contract(
        name="stop_loss_exit_ratio_pct",
        static_fallback_value=PANIC_STOP_LOSS_RATIO_FLOOR_PCT,
        dynamic_threshold_value=stop_loss_ratio_threshold,
        sample_count=len(stop_loss_ratio_samples),
        sample_floor=PANIC_STOP_LOSS_QUANTILE_SAMPLE_FLOOR,
        threshold_source="same_day_real_exit_stop_loss_ratio_p95",
    )
    avg_profit_contract = _threshold_contract(
        name="avg_exit_profit_rate_pct",
        static_fallback_value=PANIC_AVG_EXIT_PROFIT_CEILING_PCT,
        dynamic_threshold_value=avg_exit_profit_threshold,
        sample_count=len(profits),
        sample_floor=PANIC_STOP_LOSS_QUANTILE_SAMPLE_FLOOR,
        threshold_source="same_day_real_exit_profit_rate_p05",
    )
    panic_by_count = (
        bool(count_contract["sample_ready"])
        and stop_loss_count_quantile_threshold is not None
        and (
            len(current_window_stop_loss) >= stop_loss_count_quantile_threshold
            or max_rolling_stop_loss >= stop_loss_count_quantile_threshold
        )
    )
    panic_by_ratio = bool(ratio_contract["sample_ready"]) and bool(avg_profit_contract["sample_ready"]) and (
        stop_loss_ratio_threshold is not None
        and avg_exit_profit_threshold is not None
        and stop_loss_ratio >= stop_loss_ratio_threshold
        and avg_exit_profit is not None
        and avg_exit_profit <= avg_exit_profit_threshold
    )
    return {
        "panic_decision_basis": "real_exit_with_broker_provenance_only",
        "real_exit_provenance_required": True,
        "real_exit_count": len(real_exits),
        "non_real_exit_count": len(non_real_exits),
        "unproven_exit_count": len(unproven_exits),
        "sim_probe_exit_excluded_from_panic": True,
        "stop_loss_exit_count": len(stop_loss_real),
        "current_30m_stop_loss_exit_count": len(current_window_stop_loss),
        "max_rolling_30m_stop_loss_exit_count": max_rolling_stop_loss,
        "rolling_30m_stop_loss_count_quantile": PANIC_STOP_LOSS_COUNT_QUANTILE,
        "rolling_30m_stop_loss_count_quantile_threshold": stop_loss_count_quantile_threshold,
        "rolling_30m_stop_loss_count_sample": len(rolling_stop_counts),
        "rolling_30m_stop_loss_count_sample_floor": PANIC_STOP_LOSS_QUANTILE_SAMPLE_FLOOR,
        "rolling_30m_stop_loss_count_sample_ready": quantile_sample_ready,
        "stop_loss_exit_ratio_pct": stop_loss_ratio,
        "avg_exit_profit_rate_pct": avg_exit_profit,
        "avg_stop_loss_profit_rate_pct": _avg(stop_profits),
        "threshold_contract": {
            "threshold_mode": "dynamic_quantile" if count_contract["sample_ready"] else "insufficient_sample",
            "source_quality_blockers": []
            if count_contract["sample_ready"]
            else ["insufficient_quantile_baseline"],
            "thresholds": {
                "rolling_30m_stop_loss_count": count_contract,
                "stop_loss_exit_ratio_pct": ratio_contract,
                "avg_exit_profit_rate_pct": avg_profit_contract,
            },
        },
        "panic_by_stop_loss_count": panic_by_count,
        "panic_by_stop_loss_ratio": panic_by_ratio,
        "panic_detected": panic_by_count or panic_by_ratio,
        "exit_rule_counts": dict(sorted(exit_rule_counts.items())),
        "confirmation_eligible_exit_count": len(eligible),
        "never_delay_exit_count": len(never_delay),
        "confirmation_eligible_rules": sorted({_safe_str(_event_fields(row).get("exit_rule") or "-") for row in eligible}),
        "never_delay_rules": sorted({_safe_str(_event_fields(row).get("exit_rule") or "-") for row in never_delay}),
    }


def _latest_price_from_position(position: dict[str, Any]) -> float | None:
    for key in ("curr_price", "current_price", "last_price", "price"):
        value = _safe_float(position.get(key))
        if value and value > 0:
            return value
    samples = position.get("holding_price_samples")
    if isinstance(samples, list):
        for sample in reversed(samples):
            if isinstance(sample, dict):
                value = _safe_float(sample.get("price"))
                if value and value > 0:
                    return value
    return None


def _entry_price_from_position(position: dict[str, Any]) -> float | None:
    for key in ("buy_price", "entry_price", "assumed_fill_price", "order_price"):
        value = _safe_float(position.get(key))
        if value and value > 0:
            return value
    return None


def _active_position_row(position: dict[str, Any], *, source: str) -> dict[str, Any]:
    buy_price = _entry_price_from_position(position)
    curr_price = _latest_price_from_position(position)
    profit_rate = None
    if buy_price and curr_price:
        profit_rate = round(((curr_price - buy_price) / buy_price) * 100.0, 4)
    elif "profit_rate" in position:
        profit_rate = _safe_float(position.get("profit_rate"))
    actual_order_submitted = position.get("actual_order_submitted")
    broker_order_forbidden = position.get("broker_order_forbidden")
    actual_false = actual_order_submitted is False or _falsey(actual_order_submitted)
    broker_forbidden = broker_order_forbidden is True or _truthy(broker_order_forbidden)
    return {
        "source": source,
        "stock_name": position.get("stock_name") or position.get("name"),
        "stock_code": _safe_str(position.get("stock_code") or position.get("code"))[:6],
        "profit_rate_pct": profit_rate,
        "buy_price": buy_price,
        "current_price": curr_price,
        "qty": _safe_float(position.get("buy_qty") or position.get("qty")),
        "actual_order_submitted": actual_order_submitted,
        "broker_order_forbidden": broker_order_forbidden,
        "actual_order_submitted_false": actual_false,
        "broker_order_forbidden_true": broker_forbidden,
        "probe_origin_stage": position.get("probe_origin_stage"),
        "simulation_book": position.get("simulation_book"),
        "simulation_owner": position.get("simulation_owner"),
    }


def _active_positions_from_state(path: Path, *, source: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    payload = _load_json(path)
    if not isinstance(payload, dict):
        return [], {"path": str(path), "exists": path.exists(), "loaded": False}
    raw_positions = payload.get("active_positions") or payload.get("positions") or payload.get("targets") or []
    if isinstance(raw_positions, dict):
        iterable = list(raw_positions.values())
    elif isinstance(raw_positions, list):
        iterable = raw_positions
    else:
        iterable = []
    rows = [_active_position_row(item, source=source) for item in iterable if isinstance(item, dict)]
    return rows, {
        "path": str(path),
        "exists": True,
        "loaded": True,
        "updated_at": payload.get("updated_at"),
        "owner": payload.get("owner"),
        "simulation_book": payload.get("simulation_book"),
        "active_count": len(rows),
    }


def _summarize_active_recovery() -> dict[str, Any]:
    swing_rows, swing_meta = _active_positions_from_state(_swing_probe_state_path(), source="swing_probe")
    scalp_rows, scalp_meta = _active_positions_from_state(_scalp_sim_state_path(), source="scalp_sim")
    rows = swing_rows + scalp_rows
    profits = [row["profit_rate_pct"] for row in rows if row.get("profit_rate_pct") is not None]
    win_rate = _ratio(sum(1 for value in profits if value > 0), len(profits))
    avg_threshold = _quantile_float(profits, RECOVERY_ACTIVE_AVG_QUANTILE)
    if avg_threshold is not None:
        avg_threshold = min(avg_threshold, RECOVERY_CONFIRMED_ACTIVE_AVG_FLOOR_PCT)
    win_rate_samples = [100.0 if value > 0 else 0.0 for value in profits]
    win_rate_threshold = _quantile_float(win_rate_samples, RECOVERY_ACTIVE_WIN_RATE_QUANTILE)
    if win_rate_threshold is not None:
        win_rate_threshold = min(win_rate_threshold, RECOVERY_CONFIRMED_ACTIVE_WIN_RATE_FLOOR_PCT)
    provenance_violations = [
        row
        for row in rows
        if not row.get("actual_order_submitted_false") or not row.get("broker_order_forbidden_true")
    ]
    return {
        "active_positions": len(rows),
        "profit_sample": len(profits),
        "avg_unrealized_profit_rate_pct": _avg(profits),
        "win_rate_pct": win_rate if profits else None,
        "threshold_contract": {
            "threshold_mode": "dynamic_quantile" if len(profits) >= PANIC_STOP_LOSS_QUANTILE_SAMPLE_FLOOR else "insufficient_sample",
            "source_quality_blockers": []
            if len(profits) >= PANIC_STOP_LOSS_QUANTILE_SAMPLE_FLOOR
            else ["insufficient_quantile_baseline"],
            "thresholds": {
                "active_avg_unrealized_profit_rate_pct": _threshold_contract(
                    name="active_avg_unrealized_profit_rate_pct",
                    static_fallback_value=RECOVERY_CONFIRMED_ACTIVE_AVG_FLOOR_PCT,
                    dynamic_threshold_value=avg_threshold,
                    sample_count=len(profits),
                    sample_floor=PANIC_STOP_LOSS_QUANTILE_SAMPLE_FLOOR,
                    threshold_source="same_day_active_sim_probe_profit_rate_p75",
                ),
                "active_win_rate_pct": _threshold_contract(
                    name="active_win_rate_pct",
                    static_fallback_value=RECOVERY_CONFIRMED_ACTIVE_WIN_RATE_FLOOR_PCT,
                    dynamic_threshold_value=win_rate_threshold,
                    sample_count=len(win_rate_samples),
                    sample_floor=PANIC_STOP_LOSS_QUANTILE_SAMPLE_FLOOR,
                    threshold_source="same_day_active_sim_probe_win_rate_p75",
                ),
            },
        },
        "wins": sum(1 for value in profits if value > 0),
        "losses": sum(1 for value in profits if value < 0),
        "flat": sum(1 for value in profits if value == 0),
        "provenance_check": {
            "passed": not provenance_violations,
            "checked_positions": len(rows),
            "violations": provenance_violations[:10],
        },
        "state_sources": {
            "swing_probe": swing_meta,
            "scalp_sim": scalp_meta,
        },
        "positions": sorted(
            rows,
            key=lambda row: row["profit_rate_pct"] if row.get("profit_rate_pct") is not None else -999.0,
            reverse=True,
        )[:20],
    }


def _post_sell_recovery_metrics(target_date: str) -> dict[str, Any]:
    path = _post_sell_feedback_path(target_date)
    payload = _load_json(path)
    if isinstance(payload, list):
        payload = payload[-1] if payload and isinstance(payload[-1], dict) else {}
    if not isinstance(payload, dict):
        payload = {}
    soft = payload.get("soft_stop_forensics") if isinstance(payload.get("soft_stop_forensics"), dict) else {}
    above_sell = soft.get("rebound_above_sell_rate") if isinstance(soft.get("rebound_above_sell_rate"), dict) else {}
    above_buy = soft.get("rebound_above_buy_rate") if isinstance(soft.get("rebound_above_buy_rate"), dict) else {}
    sell_10_20 = max(_safe_float(above_sell.get("10m"), 0.0) or 0.0, _safe_float(above_sell.get("20m"), 0.0) or 0.0)
    buy_10_20 = max(_safe_float(above_buy.get("10m"), 0.0) or 0.0, _safe_float(above_buy.get("20m"), 0.0) or 0.0)
    sell_samples = [value for value in (_safe_float(above_sell.get("10m")), _safe_float(above_sell.get("20m"))) if value is not None]
    buy_samples = [value for value in (_safe_float(above_buy.get("10m")), _safe_float(above_buy.get("20m"))) if value is not None]
    sell_threshold = _quantile_float(sell_samples, RECOVERY_REBOUND_QUANTILE)
    if sell_threshold is not None:
        sell_threshold = max(sell_threshold, RECOVERY_WATCH_REBOUND_ABOVE_SELL_FLOOR_PCT)
    buy_threshold = _quantile_float(buy_samples, RECOVERY_REBOUND_QUANTILE)
    if buy_threshold is not None:
        buy_threshold = max(buy_threshold, RECOVERY_CONFIRMED_REBOUND_ABOVE_BUY_FLOOR_PCT)
    return {
        "source_path": str(path),
        "source_exists": path.exists(),
        "soft_stop_total": _safe_int(soft.get("total_soft_stop"), 0) if soft else 0,
        "rebound_above_sell_10_20m_pct": sell_10_20,
        "rebound_above_buy_10_20m_pct": buy_10_20,
        "threshold_contract": {
            "threshold_mode": "dynamic_quantile"
            if len(sell_samples + buy_samples) >= PANIC_STOP_LOSS_QUANTILE_SAMPLE_FLOOR
            else "insufficient_sample",
            "source_quality_blockers": []
            if len(sell_samples + buy_samples) >= PANIC_STOP_LOSS_QUANTILE_SAMPLE_FLOOR
            else ["insufficient_quantile_baseline"],
            "thresholds": {
                "rebound_above_sell_10_20m_pct": _threshold_contract(
                    name="rebound_above_sell_10_20m_pct",
                    static_fallback_value=RECOVERY_WATCH_REBOUND_ABOVE_SELL_FLOOR_PCT,
                    dynamic_threshold_value=sell_threshold,
                    sample_count=len(sell_samples),
                    sample_floor=2,
                    threshold_source="post_sell_rebound_above_sell_p75",
                ),
                "rebound_above_buy_10_20m_pct": _threshold_contract(
                    name="rebound_above_buy_10_20m_pct",
                    static_fallback_value=RECOVERY_CONFIRMED_REBOUND_ABOVE_BUY_FLOOR_PCT,
                    dynamic_threshold_value=buy_threshold,
                    sample_count=len(buy_samples),
                    sample_floor=2,
                    threshold_source="post_sell_rebound_above_buy_p75",
                ),
            },
        },
        "rebound_above_sell_rate": above_sell,
        "rebound_above_buy_rate": above_buy,
    }


def _load_source_summary(target_date: str) -> dict[str, Any]:
    buy = _load_json(_json_report_path("buy_funnel_sentinel", target_date))
    hold = _load_json(_json_report_path("holding_exit_sentinel", target_date))
    market = _load_json(_market_regime_path())
    market_breadth = _load_json(_market_panic_breadth_path(target_date))
    panic_breadth = (
        (market_breadth or {}).get("panic_breadth")
        if isinstance(market_breadth, dict)
        else {}
    )
    return {
        "buy_funnel_sentinel": {
            "path": str(_json_report_path("buy_funnel_sentinel", target_date)),
            "exists": _json_report_path("buy_funnel_sentinel", target_date).exists(),
            "primary": ((buy or {}).get("classification") or {}).get("primary") if isinstance(buy, dict) else None,
            "followup_route": ((buy or {}).get("followup") or {}).get("route") if isinstance(buy, dict) else None,
        },
        "holding_exit_sentinel": {
            "path": str(_json_report_path("holding_exit_sentinel", target_date)),
            "exists": _json_report_path("holding_exit_sentinel", target_date).exists(),
            "primary": ((hold or {}).get("classification") or {}).get("primary") if isinstance(hold, dict) else None,
            "followup_route": ((hold or {}).get("followup") or {}).get("route") if isinstance(hold, dict) else None,
            "sell_execution_scope": ((hold or {}).get("classification") or {}).get("sell_execution_scope") if isinstance(hold, dict) else None,
        },
        "market_regime": {
            "path": str(_market_regime_path()),
            "exists": _market_regime_path().exists(),
            "risk_state": market.get("risk_state") if isinstance(market, dict) else None,
            "allow_swing_entry": market.get("allow_swing_entry") if isinstance(market, dict) else None,
            "swing_score": market.get("swing_score") if isinstance(market, dict) else None,
        },
        "market_panic_breadth": {
            "path": str(_market_panic_breadth_path(target_date)),
            "exists": _market_panic_breadth_path(target_date).exists(),
            "as_of": market_breadth.get("as_of") if isinstance(market_breadth, dict) else None,
            "source_quality_status": ((market_breadth or {}).get("source_quality") or {}).get("status")
            if isinstance(market_breadth, dict)
            else None,
            "risk_off_advisory": panic_breadth.get("risk_off_advisory") if isinstance(panic_breadth, dict) else False,
            "single_market_risk_off_advisory": panic_breadth.get("single_market_risk_off_advisory")
            if isinstance(panic_breadth, dict)
            else False,
            "weighted_market_breadth": panic_breadth.get("weighted_market_breadth")
            if isinstance(panic_breadth, dict)
            else {},
            "industry_breadth": panic_breadth.get("industry_breadth") if isinstance(panic_breadth, dict) else {},
            "market_indices": panic_breadth.get("market_indices") if isinstance(panic_breadth, dict) else {},
            "reasons": panic_breadth.get("reasons") if isinstance(panic_breadth, dict) else [],
        },
    }


def _microstructure_market_context(microstructure_detector: dict[str, Any], source_summary: dict[str, Any]) -> dict[str, Any]:
    market = source_summary.get("market_regime") if isinstance(source_summary.get("market_regime"), dict) else {}
    market_breadth = (
        source_summary.get("market_panic_breadth")
        if isinstance(source_summary.get("market_panic_breadth"), dict)
        else {}
    )
    risk_state = _safe_str(market.get("risk_state") or "UNKNOWN").upper()
    evaluated_count = _safe_int(microstructure_detector.get("evaluated_symbol_count"), 0)
    risk_off_count = _safe_int(microstructure_detector.get("risk_off_advisory_count"), 0)
    risk_off_ratio = _ratio(risk_off_count, evaluated_count)
    risk_off_ratio_threshold = _quantile_float(
        [100.0 if idx < risk_off_count else 0.0 for idx in range(evaluated_count)],
        MICRO_RISK_OFF_RATIO_QUANTILE,
    )
    if risk_off_ratio_threshold is not None:
        risk_off_ratio_threshold = max(risk_off_ratio_threshold, MICRO_RISK_OFF_RATIO_FLOOR_PCT)
    evaluated_contract = _threshold_contract(
        name="microstructure_evaluated_symbol_count",
        static_fallback_value=MICRO_MARKET_BREADTH_SYMBOL_FLOOR,
        dynamic_threshold_value=evaluated_count if evaluated_count else None,
        sample_count=evaluated_count,
        sample_floor=MICRO_MARKET_BREADTH_SYMBOL_FLOOR,
        threshold_source="same_day_evaluated_universe_coverage",
    )
    risk_off_contract = _threshold_contract(
        name="microstructure_risk_off_advisory_ratio_pct",
        static_fallback_value=MICRO_RISK_OFF_RATIO_FLOOR_PCT,
        dynamic_threshold_value=risk_off_ratio_threshold,
        sample_count=evaluated_count,
        sample_floor=MICRO_MARKET_BREADTH_SYMBOL_FLOOR,
        threshold_source="same_day_microstructure_risk_off_ratio_p95",
    )
    live_breadth_risk_off = bool(market_breadth.get("risk_off_advisory"))
    market_confirms = risk_state == "RISK_OFF"
    breadth_confirms = (
        bool(evaluated_contract["sample_ready"])
        and risk_off_ratio_threshold is not None
        and risk_off_ratio >= risk_off_ratio_threshold
    )
    micro_confirmed = risk_off_count > 0 and (market_confirms or breadth_confirms)
    confirmed = micro_confirmed or live_breadth_risk_off
    local_only = risk_off_count > 0 and not confirmed
    reasons: list[str] = []
    if market_confirms:
        reasons.append("market_regime_risk_off")
    if live_breadth_risk_off:
        reasons.append("market_panic_breadth_risk_off")
    if breadth_confirms:
        reasons.append("micro_breadth_risk_off_ratio_confirmed")
    if local_only:
        reasons.append("micro_risk_off_unconfirmed_by_market_or_breadth")
    if evaluated_count < MICRO_MARKET_BREADTH_SYMBOL_FLOOR:
        reasons.append("micro_evaluated_symbol_count_below_breadth_floor")
    if risk_state in {"RISK_ON", "NEUTRAL"} and risk_off_count > 0:
        reasons.append("market_regime_not_risk_off")
    if risk_state in {"", "UNKNOWN", "NONE"}:
        reasons.append("market_regime_snapshot_missing_or_unknown")
    return {
        "metric_role": "source_quality_gate",
        "decision_authority": "source_quality_only",
        "window_policy": "intraday_observe_only",
        "sample_floor": MICRO_MARKET_BREADTH_SYMBOL_FLOOR,
        "primary_decision_metric": "confirmed_risk_off_advisory",
        "source_quality_gate": "microstructure risk_off requires market RISK_OFF or broad evaluated-symbol confirmation",
        "forbidden_uses": [
            "runtime_threshold_apply",
            "order_submit",
            "auto_sell",
            "bot_restart",
            "provider_route_change",
        ],
        "market_risk_state": risk_state or "UNKNOWN",
        "allow_swing_entry": market.get("allow_swing_entry"),
        "swing_score": market.get("swing_score"),
        "market_panic_breadth_source": market_breadth.get("path"),
        "market_panic_breadth_as_of": market_breadth.get("as_of"),
        "market_panic_breadth_source_quality_status": market_breadth.get("source_quality_status"),
        "market_panic_breadth_risk_off_advisory": live_breadth_risk_off,
        "market_panic_breadth_single_market_risk_off_advisory": bool(
            market_breadth.get("single_market_risk_off_advisory")
        ),
        "market_panic_breadth_weighted": market_breadth.get("weighted_market_breadth") or {},
        "market_panic_breadth_industry_breadth": market_breadth.get("industry_breadth") or {},
        "market_panic_breadth_indices": market_breadth.get("market_indices") or {},
        "evaluated_symbol_count": evaluated_count,
        "risk_off_advisory_count": risk_off_count,
        "risk_off_advisory_ratio_pct": risk_off_ratio,
        "breadth_symbol_floor": MICRO_MARKET_BREADTH_SYMBOL_FLOOR,
        "breadth_risk_off_ratio_floor_pct": MICRO_RISK_OFF_RATIO_FLOOR_PCT,
        "threshold_contract": {
            "threshold_mode": "dynamic_quantile"
            if evaluated_contract["sample_ready"] and risk_off_contract["sample_ready"]
            else "insufficient_sample",
            "source_quality_blockers": []
            if evaluated_contract["sample_ready"] and risk_off_contract["sample_ready"]
            else ["insufficient_quantile_baseline"],
            "thresholds": {
                "microstructure_evaluated_symbol_count": evaluated_contract,
                "microstructure_risk_off_advisory_ratio_pct": risk_off_contract,
            },
        },
        "market_confirms_risk_off": market_confirms,
        "breadth_confirms_risk_off": breadth_confirms,
        "confirmed_micro_risk_off_advisory": micro_confirmed,
        "confirmed_risk_off_advisory": confirmed,
        "portfolio_local_risk_off_only": local_only,
        "reasons": reasons,
    }


def _resolve_panic_state(
    panic_metrics: dict[str, Any],
    active_recovery: dict[str, Any],
    post_sell_recovery: dict[str, Any],
    microstructure_detector: dict[str, Any] | None = None,
    microstructure_market_context: dict[str, Any] | None = None,
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    micro = microstructure_detector if isinstance(microstructure_detector, dict) else {}
    micro_context = microstructure_market_context if isinstance(microstructure_market_context, dict) else {}
    raw_micro_risk_off = _safe_int(micro.get("risk_off_advisory_count"), 0) > 0
    micro_risk_off = bool(micro_context.get("confirmed_micro_risk_off_advisory"))
    market_breadth_risk_off = bool(micro_context.get("market_panic_breadth_risk_off_advisory"))
    micro_recovery_watch = _safe_int(micro.get("recovery_candidate_count"), 0) > 0
    micro_recovery_confirmed = _safe_int(micro.get("recovery_confirmed_count"), 0) > 0
    portfolio_stop_loss_cluster = bool(panic_metrics.get("panic_detected"))
    confirmed_panic = portfolio_stop_loss_cluster and (micro_risk_off or market_breadth_risk_off)
    risk_off_active = micro_risk_off or market_breadth_risk_off
    market_breadth_only_risk_off = (
        market_breadth_risk_off
        and not raw_micro_risk_off
        and not portfolio_stop_loss_cluster
    )
    if (
        not portfolio_stop_loss_cluster
        and not micro_risk_off
        and not market_breadth_risk_off
        and not micro_recovery_watch
        and not micro_recovery_confirmed
    ):
        reasons.append("panic thresholds not breached")
        if raw_micro_risk_off:
            reasons.append("microstructure risk_off unconfirmed by market/breadth context")
        return "NORMAL", reasons
    if portfolio_stop_loss_cluster:
        reasons.append("portfolio stop-loss cluster observed")
    if portfolio_stop_loss_cluster and not confirmed_panic:
        reasons.append("portfolio stop-loss cluster unconfirmed by market/breadth context")
    if confirmed_panic:
        reasons.append("panic thresholds breached with market/microstructure confirmation")
    if micro_risk_off:
        reasons.append("microstructure risk_off advisory confirmed by market/breadth context")
    if market_breadth_risk_off:
        reasons.append("live market panic breadth risk_off advisory")
    elif raw_micro_risk_off:
        reasons.append("microstructure risk_off unconfirmed by market/breadth context")
    active_avg = active_recovery.get("avg_unrealized_profit_rate_pct")
    active_win_rate = active_recovery.get("win_rate_pct")
    post_sell_above_sell = _safe_float(post_sell_recovery.get("rebound_above_sell_10_20m_pct"), 0.0) or 0.0
    post_sell_above_buy = _safe_float(post_sell_recovery.get("rebound_above_buy_10_20m_pct"), 0.0) or 0.0
    active_thresholds = ((active_recovery.get("threshold_contract") or {}).get("thresholds") or {})
    post_sell_thresholds = ((post_sell_recovery.get("threshold_contract") or {}).get("thresholds") or {})
    active_avg_contract = active_thresholds.get("active_avg_unrealized_profit_rate_pct") or {}
    active_win_contract = active_thresholds.get("active_win_rate_pct") or {}
    sell_rebound_contract = post_sell_thresholds.get("rebound_above_sell_10_20m_pct") or {}
    buy_rebound_contract = post_sell_thresholds.get("rebound_above_buy_10_20m_pct") or {}
    active_avg_threshold = _safe_float(active_avg_contract.get("dynamic_threshold_value"), None)
    active_win_threshold = _safe_float(active_win_contract.get("dynamic_threshold_value"), None)
    sell_rebound_threshold = _safe_float(sell_rebound_contract.get("dynamic_threshold_value"), None)
    buy_rebound_threshold = _safe_float(buy_rebound_contract.get("dynamic_threshold_value"), None)
    active_confirmed = (
        active_recovery.get("profit_sample", 0) > 0
        and active_win_rate is not None
        and active_avg is not None
        and bool(active_avg_contract.get("sample_ready"))
        and bool(active_win_contract.get("sample_ready"))
        and active_win_threshold is not None
        and active_avg_threshold is not None
        and active_win_rate >= active_win_threshold
        and active_avg >= active_avg_threshold
    )
    post_sell_confirmed = (
        bool(buy_rebound_contract.get("sample_ready"))
        and buy_rebound_threshold is not None
        and post_sell_above_buy >= buy_rebound_threshold
    )
    micro_confirmed_allowed = micro_recovery_confirmed and not risk_off_active
    if active_confirmed or post_sell_confirmed or micro_confirmed_allowed:
        reasons.append("recovery confirmed by active sim/probe or post-sell rebound above buy")
        return "RECOVERY_CONFIRMED", reasons
    if micro_recovery_confirmed and risk_off_active:
        reasons.append("microstructure recovery confirmed but market risk-off remains")
    active_watch = (
        active_avg is not None
        and bool(active_avg_contract.get("sample_ready"))
        and active_avg_threshold is not None
        and active_avg >= active_avg_threshold
    )
    post_sell_watch = (
        bool(sell_rebound_contract.get("sample_ready"))
        and sell_rebound_threshold is not None
        and post_sell_above_sell >= sell_rebound_threshold
    )
    if active_watch or post_sell_watch or micro_recovery_watch or micro_recovery_confirmed:
        reasons.append("recovery watch triggered by active sim/probe or post-sell rebound above sell")
        return "RECOVERY_WATCH", reasons
    if market_breadth_only_risk_off:
        reasons.append("market breadth risk-off watch without panic confirmation")
        return "RECOVERY_WATCH", reasons
    if portfolio_stop_loss_cluster and not confirmed_panic:
        reasons.append("portfolio-local stop-loss cluster watch without panic confirmation")
        return "RECOVERY_WATCH", reasons
    reasons.append("recovery conditions not yet met")
    return "PANIC_SELL", reasons


def _risk_regime_gate(
    panic_state: str,
    panic_metrics: dict[str, Any],
    microstructure_market_context: dict[str, Any],
) -> dict[str, Any]:
    threshold_contract = panic_metrics.get("threshold_contract") if isinstance(panic_metrics.get("threshold_contract"), dict) else {}
    micro_contract = (
        microstructure_market_context.get("threshold_contract")
        if isinstance(microstructure_market_context.get("threshold_contract"), dict)
        else {}
    )
    blockers = list(threshold_contract.get("source_quality_blockers") or []) + list(
        micro_contract.get("source_quality_blockers") or []
    )
    if panic_state == "PANIC_SELL":
        state = "confirmed_panic"
    elif panic_state == "RECOVERY_CONFIRMED":
        state = "recovery_confirmed"
    elif panic_state == "RECOVERY_WATCH":
        state = "watch"
    elif blockers and bool(panic_metrics.get("real_exit_count")):
        state = "source_quality_blocked"
    else:
        state = "normal"
    mode = "dynamic_quantile"
    if blockers:
        mode = "insufficient_sample"
    return {
        "risk_regime_gate_state": state,
        "risk_regime_gate_authority": "source_quality_only",
        "risk_regime_threshold_mode": mode,
        "source_quality_blockers": sorted(set(str(item) for item in blockers if str(item))),
        "confirmed_evidence_count": 1 if state == "confirmed_panic" else 0,
    }


def _panic_regime_mode(panic_state: str) -> str:
    if panic_state == "RECOVERY_CONFIRMED":
        return "RECOVERY_CONFIRMED"
    if panic_state == "RECOVERY_WATCH":
        return "STABILIZING"
    if panic_state == "PANIC_SELL":
        return "PANIC_DETECTED"
    return "NORMAL"


def _panic_regime_contract(mode: str) -> dict[str, Any]:
    allowed_actions_by_mode = {
        "NORMAL": ["use_existing_selected_runtime_family"],
        "PANIC_DETECTED": [
            "record_ai_buy_decision_only",
            "candidate_entry_pre_submit_freeze",
            "candidate_entry_order_cancel_design",
            "scale_in_block_candidate",
        ],
        "STABILIZING": [
            "observe_minimum_stabilization_window",
            "observe_ofi_spread_low_retest_recovery",
            "sim_probe_only_recovery_candidate",
        ],
        "RECOVERY_CONFIRMED": [
            "postclose_partial_restore_candidate",
            "bounded_next_preopen_review",
        ],
    }
    return {
        "metric_role": "risk_regime_state",
        "decision_authority": "source_quality_only",
        "window_policy": "same_day_intraday_light + postclose_attribution + next_preopen_apply",
        "sample_floor": "panic report freshness <= 5m; microstructure breadth floor when used",
        "primary_decision_metric": "source_quality_adjusted_avoided_loss_vs_missed_upside_ev_pct",
        "source_quality_gate": "panic provenance + real/sim/probe split + market/breadth confirmation",
        "panic_confirmation_policy": "portfolio stop-loss clusters are evidence; PANIC_DETECTED requires market or microstructure confirmation",
        "runtime_effect": "report_only_no_mutation",
        "allowed_runtime_apply": False,
        "mode": mode,
        "allowed_actions": allowed_actions_by_mode.get(mode, []),
        "owner_split": {
            "v2_0": "panic_entry_freeze_guard.entry_pre_submit_only",
            "v2_1": "entry_order_cancel_guard.separate_workorder_required",
            "v2_2": "holding_exit_panic_context.separate_workorder_required",
            "v2_3": "forced_reduce_or_liquidation.separate_approval_required",
        },
        "forbidden_uses": [
            "auto_sell",
            "stop_loss_relaxation",
            "threshold_relaxation",
            "tp_trailing_mutation",
            "provider_route_change",
            "bot_restart",
            "swing_real_order_enable",
            "broker_order_submit_without_approval",
        ],
    }


def _defense_actions(panic_state: str, panic_metrics: dict[str, Any]) -> list[dict[str, Any]]:
    actions = [
        {
            "id": "hard_protect_emergency_delay_forbidden",
            "decision": "enforced",
            "runtime_effect": False,
            "reason": "hard/protect/emergency stop delay is outside panic defense authority",
        },
        {
            "id": "live_threshold_mutation_forbidden",
            "decision": "enforced",
            "runtime_effect": False,
            "reason": "intraday threshold mutation remains blocked",
        },
    ]
    if panic_state == "PANIC_SELL":
        actions.append(
            {
                "id": "entry_relaxation_blocked",
                "decision": "report_only_recommendation",
                "runtime_effect": False,
                "reason": "panic sell state blocks score/spread/fallback relaxation",
            }
        )
    if panic_state in {"RECOVERY_WATCH", "RECOVERY_CONFIRMED"}:
        actions.append(
            {
                "id": "recovery_probe_review",
                "decision": "candidate_only",
                "runtime_effect": False,
                "reason": "recovery evidence may feed bounded sim/probe canary after postclose attribution",
            }
        )
    if panic_metrics.get("confirmation_eligible_exit_count", 0) > 0:
        actions.append(
            {
                "id": "soft_trailing_flow_confirmation_review",
                "decision": "candidate_only",
                "runtime_effect": False,
                "reason": "only soft/trailing/flow candidates may receive a future one-time confirmation window",
            }
        )
    return actions


def _canary_candidates(panic_state: str, panic_metrics: dict[str, Any], active_recovery: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "family": "panic_entry_freeze_guard",
            "status": "report_only_candidate" if panic_state != "NORMAL" else "inactive_no_panic",
            "allowed_runtime_apply": False,
            "next_owner": "postclose_threshold_cycle",
            "guard": "PANIC_SELL blocks entry relaxation; recovery probe must be separate from threshold relaxation",
        },
        {
            "family": "panic_stop_confirmation",
            "status": "report_only_candidate" if panic_metrics.get("confirmation_eligible_exit_count", 0) else "hold_no_eligible_exit",
            "allowed_runtime_apply": False,
            "next_owner": "postclose_holding_exit_attribution",
            "guard": "hard/protect/emergency stops excluded; soft/trailing/flow only; one-time 20-60s future canary",
        },
        {
            "family": "panic_rebound_probe",
            "status": "report_only_candidate" if panic_state == "RECOVERY_CONFIRMED" else "hold_until_recovery_confirmed",
            "allowed_runtime_apply": False,
            "next_owner": "postclose_threshold_cycle",
            "guard": "sim/probe only with actual_order_submitted=false and broker_order_forbidden=true",
            "provenance_check_passed": bool((active_recovery.get("provenance_check") or {}).get("passed", False)),
        },
        {
            "family": "panic_attribution_pack",
            "status": "active_report_only",
            "allowed_runtime_apply": False,
            "next_owner": "trade_lifecycle_attribution",
            "guard": "closed PnL must be read with forward returns and active sim/probe recovery",
        },
    ]


def build_panic_sell_defense_report(
    target_date: str,
    *,
    as_of: datetime | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    events = _load_jsonl(_pipeline_events_path(target_date))
    event_datetimes = [dt for row in events for dt in [_parse_dt(row.get("emitted_at"))] if dt is not None]
    latest_dt = max(event_datetimes) if event_datetimes else None
    if as_of is None:
        as_of = datetime.now()
    panic_metrics = _summarize_exit_metrics(events, as_of=as_of)
    active_recovery = _summarize_active_recovery()
    post_sell_recovery = _post_sell_recovery_metrics(target_date)
    microstructure_detector = summarize_microstructure_detector_from_events(events, as_of=as_of)
    source_summary = _load_source_summary(target_date)
    microstructure_market_context = _microstructure_market_context(microstructure_detector, source_summary)
    panic_state, reasons = _resolve_panic_state(
        panic_metrics,
        active_recovery,
        post_sell_recovery,
        microstructure_detector,
        microstructure_market_context,
    )
    panic_regime_mode = _panic_regime_mode(panic_state)
    risk_regime_gate = _risk_regime_gate(panic_state, panic_metrics, microstructure_market_context)
    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": "panic_sell_defense",
        "target_date": target_date,
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "as_of": as_of.isoformat(timespec="seconds"),
        "latest_event_at": latest_dt.isoformat(timespec="seconds") if latest_dt else None,
        "dry_run": bool(dry_run),
        "policy": {
            "report_only": True,
            "runtime_effect": "report_only_no_mutation",
            "live_runtime_effect": False,
            "forbidden_automations": FORBIDDEN_AUTOMATIONS,
        },
        "panic_state": panic_state,
        "panic_regime_mode": panic_regime_mode,
        "risk_regime_gate": risk_regime_gate,
        "risk_regime_gate_state": risk_regime_gate["risk_regime_gate_state"],
        "risk_regime_gate_authority": risk_regime_gate["risk_regime_gate_authority"],
        "risk_regime_threshold_mode": risk_regime_gate["risk_regime_threshold_mode"],
        "panic_state_reasons": reasons,
        "panic_regime_contract": _panic_regime_contract(panic_regime_mode),
        "panic_metrics": panic_metrics,
        "recovery_metrics": {
            "active_sim_probe": active_recovery,
            "post_sell_feedback": post_sell_recovery,
        },
        "microstructure_detector": microstructure_detector,
        "microstructure_market_context": microstructure_market_context,
        "defense_actions": _defense_actions(panic_state, panic_metrics),
        "canary_candidates": _canary_candidates(panic_state, panic_metrics, active_recovery),
        "source_summary": source_summary,
        "qna_policy": {
            "panic_detection_threshold": "portfolio stop-loss cluster uses rolling intraday quantile evidence only; PANIC_DETECTED requires market or confirmed microstructure risk-off context",
            "should_delay_stop_loss": "no for hard/protect/emergency; future candidate only for soft/trailing/flow",
            "new_buy_during_panic": "no threshold relaxation; route recovery evidence to separate probe/counterfactual",
            "swing_behavior": "dry-run/probe only unless separate approval artifact exists",
            "performance_read": "closed PnL, forward return, and active sim/probe recovery must be read separately",
        },
    }


def _fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return str(value)


def build_markdown(report: dict[str, Any]) -> str:
    panic = report["panic_metrics"]
    active = report["recovery_metrics"]["active_sim_probe"]
    post_sell = report["recovery_metrics"]["post_sell_feedback"]
    micro = report.get("microstructure_detector") if isinstance(report.get("microstructure_detector"), dict) else {}
    micro_market = (
        report.get("microstructure_market_context")
        if isinstance(report.get("microstructure_market_context"), dict)
        else {}
    )
    lines = [
        f"# Panic Sell Defense {report['target_date']}",
        "",
        "## 판정",
        "",
        f"- panic_state: `{report['panic_state']}`",
        f"- panic_regime_mode: `{report.get('panic_regime_mode', '-')}`",
        f"- risk_regime_gate_state: `{report.get('risk_regime_gate_state', '-')}`",
        f"- risk_regime_threshold_mode: `{report.get('risk_regime_threshold_mode', '-')}`",
        f"- panic_confirmation_policy: `{(report.get('panic_regime_contract') or {}).get('panic_confirmation_policy', '-')}`",
        f"- report_only: `{str(report['policy']['report_only']).lower()}`",
        f"- runtime_effect: `{report['policy']['runtime_effect']}`",
        f"- as_of: `{report['as_of']}`",
        f"- latest_event_at: `{report.get('latest_event_at') or '-'}`",
        f"- reasons: `{'; '.join(report.get('panic_state_reasons') or [])}`",
        "",
        "## 패닉 지표",
        "",
        f"- panic_decision_basis: `{panic.get('panic_decision_basis', '-')}`",
        f"- real_exit_provenance_required: `{str(panic.get('real_exit_provenance_required', False)).lower()}`",
        f"- real_exit_count: `{panic['real_exit_count']}`",
        f"- non_real_exit_count: `{panic['non_real_exit_count']}`",
        f"- unproven_exit_count: `{panic.get('unproven_exit_count', 0)}`",
        f"- sim_probe_exit_excluded_from_panic: `{str(panic.get('sim_probe_exit_excluded_from_panic', False)).lower()}`",
        f"- stop_loss_exit_count: `{panic['stop_loss_exit_count']}`",
        f"- current_30m_stop_loss_exit_count: `{panic['current_30m_stop_loss_exit_count']}`",
        f"- max_rolling_30m_stop_loss_exit_count: `{panic['max_rolling_30m_stop_loss_exit_count']}`",
        f"- rolling_30m_stop_loss_count_quantile: `{_fmt(panic.get('rolling_30m_stop_loss_count_quantile'))}`",
        f"- rolling_30m_stop_loss_count_quantile_threshold: `{_fmt(panic.get('rolling_30m_stop_loss_count_quantile_threshold'))}`",
        f"- rolling_30m_stop_loss_count_sample: `{panic.get('rolling_30m_stop_loss_count_sample', 0)}`",
        f"- rolling_30m_stop_loss_count_sample_ready: `{str(panic.get('rolling_30m_stop_loss_count_sample_ready', False)).lower()}`",
        f"- panic_threshold_mode: `{((panic.get('threshold_contract') or {}).get('threshold_mode') or '-')}`",
        f"- panic_source_quality_blockers: `{'; '.join((panic.get('threshold_contract') or {}).get('source_quality_blockers') or []) or '-'}`",
        f"- stop_loss_exit_ratio_pct: `{_fmt(panic['stop_loss_exit_ratio_pct'])}`",
        f"- avg_exit_profit_rate_pct: `{_fmt(panic['avg_exit_profit_rate_pct'])}`",
        f"- confirmation_eligible_exit_count: `{panic['confirmation_eligible_exit_count']}`",
        f"- never_delay_exit_count: `{panic['never_delay_exit_count']}`",
        "",
        "## 회복 지표",
        "",
        f"- active_positions: `{active['active_positions']}`",
        f"- active_profit_sample: `{active['profit_sample']}`",
        f"- active_avg_unrealized_profit_rate_pct: `{_fmt(active['avg_unrealized_profit_rate_pct'])}`",
        f"- active_win_rate_pct: `{_fmt(active['win_rate_pct'])}`",
        f"- sim_probe_provenance_passed: `{str((active.get('provenance_check') or {}).get('passed', False)).lower()}`",
        f"- post_sell_rebound_above_sell_10_20m_pct: `{_fmt(post_sell['rebound_above_sell_10_20m_pct'])}`",
        f"- post_sell_rebound_above_buy_10_20m_pct: `{_fmt(post_sell['rebound_above_buy_10_20m_pct'])}`",
        "",
        "## Microstructure Detector",
        "",
        f"- evaluated_symbol_count: `{micro.get('evaluated_symbol_count', 0)}`",
        f"- risk_off_advisory_count: `{micro.get('risk_off_advisory_count', 0)}`",
        f"- allow_new_long_false_count: `{micro.get('allow_new_long_false_count', 0)}`",
        f"- panic_signal_count: `{micro.get('panic_signal_count', 0)}`",
        f"- recovery_candidate_count: `{micro.get('recovery_candidate_count', 0)}`",
        f"- recovery_confirmed_count: `{micro.get('recovery_confirmed_count', 0)}`",
        f"- missing_orderbook_count: `{micro.get('missing_orderbook_count', 0)}`",
        f"- degraded_orderbook_count: `{micro.get('degraded_orderbook_count', 0)}`",
        f"- max_panic_score: `{_fmt((micro.get('metrics') or {}).get('max_panic_score') if isinstance(micro.get('metrics'), dict) else 0.0)}`",
        f"- max_recovery_score: `{_fmt((micro.get('metrics') or {}).get('max_recovery_score') if isinstance(micro.get('metrics'), dict) else 0.0)}`",
        f"- micro_cusum_triggered_symbol_count: `{(micro.get('micro_cusum_observer') or {}).get('triggered_symbol_count', 0) if isinstance(micro.get('micro_cusum_observer'), dict) else 0}`",
        f"- micro_consensus_pass_symbol_count: `{(micro.get('micro_cusum_observer') or {}).get('consensus_pass_symbol_count', 0) if isinstance(micro.get('micro_cusum_observer'), dict) else 0}`",
        f"- micro_cusum_decision_authority: `{(micro.get('micro_cusum_observer') or {}).get('decision_authority', '-') if isinstance(micro.get('micro_cusum_observer'), dict) else '-'}`",
        "",
        "## Microstructure Market Context",
        "",
        f"- market_risk_state: `{micro_market.get('market_risk_state', '-')}`",
        f"- market_panic_breadth_as_of: `{micro_market.get('market_panic_breadth_as_of') or '-'}`",
        f"- market_panic_breadth_source_quality_status: `{micro_market.get('market_panic_breadth_source_quality_status') or '-'}`",
        f"- market_panic_breadth_risk_off_advisory: `{str(micro_market.get('market_panic_breadth_risk_off_advisory', False)).lower()}`",
        f"- market_panic_breadth_single_market_risk_off_advisory: `{str(micro_market.get('market_panic_breadth_single_market_risk_off_advisory', False)).lower()}`",
        f"- evaluated_symbol_count: `{micro_market.get('evaluated_symbol_count', 0)}`",
        f"- risk_off_advisory_ratio_pct: `{_fmt(micro_market.get('risk_off_advisory_ratio_pct'))}`",
        f"- confirmed_micro_risk_off_advisory: `{str(micro_market.get('confirmed_micro_risk_off_advisory', False)).lower()}`",
        f"- confirmed_risk_off_advisory: `{str(micro_market.get('confirmed_risk_off_advisory', False)).lower()}`",
        f"- portfolio_local_risk_off_only: `{str(micro_market.get('portfolio_local_risk_off_only', False)).lower()}`",
        f"- source_quality_gate: `{micro_market.get('source_quality_gate', '-')}`",
        f"- reasons: `{'; '.join(micro_market.get('reasons') or [])}`",
        "",
        "## 방어 액션",
        "",
    ]
    lines.extend(
        f"- `{item['id']}`: `{item['decision']}` / runtime_effect=`{str(item['runtime_effect']).lower()}`"
        for item in report["defense_actions"]
    )
    lines.extend(["", "## Canary Candidates", ""])
    lines.extend(
        f"- `{item['family']}`: `{item['status']}`, allowed_runtime_apply=`{str(item['allowed_runtime_apply']).lower()}`"
        for item in report["canary_candidates"]
    )
    lines.extend(["", "## 금지된 자동변경", ""])
    lines.extend(f"- `{item}`" for item in report["policy"]["forbidden_automations"])
    lines.append("")
    return "\n".join(lines)


def save_report_artifacts(report: dict[str, Any]) -> dict[str, str]:
    report_dir = _report_dir()
    report_dir.mkdir(parents=True, exist_ok=True)
    target_date = report["target_date"]
    json_path = report_dir / f"panic_sell_defense_{target_date}.json"
    md_path = report_dir / f"panic_sell_defense_{target_date}.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    md_path.write_text(build_markdown(report), encoding="utf-8")
    return {"json": str(json_path), "markdown": str(md_path)}


def _parse_as_of(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = _parse_dt(value)
    if parsed is None:
        raise ValueError(f"invalid --as-of value: {value}")
    return parsed


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Build report-only panic sell defense report.")
    parser.add_argument("--date", dest="target_date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--as-of", dest="as_of", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--print-json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_panic_sell_defense_report(
        args.target_date,
        as_of=_parse_as_of(args.as_of) if args.as_of else None,
        dry_run=args.dry_run,
    )
    artifacts = {} if args.dry_run else save_report_artifacts(report)
    summary = {
        "status": "success",
        "target_date": args.target_date,
        "panic_state": report["panic_state"],
        "runtime_effect": report["policy"]["runtime_effect"],
        "artifacts": artifacts,
    }
    if args.print_json:
        print(json.dumps(report if args.dry_run else summary, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
