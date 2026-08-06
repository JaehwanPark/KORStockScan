"""Build upper-limit observation, cumulative EV, and bounded-live artifacts."""

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
CANDIDATE_DIR = DATA_DIR / "report" / "upper_limit_watch_candidate_source"
REPORT_DIR = DATA_DIR / "report" / "upper_limit_watch"
COUNTERFACTUAL_DIR = DATA_DIR / "report" / "upper_limit_watch_counterfactual"
BOUNDED_DIR = DATA_DIR / "threshold_cycle" / "bounded_live_candidates"

CLEAN_BASELINE_DATE = date(2026, 6, 5)
ROLLING_DAYS = 90
EXIT_HORIZON_SEC = 180
EXIT_TOLERANCE_SEC = 60
ROUND_TRIP_COST_PCT = 0.30
MIN_LIVE_SAMPLE = 1
MIN_LIVE_DATES = 1
MAX_MAE_P10_PCT = -5.0
MAX_ENTRY_SPREAD_PCT = 1.5

OBSERVATION_CONTRACT = {
    "metric_role": "diagnostic",
    "decision_authority": "upper_limit_source_observation_only",
    "window_policy": "same_symbol_same_krx_session_ordered_0b_trade_and_0d_quote",
    "sample_floor": "not_applicable_source_observation",
    "primary_decision_metric": "ordered_gap_pullback_reclaim_breakout_path_capture_rate",
    "source_quality_gate": "official_ka10017_previous_limit_up_and_ka10081_db_ohlc_match",
    "forbidden_uses": (
        "direct_real_order,buy_analysis_from_observer,threshold_change,"
        "provider_route_change,order_price_or_quantity_change,cap_change,"
        "broker_guard_change,bot_restart_authority"
    ),
}
COUNTERFACTUAL_CONTRACT = {
    "metric_role": "primary_ev",
    "decision_authority": "upper_limit_counterfactual_sim_only",
    "window_policy": "rolling_clean_baseline_ordered_two_tick_trigger_entry",
    "sample_floor": "1_verified_path_per_cohort_price_band_trigger",
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": "valid_ordered_path_fresh_bbo_and_completed_180s_label",
    "forbidden_uses": (
        "direct_real_order,provider_route_change,bot_restart,hard_safety_bypass,"
        "position_sizing_owner_override"
    ),
}


