"""Shared offline validation of fully accounted observer row quarantines.

Owned by micro-reversion source quality; no collector, trading or apply authority.
Kept outside the frozen canary benchmark module to preserve its evidence hash.
"""

from __future__ import annotations

import re
from typing import Any, Mapping

TIMESTAMP_REGRESSION_ROW_EXCLUSION_PATTERN = re.compile(
    r"^raw_row_exclusion_required:"
    r"path_exchange_timestamp_regression_exceeded_count=(\d+)$"
)
CANARY_LOSS_COUNTERS = (
    "adapter_isolated_error_count",
    "observation_dropped_envelope_count",
    "observation_queue_full_count",
    "worker_error_count",
    "writer_capture_degraded_count",
    "writer_dropped_envelope_count",
    "writer_error_count",
    "writer_manifest_error_count",
    "writer_projection_breach_count",
    "writer_queue_full_count",
    "writer_storage_self_disabled_count",
    "depth_dropped_envelope_count",
    "depth_queue_full_count",
    "depth_worker_error_count",
    "depth_writer_dropped_envelope_count",
    "depth_writer_error_count",
    "depth_writer_manifest_error_count",
    "depth_writer_projection_breach_count",
    "depth_writer_queue_full_count",
    "depth_writer_storage_self_disabled_count",
    "event_reference_error_count",
    "orphan_reference_count",
    "unreferenced_segment_count",
    "duplicate_event_reference_count",
    "duplicate_event_id_count",
    "duplicate_path_reference_pair_count",
    "path_duplicate_sequence_count",
    "path_out_of_order_sequence_count",
    "path_local_receive_timestamp_regression_count",
    "path_point_dropped_count",
    "reference_reconciliation_error_count",
    "unexplained_sequence_gap_count",
    "writer_restart_count",
    "canonical_stream_duplicate_count",
    "collector_close_failure_count",
    "collector_worker_alive_after_close_count",
    "writer_alive_after_close_count",
    "event_symbol_mismatch_count",
)
CANARY_FORBIDDEN_TRUE_FIELDS = (
    "p2_real_data_discovery_run",
    "research_policy_selected",
    "selection_authority",
    "sim_position_effect",
    "trading_runtime_effect",
    "trading_decision_effect",
    "threshold_effect",
    "broker_effect",
    "actual_order_submitted",
)


def closed_pre_enqueue_epoch_quarantine_validation(
    guard: Mapping[str, Any], collector: Mapping[str, Any]
) -> dict[str, Any]:
    """Validate exact rejection receipts for a strictly epoch-fenced consumer.

    This is not a whole-date pass. The caller MUST exclude every raw stream,
    depth and reference row outside ``allowed_sequence_epoch`` before joining.
    The existing R0/Provider validator deliberately does not call this helper.
    """
    from .canary_monitor import timestamp_source_quality_census

    rejected = {"eligible": False, "status": "pre_enqueue_epoch_contract_invalid"}
    epoch = collector.get("sequence_epoch")
    if (
        type(epoch) is not int
        or epoch <= 0
        or guard.get("status") != "stopped_clean"
        or guard.get("stop_required") is not False
        or guard.get("stop_reasons") != []
        or guard.get("raw_row_exclusion_required") is not True
        or collector.get("collector_lifecycle") != "closed"
        or collector.get("reference_reconciliation_completed") is not True
        or collector.get("broker_order_forbidden") is not True
        or any(collector.get(k) is not False for k in CANARY_FORBIDDEN_TRUE_FIELDS)
    ):
        return rejected
    for field in (
        *CANARY_LOSS_COUNTERS,
        "stale_sequence_epoch_envelope_count",
        "path_exchange_timestamp_regression_count",
        "path_exchange_timestamp_regression_exceeded_count",
        "path_exchange_timestamp_regression_quarantined_count",
    ):
        if type(collector.get(field)) is not int or collector[field] != 0:
            return {**rejected, "invalid_counter": field}
    census = timestamp_source_quality_census(dict(collector))
    if (
        census.get("exact_rejected_row_exclusion_proven") is not True
        or guard.get("timestamp_source_quality") != census
        or guard.get("source_quality_row_exclusions") != census["issues"]
    ):
        return rejected
    receipts = collector["timestamp_rejection_samples"]
    if len({r["process_pid"] for r in receipts}) != 1 or any(
        not 0 < r["local_observer_epoch"] <= epoch for r in receipts
    ):
        return rejected
    groups = [
        (
            "enqueued_count",
            "worker_processed_count",
            "writer_persisted_envelope_count",
            "path_point_submitted_count",
        )
    ]
    if collector.get("depth_capture_requested") is True:
        groups.append(
            (
                "depth_enqueued_count",
                "depth_worker_processed_count",
                "depth_writer_persisted_envelope_count",
            )
        )
    for group in groups:
        values = [collector.get(k) for k in group]
        if any(type(v) is not int or v < 0 for v in values) or len(set(values)) != 1:
            return {**rejected, "status": "pre_enqueue_persistence_mismatch"}
    return {
        "eligible": True,
        "status": "fully_accounted_pre_enqueue_epoch_only",
        "allowed_sequence_epoch": epoch,
        "quarantined_row_count": len(receipts),
        "whole_date_approval": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }


