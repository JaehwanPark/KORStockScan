"""Build the bounded AVG_DOWN buy-pressure economic replay candidate.

V2 separates gate observations, fixed-observed-exit source-only economics,
and evidence that can independently replay ADD and NO_ADD lifecycle exits.
Only the final class can carry PREOPEN runtime authority.
"""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from src.engine.automation.source_quality_hard_gate import (
    filter_source_dates_by_preflight,
    load_source_quality_preflight,
)
from src.engine.lifecycle.scale_in_incremental_counterfactual import (
    compute_fixed_exit_incremental_economics,
)
from src.engine.lifecycle.avg_down_replay import (
    build_replay_evidence,
    cost_rate_from_version,
    runtime_config_valid,
    source_only_observation_valid,
    canonical_digest,
    replay_evidence_contract_errors,
)
from src.engine.trade_profit import calculate_net_realized_pnl
from src.utils.constants import DATA_DIR, TRADING_RULES

KST = timezone(timedelta(hours=9))
REPORT_TYPE = "scalping_avg_down_recovery_calibration"
RUNTIME_UPDATE_MODE = "single_cumulative_quality_update"
FAMILY = "scalping_avg_down_recovery_quality_gate"
STAGE = "scale_in"
REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE
CLEAN_BASELINE_DATE = "2026-06-05"
CLEAN_BASELINE_TS = datetime(2026, 6, 5, tzinfo=KST)
SCHEMA_VERSION = 2
ROUTE_EVENT_SCHEMA = "avg_down_route_arbitration_v2"
EVIDENCE_CONTRACT_VERSION = "avg_down_paired_economics_v2"
FIXED_EXIT_METHOD = "fixed_observed_exit_counterfactual"
PAIRED_EXIT_METHOD = "paired_add_no_add_lifecycle_replay"
SOURCE_ONLY_AUTHORITY = "fixed_observed_exit_source_only"
RUNTIME_AUTHORITY = "paired_add_no_add_lifecycle_replay"
TARGET_ENV_KEY = "SHALLOW_VOLATILITY_AVG_DOWN_MIN_BUY_PRESSURE"
TARGET_VALUE_KEY = "shallow_min_buy_pressure"
TUNING_GRID = (80.0, 85.0, 90.0)
BOUNDS = {"min": 80.0, "max": 90.0, "unit": "buy_pressure_pct"}
MAX_STEP_PER_DAY = 5.0
RUNTIME_PROMOTION_SAMPLE_FLOOR = 10
RUNTIME_VALUE_SOURCES = frozenset({"exact_process_env", "runtime_rules_loaded_value"})
FORBIDDEN_USES = [
    "intraday_threshold_mutation",
    "hard_safety_relaxation",
    "broker_guard_bypass",
    "order_guard_relaxation",
    "quantity_cap_release",
    "provider_route_change",
    "bot_restart",
    "fixed_exit_source_only_runtime_promotion",
]


def _safe_float(value: Any, default: float | None = None) -> float | None:
    if value in (None, "", "-", "null", "none"):
        return default
    try:
        result = float(str(value).replace("+", "").replace("%", ""))
    except (TypeError, ValueError):
        return default
    return result if math.isfinite(result) else default


def _safe_int(value: Any, default: int = 0) -> int:
    number = _safe_float(value, None)
    return int(number) if number is not None and number.is_integer() else default


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _parse_time(value: Any) -> datetime | None:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KST)
    return parsed.astimezone(KST)


def _json_value(value: Any, default: Any) -> Any:
    if isinstance(value, type(default)):
        return value
    try:
        parsed = json.loads(str(value or ""))
    except (TypeError, ValueError, json.JSONDecodeError):
        return default
    return parsed if isinstance(parsed, type(default)) else default


