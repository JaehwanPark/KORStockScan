"""Causal, source-only replay for scanner entry turn timing.

The replay consumes BBO observations that were already emitted by the main
pipeline.  It does not subscribe to market data, call the broker, or alter an
entry decision.  Every trigger uses only observations at or before the trigger
timestamp; outcomes use later executable bids and the effective-dated R0-R3
comparison-cost contract.
"""

from __future__ import annotations

import ast
import json
import math
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from src.engine.monitoring.widget_comparison_cost import comparison_cost_contract
from src.engine.scalping.micro_reversion.symbol_master import VerifiedSymbolMaster
from src.utils.jsonl_io import read_json_object_strict_receipt

KST = timezone(timedelta(hours=9))
PROJECT_ROOT = Path(__file__).resolve().parents[3]
SYMBOL_MASTER_DIR = (
    PROJECT_ROOT / "data" / "report" / "micro_reversion_economic_reference"
)

MAX_QUOTE_AGE_MS = 1_000.0
PRE_ANCHOR_LOOKBACK_SEC = 120.0
MOMENTUM_WINDOW_SEC = 30.0
REBOUND_WINDOW_SEC = 120.0
MAX_INTERNAL_GAP_SEC = 15.0
OUTCOME_HORIZON_SEC = 20 * 60
TIMEOUT_MAX_LAG_SEC = 5.0
MAX_ENTRY_SPREAD_BPS = 50.0
MOMENTUM_MIN_EXECUTABLE_MOVE_PCT = 0.10
REBOUND_MIN_PRIOR_DRAWDOWN_PCT = 0.30
REBOUND_MIN_RECOVERY_PCT = 0.15
TARGET_PCTS = (0.30, 0.40, 0.50, 0.70, 1.30)
ADVERSE_PCTS = (-0.30, -0.50, -0.70)
PRIMARY_TARGET_PCT = 0.50
PRIMARY_ADVERSE_PCT = -0.50
EXACT_BBO_JOIN_FLOOR_PCT = 95.0
PRE_ANCHOR_BBO_COVERAGE_FLOOR_PCT = 95.0
PAIRED_COVERAGE_FLOOR_PCT = 95.0
RIGHT_CENSORED_MAX_PCT = 20.0
MIN_RESOLVED_SAMPLE_COUNT = 20
PRE_ANCHOR_BUNDLE_SCHEMA_VERSION = "entry_turn_pre_anchor_bbo_bundle_v2_json"

FORBIDDEN_USES = [
    "standalone_buy_or_drop",
    "broker_order_submission_or_cancel",
    "runtime_threshold_mutation",
    "scanner_slot_or_cooldown_mutation",
    "order_price_or_quantity_change",
    "provider_route_or_bot_state_change",
    "stale_quote_or_broker_guard_bypass",
    "hard_protect_or_emergency_safety_bypass",
    "daily_only_live_or_sim_auto_promotion",
    "mark_price_fill_or_exit_substitution",
    "cross_venue_or_cross_session_join",
    "unverified_symbol_or_cost_economics",
]

METRIC_CONTRACT = {
    "metric_role": "source_only_entry_turn_point_causal_replay",
    "decision_authority": "entry_turn_point_replay_observation_only",
    "window_policy": (
        "one_unit_per_scanner_promotion_symbol_venue_session_with_past_only_120s_turn_"
        "context_and_20m_forward_executable_bid_outcome"
    ),
    "sample_floor": (
        "verified_official_common_stock_master_with_source_hash_and_"
        "effective_cost_contract_and_"
        "exact_bbo_join_pct>=95_and_pre_anchor_bbo_coverage_pct>=95_and_"
        "paired_coverage_pct>=95_and_"
        "right_censored_pct<=20_and_20_resolved_primary_outcomes"
    ),
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": (
        "fresh_existing_ws_bbo_with_nonzero_integer_displayed_best_quantities_"
        "and_explicit_symbol_venue_session_local_time_and_no_pre_anchor_imputation"
    ),
    "forbidden_uses": FORBIDDEN_USES,
    "runtime_effect": False,
    "allowed_runtime_apply": False,
    "actual_order_submitted": False,
    "broker_order_forbidden": True,
}

MILESTONE_STAGES = frozenset(
    {
        "scalping_scanner_candidate_promoted",
        "scalping_scanner_runtime_target_attach",
        "scalping_scanner_fast_precheck",
        "scalping_scanner_heavy_eval_completion",
        "rising_missed_tp1_candidate_blocked",
        "rising_missed_tp1_candidate_deferred",
        "ai_confirmed",
        "latency_pass",
        "latency_block",
        "budget_pass",
        "order_bundle_submitted",
        "order_bundle_failed",
    }
)


def _safe_float(value: Any) -> float | None:
    if value in (None, "", "-", "None", "null") or isinstance(value, bool):
        return None
    try:
        parsed = float(str(value).replace(",", "").replace("%", ""))
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _is_sha256(value: Any) -> bool:
    token = str(value or "").strip().lower()
    return len(token) == 64 and all(char in "0123456789abcdef" for char in token)


def _fields(row: Mapping[str, Any]) -> Mapping[str, Any]:
    value = row.get("fields")
    return value if isinstance(value, Mapping) else {}


def _event_time(row: Mapping[str, Any]) -> datetime | None:
    value = row.get("emitted_at") or row.get("timestamp") or row.get("ts")
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=KST)
    return parsed.astimezone(KST)


def _code(row: Mapping[str, Any]) -> str:
    fields = _fields(row)
    return str(row.get("stock_code") or fields.get("stock_code") or "").strip()[:6]


def _venue(fields: Mapping[str, Any]) -> str:
    supported = {"KRX", "NXT", "PREMARKET_KRX_LIKE"}
    resolution = str(fields.get("venue_resolution") or "").strip().lower()
    if "conflict" in resolution or "mismatch" in resolution:
        return "UNKNOWN"
    raw_explicit = {
        str(fields.get(key) or "").strip().upper()
        for key in ("rising_missed_effective_venue", "effective_venue", "venue")
        if str(fields.get(key) or "").strip().upper()
        not in {"", "-", "UNKNOWN", "NONE", "NULL"}
    }
    if any(value not in supported for value in raw_explicit):
        return "UNKNOWN"
    explicit = {value for value in raw_explicit if value in supported}
    return next(iter(explicit)) if len(explicit) == 1 else "UNKNOWN"


def _session(fields: Mapping[str, Any]) -> str:
    explicit = {
        str(fields.get(key) or "").strip().lower()
        for key in ("rising_missed_market_session_bucket", "market_session_bucket")
        if str(fields.get(key) or "").strip().lower()
        not in {"", "unknown", "none", "null", "-"}
    }
    return next(iter(explicit)) if len(explicit) == 1 else "UNKNOWN"


def _is_ws_provenance(value: Any) -> bool:
    token = str(value or "").strip().lower()
    return bool(token and "ws" in token and "rest" not in token)


def _boolish(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value or "").strip().lower() in {"1", "true", "yes", "y", "on"}


