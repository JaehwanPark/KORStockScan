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


SCHEMA_VERSION = 1
REPORT_DIRNAME = "panic_sell_defense"
PANIC_WINDOW_MIN = 30
PANIC_STOP_LOSS_COUNT_FLOOR = 5
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
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for raw_line in handle:
            line = raw_line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


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
    stop_times = sorted(
        dt
        for row in events
        if _is_stop_loss_exit(row)
        for dt in [_parse_dt(row.get("emitted_at"))]
        if dt is not None
    )
    if not stop_times:
        return 0
    max_count = 0
    right = 0
    for left, start in enumerate(stop_times):
        while right < len(stop_times) and stop_times[right] <= start + timedelta(minutes=window_min):
            right += 1
        max_count = max(max_count, right - left)
    return max_count


def _summarize_exit_metrics(events: list[dict[str, Any]], *, as_of: datetime | None) -> dict[str, Any]:
    exit_events = [row for row in events if _is_holding_exit_signal(row)]
    holding_events = [row for row in events if _safe_str(row.get("pipeline")) == "HOLDING_PIPELINE"]
    non_real_keys = _non_real_attempt_keys(holding_events)
    real_exits = [
        row
        for row in exit_events
        if _attempt_key(row) not in non_real_keys and not _is_non_real_observation(row)
    ]
    non_real_exits = [
        row
        for row in exit_events
        if _attempt_key(row) in non_real_keys or _is_non_real_observation(row)
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
    stop_loss_ratio = _ratio(len(stop_loss_real), len(real_exits))
    avg_exit_profit = _avg(profits)
    panic_by_count = len(current_window_stop_loss) >= PANIC_STOP_LOSS_COUNT_FLOOR or max_rolling_stop_loss >= PANIC_STOP_LOSS_COUNT_FLOOR
    panic_by_ratio = stop_loss_ratio >= PANIC_STOP_LOSS_RATIO_FLOOR_PCT and (
        avg_exit_profit is not None and avg_exit_profit <= PANIC_AVG_EXIT_PROFIT_CEILING_PCT
    )
    return {
        "real_exit_count": len(real_exits),
        "non_real_exit_count": len(non_real_exits),
        "stop_loss_exit_count": len(stop_loss_real),
        "current_30m_stop_loss_exit_count": len(current_window_stop_loss),
        "max_rolling_30m_stop_loss_exit_count": max_rolling_stop_loss,
        "stop_loss_exit_ratio_pct": stop_loss_ratio,
        "avg_exit_profit_rate_pct": avg_exit_profit,
        "avg_stop_loss_profit_rate_pct": _avg(stop_profits),
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
    return {
        "source_path": str(path),
        "source_exists": path.exists(),
        "soft_stop_total": _safe_int(soft.get("total_soft_stop"), 0) if soft else 0,
        "rebound_above_sell_10_20m_pct": sell_10_20,
        "rebound_above_buy_10_20m_pct": buy_10_20,
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
    live_breadth_risk_off = bool(market_breadth.get("risk_off_advisory"))
    market_confirms = risk_state == "RISK_OFF"
    breadth_confirms = (
        evaluated_count >= MICRO_MARKET_BREADTH_SYMBOL_FLOOR
        and risk_off_ratio >= MICRO_RISK_OFF_RATIO_FLOOR_PCT
    )
    confirmed = (risk_off_count > 0 and (market_confirms or breadth_confirms)) or live_breadth_risk_off
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
        "market_panic_breadth_industry_breadth": market_breadth.get("industry_breadth") or {},
        "market_panic_breadth_indices": market_breadth.get("market_indices") or {},
        "evaluated_symbol_count": evaluated_count,
        "risk_off_advisory_count": risk_off_count,
        "risk_off_advisory_ratio_pct": risk_off_ratio,
        "breadth_symbol_floor": MICRO_MARKET_BREADTH_SYMBOL_FLOOR,
        "breadth_risk_off_ratio_floor_pct": MICRO_RISK_OFF_RATIO_FLOOR_PCT,
        "market_confirms_risk_off": market_confirms,
        "breadth_confirms_risk_off": breadth_confirms,
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
    micro_risk_off = bool(micro_context.get("confirmed_risk_off_advisory"))
    market_breadth_risk_off = bool(micro_context.get("market_panic_breadth_risk_off_advisory"))
    micro_recovery_watch = _safe_int(micro.get("recovery_candidate_count"), 0) > 0
    micro_recovery_confirmed = _safe_int(micro.get("recovery_confirmed_count"), 0) > 0
    risk_off_active = micro_risk_off or market_breadth_risk_off
    if not panic_metrics.get("panic_detected") and not micro_risk_off and not micro_recovery_watch and not micro_recovery_confirmed:
        reasons.append("panic thresholds not breached")
        if raw_micro_risk_off:
            reasons.append("microstructure risk_off unconfirmed by market/breadth context")
        return "NORMAL", reasons
    if panic_metrics.get("panic_detected"):
        reasons.append("panic thresholds breached")
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
    active_confirmed = (
        active_recovery.get("profit_sample", 0) > 0
        and active_win_rate is not None
        and active_avg is not None
        and active_win_rate >= RECOVERY_CONFIRMED_ACTIVE_WIN_RATE_FLOOR_PCT
        and active_avg > RECOVERY_CONFIRMED_ACTIVE_AVG_FLOOR_PCT
    )
    post_sell_confirmed = post_sell_above_buy >= RECOVERY_CONFIRMED_REBOUND_ABOVE_BUY_FLOOR_PCT
    micro_confirmed_allowed = micro_recovery_confirmed and not risk_off_active
    if active_confirmed or post_sell_confirmed or micro_confirmed_allowed:
        reasons.append("recovery confirmed by active sim/probe or post-sell rebound above buy")
        return "RECOVERY_CONFIRMED", reasons
    if micro_recovery_confirmed and risk_off_active:
        reasons.append("microstructure recovery confirmed but market risk-off remains")
    active_watch = active_avg is not None and active_avg > RECOVERY_WATCH_ACTIVE_AVG_FLOOR_PCT
    post_sell_watch = post_sell_above_sell >= RECOVERY_WATCH_REBOUND_ABOVE_SELL_FLOOR_PCT
    if active_watch or post_sell_watch or micro_recovery_watch or micro_recovery_confirmed:
        reasons.append("recovery watch triggered by active sim/probe or post-sell rebound above sell")
        return "RECOVERY_WATCH", reasons
    reasons.append("recovery conditions not yet met")
    return "PANIC_SELL", reasons


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
        f"- report_only: `{str(report['policy']['report_only']).lower()}`",
        f"- runtime_effect: `{report['policy']['runtime_effect']}`",
        f"- as_of: `{report['as_of']}`",
        f"- latest_event_at: `{report.get('latest_event_at') or '-'}`",
        f"- reasons: `{'; '.join(report.get('panic_state_reasons') or [])}`",
        "",
        "## 패닉 지표",
        "",
        f"- real_exit_count: `{panic['real_exit_count']}`",
        f"- non_real_exit_count: `{panic['non_real_exit_count']}`",
        f"- stop_loss_exit_count: `{panic['stop_loss_exit_count']}`",
        f"- current_30m_stop_loss_exit_count: `{panic['current_30m_stop_loss_exit_count']}`",
        f"- max_rolling_30m_stop_loss_exit_count: `{panic['max_rolling_30m_stop_loss_exit_count']}`",
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
        f"- evaluated_symbol_count: `{micro_market.get('evaluated_symbol_count', 0)}`",
        f"- risk_off_advisory_ratio_pct: `{_fmt(micro_market.get('risk_off_advisory_ratio_pct'))}`",
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
