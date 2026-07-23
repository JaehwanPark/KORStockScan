"""Build the protective AI-input baseline from clean real execution history.

The replay intentionally treats historical fields as legacy proxies.  It never
upgrades those rows to exact venue provenance and cannot create BUY, scale-in,
exit-defer, provider, threshold, price, or quantity authority.
"""

from __future__ import annotations

import argparse
import json
import re
import tempfile
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Iterator
from zoneinfo import ZoneInfo

from src.engine.automation.source_quality_clean_baseline import clean_baseline_policy
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import open_text_auto

KST = ZoneInfo("Asia/Seoul")
SCHEMA = "ai_input_quality_baseline_v1"
POLICY_VERSION = "baseline_v1"
PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"
SOURCE_AUDIT_DIR = DATA_DIR / "report" / "observation_source_quality_audit"
REPORT_DIR = DATA_DIR / "report" / "ai_input_quality_baseline"

OBSERVATION_CONTRACT = {
    "metric_role": "ai_input_source_quality_replay",
    "decision_authority": "source_quality_fail_closed_only",
    "window_policy": "clean_baseline_real_events_through_target_date",
    "sample_floor": "one_real_eligible_event_for_policy_build",
    "primary_decision_metric": "legacy_proxy_input_quality_status",
    "source_quality_gate": (
        "clean_baseline_policy_and_latest_observation_source_quality_audit"
    ),
    "forbidden_uses": [
        "exact_provenance_claim",
        "standalone_buy_hold_scale_in_or_exit_authority",
        "provider_or_model_change",
        "threshold_price_or_quantity_change",
        "broker_guard_bypass",
        "cross_venue_tuning",
        "real_execution_ev_claim",
    ],
}

STAGE_TO_DECISION_POINT = {
    "scalp_entry_action_decision_snapshot": "entry_screen",
    "ai_confirmed": "entry_screen",
    "ai_confirmed_terminal_no_budget": "entry_screen",
    "entry_ai_price_canary_applied": "entry_price",
    "entry_ai_price_canary_skip_order": "entry_price",
    "entry_price_canary_submit_block": "entry_price",
    "entry_ai_price_candle_source_block": "entry_price",
    "probe_continuation_deferred": "post_probe",
    "probe_source_quality_deferred": "post_probe",
    "probe_submitted": "post_probe",
    "probe_filled": "post_probe",
    "ai_holding_review": "holding_score",
    "scale_in_ai_authority_retry": "holding_score",
    "holding_flow_override_review": "holding_flow",
    "holding_flow_override_defer_exit": "holding_flow",
    "holding_flow_override_force_exit": "holding_flow",
    "holding_flow_override_candidate_cleared": "holding_flow",
    "overnight_decision": "overnight",
}
REAL_COHORTS = (
    "PREMARKET_KRX_LIKE",
    "KRX",
    "NXT_REGULAR_OVERLAP",
    "NXT_AFTERMARKET",
    "OVERNIGHT",
    "UNKNOWN",
)
DECISION_POINTS = (
    "entry_screen",
    "gatekeeper",
    "entry_price",
    "post_probe",
    "holding_score",
    "holding_flow",
    "overnight",
)

