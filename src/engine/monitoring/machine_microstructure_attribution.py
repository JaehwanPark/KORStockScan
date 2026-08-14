"""Join source-only micro-reversion observations to widget/episode machines.

The report is deliberately diagnostic.  It discovers the current machine
universe from target-date postclose artifacts, so a newly added symbol is
represented even when the micro producer did not observe it.  Missing micro
data is never imputed and never blocks the existing owner tuning path.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import tempfile
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo

from src.engine.scalping.micro_reversion.p2_replay import (
    DEFAULT_SOURCE_EXCLUSION_MANIFEST,
    load_source_exclusion_manifest,
)
from src.engine.scalping.micro_reversion.collection_targets import (
    build_collection_targets,
    write_collection_targets,
)
from src.trading.low_price_two_leg.profiles import PROFILES
from src.utils.constants import DATA_DIR

KST_SUFFIX = "+09:00"
KST = ZoneInfo("Asia/Seoul")
REPORT_TYPE = "machine_microstructure_attribution"
REPORT_SCHEMA = "machine_microstructure_attribution_v1"
OUTPUT_DIR = DATA_DIR / "report" / REPORT_TYPE
OBSERVATION_ROOT = DATA_DIR / "observations" / "scalp_micro_reversion_forward"
PRE_WINDOW_SEC = 30
POST_WINDOW_SEC = 180
CLEAN_BASELINE_DATE = date(2026, 6, 5)

METRIC_CONTRACT = {
    "metric_role": "machine_entry_microstructure_diagnostic_context",
    "decision_authority": "postclose_diagnostic_only",
    "window_policy": "target_date_anchor_minus_30s_through_plus_180s",
    "sample_floor": {
        "per_anchor_eligible_0b_rows": 1,
        "live_or_policy_promotion": "not_permitted",
    },
    "primary_decision_metric": "source_quality_and_anchor_path_coverage",
    "source_quality_gate": [
        "exact_target_date_owner_inventory",
        "exact_target_date_micro_partition",
        "target_date_on_or_after_clean_tuning_baseline",
        "path_consumer_eligible_true_when_present",
        "source_only_authority_flags",
        "valid_symbol_timestamp_and_trade_price",
    ],
    "forbidden_uses": [
        "zero_or_flat_imputation_for_missing_micro_data",
        "replacement_of_owner_policy_ev",
        "real_execution_quality_claim",
        "threshold_or_policy_selection",
        "broker_order_submission",
        "provider_or_bot_or_cap_mutation",
    ],
}
POLICY_CHANGE_READINESS_CONTRACT = {
    "current_state": "diagnostic_collection_only",
    "policy_change_allowed": False,
    "daily_report_can_change_policy": False,
    "required_evidence": {
        "minimum_observed_trading_days_per_owner_symbol_session": 5,
        "minimum_matched_entry_anchors_per_owner_symbol_session": 20,
        "minimum_bbo_complete_rate_pct": 95.0,
        "minimum_depth_window_coverage_pct": 90.0,
        "invalid_contract_row_count": 0,
        "comparison": (
            "paired_same_anchor_current_policy_vs_one_micro_conditioned_axis"
        ),
        "primary_metric": "source_quality_adjusted_ev_pct",
        "cost_policy": "fees_taxes_and_slippage_included",
        "rolling_windows_trading_days": [5, 10, 20],
        "required_absolute_ev_uplift": "greater_than_zero_in_all_windows",
        "minimum_relative_primary_ev_uplift_pct": 1.0,
        "required_net_profit": "positive_in_primary_20d_window",
        "downside_guard": "paired_p10_not_worse_and_held_unresolved_not_increased",
    },
    "promotion_boundary": {
        "candidate_timing": "next_session_preopen_exact_date_only",
        "mutation_limit": "one_existing_owner_stage_axis",
        "required_guards": [
            "source_quality_pass",
            "same_stage_owner_conflict_free",
            "before_after_runtime_provenance",
            "rollback_guard",
            "post_apply_attribution",
        ],
        "first_runtime_linkage": (
            "requires_new_runtime_family_mapping_and_explicit_operator_approval"
        ),
        "after_first_approval": (
            "bounded_candidates_may_follow_the_existing_postclose_to_preopen_chain"
        ),
    },
}
PROMOTION_CANDIDATE_INTAKE_CONTRACT = {
    "schema": "machine_microstructure_policy_promotion_candidate_v1",
    "producer_boundary": (
        "rolling_paired_policy_research_after_all_policy_change_readiness_gates"
    ),
    "consumer": ("src.engine.automation.machine_microstructure_policy_approval"),
    "initial_state": "DESIGN_REQUIRED_or_REVIEW_READY",
    "required_runtime_design": [
        "one_registered_bounded_runtime_family",
        "one_same_stage_axis",
        "bounded_before_after_values",
        "rollback_guard",
        "preopen_consumer",
        "post_apply_attribution",
    ],
    "first_operator_approval_required": True,
    "daily_report_runtime_effect": False,
}


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _read_target_json(
    path: Path,
    target_date: str,
    *,
    date_fields: tuple[str, ...] = ("target_date",),
) -> dict[str, Any] | None:
    payload = _read_json(path)
    if payload is None or not any(
        payload.get(field) == target_date for field in date_fields
    ):
        return None
    return payload


def _parse_ts(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        try:
            parsed = datetime.fromisoformat(f"{text}{KST_SUFFIX}")
        except ValueError:
            return None
    return parsed


def _finite_float(value: Any) -> float | None:
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _source(path: Path, payload: dict[str, Any] | None) -> dict[str, Any]:
    return {
        "path": str(path),
        "status": "loaded" if payload is not None else "missing_or_invalid",
        "schema": (payload or {}).get("schema"),
    }


def _widget_inventory(
    target_date: str, report_root: Path
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    calibration_path = (
        report_root
        / "widget_auto_trade_policy_calibration"
        / f"widget_auto_trade_policy_calibration_{target_date}.json"
    )
    research_path = (
        report_root
        / "widget_symbol_signal_policy_research"
        / f"widget_symbol_signal_policy_research_{target_date}.json"
    )
    expansion_path = (
        report_root
        / "widget_collector_expansion_recommendation"
        / f"widget_collector_expansion_recommendation_{target_date}.json"
    )
    calibration = _read_target_json(calibration_path, target_date)
    research = _read_target_json(
        research_path, target_date, date_fields=("target_date", "end_date")
    )
    expansion = _read_target_json(expansion_path, target_date)
    symbols: dict[str, dict[str, Any]] = {}
    anchors: list[dict[str, Any]] = []

    report_symbols = (calibration or {}).get("symbols") or {}
    if isinstance(report_symbols, dict):
        for symbol, payload in report_symbols.items():
            if not isinstance(payload, dict):
                continue
            row = symbols.setdefault(
                str(symbol),
                {
                    "symbol": str(symbol),
                    "name": payload.get("name"),
                    "scopes": [],
                    "expected_venues": [],
                    "owner_inventory_source": "target_date_postclose_report",
                },
            )
            row["owner_inventory_source"] = "target_date_postclose_report"
            if "active_widget_owner" not in row["scopes"]:
                row["scopes"].append("active_widget_owner")
            sessions = payload.get("sessions") or {}
            if not isinstance(sessions, dict):
                continue
            for session, session_payload in sessions.items():
                if not isinstance(session_payload, dict):
                    continue
                venue = str(session).split("_", 1)[0].upper()
                if (
                    venue in {"KRX", "NXT", "SOR"}
                    and venue not in row["expected_venues"]
                ):
                    row["expected_venues"].append(venue)
                trades = session_payload.get("selected_trades") or []
                if not isinstance(trades, list):
                    continue
                for index, trade in enumerate(trades, start=1):
                    if (
                        not isinstance(trade, dict)
                        or trade.get("trade_date") != target_date
                    ):
                        continue
                    entry_at = _parse_ts(trade.get("entry_at"))
                    if entry_at is None:
                        continue
                    anchors.append(
                        {
                            "anchor_id": f"widget:{symbol}:{session}:{index}:{entry_at.isoformat()}",
                            "owner": "widget",
                            "scope_id": f"{symbol}:{session}",
                            "symbol": str(symbol),
                            "session": str(session),
                            "expected_venues": [str(session).split("_", 1)[0]],
                            "anchor_at": entry_at.isoformat(),
                            "anchor_price": _finite_float(
                                trade.get("entry_price") or trade.get("average_price")
                            ),
                            "anchor_role": "counterfactual_calibration_entry",
                            "actual_order_submitted": False,
                        }
                    )

    research_symbols = (research or {}).get("symbols") or {}
    if isinstance(research_symbols, dict):
        for symbol, payload in research_symbols.items():
            symbol = str(symbol)
            row = symbols.setdefault(
                symbol,
                {
                    "symbol": symbol,
                    "name": (
                        (payload or {}).get("name")
                        if isinstance(payload, dict)
                        else None
                    ),
                    "scopes": [],
                    "expected_venues": ["SOR"],
                    "owner_inventory_source": "target_date_postclose_report",
                },
            )
            row["owner_inventory_source"] = "target_date_postclose_report"
            if "prospective_widget_research" not in row["scopes"]:
                row["scopes"].append("prospective_widget_research")

    recommendations = (expansion or {}).get("recommendations") or []
    if isinstance(recommendations, list):
        for recommendation in recommendations:
            if not isinstance(recommendation, dict):
                continue
            symbol = str(
                recommendation.get("stock_code") or recommendation.get("symbol") or ""
            )
            if not symbol:
                continue
            row = symbols.setdefault(
                symbol,
                {
                    "symbol": symbol,
                    "name": recommendation.get("stock_name"),
                    "scopes": [],
                    "expected_venues": ["SOR"],
                    "owner_inventory_source": "target_date_postclose_report",
                },
            )
            row["owner_inventory_source"] = "target_date_postclose_report"
            if "prospective_widget_collector_expansion" not in row["scopes"]:
                row["scopes"].append("prospective_widget_collector_expansion")

    for row in symbols.values():
        if not row.get("expected_venues"):
            row["expected_venues"] = ["SOR"]
        else:
            row["expected_venues"] = sorted(set(row["expected_venues"]))

    return (
        symbols,
        anchors,
        {
            "calibration": _source(calibration_path, calibration),
            "symbol_research": _source(research_path, research),
            "collector_expansion_recommendation": _source(expansion_path, expansion),
        },
    )


def _signal_anchor(row: dict[str, Any]) -> tuple[datetime | None, float | None]:
    features = row.get("signal_features") or {}
    signal = features.get("signal_bar") or {}
    if not isinstance(signal, dict):
        return None, None
    timestamp = _parse_ts(signal.get("timestamp") or signal.get("at"))
    price = _finite_float(signal.get("close_price") or signal.get("close"))
    return timestamp, price


def _has_positive_fill(legs: Any) -> bool:
    if not isinstance(legs, list):
        return False
    for leg in legs:
        if not isinstance(leg, dict):
            continue
        try:
            if int(leg.get("buy_filled_qty") or 0) > 0:
                return True
        except (TypeError, ValueError):
            continue
    return False


def _episode_inventory(
    target_date: str, report_root: Path
) -> tuple[dict[str, dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    tuning_path = (
        report_root
        / "low_price_two_leg_tuning"
        / f"low_price_two_leg_tuning_{target_date}.json"
    )
    expansion_path = (
        report_root
        / "low_price_two_leg_expanded_candidate_research"
        / f"low_price_two_leg_expanded_candidate_research_{target_date}.json"
    )
    tuning = _read_target_json(tuning_path, target_date)
    expansion = _read_target_json(expansion_path, target_date)
    profiles: dict[str, dict[str, Any]] = {}
    anchors: list[dict[str, Any]] = []

    for profile_id, spec in PROFILES.items():
        profiles[profile_id] = {
            "profile_id": profile_id,
            "symbol": spec.symbol,
            "session": spec.session,
            "scope": "active_episode_owner",
            "expected_venues": ["SOR"],
            "owner_inventory_source": "runtime_registry_fallback",
        }

    daily_profiles = ((tuning or {}).get("daily") or {}).get("profiles") or {}
    if isinstance(daily_profiles, dict):
        for profile_id, payload in daily_profiles.items():
            if not isinstance(payload, dict):
                continue
            profile_id = str(profile_id)
            row = profiles.setdefault(profile_id, {})
            row.update(
                {
                    "profile_id": profile_id,
                    "symbol": str(payload.get("symbol") or row.get("symbol") or ""),
                    "session": payload.get("session") or row.get("session"),
                    "scope": "active_episode_owner",
                    "expected_venues": ["SOR"],
                    "owner_inventory_source": "target_date_postclose_report",
                    "owner_source_quality": payload.get("source_quality"),
                    "attempted": payload.get("attempted") is True,
                }
            )
            anchor_at, anchor_price = _signal_anchor(payload)
            if anchor_at is not None:
                anchors.append(
                    {
                        "anchor_id": f"episode:{profile_id}:{anchor_at.isoformat()}",
                        "owner": "episode",
                        "scope_id": profile_id,
                        "symbol": row["symbol"],
                        "session": row["session"],
                        "expected_venues": ["SOR"],
                        "anchor_at": anchor_at.isoformat(),
                        "anchor_price": anchor_price,
                        "anchor_role": "episode_signal_bar",
                        "actual_order_submitted": _has_positive_fill(
                            payload.get("legs")
                        ),
                    }
                )

    expanded_profiles = (expansion or {}).get("profiles") or {}
    if isinstance(expanded_profiles, dict):
        for profile_id, payload in expanded_profiles.items():
            if not isinstance(payload, dict):
                continue
            profile_id = str(payload.get("profile_id") or profile_id)
            if profile_id in profiles:
                continue
            profiles[profile_id] = {
                "profile_id": profile_id,
                "symbol": str(payload.get("symbol") or ""),
                "name": payload.get("name"),
                "session": payload.get("session"),
                "scope": "prospective_episode_research",
                "expected_venues": ["SOR"],
                "discovery_lane": payload.get("discovery_lane"),
                "owner_inventory_source": "target_date_postclose_report",
            }

    candidate_symbols = (expansion or {}).get("candidate_symbols") or {}
    if isinstance(candidate_symbols, dict):
        known = {str(row.get("symbol")) for row in profiles.values()}
        for symbol, name in candidate_symbols.items():
            symbol = str(symbol)
            if symbol in known:
                continue
            profile_id = f"prospective_symbol:{symbol}"
            profiles[profile_id] = {
                "profile_id": profile_id,
                "symbol": symbol,
                "name": name,
                "session": None,
                "scope": "prospective_episode_symbol",
                "expected_venues": ["SOR"],
                "owner_inventory_source": "target_date_postclose_report",
            }

    return (
        profiles,
        anchors,
        {
            "tuning": _source(tuning_path, tuning),
            "expanded_candidate_research": _source(expansion_path, expansion),
        },
    )


def _iter_relevant_rows(
    paths: Iterable[Path], symbols: set[str]
) -> Iterable[dict[str, Any]]:
    for path in paths:
        try:
            with path.open("r", encoding="utf-8") as handle:
                for line in handle:
                    key_at = line.find('"symbol"')
                    colon_at = line.find(":", key_at + 8) if key_at >= 0 else -1
                    quote_at = line.find('"', colon_at + 1) if colon_at >= 0 else -1
                    quote_end = line.find('"', quote_at + 1) if quote_at >= 0 else -1
                    if quote_end < 0 or line[quote_at + 1 : quote_end] not in symbols:
                        continue
                    try:
                        payload = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if (
                        isinstance(payload, dict)
                        and str(payload.get("symbol")) in symbols
                    ):
                        yield payload
        except OSError:
            continue


def _micro_context(
    target_date: str,
    observation_root: Path,
    symbols: set[str],
    anchors: list[dict[str, Any]],
    source_exclusion_manifest_path: Path,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    partition = observation_root / f"trade_date={target_date}"
    stream_paths = sorted(partition.glob("venue=*/session=*/market_stream.jsonl"))
    depth_paths = sorted(partition.glob("venue=*/session=*/market_depth_stream.jsonl"))
    ref_paths = sorted(
        partition.glob("venue=*/session=*/market_stream_event_references.jsonl")
    )
    try:
        exclusion_manifest = load_source_exclusion_manifest(
            source_exclusion_manifest_path
        )
        excluded_scopes = {
            (
                str(entry["trade_date"]),
                str(entry["venue"]),
                str(entry["session_bucket"]),
                int(entry["sequence_epoch"]),
            )
            for entry in exclusion_manifest.get("exclusions") or []
        }
        exclusion_manifest_status = "loaded"
    except (KeyError, TypeError, ValueError):
        excluded_scopes = set()
        exclusion_manifest_status = "missing_or_invalid"

    def is_excluded(payload: dict[str, Any]) -> bool:
        try:
            scope = (
                target_date,
                str(payload.get("venue") or ""),
                str(payload.get("session_bucket") or ""),
                int(payload.get("sequence_epoch") or 0),
            )
        except (TypeError, ValueError):
            return False
        return scope in excluded_scopes

    inventory: dict[str, dict[str, Any]] = {
        symbol: {
            "observed_row_count": 0,
            "eligible_row_count": 0,
            "ineligible_row_count": 0,
            "source_excluded_row_count": 0,
            "invalid_contract_row_count": 0,
            "depth_row_count": 0,
            "venues": set(),
            "sessions": set(),
        }
        for symbol in symbols
    }
    windows: dict[str, dict[str, Any]] = {
        anchor["anchor_id"]: {
            "rows": [],
            "depth_rows": 0,
            "shock_reference_count": 0,
        }
        for anchor in anchors
    }
    anchors_by_symbol: dict[str, list[tuple[dict[str, Any], datetime]]] = defaultdict(
        list
    )
    for anchor in anchors:
        anchor_at = _parse_ts(anchor["anchor_at"])
        if anchor_at is not None:
            anchors_by_symbol[anchor["symbol"]].append((anchor, anchor_at))

    for payload in _iter_relevant_rows(stream_paths, symbols):
        symbol = str(payload.get("symbol"))
        item = inventory[symbol]
        item["observed_row_count"] += 1
        item["venues"].add(str(payload.get("venue") or "unknown"))
        item["sessions"].add(str(payload.get("session_bucket") or "unknown"))
        if is_excluded(payload):
            item["source_excluded_row_count"] += 1
            item["ineligible_row_count"] += 1
            continue
        timestamp = _parse_ts(
            payload.get("local_receive_timestamp") or payload.get("exchange_timestamp")
        )
        price = _finite_float(payload.get("trade_price"))
        contract_valid = payload.get("schema") in {
            "scalp_micro_reversion_market_stream_point_v1",
            "scalp_micro_reversion_market_stream_point_v2",
            "scalp_micro_reversion_market_stream_point_v3",
        } and not (
            payload.get("actual_order_submitted") is not False
            or payload.get("broker_order_forbidden") is not True
            or payload.get("trading_runtime_effect") is not False
            or timestamp is None
            or price is None
            or price <= 0
        )
        eligible = contract_valid and payload.get("path_consumer_eligible") is not False
        if not contract_valid:
            item["invalid_contract_row_count"] += 1
        item["eligible_row_count" if eligible else "ineligible_row_count"] += 1
        if not eligible:
            continue
        for anchor, anchor_at in anchors_by_symbol.get(symbol, []):
            if payload.get("venue") not in anchor["expected_venues"]:
                continue
            if (
                anchor_at - timedelta(seconds=PRE_WINDOW_SEC)
                <= timestamp
                <= anchor_at + timedelta(seconds=POST_WINDOW_SEC)
            ):
                windows[anchor["anchor_id"]]["rows"].append(
                    {
                        "timestamp": timestamp,
                        "price": price,
                        "best_bid": _finite_float(payload.get("best_bid")),
                        "best_ask": _finite_float(payload.get("best_ask")),
                        "venue": payload.get("venue"),
                        "session": payload.get("session_bucket"),
                    }
                )

    for payload in _iter_relevant_rows(depth_paths, symbols):
        symbol = str(payload.get("symbol"))
        if is_excluded(payload):
            inventory[symbol]["source_excluded_row_count"] += 1
            continue
        if (
            payload.get("schema") != "scalp_micro_reversion_market_depth_point_v1"
            or payload.get("trading_runtime_effect") is not False
            or payload.get("actual_order_submitted") is not False
            or payload.get("broker_order_forbidden") is not True
        ):
            inventory[symbol]["invalid_contract_row_count"] += 1
            continue
        inventory[symbol]["depth_row_count"] += 1
        timestamp = _parse_ts(
            payload.get("local_receive_timestamp") or payload.get("exchange_timestamp")
        )
        if timestamp is None:
            continue
        for anchor, anchor_at in anchors_by_symbol.get(symbol, []):
            if payload.get("venue") not in anchor["expected_venues"]:
                continue
            if (
                anchor_at - timedelta(seconds=PRE_WINDOW_SEC)
                <= timestamp
                <= anchor_at + timedelta(seconds=POST_WINDOW_SEC)
            ):
                windows[anchor["anchor_id"]]["depth_rows"] += 1

    for payload in _iter_relevant_rows(ref_paths, symbols):
        symbol = str(payload.get("symbol"))
        if is_excluded(payload):
            inventory[symbol]["source_excluded_row_count"] += 1
            continue
        if (
            payload.get("schema") != "scalp_micro_reversion_path_event_reference_v2"
            or payload.get("trading_runtime_effect") is not False
            or payload.get("actual_order_submitted") is not False
            or payload.get("broker_order_forbidden") is not True
        ):
            inventory[symbol]["invalid_contract_row_count"] += 1
            continue
        timestamp_ms = _finite_float(payload.get("event_detected_at_ms"))
        if timestamp_ms is None:
            continue
        timestamp = datetime.fromtimestamp(timestamp_ms / 1000.0, tz=timezone.utc)
        for anchor, anchor_at in anchors_by_symbol.get(symbol, []):
            if payload.get("venue") not in anchor["expected_venues"]:
                continue
            if (
                anchor_at - timedelta(seconds=PRE_WINDOW_SEC)
                <= timestamp
                <= anchor_at + timedelta(seconds=POST_WINDOW_SEC)
            ):
                windows[anchor["anchor_id"]]["shock_reference_count"] += 1

    for item in inventory.values():
        item["venues"] = sorted(item["venues"])
        item["sessions"] = sorted(item["sessions"])

    return (
        {
            "partition": str(partition),
            "partition_status": "loaded" if stream_paths else "missing",
            "market_stream_file_count": len(stream_paths),
            "market_depth_file_count": len(depth_paths),
            "event_reference_file_count": len(ref_paths),
            "source_exclusion_manifest_path": str(source_exclusion_manifest_path),
            "source_exclusion_manifest_status": exclusion_manifest_status,
            "source_exclusion_scope_count": len(excluded_scopes),
        },
        inventory,
        windows,
    )


def _anchor_result(
    anchor: dict[str, Any],
    symbol_inventory: dict[str, Any],
    window: dict[str, Any],
    *,
    partition_loaded: bool,
    source_contract_ready: bool,
    clean_baseline_allowed: bool,
) -> dict[str, Any]:
    rows = sorted(window["rows"], key=lambda row: row["timestamp"])
    anchor_at = _parse_ts(anchor["anchor_at"])
    post = [
        row for row in rows if anchor_at is not None and row["timestamp"] >= anchor_at
    ]
    if not clean_baseline_allowed:
        status = "pre_clean_baseline_archive_only"
    elif not partition_loaded:
        status = "micro_date_partition_missing"
    elif not source_contract_ready:
        status = "micro_source_exclusion_manifest_missing_or_invalid"
    elif symbol_inventory["observed_row_count"] == 0:
        status = "micro_symbol_not_observed"
    elif not rows:
        status = "micro_anchor_window_not_observed"
    elif not post:
        status = "micro_post_anchor_not_observed"
    else:
        status = "matched"
    reference = _finite_float(anchor.get("anchor_price"))
    if (reference is None or reference <= 0) and post:
        reference = post[0]["price"]
    metrics: dict[str, Any] = {
        "eligible_window_row_count": len(rows),
        "post_anchor_row_count": len(post),
        "depth_window_row_count": window["depth_rows"],
        "shock_reference_count": window["shock_reference_count"],
        "bbo_complete_row_count": sum(
            row["best_bid"] is not None and row["best_ask"] is not None for row in rows
        ),
        "reference_price": reference,
        "mfe_bps": None,
        "mae_bps": None,
        "terminal_return_bps": None,
        "time_to_low_ms": None,
    }
    if post and reference is not None and reference > 0:
        high = max(post, key=lambda row: row["price"])
        low = min(post, key=lambda row: row["price"])
        metrics.update(
            {
                "mfe_bps": round((high["price"] / reference - 1.0) * 10000.0, 4),
                "mae_bps": round((low["price"] / reference - 1.0) * 10000.0, 4),
                "terminal_return_bps": round(
                    (post[-1]["price"] / reference - 1.0) * 10000.0, 4
                ),
                "time_to_low_ms": (
                    round((low["timestamp"] - anchor_at).total_seconds() * 1000.0)
                    if anchor_at is not None
                    else None
                ),
            }
        )
    result = dict(anchor)
    result.update(
        {
            "micro_context_status": status,
            "micro_tuning_input_allowed": status == "matched",
            "base_owner_tuning_effect": False,
            "metrics": metrics,
        }
    )
    return result


def build_report(
    target_date: str,
    *,
    report_root: Path = DATA_DIR / "report",
    observation_root: Path = OBSERVATION_ROOT,
    source_exclusion_manifest_path: Path = DEFAULT_SOURCE_EXCLUSION_MANIFEST,
    now: datetime | None = None,
) -> dict[str, Any]:
    target_day = date.fromisoformat(target_date)
    clean_baseline_allowed = target_day >= CLEAN_BASELINE_DATE
    widget_symbols, widget_anchors, widget_sources = _widget_inventory(
        target_date, report_root
    )
    episode_profiles, episode_anchors, episode_sources = _episode_inventory(
        target_date, report_root
    )
    anchors = widget_anchors + episode_anchors
    symbols = set(widget_symbols)
    symbols.update(
        str(row.get("symbol")) for row in episode_profiles.values() if row.get("symbol")
    )
    micro_source, micro_inventory, windows = _micro_context(
        target_date,
        observation_root,
        symbols,
        anchors,
        source_exclusion_manifest_path,
    )
    results = [
        _anchor_result(
            anchor,
            micro_inventory[anchor["symbol"]],
            windows[anchor["anchor_id"]],
            partition_loaded=micro_source["partition_status"] == "loaded",
            source_contract_ready=(
                micro_source["source_exclusion_manifest_status"] == "loaded"
            ),
            clean_baseline_allowed=clean_baseline_allowed,
        )
        for anchor in anchors
    ]
    results_by_scope: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for result in results:
        results_by_scope[(result["owner"], result["scope_id"])].append(result)

    gaps: list[dict[str, Any]] = []
    for owner, rows in (("widget", widget_symbols), ("episode", episode_profiles)):
        for scope_id, row in rows.items():
            symbol = str(row.get("symbol") or scope_id)
            inventory = micro_inventory.get(symbol) or {
                "observed_row_count": 0,
                "eligible_row_count": 0,
                "ineligible_row_count": 0,
                "source_excluded_row_count": 0,
                "invalid_contract_row_count": 0,
                "depth_row_count": 0,
                "venues": [],
                "sessions": [],
            }
            scope_results = (
                [
                    result
                    for result in results
                    if result["owner"] == "widget" and result["symbol"] == symbol
                ]
                if owner == "widget"
                else results_by_scope.get((owner, str(scope_id)), [])
            )
            if not clean_baseline_allowed:
                gap_class = "pre_clean_baseline_archive_only"
            elif micro_source["partition_status"] != "loaded":
                gap_class = "micro_date_partition_missing"
            elif micro_source["source_exclusion_manifest_status"] != "loaded":
                gap_class = "micro_source_exclusion_manifest_missing_or_invalid"
            elif inventory["observed_row_count"] == 0:
                gap_class = "micro_symbol_not_observed"
            elif scope_results and any(
                item["micro_context_status"] != "matched" for item in scope_results
            ):
                gap_class = "micro_anchor_window_not_observed"
            else:
                gap_class = None
            row["micro_source_inventory"] = inventory
            row["micro_context_status"] = gap_class or (
                "matched" if scope_results else "observed_no_owner_episode"
            )
            row["micro_tuning_input_allowed"] = bool(scope_results) and all(
                item["micro_context_status"] == "matched" for item in scope_results
            )
            row["base_owner_tuning_effect"] = False
            row["anchor_results"] = scope_results
            if gap_class:
                scope_kinds = row.get("scopes") or [row.get("scope")]
                scope_kinds = [str(value) for value in scope_kinds if value]
                active_scope = (
                    "active_widget_owner"
                    if owner == "widget" and "active_widget_owner" in scope_kinds
                    else "active_episode_owner"
                    if owner == "episode" and "active_episode_owner" in scope_kinds
                    else scope_kinds[0]
                    if scope_kinds
                    else "unknown_owner_scope"
                )
                gaps.append(
                    {
                        "owner": owner,
                        "scope_id": str(scope_id),
                        "scope_kind": active_scope,
                        "symbol": symbol,
                        "expected_venues": list(row.get("expected_venues") or ["SOR"]),
                        "gap_class": gap_class,
                        "effect": "micro_context_unavailable_base_owner_tuning_unchanged",
                    }
                )

    source_gaps = [
        {"owner": "widget", "source": key, "gap_class": "owner_source_missing"}
        for key, value in widget_sources.items()
        if value["status"] != "loaded"
    ] + [
        {"owner": "episode", "source": key, "gap_class": "owner_source_missing"}
        for key, value in episode_sources.items()
        if value["status"] != "loaded"
    ]
    gaps.extend(source_gaps)
    matched = sum(item["micro_context_status"] == "matched" for item in results)
    generated = now or datetime.now().astimezone()
    decision = (
        "diagnostic_attribution_ready"
        if not gaps
        else "partial_owner_or_micro_source_gap_base_tuning_unchanged"
    )
    report = {
        "schema": REPORT_SCHEMA,
        "report_type": REPORT_TYPE,
        "target_date": target_date,
        "generated_at_kst": generated.isoformat(),
        "clean_tuning_baseline_date": CLEAN_BASELINE_DATE.isoformat(),
        "clean_baseline_allowed": clean_baseline_allowed,
        "status": "pass" if not gaps else "warning",
        "decision": decision,
        "metric_contract": METRIC_CONTRACT,
        "policy_change_readiness": POLICY_CHANGE_READINESS_CONTRACT,
        "promotion_candidate_intake_contract": PROMOTION_CANDIDATE_INTAKE_CONTRACT,
        # The daily attribution report does not invent a runtime candidate.
        # A future rolling paired-policy producer may append only candidates
        # satisfying the intake contract; the persistent approval ledger then
        # owns reminders and explicit operator-decision tracking.
        "policy_promotion_candidates": [],
        "authority": {
            "decision_authority": "postclose_diagnostic_only",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "base_owner_tuning_continues_when_micro_missing": True,
        },
        "sources": {
            "widget": widget_sources,
            "episode": episode_sources,
            "micro_reversion": micro_source,
        },
        "summary": {
            "dynamic_symbol_count": len(symbols),
            "widget_symbol_count": len(widget_symbols),
            "episode_profile_count": len(episode_profiles),
            "anchor_count": len(results),
            "matched_anchor_count": matched,
            "unmatched_anchor_count": len(results) - matched,
            "producer_consumer_gap_count": len(gaps),
        },
        "consumers": {
            "widget_postclose_tuning": {
                "mode": "supplemental_diagnostic_context",
                "base_policy_unchanged_on_missing": True,
                "symbols": widget_symbols,
            },
            "episode_machine_postclose_tuning": {
                "mode": "supplemental_diagnostic_context",
                "base_policy_unchanged_on_missing": True,
                "profiles": episode_profiles,
            },
        },
        "producer_consumer_gaps": gaps,
    }
    collection_targets = build_collection_targets(
        report,
        generated_at=generated,
    )
    selected_collection_targets = collection_targets["selected_targets"]
    report["collection_feedback"] = {
        "schema": collection_targets["schema"],
        "effective_date": collection_targets["effective_date"],
        "status": collection_targets["status"],
        "selected_symbol_count": collection_targets["budget"][
            "selected_symbol_count"
        ],
        "repair_gap_selected_symbol_count": sum(
            bool(row.get("gap_classes")) for row in selected_collection_targets
        ),
        "policy_sample_selected_symbol_count": sum(
            "micro_policy_sample_accumulation"
            in (row.get("collection_reasons") or ())
            for row in selected_collection_targets
        ),
        "overflow_symbol_count": collection_targets["budget"][
            "overflow_symbol_count"
        ],
        "manual_control_exclusion_applied": False,
        "market_data_subscription_effect": True,
        "trading_runtime_effect": False,
    }
    return report


def render_markdown(report: dict[str, Any]) -> str:
    summary = report["summary"]
    lines = [
        "# Machine Microstructure Attribution",
        "",
        f"- Target date: `{report['target_date']}`",
        f"- Status: `{report['status']}`",
        f"- Decision: `{report['decision']}`",
        "- Authority: diagnostic only; existing widget/episode policy is unchanged.",
        (
            "- Collection feedback: next-session source-only targets "
            f"`{report.get('collection_feedback', {}).get('selected_symbol_count', 0)}`; "
            "repair gaps and bounded policy-sample rotation are included; "
            "manual-control exclusions are not applied."
        ),
        "",
        "## Coverage",
        "",
        "| Dynamic symbols | Widget symbols | Episode profiles | Anchors | Matched | Gaps |",
        "| ---: | ---: | ---: | ---: | ---: | ---: |",
        (
            f"| {summary['dynamic_symbol_count']} | {summary['widget_symbol_count']} | "
            f"{summary['episode_profile_count']} | {summary['anchor_count']} | "
            f"{summary['matched_anchor_count']} | {summary['producer_consumer_gap_count']} |"
        ),
        "",
        "## Producer/Consumer Gaps",
        "",
    ]
    gaps = report["producer_consumer_gaps"]
    if not gaps:
        lines.append("- None")
    else:
        lines.extend(
            [
                "| Owner | Scope | Symbol | Gap | Effect |",
                "| --- | --- | --- | --- | --- |",
            ]
        )
        for gap in gaps:
            lines.append(
                f"| {gap.get('owner')} | {gap.get('scope_id') or gap.get('source')} | "
                f"{gap.get('symbol') or '-'} | {gap.get('gap_class')} | "
                f"{gap.get('effect') or 'micro context unavailable'} |"
            )
    lines.extend(
        [
            "",
            "Missing micro data is not imputed as zero return and does not stop the existing owner tuning path.",
            "",
            "## Policy Change Boundary",
            "",
            (
                "This daily report cannot change policy. Policy review opens only after "
                "5 observed trading days, 20 matched owner/symbol/session anchors, "
                "BBO coverage >=95%, depth coverage >=90%, and a cost-adjusted paired "
                "5/10/20-day EV improvement with no downside deterioration."
            ),
            (
                "The first runtime linkage still requires a new bounded family mapping "
                "and explicit operator approval; any approved candidate applies PREOPEN only."
            ),
            "",
        ]
    )
    return "\n".join(lines)


def _atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def write_report(
    report: dict[str, Any], output_dir: Path = OUTPUT_DIR
) -> tuple[Path, Path]:
    target_date = report["target_date"]
    json_path = output_dir / f"{REPORT_TYPE}_{target_date}.json"
    markdown_path = output_dir / f"{REPORT_TYPE}_{target_date}.md"
    _atomic_write(
        json_path,
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    _atomic_write(markdown_path, render_markdown(report))
    return json_path, markdown_path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", default=datetime.now(KST).date().isoformat())
    parser.add_argument("--report-root", type=Path, default=DATA_DIR / "report")
    parser.add_argument("--observation-root", type=Path, default=OBSERVATION_ROOT)
    parser.add_argument(
        "--source-exclusion-manifest",
        type=Path,
        default=DEFAULT_SOURCE_EXCLUSION_MANIFEST,
    )
    parser.add_argument("--output-dir", type=Path, default=OUTPUT_DIR)
    parser.add_argument(
        "--collection-target-root",
        type=Path,
        default=None,
    )
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()
    report = build_report(
        args.target_date,
        report_root=args.report_root,
        observation_root=args.observation_root,
        source_exclusion_manifest_path=args.source_exclusion_manifest,
    )
    if args.write:
        write_report(report, args.output_dir)
        collection_payload = build_collection_targets(report)
        if args.collection_target_root is None:
            write_collection_targets(collection_payload)
        else:
            write_collection_targets(
                collection_payload,
                root=args.collection_target_root,
            )
    if args.print_summary or not args.write:
        print(
            json.dumps(
                {"status": report["status"], **report["summary"]}, ensure_ascii=False
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
