"""Evaluate rising-missed TP1 policy alternatives with direct paired economics.

The historical module name remains the CLI compatibility surface.  The report no
longer builds classifier priors from retired lifecycle artifacts.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from src.engine.monitoring.widget_comparison_cost import comparison_cost_contract
from src.utils.constants import DATA_DIR
from src.utils.market_day import is_krx_trading_day

KST = timezone(timedelta(hours=9))
REPORT_DIR = DATA_DIR / "report"
OUTPUT_DIR = REPORT_DIR / "rising_missed_classifier_prior"
FEEDBACK_DIR = REPORT_DIR / "rising_missed_intraday_feedback"
CLEAN_BASELINE_DATE = date(2026, 6, 5)
MAX_SOURCE_BYTES = 64 * 1024 * 1024
MAX_SOURCE_DAYS = 20
CALIBRATION_SAMPLE_FLOOR = 30
CALIBRATION_DAY_FLOOR = 3
HOLDOUT_SAMPLE_FLOOR = 20
HOLDOUT_DAY_FLOOR = 2
BASELINE_POLICY = {
    "positive_support_min": 2,
    "spread_caution_ratio": 0.002,
    "chase_delta_pct": 3.0,
}
CANDIDATES = (
    ("positive_support_min", 1),
    ("positive_support_min", 3),
    ("spread_caution_ratio", 0.0015),
    ("spread_caution_ratio", 0.0025),
    ("chase_delta_pct", 2.5),
    ("chase_delta_pct", 3.5),
)
RUNTIME_ENV_KEYS = {
    "positive_support_min": "KORSTOCKSCAN_RISING_MISSED_TP1_POSITIVE_SUPPORT_MIN",
    "spread_caution_ratio": "KORSTOCKSCAN_RISING_MISSED_TP1_SPREAD_CAUTION_RATIO",
    "chase_delta_pct": "KORSTOCKSCAN_RISING_MISSED_TP1_CHASE_DELTA_PCT",
}
FORBIDDEN_USES = [
    "real_order_submission",
    "broker_guard_bypass",
    "order_guard_relaxation",
    "quantity_guard_relaxation",
    "provider_route_change",
    "bot_restart",
    "hard_safety_relaxation",
]


def _now() -> str:
    return datetime.now(KST).isoformat(timespec="seconds")


def _sha_bytes(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _sha_json(value: Any) -> str:
    return _sha_bytes(
        json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode()
    )


def _float(value: Any) -> float | None:
    try:
        if value in (None, "", "-"):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _atomic_write(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
    ) as handle:
        temporary = Path(handle.name)
        handle.write(body)
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)


def _next_trading_date(source_date: str) -> str:
    current = date.fromisoformat(source_date)
    for _ in range(14):
        current += timedelta(days=1)
        if is_krx_trading_day(current):
            return current.isoformat()
    raise ValueError(f"next_krx_trading_date_unavailable:{source_date}")


def _source_paths(target_date: str, explicit: Iterable[Path] = ()) -> list[Path]:
    explicit_paths = [Path(path) for path in explicit]
    if explicit_paths:
        return explicit_paths
    maximum = date.fromisoformat(target_date)
    rows: list[tuple[date, Path]] = []
    for path in FEEDBACK_DIR.glob("rising_missed_intraday_feedback_*.json"):
        suffix = path.stem.rsplit("_", 1)[-1]
        try:
            report_date = date.fromisoformat(suffix)
        except ValueError:
            continue
        if CLEAN_BASELINE_DATE <= report_date <= maximum:
            rows.append((report_date, path))
    return [path for _, path in sorted(rows)[-MAX_SOURCE_DAYS:]]


def _read_source(
    path: Path, *, maximum_date: date
) -> tuple[dict[str, Any], dict[str, Any]]:
    receipt: dict[str, Any] = {
        "path": str(path.resolve()),
        "exists": False,
        "state": "missing",
        "size_bytes": None,
        "mtime_ns": None,
        "sha256": None,
        "schema": None,
        "target_date": None,
        "authority": None,
    }
    try:
        stat_before = path.stat()
        receipt.update(
            exists=True, size_bytes=stat_before.st_size, mtime_ns=stat_before.st_mtime_ns
        )
        if stat_before.st_size > MAX_SOURCE_BYTES:
            receipt["state"] = "blocked_oversized"
            return {}, receipt
        raw = path.read_bytes()
        stat_after = path.stat()
    except OSError as exc:
        receipt["state"] = f"unreadable:{type(exc).__name__}"
        return {}, receipt
    receipt["sha256"] = _sha_bytes(raw)
    if (stat_before.st_size, stat_before.st_mtime_ns) != (
        stat_after.st_size,
        stat_after.st_mtime_ns,
    ):
        receipt["state"] = "blocked_source_changed_during_read"
        return {}, receipt
    try:
        payload = json.loads(raw)
    except (json.JSONDecodeError, ValueError):
        receipt["state"] = "malformed_json"
        return {}, receipt
    if not isinstance(payload, dict):
        receipt["state"] = "malformed_object_required"
        return {}, receipt
    receipt.update(
        schema=payload.get("schema_version"),
        target_date=payload.get("target_date"),
        authority=payload.get("decision_authority"),
    )
    if payload.get("schema_version") != 1:
        receipt["state"] = "schema_version_mismatch"
        return {}, receipt
    if payload.get("report_type") != "rising_missed_intraday_feedback":
        receipt["state"] = "schema_mismatch"
        return {}, receipt
    if (
        not str(payload.get("decision_authority") or "").startswith("source_only")
        or payload.get("runtime_effect") is not False
        or payload.get("allowed_runtime_apply") is not False
    ):
        receipt["state"] = "authority_contract_invalid"
        return {}, receipt
    source_date_text = str(payload.get("target_date") or "")
    try:
        source_date = date.fromisoformat(source_date_text)
    except ValueError:
        receipt["state"] = "source_date_invalid"
        return {}, receipt
    if source_date < CLEAN_BASELINE_DATE:
        receipt["state"] = "blocked_before_clean_baseline"
        return {}, receipt
    if source_date > maximum_date:
        receipt["state"] = "blocked_future_source"
        return {}, receipt
    if path.stem.rsplit("_", 1)[-1] != source_date_text:
        receipt["state"] = "date_identity_mismatch"
        return {}, receipt
    rows = payload.get("rising_missed_tp1_counterfactual_first_hit_label_rows")
    receipt["state"] = "valid_empty" if rows == [] else "loaded"
    if not isinstance(rows, list):
        receipt["state"] = "rows_missing_or_invalid"
        return {}, receipt
    return payload, receipt


def _primary_horizon(row: dict[str, Any]) -> dict[str, Any]:
    for item in row.get("post_block_horizon_measurements") or []:
        if isinstance(item, dict) and _int(item.get("horizon_min")) == 20:
            return item
    return {}


def _cost_pct(candidate_ts: Any) -> tuple[float | None, dict[str, Any]]:
    try:
        stamp = datetime.fromisoformat(str(candidate_ts))
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=KST)
        contract = comparison_cost_contract(stamp)
        return float(contract["round_trip_cost_pct"]), {
            "status": "verified",
            "policy_id": contract.get("policy_id"),
            "sha256": contract.get("artifact_sha256") or contract.get("sha256"),
        }
    except (TypeError, ValueError, KeyError):
        return None, {"status": "unavailable"}


def _outcome_return(row: dict[str, Any]) -> tuple[float | None, str, dict[str, Any]]:
    label = str(row.get("gross_first_hit_label") or "")
    cost_pct, cost = _cost_pct(row.get("candidate_ts"))
    if cost_pct is None:
        return None, "censored_cost_contract_unavailable", cost
    if label == "gross_target_first":
        gross = _float(row.get("gross_target_pct"))
    elif label == "adverse_stop_first":
        gross = _float(row.get("adverse_stop_pct"))
    elif label == "no_hit_within_20m":
        gross = _float(_primary_horizon(row).get("terminal_executable_move_pct"))
        if gross is None:
            return None, "censored_no_hit_terminal_exit_missing", cost
    else:
        return None, f"censored_{label or 'outcome_missing'}", cost
    if gross is None:
        return None, "censored_gross_outcome_missing", cost
    return round(gross - cost_pct, 8), "paired_cost_adjusted", cost


def _joined_rows(payloads: list[tuple[dict[str, Any], dict[str, Any]]]) -> tuple[list[dict[str, Any]], Counter[str]]:
    rows: list[dict[str, Any]] = []
    exclusions: Counter[str] = Counter()
    seen: set[tuple[str, str]] = set()
    for payload, receipt in payloads:
        if receipt.get("state") not in {"loaded", "valid_empty"}:
            continue
        source_date = str(payload.get("target_date") or "")
        support_by_id = {
            str(item.get("evaluation_id")): item
            for item in payload.get("rising_missed_tp1_counterfactual_submit_safety_rows") or []
            if isinstance(item, dict) and item.get("evaluation_id")
        }
        for label in payload.get("rising_missed_tp1_counterfactual_first_hit_label_rows") or []:
            if not isinstance(label, dict):
                exclusions["invalid_label_row"] += 1
                continue
            evaluation_id = str(label.get("evaluation_id") or "").strip()
            identity = (source_date, evaluation_id)
            if not evaluation_id:
                exclusions["evaluation_id_missing"] += 1
                continue
            if identity in seen:
                exclusions["duplicate_attempt"] += 1
                continue
            seen.add(identity)
            support = support_by_id.get(evaluation_id)
            if not support:
                exclusions["decision_context_missing"] += 1
                continue
            if label.get("entry_executable_bbo_state") != "pass":
                exclusions["entry_executable_bbo_missing"] += 1
                continue
            net_return, outcome_state, cost = _outcome_return(label)
            rows.append(
                {
                    "source_date": source_date,
                    "evaluation_id": evaluation_id,
                    "stock_code": label.get("stock_code"),
                    "candidate_ts": label.get("candidate_ts"),
                    "effective_venue": label.get("effective_venue"),
                    "market_session_bucket": label.get("market_session_bucket"),
                    "selector_reason": label.get("selector_reason"),
                    "positive_support_count": _int(support.get("positive_support_count")),
                    "spread_ratio": _float(label.get("spread_ratio")),
                    "watch_delta_pct": _float(label.get("watch_delta_pct")),
                    "outcome_label": label.get("gross_first_hit_label"),
                    "net_return_pct": net_return,
                    "outcome_state": outcome_state,
                    "cost_contract": cost,
                    "evidence_mode": "counterfactual",
                }
            )
    rows.sort(key=lambda row: (row["source_date"], str(row["candidate_ts"]), row["evaluation_id"]))
    return rows, exclusions


def _candidate_selected(row: dict[str, Any], axis: str, value: float | int) -> bool:
    # Only the support relaxation has a causally identified blocked population.
    # The other axes either tighten an unexported allowed population or alter a
    # diagnostic recheck field without changing the selector decision.
    return bool(
        axis == "positive_support_min"
        and int(value) < int(BASELINE_POLICY[axis])
        and row.get("selector_reason") == "rising_missed_tp1_insufficient_positive_support"
        and _int(row.get("positive_support_count")) >= int(value)
    )


def _split_dates(rows: list[dict[str, Any]]) -> tuple[set[str], set[str]]:
    by_date: dict[str, int] = Counter(
        row["source_date"] for row in rows if row.get("net_return_pct") is not None
    )
    holdout: set[str] = set()
    holdout_samples = 0
    for source_date in sorted(by_date, reverse=True):
        holdout.add(source_date)
        holdout_samples += by_date[source_date]
        if holdout_samples >= HOLDOUT_SAMPLE_FLOOR and len(holdout) >= HOLDOUT_DAY_FLOOR:
            break
    calibration = set(by_date) - holdout
    return calibration, holdout


def _metrics(rows: list[dict[str, Any]], dates: set[str]) -> dict[str, Any]:
    selected = [row for row in rows if row["source_date"] in dates]
    usable = [row for row in selected if row.get("net_return_pct") is not None]
    returns = [float(row["net_return_pct"]) for row in usable]
    daily_return_sum_pct: dict[str, float] = defaultdict(float)
    for row in usable:
        daily_return_sum_pct[row["source_date"]] += float(row["net_return_pct"])
    return {
        "paired_sample_count": len(usable),
        "distinct_day_count": len({row["source_date"] for row in usable}),
        "censored_count": len(selected) - len(usable),
        "outcome_counts": dict(sorted(Counter(str(row["outcome_label"]) for row in selected).items())),
        "baseline_cost_adjusted_ev_pct": 0.0 if usable else None,
        "challenger_cost_adjusted_ev_pct": round(sum(returns) / len(returns), 8) if returns else None,
        "paired_delta_ev_pct": round(sum(returns) / len(returns), 8) if returns else None,
        "baseline_daily_net_profit_krw": None,
        "challenger_daily_net_profit_krw": None,
        "paired_delta_daily_net_profit_krw": None,
        "worst_day_net_profit_krw": None,
        "paired_delta_daily_return_sum_pct": (
            round(sum(daily_return_sum_pct.values()) / len(daily_return_sum_pct), 8)
            if daily_return_sum_pct
            else None
        ),
        "worst_day_return_sum_pct": (
            round(min(daily_return_sum_pct.values()), 8)
            if daily_return_sum_pct
            else None
        ),
        "model_notional_per_attempt_krw": None,
        "daily_net_profit_authority": "unavailable_quantity_and_capital_constraints_missing",
    }


def _evaluate_candidate(rows: list[dict[str, Any]], axis: str, value: float | int) -> dict[str, Any]:
    policy = dict(BASELINE_POLICY)
    policy[axis] = value
    selected = [row for row in rows if _candidate_selected(row, axis, value)]
    calibration_dates, holdout_dates = _split_dates(selected)
    calibration = _metrics(selected, calibration_dates)
    holdout = _metrics(selected, holdout_dates)
    distinct = bool(selected)
    calibration_floor = bool(
        calibration["paired_sample_count"] >= CALIBRATION_SAMPLE_FLOOR
        and calibration["distinct_day_count"] >= CALIBRATION_DAY_FLOOR
    )
    holdout_floor = bool(
        holdout["paired_sample_count"] >= HOLDOUT_SAMPLE_FLOOR
        and holdout["distinct_day_count"] >= HOLDOUT_DAY_FLOOR
    )
    if not distinct:
        disposition = "identical_policy"
        blocker = "no_causally_identified_decision_change"
    elif not calibration_floor or not holdout_floor:
        disposition = "insufficient_mature_sample"
        blocker = "calibration_or_holdout_sample_floor"
    elif (calibration["paired_delta_ev_pct"] or 0.0) <= 0.0 or (
        holdout["paired_delta_ev_pct"] or 0.0
    ) <= 0.0:
        disposition = "measured_no_edge"
        blocker = "cost_adjusted_ev_not_improved"
    elif calibration["paired_delta_daily_net_profit_krw"] is None or holdout[
        "paired_delta_daily_net_profit_krw"
    ] is None:
        disposition = "structurally_blocked"
        blocker = "counterfactual_quantity_or_capital_constraints_missing"
    elif (
        calibration["paired_delta_daily_net_profit_krw"] <= 0.0
        or holdout["paired_delta_daily_net_profit_krw"] <= 0.0
    ):
        disposition = "measured_no_edge"
        blocker = "daily_net_profit_not_improved"
    elif (holdout["worst_day_net_profit_krw"] or 0.0) < 0.0:
        disposition = "measured_no_edge"
        blocker = "holdout_worst_day_tail_worse_than_no_trade_baseline"
    else:
        disposition = "validated_edge"
        blocker = None
    return {
        "candidate_id": f"{axis}={value}",
        "axis": axis,
        "baseline_value": BASELINE_POLICY[axis],
        "challenger_value": value,
        "baseline_policy": dict(BASELINE_POLICY),
        "challenger_policy": policy,
        "baseline_policy_sha256": _sha_json(BASELINE_POLICY),
        "challenger_policy_sha256": _sha_json(policy),
        "decision_change_count": len(selected),
        "calibration_dates": sorted(calibration_dates),
        "holdout_dates": sorted(holdout_dates),
        "calibration": calibration,
        "holdout": holdout,
        "calibration_sample_floor_met": calibration_floor,
        "holdout_sample_floor_met": holdout_floor,
        "disposition": disposition,
        "blocker": blocker,
        "runtime_apply_allowed": disposition == "validated_edge",
    }


def policy_paths(source_date: str, effective_date: str) -> tuple[Path, Path]:
    return (
        OUTPUT_DIR / f"rising_missed_tp1_policy_source_{source_date}.json",
        OUTPUT_DIR / f"rising_missed_tp1_policy_{effective_date}.json",
    )


def _policy_receipt(report: dict[str, Any], effective_date: str) -> dict[str, Any]:
    evaluated = next(
        (
            row
            for row in report["economic_evaluation"]["candidates"]
            if row.get("decision_change_count")
        ),
        None,
    )
    selected = (
        next(
            (
                row
                for row in report["economic_evaluation"]["candidates"]
                if row["disposition"] == "validated_edge"
            ),
            None,
        )
        if report.get("status") == "validated_edge"
        else None
    )
    env: dict[str, str] = {}
    if selected:
        axis = str(selected["axis"])
        env = {
            "KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ENABLED": "true",
            "KORSTOCKSCAN_RISING_MISSED_TP1_SELECTOR_ACTIVE_DATE": effective_date,
            RUNTIME_ENV_KEYS[axis]: str(selected["challenger_value"]),
        }
    receipt = {
        "schema_version": 1,
        "report_type": "rising_missed_tp1_policy",
        "runtime_family": "rising_missed_tp1_selector",
        "source_date": report["target_date"],
        "publication_date": report["generated_at"][:10],
        "effective_date": effective_date,
        "status": "validated_edge" if selected else "incumbent_preserved",
        "decision": "publish_challenger" if selected else "hold_no_edge",
        "selected_axis": selected.get("axis") if selected else None,
        "evaluated_axis": evaluated.get("axis") if evaluated else None,
        "evaluated_before_value": evaluated.get("baseline_value") if evaluated else None,
        "evaluated_after_value": evaluated.get("challenger_value") if evaluated else None,
        "economic_disposition": evaluated.get("disposition") if evaluated else report.get("status"),
        "baseline_policy": dict(BASELINE_POLICY),
        "challenger_policy": selected.get("challenger_policy") if selected else None,
        "baseline_policy_sha256": _sha_json(BASELINE_POLICY),
        "challenger_policy_sha256": selected.get("challenger_policy_sha256") if selected else None,
        "source_report_sha256": report["artifact_sha256"],
        "calibration": evaluated.get("calibration") if evaluated else None,
        "holdout": evaluated.get("holdout") if evaluated else None,
        "runtime_env_overrides": env,
        "consumer_schema": "rising_missed_tp1_selector_bounded_env_v1",
        "apply_scope": "next_preopen_single_axis_tp1_selector",
        "rollback_policy": dict(BASELINE_POLICY),
        "rollback_triggers": [
            "source_stale_or_hash_conflict",
            "consumer_contract_failure",
            "cost_adjusted_delta_turns_negative",
            "worst_day_tail_degrades",
        ],
        "allowed_runtime_apply": True,
        "runtime_effect": bool(selected),
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    receipt["policy_sha256"] = _sha_json({key: value for key, value in receipt.items() if key != "policy_sha256"})
    if selected:
        receipt["runtime_env_overrides"]["KORSTOCKSCAN_RISING_MISSED_TP1_POLICY_SHA256"] = receipt["policy_sha256"]
    return receipt


def build_report(
    target_date: str,
    *,
    source_paths: Iterable[Path] = (),
    generated_at: str | None = None,
) -> dict[str, Any]:
    date.fromisoformat(target_date)
    sources = _source_paths(target_date, source_paths)
    maximum_date = date.fromisoformat(target_date)
    loaded = [_read_source(path, maximum_date=maximum_date) for path in sources]
    rows, exclusions = _joined_rows(loaded)
    candidates = [_evaluate_candidate(rows, axis, value) for axis, value in CANDIDATES]
    viable = [row for row in candidates if row["disposition"] == "validated_edge"]
    measured = [row for row in candidates if row["disposition"] == "measured_no_edge"]
    structurally_blocked = [
        row for row in candidates if row["disposition"] == "structurally_blocked"
    ]
    source_states = Counter(receipt["state"] for _, receipt in loaded)
    exact_target = [
        receipt for _, receipt in loaded if receipt.get("target_date") == target_date
    ]
    source_blocker = next(
        (
            f"source:{receipt['state']}"
            for _, receipt in loaded
            if receipt["state"] not in {"loaded", "valid_empty"}
        ),
        None,
    )
    if not loaded:
        source_blocker = "source:missing"
    elif not exact_target and source_blocker is None:
        source_blocker = "source:exact_target_missing"
    if not loaded or not exact_target or any(
        receipt["state"] not in {"loaded", "valid_empty"} for _, receipt in loaded
    ):
        status = "structurally_blocked"
    elif any(receipt["state"] == "valid_empty" for receipt in exact_target):
        status = "valid_empty"
    elif not rows:
        status = "valid_empty"
    elif viable:
        status = "validated_edge"
    elif measured:
        status = "measured_no_edge"
    elif structurally_blocked:
        status = "structurally_blocked"
    else:
        status = "insufficient_mature_sample"
    report: dict[str, Any] = {
        "schema_version": 2,
        "report_type": "rising_missed_classifier_prior",
        "target_date": target_date,
        "generated_at": generated_at or _now(),
        "status": status,
        "decision": {
            "validated_edge": "publish_single_validated_edge",
            "structurally_blocked": "hold_structural_gap",
            "insufficient_mature_sample": "hold_maturity",
            "valid_empty": "hold_valid_empty",
        }.get(status, "hold_no_edge"),
        "source_quality": {
            "clean_tuning_baseline_date": CLEAN_BASELINE_DATE.isoformat(),
            "tuning_input_allowed": bool(loaded) and all(
                receipt["state"] in {"loaded", "valid_empty"} for _, receipt in loaded
            ) and bool(exact_target),
            "source_state_counts": dict(sorted(source_states.items())),
            "exclusion_counts": dict(sorted(exclusions.items())),
        },
        "source_receipts": [receipt for _, receipt in loaded],
        "paired_rows": rows,
        "economic_evaluation": {
            "metric_role": "direct_same_attempt_cost_adjusted_counterfactual",
            "comparison_status": status,
            "paired_sample_count": sum(
                row["calibration"]["paired_sample_count"] + row["holdout"]["paired_sample_count"]
                for row in candidates if row["decision_change_count"]
            ),
            "source_date_count": len({row["source_date"] for row in rows}),
            "candidate_count": len(candidates),
            "validated_candidate_count": len(viable),
            "candidates": candidates,
            "actual": {
                "status": "post_apply_pending",
                "cost_adjusted_ev_pct": None,
                "daily_net_profit_krw": None,
                "reason": "no_new_policy_actual_completed_receipts_yet",
            },
            "simulation": {
                "status": "not_mixed_with_counterfactual",
                "cost_adjusted_ev_pct": None,
            },
            "counterfactual": {
                "row_count": len(rows),
                "usable_outcome_count": sum(row["net_return_pct"] is not None for row in rows),
                "censored_outcome_count": sum(row["net_return_pct"] is None for row in rows),
                "daily_net_profit_authority": "unavailable_quantity_and_capital_constraints_missing",
            },
            "first_blocker": (
                None
                if viable
                else (
                    source_blocker
                    or (
                        structurally_blocked[0]["blocker"]
                        if structurally_blocked
                        else "all_distinct_candidates_no_edge_or_immature"
                    )
                )
            ),
            "closure_test": "calibration_30x3_and_holdout_20x2_cost_adjusted_ev_daily_net_tail",
            "allowed_runtime_apply": status == "validated_edge",
        },
        "baseline_policy": dict(BASELINE_POLICY),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "postclose_direct_paired_economic_evaluator",
        "forbidden_uses": FORBIDDEN_USES,
        "code_improvement_orders": [],
    }
    report["artifact_sha256"] = _sha_json(
        {key: value for key, value in report.items() if key != "artifact_sha256"}
    )
    return report


def write_outputs(
    report: dict[str, Any], *, output_json: Path, output_md: Path, effective_date: str | None = None
) -> dict[str, Any]:
    effective_date = effective_date or _next_trading_date(str(report["target_date"]))
    policy = _policy_receipt(report, effective_date)
    source_policy_path, effective_policy_path = policy_paths(str(report["target_date"]), effective_date)
    body = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    _atomic_write(output_json, body)
    lines = [
        f"# Rising-missed direct paired economics - {report['target_date']}",
        "",
        f"- status: `{report['status']}`",
        f"- decision: `{report['decision']}`",
        f"- paired rows: `{len(report['paired_rows'])}`",
        f"- effective policy date: `{effective_date}`",
        f"- policy status: `{policy['status']}`",
        "",
        "## Candidates",
        "",
        "| Candidate | Decision changes | Calibration EV | Holdout EV | Disposition | Blocker |",
        "|---|---:|---:|---:|---|---|",
    ]
    for row in report["economic_evaluation"]["candidates"]:
        lines.append(
            f"| `{row['candidate_id']}` | {row['decision_change_count']} | "
            f"{row['calibration']['paired_delta_ev_pct']} | {row['holdout']['paired_delta_ev_pct']} | "
            f"`{row['disposition']}` | `{row['blocker'] or '-'}` |"
        )
    _atomic_write(output_md, "\n".join(lines) + "\n")
    policy_body = json.dumps(policy, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    _atomic_write(source_policy_path, policy_body)
    _atomic_write(effective_policy_path, policy_body)
    return {
        "report_json": str(output_json),
        "report_md": str(output_md),
        "source_policy": str(source_policy_path),
        "effective_policy": str(effective_policy_path),
        "policy": policy,
    }


def _default_outputs(target_date: str) -> tuple[Path, Path]:
    base = OUTPUT_DIR / f"rising_missed_classifier_prior_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--effective-date")
    parser.add_argument("--source", action="append", type=Path, default=[])
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args(argv)
    output_json, output_md = _default_outputs(args.target_date)
    report = build_report(args.target_date, source_paths=args.source)
    result = write_outputs(
        report,
        output_json=args.output_json or output_json,
        output_md=args.output_md or output_md,
        effective_date=args.effective_date,
    )
    if args.print_summary:
        print(json.dumps({"status": report["status"], **result}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
