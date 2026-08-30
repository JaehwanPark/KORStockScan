"""Source-only weak-market response attribution for widget/episode entries.

The evaluator reconstructs market-scoped weakness hysteresis from immutable
observations and joins only past state to each owner entry anchor.  It never
changes entry, cancellation, target, holding, exit, quantity, or broker state.
"""

from __future__ import annotations

import math
import statistics
from bisect import bisect_left
from collections import Counter
from datetime import date, datetime
from pathlib import Path
from typing import Any, Mapping, Sequence
from zoneinfo import ZoneInfo

from src.engine.market_panic_breadth_collector import (
    MARKET_WEAKNESS_ACTIVATION_OBSERVATIONS,
    MARKET_WEAKNESS_MIN_OBSERVATION_SPACING_SEC,
    MARKET_WEAKNESS_RELEASE_OBSERVATIONS,
    market_weakness_observation_contract_errors,
)
from src.engine.scalping.micro_reversion.symbol_master import VerifiedSymbolMaster
from src.utils.jsonl_io import read_json_object_strict

KST = ZoneInfo("Asia/Seoul")
SUPPORTED_MARKETS = frozenset({"KOSPI", "KOSDAQ"})
CLEAN_BASELINE_DATE = date(2026, 6, 5)

METRIC_CONTRACT = {
    "metric_role": "source_only_market_weakness_entry_response_counterfactual",
    "decision_authority": "postclose_diagnostic_only",
    "window_policy": (
        "exact_date_daily_then_clean_baseline_cumulative_before_policy_candidate"
    ),
    "sample_floor": {
        "trading_dates": 5,
        "affected_actual_realized_entries": 20,
    },
    "aggregation_unit": "owner_and_listing_market_cohort",
    "primary_decision_metric": (
        "actual_realized_source_quality_adjusted_incremental_vs_control_pct"
    ),
    "source_quality_gate": (
        "exact_date_schema_v2_market_scoped_observations_and_verified_symbol_master"
    ),
    "forbidden_uses": [
        "widget_entry_block",
        "episode_entry_block",
        "open_buy_cancel",
        "target_order_cancel",
        "forced_exit",
        "stop_or_holding_policy_change",
        "price_or_quantity_change",
        "runtime_threshold_apply",
        "order_submit",
    ],
}


def _finite_float(value: object) -> float | None:
    try:
        result = float(value)
    except (TypeError, ValueError):
        return None
    return result if math.isfinite(result) else None


def _parse_kst(value: object) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(KST)


