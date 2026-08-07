import json
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from src.engine.scalping import entry_candidate_lifecycle_state as lifecycle

KST = ZoneInfo("Asia/Seoul")


def _candidate_fields(*, mode="performance_bounded"):
    return {
        "ai_decision_trace_id": "analyze_target:005930:1:abcd1234",
        "ai_input_payload_sha256": "a" * 64,
        "ai_prompt_version": "decision_quality_v2_14_setup_risk_adjudicator",
        "decision_quality_live_adapter": "entry_setup_v2_14_krx_bounded_probe_v1",
        "entry_setup_live_policy_status": "active_bounded_krx_canary",
        "entry_setup_live_policy_mode": mode,
        "entry_setup_live_policy_effective_venue": "KRX",
        "entry_setup_live_policy_session_bucket": "krx_regular",
        "entry_probe_first_required": True,
        "entry_ai_full_entry_forbidden": True,
    }


def _observe(path, stock, stage, fields, offset):
    return lifecycle.observe_candidate_transition(
        stock,
        "005930",
        stage,
        fields,
        observed_at=datetime(2026, 8, 7, 9, 3, tzinfo=KST) + timedelta(seconds=offset),
        output_path=path,
    )


def test_materializer_preserves_exact_candidate_full_lifecycle(tmp_path):
    path = tmp_path / "events.jsonl"
    stock = {"id": 17, "code": "005930", "name": "삼성전자"}
    assert _observe(path, stock, "ai_confirmed", _candidate_fields(), 0)
    assert _observe(
        path,
        stock,
        "probe_submitted",
        {
            "probe_bundle_id": "probe-1",
            "order_no": "buy-1",
            "qty": 1,
            "price": 100_000,
            "actual_order_submitted": True,
        },
        1,
    )
    assert _observe(
        path,
        stock,
        "probe_filled",
        {
            "probe_bundle_id": "probe-1",
            "order_no": "buy-1",
            "fill_qty": 1,
            "fill_price": 100_000,
            "probe_fill_slippage_bps": 1.5,
        },
        2,
    )
    assert _observe(
        path,
        stock,
        "residual_planned",
        {
            "post_probe_direction_state": "STRONG",
            "post_probe_continuation_action": "ALLOW",
            "requested_qty": 3,
            "filled_qty": 1,
        },
        3,
    )
    assert _observe(
        path,
        stock,
        "residual_submitted",
        {
            "probe_bundle_id": "probe-1",
            "order_no": "buy-2",
            "residual_leg_index": 1,
            "qty": 2,
            "price": 100_100,
            "post_probe_direction_state": "STRONG",
            "post_probe_continuation_action": "ALLOW",
            "actual_order_submitted": True,
        },
        4,
    )
    stock["entry_split_probe_phase"] = "residual_submitted"
    assert _observe(
        path,
        stock,
        "position_rebased_after_fill",
        {
            "order_no": "buy-2",
            "fill_price": 100_100,
            "fill_qty": 2,
            "order_requested_qty": 2,
            "order_filled_qty": 2,
        },
        5,
    )
    assert _observe(
        path,
        stock,
        "bundle_completed",
        {
            "probe_bundle_id": "probe-1",
            "requested_qty": 3,
            "filled_qty": 3,
            "avg_buy_price": 100_067,
        },
        6,
    )
    assert _observe(
        path,
        stock,
        "stat_action_decision_snapshot",
        {
            "scale_in_gate_allowed": False,
            "scale_in_blocker_reason": "continuation_not_confirmed",
            "chosen_action": "HOLD",
        },
        7,
    )
    assert _observe(
        path,
        stock,
        "holding_started",
        {"buy_price": 100_067, "buy_qty": 3},
        8,
    )
    assert _observe(
        path,
        stock,
        "exit_signal",
        {"exit_rule": "TRAILING", "sell_price": 101_000, "sell_qty": 3},
        9,
    )
    assert _observe(
        path,
        stock,
        "sell_completed",
        {
            "order_no": "sell-1",
            "buy_price": 100_067,
            "buy_qty": 3,
            "sell_price": 101_000,
            "sell_qty": 3,
            "realized_pnl_krw": 2_103,
            "profit_rate": 0.70,
            "actual_order_submitted": True,
        },
        10,
    )

    report = lifecycle.materialize_candidate_states(
        "2026-08-07", source_path=path, write=False
    )
    assert report["candidate_state_count"] == 1
    assert report["full_lifecycle_evaluable_candidate_count"] == 1
    state = report["states"][0]
    assert state["source_quality_status"] == "pass"
    assert state["probe"]["status"] == "filled"
    assert state["post_probe"]["direction_state"] == "STRONG"
    assert state["residual_multi_leg"]["status"] == "terminal_submitted"
    assert state["residual_multi_leg"]["legs"] == [
        {
            "submitted_at": "2026-08-07T09:03:04+09:00",
            "filled_at": "2026-08-07T09:03:05+09:00",
            "order_no": "buy-2",
            "leg_index": 1,
            "submitted_price": 100_100,
            "requested_qty": 2,
            "fill_price": 100_100,
            "filled_qty": 2,
            "fill_slippage_bps": 0.0,
            "terminal_state": "filled",
            "cancel_reason": None,
            "cancel_response": None,
            "broker_route": None,
        }
    ]
    assert state["scale_in"]["status"] == "evaluated_not_submitted"
    assert state["holding_exit"]["status"] == "terminal_exit_filled"
    assert state["broker_order_nos"] == ["buy-1", "buy-2", "sell-1"]
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    holding_row = next(row for row in rows if row["stage"] == "holding_started")
    assert holding_row["broker_order_no"] is None
    assert state["economics"]["entry_notional_krw"] == 300_201
    assert state["economics"]["estimated_combined_fee_tax_cost_krw"] > 0
    assert state["runtime_effect"] is False
    assert state["allowed_runtime_apply"] is False


