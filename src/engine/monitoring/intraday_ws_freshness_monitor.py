"""Build intraday websocket freshness diagnostics and postclose workorder directives."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from src.engine.monitoring.widget_comparison_cost import comparison_cost_contract
from src.engine.monitoring.pruned_candidate_bbo_collector import (
    EPISODE_RESET_GAP_SEC as SCANNER_PRUNE_BBO_EPISODE_RESET_GAP_SEC,
    MAX_ACTIVE_EPISODES as SCANNER_PRUNE_BBO_MAX_ACTIVE_EPISODES,
    MAX_ANCHOR_TO_SCHEDULE_DELAY_SEC as SCANNER_PRUNE_BBO_MAX_ANCHOR_DELAY_SEC,
    MAX_PENDING_SAMPLES as SCANNER_PRUNE_BBO_MAX_PENDING_SAMPLES,
    MAX_SCHEDULED_REQUESTS_PER_PROCESS_KST_DATE as SCANNER_PRUNE_BBO_MAX_DAILY_REQUESTS,
    METRIC_CONTRACT as SCANNER_PRUNE_BBO_COLLECTOR_METRIC_CONTRACT,
    MIN_REQUEST_INTERVAL_SEC as SCANNER_PRUNE_BBO_MIN_REQUEST_INTERVAL_SEC,
    SAMPLE_OFFSETS_SEC as SCANNER_PRUNE_BBO_SAMPLE_OFFSETS_SEC,
)
from src.engine.scalping.micro_reversion.symbol_master import VerifiedSymbolMaster
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import (
    existing_or_gzip_path,
    iter_jsonl,
    read_json_object_strict_receipt,
)

KST = timezone(timedelta(hours=9))
REPORT_TYPE = "intraday_ws_freshness_monitor"
REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE
WORKORDER_REPORT_DIR = DATA_DIR / "report" / "intraday_ws_freshness_workorder"
WORKORDER_DOC_DIR = (
    Path(__file__).resolve().parents[3] / "docs" / "code-improvement-workorders"
)
PIPELINE_EVENTS_DIR = DATA_DIR / "pipeline_events"
THRESHOLD_EVENTS_DIR = DATA_DIR / "threshold_cycle"
SYMBOL_MASTER_DIR = DATA_DIR / "report" / "micro_reversion_economic_reference"
DEFAULT_DASHBOARD_SNAPSHOT_PATH = (
    DATA_DIR / "runtime" / "kiwoom_ws_snapshot" / "latest.json"
)
DEFAULT_STALE_SEC = 30.0
INCREMENTAL_STATE_SCHEMA_VERSION = "intraday_ws_freshness_incremental_v10"
SCANNER_BBO_MAX_QUOTE_AGE_MS = 1_000.0
SCANNER_BBO_GROSS_TARGET_PCT = 1.30
SCANNER_BBO_ADVERSE_STOP_PCT = -0.70
SCANNER_BBO_HORIZON_SEC = 20 * 60
SCANNER_BBO_TIMEOUT_MAX_LAG_SEC = 5.0
SCANNER_BBO_JOIN_COVERAGE_FLOOR_PCT = 95.0
SCANNER_PRUNE_BBO_MAX_SCHEDULE_LAG_SEC = 2.0
SCANNER_PRUNE_BBO_RESOLVED_FLOOR = 20
SCANNER_PRUNE_BBO_RIGHT_CENSORED_MAX_PCT = 20.0
SCANNER_PRUNE_BBO_SCHEDULED_STATUSES = frozenset(
    {
        "new_episode_scheduled",
        "existing_episode_reused",
        "completed_episode_reused",
    }
)
SCANNER_HOTSET_CAPACITY_VALUES = (1, 2, 4, 6, 8, 12, 16)
SCANNER_HOTSET_GROSS_TARGET_VALUES = (0.30, 0.40, 0.50, 0.70, 1.30)
SCANNER_HOTSET_ADVERSE_STOP_VALUES = (-0.30, -0.50, -0.70)
SCANNER_HOTSET_COMPARISON_RESOLVED_FLOOR = 20
SCANNER_HOTSET_COMPARISON_RIGHT_CENSORED_MAX_PCT = 20.0

FORBIDDEN_USES = [
    "EV",
    "rolling_tuning",
    "MTD_tuning",
    "cumulative_tuning",
    "live_auto_promotion",
    "runtime_apply_bridge",
    "intraday_threshold_mutation",
    "stale_submit_bypass",
    "broker_guard_bypass",
    "provider_route_change",
    "order_price_change",
    "quantity_cap_change",
    "position_cap_release",
    "bot_restart",
    "real_execution_quality_approval",
]

METRIC_CONTRACT = {
    "metric_role": "source_quality_gate",
    "decision_authority": "ws_freshness_intraday_monitor_source_only",
    "window_policy": "daily_intraday_operational",
    "sample_floor": "at_least_one_ws_snapshot_or_pipeline_event",
    "primary_decision_metric": "subscription_stale_rate_pct",
    "source_quality_gate": "separate_subscription_stale_from_trade_tick_quiet_before_postclose_workorder",
    "forbidden_uses": FORBIDDEN_USES,
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "broker_order_forbidden": True,
}

DECISION_STAGE_STALE_BACKOFF_METRIC_CONTRACT = {
    "metric_role": "source_quality_diagnostic",
    "decision_authority": "instrumentation_only_no_runtime_mutation",
    "window_policy": "daily_intraday_operational_by_decision_stage",
    "sample_floor": "at_least_one_explicit_stale_backoff_event",
    "primary_decision_metric": "decision_stage_stale_backoff_count",
    "source_quality_gate": "explicit_scanner_stale_or_backoff_reason",
    "forbidden_uses": FORBIDDEN_USES,
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "broker_order_forbidden": True,
}

SCANNER_UNIQUE_FUNNEL_METRIC_CONTRACT = {
    "metric_role": "funnel_count",
    "decision_authority": "scanner_unique_lineage_source_only_no_runtime_mutation",
    "window_policy": "daily_unique_scanner_promotion_generation",
    "sample_floor": "one_valid_scanner_promotion_or_prune_lineage",
    "primary_decision_metric": "eligible_without_heavy_evaluation_count",
    "source_quality_gate": (
        "promotion_id_or_scan_generation_code_required_and_pipeline_threshold_mirrors_deduplicated"
    ),
    "forbidden_uses": FORBIDDEN_USES,
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "broker_order_forbidden": True,
}

SCANNER_EXECUTABLE_BBO_METRIC_CONTRACT = {
    "metric_role": "source_only_comparison_economics",
    "decision_authority": "scanner_funnel_executable_bbo_source_only",
    "window_policy": "daily_unique_scanner_promotion_or_prune_lineage",
    "sample_floor": (
        "verified_official_common_stock_exact_promotion_venue_session_bbo_"
        "join_coverage_pct>=95_and_one_resolved_outcome"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": (
        "exact_lineage_venue_session_fresh_executable_bbo_effective_dated_cost_"
        "contract_and_verified_official_common_stock_master"
    ),
    "forbidden_uses": [item for item in FORBIDDEN_USES if item != "EV"],
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
}

SCANNER_HOTSET_CAPACITY_PROXY_METRIC_CONTRACT = {
    "metric_role": "source_only_counterfactual_economics",
    "decision_authority": "scanner_hotset_rank_capacity_proxy_source_only",
    "window_policy": (
        "daily_first_fast_precheck_queue_rank_by_exact_promotion_venue_session"
    ),
    "sample_floor": (
        "verified_official_common_stock_exact_bbo_join_coverage_pct>=95_"
        "one_resolved_outcome_for_daily_diagnostic_only_and_20_resolved_"
        "with_right_censored_pct<=20_for_capacity_comparison"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": (
        "exact_promotion_first_queue_rank_venue_session_fresh_executable_bbo_"
        "effective_dated_cost_contract_and_verified_official_common_stock_master"
    ),
    "forbidden_uses": [
        *[item for item in FORBIDDEN_USES if item != "EV"],
        "standalone_hotset_cap_selection",
        "single_lead_live_entry_selection",
        "daily_only_live_promotion",
    ],
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
}

SCANNER_COMPARISON_COST_CONSUMER_BINDING = {
    "decision_authority": "scanner_funnel_executable_bbo_source_only",
    "source_contract_owner": "widget_comparison_cost_policy_v1",
    "binding_role": "shared_effective_dated_r0_r3_comparison_cost_input",
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
}

WS_AGE_FIELDS_MS = (
    "ws_last_0b_age_ms",
    "ws_last_0d_age_ms",
    "ws_last_0w_age_ms",
    "ws_last_0f_age_ms",
)

PROVIDER_FIELD_TOKENS = ("provider", "ai_provider", "model_provider")


def _to_float(value: Any, default: float | None = None) -> float | None:
    if value is None:
        return default
    text = str(value).strip().replace(",", "").replace("+", "")
    if text.lower() in {
        "",
        "-",
        "none",
        "null",
        "nan",
        "unknown",
        "not_available_realtime_type_age_ms",
        "not_available",
    }:
        return default
    try:
        return float(text)
    except (TypeError, ValueError):
        return default


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _listish(value: Any) -> list[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("[") and text.endswith("]"):
            try:
                parsed = json.loads(text)
            except Exception:
                try:
                    parsed = ast.literal_eval(text)
                except Exception:
                    parsed = None
            if isinstance(parsed, list):
                return parsed
    return []


def _dictish(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        text = value.strip()
        if text.startswith("{") and text.endswith("}"):
            try:
                parsed = json.loads(text)
            except Exception:
                try:
                    parsed = ast.literal_eval(text)
                except Exception:
                    parsed = None
            if isinstance(parsed, dict):
                return parsed
    return {}


def _flatten_event(row: dict[str, Any]) -> dict[str, Any]:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    merged = dict(row)
    merged.update(fields)
    return merged


def _iter_jsonl_rows(path: Path) -> Iterable[dict[str, Any]]:
    actual_path = existing_or_gzip_path(path)
    if not actual_path.exists():
        return
    yield from iter_jsonl(actual_path)


def _source_identity(path: Path) -> dict[str, Any]:
    actual_path = existing_or_gzip_path(path)
    if not actual_path.exists():
        return {
            "path": str(actual_path),
            "exists": False,
            "cacheable": False,
            "device": None,
            "inode": None,
            "size_bytes": 0,
        }
    stat = actual_path.stat()
    return {
        "path": str(actual_path),
        "exists": True,
        "cacheable": actual_path.suffix != ".gz",
        "device": int(stat.st_dev),
        "inode": int(stat.st_ino),
        "size_bytes": int(stat.st_size),
    }


def _iter_plain_jsonl_from_offset(
    path: Path,
    *,
    offset: int,
) -> tuple[Iterable[dict[str, Any]], dict[str, int]]:
    progress = {"offset": max(0, int(offset)), "invalid_json_line_count": 0}

    def _rows() -> Iterable[dict[str, Any]]:
        if not path.exists():
            return
        with path.open("rb") as handle:
            handle.seek(progress["offset"])
            while True:
                line_offset = handle.tell()
                raw_line = handle.readline()
                if not raw_line:
                    break
                if not raw_line.endswith(b"\n"):
                    handle.seek(line_offset)
                    break
                progress["offset"] = handle.tell()
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    progress["invalid_json_line_count"] += 1
                    continue
                if isinstance(payload, dict):
                    yield payload

    return _rows(), progress


def _counter_from_mapping(value: Any) -> Counter:
    if not isinstance(value, dict):
        return Counter()
    return Counter({str(key): int(count or 0) for key, count in value.items()})


def _nested_counters_from_mapping(value: Any) -> dict[str, Counter]:
    if not isinstance(value, dict):
        return defaultdict(Counter)
    restored: dict[str, Counter] = defaultdict(Counter)
    for key, counts in value.items():
        restored[str(key)] = _counter_from_mapping(counts)
    return restored


def _load_incremental_state(
    state_path: Path | None,
    *,
    target_date: str,
    stale_ms: float,
    source_identities: dict[str, dict[str, Any]],
) -> tuple[dict[str, Any] | None, str]:
    if state_path is None or not state_path.exists():
        return None, "state_missing"
    try:
        payload = json.loads(state_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None, "state_invalid"
    if not isinstance(payload, dict):
        return None, "state_invalid"
    if payload.get("schema_version") != INCREMENTAL_STATE_SCHEMA_VERSION:
        return None, "schema_changed"
    if str(payload.get("target_date") or "") != target_date:
        return None, "target_date_changed"
    try:
        cached_stale_ms = float(payload.get("stale_ms") or -1.0)
    except (TypeError, ValueError):
        return None, "state_invalid"
    if cached_stale_ms != float(stale_ms):
        return None, "stale_threshold_changed"
    cached_sources = payload.get("sources")
    if not isinstance(cached_sources, dict):
        return None, "source_state_missing"
    for source_name, identity in source_identities.items():
        cached = cached_sources.get(source_name)
        if not isinstance(cached, dict):
            return None, f"{source_name}_state_missing"
        if not identity.get("cacheable"):
            return None, f"{source_name}_not_cacheable"
        try:
            source_identity_matches = (
                str(cached.get("path") or "") == str(identity.get("path") or "")
                and int(cached.get("device") or -1) == int(identity.get("device") or -2)
                and int(cached.get("inode") or -1) == int(identity.get("inode") or -2)
            )
            cached_offset = int(cached.get("offset") or 0)
        except (TypeError, ValueError):
            return None, f"{source_name}_state_invalid"
        if not source_identity_matches:
            return None, f"{source_name}_replaced"
        if int(identity.get("size_bytes") or 0) < cached_offset:
            return None, f"{source_name}_truncated"
    return payload, "state_reused"


def _write_incremental_state(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.tmp")
    tmp_path.write_text(
        json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    tmp_path.replace(path)


def _read_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def _logical_symbol_master_date(path: Path) -> date | None:
    name = path.name
    for suffix in (".json.gz", ".json"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
            break
    prefix = "micro_reversion_symbol_master_"
    if not name.startswith(prefix):
        return None
    try:
        return date.fromisoformat(name[len(prefix) :])
    except ValueError:
        return None


def _select_symbol_master_path(target_date: str) -> Path | None:
    """Select the newest canonical master available on or before target date.

    Intraday reports cannot require the target day's postclose economic-chain
    artifact.  A prior artifact remains eligible only through each record's
    effective window, which is checked again during symbol lookup.
    """

    as_of = date.fromisoformat(target_date)
    candidates: dict[date, Path] = {}
    for pattern in (
        "micro_reversion_symbol_master_*.json",
        "micro_reversion_symbol_master_*.json.gz",
    ):
        for path in SYMBOL_MASTER_DIR.glob(pattern):
            source_date = _logical_symbol_master_date(path)
            if source_date is None or source_date > as_of:
                continue
            logical_path = (
                path.with_suffix("") if path.name.endswith(".json.gz") else path
            )
            candidates[source_date] = logical_path
    if not candidates:
        return None
    return candidates[max(candidates)]


def _load_verified_symbol_master(
    target_date: str, symbol_master_path: Path | None
) -> tuple[VerifiedSymbolMaster | None, dict[str, Any]]:
    selected_path = symbol_master_path or _select_symbol_master_path(target_date)
    selection_policy = (
        "explicit_path"
        if symbol_master_path is not None
        else "latest_canonical_source_date_on_or_before_target_date"
    )
    if selected_path is None:
        expected_path = (
            SYMBOL_MASTER_DIR / f"micro_reversion_symbol_master_{target_date}.json"
        )
        return None, {
            "status": "missing",
            "path": str(expected_path),
            "physical_path": None,
            "target_date": target_date,
            "source_date": None,
            "selection_policy": selection_policy,
            "artifact_sha256": None,
            "raw_artifact_sha256": None,
            "content_sha256": None,
            "symbol_count": 0,
        }
    try:
        receipt = read_json_object_strict_receipt(selected_path)
        source_date = _logical_symbol_master_date(receipt.logical_path)
        if source_date is not None and source_date > date.fromisoformat(target_date):
            raise ValueError("symbol_master_source_date_after_target_date")
        master = VerifiedSymbolMaster.from_payload(
            receipt.payload, require_canonical_owner=True
        )
    except (FileNotFoundError, OSError, TypeError, ValueError) as exc:
        return None, {
            "status": "invalid",
            "path": str(selected_path),
            "physical_path": None,
            "target_date": target_date,
            "source_date": None,
            "selection_policy": selection_policy,
            "artifact_sha256": None,
            "raw_artifact_sha256": None,
            "content_sha256": None,
            "symbol_count": 0,
            "error": f"{type(exc).__name__}:{exc}",
        }
    return master, {
        "status": "verified",
        "path": str(receipt.logical_path),
        "physical_path": str(receipt.physical_path),
        "target_date": target_date,
        "source_date": source_date.isoformat() if source_date is not None else None,
        "selection_policy": selection_policy,
        "artifact_sha256": receipt.decoded_sha256,
        "raw_artifact_sha256": receipt.raw_sha256,
        "content_sha256": receipt.payload.get("content_sha256"),
        "artifact_id": receipt.payload.get("artifact_id"),
        "symbol_count": master.symbol_count,
    }


def _event_time(row: dict[str, Any]) -> datetime | None:
    value = row.get("emitted_at") or row.get("generated_at") or row.get("timestamp")
    if not value:
        return None
    text = str(value).strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KST)
    return parsed.astimezone(KST)


def _valid_lineage_token(value: Any) -> str:
    token = str(value or "").strip()
    if not token or token.lower() in {"-", "none", "null", "unknown"}:
        return ""
    if token.startswith("not_applicable") or token.startswith("not_available"):
        return ""
    return token


def _positive_integer_metadata(value: Any) -> int | None:
    parsed = _to_float(value)
    if parsed is None or parsed <= 0 or not parsed.is_integer():
        return None
    return int(parsed)


def _nonnegative_integer_metadata(value: Any) -> int | None:
    parsed = _to_float(value)
    if parsed is None or parsed < 0 or not parsed.is_integer():
        return None
    return int(parsed)


def _scanner_venue_metadata(row: Mapping[str, Any]) -> str | None:
    venue = str(row.get("effective_venue") or row.get("venue") or "").strip().upper()
    return venue if venue in {"KRX", "PREMARKET_KRX_LIKE", "NXT"} else None


def _scanner_session_metadata(row: Mapping[str, Any]) -> str | None:
    session = _valid_lineage_token(row.get("market_session_bucket")).upper()
    return session if session and session != "UNKNOWN" else None


def _scanner_executable_bbo_observation(
    row: Mapping[str, Any],
) -> tuple[dict[str, Any] | None, str]:
    """Return one fresh executable BBO without mark/high/low fallback."""

    venue = _scanner_venue_metadata(row)
    market_session_bucket = _scanner_session_metadata(row)

    candidates = (
        (
            "market_data_effective_bbo",
            "market_data_effective_best_bid",
            "market_data_effective_best_ask",
            "market_data_effective_quote_age_ms",
            "market_data_effective_price_source",
            None,
            None,
        ),
        (
            "scanner_promotion_reanchor_bbo",
            "scanner_promotion_reanchor_best_bid",
            "scanner_promotion_reanchor_best_ask",
            "scanner_promotion_reanchor_effective_quote_age_ms",
            "scanner_promotion_reanchor_source",
            "scanner_promotion_reanchor_source_fresh",
            None,
        ),
        (
            "scanner_prune_observer_rest_bbo",
            "scanner_prune_observer_best_bid",
            "scanner_prune_observer_best_ask",
            "scanner_prune_observer_quote_age_ms",
            "scanner_prune_observer_price_source",
            "scanner_prune_observer_source_quality_pass",
            "scanner_prune_observer_observed_at",
        ),
    )
    gap_reasons: list[str] = []
    for (
        source,
        bid_key,
        ask_key,
        age_key,
        provenance_key,
        fresh_key,
        observed_at_key,
    ) in candidates:
        bid = _to_float(row.get(bid_key))
        ask = _to_float(row.get(ask_key))
        if bid is None and ask is None:
            continue
        if venue is None:
            gap_reasons.append(f"{source}:authoritative_venue_missing")
            continue
        if market_session_bucket is None:
            gap_reasons.append(f"{source}:authoritative_session_missing")
            continue
        if (
            bid is None
            or ask is None
            or not math.isfinite(bid)
            or not math.isfinite(ask)
            or bid <= 0
            or ask < bid
        ):
            gap_reasons.append(f"{source}:invalid_or_crossed_bbo")
            continue
        quote_age_ms = _to_float(row.get(age_key))
        if quote_age_ms is None or not math.isfinite(quote_age_ms) or quote_age_ms < 0:
            gap_reasons.append(f"{source}:quote_age_missing")
            continue
        if quote_age_ms > SCANNER_BBO_MAX_QUOTE_AGE_MS:
            gap_reasons.append(f"{source}:quote_stale")
            continue
        if (
            fresh_key
            and row.get(fresh_key) is not None
            and not _boolish(row.get(fresh_key))
        ):
            gap_reasons.append(f"{source}:source_not_fresh")
            continue
        source_provenance = _valid_lineage_token(row.get(provenance_key))
        if not source_provenance:
            gap_reasons.append(f"{source}:price_source_missing")
            continue
        observed_at = None
        if observed_at_key:
            try:
                observed_at = datetime.fromisoformat(
                    str(row.get(observed_at_key) or "").replace("Z", "+00:00")
                )
                if observed_at.tzinfo is None:
                    raise ValueError("observation timestamp must be timezone-aware")
                observed_at = observed_at.astimezone(KST)
            except ValueError:
                observed_at = None
        else:
            observed_at = _event_time(dict(row))
        if observed_at is None:
            gap_reasons.append(f"{source}:event_time_missing")
            continue
        observation = {
            "observed_at": observed_at.isoformat(),
            "observed_epoch": observed_at.timestamp(),
            "best_bid": bid,
            "best_ask": ask,
            "quote_age_ms": quote_age_ms,
            "source": source,
            "source_provenance": source_provenance,
            "venue": venue,
            "market_session_bucket": market_session_bucket,
        }
        if source == "scanner_prune_observer_rest_bbo":
            stock_code = str(row.get("stock_code") or row.get("code") or "").strip()[:6]
            expected_request_code = (
                stock_code
                if venue == "KRX"
                else (
                    f"{stock_code}_NX" if venue in {"NXT", "PREMARKET_KRX_LIKE"} else ""
                )
            )
            request_code = (
                str(row.get("scanner_prune_observer_request_code") or "")
                .strip()
                .upper()
            )
            response_request_code = (
                str(row.get("scanner_prune_observer_response_request_code") or "")
                .strip()
                .upper()
            )
            expected_observed_venue = (
                str(row.get("scanner_prune_observer_expected_observed_venue") or "")
                .strip()
                .upper()
            )
            route_observed_venue = "KRX" if venue == "KRX" else "NXT"
            if not _boolish(row.get("scanner_prune_observer_route_match")):
                gap_reasons.append(f"{source}:exact_request_route_mismatch")
                continue
            if (
                not expected_request_code
                or request_code != expected_request_code
                or response_request_code != expected_request_code
            ):
                gap_reasons.append(f"{source}:request_code_provenance_mismatch")
                continue
            if expected_observed_venue != route_observed_venue:
                gap_reasons.append(f"{source}:observed_venue_provenance_mismatch")
                continue
            if source_provenance != "ka10004_rest_orderbook_exact_request_code":
                gap_reasons.append(f"{source}:price_source_provenance_invalid")
                continue
            schedule_lag_sec = _to_float(
                row.get("scanner_prune_observer_schedule_lag_sec")
            )
            anchor_to_schedule_delay_sec = _to_float(
                row.get("scanner_prune_observer_anchor_to_schedule_delay_sec")
            )
            scheduled_offset_sec = _nonnegative_integer_metadata(
                row.get("scanner_prune_observer_scheduled_offset_sec")
            )
            if (
                schedule_lag_sec is None
                or not math.isfinite(schedule_lag_sec)
                or schedule_lag_sec < 0
            ):
                gap_reasons.append(f"{source}:schedule_lag_missing")
                continue
            if schedule_lag_sec > SCANNER_PRUNE_BBO_MAX_SCHEDULE_LAG_SEC:
                gap_reasons.append(f"{source}:schedule_lag_exceeded")
                continue
            if (
                anchor_to_schedule_delay_sec is None
                or not math.isfinite(anchor_to_schedule_delay_sec)
                or anchor_to_schedule_delay_sec < 0
            ):
                gap_reasons.append(f"{source}:anchor_to_schedule_delay_missing")
                continue
            if anchor_to_schedule_delay_sec > SCANNER_PRUNE_BBO_MAX_SCHEDULE_LAG_SEC:
                gap_reasons.append(f"{source}:anchor_to_schedule_delay_exceeded")
                continue
            if scheduled_offset_sec is None:
                gap_reasons.append(f"{source}:scheduled_offset_missing")
                continue
            observation["schedule_lag_sec"] = schedule_lag_sec
            observation["anchor_to_schedule_delay_sec"] = anchor_to_schedule_delay_sec
            observation["scheduled_offset_sec"] = scheduled_offset_sec
            observation["observer_anchor_generation_id"] = _valid_lineage_token(
                row.get("scanner_prune_observer_anchor_generation_id")
            )
        return observation, "pass"
    if gap_reasons:
        return None, "|".join(sorted(set(gap_reasons)))
    return None, "executable_bbo_missing"


def _append_scanner_bbo_observation(
    container: dict[str, Any], row: Mapping[str, Any]
) -> None:
    observation, gap_reason = _scanner_executable_bbo_observation(row)
    if observation is not None:
        observations = container.setdefault("bbo_observations", [])
        observation_key = (
            observation["observed_at"],
            observation["best_bid"],
            observation["best_ask"],
            observation["source"],
        )
        if not any(
            (
                item.get("observed_at"),
                item.get("best_bid"),
                item.get("best_ask"),
                item.get("source"),
            )
            == observation_key
            for item in observations
            if isinstance(item, dict)
        ):
            observations.append(observation)
        return
    gap_counts = container.setdefault("bbo_gap_reason_counts", {})
    gap_counts[gap_reason] = int(gap_counts.get(gap_reason) or 0) + 1


def _merge_immutable_scanner_metadata(
    container: dict[str, Any],
    field: str,
    value: str | int | None,
    *,
    authoritative: bool = False,
) -> None:
    if value in (None, ""):
        return
    current = container.get(field)
    if current in (None, "", "UNKNOWN"):
        container[field] = value
        return
    if current == value:
        return
    container["metadata_conflicts"] = _append_unique(
        container.get("metadata_conflicts"),
        f"{field}:{current}!={value}",
    )
    if authoritative:
        container[field] = value


def _scanner_generation_has_structural_contract_conflict(
    row: Mapping[str, Any],
) -> bool:
    return bool(
        row.get("outcome_conflict_count")
        or row.get("lineage_metadata_conflict_count")
        or row.get("ranked_count_conflict_count")
        or row.get("duplicate_rank_count")
        or row.get("out_of_range_rank_count")
    )


def _scanner_funnel_state_from_mapping(value: Any) -> dict[str, Any]:
    value = value if isinstance(value, dict) else {}
    lineages = value.get("lineages") if isinstance(value.get("lineages"), dict) else {}
    prunes = value.get("prunes") if isinstance(value.get("prunes"), dict) else {}
    runtime_receipts = (
        value.get("prune_observer_runtime_receipts")
        if isinstance(value.get("prune_observer_runtime_receipts"), dict)
        else {}
    )
    iteration_timing_receipts = (
        value.get("scanner_iteration_timing_receipts")
        if isinstance(value.get("scanner_iteration_timing_receipts"), dict)
        else {}
    )
    low_rebound_timing_receipts = (
        value.get("scanner_low_rebound_timing_receipts")
        if isinstance(value.get("scanner_low_rebound_timing_receipts"), dict)
        else {}
    )
    fingerprints = value.get("event_fingerprints")
    return {
        "lineages": {
            str(key): dict(item)
            for key, item in lineages.items()
            if isinstance(item, dict)
        },
        "prunes": {
            str(key): {
                **dict(item),
                "terminal_prune_observed": bool(
                    item.get("terminal_prune_observed", True)
                ),
            }
            for key, item in prunes.items()
            if isinstance(item, dict)
        },
        "prune_observer_runtime_receipts": {
            str(key): dict(item)
            for key, item in runtime_receipts.items()
            if isinstance(item, dict)
        },
        "scanner_iteration_timing_receipts": {
            str(key): dict(item)
            for key, item in iteration_timing_receipts.items()
            if isinstance(item, dict)
        },
        "scanner_low_rebound_timing_receipts": {
            str(key): dict(item)
            for key, item in low_rebound_timing_receipts.items()
            if isinstance(item, dict)
        },
        "event_fingerprints": (
            list(fingerprints) if isinstance(fingerprints, list) else []
        ),
        "relevant_raw_event_count": int(value.get("relevant_raw_event_count") or 0),
        "duplicate_mirror_event_count": int(
            value.get("duplicate_mirror_event_count") or 0
        ),
        "missing_lineage_event_count": int(
            value.get("missing_lineage_event_count") or 0
        ),
    }


def _append_unique(values: Any, value: Any) -> list[str]:
    items = [str(item) for item in values] if isinstance(values, list) else []
    token = _valid_lineage_token(value)
    if token and token not in items:
        items.append(token)
    return items


def _scanner_funnel_event_relevant(row: dict[str, Any]) -> bool:
    stage = str(row.get("stage") or row.get("event_type") or "")
    if stage in {
        "scalping_scanner_prune_bbo_source_loaded",
        "scalping_scanner_iteration_timing",
        "scalping_scanner_low_rebound_source_observed",
        "scalping_scanner_candidate_pruned",
        "scalping_scanner_prune_bbo_schedule",
        "scalping_scanner_prune_bbo_observation",
        "scalping_scanner_candidate_promoted",
        "scalping_scanner_runtime_target_attach",
        "scalping_scanner_fast_precheck",
        "scalping_scanner_heavy_eval_completion",
        "scalping_scanner_runtime_queue_lag",
        "scalping_scanner_watch_eviction",
        "scalping_scanner_ws_backoff_watch_retained",
    }:
        return True
    if stage in {
        "ai_confirmed",
        "ai_confirmed_terminal_no_budget",
        "budget_pass",
        "latency_pass",
        "latency_block",
        "order_bundle_submitted",
        "order_bundle_failed",
    }:
        return bool(_valid_lineage_token(row.get("scanner_promotion_id")))
    return False


def _scanner_funnel_event_fingerprint(row: dict[str, Any]) -> str:
    payload = {
        "stage": str(row.get("stage") or row.get("event_type") or ""),
        "code": str(row.get("stock_code") or row.get("code") or "").strip()[:6],
        "promotion_id": _valid_lineage_token(row.get("scanner_promotion_id")),
        "record_id": _valid_lineage_token(
            row.get("runtime_record_id") or row.get("record_id")
        ),
        "scan_generation_id": _valid_lineage_token(
            row.get("scanner_scan_generation_id")
        ),
        "scan_rank": _positive_integer_metadata(row.get("scanner_scan_rank")),
        "ranked_candidate_count": _positive_integer_metadata(
            row.get("scanner_ranked_candidate_count")
        ),
        "venue": _scanner_venue_metadata(row),
        "market_session_bucket": _scanner_session_metadata(row),
        "emitted_at": str(
            row.get("emitted_at")
            or row.get("generated_at")
            or row.get("timestamp")
            or ""
        ),
        "attach_outcome": str(row.get("runtime_target_attach_outcome") or ""),
        "prune_reason": str(row.get("scanner_prune_reason") or ""),
        "prune_observer_episode_id": _valid_lineage_token(
            row.get("scanner_prune_observer_episode_id")
        ),
        "prune_observer_sample_index": _nonnegative_integer_metadata(
            row.get("scanner_prune_observer_sample_index")
        ),
        "prune_observer_scheduled_offset_sec": _to_float(
            row.get("scanner_prune_observer_scheduled_offset_sec")
        ),
        "prune_observer_process_pid": _nonnegative_integer_metadata(
            row.get("scanner_prune_observer_process_pid")
        ),
        "prune_observer_configured_epoch": _to_float(
            row.get("scanner_prune_observer_configured_epoch")
        ),
        "prune_observer_configuration_status": str(
            row.get("scanner_prune_observer_configuration_status") or ""
        ),
        "scanner_iteration_id": _valid_lineage_token(row.get("scanner_iteration_id")),
        "scanner_iteration_started_epoch": _to_float(
            row.get("scanner_iteration_started_epoch")
        ),
        "eviction_reason": str(row.get("eviction_reason") or ""),
        "fast_precheck_result": str(row.get("fast_precheck_result") or ""),
    }
    canonical = json.dumps(
        payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _update_scanner_funnel_state(
    state: dict[str, Any],
    row: dict[str, Any],
    event_class: dict[str, Any],
) -> None:
    if not _scanner_funnel_event_relevant(row):
        return
    state["relevant_raw_event_count"] += 1
    fingerprint = _scanner_funnel_event_fingerprint(row)
    fingerprint_set = state.setdefault("_fingerprint_set", set())
    if fingerprint in fingerprint_set:
        state["duplicate_mirror_event_count"] += 1
        return
    fingerprint_set.add(fingerprint)

    stage = str(row.get("stage") or row.get("event_type") or "unknown")
    if stage == "scalping_scanner_prune_bbo_source_loaded":
        process_pid = _nonnegative_integer_metadata(
            row.get("scanner_prune_observer_process_pid")
        )
        configured_epoch = _to_float(row.get("scanner_prune_observer_configured_epoch"))
        receipt_key = (
            f"{process_pid or 0}:{configured_epoch or 0.0:.6f}:"
            f"{row.get('scanner_prune_observer_configuration_status') or 'configured'}"
        )
        state.setdefault("prune_observer_runtime_receipts", {})[receipt_key] = {
            "process_pid": process_pid,
            "configured_epoch": configured_epoch,
            "configured_at": str(row.get("scanner_prune_observer_configured_at") or ""),
            "configuration_status": str(
                row.get("scanner_prune_observer_configuration_status") or "unknown"
            ),
            "configured": _boolish(row.get("scanner_prune_observer_configured")),
            "configuration_receipt_status": str(
                row.get("scanner_prune_observer_configuration_receipt_status")
                or "unknown"
            ),
            "token_present": _boolish(row.get("scanner_prune_observer_token_present")),
            "sample_offsets_sec": _listish(
                row.get("scanner_prune_observer_sample_offsets_sec")
            ),
            "episode_reset_gap_sec": _to_float(
                row.get("scanner_prune_observer_episode_reset_gap_sec")
            ),
            "max_anchor_to_schedule_delay_sec": _to_float(
                row.get("scanner_prune_observer_max_anchor_to_schedule_delay_sec")
            ),
            "max_active_episode_count": _nonnegative_integer_metadata(
                row.get("scanner_prune_observer_max_active_episode_count")
            ),
            "max_pending_sample_count": _nonnegative_integer_metadata(
                row.get("scanner_prune_observer_max_pending_sample_count")
            ),
            "max_process_daily_scheduled_request_count": (
                _nonnegative_integer_metadata(
                    row.get(
                        "scanner_prune_observer_max_process_daily_scheduled_request_count"
                    )
                )
            ),
            "min_request_interval_sec": _to_float(
                row.get("scanner_prune_observer_min_request_interval_sec")
            ),
            "market_data_request_effect": _boolish(
                row.get("scanner_prune_observer_market_data_request_effect")
            ),
            "runtime_effect": _boolish(row.get("runtime_effect")),
            "allowed_runtime_apply": _boolish(row.get("allowed_runtime_apply")),
            "actual_order_submitted": _boolish(row.get("actual_order_submitted")),
            "broker_order_forbidden": _boolish(row.get("broker_order_forbidden")),
        }
        return
    if stage == "scalping_scanner_iteration_timing":
        iteration_id = _valid_lineage_token(row.get("scanner_iteration_id"))
        if not iteration_id:
            state["missing_lineage_event_count"] += 1
            return
        state.setdefault("scanner_iteration_timing_receipts", {})[iteration_id] = {
            "iteration_id": iteration_id,
            "started_epoch": _to_float(row.get("scanner_iteration_started_epoch")),
            "completed_epoch": _to_float(row.get("scanner_iteration_completed_epoch")),
            "elapsed_sec": _to_float(row.get("scanner_iteration_elapsed_sec")),
            "configured_post_sleep_sec": _to_float(
                row.get("scanner_iteration_configured_post_sleep_sec")
            ),
            "projected_start_to_start_sec": _to_float(
                row.get("scanner_iteration_projected_start_to_start_sec")
            ),
            "observed_start_to_start_sec": _to_float(
                row.get("scanner_iteration_observed_start_to_start_sec")
            ),
            "promoted_count": _nonnegative_integer_metadata(
                row.get("scanner_iteration_promoted_count")
            ),
            "venue": _scanner_venue_metadata(row) or "UNKNOWN",
            "market_session_bucket": _scanner_session_metadata(row) or "UNKNOWN",
        }
        return
    if stage == "scalping_scanner_low_rebound_source_observed":
        observed_at = str(row.get("emitted_at") or row.get("timestamp") or "").strip()
        receipt_key = hashlib.sha256(
            json.dumps(
                {
                    "observed_at": observed_at,
                    "sampled_codes": row.get("low_rebound_sampled_codes"),
                    "passed_codes": row.get("low_rebound_passed_codes"),
                },
                ensure_ascii=True,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        ).hexdigest()
        state.setdefault("scanner_low_rebound_timing_receipts", {})[receipt_key] = {
            "observed_at": observed_at,
            "stage_elapsed_ms": _to_float(row.get("low_rebound_stage_elapsed_ms")),
            "candle_fetch_attempted_count": _nonnegative_integer_metadata(
                row.get("low_rebound_candle_fetch_attempted_count")
            ),
            "candle_fetch_elapsed_total_ms": _to_float(
                row.get("low_rebound_candle_fetch_elapsed_total_ms")
            ),
            "candle_fetch_elapsed_mean_ms": _to_float(
                row.get("low_rebound_candle_fetch_elapsed_mean_ms")
            ),
            "candle_fetch_elapsed_max_ms": _to_float(
                row.get("low_rebound_candle_fetch_elapsed_max_ms")
            ),
            "universe_count": _nonnegative_integer_metadata(
                row.get("low_rebound_universe_count")
            ),
            "passed_count": _nonnegative_integer_metadata(
                row.get("low_rebound_passed_count")
            ),
        }
        return
    code = str(row.get("stock_code") or row.get("code") or "").strip()[:6]
    promotion_id = _valid_lineage_token(row.get("scanner_promotion_id"))
    generation_id = _valid_lineage_token(row.get("scanner_scan_generation_id"))
    scan_rank = _positive_integer_metadata(row.get("scanner_scan_rank"))
    ranked_candidate_count = _positive_integer_metadata(
        row.get("scanner_ranked_candidate_count")
    )
    venue = _scanner_venue_metadata(row)
    market_session_bucket = _scanner_session_metadata(row)
    if stage in {
        "scalping_scanner_candidate_pruned",
        "scalping_scanner_prune_bbo_schedule",
        "scalping_scanner_prune_bbo_observation",
    }:
        if not generation_id or not code:
            state["missing_lineage_event_count"] += 1
            return
        prune_key = f"{generation_id}:{code}"
        reason = str(row.get("scanner_prune_reason") or "unknown")
        prune = state["prunes"].setdefault(
            prune_key,
            {
                "scan_generation_id": generation_id,
                "code": code,
                "scan_rank": scan_rank,
                "ranked_candidate_count": ranked_candidate_count,
                "reason": reason,
                "reasons": [reason],
                "source_signature": str(row.get("source_signature") or ""),
                "venue": venue or "UNKNOWN",
                "market_session_bucket": market_session_bucket or "UNKNOWN",
                "bbo_observations": [],
                "bbo_gap_reason_counts": {},
                "metadata_conflicts": [],
                "terminal_prune_observed": False,
                "prune_observer_episode_id": "",
                "prune_observer_schedule_statuses": [],
                "prune_observer_sample_event_count": 0,
                "prune_observer_terminal_sample_observed": False,
                "prune_observer_gap_reason_counts": {},
                "prune_observer_schedule_lag_values_sec": [],
                "prune_observer_anchor_to_schedule_delay_values_sec": [],
                "prune_observer_budget_snapshots": [],
            },
        )
        _merge_immutable_scanner_metadata(
            prune, "scan_rank", scan_rank, authoritative=True
        )
        _merge_immutable_scanner_metadata(
            prune,
            "ranked_candidate_count",
            ranked_candidate_count,
            authoritative=True,
        )
        _merge_immutable_scanner_metadata(prune, "venue", venue, authoritative=True)
        _merge_immutable_scanner_metadata(
            prune,
            "market_session_bucket",
            market_session_bucket,
            authoritative=True,
        )
        prune["reasons"] = _append_unique(prune.get("reasons"), reason)
        if stage == "scalping_scanner_candidate_pruned":
            prune["terminal_prune_observed"] = True
            prune["reason"] = reason
            prune["source_signature"] = str(row.get("source_signature") or "")
        observer_episode_id = _valid_lineage_token(
            row.get("scanner_prune_observer_episode_id")
        )
        _merge_immutable_scanner_metadata(
            prune,
            "prune_observer_episode_id",
            observer_episode_id,
            authoritative=stage == "scalping_scanner_prune_bbo_schedule",
        )
        schedule_status = _valid_lineage_token(
            row.get("scanner_prune_observer_schedule_status")
        )
        prune["prune_observer_schedule_statuses"] = _append_unique(
            prune.get("prune_observer_schedule_statuses"), schedule_status
        )
        if stage == "scalping_scanner_prune_bbo_schedule":
            anchor_to_schedule_delay_sec = _to_float(
                row.get("scanner_prune_observer_anchor_to_schedule_delay_sec")
            )
            if (
                anchor_to_schedule_delay_sec is not None
                and math.isfinite(anchor_to_schedule_delay_sec)
                and anchor_to_schedule_delay_sec >= 0
            ):
                prune["prune_observer_anchor_to_schedule_delay_values_sec"] = (
                    list(
                        prune.get("prune_observer_anchor_to_schedule_delay_values_sec")
                        or []
                    )
                    + [anchor_to_schedule_delay_sec]
                )[-64:]
            budget_snapshot = {
                "kst_date": str(
                    row.get("scanner_prune_observer_budget_kst_date") or ""
                ),
                "active_episode_count": _nonnegative_integer_metadata(
                    row.get("scanner_prune_observer_active_episode_count")
                ),
                "pending_sample_count": _nonnegative_integer_metadata(
                    row.get("scanner_prune_observer_pending_sample_count")
                ),
                "process_daily_scheduled_request_count": (
                    _nonnegative_integer_metadata(
                        row.get(
                            "scanner_prune_observer_process_daily_scheduled_request_count"
                        )
                    )
                ),
                "process_daily_remaining_request_count": (
                    _nonnegative_integer_metadata(
                        row.get(
                            "scanner_prune_observer_process_daily_remaining_request_count"
                        )
                    )
                ),
                "worker_alive": (
                    _boolish(row.get("scanner_prune_observer_worker_alive"))
                    if row.get("scanner_prune_observer_worker_alive") is not None
                    else None
                ),
                "worker_error_count": _nonnegative_integer_metadata(
                    row.get("scanner_prune_observer_worker_error_count")
                ),
                "receipt_emit_failure_count": _nonnegative_integer_metadata(
                    row.get("scanner_prune_observer_receipt_emit_failure_count")
                ),
                "request_gap_count": _nonnegative_integer_metadata(
                    row.get("scanner_prune_observer_request_gap_count")
                ),
                "captured_sample_count": _nonnegative_integer_metadata(
                    row.get("scanner_prune_observer_captured_sample_count")
                ),
            }
            if budget_snapshot["kst_date"] or any(
                budget_snapshot[key] is not None
                for key in (
                    "active_episode_count",
                    "pending_sample_count",
                    "process_daily_scheduled_request_count",
                    "process_daily_remaining_request_count",
                )
            ):
                prune["prune_observer_budget_snapshots"] = (
                    list(prune.get("prune_observer_budget_snapshots") or [])
                    + [budget_snapshot]
                )[-64:]
        if stage == "scalping_scanner_prune_bbo_observation":
            prune["prune_observer_sample_event_count"] = (
                int(prune.get("prune_observer_sample_event_count") or 0) + 1
            )
            prune["prune_observer_terminal_sample_observed"] = bool(
                prune.get("prune_observer_terminal_sample_observed")
                or _boolish(row.get("scanner_prune_observer_terminal_sample"))
            )
            observer_status = str(row.get("scanner_prune_observer_status") or "unknown")
            observer_schedule_lag_sec = _to_float(
                row.get("scanner_prune_observer_schedule_lag_sec")
            )
            if (
                observer_schedule_lag_sec is not None
                and math.isfinite(observer_schedule_lag_sec)
                and observer_schedule_lag_sec >= 0
            ):
                prune["prune_observer_schedule_lag_values_sec"] = (
                    list(prune.get("prune_observer_schedule_lag_values_sec") or [])
                    + [observer_schedule_lag_sec]
                )[-64:]
            if observer_status != "captured":
                observer_gap_reason = str(
                    row.get("scanner_prune_observer_gap_reason")
                    or "unknown_prune_observer_gap"
                )
                gap_counts = prune.setdefault("prune_observer_gap_reason_counts", {})
                gap_counts[observer_gap_reason] = (
                    int(gap_counts.get(observer_gap_reason) or 0) + 1
                )
        if stage == "scalping_scanner_prune_bbo_observation":
            _append_scanner_bbo_observation(prune, row)
        return
    if not promotion_id:
        state["missing_lineage_event_count"] += 1
        return

    lineage = state["lineages"].setdefault(
        promotion_id,
        {
            "promotion_id": promotion_id,
            "code": code,
            "promotion_emitted_epoch": None,
            "promotion_reason": "",
            "source_signature": "",
            "scan_generation_id": generation_id,
            "scan_rank": scan_rank,
            "ranked_candidate_count": ranked_candidate_count,
            "record_ids": [],
            "stages": {},
            "attach_outcomes": [],
            "attach_reasons": [],
            "eviction_reasons": [],
            "venue": "UNKNOWN",
            "market_session_bucket": "UNKNOWN",
            "decision_stage_stale_backoff": False,
            "runtime_queue_lag": False,
            "eligible_for_heavy_entry_eval": False,
            "first_fast_precheck_epoch": None,
            "first_fast_precheck_queue_rank": None,
            "first_fast_precheck_watching_count": None,
            "first_fast_precheck_result": "",
            "first_fast_precheck_reason": "",
            "first_heavy_eval_epoch": None,
            "first_eviction_epoch": None,
            "first_entry_realtime_epoch": None,
            "first_entry_realtime_type": "",
            "first_entry_realtime_attach_anchor_epoch": None,
            "first_entry_realtime_attach_anchor_source": "",
            "manual_control_exclusion_attach_skip": False,
            "manual_control_exclusion_terminalized": False,
            "handoff_provenance_complete": False,
            "bbo_observations": [],
            "bbo_gap_reason_counts": {},
            "metadata_conflicts": [],
        },
    )
    authoritative_metadata = stage == "scalping_scanner_candidate_promoted"
    _merge_immutable_scanner_metadata(
        lineage, "code", code, authoritative=authoritative_metadata
    )
    _merge_immutable_scanner_metadata(
        lineage,
        "scan_generation_id",
        generation_id,
        authoritative=authoritative_metadata,
    )
    _merge_immutable_scanner_metadata(
        lineage,
        "scan_rank",
        scan_rank,
        authoritative=authoritative_metadata,
    )
    _merge_immutable_scanner_metadata(
        lineage,
        "ranked_candidate_count",
        ranked_candidate_count,
        authoritative=authoritative_metadata,
    )
    # A promoted WATCHING target can legitimately remain active after the
    # market session changes.  Those downstream events describe the current
    # execution venue/session and, when they do not carry the immutable scan
    # generation envelope, must not overwrite or conflict with the original
    # promotion provenance.  Events that do carry any scan identity remain
    # subject to the strict immutable-metadata contract.
    has_scan_identity = any(
        value not in (None, "")
        for value in (generation_id, scan_rank, ranked_candidate_count)
    )
    code_identity_conflict = bool(
        code
        and lineage.get("code") not in (None, "", "UNKNOWN")
        and lineage.get("code") != code
    )
    if authoritative_metadata or has_scan_identity or code_identity_conflict:
        _merge_immutable_scanner_metadata(
            lineage, "venue", venue, authoritative=authoritative_metadata
        )
        _merge_immutable_scanner_metadata(
            lineage,
            "market_session_bucket",
            market_session_bucket,
            authoritative=authoritative_metadata,
        )
    lineage["record_ids"] = _append_unique(
        lineage.get("record_ids"), row.get("runtime_record_id") or row.get("record_id")
    )
    promotion_epoch = _to_float(row.get("scanner_promotion_emitted_epoch"))
    if promotion_epoch is not None and (
        lineage.get("promotion_emitted_epoch") is None
        or stage == "scalping_scanner_candidate_promoted"
    ):
        lineage["promotion_emitted_epoch"] = promotion_epoch
    if stage == "scalping_scanner_candidate_promoted":
        lineage["promotion_reason"] = str(row.get("scanner_promotion_reason") or "")
        lineage["source_signature"] = str(row.get("source_signature") or "")
    elif not lineage.get("promotion_reason"):
        lineage["promotion_reason"] = str(row.get("scanner_promotion_reason") or "")
    if not lineage.get("source_signature"):
        lineage["source_signature"] = str(row.get("source_signature") or "")
    stage_counts = (
        lineage.get("stages") if isinstance(lineage.get("stages"), dict) else {}
    )
    stage_counts[stage] = int(stage_counts.get(stage) or 0) + 1
    lineage["stages"] = stage_counts
    _append_scanner_bbo_observation(lineage, row)
    lineage["decision_stage_stale_backoff"] = bool(
        lineage.get("decision_stage_stale_backoff")
        or event_class.get("decision_stage_stale_backoff")
    )
    lineage["runtime_queue_lag"] = bool(
        lineage.get("runtime_queue_lag")
        or stage == "scalping_scanner_runtime_queue_lag"
    )
    lineage["eligible_for_heavy_entry_eval"] = bool(
        lineage.get("eligible_for_heavy_entry_eval")
        or str(row.get("fast_precheck_result") or "") == "eligible_for_heavy_entry_eval"
    )
    event_time = _event_time(row)
    event_epoch = event_time.timestamp() if event_time is not None else None
    if stage == "scalping_scanner_fast_precheck":
        event_epoch = _to_float(row.get("fast_precheck_seen_epoch"), event_epoch)
        existing_first_epoch = _to_float(lineage.get("first_fast_precheck_epoch"))
        if event_epoch is not None and (
            existing_first_epoch is None or event_epoch < existing_first_epoch
        ):
            lineage["first_fast_precheck_epoch"] = event_epoch
            lineage["first_fast_precheck_queue_rank"] = _positive_integer_metadata(
                row.get("scanner_queue_rank")
            ) or _positive_integer_metadata(row.get("queue_rank"))
            lineage["first_fast_precheck_watching_count"] = _positive_integer_metadata(
                row.get("scanner_watching_count")
            ) or _positive_integer_metadata(row.get("watching_count"))
            lineage["first_fast_precheck_result"] = str(
                row.get("fast_precheck_result") or ""
            )
            lineage["first_fast_precheck_reason"] = str(
                row.get("fast_precheck_reason") or ""
            )
        first_realtime_epoch = _to_float(row.get("scanner_first_entry_realtime_epoch"))
        retained_realtime_epoch = _to_float(lineage.get("first_entry_realtime_epoch"))
        if first_realtime_epoch is not None and (
            retained_realtime_epoch is None
            or first_realtime_epoch < retained_realtime_epoch
        ):
            lineage["first_entry_realtime_epoch"] = first_realtime_epoch
            lineage["first_entry_realtime_type"] = str(
                row.get("scanner_first_entry_realtime_type") or ""
            )
            lineage["first_entry_realtime_attach_anchor_epoch"] = _to_float(
                row.get("scanner_entry_realtime_attach_anchor_epoch")
            )
            lineage["first_entry_realtime_attach_anchor_source"] = str(
                row.get("scanner_entry_realtime_attach_anchor_source") or ""
            )
    elif stage == "scalping_scanner_heavy_eval_completion":
        event_epoch = _to_float(row.get("heavy_eval_completed_epoch"), event_epoch)
        existing_heavy_epoch = _to_float(lineage.get("first_heavy_eval_epoch"))
        if event_epoch is not None and (
            existing_heavy_epoch is None or event_epoch < existing_heavy_epoch
        ):
            lineage["first_heavy_eval_epoch"] = event_epoch
    elif stage == "scalping_scanner_watch_eviction":
        event_epoch = _to_float(row.get("observed_epoch"), event_epoch)
        existing_eviction_epoch = _to_float(lineage.get("first_eviction_epoch"))
        if event_epoch is not None and (
            existing_eviction_epoch is None or event_epoch < existing_eviction_epoch
        ):
            lineage["first_eviction_epoch"] = event_epoch
    if stage == "scalping_scanner_runtime_target_attach":
        outcome = str(row.get("runtime_target_attach_outcome") or "unknown")
        reason = str(row.get("runtime_target_attach_reason") or "unknown")
        lineage["attach_outcomes"] = _append_unique(
            lineage.get("attach_outcomes"), outcome
        )
        lineage["attach_reasons"] = _append_unique(
            lineage.get("attach_reasons"), reason
        )
        lineage["manual_control_exclusion_attach_skip"] = bool(
            lineage.get("manual_control_exclusion_attach_skip")
            or (
                outcome == "skipped"
                and reason == "operator_manual_control_excluded_symbol"
            )
        )
        lineage["manual_control_exclusion_terminalized"] = bool(
            lineage.get("manual_control_exclusion_terminalized")
            or _boolish(row.get("manual_control_exclusion_terminalized"))
        )
        handoff_promotion_id = _valid_lineage_token(
            row.get("scanner_runtime_handoff_promotion_id")
        )
        lineage["handoff_provenance_complete"] = bool(
            lineage.get("handoff_provenance_complete")
            or (
                outcome in {"attached", "refreshed", "db_poll_attached"}
                and handoff_promotion_id == promotion_id
                and _to_float(row.get("scanner_runtime_handoff_epoch")) is not None
                and _valid_lineage_token(row.get("scanner_runtime_instance_id"))
                and row.get("scanner_attach_provenance_version")
                == "scanner_runtime_handoff_v1"
            )
        )
    if stage == "scalping_scanner_watch_eviction":
        lineage["eviction_reasons"] = _append_unique(
            lineage.get("eviction_reasons"), row.get("eviction_reason")
        )


def _scanner_lineage_economic_cohort(lineage: Mapping[str, Any]) -> str | None:
    stages = lineage.get("stages") if isinstance(lineage.get("stages"), dict) else {}
    stage_names = set(stages)
    heavy = "scalping_scanner_heavy_eval_completion" in stage_names
    if bool(lineage.get("eligible_for_heavy_entry_eval")) and not heavy:
        return "eligible_no_heavy"
    if (
        heavy
        and bool(lineage.get("runtime_queue_lag"))
        and bool(lineage.get("decision_stage_stale_backoff"))
        and bool(lineage.get("eviction_reasons"))
    ):
        return "heavy_then_stale_queue_evict"
    return None


def _scanner_prune_economic_cohort(prune: Mapping[str, Any]) -> str | None:
    reason = str(prune.get("reason") or "")
    if reason == "reentry_cooldown_no_material_upgrade" and "MARKET_GAINER" not in str(
        prune.get("source_signature") or ""
    ):
        return "non_gainer_not_rising_repeat"
    if reason == "reentry_cooldown_no_material_upgrade":
        return "market_gainer_reentry_cooldown"
    if reason == "market_gainer_reserved_full":
        return "market_gainer_reserved_full"
    if reason == "general_slot_limit":
        return "general_slot_limit"
    return None


def _coalesce_prune_observation_episodes(
    prunes: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Collapse repeated scan generations onto one stable observation episode."""

    groups: dict[str, dict[str, Any]] = {}
    for prune in prunes:
        episode_id = _valid_lineage_token(prune.get("prune_observer_episode_id"))
        fallback_key = (
            f"unobserved:{prune.get('scan_generation_id') or ''}:"
            f"{prune.get('code') or ''}"
        )
        key = episode_id or fallback_key
        current = groups.get(key)
        if current is None:
            current = {
                **dict(prune),
                "prune_observer_episode_id": episode_id,
                "scan_generation_ids": [str(prune.get("scan_generation_id") or "")],
                "bbo_observations": [],
                "bbo_gap_reason_counts": {},
                "prune_observer_schedule_statuses": [],
                "prune_observer_gap_reason_counts": {},
                "prune_observer_sample_event_count": 0,
                "prune_observer_terminal_sample_observed": False,
                "prune_observer_schedule_lag_values_sec": [],
                "prune_observer_anchor_to_schedule_delay_values_sec": [],
                "prune_observer_budget_snapshots": [],
                "metadata_conflicts": list(prune.get("metadata_conflicts") or []),
            }
            groups[key] = current
        else:
            for field in ("code", "venue", "market_session_bucket"):
                value = prune.get(field)
                existing = current.get(field)
                if value not in (None, "", "UNKNOWN") and existing not in (
                    None,
                    "",
                    "UNKNOWN",
                    value,
                ):
                    current["metadata_conflicts"] = _append_unique(
                        current.get("metadata_conflicts"),
                        f"{field}:{existing}!={value}",
                    )
        generation_id = str(prune.get("scan_generation_id") or "")
        if generation_id and generation_id not in current["scan_generation_ids"]:
            current["scan_generation_ids"].append(generation_id)
        current["reasons"] = sorted(
            set(current.get("reasons") or []) | set(prune.get("reasons") or [])
        )
        current["prune_observer_schedule_statuses"] = sorted(
            set(current.get("prune_observer_schedule_statuses") or [])
            | set(prune.get("prune_observer_schedule_statuses") or [])
        )
        for observation in prune.get("bbo_observations") or []:
            if not isinstance(observation, dict):
                continue
            observation_key = (
                observation.get("observed_at"),
                observation.get("best_bid"),
                observation.get("best_ask"),
                observation.get("source"),
            )
            if not any(
                (
                    item.get("observed_at"),
                    item.get("best_bid"),
                    item.get("best_ask"),
                    item.get("source"),
                )
                == observation_key
                for item in current["bbo_observations"]
                if isinstance(item, dict)
            ):
                current["bbo_observations"].append(dict(observation))
        for field in ("bbo_gap_reason_counts", "prune_observer_gap_reason_counts"):
            target_counts = current[field]
            for reason, count in (prune.get(field) or {}).items():
                target_counts[str(reason)] = int(
                    target_counts.get(str(reason)) or 0
                ) + int(count or 0)
        current["prune_observer_sample_event_count"] = int(
            current.get("prune_observer_sample_event_count") or 0
        ) + int(prune.get("prune_observer_sample_event_count") or 0)
        current["prune_observer_terminal_sample_observed"] = bool(
            current.get("prune_observer_terminal_sample_observed")
            or prune.get("prune_observer_terminal_sample_observed")
        )
        current["prune_observer_schedule_lag_values_sec"] = (
            list(current.get("prune_observer_schedule_lag_values_sec") or [])
            + list(prune.get("prune_observer_schedule_lag_values_sec") or [])
        )[-640:]
        current["prune_observer_anchor_to_schedule_delay_values_sec"] = (
            list(
                current.get("prune_observer_anchor_to_schedule_delay_values_sec") or []
            )
            + list(
                prune.get("prune_observer_anchor_to_schedule_delay_values_sec") or []
            )
        )[-640:]
        current["prune_observer_budget_snapshots"] = (
            list(current.get("prune_observer_budget_snapshots") or [])
            + list(prune.get("prune_observer_budget_snapshots") or [])
        )[-640:]
    return list(groups.values())