def _normalized_markets(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return sorted(
        {
            str(market).strip().upper()
            for market in value
            if str(market).strip().upper() in SUPPORTED_MARKETS
        }
    )


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = read_json_object_strict(path)
    except (FileNotFoundError, OSError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _logical_json_paths(directory: Path, pattern: str) -> list[Path]:
    logical_paths: set[Path] = set()
    for path in directory.glob(pattern):
        logical_paths.add(
            path.with_name(path.name[: -len(".gz")])
            if path.name.endswith(".json.gz")
            else path
        )
    return sorted(logical_paths)


def _load_observations(
    observation_root: Path, target_date: str
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    excluded: dict[str, int] = {}
    seen_ids: set[str] = set()
    source_dir = observation_root / target_date
    source_paths = _logical_json_paths(
        source_dir, "market_weakness_observation_*.json*"
    )
    for path in source_paths:
        payload = _read_json(path)
        reason = None
        observation_id = str(payload.get("observation_id") or "").strip()
        as_of = _parse_kst(payload.get("as_of"))
        if payload.get("schema_version") != 2:
            reason = "market_scope_schema_v2_required"
        elif payload.get("target_date") != target_date:
            reason = "target_date_mismatch"
        elif as_of is None or as_of.date().isoformat() != target_date:
            reason = "invalid_observation_time"
        else:
            contract_errors = market_weakness_observation_contract_errors(payload)
            if contract_errors:
                reason = contract_errors[0]
            elif observation_id in seen_ids:
                reason = "duplicate_observation_id"
        if reason is not None:
            excluded[reason] = excluded.get(reason, 0) + 1
            continue
        raw_state = str(payload.get("raw_state") or "")
        affected = _normalized_markets(payload.get("affected_markets"))
        recovered = _normalized_markets(payload.get("recovery_evidence_markets"))
        seen_ids.add(observation_id)
        rows.append(
            {
                "observation_id": observation_id,
                "as_of": as_of,
                "raw_state": raw_state,
                "affected_markets": affected,
                "recovery_evidence_markets": recovered,
                "path": str(path),
            }
        )
    rows.sort(key=lambda row: (row["as_of"], row["observation_id"]))
    timestamp_counts = Counter(row["as_of"] for row in rows)
    competing_count = sum(count for count in timestamp_counts.values() if count > 1)
    if competing_count:
        rows = [row for row in rows if timestamp_counts[row["as_of"]] == 1]
        excluded["competing_same_timestamp_observation"] = competing_count
    return rows, {
        "path": str(source_dir),
        "status": "loaded" if rows else "no_schema_v2_observation",
        "artifact_count": len(source_paths),
        "eligible_count": len(rows),
        "excluded_count": sum(excluded.values()),
        "partition_reconciled": bool(
            len(source_paths) == len(rows) + sum(excluded.values())
        ),
        "exclusion_counts": excluded,
    }


def _select_symbol_master(
    symbol_master_dir: Path, target_date: str
) -> tuple[dict[str, str], dict[str, Any]]:
    target_day = date.fromisoformat(target_date)
    candidates: list[tuple[date, Path]] = []
    for path in _logical_json_paths(
        symbol_master_dir, "micro_reversion_symbol_master_*.json*"
    ):
        try:
            source_day = date.fromisoformat(path.stem.rsplit("_", 1)[-1])
        except ValueError:
            continue
        if source_day <= target_day:
            candidates.append((source_day, path))
    if not candidates:
        return {}, {"status": "verified_symbol_master_missing", "path": None}
    source_day, path = max(candidates, key=lambda item: item[0])
    payload = _read_json(path)
    if payload.get("artifact_id") != (
        f"main-ai-economic-reference-{source_day.isoformat()}-symbol-master"
    ):
        return {}, {"status": "verified_symbol_master_invalid", "path": str(path)}
    try:
        master = VerifiedSymbolMaster.from_payload(
            payload, require_canonical_owner=True
        )
    except (TypeError, ValueError):
        return {}, {"status": "verified_symbol_master_invalid", "path": str(path)}
    records = payload.get("records")
    if not isinstance(records, list):
        return {}, {"status": "verified_symbol_master_invalid", "path": str(path)}
    mapping: dict[str, str] = {}
    outside_effective_window_count = 0
    for symbol in sorted(
        {
            str(record.get("symbol") or "")
            for record in records
            if isinstance(record, Mapping)
        }
    ):
        lookup = master.lookup(symbol, as_of=target_day)
        if not lookup.economic_metadata_allowed or lookup.record is None:
            outside_effective_window_count += 1
            continue
        mapping[symbol] = lookup.record.listing_market.value
    return mapping, {
        "status": "loaded" if mapping else "verified_symbol_master_empty",
        "path": str(path),
        "source_date": source_day.isoformat(),
        "eligible_symbol_count": len(mapping),
        "outside_effective_window_count": outside_effective_window_count,
        "content_sha256": payload.get("content_sha256"),
    }


def _market_timelines(
    observations: Sequence[dict[str, Any]],
) -> dict[str, list[dict[str, Any]]]:
    timelines: dict[str, list[dict[str, Any]]] = {"KOSPI": [], "KOSDAQ": []}
    state = {
        market: {
            "active": False,
            "weak_streak": 0,
            "recovery_streak": 0,
            "last_class": "",
            "last_counted_at": None,
            "activation_at": None,
            "activation_observation_id": None,
        }
        for market in SUPPORTED_MARKETS
    }
    for observation in observations:
        observed_at = observation["as_of"]
        for market in SUPPORTED_MARKETS:
            current = state[market]
            weak = market in observation["affected_markets"]
            recovered = market in observation["recovery_evidence_markets"]
            classification = "weak" if weak else "recovery" if recovered else "neutral"
            last_counted_at = current["last_counted_at"]
            if (
                last_counted_at is not None
                and (observed_at - last_counted_at).total_seconds()
                < MARKET_WEAKNESS_MIN_OBSERVATION_SPACING_SEC
            ):
                continue
            current["last_counted_at"] = observed_at
            if classification == "weak":
                current["weak_streak"] = (
                    current["weak_streak"] + 1 if current["last_class"] == "weak" else 1
                )
                current["recovery_streak"] = 0
                if (
                    not current["active"]
                    and current["weak_streak"]
                    >= MARKET_WEAKNESS_ACTIVATION_OBSERVATIONS
                ):
                    current["active"] = True
                    current["activation_at"] = observed_at
                    current["activation_observation_id"] = observation["observation_id"]
            elif classification == "recovery":
                current["weak_streak"] = 0
                current["recovery_streak"] = (
                    current["recovery_streak"] + 1
                    if current["active"] and current["last_class"] == "recovery"
                    else (1 if current["active"] else 0)
                )
                if current["recovery_streak"] >= MARKET_WEAKNESS_RELEASE_OBSERVATIONS:
                    current["active"] = False
                    current["activation_at"] = None
                    current["activation_observation_id"] = None
            else:
                current["weak_streak"] = 0
                current["recovery_streak"] = 0
            current["last_class"] = classification
            timelines[market].append(
                {
                    "as_of": observed_at,
                    "observation_id": observation["observation_id"],
                    "active": current["active"],
                    "weak_streak": current["weak_streak"],
                    "recovery_streak": current["recovery_streak"],
                    "activation_at": current["activation_at"],
                    "activation_observation_id": current["activation_observation_id"],
                }
            )
    return timelines


def _state_at(
    timeline: Sequence[dict[str, Any]], anchor_at: datetime
) -> tuple[dict[str, Any] | None, datetime | None]:
    times = [row["as_of"] for row in timeline]
    # Equal timestamps do not establish arrival order.  Use only strictly past
    # observations so a same-timestamp regime event cannot leak into entry.
    index = bisect_left(times, anchor_at) - 1
    if index < 0:
        return None, None
    current = timeline[index]
    release_at = next(
        (
            row["as_of"]
            for row in timeline[index + 1 :]
            if current["active"] and row["active"] is False
        ),
        None,
    )
    return current, release_at


def _actual_skip_comparison(
    row: Mapping[str, Any],
) -> tuple[float | None, str | None]:
    if row.get("source_quality_status") != "eligible":
        return None, "source_quality_not_eligible"
    if row.get("owner") not in {"widget", "episode"}:
        return None, "owner_invalid"
    if row.get("listing_market") not in SUPPORTED_MARKETS:
        return None, "listing_market_invalid"
    if row.get("actual_order_submitted") is not True:
        return None, "actual_order_not_submitted"
    control = row.get("control")
    if not isinstance(control, Mapping) or control.get("status") != "actual_realized":
        return None, "actual_realized_control_missing"
    realized_return = _finite_float(control.get("cost_aware_net_return_pct"))
    if realized_return is None:
        return None, "cost_aware_control_return_invalid"
    arms = row.get("candidate_arms")
    if not isinstance(arms, Mapping):
        return None, "candidate_arms_missing"
    skip = arms.get("skip_new_entry_during_confirmed_weakness")
    if not isinstance(skip, Mapping):
        return None, "skip_arm_missing"
    if not (
        skip.get("eligible") is True
        and skip.get("actual_realized_comparison") is True
        and _finite_float(skip.get("zero_exposure_counterfactual_return_pct")) == 0.0
    ):
        return None, "skip_arm_contract_invalid"
    declared_delta = _finite_float(skip.get("incremental_vs_control_pct"))
    expected_delta = round(-realized_return, 8)
    if declared_delta is None or not math.isclose(
        declared_delta, expected_delta, abs_tol=1e-8, rel_tol=1e-12
    ):
        return None, "skip_delta_reconciliation_mismatch"
    return expected_delta, None


def _actual_skip_delta(row: Mapping[str, Any]) -> float | None:
    delta, _reason = _actual_skip_comparison(row)
    return delta


def _lower_percentile(values: Sequence[float], fraction: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(len(ordered) * fraction) - 1)
    return ordered[index]


def _cumulative_skip_evidence(
    *,
    target_date: str,
    current_rows: Sequence[dict[str, Any]],
    history_report_dir: Path | None,
) -> dict[str, Any]:
    rows_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    duplicate_keys: set[tuple[str, str, str]] = set()
    duplicate_row_counts: Counter[tuple[str, str, str]] = Counter()
    source_census = {
        "history_report_count": 0,
        "accepted_history_report_count": 0,
        "rejected_history_report_count": 0,
        "pre_baseline_history_report_count": 0,
        "invalid_date_history_report_count": 0,
        "input_row_count": 0,
        "primary_key_invalid_row_count": 0,
    }
    comparison_exclusions: Counter[str] = Counter()

    def include(source_date: str, rows: object) -> None:
        if not isinstance(rows, list):
            return
        try:
            source_day = date.fromisoformat(source_date)
        except ValueError:
            return
        if source_day < CLEAN_BASELINE_DATE or source_date > target_date:
            return
        for row in rows:
            source_census["input_row_count"] += 1
            if not isinstance(row, dict):
                source_census["primary_key_invalid_row_count"] += 1
                comparison_exclusions["row_not_object"] += 1
                continue
            anchor_id = str(row.get("anchor_id") or "").strip()
            owner = str(row.get("owner") or "").strip()
            if not anchor_id or not owner:
                source_census["primary_key_invalid_row_count"] += 1
                comparison_exclusions["primary_key_missing"] += 1
                continue
            key = (source_date, owner, anchor_id)
            if key in rows_by_key or key in duplicate_keys:
                if key in rows_by_key:
                    duplicate_row_counts[key] = 2
                else:
                    duplicate_row_counts[key] += 1
                rows_by_key.pop(key, None)
                duplicate_keys.add(key)
                continue
            rows_by_key[key] = row

    if history_report_dir is not None:
        for path in _logical_json_paths(
            history_report_dir, "machine_microstructure_attribution_*.json*"
        ):
            source_date = path.stem.rsplit("_", 1)[-1]
            try:
                source_day = date.fromisoformat(source_date)
            except ValueError:
                source_census["invalid_date_history_report_count"] += 1
                continue
            if source_day >= date.fromisoformat(target_date):
                continue
            if source_day < CLEAN_BASELINE_DATE:
                source_census["pre_baseline_history_report_count"] += 1
                continue
            source_census["history_report_count"] += 1
            payload = _read_json(path)
            response = payload.get("market_weakness_entry_response")
            authority = (
                response.get("authority") if isinstance(response, Mapping) else {}
            )
            if not (
                isinstance(response, Mapping)
                and response.get("schema") == "machine_market_weakness_response_v1"
                and response.get("target_date") == source_date
                and isinstance(authority, Mapping)
                and authority.get("runtime_effect") is False
                and authority.get("allowed_runtime_apply") is False
                and authority.get("broker_order_forbidden") is True
                and authority.get("actual_order_submitted") is False
                and authority.get("policy_candidate_ready") is False
                and response.get("metric_contract") == METRIC_CONTRACT
            ):
                source_census["rejected_history_report_count"] += 1
                continue
            source_census["accepted_history_report_count"] += 1
            include(source_date, response.get("entry_responses"))
    include(target_date, list(current_rows))

    comparisons: list[tuple[str, dict[str, Any], float]] = []
    for (source_date, _owner, _anchor_id), row in rows_by_key.items():
        delta, reason = _actual_skip_comparison(row)
        if delta is None:
            comparison_exclusions[reason or "comparison_invalid"] += 1
            continue
        comparisons.append((source_date, row, delta))
    deltas = [delta for _source_date, _row, delta in comparisons]
    sample_dates = sorted({source_date for source_date, _row, _delta in comparisons})
    owner_market_cohorts: list[dict[str, Any]] = []
    cohort_keys = sorted(
        {
            (str(row.get("owner") or ""), str(row.get("listing_market") or ""))
            for _source_date, row, _delta in comparisons
        }
    )
    review_ready_cohort_count = 0
    for owner, market in cohort_keys:
        cohort_comparisons = [
            (_source_date, delta)
            for _source_date, row, delta in comparisons
            if row.get("owner") == owner and row.get("listing_market") == market
        ]
        cohort = [delta for _source_date, delta in cohort_comparisons]
        cohort_dates = {source_date for source_date, _delta in cohort_comparisons}
        cohort_average = statistics.fmean(cohort) if cohort else None
        cohort_review_ready = bool(
            len(cohort_dates) >= int(METRIC_CONTRACT["sample_floor"]["trading_dates"])
            and len(cohort)
            >= int(METRIC_CONTRACT["sample_floor"]["affected_actual_realized_entries"])
            and cohort_average is not None
            and cohort_average > 0.0
        )
        review_ready_cohort_count += int(cohort_review_ready)
        owner_market_cohorts.append(
            {
                "owner": owner,
                "listing_market": market,
                "actual_realized_trading_date_count": len(cohort_dates),
                "actual_realized_comparison_count": len(cohort),
                "incremental_vs_control_avg_pct": (
                    round(cohort_average, 8) if cohort_average is not None else None
                ),
                "incremental_vs_control_p10_pct": (
                    round(value, 8)
                    if (value := _lower_percentile(cohort, 0.10)) is not None
                    else None
                ),
                "source_only_review_ready": cohort_review_ready,
            }
        )
    average = statistics.fmean(deltas) if deltas else None
    trading_date_floor_met = len(sample_dates) >= int(
        METRIC_CONTRACT["sample_floor"]["trading_dates"]
    )
    comparison_floor_met = len(deltas) >= int(
        METRIC_CONTRACT["sample_floor"]["affected_actual_realized_entries"]
    )
    return {
        "window_start": CLEAN_BASELINE_DATE.isoformat(),
        "window_end": target_date,
        "affected_actual_realized_trading_date_count": len(sample_dates),
        "affected_actual_realized_comparison_count": len(deltas),
        "incremental_vs_control_avg_pct": (
            round(average, 8) if average is not None else None
        ),
        "incremental_vs_control_p10_pct": (
            round(value, 8)
            if (value := _lower_percentile(deltas, 0.10)) is not None
            else None
        ),
        "avoided_loss_sum_pct": round(sum(max(delta, 0.0) for delta in deltas), 8),
        "missed_upside_sum_pct": round(sum(max(-delta, 0.0) for delta in deltas), 8),
        "skip_worse_than_control_rate_pct": (
            round(sum(delta < 0.0 for delta in deltas) / len(deltas) * 100.0, 4)
            if deltas
            else None
        ),
        "sample_floor": {
            "trading_dates_met": trading_date_floor_met,
            "actual_realized_comparisons_met": comparison_floor_met,
        },
        "source_census": {
            **source_census,
            "unique_primary_key_count": len(rows_by_key),
            "duplicate_conflicted_primary_key_count": len(duplicate_keys),
            "duplicate_conflicted_row_count": sum(duplicate_row_counts.values()),
            "primary_key_partition_reconciled": bool(
                source_census["input_row_count"]
                == len(rows_by_key)
                + sum(duplicate_row_counts.values())
                + source_census["primary_key_invalid_row_count"]
            ),
            "comparison_eligible_count": len(comparisons),
            "comparison_exclusion_counts": dict(sorted(comparison_exclusions.items())),
        },
        "source_only_review_ready": review_ready_cohort_count > 0,
        "review_ready_owner_market_cohort_count": review_ready_cohort_count,
        "owner_market_cohorts": owner_market_cohorts,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }


def build_machine_market_weakness_response(
    entry_confirmation: Mapping[str, Any],
    *,
    target_date: str,
    observation_root: Path,
    symbol_master_dir: Path,
    history_report_dir: Path | None = None,
) -> dict[str, Any]:
    observations, observation_source = _load_observations(observation_root, target_date)
    symbol_markets, symbol_master_source = _select_symbol_master(
        symbol_master_dir, target_date
    )
    timelines = _market_timelines(observations)
    anchors = entry_confirmation.get("entry_anchors")
    anchors = anchors if isinstance(anchors, list) else []
    rows: list[dict[str, Any]] = []
    for anchor in anchors:
        if not isinstance(anchor, Mapping):
            continue
        anchor_id = str(anchor.get("anchor_id") or "").strip()
        owner = str(anchor.get("owner") or "").strip()
        symbol = str(anchor.get("symbol") or "").strip()
        listing_market = symbol_markets.get(symbol)
        anchor_at = _parse_kst(anchor.get("anchor_at"))
        gaps: list[str] = []
        if not anchor_id:
            gaps.append("entry_anchor_id_missing")
        if owner not in {"widget", "episode"}:
            gaps.append("entry_anchor_owner_invalid")
        if listing_market is None:
            gaps.append("verified_listing_market_missing")
        if anchor_at is None or anchor_at.date().isoformat() != target_date:
            gaps.append("exact_date_anchor_time_invalid")
        state_at_entry = None
        release_at = None
        if listing_market is not None and anchor_at is not None:
            state_at_entry, release_at = _state_at(timelines[listing_market], anchor_at)
            if state_at_entry is None:
                gaps.append("past_market_weakness_observation_missing")
        confirmed_weakness = bool(
            state_at_entry is not None and state_at_entry.get("active") is True
        )
        outcome = (
            anchor.get("owner_outcome")
            if isinstance(anchor.get("owner_outcome"), Mapping)
            else {}
        )
        realized_return = (
            _finite_float(outcome.get("cost_aware_net_return_pct"))
            if outcome.get("realized") is True
            else None
        )
        actual_realized = bool(
            anchor.get("actual_order_submitted") is True and realized_return is not None
        )
        if confirmed_weakness and realized_return is None:
            gaps.append("completed_cost_aware_owner_outcome_missing")
        delay_seconds = (
            max(0.0, (release_at - anchor_at).total_seconds())
            if confirmed_weakness and release_at is not None and anchor_at is not None
            else None
        )
        micro_classification = str(anchor.get("classification") or "")
        rows.append(
            {
                "anchor_id": anchor_id or None,
                "owner": owner or None,
                "scope_id": anchor.get("scope_id"),
                "symbol": symbol,
                "listing_market": listing_market,
                "anchor_at": anchor.get("anchor_at"),
                "anchor_role": anchor.get("anchor_role"),
                "actual_order_submitted": anchor.get("actual_order_submitted") is True,
                "market_state_at_entry": (
                    "CONFIRMED_WEAKNESS"
                    if confirmed_weakness
                    else "NOT_CONFIRMED_OR_NOT_OBSERVED"
                ),
                "state_observation_id": (
                    state_at_entry.get("observation_id") if state_at_entry else None
                ),
                "activation_observation_id": (
                    state_at_entry.get("activation_observation_id")
                    if state_at_entry
                    else None
                ),
                "control": {
                    "status": (
                        "actual_realized"
                        if actual_realized
                        else (
                            "source_only_owner_outcome"
                            if realized_return is not None
                            else "right_censored_or_missing"
                        )
                    ),
                    "cost_aware_net_return_pct": realized_return,
                },
                "candidate_arms": {
                    "delay_new_entry_until_recovery_confirmed": {
                        "eligible": confirmed_weakness,
                        "release_at": release_at.isoformat() if release_at else None,
                        "delay_seconds": delay_seconds,
                        "evaluation_status": (
                            "executable_reentry_price_required"
                            if confirmed_weakness and release_at is not None
                            else "no_confirmed_weakness_or_release_not_observed"
                        ),
                    },
                    "skip_new_entry_during_confirmed_weakness": {
                        "eligible": confirmed_weakness and realized_return is not None,
                        "zero_exposure_counterfactual_return_pct": (
                            0.0
                            if confirmed_weakness and realized_return is not None
                            else None
                        ),
                        "incremental_vs_control_pct": (
                            round(-realized_return, 8)
                            if confirmed_weakness and realized_return is not None
                            else None
                        ),
                        "actual_realized_comparison": actual_realized,
                    },
                    "relative_strength_and_liquidity_exception": {
                        "micro_supportive": (
                            micro_classification == "supportive_confirmation_candidate"
                        ),
                        "evaluation_status": (
                            "additional_exact_liquidity_velocity_receipt_required"
                        ),
                        "eligible": False,
                    },
                },
                "source_quality_status": "eligible" if not gaps else "blocked",
                "source_gap_reasons": sorted(set(gaps)),
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "broker_order_forbidden": True,
            }
        )
    actual_deltas = [
        delta for row in rows if (delta := _actual_skip_delta(row)) is not None
    ]
    affected_rows = [
        row for row in rows if row["market_state_at_entry"] == "CONFIRMED_WEAKNESS"
    ]
    eligible_rows = [row for row in rows if row["source_quality_status"] == "eligible"]
    cumulative = _cumulative_skip_evidence(
        target_date=target_date,
        current_rows=rows,
        history_report_dir=history_report_dir,
    )
    return {
        "schema": "machine_market_weakness_response_v1",
        "target_date": target_date,
        "status": (
            "source_only_evidence_accumulating"
            if eligible_rows and observations and symbol_markets
            else "source_quality_blocked_or_no_entry_anchor"
        ),
        "decision": "no_runtime_or_owner_policy_change",
        "metric_contract": METRIC_CONTRACT,
        "authority": {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "policy_candidate_ready": False,
        },
        "sources": {
            "market_weakness_observations": observation_source,
            "verified_symbol_master": symbol_master_source,
        },
        "summary": {
            "entry_anchor_count": len(rows),
            "source_quality_eligible_count": len(eligible_rows),
            "confirmed_weakness_entry_count": len(affected_rows),
            "actual_realized_comparison_count": len(actual_deltas),
            "source_quality_blocked_count": sum(
                row["source_quality_status"] == "blocked" for row in rows
            ),
            "actual_realized_source_quality_adjusted_incremental_vs_control_pct": (
                round(sum(actual_deltas) / len(actual_deltas), 8)
                if actual_deltas
                else None
            ),
            "promotion_candidate_ready": False,
        },
        "clean_baseline_cumulative": cumulative,
        "entry_responses": rows,
    }
