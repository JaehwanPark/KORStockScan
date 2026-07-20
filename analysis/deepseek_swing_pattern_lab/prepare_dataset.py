"""Prepare swing fact tables from canonical reports and pipeline events."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import create_engine, text

from analysis.deepseek_swing_pattern_lab.config import (
    CODE_IMPROVEMENT_WORKORDER_DIR,
    DATA_DIR,
    END_DATE,
    MIN_VALID_SAMPLES,
    OUTPUT_DIR,
    PIPELINE_EVENTS_DIR,
    POSTGRES_URL,
    RECO_DIAGNOSTIC_JSON_PATH,
    RECO_PATH,
    START_DATE,
    SWING_IMPROVEMENT_AUTOMATION_DIR,
    SWING_LIFECYCLE_AUDIT_DIR,
    SWING_SELECTION_FUNNEL_DIR,
    SWING_THRESHOLD_AI_REVIEW_DIR,
    THRESHOLD_CYCLE_EV_DIR,
)

SWING_STRATEGIES = {"KOSPI_ML", "KOSDAQ_ML", "MAIN"}
OFI_QI_QUALITY_FLAG_COLUMNS = (
    "micro_missing_flag",
    "micro_stale_flag",
    "observer_unhealthy_flag",
    "micro_not_ready_flag",
    "state_insufficient_flag",
)


def _reason_key_from_flag_column(column: str) -> str:
    return column.replace("_flag", "")


SWING_EVENT_STAGES = {
    "blocked_swing_gap",
    "gatekeeper_fast_reuse",
    "gatekeeper_fast_reuse_bypass",
    "blocked_gatekeeper_reject",
    "blocked_gatekeeper_missing",
    "blocked_gatekeeper_error",
    "market_regime_block",
    "market_regime_pass",
    "swing_entry_micro_context_observed",
    "swing_sim_buy_order_assumed_filled",
    "swing_sim_holding_started",
    "swing_sim_order_bundle_assumed_filled",
    "swing_scale_in_micro_context_observed",
    "swing_sim_scale_in_order_assumed_filled",
    "swing_exit_micro_context_observed",
    "holding_flow_ofi_smoothing_applied",
    "swing_sim_sell_order_assumed_filled",
    "swing_sim_sell_blocked_zero_qty",
    "order_bundle_submitted",
    "order_submitted",
    "buy_order_submitted",
}
SUBMITTED_STAGES = {"order_bundle_submitted", "order_submitted", "buy_order_submitted"}
SELL_STAGES = {
    "swing_sim_sell_order_assumed_filled",
    "sell_order_sent",
    "sell_order_submitted",
    "sell_order_failed",
    "sell_order_blocked_market_closed",
}
SCALE_IN_STAGES = {
    "swing_scale_in_micro_context_observed",
    "swing_sim_scale_in_order_assumed_filled",
    "scale_in_executed",
    "scale_in_price_resolved",
    "scale_in_price_guard_block",
    "scale_in_price_p2_observe",
    "scale_in_qty_block",
}
EXIT_STAGES = SELL_STAGES | {
    "exit_signal",
    "holding_flow_ofi_smoothing_applied",
    "preset_exit_setup",
    "protect_trailing_smooth_confirmed",
    "preset_exit_sync_ok",
    "preset_exit_sync_mismatch",
}
ENTRY_STAGES = {
    "blocked_swing_gap",
    "gatekeeper_fast_reuse",
    "gatekeeper_fast_reuse_bypass",
    "blocked_gatekeeper_reject",
    "blocked_gatekeeper_missing",
    "blocked_gatekeeper_error",
    "market_regime_block",
    "market_regime_pass",
    "swing_entry_micro_context_observed",
    "order_bundle_submitted",
    "order_submitted",
    "buy_order_submitted",
    "swing_sim_buy_order_assumed_filled",
    "swing_sim_order_bundle_assumed_filled",
}
HOLDING_STAGES = {
    "holding_started",
    "swing_sim_holding_started",
    "position_rebased_after_fill",
    "bad_entry_refined_candidate",
    "loss_fallback_probe",
    "stat_action_decision_snapshot",
    "same_symbol_loss_reentry_cooldown",
}
ACTUAL_ENTRY_STAGES = {
    "order_bundle_submitted",
    "order_submitted",
    "buy_order_submitted",
    "swing_sim_buy_order_assumed_filled",
    "swing_sim_order_bundle_assumed_filled",
}
ACTUAL_SCALE_IN_STAGES = {
    "swing_sim_scale_in_order_assumed_filled",
    "scale_in_executed",
}
ACTUAL_EXIT_STAGES = {
    "swing_sim_sell_order_assumed_filled",
    "sell_order_sent",
    "sell_order_submitted",
}
MAX_STAGES_SEEN_SAMPLES = 5

SCHEMA_VERSION = 2


def _date_text(d: str | date | datetime) -> str:
    return str(pd.to_datetime(d).date())


def _date_range() -> list[str]:
    start = date.fromisoformat(START_DATE)
    end = date.fromisoformat(END_DATE)
    if start > end:
        return [START_DATE]
    result = []
    current = start
    while current <= end:
        result.append(current.isoformat())
        current += timedelta(days=1)
    return result


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any, default: float | None = 0.0) -> float | None:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _safe_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _stage_is_probe(stage: str) -> bool:
    lowered = str(stage or "").strip().lower()
    return lowered.startswith("swing_probe_") or "probe" in lowered


def _stage_is_sim_or_dry_run(stage: str) -> bool:
    lowered = str(stage or "").strip().lower()
    return (
        lowered.startswith("swing_sim_")
        or "dry_run" in lowered
        or "assumed_filled" in lowered
    )


def _stage_actual_order_submitted(
    stage: str, fields: dict[str, Any] | None = None
) -> bool:
    fields = fields or {}
    for key in ("actual_order_submitted", "broker_order_submitted"):
        if key in fields:
            return _safe_bool(fields.get(key))
    if _stage_is_probe(stage) or _stage_is_sim_or_dry_run(stage):
        return False
    return stage in SUBMITTED_STAGES or stage in {
        "sell_order_sent",
        "sell_order_submitted",
        "scale_in_executed",
    }


def _stage_decision_authority(stage: str, fields: dict[str, Any] | None = None) -> str:
    fields = fields or {}
    explicit = str(fields.get("decision_authority") or "").strip()
    if explicit:
        return explicit
    if _stage_is_probe(stage):
        return "probe_observe_only"
    if _stage_is_sim_or_dry_run(stage):
        return "sim_equal_weight"
    if _stage_actual_order_submitted(stage, fields):
        return "real_order_event"
    return "source_quality_only"


def _merge_decision_authority(current: str, incoming: str) -> str:
    priority = {
        "probe_observe_only": 4,
        "sim_equal_weight": 3,
        "real_order_event": 2,
        "source_quality_only": 1,
        "": 0,
    }
    return incoming if priority.get(incoming, 0) > priority.get(current, 0) else current


def _safe_read_json(path: str | Path) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _read_jsonl(path: str | Path) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    rows: list[dict[str, Any]] = []
    with p.open(encoding="utf-8") as f:
        for line in f:
            try:
                payload = json.loads(line)
            except Exception:
                continue
            if isinstance(payload, dict):
                rows.append(payload)
    return rows


def _event_fields(event: dict[str, Any]) -> dict[str, Any]:
    fields = event.get("fields")
    return fields if isinstance(fields, dict) else {}


def _event_stage(event: dict[str, Any]) -> str:
    return str(event.get("stage") or event.get("event") or "").strip()


def _event_strategy(event: dict[str, Any]) -> str:
    fields = _event_fields(event)
    return str(event.get("strategy") or fields.get("strategy") or "").strip().upper()


def _event_identity(event: dict[str, Any]) -> tuple[str, str, str]:
    fields = _event_fields(event)
    record_id = str(event.get("record_id") or fields.get("record_id") or "")
    code = str(
        event.get("stock_code") or fields.get("stock_code") or fields.get("code") or ""
    )
    name = str(
        event.get("stock_name") or fields.get("stock_name") or fields.get("name") or ""
    )
    return record_id, code, name


def _is_swing_event(event: dict[str, Any]) -> bool:
    stage = _event_stage(event)
    strategy = _event_strategy(event)
    if strategy in SWING_STRATEGIES:
        return True
    if stage in SUBMITTED_STAGES:
        return False
    if stage in SWING_EVENT_STAGES or stage in SELL_STAGES:
        return True
    if stage.startswith("swing_"):
        return True
    lowered = stage.lower()
    return "gatekeeper" in lowered or "market_regime" in lowered


def _stage_group(stage: str) -> str:
    lowered = stage.lower()
    if stage in ENTRY_STAGES or "gatekeeper" in lowered or "market_regime" in lowered:
        return "entry"
    if any(
        token in lowered
        for token in ("scale_in", "pyramid", "avg_down", "reversal_add")
    ):
        return "scale_in"
    if stage in SELL_STAGES or any(
        token in lowered for token in ("sell", "exit", "trim", "time_stop", "trailing")
    ):
        return "exit"
    if any(token in lowered for token in ("holding", "hold_", "mfe", "mae")):
        return "holding"
    return "other"


def _stage_lifecycle_position(stage: str) -> str:
    g = _stage_group(stage)
    return {
        "entry": "entry",
        "scale_in": "scale_in",
        "exit": "exit",
        "holding": "holding",
    }.get(g, "other")


def load_db_trade_rows(target_date: str) -> list[dict[str, Any]]:
    engine = create_engine(POSTGRES_URL)
    query = text("""
        SELECT id, rec_date, stock_code, stock_name, strategy, trade_type, position_tag,
               status, prob, buy_price, buy_qty, buy_time, sell_price, sell_qty,
               sell_time, profit_rate, profit, updated_at,
               add_count, avg_down_count, pyramid_count, last_add_type, last_add_at,
               scale_in_locked, hard_stop_price, trailing_stop_price
        FROM recommendation_history
        WHERE rec_date = :target_date
          AND strategy IN ('KOSPI_ML', 'KOSDAQ_ML', 'MAIN')
        ORDER BY position_tag, stock_code
        """)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn, params={"target_date": target_date})
    return df.to_dict("records")


def load_recommendation_rows(path: str | Path = RECO_PATH) -> list[dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return []
    df = pd.read_csv(p, dtype={"code": str})
    return df.to_dict("records")


def build_swing_trade_fact(target_dates: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for d in target_dates:
        db_rows = []
        try:
            db_rows = load_db_trade_rows(d)
        except Exception:
            pass
        for row in db_rows:
            buy_qty = _safe_int(row.get("buy_qty"))
            sell_qty = _safe_int(row.get("sell_qty"))
            completed = str(row.get("status") or "").upper() == "COMPLETED"
            profit_rate = _safe_float(row.get("profit_rate"), None)
            valid_profit_rate = (
                profit_rate if completed and profit_rate is not None else None
            )
            rows.append(
                {
                    "date": d,
                    "record_id": str(row.get("id") or ""),
                    "stock_code": str(row.get("stock_code") or ""),
                    "stock_name": str(row.get("stock_name") or ""),
                    "strategy": str(row.get("strategy") or ""),
                    "position_tag": str(row.get("position_tag") or ""),
                    "selection_mode": "",
                    "hybrid_mean": None,
                    "meta_score": None,
                    "floor_used": None,
                    "score_rank": None,
                    "status": str(row.get("status") or ""),
                    "buy_qty": buy_qty,
                    "buy_price": _safe_float(row.get("buy_price"), None),
                    "sell_qty": sell_qty,
                    "sell_price": _safe_float(row.get("sell_price"), None),
                    "completed": completed,
                    "valid_profit_rate": valid_profit_rate,
                    "profit_rate": profit_rate,
                    "profit": _safe_float(row.get("profit")),
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "decision_authority": "sim_equal_weight",
                    "runtime_effect": False,
                    "simulation_owner": "deepseek_swing_pattern_lab",
                    "add_count": _safe_int(row.get("add_count")),
                    "avg_down_count": _safe_int(row.get("avg_down_count")),
                    "pyramid_count": _safe_int(row.get("pyramid_count")),
                    "last_add_type": str(row.get("last_add_type") or ""),
                }
            )
    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values(["date", "stock_code"]).reset_index(drop=True)


def build_swing_lifecycle_funnel_fact(target_dates: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for d in target_dates:
        audit_json = _safe_read_json(
            SWING_LIFECYCLE_AUDIT_DIR / f"swing_lifecycle_audit_{d}.json"
        )
        funnel_json = _safe_read_json(
            SWING_SELECTION_FUNNEL_DIR / f"swing_selection_funnel_{d}.json"
        )

        model = (
            funnel_json.get("model_selection", {})
            or audit_json.get("model_selection", {})
            or {}
        )
        csv_summary = (
            funnel_json.get("recommendation_csv", {})
            or audit_json.get("recommendation_csv", {})
            or {}
        )
        db_summary = (
            funnel_json.get("db_recommendations", {})
            or audit_json.get("db_lifecycle", {})
            or {}
        )
        events = (
            audit_json.get("pipeline_events", {})
            or funnel_json.get("pipeline_events", {})
            or {}
        )

        raw_counts = (
            events.get("raw_counts", {})
            if isinstance(events.get("raw_counts"), dict)
            else {}
        )
        unique_counts = (
            events.get("unique_record_counts", {})
            if isinstance(events.get("unique_record_counts"), dict)
            else {}
        )

        selected_codes = _load_today_selected_codes(d)
        split = (
            _split_blocker_unique_by_population(d, selected_codes, BLOCKER_SPLIT_STAGES)
            if selected_codes
            else {}
        )

        rows.append(
            {
                "date": d,
                "selected_count": _safe_int(model.get("selected_count")),
                "csv_rows": _safe_int(csv_summary.get("csv_rows")),
                "db_rows": _safe_int(db_summary.get("db_rows")),
                "entered_rows": _safe_int(db_summary.get("entered_rows")),
                "completed_rows": _safe_int(db_summary.get("completed_rows")),
                "valid_profit_rows": _safe_int(db_summary.get("valid_profit_rows")),
                "blocked_swing_gap_unique": _safe_int(
                    unique_counts.get("blocked_swing_gap")
                ),
                "blocked_swing_gap_raw": _safe_int(raw_counts.get("blocked_swing_gap")),
                "blocked_swing_gap_selection_unique": _safe_int(
                    split.get("blocked_swing_gap_selection_unique")
                ),
                "blocked_swing_gap_carryover_unique": _safe_int(
                    split.get("blocked_swing_gap_carryover_unique")
                ),
                "blocked_gatekeeper_reject_unique": _safe_int(
                    unique_counts.get("blocked_gatekeeper_reject")
                ),
                "blocked_gatekeeper_reject_raw": _safe_int(
                    raw_counts.get("blocked_gatekeeper_reject")
                ),
                "blocked_gatekeeper_reject_selection_unique": _safe_int(
                    split.get("blocked_gatekeeper_reject_selection_unique")
                ),
                "blocked_gatekeeper_reject_carryover_unique": _safe_int(
                    split.get("blocked_gatekeeper_reject_carryover_unique")
                ),
                "blocked_gatekeeper_missing_unique": _safe_int(
                    unique_counts.get("blocked_gatekeeper_missing")
                ),
                "blocked_gatekeeper_missing_selection_unique": _safe_int(
                    split.get("blocked_gatekeeper_missing_selection_unique")
                ),
                "blocked_gatekeeper_missing_carryover_unique": _safe_int(
                    split.get("blocked_gatekeeper_missing_carryover_unique")
                ),
                "blocked_gatekeeper_error_unique": _safe_int(
                    unique_counts.get("blocked_gatekeeper_error")
                ),
                "blocked_gatekeeper_error_selection_unique": _safe_int(
                    split.get("blocked_gatekeeper_error_selection_unique")
                ),
                "blocked_gatekeeper_error_carryover_unique": _safe_int(
                    split.get("blocked_gatekeeper_error_carryover_unique")
                ),
                "market_regime_block_unique": _safe_int(
                    unique_counts.get("market_regime_block")
                ),
                "market_regime_block_raw": _safe_int(
                    raw_counts.get("market_regime_block")
                ),
                "market_regime_block_selection_unique": _safe_int(
                    split.get("market_regime_block_selection_unique")
                ),
                "market_regime_block_carryover_unique": _safe_int(
                    split.get("market_regime_block_carryover_unique")
                ),
                "market_regime_pass_unique": _safe_int(
                    unique_counts.get("market_regime_pass")
                ),
                "submitted_raw_count": _safe_int(events.get("submitted_raw_count")),
                "submitted_unique_records": _safe_int(
                    events.get("submitted_unique_records")
                ),
                "simulated_order_raw_count": _safe_int(
                    events.get("simulated_order_raw_count")
                ),
                "simulated_order_unique_records": _safe_int(
                    events.get("simulated_order_unique_records")
                ),
                "missed_entry_unique": 0,
                "missed_entry_raw": 0,
                "blocked_reason": "",
                "gatekeeper_action": "",
                "floor_bull": model.get("floor_bull"),
                "floor_bear": model.get("floor_bear"),
                "fallback_written": bool(
                    model.get("fallback_written_to_recommendations")
                ),
                "safe_pool_count": _safe_int(model.get("safe_pool_count")),
            }
        )

        if audit_json:
            lifecycle = audit_json.get("lifecycle_events", {})
            if isinstance(lifecycle, dict):
                group_unique = lifecycle.get("group_unique_counts", {})
                if isinstance(group_unique, dict):
                    rows[-1]["missed_entry_unique"] = _safe_int(
                        group_unique.get("entry", 0)
                    ) - _safe_int(events.get("submitted_unique_records"))
                group_raw = lifecycle.get("group_raw_counts", {})
                if isinstance(group_raw, dict):
                    rows[-1]["missed_entry_raw"] = _safe_int(
                        group_raw.get("entry", 0)
                    ) - _safe_int(events.get("submitted_raw_count"))

    return pd.DataFrame(rows).sort_values(["date"]).reset_index(drop=True)


def _load_today_selected_codes(target_date: str) -> set[str]:
    recs = load_recommendation_rows(RECO_PATH)
    codes: set[str] = set()
    for row in recs:
        d = str(row.get("date") or "").strip()
        if d and str(pd.to_datetime(d).date()) == target_date:
            code = str(row.get("code") or "").strip()
            if code:
                codes.add(code.zfill(6))
    return codes


def _split_blocker_unique_by_population(
    target_date: str,
    selected_codes: set[str],
    blocker_stages: list[str],
) -> dict[str, int]:
    events = _read_jsonl(PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl")
    seen_selection: dict[str, set[tuple[str, str, str]]] = {
        s: set() for s in blocker_stages
    }
    seen_carryover: dict[str, set[tuple[str, str, str]]] = {
        s: set() for s in blocker_stages
    }

    for event in events:
        if not _is_swing_event(event):
            continue
        stage = _event_stage(event)
        if stage not in blocker_stages:
            continue
        identity = _event_identity(event)
        code = identity[1].strip().zfill(6)
        if code in selected_codes:
            seen_selection[stage].add(identity)
        elif code:
            seen_carryover[stage].add(identity)

    return {
        f"{stage}_selection_unique": len(seen_selection.get(stage, set()))
        for stage in blocker_stages
    } | {
        f"{stage}_carryover_unique": len(seen_carryover.get(stage, set()))
        for stage in blocker_stages
    }


BLOCKER_SPLIT_STAGES = [
    "blocked_swing_gap",
    "blocked_gatekeeper_reject",
    "blocked_gatekeeper_missing",
    "blocked_gatekeeper_error",
    "market_regime_block",
]


def build_swing_sequence_fact(target_dates: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for d in target_dates:
        events = _read_jsonl(PIPELINE_EVENTS_DIR / f"pipeline_events_{d}.jsonl")
        by_record: dict[tuple[str, str, str], dict[str, Any]] = {}
        for event in events:
            if not _is_swing_event(event):
                continue
            stage = _event_stage(event)
            if not stage:
                continue
            fields = _event_fields(event)
            identity = _event_identity(event)
            if identity not in by_record:
                by_record[identity] = {
                    "date": d,
                    "record_id": identity[0],
                    "stock_code": identity[1],
                    "stock_name": identity[2],
                    "strategy": str(
                        fields.get("strategy") or event.get("strategy") or ""
                    ),
                    "stage_count": 0,
                    "entered": False,
                    "held": False,
                    "scale_in_observed": False,
                    "exited": False,
                    "completed": False,
                    "exit_source": "",
                    "sell_reason_type": "",
                    "holding_flow_action": "",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "decision_authority": "",
                    "runtime_effect": False,
                    "virtual_lifecycle_owner": "deepseek_swing_pattern_lab",
                    "stage_summary": {},
                    "_sample_stages": {},
                }
            rec = by_record[identity]
            rec["stage_count"] += 1
            stage_actual_order_submitted = _stage_actual_order_submitted(stage, fields)
            stage_decision_authority = _stage_decision_authority(stage, fields)
            if stage_actual_order_submitted:
                rec["actual_order_submitted"] = True
                rec["broker_order_forbidden"] = False
            rec["decision_authority"] = _merge_decision_authority(
                str(rec.get("decision_authority") or ""),
                stage_decision_authority,
            )

            group = _stage_lifecycle_position(stage)
            if stage in ACTUAL_ENTRY_STAGES:
                rec["entered"] = True
            if group == "holding" or stage in HOLDING_STAGES:
                rec["held"] = True
            if stage in ACTUAL_SCALE_IN_STAGES:
                rec["scale_in_observed"] = True
            if stage in ACTUAL_EXIT_STAGES:
                rec["exited"] = True
                rec["exit_source"] = str(
                    fields.get("exit_source")
                    or fields.get("sell_source")
                    or rec["exit_source"]
                    or ""
                )
                rec["sell_reason_type"] = str(
                    fields.get("sell_reason_type")
                    or fields.get("sell_reason")
                    or rec["sell_reason_type"]
                    or ""
                )
                rec["holding_flow_action"] = str(
                    fields.get("holding_flow_action")
                    or fields.get("flow_action")
                    or rec["holding_flow_action"]
                    or ""
                )

            if (
                str(fields.get("status") or event.get("status") or "").upper()
                == "COMPLETED"
            ):
                rec["completed"] = True

            stage_order = _stage_lifecycle_position(stage)
            emitted_at = str(event.get("emitted_at") or "")
            stage_key = f"{stage}:{stage_order}"
            rec["stage_summary"].setdefault(
                stage_key, {"count": 0, "first_at": emitted_at, "last_at": emitted_at}
            )
            summary = rec["stage_summary"][stage_key]
            summary["count"] += 1
            if emitted_at:
                if not summary["first_at"] or emitted_at < summary["first_at"]:
                    summary["first_at"] = emitted_at
                if emitted_at > summary["last_at"]:
                    summary["last_at"] = emitted_at
            rec["_sample_stages"].setdefault(stage_key, [])
            if len(rec["_sample_stages"][stage_key]) < MAX_STAGES_SEEN_SAMPLES:
                sample = {
                    k: v
                    for k, v in fields.items()
                    if k
                    in (
                        "action",
                        "cooldown_sec",
                        "gap_pct",
                        "exit_source",
                        "profit_rate",
                        "profit",
                        "sell_reason_type",
                    )
                }
                sample.update(
                    {
                        "actual_order_submitted": stage_actual_order_submitted,
                        "broker_order_forbidden": not stage_actual_order_submitted,
                        "decision_authority": stage_decision_authority,
                    }
                )
                rec["_sample_stages"][stage_key].append(sample)

        for rec in by_record.values():
            if not rec.get("decision_authority"):
                rec["decision_authority"] = "source_quality_only"
            compressed = {}
            for stage_key, summary in rec["stage_summary"].items():
                compressed[stage_key] = {
                    "count": summary["count"],
                    "first_at": summary["first_at"],
                    "last_at": summary["last_at"],
                }
                samples = rec["_sample_stages"].get(stage_key)
                if samples:
                    compressed[stage_key]["sample_fields"] = samples[
                        :MAX_STAGES_SEEN_SAMPLES
                    ]
            rec["stages_seen"] = json.dumps(compressed, ensure_ascii=False)
            del rec["stage_summary"]
            del rec["_sample_stages"]
            rows.append(rec)

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values(["date", "record_id"]).reset_index(drop=True)


def build_swing_ofi_qi_fact(target_dates: list[str]) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for d in target_dates:
        events = _read_jsonl(PIPELINE_EVENTS_DIR / f"pipeline_events_{d}.jsonl")
        for event in events:
            if not _is_swing_event(event):
                continue
            fields = _event_fields(event)
            if not any(
                str(key).startswith(("orderbook_micro_", "swing_micro_"))
                for key in fields
            ):
                continue
            stage = _event_stage(event)
            identity = _event_identity(event)
            actual_order_submitted = _stage_actual_order_submitted(stage, fields)
            rows.append(
                {
                    "date": d,
                    "record_id": identity[0],
                    "stock_code": identity[1],
                    "stock_name": identity[2],
                    "stage": stage,
                    "group": _stage_group(stage),
                    "orderbook_micro_ready": _safe_bool(
                        fields.get("orderbook_micro_ready")
                    ),
                    "orderbook_micro_state": str(
                        fields.get("orderbook_micro_state") or ""
                    ),
                    "orderbook_micro_qi": _safe_float(
                        fields.get("orderbook_micro_qi"), None
                    ),
                    "orderbook_micro_qi_ewma": _safe_float(
                        fields.get("orderbook_micro_qi_ewma"), None
                    ),
                    "orderbook_micro_ofi_norm": _safe_float(
                        fields.get("orderbook_micro_ofi_norm"), None
                    ),
                    "orderbook_micro_ofi_z": _safe_float(
                        fields.get("orderbook_micro_ofi_z"), None
                    ),
                    "orderbook_micro_snapshot_age_ms": _safe_int(
                        fields.get("orderbook_micro_snapshot_age_ms")
                    ),
                    "orderbook_micro_observer_healthy": _safe_bool(
                        fields.get("orderbook_micro_observer_healthy")
                    ),
                    "orderbook_micro_ofi_threshold_source": str(
                        fields.get("orderbook_micro_ofi_threshold_source") or ""
                    ),
                    "orderbook_micro_ofi_bucket_key": str(
                        fields.get("orderbook_micro_ofi_bucket_key") or ""
                    ),
                    "swing_micro_advice": str(fields.get("swing_micro_advice") or ""),
                    "swing_micro_runtime_effect": _safe_bool(
                        fields.get("swing_micro_runtime_effect")
                    ),
                    "smoothing_action": str(fields.get("smoothing_action") or ""),
                    "actual_order_submitted": actual_order_submitted,
                    "broker_order_forbidden": not actual_order_submitted,
                    "decision_authority": _stage_decision_authority(stage, fields),
                    "runtime_effect": False,
                    "micro_missing_flag": False,
                    "micro_stale_flag": False,
                    "observer_unhealthy_flag": False,
                    "micro_not_ready_flag": False,
                    "state_insufficient_flag": False,
                    "stale_missing_reasons": "",
                    "stale_missing_flag": False,
                }
            )
            stale = str(fields.get("swing_micro_stale") or "").strip().lower()
            advice = str(fields.get("swing_micro_advice") or "").upper()
            state = str(fields.get("orderbook_micro_state") or "").lower()
            ready = _safe_bool(fields.get("orderbook_micro_ready"))
            healthy = _safe_bool(fields.get("orderbook_micro_observer_healthy"))
            has_micro_values = any(
                fields.get(key) not in (None, "", "-")
                for key in (
                    "orderbook_micro_qi",
                    "orderbook_micro_qi_ewma",
                    "orderbook_micro_ofi_norm",
                    "orderbook_micro_ofi_z",
                )
            )
            flags = {
                "micro_missing_flag": advice == "MISSING"
                or state in {"", "missing"}
                or (not ready and not has_micro_values),
                "micro_stale_flag": stale in {"1", "true", "yes", "y"},
                "observer_unhealthy_flag": not healthy,
                "micro_not_ready_flag": not ready,
                "state_insufficient_flag": state == "insufficient",
            }
            rows[-1].update(flags)
            rows[-1]["stale_missing_flag"] = any(flags.values())
            rows[-1]["stale_missing_reasons"] = ",".join(
                key.replace("_flag", "") for key, active in flags.items() if active
            )

    df = pd.DataFrame(rows)
    if df.empty:
        return df
    return df.sort_values(["date", "record_id"]).reset_index(drop=True)


def build_data_quality_report(
    trade_fact: pd.DataFrame,
    funnel_fact: pd.DataFrame,
    sequence_fact: pd.DataFrame,
    ofi_qi_fact: pd.DataFrame,
    target_dates: list[str],
) -> dict[str, Any]:
    analysis_days = max(len(target_dates), 1)
    min_funnel_rows = min(MIN_VALID_SAMPLES, analysis_days)
    trade_rows = len(trade_fact)
    funnel_rows = len(funnel_fact)
    seq_rows = len(sequence_fact)
    ofi_qi_rows = len(ofi_qi_fact)
    completed = int(trade_fact["completed"].sum()) if not trade_fact.empty else 0
    valid_profit = (
        int((trade_fact["valid_profit_rate"].notna()).sum())
        if not trade_fact.empty
        else 0
    )

    warnings: list[str] = []
    if funnel_rows < min_funnel_rows:
        warnings.append(
            f"funnel fact has only {funnel_rows} rows (min {min_funnel_rows})"
        )
    if trade_rows == 0 and seq_rows == 0:
        warnings.append("no trade or sequence data found for the analysis period")
    if ofi_qi_rows == 0:
        warnings.append("no OFI/QI micro context data found")

    stale_missing = (
        int(ofi_qi_fact["stale_missing_flag"].sum()) if not ofi_qi_fact.empty else 0
    )
    reason_counts: dict[str, int] = {}
    reason_ratios: dict[str, float] = {}
    reason_combination_counts: dict[str, int] = {}
    reason_combination_unique_record_counts: dict[str, int] = {}
    stale_missing_group_counts: dict[str, int] = {}
    stale_missing_group_unique_record_counts: dict[str, int] = {}
    stale_missing_stage_counts: dict[str, int] = {}
    stale_missing_unique_record_count = 0
    observer_unhealthy_overlap: dict[str, int] = {
        "observer_unhealthy_total": 0,
        "observer_unhealthy_with_other_reason": 0,
        "observer_unhealthy_only": 0,
    }
    examples: list[dict[str, Any]] = []
    if not ofi_qi_fact.empty:
        for column in OFI_QI_QUALITY_FLAG_COLUMNS:
            count = int(ofi_qi_fact[column].sum()) if column in ofi_qi_fact else 0
            key = _reason_key_from_flag_column(column)
            reason_counts[key] = count
            reason_ratios[key] = round(count / max(ofi_qi_rows, 1), 4)
        if "stale_missing_flag" in ofi_qi_fact:
            stale_rows = ofi_qi_fact[ofi_qi_fact["stale_missing_flag"] == True].copy()
        else:
            stale_rows = pd.DataFrame()
        if not stale_rows.empty:
            combination_counter: Counter[str] = Counter()
            combination_records: dict[str, set[str]] = defaultdict(set)
            group_counter: Counter[str] = Counter()
            group_records: dict[str, set[str]] = defaultdict(set)
            stage_counter: Counter[str] = Counter()
            all_records: set[str] = set()
            observer_total = 0
            observer_with_other = 0
            observer_only = 0
            for _, row in stale_rows.iterrows():
                active_reasons = [
                    _reason_key_from_flag_column(column)
                    for column in OFI_QI_QUALITY_FLAG_COLUMNS
                    if column in stale_rows and bool(row.get(column, False))
                ]
                combination = "+".join(active_reasons) if active_reasons else "unknown"
                record_id = str(row.get("record_id") or "")
                combination_counter[combination] += 1
                if record_id:
                    combination_records[combination].add(record_id)
                group_counter[str(row.get("group") or "unknown")] += 1
                if record_id:
                    group_records[str(row.get("group") or "unknown")].add(record_id)
                    all_records.add(record_id)
                stage_counter[str(row.get("stage") or "unknown")] += 1
                if "observer_unhealthy" in active_reasons:
                    observer_total += 1
                    if len(active_reasons) > 1:
                        observer_with_other += 1
                    else:
                        observer_only += 1
                if len(examples) < 10:
                    examples.append(
                        {
                            "date": str(row.get("date") or ""),
                            "record_id": str(row.get("record_id") or ""),
                            "stock_code": str(row.get("stock_code") or ""),
                            "stock_name": str(row.get("stock_name") or ""),
                            "stage": str(row.get("stage") or ""),
                            "group": str(row.get("group") or ""),
                            "reasons": active_reasons,
                            "orderbook_micro_state": str(
                                row.get("orderbook_micro_state") or ""
                            ),
                            "swing_micro_advice": str(
                                row.get("swing_micro_advice") or ""
                            ),
                            "orderbook_micro_ready": bool(
                                row.get("orderbook_micro_ready", False)
                            ),
                            "orderbook_micro_observer_healthy": bool(
                                row.get("orderbook_micro_observer_healthy", False)
                            ),
                        }
                    )
            reason_combination_counts = dict(combination_counter)
            reason_combination_unique_record_counts = {
                key: len(values) for key, values in combination_records.items()
            }
            stale_missing_group_counts = dict(group_counter)
            stale_missing_group_unique_record_counts = {
                key: len(values) for key, values in group_records.items()
            }
            stale_missing_stage_counts = dict(stage_counter)
            stale_missing_unique_record_count = len(all_records)
            observer_unhealthy_overlap = {
                "observer_unhealthy_total": observer_total,
                "observer_unhealthy_with_other_reason": observer_with_other,
                "observer_unhealthy_only": observer_only,
            }
    if stale_missing > 0:
        stale_ratio = round(stale_missing / max(ofi_qi_rows, 1), 4)
        active_reasons = ", ".join(
            f"{reason}={count}" for reason, count in reason_counts.items() if count
        )
        warning = (
            f"OFI/QI stale/missing ratio: {stale_ratio} ({stale_missing}/{ofi_qi_rows})"
        )
        if active_reasons:
            warning = f"{warning}; reasons: {active_reasons}"
        if stale_ratio > 0.3:
            warnings.append(warning)

    def _false_count(df: pd.DataFrame, column: str) -> int:
        if df.empty or column not in df:
            return 0
        return int((df[column] == False).sum())

    def _true_count(df: pd.DataFrame, column: str) -> int:
        if df.empty or column not in df:
            return 0
        return int((df[column] == True).sum())

    def _authority_counts(df: pd.DataFrame) -> dict[str, int]:
        if df.empty or "decision_authority" not in df:
            return {}
        return {
            str(key): int(value)
            for key, value in df["decision_authority"]
            .fillna("")
            .replace("", "unknown")
            .value_counts()
            .to_dict()
            .items()
        }

    sim_probe_provenance = {
        "trade_fact_actual_order_submitted_false": _false_count(
            trade_fact, "actual_order_submitted"
        ),
        "trade_fact_broker_order_forbidden_true": _true_count(
            trade_fact, "broker_order_forbidden"
        ),
        "sequence_fact_actual_order_submitted_false": _false_count(
            sequence_fact, "actual_order_submitted"
        ),
        "sequence_fact_broker_order_forbidden_true": _true_count(
            sequence_fact, "broker_order_forbidden"
        ),
        "ofi_qi_fact_actual_order_submitted_false": _false_count(
            ofi_qi_fact, "actual_order_submitted"
        ),
        "ofi_qi_fact_broker_order_forbidden_true": _true_count(
            ofi_qi_fact, "broker_order_forbidden"
        ),
        "trade_fact_decision_authority_counts": _authority_counts(trade_fact),
        "sequence_fact_decision_authority_counts": _authority_counts(sequence_fact),
        "ofi_qi_fact_decision_authority_counts": _authority_counts(ofi_qi_fact),
    }

    return {
        "schema_version": SCHEMA_VERSION,
        "analysis_window": {
            "start": target_dates[0] if target_dates else "",
            "end": target_dates[-1] if target_dates else "",
        },
        "fact_counts": {
            "swing_trade_fact_rows": trade_rows,
            "swing_lifecycle_funnel_fact_rows": funnel_rows,
            "swing_sequence_fact_rows": seq_rows,
            "swing_ofi_qi_fact_rows": ofi_qi_rows,
        },
        "completed_trades": completed,
        "valid_profit_trades": valid_profit,
        "ofi_qi_quality": {
            "sample_count": ofi_qi_rows,
            "stale_missing_count": stale_missing,
            "stale_missing_unique_record_count": stale_missing_unique_record_count,
            "stale_missing_ratio": (
                round(stale_missing / max(ofi_qi_rows, 1), 4) if ofi_qi_rows else 0.0
            ),
            "reason_counts": reason_counts,
            "reason_ratios": reason_ratios,
            "reason_combination_counts": reason_combination_counts,
            "reason_combination_unique_record_counts": reason_combination_unique_record_counts,
            "stale_missing_group_counts": stale_missing_group_counts,
            "stale_missing_group_unique_record_counts": stale_missing_group_unique_record_counts,
            "stale_missing_stage_counts": stale_missing_stage_counts,
            "observer_unhealthy_overlap": observer_unhealthy_overlap,
            "examples": examples,
        },
        "sim_probe_provenance": sim_probe_provenance,
        "warnings": warnings,
    }


def generate_data_quality_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# DeepSeek Swing Pattern Lab - Data Quality Report",
        "",
        f"## Analysis Window: {report['analysis_window']['start']} ~ {report['analysis_window']['end']}",
        "",
        "## Fact Table Row Counts",
        "",
        f"- swing_trade_fact: `{report['fact_counts']['swing_trade_fact_rows']}`",
        f"- swing_lifecycle_funnel_fact: `{report['fact_counts']['swing_lifecycle_funnel_fact_rows']}`",
        f"- swing_sequence_fact: `{report['fact_counts']['swing_sequence_fact_rows']}`",
        f"- swing_ofi_qi_fact: `{report['fact_counts']['swing_ofi_qi_fact_rows']}`",
        f"- completed_trades: `{report['completed_trades']}`",
        f"- valid_profit_trades: `{report['valid_profit_trades']}`",
        "",
    ]
    ofi_qi_quality = (
        report.get("ofi_qi_quality")
        if isinstance(report.get("ofi_qi_quality"), dict)
        else {}
    )
    if ofi_qi_quality:
        lines.extend(
            [
                "## OFI/QI Quality",
                "",
                f"- stale_missing_count: `{ofi_qi_quality.get('stale_missing_count', 0)}`",
                f"- stale_missing_unique_record_count: `{ofi_qi_quality.get('stale_missing_unique_record_count', 0)}`",
                f"- stale_missing_ratio: `{ofi_qi_quality.get('stale_missing_ratio', 0.0)}`",
                f"- reason_counts: `{ofi_qi_quality.get('reason_counts', {})}`",
                f"- reason_combination_counts: `{ofi_qi_quality.get('reason_combination_counts', {})}`",
                f"- reason_combination_unique_record_counts: `{ofi_qi_quality.get('reason_combination_unique_record_counts', {})}`",
                f"- stale_missing_group_counts: `{ofi_qi_quality.get('stale_missing_group_counts', {})}`",
                f"- stale_missing_group_unique_record_counts: `{ofi_qi_quality.get('stale_missing_group_unique_record_counts', {})}`",
                f"- observer_unhealthy_overlap: `{ofi_qi_quality.get('observer_unhealthy_overlap', {})}`",
                "",
            ]
        )
    sim_probe_provenance = (
        report.get("sim_probe_provenance")
        if isinstance(report.get("sim_probe_provenance"), dict)
        else {}
    )
    if sim_probe_provenance:
        lines.extend(
            [
                "## Sim/Probe Provenance",
                "",
                f"- trade_fact_actual_order_submitted_false: `{sim_probe_provenance.get('trade_fact_actual_order_submitted_false', 0)}`",
                f"- trade_fact_broker_order_forbidden_true: `{sim_probe_provenance.get('trade_fact_broker_order_forbidden_true', 0)}`",
                f"- sequence_fact_actual_order_submitted_false: `{sim_probe_provenance.get('sequence_fact_actual_order_submitted_false', 0)}`",
                f"- sequence_fact_broker_order_forbidden_true: `{sim_probe_provenance.get('sequence_fact_broker_order_forbidden_true', 0)}`",
                f"- ofi_qi_fact_actual_order_submitted_false: `{sim_probe_provenance.get('ofi_qi_fact_actual_order_submitted_false', 0)}`",
                f"- ofi_qi_fact_broker_order_forbidden_true: `{sim_probe_provenance.get('ofi_qi_fact_broker_order_forbidden_true', 0)}`",
                f"- trade_fact_decision_authority_counts: `{sim_probe_provenance.get('trade_fact_decision_authority_counts', {})}`",
                f"- sequence_fact_decision_authority_counts: `{sim_probe_provenance.get('sequence_fact_decision_authority_counts', {})}`",
                f"- ofi_qi_fact_decision_authority_counts: `{sim_probe_provenance.get('ofi_qi_fact_decision_authority_counts', {})}`",
                "",
            ]
        )
    if report.get("warnings"):
        lines.extend(["## Warnings", ""])
        for w in report["warnings"]:
            lines.append(f"- {w}")
        lines.append("")
    else:
        lines.extend(["## Warnings", "", "- none", ""])
    return "\n".join(lines)


def write_fact_tables(
    trade_fact: pd.DataFrame,
    funnel_fact: pd.DataFrame,
    sequence_fact: pd.DataFrame,
    ofi_qi_fact: pd.DataFrame,
) -> None:
    trade_fact.to_csv(OUTPUT_DIR / "swing_trade_fact.csv", index=False)
    funnel_fact.to_csv(OUTPUT_DIR / "swing_lifecycle_funnel_fact.csv", index=False)
    sequence_fact.to_csv(OUTPUT_DIR / "swing_sequence_fact.csv", index=False)
    ofi_qi_fact.to_csv(OUTPUT_DIR / "swing_ofi_qi_fact.csv", index=False)


def main() -> int:
    target_dates = _date_range()
    print(
        f"Preparing dataset for {len(target_dates)} dates: {target_dates[0]} ~ {target_dates[-1]}"
    )

    trade_fact = build_swing_trade_fact(target_dates)
    funnel_fact = build_swing_lifecycle_funnel_fact(target_dates)
    sequence_fact = build_swing_sequence_fact(target_dates)
    ofi_qi_fact = build_swing_ofi_qi_fact(target_dates)

    write_fact_tables(trade_fact, funnel_fact, sequence_fact, ofi_qi_fact)

    quality = build_data_quality_report(
        trade_fact, funnel_fact, sequence_fact, ofi_qi_fact, target_dates
    )
    quality_path = OUTPUT_DIR / "data_quality_report.json"
    quality_path.write_text(
        json.dumps(quality, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md_path = OUTPUT_DIR / "data_quality_report.md"
    md_path.write_text(generate_data_quality_markdown(quality), encoding="utf-8")

    manifest = {
        "schema_version": SCHEMA_VERSION,
        "run_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "analysis_window": {
            "start": target_dates[0],
            "end": target_dates[-1] if target_dates else "",
        },
        "outputs": {
            "swing_trade_fact": str(OUTPUT_DIR / "swing_trade_fact.csv"),
            "swing_lifecycle_funnel_fact": str(
                OUTPUT_DIR / "swing_lifecycle_funnel_fact.csv"
            ),
            "swing_sequence_fact": str(OUTPUT_DIR / "swing_sequence_fact.csv"),
            "swing_ofi_qi_fact": str(OUTPUT_DIR / "swing_ofi_qi_fact.csv"),
            "data_quality_report_json": str(quality_path),
            "data_quality_report_md": str(md_path),
        },
        "fact_counts": {
            "trade_rows": len(trade_fact),
            "funnel_rows": len(funnel_fact),
            "sequence_rows": len(sequence_fact),
            "ofi_qi_rows": len(ofi_qi_fact),
        },
    }
    manifest_path = OUTPUT_DIR / "run_manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    print(f"Fact tables written to {OUTPUT_DIR}")
    print(f"  trade_fact: {len(trade_fact)} rows")
    print(f"  funnel_fact: {len(funnel_fact)} rows")
    print(f"  sequence_fact: {len(sequence_fact)} rows")
    print(f"  ofi_qi_fact: {len(ofi_qi_fact)} rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
