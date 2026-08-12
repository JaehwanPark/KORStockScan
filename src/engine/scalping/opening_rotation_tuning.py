"""Postclose diagnostics and PREOPEN profile selection for Opening Rotation.

The producer is intentionally deterministic.  It may select one predeclared
profile axis for the next PREOPEN, but it never mutates intraday state, order
guards, quantity, watch capacity, profit floor, or safety behavior.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import replace
from datetime import date, datetime, timedelta, timezone
import json
import math
import os
from pathlib import Path
from statistics import fmean
from typing import Any, Iterable

from src.engine.scalping.opening_rotation import (
    POLICY_SCHEMA_VERSION,
    RUNTIME_POLICY_DIR,
    OpeningRotationRuntimePolicy,
    is_krx_regular_scope,
    load_runtime_policy,
    runtime_policy_path,
)
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import existing_or_gzip_path, open_text_auto

KST = timezone(timedelta(hours=9))
REPORT_SCHEMA_VERSION = "opening_rotation_profile_tuning_v2"
REPORT_TYPE = "opening_rotation_profile_tuning"
REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE
CANDIDATE_DIR = RUNTIME_POLICY_DIR / "candidates"
PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"
SOURCE_QUALITY_DIR = DATA_DIR / "report" / "observation_source_quality_audit"
CLEAN_BASELINE_DATE = date(2026, 6, 5)

DAY_CHANGE_BIN_LABELS = ("lt_1_5", "1_5_to_3", "3_to_5", "5_to_8", "gt_8")
PROMOTION_STAGES = {
    "scalping_scanner_candidate_promoted",
    "scalping_scanner_fast_precheck",
    "opening_rotation_1pct_observed",
    "opening_rotation_1pct_qualified",
}
ENTRY_LOWER_VALUES = (0.5, 1.0, 1.5, 2.0)
ENTRY_UPPER_VALUES = (4.0, 5.0, 6.0, 8.0)
PULLBACK_VALUES = ((0.15, 0.8), (0.25, 1.0), (0.4, 1.2))
CONFIRMATION_VALUES = (2, 3)
HOLDING_AI_TRIGGER_VALUES = (-0.3, -0.5, -0.7)
TIMEOUT_VALUES = ((240, 480), (300, 600), (360, 720))
MIN_COMPLETE_EPISODES = 30
MIN_SYMBOLS = 10
MIN_DATES = 3
MAX_DATE_CONCENTRATION = 0.50
MAX_SYMBOL_CONCENTRATION = 0.25


def _axis_value_allowed(axis: str, value: Any) -> bool:
    if axis == "day_change_lower":
        return _safe_float(value) in ENTRY_LOWER_VALUES
    if axis == "day_change_upper":
        return _safe_float(value) in ENTRY_UPPER_VALUES
    if axis == "pullback_range":
        return tuple(value or ()) in PULLBACK_VALUES
    if axis == "confirmation_min":
        return _safe_int(value, -1) in CONFIRMATION_VALUES
    if axis == "holding_ai_trigger":
        return _safe_float(value) in HOLDING_AI_TRIGGER_VALUES
    if axis == "timeout_pair":
        return tuple(_safe_int(item, -1) for item in (value or ())) in TIMEOUT_VALUES
    return False


def _safe_float(value: Any, default: float | None = None) -> float | None:
    try:
        if value in (None, "", "-", "None", "null"):
            return default
        parsed = float(value)
    except (TypeError, ValueError):
        return default
    return parsed if math.isfinite(parsed) else default


def _safe_int(value: Any, default: int = 0) -> int:
    parsed = _safe_float(value)
    return int(parsed) if parsed is not None else default


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _parse_dt(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    return (
        parsed.replace(tzinfo=KST) if parsed.tzinfo is None else parsed.astimezone(KST)
    )


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.tmp-{os.getpid()}")
    temporary.write_text(content, encoding="utf-8")
    os.replace(temporary, path)


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    _atomic_write(path, json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def report_path(target_date: str, *, root: Path = REPORT_DIR) -> Path:
    return root / f"{REPORT_TYPE}_{target_date}.json"


def report_markdown_path(target_date: str, *, root: Path = REPORT_DIR) -> Path:
    return root / f"{REPORT_TYPE}_{target_date}.md"


def candidate_path(target_date: str, *, root: Path = CANDIDATE_DIR) -> Path:
    return root / f"opening_rotation_runtime_policy_candidate_{target_date}.json"


def _event_paths(
    target_date: str, *, events_dir: Path = PIPELINE_EVENTS_DIR
) -> Iterable[tuple[str, Path]]:
    upper = date.fromisoformat(target_date)
    seen_dates: set[str] = set()
    for raw_path in sorted(events_dir.glob("pipeline_events_*.jsonl*")):
        name = raw_path.name
        token = name.removeprefix("pipeline_events_").split(".jsonl", 1)[0]
        try:
            observed_date = date.fromisoformat(token)
        except ValueError:
            continue
        if token in seen_dates:
            continue
        if CLEAN_BASELINE_DATE <= observed_date <= upper:
            canonical = existing_or_gzip_path(
                events_dir / f"pipeline_events_{token}.jsonl"
            )
            if canonical.exists():
                seen_dates.add(token)
                yield token, canonical


def _iter_events(path: Path) -> Iterable[dict[str, Any]]:
    with open_text_auto(path) as handle:
        for raw_line in handle:
            try:
                row = json.loads(raw_line)
            except (TypeError, json.JSONDecodeError):
                continue
            if isinstance(row, dict):
                yield row


def _source_quality(target_dates: set[str], *, root: Path) -> dict[str, Any]:
    statuses: dict[str, str] = {}
    missing: list[str] = []
    blocked: list[str] = []
    for target_date in sorted(target_dates):
        path = root / f"observation_source_quality_audit_{target_date}.json"
        if not path.exists():
            statuses[target_date] = "missing"
            missing.append(target_date)
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            statuses[target_date] = "malformed"
            blocked.append(target_date)
            continue
        allowed = bool((payload.get("summary") or {}).get("tuning_input_allowed"))
        status = str(payload.get("status") or "").strip().lower()
        passed = allowed and status in {"pass", "warning"}
        statuses[target_date] = "pass" if passed else "blocked"
        if not passed:
            blocked.append(target_date)
    return {
        "status": "pass" if target_dates and not missing and not blocked else "blocked",
        "tuning_input_allowed": bool(target_dates and not missing and not blocked),
        "date_statuses": statuses,
        "missing_dates": missing,
        "blocked_dates": blocked,
    }


def _day_bin(value: float | None) -> str:
    if value is None:
        return "missing"
    if value < 1.5:
        return "lt_1_5"
    if value < 3.0:
        return "1_5_to_3"
    if value <= 5.0:
        return "3_to_5"
    if value <= 8.0:
        return "5_to_8"
    return "gt_8"


def _promotion_day_change(fields: dict[str, Any]) -> float | None:
    """Return the earliest usable promotion-time day-change observation.

    Scanner promotion rows are emitted before a fresh quote is guaranteed and
    commonly omit the value.  The fast precheck and Opening evaluator carry
    the same promotion identity and can supply it without converting a later
    outcome into an entry feature.
    """

    for key in (
        "day_change_pct",
        "fluctuation",
        "fluctuation_rate",
        "opening_rotation_upstream_day_change_pct",
    ):
        value = _safe_float(fields.get(key))
        if value is not None:
            return value
    return None


def _krx_regular_opening_promotion(
    event: dict[str, Any], fields: dict[str, Any]
) -> bool:
    event_dt = _parse_dt(event.get("emitted_at") or event.get("event_time"))
    if event_dt is None or not (
        datetime.strptime("09:00", "%H:%M").time()
        <= event_dt.time()
        <= datetime.strptime("11:40", "%H:%M").time()
    ):
        return False
    venue = (
        str(
            fields.get("effective_venue")
            or fields.get("broker_route")
            or fields.get("venue")
            or ""
        )
        .strip()
        .upper()
    )
    session = str(fields.get("market_session_bucket") or "").strip().lower()
    return is_krx_regular_scope(
        effective_venue=venue,
        market_session_bucket=session,
    )


def _episode_key(fields: dict[str, Any]) -> str:
    value = str(fields.get("opening_rotation_episode_id") or "").strip()
    return value if value not in {"", "-"} else ""


def _merge_episode(
    episode: dict[str, Any],
    *,
    event: dict[str, Any],
    fields: dict[str, Any],
    target_date: str,
) -> None:
    stage = str(event.get("stage") or "")
    event_dt = _parse_dt(event.get("emitted_at") or event.get("event_time"))
    episode.setdefault("episode_id", _episode_key(fields))
    episode.setdefault("stock_code", str(event.get("stock_code") or "")[:6])
    episode.setdefault("date", target_date)
    episode.setdefault("stages", [])
    episode["stages"].append(stage)
    margin_authorized_event = _truthy(
        fields.get("opening_rotation_margin_one_share_authorized")
    )
    if margin_authorized_event:
        episode["margin_one_share_authorized_seen"] = True
    margin_order_api = str(
        fields.get("opening_rotation_margin_order_api") or ""
    ).strip()
    if margin_authorized_event and not margin_order_api:
        episode["margin_order_api_missing_seen"] = True
    if margin_order_api and margin_order_api != "kt10000":
        episode["margin_non_kt10000_order_api_seen"] = True
    if margin_authorized_event and (
        "opening_rotation_margin_credit_order_api_used" not in fields
        or fields.get("opening_rotation_margin_credit_order_api_used")
        in (None, "", "-")
    ):
        episode["margin_credit_order_api_used_missing_seen"] = True
    if _truthy(fields.get("opening_rotation_margin_credit_order_api_used")):
        episode["margin_credit_order_api_used_seen"] = True
    if stage == "opening_rotation_redundant_submit_guard_bypassed":
        guard_name = str(
            fields.get("opening_rotation_redundant_submit_guard") or "unknown"
        ).strip()
        guard_counts = episode.setdefault("redundant_submit_guard_bypass_counts", {})
        guard_counts[guard_name] = _safe_int(guard_counts.get(guard_name), 0) + 1
        episode["redundant_submit_guard_bypass_count"] = sum(
            _safe_int(value, 0) for value in guard_counts.values()
        )
    identity_targets = {
        "promotion_id",
        "profile_id",
        "policy_hash",
        "policy_schema_version",
        "effective_venue",
        "market_session_bucket",
    }
    for source, target in (
        ("opening_rotation_episode_promotion_id", "promotion_id"),
        ("opening_rotation_profile_id", "profile_id"),
        ("opening_rotation_policy_hash", "policy_hash"),
        ("opening_rotation_policy_schema_version", "policy_schema_version"),
        ("effective_venue", "effective_venue"),
        ("market_session_bucket", "market_session_bucket"),
        ("fluctuation", "day_change_pct"),
        ("day_change_pct", "day_change_pct"),
        ("pullback_pct", "pullback_pct"),
        ("confirmation_pass_count", "confirmation_pass_count"),
        ("opening_rotation_confirmation_pass_count", "confirmation_pass_count"),
        ("opening_rotation_confirmation_count", "confirmation_pass_count"),
        ("opening_rotation_buy_submit_to_fill_ms", "buy_submit_to_fill_ms"),
        ("opening_rotation_entry_best_bid", "entry_best_bid"),
        (
            "opening_rotation_margin_one_share_authorized",
            "margin_one_share_authorized",
        ),
        (
            "opening_rotation_margin_authority_reason",
            "margin_authority_reason",
        ),
        ("opening_rotation_margin_rate", "margin_rate"),
        (
            "opening_rotation_margin_orderable_amount",
            "margin_orderable_amount",
        ),
        (
            "opening_rotation_margin_orderable_qty_cap",
            "margin_orderable_qty_cap",
        ),
        (
            "opening_rotation_margin_requested_unit_price",
            "margin_requested_unit_price",
        ),
        (
            "opening_rotation_margin_cash_guard_bypassed",
            "margin_cash_guard_bypassed",
        ),
        ("opening_rotation_margin_order_api", "margin_order_api"),
        (
            "opening_rotation_margin_credit_order_api_used",
            "margin_credit_order_api_used",
        ),
        ("opening_rotation_profit_target_price", "target_price"),
        ("buy_price", "buy_price"),
        ("fill_price", "fill_price"),
        ("profit_rate", "profit_rate"),
        ("realized_pnl_krw", "realized_pnl_krw"),
        ("mfe_pct", "mfe_pct"),
        ("mae_pct", "mae_pct"),
        ("last_exit_held_sec", "held_sec"),
        ("held_sec", "held_sec"),
        ("exit_rule", "exit_rule"),
        (
            "ratchet_counterfactual_net_profit_pct",
            "ratchet_counterfactual_net_profit_pct",
        ),
        ("holding_ai_counterfactual_delta_pct", "holding_ai_counterfactual_delta_pct"),
    ):
        value = fields.get(source)
        if value not in (None, "", "-"):
            existing = episode.get(target)
            if (
                target in identity_targets
                and existing not in (None, "", "-")
                and str(existing) != str(value)
            ):
                episode[f"{target}_conflict"] = True
                continue
            episode[target] = value
    if stage == "opening_rotation_1pct_qualified":
        episode["qualified"] = True
        episode["qualified_at"] = event_dt.isoformat() if event_dt else ""
    elif stage == "holding_started":
        episode["buy_filled"] = True
        episode["buy_filled_at"] = event_dt.isoformat() if event_dt else ""
    elif stage == "opening_rotation_profit_target_ordered":
        episode["target_ordered"] = True
        episode["target_order_no"] = str(
            fields.get("opening_rotation_profit_target_order_no")
            or fields.get("ord_no")
            or fields.get("order_no")
            or ""
        ).strip()
    elif stage == "opening_rotation_ratchet_shadow":
        episode["ratchet_shadow_observed"] = True
        episode["ratchet_shadow_price"] = fields.get(
            "counterfactual_target_price", fields.get("shadow_price")
        )
    elif stage == "opening_rotation_holding_ai_handoff":
        episode["holding_ai_called"] = True
        episode["holding_ai_action"] = fields.get("action") or fields.get(
            "opening_rotation_holding_ai_action"
        )
    elif stage == "sell_completed":
        episode["completed"] = True
        episode["completed_at"] = event_dt.isoformat() if event_dt else ""
        order_no = str(
            fields.get("sell_execution_order_no") or fields.get("order_no") or ""
        ).strip()
        target_no = str(
            fields.get("opening_rotation_profit_target_order_no")
            or episode.get("target_order_no")
            or ""
        ).strip()
        episode["target_filled"] = bool(
            order_no and target_no and order_no == target_no
        )

    if _truthy(fields.get("opening_rotation_order_ambiguity")):
        episode["order_ambiguity"] = True
    if _truthy(fields.get("opening_rotation_profit_order_protection_failed")):
        episode["target_protection_failed"] = True
    if _truthy(fields.get("opening_rotation_double_sell_detected")):
        episode["double_sell_detected"] = True


def _percentile(values: list[float], quantile: float) -> float | None:
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, math.ceil(len(ordered) * quantile) - 1))
    return round(ordered[index], 6)


def _concentration(rows: list[dict[str, Any]], key: str) -> float:
    if not rows:
        return 1.0
    counts = Counter(str(row.get(key) or "missing") for row in rows)
    return max(counts.values()) / len(rows)


def _performance(
    rows: list[dict[str, Any]], *, source_quality_pass: bool
) -> dict[str, Any]:
    profits = [
        value
        for row in rows
        if (value := _safe_float(row.get("profit_rate"))) is not None
    ]
    dates = {str(row.get("date") or "") for row in rows}
    symbols = {str(row.get("stock_code") or "") for row in rows}
    equal_ev = round(fmean(profits), 6) if profits else None
    return {
        "complete_episode_count": len(profits),
        "symbol_count": len(symbols - {""}),
        "trading_date_count": len(dates - {""}),
        "equal_weight_avg_profit_pct": equal_ev,
        "source_quality_adjusted_ev_pct": equal_ev if source_quality_pass else None,
        "diagnostic_win_rate_pct": (
            round(sum(value > 0 for value in profits) / len(profits) * 100.0, 3)
            if profits
            else None
        ),
        "p10_profit_pct": _percentile(profits, 0.10),
        "max_date_concentration": round(_concentration(rows, "date"), 6),
        "max_symbol_concentration": round(_concentration(rows, "stock_code"), 6),
    }


def _candidate_specs() -> list[dict[str, Any]]:
    specs: list[dict[str, Any]] = []
    specs.extend(
        {"axis": "day_change_lower", "value": value} for value in ENTRY_LOWER_VALUES
    )
    specs.extend(
        {"axis": "day_change_upper", "value": value} for value in ENTRY_UPPER_VALUES
    )
    specs.extend(
        {"axis": "pullback_range", "value": list(value)} for value in PULLBACK_VALUES
    )
    specs.extend(
        {"axis": "confirmation_min", "value": value} for value in CONFIRMATION_VALUES
    )
    specs.extend(
        {"axis": "holding_ai_trigger", "value": value}
        for value in HOLDING_AI_TRIGGER_VALUES
    )
    specs.extend(
        {"axis": "timeout_pair", "value": list(value)} for value in TIMEOUT_VALUES
    )
    return specs


def _apply_axis(
    policy: OpeningRotationRuntimePolicy, axis: str, value: Any
) -> OpeningRotationRuntimePolicy:
    entry = policy.entry
    exit_profile = policy.exit
    if axis == "day_change_lower":
        entry = replace(entry, min_day_change_pct=float(value))
    elif axis == "day_change_upper":
        entry = replace(entry, max_day_change_pct=float(value))
    elif axis == "pullback_range":
        entry = replace(
            entry, min_pullback_pct=float(value[0]), max_pullback_pct=float(value[1])
        )
    elif axis == "confirmation_min":
        entry = replace(entry, min_confirmation_count=int(value))
    elif axis == "holding_ai_trigger":
        exit_profile = replace(exit_profile, holding_ai_trigger_pct=float(value))
    elif axis == "timeout_pair":
        exit_profile = replace(
            exit_profile, stagnation_sec=int(value[0]), max_hold_sec=int(value[1])
        )
    else:
        raise ValueError(f"unsupported opening rotation tuning axis: {axis}")
    return replace(policy, entry=entry, exit=exit_profile)


def _candidate_rows(
    rows: list[dict[str, Any]],
    policy: OpeningRotationRuntimePolicy,
    spec: dict[str, Any],
) -> tuple[list[dict[str, Any]], str]:
    axis = str(spec["axis"])
    value = spec["value"]
    candidate = _apply_axis(policy, axis, value)
    if axis in {"holding_ai_trigger", "timeout_pair"}:
        return [], "complete_tick_path_counterfactual_unavailable"
    selected: list[dict[str, Any]] = []
    for row in rows:
        change = _safe_float(row.get("day_change_pct"))
        pullback = _safe_float(row.get("pullback_pct"))
        confirmations = _safe_int(row.get("confirmation_pass_count"), -1)
        if change is None or pullback is None:
            continue
        if not (
            candidate.entry.min_day_change_pct
            <= change
            <= candidate.entry.max_day_change_pct
        ):
            continue
        if not (
            candidate.entry.min_pullback_pct
            <= pullback
            <= candidate.entry.max_pullback_pct
        ):
            continue
        if confirmations < candidate.entry.min_confirmation_count:
            continue
        selected.append(row)
    return selected, "episode_feature_filter_replay"


def _eligibility(
    metrics: dict[str, Any], *, baseline: dict[str, Any], source_quality_pass: bool
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if not source_quality_pass:
        reasons.append("source_quality_not_pass")
    if metrics["complete_episode_count"] < MIN_COMPLETE_EPISODES:
        reasons.append("complete_episode_floor_not_met")
    if metrics["symbol_count"] < MIN_SYMBOLS:
        reasons.append("symbol_floor_not_met")
    if metrics["trading_date_count"] < MIN_DATES:
        reasons.append("trading_date_floor_not_met")
    ev = metrics.get("source_quality_adjusted_ev_pct")
    if ev is None or ev <= 0:
        reasons.append("positive_source_quality_adjusted_ev_not_met")
    if metrics["max_date_concentration"] > MAX_DATE_CONCENTRATION:
        reasons.append("date_concentration_limit_exceeded")
    if metrics["max_symbol_concentration"] > MAX_SYMBOL_CONCENTRATION:
        reasons.append("symbol_concentration_limit_exceeded")
    baseline_p10 = baseline.get("p10_profit_pct")
    candidate_p10 = metrics.get("p10_profit_pct")
    if (
        baseline_p10 is not None
        and candidate_p10 is not None
        and candidate_p10 < baseline_p10
    ):
        reasons.append("downside_worsened")
    return not reasons, reasons


def _latest_policy_before(
    target_date: str, *, root: Path = RUNTIME_POLICY_DIR, inclusive: bool = False
) -> OpeningRotationRuntimePolicy | None:
    selected: tuple[str, Path] | None = None
    for path in root.glob("opening_rotation_runtime_policy_*.json"):
        token = path.stem.removeprefix("opening_rotation_runtime_policy_")
        in_range = token <= target_date if inclusive else token < target_date
        if in_range and (selected is None or token > selected[0]):
            selected = (token, path)
    return load_runtime_policy(selected[1]) if selected else None


def _policy_by_hash(
    policy_hash: str, *, root: Path = RUNTIME_POLICY_DIR
) -> OpeningRotationRuntimePolicy | None:
    expected = str(policy_hash or "").strip()
    if not expected:
        return None
    for path in sorted(
        root.glob("opening_rotation_runtime_policy_*.json"), reverse=True
    ):
        try:
            policy = load_runtime_policy(path)
        except (OSError, ValueError, TypeError, json.JSONDecodeError):
            continue
        if policy.policy_hash == expected:
            return policy
    return None


def _candidate_source_report(
    payload: dict[str, Any], *, candidate_file: Path
) -> dict[str, Any] | None:
    raw_path = str(payload.get("source_report_path") or "").strip()
    if not raw_path:
        return None
    source_path = Path(raw_path)
    if not source_path.is_absolute():
        cwd_path = Path.cwd() / source_path
        source_path = (
            cwd_path if cwd_path.exists() else candidate_file.parent / source_path
        )
    try:
        report = json.loads(source_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, TypeError):
        return None
    return report if isinstance(report, dict) else None


def _candidate_policy_contract(
    payload: dict[str, Any],
    *,
    candidate_file: Path,
    target_date: str,
    baseline: OpeningRotationRuntimePolicy,
    runtime_root: Path,
) -> tuple[OpeningRotationRuntimePolicy | None, str]:
    """Revalidate report lineage and the one-axis mutation at PREOPEN."""

    source_date = str(payload.get("target_date") or "")
    status = str(payload.get("status") or "")
    axis = str(payload.get("selected_axis") or "")
    value = payload.get("selected_value")
    proposed_payload = payload.get("proposed_policy")
    if payload.get("schema_version") != REPORT_SCHEMA_VERSION:
        return None, "candidate_schema_mismatch"
    if status not in {"eligible", "rollback"}:
        return None, "candidate_not_eligible"
    if source_date >= target_date or source_date != baseline.target_date:
        return None, "candidate_not_from_latest_runtime_session"
    if payload.get("source_active_policy_hash") != baseline.policy_hash:
        return None, "candidate_active_policy_hash_mismatch"
    if not isinstance(proposed_payload, dict):
        return None, "candidate_proposed_policy_missing"
    if status != "rollback" and payload.get("source_quality_status") != "pass":
        return None, "candidate_source_quality_not_pass"

    report = _candidate_source_report(payload, candidate_file=candidate_file)
    if report is None:
        return None, "candidate_source_report_missing_or_malformed"
    report_selected = report.get("selected_candidate") or {}
    if (
        report.get("schema_version") != REPORT_SCHEMA_VERSION
        or report.get("target_date") != source_date
        or not report.get("allowed_runtime_apply")
        or (report.get("active_policy") or {}).get("policy_hash")
        != baseline.policy_hash
        or report_selected.get("axis") != axis
        or report_selected.get("value") != value
        or report_selected.get("proposed_policy_hash")
        != proposed_payload.get("policy_hash")
    ):
        return None, "candidate_source_report_contract_mismatch"

    temporary = candidate_file.with_name(
        f".{candidate_file.name}.proposed-{os.getpid()}.json"
    )
    temporary.write_text(json.dumps(proposed_payload), encoding="utf-8")
    try:
        proposed = load_runtime_policy(temporary)
    finally:
        temporary.unlink(missing_ok=True)

    if status == "rollback":
        expected = _policy_by_hash(baseline.previous_policy_hash, root=runtime_root)
        if (
            axis != "rollback"
            or not bool((report.get("rollback") or {}).get("triggered"))
            or expected is None
            or proposed.policy_hash != expected.policy_hash
        ):
            return None, "rollback_policy_lineage_mismatch"
        return proposed, "rollback"

    if not _axis_value_allowed(axis, value):
        return None, "candidate_axis_or_value_not_predeclared"
    expected = _apply_axis(baseline, axis, value)
    if proposed.policy_hash != expected.policy_hash:
        return None, "candidate_not_exact_single_axis_mutation"
    return proposed, axis


def build_postclose_report(
    target_date: str,
    *,
    events_dir: Path = PIPELINE_EVENTS_DIR,
    source_quality_dir: Path = SOURCE_QUALITY_DIR,
    runtime_root: Path = RUNTIME_POLICY_DIR,
) -> tuple[dict[str, Any], dict[str, Any]]:
    upper = date.fromisoformat(target_date)
    if upper < CLEAN_BASELINE_DATE:
        raise ValueError("target date precedes clean tuning baseline")
    episodes: dict[str, dict[str, Any]] = {}
    stage_counts = Counter()
    funnel_reasons = Counter()
    promotion_day_changes: dict[str, float | None] = {}
    source_dates: set[str] = set()
    relevant_dates: set[str] = set()

    for source_date, path in _event_paths(target_date, events_dir=events_dir):
        source_dates.add(source_date)
        for event in _iter_events(path):
            stage = str(event.get("stage") or "")
            fields = (
                event.get("fields") if isinstance(event.get("fields"), dict) else {}
            )
            stage_counts[stage] += 1
            if stage in PROMOTION_STAGES and _krx_regular_opening_promotion(
                event, fields
            ):
                relevant_dates.add(source_date)
                promotion_id = str(
                    fields.get("scanner_promotion_id")
                    or fields.get("opening_rotation_episode_promotion_id")
                    or ""
                ).strip()
                promotion_key = f"{source_date}:{promotion_id}"
                if promotion_id:
                    promotion_day_changes.setdefault(promotion_key, None)
                    if promotion_day_changes[promotion_key] is None:
                        observed_change = _promotion_day_change(fields)
                        if observed_change is not None:
                            promotion_day_changes[promotion_key] = observed_change
            if stage == "opening_rotation_1pct_observed":
                funnel_reasons[str(fields.get("reason") or "unknown")] += 1
            episode_id = _episode_key(fields)
            if not episode_id:
                continue
            relevant_dates.add(source_date)
            episode = episodes.setdefault(f"{source_date}:{episode_id}", {})
            _merge_episode(
                episode,
                event=event,
                fields=fields,
                target_date=source_date,
            )

    day_bins = Counter(
        _day_bin(day_change_pct) for day_change_pct in promotion_day_changes.values()
    )
    contract_eligible_episodes = [
        row
        for row in episodes.values()
        if row.get("policy_schema_version") == POLICY_SCHEMA_VERSION
        and str(row.get("policy_hash") or "") not in {"", "-"}
        and not any(
            row.get(f"{target}_conflict")
            for target in (
                "promotion_id",
                "profile_id",
                "policy_hash",
                "policy_schema_version",
                "effective_venue",
                "market_session_bucket",
            )
        )
    ]
    strict_episodes = [
        row
        for row in contract_eligible_episodes
        if is_krx_regular_scope(
            effective_venue=row.get("effective_venue"),
            market_session_bucket=row.get("market_session_bucket"),
        )
    ]
    episode_scope_excluded_count = len(contract_eligible_episodes) - len(
        strict_episodes
    )
    episode_contract_conflict_count = sum(
        any(
            row.get(f"{target}_conflict")
            for target in (
                "promotion_id",
                "profile_id",
                "policy_hash",
                "policy_schema_version",
                "effective_venue",
                "market_session_bucket",
            )
        )
        for row in episodes.values()
    )
    margin_order_contract_violations = [
        row
        for row in strict_episodes
        if bool(row.get("margin_one_share_authorized_seen"))
        and (
            bool(row.get("margin_order_api_missing_seen"))
            or bool(row.get("margin_credit_order_api_used_missing_seen"))
            or bool(row.get("margin_non_kt10000_order_api_seen"))
            or bool(row.get("margin_credit_order_api_used_seen"))
        )
    ]
    complete = [
        row
        for row in strict_episodes
        if row.get("completed") and _safe_float(row.get("profit_rate")) is not None
    ]
    source_quality = _source_quality(relevant_dates, root=source_quality_dir)
    source_quality["margin_order_contract_violation_count"] = len(
        margin_order_contract_violations
    )
    if margin_order_contract_violations:
        source_quality["status"] = "blocked"
        source_quality["tuning_input_allowed"] = False
    source_quality_pass = bool(source_quality["tuning_input_allowed"])
    active_policy = _latest_policy_before(
        target_date, root=runtime_root, inclusive=True
    ) or (OpeningRotationRuntimePolicy(target_date=target_date))
    baseline_metrics = _performance(complete, source_quality_pass=source_quality_pass)
    fill_slippage_bps = [
        round((fill_price - best_bid) / best_bid * 10000.0, 6)
        for row in strict_episodes
        if (fill_price := _safe_float(row.get("fill_price"))) is not None
        and (best_bid := _safe_float(row.get("entry_best_bid"))) is not None
        and best_bid > 0
    ]
    ratchet_rows = [row for row in complete if row.get("ratchet_shadow_observed")]
    ratchet_labeled = [
        row
        for row in ratchet_rows
        if _safe_float(row.get("ratchet_counterfactual_net_profit_pct")) is not None
    ]
    holding_ai_rows = [row for row in complete if row.get("holding_ai_called")]
    holding_ai_labeled = [
        row
        for row in holding_ai_rows
        if _safe_float(row.get("holding_ai_counterfactual_delta_pct")) is not None
    ]
    duplicate_guard_bypass_episodes = [
        row
        for row in strict_episodes
        if _safe_int(row.get("redundant_submit_guard_bypass_count"), 0) > 0
    ]
    duplicate_guard_bypass_complete = [
        row
        for row in complete
        if _safe_int(row.get("redundant_submit_guard_bypass_count"), 0) > 0
    ]
    duplicate_guard_bypass_counts = Counter()
    for row in duplicate_guard_bypass_episodes:
        duplicate_guard_bypass_counts.update(
            {
                str(guard_name): _safe_int(count, 0)
                for guard_name, count in (
                    row.get("redundant_submit_guard_bypass_counts") or {}
                ).items()
            }
        )
    completed_by_day_bin = {
        label: [
            row
            for row in complete
            if _day_bin(_safe_float(row.get("day_change_pct"))) == label
        ]
        for label in DAY_CHANGE_BIN_LABELS
    }
    day_change_bin_performance = {
        label: _performance(rows, source_quality_pass=source_quality_pass)
        for label, rows in completed_by_day_bin.items()
    }
    outside_active_complete_count = sum(
        1
        for row in complete
        if (change := _safe_float(row.get("day_change_pct"))) is not None
        and not (
            active_policy.entry.min_day_change_pct
            <= change
            <= active_policy.entry.max_day_change_pct
        )
    )

    evaluations: list[dict[str, Any]] = []
    eligible_options: list[
        tuple[float, dict[str, Any], OpeningRotationRuntimePolicy]
    ] = []
    for spec in _candidate_specs():
        rows, replay_status = _candidate_rows(complete, active_policy, spec)
        metrics = _performance(rows, source_quality_pass=source_quality_pass)
        eligible, reasons = _eligibility(
            metrics, baseline=baseline_metrics, source_quality_pass=source_quality_pass
        )
        if replay_status != "episode_feature_filter_replay":
            eligible = False
            reasons.insert(0, replay_status)
        proposed = _apply_axis(active_policy, spec["axis"], spec["value"])
        baseline_ev = baseline_metrics.get("source_quality_adjusted_ev_pct")
        candidate_ev = metrics.get("source_quality_adjusted_ev_pct")
        improvement = (
            round(candidate_ev - baseline_ev, 6)
            if candidate_ev is not None and baseline_ev is not None
            else None
        )
        if improvement is None or improvement <= 0:
            eligible = False
            if "ev_improvement_not_met" not in reasons:
                reasons.append("ev_improvement_not_met")
        row = {
            **spec,
            "replay_status": replay_status,
            "metrics": metrics,
            "baseline_ev_pct": baseline_ev,
            "ev_improvement_pct": improvement,
            "eligible": eligible,
            "blocking_reasons": reasons,
            "proposed_policy_hash": proposed.policy_hash,
        }
        evaluations.append(row)
        if eligible and improvement is not None:
            eligible_options.append((improvement, row, proposed))

    selected_row: dict[str, Any] | None = None
    proposed_policy: OpeningRotationRuntimePolicy | None = None
    if eligible_options:
        _improvement, selected_row, proposed_policy = max(
            eligible_options, key=lambda item: item[0]
        )

    active_profile_start = _parse_dt(active_policy.profile_activated_at_preopen)
    active_complete = sorted(
        (
            row
            for row in complete
            if str(row.get("profile_id") or "") == active_policy.profile_id
            and (
                active_profile_start is None
                or (
                    (completed_at := _parse_dt(row.get("completed_at"))) is not None
                    and completed_at >= active_profile_start
                )
            )
        ),
        key=lambda row: str(row.get("completed_at") or ""),
    )
    first_ten = active_complete[:10]
    rollback_failures = [
        row
        for row in first_ten
        if row.get("order_ambiguity")
        or row.get("double_sell_detected")
        or row.get("target_protection_failed")
    ]
    first_ten_ev = _performance(first_ten, source_quality_pass=source_quality_pass).get(
        "source_quality_adjusted_ev_pct"
    )
    rollback_condition_met = bool(
        len(first_ten) >= 10
        and (
            rollback_failures
            or (source_quality_pass and first_ten_ev is not None and first_ten_ev <= 0)
        )
    )
    rollback_policy = (
        _policy_by_hash(active_policy.previous_policy_hash, root=runtime_root)
        if rollback_condition_met
        else None
    )
    rollback_triggered = bool(rollback_condition_met and rollback_policy is not None)
    if rollback_triggered:
        selected_row = {
            "axis": "rollback",
            "value": rollback_policy.profile_id,
            "eligible": True,
            "blocking_reasons": [],
            "proposed_policy_hash": rollback_policy.policy_hash,
        }
        proposed_policy = rollback_policy

    report: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "target_date": target_date,
        "generated_at": datetime.now(KST).isoformat(),
        "status": "pass" if source_quality_pass else "source_quality_blocked",
        "decision": (
            "rollback_candidate_selected"
            if rollback_triggered
            else (
                "single_axis_candidate_selected"
                if proposed_policy is not None
                else "diagnostic_only_no_preopen_change"
            )
        ),
        "metric_role": "rolling_opening_rotation_profile_tuning",
        "decision_authority": "bounded_next_preopen_single_axis_profile_only",
        "window_policy": "clean_baseline_promotion_and_complete_episode_units",
        "sample_floor": "30_complete_episodes_10_symbols_3_trading_dates",
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "observation_source_quality_audit_tuning_input_allowed",
        "runtime_effect": False,
        "allowed_runtime_apply": bool(proposed_policy is not None),
        "forbidden_uses": [
            "intraday_mutation",
            "quantity_change",
            "watch_slot_change",
            "scale_in_enablement",
            "net_profit_floor_change",
            "buy_window_change",
            "submit_guard_bypass",
            "hard_safety_change",
            "provider_or_bot_change",
        ],
        "source": {
            "clean_baseline_date": CLEAN_BASELINE_DATE.isoformat(),
            "source_dates": sorted(relevant_dates),
            "scanned_pipeline_dates": sorted(source_dates),
            "episode_contract": "episode_id_plus_policy_schema_and_hash_required",
        },
        "source_quality": source_quality,
        "active_policy": active_policy.as_artifact(),
        "funnel": {
            "unique_scanner_promotion_count": len(promotion_day_changes),
            "strict_episode_count": len(strict_episodes),
            "non_krx_or_unknown_episode_scope_excluded_count": (
                episode_scope_excluded_count
            ),
            "episode_contract_conflict_count": episode_contract_conflict_count,
            "complete_episode_count": len(complete),
            "qualified_episode_count": sum(
                bool(row.get("qualified")) for row in strict_episodes
            ),
            "buy_filled_episode_count": sum(
                bool(row.get("buy_filled")) for row in strict_episodes
            ),
            "margin_authorized_episode_count": sum(
                bool(row.get("margin_one_share_authorized_seen"))
                for row in strict_episodes
            ),
            "margin_cash_guard_bypassed_episode_count": sum(
                _truthy(row.get("margin_cash_guard_bypassed"))
                for row in strict_episodes
            ),
            "margin_applied_rate_counts": dict(
                Counter(
                    str(row.get("margin_rate"))
                    for row in strict_episodes
                    if row.get("margin_rate") not in (None, "", "-", 0, "0")
                ).most_common()
            ),
            "margin_order_api_counts": dict(
                Counter(
                    str(row.get("margin_order_api") or "missing")
                    for row in strict_episodes
                    if _truthy(row.get("margin_one_share_authorized"))
                ).most_common()
            ),
            "margin_credit_order_api_used_episode_count": sum(
                bool(row.get("margin_credit_order_api_used_seen"))
                for row in strict_episodes
            ),
            "margin_order_contract_violation_count": len(
                margin_order_contract_violations
            ),
            "best_bid_fill_within_10s_count": sum(
                (_safe_float(row.get("buy_submit_to_fill_ms"), 10001.0) or 10001.0)
                <= 10000.0
                for row in strict_episodes
                if row.get("buy_filled")
            ),
            "target_ordered_count": sum(
                bool(row.get("target_ordered")) for row in strict_episodes
            ),
            "target_filled_count": sum(
                bool(row.get("target_filled")) for row in complete
            ),
            "ratchet_shadow_count": sum(
                bool(row.get("ratchet_shadow_observed")) for row in strict_episodes
            ),
            "holding_ai_called_count": sum(
                bool(row.get("holding_ai_called")) for row in strict_episodes
            ),
            "timeout_300_count": sum(
                row.get("exit_rule") == "opening_rotation_stagnation_exit"
                for row in complete
            ),
            "timeout_600_count": sum(
                row.get("exit_rule") == "opening_rotation_max_hold_exit"
                for row in complete
            ),
            "order_ambiguity_count": sum(
                bool(row.get("order_ambiguity")) for row in strict_episodes
            ),
            "double_sell_count": sum(
                bool(row.get("double_sell_detected")) for row in strict_episodes
            ),
            "target_protection_failure_count": sum(
                bool(row.get("target_protection_failed")) for row in strict_episodes
            ),
            "actual_fill_slippage_sample_count": len(fill_slippage_bps),
            "actual_fill_slippage_avg_bps": (
                round(fmean(fill_slippage_bps), 6) if fill_slippage_bps else None
            ),
            "wait_drop_reason_counts": dict(funnel_reasons.most_common()),
            "duplicate_submit_guard_bypass_episode_count": len(
                duplicate_guard_bypass_episodes
            ),
            "duplicate_submit_guard_bypass_filled_episode_count": sum(
                bool(row.get("buy_filled")) for row in duplicate_guard_bypass_episodes
            ),
            "duplicate_submit_guard_bypass_complete_episode_count": len(
                duplicate_guard_bypass_complete
            ),
            "duplicate_submit_guard_bypass_counts": dict(
                duplicate_guard_bypass_counts.most_common()
            ),
        },
        "downstream_guard_overlap": {
            "status": (
                "duplicate_alpha_guard_bypass_outcomes_available"
                if duplicate_guard_bypass_complete
                else "waiting_for_complete_duplicate_guard_bypass_episode"
            ),
            "entry_owner": "opening_rotation_mechanical_entry_owner",
            "bypassed_guard_class": "generic_alpha_or_legacy_context_duplicate",
            "preserved_guard_class": (
                "stale_conflict_price_venue_account_order_quantity_cooldown_margin_"
                "greenfield_broker_and_hard_safety"
            ),
            "performance": _performance(
                duplicate_guard_bypass_complete,
                source_quality_pass=source_quality_pass,
            ),
            "runtime_effect": False,
            "decision_authority": "postclose_attribution_only",
            "forbidden_uses": (
                "additional_guard_bypass|hard_safety_relaxation|intraday_mutation|"
                "scale_in|quantity_or_cap_change|provider_or_bot_change"
            ),
        },
        "day_change_distribution": {
            **{label: int(day_bins.get(label, 0)) for label in DAY_CHANGE_BIN_LABELS},
            "missing": int(day_bins.get("missing", 0)),
        },
        "day_change_range_validation": {
            "status": (
                "outside_active_range_outcomes_available_for_review"
                if outside_active_complete_count > 0
                else "blocked_outside_active_range_complete_outcomes_missing"
            ),
            "scanner_promotion_scope": "all_regular_scanner_lineages",
            "active_range_pct": [
                active_policy.entry.min_day_change_pct,
                active_policy.entry.max_day_change_pct,
            ],
            "initial_profile_outside_bins": ["lt_1_5", "5_to_8", "gt_8"],
            "complete_episode_performance_by_bin": day_change_bin_performance,
            "outside_active_complete_episode_count": outside_active_complete_count,
            "selection_bias_warning": (
                "complete outcomes are actual Opening episodes only; promotion "
                "counts outside the active range are diagnostic until an exact "
                "counterfactual price path supplies entry, fill, and exit labels"
            ),
            "outside_active_range_auto_promotion_allowed": False,
        },
        "performance": {
            **baseline_metrics,
            "mae_p10_pct": _percentile(
                [
                    value
                    for row in complete
                    if (value := _safe_float(row.get("mae_pct"))) is not None
                ],
                0.10,
            ),
            "mfe_median_pct": _percentile(
                [
                    value
                    for row in complete
                    if (value := _safe_float(row.get("mfe_pct"))) is not None
                ],
                0.50,
            ),
            "realized_pnl_krw": sum(
                _safe_int(row.get("realized_pnl_krw")) for row in complete
            ),
        },
        "profile_evaluations": evaluations,
        "ratchet_counterfactual": {
            "runtime_state": "shadow_only_no_order_mutation",
            "shadow_complete_episode_count": len(ratchet_rows),
            "outcome_labeled_episode_count": len(ratchet_labeled),
            "promotion_status": "blocked_until_outcome_labels_and_sample_floor",
            "promotion_floor": {
                "complete_episodes": MIN_COMPLETE_EPISODES,
                "symbols": MIN_SYMBOLS,
                "trading_dates": MIN_DATES,
            },
            "required_non_degradation": [
                "initial_target_fill_rate",
                "timeout_loss_rate",
            ],
            "actual_order_mutation_allowed": False,
        },
        "holding_ai_attribution": {
            "complete_episode_count": len(holding_ai_rows),
            "save_harm_labeled_episode_count": len(holding_ai_labeled),
            "save_count": sum(
                (
                    _safe_float(row.get("holding_ai_counterfactual_delta_pct"), 0.0)
                    or 0.0
                )
                > 0
                for row in holding_ai_labeled
            ),
            "harm_count": sum(
                (
                    _safe_float(row.get("holding_ai_counterfactual_delta_pct"), 0.0)
                    or 0.0
                )
                < 0
                for row in holding_ai_labeled
            ),
            "status": (
                "diagnostic_labels_available"
                if holding_ai_labeled
                else "counterfactual_labels_missing"
            ),
        },
        "selected_candidate": selected_row,
        "rollback": {
            "active_policy_hash": active_policy.policy_hash,
            "active_profile_id": active_policy.profile_id,
            "active_profile_activated_at_preopen": (
                active_policy.profile_activated_at_preopen or None
            ),
            "active_policy_complete_episode_count": len(active_complete),
            "evaluated_episode_count": len(first_ten),
            "first_ten_source_quality_adjusted_ev_pct": first_ten_ev,
            "safety_failure_count": len(rollback_failures),
            "condition_met": rollback_condition_met,
            "triggered": rollback_triggered,
            "reason": (
                "first_ten_ev_nonpositive_or_order_safety_failure"
                if rollback_triggered
                else (
                    "previous_policy_artifact_not_found"
                    if rollback_condition_met
                    else "not_triggered"
                )
            ),
            "rollback_policy_hash": (
                rollback_policy.policy_hash if rollback_policy is not None else None
            ),
        },
    }
    candidate = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "artifact_type": "opening_rotation_runtime_policy_candidate",
        "target_date": target_date,
        "generated_at": report["generated_at"],
        "status": (
            "rollback"
            if rollback_triggered
            else "eligible" if proposed_policy is not None else "no_change"
        ),
        "selected_axis": selected_row.get("axis") if selected_row else None,
        "selected_value": selected_row.get("value") if selected_row else None,
        "source_report_path": str(report_path(target_date)),
        "source_quality_status": source_quality["status"],
        "source_report_schema_version": REPORT_SCHEMA_VERSION,
        "source_active_policy_hash": active_policy.policy_hash,
        "proposed_policy": proposed_policy.as_artifact() if proposed_policy else None,
        "rollback_triggered": rollback_triggered,
        "runtime_effect": False,
        "apply_timing": "next_preopen_only",
    }
    return report, candidate


def _render_markdown(report: dict[str, Any]) -> str:
    funnel = report["funnel"]
    performance = report["performance"]
    selected = report.get("selected_candidate") or {}
    return "\n".join(
        [
            f"# Opening Rotation profile tuning — {report['target_date']}",
            "",
            f"- Decision: `{report['decision']}`",
            f"- Source quality: `{report['source_quality']['status']}`",
            f"- Promotions / strict episodes / complete: {funnel['unique_scanner_promotion_count']} / {funnel['strict_episode_count']} / {funnel['complete_episode_count']}",
            f"- Margin authorized / cash-guard bypassed episodes: {funnel['margin_authorized_episode_count']} / {funnel['margin_cash_guard_bypassed_episode_count']}",
            f"- Duplicate submit-alpha bypassed / filled / complete episodes: {funnel['duplicate_submit_guard_bypass_episode_count']} / {funnel['duplicate_submit_guard_bypass_filled_episode_count']} / {funnel['duplicate_submit_guard_bypass_complete_episode_count']}",
            f"- Source-quality-adjusted EV: `{performance['source_quality_adjusted_ev_pct']}`",
            f"- Selected axis: `{selected.get('axis', '-')}` → `{selected.get('value', '-')}`",
            f"- Rollback: `{report['rollback']['triggered']}`",
            "",
            "Daily output is diagnostic. Only an eligible rolling/cumulative candidate may be materialized at the next PREOPEN.",
            "",
        ]
    )


def write_postclose(
    target_date: str,
    *,
    report_root: Path = REPORT_DIR,
    candidate_root: Path = CANDIDATE_DIR,
    **kwargs: Any,
) -> tuple[Path, Path, Path]:
    report, candidate = build_postclose_report(target_date, **kwargs)
    json_path = report_path(target_date, root=report_root)
    md_path = report_markdown_path(target_date, root=report_root)
    output_candidate_path = candidate_path(target_date, root=candidate_root)
    candidate["source_report_path"] = str(json_path)
    _atomic_write_json(json_path, report)
    _atomic_write(md_path, _render_markdown(report))
    _atomic_write_json(output_candidate_path, candidate)
    return json_path, md_path, output_candidate_path


def _latest_candidate_before(target_date: str, *, root: Path) -> Path | None:
    selected: tuple[str, Path] | None = None
    for path in root.glob("opening_rotation_runtime_policy_candidate_*.json"):
        token = path.stem.removeprefix("opening_rotation_runtime_policy_candidate_")
        if token < target_date and (selected is None or token > selected[0]):
            selected = (token, path)
    return selected[1] if selected else None


def apply_preopen(
    target_date: str,
    *,
    runtime_root: Path = RUNTIME_POLICY_DIR,
    candidate_root: Path = CANDIDATE_DIR,
    now_dt: datetime | None = None,
) -> tuple[OpeningRotationRuntimePolicy, Path]:
    observed_at = (now_dt or datetime.now(KST)).astimezone(KST)
    if observed_at.date().isoformat() != target_date:
        raise ValueError("PREOPEN target date must match the current KST date")
    if observed_at.time() >= datetime.strptime("09:00", "%H:%M").time():
        raise ValueError("Opening Rotation policy may only be materialized PREOPEN")

    previous = _latest_policy_before(target_date, root=runtime_root)
    baseline = previous or OpeningRotationRuntimePolicy(target_date=target_date)
    candidate_file = _latest_candidate_before(target_date, root=candidate_root)
    selected_axis = "carry_forward" if previous else "baseline"
    source_report_path = baseline.source_report_path or "runtime_default"
    next_policy = baseline
    candidate_applied = False
    if candidate_file is not None:
        payload = json.loads(candidate_file.read_text(encoding="utf-8"))
        proposed, validated_axis = _candidate_policy_contract(
            payload,
            candidate_file=candidate_file,
            target_date=target_date,
            baseline=baseline,
            runtime_root=runtime_root,
        )
        if proposed is not None:
            next_policy = proposed
            selected_axis = validated_axis
            source_report_path = str(payload.get("source_report_path") or "")
            candidate_applied = True

    profile_id = baseline.profile_id
    profile_activated_at_preopen = (
        baseline.profile_activated_at_preopen or observed_at.isoformat()
    )
    if candidate_applied:
        if selected_axis == "rollback":
            profile_id = next_policy.profile_id
        else:
            profile_id = (
                f"opening_rotation_{target_date.replace('-', '')}_{selected_axis}"
            )
        profile_activated_at_preopen = observed_at.isoformat()

    rollback_origin_hash = baseline.previous_policy_hash
    if candidate_applied:
        rollback_origin_hash = (
            next_policy.previous_policy_hash
            if selected_axis == "rollback"
            else baseline.policy_hash
        )

    applied = replace(
        next_policy,
        target_date=target_date,
        applied_at_preopen=observed_at.isoformat(),
        profile_activated_at_preopen=profile_activated_at_preopen,
        source_quality_status=(
            "PASS" if candidate_applied else baseline.source_quality_status
        ),
        source_report_path=source_report_path,
        selected_axis=selected_axis,
        # Preserve the profile's actual pre-change origin across daily
        # carry-forward artifacts.  Pointing to yesterday's identical carried
        # profile would make the first-ten rollback a no-op.
        previous_policy_hash=rollback_origin_hash,
        profile_id=profile_id,
    )
    output_path = runtime_policy_path(target_date, root=runtime_root)
    _atomic_write_json(output_path, applied.as_artifact())
    # Re-open the artifact through the same strict runtime loader.
    verified = load_runtime_policy(output_path)
    return verified, output_path


def verify_artifacts(
    target_date: str,
    *,
    report_root: Path = REPORT_DIR,
    candidate_root: Path = CANDIDATE_DIR,
    runtime_root: Path = RUNTIME_POLICY_DIR,
    phase: str = "all",
) -> dict[str, Any]:
    checked: list[str] = []
    errors: list[str] = []
    if phase in {"all", "postclose"}:
        for path in (
            report_path(target_date, root=report_root),
            report_markdown_path(target_date, root=report_root),
            candidate_path(target_date, root=candidate_root),
        ):
            checked.append(str(path))
            if not path.exists() or path.stat().st_size <= 0:
                errors.append(f"missing_or_empty:{path}")
        json_path = report_path(target_date, root=report_root)
        if json_path.exists():
            payload = json.loads(json_path.read_text(encoding="utf-8"))
            if payload.get("schema_version") != REPORT_SCHEMA_VERSION:
                errors.append("report_schema_mismatch")
            if payload.get("target_date") != target_date:
                errors.append("report_target_date_mismatch")
        candidate_json_path = candidate_path(target_date, root=candidate_root)
        if candidate_json_path.exists() and json_path.exists():
            candidate_payload = json.loads(
                candidate_json_path.read_text(encoding="utf-8")
            )
            candidate_report = json.loads(json_path.read_text(encoding="utf-8"))
            if candidate_payload.get("schema_version") != REPORT_SCHEMA_VERSION:
                errors.append("candidate_schema_mismatch")
            if candidate_payload.get("target_date") != target_date:
                errors.append("candidate_target_date_mismatch")
            if candidate_payload.get("source_report_path") != str(json_path):
                errors.append("candidate_source_report_path_mismatch")
            selected = candidate_report.get("selected_candidate") or {}
            proposed = candidate_payload.get("proposed_policy") or {}
            if candidate_payload.get("status") in {"eligible", "rollback"} and (
                selected.get("axis") != candidate_payload.get("selected_axis")
                or selected.get("value") != candidate_payload.get("selected_value")
                or selected.get("proposed_policy_hash") != proposed.get("policy_hash")
            ):
                errors.append("candidate_report_policy_lineage_mismatch")
    if phase in {"all", "preopen"}:
        path = runtime_policy_path(target_date, root=runtime_root)
        checked.append(str(path))
        if not path.exists():
            errors.append(f"missing:{path}")
        else:
            try:
                policy = load_runtime_policy(path)
            except (OSError, ValueError, TypeError) as exc:
                errors.append(f"runtime_policy_invalid:{exc}")
            else:
                if policy.target_date != target_date:
                    errors.append("runtime_policy_target_date_mismatch")
    return {
        "status": "pass" if not errors else "fail",
        "checked": checked,
        "errors": errors,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--mode", choices=("postclose", "preopen", "verify"), required=True
    )
    parser.add_argument("--target-date", required=True)
    parser.add_argument(
        "--phase", choices=("all", "postclose", "preopen"), default="all"
    )
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()

    if args.mode == "postclose":
        if args.write:
            paths = write_postclose(args.target_date)
            result: dict[str, Any] = {
                "status": "written",
                "paths": [str(path) for path in paths],
            }
        else:
            report, candidate = build_postclose_report(args.target_date)
            result = {"report": report, "candidate": candidate}
    elif args.mode == "preopen":
        if not args.write:
            raise SystemExit("--write is required for PREOPEN materialization")
        policy, path = apply_preopen(args.target_date)
        result = {
            "status": "written",
            "path": str(path),
            "policy_hash": policy.policy_hash,
        }
    else:
        result = verify_artifacts(args.target_date, phase=args.phase)
        if result["status"] != "pass":
            print(json.dumps(result, ensure_ascii=False))
            return 1
    if args.print_summary or args.mode != "postclose" or not args.write:
        print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