def _nearest_rank_percentile(
    values: Iterable[float], percentile: float
) -> float | None:
    parsed_values: list[float] = []
    for value in values:
        try:
            parsed = float(value)
        except (TypeError, ValueError):
            continue
        if math.isfinite(parsed):
            parsed_values.append(parsed)
    ordered = sorted(parsed_values)
    if not ordered:
        return None
    rank = max(1, math.ceil(len(ordered) * float(percentile)))
    return ordered[min(len(ordered), rank) - 1]


def _scanner_hotset_bbo_observations(
    lineage: Mapping[str, Any],
    *,
    venue: str,
    session: str,
    trade_date: date,
) -> tuple[list[dict[str, Any]], Counter]:
    observations: list[dict[str, Any]] = []
    filter_reasons: Counter = Counter()
    for raw_observation in lineage.get("bbo_observations") or []:
        if not isinstance(raw_observation, dict):
            filter_reasons["bbo_observation_invalid_type"] += 1
            continue
        if str(raw_observation.get("venue") or "").upper() != venue:
            filter_reasons["bbo_observation_venue_mismatch_or_missing"] += 1
            continue
        if str(raw_observation.get("market_session_bucket") or "").upper() != session:
            filter_reasons["bbo_observation_session_mismatch_or_missing"] += 1
            continue
        try:
            observed_at = datetime.fromisoformat(
                str(raw_observation.get("observed_at") or "").replace("Z", "+00:00")
            )
            if observed_at.tzinfo is None:
                raise ValueError("observation timestamp must be timezone-aware")
            observed_at = observed_at.astimezone(KST)
            bid = float(raw_observation["best_bid"])
            ask = float(raw_observation["best_ask"])
        except (KeyError, TypeError, ValueError):
            filter_reasons["bbo_observation_invalid_or_missing"] += 1
            continue
        if observed_at.date() != trade_date:
            filter_reasons["bbo_observation_target_date_mismatch"] += 1
            continue
        if not math.isfinite(bid) or not math.isfinite(ask) or bid <= 0 or ask < bid:
            filter_reasons["bbo_observation_invalid_or_crossed"] += 1
            continue
        observations.append(
            {
                **raw_observation,
                "best_bid": bid,
                "best_ask": ask,
                "observed_at": observed_at.isoformat(),
                "observed_epoch": observed_at.timestamp(),
            }
        )
    observations.sort(
        key=lambda item: (
            float(item.get("observed_epoch") or 0.0),
            str(item.get("source") or ""),
        )
    )
    return observations, filter_reasons