_BAD_QUALITY_TOKENS = {
    "blocked",
    "conflict",
    "insufficient",
    "invalid",
    "missing",
    "stale",
    "unusable",
}
_GOOD_QUALITY_TOKENS = {
    "complete",
    "fresh",
    "fresh_consistent",
    "full",
    "good",
    "usable",
}
_ROUTE_LINEAGE_STAGES = {
    "order_leg_request",
    "order_leg_sent",
    "order_leg_success",
}
_REPLAY_FIELD_KEYS = frozenset(
    {
        "ai_input_preflight_source_allowed",
        "ai_market_snapshot_broker_route",
        "ai_market_snapshot_effective_venue",
        "ai_market_snapshot_id",
        "ai_market_snapshot_market_data_route",
        "ai_market_snapshot_session_bucket",
        "ai_market_snapshot_underlying_event_venue",
        "ai_parse_fail",
        "ai_response_ms",
        "ai_result_source",
        "broker_route",
        "decision_authority",
        "dmst_stex_tp",
        "effective_dmst_stex_tp",
        "effective_venue",
        "entry_ai_price_candle_fresh",
        "entry_ai_price_response_ms",
        "entry_candle_ws_route",
        "entry_context_missing_critical",
        "entry_context_quality",
        "entry_context_stale",
        "entry_execution_broker_route",
        "holding_context_ws_route",
        "holding_score_data_quality",
        "holding_score_effective_usable",
        "market_route",
        "minute_candle_window_fresh",
        "openai_request_id",
        "openai_response_ms",
        "post_probe_direction_effective_venue",
        "post_probe_direction_market_session_bucket",
        "post_probe_direction_reason",
        "post_probe_hard_veto",
        "post_probe_live_micro_fresh",
        "post_probe_ws_tick_context_fresh",
        "pre_submit_ai_context_fresh",
        "pre_submit_ai_input_quote_stale",
        "quote_stale",
        "record_id",
        "reversal_feature_source_quality",
        "rising_missed_effective_venue",
        "rising_missed_market_session_bucket",
        "rising_missed_ws_last_route",
        "scale_in_ai_authority_input_retry_data_quality",
        "scale_in_ai_authority_input_retry_result_source",
        "scale_in_ai_authority_source_quality_state",
        "scalp_live_simulator",
        "session_bucket",
        "simulated_order",
        "stock_code",
        "tick_context_stale",
        "venue",
    }
)
_PIPELINE_STAGE_PATTERN = re.compile(
    r'"stage"\s*:\s*"('
    + "|".join(
        re.escape(stage)
        for stage in sorted(
            set(STAGE_TO_DECISION_POINT) | _ROUTE_LINEAGE_STAGES,
            key=len,
            reverse=True,
        )
    )
    + r')"'
)


def _as_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    text = str(value or "").strip().lower()
    if text in {"1", "true", "yes", "on"}:
        return True
    if text in {"0", "false", "no", "off"}:
        return False
    return None


def _as_float(value: Any) -> float | None:
    try:
        if value in (None, "", "-"):
            return None
        return float(str(value).replace(",", ""))
    except (TypeError, ValueError):
        return None


def _event_fields(event: dict[str, Any]) -> dict[str, Any]:
    fields = event.get("fields") if isinstance(event.get("fields"), dict) else {}
    merged = dict(fields)
    for key in (
        "stage",
        "stock_code",
        "stock_name",
        "emitted_at",
        "emitted_date",
        "pipeline",
        "record_id",
    ):
        if key not in merged:
            merged[key] = event.get(key)
    return merged


