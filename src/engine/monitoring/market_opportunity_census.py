"""Observe market-wide gainers independently from the live scanner universe.

The census is source-only instrumentation. It never contributes candidates to
the live scanner and has no order, threshold, provider-route, or restart
authority.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import subprocess
import time
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable, Iterable

from src.engine.monitoring.entry_turn_point_replay import (
    PRE_ANCHOR_BUNDLE_SCHEMA_VERSION,
    decode_pre_anchor_ws_bbo_bundle,
)
from src.engine.monitoring.pruned_candidate_bbo_collector import (
    OBSERVATION_SCHEMA_VERSION as PRUNE_BBO_OBSERVATION_SCHEMA_VERSION,
)
from src.engine.monitoring.widget_comparison_cost import comparison_cost_contract
from src.engine.scalping.micro_reversion.symbol_master import VerifiedSymbolMaster
from src.utils import kiwoom_utils
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import (
    existing_or_gzip_path,
    iter_jsonl,
    iter_jsonl_objects_strict,
    read_json_object_strict_receipt,
)

try:
    import fcntl
except ImportError:  # pragma: no cover - non-Unix fallback
    fcntl = None

KST = timezone(timedelta(hours=9))
REPORT_TYPE = "market_opportunity_census"
SNAPSHOT_SCHEMA_VERSION = "market_opportunity_census_v1"
REPORT_SCHEMA_VERSION = "market_opportunity_census_v3"
# Backward-compatible snapshot schema alias used by existing capture fixtures.
SCHEMA_VERSION = SNAPSHOT_SCHEMA_VERSION
SNAPSHOT_DIR = DATA_DIR / "market_opportunity_census"
REPORT_DIR = DATA_DIR / "report" / REPORT_TYPE
PIPELINE_DIR = DATA_DIR / "pipeline_events"
AI_TRACE_DIR = DATA_DIR / "ai_decision_trace"
TOP_N_WINDOWS = (10, 20, 50)
CAPTURE_CADENCE_SEC = 300
CAPTURE_CADENCE_TOLERANCE_SEC = 60
SCANNER_DETECTION_SLA_SEC = 120
OPPORTUNITY_VALIDITY_SEC = 300
OPPORTUNITY_EPISODE_RESET_GAP_SEC = 600
MIN_VALID_CAPTURE_TIMES_PER_VENUE_PANEL = 3
MIN_PRIMARY_OPPORTUNITY_EPISODES = 20
EX_POST_HORIZONS_SEC = (60, 180, 300, 600, 1200, 1800, 3600)
EX_POST_PRIMARY_HORIZON_SEC = 1200
EX_POST_TARGET_PCT = 0.50
EX_POST_ADVERSE_PCT = -0.50
EX_POST_MAX_ENTRY_SPREAD_BPS = 50.0
EX_POST_MAX_QUOTE_AGE_MS = 1_000.0
EX_POST_MAX_SCHEDULE_LAG_SEC = 2.0
EX_POST_TIMEOUT_MAX_LAG_SEC = 5.0
EX_POST_ENTRY_COVERAGE_FLOOR_PCT = 95.0
EX_POST_RIGHT_CENSORED_MAX_PCT = 20.0
EX_POST_MIN_RESOLVED_COUNT = 20
EXTERNAL_BBO_OBSERVATION_SCHEMA_VERSION = (
    "market_opportunity_external_bbo_observation_v1"
)
EXTERNAL_BBO_CAPTURE_TOP_N = 20
EXTERNAL_BBO_MIN_REQUEST_INTERVAL_SEC = 0.25
EXTERNAL_BBO_MAX_REQUESTS_PER_RUN = 40
EXTERNAL_BBO_MAX_REQUESTS_PER_KST_DATE = 4_800
EXTERNAL_BBO_BUDGET_DIR = DATA_DIR / "runtime" / REPORT_TYPE
EXTERNAL_BBO_BUDGET_SCHEMA_VERSION = "market_opportunity_external_bbo_budget_v1"
DEFAULT_SYMBOL_MASTER_DIR = DATA_DIR / "report" / "micro_reversion_economic_reference"
DEFAULT_TRIGGER_RECEIPT = (
    DATA_DIR / "runtime" / "market_opportunity_census" / "installed_trigger.json"
)
DEFAULT_TRIGGER_WRAPPER = (
    Path(__file__).resolve().parents[3]
    / "deploy"
    / "run_market_opportunity_census_intraday.sh"
)
TRIGGER_SCHEMA_VERSION = "market_opportunity_census_trigger_v2"
EXPECTED_TRIGGER_LINE_COUNT = 5
EXPECTED_TRIGGER_SCHEDULE_PREFIXES = (
    "*/5 8 * * 1-5 ",
    "*/5 9-14 * * 1-5 ",
    "0-30/5 15 * * 1-5 ",
    "35-55/5 15 * * 1-5 ",
    "*/5 16-19 * * 1-5 ",
)
EXPECTED_TRIGGER_MARKERS = (
    "MARKET_OPPORTUNITY_CENSUS_NXT_PREMARKET_5MIN",
    "MARKET_OPPORTUNITY_CENSUS_KRX_NXT_5MIN",
    "MARKET_OPPORTUNITY_CENSUS_KRX_NXT_CLOSE_5MIN",
    "MARKET_OPPORTUNITY_CENSUS_NXT_TRANSITION_5MIN",
    "MARKET_OPPORTUNITY_CENSUS_NXT_AFTERMARKET_5MIN",
)

FORBIDDEN_USES = [
    "standalone_buy",
    "live_candidate_injection",
    "score_or_threshold_mutation",
    "provider_or_model_change",
    "order_price_or_quantity_change",
    "broker_or_account_guard_bypass",
    "stale_or_source_conflict_bypass",
    "upper_limit_chase_authority",
    "bot_restart",
    "real_execution_quality_approval",
    "bounded_bbo_observer_ev_extrapolation_to_full_external_population",
]
METRIC_CONTRACT = {
    "metric_role": "scanner_market_opportunity_coverage",
    "decision_authority": "source_only_scanner_coverage_audit",
    "window_policy": "exact_capture_timestamp_venue_panel_then_forward_pipeline",
    "sample_floor": {
        "minimum_valid_capture_times_per_venue_panel": (
            MIN_VALID_CAPTURE_TIMES_PER_VENUE_PANEL
        ),
        "minimum_unique_opportunity_episodes": MIN_PRIMARY_OPPORTUNITY_EPISODES,
        "capture_cadence_sec": CAPTURE_CADENCE_SEC,
        "capture_cadence_tolerance_sec": CAPTURE_CADENCE_TOLERANCE_SEC,
        "scanner_detection_sla_sec": SCANNER_DETECTION_SLA_SEC,
        "opportunity_validity_sec": OPPORTUNITY_VALIDITY_SEC,
        "opportunity_episode_reset_gap_sec": OPPORTUNITY_EPISODE_RESET_GAP_SEC,
    },
    "primary_decision_metric": "entry_ai_provider_reach_rate_pct",
    "primary_decision_scope": {
        "panel": "liquid_common",
        "top_n": 20,
        "view": "forward_exact",
        "grouping": "venue",
        "formula": (
            "unique_opportunity_episodes_reaching_provider_within_validity / "
            "unique_opportunity_episodes * 100"
        ),
        "cross_venue_aggregation_authority": "diagnostic_only",
    },
    "secondary_diagnostic_metrics": {
        "scanner_to_entry_ai_decision_latency_sec": (
            "first same-promotion-lineage provider-backed decision timestamp "
            "minus scanner promotion"
        ),
        "terminal_coverage_reason_counts": (
            "first missing funnel owner or post-AI/submit terminal state"
        ),
        "candidate_not_promoted_first_reason_counts": (
            "first scanner_prune_reason by event time among unique opportunity "
            "episodes whose terminal coverage reason is candidate_not_promoted; "
            "reason_missing is an explicit source-quality diagnostic bucket"
        ),
        "ex_post_executable_opportunity": (
            "first exact-route source-qualified BBO at or after benchmark crossing "
            "within opportunity validity, followed by action-neutral executable-bid "
            "first-observed target/adverse and timeout outcomes on the declared "
            "bounded schedule at 1/3/5/10/20/30/60m"
        ),
    },
    "source_quality_gate": (
        "kiwoom_ka10027_success_same_venue_session_timestamp_official_master_"
        "normalized_source_payload_hash_installed_trigger_and_scanner_lineage_"
        "plus_exact_route_bbo_price_quantity_receipt_time_and_effective_cost_for_"
        "ex_post_economics"
    ),
    "forbidden_uses": FORBIDDEN_USES,
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
    "market_data_request_effect": True,
}

VENUE_REQUEST_CODES = {"KRX": "1", "NXT": "2"}
PANEL_CONTRACTS = {
    "all": {
        "trde_qty_cnd": "0000",
        "stk_cnd": "0",
        "pric_cnd": "0",
        "trde_prica_cnd": "0",
    },
    "liquid_common": {
        "trde_qty_cnd": "0010",
        "stk_cnd": "4",
        "pric_cnd": "8",
        "trde_prica_cnd": "10",
    },
}

PIPELINE_STAGE_MAP = {
    "source_seen": {
        "scalping_scanner_candidate_pruned",
        "scalping_scanner_candidate_promoted",
    },
    "candidate_evaluated": {
        "scalping_scanner_candidate_pruned",
        "scalping_scanner_candidate_promoted",
    },
    # candidate_observed is emitted on the real-source guard block path. It is
    # not the native scanner-universe denominator and must not be presented as
    # successful discovery.
    "scanner_guard_observed": {
        "scalping_scanner_candidate_observed",
        "scalping_scanner_real_source_guard_block",
    },
    "scanner_promoted": {"scalping_scanner_candidate_promoted"},
    "watch_admitted": {"scalping_scanner_candidate_promoted"},
    "runtime_watch_attached": {"scalping_scanner_runtime_target_attach"},
    "fast_precheck": {"scalping_scanner_fast_precheck"},
    "heavy_eval": {
        "scanner_async_eval_dispatched",
        "scanner_async_result_commit",
        "scalping_scanner_heavy_eval_completion",
    },
    "entry_authority_decided": {
        "scalp_entry_action_decision_snapshot",
        "pre_submit_entry_ai_authority_guard_block",
    },
    "submit_safety_checked": {
        "entry_submit_revalidation_warning",
        "entry_submit_revalidation_block",
        "order_bundle_submitted",
    },
    "submitted": {"order_bundle_submitted", "order_leg_sent"},
}
STAGE_ORDER = (
    "source_seen",
    "candidate_evaluated",
    "scanner_guard_observed",
    "scanner_promoted",
    "watch_admitted",
    "runtime_watch_attached",
    "fast_precheck",
    "heavy_eval",
    "entry_ai_trace",
    "entry_ai_provider_called",
    "entry_authority_decided",
    "submit_safety_checked",
    "submitted",
)
ENTRY_AI_ENDPOINTS = {"analyze_target", "scalping_entry"}


def _safe_code(value: Any) -> str:
    text = str(value or "").strip()
    if text.startswith("A") and len(text) >= 7:
        text = text[1:]
    return text[:6]


def _safe_float(value: Any) -> float | None:
    if value in (None, "", "-"):
        return None
    try:
        parsed = float(str(value).replace(",", "").replace("+", "").replace("%", ""))
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _lineage_value(value: Any) -> str:
    text = str(value or "").strip()
    if not text or text == "-" or text.lower().startswith("not_applicable"):
        return ""
    return text


def _parse_ts(value: Any) -> datetime | None:
    text = str(value or "").strip()
    if not text:
        return None
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KST)
    return parsed.astimezone(KST)


def _normalize_event_venue(value: Any) -> str:
    text = str(value or "").strip().upper()
    if not text:
        return "UNKNOWN"
    if (
        "INTEGRATED" in text
        or "COMBINED" in text
        or text in {"SOR", "KRX+NXT", "KRX_NXT"}
    ):
        return "UNKNOWN"
    if "NXT" in text and "KRX" not in text:
        return "NXT"
    if text in {"NXT", "NXT_REGULAR_OVERLAP", "NXT_AFTERMARKET"}:
        return "NXT"
    if "PREMARKET" in text or text.startswith("KRX") or text == "KRX":
        return "KRX"
    return "UNKNOWN"


def _event_venue(row: dict[str, Any]) -> str:
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    for value in (
        row.get("effective_venue"),
        row.get("venue"),
        fields.get("effective_venue"),
        fields.get("venue"),
        fields.get("market_data_effective_venue"),
    ):
        normalized = _normalize_event_venue(value)
        if normalized != "UNKNOWN":
            return normalized
    return "UNKNOWN"


def _capture_id(*, target_date: str, captured_at: str, venue: str, panel: str) -> str:
    raw = f"{target_date}|{captured_at}|{venue}|{panel}|ka10027"
    return "moc-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:20]


def _normalized_source_payload_sha256(
    *, request_contract: dict[str, Any], rows: list[dict[str, Any]]
) -> str:
    """Hash the sanitized request contract and normalized response rows."""
    payload = {
        "request_contract": request_contract,
        "rows": rows,
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _session_for_capture(*, venue: str, captured_at: datetime) -> str:
    minute = captured_at.hour * 60 + captured_at.minute
    if venue == "KRX":
        if 8 * 60 + 30 <= minute < 9 * 60:
            return "PREMARKET_KRX_LIKE"
        if 9 * 60 <= minute <= 15 * 60 + 30:
            return "KRX_REGULAR"
        return "OUTSIDE_KRX_BUY_WINDOW"
    if 8 * 60 <= minute < 9 * 60:
        return "NXT_PREMARKET"
    if 9 * 60 <= minute <= 15 * 60 + 30:
        return "NXT_REGULAR_OVERLAP"
    if 15 * 60 + 30 < minute <= 20 * 60:
        return "NXT_AFTERMARKET"
    return "OUTSIDE_NXT_BUY_WINDOW"


def _opportunity_episode_id(
    *,
    target_date: str,
    venue: str,
    session: str,
    stock_code: str,
    first_census_at: datetime,
) -> str:
    raw = "|".join(
        (
            target_date,
            venue,
            session,
            stock_code,
            first_census_at.isoformat(),
            str(OPPORTUNITY_VALIDITY_SEC),
            str(OPPORTUNITY_EPISODE_RESET_GAP_SEC),
        )
    )
    return "MOC-EPI-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


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
    as_of = date.fromisoformat(target_date)
    candidates: list[tuple[date, bool, Path]] = []
    for pattern in (
        "micro_reversion_symbol_master_*.json",
        "micro_reversion_symbol_master_*.json.gz",
    ):
        for path in DEFAULT_SYMBOL_MASTER_DIR.glob(pattern):
            source_date = _logical_symbol_master_date(path)
            if source_date is not None and source_date <= as_of:
                candidates.append((source_date, path.name.endswith(".json"), path))
    if not candidates:
        return None
    return max(candidates)[-1]


def _load_symbol_master_binding(
    target_date: str,
    *,
    symbol_master_path: Path | None,
) -> tuple[VerifiedSymbolMaster | None, dict[str, Any]]:
    selected = symbol_master_path or _select_symbol_master_path(target_date)
    if selected is None:
        return None, {
            "status": "missing",
            "path": None,
            "source_date": None,
            "artifact_sha256": None,
        }
    try:
        receipt = read_json_object_strict_receipt(selected)
        payload = receipt.payload
        master = VerifiedSymbolMaster.from_payload(
            payload,
            require_canonical_owner=True,
        )
        source_date = _logical_symbol_master_date(receipt.logical_path)
        if source_date is None or source_date > date.fromisoformat(target_date):
            raise ValueError("symbol_master_source_date_invalid")
    except (FileNotFoundError, OSError, TypeError, ValueError) as exc:
        return None, {
            "status": "invalid",
            "path": str(selected),
            "source_date": None,
            "artifact_sha256": None,
            "reason": type(exc).__name__,
        }
    return master, {
        "status": "verified",
        "path": str(receipt.logical_path),
        "physical_path": str(receipt.physical_path),
        "source_date": source_date.isoformat(),
        "artifact_sha256": receipt.decoded_sha256,
        "content_sha256": payload.get("content_sha256"),
        "artifact_id": payload.get("artifact_id"),
        "record_count": master.record_count,
    }


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_trigger_lines_sha256(lines: Iterable[str]) -> str:
    canonical = "\n".join(str(line).rstrip() for line in lines) + "\n"
    return _sha256_bytes(canonical.encode("utf-8"))


def _read_installed_crontab() -> str | None:
    try:
        result = subprocess.run(
            ["crontab", "-l"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5,
        )
    except (FileNotFoundError, OSError, subprocess.SubprocessError):
        return None
    return result.stdout if result.returncode == 0 else None


def _load_trigger_contract(
    path: Path | None,
    *,
    installed_crontab_text: str | None = None,
    system_timezone: str | None = None,
) -> dict[str, Any]:
    selected = path or DEFAULT_TRIGGER_RECEIPT
    try:
        receipt = read_json_object_strict_receipt(selected)
        payload = receipt.payload
    except (FileNotFoundError, OSError, TypeError, ValueError):
        return {
            "status": "missing",
            "path": str(selected),
            "capture_cadence_sec": None,
        }
    try:
        cadence_sec = int(payload.get("capture_cadence_sec") or 0)
    except (TypeError, ValueError):
        cadence_sec = 0
    trigger_lines = payload.get("trigger_lines")
    if not isinstance(trigger_lines, list):
        trigger_lines = []
    trigger_lines = [str(line).rstrip() for line in trigger_lines if str(line).strip()]
    installed_exec_start = str(payload.get("installed_exec_start") or "")
    wrapper_path = Path(installed_exec_start) if installed_exec_start else None
    wrapper_sha256 = None
    wrapper_executable = False
    if wrapper_path is not None:
        try:
            wrapper_sha256 = _sha256_bytes(wrapper_path.read_bytes())
            wrapper_executable = os.access(wrapper_path, os.X_OK)
        except OSError:
            pass
    actual_crontab = (
        installed_crontab_text
        if installed_crontab_text is not None
        else _read_installed_crontab()
    )
    actual_lines = (
        set(actual_crontab.splitlines()) if actual_crontab is not None else set()
    )
    trigger_lines_present = bool(trigger_lines) and all(
        line in actual_lines for line in trigger_lines
    )
    schedule_contract_valid = len(trigger_lines) == EXPECTED_TRIGGER_LINE_COUNT and all(
        line.startswith(f"{prefix}{installed_exec_start} ")
        and line.endswith(f"# {marker}")
        for line, prefix, marker in zip(
            trigger_lines,
            EXPECTED_TRIGGER_SCHEDULE_PREFIXES,
            EXPECTED_TRIGGER_MARKERS,
            strict=True,
        )
    )
    calculated_lines_sha256 = _canonical_trigger_lines_sha256(trigger_lines)
    expected_wrapper = str(DEFAULT_TRIGGER_WRAPPER)
    if system_timezone is None:
        try:
            timezone_result = subprocess.run(
                ["timedatectl", "show", "--property=Timezone", "--value"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
            )
            system_timezone = (
                timezone_result.stdout.strip()
                if timezone_result.returncode == 0
                else ""
            )
        except (OSError, subprocess.TimeoutExpired):
            system_timezone = ""
    reason_codes = []
    checks = {
        "schema_version": payload.get("schema_version") == TRIGGER_SCHEMA_VERSION,
        "enabled": payload.get("enabled") is True,
        "capture_cadence": cadence_sec == CAPTURE_CADENCE_SEC,
        "trigger_id": payload.get("trigger_id") == "MARKET_OPPORTUNITY_CENSUS_5MIN",
        "contract_source": (
            payload.get("contract_source") == "installed_crontab_verified"
        ),
        "schedule_timezone": (
            payload.get("schedule_timezone") == "Asia/Seoul"
            and system_timezone == "Asia/Seoul"
        ),
        "trigger_line_count": len(trigger_lines) == EXPECTED_TRIGGER_LINE_COUNT,
        "trigger_schedule": schedule_contract_valid,
        "trigger_lines_hash": (
            payload.get("trigger_lines_sha256") == calculated_lines_sha256
        ),
        "trigger_lines_installed": trigger_lines_present,
        "wrapper_path": installed_exec_start == expected_wrapper,
        "wrapper_executable": wrapper_executable,
        "wrapper_hash": (
            bool(wrapper_sha256) and wrapper_sha256 == payload.get("wrapper_sha256")
        ),
        "source_only_authority": (
            payload.get("runtime_effect") is False
            and payload.get("allowed_runtime_apply") is False
            and payload.get("actual_order_submitted") is False
            and payload.get("broker_order_forbidden") is True
        ),
    }
    reason_codes.extend(name for name, passed in checks.items() if not passed)
    valid = all(checks.values())
    return {
        "status": "verified" if valid else "invalid",
        "reason_codes": reason_codes,
        "path": str(receipt.logical_path),
        "artifact_sha256": receipt.decoded_sha256,
        "trigger_id": payload.get("trigger_id"),
        "capture_cadence_sec": cadence_sec,
        "enabled": payload.get("enabled"),
        "installed_exec_start": installed_exec_start,
        "trigger_line_count": len(trigger_lines),
        "trigger_lines_sha256": calculated_lines_sha256,
        "trigger_lines_installed": trigger_lines_present,
        "wrapper_sha256": wrapper_sha256,
        "wrapper_executable": wrapper_executable,
    }


def _capture_external_bbo_observation(
    token: str,
    *,
    code: str,
    venue: str,
    target_date: str,
    fetcher: Callable[..., Any],
    clock: Callable[[], float],
) -> dict[str, Any]:
    request_code = f"{code}_NX" if venue == "NXT" else code
    expected_observed_venue = "NXT" if venue == "NXT" else "KRX"
    request_started_epoch = float(clock())
    source_error = ""
    request_meta: dict[str, Any] = {}
    try:
        raw = fetcher(
            token,
            request_code,
            explicit_request_code=True,
            max_retries=1,
            request_owner="market_opportunity_census.external_bbo",
            request_class="source_only",
            read_rate_max_wait_sec=1.25,
            return_meta=True,
        )
        if (
            isinstance(raw, tuple)
            and len(raw) == 2
            and isinstance(raw[1], dict)
        ):
            raw_snapshot, request_meta = raw
        else:
            raw_snapshot = raw
        snapshot = raw_snapshot if isinstance(raw_snapshot, dict) else {}
    except Exception as exc:
        snapshot = {}
        source_error = type(exc).__name__
    request_completed_epoch = float(clock())
    received_epoch = _safe_float(snapshot.get("rest_received_ts"))
    bid = _safe_float(snapshot.get("best_bid"))
    ask = _safe_float(snapshot.get("best_ask"))
    bid_qty = _safe_float(snapshot.get("best_bid_qty"))
    ask_qty = _safe_float(snapshot.get("best_ask_qty"))
    response_code = str(snapshot.get("request_code") or "").strip().upper()
    response_symbol = _safe_code(snapshot.get("stock_code"))
    response_source = str(snapshot.get("source") or "").strip()
    status = "source_quality_gap"
    gap_reason = "empty_or_invalid_ka10004_response"
    if source_error:
        gap_reason = f"ka10004_request_exception:{source_error}"
    elif request_meta.get("rate_limit_retry_exhausted") is True or (
        request_meta.get("rate_limit_detected") is True and not snapshot
    ):
        gap_reason = "ka10004_rate_limited"
    elif request_meta.get("read_rate_control_status") == "deferred":
        gap_reason = "ka10004_shared_read_budget_deferred"
    elif response_source != "ka10004_rest_orderbook":
        gap_reason = "ka10004_source_provenance_invalid"
    elif (
        response_code != request_code
        or response_symbol != code
        or snapshot.get("explicit_request_code") is not True
    ):
        gap_reason = "ka10004_exact_request_route_mismatch"
    elif (
        received_epoch is None
        or not request_started_epoch <= received_epoch <= request_completed_epoch + 0.1
    ):
        gap_reason = "ka10004_response_received_epoch_invalid"
    elif (
        bid is None
        or ask is None
        or bid <= 0
        or ask < bid
        or not bid.is_integer()
        or not ask.is_integer()
    ):
        gap_reason = "ka10004_bbo_invalid_or_crossed"
    elif (
        bid_qty is None
        or ask_qty is None
        or bid_qty < 0
        or ask_qty < 0
        or not bid_qty.is_integer()
        or not ask_qty.is_integer()
    ):
        gap_reason = "ka10004_best_quantity_missing_or_invalid"
    elif (
        datetime.fromtimestamp(received_epoch, tz=KST).date().isoformat() != target_date
    ):
        gap_reason = "ka10004_observation_target_date_mismatch"
    else:
        status = "captured"
        gap_reason = "not_applicable_capture_pass"
    quote_age_ms = (
        max(0.0, (request_completed_epoch - received_epoch) * 1_000.0)
        if status == "captured" and received_epoch is not None
        else None
    )
    return {
        "schema_version": EXTERNAL_BBO_OBSERVATION_SCHEMA_VERSION,
        "status": status,
        "gap_reason": gap_reason,
        "request_attempted": True,
        "request_code": request_code,
        "response_request_code": response_code or None,
        "stock_code": code,
        "expected_observed_venue": expected_observed_venue,
        "request_started_epoch": round(request_started_epoch, 6),
        "request_completed_epoch": round(request_completed_epoch, 6),
        "request_owner": str(
            request_meta.get("request_owner")
            or "market_opportunity_census.external_bbo"
        ),
        "request_pid": request_meta.get("request_pid"),
        "request_class": str(request_meta.get("request_class") or "source_only"),
        "request_attempt_count": int(request_meta.get("request_attempt_count") or 0),
        "read_rate_control_status": str(
            request_meta.get("read_rate_control_status") or "meta_unavailable"
        ),
        "read_rate_control_reason": str(
            request_meta.get("read_rate_control_reason") or "meta_unavailable"
        ),
        "read_rate_control_waited_sec": float(
            request_meta.get("read_rate_control_waited_sec") or 0.0
        ),
        "rate_limit_detected": bool(request_meta.get("rate_limit_detected") is True),
        "rate_limit_retry_exhausted": bool(
            request_meta.get("rate_limit_retry_exhausted") is True
        ),
        "observed_epoch": (
            round(received_epoch, 6) if received_epoch is not None else None
        ),
        "quote_age_ms": round(quote_age_ms, 3) if quote_age_ms is not None else None,
        "best_bid": int(bid) if bid is not None and bid.is_integer() else None,
        "best_ask": int(ask) if ask is not None and ask.is_integer() else None,
        "best_bid_qty": (
            int(bid_qty) if bid_qty is not None and bid_qty.is_integer() else None
        ),
        "best_ask_qty": (
            int(ask_qty) if ask_qty is not None and ask_qty.is_integer() else None
        ),
        "price_source": "ka10004_external_market_census_exact_request_code",
        "source_quality_pass": status == "captured",
        "metric_role": "external_opportunity_executable_bbo_observation",
        "decision_authority": "external_market_census_bbo_observation_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "market_data_request_effect": True,
    }


def _external_bbo_budget_gap(*, code: str, venue: str, reason: str) -> dict[str, Any]:
    return {
        "schema_version": EXTERNAL_BBO_OBSERVATION_SCHEMA_VERSION,
        "status": "source_quality_gap",
        "gap_reason": reason,
        "request_attempted": False,
        "request_code": f"{code}_NX" if venue == "NXT" else code,
        "stock_code": code,
        "expected_observed_venue": "NXT" if venue == "NXT" else "KRX",
        "price_source": "ka10004_external_market_census_exact_request_code",
        "source_quality_pass": False,
        "metric_role": "external_opportunity_executable_bbo_observation",
        "decision_authority": "external_market_census_bbo_observation_only",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "market_data_request_effect": True,
    }


def capture_market_snapshots(
    token: str,
    *,
    target_date: str,
    captured_at: datetime | None = None,
    venues: Iterable[str] = ("KRX", "NXT"),
    panels: Iterable[str] = ("all", "liquid_common"),
    limit: int = 200,
    fetcher: Callable[..., list[dict[str, Any]]] | None = None,
    collect_executable_bbo: bool = False,
    bbo_fetcher: Callable[..., Any] | None = None,
    max_bbo_requests_per_run: int = EXTERNAL_BBO_MAX_REQUESTS_PER_RUN,
    bbo_request_reserver: Callable[[], dict[str, Any]] | None = None,
    clock: Callable[[], float] | None = None,
    monotonic_clock: Callable[[], float] | None = None,
    sleeper: Callable[[float], None] | None = None,
) -> list[dict[str, Any]]:
    """Fetch sanitized ka10027 and bounded exact-route BBO observations."""
    fetch = fetcher or kiwoom_utils.get_top_fluctuation_ka10027
    fetch_bbo = bbo_fetcher or kiwoom_utils.get_stock_orderbook_ka10004
    now_epoch = clock or time.time
    monotonic = monotonic_clock or time.monotonic
    sleep = sleeper or time.sleep
    bbo_request_budget = min(
        max(0, int(max_bbo_requests_per_run)),
        EXTERNAL_BBO_MAX_REQUESTS_PER_RUN,
    )
    bbo_request_count = 0
    last_bbo_request_started_monotonic: float | None = None
    observed_at = captured_at or datetime.now(KST)
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=KST)
    else:
        observed_at = observed_at.astimezone(KST)
    if observed_at.date().isoformat() != target_date:
        raise ValueError(
            "ka10027 snapshots can only be labeled with their actual capture date"
        )
    captured_at_text = observed_at.isoformat()
    records: list[dict[str, Any]] = []

    for raw_venue in venues:
        venue = str(raw_venue).strip().upper()
        if venue not in VENUE_REQUEST_CODES:
            raise ValueError(f"unsupported venue: {raw_venue}")
        for raw_panel in panels:
            panel = str(raw_panel).strip()
            if panel not in PANEL_CONTRACTS:
                raise ValueError(f"unsupported panel: {raw_panel}")
            request_contract = {
                "mrkt_tp": "000",
                "sort_tp": "1",
                "stex_tp": VENUE_REQUEST_CODES[venue],
                "updown_incls": "1",
                "crd_cnd": "0",
                **PANEL_CONTRACTS[panel],
            }
            source_error = ""
            source_request_meta: dict[str, Any] = {}
            try:
                fetch_result = fetch(
                    token,
                    mrkt_tp=request_contract["mrkt_tp"],
                    trde_qty_cnd=request_contract["trde_qty_cnd"],
                    limit=limit,
                    stex_tp=request_contract["stex_tp"],
                    sort_tp=request_contract["sort_tp"],
                    stk_cnd=request_contract["stk_cnd"],
                    crd_cnd=request_contract["crd_cnd"],
                    updown_incls=request_contract["updown_incls"],
                    pric_cnd=request_contract["pric_cnd"],
                    trde_prica_cnd=request_contract["trde_prica_cnd"],
                    request_owner="market_opportunity_census.ka10027",
                    request_class="source_only",
                    read_rate_max_wait_sec=1.25,
                    return_meta=True,
                )
                if (
                    isinstance(fetch_result, tuple)
                    and len(fetch_result) == 2
                    and isinstance(fetch_result[1], dict)
                ):
                    fetched, source_request_meta = fetch_result
                else:
                    fetched = fetch_result
            except Exception as exc:  # preserve sanitized source-unavailable evidence
                fetched = []
                source_error = type(exc).__name__

            if source_request_meta.get("rate_limit_retry_exhausted") is True or (
                source_request_meta.get("rate_limit_detected") is True
                and not fetched
            ):
                source_error = "ka10027_rate_limited"
            elif source_request_meta.get("read_rate_control_status") == "deferred":
                source_error = "ka10027_shared_read_budget_deferred"
            if not isinstance(fetched, list):
                fetched = []
                source_error = source_error or "ka10027_response_not_list"

            rows = []
            for rank, item in enumerate(fetched[:limit], start=1):
                code = _safe_code(item.get("Code"))
                if not code:
                    continue
                normalized_row = {
                    "rank": rank,
                    "stock_code": code,
                    "stock_name": str(item.get("Name") or "").strip(),
                    "current_price": _safe_float(item.get("Price")),
                    "change_rate_pct": _safe_float(item.get("ChangeRate")),
                    "volume": _safe_float(item.get("Volume")),
                    "execution_strength": _safe_float(item.get("CntrStr")),
                    "previous_close_signal": str(item.get("PreSig") or "").strip(),
                }
                if (
                    collect_executable_bbo
                    and panel == "liquid_common"
                    and rank <= EXTERNAL_BBO_CAPTURE_TOP_N
                ):
                    if bbo_request_count >= bbo_request_budget:
                        normalized_row["executable_bbo_observation"] = (
                            _external_bbo_budget_gap(
                                code=code,
                                venue=venue,
                                reason="per_run_bbo_request_budget_exhausted",
                            )
                        )
                    elif bbo_request_reserver is None:
                        normalized_row["executable_bbo_observation"] = (
                            _external_bbo_budget_gap(
                                code=code,
                                venue=venue,
                                reason="daily_bbo_budget_reservation_not_configured",
                            )
                        )
                    else:
                        try:
                            reservation = bbo_request_reserver()
                        except Exception as exc:
                            reservation = {
                                "status": (
                                    "daily_bbo_budget_reservation_exception:"
                                    f"{type(exc).__name__}"
                                ),
                                "reserved": False,
                            }
                        if reservation.get("reserved") is not True:
                            normalized_row["executable_bbo_observation"] = (
                                _external_bbo_budget_gap(
                                    code=code,
                                    venue=venue,
                                    reason=str(
                                        reservation.get("status")
                                        or "daily_bbo_budget_reservation_failed"
                                    ),
                                )
                            )
                            rows.append(normalized_row)
                            continue
                        request_monotonic = monotonic()
                        if last_bbo_request_started_monotonic is not None:
                            remaining = EXTERNAL_BBO_MIN_REQUEST_INTERVAL_SEC - (
                                request_monotonic - last_bbo_request_started_monotonic
                            )
                            while remaining > 0:
                                sleep(remaining)
                                request_monotonic = monotonic()
                                remaining = EXTERNAL_BBO_MIN_REQUEST_INTERVAL_SEC - (
                                    request_monotonic
                                    - last_bbo_request_started_monotonic
                                )
                        last_bbo_request_started_monotonic = request_monotonic
                        normalized_row["executable_bbo_observation"] = (
                            _capture_external_bbo_observation(
                                token,
                                code=code,
                                venue=venue,
                                target_date=target_date,
                                fetcher=fetch_bbo,
                                clock=now_epoch,
                            )
                        )
                        normalized_row["executable_bbo_observation"][
                            "daily_budget_reservation"
                        ] = reservation
                        bbo_request_count += 1
                rows.append(normalized_row)

            status = "ok" if rows else "source_unavailable"
            normalized_source_payload_sha256 = _normalized_source_payload_sha256(
                request_contract=request_contract,
                rows=rows,
            )
            records.append(
                {
                    "schema_version": SCHEMA_VERSION,
                    "capture_id": _capture_id(
                        target_date=target_date,
                        captured_at=captured_at_text,
                        venue=venue,
                        panel=panel,
                    ),
                    "target_date": target_date,
                    "captured_at": captured_at_text,
                    "venue": venue,
                    "session": _session_for_capture(
                        venue=venue,
                        captured_at=observed_at,
                    ),
                    "panel": panel,
                    "source": {
                        "provider": "kiwoom",
                        "api_id": "ka10027",
                        "path": "/api/dostk/rkinfo",
                        "request_contract": request_contract,
                        "normalized_source_payload_sha256": (
                            normalized_source_payload_sha256
                        ),
                        "source_hash_scope": (
                            "sanitized_request_contract_plus_normalized_response_rows"
                        ),
                        "credential_fields_stored": [],
                        "request_control": {
                            "request_owner": source_request_meta.get(
                                "request_owner"
                            ),
                            "request_pid": source_request_meta.get("request_pid"),
                            "request_class": source_request_meta.get(
                                "request_class"
                            ),
                            "request_attempt_count": source_request_meta.get(
                                "request_attempt_count"
                            ),
                            "read_rate_control_status": source_request_meta.get(
                                "read_rate_control_status"
                            ),
                            "read_rate_control_reason": source_request_meta.get(
                                "read_rate_control_reason"
                            ),
                            "read_rate_control_waited_sec": source_request_meta.get(
                                "read_rate_control_waited_sec"
                            ),
                            "read_rate_control_scope_digest": source_request_meta.get(
                                "read_rate_control_scope_digest"
                            ),
                            "rate_limit_detected": source_request_meta.get(
                                "rate_limit_detected"
                            ),
                            "rate_limit_retry_exhausted": source_request_meta.get(
                                "rate_limit_retry_exhausted"
                            ),
                        },
                        "executable_bbo_collection": {
                            "enabled": bool(
                                collect_executable_bbo and panel == "liquid_common"
                            ),
                            "schema_version": EXTERNAL_BBO_OBSERVATION_SCHEMA_VERSION,
                            "top_n": EXTERNAL_BBO_CAPTURE_TOP_N,
                            "min_request_interval_sec": (
                                EXTERNAL_BBO_MIN_REQUEST_INTERVAL_SEC
                            ),
                            "per_run_request_cap": bbo_request_budget,
                            "daily_request_cap": (
                                EXTERNAL_BBO_MAX_REQUESTS_PER_KST_DATE
                            ),
                            "daily_budget_enforcement": (
                                "durable_pre_request_reservation_fail_closed"
                            ),
                            "market_data_request_effect": bool(
                                collect_executable_bbo and panel == "liquid_common"
                            ),
                        },
                    },
                    "source_quality_status": status,
                    "source_error": source_error,
                    "row_count": len(rows),
                    "metric_contract": METRIC_CONTRACT,
                    "rows": rows,
                }
            )
    return records


def append_snapshot_records(path: Path, records: Iterable[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("a", encoding="utf-8") as handle:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            for record in records:
                handle.write(
                    json.dumps(
                        record,
                        ensure_ascii=False,
                        separators=(",", ":"),
                        default=str,
                    )
                    + "\n"
                )
                count += 1
            handle.flush()
        finally:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    return count


def _strict_nonnegative_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    numeric = _safe_float(value)
    if numeric is None or numeric < 0 or not numeric.is_integer():
        return None
    return int(numeric)


def _external_bbo_reservation_ordinal(observation: Any) -> int | None:
    if not isinstance(observation, dict) or observation.get("request_attempted") is not True:
        return None
    reservation = observation.get("daily_budget_reservation")
    if not isinstance(reservation, dict):
        return None
    ordinal = _strict_nonnegative_int(reservation.get("attempt_ordinal"))
    daily_cap = _strict_nonnegative_int(reservation.get("daily_request_cap"))
    if not (
        reservation.get("status") == "reserved"
        and reservation.get("reserved") is True
        and ordinal is not None
        and 0 < ordinal <= EXTERNAL_BBO_MAX_REQUESTS_PER_KST_DATE
        and daily_cap == EXTERNAL_BBO_MAX_REQUESTS_PER_KST_DATE
    ):
        return None
    return ordinal


def _reserve_external_bbo_request(
    path: Path,
    *,
    target_date: str,
    limit: int = EXTERNAL_BBO_MAX_REQUESTS_PER_KST_DATE,
    initial_reserved_count: int = 0,
) -> dict[str, Any]:
    """Durably reserve one request before touching Kiwoom.

    A crash after reservation can under-use the budget, but cannot make a
    subsequent invocation exceed the persisted KST-date cap.
    """

    if fcntl is None:
        return {
            "status": "ledger_lock_unavailable",
            "reserved": False,
            "attempt_ordinal": None,
        }
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("a+", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            try:
                handle.seek(0)
                raw = handle.read().strip()
                if raw:
                    try:
                        payload = json.loads(raw)
                    except json.JSONDecodeError:
                        return {
                            "status": "ledger_invalid",
                            "reserved": False,
                            "attempt_ordinal": None,
                        }
                    if (
                        not isinstance(payload, dict)
                        or payload.get("schema_version")
                        != EXTERNAL_BBO_BUDGET_SCHEMA_VERSION
                        or payload.get("target_date") != target_date
                    ):
                        return {
                            "status": "ledger_contract_mismatch",
                            "reserved": False,
                            "attempt_ordinal": None,
                        }
                    attempted_count = _strict_nonnegative_int(
                        payload.get("reserved_request_count")
                    )
                    persisted_limit = _strict_nonnegative_int(
                        payload.get("daily_request_cap")
                    )
                    if attempted_count is None or persisted_limit != int(limit):
                        return {
                            "status": "ledger_contract_mismatch",
                            "reserved": False,
                            "attempt_ordinal": None,
                        }
                else:
                    attempted_count = max(0, int(initial_reserved_count))
                bounded_limit = max(0, int(limit))
                if attempted_count >= bounded_limit:
                    return {
                        "status": "daily_request_cap_exhausted",
                        "reserved": False,
                        "attempt_ordinal": None,
                        "reserved_request_count": attempted_count,
                        "daily_request_cap": bounded_limit,
                    }
                attempted_count += 1
                payload = {
                    "schema_version": EXTERNAL_BBO_BUDGET_SCHEMA_VERSION,
                    "target_date": target_date,
                    "reserved_request_count": attempted_count,
                    "daily_request_cap": bounded_limit,
                    "updated_at": datetime.now(KST).isoformat(),
                    "market_data_request_effect": True,
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                }
                handle.seek(0)
                handle.truncate()
                handle.write(
                    json.dumps(payload, ensure_ascii=True, sort_keys=True) + "\n"
                )
                handle.flush()
                os.fsync(handle.fileno())
                return {
                    "status": "reserved",
                    "reserved": True,
                    "attempt_ordinal": attempted_count,
                    "reserved_request_count": attempted_count,
                    "daily_request_cap": bounded_limit,
                }
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    except (OSError, OverflowError, TypeError, ValueError):
        return {
            "status": "ledger_io_or_value_error",
            "reserved": False,
            "attempt_ordinal": None,
        }


def _count_external_bbo_requests(path: Path, *, target_date: str) -> int:
    """Count pre-ledger attempted requests for safe migration."""

    count = 0
    candidates = (path, path.with_name(path.name + ".gz"))
    for candidate in candidates:
        if not candidate.exists() and not candidate.is_symlink():
            continue
        for snapshot in iter_jsonl(candidate):
            if str(snapshot.get("target_date") or "") != target_date:
                continue
            for row in snapshot.get("rows") or []:
                if not isinstance(row, dict):
                    continue
                observation = row.get("executable_bbo_observation")
                if (
                    isinstance(observation, dict)
                    and observation.get("request_attempted") is True
                ):
                    count += 1
    return count


def _load_external_bbo_budget_contract(
    path: Path,
    *,
    target_date: str,
    minimum_reserved_count: int,
) -> dict[str, Any]:
    try:
        receipt = read_json_object_strict_receipt(path)
        payload = receipt.payload
        reserved_count = _strict_nonnegative_int(
            payload.get("reserved_request_count")
        )
        daily_cap = _strict_nonnegative_int(payload.get("daily_request_cap"))
    except (FileNotFoundError, OSError, OverflowError, TypeError, ValueError):
        return {
            "status": "missing_or_invalid",
            "path": str(path),
            "reserved_request_count": None,
        }
    authority_valid = bool(
        payload.get("market_data_request_effect") is True
        and payload.get("runtime_effect") is False
        and payload.get("allowed_runtime_apply") is False
        and payload.get("actual_order_submitted") is False
        and payload.get("broker_order_forbidden") is True
    )
    valid = bool(
        payload.get("schema_version") == EXTERNAL_BBO_BUDGET_SCHEMA_VERSION
        and payload.get("target_date") == target_date
        and reserved_count is not None
        and daily_cap == EXTERNAL_BBO_MAX_REQUESTS_PER_KST_DATE
        and minimum_reserved_count <= reserved_count <= daily_cap
        and authority_valid
    )
    return {
        "status": "verified" if valid else "invalid",
        "path": str(receipt.logical_path),
        "artifact_sha256": receipt.decoded_sha256,
        "reserved_request_count": reserved_count,
        "minimum_reserved_count_from_snapshot": minimum_reserved_count,
        "daily_request_cap": daily_cap,
        "authority_valid": authority_valid,
    }


def _prune_bbo_observation(
    row: dict[str, Any], *, target_date: str
) -> tuple[dict[str, Any] | None, str]:
    """Validate one bounded exact-route ka10004 observation.

    The market census reuses already collected source-only BBOs.  It never
    creates a new broker request or substitutes the ka10027 mark price for an
    executable quote.
    """

    if str(row.get("stage") or "") != "scalping_scanner_prune_bbo_observation":
        return None, "not_prune_bbo_observation"
    code = _safe_code(row.get("stock_code"))
    emitted_at = _parse_ts(row.get("emitted_at"))
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    if not code or emitted_at is None or emitted_at.date().isoformat() != target_date:
        return None, "identity_or_target_date_invalid"
    if str(fields.get("scanner_prune_observer_status") or "") != "captured":
        return None, str(
            fields.get("scanner_prune_observer_gap_reason") or "observer_not_captured"
        )
    if str(fields.get("observation_schema_version") or "") != (
        PRUNE_BBO_OBSERVATION_SCHEMA_VERSION
    ):
        return None, "observation_schema_version_missing_or_unsupported"
    if not _boolish(fields.get("scanner_prune_observer_source_quality_pass")):
        return None, "source_quality_pass_missing"
    if not _boolish(fields.get("scanner_prune_observer_route_match")):
        return None, "exact_request_route_mismatch"
    for authority_field in (
        "actual_order_submitted",
        "runtime_effect",
        "allowed_runtime_apply",
    ):
        if authority_field not in fields:
            return None, f"{authority_field}_missing"
        if _boolish(fields.get(authority_field)):
            return None, f"{authority_field}_authority_violation"
    if not _boolish(fields.get("broker_order_forbidden")):
        return None, "broker_order_forbidden_not_proven"
    if not _boolish(fields.get("market_data_request_effect")):
        return None, "market_data_request_effect_not_proven"
    if str(fields.get("decision_authority") or "") != (
        "scanner_prune_bbo_observation_only"
    ):
        return None, "decision_authority_invalid"
    if str(fields.get("scanner_prune_observer_price_source") or "") != (
        "ka10004_rest_orderbook_exact_request_code"
    ):
        return None, "price_source_invalid"

    request_code = (
        str(fields.get("scanner_prune_observer_request_code") or "").strip().upper()
    )
    response_request_code = (
        str(fields.get("scanner_prune_observer_response_request_code") or "")
        .strip()
        .upper()
    )
    if not request_code or request_code != response_request_code:
        return None, "request_response_code_mismatch"
    if _safe_code(request_code) != code:
        return None, "request_symbol_mismatch"

    observed_epoch = _safe_float(fields.get("scanner_prune_observer_observed_epoch"))
    request_started_epoch = _safe_float(
        fields.get("scanner_prune_observer_request_started_epoch")
    )
    request_completed_epoch = _safe_float(
        fields.get("scanner_prune_observer_request_completed_epoch")
    )
    anchor_to_schedule_delay_sec = _safe_float(
        fields.get("scanner_prune_observer_anchor_to_schedule_delay_sec")
    )
    schedule_lag_sec = _safe_float(
        fields.get("scanner_prune_observer_schedule_lag_sec")
    )
    scheduled_offset_sec = _safe_float(
        fields.get("scanner_prune_observer_scheduled_offset_sec")
    )
    quote_age_ms = _safe_float(fields.get("scanner_prune_observer_quote_age_ms"))
    bid = _safe_float(fields.get("scanner_prune_observer_best_bid"))
    ask = _safe_float(fields.get("scanner_prune_observer_best_ask"))
    bid_qty = _safe_float(fields.get("scanner_prune_observer_best_bid_qty"))
    ask_qty = _safe_float(fields.get("scanner_prune_observer_best_ask_qty"))
    if any(
        value is None
        for value in (
            observed_epoch,
            request_started_epoch,
            request_completed_epoch,
            anchor_to_schedule_delay_sec,
            schedule_lag_sec,
            scheduled_offset_sec,
            quote_age_ms,
            bid,
            ask,
            bid_qty,
            ask_qty,
        )
    ):
        return None, "required_numeric_field_missing"
    assert observed_epoch is not None
    assert request_started_epoch is not None
    assert request_completed_epoch is not None
    assert anchor_to_schedule_delay_sec is not None
    assert schedule_lag_sec is not None
    assert scheduled_offset_sec is not None
    assert quote_age_ms is not None
    assert bid is not None
    assert ask is not None
    assert bid_qty is not None
    assert ask_qty is not None
    if not (
        request_started_epoch <= observed_epoch <= request_completed_epoch + 0.1
        and request_started_epoch <= request_completed_epoch
        and request_completed_epoch <= emitted_at.timestamp() + 0.1
    ):
        return None, "receipt_time_invalid"
    if (
        anchor_to_schedule_delay_sec < 0
        or anchor_to_schedule_delay_sec > EX_POST_MAX_SCHEDULE_LAG_SEC
    ):
        return None, "anchor_to_schedule_delay_outside_bound"
    if schedule_lag_sec < 0 or schedule_lag_sec > EX_POST_MAX_SCHEDULE_LAG_SEC:
        return None, "schedule_lag_outside_bound"
    if not scheduled_offset_sec.is_integer() or int(scheduled_offset_sec) not in {
        0,
        3,
        10,
        20,
        30,
        60,
        180,
        300,
        600,
        1200,
    }:
        return None, "scheduled_offset_outside_contract"
    if quote_age_ms < 0 or quote_age_ms > EX_POST_MAX_QUOTE_AGE_MS:
        return None, "quote_age_invalid_or_stale"
    observed_age_ms = (request_completed_epoch - observed_epoch) * 1_000.0
    if abs(observed_age_ms - quote_age_ms) > 100.0:
        return None, "quote_age_timestamp_mismatch"
    if bid <= 0 or ask < bid:
        return None, "bbo_invalid_or_crossed"
    if bid_qty < 0 or ask_qty < 0:
        return None, "best_quantity_negative"
    if any(not value.is_integer() for value in (bid, ask, bid_qty, ask_qty)):
        return None, "bbo_price_or_quantity_not_integral"

    explicit_venue_values = {
        _normalize_event_venue(value)
        for value in (
            row.get("effective_venue"),
            row.get("venue"),
            fields.get("effective_venue"),
            fields.get("venue"),
        )
        if str(value or "").strip()
    }
    if "UNKNOWN" in explicit_venue_values or len(explicit_venue_values) != 1:
        return None, "explicit_venue_conflict_or_invalid"
    venue = next(iter(explicit_venue_values))
    if venue not in VENUE_REQUEST_CODES:
        return None, "explicit_venue_invalid"
    observed_at = datetime.fromtimestamp(observed_epoch, tz=KST)
    if observed_at.date().isoformat() != target_date:
        return None, "observation_target_date_mismatch"
    session = _session_for_capture(venue=venue, captured_at=observed_at)
    explicit_session = str(fields.get("market_session_bucket") or "").strip().upper()
    if not explicit_session or explicit_session != session:
        return None, "session_provenance_mismatch"
    raw_effective_venue = str(fields.get("effective_venue") or "").strip().upper()
    expected_request_code = (
        f"{code}_NX"
        if venue == "NXT" or raw_effective_venue == "PREMARKET_KRX_LIKE"
        else code
    )
    if request_code != expected_request_code:
        return None, "request_code_not_exact_for_venue"
    expected_observed_venue = (
        str(fields.get("scanner_prune_observer_expected_observed_venue") or "")
        .strip()
        .upper()
    )
    route_venue = "NXT" if request_code.endswith("_NX") else "KRX"
    if expected_observed_venue != route_venue:
        return None, "expected_observed_venue_mismatch"
    observer_episode_id = str(
        fields.get("scanner_prune_observer_episode_id") or ""
    ).strip()
    if not observer_episode_id:
        return None, "observer_episode_id_missing"
    return (
        {
            "stock_code": code,
            "venue": venue,
            "session": session,
            "observed_at": observed_at,
            "observed_epoch": observed_epoch,
            "best_bid": bid,
            "best_ask": ask,
            "best_bid_qty": int(bid_qty),
            "best_ask_qty": int(ask_qty),
            "spread_bps": round((ask - bid) / ask * 10_000.0, 8),
            "quote_age_ms": quote_age_ms,
            "schedule_lag_sec": schedule_lag_sec,
            "observer_episode_id": observer_episode_id,
            "scheduled_offset_sec": int(scheduled_offset_sec),
            "timeout_max_lag_sec": EX_POST_TIMEOUT_MAX_LAG_SEC,
            "price_source": "ka10004_rest_orderbook_exact_request_code",
        },
        "pass",
    )


def _promoted_ws_bbo_observations(
    row: dict[str, Any], *, target_date: str
) -> tuple[list[dict[str, Any]], list[str]]:
    """Validate a promoted-candidate exact-route WS BBO bundle.

    This source is the scanner's already subscribed 0D stream. Reuse remains
    source-only and does not imply market-data-request, scanner, or order
    authority.
    """

    if str(row.get("stage") or "") != "rising_missed_entry_turn_pre_anchor_bbo_path":
        return [], ["not_promoted_ws_bbo_bundle"]
    emitted_at = _parse_ts(row.get("emitted_at"))
    fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
    if emitted_at is None or emitted_at.date().isoformat() != target_date:
        return [], ["promoted_ws_identity_or_target_date_invalid"]
    for authority_field in (
        "actual_order_submitted",
        "runtime_effect",
        "allowed_runtime_apply",
    ):
        if authority_field not in fields:
            return [], [f"promoted_ws_{authority_field}_missing"]
        if _boolish(fields.get(authority_field)):
            return [], [f"promoted_ws_{authority_field}_authority_violation"]
    if not _boolish(fields.get("broker_order_forbidden")):
        return [], ["promoted_ws_broker_order_forbidden_not_proven"]
    if str(fields.get("decision_authority") or "") != (
        "entry_turn_pre_anchor_existing_ws_bbo_observation_only"
    ):
        return [], ["promoted_ws_decision_authority_invalid"]

    observations, decode_gaps = decode_pre_anchor_ws_bbo_bundle(row)
    normalized: list[dict[str, Any]] = []
    gaps = [f"promoted_ws_{gap}" for gap in decode_gaps]
    for observation in observations:
        if observation.get("bundle_schema_version") != PRE_ANCHOR_BUNDLE_SCHEMA_VERSION:
            gaps.append("promoted_ws_bundle_schema_version_missing_or_unsupported")
            continue
        bid_qty = _safe_float(observation.get("best_bid_qty"))
        ask_qty = _safe_float(observation.get("best_ask_qty"))
        if (
            bid_qty is None
            or ask_qty is None
            or bid_qty < 0
            or ask_qty < 0
            or not bid_qty.is_integer()
            or not ask_qty.is_integer()
        ):
            gaps.append("promoted_ws_best_quantity_missing_or_invalid")
            continue
        observed_at = _parse_ts(observation.get("observed_at"))
        code = _safe_code(observation.get("stock_code"))
        raw_venue = str(observation.get("venue") or "").strip().upper()
        venue = "KRX" if raw_venue == "PREMARKET_KRX_LIKE" else raw_venue
        if (
            observed_at is None
            or observed_at.date().isoformat() != target_date
            or not code
            or venue not in VENUE_REQUEST_CODES
        ):
            gaps.append("promoted_ws_scope_or_target_date_invalid")
            continue
        normalized.append(
            {
                "stock_code": code,
                "venue": venue,
                "session": _session_for_capture(
                    venue=venue,
                    captured_at=observed_at,
                ),
                "observed_at": observed_at,
                "observed_epoch": observed_at.timestamp(),
                "best_bid": observation["best_bid"],
                "best_ask": observation["best_ask"],
                "best_bid_qty": int(bid_qty),
                "best_ask_qty": int(ask_qty),
                "spread_bps": observation["spread_bps"],
                "quote_age_ms": observation["quote_age_ms"],
                "schedule_lag_sec": 0.0,
                "observer_episode_id": str(
                    observation.get("scanner_promotion_id") or ""
                ),
                "scheduled_offset_sec": None,
                "timeout_max_lag_sec": EX_POST_TIMEOUT_MAX_LAG_SEC,
                "price_source": "existing_ws_route_scoped_0d_snapshot",
            }
        )
    return normalized, gaps


def _external_snapshot_bbo_observation(
    snapshot: dict[str, Any],
    row: dict[str, Any],
    *,
    target_date: str,
) -> tuple[dict[str, Any] | None, str]:
    observation = row.get("executable_bbo_observation")
    if not isinstance(observation, dict):
        return None, "external_census_bbo_contract_missing"
    if observation.get("schema_version") != EXTERNAL_BBO_OBSERVATION_SCHEMA_VERSION:
        return None, "external_census_bbo_schema_version_missing_or_unsupported"
    if observation.get("status") != "captured":
        return None, str(
            observation.get("gap_reason") or "external_census_bbo_not_captured"
        )
    if observation.get("request_attempted") is not True:
        return None, "external_census_bbo_request_attempt_not_proven"
    for authority_field in (
        "runtime_effect",
        "allowed_runtime_apply",
        "actual_order_submitted",
    ):
        if authority_field not in observation:
            return None, f"external_census_{authority_field}_missing"
        if _boolish(observation.get(authority_field)):
            return None, f"external_census_{authority_field}_authority_violation"
    if not _boolish(observation.get("broker_order_forbidden")):
        return None, "external_census_broker_order_forbidden_not_proven"
    if not _boolish(observation.get("market_data_request_effect")):
        return None, "external_census_market_data_request_effect_not_proven"
    if not _boolish(observation.get("source_quality_pass")):
        return None, "external_census_source_quality_pass_missing"
    if observation.get("decision_authority") != (
        "external_market_census_bbo_observation_only"
    ):
        return None, "external_census_decision_authority_invalid"
    if observation.get("price_source") != (
        "ka10004_external_market_census_exact_request_code"
    ):
        return None, "external_census_price_source_invalid"
    reservation_ordinal = _external_bbo_reservation_ordinal(observation)
    if reservation_ordinal is None:
        return None, "external_census_daily_budget_reservation_invalid"

    code = _safe_code(row.get("stock_code"))
    observation_code = _safe_code(observation.get("stock_code"))
    venue = str(snapshot.get("venue") or "").strip().upper()
    session = str(snapshot.get("session") or "").strip().upper()
    request_code = str(observation.get("request_code") or "").strip().upper()
    response_request_code = (
        str(observation.get("response_request_code") or "").strip().upper()
    )
    expected_request_code = f"{code}_NX" if venue == "NXT" else code
    expected_observed_venue = "NXT" if venue == "NXT" else "KRX"
    if (
        not code
        or observation_code != code
        or venue not in VENUE_REQUEST_CODES
        or request_code != expected_request_code
        or response_request_code != expected_request_code
        or observation.get("expected_observed_venue") != expected_observed_venue
    ):
        return None, "external_census_exact_request_route_or_identity_mismatch"

    observed_epoch = _safe_float(observation.get("observed_epoch"))
    request_started_epoch = _safe_float(observation.get("request_started_epoch"))
    request_completed_epoch = _safe_float(observation.get("request_completed_epoch"))
    quote_age_ms = _safe_float(observation.get("quote_age_ms"))
    bid = _safe_float(observation.get("best_bid"))
    ask = _safe_float(observation.get("best_ask"))
    bid_qty = _safe_float(observation.get("best_bid_qty"))
    ask_qty = _safe_float(observation.get("best_ask_qty"))
    if any(
        value is None
        for value in (
            observed_epoch,
            request_started_epoch,
            request_completed_epoch,
            quote_age_ms,
            bid,
            ask,
            bid_qty,
            ask_qty,
        )
    ):
        return None, "external_census_required_numeric_field_missing"
    assert observed_epoch is not None
    assert request_started_epoch is not None
    assert request_completed_epoch is not None
    assert quote_age_ms is not None
    assert bid is not None
    assert ask is not None
    assert bid_qty is not None
    assert ask_qty is not None
    if not (
        request_started_epoch <= observed_epoch <= request_completed_epoch + 0.1
        and request_started_epoch <= request_completed_epoch
    ):
        return None, "external_census_receipt_time_invalid"
    if (
        quote_age_ms < 0
        or quote_age_ms > EX_POST_MAX_QUOTE_AGE_MS
        or abs((request_completed_epoch - observed_epoch) * 1_000.0 - quote_age_ms)
        > 100.0
    ):
        return None, "external_census_quote_age_invalid_or_stale"
    if (
        bid <= 0
        or ask < bid
        or bid_qty < 0
        or ask_qty < 0
        or any(not value.is_integer() for value in (bid, ask, bid_qty, ask_qty))
    ):
        return None, "external_census_bbo_price_or_quantity_invalid"
    observed_at = datetime.fromtimestamp(observed_epoch, tz=KST)
    if (
        observed_at.date().isoformat() != target_date
        or _session_for_capture(venue=venue, captured_at=observed_at) != session
    ):
        return None, "external_census_target_date_or_session_mismatch"
    return (
        {
            "stock_code": code,
            "venue": venue,
            "session": session,
            "observed_at": observed_at,
            "observed_epoch": observed_epoch,
            "best_bid": bid,
            "best_ask": ask,
            "best_bid_qty": int(bid_qty),
            "best_ask_qty": int(ask_qty),
            "spread_bps": round((ask - bid) / ask * 10_000.0, 8),
            "quote_age_ms": quote_age_ms,
            "schedule_lag_sec": 0.0,
            "observer_episode_id": str(snapshot.get("capture_id") or ""),
            "scheduled_offset_sec": None,
            "timeout_max_lag_sec": CAPTURE_CADENCE_TOLERANCE_SEC,
            "price_source": ("ka10004_external_market_census_exact_request_code"),
        },
        "pass",
    )


def _deduplicate_executable_bbo_index(
    index: dict[str, dict[str, dict[str, list[dict[str, Any]]]]],
) -> None:
    for venue_index in index.values():
        for session_index in venue_index.values():
            for session, observations in session_index.items():
                deduplicated = {
                    (
                        observation["observed_epoch"],
                        observation["best_bid"],
                        observation["best_ask"],
                        observation["best_bid_qty"],
                        observation["best_ask_qty"],
                        observation["price_source"],
                    ): observation
                    for observation in observations
                }
                session_index[session] = sorted(
                    deduplicated.values(),
                    key=lambda item: item["observed_epoch"],
                )


def _load_stage_index(
    pipeline_path: Path,
    ai_trace_path: Path,
    *,
    target_date: str,
    executable_bbo_index: (
        dict[str, dict[str, dict[str, list[dict[str, Any]]]]] | None
    ) = None,
    executable_bbo_gap_counts: Counter[str] | None = None,
    observer_runtime_receipts: list[dict[str, Any]] | None = None,
) -> dict[str, dict[str, list[dict[str, Any]]]]:
    index: dict[str, dict[str, list[dict[str, Any]]]] = defaultdict(
        lambda: defaultdict(list)
    )
    reverse_stage: dict[str, list[str]] = defaultdict(list)
    for logical_stage, raw_stages in PIPELINE_STAGE_MAP.items():
        for raw_stage in raw_stages:
            reverse_stage[raw_stage].append(logical_stage)
    for row in iter_jsonl(existing_or_gzip_path(pipeline_path)):
        raw_stage = str(row.get("stage") or "")
        logical_stages = reverse_stage.get(raw_stage, [])
        code = _safe_code(row.get("stock_code"))
        ts = _parse_ts(row.get("emitted_at"))
        fields = row.get("fields") if isinstance(row.get("fields"), dict) else {}
        if (
            raw_stage == "scalping_scanner_prune_bbo_source_loaded"
            and ts is not None
            and ts.date().isoformat() == target_date
            and observer_runtime_receipts is not None
        ):
            observer_runtime_receipts.append(
                {
                    "emitted_at": ts,
                    "process_pid": int(
                        _safe_float(fields.get("scanner_prune_observer_process_pid"))
                        or 0
                    ),
                    "configuration_status": str(
                        fields.get("scanner_prune_observer_configuration_status") or ""
                    ),
                    "configuration_receipt_status": str(
                        fields.get(
                            "scanner_prune_observer_configuration_receipt_status"
                        )
                        or ""
                    ),
                    "observation_schema_version": str(
                        fields.get("observation_schema_version") or ""
                    ),
                    "decision_authority": str(fields.get("decision_authority") or ""),
                    "authority_contract_fields_present": all(
                        key in fields
                        for key in (
                            "runtime_effect",
                            "allowed_runtime_apply",
                            "actual_order_submitted",
                            "broker_order_forbidden",
                            "market_data_request_effect",
                        )
                    ),
                    "runtime_effect": _boolish(fields.get("runtime_effect")),
                    "allowed_runtime_apply": _boolish(
                        fields.get("allowed_runtime_apply")
                    ),
                    "actual_order_submitted": _boolish(
                        fields.get("actual_order_submitted")
                    ),
                    "broker_order_forbidden": _boolish(
                        fields.get("broker_order_forbidden")
                    ),
                    "market_data_request_effect": _boolish(
                        fields.get("market_data_request_effect")
                    ),
                }
            )
        if raw_stage == "scalping_scanner_prune_bbo_observation":
            observation, gap_reason = _prune_bbo_observation(
                row, target_date=target_date
            )
            if observation is not None and executable_bbo_index is not None:
                executable_bbo_index.setdefault(code, {}).setdefault(
                    observation["venue"], {}
                ).setdefault(observation["session"], []).append(observation)
            elif observation is None and executable_bbo_gap_counts is not None:
                executable_bbo_gap_counts[gap_reason] += 1
        if raw_stage == "rising_missed_entry_turn_pre_anchor_bbo_path":
            observations, gap_reasons = _promoted_ws_bbo_observations(
                row, target_date=target_date
            )
            if executable_bbo_index is not None:
                for observation in observations:
                    executable_bbo_index.setdefault(
                        observation["stock_code"], {}
                    ).setdefault(observation["venue"], {}).setdefault(
                        observation["session"], []
                    ).append(observation)
            if executable_bbo_gap_counts is not None:
                executable_bbo_gap_counts.update(gap_reasons)
        if (
            not logical_stages
            or not code
            or ts is None
            or ts.date().isoformat() != target_date
        ):
            continue
        event_venue = _event_venue(row)
        if raw_stage == "scalping_scanner_candidate_pruned":
            reason = str(
                fields.get("scanner_prune_reason")
                or fields.get("scanner_block_reason")
                or fields.get("scanner_filter_reason")
                or fields.get("reason")
                or fields.get("block_reason")
                or ""
            )
        else:
            reason = str(
                fields.get("reason")
                or fields.get("block_reason")
                or fields.get("scanner_prune_reason")
                or fields.get("scanner_block_reason")
                or fields.get("scanner_filter_reason")
                or fields.get("scanner_promotion_reason")
                or ""
            )
        stage_row = {
            "raw_stage": raw_stage,
            "ts": ts,
            "venue": event_venue,
            "session": (
                _session_for_capture(venue=event_venue, captured_at=ts)
                if event_venue in VENUE_REQUEST_CODES
                else "UNKNOWN"
            ),
            "record_id": _lineage_value(
                row.get("record_id") or fields.get("runtime_record_id")
            ),
            "scanner_promotion_id": _lineage_value(fields.get("scanner_promotion_id")),
            "source_signature": str(fields.get("source_signature") or ""),
            "reason": reason,
            "runtime_target_attach_outcome": str(
                fields.get("runtime_target_attach_outcome") or ""
            ),
            "decision_authority": str(fields.get("decision_authority") or ""),
            "actual_order_submitted": _boolish(fields.get("actual_order_submitted")),
        }
        for logical_stage in logical_stages:
            if (
                logical_stage == "runtime_watch_attached"
                and stage_row["runtime_target_attach_outcome"] != "attached"
            ):
                continue
            index[code][logical_stage].append(stage_row)

    try:
        for row in iter_jsonl_objects_strict(ai_trace_path):
            if str(row.get("endpoint") or "") not in ENTRY_AI_ENDPOINTS:
                continue
            code = _safe_code(row.get("stock_code") or row.get("symbol"))
            ts = _parse_ts(row.get("decision_ts") or row.get("created_at"))
            if not code or ts is None or ts.date().isoformat() != target_date:
                continue
            ai_row = {
                "ts": ts,
                "venue": _normalize_event_venue(row.get("effective_venue")),
                "action": str(row.get("action") or ""),
                "provider_called": _boolish(row.get("provider_called")),
                "provider_actual": str(row.get("provider_actual") or ""),
                "result_source": str(row.get("result_source") or ""),
                "record_id": _lineage_value(row.get("record_id")),
                "request_id": str(row.get("request_id") or ""),
            }
            ai_row["session"] = (
                _session_for_capture(venue=ai_row["venue"], captured_at=ts)
                if ai_row["venue"] in VENUE_REQUEST_CODES
                else "UNKNOWN"
            )
            index[code]["entry_ai_trace"].append(ai_row)
            provider_actual = ai_row["provider_actual"].strip().lower()
            if (
                ai_row["provider_called"]
                and provider_actual
                and provider_actual != "none"
            ):
                index[code]["entry_ai_provider_called"].append(ai_row)
    except FileNotFoundError:
        pass
    if executable_bbo_index is not None:
        _deduplicate_executable_bbo_index(executable_bbo_index)
    return index


def _matching_stage_rows(
    stage_index: dict[str, dict[str, list[dict[str, Any]]]],
    *,
    code: str,
    stage: str,
    venue: str,
    session: str,
    after: datetime | None,
    before: datetime | None = None,
    require_venue: bool,
    require_session: bool,
) -> list[dict[str, Any]]:
    matched = []
    for row in stage_index.get(code, {}).get(stage, []):
        if after is not None and row["ts"] < after:
            continue
        if before is not None and row["ts"] >= before:
            continue
        if require_venue and row.get("venue") != venue:
            continue
        if require_session:
            row_session = row.get("session")
            if (
                not row_session
                and row.get("venue") in VENUE_REQUEST_CODES
                and isinstance(row.get("ts"), datetime)
            ):
                row_session = _session_for_capture(
                    venue=row["venue"],
                    captured_at=row["ts"],
                )
            if row_session != session:
                continue
        matched.append(row)
    return matched


def _build_episodes(
    snapshots: Iterable[dict[str, Any]], *, panel: str, top_n: int
) -> list[dict[str, Any]]:
    episodes: list[dict[str, Any]] = []
    active: dict[tuple[str, str, str], dict[str, Any]] = {}
    ordered_snapshots = sorted(
        snapshots,
        key=lambda row: str(row.get("captured_at") or ""),
    )
    for snapshot in ordered_snapshots:
        if (
            snapshot.get("source_quality_status") != "ok"
            or snapshot.get("panel") != panel
        ):
            continue
        captured_at = _parse_ts(snapshot.get("captured_at"))
        venue = str(snapshot.get("venue") or "")
        if captured_at is None or venue not in VENUE_REQUEST_CODES:
            continue
        session = str(snapshot.get("session") or "") or _session_for_capture(
            venue=venue,
            captured_at=captured_at,
        )
        for row in snapshot.get("rows") or []:
            rank = int(row.get("rank") or 0)
            code = _safe_code(row.get("stock_code"))
            if not code or rank <= 0 or rank > top_n:
                continue
            key = (venue, session, code)
            episode = active.get(key)
            if (
                episode is None
                or (captured_at - episode["last_census_at"]).total_seconds()
                > OPPORTUNITY_EPISODE_RESET_GAP_SEC
            ):
                episode = {
                    "target_date": captured_at.date().isoformat(),
                    "venue": venue,
                    "session": session,
                    "panel": panel,
                    "top_n": top_n,
                    "stock_code": code,
                    "stock_name": row.get("stock_name"),
                    "first_census_at": captured_at,
                    "last_census_at": captured_at,
                    "best_rank": rank,
                    "latest_rank": rank,
                    "latest_price": row.get("current_price"),
                    "latest_change_rate_pct": row.get("change_rate_pct"),
                    "snapshot_count": 0,
                }
                episode["opportunity_episode_id"] = _opportunity_episode_id(
                    target_date=episode["target_date"],
                    venue=venue,
                    session=session,
                    stock_code=code,
                    first_census_at=captured_at,
                )
                active[key] = episode
                episodes.append(episode)
            episode["first_census_at"] = min(episode["first_census_at"], captured_at)
            episode["last_census_at"] = max(episode["last_census_at"], captured_at)
            episode["best_rank"] = min(int(episode["best_rank"]), rank)
            if captured_at >= episode["last_census_at"]:
                episode["latest_rank"] = rank
                episode["latest_price"] = row.get("current_price")
                episode["latest_change_rate_pct"] = row.get("change_rate_pct")
            episode["snapshot_count"] += 1
    return sorted(
        episodes,
        key=lambda item: (
            item["venue"],
            item["session"],
            int(item["best_rank"]),
            item["stock_code"],
            item["first_census_at"],
        ),
    )


def _ex_post_horizon_outcome(
    observations: list[dict[str, Any]],
    *,
    entry: dict[str, Any],
    horizon_sec: int,
    round_trip_cost_pct: float,
    observation_watermark: datetime | None,
) -> dict[str, Any]:
    entry_epoch = float(entry["observed_epoch"])
    entry_ask = float(entry["best_ask"])
    horizon_epoch = entry_epoch + horizon_sec
    exit_row: dict[str, Any] | None = None
    label = "right_censored"
    for observation in observations:
        observed_epoch = float(observation["observed_epoch"])
        if observed_epoch <= entry_epoch or observed_epoch > horizon_epoch:
            continue
        move_pct = (float(observation["best_bid"]) - entry_ask) / entry_ask * 100.0
        if move_pct >= EX_POST_TARGET_PCT:
            label = "target_first"
            exit_row = observation
            break
        if move_pct <= EX_POST_ADVERSE_PCT:
            label = "adverse_first"
            exit_row = observation
            break
    if exit_row is None and observation_watermark is not None:
        if observation_watermark.timestamp() >= horizon_epoch:
            timeout_rows = [
                row
                for row in observations
                if horizon_epoch
                <= float(row["observed_epoch"])
                <= horizon_epoch
                + float(row.get("timeout_max_lag_sec") or EX_POST_TIMEOUT_MAX_LAG_SEC)
                and float(row.get("best_bid_qty") or 0) >= 1
            ]
            if timeout_rows:
                label = "timeout_exit"
                exit_row = timeout_rows[0]
            else:
                label = "right_censored_no_timeout_bbo"
        else:
            label = "pending_horizon"
    result: dict[str, Any] = {
        "horizon_sec": horizon_sec,
        "target_pct": EX_POST_TARGET_PCT,
        "adverse_pct": EX_POST_ADVERSE_PCT,
        "label": label,
        "gross_return_pct": None,
        "cost_adjusted_return_pct": None,
        "elapsed_sec": None,
        "exit_at": None,
        "exit_best_bid": None,
        "exit_best_bid_qty": None,
        "path_order_basis": "first_threshold_crossing_on_bounded_observations",
        "continuous_first_hit_authority": False,
        "actual_fill_claim": False,
        "spread_realization_basis": "entry_ask_to_exit_bid",
        "extra_slippage_model": "zero_extra_for_one_share_displayed_best_level",
    }
    if exit_row is None:
        return result
    gross_return_pct = (float(exit_row["best_bid"]) - entry_ask) / entry_ask * 100.0
    result.update(
        {
            "gross_return_pct": round(gross_return_pct, 8),
            "cost_adjusted_return_pct": round(
                gross_return_pct - round_trip_cost_pct, 8
            ),
            "elapsed_sec": round(float(exit_row["observed_epoch"]) - entry_epoch, 6),
            "exit_at": exit_row["observed_at"].isoformat(),
            "exit_best_bid": exit_row["best_bid"],
            "exit_best_bid_qty": exit_row["best_bid_qty"],
        }
    )
    return result


def _ex_post_executable_opportunity(
    episode: dict[str, Any],
    executable_bbo_index: dict[str, dict[str, dict[str, list[dict[str, Any]]]]],
    *,
    observation_watermark: datetime | None,
    round_trip_cost_pct: float,
) -> dict[str, Any]:
    code = str(episode.get("stock_code") or "")
    venue = str(episode.get("venue") or "")
    session = str(episode.get("session") or "")
    first_census_at = episode.get("first_census_at")
    if not isinstance(first_census_at, datetime):
        return {
            "status": "source_quality_gap",
            "gap_reason": "benchmark_crossing_time_missing",
            "exact_bbo_joined": False,
            "executable_entry_eligible": False,
            "horizons": {},
        }
    all_observations = (
        executable_bbo_index.get(code, {}).get(venue, {}).get(session, [])
    )
    validity_end = first_census_at + timedelta(seconds=OPPORTUNITY_VALIDITY_SEC)
    joined = [
        row
        for row in all_observations
        if first_census_at <= row["observed_at"] <= validity_end
    ]
    if not joined:
        return {
            "status": "source_quality_gap",
            "gap_reason": "exact_route_bbo_not_joined_within_opportunity_validity",
            "exact_bbo_joined": False,
            "executable_entry_eligible": False,
            "horizons": {},
        }
    entry = next(
        (
            row
            for row in joined
            if float(row["spread_bps"]) <= EX_POST_MAX_ENTRY_SPREAD_BPS
            and float(row.get("best_ask_qty") or 0) >= 1
        ),
        None,
    )
    if entry is None:
        return {
            "status": "excluded_uneconomic_spread_or_fill",
            "gap_reason": "no_fill_feasible_bbo_within_spread_bound",
            "exact_bbo_joined": True,
            "first_exact_bbo_at": joined[0]["observed_at"].isoformat(),
            "executable_entry_eligible": False,
            "horizons": {},
        }
    forward_observations = [
        row
        for row in all_observations
        if row["observed_epoch"] >= entry["observed_epoch"]
        and float(row.get("best_bid_qty") or 0) >= 1
    ]
    horizons = {
        str(horizon_sec): _ex_post_horizon_outcome(
            forward_observations,
            entry=entry,
            horizon_sec=horizon_sec,
            round_trip_cost_pct=round_trip_cost_pct,
            observation_watermark=observation_watermark,
        )
        for horizon_sec in EX_POST_HORIZONS_SEC
    }
    return {
        "status": "source_quality_valid",
        "gap_reason": "not_applicable",
        "exact_bbo_joined": True,
        "executable_entry_eligible": True,
        "entry_at": entry["observed_at"].isoformat(),
        "entry_delay_from_benchmark_sec": round(
            (entry["observed_at"] - first_census_at).total_seconds(), 6
        ),
        "entry_best_bid": entry["best_bid"],
        "entry_best_ask": entry["best_ask"],
        "entry_best_ask_qty": entry["best_ask_qty"],
        "entry_spread_bps": entry["spread_bps"],
        "price_source": entry["price_source"],
        "fill_feasibility_basis": "one_share_at_displayed_best_quantity",
        "observer_episode_id": entry["observer_episode_id"],
        "horizons": horizons,
        "primary_horizon_sec": EX_POST_PRIMARY_HORIZON_SEC,
        "primary_outcome": horizons[str(EX_POST_PRIMARY_HORIZON_SEC)],
    }


def _coverage_row(
    episode: dict[str, Any],
    stage_index: dict[str, dict[str, list[dict[str, Any]]]],
    *,
    after: datetime | None,
    require_venue: bool,
    before: datetime | None = None,
    require_lineage: bool = False,
    executable_bbo_index: (
        dict[str, dict[str, dict[str, list[dict[str, Any]]]]] | None
    ) = None,
    observation_watermark: datetime | None = None,
    round_trip_cost_pct: float | None = None,
) -> dict[str, Any]:
    code = episode["stock_code"]
    venue = episode["venue"]
    first_census_at = episode.get("first_census_at")
    session = episode.get("session")
    if (
        not session
        and venue in VENUE_REQUEST_CODES
        and isinstance(first_census_at, datetime)
    ):
        session = _session_for_capture(venue=venue, captured_at=first_census_at)
    session = str(session or "UNKNOWN")
    candidate_rows = {
        stage: _matching_stage_rows(
            stage_index,
            code=code,
            stage=stage,
            venue=venue,
            session=session,
            after=after,
            before=before,
            require_venue=require_venue,
            require_session=require_lineage,
        )
        for stage in STAGE_ORDER
    }
    lineage_status = "not_requested_noncausal"
    lineage_promotion_id = ""
    lineage_source_signature = ""
    lineage_record_ids: set[str] = set()
    promotions = sorted(candidate_rows["scanner_promoted"], key=lambda row: row["ts"])
    if not require_lineage and promotions:
        lineage_promotion_id = _lineage_value(promotions[0].get("scanner_promotion_id"))
        lineage_source_signature = str(promotions[0].get("source_signature") or "")
    if require_lineage:
        selected_promotion = promotions[0] if promotions else None
        if selected_promotion is None:
            lineage_status = "not_applicable_no_scanner_promotion"
            candidate_rows = {
                stage: (
                    rows
                    if stage
                    in {"source_seen", "candidate_evaluated", "scanner_guard_observed"}
                    else []
                )
                for stage, rows in candidate_rows.items()
            }
        else:
            lineage_promotion_id = _lineage_value(
                selected_promotion.get("scanner_promotion_id")
            )
            lineage_source_signature = str(
                selected_promotion.get("source_signature") or ""
            )
            next_promotion_at = min(
                (
                    row["ts"]
                    for row in promotions[1:]
                    if row["ts"] > selected_promotion["ts"]
                ),
                default=None,
            )
            if not lineage_promotion_id:
                lineage_status = "scanner_promotion_id_missing"
                candidate_rows = {
                    stage: (
                        [selected_promotion]
                        if stage == "scanner_promoted"
                        else (rows if stage == "scanner_guard_observed" else [])
                    )
                    for stage, rows in candidate_rows.items()
                }
            else:
                lineage_status = "scanner_promotion_lineage_proven"
                lineaged_pipeline_rows: dict[str, list[dict[str, Any]]] = {}
                for stage, rows in candidate_rows.items():
                    if stage in {
                        "source_seen",
                        "candidate_evaluated",
                        "scanner_guard_observed",
                    }:
                        lineaged_pipeline_rows[stage] = rows
                    elif stage == "scanner_promoted":
                        lineaged_pipeline_rows[stage] = [selected_promotion]
                    elif stage in {"entry_ai_trace", "entry_ai_provider_called"}:
                        lineaged_pipeline_rows[stage] = []
                    else:
                        lineaged_pipeline_rows[stage] = [
                            row
                            for row in rows
                            if (
                                selected_promotion["ts"] <= row["ts"]
                                and (
                                    next_promotion_at is None
                                    or row["ts"] < next_promotion_at
                                )
                                and _lineage_value(row.get("scanner_promotion_id"))
                                == lineage_promotion_id
                            )
                        ]
                        lineage_record_ids.update(
                            _lineage_value(row.get("record_id"))
                            for row in lineaged_pipeline_rows[stage]
                            if _lineage_value(row.get("record_id"))
                        )
                for stage in ("entry_ai_trace", "entry_ai_provider_called"):
                    lineaged_pipeline_rows[stage] = [
                        row
                        for row in candidate_rows[stage]
                        if (
                            selected_promotion["ts"] <= row["ts"]
                            and (
                                next_promotion_at is None
                                or row["ts"] < next_promotion_at
                            )
                            and _lineage_value(row.get("record_id"))
                            in lineage_record_ids
                        )
                    ]
                if not lineage_record_ids:
                    lineage_status = "scanner_promotion_record_lineage_pending"
                candidate_rows = lineaged_pipeline_rows

    flags: dict[str, bool] = {}
    first_times: dict[str, datetime | None] = {}
    actions: list[str] = []
    for stage in STAGE_ORDER:
        rows = candidate_rows[stage]
        flags[stage] = bool(rows)
        first_times[stage] = min((row["ts"] for row in rows), default=None)
        if stage == "entry_ai_trace":
            actions = sorted(
                {str(row.get("action") or "") for row in rows if row.get("action")}
            )
    stage_raw_events = {
        stage: sorted(
            {
                str(row.get("raw_stage") or "")
                for row in candidate_rows[stage]
                if row.get("raw_stage")
            }
        )
        for stage in STAGE_ORDER
    }
    stage_reason_codes = {
        stage: sorted(
            {
                str(row.get("reason") or "")
                for row in candidate_rows[stage]
                if row.get("reason")
            }
        )
        for stage in STAGE_ORDER
    }
    first_stage_reason_code = {
        stage: str(first_row.get("reason") or "") if first_row else None
        for stage in STAGE_ORDER
        for first_row in [
            min(
                (row for row in candidate_rows[stage] if row.get("reason")),
                key=lambda row: (
                    row["ts"],
                    str(row.get("raw_stage") or ""),
                    str(row.get("reason") or ""),
                ),
                default=None,
            )
        ]
    }

    promoted_at = first_times.get("scanner_promoted")
    scanner_detection_latency_sec = (
        round((promoted_at - first_census_at).total_seconds(), 6)
        if promoted_at is not None
        and isinstance(first_census_at, datetime)
        and promoted_at >= first_census_at
        else None
    )
    scanner_detection_sla_met = (
        scanner_detection_latency_sec is not None
        and scanner_detection_latency_sec <= SCANNER_DETECTION_SLA_SEC
    )
    stage_latency_from_promotion_sec = (
        {
            stage: (
                round((stage_at - promoted_at).total_seconds(), 6)
                if promoted_at is not None
                and stage_at is not None
                and stage_at >= promoted_at
                else None
            )
            for stage, stage_at in first_times.items()
            if stage != "scanner_promoted"
        }
        if require_lineage and lineage_promotion_id
        else {}
    )

    if not flags["scanner_promoted"]:
        no_ai_reason = (
            "scanner_source_guard_blocked_before_promotion"
            if flags["scanner_guard_observed"]
            else (
                "candidate_not_promoted"
                if flags["candidate_evaluated"]
                else "scanner_discovery_gap_or_unobserved"
            )
        )
    else:
        if require_lineage and not lineage_promotion_id:
            no_ai_reason = "scanner_promotion_lineage_unproven"
        else:
            no_ai_reason = "entry_ai_provider_reached"
            for stage, reason in (
                ("fast_precheck", "scanner_fast_precheck_gap"),
                ("heavy_eval", "scanner_heavy_eval_gap"),
                ("entry_ai_trace", "entry_ai_trace_gap"),
                ("entry_ai_provider_called", "entry_ai_preflight_or_transport_block"),
            ):
                if not flags[stage]:
                    no_ai_reason = reason
                    break

    if require_lineage and flags["scanner_promoted"] and not scanner_detection_sla_met:
        terminal_coverage_reason = "late_discovery_after_opportunity_window"
    elif flags["submitted"]:
        terminal_coverage_reason = "submitted"
    elif "entry_submit_revalidation_block" in stage_raw_events["submit_safety_checked"]:
        terminal_coverage_reason = "submit_safety_block"
    elif (
        "entry_submit_revalidation_warning" in stage_raw_events["submit_safety_checked"]
    ):
        terminal_coverage_reason = "submit_safety_warning_no_submit"
    elif (
        "pre_submit_entry_ai_authority_guard_block"
        in stage_raw_events["entry_authority_decided"]
    ):
        terminal_coverage_reason = "entry_authority_guard_block"
    elif flags["entry_authority_decided"]:
        terminal_coverage_reason = "post_authority_submit_safety_gap"
    elif flags["entry_ai_provider_called"]:
        terminal_coverage_reason = "entry_authority_decision_gap"
    else:
        terminal_coverage_reason = no_ai_reason

    ex_post_executable_opportunity = (
        _ex_post_executable_opportunity(
            episode,
            executable_bbo_index,
            observation_watermark=observation_watermark,
            round_trip_cost_pct=round_trip_cost_pct,
        )
        if executable_bbo_index is not None and round_trip_cost_pct is not None
        else {
            "status": "not_requested_noncausal_or_cost_unavailable",
            "gap_reason": "not_applicable",
            "exact_bbo_joined": False,
            "executable_entry_eligible": False,
            "horizons": {},
        }
    )

    return {
        **{
            key: (value.isoformat() if isinstance(value, datetime) else value)
            for key, value in episode.items()
        },
        "stage_reached": flags,
        "first_stage_at": {
            key: value.isoformat() if value is not None else None
            for key, value in first_times.items()
        },
        "stage_latency_from_scanner_promoted_sec": (stage_latency_from_promotion_sec),
        "stage_raw_events": stage_raw_events,
        "stage_reason_codes": stage_reason_codes,
        "first_stage_reason_code": first_stage_reason_code,
        "scanner_lineage": {
            "required": require_lineage,
            "status": lineage_status,
            "scanner_promotion_id": lineage_promotion_id or None,
            "record_ids": sorted(lineage_record_ids),
            "source_signature": lineage_source_signature,
            "prev_close_gainer_source": (
                "PREV_CLOSE_GAINER"
                in {
                    token.strip().upper()
                    for token in lineage_source_signature.split(",")
                    if token.strip()
                }
            ),
        },
        "entry_ai_actions": actions,
        "scanner_detection_sla_sec": (
            SCANNER_DETECTION_SLA_SEC if require_lineage else None
        ),
        "scanner_detection_latency_sec": scanner_detection_latency_sec,
        "scanner_detection_sla_met": (
            scanner_detection_sla_met if require_lineage else None
        ),
        "opportunity_validity_sec": OPPORTUNITY_VALIDITY_SEC,
        "terminal_coverage_reason": terminal_coverage_reason,
        "ex_post_executable_opportunity": ex_post_executable_opportunity,
    }


def _latency_summary(values: list[float]) -> dict[str, Any]:
    ordered = sorted(float(value) for value in values if value >= 0)
    if not ordered:
        return {
            "sample_count": 0,
            "p50_sec": None,
            "p95_sec": None,
            "max_sec": None,
        }

    def percentile(fraction: float) -> float:
        rank = max(0, min(len(ordered) - 1, math.ceil(len(ordered) * fraction) - 1))
        return round(ordered[rank], 6)

    return {
        "sample_count": len(ordered),
        "p50_sec": percentile(0.50),
        "p95_sec": percentile(0.95),
        "max_sec": round(ordered[-1], 6),
    }


def _summarize_rows_base(rows: list[dict[str, Any]]) -> dict[str, Any]:
    total = len(rows)
    candidate_not_promoted_rows = [
        row
        for row in rows
        if row.get("terminal_coverage_reason") == "candidate_not_promoted"
    ]
    candidate_not_promoted_first_reason_counts = dict(
        sorted(
            Counter(
                str(
                    (row.get("first_stage_reason_code") or {}).get(
                        "candidate_evaluated"
                    )
                    or "reason_missing"
                )
                for row in candidate_not_promoted_rows
            ).items()
        )
    )
    candidate_not_promoted_first_reason_count_sum = sum(
        candidate_not_promoted_first_reason_counts.values()
    )
    counts = {
        stage: sum(bool(row["stage_reached"].get(stage)) for row in rows)
        for stage in STAGE_ORDER
    }
    latency_by_stage = {
        stage: _latency_summary(
            [
                float(latency)
                for row in rows
                if (
                    latency := (
                        row.get("stage_latency_from_scanner_promoted_sec") or {}
                    ).get(stage)
                )
                is not None
            ]
        )
        for stage in (
            "fast_precheck",
            "heavy_eval",
            "entry_ai_provider_called",
            "submitted",
        )
    }
    rates = {
        stage: round((count / total * 100.0), 2) if total else 0.0
        for stage, count in counts.items()
    }
    scanner_detection_sla_met_count = sum(
        row.get("scanner_detection_sla_met") is True for row in rows
    )
    has_sla_contract = any(
        row.get("scanner_detection_sla_met") is not None for row in rows
    )
    provider_reached_within_sla_count = sum(
        bool(row["stage_reached"].get("entry_ai_provider_called"))
        and (row.get("scanner_detection_sla_met") is True if has_sla_contract else True)
        for row in rows
    )
    ex_post_rows = [row.get("ex_post_executable_opportunity") or {} for row in rows]
    ex_post_exact_bbo_joined_count = sum(
        outcome.get("exact_bbo_joined") is True for outcome in ex_post_rows
    )
    ex_post_entry_eligible_count = sum(
        outcome.get("executable_entry_eligible") is True for outcome in ex_post_rows
    )
    ex_post_primary_outcomes = [
        outcome.get("primary_outcome") or {}
        for outcome in ex_post_rows
        if outcome.get("executable_entry_eligible") is True
    ]
    ex_post_primary_label_counts = dict(
        sorted(
            Counter(
                str(outcome.get("label") or "missing")
                for outcome in ex_post_primary_outcomes
            ).items()
        )
    )
    ex_post_resolved_labels = {"target_first", "adverse_first", "timeout_exit"}
    ex_post_right_censored_labels = {
        "right_censored",
        "right_censored_no_timeout_bbo",
    }
    ex_post_resolved = [
        outcome
        for outcome in ex_post_primary_outcomes
        if outcome.get("label") in ex_post_resolved_labels
        and outcome.get("cost_adjusted_return_pct") is not None
    ]
    ex_post_right_censored_count = sum(
        outcome.get("label") in ex_post_right_censored_labels
        for outcome in ex_post_primary_outcomes
    )
    ex_post_mature_count = len(ex_post_resolved) + ex_post_right_censored_count
    ex_post_exact_bbo_join_coverage_pct = (
        round(ex_post_exact_bbo_joined_count / total * 100.0, 2) if total else 0.0
    )
    ex_post_right_censored_pct = (
        round(ex_post_right_censored_count / ex_post_mature_count * 100.0, 2)
        if ex_post_mature_count
        else None
    )
    ex_post_observed_ev = (
        round(
            sum(float(row["cost_adjusted_return_pct"]) for row in ex_post_resolved)
            / len(ex_post_resolved),
            8,
        )
        if ex_post_resolved
        else None
    )
    ex_post_floor_met = bool(
        total
        and ex_post_exact_bbo_join_coverage_pct >= EX_POST_ENTRY_COVERAGE_FLOOR_PCT
        and len(ex_post_resolved) >= EX_POST_MIN_RESOLVED_COUNT
        and ex_post_right_censored_pct is not None
        and ex_post_right_censored_pct <= EX_POST_RIGHT_CENSORED_MAX_PCT
    )
    return {
        "episode_count": total,
        "denominator_unique_opportunity_episode_count": total,
        "stage_counts": counts,
        "stage_rates_pct": rates,
        "scanner_detection_sla_met_count": scanner_detection_sla_met_count,
        "entry_ai_provider_reached_within_sla_count": (
            provider_reached_within_sla_count
        ),
        "promotion_recall_pct": (
            round(scanner_detection_sla_met_count / total * 100.0, 2)
            if total and has_sla_contract
            else rates["scanner_promoted"]
        ),
        "fast_precheck_recall_pct": rates["fast_precheck"],
        "heavy_eval_recall_pct": rates["heavy_eval"],
        "entry_ai_provider_reach_rate_pct": (
            round(provider_reached_within_sla_count / total * 100.0, 2)
            if total
            else 0.0
        ),
        "submitted_recall_pct": rates["submitted"],
        "source_seen_recall_pct": rates["source_seen"],
        "watch_admission_recall_pct": rates["watch_admitted"],
        "runtime_watch_attach_recall_pct": rates["runtime_watch_attached"],
        "candidate_recall_pct": rates["candidate_evaluated"],
        "entry_authority_decision_recall_pct": rates["entry_authority_decided"],
        "submit_safety_check_recall_pct": rates["submit_safety_checked"],
        "terminal_coverage_reason_counts": dict(
            sorted(Counter(row["terminal_coverage_reason"] for row in rows).items())
        ),
        "candidate_not_promoted_first_reason_counts": (
            candidate_not_promoted_first_reason_counts
        ),
        "candidate_not_promoted_first_reason_count_sum": (
            candidate_not_promoted_first_reason_count_sum
        ),
        "candidate_not_promoted_first_reason_conservation_delta": (
            len(candidate_not_promoted_rows)
            - candidate_not_promoted_first_reason_count_sum
        ),
        "candidate_not_promoted_first_reason_conservation_status": (
            "pass"
            if len(candidate_not_promoted_rows)
            == candidate_not_promoted_first_reason_count_sum
            else "fail"
        ),
        "scanner_lineage_status_counts": dict(
            sorted(
                Counter(
                    str((row.get("scanner_lineage") or {}).get("status") or "missing")
                    for row in rows
                ).items()
            )
        ),
        "prev_close_gainer_source_promotion_count": sum(
            bool((row.get("scanner_lineage") or {}).get("prev_close_gainer_source"))
            for row in rows
        ),
        "stage_latency_from_scanner_promoted_sec": latency_by_stage,
        "ex_post_executable_opportunity": {
            "denominator_unique_opportunity_episode_count": total,
            "exact_bbo_joined_count": ex_post_exact_bbo_joined_count,
            "exact_bbo_not_joined_count": total - ex_post_exact_bbo_joined_count,
            "exact_bbo_join_coverage_pct": ex_post_exact_bbo_join_coverage_pct,
            "executable_entry_eligible_count": ex_post_entry_eligible_count,
            "primary_horizon_sec": EX_POST_PRIMARY_HORIZON_SEC,
            "primary_label_counts": ex_post_primary_label_counts,
            "primary_label_count_sum": sum(ex_post_primary_label_counts.values()),
            "resolved_outcome_count": len(ex_post_resolved),
            "right_censored_count": ex_post_right_censored_count,
            "right_censored_pct": ex_post_right_censored_pct,
            "pending_horizon_count": ex_post_primary_label_counts.get(
                "pending_horizon", 0
            ),
            "observed_cohort_source_quality_adjusted_ev_pct": (ex_post_observed_ev),
            "source_quality_adjusted_ev_pct": (
                ex_post_observed_ev if ex_post_floor_met else None
            ),
            "economic_evidence_floor_met": ex_post_floor_met,
            "sample_floor": {
                "exact_bbo_join_coverage_pct_min": (EX_POST_ENTRY_COVERAGE_FLOOR_PCT),
                "resolved_outcome_count_min": EX_POST_MIN_RESOLVED_COUNT,
                "right_censored_pct_max": EX_POST_RIGHT_CENSORED_MAX_PCT,
            },
            "full_external_population_ev_extrapolation_allowed": (False),
            "path_order_basis": ("first_threshold_crossing_on_bounded_observations"),
            "continuous_first_hit_authority": False,
            "fill_feasibility_basis": "one_share_at_displayed_best_quantity",
            "actual_fill_claim": False,
            "spread_realization_basis": "entry_ask_to_exit_bid",
            "extra_slippage_model": ("zero_extra_for_one_share_displayed_best_level"),
            "ev_population_scope": (
                "bounded_exact_bbo_joined_external_opportunity_cohort_only"
            ),
        },
    }


def _summarize_rows(rows: list[dict[str, Any]]) -> dict[str, Any]:
    summary = _summarize_rows_base(rows)
    summary["by_venue"] = {
        venue: _summarize_rows_base([row for row in rows if row.get("venue") == venue])
        for venue in VENUE_REQUEST_CODES
    }
    return summary


def _summarize_ex_post_by_scope(
    rows: list[dict[str, Any]],
) -> tuple[dict[str, dict[str, Any]], bool]:
    scope_rows: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        scope_rows[
            (
                str(row.get("venue") or "UNKNOWN"),
                str(row.get("session") or "UNKNOWN"),
            )
        ].append(row)
    summaries = {
        f"{venue}|{session}": _summarize_rows_base(members)[
            "ex_post_executable_opportunity"
        ]
        for (venue, session), members in sorted(scope_rows.items())
    }
    return summaries, bool(summaries) and all(
        bool(summary.get("economic_evidence_floor_met"))
        for summary in summaries.values()
    )


def _snapshot_contract_error(row: dict[str, Any], *, target_date: str) -> str:
    if row.get("schema_version") != SCHEMA_VERSION:
        return "schema_version_mismatch"
    if str(row.get("target_date") or "") != target_date:
        return "target_date_mismatch"
    captured_at = _parse_ts(row.get("captured_at"))
    if captured_at is None or captured_at.date().isoformat() != target_date:
        return "capture_timestamp_mismatch"
    if row.get("venue") not in VENUE_REQUEST_CODES:
        return "venue_invalid"
    if row.get("panel") not in PANEL_CONTRACTS:
        return "panel_invalid"
    rows = row.get("rows")
    if not isinstance(rows, list):
        return "rows_not_list"
    source = row.get("source") if isinstance(row.get("source"), dict) else {}
    source_hash = str(source.get("normalized_source_payload_sha256") or "")
    if source_hash:
        request_contract = source.get("request_contract")
        if not isinstance(request_contract, dict):
            return "source_request_contract_missing"
        try:
            expected_source_hash = _normalized_source_payload_sha256(
                request_contract=request_contract,
                rows=rows,
            )
        except (TypeError, ValueError):
            return "source_payload_not_canonical"
        if source_hash != expected_source_hash:
            return "source_payload_hash_mismatch"
    if row.get("source_quality_status") == "ok" and not rows:
        return "ok_status_without_rows"
    return ""


def build_report(
    target_date: str,
    *,
    snapshot_path: Path | None = None,
    pipeline_path: Path | None = None,
    ai_trace_path: Path | None = None,
    symbol_master_path: Path | None = None,
    trigger_receipt_path: Path | None = None,
    external_bbo_budget_path: Path | None = None,
) -> dict[str, Any]:
    report_started_at = datetime.now(KST)
    snapshots_path = snapshot_path or (
        SNAPSHOT_DIR / f"{REPORT_TYPE}_{target_date}.jsonl"
    )
    events_path = pipeline_path or (
        PIPELINE_DIR / f"pipeline_events_{target_date}.jsonl"
    )
    trace_path = ai_trace_path or (
        AI_TRACE_DIR / f"ai_decision_trace_{target_date}.jsonl"
    )
    all_snapshots = list(iter_jsonl(existing_or_gzip_path(snapshots_path)))
    target_date_snapshots = [
        row for row in all_snapshots if str(row.get("target_date") or "") == target_date
    ]
    contract_errors = [
        _snapshot_contract_error(row, target_date=target_date)
        for row in target_date_snapshots
    ]
    snapshots = [
        row
        for row, error in zip(target_date_snapshots, contract_errors, strict=True)
        if not error
    ]
    executable_bbo_index: dict[str, dict[str, dict[str, list[dict[str, Any]]]]] = {}
    executable_bbo_gap_counts: Counter[str] = Counter()
    observer_runtime_receipts: list[dict[str, Any]] = []
    stage_index = _load_stage_index(
        events_path,
        trace_path,
        target_date=target_date,
        executable_bbo_index=executable_bbo_index,
        executable_bbo_gap_counts=executable_bbo_gap_counts,
        observer_runtime_receipts=observer_runtime_receipts,
    )
    latest_observer_runtime_receipt = max(
        observer_runtime_receipts,
        key=lambda row: row["emitted_at"],
        default=None,
    )
    observer_pid_contract_reflected = bool(
        latest_observer_runtime_receipt
        and latest_observer_runtime_receipt.get("process_pid")
        and latest_observer_runtime_receipt.get("configuration_status")
        == "collector_created"
        and latest_observer_runtime_receipt.get("configuration_receipt_status")
        == "emitted"
        and latest_observer_runtime_receipt.get("observation_schema_version")
        == PRUNE_BBO_OBSERVATION_SCHEMA_VERSION
        and latest_observer_runtime_receipt.get("decision_authority")
        == "scanner_prune_bbo_observation_only"
        and latest_observer_runtime_receipt.get("authority_contract_fields_present")
        is True
        and latest_observer_runtime_receipt.get("runtime_effect") is False
        and latest_observer_runtime_receipt.get("allowed_runtime_apply") is False
        and latest_observer_runtime_receipt.get("actual_order_submitted") is False
        and latest_observer_runtime_receipt.get("broker_order_forbidden") is True
        and latest_observer_runtime_receipt.get("market_data_request_effect") is True
    )
    valid_snapshots = [
        row for row in snapshots if row.get("source_quality_status") == "ok"
    ]
    external_bbo_contract_row_count = 0
    external_bbo_request_attempted_count = 0
    external_bbo_reserved_contract_row_count = 0
    external_bbo_invalid_reservation_attempt_count = 0
    external_bbo_max_reserved_ordinal = 0
    external_bbo_reservation_ordinals: list[int] = []
    for snapshot in valid_snapshots:
        if snapshot.get("panel") != "liquid_common":
            continue
        for snapshot_row in snapshot.get("rows") or []:
            if not isinstance(snapshot_row, dict):
                executable_bbo_gap_counts["external_census_snapshot_row_invalid"] += 1
                continue
            rank = int(_safe_float(snapshot_row.get("rank")) or 0)
            if rank <= 0 or rank > EXTERNAL_BBO_CAPTURE_TOP_N:
                continue
            raw_observation = snapshot_row.get("executable_bbo_observation")
            if (
                isinstance(raw_observation, dict)
                and raw_observation.get("schema_version")
                == EXTERNAL_BBO_OBSERVATION_SCHEMA_VERSION
            ):
                external_bbo_contract_row_count += 1
                external_bbo_request_attempted_count += int(
                    raw_observation.get("request_attempted") is True
                )
                reservation_ordinal = _external_bbo_reservation_ordinal(
                    raw_observation
                )
                if reservation_ordinal is not None:
                    external_bbo_reserved_contract_row_count += 1
                    external_bbo_reservation_ordinals.append(reservation_ordinal)
                    external_bbo_max_reserved_ordinal = max(
                        external_bbo_max_reserved_ordinal,
                        reservation_ordinal,
                    )
                elif raw_observation.get("request_attempted") is True:
                    external_bbo_invalid_reservation_attempt_count += 1
                    if raw_observation.get("status") != "captured":
                        executable_bbo_gap_counts[
                            "external_census_daily_budget_reservation_invalid"
                        ] += 1
            observation, gap_reason = _external_snapshot_bbo_observation(
                snapshot,
                snapshot_row,
                target_date=target_date,
            )
            if observation is None:
                executable_bbo_gap_counts[gap_reason] += 1
                continue
            executable_bbo_index.setdefault(observation["stock_code"], {}).setdefault(
                observation["venue"], {}
            ).setdefault(observation["session"], []).append(observation)
    _deduplicate_executable_bbo_index(executable_bbo_index)
    selected_external_bbo_budget_path = external_bbo_budget_path or (
        EXTERNAL_BBO_BUDGET_DIR / f"external_bbo_request_budget_{target_date}.json"
    )
    external_bbo_budget_contract = _load_external_bbo_budget_contract(
        selected_external_bbo_budget_path,
        target_date=target_date,
        minimum_reserved_count=external_bbo_max_reserved_ordinal,
    )
    external_bbo_unique_reserved_ordinal_count = len(
        set(external_bbo_reservation_ordinals)
    )
    external_bbo_duplicate_reserved_ordinal_count = (
        external_bbo_reserved_contract_row_count
        - external_bbo_unique_reserved_ordinal_count
    )
    if external_bbo_duplicate_reserved_ordinal_count:
        executable_bbo_gap_counts[
            "external_census_daily_budget_reservation_ordinal_duplicate"
        ] += external_bbo_duplicate_reserved_ordinal_count
    external_bbo_reservation_accounted_count = (
        external_bbo_reserved_contract_row_count
        + external_bbo_invalid_reservation_attempt_count
    )
    external_bbo_reservation_conservation_delta = (
        external_bbo_request_attempted_count
        - external_bbo_reservation_accounted_count
    )
    external_bbo_reservation_conservation_status = (
        "pass"
        if external_bbo_reservation_conservation_delta == 0
        and external_bbo_duplicate_reserved_ordinal_count == 0
        else "fail"
    )
    external_bbo_capture_contract_reflected = bool(
        external_bbo_reserved_contract_row_count
        and external_bbo_budget_contract.get("status") == "verified"
        and external_bbo_reservation_conservation_status == "pass"
    )
    snapshot_capture_times = [
        captured_at
        for row in valid_snapshots
        for captured_at in [_parse_ts(row.get("captured_at"))]
        if captured_at is not None
    ]
    executable_bbo_times = [
        observation["observed_at"]
        for venue_index in executable_bbo_index.values()
        for session_index in venue_index.values()
        for observations in session_index.values()
        for observation in observations
    ]
    observation_watermark = max(
        [*snapshot_capture_times, *executable_bbo_times], default=None
    )
    try:
        cost_contract = comparison_cost_contract(target_date)
    except ValueError as exc:
        cost_contract = {
            "status": "invalid",
            "trade_date": target_date,
            "reason": str(exc),
            "round_trip_cost_pct": None,
        }
    else:
        cost_contract = {**cost_contract, "status": "verified"}
    round_trip_cost_pct = _safe_float(cost_contract.get("round_trip_cost_pct"))
    missing_source_hash_snapshot_count = sum(
        not str(
            (row.get("source") if isinstance(row.get("source"), dict) else {}).get(
                "normalized_source_payload_sha256"
            )
            or ""
        )
        for row in valid_snapshots
    )
    missing_source_hash_capture_ids = sorted(
        str(row.get("capture_id") or "")
        for row in valid_snapshots
        if not str(
            (row.get("source") if isinstance(row.get("source"), dict) else {}).get(
                "normalized_source_payload_sha256"
            )
            or ""
        )
    )
    symbol_master, symbol_master_binding = _load_symbol_master_binding(
        target_date,
        symbol_master_path=symbol_master_path,
    )
    trigger_contract = _load_trigger_contract(trigger_receipt_path)
    valid_capture_times_by_venue_panel: dict[str, int] = {}
    observed_capture_cadence_by_venue_panel: dict[str, Any] = {}
    for venue in VENUE_REQUEST_CODES:
        for panel in PANEL_CONTRACTS:
            key = f"{venue}|{panel}"
            session_times: dict[str, set[datetime]] = defaultdict(set)
            for row in valid_snapshots:
                if row.get("venue") != venue or row.get("panel") != panel:
                    continue
                captured_at = _parse_ts(row.get("captured_at"))
                session = str(row.get("session") or "")
                if captured_at is None or not session or session.startswith("OUTSIDE_"):
                    continue
                session_times[session].add(captured_at)
            valid_capture_times_by_venue_panel[key] = sum(
                len(values) for values in session_times.values()
            )
            session_summaries = {}
            for session, values in sorted(session_times.items()):
                ordered = sorted(values)
                gaps = [
                    (right - left).total_seconds()
                    for left, right in zip(ordered, ordered[1:], strict=False)
                ]
                session_summaries[session] = {
                    "capture_time_count": len(ordered),
                    "first_capture_at": ordered[0].isoformat() if ordered else None,
                    "last_capture_at": ordered[-1].isoformat() if ordered else None,
                    "max_consecutive_gap_sec": max(gaps) if gaps else None,
                    "cadence_floor_met": (
                        len(ordered) >= MIN_VALID_CAPTURE_TIMES_PER_VENUE_PANEL
                        and bool(gaps)
                        and max(gaps)
                        <= CAPTURE_CADENCE_SEC + CAPTURE_CADENCE_TOLERANCE_SEC
                    ),
                }
            observed_capture_cadence_by_venue_panel[key] = {
                "sessions": session_summaries,
                "cadence_floor_met": any(
                    bool(summary.get("cadence_floor_met"))
                    for summary in session_summaries.values()
                ),
            }
    capture_cadence_floor_met = bool(observed_capture_cadence_by_venue_panel) and all(
        bool(summary.get("cadence_floor_met"))
        for summary in observed_capture_cadence_by_venue_panel.values()
    )
    missing_session_snapshot_count = sum(
        not str(row.get("session") or "").strip() for row in valid_snapshots
    )
    missing_session_capture_ids = sorted(
        str(row.get("capture_id") or "")
        for row in valid_snapshots
        if not str(row.get("session") or "").strip()
    )
    symbol_master_lookup_counts: Counter[str] = Counter()
    symbol_master_lookup_cache: dict[str, Any] = {}
    symbol_master_lookup_codes: dict[str, set[str]] = defaultdict(set)
    primary_symbol_master_lookup_counts: Counter[str] = Counter()
    primary_symbol_master_lookup_codes: dict[str, set[str]] = defaultdict(set)

    coverage: dict[str, Any] = {}
    details: dict[str, Any] = {}
    raw_episode_counts: dict[str, dict[str, int]] = {}
    primary_eligible_forward_rows: list[dict[str, Any]] = []
    primary_eligible_forward_summary = _summarize_rows([])
    for panel in PANEL_CONTRACTS:
        coverage[panel] = {}
        details[panel] = {}
        raw_episode_counts[panel] = {}
        for top_n in TOP_N_WINDOWS:
            episodes = _build_episodes(snapshots, panel=panel, top_n=top_n)
            raw_episode_counts[panel][f"top_{top_n}"] = len(episodes)
            for episode in episodes:
                if symbol_master is None:
                    episode["symbol_master_status"] = "master_unavailable"
                    continue
                code = episode["stock_code"]
                lookup = symbol_master_lookup_cache.get(code)
                if lookup is None:
                    lookup = symbol_master.lookup(
                        code,
                        as_of=date.fromisoformat(target_date),
                    )
                    symbol_master_lookup_cache[code] = lookup
                    symbol_master_lookup_counts[lookup.status.value] += 1
                    symbol_master_lookup_codes[lookup.status.value].add(code)
                episode["symbol_master_status"] = lookup.status.value
                if lookup.record is not None:
                    episode["listing_market"] = lookup.record.listing_market.value
                    episode["instrument_type"] = lookup.record.instrument_type.value
            forward_rows = [
                _coverage_row(
                    episode,
                    stage_index,
                    after=episode["first_census_at"],
                    before=(
                        episode["first_census_at"]
                        + timedelta(seconds=OPPORTUNITY_VALIDITY_SEC)
                    ),
                    require_venue=True,
                    require_lineage=True,
                    executable_bbo_index=executable_bbo_index,
                    observation_watermark=observation_watermark,
                    round_trip_cost_pct=round_trip_cost_pct,
                )
                for episode in episodes
            ]
            venue_rows = [
                _coverage_row(
                    episode,
                    stage_index,
                    after=None,
                    require_venue=True,
                )
                for episode in episodes
            ]
            any_venue_rows = [
                _coverage_row(
                    episode,
                    stage_index,
                    after=None,
                    require_venue=False,
                )
                for episode in episodes
            ]
            if panel == "liquid_common" and top_n == 20:
                for episode in episodes:
                    master_status = str(
                        episode.get("symbol_master_status") or "master_unavailable"
                    )
                    primary_symbol_master_lookup_counts[master_status] += 1
                    primary_symbol_master_lookup_codes[master_status].add(
                        str(episode.get("stock_code") or "")
                    )
                primary_eligible_forward_rows = [
                    row
                    for row in forward_rows
                    if row.get("symbol_master_status") == "verified"
                    and row.get("instrument_type") == "EQUITY"
                    and row.get("listing_market") in {"KOSPI", "KOSDAQ"}
                ]
                primary_eligible_forward_summary = _summarize_rows(
                    primary_eligible_forward_rows
                )
            key = f"top_{top_n}"
            coverage[panel][key] = {
                "forward_exact": _summarize_rows(forward_rows),
                "same_day_venue_consistent_retrospective": _summarize_rows(venue_rows),
                "same_day_any_venue_retrospective_noncausal": _summarize_rows(
                    any_venue_rows
                ),
            }
            details[panel][key] = {
                "forward_exact": forward_rows,
                "same_day_venue_consistent_retrospective": venue_rows,
            }

    primary_episode_count = primary_eligible_forward_summary.get("episode_count", 0)
    primary_ex_post_summary = dict(
        primary_eligible_forward_summary.get("ex_post_executable_opportunity") or {}
    )
    (
        primary_ex_post_by_venue_session,
        primary_ex_post_scope_floor_met,
    ) = _summarize_ex_post_by_scope(primary_eligible_forward_rows)
    primary_ex_post_summary["by_venue_session"] = primary_ex_post_by_venue_session
    primary_ex_post_summary["economic_evidence_floor_met"] = (
        primary_ex_post_scope_floor_met
    )
    if not primary_ex_post_scope_floor_met:
        primary_ex_post_summary["source_quality_adjusted_ev_pct"] = None
    primary_candidate_not_promoted_reason_missing_count = sum(
        int(
            (venue_summary.get("candidate_not_promoted_first_reason_counts") or {}).get(
                "reason_missing", 0
            )
        )
        for venue_summary in (
            primary_eligible_forward_summary.get("by_venue") or {}
        ).values()
    )
    instrumentation_blockers = []
    if symbol_master_binding.get("status") != "verified":
        instrumentation_blockers.append("official_symbol_master_binding_missing")
    elif any(
        status != "verified" and count > 0
        for status, count in primary_symbol_master_lookup_counts.items()
    ):
        instrumentation_blockers.append("official_symbol_master_lookup_gap")
    if trigger_contract.get("status") != "verified":
        instrumentation_blockers.append("installed_trigger_contract_missing")
    if not capture_cadence_floor_met:
        instrumentation_blockers.append("capture_cadence_floor_not_met")
    if missing_session_snapshot_count:
        instrumentation_blockers.append("capture_session_provenance_missing")
    if missing_source_hash_snapshot_count:
        instrumentation_blockers.append("capture_source_hash_missing")
    if primary_episode_count < MIN_PRIMARY_OPPORTUNITY_EPISODES:
        instrumentation_blockers.append("opportunity_episode_sample_floor_not_met")
    if primary_candidate_not_promoted_reason_missing_count:
        instrumentation_blockers.append("scanner_prune_first_reason_missing")
    if round_trip_cost_pct is None:
        instrumentation_blockers.append("ex_post_comparison_cost_contract_invalid")
    if primary_episode_count and not external_bbo_capture_contract_reflected:
        instrumentation_blockers.append(
            "external_opportunity_bbo_capture_contract_not_reflected"
        )
    ex_post_floor_summaries = list(primary_ex_post_by_venue_session.values()) or [
        primary_ex_post_summary
    ]
    if any(
        float(summary.get("exact_bbo_join_coverage_pct") or 0.0)
        < EX_POST_ENTRY_COVERAGE_FLOOR_PCT
        for summary in ex_post_floor_summaries
    ):
        instrumentation_blockers.append(
            "ex_post_executable_bbo_join_coverage_floor_not_met"
        )
    if any(
        int(summary.get("resolved_outcome_count") or 0) < EX_POST_MIN_RESOLVED_COUNT
        for summary in ex_post_floor_summaries
    ):
        instrumentation_blockers.append(
            "ex_post_executable_resolved_outcome_floor_not_met"
        )
    if any(
        summary.get("right_censored_pct") is not None
        and float(summary["right_censored_pct"]) > EX_POST_RIGHT_CENSORED_MAX_PCT
        for summary in ex_post_floor_summaries
    ):
        instrumentation_blockers.append(
            "ex_post_executable_right_censored_ceiling_exceeded"
        )
    scanner_recall_state = (
        "scanner_coverage_valid_submit_drought_downstream"
        if not instrumentation_blockers
        else "insufficient_evidence_scanner_recall"
    )
    primary_summary = primary_eligible_forward_summary
    source_quality_warnings = []
    if any(
        status != "verified" and count > 0
        for status, count in symbol_master_lookup_counts.items()
    ) and not any(
        status != "verified" and count > 0
        for status, count in primary_symbol_master_lookup_counts.items()
    ):
        source_quality_warnings.append("non_primary_symbol_master_lookup_gap")
    generated_at = datetime.now(KST)
    primary_decision_by_venue = {}
    for venue, venue_summary in (primary_summary.get("by_venue") or {}).items():
        venue_session_summaries = {
            scope.split("|", 1)[1]: summary
            for scope, summary in primary_ex_post_by_venue_session.items()
            if scope.startswith(f"{venue}|")
        }
        venue_ex_post_summary = dict(
            venue_summary.get("ex_post_executable_opportunity") or {}
        )
        venue_session_floor_met = bool(venue_session_summaries) and all(
            bool(summary.get("economic_evidence_floor_met"))
            for summary in venue_session_summaries.values()
        )
        venue_ex_post_summary["by_session"] = venue_session_summaries
        venue_ex_post_summary["economic_evidence_floor_met"] = venue_session_floor_met
        if not venue_session_floor_met:
            venue_ex_post_summary["source_quality_adjusted_ev_pct"] = None
        denominator = int(
            venue_summary.get("denominator_unique_opportunity_episode_count", 0)
        )
        terminal_counts = dict(
            venue_summary.get("terminal_coverage_reason_counts") or {}
        )
        terminal_count_sum = sum(int(value or 0) for value in terminal_counts.values())
        primary_decision_by_venue[venue] = {
            "denominator_unique_opportunity_episode_count": venue_summary.get(
                "denominator_unique_opportunity_episode_count", 0
            ),
            "entry_ai_provider_reached_unique": (
                venue_summary.get("entry_ai_provider_reached_within_sla_count", 0)
            ),
            "entry_ai_provider_reach_rate_pct": venue_summary.get(
                "entry_ai_provider_reach_rate_pct", 0.0
            ),
            "promotion_recall_pct": venue_summary.get("promotion_recall_pct", 0.0),
            "terminal_coverage_reason_counts": terminal_counts,
            "terminal_coverage_reason_count_sum": terminal_count_sum,
            "terminal_denominator_conservation_delta": (
                denominator - terminal_count_sum
            ),
            "terminal_denominator_conservation_status": (
                "pass" if denominator == terminal_count_sum else "fail"
            ),
            "candidate_not_promoted_first_reason_counts": dict(
                venue_summary.get("candidate_not_promoted_first_reason_counts") or {}
            ),
            "candidate_not_promoted_first_reason_count_sum": venue_summary.get(
                "candidate_not_promoted_first_reason_count_sum", 0
            ),
            "candidate_not_promoted_first_reason_conservation_delta": (
                venue_summary.get(
                    "candidate_not_promoted_first_reason_conservation_delta", 0
                )
            ),
            "candidate_not_promoted_first_reason_conservation_status": (
                venue_summary.get(
                    "candidate_not_promoted_first_reason_conservation_status",
                    "unknown",
                )
            ),
            "ex_post_executable_opportunity": venue_ex_post_summary,
        }

    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "report_type": REPORT_TYPE,
        "target_date": target_date,
        "report_started_at": report_started_at.isoformat(),
        "generated_at": generated_at.isoformat(),
        "status": (
            "ok"
            if valid_snapshots and not instrumentation_blockers
            else (
                "early_evidence_hold_sample"
                if valid_snapshots
                else "source_unavailable"
            )
        ),
        "scanner_recall_state": scanner_recall_state,
        "instrumentation_blockers": instrumentation_blockers,
        "source_quality_warnings": source_quality_warnings,
        "metric_contract": METRIC_CONTRACT,
        "primary_decision": {
            "panel": "liquid_common",
            "top_n": 20,
            "view": "forward_exact",
            "grouping": "venue",
            "metric": "entry_ai_provider_reach_rate_pct",
            "formula": (
                "entry_ai_provider_reached_unique / "
                "denominator_unique_opportunity_episode_count * 100"
            ),
            "by_venue": primary_decision_by_venue,
            "cross_venue_summary_authority": "diagnostic_only",
            "ex_post_executable_opportunity": primary_ex_post_summary,
        },
        "source_quality": {
            "snapshot_count": len(snapshots),
            "foreign_target_date_snapshot_count": (
                len(all_snapshots) - len(target_date_snapshots)
            ),
            "invalid_contract_snapshot_count": sum(
                bool(error) for error in contract_errors
            ),
            "invalid_contract_reasons": sorted(
                {error for error in contract_errors if error}
            ),
            "valid_snapshot_count": len(valid_snapshots),
            "unavailable_snapshot_count": len(snapshots) - len(valid_snapshots),
            "missing_session_snapshot_count": missing_session_snapshot_count,
            "missing_session_capture_ids": missing_session_capture_ids,
            "missing_source_hash_snapshot_count": (missing_source_hash_snapshot_count),
            "missing_source_hash_capture_ids": missing_source_hash_capture_ids,
            "verified_source_hash_snapshot_count": (
                len(valid_snapshots) - missing_source_hash_snapshot_count
            ),
            "valid_capture_times_by_venue_panel": (valid_capture_times_by_venue_panel),
            "observed_capture_cadence_by_venue_panel": (
                observed_capture_cadence_by_venue_panel
            ),
            "capture_cadence_floor_met": capture_cadence_floor_met,
            "symbol_master_binding": symbol_master_binding,
            "symbol_master_lookup_counts": dict(
                sorted(symbol_master_lookup_counts.items())
            ),
            "symbol_master_lookup_codes": {
                status: sorted(codes)
                for status, codes in sorted(symbol_master_lookup_codes.items())
            },
            "primary_symbol_master_lookup_counts": dict(
                sorted(primary_symbol_master_lookup_counts.items())
            ),
            "primary_symbol_master_lookup_codes": {
                status: sorted(code for code in codes if code)
                for status, codes in sorted(primary_symbol_master_lookup_codes.items())
            },
            "primary_candidate_not_promoted_reason_missing_count": (
                primary_candidate_not_promoted_reason_missing_count
            ),
            "ex_post_bbo_source": {
                "stages": [
                    "rising_missed_entry_turn_pre_anchor_bbo_path",
                    "scalping_scanner_prune_bbo_observation",
                ],
                "price_sources": [
                    "existing_ws_route_scoped_0d_snapshot",
                    "ka10004_external_market_census_exact_request_code",
                    "ka10004_rest_orderbook_exact_request_code",
                ],
                "valid_observation_count": len(executable_bbo_times),
                "valid_observation_count_by_price_source": dict(
                    sorted(
                        Counter(
                            observation["price_source"]
                            for venue_index in executable_bbo_index.values()
                            for session_index in venue_index.values()
                            for observations in session_index.values()
                            for observation in observations
                        ).items()
                    )
                ),
                "gap_reason_counts": dict(sorted(executable_bbo_gap_counts.items())),
                "observation_watermark": (
                    observation_watermark.isoformat()
                    if observation_watermark is not None
                    else None
                ),
                "full_external_population_ev_extrapolation_allowed": False,
                "primary_floor_scope": "venue+session",
                "primary_by_venue_session": primary_ex_post_by_venue_session,
                "required_observation_schema_version": (
                    PRUNE_BBO_OBSERVATION_SCHEMA_VERSION
                ),
                "required_promoted_ws_bundle_schema_version": (
                    PRE_ANCHOR_BUNDLE_SCHEMA_VERSION
                ),
                "required_external_census_bbo_schema_version": (
                    EXTERNAL_BBO_OBSERVATION_SCHEMA_VERSION
                ),
                "external_census_contract_row_count": (external_bbo_contract_row_count),
                "external_census_request_attempted_count": (
                    external_bbo_request_attempted_count
                ),
                "external_census_reserved_contract_row_count": (
                    external_bbo_reserved_contract_row_count
                ),
                "external_census_invalid_reservation_attempt_count": (
                    external_bbo_invalid_reservation_attempt_count
                ),
                "external_census_unique_reserved_ordinal_count": (
                    external_bbo_unique_reserved_ordinal_count
                ),
                "external_census_duplicate_reserved_ordinal_count": (
                    external_bbo_duplicate_reserved_ordinal_count
                ),
                "external_census_reservation_accounted_count": (
                    external_bbo_reservation_accounted_count
                ),
                "external_census_reservation_conservation_delta": (
                    external_bbo_reservation_conservation_delta
                ),
                "external_census_reservation_conservation_status": (
                    external_bbo_reservation_conservation_status
                ),
                "external_census_max_reserved_ordinal": (
                    external_bbo_max_reserved_ordinal
                ),
                "external_census_capture_contract_reflected": (
                    external_bbo_capture_contract_reflected
                ),
                "external_census_budget_contract": external_bbo_budget_contract,
                "producer_pid_contract_reflected": observer_pid_contract_reflected,
                "latest_producer_runtime_receipt": (
                    {
                        **latest_observer_runtime_receipt,
                        "emitted_at": latest_observer_runtime_receipt[
                            "emitted_at"
                        ].isoformat(),
                    }
                    if latest_observer_runtime_receipt is not None
                    else None
                ),
            },
            "comparison_cost_contract": cost_contract,
            "report_freshness": {
                "latest_valid_snapshot_at": (
                    max(snapshot_capture_times).isoformat()
                    if snapshot_capture_times
                    else None
                ),
                "latest_exact_bbo_at": (
                    max(executable_bbo_times).isoformat()
                    if executable_bbo_times
                    else None
                ),
                "observation_watermark": (
                    observation_watermark.isoformat()
                    if observation_watermark is not None
                    else None
                ),
                "source_to_report_lag_sec": (
                    round((generated_at - observation_watermark).total_seconds(), 6)
                    if observation_watermark is not None
                    else None
                ),
                "freshness_authority": (
                    "artifact_generation_only_not_current_pid_runtime_acceptance"
                ),
            },
            "raw_opportunity_episode_counts_before_master_gate": raw_episode_counts,
            "installed_trigger_contract": trigger_contract,
            "funnel_instrumentation_contract": {
                "source_seen": sorted(PIPELINE_STAGE_MAP["source_seen"]),
                "candidate_evaluated": sorted(
                    PIPELINE_STAGE_MAP["candidate_evaluated"]
                ),
                "watch_admitted": sorted(PIPELINE_STAGE_MAP["watch_admitted"]),
                "runtime_watch_attached": sorted(
                    PIPELINE_STAGE_MAP["runtime_watch_attached"]
                ),
                "trusted_ai": "exact entry AI trace with provider_actual!=none",
                "entry_authority_decided": sorted(
                    PIPELINE_STAGE_MAP["entry_authority_decided"]
                ),
                "submit_safety_checked": sorted(
                    PIPELINE_STAGE_MAP["submit_safety_checked"]
                ),
                "lineage_key": "scanner_promotion_id+runtime_record_id+venue+session",
                "runtime_effect": False,
            },
            "snapshot_path": str(snapshots_path),
            "pipeline_path": str(existing_or_gzip_path(events_path)),
            "ai_trace_path": str(existing_or_gzip_path(trace_path)),
            "postclose_snapshot_forward_warning": (
                "forward_exact requires intraday captures; same-day retrospective "
                "is noncausal diagnostic evidence only"
            ),
        },
        "coverage": coverage,
        "opportunity_details": details,
    }


def render_markdown(report: dict[str, Any]) -> str:
    primary = report.get("primary_decision") or {}
    ex_post_bbo_source = (
        (report.get("source_quality") or {}).get("ex_post_bbo_source") or {}
    )
    lines = [
        f"# Market Opportunity Census - {report.get('target_date')}",
        "",
        f"- status: `{report.get('status')}`",
        f"- scanner_recall_state: `{report.get('scanner_recall_state')}`",
        f"- decision_authority: `{METRIC_CONTRACT['decision_authority']}`",
        "- runtime_effect: `false`",
        "- actual_order_submitted: `false`",
        (
            "- warning: forward_exact requires intraday captures; retrospective "
            "coverage is noncausal and cannot authorize BUY."
        ),
        "- instrumentation_blockers: "
        + ", ".join(f"`{item}`" for item in report.get("instrumentation_blockers", [])),
        "",
        "## Primary Decision Metric",
        "",
        (
            "- scope: "
            f"`{primary.get('panel')}/top_{primary.get('top_n')}/"
            f"{primary.get('view')}`; official-master eligible; venue-separated"
        ),
        f"- metric: `{primary.get('metric')}`",
        "",
        "| Venue | Eligible episodes | Provider reached within SLA | Provider reach % | Promotion recall % | Terminal count sum | Conservation delta | Conservation |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    terminal_reason_lines: list[str] = []
    candidate_not_promoted_reason_lines: list[str] = []
    for venue, summary in (primary.get("by_venue") or {}).items():
        lines.append(
            "| "
            f"{venue} | "
            f"{summary.get('denominator_unique_opportunity_episode_count', 0)} | "
            f"{summary.get('entry_ai_provider_reached_unique', 0)} | "
            f"{summary.get('entry_ai_provider_reach_rate_pct', 0.0)} | "
            f"{summary.get('promotion_recall_pct', 0.0)} | "
            f"{summary.get('terminal_coverage_reason_count_sum', 0)} | "
            f"{summary.get('terminal_denominator_conservation_delta', 0)} | "
            f"{summary.get('terminal_denominator_conservation_status', 'unknown')} |"
        )
        reason_counts = summary.get("terminal_coverage_reason_counts") or {}
        terminal_reason_lines.append(
            f"- {venue} terminal coverage reasons: "
            + ", ".join(
                f"`{reason}`={count}" for reason, count in sorted(reason_counts.items())
            )
        )
        first_reason_counts = (
            summary.get("candidate_not_promoted_first_reason_counts") or {}
        )
        candidate_not_promoted_reason_lines.append(
            f"- {venue}: "
            + (
                ", ".join(
                    f"`{reason}`={count}"
                    for reason, count in sorted(first_reason_counts.items())
                )
                if first_reason_counts
                else "none"
            )
            + "; count_sum="
            f"{summary.get('candidate_not_promoted_first_reason_count_sum', 0)}"
            + "; conservation_delta="
            f"{summary.get('candidate_not_promoted_first_reason_conservation_delta', 0)}"
            + "; conservation_status="
            f"`{summary.get('candidate_not_promoted_first_reason_conservation_status', 'unknown')}`"
        )
    lines.extend(
        [
            "",
            "### Terminal Coverage Reasons",
            "",
            *terminal_reason_lines,
            "",
            "### Candidate Not Promoted First Reasons",
            "",
            *candidate_not_promoted_reason_lines,
            "",
            "## Ex-post Executable Opportunity (Source-only)",
            "",
            (
                "- Direct external-census, promoted-WS, and bounded prune-observer "
                "exact-route BBOs only; ka10027 mark prices are never substituted "
                "for executable prices."
            ),
            (
                "- comparison cost: `"
                + str(
                    (
                        (report.get("source_quality") or {}).get(
                            "comparison_cost_contract"
                        )
                        or {}
                    ).get("round_trip_cost_pct")
                )
                + "%`"
            ),
            (
                "- external BBO request reservation conservation: "
                f"attempted={ex_post_bbo_source.get('external_census_request_attempted_count', 0)}, "
                f"valid={ex_post_bbo_source.get('external_census_reserved_contract_row_count', 0)}, "
                f"invalid={ex_post_bbo_source.get('external_census_invalid_reservation_attempt_count', 0)}, "
                f"unique={ex_post_bbo_source.get('external_census_unique_reserved_ordinal_count', 0)}, "
                f"duplicate={ex_post_bbo_source.get('external_census_duplicate_reserved_ordinal_count', 0)}, "
                f"delta={ex_post_bbo_source.get('external_census_reservation_conservation_delta', 0)}, "
                f"status=`{ex_post_bbo_source.get('external_census_reservation_conservation_status', 'unknown')}`"
            ),
            "",
            "| Venue | Episodes | Exact BBO joined | Coverage % | Executable entry | Resolved 20m | Right-censored % | Observed cohort net EV % | Decision EV % | Floor |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---:|---|",
            *[
                "| "
                + f"{venue} | "
                + f"{(summary.get('ex_post_executable_opportunity') or {}).get('denominator_unique_opportunity_episode_count', 0)} | "
                + f"{(summary.get('ex_post_executable_opportunity') or {}).get('exact_bbo_joined_count', 0)} | "
                + f"{(summary.get('ex_post_executable_opportunity') or {}).get('exact_bbo_join_coverage_pct', 0.0)} | "
                + f"{(summary.get('ex_post_executable_opportunity') or {}).get('executable_entry_eligible_count', 0)} | "
                + f"{(summary.get('ex_post_executable_opportunity') or {}).get('resolved_outcome_count', 0)} | "
                + f"{(summary.get('ex_post_executable_opportunity') or {}).get('right_censored_pct')} | "
                + f"{(summary.get('ex_post_executable_opportunity') or {}).get('observed_cohort_source_quality_adjusted_ev_pct')} | "
                + f"{(summary.get('ex_post_executable_opportunity') or {}).get('source_quality_adjusted_ev_pct')} | "
                + f"{(summary.get('ex_post_executable_opportunity') or {}).get('economic_evidence_floor_met', False)} |"
                for venue, summary in (primary.get("by_venue") or {}).items()
            ],
            "",
            "## Coverage",
            "",
            "| Panel | Window | Venue | View | Episodes | Promotion recall % | Heavy recall % | Provider reach % | PREV_CLOSE_GAINER source | Promote→AI p50 sec | Submitted |",
            "|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for panel, panel_rows in report.get("coverage", {}).items():
        for window, views in panel_rows.items():
            for view, summary in sorted(views.items()):
                summaries = [("ALL", summary), *summary.get("by_venue", {}).items()]
                for venue, venue_summary in summaries:
                    counts = venue_summary.get("stage_counts") or {}
                    latency = (
                        venue_summary.get("stage_latency_from_scanner_promoted_sec")
                        or {}
                    ).get("entry_ai_provider_called") or {}
                    lines.append(
                        "| "
                        f"{panel} | {window.replace('top_', '')} | {venue} | "
                        f"{view} | {venue_summary.get('episode_count', 0)} | "
                        f"{venue_summary.get('promotion_recall_pct')} | "
                        f"{venue_summary.get('heavy_eval_recall_pct')} | "
                        f"{venue_summary.get('entry_ai_provider_reach_rate_pct')} | "
                        f"{venue_summary.get('prev_close_gainer_source_promotion_count', 0)} | "
                        f"{latency.get('p50_sec')} | "
                        f"{counts.get('submitted', 0)} |"
                    )
    lines.extend(
        [
            "",
            "## Forbidden Uses",
            "",
            *[f"- `{item}`" for item in FORBIDDEN_USES],
            "",
        ]
    )
    return "\n".join(lines)


def write_report(report: dict[str, Any]) -> tuple[Path, Path]:
    target_date = str(report.get("target_date") or date.today().isoformat())
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    json_path = REPORT_DIR / f"{REPORT_TYPE}_{target_date}.json"
    md_path = REPORT_DIR / f"{REPORT_TYPE}_{target_date}.md"
    json_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, md_path


def _parse_csv(value: str) -> tuple[str, ...]:
    return tuple(item.strip() for item in value.split(",") if item.strip())


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target-date", default=date.today().isoformat())
    parser.add_argument("--capture", action="store_true")
    parser.add_argument("--capture-only", action="store_true")
    parser.add_argument("--write", action="store_true")
    parser.add_argument("--venues", default="KRX,NXT")
    parser.add_argument("--panels", default="all,liquid_common")
    parser.add_argument("--limit", type=int, default=200)
    parser.add_argument("--snapshot-path")
    parser.add_argument("--pipeline-path")
    parser.add_argument("--ai-trace-path")
    parser.add_argument("--symbol-master-path")
    parser.add_argument("--trigger-receipt-path")
    parser.add_argument(
        "--skip-executable-bbo",
        action="store_true",
        help="Disable bounded source-only ka10004 capture for this invocation.",
    )
    parser.add_argument("--print-summary", action="store_true")
    args = parser.parse_args()
    if args.capture_only and not args.capture:
        parser.error("--capture-only requires --capture")
    if args.capture_only and args.write:
        parser.error("--capture-only cannot be combined with --write")

    snapshot_path = (
        Path(args.snapshot_path)
        if args.snapshot_path
        else SNAPSHOT_DIR / f"{REPORT_TYPE}_{args.target_date}.jsonl"
    )
    captured_count = 0
    if args.capture:
        token = kiwoom_utils.get_kiwoom_token()
        if not token:
            raise SystemExit("Kiwoom token unavailable")
        bbo_budget_path = EXTERNAL_BBO_BUDGET_DIR / (
            f"external_bbo_request_budget_{args.target_date}.json"
        )
        pre_ledger_bbo_request_count = _count_external_bbo_requests(
            snapshot_path,
            target_date=args.target_date,
        )
        records = capture_market_snapshots(
            token,
            target_date=args.target_date,
            venues=_parse_csv(args.venues),
            panels=_parse_csv(args.panels),
            limit=max(1, args.limit),
            collect_executable_bbo=not args.skip_executable_bbo,
            bbo_request_reserver=lambda: _reserve_external_bbo_request(
                bbo_budget_path,
                target_date=args.target_date,
                initial_reserved_count=pre_ledger_bbo_request_count,
            ),
        )
        captured_count = append_snapshot_records(snapshot_path, records)

    if args.capture_only:
        print(
            json.dumps(
                {
                    "status": "captured_source_only",
                    "captured_records": captured_count,
                    "snapshot_path": str(snapshot_path),
                    "external_bbo_budget_path": str(bbo_budget_path),
                    "external_bbo_pre_ledger_request_count": (
                        pre_ledger_bbo_request_count
                    ),
                    "external_bbo_daily_request_cap": (
                        EXTERNAL_BBO_MAX_REQUESTS_PER_KST_DATE
                    ),
                    "external_bbo_collection_enabled": (not args.skip_executable_bbo),
                    "market_data_request_effect": (not args.skip_executable_bbo),
                    "runtime_effect": False,
                    "allowed_runtime_apply": False,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return

    report = build_report(
        args.target_date,
        snapshot_path=snapshot_path,
        pipeline_path=Path(args.pipeline_path) if args.pipeline_path else None,
        ai_trace_path=Path(args.ai_trace_path) if args.ai_trace_path else None,
        symbol_master_path=(
            Path(args.symbol_master_path) if args.symbol_master_path else None
        ),
        trigger_receipt_path=(
            Path(args.trigger_receipt_path) if args.trigger_receipt_path else None
        ),
    )
    output_paths: tuple[Path, Path] | None = None
    if args.write:
        output_paths = write_report(report)
    if args.print_summary or args.capture or args.write:
        liquid_top_20 = (
            report.get("coverage", {})
            .get("liquid_common", {})
            .get("top_20", {})
            .get("same_day_venue_consistent_retrospective", {})
        )
        print(
            json.dumps(
                {
                    "status": report.get("status"),
                    "scanner_recall_state": report.get("scanner_recall_state"),
                    "instrumentation_blockers": report.get("instrumentation_blockers"),
                    "captured_records": captured_count,
                    "snapshot_path": str(snapshot_path),
                    "report_paths": (
                        [str(path) for path in output_paths] if output_paths else []
                    ),
                    "liquid_top_20_retrospective": liquid_top_20,
                    "runtime_effect": False,
                    "actual_order_submitted": False,
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )


if __name__ == "__main__":
    main()