def _scanner_hotset_sampled_first_hit(
    observations: list[dict[str, Any]],
    *,
    gross_target_pct: float,
    adverse_stop_pct: float,
    round_trip_cost_pct: float | None,
) -> dict[str, Any]:
    if not observations:
        return {
            "label": "unresolved_source_quality_blocked",
            "gross_return_pct": None,
            "cost_adjusted_return_pct": None,
            "hit_sec": None,
        }
    entry = observations[0]
    entry_epoch = float(entry["observed_epoch"])
    entry_ask = float(entry["best_ask"])
    horizon_epoch = entry_epoch + SCANNER_BBO_HORIZON_SEC
    label = "sampled_path_right_censored_no_timeout_bbo"
    exit_observation: dict[str, Any] | None = None
    for observation in observations[1:]:
        observed_epoch = float(observation["observed_epoch"])
        if observed_epoch <= entry_epoch or observed_epoch > horizon_epoch:
            continue
        move_pct = (float(observation["best_bid"]) - entry_ask) / entry_ask * 100.0
        if move_pct >= float(gross_target_pct):
            label = "sampled_gross_target_first"
            exit_observation = observation
            break
        if move_pct <= float(adverse_stop_pct):
            label = "sampled_adverse_stop_first"
            exit_observation = observation
            break
    if exit_observation is None:
        timeout_candidates = [
            observation
            for observation in observations[1:]
            if horizon_epoch
            <= float(observation["observed_epoch"])
            <= horizon_epoch + SCANNER_BBO_TIMEOUT_MAX_LAG_SEC
        ]
        if timeout_candidates:
            label = "sampled_timeout_exit"
            exit_observation = timeout_candidates[0]
    if exit_observation is None:
        return {
            "label": label,
            "gross_return_pct": None,
            "cost_adjusted_return_pct": None,
            "hit_sec": None,
        }
    gross_return_pct = (
        (float(exit_observation["best_bid"]) - entry_ask) / entry_ask * 100.0
    )
    return {
        "label": label,
        "gross_return_pct": gross_return_pct,
        "cost_adjusted_return_pct": (
            gross_return_pct - round_trip_cost_pct
            if round_trip_cost_pct is not None
            else None
        ),
        "hit_sec": max(0.0, float(exit_observation["observed_epoch"]) - entry_epoch),
    }