def _event_datetime(event: dict[str, Any]) -> datetime | None:
    raw = str(event.get("emitted_at") or event.get("timestamp") or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    return (
        parsed.replace(tzinfo=KST) if parsed.tzinfo is None else parsed.astimezone(KST)
    )


def _is_real_event(event: dict[str, Any], fields: dict[str, Any]) -> bool:
    if str(event.get("pipeline") or "").upper().startswith("SIM"):
        return False
    if _as_bool(fields.get("simulated_order")) is True:
        return False
    if _as_bool(fields.get("scalp_live_simulator")) is True:
        return False
    authority = str(fields.get("decision_authority") or "").lower()
    return "sim_observation_only" not in authority


def _explicit_cohort(
    fields: dict[str, Any],
    *,
    event_time: datetime | None,
) -> tuple[str | None, str | None]:
    session = (
        str(
            fields.get("post_probe_direction_market_session_bucket")
            or fields.get("rising_missed_market_session_bucket")
            or fields.get("ai_market_snapshot_session_bucket")
            or fields.get("session_bucket")
            or ""
        )
        .strip()
        .lower()
    )
    venue = (
        str(
            fields.get("post_probe_direction_effective_venue")
            or fields.get("rising_missed_effective_venue")
            or fields.get("ai_market_snapshot_effective_venue")
            or fields.get("effective_venue")
            or fields.get("venue")
            or ""
        )
        .strip()
        .upper()
    )
    if "premarket" in session:
        return "PREMARKET_KRX_LIKE", "explicit_session"
    if venue == "KRX":
        return "KRX", "explicit_venue"
    if venue == "NXT":
        if "aftermarket" in session or "after_market" in session:
            return "NXT_AFTERMARKET", "explicit_venue_session"
        if session and event_time is not None and event_time.hour >= 16:
            return "NXT_AFTERMARKET", "explicit_venue_session_clock"
        if any(
            token in session
            for token in ("nxt_regular", "nxt_entry", "nxt_open", "overlap")
        ):
            return "NXT_REGULAR_OVERLAP", "explicit_venue_session"
        return "UNKNOWN", "explicit_nxt_session_missing"
    if "overnight" in session:
        return "OVERNIGHT", "explicit_session"
    if venue in {"SOR", "INTEGRATED", "KRX_NXT_INTEGRATED"}:
        if "krx" in session:
            return "KRX", "legacy_route_value_normalized_by_session"
        return None, "legacy_route_value_without_session"
    return None, None


def _broker_route(fields: dict[str, Any]) -> str | None:
    value = (
        str(
            fields.get("ai_market_snapshot_broker_route")
            or fields.get("effective_dmst_stex_tp")
            or fields.get("dmst_stex_tp")
            or fields.get("entry_execution_broker_route")
            or fields.get("broker_route")
            or ""
        )
        .strip()
        .upper()
    )
    return value if value in {"KRX", "NXT", "SOR"} else None


def _market_data_route(fields: dict[str, Any]) -> str | None:
    value = (
        str(
            fields.get("ai_market_snapshot_market_data_route")
            or fields.get("rising_missed_ws_last_route")
            or fields.get("entry_candle_ws_route")
            or fields.get("holding_context_ws_route")
            or fields.get("market_route")
            or ""
        )
        .strip()
        .lower()
    )
    aliases = {
        "krx_regular": "krx_only",
        "krx_only": "krx_only",
        "nxt_regular": "nxt_only",
        "nxt_only": "nxt_only",
        "integrated": "krx_nxt_integrated",
        "sor": "krx_nxt_integrated",
        "krx_nxt_integrated": "krx_nxt_integrated",
    }
    return aliases.get(value)


def _underlying_event_venue(fields: dict[str, Any]) -> str | None:
    value = (
        str(fields.get("ai_market_snapshot_underlying_event_venue") or "")
        .strip()
        .upper()
    )
    return value if value in {"KRX", "NXT"} else None


def _quality_text(value: Any) -> str:
    return str(value or "").strip().lower().replace("-", "_")


def _quality_contains(value: Any, tokens: set[str]) -> bool:
    text = _quality_text(value)
    return any(token in text for token in tokens)


def _provider_called(fields: dict[str, Any]) -> bool:
    result_source = _quality_text(
        fields.get("ai_result_source")
        or fields.get("scale_in_ai_authority_input_retry_result_source")
    )
    response_ms = _as_float(
        fields.get("ai_response_ms")
        or fields.get("openai_response_ms")
        or fields.get("entry_ai_price_response_ms")
    )
    return bool(
        result_source in {"live", "provider", "primary", "fallback"}
        or (response_ms is not None and response_ms > 0)
        or fields.get("openai_request_id")
    )


def _legacy_proxy_quality(
    *,
    event_stage: str,
    decision_point: str,
    cohort: str,
    fields: dict[str, Any],
) -> tuple[str, list[str]]:
    """Classify only quality evidence present in historical real events."""

    blockers: list[str] = []
    partial: list[str] = []
    if cohort == "UNKNOWN":
        blockers.append("venue_lineage_unavailable")

    exact_allowed = _as_bool(fields.get("ai_input_preflight_source_allowed"))
    if exact_allowed is False:
        blockers.append("historical_exact_preflight_blocked")
    elif exact_allowed is True:
        return ("allowed", []) if not blockers else ("blocked", blockers)

    stale_flags = (
        "quote_stale",
        "pre_submit_ai_input_quote_stale",
        "tick_context_stale",
        "entry_context_stale",
    )
    if any(_as_bool(fields.get(key)) is True for key in stale_flags):
        blockers.append("legacy_stale_market_input")
    if _as_bool(fields.get("pre_submit_ai_context_fresh")) is False:
        blockers.append("legacy_stale_ai_context")

    if decision_point in {"entry_screen", "gatekeeper"}:
        entry_quality = fields.get("entry_context_quality")
        if _quality_contains(entry_quality, _BAD_QUALITY_TOKENS):
            blockers.append("entry_context_quality_blocked")
        elif entry_quality in (None, "", "-"):
            partial.append("entry_context_quality_unobserved")
        if _as_bool(fields.get("entry_context_missing_critical")) is True:
            blockers.append("entry_context_missing_critical")

    elif decision_point == "entry_price":
        if event_stage in {
            "entry_price_canary_submit_block",
            "entry_ai_price_candle_source_block",
        }:
            blockers.append("entry_price_source_guard_blocked")
        candle_fresh = _as_bool(
            fields.get("entry_ai_price_candle_fresh")
            or fields.get("minute_candle_window_fresh")
        )
        if candle_fresh is False:
            blockers.append("entry_price_candle_not_fresh")
        if candle_fresh is None:
            partial.append("entry_price_candle_freshness_unobserved")

    elif decision_point == "post_probe":
        if event_stage == "probe_source_quality_deferred":
            blockers.append("probe_source_quality_deferred")
        if _as_bool(fields.get("post_probe_hard_veto")) is True:
            partial.append("post_probe_hard_veto_not_input_quality")
        market_fresh = _as_bool(fields.get("post_probe_live_micro_fresh"))
        tick_fresh = _as_bool(fields.get("post_probe_ws_tick_context_fresh"))
        if market_fresh is False and tick_fresh is False:
            blockers.append("post_probe_fresh_direction_groups_unavailable")
        elif market_fresh is None and tick_fresh is None:
            partial.append("post_probe_source_freshness_unobserved")
        if _quality_text(fields.get("post_probe_direction_reason")) in {
            "post_probe_ai_action_not_fresh",
            "post_probe_ai_action_missing",
        }:
            partial.append("stale_ai_action_provenance_only")

    elif decision_point == "holding_score":
        if event_stage == "scale_in_ai_authority_retry":
            quality = fields.get("scale_in_ai_authority_input_retry_data_quality")
            source_state = fields.get("scale_in_ai_authority_source_quality_state")
            if _quality_contains(quality, _BAD_QUALITY_TOKENS) or _quality_contains(
                source_state, _BAD_QUALITY_TOKENS
            ):
                blockers.append("scale_in_input_quality_unusable")
        else:
            quality = fields.get("holding_score_data_quality")
            usable = _as_bool(fields.get("holding_score_effective_usable"))
            if _quality_contains(quality, _BAD_QUALITY_TOKENS) or usable is False:
                blockers.append("holding_score_input_unusable")
            elif quality in (None, "", "-"):
                partial.append("holding_score_quality_unobserved")

    elif decision_point == "holding_flow":
        candle_fresh = _as_bool(fields.get("minute_candle_window_fresh"))
        reversal_quality = fields.get("reversal_feature_source_quality")
        if candle_fresh is False:
            blockers.append("holding_flow_candle_not_fresh")
        if _quality_contains(reversal_quality, _BAD_QUALITY_TOKENS):
            blockers.append("holding_flow_market_context_unusable")
        if (
            candle_fresh is None
            and reversal_quality in (None, "", "-")
            and fields.get("ai_input_preflight_source_allowed") in (None, "", "-")
        ):
            partial.append("holding_flow_source_quality_unobserved")

    elif decision_point == "overnight":
        blockers.append("real_overnight_reconciliation_evidence_required")

    if blockers:
        return "blocked", sorted(set(blockers + partial))
    if partial:
        return "partial", sorted(set(partial))
    return "allowed", []


def _pipeline_paths(
    *,
    baseline_date: str,
    target_date: str,
    pipeline_events_dir: Path,
) -> list[Path]:
    candidates = set(pipeline_events_dir.glob("pipeline_events_*.jsonl"))
    candidates.update(pipeline_events_dir.glob("pipeline_events_*.jsonl.gz"))
    paths_by_date: dict[str, Path] = {}
    for path in sorted(candidates):
        date_token = path.name.removeprefix("pipeline_events_").split(".jsonl", 1)[0]
        if baseline_date <= date_token <= target_date:
            selected = paths_by_date.get(date_token)
            if selected is None or (selected.suffix == ".gz" and path.suffix != ".gz"):
                paths_by_date[date_token] = path
    return [paths_by_date[key] for key in sorted(paths_by_date)]


def _relevant_events(path: Path) -> Iterator[dict[str, Any]]:
    with open_text_auto(path) as handle:
        for raw_line in handle:
            match = _PIPELINE_STAGE_PATTERN.search(raw_line)
            if match is None or match.group(1) not in STAGE_TO_DECISION_POINT:
                continue
            try:
                event = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            if not isinstance(event, dict):
                continue
            stage = str(event.get("stage") or "")
            if stage in STAGE_TO_DECISION_POINT:
                yield event


def _empty_bucket() -> dict[str, Any]:
    return {
        "real_row_count": 0,
        "legacy_proxy_allowed_count": 0,
        "legacy_proxy_partial_count": 0,
        "legacy_proxy_blocked_count": 0,
        "provider_called_count": 0,
        "provider_called_while_blocked_count": 0,
        "parse_failure_count": 0,
        "venue_lineage_sources": Counter(),
        "broker_route_counts": Counter(),
        "broker_route_sources": Counter(),
        "market_data_route_counts": Counter(),
        "underlying_event_venue_counts": Counter(),
        "quality_reasons": Counter(),
        "event_stages": Counter(),
    }


def _scan_events_and_order_route_lineage(
    paths: list[Path],
    relevant_event_spool,
) -> tuple[dict[tuple[str, str], str], dict[tuple[str, str], str]]:
    """Read each source once and keep route lineage separate from AI evidence."""

    by_record: dict[tuple[str, str], set[str]] = defaultdict(set)
    by_symbol: dict[tuple[str, str], set[str]] = defaultdict(set)
    for path in paths:
        with open_text_auto(path) as handle:
            for raw_line in handle:
                match = _PIPELINE_STAGE_PATTERN.search(raw_line)
                if match is None:
                    continue
                try:
                    event = json.loads(raw_line)
                except json.JSONDecodeError:
                    continue
                if not isinstance(event, dict):
                    continue
                stage = str(event.get("stage") or "")
                if stage in STAGE_TO_DECISION_POINT:
                    raw_fields = (
                        event.get("fields")
                        if isinstance(event.get("fields"), dict)
                        else {}
                    )
                    compact_event = {
                        key: event.get(key)
                        for key in (
                            "pipeline",
                            "stage",
                            "stock_code",
                            "stock_name",
                            "emitted_at",
                            "emitted_date",
                            "record_id",
                        )
                        if event.get(key) not in (None, "")
                    }
                    compact_event["fields"] = {
                        key: raw_fields.get(key)
                        for key in _REPLAY_FIELD_KEYS
                        if key in raw_fields
                    }
                    relevant_event_spool.write(
                        json.dumps(
                            compact_event,
                            ensure_ascii=False,
                            separators=(",", ":"),
                            default=str,
                        )
                        + "\n"
                    )
                if stage not in _ROUTE_LINEAGE_STAGES:
                    continue
                fields = _event_fields(event)
                route = _broker_route(fields)
                if route is None:
                    continue
                event_time = _event_datetime(event)
                date_value = str(event.get("emitted_date") or "") or (
                    event_time.date().isoformat() if event_time is not None else ""
                )
                record_id = str(event.get("record_id") or fields.get("record_id") or "")
                stock_code = str(
                    event.get("stock_code") or fields.get("stock_code") or ""
                )
                if date_value and record_id:
                    by_record[(date_value, record_id)].add(route)
                if date_value and stock_code:
                    by_symbol[(date_value, stock_code)].add(route)
    exact_record = {
        key: next(iter(routes)) for key, routes in by_record.items() if len(routes) == 1
    }
    unique_symbol = {
        key: next(iter(routes)) for key, routes in by_symbol.items() if len(routes) == 1
    }
    return exact_record, unique_symbol


def _load_source_audit(target_date: str, source_audit_dir: Path) -> dict[str, Any]:
    path = source_audit_dir / f"observation_source_quality_audit_{target_date}.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {
            "artifact": str(path),
            "status": "missing",
            "tuning_input_allowed": False,
        }
    except Exception as exc:
        return {
            "artifact": str(path),
            "status": "invalid",
            "tuning_input_allowed": False,
            "error": f"{type(exc).__name__}:{str(exc)[:160]}",
        }
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    return {
        "artifact": str(path),
        "status": str(payload.get("status") or "unknown"),
        "generated_at": payload.get("generated_at"),
        "event_count": summary.get("event_count"),
        "hard_blocking_contract_gap_count": summary.get(
            "hard_blocking_contract_gap_count"
        ),
        "review_warning_count": summary.get("review_warning_count"),
        "tuning_input_allowed": bool(summary.get("tuning_input_allowed", False)),
    }