def timestamp_regression_row_quarantine_validation(
    guard: Mapping[str, Any], collector: Mapping[str, Any]
) -> dict[str, Any]:
    """Allow only fully accounted, consumer-ineligible timestamp rows.

    The canary's generic ``raw_row_exclusion_required`` flag also covers real
    capture loss.  That state must remain fail-closed.  Timestamp-regression
    rows are different: the V3 producer marks each affected row consumer
    ineligible and this consumer independently skips it.  We therefore keep
    the remaining date usable only when the producer proves exact accounting,
    lossless persistence, and the dedicated row-quarantine authority contract.
    """

    base = {
        "eligible": False,
        "status": "not_applicable",
        "quarantined_row_count": None,
    }
    if guard.get("raw_row_exclusion_required") is not True:
        return base
    exclusions = guard.get("source_quality_row_exclusions")
    if (
        not isinstance(exclusions, (list, tuple))
        or isinstance(exclusions, (str, bytes))
        or len(exclusions) != 1
        or not isinstance(exclusions[0], str)
    ):
        return {**base, "status": "mixed_or_invalid_row_exclusion_reasons"}
    match = TIMESTAMP_REGRESSION_ROW_EXCLUSION_PATTERN.fullmatch(exclusions[0])
    if match is None:
        return {**base, "status": "non_timestamp_row_exclusion_present"}
    quarantined_count = int(match.group(1))
    if quarantined_count <= 0:
        return {**base, "status": "invalid_timestamp_quarantine_count"}

    def exact_nonnegative_int(field: str) -> int | None:
        value = collector.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            return None
        return value

    if (
        guard.get("status") != "stopped_clean"
        or guard.get("stop_required") is not False
        or guard.get("stop_reasons") not in ([], ())
    ):
        return {
            **base,
            "status": "row_quarantine_requires_stopped_clean_canary",
            "quarantined_row_count": quarantined_count,
        }
    if (
        collector.get("collector_lifecycle") != "closed"
        or collector.get("reference_reconciliation_completed") is not True
    ):
        return {
            **base,
            "status": "row_quarantine_requires_closed_reconciled_collector",
            "quarantined_row_count": quarantined_count,
        }
    if (
        exact_nonnegative_int("path_exchange_timestamp_regression_exceeded_count")
        != quarantined_count
    ):
        return {
            **base,
            "status": "timestamp_quarantine_count_mismatch",
            "quarantined_row_count": quarantined_count,
        }
    regression_total = exact_nonnegative_int("path_exchange_timestamp_regression_count")
    tolerated_count = exact_nonnegative_int(
        "path_exchange_timestamp_regression_quarantined_count"
    )
    if (
        regression_total is None
        or tolerated_count is None
        or regression_total != tolerated_count + quarantined_count
    ):
        return {
            **base,
            "status": "timestamp_regression_accounting_mismatch",
            "quarantined_row_count": quarantined_count,
        }
    invalid_loss_fields = [
        field for field in CANARY_LOSS_COUNTERS if exact_nonnegative_int(field) != 0
    ]
    if invalid_loss_fields:
        return {
            **base,
            "status": "capture_loss_or_missing_counter",
            "quarantined_row_count": quarantined_count,
            "invalid_loss_fields": invalid_loss_fields,
        }
    invalid_authority_fields = [
        field
        for field in CANARY_FORBIDDEN_TRUE_FIELDS
        if collector.get(field) is not False
    ]
    if invalid_authority_fields or collector.get("broker_order_forbidden") is not True:
        return {
            **base,
            "status": "row_quarantine_authority_contract_invalid",
            "quarantined_row_count": quarantined_count,
            "invalid_authority_fields": invalid_authority_fields,
        }
    observation_counts = [
        exact_nonnegative_int(field)
        for field in (
            "enqueued_count",
            "worker_processed_count",
            "writer_persisted_envelope_count",
            "path_point_submitted_count",
        )
    ]
    if (
        any(value is None for value in observation_counts)
        or len(set(observation_counts)) != 1
        or regression_total > observation_counts[0]
    ):
        return {
            **base,
            "status": "observation_persistence_accounting_mismatch",
            "quarantined_row_count": quarantined_count,
        }
    if collector.get("depth_capture_requested") is True:
        depth_counts = [
            exact_nonnegative_int(field)
            for field in (
                "depth_enqueued_count",
                "depth_worker_processed_count",
                "depth_writer_persisted_envelope_count",
            )
        ]
        if any(value is None for value in depth_counts) or len(set(depth_counts)) != 1:
            return {
                **base,
                "status": "depth_persistence_accounting_mismatch",
                "quarantined_row_count": quarantined_count,
            }
    metric_contracts = collector.get("metric_contracts")
    quarantine_contract = (
        metric_contracts.get("exchange_timestamp_regression_canary")
        if isinstance(metric_contracts, Mapping)
        else None
    )
    forbidden_uses = (
        quarantine_contract.get("forbidden_uses")
        if isinstance(quarantine_contract, Mapping)
        else None
    )
    if (
        not isinstance(forbidden_uses, (list, tuple))
        or not all(isinstance(value, str) for value in forbidden_uses)
        or not isinstance(quarantine_contract, Mapping)
        or not all(
            (
                quarantine_contract.get("metric_role")
                == "source_quality_incident_and_raw_row_exclusion",
                quarantine_contract.get("decision_authority")
                == "observer_row_quarantine_only",
                quarantine_contract.get("primary_decision_metric")
                == "path_exchange_timestamp_regression_exceeded_count",
                quarantine_contract.get("source_quality_gate")
                == (
                    "affected_rows_remain_path_consumer_ineligible_and_are_skipped_by_"
                    "p2_reconstruction_without_imputation"
                ),
                "detector_or_path_consumption_of_quarantined_row"
                in (quarantine_contract.get("forbidden_uses") or ()),
                "broker_order_submission"
                in (quarantine_contract.get("forbidden_uses") or ()),
            )
        )
    ):
        return {
            **base,
            "status": "timestamp_quarantine_metric_contract_invalid",
            "quarantined_row_count": quarantined_count,
        }
    return {
        "eligible": True,
        "status": "fully_accounted_consumer_ineligible_rows",
        "quarantined_row_count": quarantined_count,
        "invalid_loss_fields": [],
    }
