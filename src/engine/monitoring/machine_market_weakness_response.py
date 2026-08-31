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
    market_weakness_observation_contract_errors,
)
from src.engine.risk.market_weakness_threshold_policy import (
    ALLOWED_ACTIVATION_OBSERVATIONS,
    ALLOWED_RELEASE_OBSERVATIONS,
    BASELINE_ACTIVATION_OBSERVATIONS,
    BASELINE_RELEASE_OBSERVATIONS,
    MIN_OBSERVATION_SPACING_SEC,
    observation_thresholds,
    resolve_effective_thresholds,
    THRESHOLD_REVIEW_METHOD,
    threshold_recommendation_review_hash,
)
from src.engine.scalping.micro_reversion.symbol_master import VerifiedSymbolMaster
from src.utils.jsonl_io import read_json_object_strict
from src.utils.market_day import is_krx_trading_day

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
        "actual_realized_trading_dates": 5,
        "counterfactual_trading_dates": 10,
        "counterfactual_entry_signals": 50,
        "holdout_trading_dates": 3,
        "current_policy_observed_trading_dates": 3,
        "per_listing_market_signals": 10,
        "per_owner_signals": 10,
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
        "same_day_runtime_threshold_apply",
        "order_submit",
    ],
}

# Schema-v1 realized owner outcomes remain clean-baseline evidence for the
# pre-existing skip-response diagnostic.  They are never admitted to the new
# executable-BBO threshold review, which requires schema-v2 rows and the full
# candidate-state matrix.
LEGACY_REALIZED_METRIC_CONTRACT = {
    **METRIC_CONTRACT,
    "sample_floor": {
        "trading_dates": 5,
        "affected_actual_realized_entries": 20,
    },
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
        activation, release, spacing_sec = observation_thresholds(payload)
        seen_ids.add(observation_id)
        rows.append(
            {
                "observation_id": observation_id,
                "as_of": as_of,
                "raw_state": raw_state,
                "affected_markets": affected,
                "recovery_evidence_markets": recovered,
                "activation_unique_observations": activation,
                "release_unique_observations": release,
                "minimum_observation_spacing_sec": spacing_sec,
                "path": str(path),
            }
        )
    rows.sort(key=lambda row: (row["as_of"], row["observation_id"]))
    timestamp_counts = Counter(row["as_of"] for row in rows)
    competing_count = sum(count for count in timestamp_counts.values() if count > 1)
    if competing_count:
        rows = [row for row in rows if timestamp_counts[row["as_of"]] == 1]
        excluded["competing_same_timestamp_observation"] = competing_count
    threshold_pairs = {
        (
            int(row["activation_unique_observations"]),
            int(row["release_unique_observations"]),
            int(row["minimum_observation_spacing_sec"]),
        )
        for row in rows
    }
    if len(threshold_pairs) > 1:
        excluded["mixed_intraday_hysteresis_policy"] = len(rows)
        rows = []
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
        "effective_hysteresis": (
            {
                "activation_unique_observations": next(iter(threshold_pairs))[0],
                "release_unique_observations": next(iter(threshold_pairs))[1],
                "minimum_observation_spacing_sec": next(iter(threshold_pairs))[2],
            }
            if len(threshold_pairs) == 1
            else None
        ),
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
    *,
    activation_observations: int,
    release_observations: int,
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
                < MIN_OBSERVATION_SPACING_SEC
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
                    and current["weak_streak"] >= activation_observations
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
                if current["recovery_streak"] >= release_observations:
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
                and response.get("schema")
                in {
                    "machine_market_weakness_response_v1",
                    "machine_market_weakness_response_v2",
                }
                and response.get("target_date") == source_date
                and isinstance(authority, Mapping)
                and authority.get("runtime_effect") is False
                and authority.get("allowed_runtime_apply") is False
                and authority.get("broker_order_forbidden") is True
                and authority.get("actual_order_submitted") is False
                and (
                    (
                        response.get("schema") == "machine_market_weakness_response_v1"
                        and (
                            response.get("metric_contract") == METRIC_CONTRACT
                            or response.get("metric_contract")
                            == LEGACY_REALIZED_METRIC_CONTRACT
                        )
                    )
                    or (
                        response.get("schema") == "machine_market_weakness_response_v2"
                        and response.get("metric_contract") == METRIC_CONTRACT
                    )
                )
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
            len(cohort_dates)
            >= int(METRIC_CONTRACT["sample_floor"]["actual_realized_trading_dates"])
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
        METRIC_CONTRACT["sample_floor"]["actual_realized_trading_dates"]
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


def _counterfactual_30m_return(row: Mapping[str, Any]) -> float | None:
    if row.get("counterfactual_source_quality_status") != "eligible":
        return None
    counterfactual = row.get("executable_bbo_counterfactual")
    horizons = (
        counterfactual.get("horizons_minutes")
        if isinstance(counterfactual, Mapping)
        else None
    )
    horizon = horizons.get("30") if isinstance(horizons, Mapping) else None
    if not isinstance(horizon, Mapping) or horizon.get("observed") is not True:
        return None
    first_hit = counterfactual.get("target_adverse_first_hit")
    if (
        isinstance(first_hit, Mapping)
        and first_hit.get("state") == "same_timestamp_ambiguous"
    ):
        return None
    return _finite_float(horizon.get("cost_aware_net_return_pct"))


def _cumulative_counterfactual_evidence(
    *,
    target_date: str,
    current_rows: Sequence[dict[str, Any]],
    history_report_dir: Path | None,
    current_activation_observations: int,
    current_release_observations: int,
) -> dict[str, Any]:
    rows_by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    duplicate_keys: set[tuple[str, str, str]] = set()
    rejected_history = 0
    pre_baseline_history = 0
    non_trading_day_history = 0

    def include(source_date: str, rows: object) -> None:
        if not isinstance(rows, list):
            return
        for row in rows:
            if not isinstance(row, dict):
                continue
            owner = str(row.get("owner") or "")
            anchor_id = str(row.get("anchor_id") or "")
            if not owner or not anchor_id:
                continue
            key = (source_date, owner, anchor_id)
            if key in rows_by_key or key in duplicate_keys:
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
                continue
            if source_day >= date.fromisoformat(target_date):
                continue
            if source_day < CLEAN_BASELINE_DATE:
                pre_baseline_history += 1
                continue
            if not is_krx_trading_day(source_day):
                non_trading_day_history += 1
                continue
            payload = _read_json(path)
            response = payload.get("market_weakness_entry_response")
            authority = (
                response.get("authority") if isinstance(response, Mapping) else None
            )
            if not (
                isinstance(response, Mapping)
                and response.get("schema") == "machine_market_weakness_response_v2"
                and response.get("target_date") == source_date
                and response.get("metric_contract") == METRIC_CONTRACT
                and isinstance(authority, Mapping)
                and authority.get("runtime_effect") is False
                and authority.get("allowed_runtime_apply") is False
                and authority.get("broker_order_forbidden") is True
            ):
                rejected_history += 1
                continue
            include(source_date, response.get("entry_responses"))
    include(target_date, list(current_rows))

    eligible: list[tuple[str, dict[str, Any], float]] = []
    exclusions: Counter[str] = Counter()
    # Every daily row persists the complete bounded grid.  This keeps older
    # clean-baseline rows comparable after the effective exact-date policy has
    # moved away from 2/3, without relabeling or future-data leakage.
    required_candidate_keys = {
        f"a{activation}_r{release}"
        for activation in ALLOWED_ACTIVATION_OBSERVATIONS
        for release in ALLOWED_RELEASE_OBSERVATIONS
    }
    for (source_date, _owner, _anchor_id), row in rows_by_key.items():
        net_return = _counterfactual_30m_return(row)
        if net_return is None:
            exclusions["counterfactual_30m_not_eligible"] += 1
            continue
        states = row.get("threshold_candidate_states")
        if not isinstance(states, Mapping) or any(
            not isinstance(states.get(key), bool) for key in required_candidate_keys
        ):
            exclusions["threshold_candidate_state_matrix_incomplete"] += 1
            continue
        if row.get("listing_market") not in SUPPORTED_MARKETS:
            exclusions["listing_market_invalid"] += 1
            continue
        eligible.append((source_date, row, net_return))

    dates = sorted({source_date for source_date, _row, _return in eligible})
    holdout_date_count = min(
        max(int(METRIC_CONTRACT["sample_floor"]["holdout_trading_dates"]), 3),
        max(0, len(dates) // 3),
    )
    holdout_dates = set(dates[-holdout_date_count:]) if holdout_date_count else set()
    calibration_dates = set(dates) - holdout_dates
    market_counts = Counter(
        str(row.get("listing_market")) for _day, row, _ret in eligible
    )
    owner_counts = Counter(str(row.get("owner")) for _day, row, _ret in eligible)
    floors = {
        "trading_dates_met": len(dates)
        >= int(METRIC_CONTRACT["sample_floor"]["counterfactual_trading_dates"]),
        "counterfactual_entry_signals_met": len(eligible)
        >= int(METRIC_CONTRACT["sample_floor"]["counterfactual_entry_signals"]),
        "holdout_trading_dates_met": len(holdout_dates)
        >= int(METRIC_CONTRACT["sample_floor"]["holdout_trading_dates"]),
        "per_listing_market_signals_met": all(
            market_counts[market]
            >= int(METRIC_CONTRACT["sample_floor"]["per_listing_market_signals"])
            for market in SUPPORTED_MARKETS
        ),
        "per_owner_signals_met": all(
            owner_counts[owner]
            >= int(METRIC_CONTRACT["sample_floor"]["per_owner_signals"])
            for owner in ("widget", "episode")
        ),
    }
    current_key = f"a{current_activation_observations}_r{current_release_observations}"
    current_policy_observed_dates = sorted(
        {
            source_date
            for source_date, row, _net_return in eligible
            if isinstance(row.get("effective_hysteresis"), Mapping)
            and row["effective_hysteresis"].get("activation_unique_observations")
            == current_activation_observations
            and row["effective_hysteresis"].get("release_unique_observations")
            == current_release_observations
        }
    )
    floors["current_policy_observed_trading_dates_met"] = bool(
        len(current_policy_observed_dates)
        >= int(METRIC_CONTRACT["sample_floor"]["current_policy_observed_trading_dates"])
    )
    all_floors_met = all(floors.values())

    def policy_metrics(key: str) -> dict[str, Any]:
        deltas: list[tuple[str, float]] = []
        candidate_returns: list[float] = []
        current_policy_returns: list[float] = []
        false_positive = false_negative = 0
        stratum_rows: dict[str, list[dict[str, Any]]] = {
            "owner:widget": [],
            "owner:episode": [],
            "market:KOSPI": [],
            "market:KOSDAQ": [],
        }
        for source_date, row, net_return in eligible:
            states = row["threshold_candidate_states"]
            current_policy_blocked = bool(states[current_key])
            candidate_blocked = bool(states[key])
            current_policy_return = 0.0 if current_policy_blocked else net_return
            candidate_policy_return = 0.0 if candidate_blocked else net_return
            deltas.append(
                (source_date, candidate_policy_return - current_policy_return)
            )
            candidate_returns.append(candidate_policy_return)
            current_policy_returns.append(current_policy_return)
            counterfactual = row.get("executable_bbo_counterfactual")
            first_hit_payload = (
                counterfactual.get("target_adverse_first_hit")
                if isinstance(counterfactual, Mapping)
                else None
            )
            first_hit = str(
                (
                    first_hit_payload.get("state")
                    if isinstance(first_hit_payload, Mapping)
                    else None
                )
                or "unresolved"
            )
            favorable = first_hit == "target_first" or net_return > 0.0
            adverse = first_hit == "adverse_first" or net_return < 0.0
            candidate_misclassified = int(
                (candidate_blocked and favorable) or (not candidate_blocked and adverse)
            )
            current_misclassified = int(
                (current_policy_blocked and favorable)
                or (not current_policy_blocked and adverse)
            )
            false_positive += int(candidate_blocked and favorable)
            false_negative += int(not candidate_blocked and adverse)
            for stratum in (
                f"owner:{row.get('owner')}",
                f"market:{row.get('listing_market')}",
            ):
                if stratum in stratum_rows:
                    stratum_rows[stratum].append(
                        {
                            "source_date": source_date,
                            "delta": candidate_policy_return - current_policy_return,
                            "candidate_misclassified": candidate_misclassified,
                            "current_misclassified": current_misclassified,
                        }
                    )
        calibration = [delta for day, delta in deltas if day in calibration_dates]
        holdout = [delta for day, delta in deltas if day in holdout_dates]
        full = [delta for _day, delta in deltas]

        def stratum_guard(rows: list[dict[str, Any]]) -> dict[str, Any]:
            stratum_holdout = [
                float(row["delta"])
                for row in rows
                if row["source_date"] in holdout_dates
            ]
            stratum_full = [float(row["delta"]) for row in rows]
            return {
                "sample_count": len(stratum_full),
                "holdout_sample_count": len(stratum_holdout),
                "holdout_incremental_vs_current_policy_avg_pct": (
                    round(statistics.fmean(stratum_holdout), 8)
                    if stratum_holdout
                    else None
                ),
                "full_incremental_vs_current_policy_avg_pct": (
                    round(statistics.fmean(stratum_full), 8) if stratum_full else None
                ),
                "candidate_misclassification_count": sum(
                    int(row["candidate_misclassified"]) for row in rows
                ),
                "current_policy_misclassification_count": sum(
                    int(row["current_misclassified"]) for row in rows
                ),
            }

        return {
            "candidate_key": key,
            "sample_count": len(full),
            "calibration_sample_count": len(calibration),
            "holdout_sample_count": len(holdout),
            "calibration_incremental_vs_current_policy_avg_pct": (
                round(statistics.fmean(calibration), 8) if calibration else None
            ),
            "holdout_incremental_vs_current_policy_avg_pct": (
                round(statistics.fmean(holdout), 8) if holdout else None
            ),
            "full_incremental_vs_current_policy_avg_pct": (
                round(statistics.fmean(full), 8) if full else None
            ),
            "full_incremental_vs_current_policy_p10_pct": (
                round(value, 8)
                if (value := _lower_percentile(full, 0.10)) is not None
                else None
            ),
            "candidate_source_quality_adjusted_ev_pct": (
                round(statistics.fmean(candidate_returns), 8)
                if candidate_returns
                else None
            ),
            "current_policy_source_quality_adjusted_ev_pct": (
                round(statistics.fmean(current_policy_returns), 8)
                if current_policy_returns
                else None
            ),
            "false_positive_missed_upside_count": false_positive,
            "false_negative_missed_weakness_count": false_negative,
            "misclassification_count": false_positive + false_negative,
            "stratum_guards": {
                stratum: stratum_guard(rows)
                for stratum, rows in sorted(stratum_rows.items())
            },
        }

    candidate_rows: list[dict[str, Any]] = []
    current_policy_metrics = policy_metrics(current_key)
    neighboring_pairs = sorted(
        {
            (activation, current_release_observations)
            for activation in ALLOWED_ACTIVATION_OBSERVATIONS
            if abs(activation - current_activation_observations) == 1
        }
        | {
            (current_activation_observations, release)
            for release in ALLOWED_RELEASE_OBSERVATIONS
            if abs(release - current_release_observations) == 1
        }
    )
    for activation, release in neighboring_pairs:
        key = f"a{activation}_r{release}"
        metrics = policy_metrics(key)
        calibration_ev = _finite_float(
            metrics.get("calibration_incremental_vs_current_policy_avg_pct")
        )
        holdout_ev = _finite_float(
            metrics.get("holdout_incremental_vs_current_policy_avg_pct")
        )
        full_ev = _finite_float(
            metrics.get("full_incremental_vs_current_policy_avg_pct")
        )
        p10 = _finite_float(metrics.get("full_incremental_vs_current_policy_p10_pct"))
        review_passed = bool(
            all_floors_met
            and calibration_ev is not None
            and calibration_ev >= 0.005
            and holdout_ev is not None
            and holdout_ev >= 0.0
            and full_ev is not None
            and full_ev >= 0.003
            and p10 is not None
            and p10 >= -0.05
            and int(metrics["misclassification_count"])
            <= int(current_policy_metrics["misclassification_count"])
            and all(
                int(guard["sample_count"])
                >= int(METRIC_CONTRACT["sample_floor"]["per_owner_signals"])
                and int(guard["holdout_sample_count"]) > 0
                and _finite_float(
                    guard.get("holdout_incremental_vs_current_policy_avg_pct")
                )
                is not None
                and float(guard["holdout_incremental_vs_current_policy_avg_pct"]) >= 0.0
                and _finite_float(
                    guard.get("full_incremental_vs_current_policy_avg_pct")
                )
                is not None
                and float(guard["full_incremental_vs_current_policy_avg_pct"]) >= 0.0
                and int(guard["candidate_misclassification_count"])
                <= int(guard["current_policy_misclassification_count"])
                for guard in metrics["stratum_guards"].values()
            )
        )
        candidate_rows.append(
            {
                "activation_unique_observations": activation,
                "release_unique_observations": release,
                "changed_axis": (
                    "activation_unique_observations"
                    if activation != current_activation_observations
                    else "release_unique_observations"
                ),
                **metrics,
                "review_status": (
                    "passed_out_of_sample_review"
                    if review_passed
                    else "blocked_by_sample_or_economic_guard"
                ),
                "review_passed": review_passed,
            }
        )
    passing = [row for row in candidate_rows if row["review_passed"] is True]
    selected = (
        max(
            passing,
            key=lambda row: (
                float(row["holdout_incremental_vs_current_policy_avg_pct"]),
                float(row["full_incremental_vs_current_policy_avg_pct"]),
                -int(row["misclassification_count"]),
                row["candidate_key"],
            ),
        )
        if passing
        else None
    )
    selected_policy = (
        {
            key: value
            for key, value in selected.items()
            if key
            in {
                "activation_unique_observations",
                "release_unique_observations",
                "changed_axis",
                "candidate_key",
                "sample_count",
                "calibration_sample_count",
                "holdout_sample_count",
                "calibration_incremental_vs_current_policy_avg_pct",
                "holdout_incremental_vs_current_policy_avg_pct",
                "full_incremental_vs_current_policy_avg_pct",
                "full_incremental_vs_current_policy_p10_pct",
                "candidate_source_quality_adjusted_ev_pct",
                "current_policy_source_quality_adjusted_ev_pct",
                "false_positive_missed_upside_count",
                "false_negative_missed_weakness_count",
                "misclassification_count",
                "stratum_guards",
                "review_status",
            }
        }
        if selected is not None
        else None
    )
    review_payload = {
        "window_start": CLEAN_BASELINE_DATE.isoformat(),
        "window_end": target_date,
        "calibration_dates": sorted(calibration_dates),
        "holdout_dates": sorted(holdout_dates),
        "current_policy_observed_dates": current_policy_observed_dates,
        "sample_floor": floors,
        "current_policy": {
            "activation_unique_observations": current_activation_observations,
            "release_unique_observations": current_release_observations,
            **current_policy_metrics,
        },
        "selected_policy": selected_policy,
    }
    recommendation = {
        **review_payload,
        "review_method": THRESHOLD_REVIEW_METHOD,
        "counterfactual_entry_signal_count": len(eligible),
        "owner_signal_counts": dict(sorted(owner_counts.items())),
        "listing_market_signal_counts": dict(sorted(market_counts.items())),
        "source_census": {
            "unique_primary_key_count": len(rows_by_key),
            "duplicate_conflicted_primary_key_count": len(duplicate_keys),
            "pre_baseline_history_report_count": pre_baseline_history,
            "non_trading_day_history_report_count": non_trading_day_history,
            "rejected_history_report_count": rejected_history,
            "comparison_exclusion_counts": dict(sorted(exclusions.items())),
        },
        "candidates": candidate_rows,
        "policy_candidate_ready": selected_policy is not None,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    recommendation["review_hash"] = threshold_recommendation_review_hash(recommendation)
    return recommendation


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
    effective_hysteresis = observation_source.get("effective_hysteresis") or {}
    if not effective_hysteresis:
        effective = resolve_effective_thresholds(
            target_date=date.fromisoformat(target_date)
        )
        effective_hysteresis = {
            "activation_unique_observations": (
                effective.activation_unique_observations
            ),
            "release_unique_observations": effective.release_unique_observations,
            "minimum_observation_spacing_sec": MIN_OBSERVATION_SPACING_SEC,
            "source": effective.source,
            "status": effective.status,
            "policy_hash": effective.policy_hash,
        }
    activation_observations = int(
        effective_hysteresis.get("activation_unique_observations")
        or BASELINE_ACTIVATION_OBSERVATIONS
    )
    release_observations = int(
        effective_hysteresis.get("release_unique_observations")
        or BASELINE_RELEASE_OBSERVATIONS
    )
    timelines = _market_timelines(
        observations,
        activation_observations=activation_observations,
        release_observations=release_observations,
    )
    candidate_pairs = sorted(
        (activation, release)
        for activation in ALLOWED_ACTIVATION_OBSERVATIONS
        for release in ALLOWED_RELEASE_OBSERVATIONS
    )
    candidate_timelines = {
        f"a{activation}_r{release}": _market_timelines(
            observations,
            activation_observations=activation,
            release_observations=release,
        )
        for activation, release in candidate_pairs
    }
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
            anchor.get("actual_order_submitted") is True
            and anchor.get("actual_realized_response_eligible") is not False
            and realized_return is not None
        )
        counterfactual = (
            anchor.get("market_weakness_counterfactual")
            if isinstance(anchor.get("market_weakness_counterfactual"), Mapping)
            else {}
        )
        counterfactual_30m = (
            (counterfactual.get("horizons_minutes") or {}).get("30")
            if isinstance(counterfactual.get("horizons_minutes"), Mapping)
            else None
        )
        counterfactual_return = (
            _finite_float(counterfactual_30m.get("cost_aware_net_return_pct"))
            if isinstance(counterfactual_30m, Mapping)
            and counterfactual_30m.get("observed") is True
            else None
        )
        counterfactual_gaps: list[str] = []
        if counterfactual.get("source_quality_status") != "eligible":
            counterfactual_gaps.extend(
                str(reason)
                for reason in counterfactual.get("source_gap_reasons")
                or ["executable_bbo_counterfactual_missing"]
            )
        first_hit = (
            str(
                (counterfactual.get("target_adverse_first_hit") or {}).get("state")
                or "unresolved"
            )
            if isinstance(counterfactual.get("target_adverse_first_hit"), Mapping)
            else "unresolved"
        )
        if confirmed_weakness:
            accuracy_class = (
                "true_positive_avoided_adverse"
                if first_hit == "adverse_first"
                or (counterfactual_return is not None and counterfactual_return < 0.0)
                else (
                    "false_positive_missed_upside"
                    if first_hit == "target_first"
                    or (
                        counterfactual_return is not None
                        and counterfactual_return > 0.0
                    )
                    else "positive_alert_unresolved"
                )
            )
        else:
            accuracy_class = (
                "false_negative_missed_weakness"
                if first_hit == "adverse_first"
                or (counterfactual_return is not None and counterfactual_return < 0.0)
                else (
                    "true_negative_entry_opportunity"
                    if first_hit == "target_first"
                    or (
                        counterfactual_return is not None
                        and counterfactual_return > 0.0
                    )
                    else "negative_alert_unresolved"
                )
            )
        threshold_candidate_states: dict[str, bool | None] = {}
        if listing_market is not None and anchor_at is not None:
            for key, candidate_timeline in candidate_timelines.items():
                candidate_state, _candidate_release = _state_at(
                    candidate_timeline[listing_market], anchor_at
                )
                threshold_candidate_states[key] = (
                    candidate_state.get("active") is True
                    if candidate_state is not None
                    else None
                )
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
                "effective_hysteresis": {
                    "activation_unique_observations": activation_observations,
                    "release_unique_observations": release_observations,
                },
                "threshold_candidate_states": threshold_candidate_states,
                "alert_accuracy_class": accuracy_class,
                "executable_bbo_counterfactual": counterfactual,
                "counterfactual_source_quality_status": (
                    "eligible" if not counterfactual_gaps else "blocked"
                ),
                "counterfactual_source_gap_reasons": sorted(set(counterfactual_gaps)),
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
                    "counterfactual_30m_cost_aware_net_return_pct": (
                        counterfactual_return
                    ),
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
                        "eligible": confirmed_weakness
                        and (actual_realized or counterfactual_return is not None),
                        "zero_exposure_counterfactual_return_pct": (
                            0.0
                            if confirmed_weakness
                            and (actual_realized or counterfactual_return is not None)
                            else None
                        ),
                        "incremental_vs_control_pct": (
                            round(-realized_return, 8)
                            if confirmed_weakness and realized_return is not None
                            else None
                        ),
                        "incremental_vs_counterfactual_30m_pct": (
                            round(-counterfactual_return, 8)
                            if confirmed_weakness and counterfactual_return is not None
                            else None
                        ),
                        "actual_realized_comparison": actual_realized,
                        "executable_bbo_counterfactual_comparison": (
                            counterfactual_return is not None
                        ),
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
    threshold_recommendation = _cumulative_counterfactual_evidence(
        target_date=target_date,
        current_rows=rows,
        history_report_dir=history_report_dir,
        current_activation_observations=activation_observations,
        current_release_observations=release_observations,
    )
    return {
        "schema": "machine_market_weakness_response_v2",
        "target_date": target_date,
        "status": (
            "source_only_evidence_accumulating"
            if eligible_rows and observations and symbol_markets
            else "source_quality_blocked_or_no_entry_anchor"
        ),
        "decision": (
            "next_exact_date_hysteresis_candidate_review_passed"
            if threshold_recommendation["policy_candidate_ready"]
            else "accumulate_counterfactual_evidence_keep_baseline"
        ),
        "metric_contract": METRIC_CONTRACT,
        "authority": {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "policy_candidate_ready": threshold_recommendation[
                "policy_candidate_ready"
            ],
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
            "promotion_candidate_ready": threshold_recommendation[
                "policy_candidate_ready"
            ],
        },
        "clean_baseline_cumulative": cumulative,
        "threshold_recommendation": threshold_recommendation,
        "entry_responses": rows,
    }
