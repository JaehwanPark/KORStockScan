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
from src.engine.scalping.micro_reversion.symbol_master import VerifiedSymbolMaster
from src.utils.constants import DATA_DIR
from src.utils.jsonl_io import existing_or_gzip_path, iter_jsonl

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
INCREMENTAL_STATE_SCHEMA_VERSION = "intraday_ws_freshness_incremental_v6"
SCANNER_BBO_MAX_QUOTE_AGE_MS = 1_000.0
SCANNER_BBO_GROSS_TARGET_PCT = 1.30
SCANNER_BBO_ADVERSE_STOP_PCT = -0.70
SCANNER_BBO_HORIZON_SEC = 20 * 60
SCANNER_BBO_TIMEOUT_MAX_LAG_SEC = 5.0
SCANNER_BBO_JOIN_COVERAGE_FLOOR_PCT = 95.0

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


def _load_verified_symbol_master(
    target_date: str, symbol_master_path: Path | None
) -> tuple[VerifiedSymbolMaster | None, dict[str, Any]]:
    requested_path = symbol_master_path or (
        SYMBOL_MASTER_DIR / f"micro_reversion_symbol_master_{target_date}.json"
    )
    actual_path = existing_or_gzip_path(requested_path)
    if not actual_path.exists():
        return None, {
            "status": "missing",
            "path": str(actual_path),
            "artifact_sha256": None,
            "symbol_count": 0,
        }
    try:
        master = VerifiedSymbolMaster.from_json_path(
            actual_path, require_canonical_owner=True
        )
        artifact_sha256 = hashlib.sha256(actual_path.read_bytes()).hexdigest()
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return None, {
            "status": "invalid",
            "path": str(actual_path),
            "artifact_sha256": None,
            "symbol_count": 0,
            "error": f"{type(exc).__name__}:{exc}",
        }
    return master, {
        "status": "verified",
        "path": str(actual_path),
        "artifact_sha256": artifact_sha256,
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
        ),
        (
            "scanner_promotion_reanchor_bbo",
            "scanner_promotion_reanchor_best_bid",
            "scanner_promotion_reanchor_best_ask",
            "scanner_promotion_reanchor_effective_quote_age_ms",
            "scanner_promotion_reanchor_source",
            "scanner_promotion_reanchor_source_fresh",
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
        observed_at = _event_time(dict(row))
        if observed_at is None:
            gap_reasons.append(f"{source}:event_time_missing")
            continue
        return (
            {
                "observed_at": observed_at.isoformat(),
                "observed_epoch": observed_at.timestamp(),
                "best_bid": bid,
                "best_ask": ask,
                "quote_age_ms": quote_age_ms,
                "source": source,
                "source_provenance": source_provenance,
                "venue": venue,
                "market_session_bucket": market_session_bucket,
            },
            "pass",
        )
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
    fingerprints = value.get("event_fingerprints")
    return {
        "lineages": {
            str(key): dict(item)
            for key, item in lineages.items()
            if isinstance(item, dict)
        },
        "prunes": {
            str(key): dict(item)
            for key, item in prunes.items()
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
        "scalping_scanner_candidate_pruned",
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
    code = str(row.get("stock_code") or row.get("code") or "").strip()[:6]
    promotion_id = _valid_lineage_token(row.get("scanner_promotion_id"))
    generation_id = _valid_lineage_token(row.get("scanner_scan_generation_id"))
    scan_rank = _positive_integer_metadata(row.get("scanner_scan_rank"))
    ranked_candidate_count = _positive_integer_metadata(
        row.get("scanner_ranked_candidate_count")
    )
    venue = _scanner_venue_metadata(row)
    market_session_bucket = _scanner_session_metadata(row)
    if stage == "scalping_scanner_candidate_pruned":
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
    if prune.get(
        "reason"
    ) == "reentry_cooldown_no_material_upgrade" and "MARKET_GAINER" not in str(
        prune.get("source_signature") or ""
    ):
        return "non_gainer_not_rising_repeat"
    return None


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
    for prune in prunes:
        cohort = _scanner_prune_economic_cohort(prune)
        if cohort:
            candidates.append(
                (
                    cohort,
                    f"{prune.get('scan_generation_id') or ''}:{prune.get('code') or ''}",
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
        if venue not in {"KRX", "PREMARKET_KRX_LIKE", "NXT"}:
            bbo_join_block_reason = "authoritative_venue_missing"
        elif session in {"", "UNKNOWN"}:
            bbo_join_block_reason = "authoritative_session_missing"
        elif metadata_conflicts:
            bbo_join_block_reason = "immutable_lineage_metadata_conflict"
        elif not observations:
            bbo_join_block_reason = (
                observation_filter_reasons.most_common(1)[0][0]
                if observation_filter_reasons
                else "fresh_executable_bbo_missing"
            )
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
            if observed_epoch <= entry_epoch or observed_epoch > horizon_epoch:
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
        venue_session_economics.append(
            {
                "venue": venue,
                "market_session_bucket": session,
                "status": group_status,
                "source_census_count": len(group_rows),
                "eligible_verified_common_stock_candidate_count": len(
                    group_eligible_rows
                ),
                "official_symbol_master_excluded_count": len(group_rows)
                - len(group_eligible_rows),
                "exact_bbo_joined_count": len(group_joined_rows),
                "exact_bbo_join_coverage_pct": group_coverage_pct,
                "resolved_outcome_count": len(group_resolved_rows),
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
    source_capture_design_required = any(
        row["source_capture_gap"]
        and row["cohort"] == "non_gainer_not_rising_repeat"
        and row["exact_bbo_joined_count"] == 0
        for row in cohort_source_quality
    )
    source_capture_repair_required = any(
        row["source_capture_gap"] for row in cohort_source_quality
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
        "source_capture_design_required": source_capture_design_required,
        "source_capture_repair_required": source_capture_repair_required,
        "first_hit_observation_contract": (
            "sampled_scanner_stage_bbo_event_order_not_continuous_market_path"
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
    prunes = list((state.get("prunes") or {}).values())
    bbo_attribution = _scanner_bbo_economic_attribution(
        lineages,
        prunes,
        target_date=target_date,
        symbol_master=symbol_master,
        symbol_master_binding=symbol_master_binding,
    )
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
                for prune in prunes
                if prune.get("reason") == "reentry_cooldown_no_material_upgrade"
                and "MARKET_GAINER" not in str(prune.get("source_signature") or "")
            ),
            "executable_bbo_ev_status": bbo_attribution["status"],
            "executable_bbo_attribution": bbo_attribution,
        },
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
        "source_capture_design_required": bool(
            attribution.get("source_capture_design_required")
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
        )
    )
    if (
        economic_candidate_count
        and economic_cohorts.get("executable_bbo_ev_status")
        != "source_only_economics_available"
    ):
        source_capture_design_required = bool(
            (economic_cohorts.get("executable_bbo_attribution") or {}).get(
                "source_capture_design_required"
            )
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
                "decision": (
                    "design_family_candidate"
                    if source_capture_design_required
                    else "defer_evidence"
                ),
                "next_action": (
                    "design_capacity_bounded_source_only_bbo_capture_for_depleted_scanner_cohorts"
                    if source_capture_design_required
                    else "recheck_exact_bbo_coverage_and_resolved_outcomes_after_next_natural_session"
                ),
                "implementation_state": (
                    "executable_bbo_consumer_implemented_source_capture_design_required"
                    if source_capture_design_required
                    else "executable_bbo_join_implemented_waiting_source_quality"
                ),
                "order_id": "order_scanner_funnel_executable_bbo_join",
                "title": "Scanner funnel executable-BBO economic attribution",
                "priority": 2,
                "intent": (
                    "Join each unique lost scanner generation to fresh executable bid/ask, quote age, "
                    "venue/session, fixed effective-dated costs, sampled target/adverse first-hit, and "
                    "sampled timeout exit without claiming a continuous market path."
                ),
                "evidence": [
                    f"economic_candidate_count={economic_candidate_count}",
                    f"economic_cohorts={economic_cohorts_evidence}",
                ],
                "files_likely_touched": [
                    "src/engine/scalping/micro_reversion/collection_targets.py",
                    "src/engine/monitoring/rising_missed_intraday_feedback.py",
                    "src/engine/monitoring/intraday_ws_freshness_monitor.py",
                    "src/tests/test_micro_reversion_collection_targets.py",
                    "src/tests/test_rising_missed_intraday_feedback.py",
                    "src/tests/test_intraday_ws_freshness_monitor.py",
                ],
                "acceptance_tests": [
                    "source_capture_design_preserves_active_owner_targets_and_reviewed_ws_item_budget",
                    "exact_promotion_venue_session_bbo_join_coverage_pct>=95",
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