def _canonical_hash(value: Any) -> str:
    payload = json.dumps(
        value, ensure_ascii=True, sort_keys=True, separators=(",", ":"), default=str
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _events_path(target_date: str) -> Path:
    return DATA_DIR / "pipeline_events" / f"pipeline_events_{target_date}.jsonl"


def _events_paths_for_date(target_date: str) -> list[Path]:
    path = _events_path(target_date)
    result: list[Path] = []
    gzip_path = path.with_suffix(path.suffix + ".gz")
    if path.exists():
        result.append(path)
    elif gzip_path.exists():
        result.append(gzip_path)
    late = path.with_name(f"{path.stem}.late.jsonl")
    late_gzip = late.with_suffix(late.suffix + ".gz")
    if late.exists():
        result.append(late)
    elif late_gzip.exists():
        result.append(late_gzip)
    return result


def _date_from_events_path(path: Path) -> str | None:
    name = path.name
    for suffix in (".late.jsonl.gz", ".late.jsonl", ".jsonl.gz", ".jsonl"):
        if name.startswith("pipeline_events_") and name.endswith(suffix):
            return name.removeprefix("pipeline_events_").removesuffix(suffix)
    return None


def _iter_events_paths_for_window(target_date: str) -> list[Path]:
    paths_by_date: dict[str, dict[str, Path]] = {}
    for pattern in (
        "pipeline_events_*.jsonl",
        "pipeline_events_*.jsonl.gz",
        "pipeline_events_*.late.jsonl",
        "pipeline_events_*.late.jsonl.gz",
    ):
        for path in sorted((DATA_DIR / "pipeline_events").glob(pattern)):
            source_date = _date_from_events_path(path)
            if not source_date or not (
                CLEAN_BASELINE_DATE <= source_date <= target_date
            ):
                continue
            part = "late" if ".late.jsonl" in path.name else "base"
            by_part = paths_by_date.setdefault(source_date, {})
            previous = by_part.get(part)
            if previous is None or previous.suffix == ".gz":
                by_part[part] = path
    return [
        paths_by_date[source_date][part]
        for source_date in sorted(paths_by_date)
        for part in ("base", "late")
        if part in paths_by_date[source_date]
    ]


def _iter_events(paths: list[Path]) -> Iterable[dict[str, Any]]:
    for source in paths:
        source_date = _date_from_events_path(source)
        opener = gzip.open if str(source).endswith(".gz") else open
        if not source.exists():
            continue
        with opener(source, "rt", encoding="utf-8", errors="ignore") as handle:
            for line in handle:
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(event, dict):
                    continue
                fields = (
                    event.get("fields") if isinstance(event.get("fields"), dict) else {}
                )
                yield {**event, **fields, "_source_event_date": source_date}


def _current_value() -> float:
    value = _safe_float(
        getattr(TRADING_RULES, "SHALLOW_VOLATILITY_AVG_DOWN_MIN_BUY_PRESSURE", 85.0),
        85.0,
    )
    return 85.0 if value is None else value


def _identity(event: dict[str, Any]) -> str:
    return str(
        event.get("position_episode_id") or event.get("main_lifecycle_id") or ""
    ).strip()


def _terminal_price(event: dict[str, Any]) -> float | None:
    value = _safe_float(
        event.get("position_weighted_sell_price")
        or event.get("sell_price")
        or event.get("main_lifecycle_exit_price"),
        None,
    )
    return value if value is not None and value.is_integer() else None


def _valid_route_arm(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    selected_route = str(value.get("selected_route") or "").strip()
    signature = str(value.get("behavior_signature") or "").strip()
    if not selected_route or not signature:
        return None
    if not isinstance(value.get("should_add"), bool) or not isinstance(
        value.get("route_evaluation_complete"), bool
    ):
        return None
    should_add = _boolish(value.get("should_add"))
    if should_add == (selected_route in {"NO_ADD", "NOT_EVALUATED_DOWNSTREAM"}):
        return None
    proposed_add_price = _safe_float(value.get("proposed_add_price"), None)
    if proposed_add_price is not None and not proposed_add_price.is_integer():
        proposed_add_price = None
    result = {
        "should_add": should_add,
        "selected_route": selected_route,
        "behavior_signature": signature,
        "action_reason": str(value.get("action_reason") or ""),
        "proposed_add_price": proposed_add_price,
        "proposed_add_qty": _safe_int(value.get("proposed_add_qty"), 0),
        "sizing_status": str(value.get("sizing_status") or "not_available"),
        "price_allowed": _boolish(value.get("price_allowed")),
        "exit_replay_method": str(value.get("exit_replay_method") or FIXED_EXIT_METHOD),
        "route_evaluation_complete": _boolish(
            value.get("route_evaluation_complete", False)
        ),
    }
    result["economic_inputs_complete"] = bool(
        result["route_evaluation_complete"]
        and (
            not should_add
            or (
                result["proposed_add_price"] is not None
                and result["proposed_add_price"] > 0
                and result["proposed_add_qty"] > 0
                and result["price_allowed"]
            )
        )
    )
    return result


def _valid_paired_exit_outcome(value: Any) -> dict[str, Any] | None:
    if not isinstance(value, dict):
        return None
    exit_price = _safe_float(value.get("exit_price"), None)
    source_event_id = str(value.get("terminal_source_event_id") or "").strip()
    exit_policy_version = str(value.get("exit_policy_version") or "").strip()
    if (
        str(value.get("status") or "").upper() != "COMPLETED"
        or exit_price is None
        or exit_price <= 0
        or not exit_price.is_integer()
        or not source_event_id
        or exit_policy_version in {"", "unknown"}
        or str(value.get("evaluation_method") or "") != PAIRED_EXIT_METHOD
        or str(value.get("evidence_authority") or "") != RUNTIME_AUTHORITY
    ):
        return None
    return {
        "status": "COMPLETED",
        "exit_price": exit_price,
        "terminal_source_event_id": source_event_id,
        "exit_policy_version": exit_policy_version,
        "evaluation_method": PAIRED_EXIT_METHOD,
        "evidence_authority": RUNTIME_AUTHORITY,
    }


def _collect_exact_evidence(
    paths: list[Path], *, replay_cache: dict | None = None
) -> dict[str, Any]:
    diagnostics: Counter[str] = Counter()
    raw_event_count = 0
    legacy_proxy_event_count = 0
    observed: dict[str, dict[str, Any]] = {}
    observed_hashes: dict[str, str] = {}
    conflicted_ids: set[str] = set()
    terminals: dict[str, dict[str, Any]] = {}
    terminal_hashes: dict[str, str] = {}
    runtime_configs: list[dict[str, Any]] = []
    sizing_events: dict[str, dict[str, Any]] = {}
    sizing_conflicts: set[str] = set()
    replay_frames: dict[str, list[dict[str, Any]]] = {}

    for event in _iter_events(paths):
        raw_event_count += 1
        stage = str(event.get("stage") or "")
        if stage in {
            "scalp_sim_scale_in_candidate_funnel",
            "stop_line_touch_mandatory_avg_down_submitted",
        }:
            legacy_proxy_event_count += 1
        observed_at = _parse_time(event.get("emitted_at"))
        source_date = str(event.get("_source_event_date") or "")
        if observed_at is None or observed_at < CLEAN_BASELINE_TS:
            diagnostics["invalid_or_prebaseline_timestamp"] += 1
            continue
        if source_date and observed_at.date().isoformat() != source_date:
            diagnostics["timestamp_file_date_mismatch"] += 1
            continue

        if stage == "avg_down_runtime_config_observed":
            if not runtime_config_valid(
                {
                    **event,
                    "runtime_pid_value_verified": _boolish(
                        event.get("runtime_pid_value_verified")
                    ),
                }
            ):
                diagnostics["invalid_runtime_config_snapshot"] += 1
                continue
            runtime_configs.append(
                {
                    "source_date": source_date,
                    "effective_min_buy_pressure": float(
                        event["effective_min_buy_pressure"]
                    ),
                    "configured_min_buy_pressure": float(
                        event["configured_min_buy_pressure"]
                    ),
                    "runtime_pid_value_verified": True,
                    "policy_version": str(event["avg_down_policy_version"]),
                    "sizing_policy_version": str(event["sizing_policy_version"]),
                    "cost_policy_version": str(event["cost_policy_version"]),
                    "runtime_value_source": str(event["runtime_value_source"]),
                }
            )
            continue

        if stage == "avg_down_route_sizing_observed":
            source_id = str(event.get("source_observation_id") or "")
            if not source_id or not source_only_observation_valid(
                event, "source_only_route_sizing_observation"
            ):
                diagnostics["sizing_enrichment_contract_invalid"] += 1
                continue
            if source_id in sizing_events and _canonical_hash(
                sizing_events[source_id]
            ) != _canonical_hash(event):
                sizing_conflicts.add(source_id)
            sizing_events[source_id] = event
            continue

        if stage == "avg_down_exit_replay_frame_observed":
            source_id = str(event.get("source_observation_id") or "")
            if source_id in (replay_cache or {}):
                # The exact physical source files were checked before reading.
                # Do not retain every historical frame in cumulative memory.
                continue
            if not source_id or not source_only_observation_valid(
                event, "source_only_paired_exit_replay"
            ):
                diagnostics["replay_frame_authority_contract_invalid"] += 1
                continue
            replay_at = _parse_time(
                event.get("replay_observed_at") or observed_at.isoformat()
            )
            if (
                replay_at is None
                or replay_at.date() != observed_at.date()
                or not -0.001 <= (observed_at - replay_at).total_seconds() <= 5
            ):
                diagnostics["replay_frame_event_cutoff_invalid"] += 1
                continue
            frame = {
                key: event.get(key)
                for key in (
                    "source_event_id",
                    "source_observation_id",
                    "scale_in_decision_id",
                    "position_episode_id",
                    "stock_code",
                    "venue",
                    "exit_policy_version",
                    "replay_frame_schema",
                    "sequence",
                    "capture_gap",
                    "capture_end",
                )
            }
            frame.update(
                emitted_at=replay_at.isoformat(),
                market=_json_value(event.get("market"), {}),
                external_results=_json_value(event.get("external_results"), {}),
                full_policy_decisions=_json_value(
                    event.get("full_policy_decisions"), {}
                ),
            )
            replay_frames.setdefault(source_id, []).append(frame)
            continue

        if stage == "avg_down_route_arbitration_observed":
            if str(event.get("avg_down_route_schema") or "") != ROUTE_EVENT_SCHEMA:
                diagnostics["legacy_or_unknown_route_schema"] += 1
                continue
            source_event_id = str(event.get("source_event_id") or "").strip()
            decision_id = str(event.get("scale_in_decision_id") or "").strip()
            episode_id = _identity(event)
            symbol = str(event.get("stock_code") or event.get("code") or "").strip()
            venue = next(
                (
                    value
                    for raw in (
                        event.get("main_lifecycle_venue"),
                        event.get("holding_context_venue"),
                        event.get("venue"),
                    )
                    if (value := str(raw or "").strip().upper())
                    in {"KRX", "NXT", "PREMARKET_KRX_LIKE"}
                ),
                "",
            )
            current = _safe_float(event.get("effective_min_buy_pressure"), None)
            pre_qty = _safe_int(event.get("pre_add_buy_qty"), 0)
            pre_price = _safe_float(event.get("pre_add_buy_price"), None)
            replay = _json_value(event.get("route_replay"), {})
            if (
                not source_event_id
                or not decision_id
                or not episode_id
                or len(symbol) != 6
                or not symbol.isdigit()
                or venue not in {"KRX", "NXT", "PREMARKET_KRX_LIKE"}
                or current is None
                or pre_qty <= 0
                or pre_price is None
                or pre_price <= 0
                or not replay
            ):
                diagnostics["route_required_field_missing"] += 1
                continue
            normalized_replay: dict[str, Any] = {}
            for key, arm in replay.items():
                threshold = _safe_float(key, None)
                normalized = _valid_route_arm(arm)
                if threshold is not None and normalized is not None:
                    normalized_replay[f"{threshold:g}"] = normalized
            if f"{current:g}" not in normalized_replay:
                diagnostics["current_route_replay_missing"] += 1
                continue
            normalized = {
                "source_event_id": source_event_id,
                "scale_in_decision_id": decision_id,
                "position_episode_id": episode_id,
                "stock_code": symbol,
                "venue": venue,
                "session": str(
                    event.get("main_lifecycle_session_bucket")
                    or event.get("holding_context_session")
                    or event.get("session")
                    or "unknown"
                ),
                "decision_time": observed_at,
                "source_date": source_date,
                "effective_min_buy_pressure": current,
                "configured_min_buy_pressure": _safe_float(
                    event.get("configured_min_buy_pressure"), current
                ),
                "pre_add_buy_qty": pre_qty,
                "pre_add_buy_price": pre_price,
                "route_replay": normalized_replay,
                "independent_replay_input": {
                    **{
                        key: event.get(key)
                        for key in (
                            "source_event_id",
                            "position_episode_id",
                            "scale_in_decision_id",
                            "pre_add_buy_qty",
                            "pre_add_buy_price",
                            "exit_policy_version",
                            "cost_rate",
                            "replay_peak_price",
                            "replay_start_sequence",
                            "replay_max_frame_gap_sec",
                            "effective_min_buy_pressure",
                        )
                    },
                    "emitted_at": observed_at.isoformat(),
                    "pre_add_buy_qty": pre_qty,
                    "pre_add_buy_price": pre_price,
                    "position_episode_id": episode_id,
                    "stock_code": symbol,
                    "venue": venue,
                    "initial_policy_state": _json_value(
                        event.get("initial_policy_state"), {}
                    ),
                    "policy_snapshot": _json_value(event.get("policy_snapshot"), {}),
                    "route_replay": replay,
                    "independent_exit_replay_frames": [],
                },
                "source_authority": str(
                    event.get("evidence_authority") or SOURCE_ONLY_AUTHORITY
                ),
                "exit_replay_feasibility": str(
                    event.get("exit_replay_feasibility")
                    or "requires_paired_exit_replay"
                ),
                "policy_version": str(
                    event.get("avg_down_policy_version") or "unknown"
                ),
                "sizing_policy_version": str(
                    event.get("sizing_policy_version") or "unknown"
                ),
                "cost_policy_version": str(
                    event.get("cost_policy_version") or "trade_profit_default"
                ),
                "runtime_value_source": str(
                    event.get("runtime_value_source") or "unknown"
                ),
                "runtime_candidate_quality_update_id": str(
                    event.get("runtime_candidate_quality_update_id") or ""
                ),
                "runtime_candidate_evidence_contract_version": str(
                    event.get("runtime_candidate_evidence_contract_version") or ""
                ),
                "runtime_candidate_evidence_digest": str(
                    event.get("runtime_candidate_evidence_digest") or ""
                ),
                "runtime_candidate_selected": _boolish(
                    event.get("runtime_candidate_selected")
                ),
                "runtime_env_written": _boolish(event.get("runtime_env_written")),
                "runtime_pid_value_verified": _boolish(
                    event.get("runtime_pid_value_verified")
                ),
                "runtime_natural_match": _boolish(event.get("runtime_natural_match")),
                "runtime_behavior_changed": _boolish(
                    event.get("runtime_behavior_changed")
                ),
                "runtime_previous_min_buy_pressure": _safe_float(
                    event.get("runtime_previous_min_buy_pressure"), None
                ),
                "runtime_attribution_state": str(
                    event.get("runtime_attribution_state") or "unknown"
                ),
            }
            content_hash = _canonical_hash(
                {**normalized, "decision_time": observed_at.isoformat()}
            )
            if source_event_id in observed_hashes:
                if observed_hashes[source_event_id] == content_hash:
                    diagnostics["duplicate_event_count"] += 1
                else:
                    diagnostics["conflicting_duplicate_event_count"] += 1
                    conflicted_ids.add(source_event_id)
                continue
            observed_hashes[source_event_id] = content_hash
            observed[source_event_id] = normalized
            continue

        if stage not in {"sell_completed", "avg_down_route_arbitration_terminal"}:
            continue
        episode_id = _identity(event)
        terminal_decision_id = str(event.get("scale_in_decision_id") or "").strip()
        sell_price = _terminal_price(event)
        status = str(
            event.get("status") or event.get("terminal_status") or "COMPLETED"
        ).upper()
        paired_exit_replay_raw = _json_value(event.get("paired_exit_replay"), {})
        paired_exit_replay = {
            str(key): normalized
            for key, value in paired_exit_replay_raw.items()
            if (normalized := _valid_paired_exit_outcome(value)) is not None
        }
        real_completed = stage == "sell_completed" and (
            status == "COMPLETED"
            and _boolish(event.get("actual_order_submitted"))
            and _boolish(event.get("sell_execution_receipt_economics_complete"))
            and _boolish(event.get("sell_execution_receipt_quantity_contract_complete"))
        )
        explicit_replay_completed = stage == "avg_down_route_arbitration_terminal" and (
            status == "COMPLETED"
            and bool(terminal_decision_id)
            and (
                (
                    str(event.get("evidence_authority") or "") == SOURCE_ONLY_AUTHORITY
                    and sell_price is not None
                )
                or (
                    str(event.get("evidence_authority") or "") == RUNTIME_AUTHORITY
                    and bool(paired_exit_replay)
                )
            )
        )
        if (
            not episode_id
            or (sell_price is not None and sell_price <= 0)
            or not (real_completed or explicit_replay_completed)
        ):
            diagnostics["terminal_incomplete_or_untrusted"] += 1
            continue
        normalized_terminal = {
            "position_episode_id": episode_id,
            "scale_in_decision_id": terminal_decision_id,
            "terminal_time": observed_at,
            "sell_price": sell_price,
            "status": "COMPLETED",
            "stage": stage,
            "evidence_authority": str(
                event.get("evidence_authority") or "real_fill_completed"
            ),
            "paired_exit_replay": paired_exit_replay,
            "source_observation_id": str(event.get("source_observation_id") or ""),
            "stock_code": str(event.get("stock_code") or event.get("code") or ""),
            "venue": str(event.get("main_lifecycle_venue") or event.get("venue") or ""),
            "policy_version": str(event.get("avg_down_policy_version") or ""),
            "sizing_policy_version": str(event.get("sizing_policy_version") or ""),
            "cost_policy_version": str(event.get("cost_policy_version") or ""),
        }
        terminal_hash = _canonical_hash(
            {**normalized_terminal, "terminal_time": observed_at.isoformat()}
        )
        terminal_identity = (
            f"decision:{terminal_decision_id}"
            if stage == "avg_down_route_arbitration_terminal"
            else f"episode:{episode_id}"
        )
        if terminal_identity in terminal_hashes:
            if terminal_hashes[terminal_identity] == terminal_hash:
                diagnostics["duplicate_terminal_count"] += 1
            else:
                diagnostics["conflicting_terminal_count"] += 1
                terminals.pop(terminal_identity, None)
            continue
        terminal_hashes[terminal_identity] = terminal_hash
        terminals[terminal_identity] = normalized_terminal

    for source_event_id in conflicted_ids:
        observed.pop(source_event_id, None)

    for source_id, row in observed.items():
        if source_id in (replay_cache or {}):
            row["independent_replay_input"]["cached_replay_result"] = replay_cache[
                source_id
            ]
        row["independent_replay_input"]["independent_exit_replay_frames"] = (
            replay_frames.get(source_id, [])
        )
        enrichment = sizing_events.get(source_id)
        if enrichment is None:
            continue
        enriched_at = _parse_time(enrichment.get("emitted_at"))
        if (
            source_id in sizing_conflicts
            or _identity(enrichment) != row["position_episode_id"]
            or enrichment.get("scale_in_decision_id") != row["scale_in_decision_id"]
            or _safe_float(enrichment.get("pre_add_buy_price"))
            != row["pre_add_buy_price"]
            or _safe_int(enrichment.get("pre_add_buy_qty")) != row["pre_add_buy_qty"]
            or enriched_at is None
            or not 0 <= (enriched_at - row["decision_time"]).total_seconds() <= 2.0
        ):
            diagnostics["sizing_enrichment_identity_or_time_mismatch"] += 1
            continue
        for key, values in _json_value(enrichment.get("sizing_replay"), {}).items():
            arm = row["route_replay"].get(key)
            if not arm or not isinstance(values, dict) or not arm["should_add"]:
                continue
            if (
                _safe_float(values.get("proposed_add_price"))
                != arm["proposed_add_price"]
            ):
                diagnostics["sizing_enrichment_price_mismatch"] += 1
                continue
            if (
                arm["sizing_status"]
                != "real_budget_not_available_without_extra_api_call"
            ):
                continue
            updated = _valid_route_arm(
                {
                    **arm,
                    "proposed_add_price": _safe_float(values.get("proposed_add_price")),
                    "proposed_add_qty": _safe_int(values.get("proposed_add_qty")),
                    "sizing_status": "existing_sizing_owner_observed",
                    "behavior_signature": _canonical_hash(
                        {"action": arm["behavior_signature"], "sizing": values}
                    ),
                }
            )
            if updated is not None:
                row["route_replay"][key] = updated
                # Preserve the original replay action/expiry; enrich only the
                # quantity fields, never its authority or policy result.
                row["independent_replay_input"]["route_replay"][key].update(
                    proposed_add_qty=updated["proposed_add_qty"],
                    proposed_add_price=updated["proposed_add_price"],
                )
                row["sizing_enrichment_digest"] = _canonical_hash(enrichment)

    decision_rows: dict[str, dict[str, Any]] = {}
    decision_hashes: dict[str, str] = {}
    conflicted_decision_ids: set[str] = set()
    for row in sorted(observed.values(), key=lambda item: item["decision_time"]):
        decision_id = row["scale_in_decision_id"]
        decision_hash = _canonical_hash(
            {
                key: (value.isoformat() if isinstance(value, datetime) else value)
                for key, value in row.items()
                if key != "source_event_id"
            }
        )
        if decision_id in decision_hashes:
            if decision_hashes[decision_id] == decision_hash:
                diagnostics["duplicate_decision_count"] += 1
            else:
                diagnostics["conflicting_decision_count"] += 1
                conflicted_decision_ids.add(decision_id)
            continue
        decision_hashes[decision_id] = decision_hash
        decision_rows[decision_id] = row

    for decision_id in conflicted_decision_ids:
        decision_rows.pop(decision_id, None)

    decisions: list[dict[str, Any]] = []
    for row in sorted(decision_rows.values(), key=lambda item: item["decision_time"]):
        terminal = terminals.get(
            f"decision:{row['scale_in_decision_id']}"
        ) or terminals.get(f"episode:{row['position_episode_id']}")
        if not terminal:
            row["outcome_state"] = "pending_outcome"
        elif terminal["position_episode_id"] != row["position_episode_id"]:
            row["outcome_state"] = "terminal_identity_mismatch"
            diagnostics["terminal_identity_mismatch"] += 1
        elif any(
            terminal.get(key) and terminal[key] != row[key]
            for key in (
                "stock_code",
                "venue",
                "policy_version",
                "sizing_policy_version",
                "cost_policy_version",
            )
        ) or (
            terminal.get("source_observation_id")
            and terminal["source_observation_id"] != row["source_event_id"]
        ):
            row["outcome_state"] = "terminal_lineage_mismatch"
            diagnostics["terminal_lineage_mismatch"] += 1
        elif terminal["terminal_time"] <= row["decision_time"]:
            row["outcome_state"] = "terminal_before_decision"
            diagnostics["terminal_before_decision"] += 1
        else:
            row["outcome_state"] = (
                "completed_before_horizon"
                if terminal["terminal_time"]
                <= row["decision_time"] + timedelta(minutes=30)
                else "completed_after_horizon"
            )
            row["terminal"] = terminal
        decisions.append(row)
    return {
        "raw_event_count": raw_event_count,
        "legacy_proxy_event_count": legacy_proxy_event_count,
        "decisions": decisions,
        "runtime_configs": runtime_configs,
        "diagnostics": dict(sorted(diagnostics.items())),
        "unique_decision_count": len(decisions),
        "unique_episode_count": len({row["position_episode_id"] for row in decisions}),
        "terminal_counts": dict(Counter(row.get("outcome_state") for row in decisions)),
    }


def _replay_source_files(paths: list[Path]) -> dict:
    identity = {}
    for path in paths:
        try:
            stat = path.stat()
        except OSError:
            continue
        day = _date_from_events_path(path)
        identity.setdefault(day, {})[str(path.absolute())] = [
            stat.st_size,
            stat.st_mtime_ns,
        ]
    return identity


def _load_replay_cache(paths: list[Path]) -> tuple[dict, dict, dict, str]:
    """Reuse only verified source-only results of unchanged physical inputs.

    Source-date quality filtering has already run. Historical frames need not
    accumulate in memory, and pending exact-prompt replies survive next-day jobs.
    A code change invalidates cached evaluation, never silently re-labels it.
    """
    from src.engine.lifecycle.avg_down_policy_replay import implementation_identity

    source_files = _replay_source_files(paths)
    implementation = canonical_digest(implementation_identity())
    cached, replies = {}, {}
    for day, identity in source_files.items():
        path = DATA_DIR / "report" / REPORT_TYPE / f"{REPORT_TYPE}_{day}.json"
        try:
            if path.stat().st_size > 32_000_000:
                continue
            previous = json.loads(path.read_text(encoding="utf-8"))
            replay = previous.get("independent_exit_replay")
            if previous.get("target_date") != day or replay_evidence_contract_errors(
                replay
            ):
                continue
            unchanged = (
                previous.get("replay_source_files", {}).get(day) == identity
                and previous.get("replay_engine_implementation") == implementation
            )
            for episode, value in replay["episodes"].items():
                if value.get("replay_source_date") != day:
                    continue
                replies[episode] = value.get("policy_ai_replay_records", [])
                if unchanged and value.get("replay_observation_digest"):
                    cached[value["source_observation_id"]] = value
        except (OSError, ValueError, TypeError, KeyError, AttributeError):
            continue
    return cached, replies, source_files, implementation


def _arm_incremental_pnl(
    arm: dict[str, Any],
    sell_price: float,
    *,
    pre_add_qty: int,
    pre_add_price: float,
    cost_rate: float,
) -> int | None:
    if not arm.get("route_evaluation_complete"):
        return None
    if not arm.get("should_add"):
        return 0
    if not arm.get("economic_inputs_complete"):
        return None
    economics = compute_fixed_exit_incremental_economics(
        pre_add_qty=pre_add_qty,
        pre_add_price=pre_add_price,
        proposed_qty=arm["proposed_add_qty"],
        proposed_price=arm["proposed_add_price"],
        exit_price=sell_price,
        cost_rate=cost_rate,
    )
    return int(economics["incremental_pnl_krw"])


def _arm_total_pnl(
    arm: dict[str, Any],
    exit_price: float,
    *,
    pre_add_qty: int,
    pre_add_price: float,
    cost_rate: float,
) -> int | None:
    if not arm.get("route_evaluation_complete"):
        return None
    base_pnl = calculate_net_realized_pnl(
        pre_add_price, int(exit_price), pre_add_qty, cost_rate=cost_rate
    )
    if not arm.get("should_add"):
        return int(base_pnl)
    if not arm.get("economic_inputs_complete"):
        return None
    economics = compute_fixed_exit_incremental_economics(
        pre_add_qty=pre_add_qty,
        pre_add_price=pre_add_price,
        proposed_qty=arm["proposed_add_qty"],
        proposed_price=arm["proposed_add_price"],
        exit_price=exit_price,
        cost_rate=cost_rate,
    )
    return int(economics["add_pnl_krw"])


def _candidate_economics(
    decisions: list[dict[str, Any]],
    *,
    current: float,
    candidate: float,
    paired_only: bool = False,
) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    excluded: Counter[str] = Counter()
    seen_episodes: set[str] = set()
    for row in decisions:
        episode_id = row["position_episode_id"]
        if episode_id in seen_episodes:
            excluded["repeated_decision_same_episode"] += 1
            continue
        seen_episodes.add(episode_id)
        terminal = row.get("terminal")
        if not isinstance(terminal, dict):
            excluded[str(row.get("outcome_state") or "pending_outcome")] += 1
            continue
        current_arm = row["route_replay"].get(f"{current:g}")
        candidate_arm = row["route_replay"].get(f"{candidate:g}")
        if not current_arm or not candidate_arm:
            excluded["paired_route_missing"] += 1
            continue
        cost_rate = cost_rate_from_version(row.get("cost_policy_version"))
        if cost_rate is None:
            excluded["frozen_cost_policy_rate_missing"] += 1
            continue
        arm_kwargs = {
            "pre_add_qty": row["pre_add_buy_qty"],
            "pre_add_price": row["pre_add_buy_price"],
            "cost_rate": cost_rate,
        }
        paired_outcomes = terminal.get("paired_exit_replay")
        paired_outcomes = paired_outcomes if isinstance(paired_outcomes, dict) else {}
        current_outcome = paired_outcomes.get(f"{current:g}")
        candidate_outcome = paired_outcomes.get(f"{candidate:g}")
        no_add_outcome = paired_outcomes.get("NO_ADD")
        paired_outcome_rows = (
            [current_outcome, candidate_outcome, no_add_outcome]
            if all(
                isinstance(value, dict)
                for value in (current_outcome, candidate_outcome, no_add_outcome)
            )
            else []
        )
        paired_exit_policy_versions = {
            str(value.get("exit_policy_version") or "") for value in paired_outcome_rows
        }
        paired_terminal_source_ids = [
            str(value.get("terminal_source_event_id") or "")
            for value in paired_outcome_rows
        ]
        paired_ready = bool(
            # The observation remains immutable source-only evidence. Replay
            # authority belongs to a separately bound terminal, not to a
            # prediction of its future exit method on the original route arm.
            terminal.get("stage") == "avg_down_route_arbitration_terminal"
            and terminal.get("evidence_authority") == RUNTIME_AUTHORITY
            and terminal.get("source_observation_id") == row["source_event_id"]
            and all(
                terminal.get(key) and terminal[key] == row[key]
                for key in (
                    "stock_code",
                    "venue",
                    "policy_version",
                    "sizing_policy_version",
                    "cost_policy_version",
                )
            )
            and isinstance(current_outcome, dict)
            and isinstance(candidate_outcome, dict)
            and isinstance(no_add_outcome, dict)
            and len(paired_exit_policy_versions) == 1
            and "" not in paired_exit_policy_versions
            and len(set(paired_terminal_source_ids)) == 3
        )
        if paired_only and not paired_ready:
            excluded["paired_exit_replay_incomplete"] += 1
            continue
        if paired_ready:
            no_add_total_pnl = calculate_net_realized_pnl(
                row["pre_add_buy_price"],
                int(no_add_outcome["exit_price"]),
                row["pre_add_buy_qty"],
                cost_rate=cost_rate,
            )
            current_total_pnl = _arm_total_pnl(
                current_arm, current_outcome["exit_price"], **arm_kwargs
            )
            candidate_total_pnl = _arm_total_pnl(
                candidate_arm, candidate_outcome["exit_price"], **arm_kwargs
            )
            current_pnl = (
                None
                if current_total_pnl is None
                else int(current_total_pnl - no_add_total_pnl)
            )
            candidate_pnl = (
                None
                if candidate_total_pnl is None
                else int(candidate_total_pnl - no_add_total_pnl)
            )
            current_exit_price = current_outcome["exit_price"]
            candidate_exit_price = candidate_outcome["exit_price"]
            no_add_exit_price = no_add_outcome["exit_price"]
            economics_method = PAIRED_EXIT_METHOD
        else:
            fixed_exit_price = _safe_float(terminal.get("sell_price"), None)
            if fixed_exit_price is None:
                excluded["paired_exit_replay_incomplete"] += 1
                continue
            current_pnl = _arm_incremental_pnl(
                current_arm, fixed_exit_price, **arm_kwargs
            )
            candidate_pnl = _arm_incremental_pnl(
                candidate_arm, fixed_exit_price, **arm_kwargs
            )
            current_exit_price = fixed_exit_price
            candidate_exit_price = fixed_exit_price
            no_add_exit_price = fixed_exit_price
            economics_method = FIXED_EXIT_METHOD
        if current_pnl is None or candidate_pnl is None:
            excluded["price_or_sizing_input_missing"] += 1
            continue
        reference_notional = row["pre_add_buy_price"] * row["pre_add_buy_qty"]
        if reference_notional <= 0:
            excluded["reference_notional_invalid"] += 1
            continue
        rows.append(
            {
                "scale_in_decision_id": row["scale_in_decision_id"],
                "position_episode_id": episode_id,
                "venue": row["venue"],
                "reference_notional": reference_notional,
                "current_incremental_pnl_krw": current_pnl,
                "candidate_incremental_pnl_krw": candidate_pnl,
                "candidate_minus_current_pnl_krw": candidate_pnl - current_pnl,
                "current_behavior_signature": current_arm["behavior_signature"],
                "candidate_behavior_signature": candidate_arm["behavior_signature"],
                "behavior_changed": current_arm["behavior_signature"]
                != candidate_arm["behavior_signature"],
                "candidate_should_add": candidate_arm["should_add"],
                "current_should_add": current_arm["should_add"],
                "economics_method": economics_method,
                "current_exit_price": current_exit_price,
                "candidate_exit_price": candidate_exit_price,
                "no_add_exit_price": no_add_exit_price,
                "candidate_add_notional": (
                    (candidate_arm.get("proposed_add_price") or 0)
                    * candidate_arm.get("proposed_add_qty", 0)
                ),
                "paired_exit_replay_ready": paired_ready,
                "paired_exit_policy_version": (
                    next(iter(paired_exit_policy_versions)) if paired_ready else ""
                ),
                "paired_terminal_source_event_ids": (
                    paired_terminal_source_ids if paired_ready else []
                ),
            }
        )
    sample_count = len(rows)
    reference_total = sum(row["reference_notional"] for row in rows)
    candidate_pnl_total = sum(row["candidate_incremental_pnl_krw"] for row in rows)
    current_pnl_total = sum(row["current_incremental_pnl_krw"] for row in rows)
    paired_terminal_ids = [
        source_id
        for row in rows
        for source_id in row["paired_terminal_source_event_ids"]
    ]
    paired_exit_policy_versions = sorted(
        {
            row["paired_exit_policy_version"]
            for row in rows
            if row["paired_exit_policy_version"]
        }
    )
    candidate_pct_rows = [
        100.0 * row["candidate_incremental_pnl_krw"] / row["reference_notional"]
        for row in rows
    ]
    current_pct_rows = [
        100.0 * row["current_incremental_pnl_krw"] / row["reference_notional"]
        for row in rows
    ]
    add_returns = [
        100.0 * row["candidate_incremental_pnl_krw"] / row["candidate_add_notional"]
        for row in rows
        if row["candidate_should_add"] and row["candidate_add_notional"] > 0
    ]
    return {
        "candidate_value": candidate,
        "evaluation_method": (
            PAIRED_EXIT_METHOD if paired_only else "mixed_source_diagnostic"
        ),
        "sample_count": sample_count,
        "unique_complete_episode_count": len(
            {row["position_episode_id"] for row in rows}
        ),
        "behavior_change_count": sum(bool(row["behavior_changed"]) for row in rows),
        "candidate_add_count": sum(bool(row["candidate_should_add"]) for row in rows),
        "current_add_count": sum(bool(row["current_should_add"]) for row in rows),
        "candidate_only_add_count": sum(
            row["candidate_should_add"] and not row["current_should_add"]
            for row in rows
        ),
        "removed_add_count": sum(
            row["current_should_add"] and not row["candidate_should_add"]
            for row in rows
        ),
        "paired_exit_replay_ready_count": sum(
            bool(row["paired_exit_replay_ready"]) for row in rows
        ),
        "paired_exit_policy_versions": paired_exit_policy_versions,
        "paired_terminal_source_ids_unique": bool(paired_terminal_ids)
        and len(paired_terminal_ids) == len(set(paired_terminal_ids)),
        "venue_counts": dict(Counter(row["venue"] for row in rows)),
        "source_quality_adjusted_ev_pct": (
            round(sum(candidate_pct_rows) / sample_count, 6) if sample_count else None
        ),
        "current_source_quality_adjusted_ev_pct": (
            round(sum(current_pct_rows) / sample_count, 6) if sample_count else None
        ),
        "candidate_minus_current_ev_pct": (
            round((sum(candidate_pct_rows) - sum(current_pct_rows)) / sample_count, 6)
            if sample_count
            else None
        ),
        "notional_weighted_ev_pct": (
            round(100.0 * candidate_pnl_total / reference_total, 6)
            if reference_total > 0
            else None
        ),
        "equal_weight_avg_profit_pct": (
            round(sum(add_returns) / len(add_returns), 6) if add_returns else None
        ),
        "candidate_incremental_net_profit_krw": candidate_pnl_total,
        "current_incremental_net_profit_krw": current_pnl_total,
        "candidate_minus_current_net_profit_krw": candidate_pnl_total
        - current_pnl_total,
        "normal_no_add_incremental_net_profit_krw": 0,
        "reference_notional_krw": reference_total,
        "excluded_by_reason": dict(sorted(excluded.items())),
        "comparison_universe_hash": _canonical_hash(rows),
    }


def _source_dates(paths: list[Path]) -> list[str]:
    return sorted(
        {
            source_date
            for path in paths
            if (source_date := _date_from_events_path(path)) is not None
        }
    )


def _positive_economic_improvement(item: dict[str, Any], *, current: float) -> bool:
    """Allow a proven NO_ADD improvement without inventing positive ADD PnL.

    A tightening which only removes ADDs can equal the NO_ADD control. Every
    other candidate must strictly beat it. Both must improve over the current
    policy in equal-weight EV and net KRW on the same complete universe.
    """
    no_add_tightening = bool(
        item["candidate_value"] > current
        and item["removed_add_count"] > 0
        and item["candidate_only_add_count"] == 0
    )
    ev = item["source_quality_adjusted_ev_pct"]
    delta_ev = item["candidate_minus_current_ev_pct"]
    pnl = item["candidate_incremental_net_profit_krw"]
    return bool(
        ev is not None
        and delta_ev is not None
        and (ev >= 0.0 if no_add_tightening else ev > 0.0)
        and (pnl >= 0 if no_add_tightening else pnl > 0)
        and delta_ev > 0.0
        and item["candidate_minus_current_net_profit_krw"] > 0
    )


def build_report(
    target_date: str,
    *,
    generated_at: str | None = None,
    policy_ai_enabled: bool = False,
    cached_policy_ai_records: dict | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or datetime.now(KST).isoformat(timespec="seconds")
    intended_paths = _iter_events_paths_for_window(target_date)
    intended_dates = _source_dates(intended_paths)
    allowed_dates, excluded_dates = filter_source_dates_by_preflight(
        intended_dates, preflight_loader=load_source_quality_preflight
    )
    allowed_set = set(allowed_dates)
    paths = [
        path for path in intended_paths if _date_from_events_path(path) in allowed_set
    ]
    replay_cache, prior_replies, replay_source_files, replay_implementation = (
        _load_replay_cache(paths)
    )
    evidence = _collect_exact_evidence(paths, replay_cache=replay_cache)
    prior_replies.update(cached_policy_ai_records or {})
    all_decisions = evidence["decisions"]
    target_date_decisions = [
        row for row in all_decisions if row.get("source_date") == target_date
    ]
    target_date_configs = [
        row for row in evidence["runtime_configs"] if row["source_date"] == target_date
    ]
    current_sources = [*target_date_decisions, *target_date_configs]
    observed_currents = sorted(
        {float(row["effective_min_buy_pressure"]) for row in current_sources}
    )
    observed_policy_versions = sorted(
        {str(row.get("policy_version") or "") for row in current_sources}
    )
    observed_policy_cohorts = sorted(
        {
            (
                str(row.get("policy_version") or ""),
                str(row.get("sizing_policy_version") or ""),
                str(row.get("cost_policy_version") or ""),
            )
            for row in current_sources
        }
    )
    observed_runtime_value_sources = sorted(
        {str(row.get("runtime_value_source") or "unknown") for row in current_sources}
    )
    runtime_current_provenance_ready = (
        bool(current_sources)
        and all(
            value in RUNTIME_VALUE_SOURCES for value in observed_runtime_value_sources
        )
        and all(
            row.get("runtime_pid_value_verified") is True
            and row.get("configured_min_buy_pressure")
            == row.get("effective_min_buy_pressure")
            for row in current_sources
        )
        and all(
            value not in {"", "unknown"}
            for cohort in observed_policy_cohorts
            for value in cohort
        )
    )
    configured_current = _current_value()
    exact_current = (
        observed_currents[0]
        if (
            len(observed_currents) == 1
            and len(observed_policy_cohorts) == 1
            and runtime_current_provenance_ready
        )
        else None
    )
    current = exact_current if exact_current is not None else configured_current
    selected_policy_cohort = (
        observed_policy_cohorts[0] if exact_current is not None else None
    )
    selected_policy_version = (
        selected_policy_cohort[0] if selected_policy_cohort is not None else None
    )
    decisions = [
        row
        for row in all_decisions
        if exact_current is not None
        and row.get("runtime_pid_value_verified") is True
        and row.get("configured_min_buy_pressure")
        == row.get("effective_min_buy_pressure")
        and float(row["effective_min_buy_pressure"]) == exact_current
        and (
            str(row.get("policy_version") or ""),
            str(row.get("sizing_policy_version") or ""),
            str(row.get("cost_policy_version") or ""),
        )
        == selected_policy_cohort
    ]
    neighbor_values = [
        value
        for value in TUNING_GRID
        if value != current and abs(value - current) <= MAX_STEP_PER_DAY
    ]
    source_economics = [
        _candidate_economics(decisions, current=current, candidate=value)
        for value in neighbor_values
    ]
    paired_economics = [
        _candidate_economics(
            decisions, current=current, candidate=value, paired_only=True
        )
        for value in neighbor_values
    ]
    source_complete = [
        item
        for item in source_economics
        if item["sample_count"] >= RUNTIME_PROMOTION_SAMPLE_FLOOR
        and item["behavior_change_count"] > 0
    ]
    source_positive = [
        item
        for item in source_complete
        if _positive_economic_improvement(item, current=current)
    ]
    source_winner = max(
        source_positive,
        key=lambda item: (
            item["source_quality_adjusted_ev_pct"],
            item["candidate_minus_current_ev_pct"],
        ),
        default=None,
    )
    paired_complete = [
        item
        for item in paired_economics
        if item["sample_count"] >= RUNTIME_PROMOTION_SAMPLE_FLOOR
        and item["behavior_change_count"] > 0
        and item["paired_exit_replay_ready_count"] == item["sample_count"]
        and len(item["paired_exit_policy_versions"]) == 1
        and item["paired_terminal_source_ids_unique"]
    ]
    paired_positive = [
        item
        for item in paired_complete
        if _positive_economic_improvement(item, current=current)
    ]
    runtime_winner = max(
        paired_positive,
        key=lambda item: (
            item["source_quality_adjusted_ev_pct"],
            item["candidate_minus_current_ev_pct"],
        ),
        default=None,
    )
    source_winner_has_complete_paired_evidence = bool(
        source_winner
        and any(
            item["candidate_value"] == source_winner["candidate_value"]
            for item in paired_complete
        )
    )
    winner = runtime_winner or (
        None if source_winner_has_complete_paired_evidence else source_winner
    )
    exact_contract_available = bool(decisions) and exact_current is not None
    bounds_ok = BOUNDS["min"] <= current <= BOUNDS["max"]
    max_paired_sample = max(
        (item["sample_count"] for item in paired_economics), default=0
    )
    sample_floor_passed = max_paired_sample >= RUNTIME_PROMOTION_SAMPLE_FLOOR
    paired_ready = bool(
        runtime_winner
        and runtime_winner["sample_count"] > 0
        and runtime_winner["paired_exit_replay_ready_count"]
        == runtime_winner["sample_count"]
    )
    winner_venues = set((runtime_winner or {}).get("venue_counts") or {})
    venue_scope_ready = bool(runtime_winner) and winner_venues.issuperset(
        {"KRX", "NXT"}
    )
    runtime_ready = bool(
        runtime_winner
        and exact_contract_available
        and bounds_ok
        and sample_floor_passed
        and paired_ready
        and venue_scope_ready
    )
    max_economic_sample = max(
        (item["sample_count"] for item in source_economics), default=0
    )
    coverage_gap = any(
        any(
            count > 0
            for reason_key, count in item["excluded_by_reason"].items()
            if reason_key not in {"repeated_decision_same_episode"}
        )
        for item in source_economics
    )
    if not paths:
        state, reason = "hold_sample", "source_pipeline_events_missing"
    elif not exact_contract_available:
        state, reason = (
            "hold_runtime_scope",
            "exact_route_contract_missing_or_conflicting_current",
        )
    elif not bounds_ok:
        state, reason = "hold_runtime_scope", "current_value_outside_versioned_bounds"
    elif runtime_winner:
        if not venue_scope_ready:
            state, reason = (
                "hold_runtime_scope",
                "common_runtime_venue_scope_not_closed",
            )
        else:
            state = (
                "adjust_down" if winner["candidate_value"] < current else "adjust_up"
            )
            reason = "paired_incremental_net_edge_ready"
    elif coverage_gap:
        state, reason = "hold_runtime_scope", "route_economic_coverage_gap"
    elif not source_economics or max_economic_sample < RUNTIME_PROMOTION_SAMPLE_FLOOR:
        state, reason = "hold_sample", "unique_complete_parent_episode_floor_not_met"
    elif all(item["behavior_change_count"] == 0 for item in source_economics):
        state, reason = "hold_no_change", "no_effect_after_route_arbitration"
    elif source_winner_has_complete_paired_evidence and not runtime_winner:
        state, reason = "hold_no_edge", "paired_economic_hypothesis_rejected"
    elif not source_winner:
        state, reason = "hold_no_edge", "economic_hypothesis_rejected"
    elif not runtime_winner:
        state, reason = "hold_runtime_scope", "requires_paired_exit_replay"
    else:
        state, reason = "hold_no_edge", "economic_hypothesis_rejected"

    recommended = float(winner["candidate_value"]) if winner else current
    changed = bool(winner and recommended != current)
    evidence_authority = RUNTIME_AUTHORITY if runtime_ready else SOURCE_ONLY_AUTHORITY
    evaluation_method = PAIRED_EXIT_METHOD if runtime_ready else FIXED_EXIT_METHOD
    selected_exit_policy_version = (
        runtime_winner["paired_exit_policy_versions"][0]
        if runtime_winner
        and len(runtime_winner.get("paired_exit_policy_versions") or []) == 1
        else evaluation_method
    )
    comparison_hash = (
        winner["comparison_universe_hash"]
        if winner
        else _canonical_hash(
            {
                "source_economics": source_economics,
                "paired_runtime_economics": paired_economics,
            }
        )
    )
    source_dates = _source_dates(paths)
    evidence_material = {
        "target_date": target_date,
        "source_dates": source_dates,
        "family": FAMILY,
        "stage": STAGE,
        "current_value": current,
        "recommended_value": recommended,
        "target_env_key": TARGET_ENV_KEY,
        "bounds": BOUNDS,
        "max_step_per_day": MAX_STEP_PER_DAY,
        "evaluation_method": evaluation_method,
        "exit_policy_version": selected_exit_policy_version,
        "evidence_authority": evidence_authority,
        "comparison_universe_hash": comparison_hash,
        "cost_rate": (
            cost_rate_from_version(selected_policy_cohort[2])
            if selected_policy_cohort
            else None
        ),
        "source_economics": source_economics,
        "paired_runtime_economics": paired_economics,
    }
    evidence_digest = _canonical_hash(evidence_material)
    quality_update_id = f"{FAMILY}:{target_date}:{evidence_digest[:16]}"
    cumulative_window = {
        "window_policy": "clean_baseline_cumulative",
        "cohort_policy": "same_avg_down_policy_version_only",
        "clean_tuning_baseline_date": CLEAN_BASELINE_DATE,
        "start_date": CLEAN_BASELINE_DATE,
        "end_date": target_date,
        "source_dates": source_dates,
        "source_date_count": len(source_dates),
        "source_quality_excluded_date_count": len(excluded_dates),
        "source_quality_excluded_dates": excluded_dates,
    }
    condition_feasibility = {
        "state": (
            "bounded_candidate_ready"
            if runtime_ready and state in {"adjust_up", "adjust_down"}
            else reason
        ),
        "exact_route_contract_available": exact_contract_available,
        "unique_complete_parent_episode_floor_passed": sample_floor_passed,
        "paired_exit_replay_ready": paired_ready,
        "common_runtime_venue_scope_ready": venue_scope_ready,
        "runtime_current_value_provenance_ready": runtime_current_provenance_ready,
        "same_stage_owner_selection_required": True,
        "selected_exit_policy_version": selected_exit_policy_version,
    }
    if exact_contract_available:
        source_quality_gate = "pass_with_row_exclusions" if excluded_dates else "pass"
    else:
        source_quality_gate = "source_quality_blocked"
    metric_contract = {
        "metric_role": "bounded_tunable_incremental_economic_replay",
        "decision_authority": "postclose_candidate_preopen_only",
        "window_policy": "clean_baseline_cumulative_same_policy_version",
        "sample_floor": "unique_complete_eligible_parent_episode>=10",
        "primary_decision_metric": "source_quality_adjusted_ev_pct",
        "source_quality_gate": "exact_route_identity_terminal_and_daily_preflight",
        "forbidden_uses": FORBIDDEN_USES,
    }
    decision_accounting = {
        key: value
        for key, value in evidence.items()
        if key not in {"decisions", "runtime_configs"}
    }
    decision_accounting.update(
        {
            "same_policy_version_decision_count": len(decisions),
            "runtime_value_unverified_decision_count": sum(
                row.get("runtime_pid_value_verified") is not True
                or row.get("configured_min_buy_pressure")
                != row.get("effective_min_buy_pressure")
                for row in all_decisions
            ),
            "target_date_route_observation_count": len(target_date_decisions),
            "target_date_runtime_config_count": len(target_date_configs),
            "selected_policy_version": selected_policy_version,
            "selected_policy_cohort": list(selected_policy_cohort or ()),
            "observed_target_date_current_values": observed_currents,
            "observed_target_date_policy_versions": observed_policy_versions,
            "observed_target_date_policy_cohorts": [
                list(value) for value in observed_policy_cohorts
            ],
            "observed_runtime_value_sources": observed_runtime_value_sources,
        }
    )
    selected_observations = [
        row for row in decisions if row.get("runtime_candidate_selected")
    ]
    runtime_attribution_states = Counter(
        str(row.get("runtime_attribution_state") or "unknown")
        for row in selected_observations
    )

    def attributed_ids(rows):
        return {
            (row["runtime_candidate_quality_update_id"], row["position_episode_id"])
            for row in rows
        }

    matched = [
        row
        for row in selected_observations
        if row.get("runtime_pid_value_verified") and row.get("runtime_natural_match")
    ]
    changed_matches = [row for row in matched if row.get("runtime_behavior_changed")]
    attributed = [
        row for row in changed_matches if isinstance(row.get("terminal"), dict)
    ]
    runtime_application_attribution = {
        "selected_observation_count": len(selected_observations),
        "env_written_observation_count": sum(
            bool(row.get("runtime_env_written")) for row in selected_observations
        ),
        "pid_verified_observation_count": sum(
            bool(row.get("runtime_pid_value_verified")) for row in selected_observations
        ),
        "natural_match_count": len(attributed_ids(matched)),
        "natural_match_observation_count": len(matched),
        "behavior_changed_episode_count": len(attributed_ids(changed_matches)),
        "terminal_attributed_count": len(attributed_ids(attributed)),
        "terminal_attributed_observation_count": len(attributed),
        "no_add_behavior_changed_episode_count": len(
            attributed_ids(
                [
                    row
                    for row in changed_matches
                    if not row["route_replay"][
                        f"{row['effective_min_buy_pressure']:g}"
                    ]["should_add"]
                ]
            )
        ),
        "fill_attribution_state": "requires_exact_add_receipt_not_inferred_from_exit",
        "realized_improvement_claimed": False,
        "quality_update_ids": sorted(
            {
                str(row.get("runtime_candidate_quality_update_id") or "")
                for row in decisions
                if row.get("runtime_candidate_selected")
            }
        ),
        "attribution_states": dict(sorted(runtime_attribution_states.items())),
    }
    candidate = {
        "family": FAMILY,
        "stage": STAGE,
        "priority": 37,
        "family_type": "bounded_tunable_scalping_avg_down_recovery_gate",
        "source_date": target_date,
        "target_date": target_date,
        "calibration_state": state,
        "calibration_reason": reason,
        "threshold_version": f"{FAMILY}:{target_date}:v2",
        "quality_update_id": quality_update_id,
        "evidence_contract_version": EVIDENCE_CONTRACT_VERSION,
        "evidence_digest": evidence_digest,
        "evaluation_method": evaluation_method,
        "evidence_authority": evidence_authority,
        "runtime_update_mode": RUNTIME_UPDATE_MODE,
        "max_runtime_apply_count": 1,
        "cumulative_quality_window": cumulative_window,
        "post_apply_attribution_required": True,
        "sample_count": int(winner["sample_count"] if winner else max_economic_sample),
        "paired_sample_count": max_paired_sample,
        "source_sample_count": evidence["unique_decision_count"],
        "sample_floor": RUNTIME_PROMOTION_SAMPLE_FLOOR,
        "sample_floor_passed": sample_floor_passed,
        "allowed_runtime_apply": runtime_ready
        and state in {"adjust_up", "adjust_down"},
        "recommended_values_changed": changed,
        "safety_revert_required": False,
        "source_quality_gate": source_quality_gate,
        "current_value": current,
        "current_value_source": (
            (
                "same_day_runtime_config_event"
                if target_date_configs
                else "same_day_runtime_route_event"
            )
            if exact_current is not None
            else "runtime_rules_display_only"
        ),
        "current_runtime_value_sources": observed_runtime_value_sources,
        "recommended_value": recommended,
        "current_values": {TARGET_VALUE_KEY: current},
        "recommended_values": {TARGET_VALUE_KEY: recommended},
        "target_env_key": TARGET_ENV_KEY,
        "target_env_keys": [TARGET_ENV_KEY] if changed else [],
        "changed_target_env_keys": [TARGET_ENV_KEY] if changed else [],
        "bounds": BOUNDS,
        "bounds_version": "avg_down_buy_pressure_bounds_v1",
        "max_step_per_day": MAX_STEP_PER_DAY,
        "rollback_value": current,
        "comparison_universe_hash": comparison_hash,
        "cost_policy_version": (
            selected_policy_cohort[2] if selected_policy_cohort else "unknown"
        ),
        "exit_policy_version": selected_exit_policy_version,
        "sizing_policy_version": "recorded_existing_position_sizing_owner",
        "impact_scope": "common_runtime",
        "venue_scope_authority": (
            "common_or_all_active_venues" if venue_scope_ready else "incomplete"
        ),
        "condition_feasibility": condition_feasibility,
        "runtime_application_attribution": runtime_application_attribution,
        "metric_contract": metric_contract,
        "source_metrics": {
            "economic_decision_policy": "directional_add_or_no_add_improvement_v1",
            "coverage_gap": coverage_gap,
            "decision_accounting": decision_accounting,
            "candidate_economics": source_economics,
            "paired_runtime_candidate_economics": paired_economics,
            "selected_candidate_economics": winner,
            "diagnostic_target_hit_and_mfe_mae": {
                "runtime_promotion_guard": False,
                "reason": "legacy_target_hit_and_mfe_mae_are_diagnostic_only",
            },
            "deep_recovery_diagnostic": {
                "runtime_promotion_guard": False,
                "reason": "deep_path_is_not_joined_to_shallow_candidate_floor",
            },
        },
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "postclose_candidate_preopen_only",
        "forbidden_uses": FORBIDDEN_USES,
    }
    contract = {
        "update_mode": RUNTIME_UPDATE_MODE,
        "owner_family": FAMILY,
        "owner_stage": STAGE,
        "max_runtime_apply_count": 1,
        "runtime_apply_candidate_count": 1,
        "allowed_runtime_apply_count": int(candidate["allowed_runtime_apply"]),
        "quality_update_id": quality_update_id,
        "evidence_contract_version": EVIDENCE_CONTRACT_VERSION,
        "evidence_digest": evidence_digest,
        "cumulative_quality_window": cumulative_window,
        "post_apply_attribution_required": True,
        "runtime_effect": False,
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "target_date": target_date,
        "generated_at": generated_at,
        "family": FAMILY,
        "stage": STAGE,
        "runtime_effect": False,
        "allowed_runtime_apply": candidate["allowed_runtime_apply"],
        "decision_authority": "postclose_candidate_preopen_only",
        "forbidden_uses": FORBIDDEN_USES,
        "metric_contract": metric_contract,
        "source_quality": {
            "status": "pass" if paths else "missing_input",
            "input": [str(path) for path in paths],
            "intended_input": [str(path) for path in intended_paths],
            "daily_input": [
                str(path)
                for path in paths
                if _date_from_events_path(path) == target_date
            ],
            "clean_baseline_date": CLEAN_BASELINE_DATE,
            "source_quality_excluded_dates": excluded_dates,
        },
        "runtime_update_contract": contract,
        "replay_source_files": replay_source_files,
        "replay_engine_implementation": replay_implementation,
        "independent_exit_replay": build_replay_evidence(
            [row["independent_replay_input"] for row in decisions],
            policy_ai_enabled=policy_ai_enabled,
            cached_policy_ai_records=prior_replies,
        ),
        "calibration_candidates": [candidate],
    }


def _default_output_paths(target_date: str) -> tuple[Path, Path]:
    base = REPORT_DIR / f"{REPORT_TYPE}_{target_date}"
    return base.with_suffix(".json"), base.with_suffix(".md")


def write_outputs(
    report: dict[str, Any], *, output_json: Path, output_md: Path
) -> None:
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    candidate = (report.get("calibration_candidates") or [{}])[0]
    selected = (candidate.get("source_metrics") or {}).get(
        "selected_candidate_economics"
    )
    replay = report.get("independent_exit_replay") or {}
    lines = [
        f"# {report.get('target_date')} Scalping AVG_DOWN Recovery Calibration v2",
        "",
        f"- calibration_state: `{candidate.get('calibration_state')}`",
        f"- calibration_reason: `{candidate.get('calibration_reason')}`",
        f"- allowed_runtime_apply: `{str(candidate.get('allowed_runtime_apply')).lower()}`",
        f"- current_value: `{candidate.get('current_value')}`",
        f"- recommended_value: `{candidate.get('recommended_value')}`",
        f"- evidence_authority: `{candidate.get('evidence_authority')}`",
        f"- condition_feasibility: `{candidate.get('condition_feasibility')}`",
        f"- selected_candidate_economics: `{selected}`",
        f"- independent_exit_replay: `{replay.get('state')}`",
        f"- replay_complete_episodes: `{replay.get('complete_episode_count', 0)}` / `{replay.get('unique_episode_count', 0)}`",
        f"- replay_blockers: `{replay.get('blocker_counts', {})}`",
        f"- replay_next_action: `{replay.get('next_action')}`",
        "- independent_replay_authority: `source-only; not real fill quality or live approval`",
        "- runtime_effect: `false`",
    ]
    output_md.parent.mkdir(parents=True, exist_ok=True)
    output_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build bounded scalping AVG_DOWN economic replay candidate."
    )
    parser.add_argument("--target-date", default=datetime.now(KST).strftime("%Y-%m-%d"))
    parser.add_argument("--output-json", type=Path)
    parser.add_argument("--output-md", type=Path)
    parser.add_argument("--print-summary", action="store_true")
    parser.add_argument(
        "--policy-replay-ai",
        choices=("none", "current"),
        default="none",
        help="Source-only independent replay using the existing holding AI route; bounded calls only.",
    )
    args = parser.parse_args(argv)
    output_json, output_md = (
        (args.output_json, args.output_md)
        if args.output_json and args.output_md
        else _default_output_paths(args.target_date)
    )
    cached_records = {}
    if args.policy_replay_ai == "current":
        try:
            previous = json.loads(output_json.read_text(encoding="utf-8"))
            cached_records = {
                episode: row.get("policy_ai_replay_records", [])
                for episode, row in previous.get("independent_exit_replay", {})
                .get("episodes", {})
                .items()
                if isinstance(row, dict)
            }
        except (OSError, ValueError, AttributeError):
            pass
    report = build_report(
        args.target_date,
        policy_ai_enabled=args.policy_replay_ai == "current",
        cached_policy_ai_records=cached_records,
    )
    write_outputs(report, output_json=output_json, output_md=output_md)
    if args.print_summary:
        candidate = report["calibration_candidates"][0]
        print(
            json.dumps(
                {
                    "target_date": args.target_date,
                    "state": candidate["calibration_state"],
                    "reason": candidate["calibration_reason"],
                    "allowed_runtime_apply": candidate["allowed_runtime_apply"],
                    "current_value": candidate["current_value"],
                    "recommended_value": candidate["recommended_value"],
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
