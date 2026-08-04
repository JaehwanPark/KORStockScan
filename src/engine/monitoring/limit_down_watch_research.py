"""Build source-only research artifacts for the limit-down observation lane.

This producer turns ordered observation visits into deterministic counterfactual
labels, cohort/price-band sim policies, post-sim attribution, and a bounded
live-auto eligibility contract.  The producer never submits an order; a separate
runtime consumer may hand an eligible symbol to the normal scalping pipeline.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from datetime import date, datetime, timedelta
import gzip
import json
import math
import os
from pathlib import Path
import tempfile
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PROJECT_ROOT / "data"
EVENT_DIR = DATA_DIR / "pipeline_events"
CANDIDATE_DIR = DATA_DIR / "report" / "limit_down_watch_candidate_source"
COUNTERFACTUAL_DIR = DATA_DIR / "report" / "limit_down_watch_counterfactual"
SIM_POLICY_DIR = DATA_DIR / "threshold_cycle" / "scalp_sim_policies"
POST_SIM_DIR = DATA_DIR / "report" / "limit_down_watch_post_sim_attribution"
BOUNDED_CANDIDATE_DIR = DATA_DIR / "threshold_cycle" / "bounded_live_candidates"

ROLLOUT_DATE = date(2026, 7, 28)
HORIZONS_SEC = (30, 60, 180, 300, 600)
SELECTED_EXIT_HORIZON_SEC = 180
MIN_COUNTERFACTUAL_SAMPLE = 20
MIN_COUNTERFACTUAL_DATES = 5
MIN_CELL_SAMPLE = 5
MIN_CELL_DATES = 3
MIN_POST_SIM_SAMPLE = 20
MIN_POST_SIM_CELL_SAMPLE = 5
MIN_LIVE_AUTO_CELL_SAMPLE = 1
MIN_LIVE_AUTO_CELL_DATES = 1
DEFAULT_ROUND_TRIP_COST_PCT = 0.30
ROLLING_WINDOW_CALENDAR_DAYS = 90
LIVE_AUTO_MAX_MAE_P10_PCT = -5.0
LIVE_AUTO_MAX_RELOCK_RATE_PCT = 0.0
LIVE_AUTO_MIN_BBO_COVERAGE_PCT = 100.0
LIVE_AUTO_MAX_ENTRY_SPREAD_PCT = 1.5
NEAR_LIMIT_LIVE_MIN_REBOUND_FROM_LOW_PCT = 1.0
LIVE_ELIGIBLE_COHORTS = {
    "consecutive_limit_down_2plus",
    "single_limit_down",
    "near_limit_rebound",
}

SOURCE_ONLY_FIELDS = {
    "runtime_effect": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "allowed_runtime_apply": False,
}
FORBIDDEN_USES = (
    "direct_real_order,automatic_runtime_apply,provider_route_change,"
    "bot_restart,hard_safety_bypass"
)
LIVE_AUTO_FORBIDDEN_USES = (
    "direct_broker_order_submission,hard_safety_bypass,stale_quote_bypass,"
    "account_order_quantity_cooldown_bypass,provider_route_change,bot_restart,"
    "scale_in,reentry,overnight,position_sizing_owner_override"
)
COUNTERFACTUAL_CONTRACT = {
    "metric_role": "primary_ev",
    "decision_authority": "limit_down_counterfactual_sim_only",
    "window_policy": "rolling_clean_baseline_ordered_unlock_entry",
    "sample_floor": "5_dates_20_paths_with_independent_cell_floors",
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": "valid_ordered_path_and_raw_row_exclusion",
    "forbidden_uses": FORBIDDEN_USES,
}
POST_SIM_CONTRACT = {
    "metric_role": "primary_ev",
    "decision_authority": "limit_down_post_sim_attribution_only",
    "window_policy": "rolling_clean_baseline_post_sim_attribution",
    "sample_floor": "20_prior_policy_matches_with_independent_cell_floors",
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": "valid_sim_attribution_and_raw_row_exclusion",
    "forbidden_uses": FORBIDDEN_USES,
}


def _safe_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _contract_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    normalized = str(value or "").strip().lower()
    if normalized in {"1", "true"}:
        return True
    if normalized in {"0", "false"}:
        return False
    return None


def _parse_dt(value: Any) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value or "").strip())
    except ValueError:
        return None


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, ensure_ascii=False, indent=2, allow_nan=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def _event_contract_valid(row: dict[str, Any]) -> bool:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    return bool(
        fields.get("decision_authority") == "limit_down_source_observation_only"
        and _contract_bool(fields.get("runtime_effect")) is False
        and _contract_bool(fields.get("actual_order_submitted")) is False
        and _contract_bool(fields.get("broker_order_forbidden")) is True
    )


def _event_path(target_date: str) -> Path | None:
    raw = EVENT_DIR / f"pipeline_events_{target_date}.jsonl"
    compressed = raw.with_suffix(raw.suffix + ".gz")
    if raw.exists():
        return raw
    return compressed if compressed.exists() else None


def _iter_events(path: Path) -> Iterable[dict[str, Any]]:
    opener = gzip.open if path.suffix == ".gz" else open
    with opener(path, "rt", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                yield {"_invalid_json": True}
                continue
            yield row if isinstance(row, dict) else {"_invalid_schema": True}


def _candidate_source(
    target_date: str,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    path = CANDIDATE_DIR / f"limit_down_watch_candidate_source_{target_date}.json"
    payload = _load_json(path)
    candidates = (
        payload.get("candidates") if isinstance(payload.get("candidates"), list) else []
    )
    valid = bool(
        payload.get("schema_version") == 1
        and payload.get("report_type") == "limit_down_watch_candidate_source"
        and payload.get("target_date") == target_date
        and payload.get("status") in {"pass", "partial"}
        and payload.get("candidate_count") == len(candidates)
        and payload.get("decision_authority") == "limit_down_source_observation_only"
        and payload.get("runtime_effect") is False
        and payload.get("actual_order_submitted") is False
        and payload.get("broker_order_forbidden") is True
    )
    by_code = {
        str(row.get("code") or "").strip(): row
        for row in candidates
        if isinstance(row, dict) and str(row.get("code") or "").strip()
    }
    return by_code, {
        "path": str(path),
        "valid": valid,
        "status": payload.get("status") if payload else "missing",
        "candidate_count": len(by_code),
    }


def collect_observation_visits(
    target_date: str,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Collect visit-scoped ordered events without materializing unrelated rows."""

    candidates, candidate_status = _candidate_source(target_date)
    path = _event_path(target_date)
    status = {
        "path": (
            str(path)
            if path
            else str(EVENT_DIR / f"pipeline_events_{target_date}.jsonl")
        ),
        "exists": path is not None,
        "valid": False,
        "matching_event_count": 0,
        "contract_violation_count": 0,
        "invalid_row_count": 0,
        "candidate_source": candidate_status,
    }
    if candidate_status["valid"] and candidate_status["candidate_count"] == 0:
        status["valid"] = True
        status["scan_skipped"] = True
        status["scan_skip_reason"] = "valid_no_candidate"
        return [], status
    if path is None or not candidate_status["valid"]:
        return [], status

    active: dict[str, dict[str, Any]] = {}
    visits: list[dict[str, Any]] = []
    visit_sequence: defaultdict[str, int] = defaultdict(int)

    def close_visit(code: str, reason: str) -> None:
        visit = active.pop(code, None)
        if visit is None:
            return
        visit["release_reason"] = reason
        visits.append(visit)

    try:
        for event in _iter_events(path):
            if event.get("_invalid_json") or event.get("_invalid_schema"):
                status["invalid_row_count"] += 1
                continue
            if event.get("pipeline") != "LIMIT_DOWN_WATCH":
                continue
            status["matching_event_count"] += 1
            if not _event_contract_valid(event):
                status["contract_violation_count"] += 1
                continue
            code = str(event.get("stock_code") or "").strip()
            stage = str(event.get("stage") or "").strip()
            fields = (
                event.get("fields") if isinstance(event.get("fields"), dict) else {}
            )
            emitted_at = _parse_dt(event.get("emitted_at"))
            if not code or emitted_at is None:
                status["invalid_row_count"] += 1
                continue
            if stage == "limit_down_watch_registered":
                close_visit(code, "implicit_reregister")
                visit_sequence[code] += 1
                source = candidates.get(code) or {}
                active[code] = {
                    "row_id": f"{target_date}:{code}:{visit_sequence[code]}",
                    "target_date": target_date,
                    "code": code,
                    "name": str(event.get("stock_name") or source.get("name") or code),
                    "registered_at": emitted_at.isoformat(),
                    "cohort": str(
                        source.get("cohort") or fields.get("cohort") or "unknown"
                    ),
                    "price_band": str(
                        source.get("price_band")
                        or fields.get("price_band")
                        or "unknown"
                    ),
                    "consecutive_count": _safe_int(
                        source.get("consecutive_count")
                        or fields.get("consecutive_count")
                    ),
                    "candidate_kind": str(
                        source.get("candidate_kind") or "exact_limit_down"
                    ),
                    "limit_down_close": _safe_int(source.get("limit_down_close")),
                    "lower_limit_price": _safe_int(fields.get("lower_limit_price")),
                    "transitions": [],
                    "confirmations": [],
                    "snapshots": [],
                }
                continue
            visit = active.get(code)
            if visit is None:
                continue
            if stage == "limit_down_watch_state_transition":
                visit["transitions"].append(
                    {
                        "at": emitted_at.isoformat(),
                        "phase": str(fields.get("phase") or ""),
                        "previous_phase": str(fields.get("previous_phase") or ""),
                        "current_price": _safe_int(fields.get("current_price")),
                    }
                )
            elif stage == "limit_down_watch_unlock_confirmed":
                visit["confirmations"].append(
                    {
                        "at": emitted_at.isoformat(),
                        "phase": str(fields.get("phase") or "UNLOCKED"),
                        "current_price": _safe_int(fields.get("current_price")),
                        "best_ask": _safe_int(fields.get("best_ask")),
                        "best_bid": _safe_int(fields.get("best_bid")),
                        "spread": _safe_int(fields.get("spread"), -1),
                        "confirmation_tick_count": _safe_int(
                            fields.get("confirmation_tick_count")
                        ),
                        "confirmation_type": "exact_unlock",
                    }
                )
            elif stage == "limit_down_watch_rebound_confirmed":
                visit["confirmations"].append(
                    {
                        "at": emitted_at.isoformat(),
                        "phase": str(fields.get("phase") or "NEAR_REBOUND_OBSERVING"),
                        "current_price": _safe_int(fields.get("current_price")),
                        "open_price": _safe_int(fields.get("open_price")),
                        "low_price": _safe_int(fields.get("low_price")),
                        "rebound_from_low_pct": _safe_float(
                            fields.get("rebound_from_low_pct")
                        ),
                        "best_ask": _safe_int(fields.get("best_ask")),
                        "best_bid": _safe_int(fields.get("best_bid")),
                        "confirmation_tick_count": _safe_int(
                            fields.get("confirmation_tick_count")
                        ),
                        "confirmation_type": "near_rebound",
                    }
                )
            elif stage == "limit_down_watch_snapshot":
                visit["snapshots"].append(
                    {
                        "at": emitted_at.isoformat(),
                        "phase": str(fields.get("phase") or ""),
                        "current_price": _safe_int(fields.get("current_price")),
                        "open_price": _safe_int(fields.get("open_price")),
                        "high_price": _safe_int(fields.get("high_price")),
                        "low_price": _safe_int(fields.get("low_price")),
                        "best_ask": _safe_int(fields.get("best_ask")),
                        "best_bid": _safe_int(fields.get("best_bid")),
                        "spread": _safe_int(fields.get("spread"), -1),
                        "trade_value": _safe_int(fields.get("trade_value")),
                        "volume": _safe_int(fields.get("volume")),
                    }
                )
            elif stage == "limit_down_watch_released":
                close_visit(code, str(fields.get("reason") or "released"))
    except (OSError, UnicodeError):
        return [], status

    for code in list(active):
        close_visit(code, "session_file_ended")
    status["valid"] = bool(
        status["exists"]
        and status["candidate_source"]["valid"]
        and status["contract_violation_count"] == 0
        and status["invalid_row_count"] == 0
    )
    return visits, status