def _executable_ws_bbo(row: Mapping[str, Any]) -> tuple[dict[str, Any] | None, str]:
    """Extract one fresh existing-WS BBO; REST and mark prices are forbidden."""

    fields = _fields(row)
    event_time = _event_time(row)
    venue = _venue(fields)
    session = _session(fields)
    if event_time is None:
        return None, "event_time_missing"
    if venue == "UNKNOWN":
        return None, "explicit_venue_missing"
    if session == "UNKNOWN":
        return None, "explicit_session_missing"

    candidates = (
        (
            "market_data_effective_bbo",
            "market_data_effective_best_bid",
            "market_data_effective_best_ask",
            "market_data_effective_quote_age_ms",
            "market_data_effective_price_source",
            "market_data_effective_quote_observed_epoch",
            "market_data_effective_quote_reference_epoch",
            "market_data_effective_best_bid_qty",
            "market_data_effective_best_ask_qty",
            "market_data_effective_best_bid_qty_source_valid",
            "market_data_effective_best_ask_qty_source_valid",
            "market_data_freshness_state",
        ),
        (
            "nxt_post_block_ws_0d_bbo",
            "rising_missed_nxt_post_block_ws_0d_best_bid",
            "rising_missed_nxt_post_block_ws_0d_best_ask",
            "rising_missed_nxt_post_block_ws_0d_age_ms",
            "rising_missed_nxt_post_block_price_source",
            None,
            None,
            None,
            None,
            None,
            None,
            None,
        ),
    )
    gaps: list[str] = []
    for (
        source,
        bid_key,
        ask_key,
        age_key,
        provenance_key,
        epoch_key,
        reference_epoch_key,
        bid_qty_key,
        ask_qty_key,
        bid_qty_valid_key,
        ask_qty_valid_key,
        freshness_state_key,
    ) in candidates:
        bid = _safe_float(fields.get(bid_key))
        ask = _safe_float(fields.get(ask_key))
        if bid is None and ask is None:
            continue
        if bid is None or ask is None or bid <= 0 or ask < bid:
            gaps.append(f"{source}:invalid_or_crossed_bbo")
            continue
        age_ms = _safe_float(fields.get(age_key))
        if age_ms is None or age_ms < 0:
            gaps.append(f"{source}:quote_age_missing")
            continue
        if age_ms > MAX_QUOTE_AGE_MS:
            gaps.append(f"{source}:quote_stale")
            continue
        provenance = str(fields.get(provenance_key) or "").strip()
        if not _is_ws_provenance(provenance):
            gaps.append(f"{source}:existing_ws_provenance_unproven")
            continue
        if (
            freshness_state_key
            and str(fields.get(freshness_state_key) or "").strip().lower() != "fresh_ws"
        ):
            gaps.append(f"{source}:fresh_ws_state_unproven")
            continue
        bid_qty = _safe_float(fields.get(bid_qty_key)) if bid_qty_key else None
        ask_qty = _safe_float(fields.get(ask_qty_key)) if ask_qty_key else None
        if not (
            bid_qty_key
            and ask_qty_key
            and bid_qty_valid_key
            and ask_qty_valid_key
            and _boolish(fields.get(bid_qty_valid_key))
            and _boolish(fields.get(ask_qty_valid_key))
            and bid_qty is not None
            and ask_qty is not None
            and bid_qty >= 1
            and ask_qty >= 1
            and bid_qty.is_integer()
            and ask_qty.is_integer()
        ):
            gaps.append(f"{source}:displayed_best_quantity_missing_or_not_fillable")
            continue
        observed_epoch = _safe_float(fields.get(epoch_key)) if epoch_key else None
        reference_epoch = (
            _safe_float(fields.get(reference_epoch_key))
            if reference_epoch_key
            else None
        )
        if reference_epoch is None:
            # Legacy rows recorded age relative to event emission.  New rows
            # persist the exact enrichment reference epoch so logger latency is
            # not misclassified as quote staleness.
            reference_epoch = event_time.timestamp()
        if reference_epoch > event_time.timestamp() + 0.1:
            gaps.append(f"{source}:quote_reference_after_event")
            continue
        observed_at = (
            datetime.fromtimestamp(observed_epoch, tz=KST)
            if observed_epoch is not None
            else datetime.fromtimestamp(reference_epoch, tz=KST)
            - timedelta(milliseconds=age_ms)
        )
        observed_lag_ms = (reference_epoch - observed_at.timestamp()) * 1_000.0
        if observed_lag_ms < 0:
            gaps.append(f"{source}:observation_time_after_event")
            continue
        if observed_lag_ms > MAX_QUOTE_AGE_MS:
            gaps.append(f"{source}:observation_time_stale")
            continue
        if abs(observed_lag_ms - age_ms) > 100.0:
            gaps.append(f"{source}:quote_age_timestamp_mismatch")
            continue
        return (
            {
                "observed_at": observed_at.isoformat(),
                "observed_epoch": observed_at.timestamp(),
                "event_epoch": event_time.timestamp(),
                "reference_epoch": reference_epoch,
                "best_bid": bid,
                "best_ask": ask,
                "best_bid_qty": int(bid_qty),
                "best_ask_qty": int(ask_qty),
                "spread_bps": (ask - bid) / ask * 10_000.0,
                "quote_age_ms": age_ms,
                "source": source,
                "source_provenance": provenance,
                "stage": str(row.get("stage") or ""),
                "stock_code": _code(row),
                "venue": venue,
                "market_session_bucket": session,
                "scanner_promotion_id": str(
                    fields.get("scanner_promotion_id") or ""
                ).strip(),
                "evaluation_id": str(
                    fields.get("rising_missed_tp1_evaluation_id") or ""
                ).strip(),
            },
            "pass",
        )
    if gaps:
        return None, "|".join(sorted(set(gaps)))
    return None, "executable_existing_ws_bbo_missing"


def _parse_bbo_sample_list(value: Any) -> tuple[list[Any] | None, str]:
    """Decode bounded BBO bundles after scalar pipeline-event persistence.

    ``emit_pipeline_event`` intentionally stores field values as strings.  New
    producers emit canonical JSON; ``literal_eval`` is retained only for the
    already persisted Python-repr rows from earlier runtime revisions.
    """

    if isinstance(value, list):
        return value, "native_list"
    if not isinstance(value, str) or not value.strip():
        return None, "samples_missing"
    if len(value) > 1_000_000:
        return None, "samples_payload_too_large"
    text = value.strip()
    try:
        decoded = json.loads(text)
        decoder = "canonical_json"
    except (json.JSONDecodeError, TypeError):
        try:
            decoded = ast.literal_eval(text)
            decoder = "legacy_python_repr"
        except (SyntaxError, ValueError):
            return None, "samples_malformed"
    if not isinstance(decoded, list):
        return None, "samples_not_list"
    if len(decoded) > 256:
        return None, "samples_count_exceeds_bound"
    return decoded, decoder


