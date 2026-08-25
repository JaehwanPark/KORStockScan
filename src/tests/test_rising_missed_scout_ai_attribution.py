import json
from datetime import datetime

from src.engine import sniper_execution_receipts as receipts
from src.engine import sniper_state_handlers as handlers
from src.engine.monitoring import scalping_pyramid_intraday_feedback as feedback
from src.engine.scalping.rising_missed_one_share_entry import (
    FORCED_ENTRY_REASON,
    freeze_scout_ai_parent_fields,
    scout_ai_execution_attribution_fields,
)


def _entry_ai_stock() -> dict:
    return {
        "id": 7,
        "name": "TEST",
        "code": "123456",
        "last_watching_ai_decision_trace_id": "trace-entry-1",
        "last_watching_ai_snapshot_id": "snapshot-entry-1",
        "last_watching_ai_action": "DROP",
        "last_watching_ai_score": 14,
        "last_watching_ai_result_source": "live",
        "last_watching_ai_attempt_contract_status": "pass",
        "last_watching_ai_probe_intent": False,
        "last_watching_ai_probe_intent_status": "not_eligible",
        "last_watching_ai_probe_intent_prompt_version": (
            "decision_quality_v2_7_probe_v1"
        ),
        "last_watching_ai_probe_intent_eligibility_path": "not_eligible",
        "last_watching_ai_probe_intent_after_cost_reward_risk": 0.0,
    }


def _armed_scout_stock() -> dict:
    stock = _entry_ai_stock()
    stock.update(freeze_scout_ai_parent_fields(stock))
    stock.update(
        {
            "rising_missed_one_share_entry_forced": True,
            "rising_missed_one_share_scout": True,
            "forced_entry_reason": FORCED_ENTRY_REASON,
            "entry_split_probe_bundle_id": "probe-bundle-1",
        }
    )
    return stock


def test_scout_attribution_freezes_non_authoritative_ai_drop() -> None:
    stock = _armed_scout_stock()
    stock.update(
        {
            "last_watching_ai_decision_trace_id": "trace-newer",
            "last_watching_ai_snapshot_id": "snapshot-newer",
            "last_watching_ai_action": "BUY",
            "last_watching_ai_score": 91,
        }
    )

    fields = scout_ai_execution_attribution_fields(
        stock,
        stage="probe_submitted",
        actual_order_submitted=True,
    )

    assert fields["scout_ai_attribution_status"] == "linked_frozen_parent"
    assert fields["scout_ai_parent_decision_trace_id"] == "trace-entry-1"
    assert fields["scout_ai_parent_snapshot_id"] == "snapshot-entry-1"
    assert fields["scout_ai_parent_action"] == "DROP"
    assert fields["scout_ai_parent_score"] == 14
    assert fields["scout_ai_parent_probe_intent"] is False
    assert fields["scout_ai_action_used_as_submit_authority"] is False
    assert fields["scout_ai_parent_actual_order_submitted"] is False
    assert fields["scout_submission_authority"] == "rising_missed_submit_guard"
    assert fields["scout_attribution_actual_order_submitted"] is True
    assert fields["scout_attribution_runtime_effect"] is False
    assert fields["scout_probe_bundle_id"] == "probe-bundle-1"