def _safe_float(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _safe_int(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _parse_dt(value: Any) -> datetime | None:
    try:
        return datetime.fromisoformat(str(value or "").strip())
    except ValueError:
        return None


def _load_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _atomic_write(path: Path, payload: dict[str, Any]) -> None:
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
                payload = json.loads(line)
            except json.JSONDecodeError:
                yield {"_invalid": True}
                continue
            yield payload if isinstance(payload, dict) else {"_invalid": True}


def _event_contract_valid(fields: dict[str, Any]) -> bool:
    return bool(
        fields.get("decision_authority") == "upper_limit_source_observation_only"
        and fields.get("runtime_effect") is False
        and fields.get("actual_order_submitted") is False
        and fields.get("broker_order_forbidden") is True
    )


def _candidate_source(
    target_date: str,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    path = CANDIDATE_DIR / f"upper_limit_watch_candidate_source_{target_date}.json"
    payload = _load_json(path)
    rows = (
        payload.get("candidates") if isinstance(payload.get("candidates"), list) else []
    )
    valid = bool(
        payload.get("schema_version") == 1
        and payload.get("report_type") == "upper_limit_watch_candidate_source"
        and payload.get("target_date") == target_date
        and payload.get("status") in {"pass", "partial"}
        and payload.get("candidate_count") == len(rows)
        and payload.get("decision_authority") == "upper_limit_source_observation_only"
        and payload.get("runtime_effect") is False
        and payload.get("actual_order_submitted") is False
        and payload.get("broker_order_forbidden") is True
    )
    return (
        {
            str(row.get("code") or "").strip(): row
            for row in rows
            if isinstance(row, dict) and str(row.get("code") or "").strip()
        },
        {
            "path": str(path),
            "valid": valid,
            "status": payload.get("status", "missing"),
            "candidate_count": len(rows),
        },
    )


def collect_visits(target_date: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    candidates, candidate_status = _candidate_source(target_date)
    event_path = _event_path(target_date)
    source = {
        "event_path": str(
            event_path or EVENT_DIR / f"pipeline_events_{target_date}.jsonl"
        ),
        "candidate_source": candidate_status,
        "matching_event_count": 0,
        "invalid_row_count": 0,
        "contract_violation_count": 0,
        "valid": False,
    }
    if candidate_status["valid"] and not candidates:
        source.update({"valid": True, "scan_skip_reason": "valid_no_candidate"})
        return [], source
    if not candidate_status["valid"] or event_path is None:
        return [], source

    active: dict[str, dict[str, Any]] = {}
    completed: list[dict[str, Any]] = []
    sequences: defaultdict[str, int] = defaultdict(int)

    def close(code: str, reason: str) -> None:
        visit = active.pop(code, None)
        if visit:
            visit["release_reason"] = reason
            completed.append(visit)

    try:
        for event in _iter_events(event_path):
            if event.get("_invalid"):
                source["invalid_row_count"] += 1
                continue
            if event.get("pipeline") != "UPPER_LIMIT_WATCH":
                continue
            source["matching_event_count"] += 1
            fields = (
                event.get("fields") if isinstance(event.get("fields"), dict) else {}
            )
            if not _event_contract_valid(fields):
                source["contract_violation_count"] += 1
                continue
            code = str(event.get("stock_code") or "").strip()
            emitted = _parse_dt(event.get("emitted_at"))
            stage = str(event.get("stage") or "")
            if not code or emitted is None:
                source["invalid_row_count"] += 1
                continue
            if stage == "upper_limit_watch_registered":
                close(code, "implicit_reregister")
                sequences[code] += 1
                candidate = candidates.get(code, {})
                active[code] = {
                    "row_id": f"{target_date}:{code}:{sequences[code]}",
                    "target_date": target_date,
                    "code": code,
                    "name": str(
                        event.get("stock_name") or candidate.get("name") or code
                    ),
                    "cohort": str(
                        candidate.get("cohort") or fields.get("cohort") or "unknown"
                    ),
                    "price_band": str(
                        candidate.get("price_band")
                        or fields.get("price_band")
                        or "unknown"
                    ),
                    "registered_at": emitted.isoformat(),
                    "trigger": None,
                    "snapshots": [],
                }
                continue
            visit = active.get(code)
            if visit is None:
                continue
            if (
                stage == "upper_limit_watch_trigger_confirmed"
                and visit["trigger"] is None
            ):
                visit["trigger"] = {
                    "at": emitted.isoformat(),
                    "trigger_type": str(fields.get("trigger_type") or ""),
                    "current_price": _safe_int(fields.get("current_price")),
                    "best_ask": _safe_int(fields.get("best_ask")),
                    "best_bid": _safe_int(fields.get("best_bid")),
                    "quote_age_sec": _safe_float(fields.get("quote_age_sec")),
                    "confirmation_tick_count": _safe_int(
                        fields.get("confirmation_tick_count")
                    ),
                }
            elif stage == "upper_limit_watch_snapshot":
                visit["snapshots"].append(
                    {
                        "at": emitted.isoformat(),
                        "current_price": _safe_int(fields.get("current_price")),
                        "high_price": _safe_int(fields.get("high_price")),
                        "low_price": _safe_int(fields.get("low_price")),
                    }
                )
            elif stage == "upper_limit_watch_released":
                close(code, str(fields.get("reason") or "released"))
    except (OSError, UnicodeError):
        return [], source
    for code in list(active):
        close(code, "session_file_ended")
    source["valid"] = bool(
        source["invalid_row_count"] == 0
        and source["contract_violation_count"] == 0
        and source["matching_event_count"] > 0
    )
    return completed, source


def _pct(exit_price: int, entry_price: int) -> float | None:
    if exit_price <= 0 or entry_price <= 0:
        return None
    return round((exit_price / entry_price - 1.0) * 100.0, 6)


def _label(visit: dict[str, Any]) -> dict[str, Any]:
    trigger = visit.get("trigger") if isinstance(visit.get("trigger"), dict) else {}
    trigger_at = _parse_dt(trigger.get("at"))
    entry_ask = _safe_int(trigger.get("best_ask"))
    entry_bid = _safe_int(trigger.get("best_bid"))
    quote_age_sec = _safe_float(trigger.get("quote_age_sec"))
    result = {
        **{
            key: visit.get(key)
            for key in ("row_id", "target_date", "code", "name", "cohort", "price_band")
        },
        "trigger_type": str(trigger.get("trigger_type") or ""),
        "label_status": "insufficient_ordered_path",
        "entry_bbo_present": bool(
            entry_ask >= entry_bid > 0
            and quote_age_sec is not None
            and 0.0 <= quote_age_sec <= 5.0
        ),
    }
    if trigger_at is None or _safe_int(trigger.get("confirmation_tick_count")) < 2:
        return result
    if not result["entry_bbo_present"]:
        result["label_status"] = "entry_bbo_missing"
        return result
    snapshots = []
    for row in visit.get("snapshots", []):
        at = _parse_dt(row.get("at")) if isinstance(row, dict) else None
        if at is not None and at >= trigger_at:
            snapshots.append((at, row))
    horizon = [
        item
        for item in snapshots
        if EXIT_HORIZON_SEC
        <= (item[0] - trigger_at).total_seconds()
        <= EXIT_HORIZON_SEC + EXIT_TOLERANCE_SEC
    ]
    if not horizon:
        return result
    exit_at, exit_row = min(horizon, key=lambda item: item[0])
    exit_price = _safe_int(exit_row.get("current_price"))
    path_prices = [
        _safe_int(row.get("current_price"))
        for at, row in snapshots
        if at <= exit_at and _safe_int(row.get("current_price")) > 0
    ]
    if exit_price <= 0 or not path_prices:
        return result
    gross = _pct(exit_price, entry_ask)
    result.update(
        {
            "label_status": "pass",
            "entry_at": trigger_at.isoformat(),
            "entry_price": entry_ask,
            "entry_bid": entry_bid,
            "entry_spread_pct": round((entry_ask - entry_bid) / entry_ask * 100.0, 6),
            "exit_at": exit_at.isoformat(),
            "exit_price": exit_price,
            "gross_return_pct": gross,
            "net_return_pct": round((gross or 0.0) - ROUND_TRIP_COST_PCT, 6),
            "mfe_pct": _pct(max(path_prices), entry_ask),
            "mae_pct": _pct(min(path_prices), entry_ask),
        }
    )
    return result


def _percentile(values: list[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * quantile
    lower, upper = math.floor(index), math.ceil(index)
    if lower == upper:
        return round(ordered[lower], 6)
    weight = index - lower
    return round(ordered[lower] * (1 - weight) + ordered[upper] * weight, 6)


def _metrics(rows: list[dict[str, Any]]) -> dict[str, Any]:
    passed = [row for row in rows if row.get("label_status") == "pass"]
    returns = [_safe_float(row.get("net_return_pct")) for row in passed]
    returns = [value for value in returns if value is not None]
    maes = [_safe_float(row.get("mae_pct")) for row in passed]
    maes = [value for value in maes if value is not None]
    return {
        "sample_count": len(passed),
        "observation_date_count": len({row.get("target_date") for row in passed}),
        "source_quality_adjusted_ev_pct": (
            round(sum(returns) / len(returns), 6) if returns else None
        ),
        "downside_p10_pct": _percentile(returns, 0.10),
        "mae_p10_pct": _percentile(maes, 0.10),
        "entry_bbo_coverage_pct": (
            round(
                100.0
                * sum(1 for row in passed if row.get("entry_bbo_present"))
                / len(passed),
                6,
            )
            if passed
            else 0.0
        ),
        "diagnostic_win_rate_pct": (
            round(100.0 * sum(1 for value in returns if value > 0) / len(returns), 6)
            if returns
            else None
        ),
    }


def _latest_prior(target_date: str) -> dict[str, Any]:
    target = date.fromisoformat(target_date)
    dated: list[tuple[date, Path]] = []
    for path in COUNTERFACTUAL_DIR.glob("upper_limit_watch_counterfactual_*.json"):
        try:
            artifact_date = date.fromisoformat(path.stem.rsplit("_", 1)[-1])
        except ValueError:
            continue
        if CLEAN_BASELINE_DATE <= artifact_date < target:
            dated.append((artifact_date, path))
    return _load_json(max(dated)[1]) if dated else {}


def _prior_counterfactual_valid(payload: dict[str, Any], target_date: str) -> bool:
    if not payload:
        return True
    try:
        prior_date = date.fromisoformat(str(payload.get("target_date") or ""))
    except ValueError:
        return False
    rows = payload.get("rows") if isinstance(payload.get("rows"), list) else None
    if rows is None:
        return False
    row_ids = set()
    for row in rows:
        if not isinstance(row, dict) or not row.get("row_id"):
            return False
        try:
            row_date = date.fromisoformat(str(row.get("target_date") or ""))
        except ValueError:
            return False
        row_id = str(row.get("row_id"))
        if not CLEAN_BASELINE_DATE <= row_date <= prior_date or row_id in row_ids:
            return False
        row_ids.add(row_id)
    return bool(
        payload.get("schema_version") == 1
        and payload.get("report_type") == "upper_limit_watch_counterfactual"
        and CLEAN_BASELINE_DATE <= prior_date < date.fromisoformat(target_date)
        and payload.get("source_quality_status") == "pass"
        and payload.get("decision_authority") == "upper_limit_counterfactual_sim_only"
        and payload.get("runtime_effect") is False
        and payload.get("actual_order_submitted") is False
        and payload.get("broker_order_forbidden") is True
    )


def _rolling_rows(
    rows: Iterable[dict[str, Any]], target_date: str
) -> list[dict[str, Any]]:
    cutoff = date.fromisoformat(target_date) - timedelta(days=ROLLING_DAYS - 1)
    target = date.fromisoformat(target_date)
    selected = []
    for row in rows:
        if not isinstance(row, dict) or not row.get("row_id"):
            continue
        try:
            row_date = date.fromisoformat(str(row.get("target_date")))
        except ValueError:
            continue
        if cutoff <= row_date <= target:
            selected.append(row)
    return selected


def build_artifacts(target_date: str) -> dict[str, Path]:
    visits, source = collect_visits(target_date)
    current = [_label(visit) for visit in visits]
    prior = _latest_prior(target_date)
    prior_valid = _prior_counterfactual_valid(prior, target_date)
    prior_rows = (
        prior.get("rows") if prior_valid and isinstance(prior.get("rows"), list) else []
    )
    deduped = {
        str(row.get("row_id")): row
        for row in [*prior_rows, *current]
        if isinstance(row, dict) and row.get("row_id")
    }
    rows = sorted(
        _rolling_rows(deduped.values(), target_date),
        key=lambda row: str(row.get("row_id")),
    )
    grouped: defaultdict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        if row.get("label_status") == "pass":
            grouped[
                (
                    str(row.get("cohort")),
                    str(row.get("price_band")),
                    str(row.get("trigger_type")),
                )
            ].append(row)
    cells = []
    for (cohort, band, trigger), cell_rows in sorted(grouped.items()):
        metrics = _metrics(cell_rows)
        cells.append(
            {
                "policy_key": f"{cohort}|{band}|{trigger}",
                "cohort": cohort,
                "price_band": band,
                "trigger_type": trigger,
                **metrics,
            }
        )
    source_valid = bool(source.get("valid") and prior_valid)
    counterfactual = {
        "schema_version": 1,
        "report_type": "upper_limit_watch_counterfactual",
        "target_date": target_date,
        "generated_at": datetime.now().isoformat(),
        "status": "pass" if source_valid else "source_blocked",
        "source_quality_status": "pass" if source_valid else "blocked",
        "source_status": source,
        "rolling_window_calendar_days": ROLLING_DAYS,
        "cumulative_update": {
            "mode": "latest_prior_rolling_rows_plus_current_dedup_by_row_id",
            "prior_target_date": prior.get("target_date"),
            "prior_artifact_valid": prior_valid,
            "prior_row_count": len(prior_rows),
            "current_row_count": len(current),
            "rolling_row_count": len(rows),
        },
        **_metrics(rows),
        "policy_cells": cells,
        "rows": rows,
        **COUNTERFACTUAL_CONTRACT,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": False,
    }
    ready_cells = []
    for cell in cells:
        if (
            source_valid
            and _safe_int(cell.get("sample_count")) >= MIN_LIVE_SAMPLE
            and _safe_int(cell.get("observation_date_count")) >= MIN_LIVE_DATES
            and (_safe_float(cell.get("source_quality_adjusted_ev_pct")) or 0.0) > 0.0
            and (_safe_float(cell.get("downside_p10_pct")) or -999.0) > 0.0
            and (_safe_float(cell.get("mae_p10_pct")) or -999.0) >= MAX_MAE_P10_PCT
            and (_safe_float(cell.get("entry_bbo_coverage_pct")) or 0.0) >= 100.0
        ):
            ready_cells.append(dict(cell))
    bounded = {
        "schema_version": 1,
        "report_type": "upper_limit_watch_bounded_live_candidate",
        "target_date": target_date,
        "generated_at": datetime.now().isoformat(),
        "status": "live_auto_apply_ready" if ready_cells else "blocked",
        "ready_candidate_count": len(ready_cells),
        "candidates": ready_cells,
        "decision_authority": "upper_limit_live_auto_eligibility_candidate",
        "operator_approval_required": False,
        "preopen_consumer_implemented": True,
        "activation_mode": "latest_valid_prior_date_policy_auto_loaded",
        "sample_floor": "1_verified_ordered_path_per_cohort_price_band_trigger",
        "risk_contract": {
            "max_concurrent_positions": 1,
            "max_daily_entries": 1,
            "quantity_owner": "position_sizing_dynamic_formula",
            "scale_in_allowed": False,
            "same_day_reentry_allowed": False,
            "overnight_allowed": False,
            "entry_requires_two_ordered_trigger_ticks": True,
            "entry_requires_fresh_quote_and_bbo": True,
            "max_entry_spread_pct": MAX_ENTRY_SPREAD_PCT,
            "normal_scalping_ai_and_submit_guards_required": True,
            "upper_limit_entry_proximity_guard_required": True,
            "hard_safety_priority": "unchanged_and_unbypassable",
        },
        "forbidden_uses": (
            "direct_broker_submission_from_observer,hard_safety_bypass,"
            "stale_quote_bypass,provider_route_change,bot_restart,scale_in,reentry,overnight"
        ),
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": bool(ready_cells),
    }
    report = {
        "schema_version": 1,
        "report_type": "upper_limit_watch_report",
        "target_date": target_date,
        "generated_at": datetime.now().isoformat(),
        "status": "pass" if source_valid else "source_blocked",
        "candidate_count": source.get("candidate_source", {}).get(
            "candidate_count", len(visits)
        ),
        "visit_count": len(visits),
        "trigger_count": sum(1 for row in current if row.get("trigger_type")),
        "ordered_labeled_path_count": sum(
            1 for row in current if row.get("label_status") == "pass"
        ),
        "ordered_path_capture_rate_pct": (
            round(
                100.0
                * sum(1 for row in current if row.get("label_status") == "pass")
                / len(visits),
                6,
            )
            if visits
            else 0.0
        ),
        "bounded_live_ready_candidate_count": len(ready_cells),
        "source_status": source,
        **OBSERVATION_CONTRACT,
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    paths = {
        "report": REPORT_DIR / f"upper_limit_watch_report_{target_date}.json",
        "counterfactual": COUNTERFACTUAL_DIR
        / f"upper_limit_watch_counterfactual_{target_date}.json",
        "bounded": BOUNDED_DIR
        / f"upper_limit_watch_bounded_live_candidate_{target_date}.json",
    }
    for key, payload in (
        ("report", report),
        ("counterfactual", counterfactual),
        ("bounded", bounded),
    ):
        _atomic_write(paths[key], payload)
    return paths


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--target-date", required=True)
    args = parser.parse_args()
    target = date.fromisoformat(args.target_date)
    if target < CLEAN_BASELINE_DATE:
        raise SystemExit("target date precedes clean tuning baseline")
    paths = build_artifacts(args.target_date)
    print(
        json.dumps({key: str(path) for key, path in paths.items()}, ensure_ascii=False)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
