import json
from pathlib import Path

import pytest

from src.engine.scalping.micro_reversion.execution_journal import (
    ExecutionJournalRecord,
    FillState,
    OrderOrigin,
    OrderTerminalReason,
    SubmissionState,
    append_execution_journal_record,
)


def _record(**overrides) -> ExecutionJournalRecord:
    values = {
        "record_id": "receipt-1",
        "event_id": "event-1",
        "symbol": "000001",
        "observed_at": "2026-08-08T09:00:02+09:00",
        "event_detected_ts": "2026-08-08T09:00:00+09:00",
        "receipt_sequence": 1,
        "submission_state": SubmissionState.SUBMITTED,
        "order_origin": OrderOrigin.MICRO_REVERSION,
        "fill_state": FillState.FULL_FILL,
        "execution_evidence_eligible": True,
        "order_decision_id": "decision-1",
        "quote_snapshot_id": "quote-1",
        "origin_strategy_family": "scalp_micro_reversion",
        "entry_policy_version": "entry-v1",
        "order_decision_ts": "2026-08-08T09:00:00.100+09:00",
        "submit_ts": "2026-08-08T09:00:00.200+09:00",
        "broker_ack_ts": "2026-08-08T09:00:00.300+09:00",
        "first_fill_ts": "2026-08-08T09:00:00.400+09:00",
        "cumulative_fill_qty": 1,
        "fill_vwap": 10_000,
        "order_terminal_ts": "2026-08-08T09:00:00.400+09:00",
        "order_terminal_reason": OrderTerminalReason.FILLED,
    }
    values.update(overrides)
    return ExecutionJournalRecord(**values)


def test_execution_journal_preserves_orthogonal_provenance(tmp_path: Path) -> None:
    path = tmp_path / "execution.jsonl"
    append_execution_journal_record(path, _record())

    payload = json.loads(path.read_text().strip())
    assert payload["strategy_order_submitted"] is True
    assert payload["observed_actual_order_submitted"] is True
    assert payload["journal_broker_action_forbidden"] is True
    assert payload["fill_state"] == "FULL_FILL"


def test_external_order_cannot_be_strategy_evidence() -> None:
    with pytest.raises(ValueError, match="external order"):
        _record(
            order_origin=OrderOrigin.EXTERNAL_OTHER_STRATEGY,
            origin_strategy_family="other_strategy",
            execution_evidence_eligible=True,
        )


def test_no_fill_requires_submitted_terminal_receipt() -> None:
    with pytest.raises(ValueError, match="terminal receipt"):
        _record(
            fill_state=FillState.NO_FILL,
            cumulative_fill_qty=0,
            fill_vwap=None,
            first_fill_ts=None,
            order_terminal_ts=None,
            order_terminal_reason=OrderTerminalReason.UNKNOWN,
            execution_evidence_eligible=False,
        )


def test_counterfactual_touch_is_not_real_execution_evidence() -> None:
    record = _record(
        submission_state=SubmissionState.NOT_SUBMITTED,
        order_origin=OrderOrigin.COUNTERFACTUAL,
        fill_state=FillState.TOUCH_ONLY,
        execution_evidence_eligible=False,
        hypothetical_entry_policy="RESTING_BID",
        order_decision_id=None,
        quote_snapshot_id=None,
        origin_strategy_family=None,
        entry_policy_version=None,
        order_decision_ts=None,
        submit_ts=None,
        broker_ack_ts=None,
        first_fill_ts=None,
        cumulative_fill_qty=0,
        fill_vwap=None,
        order_terminal_ts=None,
        order_terminal_reason=OrderTerminalReason.UNKNOWN,
    )
    assert record.observed_actual_order_submitted is False
    assert record.execution_evidence_eligible is False


def test_micro_reversion_origin_requires_decision_quote_pair_even_not_submitted() -> (
    None
):
    with pytest.raises(ValueError, match="decision and quote pairing"):
        _record(
            submission_state=SubmissionState.NOT_SUBMITTED,
            fill_state=FillState.NOT_APPLICABLE,
            execution_evidence_eligible=False,
            order_decision_id=None,
            quote_snapshot_id=None,
            submit_ts=None,
            broker_ack_ts=None,
            first_fill_ts=None,
            cumulative_fill_qty=0,
            fill_vwap=None,
            order_terminal_ts=None,
            order_terminal_reason=OrderTerminalReason.UNKNOWN,
        )


def test_fill_must_not_follow_terminal_receipt() -> None:
    with pytest.raises(ValueError, match="first_fill_ts"):
        _record(order_terminal_ts="2026-08-08T09:00:00.350+09:00")


def test_external_origin_cannot_claim_not_submitted() -> None:
    with pytest.raises(ValueError, match="external order origin"):
        _record(
            submission_state=SubmissionState.NOT_SUBMITTED,
            order_origin=OrderOrigin.EXTERNAL_OTHER_STRATEGY,
            origin_strategy_family="other_strategy",
            fill_state=FillState.NOT_APPLICABLE,
            execution_evidence_eligible=False,
            submit_ts=None,
            broker_ack_ts=None,
            first_fill_ts=None,
            cumulative_fill_qty=0,
            fill_vwap=None,
            order_terminal_ts=None,
            order_terminal_reason=OrderTerminalReason.UNKNOWN,
        )
