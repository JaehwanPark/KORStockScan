"""Postclose scale-in incremental counterfactual EV producer.

Computes ADD vs NO_ADD incremental PnL for every sim scale-in decision
over 10min/30min/60min/final-liquidation horizons.

Input:
  - pipeline_events_{date}.jsonl / .jsonl.gz
  - scalp_sim_scale_in_counterfactual_started events (new instrumentation)
  - For backfill: scalp_sim_scale_in_order_assumed_filled / _unfilled events

Output:
  - scale_in_incremental_counterfactual_{date}.json
  - scale_in_incremental_counterfactual_{date}.md
"""

from __future__ import annotations

import argparse
import gzip
import json
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from src.engine.automation.source_quality_clean_baseline import (
    clean_baseline_policy,
    filter_allowed_dates,
    is_date_allowed,
)
from src.engine.trade_profit import calculate_net_realized_pnl
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import existing_or_gzip_path

REPORT_DIR = DATA_DIR / "report" / "scale_in_incremental_counterfactual"
PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"
SCHEMA_VERSION = 1
REPORT_TYPE = "scale_in_incremental_counterfactual"
SAMPLE_FLOOR = 5
PROMOTE_SAMPLE_FLOOR = 10
POSITIVE_INCREMENTAL_EV_PCT = 0.30
NEGATIVE_INCREMENTAL_EV_PCT = -0.30
EV_LABEL_VERSION = "incremental_counterfactual_v2"
COUNTERFACTUAL_METHOD = "treatment_path_added_tranche_return"
RUNTIME_AUTHORITY_METHOD = "paired_add_no_add_lifecycle_replay"

HORIZONS = {
    "10min": 10 * 60,
    "30min": 30 * 60,
    "60min": 60 * 60,
    "final": None,
}

FORBIDDEN_USES = [
    "real order enablement",
    "threshold mutation",
    "provider change",
    "bot restart",
    "position cap release",
    "broker order submit",
    "real scale_in submit",
    "intraday threshold mutation",
]

COHORT_FIELDS = [
    "arm",
    "quote_touched",
    "first_add",
]


def report_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def _event_path(target_date: str) -> Path:
    plain = PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl"
    return plain if plain.exists() else plain.with_suffix(plain.suffix + ".gz")


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value in (None, "", "null", "none"):
            return default
        return float(value)
    except Exception:
        return default


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, "", "null", "none"):
            return default
        return int(float(value))
    except Exception:
        return default


def _iter_events(target_date: str) -> Iterable[dict[str, Any]]:
    path = existing_or_gzip_path(_event_path(target_date))
    if not path or not path.exists():
        return
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            try:
                row = json.loads(line)
            except Exception:
                continue
            if isinstance(row, dict):
                yield row


def _event_allowed_by_clean_baseline(
    event: dict[str, Any], policy: dict[str, Any]
) -> bool:
    baseline_text = str(policy.get("clean_tuning_baseline_ts_kst") or "")
    if not baseline_text:
        return True
    try:
        baseline = datetime.fromisoformat(
            baseline_text.replace("Z", "+00:00")
        ).timestamp()
    except Exception:
        return False
    emitted = _parse_emitted_at(event)
    return emitted > 0 and emitted >= baseline


def _has_sim_counterfactual_authority(event: dict[str, Any]) -> bool:
    fields = event.get("fields") if isinstance(event.get("fields"), dict) else {}
    stage = str(event.get("stage") or "")
    actual = fields.get("actual_order_submitted")
    broker_forbidden = fields.get("broker_order_forbidden")
    if stage == "scalp_sim_scale_in_counterfactual_started":
        return actual is False and broker_forbidden is True
    if stage in {
        "scalp_sim_scale_in_order_assumed_filled",
        "scalp_sim_scale_in_order_unfilled",
    }:
        return actual not in {True, "true", "True", 1} and broker_forbidden not in {
            False,
            "false",
            "False",
            0,
        }
    return False


def _parse_emitted_at(event: dict[str, Any]) -> float:
    text = str(event.get("emitted_at") or "")
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone(timedelta(hours=9)))
        return parsed.timestamp()
    except Exception:
        pass
    return 0.0