def test_one_share_policy_forbidden_components_do_not_pass(tmp_path):
    path = tmp_path / "events.jsonl"
    stock = {"id": 18, "code": "005930"}
    assert _observe(
        path,
        stock,
        "ai_confirmed",
        _candidate_fields(mode="one_share_exploration"),
        0,
    )
    assert _observe(
        path,
        stock,
        "probe_filled",
        {"probe_bundle_id": "probe-2", "fill_qty": 1, "fill_price": 100_000},
        1,
    )
    assert _observe(
        path,
        stock,
        "residual_blocked",
        {
            "entry_split_probe_terminal_outcome": "residual_not_submitted",
            "post_probe_direction_state": "STRONG",
            "post_probe_continuation_action": "BLOCK",
        },
        2,
    )
    report = lifecycle.materialize_candidate_states(
        "2026-08-07", source_path=path, write=False
    )
    state = report["states"][0]
    assert state["residual_multi_leg"]["status"] == "policy_forbidden"
    assert state["scale_in"]["status"] == "policy_forbidden"
    assert state["source_quality_status"] == "blocked"
    assert report["full_lifecycle_evaluable_candidate_count"] == 0


def test_cancelled_residual_leg_is_explicit_terminal_state(tmp_path):
    path = tmp_path / "events.jsonl"
    stock = {"id": 24, "code": "005930"}
    assert _observe(path, stock, "ai_confirmed", _candidate_fields(), 0)
    assert _observe(
        path,
        stock,
        "probe_filled",
        {
            "probe_bundle_id": "probe-cancel",
            "order_no": "buy-probe",
            "fill_qty": 1,
            "fill_price": 100_000,
        },
        1,
    )
    stock["entry_split_probe_phase"] = "residual_submitted"
    assert _observe(
        path,
        stock,
        "residual_submitted",
        {
            "probe_bundle_id": "probe-cancel",
            "order_no": "buy-residual",
            "residual_leg_index": 1,
            "qty": 2,
            "price": 100_100,
            "post_probe_direction_state": "STRONG",
            "post_probe_continuation_action": "ALLOW_NORMAL",
        },
        2,
    )
    assert _observe(
        path,
        stock,
        "entry_order_cancel_confirmed",
        {
            "orig_ord_no": "buy-residual",
            "tag": "entry_split_probe_residual_1",
            "qty": 2,
            "filled_qty": 0,
            "remaining_qty": 2,
            "cancel_reason": "entry_split_leg_ttl",
            "cancel_response": "success",
        },
        3,
    )
    assert _observe(
        path,
        stock,
        "residual_partial_complete",
        {
            "probe_bundle_id": "probe-cancel",
            "requested_qty": 3,
            "filled_qty": 1,
        },
        4,
    )

    state = lifecycle.materialize_candidate_states(
        "2026-08-07", source_path=path, write=False
    )["states"][0]
    assert state["residual_multi_leg"]["status"] == "terminal_submitted"
    assert state["residual_multi_leg"]["legs"][0]["terminal_state"] == (
        "cancelled_unfilled"
    )


def test_route_conflict_blocks_source_quality_and_raw_fields_are_bounded(tmp_path):
    path = tmp_path / "events.jsonl"
    stock = {"id": 19, "code": "005930"}
    assert _observe(path, stock, "ai_confirmed", _candidate_fields(), 0)
    assert _observe(
        path,
        stock,
        "probe_submitted",
        {
            "effective_venue": "NXT",
            "order_no": "buy-3",
            "qty": 1,
            "price": 100_000,
            "access_token": "must-not-be-recorded",
        },
        1,
    )
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert rows[-1]["route_conflict"] is True
    assert "access_token" not in rows[-1]["data"]
    report = lifecycle.materialize_candidate_states(
        "2026-08-07", source_path=path, write=False
    )
    assert "venue_or_session_conflict" in report["states"][0]["source_quality_blockers"]