def _scanner_watch_pressure_summary(
    lineages: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    buckets = (
        ("1_4", 1, 4),
        ("5_8", 5, 8),
        ("9_12", 9, 12),
        ("13_16", 13, 16),
        ("17_plus", 17, 10_000),
    )
    rows: list[dict[str, Any]] = []
    lineage_list = list(lineages)
    for label, lower, upper in buckets:
        selected = [
            item
            for item in lineage_list
            if lower
            <= int(item.get("first_fast_precheck_watching_count") or 0)
            <= upper
        ]
        if not selected:
            continue
        heavy_lags: list[float] = []
        eviction_lags: list[float] = []
        for item in selected:
            promotion_epoch = _to_float(item.get("promotion_emitted_epoch"))
            heavy_epoch = _to_float(item.get("first_heavy_eval_epoch"))
            eviction_epoch = _to_float(item.get("first_eviction_epoch"))
            if (
                promotion_epoch is not None
                and heavy_epoch is not None
                and heavy_epoch >= promotion_epoch
            ):
                heavy_lags.append(heavy_epoch - promotion_epoch)
            if (
                promotion_epoch is not None
                and eviction_epoch is not None
                and eviction_epoch >= promotion_epoch
            ):
                eviction_lags.append(eviction_epoch - promotion_epoch)
        heavy_count = sum(
            "scalping_scanner_heavy_eval_completion" in (item.get("stages") or {})
            for item in selected
        )
        stale_count = sum(
            bool(item.get("decision_stage_stale_backoff")) for item in selected
        )
        eligible_count = sum(
            bool(item.get("eligible_for_heavy_entry_eval")) for item in selected
        )
        rows.append(
            {
                "watching_count_bucket": label,
                "promotion_count": len(selected),
                "eligible_for_heavy_count": eligible_count,
                "heavy_eval_reached_count": heavy_count,
                "decision_stage_stale_backoff_count": stale_count,
                "eligible_for_heavy_rate_pct": _rate_pct(eligible_count, len(selected)),
                "heavy_eval_reach_rate_pct": _rate_pct(heavy_count, len(selected)),
                "decision_stage_stale_backoff_rate_pct": _rate_pct(
                    stale_count, len(selected)
                ),
                "promotion_to_heavy_p50_sec": (
                    round(_nearest_rank_percentile(heavy_lags, 0.50), 6)
                    if heavy_lags
                    else None
                ),
                "promotion_to_heavy_p90_sec": (
                    round(_nearest_rank_percentile(heavy_lags, 0.90), 6)
                    if heavy_lags
                    else None
                ),
                "promotion_to_eviction_p50_sec": (
                    round(_nearest_rank_percentile(eviction_lags, 0.50), 6)
                    if eviction_lags
                    else None
                ),
                "observational_only_not_causal_cap_replay": True,
            }
        )
    return rows


def _scanner_hotset_capacity_counterfactual(
    lineages: Iterable[Mapping[str, Any]],
    *,
    target_date: str,
    symbol_master: VerifiedSymbolMaster | None,
    symbol_master_binding: Mapping[str, Any],
) -> dict[str, Any]:
    lineage_list = list(lineages)
    trade_date = date.fromisoformat(target_date)
    try:
        cost_contract = comparison_cost_contract(target_date)
        round_trip_cost_pct = float(cost_contract["round_trip_cost_pct"])
        cost_contract_status = "verified"
    except ValueError as exc:
        cost_contract = {
            "status": "blocked",
            "trade_date": target_date,
            "error": str(exc),
        }
        round_trip_cost_pct = None
        cost_contract_status = "blocked"

    rows: list[dict[str, Any]] = []
    rank_missing_count = 0
    source_gap_counts: Counter = Counter()
    symbol_master_status_counts: Counter = Counter()
    for lineage in lineage_list:
        queue_rank = _positive_integer_metadata(
            lineage.get("first_fast_precheck_queue_rank")
        )
        if queue_rank is None:
            rank_missing_count += 1
            continue
        code = str(lineage.get("code") or "").strip()[:6]
        venue = str(lineage.get("venue") or "UNKNOWN").upper()
        session = str(lineage.get("market_session_bucket") or "UNKNOWN").upper()
        lookup = (
            symbol_master.lookup(code, as_of=trade_date)
            if symbol_master is not None and code
            else None
        )
        symbol_master_status = (
            lookup.status.value if lookup is not None else "master_unavailable"
        )
        symbol_master_status_counts[symbol_master_status] += 1
        symbol_master_block_reason = None
        if symbol_master_binding.get("status") != "verified":
            symbol_master_block_reason = (
                "official_symbol_master_binding_missing_or_invalid"
            )
        elif lookup is None or not lookup.economic_metadata_allowed:
            symbol_master_block_reason = (
                f"official_symbol_master_{symbol_master_status}"
            )

        observations, observation_filter_reasons = _scanner_hotset_bbo_observations(
            lineage,
            venue=venue,
            session=session,
            trade_date=trade_date,
        )
        bbo_block_reason = None
        if venue not in {"KRX", "PREMARKET_KRX_LIKE", "NXT"}:
            bbo_block_reason = "authoritative_venue_missing"
        elif session in {"", "UNKNOWN"}:
            bbo_block_reason = "authoritative_session_missing"
        elif lineage.get("metadata_conflicts"):
            bbo_block_reason = "immutable_lineage_metadata_conflict"
        elif not observations:
            bbo_block_reason = (
                observation_filter_reasons.most_common(1)[0][0]
                if observation_filter_reasons
                else "fresh_executable_bbo_missing"
            )
        if bbo_block_reason:
            source_gap_counts[bbo_block_reason] += 1
        if symbol_master_block_reason:
            source_gap_counts[symbol_master_block_reason] += 1
        rows.append(
            {
                "promotion_id": str(lineage.get("promotion_id") or ""),
                "stock_code": code,
                "venue": venue,
                "market_session_bucket": session,
                "first_queue_rank": queue_rank,
                "first_watching_count": _positive_integer_metadata(
                    lineage.get("first_fast_precheck_watching_count")
                ),
                "promotion_reason": str(lineage.get("promotion_reason") or ""),
                "source_signature": str(lineage.get("source_signature") or ""),
                "symbol_master_status": symbol_master_status,
                "symbol_master_block_reason": symbol_master_block_reason,
                "bbo_join_status": "joined" if bbo_block_reason is None else "blocked",
                "bbo_join_block_reason": bbo_block_reason,
                "observations": observations,
            }
        )

    scenarios: list[dict[str, Any]] = []
    group_keys = sorted(
        {
            (row["venue"], row["market_session_bucket"])
            for row in rows
            if row["symbol_master_block_reason"] is None
        }
    )
    for venue, session in group_keys:
        group_rows = [
            row
            for row in rows
            if row["venue"] == venue and row["market_session_bucket"] == session
        ]
        for capacity in SCANNER_HOTSET_CAPACITY_VALUES:
            selected_rows = [
                row for row in group_rows if row["first_queue_rank"] <= capacity
            ]
            eligible_rows = [
                row
                for row in selected_rows
                if row["symbol_master_block_reason"] is None
            ]
            joined_rows = [
                row for row in eligible_rows if row["bbo_join_status"] == "joined"
            ]
            join_coverage_pct = _rate_pct(len(joined_rows), len(eligible_rows))
            source_quality_ready = bool(
                eligible_rows
                and cost_contract_status == "verified"
                and symbol_master_binding.get("status") == "verified"
                and join_coverage_pct >= SCANNER_BBO_JOIN_COVERAGE_FLOOR_PCT
            )
            for gross_target_pct in SCANNER_HOTSET_GROSS_TARGET_VALUES:
                for adverse_stop_pct in SCANNER_HOTSET_ADVERSE_STOP_VALUES:
                    outcomes = [
                        _scanner_hotset_sampled_first_hit(
                            row["observations"],
                            gross_target_pct=gross_target_pct,
                            adverse_stop_pct=adverse_stop_pct,
                            round_trip_cost_pct=round_trip_cost_pct,
                        )
                        for row in joined_rows
                    ]
                    path_resolved = [
                        item
                        for item in outcomes
                        if item["gross_return_pct"] is not None
                    ]
                    cost_adjusted_resolved = [
                        item
                        for item in outcomes
                        if item["cost_adjusted_return_pct"] is not None
                    ]
                    first_hit_counts = Counter(item["label"] for item in outcomes)
                    target_returns = [
                        float(item["cost_adjusted_return_pct"])
                        for item in cost_adjusted_resolved
                        if item["label"] == "sampled_gross_target_first"
                    ]
                    adverse_returns = [
                        float(item["cost_adjusted_return_pct"])
                        for item in cost_adjusted_resolved
                        if item["label"] == "sampled_adverse_stop_first"
                    ]
                    resolved_returns = [
                        float(item["cost_adjusted_return_pct"])
                        for item in cost_adjusted_resolved
                    ]
                    right_censored_count = int(
                        first_hit_counts.get(
                            "sampled_path_right_censored_no_timeout_bbo", 0
                        )
                    )
                    right_censored_rate_pct = _rate_pct(
                        right_censored_count, len(outcomes)
                    )
                    ev_pct = (
                        sum(resolved_returns) / len(resolved_returns)
                        if source_quality_ready and resolved_returns
                        else None
                    )
                    daily_diagnostic_comparison_ready = bool(
                        source_quality_ready
                        and len(cost_adjusted_resolved)
                        >= SCANNER_HOTSET_COMPARISON_RESOLVED_FLOOR
                        and right_censored_rate_pct
                        <= SCANNER_HOTSET_COMPARISON_RIGHT_CENSORED_MAX_PCT
                    )
                    status = (
                        "source_only_economics_available"
                        if ev_pct is not None
                        else (
                            "evidence_accumulating_no_resolved_executable_outcome"
                            if source_quality_ready
                            else "source_quality_blocked"
                        )
                    )
                    scenarios.append(
                        {
                            "venue": venue,
                            "market_session_bucket": session,
                            "capacity_proxy": capacity,
                            "gross_target_pct": gross_target_pct,
                            "adverse_stop_pct": adverse_stop_pct,
                            "status": status,
                            "selected_candidate_count": len(selected_rows),
                            "eligible_verified_common_stock_candidate_count": len(
                                eligible_rows
                            ),
                            "exact_bbo_joined_count": len(joined_rows),
                            "exact_bbo_join_coverage_pct": join_coverage_pct,
                            "resolved_outcome_count": len(path_resolved),
                            "cost_adjusted_resolved_outcome_count": len(
                                cost_adjusted_resolved
                            ),
                            "right_censored_count": right_censored_count,
                            "right_censored_rate_pct": right_censored_rate_pct,
                            "first_hit_counts": dict(sorted(first_hit_counts.items())),
                            "target_first_rate_pct_of_resolved": _rate_pct(
                                int(
                                    first_hit_counts.get(
                                        "sampled_gross_target_first", 0
                                    )
                                ),
                                len(path_resolved),
                            ),
                            "source_quality_adjusted_ev_pct": (
                                round(ev_pct, 8) if ev_pct is not None else None
                            ),
                            "avg_target_first_net_return_pct": (
                                round(sum(target_returns) / len(target_returns), 8)
                                if target_returns
                                else None
                            ),
                            "avg_adverse_first_net_return_pct": (
                                round(sum(adverse_returns) / len(adverse_returns), 8)
                                if adverse_returns
                                else None
                            ),
                            "worst_resolved_net_return_pct": (
                                round(min(resolved_returns), 8)
                                if resolved_returns
                                else None
                            ),
                            "source_quality_ready": source_quality_ready,
                            "daily_diagnostic_comparison_ready": (
                                daily_diagnostic_comparison_ready
                            ),
                            "daily_diagnostic_comparison_block_reasons": [
                                reason
                                for reason, blocked in (
                                    (
                                        "source_quality_not_ready",
                                        not source_quality_ready,
                                    ),
                                    (
                                        "resolved_outcome_floor_not_met",
                                        len(cost_adjusted_resolved)
                                        < SCANNER_HOTSET_COMPARISON_RESOLVED_FLOOR,
                                    ),
                                    (
                                        "right_censored_rate_above_max",
                                        right_censored_rate_pct
                                        > SCANNER_HOTSET_COMPARISON_RIGHT_CENSORED_MAX_PCT,
                                    ),
                                )
                                if blocked
                            ],
                            "round_trip_cost_pct": round_trip_cost_pct,
                            "ev_population_contract": (
                                "resolved_sampled_first_hit_or_timeout_only_"
                                "right_censored_excluded_not_zero_filled"
                            ),
                            "decision_authority": (
                                "scanner_hotset_rank_capacity_proxy_source_only"
                            ),
                            "runtime_effect": False,
                            "allowed_runtime_apply": False,
                            "actual_order_submitted": False,
                            "broker_order_forbidden": True,
                        }
                    )

    best_by_group: list[dict[str, Any]] = []
    for venue, session in group_keys:
        available = [
            row
            for row in scenarios
            if row["venue"] == venue
            and row["market_session_bucket"] == session
            and row["source_quality_adjusted_ev_pct"] is not None
        ]
        comparison_ready = [
            row for row in available if row["daily_diagnostic_comparison_ready"]
        ]
        best = max(
            comparison_ready,
            key=lambda item: float(item["source_quality_adjusted_ev_pct"]),
            default=None,
        )
        highest_daily_diagnostic = max(
            available,
            key=lambda item: float(item["source_quality_adjusted_ev_pct"]),
            default=None,
        )
        best_by_group.append(
            {
                "venue": venue,
                "market_session_bucket": session,
                "decision": (
                    "positive_daily_proxy_requires_multi_date_holdout_and_fill_review"
                    if best is not None
                    and float(best["source_quality_adjusted_ev_pct"]) > 0
                    else (
                        "no_positive_cost_adjusted_capacity_proxy"
                        if best is not None
                        else (
                            "capacity_comparison_floor_not_met"
                            if highest_daily_diagnostic is not None
                            else "source_quality_or_resolved_sample_blocked"
                        )
                    )
                ),
                "best_floor_eligible_daily_diagnostic_scenario_no_selection_authority": best,
                "highest_daily_diagnostic_scenario_no_selection_authority": (
                    highest_daily_diagnostic
                ),
            }
        )

    available_scenario_count = sum(
        row["source_quality_adjusted_ev_pct"] is not None for row in scenarios
    )
    return {
        "metric_contract": SCANNER_HOTSET_CAPACITY_PROXY_METRIC_CONTRACT,
        "status": (
            "source_only_capacity_proxy_available"
            if available_scenario_count
            else (
                "not_applicable_no_ranked_fast_precheck_lineage"
                if not rows
                else "source_quality_blocked"
            )
        ),
        "counterfactual_type": (
            "first_observed_queue_rank_capacity_proxy_not_runtime_scheduler_replay"
        ),
        "ranked_lineage_count": len(rows),
        "rank_missing_lineage_count": rank_missing_count,
        "official_symbol_master_lookup_counts": dict(
            sorted(symbol_master_status_counts.items())
        ),
        "source_gap_counts": dict(sorted(source_gap_counts.items())),
        "capacity_values": list(SCANNER_HOTSET_CAPACITY_VALUES),
        "gross_target_values": list(SCANNER_HOTSET_GROSS_TARGET_VALUES),
        "adverse_stop_values": list(SCANNER_HOTSET_ADVERSE_STOP_VALUES),
        "capacity_comparison_resolved_floor": (
            SCANNER_HOTSET_COMPARISON_RESOLVED_FLOOR
        ),
        "capacity_comparison_right_censored_max_pct": (
            SCANNER_HOTSET_COMPARISON_RIGHT_CENSORED_MAX_PCT
        ),
        "scenario_count": len(scenarios),
        "available_scenario_count": available_scenario_count,
        "best_daily_scenario_by_venue_session": best_by_group,
        "watch_pressure_observational_summary": _scanner_watch_pressure_summary(
            lineage_list
        ),
        "scenarios": scenarios,
        "comparison_cost_contract_status": cost_contract_status,
        "comparison_cost_contract": cost_contract,
        "official_symbol_master_binding": dict(symbol_master_binding),
        "limitations": [
            "capacity_proxy_filters_actual_first_queue_rank_and_does_not_rerun_admission_or_eviction",
            "sampled_scanner_stage_bbo_event_order_is_not_a_continuous_market_path",
            "right_censored_rows_are_not_normalized_to_zero_profit",
            "passive_bid_or_bid_plus_one_fill_feasibility_is_not_claimed",
            "daily_results_cannot_select_a_live_watch_cap_or_single_lead_entry",
            "cross_venue_session_ev_aggregation_is_forbidden",
        ],
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def _scanner_bbo_economic_attribution(
    lineages: list[dict[str, Any]],
    prunes: list[dict[str, Any]],
    *,
    target_date: str,
    symbol_master: VerifiedSymbolMaster | None,
    symbol_master_binding: Mapping[str, Any],
) -> dict[str, Any]:
    try:
        cost_contract = comparison_cost_contract(target_date)
        round_trip_cost_pct = float(cost_contract["round_trip_cost_pct"])
        cost_contract_status = "verified"
    except ValueError as exc:
        cost_contract = {
            "status": "blocked",
            "trade_date": target_date,
            "error": str(exc),
        }
        round_trip_cost_pct = None
        cost_contract_status = "blocked"
    trade_date = date.fromisoformat(target_date)
    candidates: list[tuple[str, str, Mapping[str, Any]]] = []
    for lineage in lineages:
        cohort = _scanner_lineage_economic_cohort(lineage)
        if cohort:
            candidates.append((cohort, str(lineage.get("promotion_id") or ""), lineage))
    for prune in _coalesce_prune_observation_episodes(prunes):
        cohort = _scanner_prune_economic_cohort(prune)
        if cohort:
            candidates.append(
                (
                    cohort,
                    str(prune.get("prune_observer_episode_id") or "")
                    or f"{prune.get('scan_generation_id') or ''}:{prune.get('code') or ''}",
                    prune,
                )
            )

    rows: list[dict[str, Any]] = []
    missing_reason_counts: Counter = Counter()
    symbol_master_status_counts: Counter = Counter()
    for cohort, lineage_key, container in candidates:
        stock_code = str(container.get("code") or "")
        venue = str(container.get("venue") or "UNKNOWN").upper()
        session = str(container.get("market_session_bucket") or "UNKNOWN").upper()
        metadata_conflicts = container.get("metadata_conflicts") or []
        symbol_lookup = (
            symbol_master.lookup(stock_code, as_of=trade_date)
            if symbol_master is not None and stock_code
            else None
        )
        symbol_master_status = (
            symbol_lookup.status.value
            if symbol_lookup is not None
            else "master_unavailable"
        )
        symbol_master_status_counts[symbol_master_status] += 1
        observations = []
        observation_filter_reasons: Counter = Counter()
        for raw_observation in container.get("bbo_observations") or []:
            if not isinstance(raw_observation, dict):
                continue
            observation_venue = str(raw_observation.get("venue") or "").upper()
            observation_session = str(
                raw_observation.get("market_session_bucket") or ""
            ).upper()
            if observation_venue != venue:
                observation_filter_reasons[
                    "bbo_observation_venue_mismatch_or_missing"
                ] += 1
                continue
            if observation_session != session:
                observation_filter_reasons[
                    "bbo_observation_session_mismatch_or_missing"
                ] += 1
                continue
            try:
                observation_at = datetime.fromisoformat(
                    str(raw_observation.get("observed_at") or "").replace("Z", "+00:00")
                )
                if observation_at.tzinfo is None:
                    raise ValueError("observation timestamp must be timezone-aware")
                observation_at = observation_at.astimezone(KST)
            except ValueError:
                observation_filter_reasons[
                    "bbo_observation_time_invalid_or_missing"
                ] += 1
                continue
            if observation_at.date() != trade_date:
                observation_filter_reasons["bbo_observation_target_date_mismatch"] += 1
                continue
            observations.append(
                {
                    **raw_observation,
                    "observed_at": observation_at.isoformat(),
                    "observed_epoch": observation_at.timestamp(),
                }
            )
        observations.sort(
            key=lambda item: (
                float(item.get("observed_epoch") or 0.0),
                str(item.get("source") or ""),
            )
        )
        prune_episode = bool(
            _valid_lineage_token(container.get("prune_observer_episode_id"))
        )
        prune_observer_selected = bool(
            prune_episode
            and (
                set(container.get("prune_observer_schedule_statuses") or [])
                & SCANNER_PRUNE_BBO_SCHEDULED_STATUSES
                or container.get("bbo_observations")
            )
        )
        if prune_episode:
            anchor_observations = [
                observation
                for observation in observations
                if observation.get("scheduled_offset_sec") == 0
            ]
            if anchor_observations:
                anchor = anchor_observations[0]
                observations = [anchor] + [
                    observation
                    for observation in observations
                    if observation is not anchor
                    and float(observation.get("observed_epoch") or 0.0)
                    > float(anchor.get("observed_epoch") or 0.0)
                ]
        symbol_master_block_reason = None
        if symbol_master_binding.get("status") != "verified":
            symbol_master_block_reason = (
                "official_symbol_master_binding_missing_or_invalid"
            )
        elif symbol_lookup is None or not symbol_lookup.economic_metadata_allowed:
            symbol_master_block_reason = (
                f"official_symbol_master_{symbol_master_status}"
            )
        bbo_join_block_reason = None
        prune_observer_health_gap_reason = None
        if prune_episode:
            budget_snapshots = [
                snapshot
                for snapshot in container.get("prune_observer_budget_snapshots") or []
                if isinstance(snapshot, dict)
            ]
            if any(
                (_to_float(snapshot.get("worker_error_count"), 0.0) or 0.0) > 0
                for snapshot in budget_snapshots
            ):
                prune_observer_health_gap_reason = (
                    "prune_observer_worker_error_observed"
                )
            elif any(
                (_to_float(snapshot.get("receipt_emit_failure_count"), 0.0) or 0.0) > 0
                for snapshot in budget_snapshots
            ):
                prune_observer_health_gap_reason = (
                    "prune_observer_receipt_emit_failure_observed"
                )
            elif any(
                snapshot.get("worker_alive") is False for snapshot in budget_snapshots
            ):
                prune_observer_health_gap_reason = (
                    "prune_observer_worker_unhealthy_observed"
                )
        if venue not in {"KRX", "PREMARKET_KRX_LIKE", "NXT"}:
            bbo_join_block_reason = "authoritative_venue_missing"
        elif session in {"", "UNKNOWN"}:
            bbo_join_block_reason = "authoritative_session_missing"
        elif metadata_conflicts:
            bbo_join_block_reason = "immutable_lineage_metadata_conflict"
        elif prune_observer_health_gap_reason:
            bbo_join_block_reason = prune_observer_health_gap_reason
        elif not observations:
            bbo_join_block_reason = (
                observation_filter_reasons.most_common(1)[0][0]
                if observation_filter_reasons
                else "fresh_executable_bbo_missing"
            )
        elif prune_episode and observations[0].get("scheduled_offset_sec") != 0:
            bbo_join_block_reason = "prune_offset_zero_executable_bbo_missing"
        if bbo_join_block_reason or symbol_master_block_reason:
            if bbo_join_block_reason:
                missing_reason_counts[bbo_join_block_reason] += 1
                for reason, count in (
                    container.get("bbo_gap_reason_counts") or {}
                ).items():
                    missing_reason_counts[str(reason)] += int(count or 0)
            if symbol_master_block_reason:
                missing_reason_counts[symbol_master_block_reason] += 1
            rows.append(
                {
                    "cohort": cohort,
                    "lineage_key": lineage_key,
                    "stock_code": stock_code,
                    "venue": venue,
                    "market_session_bucket": session,
                    "prune_observer_selected": prune_observer_selected,
                    "observation_population_role": (
                        "bounded_observer_selected_episode"
                        if prune_observer_selected
                        else "full_funnel_census_not_observer_selected"
                    ),
                    "symbol_master_status": symbol_master_status,
                    "bbo_join_status": (
                        "source_quality_blocked"
                        if bbo_join_block_reason
                        else "excluded_official_symbol_master"
                    ),
                    "bbo_join_block_reason": bbo_join_block_reason,
                    "symbol_master_block_reason": symbol_master_block_reason,
                    "primary_exclusion_reason": (
                        symbol_master_block_reason
                        if symbol_master_block_reason
                        else bbo_join_block_reason
                    ),
                    "first_hit_label": (
                        "excluded_official_symbol_master"
                        if symbol_master_block_reason
                        else "unresolved_source_quality_blocked"
                    ),
                    "gross_return_pct": None,
                    "cost_adjusted_return_pct": None,
                }
            )
            continue

        entry = observations[0]
        entry_epoch = float(entry["observed_epoch"])
        entry_ask = float(entry["best_ask"])
        horizon_epoch = entry_epoch + SCANNER_BBO_HORIZON_SEC
        first_hit_label = "sampled_path_right_censored_no_timeout_bbo"
        exit_observation: dict[str, Any] | None = None
        for observation in observations[1:]:
            observed_epoch = float(observation["observed_epoch"])
            outside_horizon = (
                int(observation.get("scheduled_offset_sec") or -1)
                > SCANNER_BBO_HORIZON_SEC
                if prune_episode
                else observed_epoch > horizon_epoch
            )
            if observed_epoch <= entry_epoch or outside_horizon:
                continue
            move_pct = (float(observation["best_bid"]) - entry_ask) / entry_ask * 100.0
            if move_pct >= SCANNER_BBO_GROSS_TARGET_PCT:
                first_hit_label = "sampled_gross_target_first"
                exit_observation = observation
                break
            if move_pct <= SCANNER_BBO_ADVERSE_STOP_PCT:
                first_hit_label = "sampled_adverse_stop_first"
                exit_observation = observation
                break
        if exit_observation is None:
            if prune_episode:
                timeout_candidates = [
                    observation
                    for observation in observations[1:]
                    if int(observation.get("scheduled_offset_sec") or -1)
                    >= SCANNER_BBO_HORIZON_SEC
                ]
            else:
                timeout_candidates = [
                    observation
                    for observation in observations[1:]
                    if horizon_epoch
                    <= float(observation["observed_epoch"])
                    <= horizon_epoch + SCANNER_BBO_TIMEOUT_MAX_LAG_SEC
                ]
            if timeout_candidates:
                first_hit_label = "sampled_timeout_exit"
                exit_observation = timeout_candidates[0]

        gross_return_pct = None
        cost_adjusted_return_pct = None
        if exit_observation is not None:
            gross_return_pct = (
                (float(exit_observation["best_bid"]) - entry_ask) / entry_ask * 100.0
            )
            cost_adjusted_return_pct = (
                gross_return_pct - round_trip_cost_pct
                if round_trip_cost_pct is not None
                else None
            )
        rows.append(
            {
                "cohort": cohort,
                "lineage_key": lineage_key,
                "stock_code": stock_code,
                "venue": venue,
                "market_session_bucket": session,
                "prune_observer_selected": prune_observer_selected,
                "observation_population_role": (
                    "bounded_observer_selected_episode"
                    if prune_observer_selected
                    else "full_funnel_census_not_observer_selected"
                ),
                "symbol_master_status": symbol_master_status,
                "bbo_join_status": "joined",
                "bbo_join_block_reason": None,
                "symbol_master_block_reason": None,
                "primary_exclusion_reason": None,
                "entry_observed_at": entry.get("observed_at"),
                "entry_best_bid": entry.get("best_bid"),
                "entry_best_ask": entry.get("best_ask"),
                "entry_quote_age_ms": entry.get("quote_age_ms"),
                "entry_bbo_source": entry.get("source"),
                "entry_observer_anchor_generation_id": entry.get(
                    "observer_anchor_generation_id"
                ),
                "observed_bbo_count": len(observations),
                "first_hit_label": first_hit_label,
                "exit_observed_at": (
                    exit_observation.get("observed_at")
                    if exit_observation is not None
                    else None
                ),
                "exit_best_bid": (
                    exit_observation.get("best_bid")
                    if exit_observation is not None
                    else None
                ),
                "gross_return_pct": (
                    round(gross_return_pct, 8) if gross_return_pct is not None else None
                ),
                "cost_adjusted_return_pct": (
                    round(cost_adjusted_return_pct, 8)
                    if cost_adjusted_return_pct is not None
                    else None
                ),
            }
        )

    candidate_count = len(rows)
    eligible_rows = [
        row for row in rows if row.get("symbol_master_block_reason") is None
    ]
    symbol_master_excluded_rows = [
        row for row in rows if row.get("symbol_master_block_reason") is not None
    ]
    joined_rows = [row for row in eligible_rows if row["bbo_join_status"] == "joined"]
    resolved_rows = [
        row for row in joined_rows if row.get("cost_adjusted_return_pct") is not None
    ]
    join_coverage_pct = _rate_pct(len(joined_rows), len(eligible_rows))

    def _economic_group_summary(
        group_rows: list[dict[str, Any]],
        *,
        dimensions: Mapping[str, str],
    ) -> dict[str, Any]:
        group_eligible_rows = [
            row for row in group_rows if row.get("symbol_master_block_reason") is None
        ]
        group_joined_rows = [
            row for row in group_eligible_rows if row.get("bbo_join_status") == "joined"
        ]
        group_resolved_rows = [
            row
            for row in group_joined_rows
            if row.get("cost_adjusted_return_pct") is not None
        ]
        group_coverage_pct = _rate_pct(len(group_joined_rows), len(group_eligible_rows))
        group_right_censored_count = sum(
            row.get("first_hit_label") == "sampled_path_right_censored_no_timeout_bbo"
            for row in group_joined_rows
        )
        group_right_censored_rate_pct = _rate_pct(
            group_right_censored_count, len(group_joined_rows)
        )
        group_source_quality_ready = bool(
            group_eligible_rows
            and cost_contract_status == "verified"
            and symbol_master_binding.get("status") == "verified"
            and group_coverage_pct >= SCANNER_BBO_JOIN_COVERAGE_FLOOR_PCT
        )
        if cost_contract_status != "verified":
            group_status = "source_quality_blocked_comparison_cost_contract"
        elif symbol_master_binding.get("status") != "verified":
            group_status = "source_quality_blocked_official_symbol_master_binding"
        elif not group_eligible_rows:
            group_status = "excluded_no_verified_official_common_stock_candidate"
        elif not group_source_quality_ready:
            group_status = (
                "source_quality_blocked_executable_bbo_join_coverage_below_floor"
            )
        elif not group_resolved_rows:
            group_status = "evidence_accumulating_no_resolved_executable_outcome"
        else:
            group_status = "source_only_economics_available"
        group_ev_pct = (
            round(
                sum(
                    float(row["cost_adjusted_return_pct"])
                    for row in group_resolved_rows
                )
                / len(group_resolved_rows),
                8,
            )
            if group_source_quality_ready and group_resolved_rows
            else None
        )
        return {
            **dimensions,
            "status": group_status,
            "source_census_count": len(group_rows),
            "eligible_verified_common_stock_candidate_count": len(group_eligible_rows),
            "official_symbol_master_excluded_count": len(group_rows)
            - len(group_eligible_rows),
            "exact_bbo_joined_count": len(group_joined_rows),
            "exact_bbo_join_coverage_pct": group_coverage_pct,
            "resolved_outcome_count": len(group_resolved_rows),
            "right_censored_count": group_right_censored_count,
            "right_censored_rate_pct_of_joined": group_right_censored_rate_pct,
            "right_censored_or_blocked_count": len(group_eligible_rows)
            - len(group_resolved_rows),
            "first_hit_counts": dict(
                sorted(
                    Counter(
                        str(row.get("first_hit_label") or "unknown")
                        for row in group_rows
                    ).items()
                )
            ),
            "source_quality_adjusted_ev_pct": group_ev_pct,
            "source_quality_ready": group_source_quality_ready,
        }

    venue_session_economics: list[dict[str, Any]] = []
    venue_session_keys = sorted(
        {
            (
                str(row.get("venue") or "UNKNOWN"),
                str(row.get("market_session_bucket") or "UNKNOWN"),
            )
            for row in rows
        }
    )
    for venue, session in venue_session_keys:
        group_rows = [
            row
            for row in rows
            if row.get("venue") == venue and row.get("market_session_bucket") == session
        ]
        venue_session_economics.append(
            _economic_group_summary(
                group_rows,
                dimensions={
                    "venue": venue,
                    "market_session_bucket": session,
                },
            )
        )
    eligible_venue_session_economics = [
        group
        for group in venue_session_economics
        if group["eligible_verified_common_stock_candidate_count"] > 0
    ]
    source_quality_ready = bool(
        eligible_rows
        and cost_contract_status == "verified"
        and symbol_master_binding.get("status") == "verified"
        and eligible_venue_session_economics
        and all(
            bool(group["source_quality_ready"])
            for group in eligible_venue_session_economics
        )
    )
    if not candidate_count:
        status = "not_applicable_no_economic_cohort"
    elif cost_contract_status != "verified":
        status = "source_quality_blocked_comparison_cost_contract"
    elif symbol_master_binding.get("status") != "verified":
        status = "source_quality_blocked_official_symbol_master_binding"
    elif not eligible_rows:
        status = "source_quality_blocked_no_verified_official_common_stock_candidate"
    elif not source_quality_ready:
        status = "source_quality_blocked_executable_bbo_join_coverage_below_floor"
    elif not resolved_rows:
        status = "evidence_accumulating_no_resolved_executable_outcome"
    else:
        status = "source_only_economics_available"
    single_group_ev = (
        eligible_venue_session_economics[0]["source_quality_adjusted_ev_pct"]
        if len(eligible_venue_session_economics) == 1
        else None
    )
    ev_pct = single_group_ev if source_quality_ready else None
    aggregate_ev_status = (
        "not_computed_cross_venue_session_forbidden"
        if len(eligible_venue_session_economics) > 1
        else (
            "available_single_venue_session"
            if ev_pct is not None
            else "unavailable_source_quality_or_outcome"
        )
    )
    first_hit_counts = Counter(
        str(row.get("first_hit_label") or "unknown") for row in rows
    )
    group_counts: Counter = Counter(
        (
            str(row.get("cohort") or "unknown"),
            str(row.get("venue") or "UNKNOWN"),
            str(row.get("market_session_bucket") or "UNKNOWN"),
        )
        for row in rows
    )
    cohort_source_quality: list[dict[str, Any]] = []
    cohort_venue_session_economics: list[dict[str, Any]] = []
    cohort_keys = sorted(
        {
            (
                str(row.get("cohort") or "unknown"),
                str(row.get("venue") or "UNKNOWN"),
                str(row.get("market_session_bucket") or "UNKNOWN"),
            )
            for row in rows
        }
    )
    for cohort, venue, session in cohort_keys:
        cohort_rows = [
            row
            for row in rows
            if row.get("cohort") == cohort
            and row.get("venue") == venue
            and row.get("market_session_bucket") == session
        ]
        cohort_eligible_rows = [
            row for row in cohort_rows if row.get("symbol_master_block_reason") is None
        ]
        cohort_joined_rows = [
            row
            for row in cohort_eligible_rows
            if row.get("bbo_join_status") == "joined"
        ]
        cohort_resolved_rows = [
            row
            for row in cohort_joined_rows
            if row.get("cost_adjusted_return_pct") is not None
        ]
        cohort_missing_reasons = Counter(
            str(row.get("primary_exclusion_reason") or "fresh_executable_bbo_missing")
            for row in cohort_eligible_rows
            if row.get("bbo_join_status") != "joined"
        )
        cohort_coverage_pct = _rate_pct(
            len(cohort_joined_rows), len(cohort_eligible_rows)
        )
        cohort_venue_session_economics.append(
            _economic_group_summary(
                cohort_rows,
                dimensions={
                    "cohort": cohort,
                    "venue": venue,
                    "market_session_bucket": session,
                },
            )
        )
        source_capture_gap = bool(
            symbol_master_binding.get("status") == "verified"
            and cost_contract_status == "verified"
            and cohort_eligible_rows
            and cohort_coverage_pct < SCANNER_BBO_JOIN_COVERAGE_FLOOR_PCT
        )
        cohort_source_quality.append(
            {
                "cohort": cohort,
                "venue": venue,
                "market_session_bucket": session,
                "source_census_count": len(cohort_rows),
                "eligible_verified_common_stock_candidate_count": len(
                    cohort_eligible_rows
                ),
                "official_symbol_master_excluded_count": len(cohort_rows)
                - len(cohort_eligible_rows),
                "exact_bbo_joined_count": len(cohort_joined_rows),
                "exact_bbo_join_coverage_pct": cohort_coverage_pct,
                "resolved_outcome_count": len(cohort_resolved_rows),
                "source_capture_gap_count": len(cohort_eligible_rows)
                - len(cohort_joined_rows),
                "source_capture_gap": source_capture_gap,
                "first_depleted_stage": (
                    "scanner_candidate_pruned_executable_bbo_source_capture"
                    if source_capture_gap and cohort == "non_gainer_not_rising_repeat"
                    else (
                        "scanner_lifecycle_event_executable_bbo_provenance"
                        if source_capture_gap
                        else None
                    )
                ),
                "missing_reason_counts": dict(sorted(cohort_missing_reasons.items())),
            }
        )
    prune_cohort_names = {
        "non_gainer_not_rising_repeat",
        "market_gainer_reentry_cooldown",
        "market_gainer_reserved_full",
        "general_slot_limit",
    }
    prune_observer_selected_rows = [
        row
        for row in rows
        if row.get("cohort") in prune_cohort_names
        and bool(row.get("prune_observer_selected"))
    ]
    prune_acceptance_groups = []
    prune_acceptance_keys = sorted(
        {
            (
                str(row.get("cohort") or "unknown"),
                str(row.get("venue") or "UNKNOWN"),
                str(row.get("market_session_bucket") or "UNKNOWN"),
            )
            for row in prune_observer_selected_rows
        }
    )
    for cohort, venue, session in prune_acceptance_keys:
        selected_group_rows = [
            row
            for row in prune_observer_selected_rows
            if row.get("cohort") == cohort
            and row.get("venue") == venue
            and row.get("market_session_bucket") == session
        ]
        selected_group = _economic_group_summary(
            selected_group_rows,
            dimensions={
                "cohort": cohort,
                "venue": venue,
                "market_session_bucket": session,
                "population_role": "bounded_observer_selected_episode",
            },
        )
        if (
            int(
                selected_group.get("eligible_verified_common_stock_candidate_count")
                or 0
            )
            > 0
        ):
            prune_acceptance_groups.append(selected_group)
    prune_acceptance_ready = bool(
        prune_acceptance_groups
        and all(
            float(group.get("exact_bbo_join_coverage_pct") or 0.0)
            >= SCANNER_BBO_JOIN_COVERAGE_FLOOR_PCT
            and int(group.get("resolved_outcome_count") or 0)
            >= SCANNER_PRUNE_BBO_RESOLVED_FLOOR
            and float(group.get("right_censored_rate_pct_of_joined") or 0.0)
            <= SCANNER_PRUNE_BBO_RIGHT_CENSORED_MAX_PCT
            for group in prune_acceptance_groups
        )
    )
    prune_observer_acceptance = {
        "status": (
            "acceptance_ready_source_only"
            if prune_acceptance_ready
            else (
                "sample_or_source_quality_floor_not_met"
                if prune_acceptance_groups
                else "not_applicable_no_verified_prune_cohort"
            )
        ),
        "acceptance_ready": prune_acceptance_ready,
        "group_count": len(prune_acceptance_groups),
        "population_role": "bounded_observer_selected_episode",
        "full_funnel_population_ev_extrapolation_allowed": False,
        "exact_bbo_join_coverage_floor_pct": SCANNER_BBO_JOIN_COVERAGE_FLOOR_PCT,
        "resolved_outcome_floor_per_group": SCANNER_PRUNE_BBO_RESOLVED_FLOOR,
        "right_censored_max_pct_per_group": (SCANNER_PRUNE_BBO_RIGHT_CENSORED_MAX_PCT),
        "groups": prune_acceptance_groups,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    source_capture_design_required = False
    source_capture_repair_required = bool(
        any(
            row["source_capture_gap"] and row.get("cohort") not in prune_cohort_names
            for row in cohort_source_quality
        )
        or any(
            str(group.get("status") or "").startswith("source_quality_blocked")
            for group in prune_acceptance_groups
        )
    )
    economic_prunes = [
        prune for prune in prunes if _scanner_prune_economic_cohort(prune) is not None
    ]
    if any(prune.get("bbo_observations") for prune in economic_prunes):
        source_capture_implementation_state = (
            "bounded_prune_rest_bbo_collector_runtime_receipts_observed"
        )
    elif any(
        prune.get("prune_observer_schedule_statuses")
        or _valid_lineage_token(prune.get("prune_observer_episode_id"))
        for prune in economic_prunes
    ):
        source_capture_implementation_state = (
            "bounded_prune_rest_bbo_collector_schedule_receipts_observed"
        )
    elif economic_prunes:
        source_capture_implementation_state = (
            "bounded_prune_rest_bbo_collector_implemented_"
            "waiting_next_pid_natural_episode_receipts"
        )
    else:
        source_capture_implementation_state = (
            "executable_bbo_join_implemented_waiting_source_quality"
        )
    return {
        "metric_contract": SCANNER_EXECUTABLE_BBO_METRIC_CONTRACT,
        "status": status,
        "economic_candidate_count": candidate_count,
        "eligible_verified_common_stock_candidate_count": len(eligible_rows),
        "official_symbol_master_excluded_count": len(symbol_master_excluded_rows),
        "exact_bbo_joined_count": len(joined_rows),
        "exact_promotion_venue_session_bbo_join_coverage_pct": join_coverage_pct,
        "join_coverage_floor_pct": SCANNER_BBO_JOIN_COVERAGE_FLOOR_PCT,
        "resolved_outcome_count": len(resolved_rows),
        "right_censored_or_blocked_count": candidate_count - len(resolved_rows),
        "eligible_right_censored_or_blocked_count": len(eligible_rows)
        - len(resolved_rows),
        "right_censored_blocked_or_excluded_count": candidate_count
        - len(resolved_rows),
        "first_hit_counts": dict(sorted(first_hit_counts.items())),
        "source_quality_adjusted_ev_pct": ev_pct,
        "aggregate_ev_status": aggregate_ev_status,
        "venue_session_economics": venue_session_economics,
        "round_trip_cost_pct": round_trip_cost_pct,
        "comparison_cost_contract_status": cost_contract_status,
        "comparison_cost_contract": cost_contract,
        "comparison_cost_consumer_binding": (SCANNER_COMPARISON_COST_CONSUMER_BINDING),
        "official_symbol_master_binding": dict(symbol_master_binding),
        "official_symbol_master_lookup_counts": dict(
            sorted(symbol_master_status_counts.items())
        ),
        "gross_target_pct": SCANNER_BBO_GROSS_TARGET_PCT,
        "adverse_stop_pct": SCANNER_BBO_ADVERSE_STOP_PCT,
        "first_hit_boundary_contract_source": (
            "rising_missed_intraday_feedback_tp1_contract"
        ),
        "horizon_sec": SCANNER_BBO_HORIZON_SEC,
        "timeout_max_lag_sec": SCANNER_BBO_TIMEOUT_MAX_LAG_SEC,
        "missing_reason_counts": dict(sorted(missing_reason_counts.items())),
        "cohort_venue_session_counts": [
            {
                "cohort": cohort,
                "venue": venue,
                "market_session_bucket": session,
                "count": count,
            }
            for (cohort, venue, session), count in sorted(group_counts.items())
        ],
        "cohort_source_quality": cohort_source_quality,
        "cohort_venue_session_economics": cohort_venue_session_economics,
        "prune_observer_selected_venue_session_economics": (prune_acceptance_groups),
        "prune_observer_acceptance": prune_observer_acceptance,
        "source_capture_design_required": source_capture_design_required,
        "source_capture_implementation_state": source_capture_implementation_state,
        "source_capture_repair_required": source_capture_repair_required,
        "first_hit_observation_contract": (
            "sampled_scanner_stage_bbo_event_order_with_prune_offset_zero_"
            "anchor_to_schedule_and_schedule_lag_le_2s_"
            "not_continuous_market_path"
        ),
        "rows": rows[:200],
        "row_export_limit": 200,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


def _scanner_unique_funnel_summary(
    state: dict[str, Any],
    *,
    target_date: str,
    symbol_master: VerifiedSymbolMaster | None,
    symbol_master_binding: Mapping[str, Any],
) -> dict[str, Any]:
    lineages = list((state.get("lineages") or {}).values())
    prune_observer_runtime_receipts = list(
        (state.get("prune_observer_runtime_receipts") or {}).values()
    )
    scanner_iteration_timing_receipts = list(
        (state.get("scanner_iteration_timing_receipts") or {}).values()
    )
    scanner_low_rebound_timing_receipts = list(
        (state.get("scanner_low_rebound_timing_receipts") or {}).values()
    )
    prunes = [
        prune
        for prune in (state.get("prunes") or {}).values()
        if bool(prune.get("terminal_prune_observed", True))
    ]
    prune_observation_episodes = _coalesce_prune_observation_episodes(prunes)
    bbo_attribution = _scanner_bbo_economic_attribution(
        lineages,
        prunes,
        target_date=target_date,
        symbol_master=symbol_master,
        symbol_master_binding=symbol_master_binding,
    )
    hotset_capacity_counterfactual = _scanner_hotset_capacity_counterfactual(
        lineages,
        target_date=target_date,
        symbol_master=symbol_master,
        symbol_master_binding=symbol_master_binding,
    )
    prune_observer_schedule_status_counts = Counter(
        status
        for episode in prune_observation_episodes
        for status in episode.get("prune_observer_schedule_statuses") or []
    )
    eligible_prune_observation_episodes = [
        episode
        for episode in prune_observation_episodes
        if _scanner_prune_economic_cohort(episode) is not None
    ]
    scheduled_prune_observation_episodes = [
        episode
        for episode in eligible_prune_observation_episodes
        if set(episode.get("prune_observer_schedule_statuses") or [])
        & {
            "new_episode_scheduled",
            "existing_episode_reused",
            "completed_episode_reused",
        }
    ]
    exact_bbo_prune_observation_episodes = [
        episode
        for episode in eligible_prune_observation_episodes
        if bool(episode.get("bbo_observations"))
    ]
    prune_observer_schedule_lag_values_sec: list[float] = []
    prune_observer_anchor_to_schedule_delay_values_sec: list[float] = []
    for episode in eligible_prune_observation_episodes:
        for value in episode.get("prune_observer_schedule_lag_values_sec") or []:
            parsed_value = _to_float(value)
            if parsed_value is not None and math.isfinite(parsed_value):
                prune_observer_schedule_lag_values_sec.append(parsed_value)
        for value in (
            episode.get("prune_observer_anchor_to_schedule_delay_values_sec") or []
        ):
            parsed_value = _to_float(value)
            if parsed_value is not None and math.isfinite(parsed_value):
                prune_observer_anchor_to_schedule_delay_values_sec.append(parsed_value)
    prune_observer_budget_snapshots = [
        snapshot
        for episode in eligible_prune_observation_episodes
        for snapshot in episode.get("prune_observer_budget_snapshots") or []
        if isinstance(snapshot, dict)
    ]
    valid_runtime_configuration_receipts = [
        row
        for row in prune_observer_runtime_receipts
        if int(row.get("process_pid") or 0) > 0
        and float(row.get("configured_epoch") or 0.0) > 0.0
        and row.get("configuration_status")
        in {"collector_created", "collector_token_refreshed"}
        and row.get("configured") is True
        and row.get("configuration_receipt_status") == "emitted"
        and row.get("token_present") is True
        and list(row.get("sample_offsets_sec") or [])
        == list(SCANNER_PRUNE_BBO_SAMPLE_OFFSETS_SEC)
        and float(row.get("episode_reset_gap_sec") or 0.0)
        == SCANNER_PRUNE_BBO_EPISODE_RESET_GAP_SEC
        and float(row.get("max_anchor_to_schedule_delay_sec") or 0.0)
        == SCANNER_PRUNE_BBO_MAX_ANCHOR_DELAY_SEC
        and int(row.get("max_active_episode_count") or 0)
        == SCANNER_PRUNE_BBO_MAX_ACTIVE_EPISODES
        and int(row.get("max_pending_sample_count") or 0)
        == SCANNER_PRUNE_BBO_MAX_PENDING_SAMPLES
        and int(row.get("max_process_daily_scheduled_request_count") or 0)
        == SCANNER_PRUNE_BBO_MAX_DAILY_REQUESTS
        and float(row.get("min_request_interval_sec") or 0.0)
        >= SCANNER_PRUNE_BBO_MIN_REQUEST_INTERVAL_SEC
        and row.get("market_data_request_effect") is True
        and row.get("runtime_effect") is False
        and row.get("allowed_runtime_apply") is False
        and row.get("actual_order_submitted") is False
        and row.get("broker_order_forbidden") is True
    ]
    collector_not_configured_count = int(
        prune_observer_schedule_status_counts.get("collector_not_configured") or 0
    )
    schedule_receipt_count = sum(prune_observer_schedule_status_counts.values())
    if exact_bbo_prune_observation_episodes:
        runtime_hook_state = (
            "bounded_prune_rest_bbo_collector_runtime_receipts_observed"
        )
    elif scheduled_prune_observation_episodes:
        runtime_hook_state = (
            "bounded_prune_rest_bbo_collector_schedule_receipts_observed"
        )
    elif collector_not_configured_count:
        runtime_hook_state = "bounded_prune_rest_bbo_collector_not_configured"
    elif eligible_prune_observation_episodes and not schedule_receipt_count:
        runtime_hook_state = (
            "bounded_prune_rest_bbo_collector_loaded_but_schedule_receipt_missing"
            if valid_runtime_configuration_receipts
            else "bounded_prune_rest_bbo_collector_load_and_schedule_receipt_missing"
        )
    elif valid_runtime_configuration_receipts:
        runtime_hook_state = (
            "bounded_prune_rest_bbo_collector_loaded_healthy_no_natural_sample"
        )
    else:
        runtime_hook_state = (
            "bounded_prune_rest_bbo_collector_process_reflection_missing"
        )
    if (
        eligible_prune_observation_episodes
        or prune_observer_runtime_receipts
        or schedule_receipt_count
    ):
        bbo_attribution["source_capture_implementation_state"] = runtime_hook_state
    if collector_not_configured_count or (
        eligible_prune_observation_episodes and not schedule_receipt_count
    ):
        bbo_attribution["source_capture_repair_required"] = True
    prune_observer_summary = {
        "metric_contract": SCANNER_PRUNE_BBO_COLLECTOR_METRIC_CONTRACT,
        "runtime_configuration_receipt_count": len(prune_observer_runtime_receipts),
        "runtime_configuration_valid_receipt_count": len(
            valid_runtime_configuration_receipts
        ),
        "runtime_hook_state": runtime_hook_state,
        "runtime_configuration_status_counts": dict(
            sorted(
                Counter(
                    str(row.get("configuration_status") or "unknown")
                    for row in prune_observer_runtime_receipts
                ).items()
            )
        ),
        "runtime_configuration_receipts": sorted(
            prune_observer_runtime_receipts,
            key=lambda row: (
                float(row.get("configured_epoch") or 0.0),
                int(row.get("process_pid") or 0),
            ),
        )[-20:],
        "acceptance": dict(bbo_attribution.get("prune_observer_acceptance") or {}),
        "eligible_episode_census_count": len(eligible_prune_observation_episodes),
        "scheduled_stable_episode_count": len(scheduled_prune_observation_episodes),
        "schedule_coverage_pct": _rate_pct(
            len(scheduled_prune_observation_episodes),
            len(eligible_prune_observation_episodes),
        ),
        "exact_bbo_observed_episode_count": len(exact_bbo_prune_observation_episodes),
        "exact_bbo_episode_coverage_pct": _rate_pct(
            len(exact_bbo_prune_observation_episodes),
            len(eligible_prune_observation_episodes),
        ),
        "sample_event_count": sum(
            int(episode.get("prune_observer_sample_event_count") or 0)
            for episode in eligible_prune_observation_episodes
        ),
        "schedule_lag_sample_count": len(prune_observer_schedule_lag_values_sec),
        "schedule_lag_p50_sec": _nearest_rank_percentile(
            prune_observer_schedule_lag_values_sec, 0.50
        ),
        "schedule_lag_p95_sec": _nearest_rank_percentile(
            prune_observer_schedule_lag_values_sec, 0.95
        ),
        "schedule_lag_max_sec": (
            max(prune_observer_schedule_lag_values_sec)
            if prune_observer_schedule_lag_values_sec
            else None
        ),
        "schedule_lag_exceeded_sample_count": sum(
            value > SCANNER_PRUNE_BBO_MAX_SCHEDULE_LAG_SEC
            for value in prune_observer_schedule_lag_values_sec
        ),
        "max_economic_schedule_lag_sec": SCANNER_PRUNE_BBO_MAX_SCHEDULE_LAG_SEC,
        "anchor_to_schedule_delay_sample_count": len(
            prune_observer_anchor_to_schedule_delay_values_sec
        ),
        "anchor_to_schedule_delay_p95_sec": _nearest_rank_percentile(
            prune_observer_anchor_to_schedule_delay_values_sec, 0.95
        ),
        "anchor_to_schedule_delay_max_sec": (
            max(prune_observer_anchor_to_schedule_delay_values_sec)
            if prune_observer_anchor_to_schedule_delay_values_sec
            else None
        ),
        "anchor_to_schedule_delay_exceeded_sample_count": sum(
            value > SCANNER_PRUNE_BBO_MAX_SCHEDULE_LAG_SEC
            for value in prune_observer_anchor_to_schedule_delay_values_sec
        ),
        "terminal_sample_observed_episode_count": sum(
            bool(episode.get("prune_observer_terminal_sample_observed"))
            for episode in eligible_prune_observation_episodes
        ),
        "schedule_status_counts": dict(
            sorted(prune_observer_schedule_status_counts.items())
        ),
        "budget_snapshot_count": len(prune_observer_budget_snapshots),
        "max_active_episode_count": max(
            (
                int(snapshot["active_episode_count"])
                for snapshot in prune_observer_budget_snapshots
                if snapshot.get("active_episode_count") is not None
            ),
            default=None,
        ),
        "max_pending_sample_count": max(
            (
                int(snapshot["pending_sample_count"])
                for snapshot in prune_observer_budget_snapshots
                if snapshot.get("pending_sample_count") is not None
            ),
            default=None,
        ),
        "max_process_daily_scheduled_request_count": max(
            (
                int(snapshot["process_daily_scheduled_request_count"])
                for snapshot in prune_observer_budget_snapshots
                if snapshot.get("process_daily_scheduled_request_count") is not None
            ),
            default=None,
        ),
        "min_process_daily_remaining_request_count": min(
            (
                int(snapshot["process_daily_remaining_request_count"])
                for snapshot in prune_observer_budget_snapshots
                if snapshot.get("process_daily_remaining_request_count") is not None
            ),
            default=None,
        ),
        "worker_unhealthy_receipt_count": sum(
            snapshot.get("worker_alive") is False
            for snapshot in prune_observer_budget_snapshots
        ),
        "max_worker_error_count": max(
            (
                int(snapshot["worker_error_count"])
                for snapshot in prune_observer_budget_snapshots
                if snapshot.get("worker_error_count") is not None
            ),
            default=None,
        ),
        "max_receipt_emit_failure_count": max(
            (
                int(snapshot["receipt_emit_failure_count"])
                for snapshot in prune_observer_budget_snapshots
                if snapshot.get("receipt_emit_failure_count") is not None
            ),
            default=None,
        ),
        "max_request_gap_count": max(
            (
                int(snapshot["request_gap_count"])
                for snapshot in prune_observer_budget_snapshots
                if snapshot.get("request_gap_count") is not None
            ),
            default=None,
        ),
        "max_captured_sample_count": max(
            (
                int(snapshot["captured_sample_count"])
                for snapshot in prune_observer_budget_snapshots
                if snapshot.get("captured_sample_count") is not None
            ),
            default=None,
        ),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    iteration_elapsed_values = [
        float(row["elapsed_sec"])
        for row in scanner_iteration_timing_receipts
        if row.get("elapsed_sec") is not None
        and math.isfinite(float(row["elapsed_sec"]))
        and float(row["elapsed_sec"]) >= 0.0
    ]
    projected_start_to_start_values = [
        float(row["projected_start_to_start_sec"])
        for row in scanner_iteration_timing_receipts
        if row.get("projected_start_to_start_sec") is not None
        and math.isfinite(float(row["projected_start_to_start_sec"]))
        and float(row["projected_start_to_start_sec"]) >= 0.0
    ]
    observed_start_to_start_values = [
        float(row["observed_start_to_start_sec"])
        for row in scanner_iteration_timing_receipts
        if row.get("observed_start_to_start_sec") is not None
        and math.isfinite(float(row["observed_start_to_start_sec"]))
        and float(row["observed_start_to_start_sec"]) >= 0.0
    ]
    low_rebound_stage_elapsed_values_ms = [
        float(row["stage_elapsed_ms"])
        for row in scanner_low_rebound_timing_receipts
        if row.get("stage_elapsed_ms") is not None
        and math.isfinite(float(row["stage_elapsed_ms"]))
        and float(row["stage_elapsed_ms"]) >= 0.0
    ]
    low_rebound_fetch_elapsed_values_ms = [
        float(row["candle_fetch_elapsed_total_ms"])
        for row in scanner_low_rebound_timing_receipts
        if row.get("candle_fetch_elapsed_total_ms") is not None
        and math.isfinite(float(row["candle_fetch_elapsed_total_ms"]))
        and float(row["candle_fetch_elapsed_total_ms"]) >= 0.0
    ]
    scanner_timing_summary = {
        "metric_role": "source_quality_instrumentation",
        "decision_authority": "scalping_scanner_timing_observation_only",
        "window_policy": "target_date_complete_live_buy_window_iterations",
        "sample_floor": (
            "two_complete_iterations_in_same_buy_window_and_one_low_rebound_stage_receipt"
        ),
        "primary_decision_metric": "scanner_iteration_observed_start_to_start_sec",
        "source_quality_gate": "monotonic_elapsed_receipts_present_without_imputation",
        "iteration_receipt_count": len(scanner_iteration_timing_receipts),
        "iteration_elapsed_sample_count": len(iteration_elapsed_values),
        "iteration_elapsed_p50_sec": _nearest_rank_percentile(
            iteration_elapsed_values, 0.50
        ),
        "iteration_elapsed_p95_sec": _nearest_rank_percentile(
            iteration_elapsed_values, 0.95
        ),
        "iteration_elapsed_max_sec": (
            max(iteration_elapsed_values) if iteration_elapsed_values else None
        ),
        "projected_start_to_start_p50_sec": _nearest_rank_percentile(
            projected_start_to_start_values, 0.50
        ),
        "projected_start_to_start_p95_sec": _nearest_rank_percentile(
            projected_start_to_start_values, 0.95
        ),
        "observed_start_to_start_sample_count": len(observed_start_to_start_values),
        "observed_start_to_start_p50_sec": _nearest_rank_percentile(
            observed_start_to_start_values, 0.50
        ),
        "observed_start_to_start_p95_sec": _nearest_rank_percentile(
            observed_start_to_start_values, 0.95
        ),
        "low_rebound_stage_receipt_count": len(scanner_low_rebound_timing_receipts),
        "low_rebound_stage_elapsed_sample_count": len(
            low_rebound_stage_elapsed_values_ms
        ),
        "low_rebound_stage_elapsed_p50_ms": _nearest_rank_percentile(
            low_rebound_stage_elapsed_values_ms, 0.50
        ),
        "low_rebound_stage_elapsed_p95_ms": _nearest_rank_percentile(
            low_rebound_stage_elapsed_values_ms, 0.95
        ),
        "low_rebound_candle_fetch_attempted_count": sum(
            int(row.get("candle_fetch_attempted_count") or 0)
            for row in scanner_low_rebound_timing_receipts
        ),
        "low_rebound_candle_fetch_elapsed_total_ms": round(
            sum(low_rebound_fetch_elapsed_values_ms), 3
        ),
        "timing_source_quality_state": (
            "pass"
            if observed_start_to_start_values and low_rebound_stage_elapsed_values_ms
            else (
                "partial_missing_iteration_or_low_rebound_receipt"
                if scanner_iteration_timing_receipts
                or scanner_low_rebound_timing_receipts
                else "not_observed_pre_instrumentation_or_no_natural_iteration"
            )
        ),
        "scanner_sleep_placement": "post_iteration_work",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "forbidden_uses": [
            "scanner_interval_hot_mutation",
            "scanner_slot_or_threshold_change",
            "provider_or_bot_change",
            "broker_or_hard_safety_bypass",
        ],
    }
    final_outcomes: Counter = Counter()
    prune_reasons: Counter = Counter()
    venues: Counter = Counter()
    attach_success_count = 0
    handoff_complete_count = 0
    eligible_count = 0
    eligible_without_heavy_count = 0
    manual_attach_skip_count = 0
    manual_terminalized_count = 0
    unique_records: set[str] = set()
    unique_symbols: set[str] = set()
    generation_terminal_keys: dict[str, set[tuple[str, str]]] = defaultdict(set)
    generation_ranked_counts: dict[str, int] = {}
    generation_ranked_count_values: dict[str, set[int]] = defaultdict(set)
    generation_rank_codes: dict[str, dict[int, set[str]]] = defaultdict(
        lambda: defaultdict(set)
    )
    generation_lineage_metadata_conflict_counts: Counter = Counter()
    immutable_metadata_conflict_count = 0
    immutable_metadata_conflict_rows_sample: list[dict[str, Any]] = []
    for lineage in lineages:
        stages = (
            lineage.get("stages") if isinstance(lineage.get("stages"), dict) else {}
        )
        stage_names = set(stages)
        unique_records.update(str(item) for item in lineage.get("record_ids") or [])
        if lineage.get("code"):
            unique_symbols.add(str(lineage["code"]))
        metadata_conflicts = (
            lineage.get("metadata_conflicts")
            if isinstance(lineage.get("metadata_conflicts"), list)
            else []
        )
        immutable_metadata_conflict_count += len(metadata_conflicts)
        if metadata_conflicts and len(immutable_metadata_conflict_rows_sample) < 50:
            immutable_metadata_conflict_rows_sample.append(
                {
                    "lineage_type": "promotion",
                    "promotion_id": str(lineage.get("promotion_id") or ""),
                    "scan_generation_id": _valid_lineage_token(
                        lineage.get("scan_generation_id")
                    ),
                    "code": str(lineage.get("code") or ""),
                    "metadata_conflicts": list(metadata_conflicts),
                }
            )
        generation_id = _valid_lineage_token(lineage.get("scan_generation_id"))
        if generation_id:
            generation_lineage_metadata_conflict_counts[generation_id] += len(
                metadata_conflicts
            )
            generation_terminal_keys[generation_id].add(
                (str(lineage.get("code") or ""), "promoted")
            )
            ranked_count = int(_to_float(lineage.get("ranked_candidate_count"), 0) or 0)
            if ranked_count:
                generation_ranked_count_values[generation_id].add(ranked_count)
                generation_ranked_counts[generation_id] = max(
                    generation_ranked_counts.get(generation_id, 0), ranked_count
                )
            scan_rank = int(_to_float(lineage.get("scan_rank"), 0) or 0)
            if scan_rank:
                generation_rank_codes[generation_id][scan_rank].add(
                    str(lineage.get("code") or "")
                )
        venues[str(lineage.get("venue") or "UNKNOWN")] += 1
        attach_success = bool(
            set(lineage.get("attach_outcomes") or [])
            & {"attached", "refreshed", "db_poll_attached"}
        )
        attach_success_count += int(attach_success)
        handoff_complete_count += int(
            attach_success and bool(lineage.get("handoff_provenance_complete"))
        )
        eligible = bool(lineage.get("eligible_for_heavy_entry_eval"))
        heavy = "scalping_scanner_heavy_eval_completion" in stage_names
        eligible_count += int(eligible)
        eligible_without_heavy_count += int(eligible and not heavy)
        manual_attach_skip_count += int(
            bool(lineage.get("manual_control_exclusion_attach_skip"))
        )
        manual_terminalized_count += int(
            bool(lineage.get("manual_control_exclusion_terminalized"))
        )
        attach_outcomes = set(lineage.get("attach_outcomes") or [])
        eviction_reasons = set(lineage.get("eviction_reasons") or [])
        if "order_bundle_submitted" in stage_names:
            outcome = "submitted"
        elif "order_bundle_failed" in stage_names:
            outcome = "order_bundle_failed"
        elif lineage.get("manual_control_exclusion_attach_skip"):
            outcome = "manual_control_exclusion_attach_skipped"
        elif "skipped" in attach_outcomes:
            outcome = "runtime_attach_skipped"
        elif any("recovery_exhausted" in reason for reason in eviction_reasons):
            outcome = "direct_ws_recovery_exhausted"
        elif eviction_reasons:
            outcome = (
                "queue_lag_with_stale_context"
                if lineage.get("runtime_queue_lag")
                and lineage.get("decision_stage_stale_backoff")
                else "other_evicted"
            )
        elif "latency_block" in stage_names:
            outcome = "latency_blocked"
        elif stage_names & {"latency_pass", "budget_pass"}:
            outcome = "downstream_guard_passed_right_censored"
        elif "ai_confirmed" in stage_names:
            outcome = "recovered_ai"
        elif "ai_confirmed_terminal_no_budget" in stage_names:
            outcome = "ai_budget_terminal_no_call"
        elif heavy:
            outcome = "recovered_heavy_no_ai"
        elif "scalping_scanner_fast_precheck" in stage_names:
            outcome = (
                "active_queue_lag_right_censored"
                if lineage.get("runtime_queue_lag")
                and lineage.get("decision_stage_stale_backoff")
                else "fast_precheck_only_right_censored"
            )
        else:
            outcome = "active_right_censored"
        final_outcomes[outcome] += 1
    for prune in prunes:
        reasons = prune.get("reasons") or [prune.get("reason") or "unknown"]
        for reason in reasons:
            prune_reasons[str(reason)] += 1
        metadata_conflicts = (
            prune.get("metadata_conflicts")
            if isinstance(prune.get("metadata_conflicts"), list)
            else []
        )
        immutable_metadata_conflict_count += len(metadata_conflicts)
        if metadata_conflicts and len(immutable_metadata_conflict_rows_sample) < 50:
            immutable_metadata_conflict_rows_sample.append(
                {
                    "lineage_type": "prune",
                    "promotion_id": None,
                    "scan_generation_id": _valid_lineage_token(
                        prune.get("scan_generation_id")
                    ),
                    "code": str(prune.get("code") or ""),
                    "metadata_conflicts": list(metadata_conflicts),
                }
            )
        generation_id = _valid_lineage_token(prune.get("scan_generation_id"))
        if generation_id:
            generation_lineage_metadata_conflict_counts[generation_id] += len(
                metadata_conflicts
            )
            for reason in reasons:
                generation_terminal_keys[generation_id].add(
                    (str(prune.get("code") or ""), f"pruned:{reason}")
                )
            ranked_count = int(_to_float(prune.get("ranked_candidate_count"), 0) or 0)
            if ranked_count:
                generation_ranked_count_values[generation_id].add(ranked_count)
                generation_ranked_counts[generation_id] = max(
                    generation_ranked_counts.get(generation_id, 0), ranked_count
                )
            scan_rank = int(_to_float(prune.get("scan_rank"), 0) or 0)
            if scan_rank:
                generation_rank_codes[generation_id][scan_rank].add(
                    str(prune.get("code") or "")
                )
    conservation_rows = []
    for generation_id in sorted(generation_terminal_keys):
        ranked_count = generation_ranked_counts.get(generation_id, 0)
        terminal_keys = generation_terminal_keys[generation_id]
        terminal_codes = {code for code, _outcome in terminal_keys}
        row = {
            "scan_generation_id": generation_id,
            "ranked_candidate_count": ranked_count,
            "terminal_candidate_count": len(terminal_codes),
            "conservation_delta": ranked_count - len(terminal_codes),
            "outcome_conflict_count": sum(
                len(
                    {
                        outcome
                        for item_code, outcome in terminal_keys
                        if item_code == code
                    }
                )
                > 1
                for code in terminal_codes
            ),
            "missing_ranked_candidate_count": int(ranked_count <= 0),
            "ranked_count_conflict_count": max(
                0, len(generation_ranked_count_values[generation_id]) - 1
            ),
            "duplicate_rank_count": sum(
                len(codes) > 1
                for rank, codes in generation_rank_codes[generation_id].items()
                if 1 <= rank <= ranked_count
            ),
            "missing_rank_count": sum(
                rank not in generation_rank_codes[generation_id]
                for rank in range(1, ranked_count + 1)
            ),
            "out_of_range_rank_count": sum(
                not 1 <= rank <= ranked_count
                for rank in generation_rank_codes[generation_id]
            ),
            "lineage_metadata_conflict_count": int(
                generation_lineage_metadata_conflict_counts[generation_id]
            ),
        }
        row["metadata_conflict_count"] = sum(
            int(row[key])
            for key in (
                "missing_ranked_candidate_count",
                "ranked_count_conflict_count",
                "duplicate_rank_count",
                "missing_rank_count",
                "out_of_range_rank_count",
                "lineage_metadata_conflict_count",
            )
        )
        conservation_rows.append(row)
    return {
        "metric_contract": SCANNER_UNIQUE_FUNNEL_METRIC_CONTRACT,
        "relevant_raw_event_count": int(state.get("relevant_raw_event_count") or 0),
        "duplicate_mirror_event_count": int(
            state.get("duplicate_mirror_event_count") or 0
        ),
        "missing_lineage_event_count": int(
            state.get("missing_lineage_event_count") or 0
        ),
        "unique_promotion_count": len(lineages),
        "unique_runtime_record_count": len(unique_records),
        "unique_symbol_count": len(unique_symbols),
        "attach_success_count": attach_success_count,
        "handoff_provenance_complete_count": handoff_complete_count,
        "handoff_provenance_coverage_pct": _rate_pct(
            handoff_complete_count, attach_success_count
        ),
        "eligible_for_heavy_entry_eval_count": eligible_count,
        "eligible_without_heavy_evaluation_count": eligible_without_heavy_count,
        "eligible_without_heavy_evaluation_rate_pct": _rate_pct(
            eligible_without_heavy_count, eligible_count
        ),
        "manual_control_exclusion_attach_skip_count": manual_attach_skip_count,
        "manual_control_exclusion_terminalized_count": manual_terminalized_count,
        "unique_pruned_candidate_count": len(prunes),
        "scanner_timing_summary": scanner_timing_summary,
        "prune_observer_summary": prune_observer_summary,
        "prune_reason_counts": dict(sorted(prune_reasons.items())),
        "immutable_metadata_conflict_count": immutable_metadata_conflict_count,
        "immutable_metadata_conflict_rows_sample": (
            immutable_metadata_conflict_rows_sample
        ),
        "scan_generation_conservation": {
            "generation_count": len(conservation_rows),
            "complete_generation_count": sum(
                row["conservation_delta"] == 0
                and row["outcome_conflict_count"] == 0
                and row["metadata_conflict_count"] == 0
                for row in conservation_rows
            ),
            "incomplete_generation_count": sum(
                row["conservation_delta"] != 0
                or row["outcome_conflict_count"] != 0
                or row["metadata_conflict_count"] != 0
                for row in conservation_rows
            ),
            "structural_contract_conflict_generation_count": sum(
                _scanner_generation_has_structural_contract_conflict(row)
                for row in conservation_rows
            ),
            "structural_contract_conflict_rows_sample": [
                row
                for row in conservation_rows
                if _scanner_generation_has_structural_contract_conflict(row)
            ][:50],
            "incomplete_rows_sample": [
                row
                for row in conservation_rows
                if row["conservation_delta"] != 0
                or row["outcome_conflict_count"] != 0
                or row["metadata_conflict_count"] != 0
            ][:50],
            "rows": conservation_rows[:50],
        },
        "final_outcome_counts": dict(sorted(final_outcomes.items())),
        "venue_counts": dict(sorted(venues.items())),
        "economic_cohorts": {
            "eligible_no_heavy": eligible_without_heavy_count,
            "heavy_then_stale_queue_evict": sum(
                1
                for lineage in lineages
                if "scalping_scanner_heavy_eval_completion"
                in (lineage.get("stages") or {})
                and lineage.get("runtime_queue_lag")
                and lineage.get("decision_stage_stale_backoff")
                and lineage.get("eviction_reasons")
            ),
            "non_gainer_not_rising_repeat": sum(
                1
                for prune in prune_observation_episodes
                if _scanner_prune_economic_cohort(prune)
                == "non_gainer_not_rising_repeat"
            ),
            "market_gainer_reentry_cooldown": sum(
                1
                for prune in prune_observation_episodes
                if _scanner_prune_economic_cohort(prune)
                == "market_gainer_reentry_cooldown"
            ),
            "market_gainer_reserved_full": sum(
                1
                for prune in prune_observation_episodes
                if _scanner_prune_economic_cohort(prune)
                == "market_gainer_reserved_full"
            ),
            "general_slot_limit": sum(
                1
                for prune in prune_observation_episodes
                if _scanner_prune_economic_cohort(prune) == "general_slot_limit"
            ),
            "executable_bbo_ev_status": bbo_attribution["status"],
            "executable_bbo_attribution": bbo_attribution,
        },
        "hotset_capacity_counterfactual": hotset_capacity_counterfactual,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }


def _time_bucket(row: dict[str, Any]) -> str:
    ts = _event_time(row)
    if ts is None:
        return "unknown"
    hm = ts.hour * 100 + ts.minute
    if hm < 900:
        return "pre_0900"
    if hm < 1200:
        return "regular_0900_1200"
    if hm < 1500:
        return "regular_1200_1500"
    if hm < 1520:
        return "regular_1500_1520"
    if hm < 1530:
        return "closing_1520_1530"
    return "post_1530"


def _source_paths(target_date: str) -> dict[str, Path]:
    return {
        "pipeline_events": existing_or_gzip_path(
            PIPELINE_EVENTS_DIR / f"pipeline_events_{target_date}.jsonl"
        ),
        "threshold_events": existing_or_gzip_path(
            THRESHOLD_EVENTS_DIR / f"threshold_events_{target_date}.jsonl"
        ),
    }


def _rate_pct(count: int, total: int) -> float:
    return round((float(count) / float(total) * 100.0), 4) if total else 0.0


def _counter_rows(
    counter: Counter, *, limit: int = 20, key_name: str = "key"
) -> list[dict[str, Any]]:
    return [
        {key_name: str(key), "count": int(value)}
        for key, value in counter.most_common(limit)
    ]


def _snapshot_generated_at(snapshot: dict[str, Any]) -> datetime | None:
    value = snapshot.get("generated_at")
    if value:
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            parsed = None
        if parsed is not None:
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=KST)
            return parsed.astimezone(KST)
    epoch = _to_float(snapshot.get("generated_at_epoch"))
    if epoch is None:
        return None
    try:
        return datetime.fromtimestamp(epoch, tz=KST)
    except (OverflowError, OSError, ValueError):
        return None


def _resolve_snapshot(
    requested_path: Path | None,
    *,
    target_date: str,
) -> tuple[Path | None, dict[str, Any], dict[str, Any]]:
    explicit = requested_path is not None
    selected_path = requested_path if explicit else DEFAULT_DASHBOARD_SNAPSHOT_PATH
    payload = _read_json(selected_path)
    generated_at = _snapshot_generated_at(payload)
    provenance = {
        "source": "explicit_subscription_snapshot" if explicit else "none",
        "selected": False,
        "selection_reason": "path_missing",
        "schema_version": str(payload.get("schema_version") or "unknown"),
        "generated_at": generated_at.isoformat() if generated_at else None,
        "subscription_state_available": False,
    }
    if selected_path is None or not selected_path.exists():
        return selected_path, {}, provenance
    if not payload:
        provenance["selection_reason"] = "invalid_or_empty_json"
        return selected_path, {}, provenance
    if explicit:
        provenance.update(
            {
                "selected": True,
                "selection_reason": "explicit_path",
                "subscription_state_available": bool(
                    isinstance(payload.get("rows"), list)
                    or isinstance(payload.get("symbols"), list)
                ),
            }
        )
        return selected_path, payload, provenance
    if str(payload.get("schema_version") or "") != "kiwoom_ws_dashboard_snapshot_v1":
        provenance["selection_reason"] = "unsupported_default_snapshot_schema"
        return selected_path, {}, provenance
    if generated_at is None:
        provenance["selection_reason"] = "default_snapshot_generated_at_missing"
        return selected_path, {}, provenance
    if generated_at.date().isoformat() != target_date:
        provenance["selection_reason"] = "default_snapshot_target_date_mismatch"
        return selected_path, {}, provenance
    provenance.update(
        {
            "source": "same_day_live_dashboard_snapshot_fallback",
            "selected": True,
            "selection_reason": "same_day_schema_match",
            "subscription_state_available": False,
        }
    )
    return selected_path, payload, provenance


def _dashboard_snapshot_rows(
    snapshot: dict[str, Any], *, stale_ms: float
) -> list[dict[str, Any]]:
    stocks = snapshot.get("stocks")
    if not isinstance(stocks, dict):
        return []
    rows: list[dict[str, Any]] = []
    for stock_code, raw in stocks.items():
        if not isinstance(raw, dict):
            continue
        ages = _dictish(raw.get("last_realtime_type_ages_ms"))
        numeric_ages = [
            age for value in ages.values() if (age := _to_float(value)) is not None
        ]
        last_receive_age_ms = min(numeric_ages) if numeric_ages else None
        age_0b_ms = _to_float(raw.get("last_0b_age_ms"))
        if age_0b_ms is None:
            age_0b_ms = _to_float(ages.get("0B"))
        age_0d_ms = _to_float(ages.get("0D"))
        non_trade_fresh = any(
            (age := _to_float(ages.get(realtime_type))) is not None and age < stale_ms
            for realtime_type in ("0D", "0w", "0F")
        )
        if last_receive_age_ms is None:
            freshness_state = "no_tick"
        elif last_receive_age_ms >= stale_ms:
            freshness_state = "stale"
        else:
            freshness_state = "fresh"
        trade_tick_quiet = bool(
            freshness_state == "fresh"
            and non_trade_fresh
            and (age_0b_ms is None or age_0b_ms >= stale_ms)
        )
        last_trade_cum_volume = _to_float(raw.get("last_trade_cum_volume"))
        if last_trade_cum_volume is None:
            last_trade_cum_volume = _to_float(
                _dictish(raw.get("last_trade_tick")).get("cum_volume")
            )
        rows.append(
            {
                "stock_code": str(stock_code),
                "freshness_state": freshness_state,
                "last_receive_age_sec": (
                    round(last_receive_age_ms / 1000.0, 3)
                    if last_receive_age_ms is not None
                    else None
                ),
                "last_0b_age_sec": (
                    round(age_0b_ms / 1000.0, 3) if age_0b_ms is not None else None
                ),
                "last_0d_age_sec": (
                    round(age_0d_ms / 1000.0, 3) if age_0d_ms is not None else None
                ),
                "last_trade_cum_volume": last_trade_cum_volume,
                "trade_tick_quiet": trade_tick_quiet,
                "repair_recommended": False,
                "repair_reason": "dashboard_snapshot_subscription_state_unavailable",
                "observed_market_route": str(
                    raw.get("last_ws_market_route") or "unknown"
                ),
                "observed_market_suffix": str(raw.get("last_ws_market_suffix") or ""),
                "snapshot_row_authority": "live_dashboard_observation_only",
                "subscription_state_available": False,
            }
        )
    return rows


def _snapshot_rows(
    snapshot: dict[str, Any], *, stale_ms: float
) -> list[dict[str, Any]]:
    rows = snapshot.get("rows")
    if isinstance(rows, list):
        return [row for row in rows if isinstance(row, dict)]
    if isinstance(snapshot.get("symbols"), list):
        return [row for row in snapshot["symbols"] if isinstance(row, dict)]
    return _dashboard_snapshot_rows(snapshot, stale_ms=stale_ms)


def _row_provider_none(row: dict[str, Any]) -> bool:
    for key, value in row.items():
        key_l = str(key).lower()
        if not any(token in key_l for token in PROVIDER_FIELD_TOKENS):
            continue
        if str(value).strip().lower() == "none":
            return True
    return False


def _pipeline_event_class(row: dict[str, Any], *, stale_ms: float) -> dict[str, Any]:
    stage = str(row.get("stage") or row.get("event_type") or "unknown")
    reason_values = {
        str(row.get("source_quality_block_reason") or "").strip(),
        str(row.get("reason") or "").strip(),
        str(row.get("skip_reason") or "").strip(),
        str(row.get("fast_precheck_reason") or "").strip(),
        str(row.get("fast_precheck_observed_reason") or "").strip(),
        str(row.get("scanner_ws_stale_backoff_reason") or "").strip(),
        str(row.get("risk_state") or "").strip(),
        str(row.get("zero_context_blocker") or "").strip(),
    }
    decision_stage_stale_backoff_reasons = {
        "persistent_ws_gap",
        "scanner_ws_stale_backoff_active",
        "stale_ws_snapshot",
        "ws_snapshot_missing_or_zero",
    }
    decision_stage_stale_backoff = bool(
        reason_values & decision_stage_stale_backoff_reasons
    )
    stale_backoff_reason = next(
        (
            reason
            for reason in (
                str(row.get("scanner_ws_stale_backoff_reason") or "").strip(),
                str(row.get("fast_precheck_observed_reason") or "").strip(),
                str(row.get("fast_precheck_reason") or "").strip(),
                str(row.get("source_quality_block_reason") or "").strip(),
                str(row.get("reason") or "").strip(),
                str(row.get("skip_reason") or "").strip(),
                str(row.get("risk_state") or "").strip(),
                str(row.get("zero_context_blocker") or "").strip(),
            )
            if reason in decision_stage_stale_backoff_reasons
        ),
        "not_applicable",
    )
    trade_tick_quiet = (
        _boolish(row.get("trade_tick_quiet"))
        or "trade_tick_quiet" in reason_values
        or str(row.get("trade_tick_quiet_reason") or "").strip()
        == "fresh_non_trade_ws_without_fresh_0b"
    )
    repair_recommended = _boolish(row.get("repair_recommended"))
    repair_reason = str(row.get("repair_reason") or "").strip() or "none"
    freshness_state = str(row.get("freshness_state") or "").strip()
    subscription_stale = (
        repair_recommended
        or repair_reason
        in {
            "subscription_no_tick",
            "subscription_stale",
        }
        or freshness_state in {"no_tick", "stale"}
    )

    age_0b = _to_float(row.get("ws_last_0b_age_ms"))
    age_0d = _to_float(row.get("ws_last_0d_age_ms"))
    if age_0b is None:
        age_0b = _to_float(row.get("last_0b_age_sec"))
        age_0b = age_0b * 1000.0 if age_0b is not None else None
    if age_0d is None:
        age_0d = _to_float(row.get("last_0d_age_sec"))
        age_0d = age_0d * 1000.0 if age_0d is not None else None

    stale_0b = age_0b is not None and age_0b >= stale_ms
    stale_0d = age_0d is not None and age_0d >= stale_ms
    fresh_0d = age_0d is not None and age_0d < stale_ms
    both_stale = stale_0b and stale_0d
    quiet_by_age = fresh_0d and stale_0b

    if not trade_tick_quiet and quiet_by_age:
        trade_tick_quiet = True

    submit_related = "submit" in stage.lower() or "order_bundle" in stage.lower()
    scout_related = "scout" in stage.lower() or "rising_missed" in json.dumps(
        row, ensure_ascii=False
    )
    stage_lower = stage.lower()
    if "watch_eviction" in stage_lower:
        watchlist_outcome = "evicted"
    elif "watch_retained" in stage_lower:
        watchlist_outcome = "retained"
    else:
        watchlist_outcome = "decision_stage_only"

    repair_cycle_state = str(row.get("ws_repair_cycle_state") or "").strip()
    repair_required_observed = "ws_subscription_repair_required" in row
    repair_batch_required_observed = "ws_repair_batch_required" in row
    repair_required = _boolish(row.get("ws_subscription_repair_required"))
    repair_batch_required = _boolish(row.get("ws_repair_batch_required"))
    if not repair_cycle_state:
        if repair_required or repair_batch_required:
            repair_cycle_state = "repair_required_without_cycle_state"
        else:
            repair_cycle_state = "not_observed"
    repair_recheck_reason = str(
        row.get("fast_precheck_ws_stale_backoff_recheck_reason")
        or row.get("scanner_ws_stale_backoff_recheck_reason")
        or "not_observed"
    ).strip()

    last_trade_cum_volume = _to_float(row.get("last_trade_cum_volume"))
    if last_trade_cum_volume is None:
        last_trade_tick = _dictish(row.get("last_trade_tick"))
        last_trade_cum_volume = _to_float(last_trade_tick.get("cum_volume"))
    signed_tape_volume_observed = any(
        _to_float(row.get(key)) is not None
        for key in (
            "market_data_signed_tape_buy_volume",
            "market_data_signed_tape_sell_volume",
        )
    )
    if not trade_tick_quiet:
        quiet_volume_provenance = "not_applicable"
    elif last_trade_cum_volume is not None:
        quiet_volume_provenance = (
            "cumulative_volume_positive"
            if last_trade_cum_volume > 0
            else "cumulative_volume_zero"
        )
    elif signed_tape_volume_observed:
        quiet_volume_provenance = "signed_tape_only_cumulative_volume_missing"
    else:
        quiet_volume_provenance = "cumulative_volume_missing"

    return {
        "stage": stage,
        "stock_code": str(row.get("stock_code") or ""),
        "stock_name": str(row.get("stock_name") or ""),
        "time_bucket": _time_bucket(row),
        "trade_tick_quiet": bool(trade_tick_quiet),
        "subscription_stale": bool(subscription_stale),
        "decision_stage_stale_backoff": decision_stage_stale_backoff,
        "both_ws_stale": bool(both_stale),
        "fresh_0d_stale_0b": bool(quiet_by_age),
        "provider_none": _row_provider_none(row),
        "submit_related": submit_related,
        "scout_related": scout_related,
        "ws_age_observed": any(
            _to_float(row.get(key)) is not None for key in WS_AGE_FIELDS_MS
        )
        or age_0b is not None
        or age_0d is not None,
        "age_0b_ms": age_0b,
        "age_0d_ms": age_0d,
        "repair_reason": repair_reason,
        "freshness_state": freshness_state or "-",
        "stale_backoff_reason": stale_backoff_reason,
        "stale_backoff_repair_cycle_state": repair_cycle_state,
        "stale_backoff_recheck_reason": repair_recheck_reason,
        "stale_backoff_watchlist_outcome": watchlist_outcome,
        "both_ws_stale_repair_required": (
            "required"
            if repair_required or repair_batch_required
            else (
                "not_required"
                if repair_required_observed or repair_batch_required_observed
                else "not_observed"
            )
        ),
        "trade_tick_quiet_volume_provenance": quiet_volume_provenance,
    }


def _snapshot_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    states: Counter = Counter()
    repair_reasons: Counter = Counter()
    route_counts: Counter = Counter()
    suffix_counts: Counter = Counter()
    observed_route_counts: Counter = Counter()
    observed_suffix_counts: Counter = Counter()
    quiet_rows: list[dict[str, Any]] = []
    repair_rows: list[dict[str, Any]] = []
    multi_route_rows: list[dict[str, Any]] = []
    subscription_stale_like_rows: list[dict[str, Any]] = []
    observed_stale_like_rows: list[dict[str, Any]] = []
    quiet_cumulative_volume_provenance: Counter = Counter()
    quota_units = 0
    for row in rows:
        state = str(row.get("freshness_state") or "unknown")
        states[state] += 1
        reason = str(row.get("repair_reason") or "none")
        repair_reasons[reason] += 1
        quota_units += int(_to_float(row.get("registered_item_quota_units"), 0.0) or 0)
        for route, count in _dictish(row.get("registered_route_counts")).items():
            route_counts[str(route)] += int(_to_float(count, 0.0) or 0)
        for suffix in _listish(row.get("registered_market_suffixes")):
            suffix_counts[str(suffix) or "KRX"] += 1
        observed_route = str(row.get("observed_market_route") or "").strip()
        if observed_route:
            observed_route_counts[observed_route] += 1
        observed_suffix = str(row.get("observed_market_suffix") or "").strip()
        if row.get("observed_market_suffix") is not None:
            observed_suffix_counts[observed_suffix or "KRX"] += 1
        if _boolish(row.get("multi_route_registered")):
            multi_route_rows.append(row)
        if _boolish(row.get("trade_tick_quiet")):
            quiet_rows.append(row)
            cumulative_volume = _to_float(row.get("last_trade_cum_volume"))
            if cumulative_volume is None:
                quiet_cumulative_volume_provenance["cumulative_volume_missing"] += 1
            elif cumulative_volume > 0:
                quiet_cumulative_volume_provenance["cumulative_volume_positive"] += 1
            else:
                quiet_cumulative_volume_provenance["cumulative_volume_zero"] += 1
        if _boolish(row.get("repair_recommended")):
            repair_rows.append(row)
        if state in {"stale", "no_tick"}:
            observed_stale_like_rows.append(row)
            if row.get("subscription_state_available") is not False:
                subscription_stale_like_rows.append(row)
    total = len(rows)
    stale_like = len(subscription_stale_like_rows)
    return {
        "row_count": total,
        "freshness_state_counts": dict(states),
        "repair_reason_counts": dict(repair_reasons),
        "subscription_stale_like_count": stale_like,
        "subscription_stale_like_rate_pct": _rate_pct(stale_like, total),
        "observed_stale_like_count": len(observed_stale_like_rows),
        "observed_stale_like_rate_pct": _rate_pct(len(observed_stale_like_rows), total),
        "trade_tick_quiet_count": len(quiet_rows),
        "trade_tick_quiet_rate_pct": _rate_pct(len(quiet_rows), total),
        "trade_tick_quiet_cumulative_volume_provenance_counts": dict(
            quiet_cumulative_volume_provenance
        ),
        "repair_recommended_count": len(repair_rows),
        "registered_item_quota_units": quota_units,
        "registered_route_counts": dict(route_counts),
        "registered_market_suffix_counts": dict(suffix_counts),
        "observed_market_route_counts": dict(observed_route_counts),
        "observed_market_suffix_counts": dict(observed_suffix_counts),
        "multi_route_registered_count": len(multi_route_rows),
        "multi_route_registered_rate_pct": _rate_pct(len(multi_route_rows), total),
        "route_repair_policy": "remove_then_reg_required_for_route_transition",
        "top_trade_tick_quiet_symbols": [
            {
                "stock_code": str(row.get("stock_code") or ""),
                "last_0b_age_sec": row.get("last_0b_age_sec"),
                "last_0d_age_sec": row.get("last_0d_age_sec"),
                "last_trade_cum_volume": row.get("last_trade_cum_volume"),
            }
            for row in quiet_rows[:20]
        ],
        "top_repair_symbols": [
            {
                "stock_code": str(row.get("stock_code") or ""),
                "freshness_state": row.get("freshness_state"),
                "repair_reason": row.get("repair_reason"),
                "last_receive_age_sec": row.get("last_receive_age_sec"),
            }
            for row in repair_rows[:20]
        ],
        "top_multi_route_symbols": [
            {
                "stock_code": str(row.get("stock_code") or ""),
                "registered_items": row.get("registered_items") or [],
                "registered_market_routes": row.get("registered_market_routes") or [],
                "registered_item_quota_units": row.get("registered_item_quota_units"),
            }
            for row in multi_route_rows[:20]
        ],
    }


def _scanner_economic_cohorts_evidence(
    economic_cohorts: Mapping[str, Any],
) -> dict[str, Any]:
    attribution = (
        economic_cohorts.get("executable_bbo_attribution")
        if isinstance(economic_cohorts.get("executable_bbo_attribution"), dict)
        else {}
    )
    return {
        "eligible_no_heavy": int(economic_cohorts.get("eligible_no_heavy") or 0),
        "heavy_then_stale_queue_evict": int(
            economic_cohorts.get("heavy_then_stale_queue_evict") or 0
        ),
        "non_gainer_not_rising_repeat": int(
            economic_cohorts.get("non_gainer_not_rising_repeat") or 0
        ),
        "market_gainer_reentry_cooldown": int(
            economic_cohorts.get("market_gainer_reentry_cooldown") or 0
        ),
        "market_gainer_reserved_full": int(
            economic_cohorts.get("market_gainer_reserved_full") or 0
        ),
        "general_slot_limit": int(economic_cohorts.get("general_slot_limit") or 0),
        "executable_bbo_ev_status": economic_cohorts.get("executable_bbo_ev_status"),
        "exact_bbo_joined_count": int(attribution.get("exact_bbo_joined_count") or 0),
        "exact_promotion_venue_session_bbo_join_coverage_pct": attribution.get(
            "exact_promotion_venue_session_bbo_join_coverage_pct"
        ),
        "resolved_outcome_count": int(attribution.get("resolved_outcome_count") or 0),
        "source_quality_adjusted_ev_pct": attribution.get(
            "source_quality_adjusted_ev_pct"
        ),
        "aggregate_ev_status": attribution.get("aggregate_ev_status"),
        "venue_session_economics": attribution.get("venue_session_economics"),
        "comparison_cost_contract_sha256": (
            (attribution.get("comparison_cost_contract") or {}).get("contract_sha256")
            if isinstance(attribution.get("comparison_cost_contract"), dict)
            else None
        ),
        "official_symbol_master_status": (
            (attribution.get("official_symbol_master_binding") or {}).get("status")
            if isinstance(attribution.get("official_symbol_master_binding"), dict)
            else None
        ),
        "official_symbol_master_artifact_sha256": (
            (attribution.get("official_symbol_master_binding") or {}).get(
                "artifact_sha256"
            )
            if isinstance(attribution.get("official_symbol_master_binding"), dict)
            else None
        ),
        "official_symbol_master_lookup_counts": attribution.get(
            "official_symbol_master_lookup_counts"
        ),
        "cohort_source_quality": attribution.get("cohort_source_quality"),
        "cohort_venue_session_economics": attribution.get(
            "cohort_venue_session_economics"
        ),
        "source_capture_design_required": bool(
            attribution.get("source_capture_design_required")
        ),
        "source_capture_implementation_state": attribution.get(
            "source_capture_implementation_state"
        ),
        "source_capture_repair_required": bool(
            attribution.get("source_capture_repair_required")
        ),
    }


def _build_workorders(
    summary: dict[str, Any], *, target_date: str
) -> list[dict[str, Any]]:
    counts = summary["pipeline_counts"]
    snapshot = summary["snapshot_summary"]
    scanner_funnel = summary.get("scanner_unique_funnel") or {}
    economic_cohorts = scanner_funnel.get("economic_cohorts") or {}
    prune_observer_summary = scanner_funnel.get("prune_observer_summary") or {}
    economic_cohorts_evidence = _scanner_economic_cohorts_evidence(economic_cohorts)
    causal = summary.get("causal_attribution") or {}
    quiet_volume_counts = (causal.get("trade_tick_quiet") or {}).get(
        "cumulative_volume_provenance_counts", {}
    ) or {}
    quiet_volume_observed_count = sum(
        int(quiet_volume_counts.get(key, 0) or 0)
        for key in ("cumulative_volume_positive", "cumulative_volume_zero")
    )
    quiet_volume_observed_count += sum(
        int(
            (
                snapshot.get("trade_tick_quiet_cumulative_volume_provenance_counts")
                or {}
            ).get(key, 0)
            or 0
        )
        for key in ("cumulative_volume_positive", "cumulative_volume_zero")
    )
    orders: list[dict[str, Any]] = []
    base = {
        "target_date": target_date,
        "source_report_type": REPORT_TYPE,
        "decision": "implement_now",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "decision_authority": METRIC_CONTRACT["decision_authority"],
        "forbidden_uses": FORBIDDEN_USES,
    }
    attach_success_count = int(scanner_funnel.get("attach_success_count") or 0)
    handoff_complete_count = int(
        scanner_funnel.get("handoff_provenance_complete_count") or 0
    )
    if attach_success_count > handoff_complete_count:
        orders.append(
            {
                **base,
                "decision": "defer_evidence",
                "next_action": "verify_after_current_runtime_reflection",
                "implementation_state": "handoff_provenance_implemented_not_runtime_reflected",
                "order_id": "order_scanner_runtime_handoff_provenance_gap",
                "title": "Scanner runtime handoff provenance closure",
                "priority": 1,
                "intent": (
                    "Require an exact promotion id, local runtime handoff epoch, runtime instance id, "
                    "and provenance version on every successful scanner WATCHING attach."
                ),
                "evidence": [
                    f"attach_success_count={attach_success_count}",
                    f"handoff_provenance_complete_count={handoff_complete_count}",
                    "handoff_provenance_coverage_pct="
                    f"{scanner_funnel.get('handoff_provenance_coverage_pct', 0.0)}",
                ],
                "files_likely_touched": [
                    "src/engine/kiwoom_sniper_v2.py",
                    "src/engine/monitoring/intraday_ws_freshness_monitor.py",
                    "src/tests/test_kiwoom_sniper_market_regime_runtime.py",
                    "src/tests/test_intraday_ws_freshness_monitor.py",
                ],
                "acceptance_tests": [
                    "successful_attach_handoff_provenance_coverage_pct=100",
                    "same_promotion_refresh_preserves_handoff_epoch",
                    "new_promotion_rotates_handoff_epoch",
                ],
            }
        )
    eligible_no_heavy = int(
        scanner_funnel.get("eligible_without_heavy_evaluation_count") or 0
    )
    if eligible_no_heavy:
        orders.append(
            {
                **base,
                "decision": "defer_evidence",
                "next_action": "recheck_after_next_natural_session",
                "implementation_state": "closed_loop_instrumentation_active",
                "order_id": "order_scanner_eligible_no_heavy_closed_loop",
                "title": "Scanner eligible-to-heavy evaluation loss closure",
                "priority": 1,
                "intent": (
                    "Attribute unique promotions that passed fast precheck but never reached heavy "
                    "evaluation, preserving WS stale, queue-lag, eviction, venue, and terminal outcome."
                ),
                "evidence": [
                    f"eligible_without_heavy_evaluation_count={eligible_no_heavy}",
                    "eligible_without_heavy_evaluation_rate_pct="
                    f"{scanner_funnel.get('eligible_without_heavy_evaluation_rate_pct', 0.0)}",
                    f"final_outcome_counts={scanner_funnel.get('final_outcome_counts', {})}",
                    f"economic_cohorts={economic_cohorts_evidence}",
                ],
                "files_likely_touched": [
                    "src/engine/monitoring/intraday_ws_freshness_monitor.py",
                    "src/engine/scalping/scanner_scheduler_replay.py",
                    "src/tests/test_intraday_ws_freshness_monitor.py",
                ],
                "acceptance_tests": [
                    "pipeline_threshold_mirror_events_are_deduplicated",
                    "every_unique_promotion_has_one_final_outcome_or_active_right_censored",
                    "missing_executable_bbo_remains_source_quality_blocked_not_zero_ev",
                ],
            }
        )
    manual_attach_skips = int(
        scanner_funnel.get("manual_control_exclusion_attach_skip_count") or 0
    )
    if manual_attach_skips:
        orders.append(
            {
                **base,
                "decision": "defer_evidence",
                "next_action": "verify_zero_after_current_runtime_reflection",
                "implementation_state": "scanner_prefilter_and_exact_terminalization_implemented",
                "order_id": "order_scanner_manual_exclusion_slot_leak",
                "title": "Scanner manual-exclusion WATCHING slot leak verification",
                "priority": 1,
                "intent": (
                    "Verify manually controlled symbols are pruned before WATCHING persistence and "
                    "that legacy exact zero-fill generations are terminalized without touching holdings."
                ),
                "evidence": [
                    f"manual_control_exclusion_attach_skip_count={manual_attach_skips}",
                    "manual_control_exclusion_terminalized_count="
                    f"{scanner_funnel.get('manual_control_exclusion_terminalized_count', 0)}",
                ],
                "files_likely_touched": [
                    "src/scanners/scalping_scanner.py",
                    "src/engine/kiwoom_sniper_v2.py",
                    "src/tests/test_scalping_scanner_candidate_pool.py",
                    "src/tests/test_kiwoom_sniper_market_regime_runtime.py",
                ],
                "acceptance_tests": [
                    "manual_excluded_scanner_promotion_count=0",
                    "manual_excluded_scanner_ws_reg_count=0",
                    "manual_excluded_zero_fill_watching_count=0",
                    "other_owner_and_filled_position_mutation_count=0",
                ],
            }
        )
    conservation = scanner_funnel.get("scan_generation_conservation") or {}
    incomplete_generations = int(conservation.get("incomplete_generation_count") or 0)
    immutable_metadata_conflicts = int(
        scanner_funnel.get("immutable_metadata_conflict_count") or 0
    )
    if incomplete_generations or immutable_metadata_conflicts:
        incomplete_rows = conservation.get("incomplete_rows_sample") or []
        structural_rows = (
            conservation.get("structural_contract_conflict_rows_sample") or []
        )
        structural_contract_conflict = bool(
            int(conservation.get("structural_contract_conflict_generation_count") or 0)
            or immutable_metadata_conflicts
        )
        orders.append(
            {
                **base,
                "decision": (
                    "implement_now"
                    if structural_contract_conflict
                    else "defer_evidence"
                ),
                "next_action": (
                    "repair_scanner_metadata_contract_and_rebuild"
                    if structural_contract_conflict
                    else "verify_after_next_natural_scan_generation"
                ),
                "implementation_state": (
                    "immutable_scanner_metadata_conflict_detected"
                    if structural_contract_conflict
                    else (
                        "scanner_candidate_prune_receipts_implemented_"
                        "waiting_natural_generation"
                    )
                ),
                "order_id": "order_scanner_scan_generation_conservation_gap",
                "title": "Scanner ranked-to-promotion funnel conservation gap",
                "priority": 1,
                "intent": (
                    "Preserve exact code, generation, rank, ranked count, venue, and session on each "
                    "scanner lineage, then require every ranked candidate to terminate as exactly one "
                    "promotion, explicit guard block, or first-blocker prune receipt."
                ),
                "evidence": [
                    f"incomplete_generation_count={incomplete_generations}",
                    f"immutable_metadata_conflict_count={immutable_metadata_conflicts}",
                    "structural_contract_conflict_generation_count="
                    f"{conservation.get('structural_contract_conflict_generation_count', 0)}",
                    f"incomplete_conservation_rows_sample={incomplete_rows}",
                    f"structural_contract_conflict_rows_sample={structural_rows}",
                    "immutable_metadata_conflict_rows_sample="
                    f"{scanner_funnel.get('immutable_metadata_conflict_rows_sample', [])}",
                ],
                "files_likely_touched": [
                    "src/scanners/scalping_scanner.py",
                    "src/engine/monitoring/intraday_ws_freshness_monitor.py",
                    "src/tests/test_scalping_scanner_candidate_pool.py",
                    "src/tests/test_intraday_ws_freshness_monitor.py",
                ],
                "acceptance_tests": [
                    "ranked_candidate_count=unique_promoted_plus_unique_pruned_per_generation",
                    "incomplete_generation_count=0",
                    "immutable_metadata_conflict_count=0",
                    "structural_contract_conflict_generation_count=0",
                ],
            }
        )
    economic_candidate_count = sum(
        int(economic_cohorts.get(key) or 0)
        for key in (
            "eligible_no_heavy",
            "heavy_then_stale_queue_evict",
            "non_gainer_not_rising_repeat",
            "market_gainer_reentry_cooldown",
            "market_gainer_reserved_full",
            "general_slot_limit",
        )
    )
    prune_observer_acceptance = prune_observer_summary.get("acceptance") or {}
    prune_observer_acceptance_pending = bool(
        int(prune_observer_summary.get("eligible_episode_census_count") or 0) > 0
        and not bool(prune_observer_acceptance.get("acceptance_ready"))
    )
    if economic_candidate_count and (
        economic_cohorts.get("executable_bbo_ev_status")
        != "source_only_economics_available"
        or prune_observer_acceptance_pending
    ):
        source_capture_implementation_state = str(
            (economic_cohorts.get("executable_bbo_attribution") or {}).get(
                "source_capture_implementation_state"
            )
            or "unknown"
        )
        orders.append(
            {
                **base,
                "decision_authority": SCANNER_EXECUTABLE_BBO_METRIC_CONTRACT[
                    "decision_authority"
                ],
                "forbidden_uses": SCANNER_EXECUTABLE_BBO_METRIC_CONTRACT[
                    "forbidden_uses"
                ],
                "decision": "defer_evidence",
                "next_action": (
                    "recheck_prune_observer_receipts_exact_bbo_coverage_and_"
                    "resolved_outcomes_after_next_natural_session"
                ),
                "implementation_state": source_capture_implementation_state,
                "order_id": "order_scanner_funnel_executable_bbo_join",
                "title": "Scanner funnel executable-BBO economic attribution",
                "priority": 2,
                "intent": (
                    "Preserve the full lost-scanner census while joining each explicitly selected "
                    "bounded observer episode to fresh executable bid/ask, quote age, venue/session, "
                    "fixed effective-dated costs, sampled target/adverse first-hit, and sampled timeout "
                    "exit without claiming a continuous market path or extrapolating sampled EV to the "
                    "full prune population."
                ),
                "evidence": [
                    f"economic_candidate_count={economic_candidate_count}",
                    f"economic_cohorts={economic_cohorts_evidence}",
                    f"prune_observer_summary={prune_observer_summary}",
                ],
                "files_likely_touched": [
                    "src/engine/monitoring/pruned_candidate_bbo_collector.py",
                    "src/scanners/scalping_scanner.py",
                    "src/engine/monitoring/intraday_ws_freshness_monitor.py",
                    "src/tests/test_pruned_candidate_bbo_collector.py",
                    "src/tests/test_intraday_ws_freshness_monitor.py",
                ],
                "acceptance_tests": [
                    "source_capture_preserves_active_owner_targets_and_adds_zero_ws_registrations",
                    "ka10004_requests_remain_within_process_daily_and_interval_budget",
                    "bounded_observer_selected_episode_bbo_join_coverage_pct>=95",
                    "each_selected_prune_cohort_venue_session_resolved_outcome_count>=20",
                    "each_selected_prune_cohort_venue_session_right_censored_pct<=20",
                    "full_prune_population_ev_extrapolation_allowed=false",
                    "missing_bbo_is_source_quality_blocked_not_zero_profit",
                    "KRX_PREMARKET_KRX_LIKE_NXT_results_are_separate",
                    "fixed_cost_contract_effective_date_and_source_hash_match",
                    "official_common_stock_master_exact_date_hash_and_lookup_pass",
                ],
            }
        )
    if counts.get("subscription_stale", 0) or snapshot.get(
        "repair_recommended_count", 0
    ):
        orders.append(
            {
                **base,
                "order_id": "order_ws_subscription_stale_repair_observability",
                "title": "WS subscription stale repair observability",
                "priority": 1,
                "intent": (
                    "Use intraday subscription_stale/no_tick evidence to verify REMOVE->REG recovery "
                    "timing, item budget, duplicate REG suppression, and repair cooldown provenance."
                ),
                "evidence": [
                    f"pipeline_subscription_stale_count={counts.get('subscription_stale', 0)}",
                    f"snapshot_repair_recommended_count={snapshot.get('repair_recommended_count', 0)}",
                ],
                "files_likely_touched": [
                    "src/engine/kiwoom_websocket.py",
                    "src/engine/monitoring/intraday_ws_freshness_monitor.py",
                    "src/tests/test_kiwoom_websocket.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_kiwoom_websocket.py src/tests/test_intraday_ws_freshness_monitor.py",
                ],
            }
        )
    if counts.get("decision_stage_stale_backoff", 0):
        orders.append(
            {
                **base,
                "decision": "defer_evidence",
                "next_action": "recheck_after_postclose",
                "implementation_state": "implemented_in_source_report",
                "order_id": "order_ws_decision_stage_stale_backoff_attribution",
                "title": "WS decision-stage stale backoff attribution",
                "priority": 1,
                "intent": (
                    "Attribute explicit scanner stale/backoff rows to subscription repair, "
                    "decision-stage freshness, and watchlist eviction timing without weakening "
                    "the stale submit boundary."
                ),
                "evidence": [
                    "decision_stage_stale_backoff_count="
                    f"{counts.get('decision_stage_stale_backoff', 0)}",
                    "causal_attribution="
                    f"{causal.get('decision_stage_stale_backoff', {})}",
                ],
                "files_likely_touched": [
                    "src/engine/kiwoom_websocket.py",
                    "src/engine/sniper_state_handlers.py",
                    "src/engine/monitoring/intraday_ws_freshness_monitor.py",
                    "src/tests/test_intraday_ws_freshness_monitor.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/python -m pytest -q "
                    "src/tests/test_kiwoom_websocket.py "
                    "src/tests/test_intraday_ws_freshness_monitor.py",
                ],
            }
        )
    if counts.get("trade_tick_quiet", 0) or snapshot.get("trade_tick_quiet_count", 0):
        orders.append(
            {
                **base,
                "decision": "defer_evidence",
                "next_action": "recheck_after_postclose",
                "implementation_state": (
                    "implemented_in_source_report"
                    if quiet_volume_observed_count > 0
                    else "implemented_pending_new_dashboard_snapshot"
                ),
                "order_id": "order_ws_trade_tick_quiet_low_liquidity_classification",
                "title": "WS trade tick quiet low-liquidity classification",
                "priority": 2,
                "intent": (
                    "Keep fresh 0D plus stale/missing 0B as trade_tick_quiet source-quality evidence, "
                    "and enrich low-liquidity classification with cumulative-volume provenance before "
                    "requesting subscription repair."
                ),
                "evidence": [
                    f"pipeline_trade_tick_quiet_count={counts.get('trade_tick_quiet', 0)}",
                    f"fresh_0d_stale_0b_count={counts.get('fresh_0d_stale_0b', 0)}",
                    f"snapshot_trade_tick_quiet_count={snapshot.get('trade_tick_quiet_count', 0)}",
                    "cumulative_volume_provenance="
                    f"{(causal.get('trade_tick_quiet') or {}).get('cumulative_volume_provenance_counts', {})}",
                    "snapshot_cumulative_volume_provenance="
                    f"{snapshot.get('trade_tick_quiet_cumulative_volume_provenance_counts', {})}",
                ],
                "files_likely_touched": [
                    "src/engine/kiwoom_websocket.py",
                    "src/engine/sniper_state_handlers.py",
                    "src/engine/monitoring/intraday_ws_freshness_monitor.py",
                    "src/tests/test_state_handler_fast_signatures.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_state_handler_fast_signatures.py src/tests/test_intraday_ws_freshness_monitor.py",
                ],
            }
        )
    if counts.get("both_ws_stale", 0):
        orders.append(
            {
                **base,
                "decision": "defer_evidence",
                "next_action": "recheck_after_postclose",
                "implementation_state": "implemented_in_source_report",
                "order_id": "order_ws_total_stale_escalation",
                "title": "WS total stale escalation",
                "priority": 1,
                "intent": (
                    "Treat rows where both trade and orderbook websocket freshness are stale as "
                    "subscription/connection quality incidents and verify repair evidence after postclose."
                ),
                "evidence": [
                    f"both_ws_stale_count={counts.get('both_ws_stale', 0)}",
                    "repair_attribution=" f"{causal.get('both_ws_stale', {})}",
                ],
                "files_likely_touched": [
                    "src/engine/kiwoom_websocket.py",
                    "src/engine/monitoring/quote_stale_frequency_report.py",
                    "src/engine/monitoring/intraday_ws_freshness_monitor.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_kiwoom_websocket.py src/tests/test_intraday_ws_freshness_monitor.py",
                ],
            }
        )
    if counts.get("provider_none", 0):
        orders.append(
            {
                **base,
                "order_id": "order_ai_provider_none_intraday_incident",
                "title": "AI provider none intraday incident",
                "priority": 1,
                "intent": (
                    "Investigate and close intraday AI provider provenance rows that resolved to none. "
                    "Provider route must stay explicit and must not be silently treated as healthy."
                ),
                "evidence": [f"provider_none_count={counts.get('provider_none', 0)}"],
                "files_likely_touched": [
                    "src/engine/sniper_state_handlers.py",
                    "src/engine/ai",
                    "src/engine/monitoring/intraday_ws_freshness_monitor.py",
                ],
                "acceptance_tests": [
                    "PYTHONPATH=. .venv/bin/python -m pytest -q src/tests/test_state_handler_fast_signatures.py src/tests/test_intraday_ws_freshness_monitor.py",
                ],
            }
        )
    if not orders:
        return []
    orders.sort(
        key=lambda item: (int(item.get("priority", 99)), str(item.get("order_id")))
    )
    return orders


def build_report(
    target_date: str | None = None,
    *,
    pipeline_path: Path | None = None,
    threshold_path: Path | None = None,
    subscription_snapshot_path: Path | None = None,
    stale_sec: float = DEFAULT_STALE_SEC,
    generated_at: str | None = None,
    incremental_state_path: Path | None = None,
    symbol_master_path: Path | None = None,
) -> dict[str, Any]:
    target_date = target_date or date.today().isoformat()
    stale_ms = float(stale_sec) * 1000.0
    paths = _source_paths(target_date)
    if pipeline_path is not None:
        paths["pipeline_events"] = pipeline_path
    if threshold_path is not None:
        paths["threshold_events"] = threshold_path

    source_missing = [name for name, path in paths.items() if not path.exists()]
    source_identities = {
        source_name: _source_identity(path) for source_name, path in paths.items()
    }
    cached_state, incremental_state_reason = _load_incremental_state(
        incremental_state_path,
        target_date=target_date,
        stale_ms=stale_ms,
        source_identities=source_identities,
    )
    try:
        row_count_by_source = _counter_from_mapping(
            (cached_state or {}).get("row_count_by_source")
        )
        counts = _counter_from_mapping((cached_state or {}).get("counts"))
        stage_counts = _nested_counters_from_mapping(
            (cached_state or {}).get("stage_counts")
        )
        time_bucket_counts = _nested_counters_from_mapping(
            (cached_state or {}).get("time_bucket_counts")
        )
        symbol_counts = _nested_counters_from_mapping(
            (cached_state or {}).get("symbol_counts")
        )
        provenance_counts = _nested_counters_from_mapping(
            (cached_state or {}).get("provenance_counts")
        )
        scanner_funnel_state = _scanner_funnel_state_from_mapping(
            (cached_state or {}).get("scanner_funnel_state")
        )
        total_events = int((cached_state or {}).get("total_events") or 0)
    except (TypeError, ValueError):
        cached_state = None
        incremental_state_reason = "aggregate_state_invalid"
        row_count_by_source = Counter()
        counts = Counter()
        stage_counts = defaultdict(Counter)
        time_bucket_counts = defaultdict(Counter)
        symbol_counts = defaultdict(Counter)
        provenance_counts = defaultdict(Counter)
        scanner_funnel_state = _scanner_funnel_state_from_mapping(None)
        total_events = 0
    scanner_funnel_state["_fingerprint_set"] = set(
        scanner_funnel_state.get("event_fingerprints") or []
    )
    appended_event_count = 0
    invalid_json_line_count = 0
    source_offsets: dict[str, dict[str, Any]] = {}
    for source_name, path in paths.items():
        identity = source_identities[source_name]
        cached_source = (
            (cached_state or {}).get("sources", {}).get(source_name, {})
            if cached_state
            else {}
        )
        start_offset = int(cached_source.get("offset") or 0)
        actual_path = Path(str(identity.get("path") or path))
        if identity.get("cacheable"):
            source_rows, progress = _iter_plain_jsonl_from_offset(
                actual_path,
                offset=start_offset,
            )
        else:
            source_rows = _iter_jsonl_rows(path)
            progress = {"offset": 0, "invalid_json_line_count": 0}
        source_appended_count = 0
        for raw in source_rows:
            row_count_by_source[source_name] += 1
            total_events += 1
            appended_event_count += 1
            source_appended_count += 1
            flattened = _flatten_event(raw)
            item = _pipeline_event_class(flattened, stale_ms=stale_ms)
            _update_scanner_funnel_state(
                scanner_funnel_state,
                flattened,
                item,
            )
            for key in (
                "trade_tick_quiet",
                "subscription_stale",
                "decision_stage_stale_backoff",
                "both_ws_stale",
                "fresh_0d_stale_0b",
                "provider_none",
                "submit_related",
                "scout_related",
                "ws_age_observed",
            ):
                if item.get(key):
                    counts[key] += 1
            stage = str(item.get("stage") or "unknown")
            bucket = str(item.get("time_bucket") or "unknown")
            code = str(item.get("stock_code") or "")
            for key in (
                "trade_tick_quiet",
                "subscription_stale",
                "decision_stage_stale_backoff",
                "both_ws_stale",
                "provider_none",
            ):
                if item.get(key):
                    stage_counts[key][stage] += 1
                    time_bucket_counts[key][bucket] += 1
                    if code:
                        symbol_counts[key][code] += 1
            if item.get("decision_stage_stale_backoff"):
                for dimension in (
                    "stale_backoff_reason",
                    "stale_backoff_repair_cycle_state",
                    "stale_backoff_recheck_reason",
                    "stale_backoff_watchlist_outcome",
                ):
                    provenance_counts[dimension][str(item.get(dimension))] += 1
            if item.get("both_ws_stale"):
                provenance_counts["both_ws_stale_repair_cycle_state"][
                    str(item.get("stale_backoff_repair_cycle_state"))
                ] += 1
                provenance_counts["both_ws_stale_repair_required"][
                    str(item.get("both_ws_stale_repair_required"))
                ] += 1
            if item.get("trade_tick_quiet"):
                provenance_counts["trade_tick_quiet_volume_provenance"][
                    str(item.get("trade_tick_quiet_volume_provenance"))
                ] += 1
        invalid_json_line_count += int(progress["invalid_json_line_count"])
        end_identity = _source_identity(actual_path)
        source_identity_stable = bool(
            identity.get("device") == end_identity.get("device")
            and identity.get("inode") == end_identity.get("inode")
        )
        source_offsets[source_name] = {
            **(end_identity if source_identity_stable else identity),
            "offset": int(progress["offset"]),
            "start_offset": start_offset,
            "appended_event_count": source_appended_count,
            "source_identity_stable_during_scan": source_identity_stable,
        }

    incremental_state_persisted = bool(
        incremental_state_path is not None
        and all(identity.get("cacheable") for identity in source_identities.values())
        and all(
            source.get("source_identity_stable_during_scan")
            for source in source_offsets.values()
        )
    )
    if incremental_state_persisted and incremental_state_path is not None:
        _write_incremental_state(
            incremental_state_path,
            {
                "schema_version": INCREMENTAL_STATE_SCHEMA_VERSION,
                "target_date": target_date,
                "stale_ms": stale_ms,
                "sources": {
                    source_name: {
                        "path": source.get("path"),
                        "device": source.get("device"),
                        "inode": source.get("inode"),
                        "offset": source.get("offset"),
                    }
                    for source_name, source in source_offsets.items()
                },
                "row_count_by_source": dict(row_count_by_source),
                "counts": dict(counts),
                "stage_counts": {
                    key: dict(counter) for key, counter in stage_counts.items()
                },
                "time_bucket_counts": {
                    key: dict(counter) for key, counter in time_bucket_counts.items()
                },
                "symbol_counts": {
                    key: dict(counter) for key, counter in symbol_counts.items()
                },
                "provenance_counts": {
                    key: dict(counter) for key, counter in provenance_counts.items()
                },
                "scanner_funnel_state": {
                    key: value
                    for key, value in {
                        **scanner_funnel_state,
                        "event_fingerprints": sorted(
                            scanner_funnel_state.get("_fingerprint_set") or set()
                        ),
                    }.items()
                    if key != "_fingerprint_set"
                },
                "total_events": total_events,
            },
        )

    (
        resolved_snapshot_path,
        snapshot_payload,
        snapshot_provenance,
    ) = _resolve_snapshot(subscription_snapshot_path, target_date=target_date)
    snapshot_rows = _snapshot_rows(snapshot_payload, stale_ms=stale_ms)
    snapshot = _snapshot_summary(snapshot_rows)
    symbol_master, symbol_master_binding = _load_verified_symbol_master(
        target_date, symbol_master_path
    )
    scanner_unique_funnel = _scanner_unique_funnel_summary(
        scanner_funnel_state,
        target_date=target_date,
        symbol_master=symbol_master,
        symbol_master_binding=symbol_master_binding,
    )

    summary = {
        "target_date": target_date,
        "generated_at": generated_at or datetime.now(tz=KST).isoformat(),
        "report_type": REPORT_TYPE,
        "metric_contract": METRIC_CONTRACT,
        "decision_stage_stale_backoff_metric_contract": (
            DECISION_STAGE_STALE_BACKOFF_METRIC_CONTRACT
        ),
        "source_paths": {name: str(path) for name, path in paths.items()},
        "official_symbol_master_binding": symbol_master_binding,
        "source_missing": source_missing,
        "input_processing": {
            "mode": (
                "incremental_streaming_aggregation"
                if cached_state is not None
                else "full_streaming_rebuild"
            ),
            "memory_bounded_streaming": True,
            "retained_state_scope": "daily_unique_scanner_lineages_and_relevant_event_hashes",
            "memory_growth_bound": (
                "O(daily_unique_scanner_promotions+daily_unique_prunes+"
                "daily_scanner_timing_and_runtime_receipts+"
                "daily_relevant_event_fingerprints)"
            ),
            "full_event_list_materialized": False,
            "aggregated_event_count": total_events,
            "appended_event_count": appended_event_count,
            "invalid_json_line_count": invalid_json_line_count,
            "incremental_state_reason": incremental_state_reason,
            "incremental_state_path": (
                str(incremental_state_path) if incremental_state_path else None
            ),
            "incremental_state_persisted": incremental_state_persisted,
            "source_offsets": source_offsets,
        },
        "subscription_snapshot_path": (
            str(resolved_snapshot_path) if resolved_snapshot_path else None
        ),
        "subscription_snapshot_provenance": snapshot_provenance,
        "row_count_by_source": dict(row_count_by_source),
        "pipeline_counts": dict(counts),
        "pipeline_event_count": total_events,
        "pipeline_rates": {
            "trade_tick_quiet_rate_pct": _rate_pct(
                int(counts.get("trade_tick_quiet", 0)), total_events
            ),
            "subscription_stale_rate_pct": _rate_pct(
                int(counts.get("subscription_stale", 0)), total_events
            ),
            "decision_stage_stale_backoff_rate_pct": _rate_pct(
                int(counts.get("decision_stage_stale_backoff", 0)), total_events
            ),
            "both_ws_stale_rate_pct": _rate_pct(
                int(counts.get("both_ws_stale", 0)), total_events
            ),
            "provider_none_rate_pct": _rate_pct(
                int(counts.get("provider_none", 0)), total_events
            ),
        },
        "snapshot_summary": snapshot,
        "scanner_unique_funnel": scanner_unique_funnel,
        "by_stage": {
            key: _counter_rows(counter, key_name="stage")
            for key, counter in sorted(stage_counts.items())
        },
        "by_time_bucket": {
            key: _counter_rows(counter, key_name="time_bucket")
            for key, counter in sorted(time_bucket_counts.items())
        },
        "by_symbol": {
            key: _counter_rows(counter, key_name="stock_code")
            for key, counter in sorted(symbol_counts.items())
        },
        "causal_attribution": {
            "decision_stage_stale_backoff": {
                "sample_count": int(counts.get("decision_stage_stale_backoff", 0)),
                "reason_counts": dict(
                    provenance_counts.get("stale_backoff_reason", Counter())
                ),
                "repair_cycle_state_counts": dict(
                    provenance_counts.get("stale_backoff_repair_cycle_state", Counter())
                ),
                "recheck_reason_counts": dict(
                    provenance_counts.get("stale_backoff_recheck_reason", Counter())
                ),
                "watchlist_outcome_counts": dict(
                    provenance_counts.get("stale_backoff_watchlist_outcome", Counter())
                ),
            },
            "both_ws_stale": {
                "sample_count": int(counts.get("both_ws_stale", 0)),
                "repair_cycle_state_counts": dict(
                    provenance_counts.get("both_ws_stale_repair_cycle_state", Counter())
                ),
                "repair_required_counts": dict(
                    provenance_counts.get("both_ws_stale_repair_required", Counter())
                ),
            },
            "trade_tick_quiet": {
                "sample_count": int(counts.get("trade_tick_quiet", 0)),
                "cumulative_volume_provenance_counts": dict(
                    provenance_counts.get(
                        "trade_tick_quiet_volume_provenance", Counter()
                    )
                ),
            },
        },
    }
    workorders = _build_workorders(summary, target_date=target_date)
    workorder_decision_counts = Counter(
        str(item.get("decision") or "unspecified") for item in workorders
    )
    summary["workorder_directives"] = workorders
    summary["workorder_summary"] = {
        "selected_order_count": len(workorders),
        "decision_counts": dict(sorted(workorder_decision_counts.items())),
        "implement_now_runtime_effect_false_count": sum(
            1
            for item in workorders
            if item.get("decision") == "implement_now"
            and item.get("runtime_effect") is False
        ),
        "defer_evidence_count": sum(
            1 for item in workorders if item.get("decision") == "defer_evidence"
        ),
        "design_family_candidate_count": sum(
            1
            for item in workorders
            if item.get("decision") == "design_family_candidate"
        ),
        "provider_none_incident_count": int(counts.get("provider_none", 0)),
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    return summary


def _render_monitor_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Intraday WS Freshness Monitor - {report.get('target_date')}",
        "",
        "## Decision",
        "",
    ]
    workorder_count = (report.get("workorder_summary") or {}).get(
        "selected_order_count", 0
    )
    if workorder_count:
        lines.append(
            f"- postclose_workorder_required: `{workorder_count}` source-only directives"
        )
    else:
        lines.append("- postclose_workorder_required: `0`")
    lines.extend(
        [
            "- runtime_effect: `false`",
            "- allowed_runtime_apply: `false`",
            "",
            "## Evidence",
            "",
            f"- pipeline_event_count: `{report.get('pipeline_event_count')}`",
            f"- input_processing: `{report.get('input_processing')}`",
            f"- pipeline_counts: `{report.get('pipeline_counts')}`",
            f"- pipeline_rates: `{report.get('pipeline_rates')}`",
            f"- causal_attribution: `{report.get('causal_attribution')}`",
            f"- scanner_unique_funnel: `{report.get('scanner_unique_funnel')}`",
            "- subscription_snapshot_path: "
            f"`{report.get('subscription_snapshot_path')}`",
            "- subscription_snapshot_provenance: "
            f"`{report.get('subscription_snapshot_provenance')}`",
            f"- snapshot_summary: `{report.get('snapshot_summary')}`",
            f"- source_missing: `{report.get('source_missing')}`",
            "",
            "## Metric Contract",
            "",
            f"- metric_role: `{METRIC_CONTRACT['metric_role']}`",
            f"- decision_authority: `{METRIC_CONTRACT['decision_authority']}`",
            f"- primary_decision_metric: `{METRIC_CONTRACT['primary_decision_metric']}`",
            f"- forbidden_uses: `{','.join(FORBIDDEN_USES)}`",
            "",
            "## Workorder Directives",
            "",
        ]
    )
    orders = report.get("workorder_directives") or []
    if not orders:
        lines.append("- none")
    for order in orders:
        lines.append(
            "- "
            f"`{order.get('order_id')}` priority={order.get('priority')} "
            f"decision={order.get('decision')} "
            f"runtime_effect={order.get('runtime_effect')} title={order.get('title')}"
        )
    return "\n".join(lines) + "\n"


def _render_workorder_markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# Intraday WS Freshness Postclose Workorder - {report.get('target_date')}",
        "",
        "Codex execution scope: implement only source-quality, instrumentation, report, provenance, and tests.",
        "",
        "## 2-Pass Execution",
        "",
        "1. First pass: implement instrumentation/report/provenance fixes, run code review, fix defects, and re-review.",
        "2. Second pass: confirm final review, regenerate the related report, and inspect workorder diff.",
        "",
        "## Guardrails",
        "",
        "- runtime_effect=false",
        "- allowed_runtime_apply=false",
        "- broker_order_forbidden=true",
        f"- forbidden_uses={','.join(FORBIDDEN_USES)}",
        "",
        "## Selected Directives",
        "",
    ]
    orders = report.get("workorder_directives") or []
    if not orders:
        lines.append("- none")
    for order in orders:
        lines.extend(
            [
                f"### {order.get('order_id')}",
                "",
                f"- decision: `{order.get('decision')}`",
                f"- priority: `{order.get('priority')}`",
                f"- title: {order.get('title')}",
                f"- intent: {order.get('intent')}",
                f"- evidence: `{order.get('evidence')}`",
                f"- files_likely_touched: `{order.get('files_likely_touched')}`",
                f"- acceptance_tests: `{order.get('acceptance_tests')}`",
                "",
            ]
        )
    lines.extend(
        [
            "## Required Final Report Split",
            "",
            "- Existing implementation",
            "- New implementation",
            "- Deferred or non-implement items",
            "",
        ]
    )
    return "\n".join(lines)


def write_report(
    report: dict[str, Any], *, monitor_only: bool = False
) -> tuple[Path, Path, Path | None, Path | None]:
    target_date = str(report.get("target_date") or date.today().isoformat())
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    monitor_json = REPORT_DIR / f"{REPORT_TYPE}_{target_date}.json"
    monitor_md = REPORT_DIR / f"{REPORT_TYPE}_{target_date}.md"

    monitor_json.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    monitor_md.write_text(_render_monitor_markdown(report), encoding="utf-8")
    if monitor_only:
        return monitor_json, monitor_md, None, None

    WORKORDER_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    WORKORDER_DOC_DIR.mkdir(parents=True, exist_ok=True)
    workorder_json = (
        WORKORDER_REPORT_DIR / f"intraday_ws_freshness_workorder_{target_date}.json"
    )
    workorder_md = (
        WORKORDER_DOC_DIR / f"intraday_ws_freshness_workorder_{target_date}.md"
    )
    workorder_payload = {
        "target_date": target_date,
        "source_report_type": REPORT_TYPE,
        "source_report_path": str(monitor_json),
        "metric_contract": METRIC_CONTRACT,
        "orders": report.get("workorder_directives") or [],
        "summary": report.get("workorder_summary") or {},
    }
    workorder_json.write_text(
        json.dumps(workorder_payload, ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )
    workorder_md.write_text(_render_workorder_markdown(report), encoding="utf-8")
    return monitor_json, monitor_md, workorder_json, workorder_md


def _run_once(args: argparse.Namespace) -> dict[str, Any]:
    snapshot_path = (
        Path(args.subscription_snapshot) if args.subscription_snapshot else None
    )
    report = build_report(
        args.target_date,
        pipeline_path=Path(args.pipeline_path) if args.pipeline_path else None,
        threshold_path=Path(args.threshold_path) if args.threshold_path else None,
        subscription_snapshot_path=snapshot_path,
        stale_sec=args.stale_sec,
        incremental_state_path=(
            Path(args.incremental_state_path) if args.incremental_state_path else None
        ),
        symbol_master_path=(
            Path(args.symbol_master_path) if args.symbol_master_path else None
        ),
    )
    if args.write:
        monitor_json, monitor_md, workorder_json, workorder_md = write_report(
            report,
            monitor_only=args.monitor_only,
        )
        print(
            json.dumps(
                {
                    "monitor_json": str(monitor_json),
                    "monitor_md": str(monitor_md),
                    "workorder_json": str(workorder_json) if workorder_json else None,
                    "workorder_md": str(workorder_md) if workorder_md else None,
                },
                ensure_ascii=False,
            )
        )
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", default=date.today().isoformat())
    parser.add_argument("--pipeline-path")
    parser.add_argument("--threshold-path")
    parser.add_argument("--subscription-snapshot")
    parser.add_argument("--incremental-state-path")
    parser.add_argument("--symbol-master-path")
    parser.add_argument("--stale-sec", type=float, default=DEFAULT_STALE_SEC)
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--monitor-only", action="store_true")
    parser.add_argument("--watch-iterations", type=int, default=1)
    parser.add_argument("--interval-sec", type=float, default=60.0)
    args = parser.parse_args(argv)

    iterations = max(1, int(args.watch_iterations or 1))
    for idx in range(iterations):
        _run_once(args)
        if idx < iterations - 1:
            time.sleep(max(1.0, float(args.interval_sec)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