def _find_counterfactual_events(
    target_date: str,
    diagnostics: dict[str, int] | None = None,
) -> list[dict[str, Any]]:
    """Find scale_in_counterfactual_started events, or reconstruct from legacy events."""
    cf_events: list[dict[str, Any]] = []
    cf_decision_ids: set[str] = set()

    policy = clean_baseline_policy()
    events_by_sim: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in _iter_events(target_date):
        if not _event_allowed_by_clean_baseline(item, policy):
            continue
        fields = item.get("fields") if isinstance(item.get("fields"), dict) else {}
        sim_id = fields.get("sim_record_id")
        if not sim_id:
            continue
        stage = str(item.get("stage") or "")
        if stage.startswith("scalp_sim_"):
            events_by_sim[str(sim_id)].append(item)

    for item in _iter_events(target_date):
        if not _event_allowed_by_clean_baseline(item, policy):
            continue
        stage = str(item.get("stage") or "")
        fields = item.get("fields") if isinstance(item.get("fields"), dict) else {}

        if stage == "scalp_sim_scale_in_counterfactual_started":
            if not _has_sim_counterfactual_authority(item):
                continue
            cf_decision_id = str(fields.get("scale_in_decision_id") or "")
            if not cf_decision_id:
                if diagnostics is not None:
                    diagnostics["missing_scale_in_decision_id"] = (
                        diagnostics.get("missing_scale_in_decision_id", 0) + 1
                    )
                continue
            if cf_decision_id in cf_decision_ids:
                continue
            cf_decision_ids.add(cf_decision_id)
            cf_events.append(item)
            continue

    legacy_events = _reconstruct_counterfactual_from_legacy(target_date, events_by_sim)
    for item in legacy_events:
        fields = item.get("fields") if isinstance(item.get("fields"), dict) else {}
        decision_id = str(fields.get("scale_in_decision_id") or "")
        if not decision_id or decision_id in cf_decision_ids:
            continue
        cf_decision_ids.add(decision_id)
        cf_events.append(item)

    return cf_events


def _reconstruct_counterfactual_from_legacy(
    target_date: str, events_by_sim: dict[str, list[dict[str, Any]]]
) -> list[dict[str, Any]]:
    """Backfill: reconstruct counterfactual data from legacy scale-in events."""
    cf_events: list[dict[str, Any]] = []
    cf_decision_ids: set[str] = set()

    for sim_id, events in events_by_sim.items():
        for item in events:
            stage = str(item.get("stage") or "")
            if stage not in {
                "scalp_sim_scale_in_order_assumed_filled",
                "scalp_sim_scale_in_order_unfilled",
            }:
                continue
            if not _has_sim_counterfactual_authority(item):
                continue
            fields = item.get("fields") if isinstance(item.get("fields"), dict) else {}
            add_type = str(
                fields.get("add_type") or fields.get("scale_in_arm") or ""
            ).upper()
            if add_type not in ("AVG_DOWN", "PYRAMID"):
                if "avg_down" in stage.lower():
                    add_type = "AVG_DOWN"
                elif "pyramid" in stage.lower():
                    add_type = "PYRAMID"
                else:
                    continue

            emitted_at = _parse_emitted_at(item)
            ord_no = str(
                fields.get("ord_no")
                or fields.get("candidate_id")
                or f"{sim_id}:{emitted_at}"
            )
            decision_id = str(
                fields.get("scale_in_decision_id")
                or f"{sim_id}+{add_type}+{int(emitted_at * 1000)}"
            )
            if decision_id in cf_decision_ids:
                continue
            cf_decision_ids.add(decision_id)

            is_filled = stage == "scalp_sim_scale_in_order_assumed_filled"
            qty = _safe_int(fields.get("qty"), 0)
            fill_price = _safe_int(
                fields.get("assumed_fill_price") or fields.get("limit_price"), 0
            )
            prev_qty = _safe_int(fields.get("prev_buy_qty"), 0)
            prev_price = _safe_int(
                fields.get("prev_buy_price") or fields.get("buy_price"), 0
            )
            curr_price = _safe_int(fields.get("curr_price"), fill_price)

            if prev_price <= 0 and fill_price > 0:
                prev_price = fill_price

            proposed_notional = fill_price * qty if fill_price > 0 and qty > 0 else 0
            decision_profit_rate = (
                round((fill_price - prev_price) / prev_price * 100.0, 2)
                if prev_price > 0
                else 0.0
            )

            cf_event = {
                "stage": "scalp_sim_scale_in_counterfactual_started",
                "emitted_at": item.get("emitted_at"),
                "stock_code": item.get("stock_code"),
                "fields": {
                    "scale_in_decision_id": decision_id,
                    "sim_record_id": sim_id,
                    "candidate_id": ord_no,
                    "scale_in_arm": add_type,
                    "decision_time": emitted_at,
                    "decision_profit_rate": decision_profit_rate,
                    "pre_add_buy_price": prev_price,
                    "pre_add_buy_qty": prev_qty,
                    "proposed_add_price": fill_price,
                    "proposed_add_qty": qty,
                    "proposed_add_notional": proposed_notional,
                    "quote_touched": is_filled,
                    "treatment_state": (
                        "ADD_FILLED" if is_filled else "WOULD_ADD_UNFILLED"
                    ),
                    "control_state": "NO_ADD",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "runtime_effect": False,
                    "decision_authority": "sim_scale_in_counterfactual_only",
                    "source_provenance": "reconstructed_from_legacy_pipeline_event",
                },
            }
            cf_events.append(cf_event)

    return cf_events