def test_tampered_event_authority_contract_cannot_pass_source_quality(tmp_path):
    path = tmp_path / "events.jsonl"
    stock = {"id": 25, "code": "005930"}
    assert _observe(path, stock, "ai_confirmed", _candidate_fields(), 0)
    row = json.loads(path.read_text(encoding="utf-8"))
    row["runtime_effect"] = True
    path.write_text(json.dumps(row) + "\n", encoding="utf-8")

    state = lifecycle.materialize_candidate_states(
        "2026-08-07", source_path=path, write=False
    )["states"][0]
    assert "event_authority_contract_invalid" in state["source_quality_blockers"]
    assert state["source_quality_status"] == "blocked"


def test_duplicate_transition_signature_is_suppressed(tmp_path):
    path = tmp_path / "events.jsonl"
    stock = {"id": 20, "code": "005930"}
    assert _observe(path, stock, "ai_confirmed", _candidate_fields(), 0)
    fields = {"probe_bundle_id": "probe-4", "order_no": "buy-4", "qty": 1}
    assert _observe(path, stock, "probe_submitted", fields, 1)
    assert not _observe(path, stock, "probe_submitted", fields, 2)


def test_latest_pre_submit_candidate_owns_lifecycle_and_execution_locks_it(tmp_path):
    path = tmp_path / "events.jsonl"
    stock = {"id": 22, "code": "005930"}
    first = _candidate_fields()
    second = {
        **_candidate_fields(),
        "ai_decision_trace_id": "analyze_target:005930:2:efgh5678",
        "ai_input_payload_sha256": "b" * 64,
    }
    third = {
        **_candidate_fields(),
        "ai_decision_trace_id": "analyze_target:005930:3:ijkl9012",
        "ai_input_payload_sha256": "c" * 64,
    }

    assert _observe(path, stock, "ai_confirmed", first, 0)
    assert _observe(path, stock, "ai_confirmed", second, 1)
    assert (
        stock[lifecycle.CONTEXT_KEY]["decision_trace_id"]
        == second["ai_decision_trace_id"]
    )
    assert _observe(
        path,
        stock,
        "probe_submitted",
        {"probe_bundle_id": "probe-latest", "order_no": "buy-latest", "qty": 1},
        2,
    )
    assert not _observe(path, stock, "ai_confirmed", third, 3)
    assert (
        stock[lifecycle.CONTEXT_KEY]["decision_trace_id"]
        == second["ai_decision_trace_id"]
    )

    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert [row["decision_trace_id"] for row in rows] == [
        first["ai_decision_trace_id"],
        second["ai_decision_trace_id"],
        second["ai_decision_trace_id"],
    ]


def test_non_candidate_decision_clears_unsubmitted_candidate_context(tmp_path):
    path = tmp_path / "events.jsonl"
    stock = {"id": 23, "code": "005930"}
    assert _observe(path, stock, "ai_confirmed", _candidate_fields(), 0)

    assert not _observe(
        path,
        stock,
        "ai_confirmed",
        {
            "ai_decision_trace_id": "analyze_target:005930:v213",
            "ai_input_payload_sha256": "d" * 64,
            "decision_quality_live_adapter": "decision_quality_v2_13_live",
            "entry_setup_live_policy_status": "control_v2_13",
            "entry_setup_live_policy_effective_venue": "KRX",
            "entry_setup_live_policy_session_bucket": "krx_regular",
        },
        1,
    )
    assert lifecycle.CONTEXT_KEY not in stock


def test_restart_recovery_keeps_cross_midnight_event_on_candidate_trade_date(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(lifecycle, "EVENT_DIR", tmp_path)
    stock = {"id": 21, "code": "005930"}
    fields = {
        **_candidate_fields(),
        "entry_setup_live_policy_target_date": "2026-08-07",
    }
    assert lifecycle.observe_candidate_transition(
        stock,
        "005930",
        "ai_confirmed",
        fields,
        observed_at=datetime(2026, 8, 7, 23, 59, 50, tzinfo=KST),
    )
    assert lifecycle.observe_candidate_transition(
        stock,
        "005930",
        "probe_submitted",
        {"probe_bundle_id": "probe-restart", "order_no": "buy-restart", "qty": 1},
        observed_at=datetime(2026, 8, 7, 23, 59, 51, tzinfo=KST),
    )
    stock.pop(lifecycle.CONTEXT_KEY)
    stock["entry_split_probe_bundle_id"] = "probe-restart"

    assert lifecycle.observe_candidate_transition(
        stock,
        "005930",
        "holding_started",
        {"buy_price": 100_000, "buy_qty": 1},
        observed_at=datetime(2026, 8, 8, 0, 0, 2, tzinfo=KST),
    )

    prior_path = lifecycle.event_path("2026-08-07")
    current_path = lifecycle.event_path("2026-08-08")
    rows = [
        json.loads(line) for line in prior_path.read_text(encoding="utf-8").splitlines()
    ]
    assert rows[-1]["stage"] == "holding_started"
    assert rows[-1]["trade_date"] == "2026-08-07"
    assert not current_path.exists()
    assert stock[lifecycle.CONTEXT_KEY]["recovered_after_restart"] is True
