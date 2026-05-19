"""Report-only panic buying attribution.

The report detects intraday panic buying and buying exhaustion from pipeline
events, separates TP/runner counterfactuals from real order behavior, and routes
future runner TP work to approval-required candidates. It never mutates runtime
thresholds or order behavior.
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any

from src.engine.panic_buying_state_detector import summarize_microstructure_detector_from_events
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import read_jsonl


SCHEMA_VERSION = 1
REPORT_DIRNAME = "panic_buying"
TP_RULE_MARKERS = ("take_profit", "trailing", "preset_tp", "익절", "profit")
HARD_PROTECT_EMERGENCY_RULE_MARKERS = (
    "emergency",
    "protect_hard_stop",
    "scalp_hard_stop_pct",
    "scalp_preset_hard_stop_pct",
    "hard_stop",
)
FORBIDDEN_AUTOMATIONS = [
    "live_threshold_runtime_mutation",
    "take_profit_policy_change",
    "trailing_policy_change",
    "auto_sell",
    "auto_buy",
    "bot_restart",
    "provider_route_change",
]


def _pipeline_events_path(target_date: str) -> Path:
    return DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"


def _report_dir() -> Path:
    return DATA_DIR / "report" / REPORT_DIRNAME


def _json_report_path(dirname: str, target_date: str) -> Path:
    return DATA_DIR / "report" / dirname / f"{dirname}_{target_date}.json"


def _market_panic_breadth_path(target_date: str) -> Path:
    return _json_report_path("market_panic_breadth", target_date)


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


def _truthy(value: Any) -> bool:
    return _safe_str(value).lower() in {"1", "true", "yes", "y"}


def _falsey(value: Any) -> bool:
    return _safe_str(value).lower() in {"0", "false", "no", "n"}


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
    """Propagate sim/probe provenance to sparse sibling exit/sell rows."""
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


def _is_hard_protect_emergency_exit(row: dict[str, Any]) -> bool:
    text = _exit_rule_text(row)
    return any(marker in text for marker in HARD_PROTECT_EMERGENCY_RULE_MARKERS)


def _is_tp_like_exit(row: dict[str, Any]) -> bool:
    if _is_hard_protect_emergency_exit(row):
        return False
    text = _exit_rule_text(row)
    profit = _profit_rate(row)
    return any(marker in text for marker in TP_RULE_MARKERS) or (profit is not None and profit > 0)


def _profit_rate(row: dict[str, Any]) -> float | None:
    fields = _event_fields(row)
    return _safe_float(
        fields.get("profit_rate")
        or fields.get("realized_profit_rate")
        or fields.get("return_pct")
        or fields.get("profit_pct")
    )


def _summarize_tp_counterfactual(events: list[dict[str, Any]]) -> dict[str, Any]:
    holding_rows = [row for row in events if _safe_str(row.get("pipeline")) == "HOLDING_PIPELINE"]
    exit_rows = [row for row in holding_rows if "exit" in _safe_str(row.get("stage")) or "sell" in _safe_str(row.get("stage"))]
    non_real_keys = _non_real_attempt_keys(holding_rows)
    real_exit_rows = [
        row
        for row in exit_rows
        if _attempt_key(row) not in non_real_keys and not _is_non_real_observation(row)
    ]
    non_real_exit_rows = [
        row
        for row in exit_rows
        if _attempt_key(row) in non_real_keys or _is_non_real_observation(row)
    ]
    tp_rows = [row for row in real_exit_rows if _is_tp_like_exit(row)]
    non_real_tp_rows = [row for row in non_real_exit_rows if _is_tp_like_exit(row)]
    profits = [value for row in tp_rows for value in [_profit_rate(row)] if value is not None]
    peak_profits = [
        value
        for row in tp_rows
        for value in [_safe_float(_event_fields(row).get("peak_profit"), None)]
        if value is not None
    ]
    trailing_rows = [row for row in tp_rows if "trailing" in _exit_rule_text(row)]
    return {
        "policy": {
            "report_only": True,
            "runtime_effect": "counterfactual_only_no_order_change",
            "does_not_submit_orders": True,
        },
        "real_exit_count": len(real_exit_rows),
        "non_real_exit_count": len(non_real_exit_rows),
        "tp_like_exit_count": len(tp_rows),
        "non_real_tp_like_exit_count": len(non_real_tp_rows),
        "trailing_winner_count": len(trailing_rows),
        "avg_tp_profit_rate_pct": _avg(profits),
        "avg_tp_peak_profit_rate_pct": _avg(peak_profits),
        "candidate_context_count": len(tp_rows) + len(trailing_rows),
        "exit_rule_counts": dict(sorted(Counter(_safe_str(_event_fields(row).get("exit_rule") or "-") for row in tp_rows).items())),
    }


def _load_source_summary(target_date: str) -> dict[str, Any]:
    buy = _load_json(_json_report_path("buy_funnel_sentinel", target_date))
    hold = _load_json(_json_report_path("holding_exit_sentinel", target_date))
    panic_sell = _load_json(_json_report_path("panic_sell_defense", target_date))
    market_breadth = _load_json(_market_panic_breadth_path(target_date))
    panic_breadth = (
        market_breadth.get("panic_breadth")
        if isinstance(market_breadth, dict) and isinstance(market_breadth.get("panic_breadth"), dict)
        else {}
    )
    return {
        "buy_funnel_sentinel": {
            "path": str(_json_report_path("buy_funnel_sentinel", target_date)),
            "exists": _json_report_path("buy_funnel_sentinel", target_date).exists(),
            "primary": ((buy or {}).get("classification") or {}).get("primary") if isinstance(buy, dict) else None,
        },
        "holding_exit_sentinel": {
            "path": str(_json_report_path("holding_exit_sentinel", target_date)),
            "exists": _json_report_path("holding_exit_sentinel", target_date).exists(),
            "primary": ((hold or {}).get("classification") or {}).get("primary") if isinstance(hold, dict) else None,
        },
        "panic_sell_defense": {
            "path": str(_json_report_path("panic_sell_defense", target_date)),
            "exists": _json_report_path("panic_sell_defense", target_date).exists(),
            "panic_state": (panic_sell or {}).get("panic_state") if isinstance(panic_sell, dict) else None,
        },
        "market_panic_breadth": {
            "path": str(_market_panic_breadth_path(target_date)),
            "exists": _market_panic_breadth_path(target_date).exists(),
            "as_of": market_breadth.get("as_of") if isinstance(market_breadth, dict) else None,
            "source_quality_status": ((market_breadth or {}).get("source_quality") or {}).get("status")
            if isinstance(market_breadth, dict)
            else None,
            "risk_on_advisory": bool(panic_breadth.get("risk_on_advisory")),
            "risk_off_advisory": bool(panic_breadth.get("risk_off_advisory")),
            "single_market_risk_on_advisory": bool(panic_breadth.get("single_market_risk_on_advisory")),
            "single_market_risk_off_advisory": bool(panic_breadth.get("single_market_risk_off_advisory")),
            "weighted_market_breadth": panic_breadth.get("weighted_market_breadth")
            if isinstance(panic_breadth, dict)
            else {},
            "industry_breadth": panic_breadth.get("industry_breadth") if isinstance(panic_breadth, dict) else {},
            "stock_breadth": panic_breadth.get("stock_breadth") if isinstance(panic_breadth, dict) else {},
            "risk_on_reasons": panic_breadth.get("risk_on_reasons") if isinstance(panic_breadth, dict) else [],
        },
    }


def _market_breadth_context(source_summary: dict[str, Any], micro: dict[str, Any]) -> dict[str, Any]:
    market = (
        source_summary.get("market_panic_breadth")
        if isinstance(source_summary.get("market_panic_breadth"), dict)
        else {}
    )
    active_or_watch = _safe_int(micro.get("panic_buy_active_count"), 0) + _safe_int(micro.get("panic_buy_watch_count"), 0)
    source_ok = bool(market.get("exists")) and _safe_str(market.get("source_quality_status")) == "ok"
    risk_on = bool(market.get("risk_on_advisory"))
    reasons: list[str] = []
    if risk_on:
        reasons.append("market_panic_breadth_risk_on")
    if active_or_watch > 0 and not risk_on:
        reasons.append("local_panic_buy_unconfirmed_by_market_breadth")
    if not source_ok:
        reasons.append("market_panic_breadth_source_unavailable")
    return {
        "metric_role": "source_quality_gate",
        "decision_authority": "source_quality_only",
        "runtime_effect": "report_only_no_mutation",
        "market_panic_breadth_source": market.get("path"),
        "market_panic_breadth_as_of": market.get("as_of"),
        "market_panic_breadth_source_quality_status": market.get("source_quality_status"),
        "market_panic_breadth_risk_on_advisory": risk_on,
        "market_panic_breadth_risk_off_advisory": bool(market.get("risk_off_advisory")),
        "market_panic_breadth_single_market_risk_on_advisory": bool(
            market.get("single_market_risk_on_advisory")
        ),
        "market_panic_breadth_single_market_risk_off_advisory": bool(
            market.get("single_market_risk_off_advisory")
        ),
        "market_panic_breadth_weighted": market.get("weighted_market_breadth") or {},
        "market_wide_panic_buy_confirmed": bool(active_or_watch > 0 and risk_on),
        "local_panic_buy_signal_count": active_or_watch,
        "industry_breadth": market.get("industry_breadth") or {},
        "stock_breadth": market.get("stock_breadth") or {},
        "reasons": reasons or ["no market-wide panic-buy confirmation required for NORMAL state"],
        "forbidden_uses": list(dict.fromkeys(FORBIDDEN_AUTOMATIONS + ["order_submit"])),
    }


def _resolve_panic_buy_state(micro: dict[str, Any]) -> tuple[str, list[str]]:
    exhausted = _safe_int(micro.get("exhaustion_confirmed_count"), 0)
    exhaustion_watch = _safe_int(micro.get("exhaustion_candidate_count"), 0)
    active = _safe_int(micro.get("panic_buy_active_count"), 0)
    watch = _safe_int(micro.get("panic_buy_watch_count"), 0)
    if exhausted > 0:
        return "BUYING_EXHAUSTED", [f"exhaustion_confirmed_count={exhausted}"]
    if exhaustion_watch > 0:
        return "EXHAUSTION_WATCH", [f"exhaustion_candidate_count={exhaustion_watch}"]
    if active > 0:
        return "PANIC_BUY", [f"panic_buy_active_count={active}"]
    if watch > 0:
        return "PANIC_BUY_WATCH", [f"panic_buy_watch_count={watch}"]
    return "NORMAL", ["no panic buying threshold breached"]


def _latest_internal_states(micro: dict[str, Any]) -> set[str]:
    signals = micro.get("latest_signals") if isinstance(micro.get("latest_signals"), list) else []
    return {
        _safe_str(item.get("internal_state"))
        for item in signals
        if isinstance(item, dict) and _safe_str(item.get("internal_state"))
    }


def _panic_buy_regime_mode(panic_buy_state: str, micro: dict[str, Any]) -> str:
    internal_states = _latest_internal_states(micro)
    force_exit_runner_count = _safe_int(micro.get("force_exit_runner_count"), 0)
    allow_runner_count = _safe_int(micro.get("allow_runner_count"), 0)
    if "COOLDOWN" in internal_states:
        return "COOLDOWN"
    if panic_buy_state in {"BUYING_EXHAUSTED", "EXHAUSTION_WATCH"} or force_exit_runner_count > 0:
        return "PANIC_BUY_EXHAUSTION"
    if panic_buy_state == "PANIC_BUY" and allow_runner_count > 0:
        return "PANIC_BUY_CONTINUATION"
    if panic_buy_state in {"PANIC_BUY", "PANIC_BUY_WATCH"}:
        return "PANIC_BUY_DETECTED"
    return "NORMAL"


def _panic_buy_regime_contract(mode: str) -> dict[str, Any]:
    actions_by_mode = {
        "NORMAL": ["regular_entry_exit_at_existing_runtime_policy", "fixed_tp_allowed_by_existing_policy"],
        "PANIC_BUY_DETECTED": [
            "report_chase_entry_freeze_candidate",
            "report_partial_tp_runner_candidate",
            "block_only_after_future_approval_artifact",
        ],
        "PANIC_BUY_CONTINUATION": [
            "report_runner_hold_candidate",
            "report_volatility_adjusted_trailing_width_candidate",
            "future_entry_only_pullback_or_rebreak_candidate",
        ],
        "PANIC_BUY_EXHAUSTION": [
            "report_runner_cleanup_or_tight_trailing_candidate",
            "report_new_entry_freeze_candidate",
        ],
        "COOLDOWN": [
            "report_reentry_cooldown_candidate",
            "watch_excessive_pullback_counterfactual",
        ],
    }
    return {
        "metric_role": "risk_regime_state",
        "decision_authority": "source_quality_only",
        "window_policy": "same_day_intraday_light + postclose_attribution + next_preopen_apply",
        "sample_floor": "panic buying report freshness <= 2m intraday or postclose regenerated source bundle",
        "primary_decision_metric": "source_quality_adjusted_runner_vs_fixed_tp_ev_pct",
        "source_quality_gate": (
            "panic buying detector confidence + market/breadth risk-on context + "
            "real/sim/probe split + TP counterfactual provenance"
        ),
        "runtime_effect": "report_only_no_mutation",
        "allowed_runtime_apply": False,
        "mode": mode,
        "allowed_actions": actions_by_mode.get(mode, actions_by_mode["NORMAL"]),
        "owner_split": {
            "V2.0": "panic_buy_runner_tp_canary_existing_position_tp_only",
            "V2.1": "panic_buy_chase_entry_freeze",
            "V2.2": "panic_buy_continuation_trailing_width",
            "V2.3": "panic_buy_exhaustion_runner_cleanup",
            "V2.4": "panic_buy_cooldown_reentry_guard",
        },
        "forbidden_uses": [
            "auto_buy",
            "chase_entry_without_pullback_rebreak_guard",
            "full_market_sell",
            "take_profit_policy_change_without_approval",
            "trailing_policy_change_without_approval",
            "hard_protect_emergency_override",
            "provider_route_change",
            "bot_restart",
            "broker_order_submit_without_approval",
        ],
    }


def _panic_buy_metrics(micro: dict[str, Any]) -> dict[str, Any]:
    metrics = micro.get("metrics") if isinstance(micro.get("metrics"), dict) else {}
    return {
        "evaluated_symbol_count": _safe_int(micro.get("evaluated_symbol_count"), 0),
        "panic_buy_signal_count": _safe_int(micro.get("panic_buy_signal_count"), 0),
        "panic_buy_active_count": _safe_int(micro.get("panic_buy_active_count"), 0),
        "panic_buy_watch_count": _safe_int(micro.get("panic_buy_watch_count"), 0),
        "allow_tp_override_count": _safe_int(micro.get("allow_tp_override_count"), 0),
        "allow_runner_count": _safe_int(micro.get("allow_runner_count"), 0),
        "missing_orderbook_count": _safe_int(micro.get("missing_orderbook_count"), 0),
        "degraded_orderbook_count": _safe_int(micro.get("degraded_orderbook_count"), 0),
        "missing_trade_aggressor_count": _safe_int(micro.get("missing_trade_aggressor_count"), 0),
        "carried_orderbook_snapshot_count": _safe_int(micro.get("carried_orderbook_snapshot_count"), 0),
        "carried_trade_aggressor_snapshot_count": _safe_int(micro.get("carried_trade_aggressor_snapshot_count"), 0),
        "max_panic_buy_score": _safe_float(metrics.get("max_panic_buy_score"), 0.0),
        "avg_confidence": _safe_float(metrics.get("avg_confidence"), 0.0),
    }


def _exhaustion_metrics(micro: dict[str, Any]) -> dict[str, Any]:
    metrics = micro.get("metrics") if isinstance(micro.get("metrics"), dict) else {}
    return {
        "exhaustion_candidate_count": _safe_int(micro.get("exhaustion_candidate_count"), 0),
        "exhaustion_confirmed_count": _safe_int(micro.get("exhaustion_confirmed_count"), 0),
        "force_exit_runner_count": _safe_int(micro.get("force_exit_runner_count"), 0),
        "max_exhaustion_score": _safe_float(metrics.get("max_exhaustion_score"), 0.0),
    }


def _canary_candidates(
    panic_buy_state: str,
    panic_buy_regime_mode: str,
    panic_metrics: dict[str, Any],
    exhaustion_metrics: dict[str, Any],
    tp_counterfactual: dict[str, Any],
) -> list[dict[str, Any]]:
    active = _safe_int(panic_metrics.get("panic_buy_active_count"), 0)
    tp_context = _safe_int(tp_counterfactual.get("candidate_context_count"), 0)
    avg_confidence = _safe_float(panic_metrics.get("avg_confidence"), 0.0) or 0.0
    candidate_ready = panic_buy_state == "PANIC_BUY" and active > 0 and tp_context > 0 and avg_confidence >= 0.55
    status = "report_only_candidate" if candidate_ready else "hold_until_confirmed_panic_buy_with_tp_context"
    if avg_confidence < 0.55 and active > 0:
        status = "hold_low_detector_confidence"
    return [
        {
            "family": "panic_buy_runner_tp_canary",
            "status": status,
            "allowed_runtime_apply": False,
            "next_owner": "future_checklist_approval_required",
            "guard": (
                "report-only V1; future canary must keep hard/protect/emergency stop priority, "
                "receipt/provenance safety, same-stage owner guard, and opportunity-vs-giveback rollback"
            ),
            "source_metrics": {
                "panic_buy_state": panic_buy_state,
                "panic_buy_regime_mode": panic_buy_regime_mode,
                "panic_buy_active_count": active,
                "exhaustion_confirmed_count": _safe_int(exhaustion_metrics.get("exhaustion_confirmed_count"), 0),
                "tp_counterfactual_count": tp_context,
                "avg_confidence": avg_confidence,
            },
        }
    ]


def build_panic_buying_report(
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
    micro = summarize_microstructure_detector_from_events(events, as_of=as_of)
    source_summary = _load_source_summary(target_date)
    market_breadth_context = _market_breadth_context(source_summary, micro)
    panic_buy_state, reasons = _resolve_panic_buy_state(micro)
    panic_buy_regime_mode = _panic_buy_regime_mode(panic_buy_state, micro)
    panic_metrics = _panic_buy_metrics(micro)
    exhaustion = _exhaustion_metrics(micro)
    tp_counterfactual = _summarize_tp_counterfactual(events)
    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": "panic_buying",
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
        "panic_buy_state": panic_buy_state,
        "panic_buy_regime_mode": panic_buy_regime_mode,
        "panic_buy_regime_contract": _panic_buy_regime_contract(panic_buy_regime_mode),
        "panic_buy_state_reasons": reasons,
        "panic_buy_metrics": panic_metrics,
        "exhaustion_metrics": exhaustion,
        "microstructure_detector": micro,
        "market_breadth_context": market_breadth_context,
        "tp_counterfactual_summary": tp_counterfactual,
        "canary_candidates": _canary_candidates(
            panic_buy_state,
            panic_buy_regime_mode,
            panic_metrics,
            exhaustion,
            tp_counterfactual,
        ),
        "source_summary": source_summary,
        "qna_policy": {
            "should_change_take_profit_now": "no; report-only until separate approval artifact and rollback guard exist",
            "panic_buy_is_new_buy_signal": "no; it is runner/TP attribution context for existing long positions",
            "exhaustion_behavior": "future runner cleanup or tight trailing candidate only, no V1 runtime action",
            "performance_read": "closed PnL, TP counterfactual, and detector confidence must be read separately",
        },
    }


def _fmt(value: Any) -> str:
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    return str(value)


def build_markdown(report: dict[str, Any]) -> str:
    panic = report["panic_buy_metrics"]
    exhaustion = report["exhaustion_metrics"]
    tp = report["tp_counterfactual_summary"]
    micro = report.get("microstructure_detector") if isinstance(report.get("microstructure_detector"), dict) else {}
    market = report.get("market_breadth_context") if isinstance(report.get("market_breadth_context"), dict) else {}
    lines = [
        f"# Panic Buying {report['target_date']}",
        "",
        "## 판정",
        "",
        f"- panic_buy_state: `{report['panic_buy_state']}`",
        f"- panic_buy_regime_mode: `{report.get('panic_buy_regime_mode', '-')}`",
        f"- report_only: `{str(report['policy']['report_only']).lower()}`",
        f"- runtime_effect: `{report['policy']['runtime_effect']}`",
        f"- as_of: `{report['as_of']}`",
        f"- latest_event_at: `{report.get('latest_event_at') or '-'}`",
        f"- reasons: `{'; '.join(report.get('panic_buy_state_reasons') or [])}`",
        "",
        "## 패닉바잉 지표",
        "",
        f"- evaluated_symbol_count: `{panic['evaluated_symbol_count']}`",
        f"- panic_buy_active_count: `{panic['panic_buy_active_count']}`",
        f"- panic_buy_watch_count: `{panic['panic_buy_watch_count']}`",
        f"- allow_tp_override_count: `{panic['allow_tp_override_count']}`",
        f"- allow_runner_count: `{panic['allow_runner_count']}`",
        f"- max_panic_buy_score: `{_fmt(panic['max_panic_buy_score'])}`",
        f"- avg_confidence: `{_fmt(panic['avg_confidence'])}`",
        "",
        "## 소진 지표",
        "",
        f"- exhaustion_candidate_count: `{exhaustion['exhaustion_candidate_count']}`",
        f"- exhaustion_confirmed_count: `{exhaustion['exhaustion_confirmed_count']}`",
        f"- force_exit_runner_count: `{exhaustion['force_exit_runner_count']}`",
        f"- max_exhaustion_score: `{_fmt(exhaustion['max_exhaustion_score'])}`",
        "",
        "## TP Counterfactual",
        "",
        f"- tp_like_exit_count: `{tp['tp_like_exit_count']}`",
        f"- trailing_winner_count: `{tp['trailing_winner_count']}`",
        f"- candidate_context_count: `{tp['candidate_context_count']}`",
        f"- avg_tp_profit_rate_pct: `{_fmt(tp['avg_tp_profit_rate_pct'])}`",
        f"- runtime_effect: `{tp['policy']['runtime_effect']}`",
        "",
        "## Microstructure Detector",
        "",
        f"- missing_orderbook_count: `{micro.get('missing_orderbook_count', 0)}`",
        f"- degraded_orderbook_count: `{micro.get('degraded_orderbook_count', 0)}`",
        f"- missing_trade_aggressor_count: `{micro.get('missing_trade_aggressor_count', 0)}`",
        f"- carried_orderbook_snapshot_count: `{micro.get('carried_orderbook_snapshot_count', 0)}`",
        f"- carried_trade_aggressor_snapshot_count: `{micro.get('carried_trade_aggressor_snapshot_count', 0)}`",
        f"- micro_cusum_triggered_symbol_count: `{(micro.get('micro_cusum_observer') or {}).get('triggered_symbol_count', 0) if isinstance(micro.get('micro_cusum_observer'), dict) else 0}`",
        f"- micro_consensus_pass_symbol_count: `{(micro.get('micro_cusum_observer') or {}).get('consensus_pass_symbol_count', 0) if isinstance(micro.get('micro_cusum_observer'), dict) else 0}`",
        f"- micro_cusum_decision_authority: `{(micro.get('micro_cusum_observer') or {}).get('decision_authority', '-') if isinstance(micro.get('micro_cusum_observer'), dict) else '-'}`",
        "",
        "## Market Breadth Context",
        "",
        f"- market_panic_breadth_source_quality_status: `{market.get('market_panic_breadth_source_quality_status') or '-'}`",
        f"- market_panic_breadth_risk_on_advisory: `{str(market.get('market_panic_breadth_risk_on_advisory', False)).lower()}`",
        f"- market_panic_breadth_risk_off_advisory: `{str(market.get('market_panic_breadth_risk_off_advisory', False)).lower()}`",
        f"- market_panic_breadth_single_market_risk_on_advisory: `{str(market.get('market_panic_breadth_single_market_risk_on_advisory', False)).lower()}`",
        f"- market_panic_breadth_single_market_risk_off_advisory: `{str(market.get('market_panic_breadth_single_market_risk_off_advisory', False)).lower()}`",
        f"- market_wide_panic_buy_confirmed: `{str(market.get('market_wide_panic_buy_confirmed', False)).lower()}`",
        f"- market_breadth_decision_authority: `{market.get('decision_authority', '-')}`",
        "",
        "## Canary Candidates",
        "",
    ]
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
    json_path = report_dir / f"panic_buying_{target_date}.json"
    md_path = report_dir / f"panic_buying_{target_date}.md"
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
    parser = argparse.ArgumentParser(description="Build report-only panic buying report.")
    parser.add_argument("--date", dest="target_date", default=datetime.now().strftime("%Y-%m-%d"))
    parser.add_argument("--as-of", dest="as_of", default="")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--print-json", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    report = build_panic_buying_report(
        args.target_date,
        as_of=_parse_as_of(args.as_of) if args.as_of else None,
        dry_run=args.dry_run,
    )
    artifacts = {} if args.dry_run else save_report_artifacts(report)
    summary = {
        "status": "success",
        "target_date": args.target_date,
        "panic_buy_state": report["panic_buy_state"],
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
