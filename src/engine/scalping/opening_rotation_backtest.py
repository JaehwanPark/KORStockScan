"""Strict retrospective report for the OPENING_ROTATION_1PCT strategy.

This producer does not create a simulator or order path.  It replays only
historical scanner events that contain every field required by the live
deterministic policy, and reports incomplete legacy rows as source-quality
coverage rather than fabricating a decision.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from collections import Counter
from dataclasses import asdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from src.engine.automation.source_quality_clean_baseline import clean_baseline_policy
from src.engine.scalping.opening_rotation import (
    EntryConfig,
    POSITION_TAG,
    entry_time_bucket,
    entry_time_bucket_labels,
    entry_window_version,
    evaluate_entry,
    parse_source_signature,
)
from src.engine.trade_profit import calculate_net_realized_pnl
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import existing_or_gzip_path, open_text_auto

REPORT_TYPE = "opening_rotation_1pct_backtest"
SCHEMA_VERSION = 3
REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE
PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"
POST_SELL_DIR = DATA_DIR / "post_sell"
KST = timezone(timedelta(hours=9))

EXPLICIT_ENTRY_STAGES = {
    "opening_rotation_1pct_observed",
    "opening_rotation_1pct_qualified",
    "opening_rotation_1pct_retag_blocked",
}
UPSTREAM_BLOCK_STAGE = "opening_rotation_1pct_upstream_blocked"
EXACT_LIFECYCLE_STAGES = {
    "order_bundle_submitted",
    "holding_started",
    "opening_rotation_1pct_hold",
    "opening_rotation_1pct_exit_signal",
    "sell_completed",
}
METRIC_CONTRACT_FIELDS = (
    "metric_role",
    "decision_authority",
    "window_policy",
    "sample_floor",
    "primary_decision_metric",
    "source_quality_gate",
    "allowed_runtime_apply",
    "forbidden_uses",
)
EXACT_COMPLETION_CONTRACT = {
    "metric_role": "exact_real_trade_performance_source",
    "decision_authority": "real_execution_observation_only",
    "window_policy": "clean_baseline_completed_trade_event_time",
    "sample_floor": "consumer_owned_no_direct_runtime_authority",
    "primary_decision_metric": "net_profit_rate_and_realized_pnl_krw",
    "source_quality_gate": ("completed_db_status_valid_net_profit_real_broker_receipt"),
}
EXACT_QUALIFICATION_CONTRACT = {
    "metric_role": "bounded_tunable_live_strategy",
    "decision_authority": "operator_requested_real_opening_rotation_1pct",
    "window_policy": "same_day_preopen_configured_observation_and_entry_window_kst",
    "sample_floor": "not_applicable_operator_requested_live_runtime",
    "primary_decision_metric": "cost_aware_net_profit_rate_and_realized_pnl_krw",
    "source_quality_gate": "fresh_quote_trusted_ticks_orderbook_and_minute_candles",
    "allowed_runtime_apply": True,
}
REQUIRED_REPLAY_FIELDS = (
    "source_signature",
    "day_change_pct",
    "curr_price",
    "quote_age_ms",
    "quote_stale",
    "tick_context_stale",
    "tick_context_quality",
    "tick_aggressor_pressure_usable",
    "spread_bp",
    "buy_pressure_10t",
    "tick_aggressor_trusted_count",
    "tick_acceleration_ratio",
    "price_change_10t_pct",
    "volume_ratio_pct",
    "micro_vwap_available",
    "curr_vs_micro_vwap_bp",
    "microstructure_reaction_ask_sweep_score",
    "microstructure_reaction_post_sweep_hold_score",
    "microstructure_reaction_bid_replenishment_score",
    "microstructure_reaction_wall_replenishment_risk_score",
    "microstructure_reaction_vi_proximity_risk",
)
FORBIDDEN_USES = (
    "broker_order_submit",
    "runtime_threshold_mutation",
    "provider_route_change",
    "bot_restart",
    "hard_safety_relaxation",
    "sim_as_real_execution_quality",
    "incomplete_legacy_row_as_performance_sample",
    "ev_promotion_without_consumer_owned_sample_floor",
)


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, "", "-", "None", "none", "null"):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, "", "-", "None", "none", "null"):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _optional_float(value: Any) -> float | None:
    try:
        if value in (None, "", "-", "None", "none", "null"):
            return None
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _first(fields: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = fields.get(key)
        if value not in (None, "", "-", "None", "none", "null", "not_evaluated"):
            return value
    return None


def _parse_event_dt(event: dict[str, Any]) -> datetime | None:
    raw = str(event.get("emitted_at") or event.get("event_time") or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    return (
        parsed.replace(tzinfo=KST) if parsed.tzinfo is None else parsed.astimezone(KST)
    )


def _baseline_dt(policy: dict[str, Any]) -> datetime:
    if not policy.get("enabled", True):
        raise ValueError("clean tuning baseline policy must remain enabled")
    raw = str(policy.get("clean_tuning_baseline_ts_kst") or "").strip()
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError as exc:
        raise ValueError(f"invalid clean tuning baseline timestamp: {raw!r}") from exc
    return (
        parsed.replace(tzinfo=KST) if parsed.tzinfo is None else parsed.astimezone(KST)
    )


def _row_allowed(event_dt: datetime | None, baseline: datetime) -> bool:
    return bool(event_dt and event_dt >= baseline)


def _forbidden_use_tokens(value: Any) -> set[str]:
    if isinstance(value, (list, tuple, set)):
        parts = [str(item) for item in value]
    else:
        parts = re.split(r"[|,/\s]+", str(value or ""))
    return {part.strip().lower() for part in parts if part.strip()}


def _missing_metric_contract_fields(fields: dict[str, Any]) -> list[str]:
    return [key for key in METRIC_CONTRACT_FIELDS if key not in fields]


def _entry_config_snapshot(config: EntryConfig) -> dict[str, Any]:
    snapshot = asdict(config)
    for key, value in tuple(snapshot.items()):
        if hasattr(value, "isoformat"):
            snapshot[key] = value.isoformat()
    return snapshot


def _config_fingerprint(config_snapshot: dict[str, Any]) -> str:
    encoded = json.dumps(
        config_snapshot,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()[:12]


def _flat_performance(rows: list[dict[str, Any]]) -> dict[str, Any]:
    profits = [_safe_float(row.get("profit_rate")) for row in rows]
    notionals = [
        _safe_float(row.get("buy_price")) * _safe_int(row.get("buy_qty"))
        for row in rows
    ]
    notional_total = sum(notionals)
    return {
        "completed_trade_count": len(rows),
        "win_count": sum(1 for value in profits if value > 0),
        "loss_count": sum(1 for value in profits if value < 0),
        "diagnostic_win_rate_pct": (
            round((sum(1 for value in profits if value > 0) / len(profits)) * 100.0, 3)
            if profits
            else None
        ),
        "equal_weight_avg_profit_pct": (
            round(sum(profits) / len(profits), 4) if profits else None
        ),
        "notional_weighted_ev_pct": (
            round(
                sum(profit * notional for profit, notional in zip(profits, notionals))
                / notional_total,
                4,
            )
            if profits and notional_total > 0
            else None
        ),
        "simple_sum_profit_pct": round(sum(profits), 4),
        "realized_pnl_krw": sum(_safe_int(row.get("realized_pnl_krw")) for row in rows),
    }


def _cohort_performance(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_fill_quality: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        fill_quality = str(row.get("entry_fill_quality") or "UNKNOWN")
        by_fill_quality.setdefault(fill_quality, []).append(row)
    combined = _flat_performance(rows)
    combined["performance_by_fill_quality"] = {
        fill_quality: _flat_performance(fill_rows)
        for fill_quality, fill_rows in sorted(by_fill_quality.items())
    }
    combined["combined_fill_quality_ev_suppressed"] = len(by_fill_quality) > 1
    if combined["combined_fill_quality_ev_suppressed"]:
        combined["equal_weight_avg_profit_pct"] = None
        combined["notional_weighted_ev_pct"] = None
    return combined


def _eligible_session_dates(
    target_dates: list[str], baseline: datetime, config: EntryConfig
) -> list[str]:
    eligible: list[str] = []
    for token in target_dates:
        session_date = date.fromisoformat(token)
        if session_date.weekday() >= 5:
            continue
        session_entry_end = datetime.combine(
            session_date,
            config.entry_end,
            tzinfo=KST,
        )
        if session_entry_end < baseline:
            continue
        eligible.append(token)
    return eligible


def _record_key(event: dict[str, Any], fields: dict[str, Any], target_date: str) -> str:
    record_id = event.get("record_id") or fields.get("record_id") or fields.get("id")
    if record_id not in (None, "", "-"):
        return f"{target_date}:record:{record_id}"
    promotion_id = str(fields.get("scanner_promotion_id") or "").strip()
    code = str(event.get("stock_code") or fields.get("stock_code") or "").strip()[:6]
    return f"{target_date}:scanner:{promotion_id or code}"


def _is_legacy_scanner_event(event: dict[str, Any], fields: dict[str, Any]) -> bool:
    if str(event.get("pipeline") or "") != "ENTRY_PIPELINE":
        return False
    stage = str(event.get("stage") or "")
    if stage in EXPLICIT_ENTRY_STAGES:
        return False
    tags = {
        str(fields.get(key) or "").strip().upper()
        for key in ("position_tag", "target_position_tag", "momentum_tag")
    }
    return bool(
        stage == "scalping_scanner_fast_precheck"
        or "SCANNER" in tags
        or fields.get("scanner_promotion_id")
    ) and bool(parse_source_signature(fields.get("source_signature")))


def _canonical_replay_inputs(
    fields: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    source_signature = _first(fields, "source_signature", "scanner_source_signature")
    day_change_pct = _first(fields, "day_change_pct", "fluctuation", "fluctuation_rate")
    curr_price = _first(
        fields,
        "curr_price",
        "current_price",
        "current_price_observed",
        "latest_price",
        "signal_price",
    )
    vwap_distance = _first(fields, "curr_vs_micro_vwap_bp", "micro_vwap_bp")
    values = {
        "source_signature": source_signature,
        "day_change_pct": day_change_pct,
        "curr_price": curr_price,
        "quote_age_ms": _first(fields, "quote_age_ms", "quote_age_at_submit_ms"),
        "quote_stale": _first(fields, "quote_stale"),
        "tick_context_stale": _first(fields, "tick_context_stale"),
        "tick_context_quality": _first(fields, "tick_context_quality"),
        "tick_aggressor_pressure_usable": _first(
            fields,
            "tick_aggressor_pressure_usable",
            "microstructure_reaction_tick_aggressor_pressure_usable",
        ),
        "spread_bp": _first(fields, "spread_bp", "spread_bps"),
        "buy_pressure_10t": _first(fields, "buy_pressure_10t", "buy_pressure"),
        "tick_aggressor_trusted_count": _first(
            fields,
            "tick_aggressor_trusted_count",
            "microstructure_reaction_tick_aggressor_trusted_count",
        ),
        "tick_acceleration_ratio": _first(
            fields, "tick_acceleration_ratio", "tick_accel"
        ),
        "price_change_10t_pct": _first(fields, "price_change_10t_pct"),
        "volume_ratio_pct": _first(fields, "volume_ratio_pct", "volume_ratio"),
        "micro_vwap_available": _first(fields, "micro_vwap_available"),
        "curr_vs_micro_vwap_bp": vwap_distance,
        "microstructure_reaction_ask_sweep_score": _first(
            fields, "microstructure_reaction_ask_sweep_score", "ask_sweep_score"
        ),
        "microstructure_reaction_post_sweep_hold_score": _first(
            fields,
            "microstructure_reaction_post_sweep_hold_score",
            "post_sweep_hold_score",
        ),
        "microstructure_reaction_bid_replenishment_score": _first(
            fields,
            "microstructure_reaction_bid_replenishment_score",
            "bid_replenishment_score",
        ),
        "microstructure_reaction_wall_replenishment_risk_score": _first(
            fields,
            "microstructure_reaction_wall_replenishment_risk_score",
            "wall_replenishment_risk_score",
        ),
        "microstructure_reaction_vi_proximity_risk": _first(
            fields, "microstructure_reaction_vi_proximity_risk", "vi_proximity_risk"
        ),
    }
    missing = {key: value for key, value in values.items() if value is None}
    packet = {
        key: value
        for key, value in values.items()
        if key not in {"source_signature", "day_change_pct"} and value is not None
    }
    packet["quote_stale_threshold_ms"] = (
        _first(fields, "quote_stale_threshold_ms") or 3000
    )
    return values, {"packet": packet, "missing": tuple(missing)}


def _iter_candidate_events(path: Path) -> Iterable[dict[str, Any]]:
    actual_path = existing_or_gzip_path(path)
    if not actual_path.exists():
        return
    with open_text_auto(actual_path) as handle:
        for raw_line in handle:
            if not any(
                token in raw_line
                for token in (
                    "opening_rotation_1pct",
                    "OPENING_ROTATION_1PCT",
                    '"scanner_promotion_id"',
                    '"source_signature"',
                    "holding_started",
                    "sell_completed",
                    "order_bundle_submitted",
                )
            ):
                continue
            try:
                event = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            if isinstance(event, dict):
                yield event


def _date_keys(start_date: str, end_date: str, events_dir: Path) -> list[str]:
    start = date.fromisoformat(start_date)
    end = date.fromisoformat(end_date)
    result: list[str] = []
    for path in sorted(events_dir.glob("pipeline_events_*.jsonl*")):
        token = path.name.replace("pipeline_events_", "").split(".jsonl", 1)[0]
        try:
            parsed = date.fromisoformat(token)
        except ValueError:
            continue
        if start <= parsed <= end and token not in result:
            result.append(token)
    return result


def _post_sell_inventory(
    target_dates: list[str], post_sell_dir: Path
) -> dict[str, Any]:
    counts = Counter()
    tagged_counts = Counter()
    for target_date in target_dates:
        for lane, prefix in (
            ("real", "post_sell_evaluations"),
            ("sim", "sim_post_sell_evaluations"),
        ):
            path = existing_or_gzip_path(
                post_sell_dir / f"{prefix}_{target_date}.jsonl"
            )
            if not path.exists():
                continue
            with open_text_auto(path) as handle:
                for raw_line in handle:
                    try:
                        row = json.loads(raw_line)
                    except json.JSONDecodeError:
                        continue
                    if not isinstance(row, dict):
                        continue
                    counts[lane] += 1
                    if str(row.get("position_tag") or "").upper() == POSITION_TAG:
                        tagged_counts[lane] += 1
    return {
        "real_evaluation_count": counts["real"],
        "sim_evaluation_count": counts["sim"],
        "opening_rotation_real_evaluation_count": tagged_counts["real"],
        "opening_rotation_sim_evaluation_count": tagged_counts["sim"],
        "legacy_rows_used_as_exact_outcomes": 0,
        "reason": "legacy post-sell outcomes start from another strategy entry and cannot label a hypothetical opening-rotation entry",
    }


def build_report(
    *,
    start_date: str,
    end_date: str,
    events_dir: Path = PIPELINE_EVENTS_DIR,
    post_sell_dir: Path = POST_SELL_DIR,
    config: EntryConfig | None = None,
) -> dict[str, Any]:
    config = config or EntryConfig()
    config_snapshot = _entry_config_snapshot(config)
    config_fingerprint = _config_fingerprint(config_snapshot)
    policy = clean_baseline_policy()
    baseline = _baseline_dt(policy)
    target_dates = _date_keys(start_date, end_date, events_dir)
    eligible_session_dates = _eligible_session_dates(target_dates, baseline, config)
    counters = Counter()
    missing_counts = Counter()
    reason_counts = Counter()
    exact_trades: dict[str, dict[str, Any]] = {}
    replay_states: dict[str, dict[str, Any]] = {}
    replay_qualified_keys: set[str] = set()
    replay_qualified: list[dict[str, Any]] = []

    for target_date in target_dates:
        path = events_dir / f"pipeline_events_{target_date}.jsonl"
        for event in _iter_candidate_events(path):
            counters["candidate_lines_parsed"] += 1
            event_dt = _parse_event_dt(event)
            if not _row_allowed(event_dt, baseline):
                counters["clean_baseline_excluded"] += 1
                continue
            fields = (
                event.get("fields") if isinstance(event.get("fields"), dict) else {}
            )
            stage = str(event.get("stage") or "")
            key = _record_key(event, fields, target_date)

            if stage == UPSTREAM_BLOCK_STAGE:
                counters["upstream_block_count"] += 1
                upstream_reason = str(
                    fields.get("upstream_skip_reason") or fields.get("reason") or "-"
                )
                counters[f"upstream_reason:{upstream_reason}"] += 1
                if _truthy(fields.get("opening_rotation_upstream_exact_candidate")):
                    counters["upstream_exact_candidate_block_count"] += 1
                if not _truthy(
                    fields.get("opening_rotation_upstream_exact_candidate_known")
                ):
                    counters["upstream_day_change_missing_count"] += 1
                continue

            if stage in EXPLICIT_ENTRY_STAGES:
                counters[f"exact_stage_{stage}"] += 1
                reason_counts[
                    str(fields.get("reason") or fields.get("block_reason") or "-")
                ] += 1
                trade = exact_trades.setdefault(
                    key,
                    {
                        "record_key": key,
                        "record_id": event.get("record_id"),
                        "date": target_date,
                        "stock_code": str(event.get("stock_code") or "")[:6],
                        "stock_name": str(event.get("stock_name") or ""),
                        "position_tag": POSITION_TAG,
                        "entry_decision_source": "exact_runtime_event",
                        "qualified": False,
                        "submitted": False,
                        "filled": False,
                        "completed": False,
                    },
                )
                if stage == "opening_rotation_1pct_qualified":
                    _, exact_replay = _canonical_replay_inputs(fields)
                    qualification_contract_missing = _missing_metric_contract_fields(
                        fields
                    )
                    qualification_missing = [
                        *exact_replay["missing"],
                        *(
                            f"metric_contract:{key}"
                            for key in qualification_contract_missing
                        ),
                    ]
                    qualification_contract_mismatch = [
                        f"metric_contract_mismatch:{key}"
                        for key, expected_value in EXACT_QUALIFICATION_CONTRACT.items()
                        if fields.get(key) != expected_value
                    ]
                    qualification_missing.extend(qualification_contract_mismatch)
                    if qualification_missing:
                        counters["exact_qualification_source_quality_rejected"] += 1
                        missing_counts.update(qualification_missing)
                        trade["qualification_source_quality_allowed"] = False
                        trade["qualification_source_quality_missing"] = (
                            qualification_missing
                        )
                    else:
                        trade.update(
                            {
                                "qualified": True,
                                "qualification_source_quality_allowed": True,
                                "qualified_at": (
                                    event_dt.isoformat() if event_dt else ""
                                ),
                                "qualified_price": _safe_int(
                                    fields.get("curr_price")
                                    or fields.get("qualified_price"),
                                    0,
                                ),
                            }
                        )
                continue

            if key in exact_trades and stage in EXACT_LIFECYCLE_STAGES:
                trade = exact_trades[key]
                if stage == "order_bundle_submitted":
                    trade["submitted"] = bool(
                        fields.get("actual_order_submitted") is True
                        or str(fields.get("actual_order_submitted") or "").lower()
                        == "true"
                    )
                elif stage == "holding_started":
                    actual_order_submitted = bool(
                        fields.get("actual_order_submitted") is True
                        or str(fields.get("actual_order_submitted") or "").lower()
                        == "true"
                    )
                    broker_order_forbidden = bool(
                        fields.get("broker_order_forbidden") is True
                        or str(fields.get("broker_order_forbidden") or "").lower()
                        == "true"
                    )
                    holding_position_tag = (
                        str(fields.get("position_tag") or "").strip().upper()
                    )
                    tagged_opening_rotation = holding_position_tag == POSITION_TAG
                    observed_fill_quality = (
                        str(fields.get("fill_quality") or "UNKNOWN").strip().upper()
                    )
                    if observed_fill_quality not in {"FULL_FILL", "PARTIAL_FILL"}:
                        observed_fill_quality = "UNKNOWN"
                    partial_fill_observed = bool(
                        trade.get("partial_fill_observed")
                        or observed_fill_quality == "PARTIAL_FILL"
                    )
                    entry_fill_quality = observed_fill_quality
                    if partial_fill_observed and observed_fill_quality == "FULL_FILL":
                        entry_fill_quality = "PARTIAL_THEN_FULL"
                    derived_entry_time_bucket = (
                        entry_time_bucket(event_dt, config)
                        if event_dt is not None
                        else "outside_entry_window"
                    )
                    emitted_entry_time_bucket = str(
                        fields.get("opening_rotation_entry_time_bucket") or ""
                    ).strip()
                    first_filled_at = str(trade.get("filled_at") or "")
                    first_entry_time_bucket = str(
                        trade.get("opening_rotation_entry_time_bucket") or ""
                    )
                    expected_emitted_bucket = (
                        first_entry_time_bucket
                        if first_filled_at
                        else derived_entry_time_bucket
                    )
                    if (
                        emitted_entry_time_bucket
                        and emitted_entry_time_bucket != expected_emitted_bucket
                    ):
                        counters["entry_time_bucket_provenance_mismatch"] += 1
                    trade.update(
                        {
                            "fill_observed": True,
                            "filled": (
                                actual_order_submitted
                                and not broker_order_forbidden
                                and tagged_opening_rotation
                            ),
                            "execution_lane": (
                                "real"
                                if actual_order_submitted
                                and not broker_order_forbidden
                                and tagged_opening_rotation
                                else "sim_probe_or_untagged"
                            ),
                            "holding_position_tag": holding_position_tag,
                            "entry_fill_quality": entry_fill_quality,
                            "partial_fill_observed": partial_fill_observed,
                            "buy_price": _safe_float(fields.get("buy_price")),
                            "buy_qty": _safe_int(fields.get("buy_qty")),
                            "fill_price": _safe_float(fields.get("fill_price")),
                            "filled_at": first_filled_at
                            or (event_dt.isoformat() if event_dt else ""),
                            "opening_rotation_entry_time_bucket": (
                                first_entry_time_bucket or derived_entry_time_bucket
                            ),
                            "opening_rotation_entry_time_bucket_source": (
                                trade.get("opening_rotation_entry_time_bucket_source")
                                or (
                                    "receipt_field_verified"
                                    if emitted_entry_time_bucket
                                    == derived_entry_time_bucket
                                    else "holding_started_event_time"
                                )
                            ),
                            "opening_rotation_window_version": str(
                                fields.get("opening_rotation_window_version")
                                or trade.get("opening_rotation_window_version")
                                or entry_window_version(config)
                            ),
                        }
                    )
                elif stage == "opening_rotation_1pct_exit_signal":
                    trade.update(
                        {
                            "exit_rule": str(fields.get("exit_rule") or ""),
                            "exit_signal_at": event_dt.isoformat() if event_dt else "",
                        }
                    )
                elif stage == "sell_completed":
                    sell_price = _safe_float(fields.get("sell_price"))
                    profit_rate = _optional_float(fields.get("profit_rate"))
                    actual_order_submitted = bool(
                        fields.get("actual_order_submitted") is True
                        or str(fields.get("actual_order_submitted") or "").lower()
                        == "true"
                    )
                    broker_order_forbidden = bool(
                        fields.get("broker_order_forbidden") is True
                        or str(fields.get("broker_order_forbidden") or "").lower()
                        == "true"
                    )
                    completion_position_tag = (
                        str(fields.get("position_tag") or "").strip().upper()
                    )
                    trade_status = str(fields.get("trade_status") or "").strip().upper()
                    forbidden_tokens = _forbidden_use_tokens(
                        fields.get("forbidden_uses")
                    )
                    completion_entry_time_bucket = str(
                        fields.get("opening_rotation_entry_time_bucket") or ""
                    ).strip()
                    if (
                        completion_entry_time_bucket
                        and completion_entry_time_bucket
                        != str(trade.get("opening_rotation_entry_time_bucket") or "")
                    ):
                        counters["completion_entry_time_bucket_mismatch"] += 1
                    completion_source_quality_reasons: list[str] = []
                    if not trade.get("qualified"):
                        completion_source_quality_reasons.append(
                            "opening_rotation_qualification_missing"
                        )
                    if not trade.get("filled"):
                        completion_source_quality_reasons.append(
                            "exact_tagged_real_fill_missing"
                        )
                    if not actual_order_submitted or broker_order_forbidden:
                        completion_source_quality_reasons.append(
                            "real_broker_completion_missing"
                        )
                    if completion_position_tag != POSITION_TAG:
                        completion_source_quality_reasons.append(
                            "completion_position_tag_mismatch"
                        )
                    if trade_status != "COMPLETED":
                        completion_source_quality_reasons.append(
                            "completed_trade_status_missing"
                        )
                    for (
                        contract_key,
                        expected_value,
                    ) in EXACT_COMPLETION_CONTRACT.items():
                        if fields.get(contract_key) != expected_value:
                            completion_source_quality_reasons.append(
                                f"completion_contract_mismatch:{contract_key}"
                            )
                    if "allowed_runtime_apply" not in fields or fields.get(
                        "allowed_runtime_apply"
                    ) not in {False, "false", "False", 0, "0"}:
                        completion_source_quality_reasons.append(
                            "completion_contract_mismatch:allowed_runtime_apply"
                        )
                    if not fields.get("forbidden_uses"):
                        completion_source_quality_reasons.append(
                            "completion_contract_mismatch:forbidden_uses"
                        )
                    if "ev" in forbidden_tokens:
                        completion_source_quality_reasons.append(
                            "producer_contract_forbids_ev"
                        )
                    if profit_rate is None:
                        completion_source_quality_reasons.append(
                            "valid_profit_rate_missing"
                        )
                    if sell_price <= 0:
                        completion_source_quality_reasons.append(
                            "valid_sell_price_missing"
                        )
                    if _safe_float(trade.get("buy_price")) <= 0:
                        completion_source_quality_reasons.append(
                            "valid_buy_price_missing"
                        )
                    if _safe_int(trade.get("buy_qty")) <= 0:
                        completion_source_quality_reasons.append(
                            "valid_buy_qty_missing"
                        )
                    real_completion = not completion_source_quality_reasons
                    if completion_source_quality_reasons:
                        counters["completion_source_quality_rejected"] += 1
                        reason_counts.update(completion_source_quality_reasons)
                    trade.update(
                        {
                            "completion_observed": True,
                            "completed": real_completion,
                            "completion_source_quality_allowed": (
                                not completion_source_quality_reasons
                            ),
                            "completion_source_quality_reasons": (
                                completion_source_quality_reasons
                            ),
                            "completion_position_tag": completion_position_tag,
                            "trade_status": trade_status,
                            "sell_price": sell_price,
                            "profit_rate": profit_rate,
                            "completed_at": event_dt.isoformat() if event_dt else "",
                            "exit_rule": str(
                                fields.get("exit_rule") or trade.get("exit_rule") or ""
                            ),
                        }
                    )
                    trade["realized_pnl_krw"] = _safe_int(
                        fields.get("realized_pnl_krw"),
                        calculate_net_realized_pnl(
                            trade.get("buy_price"), sell_price, trade.get("buy_qty")
                        ),
                    )
                continue

            if not _is_legacy_scanner_event(event, fields) or event_dt is None:
                continue
            if key in replay_qualified_keys:
                continue
            if (
                event_dt.time() < config.observe_start
                or event_dt.time() > config.entry_end
            ):
                continue
            counters["legacy_scanner_event_count"] += 1
            values, replay = _canonical_replay_inputs(fields)
            if replay["missing"]:
                counters["legacy_incomplete_packet_count"] += 1
                missing_counts.update(replay["missing"])
                continue
            counters["legacy_complete_packet_count"] += 1
            decision = evaluate_entry(
                previous_state=replay_states.get(key),
                feature_packet=replay["packet"],
                source_signature=values["source_signature"],
                day_change_pct=_safe_float(values["day_change_pct"]),
                intraday_high_price=_first(
                    fields, "intraday_high_price", "day_high", "high_price"
                ),
                now_dt=event_dt.replace(tzinfo=None),
                config=config,
            )
            replay_states[key] = dict(decision.get("state") or {})
            reason_counts[str(decision.get("reason") or "-")] += 1
            if decision.get("qualified"):
                counters["legacy_replay_qualified_count"] += 1
                replay_qualified_keys.add(key)
                replay_qualified.append(
                    {
                        "record_key": key,
                        "record_id": event.get("record_id"),
                        "date": target_date,
                        "stock_code": str(event.get("stock_code") or "")[:6],
                        "stock_name": str(event.get("stock_name") or ""),
                        "qualified_at": event_dt.isoformat(),
                        "qualified_price": _safe_int(decision.get("curr_price")),
                        "entry_decision_source": "strict_legacy_event_replay",
                        "outcome_status": "forward_price_path_unavailable",
                    }
                )

    completed = [row for row in exact_trades.values() if row.get("completed")]
    profits = [_safe_float(row.get("profit_rate")) for row in completed]
    overall_performance = _cohort_performance(completed)
    fill_quality_performance = overall_performance["performance_by_fill_quality"]
    combined_fill_quality_ev_suppressed = overall_performance[
        "combined_fill_quality_ev_suppressed"
    ]
    completed_by_entry_time_bucket: dict[str, list[dict[str, Any]]] = {
        label: [] for label in entry_time_bucket_labels(config)
    }
    for row in completed:
        bucket = str(
            row.get("opening_rotation_entry_time_bucket") or "outside_entry_window"
        )
        completed_by_entry_time_bucket.setdefault(bucket, []).append(row)
    entry_time_bucket_performance = {
        bucket: _cohort_performance(rows)
        for bucket, rows in completed_by_entry_time_bucket.items()
    }
    pnl_by_date: dict[str, int] = {
        target_date: 0 for target_date in eligible_session_dates
    }
    for row in completed:
        target_date = str(row.get("date") or "")
        pnl_by_date.setdefault(target_date, 0)
        pnl_by_date[target_date] += _safe_int(row.get("realized_pnl_krw"))
    target_hit_days = sum(1 for value in pnl_by_date.values() if value >= 30_000)
    performance_evaluable = bool(completed)
    legacy_complete = counters["legacy_complete_packet_count"]
    legacy_total = counters["legacy_scanner_event_count"]
    status = (
        "exact_real_performance_available"
        if performance_evaluable
        else "source_quality_limited_no_completed_opening_rotation_trade"
    )

    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "generated_at": datetime.now(KST).isoformat(),
        "start_date": start_date,
        "end_date": end_date,
        "status": status,
        "metric_role": "descriptive_exact_real_trade_performance",
        "decision_authority": "retrospective_report_only",
        "window_policy": (
            "clean_baseline_weekday_source_sessions_strict_live_policy_replay"
        ),
        "sample_floor": (
            "one_exact_completed_real_trade_for_descriptive_output_only_no_promotion"
        ),
        "primary_decision_metric": "realized_pnl_krw_and_notional_weighted_ev_pct",
        "source_quality_gate": (
            "valid_clean_baseline_and_exact_qualified_tagged_completed_real_lifecycle"
        ),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "forbidden_uses": list(FORBIDDEN_USES),
        "clean_baseline": policy,
        "report_identity": {
            "schema_version": SCHEMA_VERSION,
            "config_fingerprint": config_fingerprint,
            "entry_config": config_snapshot,
            "opening_rotation_window_version": entry_window_version(config),
            "entry_time_bucket_minutes": 30,
        },
        "summary": {
            "source_date_count": len(target_dates),
            "candidate_lines_parsed": counters["candidate_lines_parsed"],
            "clean_baseline_excluded_count": counters["clean_baseline_excluded"],
            "exact_observation_count": counters[
                "exact_stage_opening_rotation_1pct_observed"
            ],
            "upstream_block_count": counters["upstream_block_count"],
            "upstream_exact_candidate_block_count": counters[
                "upstream_exact_candidate_block_count"
            ],
            "upstream_day_change_missing_count": counters[
                "upstream_day_change_missing_count"
            ],
            "exact_qualification_count": counters[
                "exact_stage_opening_rotation_1pct_qualified"
            ],
            "legacy_scanner_event_count": legacy_total,
            "legacy_complete_packet_count": legacy_complete,
            "legacy_complete_packet_rate_pct": (
                round((legacy_complete / legacy_total) * 100.0, 3)
                if legacy_total
                else 0.0
            ),
            "legacy_replay_qualified_count": counters["legacy_replay_qualified_count"],
            "exact_completed_trade_count": len(completed),
            "exact_qualification_source_quality_rejected_count": counters[
                "exact_qualification_source_quality_rejected"
            ],
            "completion_source_quality_rejected_count": counters[
                "completion_source_quality_rejected"
            ],
            "entry_time_bucket_provenance_mismatch_count": counters[
                "entry_time_bucket_provenance_mismatch"
            ],
            "completion_entry_time_bucket_mismatch_count": counters[
                "completion_entry_time_bucket_mismatch"
            ],
            "performance_evaluable": performance_evaluable,
        },
        "real_performance": {
            "completed_trade_count": len(completed),
            "win_count": sum(1 for value in profits if value > 0),
            "loss_count": sum(1 for value in profits if value < 0),
            "diagnostic_win_rate_pct": (
                round(
                    (sum(1 for value in profits if value > 0) / len(profits)) * 100.0, 3
                )
                if profits
                else None
            ),
            "equal_weight_avg_profit_pct": (
                overall_performance["equal_weight_avg_profit_pct"]
            ),
            "notional_weighted_ev_pct": overall_performance["notional_weighted_ev_pct"],
            "simple_sum_profit_pct": overall_performance["simple_sum_profit_pct"],
            "combined_fill_quality_ev_suppressed": (
                combined_fill_quality_ev_suppressed
            ),
            "performance_by_fill_quality": fill_quality_performance,
            "realized_pnl_krw": sum(
                _safe_int(row.get("realized_pnl_krw")) for row in completed
            ),
            "evaluated_day_count": len(pnl_by_date),
            "daily_denominator_policy": (
                "weekday_pipeline_source_session_with_clean_entry_window"
            ),
            "daily_profit_target_krw": 30_000,
            "daily_target_hit_days": target_hit_days,
            "daily_target_hit_rate_pct": (
                round((target_hit_days / len(pnl_by_date)) * 100.0, 3)
                if pnl_by_date and performance_evaluable
                else None
            ),
            "daily_realized_pnl_krw": dict(sorted(pnl_by_date.items())),
        },
        "entry_time_bucket_performance_contract": {
            "metric_role": "descriptive_exact_real_trade_cohort_performance",
            "decision_authority": "retrospective_report_only",
            "window_policy": "first_real_buy_fill_time_kst_clock_aligned_30m",
            "sample_floor": "one_exact_completed_real_trade_per_bucket_for_description_only",
            "primary_decision_metric": "notional_weighted_ev_pct_and_realized_pnl_krw",
            "source_quality_gate": (
                "valid_clean_baseline_exact_tagged_completed_real_lifecycle"
            ),
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "forbidden_uses": list(FORBIDDEN_USES),
        },
        "entry_time_bucket_performance": entry_time_bucket_performance,
        "source_quality": {
            "required_replay_fields": list(REQUIRED_REPLAY_FIELDS),
            "missing_field_counts": dict(missing_counts.most_common()),
            "reason_counts": dict(reason_counts.most_common()),
            "upstream_block_reason_counts": {
                key.removeprefix("upstream_reason:"): value
                for key, value in counters.most_common()
                if key.startswith("upstream_reason:")
            },
            "legacy_performance_authority": "none_without_complete_entry_and_forward_path",
        },
        "auxiliary_post_sell_inventory": _post_sell_inventory(
            target_dates, post_sell_dir
        ),
        "exact_trade_rows": sorted(
            exact_trades.values(),
            key=lambda row: (str(row.get("date")), str(row.get("qualified_at"))),
        ),
        "legacy_replay_qualified_rows": replay_qualified,
    }


def render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") or {}
    perf = report.get("real_performance") or {}
    inventory = report.get("auxiliary_post_sell_inventory") or {}
    missing = report.get("source_quality", {}).get("missing_field_counts") or {}
    identity = report.get("report_identity") or {}
    bucket_performance = report.get("entry_time_bucket_performance") or {}
    daily_hit_rate = perf.get("daily_target_hit_rate_pct")
    daily_hit_rate_text = (
        "평가 불가" if daily_hit_rate is None else f"{daily_hit_rate:.3f}%"
    )
    lines = [
        "# OPENING_ROTATION_1PCT Backtest",
        "",
        f"- 기간: `{report.get('start_date')}` ~ `{report.get('end_date')}`",
        f"- 판정: `{report.get('status')}`",
        f"- 설정 지문: `{identity.get('config_fingerprint', '-')}`",
        f"- 진입창 버전: `{identity.get('opening_rotation_window_version', '-')}`",
        f"- 과거 SCANNER 이벤트: `{summary.get('legacy_scanner_event_count', 0)}`",
        f"- 완전 진입 패킷: `{summary.get('legacy_complete_packet_count', 0)}`",
        f"- 엄격 재생 진입: `{summary.get('legacy_replay_qualified_count', 0)}`",
        f"- upstream 차단 관측: `{summary.get('upstream_block_count', 0)}`",
        f"- upstream exact 후보 차단: `{summary.get('upstream_exact_candidate_block_count', 0)}`",
        f"- upstream 등락률 미확정: `{summary.get('upstream_day_change_missing_count', 0)}`",
        f"- 신규 태그 완료 거래: `{perf.get('completed_trade_count', 0)}`",
        f"- 실현손익: `{perf.get('realized_pnl_krw', 0):,}원`",
        f"- 일 3만원 달성일: `{perf.get('daily_target_hit_days', 0)}`",
        f"- 유효 장 수: `{perf.get('evaluated_day_count', 0)}`",
        f"- 일 3만원 달성률: `{daily_hit_rate_text}`",
        "",
        "## Source quality",
        "",
    ]
    if missing:
        lines.extend(f"- `{key}`: {value}" for key, value in list(missing.items())[:12])
    else:
        lines.append("- 누락 필드 집계 없음")
    lines.extend(
        [
            "",
            "## Entry-time 30-minute performance",
            "",
            "| 진입 cohort | 완료 | 승 | 승률 | notional EV | 실현손익 |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
    for bucket, bucket_perf in bucket_performance.items():
        win_rate = bucket_perf.get("diagnostic_win_rate_pct")
        weighted_ev = bucket_perf.get("notional_weighted_ev_pct")
        lines.append(
            f"| {bucket} | {bucket_perf.get('completed_trade_count', 0)} | "
            f"{bucket_perf.get('win_count', 0)} | "
            f"{'-' if win_rate is None else f'{win_rate:.3f}%'} | "
            f"{'분리 집계' if weighted_ev is None and bucket_perf.get('combined_fill_quality_ev_suppressed') else '-' if weighted_ev is None else f'{weighted_ev:+.4f}%'} | "
            f"{bucket_perf.get('realized_pnl_krw', 0):,}원 |"
        )
    lines.extend(
        [
            "",
            "## Existing outcome inventory",
            "",
            f"- real post-sell: `{inventory.get('real_evaluation_count', 0)}`",
            f"- sim post-sell: `{inventory.get('sim_evaluation_count', 0)}`",
            "- 기존 타 전략의 post-sell 결과는 가상 진입의 성과로 합산하지 않았습니다.",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(
    report: dict[str, Any], output_dir: Path = REPORT_DIR
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    config_fingerprint = str(
        (report.get("report_identity") or {}).get("config_fingerprint") or "legacy"
    )
    suffix = f"{report['start_date']}_{report['end_date']}_{config_fingerprint}"
    json_path = output_dir / f"{REPORT_TYPE}_{suffix}.json"
    md_path = output_dir / f"{REPORT_TYPE}_{suffix}.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, md_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    report = build_report(start_date=args.start_date, end_date=args.end_date)
    if args.write:
        paths = write_report(report)
        print("\n".join(str(path) for path in paths))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
