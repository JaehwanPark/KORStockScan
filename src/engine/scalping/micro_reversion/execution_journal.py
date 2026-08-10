"""Append-only provenance journal for observed execution evidence.

Submission state, order origin, fill state, and evidence eligibility are
orthogonal.  This module has no broker client or order/cancel authority.
"""

from __future__ import annotations

import fcntl
import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import StrEnum
from pathlib import Path
from typing import Any

from .contracts import normalize_symbol

EXECUTION_JOURNAL_SCHEMA = "scalp_micro_reversion_execution_journal_v3"
EXECUTION_JOURNAL_AUTHORITY = "execution_receipt_observation_only"
EXECUTION_JOURNAL_METRIC_CONTRACT = {
    "metric_role": "execution_observation_provenance",
    "decision_authority": EXECUTION_JOURNAL_AUTHORITY,
    "window_policy": "append_only_event_decision_order_and_receipt_timeline",
    "sample_floor": "no_promotion_until_forward_clustered_economic_gate_closes",
    "primary_decision_metric": "source_quality_adjusted_ev_pct",
    "source_quality_gate": (
        "submission_origin_fill_state_separated_and_terminal_receipt_"
        "required_for_no_fill"
    ),
    "forbidden_uses": (
        "broker_order_submission",
        "broker_order_cancel",
        "automated_sell",
        "threshold_or_provider_change",
        "quantity_or_cap_change",
        "external_order_as_micro_reversion_fill_evidence",
        "touch_or_trade_through_as_real_fill",
    ),
}


class SubmissionState(StrEnum):
    NOT_SUBMITTED = "NOT_SUBMITTED"
    SUBMITTED = "SUBMITTED"
    UNKNOWN = "UNKNOWN"


class OrderOrigin(StrEnum):
    NONE = "NONE"
    COUNTERFACTUAL = "COUNTERFACTUAL"
    EXTERNAL_OTHER_STRATEGY = "EXTERNAL_OTHER_STRATEGY"
    MICRO_REVERSION = "MICRO_REVERSION"