def _percentile(values: list[float], percentile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * percentile
    lower = math.floor(index)
    upper = math.ceil(index)
    if lower == upper:
        return round(ordered[lower], 6)
    weight = index - lower
    return round(ordered[lower] * (1.0 - weight) + ordered[upper] * weight, 6)


def _pct(exit_price: int, entry_price: int) -> float | None:
    if exit_price <= 0 or entry_price <= 0:
        return None
    return round((exit_price / entry_price - 1.0) * 100.0, 6)


def label_observation_visit(visit: dict[str, Any]) -> dict[str, Any]:
    snapshots = [row for row in visit.get("snapshots", []) if isinstance(row, dict)]
    snapshots.sort(key=lambda row: str(row.get("at") or ""))
    lower_limit = _safe_int(visit.get("lower_limit_price"))
    unlocked = [
        (index, row)
        for index, row in enumerate(snapshots)
        if row.get("phase") in {"UNLOCKED", "UNLOCKED_AGAIN"}
        and _safe_int(row.get("current_price")) > lower_limit > 0
    ]
    label = {
        "row_id": visit.get("row_id"),
        "target_date": visit.get("target_date"),
        "code": visit.get("code"),
        "name": visit.get("name"),
        "cohort": visit.get("cohort"),
        "price_band": visit.get("price_band"),
        "consecutive_count": _safe_int(visit.get("consecutive_count")),
        "registered_at": visit.get("registered_at"),
        "release_reason": visit.get("release_reason"),
        "ordered_snapshot_count": len(snapshots),
        "label_status": "insufficient_ordered_unlock_confirmation",
        **SOURCE_ONLY_FIELDS,
    }
    cohort = str(visit.get("cohort") or "")
    if cohort not in LIVE_ELIGIBLE_COHORTS:
        label["label_status"] = "observation_only_cohort_separate_contract_required"
        return label
    if cohort == "near_limit_rebound":
        label["label_status"] = "insufficient_ordered_rebound_confirmation"
    confirmation = None
    confirmation_type = "exact_unlock"
    if cohort == "near_limit_rebound":
        confirmation_type = "near_rebound"
        confirmations = [
            row
            for row in visit.get("confirmations", [])
            if isinstance(row, dict)
            and row.get("confirmation_type") == "near_rebound"
            and _safe_int(row.get("confirmation_tick_count")) >= 2
            and _safe_int(row.get("current_price"))
            >= _safe_int(row.get("open_price"))
            > 0
            and _safe_int(row.get("current_price"))
            > _safe_int(row.get("low_price"))
            > 0
            and (_safe_float(row.get("rebound_from_low_pct")) or 0.0)
            >= NEAR_LIMIT_LIVE_MIN_REBOUND_FROM_LOW_PCT
        ]
        confirmations.sort(key=lambda row: str(row.get("at") or ""))
        confirmation = confirmations[0] if confirmations else None
        trigger_rows = []
    else:
        confirmations = [
            row for row in visit.get("confirmations", []) if isinstance(row, dict)
        ]
        confirmations.sort(key=lambda row: str(row.get("at") or ""))
        confirmation = confirmations[0] if confirmations else None
        trigger_rows = unlocked
    if confirmation is None:
        if len(trigger_rows) < 2:
            return label
        first_index, first = trigger_rows[0]
        first_at = _parse_dt(first.get("at"))
        if first_at is None:
            return label
        for index, row in trigger_rows[1:]:
            observed_at = _parse_dt(row.get("at"))
            if (
                index > first_index
                and observed_at is not None
                and 0.0 <= (observed_at - first_at).total_seconds() <= 30.0
            ):
                confirmation = row
                break
    if confirmation is None:
        return label
    entry_at = _parse_dt(confirmation.get("at"))
    if entry_at is None:
        return label
    current_entry = _safe_int(confirmation.get("current_price"))
    best_ask = _safe_int(confirmation.get("best_ask"))
    entry_price = best_ask if best_ask > 0 else current_entry
    if entry_price <= 0 or (
        cohort in {"consecutive_limit_down_2plus", "single_limit_down"}
        and entry_price <= lower_limit
    ):
        return label

    after = []
    for row in snapshots:
        observed_at = _parse_dt(row.get("at"))
        price = _safe_int(row.get("current_price"))
        if observed_at is None or observed_at < entry_at or price <= 0:
            continue
        after.append((observed_at, row))
    if not after:
        return label

    horizon_rows: dict[str, dict[str, Any] | None] = {}
    for horizon in HORIZONS_SEC:
        point = next(
            (
                (observed_at, row)
                for observed_at, row in after
                if (observed_at - entry_at).total_seconds() >= horizon
            ),
            None,
        )
        horizon_rows[str(horizon)] = (
            {
                "at": point[0].isoformat(),
                "price": _safe_int(point[1].get("current_price")),
                "gross_return_pct": _pct(
                    _safe_int(point[1].get("current_price")), entry_price
                ),
            }
            if point
            else None
        )
    selected = horizon_rows[str(SELECTED_EXIT_HORIZON_SEC)]
    if selected is None:
        final_at, final_row = after[-1]
        if (final_at - entry_at).total_seconds() < 30.0:
            return label
        selected = {
            "at": final_at.isoformat(),
            "price": _safe_int(final_row.get("current_price")),
            "gross_return_pct": _pct(
                _safe_int(final_row.get("current_price")), entry_price
            ),
        }

    spread_pct = None
    best_bid = _safe_int(confirmation.get("best_bid"))
    if best_ask > 0 and best_bid > 0 and best_ask >= best_bid:
        spread_pct = round((best_ask - best_bid) / best_ask * 100.0, 6)
    cost_pct = max(
        DEFAULT_ROUND_TRIP_COST_PCT,
        round((spread_pct or 0.0) * 2.0, 6),
    )
    prices = [_safe_int(row.get("current_price")) for _, row in after]
    prices = [price for price in prices if price > 0]
    gross_return = _safe_float(selected.get("gross_return_pct"))
    transitions = [row for row in visit.get("transitions", []) if isinstance(row, dict)]
    relocked_after_entry = any(
        row.get("phase") == "RELOCKED"
        and (_parse_dt(row.get("at")) or datetime.min) >= entry_at
        for row in transitions
    )
    selected_at = _parse_dt(selected.get("at"))
    if selected_at is None:
        return label
    duration_sec = max(0.0, (selected_at - entry_at).total_seconds())
    label.update(
        {
            "label_status": "pass",
            "entry_at": entry_at.isoformat(),
            "entry_confirmation_type": confirmation_type,
            "entry_price": entry_price,
            "entry_price_source": "best_ask" if best_ask > 0 else "current_tick_proxy",
            "entry_bbo_available": best_ask > 0 and best_bid > 0,
            "entry_spread_pct": spread_pct,
            "exit_at": selected.get("at"),
            "exit_price": _safe_int(selected.get("price")),
            "selected_exit_horizon_sec": SELECTED_EXIT_HORIZON_SEC,
            "actual_observation_duration_sec": round(duration_sec, 3),
            "slot_hours": round(duration_sec / 3600.0, 6),
            "gross_return_pct": gross_return,
            "estimated_round_trip_cost_pct": cost_pct,
            "net_return_pct": (
                round(gross_return - cost_pct, 6) if gross_return is not None else None
            ),
            "mfe_pct": _pct(max(prices), entry_price) if prices else None,
            "mae_pct": _pct(min(prices), entry_price) if prices else None,
            "relocked_after_entry": relocked_after_entry,
            "horizon_outcomes": horizon_rows,
        }
    )
    return label


def _latest_prior_artifact(
    directory: Path, prefix: str, target_date: str
) -> dict[str, Any]:
    target = date.fromisoformat(target_date)
    candidates: list[tuple[date, Path]] = []
    for path in directory.glob(f"{prefix}_*.json"):
        suffix = path.stem.removeprefix(f"{prefix}_")
        try:
            artifact_date = date.fromisoformat(suffix)
        except ValueError:
            continue
        if ROLLOUT_DATE <= artifact_date < target:
            candidates.append((artifact_date, path))
    return _load_json(max(candidates)[1]) if candidates else {}


def _rows_in_rolling_window(
    rows: Iterable[dict[str, Any]], target_date: str
) -> list[dict[str, Any]]:
    target = date.fromisoformat(target_date)
    window_start = max(
        ROLLOUT_DATE, target - timedelta(days=ROLLING_WINDOW_CALENDAR_DAYS)
    )
    selected = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        try:
            row_date = date.fromisoformat(str(row.get("target_date") or ""))
        except ValueError:
            continue
        if window_start <= row_date <= target:
            selected.append(row)
    return selected


def _prior_counterfactual_valid(payload: dict[str, Any], target_date: str) -> bool:
    if not payload:
        return True
    rows = payload.get("rows")
    try:
        artifact_date = date.fromisoformat(str(payload.get("target_date") or ""))
        current_date = date.fromisoformat(target_date)
    except ValueError:
        return False
    row_ids = (
        [str(row.get("row_id") or "") for row in rows if isinstance(row, dict)]
        if isinstance(rows, list)
        else []
    )
    cumulative = payload.get("cumulative_update")
    cumulative_valid = bool(
        cumulative is None
        or (
            isinstance(cumulative, dict)
            and cumulative.get("mode")
            == "latest_prior_rolling_rows_plus_current_dedup_by_row_id"
            and _safe_int(cumulative.get("deduplicated_rolling_row_count")) == len(rows)
        )
    )
    return bool(
        payload.get("schema_version") == 1
        and payload.get("report_type") == "limit_down_watch_counterfactual"
        and artifact_date < current_date
        and isinstance(rows, list)
        and len(row_ids) == len(rows)
        and all(row_ids)
        and len(set(row_ids)) == len(row_ids)
        and payload.get("runtime_effect") is False
        and payload.get("actual_order_submitted") is False
        and payload.get("broker_order_forbidden") is True
        and payload.get("allowed_runtime_apply") is False
        and all(
            payload.get(field) == expected
            for field, expected in COUNTERFACTUAL_CONTRACT.items()
        )
        and cumulative_valid
    )


def _aggregate_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    valid = [
        row
        for row in rows
        if row.get("label_status") == "pass"
        and _safe_float(row.get("net_return_pct")) is not None
    ]
    net_returns = [_safe_float(row.get("net_return_pct")) for row in valid]
    net_returns = [value for value in net_returns if value is not None]
    mfe = [_safe_float(row.get("mfe_pct")) for row in valid]
    mfe = [value for value in mfe if value is not None]
    mae = [_safe_float(row.get("mae_pct")) for row in valid]
    mae = [value for value in mae if value is not None]
    dates = {str(row.get("target_date")) for row in valid if row.get("target_date")}
    slot_hours = sum(
        max(0.0, _safe_float(row.get("slot_hours")) or 0.0) for row in valid
    )
    total_net = sum(net_returns)
    mean_net = total_net / len(net_returns) if net_returns else None
    sample_std = None
    if len(net_returns) >= 2 and mean_net is not None:
        sample_std = math.sqrt(
            sum((value - mean_net) ** 2 for value in net_returns)
            / (len(net_returns) - 1)
        )
    weighted_denominator = sum(
        max(0, _safe_int(row.get("entry_price"))) for row in valid
    )
    weighted_numerator = sum(
        max(0, _safe_int(row.get("entry_price")))
        * (_safe_float(row.get("net_return_pct")) or 0.0)
        for row in valid
    )
    return {
        "sample_count": len(valid),
        "observation_date_count": len(dates),
        "included_dates": sorted(dates),
        "source_quality_adjusted_ev_pct": (
            round(mean_net, 6) if mean_net is not None else None
        ),
        "ev_lower_confidence_bound_90_pct": (
            round(mean_net - 1.645 * sample_std / math.sqrt(len(net_returns)), 6)
            if mean_net is not None and sample_std is not None
            else None
        ),
        "notional_weighted_ev_pct": (
            round(weighted_numerator / weighted_denominator, 6)
            if weighted_denominator > 0
            else None
        ),
        "expected_daily_net_profit_per_watch_slot_hour_pct": (
            round(total_net / slot_hours, 6) if slot_hours > 0 else None
        ),
        "downside_p10_pct": _percentile(net_returns, 0.10),
        "mfe_p50_pct": _percentile(mfe, 0.50),
        "mae_p10_pct": _percentile(mae, 0.10),
        "relock_rate_pct": (
            round(
                sum(1 for row in valid if row.get("relocked_after_entry") is True)
                / len(valid)
                * 100.0,
                4,
            )
            if valid
            else None
        ),
        "entry_bbo_coverage_pct": (
            round(
                sum(1 for row in valid if row.get("entry_bbo_available") is True)
                / len(valid)
                * 100.0,
                4,
            )
            if valid
            else None
        ),
    }


def _cell_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: defaultdict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("label_status") != "pass":
            continue
        if str(row.get("cohort") or "") not in LIVE_ELIGIBLE_COHORTS:
            continue
        grouped[
            (
                str(row.get("cohort") or "unknown"),
                str(row.get("price_band") or "unknown"),
            )
        ].append(row)
    result = []
    for (cohort, band), members in sorted(grouped.items()):
        metrics = _aggregate_rows(members)
        ev = _safe_float(metrics.get("source_quality_adjusted_ev_pct"))
        result.append(
            {
                "policy_key": f"{cohort}|{band}",
                "cohort": cohort,
                "price_band": band,
                **metrics,
                "eligible_for_sim": bool(
                    metrics["sample_count"] >= MIN_CELL_SAMPLE
                    and metrics["observation_date_count"] >= MIN_CELL_DATES
                    and ev is not None
                    and ev > 0.0
                ),
            }
        )
    return result


def build_counterfactual(
    target_date: str,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    visits, source_status = collect_observation_visits(target_date)
    current_rows = [label_observation_visit(visit) for visit in visits]
    prior = _latest_prior_artifact(
        COUNTERFACTUAL_DIR, "limit_down_watch_counterfactual", target_date
    )
    prior_valid = _prior_counterfactual_valid(prior, target_date)
    prior_rows = (
        prior.get("rows") if prior_valid and isinstance(prior.get("rows"), list) else []
    )
    source_status = dict(source_status)
    source_status["prior_counterfactual_present"] = bool(prior)
    source_status["prior_counterfactual_valid"] = prior_valid
    source_status["valid"] = bool(source_status.get("valid") and prior_valid)
    deduped = {
        str(row.get("row_id")): row
        for row in [*prior_rows, *current_rows]
        if isinstance(row, dict) and row.get("row_id")
    }
    rows = sorted(
        _rows_in_rolling_window(deduped.values(), target_date),
        key=lambda row: str(row.get("row_id")),
    )
    cumulative_update = {
        "mode": "latest_prior_rolling_rows_plus_current_dedup_by_row_id",
        "prior_artifact_target_date": prior.get("target_date"),
        "prior_input_row_count": len(prior_rows),
        "current_input_row_count": len(current_rows),
        "deduplicated_rolling_row_count": len(rows),
        "duplicate_or_out_of_window_row_count": max(
            0, len(prior_rows) + len(current_rows) - len(rows)
        ),
    }
    metrics = _aggregate_rows(rows)
    cells = _cell_rows(rows)
    eligible_cells = [row for row in cells if row.get("eligible_for_sim") is True]
    best_ev = max(
        (
            _safe_float(row.get("source_quality_adjusted_ev_pct")) or -math.inf
            for row in eligible_cells
        ),
        default=None,
    )
    sufficient = bool(
        source_status["valid"]
        and metrics["sample_count"] >= MIN_COUNTERFACTUAL_SAMPLE
        and metrics["observation_date_count"] >= MIN_COUNTERFACTUAL_DATES
        and eligible_cells
    )
    payload = {
        "schema_version": 1,
        "report_type": "limit_down_watch_counterfactual",
        "target_date": target_date,
        "generated_at": datetime.now().isoformat(),
        "status": (
            "pass"
            if sufficient
            else ("insufficient_sample" if source_status["valid"] else "source_blocked")
        ),
        "source_quality_status": "pass" if source_status["valid"] else "blocked",
        "source_status": source_status,
        "rolling_window_calendar_days": ROLLING_WINDOW_CALENDAR_DAYS,
        "cumulative_update": cumulative_update,
        **metrics,
        "consecutive_limit_down_2plus_sample_count": sum(
            1
            for row in rows
            if row.get("label_status") == "pass"
            and row.get("cohort") == "consecutive_limit_down_2plus"
        ),
        "single_limit_down_sample_count": sum(
            1
            for row in rows
            if row.get("label_status") == "pass"
            and row.get("cohort") == "single_limit_down"
        ),
        "near_limit_rebound_sample_count": sum(
            1
            for row in rows
            if row.get("label_status") == "pass"
            and row.get("cohort") == "near_limit_rebound"
        ),
        "eligible_policy_count": len(eligible_cells),
        "best_eligible_policy_ev_pct": (
            None if best_ev in {None, -math.inf} else round(best_ev, 6)
        ),
        "policy_cells": cells,
        "rows": rows,
        **COUNTERFACTUAL_CONTRACT,
        **SOURCE_ONLY_FIELDS,
    }
    return payload, current_rows, source_status


def build_sim_policy_catalog(
    target_date: str, counterfactual: dict[str, Any]
) -> dict[str, Any]:
    cells = (
        counterfactual.get("policy_cells")
        if isinstance(counterfactual.get("policy_cells"), list)
        else []
    )
    policies = []
    for row in cells:
        if not isinstance(row, dict) or row.get("eligible_for_sim") is not True:
            continue
        policies.append(
            {
                "policy_key": row.get("policy_key"),
                "cohort": row.get("cohort"),
                "price_band": row.get("price_band"),
                "source_quality_adjusted_ev_pct": row.get(
                    "source_quality_adjusted_ev_pct"
                ),
                "sample_count": row.get("sample_count"),
                "observation_date_count": row.get("observation_date_count"),
                "entry_rule": (
                    "two_ordered_near_rebound_snapshots_within_30s_"
                    "at_or_above_session_open_and_1pct_above_low"
                    if row.get("cohort") == "near_limit_rebound"
                    else "two_ordered_unlocked_snapshots_within_30s_above_lower_limit"
                ),
                "exit_horizon_sec": SELECTED_EXIT_HORIZON_SEC,
                "execution_cost_policy": "max_30bp_or_twice_observed_spread",
                "runtime_effect": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            }
        )
    return {
        "schema_version": 1,
        "report_type": "limit_down_watch_sim_policy_catalog",
        "target_date": target_date,
        "generated_at": datetime.now().isoformat(),
        "status": "pass" if policies else "insufficient_sample",
        "allowed_sim_apply": bool(policies),
        "active_policy_count": len(policies),
        "active_policies": policies,
        "decision_authority": "limit_down_sim_policy_only",
        "forbidden_uses": FORBIDDEN_USES,
        **SOURCE_ONLY_FIELDS,
    }


def build_post_sim_attribution(
    target_date: str, current_rows: list[dict[str, Any]]
) -> dict[str, Any]:
    prior_policy = _latest_prior_artifact(
        SIM_POLICY_DIR, "limit_down_watch_sim_policy_catalog", target_date
    )
    policies = (
        prior_policy.get("active_policies")
        if isinstance(prior_policy.get("active_policies"), list)
        else []
    )
    policy_keys = {
        str(row.get("policy_key"))
        for row in policies
        if isinstance(row, dict) and row.get("policy_key")
    }
    matched_current = [
        {**row, "matched_policy_key": f"{row.get('cohort')}|{row.get('price_band')}"}
        for row in current_rows
        if row.get("label_status") == "pass"
        and f"{row.get('cohort')}|{row.get('price_band')}" in policy_keys
    ]
    prior = _latest_prior_artifact(
        POST_SIM_DIR, "limit_down_watch_post_sim_attribution", target_date
    )
    prior_rows = prior.get("rows") if isinstance(prior.get("rows"), list) else []
    rows = {
        str(row.get("row_id")): row
        for row in [*prior_rows, *matched_current]
        if isinstance(row, dict) and row.get("row_id")
    }
    rows_list = sorted(
        _rows_in_rolling_window(rows.values(), target_date),
        key=lambda row: str(row.get("row_id")),
    )
    metrics = _aggregate_rows(rows_list)
    cell_metrics = _cell_rows(rows_list)
    qualified = [
        row
        for row in cell_metrics
        if row.get("sample_count", 0) >= MIN_POST_SIM_CELL_SAMPLE
        and row.get("observation_date_count", 0) >= MIN_CELL_DATES
        and (_safe_float(row.get("source_quality_adjusted_ev_pct")) or 0.0) > 0.0
    ]
    best_ev = max(
        (
            _safe_float(row.get("source_quality_adjusted_ev_pct")) or -math.inf
            for row in qualified
        ),
        default=None,
    )
    sufficient = bool(metrics["sample_count"] >= MIN_POST_SIM_SAMPLE and qualified)
    return {
        "schema_version": 1,
        "report_type": "limit_down_watch_post_sim_attribution",
        "target_date": target_date,
        "generated_at": datetime.now().isoformat(),
        "status": "pass" if sufficient else "insufficient_sample",
        "source_quality_status": "pass" if prior_policy else "policy_missing",
        "prior_policy_target_date": prior_policy.get("target_date"),
        "rolling_window_calendar_days": ROLLING_WINDOW_CALENDAR_DAYS,
        **metrics,
        "qualified_policy_count": len(qualified),
        "best_qualified_policy_ev_pct": (
            None if best_ev in {None, -math.inf} else round(best_ev, 6)
        ),
        "policy_cells": cell_metrics,
        "rows": rows_list,
        **POST_SIM_CONTRACT,
        **SOURCE_ONLY_FIELDS,
    }


def build_bounded_live_candidate(
    target_date: str, counterfactual: dict[str, Any]
) -> dict[str, Any]:
    cells = (
        counterfactual.get("policy_cells")
        if isinstance(counterfactual.get("policy_cells"), list)
        else []
    )
    candidates = []
    for row in cells:
        if not isinstance(row, dict):
            continue
        if str(row.get("cohort") or "") not in LIVE_ELIGIBLE_COHORTS:
            continue
        ev = _safe_float(row.get("source_quality_adjusted_ev_pct"))
        downside = _safe_float(row.get("downside_p10_pct"))
        mae_p10 = _safe_float(row.get("mae_p10_pct"))
        relock_rate = _safe_float(row.get("relock_rate_pct"))
        bbo_rate = _safe_float(row.get("entry_bbo_coverage_pct"))
        if not (
            counterfactual.get("source_quality_status") == "pass"
            and row.get("sample_count", 0) >= MIN_LIVE_AUTO_CELL_SAMPLE
            and row.get("observation_date_count", 0) >= MIN_LIVE_AUTO_CELL_DATES
            and ev is not None
            and ev > 0.0
            and downside is not None
            and downside > 0.0
            and mae_p10 is not None
            and mae_p10 >= LIVE_AUTO_MAX_MAE_P10_PCT
            and relock_rate is not None
            and relock_rate <= LIVE_AUTO_MAX_RELOCK_RATE_PCT
            and bbo_rate is not None
            and bbo_rate >= LIVE_AUTO_MIN_BBO_COVERAGE_PCT
        ):
            continue
        candidates.append(
            {
                "policy_key": row.get("policy_key"),
                "cohort": row.get("cohort"),
                "price_band": row.get("price_band"),
                "source_quality_adjusted_ev_pct": ev,
                "sample_count": row.get("sample_count"),
                "observation_date_count": row.get("observation_date_count"),
                "evidence_mode": "single_verified_ordered_path_allowed",
                "ev_lower_confidence_bound_90_pct": row.get(
                    "ev_lower_confidence_bound_90_pct"
                ),
                "downside_p10_pct": downside,
                "mae_p10_pct": mae_p10,
                "relock_rate_pct": relock_rate,
                "entry_bbo_coverage_pct": bbo_rate,
            }
        )
    ready = bool(candidates)
    return {
        "schema_version": 1,
        "report_type": "limit_down_watch_bounded_live_candidate",
        "target_date": target_date,
        "generated_at": datetime.now().isoformat(),
        "status": "live_auto_apply_ready" if ready else "blocked",
        "ready_candidate_count": len(candidates),
        "candidates": candidates,
        "decision_authority": "limit_down_live_auto_eligibility_candidate",
        "operator_approval_required": False,
        "preopen_consumer_implemented": True,
        "activation_mode": "latest_valid_prior_date_policy_auto_loaded",
        "source_artifact": str(
            COUNTERFACTUAL_DIR / f"limit_down_watch_counterfactual_{target_date}.json"
        ),
        "sample_floor": "1_verified_ordered_path_per_cohort_price_band",
        "risk_contract": {
            "max_concurrent_positions": 1,
            "max_daily_entries": 1,
            "quantity_owner": "position_sizing_dynamic_formula",
            "requested_quantity_override": None,
            "additional_risk_clamp": "worst_case_capital_loss_not_stop_fill_assumption",
            "scale_in_allowed": False,
            "same_day_reentry_allowed": False,
            "overnight_allowed": False,
            "entry_requires_two_ordered_unlocked_ticks": True,
            "entry_requires_two_ordered_trigger_ticks": True,
            "near_rebound_requires_session_open_recovery": True,
            "near_rebound_min_from_low_pct": (NEAR_LIMIT_LIVE_MIN_REBOUND_FROM_LOW_PCT),
            "entry_requires_fresh_quote_and_bbo": True,
            "max_entry_spread_pct": LIVE_AUTO_MAX_ENTRY_SPREAD_PCT,
            "relock_or_stale_cancels_unfilled_entry": True,
            "normal_scalping_ai_and_submit_guards_required": True,
            "hard_safety_priority": "unchanged_and_unbypassable",
        },
        "forbidden_uses": LIVE_AUTO_FORBIDDEN_USES,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": ready,
    }


def produce_research_artifacts(target_date: str) -> dict[str, Path]:
    counterfactual, current_rows, _source = build_counterfactual(target_date)
    sim_policy = build_sim_policy_catalog(target_date, counterfactual)
    post_sim = build_post_sim_attribution(target_date, current_rows)
    bounded = build_bounded_live_candidate(target_date, counterfactual)
    paths = {
        "counterfactual": COUNTERFACTUAL_DIR
        / f"limit_down_watch_counterfactual_{target_date}.json",
        "sim_policy_catalog": SIM_POLICY_DIR
        / f"limit_down_watch_sim_policy_catalog_{target_date}.json",
        "post_sim_attribution": POST_SIM_DIR
        / f"limit_down_watch_post_sim_attribution_{target_date}.json",
        "bounded_live_candidate": BOUNDED_CANDIDATE_DIR
        / f"limit_down_watch_bounded_live_candidate_{target_date}.json",
    }
    for key, payload in (
        ("counterfactual", counterfactual),
        ("sim_policy_catalog", sim_policy),
        ("post_sim_attribution", post_sim),
        ("bounded_live_candidate", bounded),
    ):
        _atomic_write_json(paths[key], payload)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-date", default=date.today().isoformat())
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if not args.write:
        counterfactual, current_rows, source = build_counterfactual(args.target_date)
        print(
            json.dumps(
                {
                    "counterfactual": counterfactual,
                    "current_row_count": len(current_rows),
                    "source": source,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0
    paths = produce_research_artifacts(args.target_date)
    for path in paths.values():
        print(path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