def test_submit_authority_refreshes_scout_parent_to_current_wait_probe() -> None:
    stock = _armed_scout_stock()
    stock.update(
        {
            "last_watching_ai_decision_trace_id": "trace-wait-probe",
            "last_watching_ai_snapshot_id": "snapshot-wait-probe",
            "last_watching_ai_action": "WAIT",
            "last_watching_ai_score": 65,
            "last_watching_ai_result_source": "live",
            "last_watching_ai_attempt_contract_status": "pass",
            "last_watching_ai_probe_intent": True,
            "last_watching_ai_probe_intent_status": "eligible_wait_probe",
            "last_watching_ai_probe_intent_eligibility_path": (
                "v2_13_clean_continuation_wait"
            ),
            "last_watching_ai_probe_intent_after_cost_reward_risk": 0.875,
        }
    )

    refreshed = handlers._refresh_rising_missed_scout_ai_parent_provenance(stock)
    fields = scout_ai_execution_attribution_fields(
        stock,
        stage="probe_submitted",
        actual_order_submitted=True,
    )

    assert refreshed["rising_missed_scout_parent_ai_action"] == "WAIT"
    assert refreshed["rising_missed_scout_parent_ai_score"] == 65
    assert fields["scout_ai_parent_decision_trace_id"] == "trace-wait-probe"
    assert fields["scout_ai_parent_snapshot_id"] == "snapshot-wait-probe"
    assert fields["scout_ai_parent_score"] == 65
    assert fields["scout_ai_parent_probe_intent"] is True
    assert fields["scout_ai_parent_probe_intent_status"] == "eligible_wait_probe"
    assert fields["scout_ai_parent_probe_intent_eligibility_path"] == (
        "v2_13_clean_continuation_wait"
    )
    assert fields["scout_ai_parent_probe_intent_after_cost_reward_risk"] == 0.875


def test_non_scout_has_no_execution_attribution() -> None:
    assert (
        scout_ai_execution_attribution_fields(
            _entry_ai_stock(),
            stage="order_bundle_submitted",
            actual_order_submitted=True,
        )
        == {}
    )


def test_pre_ai_scout_stage_is_pending_not_provenance_incomplete() -> None:
    stock = {
        "id": 8,
        "name": "PRE_AI_SCOUT",
        "code": "234567",
        "rising_missed_one_share_entry_forced": True,
        "rising_missed_one_share_scout": True,
        "forced_entry_reason": FORCED_ENTRY_REASON,
    }

    pending = scout_ai_execution_attribution_fields(
        stock,
        stage="rising_missed_scout_allocator_order_plan",
        actual_order_submitted=False,
    )
    invalid_submit = scout_ai_execution_attribution_fields(
        stock,
        stage="probe_submitted",
        actual_order_submitted=True,
    )

    assert pending["scout_ai_attribution_status"] == (
        "parent_ai_not_evaluated_yet"
    )
    assert invalid_submit["scout_ai_attribution_status"] == (
        "parent_provenance_incomplete"
    )
    summary = feedback._one_share_summary(
        [
            {"scout_ai_attribution_status": pending["scout_ai_attribution_status"]},
            {
                "scout_ai_attribution_status": (
                    "linked_parent_pending_probe_bundle"
                )
            },
            {
                "scout_ai_attribution_status": invalid_submit[
                    "scout_ai_attribution_status"
                ]
            },
        ]
    )
    assert summary["scout_ai_attribution_incomplete_count"] == 1
    assert summary["scout_ai_attribution_pre_ai_pending_count"] == 1
    assert summary["scout_ai_attribution_probe_bundle_pending_count"] == 1


def test_receipt_confirmed_position_marker_preserves_scout_attribution() -> None:
    stock = _entry_ai_stock()
    stock.update(freeze_scout_ai_parent_fields(stock))
    stock.update(
        {
            "rising_missed_scout_position_cycle_active": True,
            "entry_split_probe_bundle_id": "probe-bundle-restored",
        }
    )

    fields = scout_ai_execution_attribution_fields(
        stock,
        stage="holding_started_after_reload",
        actual_order_submitted=True,
    )

    assert fields["scout_ai_attribution_status"] == "linked_frozen_parent"
    assert fields["scout_probe_bundle_id"] == "probe-bundle-restored"
    assert fields["scout_execution_stage"] == "holding_started_after_reload"