class FillState(StrEnum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    TOUCH_ONLY = "TOUCH_ONLY"
    TRADE_THROUGH = "TRADE_THROUGH"
    NO_FILL = "NO_FILL"
    PARTIAL_FILL = "PARTIAL_FILL"
    FULL_FILL = "FULL_FILL"
    RECEIPT_INCOMPLETE = "RECEIPT_INCOMPLETE"


class OrderTerminalReason(StrEnum):
    FILLED = "FILLED"
    CANCEL_CONFIRMED = "CANCEL_CONFIRMED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True, slots=True)
class ExecutionJournalRecord:
    record_id: str
    event_id: str
    symbol: str
    observed_at: str
    event_detected_ts: str
    receipt_sequence: int
    submission_state: SubmissionState
    order_origin: OrderOrigin
    fill_state: FillState
    execution_evidence_eligible: bool
    order_decision_id: str | None = None
    quote_snapshot_id: str | None = None
    origin_strategy_family: str | None = None
    hypothetical_entry_policy: str | None = None
    entry_policy_version: str | None = None
    reference_bid: float | None = None
    reference_ask: float | None = None
    bid_depth: float | None = None
    ask_depth: float | None = None
    shock_low: float | None = None
    order_decision_ts: str | None = None
    submit_ts: str | None = None
    broker_ack_ts: str | None = None
    first_fill_ts: str | None = None
    cumulative_fill_qty: int = 0
    fill_vwap: float | None = None
    tp_submit_ts: str | None = None
    tp_ack_ts: str | None = None
    tp_fill_ts: str | None = None
    cancel_request_ts: str | None = None
    cancel_confirm_ts: str | None = None
    order_terminal_ts: str | None = None
    order_terminal_reason: OrderTerminalReason = OrderTerminalReason.UNKNOWN
    late_fill_qty: int = 0
    schema: str = EXECUTION_JOURNAL_SCHEMA

    def __post_init__(self) -> None:
        if not str(self.record_id).strip() or not str(self.event_id).strip():
            raise ValueError("record_id and event_id are required")
        symbol = normalize_symbol(self.symbol)
        if not symbol:
            raise ValueError("symbol is required")
        if self.receipt_sequence < 0:
            raise ValueError("receipt_sequence must not be negative")
        if self.cumulative_fill_qty < 0 or self.late_fill_qty < 0:
            raise ValueError("fill quantities must not be negative")
        if self.fill_vwap is not None and self.fill_vwap <= 0:
            raise ValueError("fill_vwap must be positive")
        for field_name in ("reference_bid", "reference_ask", "shock_low"):
            value = getattr(self, field_name)
            if value is not None and value <= 0:
                raise ValueError(f"{field_name} must be positive")
        for field_name in ("bid_depth", "ask_depth"):
            value = getattr(self, field_name)
            if value is not None and value < 0:
                raise ValueError(f"{field_name} must not be negative")
        if (
            self.reference_bid is not None
            and self.reference_ask is not None
            and self.reference_ask < self.reference_bid
        ):
            raise ValueError("reference_ask must not be below reference_bid")
        submission_state = SubmissionState(self.submission_state)
        order_origin = OrderOrigin(self.order_origin)
        fill_state = FillState(self.fill_state)
        terminal_reason = OrderTerminalReason(self.order_terminal_reason)
        observed_at = _parse_aware_timestamp(self.observed_at, field_name="observed_at")
        detected_at = _parse_aware_timestamp(
            self.event_detected_ts, field_name="event_detected_ts"
        )
        if observed_at < detected_at:
            raise ValueError("observed_at must not precede event_detected_ts")
        parsed_timestamps: dict[str, datetime] = {}
        for field_name in (
            "order_decision_ts",
            "submit_ts",
            "broker_ack_ts",
            "first_fill_ts",
            "tp_submit_ts",
            "tp_ack_ts",
            "tp_fill_ts",
            "cancel_request_ts",
            "cancel_confirm_ts",
            "order_terminal_ts",
        ):
            value = getattr(self, field_name)
            if value is not None:
                parsed_timestamps[field_name] = _parse_aware_timestamp(
                    value, field_name=field_name
                )
        _validate_timestamp_order(parsed_timestamps)

        object.__setattr__(self, "symbol", symbol)
        object.__setattr__(self, "submission_state", submission_state)
        object.__setattr__(self, "order_origin", order_origin)
        object.__setattr__(self, "fill_state", fill_state)
        object.__setattr__(self, "order_terminal_reason", terminal_reason)
        self._validate_provenance_contract()

    @property
    def strategy_order_submitted(self) -> bool:
        return (
            self.order_origin is OrderOrigin.MICRO_REVERSION
            and self.submission_state is SubmissionState.SUBMITTED
        )

    @property
    def observed_actual_order_submitted(self) -> bool | None:
        if self.submission_state is SubmissionState.SUBMITTED:
            return True
        if self.submission_state is SubmissionState.NOT_SUBMITTED:
            return False
        return None

    def _validate_provenance_contract(self) -> None:
        if self.submission_state is SubmissionState.NOT_SUBMITTED:
            if any(
                value is not None
                for value in (
                    self.submit_ts,
                    self.broker_ack_ts,
                    self.first_fill_ts,
                    self.cancel_request_ts,
                    self.cancel_confirm_ts,
                    self.order_terminal_ts,
                )
            ):
                raise ValueError(
                    "NOT_SUBMITTED must not carry broker receipt timestamps"
                )
            if (
                self.cumulative_fill_qty
                or self.fill_vwap is not None
                or self.late_fill_qty
            ):
                raise ValueError("NOT_SUBMITTED must not carry observed fills")
            if self.fill_state not in {
                FillState.NOT_APPLICABLE,
                FillState.TOUCH_ONLY,
                FillState.TRADE_THROUGH,
            }:
                raise ValueError(
                    "NOT_SUBMITTED requires counterfactual or N/A fill state"
                )
        if (
            self.submission_state is SubmissionState.SUBMITTED
            and self.submit_ts is None
        ):
            raise ValueError("SUBMITTED requires submit_ts")
        if self.order_origin is OrderOrigin.NONE:
            if self.submission_state is not SubmissionState.NOT_SUBMITTED:
                raise ValueError("NONE origin requires NOT_SUBMITTED")
        elif self.order_origin is OrderOrigin.COUNTERFACTUAL:
            if self.submission_state is not SubmissionState.NOT_SUBMITTED:
                raise ValueError("COUNTERFACTUAL origin cannot be submitted")
            if not self.hypothetical_entry_policy:
                raise ValueError(
                    "COUNTERFACTUAL origin requires hypothetical_entry_policy"
                )
        elif self.order_origin is OrderOrigin.EXTERNAL_OTHER_STRATEGY:
            if self.submission_state is SubmissionState.NOT_SUBMITTED:
                raise ValueError(
                    "external order origin requires submitted or unknown state"
                )
            if not self.origin_strategy_family:
                raise ValueError("external order requires origin_strategy_family")
            if self.execution_evidence_eligible:
                raise ValueError(
                    "external order cannot be micro-reversion execution evidence"
                )
        elif self.order_origin is OrderOrigin.MICRO_REVERSION:
            if not self.origin_strategy_family or not self.entry_policy_version:
                raise ValueError(
                    "micro-reversion order requires strategy family and policy version"
                )
            if not self.order_decision_id or not self.quote_snapshot_id:
                raise ValueError(
                    "micro-reversion origin requires decision and quote pairing"
                )
        if self.execution_evidence_eligible and not self.strategy_order_submitted:
            raise ValueError(
                "execution evidence is eligible only for submitted micro-reversion orders"
            )

        if self.fill_state in {FillState.PARTIAL_FILL, FillState.FULL_FILL}:
            if self.submission_state is not SubmissionState.SUBMITTED:
                raise ValueError("real fill states require a submitted order")
            if self.cumulative_fill_qty <= 0 or self.fill_vwap is None:
                raise ValueError("fill states require positive quantity and fill_vwap")
            if self.first_fill_ts is None:
                raise ValueError("fill states require first_fill_ts")
            if self.fill_state is FillState.FULL_FILL and (
                self.order_terminal_ts is None
                or self.order_terminal_reason is not OrderTerminalReason.FILLED
            ):
                raise ValueError("FULL_FILL requires a FILLED terminal receipt")
        elif self.fill_state is FillState.NO_FILL:
            if self.submission_state is not SubmissionState.SUBMITTED:
                raise ValueError("NO_FILL requires a submitted order")
            if self.cumulative_fill_qty != 0 or self.fill_vwap is not None:
                raise ValueError("NO_FILL must not carry fill quantity or fill_vwap")
            if self.order_terminal_ts is None or self.order_terminal_reason not in {
                OrderTerminalReason.CANCEL_CONFIRMED,
                OrderTerminalReason.REJECTED,
                OrderTerminalReason.EXPIRED,
            }:
                raise ValueError("NO_FILL requires a confirmed terminal receipt")
        elif self.fill_state in {FillState.TOUCH_ONLY, FillState.TRADE_THROUGH}:
            if self.cumulative_fill_qty != 0 or self.fill_vwap is not None:
                raise ValueError("counterfactual touch states must not carry fills")
            if self.execution_evidence_eligible:
                raise ValueError(
                    "touch/trade-through cannot be real execution evidence"
                )
        elif self.fill_state is FillState.NOT_APPLICABLE:
            if self.cumulative_fill_qty != 0 or self.fill_vwap is not None:
                raise ValueError("NOT_APPLICABLE must not carry fills")
        elif self.fill_state is FillState.RECEIPT_INCOMPLETE:
            if self.execution_evidence_eligible:
                raise ValueError("incomplete receipts cannot be execution evidence")

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.update(
            {
                "submission_state": self.submission_state.value,
                "order_origin": self.order_origin.value,
                "fill_state": self.fill_state.value,
                "order_terminal_reason": self.order_terminal_reason.value,
                "strategy_order_submitted": self.strategy_order_submitted,
                "observed_actual_order_submitted": (
                    self.observed_actual_order_submitted
                ),
                "actual_order_submitted": self.observed_actual_order_submitted,
                "journal_runtime_effect": False,
                "journal_broker_action_forbidden": True,
                "runtime_effect": False,
                **EXECUTION_JOURNAL_METRIC_CONTRACT,
            }
        )
        return payload


def append_execution_journal_record(
    path: Path,
    record: ExecutionJournalRecord,
) -> None:
    """Durably append one raw observation without deduplicating audit evidence."""

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    encoded = (
        json.dumps(record.as_dict(), ensure_ascii=False, sort_keys=True) + "\n"
    ).encode("utf-8")
    descriptor = os.open(target, os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o640)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        remaining = memoryview(encoded)
        while remaining:
            written = os.write(descriptor, remaining)
            if written <= 0:
                raise OSError("execution journal append made no progress")
            remaining = remaining[written:]
        os.fsync(descriptor)
    finally:
        fcntl.flock(descriptor, fcntl.LOCK_UN)
        os.close(descriptor)


def _validate_timestamp_order(timestamps: dict[str, datetime]) -> None:
    ordered_pairs = (
        ("order_decision_ts", "submit_ts"),
        ("submit_ts", "broker_ack_ts"),
        ("submit_ts", "first_fill_ts"),
        ("first_fill_ts", "order_terminal_ts"),
        ("cancel_request_ts", "cancel_confirm_ts"),
        ("submit_ts", "order_terminal_ts"),
    )
    for earlier_name, later_name in ordered_pairs:
        earlier = timestamps.get(earlier_name)
        later = timestamps.get(later_name)
        if earlier is not None and later is not None and later < earlier:
            raise ValueError(f"{later_name} must not precede {earlier_name}")


def _parse_aware_timestamp(value: str, *, field_name: str) -> datetime:
    text = str(value or "").strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field_name} must include a timezone offset")
    return parsed