def _find_evaluation_price(
    events: list[dict[str, Any]],
    decision_time: float,
    horizon_sec: int | None,
) -> float | None:
    """Find market price at evaluation horizon from pipeline events."""
    if horizon_sec is None:
        terminal_candidates: list[tuple[float, float]] = []
        for item in events:
            emitted = _parse_emitted_at(item)
            if emitted < decision_time:
                continue
            stage = str(item.get("stage") or "")
            if stage == "scalp_sim_sell_order_assumed_filled":
                fields = (
                    item.get("fields") if isinstance(item.get("fields"), dict) else {}
                )
                sell_price = _safe_int(
                    fields.get("assumed_fill_price") or fields.get("sell_price")
                )
                if sell_price and sell_price > 0:
                    terminal_candidates.append((emitted, float(sell_price)))
                    continue
                buy_price_for_profit = _safe_float(fields.get("buy_price"))
                profit_rate_str = fields.get("profit_rate") or fields.get(
                    "realized_profit_rate"
                )
                profit_rate = _safe_float(profit_rate_str)
                if (
                    buy_price_for_profit
                    and buy_price_for_profit > 0
                    and profit_rate is not None
                ):
                    terminal_candidates.append(
                        (
                            emitted,
                            float(buy_price_for_profit * (1.0 + profit_rate / 100.0)),
                        )
                    )
        terminal_candidates.sort(key=lambda item: item[0])
        return terminal_candidates[-1][1] if terminal_candidates else None

    target_time = decision_time + float(horizon_sec)
    candidates = []
    for item in events:
        emitted = _parse_emitted_at(item)
        if emitted < target_time:
            continue
        fields = item.get("fields") if isinstance(item.get("fields"), dict) else {}
        curr_price = _safe_int(fields.get("curr_price"))
        if curr_price and curr_price > 0:
            candidates.append((emitted, float(curr_price)))
        else:
            profit_rate = _safe_float(
                fields.get("profit_rate") or fields.get("trigger_profit_rate")
            )
            buy_price = _safe_int(fields.get("buy_price"))
            if profit_rate is not None and buy_price and buy_price > 0:
                eval_price = float(buy_price * (1.0 + profit_rate / 100.0))
                candidates.append((emitted, eval_price))

    if candidates:
        candidates.sort(key=lambda x: x[0])
        return candidates[0][1]
    return None