def build_baseline_policy(
    *,
    target_date: str,
    pipeline_events_dir: Path = PIPELINE_EVENTS_DIR,
    source_audit_dir: Path = SOURCE_AUDIT_DIR,
    clean_policy: dict[str, Any] | None = None,
) -> dict[str, Any]:
    clean_policy = clean_policy or clean_baseline_policy()
    baseline_date = str(clean_policy.get("clean_tuning_baseline_date") or "")
    baseline_ts_raw = str(clean_policy.get("clean_tuning_baseline_ts_kst") or "")
    try:
        baseline_ts = datetime.fromisoformat(baseline_ts_raw).astimezone(KST)
    except ValueError:
        baseline_ts = None
    paths = _pipeline_paths(
        baseline_date=baseline_date,
        target_date=target_date,
        pipeline_events_dir=pipeline_events_dir,
    )
    buckets: dict[tuple[str, str], dict[str, Any]] = defaultdict(_empty_bucket)
    latest_symbol_cohort: dict[str, tuple[str, str, str]] = {}
    parse_failures = 0
    eligible_real_rows = 0
    exact_provenance_rows = 0

    with tempfile.TemporaryFile(mode="w+t", encoding="utf-8") as relevant_spool:
        route_by_record, route_by_symbol = _scan_events_and_order_route_lineage(
            paths,
            relevant_spool,
        )
        relevant_spool.seek(0)
        for raw_line in relevant_spool:
            try:
                event = json.loads(raw_line)
            except json.JSONDecodeError:
                continue
            event_time = _event_datetime(event)
            if baseline_ts is not None and (
                event_time is None or event_time < baseline_ts
            ):
                continue
            fields = _event_fields(event)
            if not _is_real_event(event, fields):
                continue
            stage = str(event.get("stage") or "")
            decision_point = STAGE_TO_DECISION_POINT[stage]
            stock_code = str(event.get("stock_code") or fields.get("stock_code") or "")
            event_date = str(event.get("emitted_date") or "") or (
                event_time.date().isoformat() if event_time is not None else ""
            )
            cohort, lineage_source = _explicit_cohort(
                fields,
                event_time=event_time,
            )
            if cohort is not None and stock_code:
                latest_symbol_cohort[stock_code] = (
                    event_date,
                    cohort,
                    str(lineage_source),
                )
            elif stock_code:
                prior = latest_symbol_cohort.get(stock_code)
                if prior and prior[0] == event_date:
                    cohort = prior[1]
                    lineage_source = "same_day_symbol_lineage_proxy"
            cohort = cohort or "UNKNOWN"
            lineage_source = lineage_source or "unavailable"

            status, reasons = _legacy_proxy_quality(
                event_stage=stage,
                decision_point=decision_point,
                cohort=cohort,
                fields=fields,
            )
            bucket = buckets[(cohort, decision_point)]
            bucket["real_row_count"] += 1
            bucket[f"legacy_proxy_{status}_count"] += 1
            bucket["venue_lineage_sources"][lineage_source] += 1
            broker_route = _broker_route(fields)
            broker_route_source = "ai_event"
            if broker_route is None:
                record_id = str(event.get("record_id") or fields.get("record_id") or "")
                broker_route = route_by_record.get((event_date, record_id))
                broker_route_source = "same_record_downstream_order_resolution"
            if broker_route is None and stock_code:
                broker_route = route_by_symbol.get((event_date, stock_code))
                broker_route_source = "same_day_symbol_unique_order_route"
            if broker_route is not None:
                bucket["broker_route_counts"][broker_route] += 1
                bucket["broker_route_sources"][broker_route_source] += 1
            market_data_route = _market_data_route(fields)
            if market_data_route is not None:
                bucket["market_data_route_counts"][market_data_route] += 1
            underlying_venue = _underlying_event_venue(fields)
            if underlying_venue is not None:
                bucket["underlying_event_venue_counts"][underlying_venue] += 1
            bucket["event_stages"][stage] += 1
            bucket["quality_reasons"].update(reasons)
            called = _provider_called(fields)
            if called:
                bucket["provider_called_count"] += 1
            if called and status == "blocked":
                bucket["provider_called_while_blocked_count"] += 1
            parse_failed = _as_bool(fields.get("ai_parse_fail")) is True
            if parse_failed:
                bucket["parse_failure_count"] += 1
                parse_failures += 1
            if fields.get("ai_market_snapshot_id"):
                exact_provenance_rows += 1
            eligible_real_rows += 1

            if stage == "scalp_entry_action_decision_snapshot":
                proxy_bucket = buckets[(cohort, "gatekeeper")]
                for key in (
                    "real_row_count",
                    f"legacy_proxy_{status}_count",
                    "provider_called_count",
                    "provider_called_while_blocked_count",
                    "parse_failure_count",
                ):
                    if key == "provider_called_count" and not called:
                        continue
                    if key == "provider_called_while_blocked_count" and not (
                        called and status == "blocked"
                    ):
                        continue
                    if key == "parse_failure_count" and not parse_failed:
                        continue
                    proxy_bucket[key] += 1
                proxy_bucket["venue_lineage_sources"][lineage_source] += 1
                if broker_route is not None:
                    proxy_bucket["broker_route_counts"][broker_route] += 1
                    proxy_bucket["broker_route_sources"][broker_route_source] += 1
                if market_data_route is not None:
                    proxy_bucket["market_data_route_counts"][market_data_route] += 1
                if underlying_venue is not None:
                    proxy_bucket["underlying_event_venue_counts"][underlying_venue] += 1
                proxy_bucket["event_stages"]["scalp_entry_action_proxy"] += 1
                proxy_bucket["quality_reasons"].update(reasons)

    matrix: list[dict[str, Any]] = []
    for cohort in REAL_COHORTS:
        for decision_point in DECISION_POINTS:
            bucket = buckets[(cohort, decision_point)]
            row_count = int(bucket["real_row_count"])
            if cohort == "OVERNIGHT" or decision_point == "overnight":
                policy_state = (
                    "observed_restrictive_only"
                    if row_count
                    else "restrictive_only_no_real_reconciliation_evidence"
                )
            elif row_count == 0:
                policy_state = "unobserved_keep_runtime_fail_closed"
            else:
                policy_state = "legacy_proxy_observed_not_exact"
            matrix.append(
                {
                    "cohort": cohort,
                    "decision_point": decision_point,
                    "policy_state": policy_state,
                    "exact_provenance": False,
                    "real_row_count": row_count,
                    "legacy_proxy_allowed_count": int(
                        bucket["legacy_proxy_allowed_count"]
                    ),
                    "legacy_proxy_partial_count": int(
                        bucket["legacy_proxy_partial_count"]
                    ),
                    "legacy_proxy_blocked_count": int(
                        bucket["legacy_proxy_blocked_count"]
                    ),
                    "provider_called_count": int(bucket["provider_called_count"]),
                    "provider_called_while_blocked_count": int(
                        bucket["provider_called_while_blocked_count"]
                    ),
                    "parse_failure_count": int(bucket["parse_failure_count"]),
                    "venue_lineage_sources": dict(
                        sorted(bucket["venue_lineage_sources"].items())
                    ),
                    "broker_route_counts": dict(
                        sorted(bucket["broker_route_counts"].items())
                    ),
                    "broker_route_sources": dict(
                        sorted(bucket["broker_route_sources"].items())
                    ),
                    "market_data_route_counts": dict(
                        sorted(bucket["market_data_route_counts"].items())
                    ),
                    "underlying_event_venue_counts": dict(
                        sorted(bucket["underlying_event_venue_counts"].items())
                    ),
                    "quality_reasons": dict(bucket["quality_reasons"].most_common()),
                    "event_stages": dict(sorted(bucket["event_stages"].items())),
                }
            )

    source_audit = _load_source_audit(target_date, source_audit_dir)
    known_venue_rows = sum(
        row["real_row_count"]
        for row in matrix
        if row["cohort"] != "UNKNOWN" and row["decision_point"] != "gatekeeper"
    )
    proxy_allowed_rows = sum(
        row["legacy_proxy_allowed_count"]
        for row in matrix
        if row["decision_point"] != "gatekeeper"
    )
    proxy_partial_rows = sum(
        row["legacy_proxy_partial_count"]
        for row in matrix
        if row["decision_point"] != "gatekeeper"
    )
    proxy_blocked_rows = sum(
        row["legacy_proxy_blocked_count"]
        for row in matrix
        if row["decision_point"] != "gatekeeper"
    )
    provider_called_while_blocked = sum(
        row["provider_called_while_blocked_count"]
        for row in matrix
        if row["decision_point"] != "gatekeeper"
    )
    protective_rules = {
        "market_critical_missing": "skip_provider_and_wait_or_block_submit",
        "optional_input_missing": "preserve_null_with_missing_reason",
        "holding_score_unreconciled": "score_50_unusable_and_no_scale_in_support",
        "holding_flow_unreconciled": ("ai_cannot_defer_deterministic_exit_candidate"),
        "overnight_unreconciled": "sell_today",
        "broker_route_is_independent_dimension": (
            "never_classify_sor_as_effective_venue"
        ),
        "integrated_market_data_underlying_unknown": (
            "preserve_unknown_and_forbid_nxt_specific_authority"
        ),
        "exact_v2_promotion": ("requires_ready_venue_session_decision_point_matrix"),
    }
    readiness_blockers: list[str] = []
    if not clean_policy.get("enabled", False):
        readiness_blockers.append("clean_baseline_policy_disabled")
    if baseline_ts is None:
        readiness_blockers.append("clean_baseline_timestamp_invalid")
    if not source_audit.get("tuning_input_allowed", False):
        readiness_blockers.append("source_quality_audit_not_allowed")
    if eligible_real_rows <= 0:
        readiness_blockers.append("no_clean_baseline_real_ai_input_rows")
    if known_venue_rows <= 0:
        readiness_blockers.append("no_venue_attributed_real_ai_input_rows")
    status = "ready_baseline_v1" if not readiness_blockers else "not_ready"
    return {
        "schema": SCHEMA,
        "policy_version": POLICY_VERSION,
        "status": status,
        "generated_at": datetime.now(tz=KST).isoformat(),
        "target_date": target_date,
        "clean_tuning_baseline": {
            "date": baseline_date,
            "timestamp_kst": baseline_ts_raw,
            "policy_enabled": bool(clean_policy.get("enabled", False)),
        },
        "source_artifacts": [str(path) for path in paths],
        "source_artifact_count": len(paths),
        "source_quality_audit": source_audit,
        "eligible_real_row_count": eligible_real_rows,
        "historical_exact_provenance_row_count": exact_provenance_rows,
        "legacy_proxy_parse_failure_count": parse_failures,
        "validation_summary": {
            "venue_attributed_real_row_count": known_venue_rows,
            "legacy_proxy_allowed_count": proxy_allowed_rows,
            "legacy_proxy_partial_count": proxy_partial_rows,
            "legacy_proxy_blocked_count": proxy_blocked_rows,
            "provider_called_while_blocked_count": provider_called_while_blocked,
            "policy_finding": (
                "historical_defective_input_provider_calls_observed"
                if provider_called_while_blocked
                else "no_historical_defective_input_provider_call_observed"
            ),
        },
        "readiness_blockers": readiness_blockers,
        "runtime_effect": "protective_fail_closed_only",
        "allowed_runtime_apply": status == "ready_baseline_v1",
        "can_open_order_authority": False,
        "can_relax_threshold": False,
        "can_change_provider": False,
        "protective_rules": protective_rules,
        "venue_decision_matrix": matrix,
        "observation_contract": OBSERVATION_CONTRACT,
    }


def write_baseline_policy(
    payload: dict[str, Any],
    *,
    output_dir: Path = REPORT_DIR,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    target_date = str(payload.get("target_date") or "").strip()
    path = output_dir / f"ai_input_quality_baseline_{target_date}.json"
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return path


def _parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build protective AI input quality baseline from real events."
    )
    parser.add_argument("--target-date", required=True)
    parser.add_argument("--output-dir", type=Path, default=REPORT_DIR)
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = _parse_args(argv)
    payload = build_baseline_policy(target_date=args.target_date)
    path = write_baseline_policy(payload, output_dir=args.output_dir)
    print(
        json.dumps(
            {
                "artifact": str(path),
                "status": payload["status"],
                "eligible_real_row_count": payload["eligible_real_row_count"],
                "readiness_blockers": payload["readiness_blockers"],
            },
            ensure_ascii=False,
        )
    )
    return 0 if payload["status"] == "ready_baseline_v1" else 2


if __name__ == "__main__":
    raise SystemExit(main())