def test_entry_pipeline_emits_scout_parent_link(monkeypatch) -> None:
    emitted = []
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda *args, **kwargs: emitted.append((args, kwargs)),
    )

    handlers._log_entry_pipeline(
        _armed_scout_stock(),
        "123456",
        "order_bundle_submitted",
        actual_order_submitted=True,
    )

    fields = emitted[-1][1]["fields"]
    assert fields["scout_ai_parent_decision_trace_id"] == "trace-entry-1"
    assert fields["scout_execution_stage"] == "order_bundle_submitted"
    assert fields["scout_attribution_actual_order_submitted"] is True
    assert fields["actual_order_submitted"] is True
    assert fields["ai_decision_trace_id"] == "trace-entry-1"
    assert fields["ai_input_snapshot_id"] == "snapshot-entry-1"


def test_receipt_snapshot_preserves_frozen_scout_parent() -> None:
    for key in freeze_scout_ai_parent_fields(_entry_ai_stock()):
        assert key in receipts._SELL_RECEIPT_SNAPSHOT_KEYS
    assert "entry_split_probe_bundle_id" in receipts._SELL_RECEIPT_SNAPSHOT_KEYS
    assert (
        "rising_missed_scout_position_cycle_active"
        in receipts._BUY_RECEIPT_SNAPSHOT_KEYS
    )
    assert (
        "rising_missed_scout_position_cycle_active"
        in receipts._SELL_COMPLETE_RESET_KEYS
    )
    assert (
        "rising_missed_scout_position_cycle_active"
        in receipts._SELL_REVIVE_RESET_KEYS
    )


def test_buy_receipt_persists_position_cycle_marker(monkeypatch) -> None:
    class _CaptureSession:
        def __init__(self):
            self.updated = None

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def query(self, *args, **kwargs):
            return self

        def filter_by(self, **kwargs):
            return self

        def filter(self, *args, **kwargs):
            return self

        def update(self, values, synchronize_session=False):
            self.updated = dict(values)
            return 1

    session = _CaptureSession()
    monkeypatch.setattr(
        receipts,
        "DB",
        type("_DB", (), {"get_session": lambda self: session})(),
    )

    receipts._update_db_for_buy(
        7,
        10000,
        datetime(2026, 8, 24, 13, 0, 0),
        {
            "code": "123456",
            "buy_price": 10000,
            "buy_qty": 1,
            "buy_execution_notified": True,
            "rising_missed_scout_position_cycle_active": True,
        },
    )

    assert session.updated["status"] == "HOLDING"
    assert session.updated["rising_missed_scout_position_cycle_active"] is True


def test_feedback_consumer_joins_scout_attribution_across_lifecycle() -> None:
    attribution = scout_ai_execution_attribution_fields(
        _armed_scout_stock(),
        stage="rising_missed_one_share_entry",
        actual_order_submitted=False,
    )
    plan = {
        "pipeline": "ENTRY_PIPELINE",
        "stage": "rising_missed_one_share_entry",
        "record_id": 7,
        "stock_code": "123456",
        "stock_name": "TEST",
        "emitted_at": "2026-08-03T08:05:00+09:00",
        "fields": {
            "rising_missed_one_share_scout": True,
            **attribution,
        },
    }
    item = feedback._one_share_record(plan)
    scout = _armed_scout_stock()
    for stage, emitted_at in (
        ("probe_submitted", "2026-08-03T08:05:01+09:00"),
        ("probe_filled", "2026-08-03T08:05:02+09:00"),
        ("order_bundle_submitted", "2026-08-03T08:05:03+09:00"),
        ("holding_started", "2026-08-03T08:05:04+09:00"),
        ("sell_completed", "2026-08-03T08:10:00+09:00"),
    ):
        event = {
            "pipeline": (
                "ENTRY_PIPELINE" if stage == "probe_submitted" else "HOLDING_PIPELINE"
            ),
            "stage": stage,
            "record_id": 7,
            "stock_code": "123456",
            "emitted_at": emitted_at,
            "fields": {
                **scout_ai_execution_attribution_fields(
                    scout,
                    stage=stage,
                    actual_order_submitted=True,
                ),
                "actual_order_submitted": True,
                "qty": 1,
                "buy_qty": 1,
                "fill_qty": 1,
                "profit_rate": "+1.00",
            },
        }
        feedback._update_scout_ai_execution_attribution(item, event)
        feedback._update_real_entry_lifecycle(item, event)
        if stage == "sell_completed":
            feedback._update_sell(item, event)

    assert item["scout_ai_parent_decision_trace_id"] == "trace-entry-1"
    assert item["scout_ai_attribution_real_submission_seen"] is True
    assert item["scout_ai_attribution_conflict"] is False
    assert set(item["scout_ai_attribution_lifecycle_stages"]) == {
        "rising_missed_one_share_entry",
        "probe_submitted",
        "probe_filled",
        "order_bundle_submitted",
        "holding_started",
        "sell_completed",
    }
    summary = feedback._one_share_summary([item])
    assert summary["scout_ai_attribution_linked_count"] == 1
    assert summary["scout_ai_attribution_incomplete_count"] == 0
    assert summary["scout_ai_attribution_conflict_count"] == 0
    assert summary["scout_ai_attribution_closed_full_lifecycle_count"] == 1
    assert summary["scout_ai_attribution_closed_incomplete_lifecycle_count"] == 0