def _compute_incremental_pnl(
    pre_add_qty: int,
    pre_add_price: int,
    proposed_qty: int,
    proposed_price: int,
    eval_price: float,
) -> dict[str, Any]:
    """Compute incremental PnL for added shares."""
    no_add_pnl = calculate_net_realized_pnl(pre_add_price, int(eval_price), pre_add_qty)
    added_tranche_pnl = calculate_net_realized_pnl(
        proposed_price, int(eval_price), proposed_qty
    )
    add_pnl_total = no_add_pnl + added_tranche_pnl
    incremental_pnl_krw = added_tranche_pnl
    incremental_notional_ev_pct = (
        round(incremental_pnl_krw / (proposed_price * proposed_qty) * 100.0, 4)
        if proposed_price > 0 and proposed_qty > 0
        else None
    )
    return {
        "no_add_pnl_krw": no_add_pnl,
        "add_pnl_krw": add_pnl_total,
        "incremental_pnl_krw": incremental_pnl_krw,
        "incremental_notional_ev_pct": incremental_notional_ev_pct,
        "evaluation_price": eval_price,
    }


def build_report(target_date: str) -> dict[str, Any]:
    target_date = str(target_date).strip()
    clean_policy = clean_baseline_policy()
    if not is_date_allowed(target_date, clean_policy):
        return {
            "schema_version": SCHEMA_VERSION,
            "date": target_date,
            "report_type": REPORT_TYPE,
            "runtime_effect": False,
            "decision_authority": "sim_scale_in_counterfactual_only",
            "error": "date_excluded_by_clean_baseline_policy",
            "clean_baseline_policy": clean_policy,
            "rows": [],
            "summary": {},
        }

    source_diagnostics: dict[str, int] = {}
    cf_events = _find_counterfactual_events(target_date, source_diagnostics)
    if not cf_events:
        return {
            "schema_version": SCHEMA_VERSION,
            "date": target_date,
            "report_type": REPORT_TYPE,
            "runtime_effect": False,
            "decision_authority": "sim_scale_in_counterfactual_only",
            "error": "no_counterfactual_events_found",
            "source_quality_gate": (
                "pass_with_row_exclusions"
                if source_diagnostics
                else "clean_baseline_policy_sim_only_probe_events"
            ),
            "rows": [],
            "summary": {
                "counterfactual_event_count": 0,
                "source_quality_excluded_event_count": sum(source_diagnostics.values()),
                "source_quality_exclusion_reasons": source_diagnostics,
            },
        }

    events_by_sim: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in _iter_events(target_date):
        if not _event_allowed_by_clean_baseline(item, clean_policy):
            continue
        fields = item.get("fields") if isinstance(item.get("fields"), dict) else {}
        sim_id = fields.get("sim_record_id")
        if sim_id:
            events_by_sim[str(sim_id)].append(item)

    rows: list[dict[str, Any]] = []
    incomplete_count = 0
    incomplete_reasons: dict[str, int] = defaultdict(int)

    for cf_event in cf_events:
        fields = (
            cf_event.get("fields") if isinstance(cf_event.get("fields"), dict) else {}
        )
        sim_id = str(fields.get("sim_record_id") or "")
        decision_id = str(fields.get("scale_in_decision_id") or "")
        decision_time = _safe_float(fields.get("decision_time"), 0.0)
        pre_add_qty = _safe_int(fields.get("pre_add_buy_qty"))
        pre_add_price = _safe_int(fields.get("pre_add_buy_price"))
        proposed_qty = _safe_int(fields.get("proposed_add_qty"))
        proposed_price = _safe_int(fields.get("proposed_add_price"))
        proposed_notional = _safe_int(fields.get("proposed_add_notional"))

        if proposed_qty <= 0 or proposed_price <= 0:
            rows.append(
                {
                    "scale_in_decision_id": decision_id,
                    "sim_record_id": sim_id,
                    "status": "counterfactual_input_incomplete",
                    "reason": "missing_qty_or_price",
                }
            )
            incomplete_count += 1
            incomplete_reasons["missing_qty_or_price"] += 1
            continue

        sim_events = events_by_sim.get(sim_id, [])
        row = {
            "scale_in_decision_id": decision_id,
            "sim_record_id": sim_id,
            "candidate_id": str(fields.get("candidate_id") or ""),
            "scale_in_arm": str(fields.get("scale_in_arm") or ""),
            "decision_time": decision_time,
            "decision_profit_rate": _safe_float(fields.get("decision_profit_rate")),
            "pre_add_buy_price": pre_add_price,
            "pre_add_buy_qty": pre_add_qty,
            "proposed_add_price": proposed_price,
            "proposed_add_qty": proposed_qty,
            "proposed_add_notional": proposed_notional,
            "quote_touched": bool(fields.get("quote_touched")),
            "execution_arm": str(
                fields.get("execution_arm") or "LEGACY_PASSIVE"
            ).upper(),
            "treatment_state": (
                "ADD_FILLED"
                if bool(fields.get("quote_touched"))
                else "WOULD_ADD_UNFILLED"
            ),
            "runtime_ev_eligible": bool(
                fields.get("runtime_ev_eligible") is True
                and str(fields.get("execution_arm") or "").upper()
                == "MARKETABLE_OBSERVATION"
                and fields.get("quote_touched") is True
            ),
            "counterfactual_method": COUNTERFACTUAL_METHOD,
            "runtime_authority_ready": False,
            "runtime_authority_block_reason": "paired_add_lifecycle_replay_not_implemented",
            "control_state": "NO_ADD",
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "runtime_effect": False,
            "decision_authority": "sim_scale_in_counterfactual_only",
            "source_provenance": str(
                fields.get("source_provenance") or "instrumentation"
            ),
            "horizons": {},
        }

        all_horizons_complete = True
        for horizon_name, horizon_sec in HORIZONS.items():
            eval_price = _find_evaluation_price(sim_events, decision_time, horizon_sec)
            if eval_price is None:
                row["horizons"][horizon_name] = {
                    "status": "horizon_incomplete",
                    "reason": "no_evaluation_price",
                }
                all_horizons_complete = False
                incomplete_reasons[f"horizon_incomplete_{horizon_name}"] += 1
            else:
                result = _compute_incremental_pnl(
                    pre_add_qty, pre_add_price, proposed_qty, proposed_price, eval_price
                )
                row["horizons"][horizon_name] = result

        row["all_horizons_complete"] = all_horizons_complete
        row["final_horizon_complete"] = (
            row["horizons"].get("final", {}).get("incremental_notional_ev_pct")
            is not None
        )
        # This is an added-tranche observation evaluated at the canonical
        # NO_ADD exit, not a replay of the complete ADD lifecycle.
        row["runtime_authority_ready"] = False
        row["runtime_authority_block_reason"] = (
            "paired_add_lifecycle_replay_not_implemented"
            if row["runtime_ev_eligible"] and row["final_horizon_complete"]
            else "marketable_primary_or_final_control_label_missing"
        )
        if not all_horizons_complete:
            incomplete_count += 1

        rows.append(row)

    summary = _build_summary(rows, target_date, incomplete_count, incomplete_reasons)
    summary["candidate_funnel_by_arm"] = _candidate_funnel_by_arm(
        target_date, clean_policy
    )
    summary["source_quality_excluded_event_count"] = sum(source_diagnostics.values())
    summary["source_quality_exclusion_reasons"] = source_diagnostics
    cohorts = _build_cohorts(rows)

    return {
        "schema_version": SCHEMA_VERSION,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "report_type": REPORT_TYPE,
        "metric_role": "sim_probe_ev",
        "decision_authority": "sim_scale_in_counterfactual_only",
        "primary_decision_metric": "incremental_notional_ev_pct",
        "scale_in_ev_label_version": EV_LABEL_VERSION,
        "runtime_effect": False,
        "window_policy": "daily_only",
        "sample_floor": SAMPLE_FLOOR,
        "primary_authority_cohort": "ADD_FILLED",
        "counterfactual_method": COUNTERFACTUAL_METHOD,
        "runtime_authority_method_required": RUNTIME_AUTHORITY_METHOD,
        "runtime_authority_ready": False,
        "forbidden_uses": FORBIDDEN_USES,
        "source_quality_gate": (
            "pass_with_row_exclusions"
            if source_diagnostics
            else "clean_baseline_policy_sim_only_probe_events"
        ),
        "clean_baseline_policy": clean_policy,
        "summary": summary,
        "cohorts": cohorts,
        "rows": rows,
    }


