"""Main source replay readers transferred from retired episode attribution."""
from __future__ import annotations
from src.engine.scalping.micro_reversion.observer_source_quality import source_close_verified, MAIN_SOURCE_CONTRACT, source_loss_counters, main_raw_epoch_validation
import gzip
import hashlib
import json
import math
from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence
from zoneinfo import ZoneInfo
from src.engine.scalping.micro_reversion.observer_source_quality import CANARY_LOSS_COUNTERS as CANARY_LOSS_COUNTERS, CANARY_FORBIDDEN_TRUE_FIELDS as CANARY_FORBIDDEN_TRUE_FIELDS, closed_pre_enqueue_epoch_quarantine_validation, timestamp_regression_row_quarantine_validation as _timestamp_regression_row_quarantine_validation
from src.engine.scalping.micro_reversion.p2_replay import DEFAULT_SOURCE_EXCLUSION_MANIFEST, load_source_exclusion_manifest
from src.engine.scalping.micro_reversion.path_journal import MARKET_STREAM_CONTRACT_ID, MarketDepthPoint, MarketStreamPoint, readable_partition_path_files
from src.engine.scalping.micro_reversion.path_capture import PathEventReference
from src.engine.scalping.micro_reversion.depth_join import validate_depth_row as validate_canonical_depth_row
from src.trading.market.confirmation_window import FEATURE_VERSION, build_confirmation_window
from src.utils.constants import DATA_DIR
from src.utils.market_day import is_krx_trading_day

POSTCLOSE_COMPLETE_TIME = time(20, 0)

KST_SUFFIX = "+09:00"

KST = ZoneInfo("Asia/Seoul")

OBSERVATION_ROOT = DATA_DIR / "observations" / "scalp_micro_reversion_forward"

DEFAULT_CANARY_SNAPSHOT_PATH = (
    DATA_DIR / "runtime" / "scalp_micro_reversion_forward_collector" / "latest.json"
)

CANARY_DAILY_SNAPSHOT_DIR = (
    DATA_DIR / "source_quality" / "scalp_micro_reversion_canary_daily"
)

PRE_WINDOW_SEC = 30

POST_WINDOW_SEC = 180

MARKET_WEAKNESS_COUNTERFACTUAL_POST_WINDOW_SEC = 30 * 60

CANARY_COMPLETE_AFTER_KST = time(20, 0)

DUAL_AFTERMARKET_SESSION_PREFIX = "KRX_NXT_AFTERMARKET"

def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None

def daily_canary_snapshot_path(
    target_date: date, *, root: Path = CANARY_DAILY_SNAPSHOT_DIR
) -> Path:
    return (
        root / f"scalp_micro_reversion_canary_snapshot_{target_date.isoformat()}.json"
    )

def _canary_snapshot_date(payload: dict[str, Any] | None) -> date | None:
    generated_at = _parse_owner_ts((payload or {}).get("generated_at"))
    return generated_at.astimezone(KST).date() if generated_at is not None else None

def resolve_target_canary_snapshot(
    *,
    target_date: date,
    latest_path: Path | None,
    daily_root: Path = CANARY_DAILY_SNAPSHOT_DIR,
) -> Path | None:
    if latest_path is None:
        return None
    daily_path = daily_canary_snapshot_path(target_date, root=daily_root)
    if _canary_snapshot_date(_read_json(latest_path)) == target_date:
        return latest_path
    if daily_path.exists():
        return daily_path
    return latest_path

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