def _bundled_pre_anchor_ws_bbos(
    row: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Expand one bounded runtime ring without weakening BBO provenance."""

    fields = _fields(row)
    event_time = _event_time(row)
    venue = _venue(fields)
    session = _session(fields)
    raw_samples, samples_decoder = _parse_bbo_sample_list(
        fields.get("rising_missed_entry_turn_bbo_samples")
    )
    bundle_schema_version = str(
        fields.get("rising_missed_entry_turn_bbo_bundle_schema_version") or ""
    ).strip()
    if event_time is None:
        return [], ["pre_anchor_bundle:event_time_missing"]
    if venue == "UNKNOWN" or session == "UNKNOWN":
        return [], ["pre_anchor_bundle:explicit_venue_or_session_missing"]
    if raw_samples is None:
        return [], [f"pre_anchor_bundle:{samples_decoder}"]
    if samples_decoder == "canonical_json" and bundle_schema_version != (
        PRE_ANCHOR_BUNDLE_SCHEMA_VERSION
    ):
        return [], ["pre_anchor_bundle:schema_version_missing_or_unsupported"]
    declared_sample_count = _safe_float(
        fields.get("rising_missed_entry_turn_bbo_sample_count")
    )
    if (
        declared_sample_count is None
        or not declared_sample_count.is_integer()
        or int(declared_sample_count) != len(raw_samples)
    ):
        return [], ["pre_anchor_bundle:sample_count_mismatch"]
    if not raw_samples:
        capture_reason = str(
            fields.get("rising_missed_entry_turn_bbo_last_capture_reason") or "unknown"
        ).strip()
        return [], [f"pre_anchor_bundle:no_samples:{capture_reason}"]
    evaluation_id = str(fields.get("rising_missed_tp1_evaluation_id") or "").strip()
    promotion_id = str(fields.get("scanner_promotion_id") or "").strip()
    observations: list[dict[str, Any]] = []
    gaps: list[str] = []
    for sample in raw_samples:
        if not isinstance(sample, Mapping):
            gaps.append("pre_anchor_bundle:sample_not_object")
            continue
        sample_venue = str(sample.get("effective_venue") or "").strip().upper()
        sample_session = str(sample.get("market_session_bucket") or "").strip().lower()
        sample_promotion_id = str(sample.get("scanner_promotion_id") or "").strip()
        if (
            sample_venue != venue
            or sample_session != session
            or not promotion_id
            or sample_promotion_id != promotion_id
        ):
            gaps.append("pre_anchor_bundle:lineage_or_scope_mismatch")
            continue
        if bundle_schema_version == PRE_ANCHOR_BUNDLE_SCHEMA_VERSION:
            code = _code(row)
            market_route = str(sample.get("market_route") or "").strip().lower()
            observed_item = str(sample.get("observed_item") or "").strip().upper()
            route_scope_status = str(sample.get("route_scope_status") or "").strip()
            if venue == "KRX":
                route_identity_valid = bool(
                    code and market_route == "krx_regular" and observed_item == code
                )
            elif venue == "NXT":
                route_identity_valid = bool(
                    code
                    and market_route == "nxt_only"
                    and observed_item == f"{code}_NX"
                )
            else:
                route_identity_valid = bool(
                    code
                    and (
                        (
                            market_route == "nxt_only"
                            and observed_item == f"{code}_NX"
                            and route_scope_status == "exact_0d_route_snapshot"
                        )
                        or (
                            market_route == "krx_nxt_integrated"
                            and observed_item == f"{code}_AL"
                            and route_scope_status
                            == "exact_0d_integrated_route_nxt_only_depth_proven"
                        )
                    )
                )
            if not route_identity_valid:
                gaps.append("pre_anchor_bundle:exact_route_identity_invalid")
                continue
        bid = _safe_float(sample.get("best_bid"))
        ask = _safe_float(sample.get("best_ask"))
        bid_qty = _safe_float(sample.get("best_bid_qty"))
        ask_qty = _safe_float(sample.get("best_ask_qty"))
        age_ms = _safe_float(sample.get("quote_age_ms"))
        observed_epoch = _safe_float(sample.get("observed_epoch"))
        recorded_epoch = _safe_float(sample.get("recorded_epoch"))
        provenance = str(sample.get("source_provenance") or "").strip()
        observed_venue = str(sample.get("observed_venue") or "").strip().upper()
        route_scope_status = str(sample.get("route_scope_status") or "").strip()
        if bid is None or ask is None or bid <= 0 or ask < bid:
            gaps.append("pre_anchor_bundle:invalid_or_crossed_bbo")
            continue
        if (
            bid_qty is None
            or ask_qty is None
            or bid_qty < 1
            or ask_qty < 1
            or not bid_qty.is_integer()
            or not ask_qty.is_integer()
        ):
            gaps.append(
                "pre_anchor_bundle:displayed_best_quantity_missing_or_not_fillable"
            )
            continue
        if age_ms is None or age_ms < 0 or age_ms > MAX_QUOTE_AGE_MS:
            gaps.append("pre_anchor_bundle:quote_age_invalid_or_stale")
            continue
        if not _is_ws_provenance(provenance):
            gaps.append("pre_anchor_bundle:existing_ws_provenance_unproven")
            continue
        expected_observed_venue = "NXT" if venue == "PREMARKET_KRX_LIKE" else venue
        if (
            observed_venue != expected_observed_venue
            or not route_scope_status.startswith("exact_0d_")
            or route_scope_status == "exact_0d_integrated_sor_execution_route"
        ):
            gaps.append("pre_anchor_bundle:exact_route_venue_provenance_invalid")
            continue
        if (
            observed_epoch is None
            or recorded_epoch is None
            or observed_epoch > recorded_epoch
            or recorded_epoch > event_time.timestamp()
        ):
            gaps.append("pre_anchor_bundle:observation_time_invalid")
            continue
        observed_lag_ms = (recorded_epoch - observed_epoch) * 1_000.0
        if observed_lag_ms > MAX_QUOTE_AGE_MS or abs(observed_lag_ms - age_ms) > 100.0:
            gaps.append("pre_anchor_bundle:quote_age_timestamp_mismatch")
            continue
        observations.append(
            {
                "observed_at": datetime.fromtimestamp(
                    observed_epoch, tz=KST
                ).isoformat(),
                "observed_epoch": observed_epoch,
                "event_epoch": event_time.timestamp(),
                "best_bid": bid,
                "best_ask": ask,
                "best_bid_qty": int(bid_qty),
                "best_ask_qty": int(ask_qty),
                "spread_bps": (ask - bid) / ask * 10_000.0,
                "quote_age_ms": age_ms,
                "source": "entry_turn_pre_anchor_bbo_ring",
                "bundle_decoder": samples_decoder,
                "bundle_schema_version": bundle_schema_version or "legacy_absent",
                "source_provenance": provenance,
                "stage": "rising_missed_entry_turn_pre_anchor_bbo_path",
                "stock_code": _code(row),
                "venue": venue,
                "market_session_bucket": session,
                "scanner_promotion_id": promotion_id,
                "evaluation_id": evaluation_id,
            }
        )
    return observations, gaps


def decode_pre_anchor_ws_bbo_bundle(
    row: Mapping[str, Any],
) -> tuple[list[dict[str, Any]], list[str]]:
    """Public source-quality decoder shared by source-only report consumers."""

    return _bundled_pre_anchor_ws_bbos(row)


def _master_date(path: Path) -> date | None:
    prefix = "micro_reversion_symbol_master_"
    name = path.name
    for suffix in (".json.gz", ".json"):
        if name.endswith(suffix):
            name = name[: -len(suffix)]
            break
    if not name.startswith(prefix):
        return None
    try:
        return date.fromisoformat(name[len(prefix) :])
    except ValueError:
        return None


def load_verified_symbol_master(
    target_date: str,
    *,
    symbol_master_path: Path | None = None,
) -> tuple[VerifiedSymbolMaster | None, dict[str, Any]]:
    """Resolve the latest eligible canonical master without invalid fallback."""

    target = date.fromisoformat(target_date)
    source_date: date | None = None
    if symbol_master_path is not None:
        selected = Path(symbol_master_path)
        source_date = _master_date(selected)
        if source_date is None:
            return None, {
                "status": "invalid",
                "target_date": target_date,
                "source_date": None,
                "path": str(selected),
                "error": "symbol_master_source_date_missing_or_invalid",
                "selection_policy": "explicit_path_requires_dated_canonical_filename",
            }
        if source_date > target:
            return None, {
                "status": "invalid",
                "target_date": target_date,
                "source_date": source_date.isoformat(),
                "path": str(selected),
                "error": "symbol_master_source_date_after_target_date",
                "selection_policy": "explicit_path_forbids_future_source_date",
            }
    else:
        candidates_by_date: dict[date, Path] = {}
        for pattern in (
            "micro_reversion_symbol_master_*.json",
            "micro_reversion_symbol_master_*.json.gz",
        ):
            for path in SYMBOL_MASTER_DIR.glob(pattern):
                logical_date = _master_date(path)
                if logical_date is None or logical_date > target:
                    continue
                logical_path = path.with_suffix("") if path.suffix == ".gz" else path
                candidates_by_date[logical_date] = logical_path
        candidates = sorted(candidates_by_date.items(), key=lambda item: item[0])
        if not candidates:
            return None, {
                "status": "missing",
                "target_date": target_date,
                "source_date": None,
                "path": None,
                "selection_policy": "latest_source_date_on_or_before_target_date",
            }
        source_date, selected = candidates[-1]
    try:
        receipt = read_json_object_strict_receipt(selected)
        source_date = _master_date(receipt.logical_path)
        if source_date is None:
            raise ValueError("symbol_master_source_date_missing_or_invalid")
        if source_date > target:
            raise ValueError("symbol_master_source_date_after_target_date")
        master = VerifiedSymbolMaster.from_payload(
            receipt.payload, require_canonical_owner=True
        )
    except (FileNotFoundError, OSError, TypeError, ValueError) as exc:
        return None, {
            "status": "invalid",
            "target_date": target_date,
            "source_date": source_date.isoformat() if source_date else None,
            "path": str(selected),
            "error": f"{type(exc).__name__}:{exc}",
            "selection_policy": "no_fallback_after_latest_eligible_invalid",
        }
    return master, {
        "status": "verified",
        "target_date": target_date,
        "source_date": source_date.isoformat() if source_date else None,
        "path": str(receipt.logical_path),
        "physical_path": str(receipt.physical_path),
        "artifact_sha256": receipt.decoded_sha256,
        "raw_artifact_sha256": receipt.raw_sha256,
        "content_sha256": receipt.payload.get("content_sha256"),
        "artifact_id": receipt.payload.get("artifact_id"),
        "symbol_count": master.symbol_count,
        "selection_policy": "explicit_path_or_latest_source_date_on_or_before_target_date",
    }


def _dedupe_observations(rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[float, float, float, int, int]] = set()
    for raw in sorted(rows, key=lambda item: float(item["observed_epoch"])):
        item = dict(raw)
        key = (
            float(item["observed_epoch"]),
            float(item["best_bid"]),
            float(item["best_ask"]),
            int(item["best_bid_qty"]),
            int(item["best_ask_qty"]),
        )
        if key in seen:
            continue
        seen.add(key)
        if deduped and (
            float(item["best_bid"]) == float(deduped[-1]["best_bid"])
            and float(item["best_ask"]) == float(deduped[-1]["best_ask"])
            and not item.get("evaluation_id")
        ):
            continue
        deduped.append(item)
    return deduped


def _max_gap_sec(rows: list[dict[str, Any]]) -> float:
    if len(rows) < 2:
        return math.inf
    return max(
        float(current["observed_epoch"]) - float(previous["observed_epoch"])
        for previous, current in zip(rows, rows[1:], strict=False)
    )


def _contiguous_suffix(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not rows:
        return []
    start = len(rows) - 1
    while start > 0:
        gap_sec = float(rows[start]["observed_epoch"]) - float(
            rows[start - 1]["observed_epoch"]
        )
        if gap_sec > MAX_INTERNAL_GAP_SEC:
            break
        start -= 1
    return rows[start:]


def _turn_profile(
    history: list[dict[str, Any]],
) -> tuple[str | None, dict[str, Any]]:
    """Classify a turn using only the supplied past-and-current history."""

    current = history[-1]
    current_epoch = float(current["observed_epoch"])
    if float(current["spread_bps"]) > MAX_ENTRY_SPREAD_BPS:
        return None, {"reason": "uneconomic_spread"}
    rebound_rows = _contiguous_suffix(
        [
            row
            for row in history
            if current_epoch - float(row["observed_epoch"]) <= REBOUND_WINDOW_SEC
        ]
    )
    if len(rebound_rows) >= 5:
        prior = rebound_rows[:-1]
        prior_low_bid = min(float(row["best_bid"]) for row in prior)
        prior_low_index = min(
            range(len(prior)), key=lambda index: float(prior[index]["best_bid"])
        )
        if prior_low_index > 0:
            prior_peak_ask = max(
                float(row["best_ask"]) for row in prior[:prior_low_index]
            )
            drawdown_pct = (prior_low_bid - prior_peak_ask) / prior_peak_ask * 100.0
            recovery_pct = (
                (float(current["best_bid"]) - prior_low_bid) / prior_low_bid * 100.0
            )
            last_three = rebound_rows[-3:]
            confirmed = float(last_three[0]["best_bid"]) <= float(
                last_three[1]["best_bid"]
            ) <= float(last_three[2]["best_bid"]) and float(
                last_three[2]["best_bid"]
            ) > float(
                last_three[0]["best_bid"]
            )
            low_precedes_confirmation = prior_low_index <= len(prior) - 2
            if (
                drawdown_pct <= -REBOUND_MIN_PRIOR_DRAWDOWN_PCT
                and recovery_pct >= REBOUND_MIN_RECOVERY_PCT
                and confirmed
                and low_precedes_confirmation
            ):
                return "rebound_turn_entry", {
                    "prior_drawdown_pct": round(drawdown_pct, 6),
                    "recovery_from_low_pct": round(recovery_pct, 6),
                    "confirmation_sample_count": len(rebound_rows),
                    "reason": "drawdown_low_then_two_sample_bid_recovery",
                }

    momentum_rows = [
        row
        for row in history
        if current_epoch - float(row["observed_epoch"]) <= MOMENTUM_WINDOW_SEC
    ]
    if (
        len(momentum_rows) >= 4
        and _max_gap_sec(momentum_rows[-4:]) <= MAX_INTERNAL_GAP_SEC
    ):
        last_four = momentum_rows[-4:]
        executable_move_pct = (
            (float(last_four[-1]["best_bid"]) - float(last_four[-3]["best_ask"]))
            / float(last_four[-3]["best_ask"])
            * 100.0
        )
        prior_move_pct = (
            (float(last_four[-2]["best_bid"]) - float(last_four[0]["best_ask"]))
            / float(last_four[0]["best_ask"])
            * 100.0
        )
        confirmed = (
            float(last_four[-3]["best_bid"])
            < float(last_four[-2]["best_bid"])
            <= float(last_four[-1]["best_bid"])
        )
        paused_before_acceleration = prior_move_pct <= MOMENTUM_MIN_EXECUTABLE_MOVE_PCT
        if (
            executable_move_pct >= MOMENTUM_MIN_EXECUTABLE_MOVE_PCT
            and confirmed
            and paused_before_acceleration
        ):
            return "momentum_turn_entry", {
                "executable_confirmation_move_pct": round(executable_move_pct, 6),
                "prior_executable_move_pct": round(prior_move_pct, 6),
                "confirmation_sample_count": len(momentum_rows),
                "reason": "pause_then_two_sample_executable_bid_acceleration",
            }
    return None, {"reason": "turn_not_confirmed"}


def _detect_turns(observations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    turns: list[dict[str, Any]] = []
    last_profile: str | None = None
    last_trigger_epoch = -math.inf
    for index, observation in enumerate(observations):
        profile, evidence = _turn_profile(observations[: index + 1])
        if profile is None:
            last_profile = None
            continue
        trigger_epoch = float(observation["observed_epoch"])
        if profile == last_profile and trigger_epoch - last_trigger_epoch <= 10.0:
            continue
        turns.append(
            {
                "profile": profile,
                "trigger_at": observation["observed_at"],
                "trigger_epoch": trigger_epoch,
                "entry_best_bid": observation["best_bid"],
                "entry_best_ask": observation["best_ask"],
                "entry_best_bid_qty": observation["best_bid_qty"],
                "entry_best_ask_qty": observation["best_ask_qty"],
                "entry_spread_bps": round(float(observation["spread_bps"]), 6),
                "source": observation["source"],
                "source_provenance": observation["source_provenance"],
                "evidence": evidence,
            }
        )
        last_profile = profile
        last_trigger_epoch = trigger_epoch
    return turns


def _scenario_outcome(
    observations: list[dict[str, Any]],
    *,
    turn: Mapping[str, Any],
    target_pct: float,
    adverse_pct: float,
    round_trip_cost_pct: float,
    observation_watermark: datetime | None,
) -> dict[str, Any]:
    entry_epoch = float(turn["trigger_epoch"])
    entry_ask = float(turn["entry_best_ask"])
    horizon_epoch = entry_epoch + OUTCOME_HORIZON_SEC
    exit_row: Mapping[str, Any] | None = None
    label = "right_censored"
    for observation in observations:
        observed_epoch = float(observation["observed_epoch"])
        if observed_epoch <= entry_epoch or observed_epoch > horizon_epoch:
            continue
        move_pct = (float(observation["best_bid"]) - entry_ask) / entry_ask * 100.0
        if move_pct >= target_pct:
            label = "target_first"
            exit_row = observation
            break
        if move_pct <= adverse_pct:
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
                <= horizon_epoch + TIMEOUT_MAX_LAG_SEC
            ]
            if timeout_rows:
                label = "timeout_exit"
                exit_row = timeout_rows[0]
            else:
                label = "right_censored_no_timeout_bbo"
        else:
            label = "pending_horizon"
    if exit_row is None:
        return {
            "target_pct": target_pct,
            "adverse_pct": adverse_pct,
            "label": label,
            "gross_return_pct": None,
            "cost_adjusted_return_pct": None,
            "elapsed_sec": None,
            "entry_best_ask_qty": int(turn["entry_best_ask_qty"]),
            "exit_best_bid_qty": None,
            "fill_feasibility_basis": (
                "displayed_best_ask_and_bid_quantity_at_exact_route_bbo"
            ),
            "actual_fill_claim": False,
        }
    gross_return_pct = (float(exit_row["best_bid"]) - entry_ask) / entry_ask * 100.0
    return {
        "target_pct": target_pct,
        "adverse_pct": adverse_pct,
        "label": label,
        "gross_return_pct": round(gross_return_pct, 8),
        "cost_adjusted_return_pct": round(gross_return_pct - round_trip_cost_pct, 8),
        "elapsed_sec": round(float(exit_row["observed_epoch"]) - entry_epoch, 6),
        "entry_best_ask_qty": int(turn["entry_best_ask_qty"]),
        "exit_best_bid_qty": int(exit_row["best_bid_qty"]),
        "fill_feasibility_basis": (
            "displayed_best_ask_and_bid_quantity_at_exact_route_bbo"
        ),
        "actual_fill_claim": False,
    }


def _first_epoch(milestones: Mapping[str, float], stage: str) -> float | None:
    value = milestones.get(stage)
    return float(value) if value is not None else None


def _nearest_percentile(values: Iterable[float], percentile: float) -> float | None:
    ordered = sorted(float(value) for value in values if math.isfinite(float(value)))
    if not ordered:
        return None
    rank = max(1, math.ceil(len(ordered) * percentile))
    return round(ordered[min(rank, len(ordered)) - 1], 6)


def _causal_bucket(
    *,
    candidate: Mapping[str, Any],
    turn: Mapping[str, Any] | None,
    milestones: Mapping[str, float],
    primary_outcome: Mapping[str, Any] | None,
) -> str:
    if turn is None:
        if candidate.get("current_outcome_source_quality_status") != "pass":
            return "source_quality_unresolved"
        current_outcome = candidate.get("current_primary_outcome") or {}
        current_label = str(current_outcome.get("label") or "")
        current_net = _safe_float(current_outcome.get("cost_adjusted_return_pct"))
        if current_label == "adverse_first" or (
            current_net is not None and current_net <= 0
        ):
            return "signal_false_positive"
        if current_label in {"target_first", "timeout_exit"}:
            return "turn_definition_false_negative"
        return "source_quality_unresolved"
    if (
        primary_outcome is None
        or primary_outcome.get("cost_adjusted_return_pct") is None
    ):
        return "source_quality_unresolved"
    if float(turn["entry_spread_bps"]) > MAX_ENTRY_SPREAD_BPS:
        return "uneconomic_spread_or_fill"
    if str(primary_outcome.get("label")) == "adverse_first":
        return "signal_false_positive"
    if float(primary_outcome["cost_adjusted_return_pct"]) <= 0:
        return "uneconomic_spread_or_fill"
    candidate_epoch = float(candidate["candidate_epoch"])
    trigger_epoch = float(turn["trigger_epoch"])
    promotion_epoch = _first_epoch(milestones, "scalping_scanner_candidate_promoted")
    attach_epoch = _first_epoch(milestones, "scalping_scanner_runtime_target_attach")
    heavy_epoch = _first_epoch(milestones, "scalping_scanner_heavy_eval_completion")
    if promotion_epoch is not None and trigger_epoch < promotion_epoch:
        return "discovery_late"
    if attach_epoch is not None and trigger_epoch < attach_epoch:
        return "watch_attach_late"
    if heavy_epoch is not None and trigger_epoch < heavy_epoch:
        return "evaluation_queue_late"
    if trigger_epoch < candidate_epoch:
        return (
            "rebound_signal_late_chase"
            if turn.get("profile") == "rebound_turn_entry"
            else "momentum_signal_late_chase"
        )
    if trigger_epoch > candidate_epoch:
        return (
            "rebound_signal_too_early"
            if turn.get("profile") == "rebound_turn_entry"
            else "momentum_signal_too_early"
        )
    return "AI_or_gate_false_negative"


def build_entry_turn_point_replay(
    events: Iterable[Mapping[str, Any]],
    *,
    target_date: str,
    current_label_rows: Iterable[Mapping[str, Any]],
    observation_watermark: datetime | None,
    symbol_master: VerifiedSymbolMaster | None,
    symbol_master_binding: Mapping[str, Any],
) -> dict[str, Any]:
    """Build a bounded causal replay from projected pipeline events."""

    event_rows = list(events)
    try:
        cost_contract = comparison_cost_contract(target_date)
        round_trip_cost_pct = float(cost_contract["round_trip_cost_pct"])
        cost_status = "verified"
    except (TypeError, ValueError) as exc:
        cost_contract = {"error": f"{type(exc).__name__}:{exc}"}
        round_trip_cost_pct = None
        cost_status = "invalid"

    current_by_evaluation = {
        str(row.get("evaluation_id") or ""): row
        for row in current_label_rows
        if str(row.get("evaluation_id") or "")
    }
    candidates: list[dict[str, Any]] = []
    seen_candidate_ids: set[str] = set()
    milestones_by_promotion: dict[str, dict[str, float]] = defaultdict(dict)
    observations_by_key: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(
        list
    )
    bbo_gap_reasons: Counter[str] = Counter()
    pre_anchor_bbo_path_event_count = 0
    pre_anchor_bbo_path_observation_count = 0
    for row in event_rows:
        fields = _fields(row)
        stage = str(row.get("stage") or "")
        event_time = _event_time(row)
        if event_time is not None and event_time.date().isoformat() != target_date:
            continue
        promotion_id = str(fields.get("scanner_promotion_id") or "").strip()
        if promotion_id and stage in MILESTONE_STAGES and event_time is not None:
            current = milestones_by_promotion[promotion_id].get(stage)
            epoch = event_time.timestamp()
            if current is None or epoch < current:
                milestones_by_promotion[promotion_id][stage] = epoch
        if stage == "rising_missed_entry_turn_pre_anchor_bbo_path":
            pre_anchor_bbo_path_event_count += 1
            observations, gap_reasons = _bundled_pre_anchor_ws_bbos(row)
            pre_anchor_bbo_path_observation_count += len(observations)
            for gap_reason in gap_reasons:
                bbo_gap_reasons[gap_reason] += 1
        else:
            observation, gap_reason = _executable_ws_bbo(row)
            observations = [observation] if observation is not None else []
            if (
                observation is None
                and gap_reason != "executable_existing_ws_bbo_missing"
            ):
                bbo_gap_reasons[gap_reason] += 1
        for observation in observations:
            if not observation.get("stock_code"):
                continue
            key = (
                str(observation["stock_code"]),
                str(observation["venue"]),
                str(observation["market_session_bucket"]),
            )
            observations_by_key[key].append(observation)
        if stage != "rising_missed_tp1_counterfactual_submit_safety":
            continue
        evaluation_id = str(fields.get("rising_missed_tp1_evaluation_id") or "").strip()
        code = _code(row)
        venue = _venue(fields)
        session = _session(fields)
        if (
            event_time is None
            or not evaluation_id
            or not code
            or evaluation_id in seen_candidate_ids
        ):
            continue
        seen_candidate_ids.add(evaluation_id)
        current_label = current_by_evaluation.get(evaluation_id, {})
        candidates.append(
            {
                "evaluation_id": evaluation_id,
                "stock_code": code,
                "stock_name": str(row.get("stock_name") or ""),
                "candidate_at": event_time.isoformat(),
                "candidate_epoch": event_time.timestamp(),
                "candidate_lane": fields.get("rising_missed_tp1_candidate_lane"),
                "selector_reason": fields.get("selector_reason"),
                "effective_venue": venue,
                "market_session_bucket": session,
                "scanner_promotion_id": promotion_id,
                "legacy_current_gross_first_hit_label": current_label.get(
                    "gross_first_hit_label"
                ),
                "legacy_current_first_hit_price_source": current_label.get(
                    "first_hit_price_source"
                ),
                "legacy_current_entry_best_ask": current_label.get(
                    "entry_executable_best_ask"
                ),
            }
        )

    for key, rows in list(observations_by_key.items()):
        observations_by_key[key] = _dedupe_observations(rows)

    candidate_evaluation_count = len(candidates)
    candidates_by_promotion_scope: dict[tuple[str, ...], dict[str, Any]] = {}
    for candidate in candidates:
        promotion_id = str(candidate.get("scanner_promotion_id") or "")
        unit_key = (
            (
                "promotion_scope",
                promotion_id,
                str(candidate.get("stock_code") or ""),
                str(candidate.get("effective_venue") or ""),
                str(candidate.get("market_session_bucket") or ""),
            )
            if promotion_id
            else ("missing_promotion", str(candidate.get("evaluation_id") or ""))
        )
        existing = candidates_by_promotion_scope.get(unit_key)
        if existing is None or float(candidate["candidate_epoch"]) < float(
            existing["candidate_epoch"]
        ):
            candidates_by_promotion_scope[unit_key] = candidate
    candidates = sorted(
        candidates_by_promotion_scope.values(),
        key=lambda item: (
            float(item["candidate_epoch"]),
            str(item.get("evaluation_id") or ""),
        ),
    )

    trade_date = date.fromisoformat(target_date)
    rows: list[dict[str, Any]] = []
    cause_counts: Counter[str] = Counter()
    profile_counts: Counter[str] = Counter()
    source_quality_counts: Counter[str] = Counter()
    milestone_reach_counts: Counter[str] = Counter()
    milestone_to_candidate_lags: dict[str, list[float]] = defaultdict(list)
    lane_cause_counts: dict[str, Counter[str]] = defaultdict(Counter)
    scenario_returns: dict[tuple[str, float, float], list[float]] = defaultdict(list)
    scenario_labels: dict[tuple[str, float, float], Counter[str]] = defaultdict(Counter)
    verified_candidate_count = 0
    exact_bbo_joined_count = 0
    pre_anchor_bbo_qualified_count = 0
    paired_count = 0
    primary_right_censored_count = 0
    primary_resolved_count = 0
    current_primary_resolved_count = 0
    for candidate in candidates:
        code = str(candidate["stock_code"])
        if symbol_master is None:
            master_status = "master_unavailable"
        else:
            lookup = symbol_master.lookup(code, as_of=trade_date)
            master_status = str(lookup.status.value)
            if lookup.economic_metadata_allowed and lookup.record is not None:
                instrument_type = str(lookup.record.instrument_type.value)
                listing_market = str(lookup.record.listing_market.value)
                if instrument_type != "EQUITY":
                    master_status = f"excluded_instrument_type:{instrument_type}"
                elif listing_market not in {"KOSPI", "KOSDAQ"}:
                    master_status = f"excluded_listing_market:{listing_market}"
        verified = master_status == "verified"
        verified_candidate_count += int(verified)
        key = (
            code,
            str(candidate["effective_venue"]),
            str(candidate["market_session_bucket"]),
        )
        candidate_promotion_id = str(candidate.get("scanner_promotion_id") or "")
        all_observations = [
            item
            for item in observations_by_key.get(key, [])
            if candidate_promotion_id
            and str(item.get("scanner_promotion_id") or "") == candidate_promotion_id
        ]
        candidate_epoch = float(candidate["candidate_epoch"])
        window_start = candidate_epoch - PRE_ANCHOR_LOOKBACK_SEC
        window_end = (
            candidate_epoch
            + REBOUND_WINDOW_SEC
            + OUTCOME_HORIZON_SEC
            + TIMEOUT_MAX_LAG_SEC
        )
        observations = [
            item
            for item in all_observations
            if window_start <= float(item["observed_epoch"]) <= window_end
        ]
        direct_candidate_entry_observations = [
            item
            for item in observations
            if item.get("stage") == "rising_missed_tp1_counterfactual_submit_safety"
            and item.get("evaluation_id") == candidate.get("evaluation_id")
            and float(item["observed_epoch"]) <= candidate_epoch
        ]
        ring_candidate_entry_observations = [
            item
            for item in observations
            if item.get("stage") == "rising_missed_entry_turn_pre_anchor_bbo_path"
            and item.get("evaluation_id") == candidate.get("evaluation_id")
            and 0.0 <= candidate_epoch - float(item["observed_epoch"]) <= 1.0
        ]
        candidate_entry_observation = (
            direct_candidate_entry_observations[-1]
            if direct_candidate_entry_observations
            else (
                ring_candidate_entry_observations[-1]
                if ring_candidate_entry_observations
                else None
            )
        )
        candidate_entry_source = (
            str(candidate_entry_observation.get("source") or "")
            if candidate_entry_observation is not None
            else None
        )
        exact_joined = candidate_entry_observation is not None
        exact_bbo_joined_count += int(verified and exact_joined)
        pre_observation_count = sum(
            float(item["observed_epoch"]) <= candidate_epoch for item in observations
        )
        pre_anchor_observations = [
            item
            for item in observations
            if float(item["observed_epoch"]) <= candidate_epoch
        ]
        pre_anchor_contiguous_count = len(_contiguous_suffix(pre_anchor_observations))
        pre_anchor_path_qualified = pre_anchor_contiguous_count >= 5
        pre_anchor_bbo_qualified_count += int(verified and pre_anchor_path_qualified)
        turns = _detect_turns(observations) if verified else []
        eligible_turns = [
            item
            for item in turns
            if candidate_epoch - PRE_ANCHOR_LOOKBACK_SEC
            <= float(item["trigger_epoch"])
            <= candidate_epoch + REBOUND_WINDOW_SEC
        ]
        turn = (
            min(
                eligible_turns,
                key=lambda item: (
                    abs(float(item["trigger_epoch"]) - candidate_epoch),
                    float(item["trigger_epoch"]) > candidate_epoch,
                ),
            )
            if eligible_turns
            else None
        )
        current_primary_outcome: dict[str, Any] | None = None
        if (
            verified
            and candidate_entry_observation is not None
            and round_trip_cost_pct is not None
        ):
            current_anchor = {
                "trigger_epoch": candidate_entry_observation["observed_epoch"],
                "entry_best_ask": candidate_entry_observation["best_ask"],
                "entry_best_ask_qty": candidate_entry_observation["best_ask_qty"],
            }
            current_primary_outcome = _scenario_outcome(
                all_observations,
                turn=current_anchor,
                target_pct=PRIMARY_TARGET_PCT,
                adverse_pct=PRIMARY_ADVERSE_PCT,
                round_trip_cost_pct=round_trip_cost_pct,
                observation_watermark=observation_watermark,
            )
        candidate["current_primary_outcome"] = current_primary_outcome
        candidate["current_outcome_source_quality_status"] = (
            "pass"
            if current_primary_outcome is not None
            and current_primary_outcome.get("cost_adjusted_return_pct") is not None
            else "source_gap_non_executable_or_unresolved_current_outcome"
        )
        current_primary_resolved_count += int(
            candidate["current_outcome_source_quality_status"] == "pass"
        )
        scenarios: list[dict[str, Any]] = []
        primary_outcome: dict[str, Any] | None = None
        if verified and turn is not None and round_trip_cost_pct is not None:
            profile = str(turn["profile"])
            profile_counts[profile] += 1
            for target_pct in TARGET_PCTS:
                for adverse_pct in ADVERSE_PCTS:
                    outcome = _scenario_outcome(
                        all_observations,
                        turn=turn,
                        target_pct=target_pct,
                        adverse_pct=adverse_pct,
                        round_trip_cost_pct=round_trip_cost_pct,
                        observation_watermark=observation_watermark,
                    )
                    scenarios.append(outcome)
                    scenario_key = (profile, target_pct, adverse_pct)
                    scenario_labels[scenario_key][str(outcome["label"])] += 1
                    value = outcome.get("cost_adjusted_return_pct")
                    if value is not None:
                        scenario_returns[scenario_key].append(float(value))
                    if (
                        target_pct == PRIMARY_TARGET_PCT
                        and adverse_pct == PRIMARY_ADVERSE_PCT
                    ):
                        primary_outcome = outcome
            if (
                primary_outcome
                and primary_outcome.get("cost_adjusted_return_pct") is not None
            ):
                paired_count += int(
                    candidate.get("current_outcome_source_quality_status") == "pass"
                )
                primary_resolved_count += 1
            else:
                primary_right_censored_count += 1
        else:
            if not verified:
                source_quality_counts[f"symbol_master:{master_status}"] += 1
            elif not candidate_promotion_id:
                source_quality_counts["scanner_promotion_id_missing"] += 1
            elif not exact_joined:
                source_quality_counts["exact_venue_session_ws_bbo_missing"] += 1
            elif turn is None:
                source_quality_counts[
                    (
                        "pre_anchor_path_missing_or_insufficient"
                        if not pre_anchor_path_qualified
                        else "causal_turn_not_confirmed"
                    )
                ] += 1
            elif round_trip_cost_pct is None:
                source_quality_counts["comparison_cost_contract_invalid"] += 1

        milestones = milestones_by_promotion.get(
            str(candidate.get("scanner_promotion_id") or ""), {}
        )
        if candidate.get("current_outcome_source_quality_status") != "pass":
            source_quality_counts["current_outcome_non_executable_or_unresolved"] += 1
        cause = (
            "source_quality_unresolved"
            if (
                not verified
                or not candidate_promotion_id
                or not exact_joined
                or (turn is None and not pre_anchor_path_qualified)
            )
            else _causal_bucket(
                candidate=candidate,
                turn=turn,
                milestones=milestones,
                primary_outcome=primary_outcome,
            )
        )
        cause_counts[cause] += 1
        lane = str(candidate.get("candidate_lane") or "unknown")
        lane_cause_counts[lane][cause] += 1
        for stage, epoch in milestones.items():
            milestone_reach_counts[stage] += 1
            if epoch <= candidate_epoch:
                milestone_to_candidate_lags[stage].append(candidate_epoch - epoch)
        rows.append(
            {
                **candidate,
                "official_symbol_master_status": master_status,
                "candidate_entry_bbo_source": candidate_entry_source,
                "exact_ws_bbo_observation_count": len(observations),
                "pre_anchor_ws_bbo_observation_count": pre_observation_count,
                "pre_anchor_contiguous_ws_bbo_observation_count": (
                    pre_anchor_contiguous_count
                ),
                "pre_anchor_bbo_path_qualified": pre_anchor_path_qualified,
                "turn": turn,
                "turn_lag_vs_candidate_sec": (
                    round(float(turn["trigger_epoch"]) - candidate_epoch, 6)
                    if turn is not None
                    else None
                ),
                "milestones": {
                    stage: datetime.fromtimestamp(epoch, tz=KST).isoformat()
                    for stage, epoch in sorted(milestones.items())
                },
                "primary_outcome": primary_outcome,
                "scenario_outcomes": scenarios,
                "causal_bucket": cause,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            }
        )

    verified_denominator = verified_candidate_count
    exact_join_pct = (
        round(exact_bbo_joined_count / verified_denominator * 100.0, 6)
        if verified_denominator
        else 0.0
    )
    paired_coverage_pct = (
        round(paired_count / primary_resolved_count * 100.0, 6)
        if primary_resolved_count
        else 0.0
    )
    pre_anchor_bbo_coverage_pct = (
        round(pre_anchor_bbo_qualified_count / verified_denominator * 100.0, 6)
        if verified_denominator
        else 0.0
    )
    primary_attempt_count = primary_resolved_count + primary_right_censored_count
    right_censored_pct = (
        round(primary_right_censored_count / primary_attempt_count * 100.0, 6)
        if primary_attempt_count
        else 100.0
    )
    symbol_master_hash_verified = _is_sha256(
        symbol_master_binding.get("artifact_sha256")
    )
    floor_met = bool(
        symbol_master_binding.get("status") == "verified"
        and symbol_master_hash_verified
        and cost_status == "verified"
        and exact_join_pct >= EXACT_BBO_JOIN_FLOOR_PCT
        and pre_anchor_bbo_coverage_pct >= PRE_ANCHOR_BBO_COVERAGE_FLOOR_PCT
        and paired_coverage_pct >= PAIRED_COVERAGE_FLOOR_PCT
        and right_censored_pct <= RIGHT_CENSORED_MAX_PCT
        and primary_resolved_count >= MIN_RESOLVED_SAMPLE_COUNT
    )
    economics_rows = []
    for scenario_key in sorted(scenario_labels):
        profile, target_pct, adverse_pct = scenario_key
        values = scenario_returns.get(scenario_key, [])
        scenario_count = sum(scenario_labels[scenario_key].values())
        scenario_right_censored_count = scenario_count - len(values)
        scenario_right_censored_pct = (
            round(scenario_right_censored_count / scenario_count * 100.0, 6)
            if scenario_count
            else 100.0
        )
        scenario_floor_met = bool(
            floor_met
            and len(values) >= MIN_RESOLVED_SAMPLE_COUNT
            and scenario_right_censored_pct <= RIGHT_CENSORED_MAX_PCT
        )
        economics_rows.append(
            {
                "profile": profile,
                "target_pct": target_pct,
                "adverse_pct": adverse_pct,
                "sample_count": scenario_count,
                "resolved_count": len(values),
                "right_censored_count": scenario_right_censored_count,
                "right_censored_pct": scenario_right_censored_pct,
                "label_counts": dict(sorted(scenario_labels[scenario_key].items())),
                "source_quality_adjusted_ev_pct": (
                    round(sum(values) / len(values), 8)
                    if scenario_floor_met and values
                    else None
                ),
                "equal_weight_avg_profit_pct": (
                    round(sum(values) / len(values), 8) if values else None
                ),
                "comparison_floor_met": scenario_floor_met,
                "promotion_allowed": False,
            }
        )
    stage_latency_rows = []
    for stage in sorted(MILESTONE_STAGES):
        values = milestone_to_candidate_lags.get(stage, [])
        stage_latency_rows.append(
            {
                "stage": stage,
                "candidate_reach_count": int(milestone_reach_counts.get(stage, 0)),
                "stage_before_candidate_count": len(values),
                "stage_to_candidate_p50_sec": _nearest_percentile(values, 0.50),
                "stage_to_candidate_p95_sec": _nearest_percentile(values, 0.95),
            }
        )
    return {
        "metric_contract": METRIC_CONTRACT,
        "status": (
            "source_only_comparison_ready" if floor_met else "source_quality_blocked"
        ),
        "candidate_count": len(candidates),
        "candidate_evaluation_count": candidate_evaluation_count,
        "candidate_unit": "scanner_promotion_symbol_venue_session",
        "runtime_instrumentation_reflected": pre_anchor_bbo_path_event_count > 0,
        "pre_anchor_bbo_path_event_count": pre_anchor_bbo_path_event_count,
        "pre_anchor_bbo_path_observation_count": (
            pre_anchor_bbo_path_observation_count
        ),
        "verified_official_common_stock_candidate_count": verified_candidate_count,
        "exact_ws_bbo_joined_count": exact_bbo_joined_count,
        "exact_ws_bbo_join_coverage_pct": exact_join_pct,
        "pre_anchor_bbo_qualified_count": pre_anchor_bbo_qualified_count,
        "pre_anchor_bbo_coverage_pct": pre_anchor_bbo_coverage_pct,
        "paired_current_and_turn_outcome_count": paired_count,
        "paired_coverage_pct": paired_coverage_pct,
        "current_point_primary_resolved_outcome_count": (
            current_primary_resolved_count
        ),
        "primary_resolved_outcome_count": primary_resolved_count,
        "primary_right_censored_count": primary_right_censored_count,
        "primary_right_censored_pct": right_censored_pct,
        "profile_counts": dict(sorted(profile_counts.items())),
        "causal_bucket_counts": dict(sorted(cause_counts.items())),
        "causal_bucket_counts_by_candidate_lane": [
            {
                "candidate_lane": lane,
                "candidate_count": sum(counter.values()),
                "causal_bucket_counts": dict(sorted(counter.items())),
            }
            for lane, counter in sorted(lane_cause_counts.items())
        ],
        "stage_latency_to_candidate": stage_latency_rows,
        "source_quality_gap_counts": dict(sorted(source_quality_counts.items())),
        "bbo_extraction_gap_counts": dict(sorted(bbo_gap_reasons.items())),
        "comparison_cost_contract_status": cost_status,
        "comparison_cost_contract": cost_contract,
        "official_symbol_master_binding": dict(symbol_master_binding),
        "acceptance": {
            "exact_bbo_join_floor_pct": EXACT_BBO_JOIN_FLOOR_PCT,
            "pre_anchor_bbo_coverage_floor_pct": (PRE_ANCHOR_BBO_COVERAGE_FLOOR_PCT),
            "paired_coverage_floor_pct": PAIRED_COVERAGE_FLOOR_PCT,
            "right_censored_max_pct": RIGHT_CENSORED_MAX_PCT,
            "minimum_resolved_sample_count": MIN_RESOLVED_SAMPLE_COUNT,
            "official_symbol_master_hash_verified": symbol_master_hash_verified,
            "runtime_instrumentation_reflected": pre_anchor_bbo_path_event_count > 0,
            "all_floors_met": floor_met,
        },
        "turn_definition": {
            "causal_past_only": True,
            "pre_anchor_lookback_sec": PRE_ANCHOR_LOOKBACK_SEC,
            "momentum_window_sec": MOMENTUM_WINDOW_SEC,
            "rebound_window_sec": REBOUND_WINDOW_SEC,
            "max_internal_gap_sec": MAX_INTERNAL_GAP_SEC,
            "max_entry_spread_bps": MAX_ENTRY_SPREAD_BPS,
            "momentum_min_executable_move_pct": MOMENTUM_MIN_EXECUTABLE_MOVE_PCT,
            "rebound_min_prior_drawdown_pct": REBOUND_MIN_PRIOR_DRAWDOWN_PCT,
            "rebound_min_recovery_pct": REBOUND_MIN_RECOVERY_PCT,
            "target_pcts": list(TARGET_PCTS),
            "adverse_pcts": list(ADVERSE_PCTS),
            "primary_target_pct": PRIMARY_TARGET_PCT,
            "primary_adverse_pct": PRIMARY_ADVERSE_PCT,
            "outcome_horizon_sec": OUTCOME_HORIZON_SEC,
            "timeout_max_lag_sec": TIMEOUT_MAX_LAG_SEC,
        },
        "economics_by_profile_scenario": economics_rows,
        "rows": rows[:200],
        "row_export_limit": 200,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "promotion_allowed": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }


__all__ = [
    "METRIC_CONTRACT",
    "MILESTONE_STAGES",
    "build_entry_turn_point_replay",
    "load_verified_symbol_master",
]