def _candidate_funnel_by_arm(
    target_date: str, clean_policy: dict[str, Any]
) -> dict[str, dict[str, int]]:
    funnel: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for item in _iter_events(target_date):
        if not _event_allowed_by_clean_baseline(item, clean_policy):
            continue
        stage = str(item.get("stage") or "")
        fields = item.get("fields") if isinstance(item.get("fields"), dict) else {}
        arm = str(
            fields.get("scale_in_arm") or fields.get("add_type") or "unknown"
        ).upper()
        state = str(fields.get("scale_in_candidate_funnel_state") or "")
        if stage == "scalp_sim_panic_scale_in_blocked":
            state = "panic_blocked"
        elif stage == "scale_in_price_guard_block" and fields.get("sim_record_id"):
            state = "price_guard_blocked"
        elif stage == "scale_in_qty_block" and fields.get("sim_record_id"):
            state = "qty_guard_blocked"
        if state:
            funnel[arm][state] += 1
    return {arm: dict(counts) for arm, counts in funnel.items()}


def _build_summary(
    rows: list[dict[str, Any]],
    target_date: str,
    incomplete_count: int,
    incomplete_reasons: dict[str, int],
) -> dict[str, Any]:
    final_complete_rows = [r for r in rows if r.get("final_horizon_complete")]
    all_horizons_complete_rows = [r for r in rows if r.get("all_horizons_complete")]
    arm_counts: dict[str, int] = defaultdict(int)
    execution_arm_counts: dict[str, int] = defaultdict(int)
    filled_count = 0
    unfilled_count = 0

    for row in rows:
        arm = str(row.get("scale_in_arm") or "unknown")
        arm_counts[arm] += 1
        execution_arm_counts[str(row.get("execution_arm") or "unknown")] += 1
        if row.get("quote_touched"):
            filled_count += 1
        else:
            unfilled_count += 1

    horizon_ev: dict[str, dict[str, Any]] = {}
    for horizon_name in HORIZONS:
        ev_values = []
        for row in rows:
            if not row.get("runtime_ev_eligible"):
                continue
            horizon = row.get("horizons", {}).get(horizon_name)
            if isinstance(horizon, dict):
                ev = horizon.get("incremental_notional_ev_pct")
                if ev is not None:
                    ev_values.append(float(ev))
        if ev_values:
            avg_ev = round(sum(ev_values) / len(ev_values), 4)
            win_count = sum(1 for ev in ev_values if ev > 0)
            horizon_ev[horizon_name] = {
                "sample": len(ev_values),
                "incremental_notional_ev_pct": avg_ev,
                "diagnostic_win_rate": (
                    round(win_count / len(ev_values), 4) if ev_values else None
                ),
            }
        else:
            horizon_ev[horizon_name] = {
                "sample": 0,
                "incremental_notional_ev_pct": None,
                "diagnostic_win_rate": None,
            }

    return {
        "counterfactual_event_count": len(rows),
        "complete_row_count": len(final_complete_rows),
        "final_horizon_complete_row_count": len(final_complete_rows),
        "all_horizons_complete_row_count": len(all_horizons_complete_rows),
        "rows_with_any_horizon_gap_count": incomplete_count,
        "incomplete_row_count": incomplete_count,
        "incomplete_reasons": dict(incomplete_reasons),
        "arm_counts": dict(arm_counts),
        "execution_arm_counts": dict(execution_arm_counts),
        "filled_count": filled_count,
        "unfilled_count": unfilled_count,
        "horizon_summary": horizon_ev,
    }