def test_feedback_report_consumes_attribution_from_every_lifecycle_stage(
    tmp_path,
) -> None:
    scout = _armed_scout_stock()
    events = []
    for stage, emitted_at, pipeline in (
        (
            "rising_missed_one_share_entry",
            "2026-08-03T08:05:00+09:00",
            "ENTRY_PIPELINE",
        ),
        ("probe_submitted", "2026-08-03T08:05:01+09:00", "ENTRY_PIPELINE"),
        ("probe_filled", "2026-08-03T08:05:02+09:00", "HOLDING_PIPELINE"),
        ("order_bundle_submitted", "2026-08-03T08:05:03+09:00", "ENTRY_PIPELINE"),
        ("holding_started", "2026-08-03T08:05:04+09:00", "HOLDING_PIPELINE"),
        ("sell_completed", "2026-08-03T08:10:00+09:00", "HOLDING_PIPELINE"),
    ):
        fields = {
            **scout_ai_execution_attribution_fields(
                scout,
                stage=stage,
                actual_order_submitted=stage != "rising_missed_one_share_entry",
            ),
            "rising_missed_one_share_scout": True,
            "actual_order_submitted": stage != "rising_missed_one_share_entry",
            "qty": 1,
            "buy_qty": 1,
            "fill_qty": 1,
        }
        if stage == "sell_completed":
            fields["profit_rate"] = "+1.00"
        events.append(
            {
                "pipeline": pipeline,
                "stage": stage,
                "record_id": 7,
                "stock_code": "123456",
                "stock_name": "TEST",
                "emitted_at": emitted_at,
                "fields": fields,
            }
        )

    pipeline_path = tmp_path / "pipeline_events_2026-08-03.jsonl"
    pipeline_path.write_text(
        "".join(json.dumps(event) + "\n" for event in events),
        encoding="utf-8",
    )

    report = feedback.build_report(
        "2026-08-03",
        pipeline_path=pipeline_path,
        generated_at="2026-08-03T15:40:00+09:00",
    )

    summary = report["summary"]
    assert summary["scout_ai_attribution_closed_full_lifecycle_count"] == 1, "|".join(
        report["one_share_pyramid_opportunity_rows"][0].get(
            "scout_ai_attribution_lifecycle_stages"
        )
        or []
    )
    assert summary["scout_ai_attribution_closed_incomplete_lifecycle_count"] == 0
    assert set(
        report["one_share_pyramid_opportunity_rows"][0][
            "scout_ai_attribution_lifecycle_stages"
        ]
    ) >= {
        "probe_submitted",
        "probe_filled",
        "order_bundle_submitted",
        "holding_started",
        "sell_completed",
    }