def _parse_owner_ts(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo is not None else None

def _finite_float(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None

def _partition_stream_files(
    partition: Path, logical_name: str
) -> tuple[list[tuple[Path, str, str]], list[str]]:
    paths: list[tuple[Path, str, str]] = []
    errors: list[str] = []
    for session_dir in sorted(partition.glob("venue=*/session=*")):
        venue = session_dir.parent.name.partition("=")[2]
        session = session_dir.name.partition("=")[2]
        if not venue or not session:
            errors.append(f"{session_dir}:invalid_partition_scope")
            continue
        base = session_dir / logical_name
        try:
            discovered = readable_partition_path_files(base)
        except ValueError as exc:
            errors.append(f"{base}:{exc}")
            continue
        paths.extend((path, venue, session) for path in discovered)
    return paths, errors

def _iter_relevant_rows(
    paths: Iterable[tuple[Path, str, str]],
    symbols: set[str],
    *,
    diagnostics: dict[str, int] | None = None,
) -> Iterable[dict[str, Any]]:
    for path, partition_venue, partition_session in paths:
        try:
            opener = gzip.open if path.suffix == ".gz" else Path.open
            with opener(path, "rt", encoding="utf-8") as handle:
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
                        if diagnostics is not None:
                            diagnostics["malformed_relevant_json_line_count"] = (
                                diagnostics.get("malformed_relevant_json_line_count", 0)
                                + 1
                            )
                        continue
                    if (
                        isinstance(payload, dict)
                        and str(payload.get("symbol")) in symbols
                    ):
                        row = dict(payload)
                        row["_partition_venue"] = partition_venue
                        row["_partition_session_bucket"] = partition_session
                        yield row
        except OSError:
            if diagnostics is not None:
                diagnostics["source_file_read_error_count"] = (
                    diagnostics.get("source_file_read_error_count", 0) + 1
                )
            continue

def _scope_contract_key(payload: dict[str, Any]) -> str:
    return (
        f"{str(payload.get('venue') or 'unknown')}|"
        f"{str(payload.get('session_bucket') or 'unknown')}"
    )

def _physical_scope_contract_key(payload: dict[str, Any]) -> str:
    return (
        f"{str(payload.get('_partition_venue') or 'unknown')}|"
        f"{str(payload.get('_partition_session_bucket') or 'unknown')}"
    )

def _physical_scope_matches_row(payload: dict[str, Any]) -> bool:
    return bool(
        payload.get("venue") == payload.get("_partition_venue")
        and payload.get("session_bucket") == payload.get("_partition_session_bucket")
    )

def _market_axis_context(payload: Mapping[str, Any]) -> dict[str, Any]:
    """Preserve market-data scope without inferring a physical fill venue."""

    venue = str(payload.get("venue") or "").strip().upper()
    session = (
        str(
            payload.get("market_session_regime")
            or payload.get("session_bucket")
            or "UNKNOWN"
        )
        .strip()
        .upper()
    )
    decision_scope = (
        str(
            payload.get("decision_market_scope")
            or payload.get("effective_venue")
            or venue
            or "UNKNOWN"
        )
        .strip()
        .upper()
    )
    route = str(payload.get("market_data_route") or "").strip().lower()
    if route not in {"krx_only", "nxt_only", "krx_nxt_integrated"}:
        route = {
            "KRX": "krx_only",
            "NXT": "nxt_only",
            "SOR": "krx_nxt_integrated",
            "KRX_NXT_INTEGRATED": "krx_nxt_integrated",
        }.get(decision_scope, "unknown")
    actual_venue = (
        str(payload.get("actual_execution_venue") or "UNKNOWN").strip().upper()
    )
    if actual_venue not in {"KRX", "NXT"}:
        actual_venue = "UNKNOWN"
    dual_source_only = bool(
        decision_scope == "KRX_NXT_INTEGRATED"
        or session.startswith(DUAL_AFTERMARKET_SESSION_PREFIX)
    )
    return {
        "decision_market_scope": decision_scope,
        "market_data_route": route,
        "market_session_regime": session,
        "actual_execution_venue": actual_venue,
        "dual_source_only": dual_source_only,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }

def _depth_item_matches_scope(payload: dict[str, Any]) -> bool:
    symbol = str(payload.get("symbol") or "").strip()
    venue = str(payload.get("venue") or "").strip().upper()
    expected_item = (
        symbol
        if venue == "KRX"
        else (
            f"{symbol}_NX"
            if venue == "NXT"
            else f"{symbol}_AL" if venue == "SOR" else ""
        )
    )
    return bool(symbol and expected_item and payload.get("item") == expected_item)

def _validate_stream_row(
    payload: dict[str, Any],
) -> tuple[bool, bool, datetime | None, float | None, float | None, float | None]:
    schema = payload.get("schema")
    timestamp = _parse_owner_ts(
        payload.get("local_receive_timestamp") or payload.get("exchange_timestamp")
    )
    price = _finite_float(payload.get("trade_price"))
    best_bid = _finite_float(payload.get("best_bid"))
    best_ask = _finite_float(payload.get("best_ask"))
    authority_valid = bool(
        payload.get("actual_order_submitted") is False
        and payload.get("broker_order_forbidden") is True
        and payload.get("trading_runtime_effect") is False
    )
    path_consumer_eligible = payload.get("path_consumer_eligible") is not False
    basic_valid = bool(
        schema
        in {
            "scalp_micro_reversion_market_stream_point_v1",
            "scalp_micro_reversion_market_stream_point_v2",
            "scalp_micro_reversion_market_stream_point_v3",
        }
        and authority_valid
        and timestamp is not None
        and price is not None
        and price > 0
        and (best_bid is None or best_bid > 0)
        and (best_ask is None or best_ask > 0)
        and not (best_bid is not None and best_ask is not None and best_ask < best_bid)
    )
    if basic_valid and schema == "scalp_micro_reversion_market_stream_point_v3":
        try:
            if payload.get("metric_contract_id") != MARKET_STREAM_CONTRACT_ID:
                raise ValueError("unexpected canonical stream metric contract")
            MarketStreamPoint(
                symbol=str(payload.get("symbol") or ""),
                exchange_timestamp=payload.get("exchange_timestamp"),
                local_receive_timestamp=payload.get("local_receive_timestamp"),
                source_sequence=payload.get("source_sequence"),
                sequence_epoch=payload.get("sequence_epoch"),
                series_sequence=payload.get("series_sequence"),
                venue=payload.get("venue"),
                session_bucket=payload.get("session_bucket"),
                realtime_type=payload.get("realtime_type"),
                trade_price=price,
                trade_qty=payload.get("trade_qty"),
                best_bid=best_bid,
                best_ask=best_ask,
                bid_depth=payload.get("bid_depth"),
                ask_depth=payload.get("ask_depth"),
                quote_age_ms=payload.get("quote_age_ms"),
                aggressor_side=payload.get("aggressor_side") or "UNKNOWN",
                path_order_status=payload.get("path_order_status"),
                path_consumer_eligible=payload.get("path_consumer_eligible"),
                exchange_timestamp_regression_ms=payload.get(
                    "exchange_timestamp_regression_ms"
                ),
                schema=payload.get("schema"),
            )
        except (TypeError, ValueError):
            basic_valid = False
            path_consumer_eligible = False
    # V1/V2 are archive compatibility rows. They predate the V3 ordering
    # provenance fields, so only the shared strict timestamp/price/authority
    # contract applies and they can never claim V3 path-order validation.
    return (
        basic_valid,
        path_consumer_eligible,
        timestamp,
        price,
        best_bid,
        best_ask,
    )

def _validate_depth_row(
    payload: dict[str, Any],
) -> tuple[
    bool, datetime | None, float | None, float | None, float | None, float | None
]:
    timestamp = _parse_owner_ts(
        payload.get("local_receive_timestamp") or payload.get("exchange_timestamp")
    )
    bid_depth = _finite_float(payload.get("bid_depth"))
    ask_depth = _finite_float(payload.get("ask_depth"))
    best_bid = _finite_float(payload.get("best_bid"))
    best_ask = _finite_float(payload.get("best_ask"))
    valid = bool(
        payload.get("schema") == "scalp_micro_reversion_market_depth_point_v1"
        and payload.get("trading_runtime_effect") is False
        and payload.get("actual_order_submitted") is False
        and payload.get("broker_order_forbidden") is True
        and timestamp is not None
        and _depth_item_matches_scope(payload)
    )
    if valid:
        try:
            validate_canonical_depth_row(payload)
            MarketDepthPoint(
                symbol=str(payload.get("symbol") or ""),
                exchange_timestamp=payload.get("exchange_timestamp"),
                local_receive_timestamp=payload.get("local_receive_timestamp"),
                source_sequence=payload.get("source_sequence"),
                sequence_epoch=payload.get("sequence_epoch"),
                series_sequence=payload.get("series_sequence"),
                venue=payload.get("venue"),
                session_bucket=payload.get("session_bucket"),
                item=payload.get("item"),
                orderbook_time_raw=payload.get("orderbook_time_raw"),
                best_bid=best_bid,
                best_ask=best_ask,
                best_bid_qty=payload.get("best_bid_qty"),
                best_ask_qty=payload.get("best_ask_qty"),
                bid_depth=payload.get("bid_depth"),
                ask_depth=payload.get("ask_depth"),
                bid_levels=payload.get("bid_levels"),
                ask_levels=payload.get("ask_levels"),
                route_depth_totals=payload.get("route_depth_totals"),
                realtime_type=payload.get("realtime_type"),
                schema=payload.get("schema"),
            )
        except (TypeError, ValueError):
            valid = False
    return valid, timestamp, bid_depth, ask_depth, best_bid, best_ask

def _validate_reference_row(
    payload: dict[str, Any], target_date: str
) -> tuple[bool, datetime | None]:
    valid = bool(
        payload.get("schema") == "scalp_micro_reversion_path_event_reference_v2"
        and payload.get("trading_runtime_effect") is False
        and payload.get("actual_order_submitted") is False
        and payload.get("broker_order_forbidden") is True
        and not isinstance(payload.get("event_detected_at_ms"), bool)
    )
    if valid:
        try:
            reference = PathEventReference(
                parent_wave_id=payload.get("parent_wave_id"),
                path_segment_id=payload.get("path_segment_id"),
                shock_event_id=payload.get("shock_event_id"),
                shock_horizon_ms=payload.get("shock_horizon_ms"),
                event_sequence_in_wave=payload.get("event_sequence_in_wave"),
                event_detected_at_ms=payload.get("event_detected_at_ms"),
                symbol=payload.get("symbol"),
                venue=payload.get("venue"),
                session_bucket=payload.get("session_bucket"),
                sequence_epoch=payload.get("sequence_epoch"),
                capture_started_at=payload.get("capture_started_at"),
                segment_event_detected_at_ms=payload.get(
                    "segment_event_detected_at_ms"
                ),
                capture_ended_at=payload.get("capture_ended_at"),
                schema=payload.get("schema"),
            )
            timestamp = datetime.fromtimestamp(
                reference.event_detected_at_ms / 1000.0, tz=timezone.utc
            )
        except (OSError, OverflowError, TypeError, ValueError):
            return False, None
        valid = timestamp.astimezone(KST).date().isoformat() == target_date
        return valid, timestamp
    return False, None

def _closed_ingress_receipt_loss(
    guard: dict[str, Any], collector: dict[str, Any]
) -> bool:
    """Recognize irreversible source loss, never permission to consume bad input."""
    timestamp = guard.get("timestamp_source_quality") or {}
    if not isinstance(timestamp, dict):
        return False
    counts = timestamp.get("counts") or {}
    if not isinstance(counts, dict):
        return False
    fields = (
        "invalid_depth_timestamp_count",
        "invalid_exchange_timestamp_count",
        "stale_exchange_timestamp_block_count",
    )
    if any(type(counts.get(key)) is not int or counts[key] < 0 for key in fields):
        return False
    issues = [
        f"timestamp_source_rejected_before_enqueue:{key}={counts[key]}"
        for key in fields
        if counts[key] > 0
    ]
    declared_exclusions = guard.get("source_quality_row_exclusions")
    declared_issues = timestamp.get("issues")
    if any(
        not isinstance(values, list)
        or any(not isinstance(value, str) for value in values)
        for values in (declared_exclusions, declared_issues)
    ):
        return False
    return bool(
        issues
        and guard.get("status") == "stopped_clean"
        and guard.get("stop_required") is False
        and guard.get("stop_reasons") == []
        and guard.get("raw_row_exclusion_required") is True
        and sorted(declared_exclusions) == sorted(issues)
        and sorted(declared_issues) == sorted(issues)
        and timestamp.get("exact_rejected_row_exclusion_proven") is False
        and timestamp.get("rejection_stage") == "before_observer_enqueue"
        and collector.get("collector_lifecycle") == "closed"
        and source_close_verified(collector)
        and all(
            type(collector.get(key)) is int and collector[key] == 0
            for key in source_loss_counters(collector)
        )
        and all(collector.get(key) is False for key in CANARY_FORBIDDEN_TRUE_FIELDS)
        and collector.get("broker_order_forbidden") is True
    )

def _micro_context(
    target_date: str,
    observation_root: Path,
    symbols: set[str],
    anchors: list[dict[str, Any]],
    source_exclusion_manifest_path: Path,
    canary_snapshot_path: Path | None,
    canary_evaluated_at: datetime,
) -> tuple[dict[str, Any], dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    partition = observation_root / f"trade_date={target_date}"
    stream_paths, stream_path_errors = _partition_stream_files(
        partition, "market_stream.jsonl"
    )
    depth_paths, depth_path_errors = _partition_stream_files(
        partition, "market_depth_stream.jsonl"
    )
    ref_paths, ref_path_errors = _partition_stream_files(
        partition, "market_stream_event_references.jsonl"
    )
    read_diagnostics: dict[str, int] = {
        "malformed_relevant_json_line_count": 0,
        "source_file_read_error_count": 0,
        "partition_scope_mismatch_row_count": 0,
    }
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

    canary_payload = None
    canary_status = "not_requested"
    allowed_canary_epoch: int | None = None
    unverified_epoch_row_counts: Counter[str] = Counter()
    canary_source: dict[str, Any] = {
        "path": str(canary_snapshot_path) if canary_snapshot_path else None,
        "status": canary_status,
    }
    if canary_snapshot_path is not None:
        canary_payload = _read_json(canary_snapshot_path)
        raw_guard = (canary_payload or {}).get("canary_guard")
        raw_collector = (canary_payload or {}).get("collector_snapshot")
        raw_archive_validation = (canary_payload or {}).get("archive_validation")
        guard = raw_guard if isinstance(raw_guard, dict) else {}
        collector = raw_collector if isinstance(raw_collector, dict) else {}
        archive_validation = (
            raw_archive_validation if isinstance(raw_archive_validation, dict) else {}
        )
        generated_at = _parse_owner_ts((canary_payload or {}).get("generated_at"))
        canary_target_date_matches = bool(
            generated_at is not None
            and generated_at.astimezone(KST).date().isoformat() == target_date
        )
        canary_target_day_complete = bool(
            canary_target_date_matches
            and generated_at is not None
            and generated_at.astimezone(KST).time().replace(tzinfo=None)
            >= CANARY_COMPLETE_AFTER_KST
        )
        valid_until_epoch = _finite_float(
            (canary_payload or {}).get("valid_until_epoch")
        )
        archived_at = _parse_owner_ts(
            archive_validation.get("archived_at_kst")
            if isinstance(archive_validation, dict)
            else None
        )
        archived_freshness_valid = bool(
            isinstance(archive_validation, dict)
            and archive_validation.get("schema")
            == "scalp_micro_reversion_canary_archive_validation_v1"
            and archive_validation.get("target_date") == target_date
            and archive_validation.get("target_day_complete") is True
            and archive_validation.get("source_fresh_at_archive") is True
            and archive_validation.get("source_generated_not_after_archive") is True
            and archived_at is not None
            and generated_at is not None
            and generated_at <= archived_at
        )
        generation_causal = bool(
            archived_freshness_valid
            or (generated_at is not None and generated_at <= canary_evaluated_at)
        )
        stopped_clean_closed = bool(
            guard.get("status") == "stopped_clean"
            and isinstance(collector, dict)
            and collector.get("collector_lifecycle") == "closed"
            and source_close_verified(collector)
        )
        row_quarantine_validation = _timestamp_regression_row_quarantine_validation(
            guard, collector
        )
        if row_quarantine_validation.get("eligible") is not True:
            epoch_validation = closed_pre_enqueue_epoch_quarantine_validation(
                guard, collector
            )
            if epoch_validation.get("eligible") is True:
                row_quarantine_validation = epoch_validation
                allowed_canary_epoch = epoch_validation["allowed_sequence_epoch"]
        isolated_row_quarantine = bool(
            row_quarantine_validation.get("eligible") is True
        )
        live_freshness_valid = bool(
            stopped_clean_closed
            or (
                guard.get("status") == "healthy_observer_canary"
                and valid_until_epoch is not None
                and valid_until_epoch >= canary_evaluated_at.timestamp()
            )
        )
        canary_freshness_valid = archived_freshness_valid or live_freshness_valid
        canary_contract_valid = bool(
            (canary_payload or {}).get("schema")
            == "scalp_micro_reversion_canary_monitor_v1"
            and canary_target_date_matches
            and generation_causal
            and isinstance(guard, dict)
            and guard.get("status") in {"healthy_observer_canary", "stopped_clean"}
            and (
                (
                    guard.get("status") == "healthy_observer_canary"
                    and collector.get("collector_lifecycle") == "running"
                )
                or stopped_clean_closed
            )
            and guard.get("stop_required") is False
            and (
                guard.get("raw_row_exclusion_required") is False
                or isolated_row_quarantine
            )
            and isinstance(collector, dict)
            and collector.get("selection_authority") is False
            and collector.get("trading_runtime_effect") is False
            and collector.get("actual_order_submitted") is False
            and collector.get("broker_order_forbidden") is True
        )
        canary_valid = bool(
            canary_contract_valid
            and canary_target_day_complete
            and canary_freshness_valid
        )
        canary_status = (
            (
                "loaded_pass_with_row_quarantine"
                if isolated_row_quarantine
                else "loaded_pass"
            )
            if canary_valid
            else (
                "target_date_evidence_unavailable"
                if canary_payload is None or not canary_target_date_matches
                else (
                    "target_date_evidence_incomplete"
                    if not canary_target_day_complete
                    else (
                        "missing_or_invalid"
                        if not canary_contract_valid
                        else (
                            "target_date_evidence_stale"
                            if not canary_freshness_valid
                            else "missing_or_invalid"
                        )
                    )
                )
            )
        )
        canary_source = {
            "path": str(canary_snapshot_path),
            "status": canary_status,
            "generated_at": (
                generated_at.isoformat() if generated_at is not None else None
            ),
            "target_day_complete": canary_target_day_complete,
            "complete_after_kst": CANARY_COMPLETE_AFTER_KST.isoformat(),
            "fresh_at_evaluation_or_archive": canary_freshness_valid,
            "generated_not_after_evaluation_or_archive": generation_causal,
            "valid_until_epoch": valid_until_epoch,
            "archive_validation": (
                archive_validation if isinstance(archive_validation, dict) else None
            ),
            "stopped_clean_closed": stopped_clean_closed,
            "guard_status": guard.get("status") if isinstance(guard, dict) else None,
            "stop_required": (
                guard.get("stop_required") if isinstance(guard, dict) else None
            ),
            "raw_row_exclusion_required": (
                guard.get("raw_row_exclusion_required")
                if isinstance(guard, dict)
                else None
            ),
            "row_quarantine_validation": row_quarantine_validation,
            "allowed_sequence_epoch": allowed_canary_epoch,
            "whole_date_approval": False if allowed_canary_epoch is not None else None,
            "immutable_ingress_receipt_loss": bool(
                (canary_payload or {}).get("schema")
                == "scalp_micro_reversion_canary_monitor_v1"
                and canary_target_day_complete
                and generation_causal
                and canary_freshness_valid
                and _closed_ingress_receipt_loss(guard, collector)
            ),
            "sequence_epoch": (
                collector.get("sequence_epoch") if isinstance(collector, dict) else None
            ),
            "source_sha256": (
                hashlib.sha256(canary_snapshot_path.read_bytes()).hexdigest()
                if canary_payload is not None
                else None
            ),
        }

    # Main raw rows need their own closed epoch evidence. A legacy or latest
    # receipt cannot retroactively approve unrelated collector generations.
    allowed_main_epochs=set()
    if canary_payload and (canary_payload.get('collector_snapshot') or {}).get('source_contract')==MAIN_SOURCE_CONTRACT:
        main_validation=main_raw_epoch_validation(canary_payload,source_date=target_date)
        allowed_main_epochs.update(main_validation.get('allowed_sequence_epochs',[]))
        from src.engine.scalping.continuous_reversal_source import _source_quality_receipt
        quality=_source_quality_receipt(observation_root.parents[1],target_date)
        allowed_main_epochs.update(quality.get('allowed_sequence_epochs',[]))
        allowed_main_epochs.difference_update(quality.get('denied_sequence_epochs',[]))
        canary_source['main_raw_source_quality_receipt']=quality
        canary_source['main_raw_epoch_validation']=main_validation
        canary_valid=canary_valid and bool(allowed_main_epochs)
        if not allowed_main_epochs:canary_source['status']='main_raw_closed_epoch_unverified'

    def is_excluded(payload: dict[str, Any]) -> bool:
        contract=payload.get('source_contract')
        if contract is not None and contract != MAIN_SOURCE_CONTRACT:
            unverified_epoch_row_counts['unsupported_source_contract'] += 1
            return True
        if payload.get('source_contract')==MAIN_SOURCE_CONTRACT and (type(payload.get('sequence_epoch')) is not int or payload['sequence_epoch'] not in allowed_main_epochs):
            unverified_epoch_row_counts[str(payload.get('sequence_epoch'))] += 1
            return True
        if allowed_canary_epoch is not None:
            epoch = payload.get("sequence_epoch")
            if type(epoch) is not int or epoch != allowed_canary_epoch:
                unverified_epoch_row_counts[str(epoch)] += 1
                return True
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
            "invalid_contract_scope_counts": defaultdict(int),
            "depth_row_count": 0,
            "venues": set(),
            "sessions": set(),
            "decision_market_scopes": set(),
            "market_data_routes": set(),
            "market_session_regimes": set(),
            "actual_execution_venue_counts": defaultdict(int),
            "dual_actual_execution_venue_counts": defaultdict(int),
            "dual_source_only_row_count": 0,
        }
        for symbol in symbols
    }
    windows: dict[str, dict[str, Any]] = {
        anchor["anchor_id"]: {
            "rows": [],
            "raw_market_rows": [],
            "depth_rows": 0,
            "depth_points": [],
            "raw_depth_rows": [],
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

    def post_window_sec(anchor: Mapping[str, Any]) -> int:
        if anchor.get("native_operating_parent") is True:
            start = _parse_ts(anchor.get("anchor_at"))
            end = _parse_ts(
                (anchor.get("native_operating_state") or {}).get("observed_at")
            )
            if start and end:
                return max(5, min(8 * 3600, int((end - start).total_seconds())))
        if anchor.get("bounded_entry_opportunity_replay") is True:
            return 180
        if anchor.get("adaptive_exit_source_only") is True:
            return ADAPTIVE_EXIT_HORIZON_SEC
        rebound_frame = anchor.get("rebound_source_frame")
        if isinstance(rebound_frame, Mapping):
            observation_end = _parse_ts(rebound_frame.get("parent_horizon_end"))
            observation_start = _parse_ts(anchor.get("anchor_at"))
            if observation_end is not None and observation_start is not None:
                return max(
                    0,
                    min(
                        8 * 3600,
                        int((observation_end - observation_start).total_seconds()),
                    ),
                )
        return (
            MARKET_WEAKNESS_COUNTERFACTUAL_POST_WINDOW_SEC
            if anchor.get("anchor_role") in _ENTRY_CONFIRMATION_ANCHOR_ROLES
            or anchor.get("anchor_role") == "source_only_rebound_owner_decision"
            else POST_WINDOW_SEC
        )

    adaptive_source_rows = {"market": 0, "depth": 0}
    for payload in _iter_relevant_rows(
        stream_paths, symbols, diagnostics=read_diagnostics
    ):
        symbol = str(payload.get("symbol"))
        item = inventory[symbol]
        item["observed_row_count"] += 1
        if not _physical_scope_matches_row(payload):
            item["venues"].add(str(payload.get("_partition_venue") or "unknown"))
            item["sessions"].add(
                str(payload.get("_partition_session_bucket") or "unknown")
            )
            item["invalid_contract_row_count"] += 1
            item["invalid_contract_scope_counts"][
                _physical_scope_contract_key(payload)
            ] += 1
            item["ineligible_row_count"] += 1
            read_diagnostics["partition_scope_mismatch_row_count"] += 1
            continue
        item["venues"].add(str(payload.get("venue") or "unknown"))
        item["sessions"].add(str(payload.get("session_bucket") or "unknown"))
        market_axes = _market_axis_context(payload)
        item["decision_market_scopes"].add(market_axes["decision_market_scope"])
        item["market_data_routes"].add(market_axes["market_data_route"])
        item["market_session_regimes"].add(market_axes["market_session_regime"])
        item["actual_execution_venue_counts"][
            market_axes["actual_execution_venue"]
        ] += 1
        item["dual_source_only_row_count"] += int(market_axes["dual_source_only"])
        if market_axes["dual_source_only"]:
            item["dual_actual_execution_venue_counts"][
                market_axes["actual_execution_venue"]
            ] += 1
        if is_excluded(payload):
            item["source_excluded_row_count"] += 1
            item["ineligible_row_count"] += 1
            continue
        (
            contract_valid,
            path_consumer_eligible,
            timestamp,
            price,
            best_bid,
            best_ask,
        ) = _validate_stream_row(payload)
        if (
            contract_valid
            and timestamp is not None
            and timestamp.astimezone(KST).date().isoformat() != target_date
        ):
            contract_valid = False
            path_consumer_eligible = False
        eligible = contract_valid and path_consumer_eligible
        if not contract_valid:
            item["invalid_contract_row_count"] += 1
            item["invalid_contract_scope_counts"][_scope_contract_key(payload)] += 1
        item["eligible_row_count" if eligible else "ineligible_row_count"] += 1
        if not eligible:
            continue
        normalized_market_row = {
            "timestamp": timestamp,
            "price": price,
            "best_bid": best_bid,
            "best_ask": best_ask,
            "venue": payload.get("venue"),
            "session": payload.get("session_bucket"),
            "sequence_epoch": payload.get("sequence_epoch"),
            **market_axes,
        }
        for anchor, anchor_at in anchors_by_symbol.get(symbol, []):
            if payload.get("venue") not in anchor["expected_venues"]:
                continue
            if payload.get("session_bucket") not in anchor.get(
                "expected_session_buckets", ()
            ):
                continue
            if (
                anchor_at - timedelta(seconds=PRE_WINDOW_SEC)
                <= timestamp
                <= anchor_at + timedelta(seconds=post_window_sec(anchor))
            ):
                if (
                    anchor.get("adaptive_exit_source_only") is True
                    or anchor.get("bounded_entry_opportunity_replay") is True
                ):
                    window = windows[anchor["anchor_id"]]
                    if (
                        len(window["raw_market_rows"]) >= ADAPTIVE_EXIT_MAX_SOURCE_ROWS
                        or adaptive_source_rows["market"]
                        >= ADAPTIVE_EXIT_MAX_TOTAL_SOURCE_ROWS // 2
                    ):
                        window["adaptive_exit_source_overflow"] = True
                    else:
                        window["raw_market_rows"].append(payload)
                        adaptive_source_rows["market"] += 1
                    continue
                window = windows[anchor["anchor_id"]]
                if anchor.get("native_operating_parent") and (
                    len(window["raw_market_rows"]) >= ADAPTIVE_EXIT_MAX_SOURCE_ROWS
                    or adaptive_source_rows["market"]
                    >= ADAPTIVE_EXIT_MAX_TOTAL_SOURCE_ROWS // 2
                ):
                    window["adaptive_exit_source_overflow"] = True
                    continue
                if anchor.get("native_operating_parent"):
                    adaptive_source_rows["market"] += 1
                windows[anchor["anchor_id"]]["rows"].append(normalized_market_row)
                # A source row can fall inside many overlapping owner windows.
                # The iterator yields a fresh immutable-by-contract mapping for
                # each line, so retain one shared reference instead of copying
                # the full raw row once per anchor.  Consumers copy before any
                # normalization, preserving report values while bounding the
                # in-memory working set.
                windows[anchor["anchor_id"]]["raw_market_rows"].append(payload)

    for payload in _iter_relevant_rows(
        depth_paths, symbols, diagnostics=read_diagnostics
    ):
        symbol = str(payload.get("symbol"))
        if not _physical_scope_matches_row(payload):
            inventory[symbol]["invalid_contract_row_count"] += 1
            inventory[symbol]["invalid_contract_scope_counts"][
                _physical_scope_contract_key(payload)
            ] += 1
            read_diagnostics["partition_scope_mismatch_row_count"] += 1
            continue
        if is_excluded(payload):
            inventory[symbol]["source_excluded_row_count"] += 1
            continue
        (
            valid_depth,
            timestamp,
            bid_depth,
            ask_depth,
            depth_best_bid,
            depth_best_ask,
        ) = _validate_depth_row(payload)
        if (
            valid_depth
            and timestamp is not None
            and timestamp.astimezone(KST).date().isoformat() != target_date
        ):
            valid_depth = False
        if not valid_depth:
            inventory[symbol]["invalid_contract_row_count"] += 1
            inventory[symbol]["invalid_contract_scope_counts"][
                _scope_contract_key(payload)
            ] += 1
            continue
        inventory[symbol]["depth_row_count"] += 1
        normalized_depth_point = {
            "venue": payload.get("venue"),
            "sequence_epoch": int(payload["sequence_epoch"]),
            "timestamp": timestamp,
            "best_bid": depth_best_bid,
            "best_bid_qty": int(payload["best_bid_qty"]),
            "best_ask": depth_best_ask,
            "best_ask_qty": int(payload["best_ask_qty"]),
            "bid_depth": bid_depth,
            "ask_depth": ask_depth,
        }
        for anchor, anchor_at in anchors_by_symbol.get(symbol, []):
            if payload.get("venue") not in anchor["expected_venues"]:
                continue
            if payload.get("session_bucket") not in anchor.get(
                "expected_session_buckets", ()
            ):
                continue
            if (
                anchor_at - timedelta(seconds=PRE_WINDOW_SEC)
                <= timestamp
                <= anchor_at + timedelta(seconds=post_window_sec(anchor))
            ):
                if (
                    anchor.get("adaptive_exit_source_only") is True
                    or anchor.get("bounded_entry_opportunity_replay") is True
                ):
                    window = windows[anchor["anchor_id"]]
                    if (
                        len(window["raw_depth_rows"]) >= ADAPTIVE_EXIT_MAX_SOURCE_ROWS
                        or adaptive_source_rows["depth"]
                        >= ADAPTIVE_EXIT_MAX_TOTAL_SOURCE_ROWS // 2
                    ):
                        window["adaptive_exit_source_overflow"] = True
                    else:
                        window["raw_depth_rows"].append(payload)
                        adaptive_source_rows["depth"] += 1
                    continue
                window = windows[anchor["anchor_id"]]
                if anchor.get("native_operating_parent") and (
                    len(window["raw_depth_rows"]) >= ADAPTIVE_EXIT_MAX_SOURCE_ROWS
                    or adaptive_source_rows["depth"]
                    >= ADAPTIVE_EXIT_MAX_TOTAL_SOURCE_ROWS // 2
                ):
                    window["adaptive_exit_source_overflow"] = True
                    continue
                windows[anchor["anchor_id"]]["depth_rows"] += 1
                windows[anchor["anchor_id"]]["depth_points"].append(
                    normalized_depth_point
                )
                window = windows[anchor["anchor_id"]]
                if anchor.get("native_operating_parent") and (
                    len(window["raw_depth_rows"]) >= ADAPTIVE_EXIT_MAX_SOURCE_ROWS
                    or adaptive_source_rows["depth"]
                    >= ADAPTIVE_EXIT_MAX_TOTAL_SOURCE_ROWS // 2
                ):
                    window["adaptive_exit_source_overflow"] = True
                else:
                    window["raw_depth_rows"].append(payload)
                    if anchor.get("native_operating_parent"):
                        adaptive_source_rows["depth"] += 1

    for payload in _iter_relevant_rows(
        (() if (canary_payload or {}).get("collector_snapshot", {}).get("source_contract") == MAIN_SOURCE_CONTRACT else ref_paths), symbols, diagnostics=read_diagnostics
    ):
        symbol = str(payload.get("symbol"))
        if not _physical_scope_matches_row(payload):
            inventory[symbol]["invalid_contract_row_count"] += 1
            inventory[symbol]["invalid_contract_scope_counts"][
                _physical_scope_contract_key(payload)
            ] += 1
            read_diagnostics["partition_scope_mismatch_row_count"] += 1
            continue
        if is_excluded(payload):
            inventory[symbol]["source_excluded_row_count"] += 1
            continue
        valid_reference, timestamp = _validate_reference_row(payload, target_date)
        if not valid_reference or timestamp is None:
            inventory[symbol]["invalid_contract_row_count"] += 1
            inventory[symbol]["invalid_contract_scope_counts"][
                _scope_contract_key(payload)
            ] += 1
            continue
        for anchor, anchor_at in anchors_by_symbol.get(symbol, []):
            if payload.get("venue") not in anchor["expected_venues"]:
                continue
            if payload.get("session_bucket") not in anchor.get(
                "expected_session_buckets", ()
            ):
                continue
            if (
                anchor_at - timedelta(seconds=PRE_WINDOW_SEC)
                <= timestamp
                <= anchor_at + timedelta(seconds=post_window_sec(anchor))
            ):
                windows[anchor["anchor_id"]]["shock_reference_count"] += 1

    for item in inventory.values():
        item["venues"] = sorted(item["venues"])
        item["sessions"] = sorted(item["sessions"])
        item["decision_market_scopes"] = sorted(item["decision_market_scopes"])
        item["market_data_routes"] = sorted(item["market_data_routes"])
        item["market_session_regimes"] = sorted(item["market_session_regimes"])
        item["actual_execution_venue_counts"] = dict(
            sorted(item["actual_execution_venue_counts"].items())
        )
        item["dual_actual_execution_venue_counts"] = dict(
            sorted(item["dual_actual_execution_venue_counts"].items())
        )
        item["invalid_contract_scope_counts"] = dict(
            sorted(item["invalid_contract_scope_counts"].items())
        )

    shard_discovery_error_count = (
        len(stream_path_errors) + len(depth_path_errors) + len(ref_path_errors)
    )
    source_contract_ready = bool(
        exclusion_manifest_status == "loaded"
        and canary_status
        in {
            "not_requested",
            "loaded_pass",
            "loaded_pass_with_row_quarantine",
        }
        and shard_discovery_error_count == 0
        and read_diagnostics["malformed_relevant_json_line_count"] == 0
        and read_diagnostics["source_file_read_error_count"] == 0
    )
    return (
        {
            "partition": str(partition),
            "partition_status": "loaded" if stream_paths else "missing",
            "market_stream_file_count": len(stream_paths),
            "market_depth_file_count": len(depth_paths),
            "event_reference_file_count": len(ref_paths),
            "stream_shard_discovery_errors": stream_path_errors,
            "depth_shard_discovery_errors": depth_path_errors,
            "event_reference_shard_discovery_errors": ref_path_errors,
            "shard_discovery_error_count": shard_discovery_error_count,
            **read_diagnostics,
            "source_exclusion_manifest_path": str(source_exclusion_manifest_path),
            "source_exclusion_manifest_status": exclusion_manifest_status,
            "source_exclusion_scope_count": len(excluded_scopes),
            "unverified_canary_epoch_row_counts": dict(unverified_epoch_row_counts),
            "unverified_canary_epoch_row_count": sum(
                unverified_epoch_row_counts.values()
            ),
            "canary_source_quality": canary_source,
            "source_contract_ready": source_contract_ready,
            "dual_source_only_row_count": sum(
                item["dual_source_only_row_count"] for item in inventory.values()
            ),
            "dual_actual_execution_venue_unknown_row_count": sum(
                item["dual_actual_execution_venue_counts"].get("UNKNOWN", 0)
                for item in inventory.values()
            ),
            "dual_auto_promotion_candidate_count": 0,
        },
        inventory,
        windows,
    )

def _invalid_contract_count_for_scope(
    inventory: dict[str, Any],
    *,
    expected_venues: Iterable[str],
    expected_sessions: Iterable[str],
) -> int:
    counts = inventory.get("invalid_contract_scope_counts") or {}
    venues = set(expected_venues)
    sessions = set(expected_sessions)
    total = 0
    for key, raw_count in counts.items():
        venue, _, session = str(key).partition("|")
        if (
            venue == "unknown"
            or session == "unknown"
            or (venue in venues and session in sessions)
        ):
            total += int(raw_count or 0)
    return total

_ENTRY_CONFIRMATION_ANCHOR_ROLES = frozenset(
    {
        "actual_market_weakness_blocked_entry_signal",
        "counterfactual_calibration_entry",
        "episode_signal_decision_leg",
        "episode_signal_bar",
        "prospective_episode_research_signal",
    }
)

def _entry_checkpoint_ask_depletion_feature(
    anchor: dict[str, Any],
    window: dict[str, Any],
    *,
    source_complete: bool,
    checkpoint_sec: int,
) -> dict[str, Any] | None:
    """Use the same fixed-price one-second kernel as the live route adapter."""
    if anchor.get("anchor_role") not in _ENTRY_CONFIRMATION_ANCHOR_ROLES:
        return None
    anchor_at = _parse_ts(anchor.get("anchor_at"))
    if anchor_at is None:
        return {
            "source_quality_status": "source_gap",
            "source_gap_reasons": ["decision_anchor_timestamp_invalid"],
        }
    checkpoint_at = anchor_at + timedelta(seconds=checkpoint_sec)
    window_start = checkpoint_at - timedelta(seconds=1)

    def scoped_rows(key: str) -> list[dict[str, Any]]:
        return [
            row
            for row in window.get(key) or ()
            if isinstance(row, dict)
            and (
                _parse_owner_ts(row.get("local_receive_timestamp")) is None
                or _parse_owner_ts(row.get("local_receive_timestamp")) <= checkpoint_at
            )
            and str(row.get("symbol") or "") == str(anchor.get("symbol") or "")
            and row.get("venue") in (anchor.get("expected_venues") or ())
            and row.get("session_bucket")
            in (anchor.get("expected_session_buckets") or ())
        ]

    depths = scoped_rows("raw_depth_rows")
    trades = scoped_rows("raw_market_rows")
    expected_items = {
        _registration_item_for_exact_route(anchor.get("symbol"), venue)
        for venue in anchor.get("expected_venues") or ()
    } - {""}
    exact_item = next(iter(expected_items)) if len(expected_items) == 1 else None
    # Bind to the latest causal depth route, never to a future/other-route tick.
    endpoint = max(
        [
            row
            for row in depths
            if _parse_owner_ts(row.get("local_receive_timestamp")) is not None
            and row.get("item") == exact_item
        ],
        key=lambda r: _parse_owner_ts(r["local_receive_timestamp"]),
        default={},
    )
    item, epoch = exact_item, endpoint.get("sequence_epoch")
    feature = build_confirmation_window(
        depth_rows=depths,
        trade_rows=trades,
        item=item,
        epoch=epoch,
        checkpoint_at_ms=int(checkpoint_at.timestamp() * 1_000),
        source_complete=source_complete,
    )
    return {
        "schema": "scalp_micro_reversion_ask_depletion_v2",
        "feature_version": FEATURE_VERSION,
        "runtime_effect": False,
        "trading_runtime_effect": False,
        "trading_decision_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "source_quality_status": feature["source_quality_status"],
        "source_gap_reasons": feature["source_gap_reasons"],
        "context": {
            "symbol": anchor.get("symbol"),
            "venue": endpoint.get("venue"),
            "session_bucket": endpoint.get("session_bucket"),
            "sequence_epoch": epoch,
            "item": item,
            "anchor_event_local_receive_timestamp_ms": int(
                window_start.timestamp() * 1_000
            ),
            "observed_through_local_receive_timestamp_ms": int(
                checkpoint_at.timestamp() * 1_000
            ),
        },
        "horizons": [feature],
        "decision_anchor_binding": {
            "decision_anchor_id": anchor["anchor_id"],
            "decision_anchor_at": anchor_at.isoformat(),
            "checkpoint_sec": checkpoint_sec,
            "checkpoint_at": checkpoint_at.isoformat(),
            "window_started_at": window_start.isoformat(),
            "window_horizon_ms": 1_000,
            "binding_policy": "past_only_0b_0d_window_ending_at_exact_checkpoint",
            "future_outcome_input_used": False,
        },
    }

def _registration_item_for_exact_route(symbol: Any, venue: Any) -> str:
    normalized_symbol = str(symbol or "").strip().upper()
    normalized_venue = str(venue or "").strip().upper()
    if len(normalized_symbol) != 6 or not normalized_symbol.isdigit():
        return ""
    if normalized_venue == "KRX":
        return normalized_symbol
    if normalized_venue == "NXT":
        return f"{normalized_symbol}_NX"
    if normalized_venue == "SOR":
        return f"{normalized_symbol}_AL"
    return ""

def _collect_generation_source_paths(value: Any) -> set[Path]:
    """Return only producer-declared source paths from an attribution report."""

    paths: set[Path] = set()
    if isinstance(value, Mapping):
        for key, item in value.items():
            if key in {
                "path",
                "partition",
                "source_exclusion_manifest_path",
            } and isinstance(item, str):
                paths.add(Path(item))
            elif (
                key == "paths"
                and isinstance(item, Sequence)
                and not isinstance(item, (str, bytes))
            ):
                paths.update(Path(path) for path in item if isinstance(path, str))
            else:
                paths.update(_collect_generation_source_paths(item))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            paths.update(_collect_generation_source_paths(item))
    return paths

def _path_generation_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return [{"path": str(path), "state": "missing"}]
    if path.is_file():
        stat = path.stat()
        return [
            {
                "path": str(path),
                "state": "file",
                "size": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
            }
        ]
    rows: list[dict[str, Any]] = []
    for child in sorted(
        candidate for candidate in path.rglob("*") if candidate.is_file()
    ):
        stat = child.stat()
        rows.append(
            {
                "path": str(child),
                "state": "file",
                "size": stat.st_size,
                "mtime_ns": stat.st_mtime_ns,
            }
        )
    if not rows:
        rows.append({"path": str(path), "state": "empty_directory"})
    return rows

def _source_generation_contract(
    sources: Mapping[str, Any], *, extra_paths: Iterable[Path] = ()
) -> dict[str, Any]:
    paths = _collect_generation_source_paths(sources)
    paths.update(extra_paths)
    rows = [
        row
        for path in sorted(paths, key=lambda value: str(value))
        for row in _path_generation_rows(path)
    ]
    encoded = json.dumps(rows, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    producer_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return {
        "schema": "machine_microstructure_source_generation_v1",
        "source_date": None,
        "fingerprint_basis": "declared_source_path_size_mtime_ns",
        "source_roots": [
            str(path) for path in sorted(paths, key=lambda value: str(value))
        ],
        "source_rows": rows,
        "source_fingerprint": hashlib.sha256(encoded.encode()).hexdigest(),
        "producer_sha256": producer_sha256,
    }

# Shared source-window bounds; retained unchanged from their original contract.
ADAPTIVE_EXIT_HORIZON_SEC = 1200
ADAPTIVE_EXIT_MAX_SOURCE_ROWS = 30000
ADAPTIVE_EXIT_MAX_TOTAL_SOURCE_ROWS = 120000

def _previous_krx_trading_date(value: date) -> date:
    candidate = value - timedelta(days=1)
    for _ in range(14):
        if is_krx_trading_day(candidate):
            return candidate
        candidate -= timedelta(days=1)
    raise ValueError("previous_krx_trading_date_unresolved")

def resolve_completed_machine_target_date(*, now: datetime | None = None) -> date:
    current = (now or datetime.now(KST)).astimezone(KST)
    if (
        is_krx_trading_day(current.date())
        and current.time().replace(tzinfo=None) >= POSTCLOSE_COMPLETE_TIME
    ):
        return current.date()
    return _previous_krx_trading_date(current.date())