def _build_cohorts(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Build cohort-separated summaries."""
    final_complete_rows = [r for r in rows if r.get("final_horizon_complete")]

    cohorts: dict[str, Any] = {
        "by_arm": {},
        "by_quote_touched": {},
        "combined": {},
    }

    for arm in ("AVG_DOWN", "PYRAMID"):
        arm_rows = [
            r
            for r in final_complete_rows
            if r.get("runtime_ev_eligible")
            and str(r.get("scale_in_arm") or "").upper() == arm
        ]
        cohorts["by_arm"][arm] = _cohort_ev_summary(arm_rows)

    for touched_label, touched_bool in [("filled", True), ("unfilled", False)]:
        touched_rows = [
            r for r in final_complete_rows if r.get("quote_touched") == touched_bool
        ]
        cohorts["by_quote_touched"][touched_label] = _cohort_ev_summary(touched_rows)

    cohorts["combined_primary_filled"] = _cohort_ev_summary(
        [r for r in final_complete_rows if r.get("runtime_ev_eligible")]
    )
    return cohorts


def _cohort_ev_summary(cohort_rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not cohort_rows:
        return {"sample": 0, "horizons": {}}

    horizon_summary: dict[str, dict[str, Any]] = {}
    for horizon_name in HORIZONS:
        ev_values = []
        pnl_values = []
        for row in cohort_rows:
            horizon = row.get("horizons", {}).get(horizon_name)
            if isinstance(horizon, dict):
                ev = horizon.get("incremental_notional_ev_pct")
                pnl = horizon.get("incremental_pnl_krw")
                if ev is not None:
                    ev_values.append(float(ev))
                if pnl is not None:
                    pnl_values.append(float(pnl))
        if ev_values:
            win_count = sum(1 for ev in ev_values if ev > 0)
            horizon_summary[horizon_name] = {
                "sample": len(ev_values),
                "incremental_notional_ev_pct": round(
                    sum(ev_values) / len(ev_values), 4
                ),
                "diagnostic_win_rate": round(win_count / len(ev_values), 4),
                "avg_incremental_pnl_krw": (
                    round(sum(pnl_values) / len(pnl_values)) if pnl_values else None
                ),
            }
        else:
            horizon_summary[horizon_name] = {"sample": 0}

    return {
        "sample": len(cohort_rows),
        "horizons": horizon_summary,
    }


def write_outputs(report: dict[str, Any]) -> tuple[Path, Path]:
    target_date = str(report.get("date") or "")
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    json_path, md_path = report_paths(target_date)
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    md_path.write_text(_render_markdown(report), encoding="utf-8")
    return json_path, md_path


def _render_markdown(report: dict[str, Any]) -> str:
    summary = report.get("summary") if isinstance(report.get("summary"), dict) else {}
    cohorts = report.get("cohorts") if isinstance(report.get("cohorts"), dict) else {}
    lines = [
        f"# Scale-In Incremental Counterfactual - {report.get('date')}",
        "",
        "## Contract",
        f"- ev_label_version: `{report.get('scale_in_ev_label_version')}`",
        f"- primary_decision_metric: `{report.get('primary_decision_metric')}`",
        f"- decision_authority: `{report.get('decision_authority')}`",
        f"- runtime_effect: `{report.get('runtime_effect')}`",
        "",
        "## Summary",
        f"- counterfactual_event_count: `{summary.get('counterfactual_event_count')}`",
        f"- complete_row_count: `{summary.get('complete_row_count')}`",
        f"- incomplete_row_count: `{summary.get('incomplete_row_count')}`",
        f"- arm_counts: `{summary.get('arm_counts')}`",
        f"- execution_arm_counts: `{summary.get('execution_arm_counts')}`",
        f"- filled_count: `{summary.get('filled_count')}`",
        f"- unfilled_count: `{summary.get('unfilled_count')}`",
        f"- candidate_funnel_by_arm: `{summary.get('candidate_funnel_by_arm')}`",
        f"- incomplete_reasons: `{summary.get('incomplete_reasons')}`",
        "",
        "## Horizon Summary",
    ]
    horizon_summary = (
        summary.get("horizon_summary")
        if isinstance(summary.get("horizon_summary"), dict)
        else {}
    )
    for horizon_name in HORIZONS:
        h = horizon_summary.get(horizon_name, {})
        lines.append(
            f"- `{horizon_name}`: sample={h.get('sample')}, "
            f"ev={h.get('incremental_notional_ev_pct')}, "
            f"win_rate={h.get('diagnostic_win_rate')}"
        )

    lines.extend(["", "## Cohort Summary", ""])
    for cohort_name, cohort_data in cohorts.items():
        if not isinstance(cohort_data, dict):
            continue
        lines.append(f"### {cohort_name}")
        for key, value in cohort_data.items():
            if not isinstance(value, dict):
                continue
            h = value.get("horizons", {})
            final_h = h.get("final", {})
            lines.append(
                f"- `{key}`: sample={value.get('sample')}, "
                f"final_ev={final_h.get('incremental_notional_ev_pct')}, "
                f"final_win_rate={final_h.get('diagnostic_win_rate')}"
            )
    return "\n".join(lines)


def build_backfill_report(
    target_date: str,
    *,
    start_date: str | None = None,
    end_date: str | None = None,
) -> dict[str, Any]:
    """Aggregate multiple daily reports for rolling/MTD windows."""
    start = str(start_date or target_date).strip()
    end = str(end_date or target_date).strip()
    dates = []
    current = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")
    while current <= end_dt:
        dates.append(current.strftime("%Y-%m-%d"))
        current += timedelta(days=1)

    all_rows: list[dict[str, Any]] = []
    clean_policy = clean_baseline_policy()
    allowed_dates, _ = filter_allowed_dates(dates, clean_policy)

    for source_date in allowed_dates:
        daily = build_report(source_date)
        if daily.get("error"):
            continue
        daily_rows = daily.get("rows", [])
        for row in daily_rows:
            row.setdefault("source_date", source_date)
        all_rows.extend(daily_rows)

    incomplete_reasons: dict[str, int] = defaultdict(int)
    incomplete_count = 0
    for row in all_rows:
        if not row.get("all_horizons_complete"):
            incomplete_count += 1
        for horizon_name, horizon_data in (row.get("horizons") or {}).items():
            if (
                isinstance(horizon_data, dict)
                and horizon_data.get("status") == "horizon_incomplete"
            ):
                incomplete_reasons[f"horizon_incomplete_{horizon_name}"] += 1
        if row.get("status") == "counterfactual_input_incomplete":
            incomplete_reasons[
                str(row.get("reason") or "counterfactual_input_incomplete")
            ] += 1
    summary = _build_summary(
        all_rows, target_date, incomplete_count, incomplete_reasons
    )
    cohorts = _build_cohorts(all_rows)

    return {
        "schema_version": SCHEMA_VERSION,
        "date": target_date,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "report_type": REPORT_TYPE,
        "metric_role": "sim_probe_ev",
        "decision_authority": "sim_scale_in_counterfactual_only",
        "primary_decision_metric": "incremental_notional_ev_pct",
        "scale_in_ev_label_version": EV_LABEL_VERSION,
        "counterfactual_method": COUNTERFACTUAL_METHOD,
        "runtime_authority_method_required": RUNTIME_AUTHORITY_METHOD,
        "runtime_authority_ready": False,
        "window_policy": f"{start}_to_{end}",
        "runtime_effect": False,
        "sample_floor": SAMPLE_FLOOR,
        "forbidden_uses": FORBIDDEN_USES,
        "clean_baseline_policy": clean_policy,
        "source_dates": allowed_dates,
        "summary": summary,
        "cohorts": cohorts,
        "rows": all_rows,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build scale-in incremental counterfactual report."
    )
    parser.add_argument("--date", dest="target_date", default=date.today().isoformat())
    parser.add_argument("--start-date")
    parser.add_argument("--end-date")
    parser.add_argument(
        "--backfill",
        action="store_true",
        help="Aggregate daily reports into rolling/MTD window",
    )
    args = parser.parse_args(argv)
    target_date = str(args.target_date).strip()

    if args.backfill or args.start_date or args.end_date:
        report = build_backfill_report(
            target_date,
            start_date=args.start_date,
            end_date=args.end_date,
        )
    else:
        report = build_report(target_date)

    json_path, md_path = write_outputs(report)
    print(f"Wrote {json_path} ({len(report.get('rows', []))} rows)")
    print(f"Wrote {md_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
