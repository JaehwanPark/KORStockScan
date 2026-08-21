from __future__ import annotations

import json
import threading
import time
from dataclasses import replace
from datetime import datetime

import pytest

from src.engine.ai.hot_path_ai_dispatcher import HotPathAIDispatcher
from src.engine.scalping.scanner_async_eval import (
    ScannerAsyncEvalCoordinator,
    ScannerAsyncEvalResult,
)
from src.engine.scalping.scanner_runtime_scheduler import ScannerGeneration
from src.engine import sniper_state_handlers as handlers


class _FakeAI:
    def analyze_target(self, *args, **kwargs):
        return {"action": "BUY", "score": 77, "reason": "fresh continuation"}


def _generation(venue="KRX"):
    return ScannerGeneration(
        code="005930",
        promotion_id="PROMO-ASYNC",
        revision=1,
        record_id=7,
        venue=venue,
        promotion_epoch=time.time() - 1,
        attach_epoch=time.time() - 0.5,
        observed_price=1000,
        source_signature="VALUE_TOP",
    )


def test_clean_profit_rising_missed_exit_records_short_confirmation_window(
    monkeypatch,
):
    handlers._RISING_MISSED_SAME_DAY_REENTRY_RISK.clear()
    monkeypatch.setenv(
        "KORSTOCKSCAN_RISING_MISSED_CLEAN_PROFIT_REENTRY_CONFIRM_SEC", "60"
    )
    stock = {
        "name": "SK innovation",
        "strategy": "SCALPING",
        "rising_missed_one_share_scout": True,
        "forced_entry_reason": handlers.RISING_MISSED_FORCED_ENTRY_REASON,
        "avg_down_count": 0,
    }
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda *_a, **_k: None)

    marked = handlers._record_rising_missed_same_day_reentry_risk(
        "096770",
        stock=stock,
        exit_rule="scalp_trailing_take_profit",
        profit_rate=0.5,
        exit_price=109600,
        now_ts=1000.0,
        source_stage="sell_order_sent",
    )

    assert marked["marked"] is True
    assert marked["reentry_action"] == "confirm"
    assert marked["reason"] == (
        "prior_rising_missed_exit_clean_profit_requires_confirmation"
    )
    assert marked["exit_price"] == 109600
    assert marked["expires_at"] == 1060.0
    handlers._RISING_MISSED_SAME_DAY_REENTRY_RISK.clear()


@pytest.mark.parametrize(
    ("realized_profit", "expected_action", "expected_reason", "expected_expires_at"),
    [
        (
            -0.10,
            "block",
            "prior_rising_missed_exit_non_positive",
            None,
        ),
        (
            0.42,
            "confirm",
            "prior_rising_missed_exit_clean_profit_requires_confirmation",
            1080.0,
        ),
    ],
)
def test_sell_receipt_reconciles_submit_time_reentry_context(
    monkeypatch,
    realized_profit,
    expected_action,
    expected_reason,
    expected_expires_at,
):
    handlers._RISING_MISSED_SAME_DAY_REENTRY_RISK.clear()
    handlers._RISING_MISSED_SAME_DAY_REENTRY_RISK["096770"] = {
        "code": "096770",
        "stock_name": "SK innovation",
        "marked_at": 1000.0,
        "expires_at": 1060.0,
        "ttl_sec": 60,
        "exit_rule": "sell_submit_rule",
        "profit_rate": 0.30,
        "exit_price": 109600,
        "avg_down_count": 0,
        "reentry_action": "confirm",
        "reason": "prior_rising_missed_exit_clean_profit_requires_confirmation",
        "source_stage": "sell_order_sent",
    }
    monkeypatch.setattr(
        handlers,
        "_rising_missed_clean_profit_reentry_confirm_sec",
        lambda: 60,
    )
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda *_a, **_k: None)

    reconciled = handlers.reconcile_rising_missed_reentry_after_sell_completed(
        "096770",
        profit_rate=realized_profit,
        exit_price=109450,
        exit_rule="broker_fill_rule",
        completed_at=1020.0,
    )

    assert reconciled["reconciled"] is True
    assert reconciled["reentry_action"] == expected_action
    assert reconciled["reason"] == expected_reason
    assert reconciled["exit_price"] == 109450
    assert reconciled["profit_rate"] == realized_profit
    assert reconciled["source_stage"] == "sell_completed"
    assert reconciled["exit_receipt_reconciled"] is True
    if expected_expires_at is None:
        assert reconciled["expires_at"] > 1020.0
    else:
        assert reconciled["expires_at"] == expected_expires_at
    handlers._RISING_MISSED_SAME_DAY_REENTRY_RISK.clear()


def test_sell_completed_fallback_escalates_negative_receipt_to_day_block(
    monkeypatch,
):
    handlers._RISING_MISSED_SAME_DAY_REENTRY_RISK.clear()
    handlers._RISING_MISSED_SAME_DAY_REENTRY_RISK["096770"] = {
        "code": "096770",
        "marked_at": 1000.0,
        "expires_at": 1060.0,
        "ttl_sec": 60,
        "exit_rule": "sell_submit_rule",
        "profit_rate": 0.30,
        "exit_price": 109600,
        "avg_down_count": 0,
        "reentry_action": "confirm",
        "reason": "prior_rising_missed_exit_clean_profit_requires_confirmation",
    }
    monkeypatch.setattr(
        handlers,
        "_rising_missed_same_day_reentry_guard_enabled",
        lambda: True,
    )
    monkeypatch.setattr(
        handlers,
        "_reconcile_rising_missed_reentry_risk_with_sell_completed",
        lambda *_a, **_k: {
            "action": "block_realized_non_positive",
            "realized_profit_rate": -0.10,
            "realized_exit_rule": "broker_fill_rule",
            "realized_exit_price": 109450,
            "sell_completed_at": 1020.0,
        },
    )
    monkeypatch.setattr(
        handlers,
        "_rising_missed_same_day_reentry_expires_at",
        lambda marked_at: (2000.0, int(2000.0 - marked_at)),
    )

    decision = handlers.evaluate_rising_missed_same_day_reentry_guard(
        "096770",
        now_ts=1030.0,
    )

    assert decision["allowed"] is False
    assert decision["reentry_action"] == "block"
    assert decision["reason"] == "prior_rising_missed_exit_non_positive"
    assert decision["last_exit_profit_rate"] == -0.10
    assert decision["last_exit_price"] == 109450
    assert decision["risk_expires_at"] == 2000.0
    handlers._RISING_MISSED_SAME_DAY_REENTRY_RISK.clear()


def test_clean_profit_reentry_confirmation_blocks_wait_above_exit():
    guard = {
        "allowed": False,
        "reentry_action": "confirm",
        "last_exit_at": 1000.0,
        "last_exit_price": 109600,
        "last_exit_profit_rate": 0.5,
        "last_exit_rule": "scalp_trailing_take_profit",
        "risk_remaining_sec": 50,
    }
    stock = {
        "last_watching_ai_action": "WAIT",
        "last_watching_ai_result_source": "live",
        "last_watching_ai_confirmed_at": 1010.0,
        "last_watching_ai_snapshot_id": "aims-new",
        "last_watching_ai_decision_trace_id": "analyze-target-new",
        "last_watching_ai_decision_price": 109900,
        "last_watching_ai_probe_intent": True,
    }

    decision = handlers._evaluate_rising_missed_clean_profit_reentry_confirmation(
        guard,
        stock,
    )

    assert decision["allowed"] is False
    assert decision["reason"] == "recent_clean_profit_wait_probe_above_exit"
    assert decision["reentry_confirmation_status"] == "deferred_no_new_entry_edge"
    assert decision["reentry_confirmation_price_vs_exit_pct"] == pytest.approx(0.273723)


def test_recent_exit_ai_context_declares_executable_price_provenance():
    context = handlers._rising_missed_recent_exit_ai_context(
        {"code": "096770"},
        {
            "reentry_action": "confirm",
            "last_exit_at": 1000.0,
            "last_exit_price": 109600,
            "last_exit_profit_rate": 0.5,
            "last_exit_rule": "scalp_trailing_take_profit",
            "risk_remaining_sec": 50,
        },
        now_ts=1010.0,
    )

    assert context["exit_price"] == 109600
    assert (
        context["exit_price_source"]
        == "sell_submit_executable_price_or_revalidated_mark"
    )
    assert "executable_price_or_revalidated_mark" in context["source_quality_gate"]


def test_recent_exit_ai_context_prefers_reconciled_broker_receipt_provenance():
    context = handlers._rising_missed_recent_exit_ai_context(
        {"code": "096770"},
        {
            "reentry_action": "confirm",
            "last_exit_at": 1000.0,
            "last_exit_price": 109450,
            "last_exit_profit_rate": 0.42,
            "last_exit_rule": "scalp_trailing_take_profit",
            "last_exit_source_stage": "sell_completed",
            "last_exit_receipt_reconciled": True,
            "risk_remaining_sec": 50,
        },
        now_ts=1010.0,
    )

    assert context["exit_price_source"] == "broker_sell_completed_receipt"
    assert context["source_quality_gate"] == "broker_sell_completed_receipt"
    assert context["exit_source_stage"] == "sell_completed"
    assert context["exit_receipt_reconciled"] is True


def test_recent_exit_ai_context_does_not_treat_false_string_as_receipt():
    context = handlers._rising_missed_recent_exit_ai_context(
        {"code": "096770"},
        {
            "reentry_action": "confirm",
            "last_exit_at": 1000.0,
            "last_exit_price": 109600,
            "last_exit_profit_rate": 0.30,
            "last_exit_rule": "sell_submit_rule",
            "last_exit_source_stage": "sell_order_sent",
            "last_exit_receipt_reconciled": "false",
            "risk_remaining_sec": 50,
        },
        now_ts=1010.0,
    )

    assert context["exit_receipt_reconciled"] is False
    assert (
        context["exit_price_source"]
        == "sell_submit_executable_price_or_revalidated_mark"
    )


def test_reentry_context_restart_hydration_prefers_latest_sell_receipt(
    monkeypatch,
    tmp_path,
):
    data_dir = tmp_path / "data"
    event_dir = data_dir / "pipeline_events"
    event_dir.mkdir(parents=True)
    target_date = "2026-07-31"
    rows = [
        {
            "pipeline": "ENTRY_PIPELINE",
            "stage": "rising_missed_same_day_reentry_risk_marked",
            "stock_code": "096770",
            "stock_name": "SK innovation",
            "emitted_at": "2026-07-31T10:24:30+09:00",
            "fields": {
                "risk_expires_at": 1785461130.0,
                "ttl_sec": 60,
                "exit_rule": "sell_submit_rule",
                "profit_rate": "+0.30",
                "exit_price": 109600,
                "avg_down_count": 0,
                "reentry_action": "confirm",
                "risk_reason": (
                    "prior_rising_missed_exit_clean_profit_requires_confirmation"
                ),
                "source_stage": "sell_order_sent",
            },
        },
        {
            "pipeline": "ENTRY_PIPELINE",
            "stage": "rising_missed_reentry_exit_receipt_reconciled",
            "stock_code": "096770",
            "stock_name": "SK innovation",
            "emitted_at": "2026-07-31T10:24:32+09:00",
            "fields": {
                "risk_expires_at": 1785461132.0,
                "ttl_sec": 60,
                "exit_rule": "broker_fill_rule",
                "profit_rate": "+0.42",
                "exit_price": 109450,
                "avg_down_count": 0,
                "reentry_action": "confirm",
                "risk_reason": (
                    "prior_rising_missed_exit_clean_profit_requires_confirmation"
                ),
                "source_stage": "sell_completed",
                "exit_receipt_reconciled": True,
            },
        },
    ]
    path = event_dir / f"pipeline_events_{target_date}.jsonl"
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )
    monkeypatch.setattr(handlers, "DATA_DIR", data_dir)
    handlers._RISING_MISSED_REENTRY_RISK_EVENT_CACHE.update(
        {
            "date": "",
            "path": "",
            "device": 0,
            "inode": 0,
            "mtime_ns": 0,
            "size": 0,
            "offset": 0,
            "rows_by_code": {},
        }
    )

    loaded = handlers._load_rising_missed_reentry_risk_events(target_date)

    latest = loaded["096770"][-1]
    assert latest["exit_price"] == 109450
    assert latest["profit_rate"] == 0.42
    assert latest["source_stage"] == "sell_completed"
    assert latest["exit_receipt_reconciled"] is True


@pytest.mark.parametrize(
    ("action", "decision_price", "probe_intent", "expected_reason"),
    [
        ("BUY", 110000, False, "recent_clean_profit_fresh_buy_confirmed"),
        ("WAIT", 109500, True, "recent_clean_profit_wait_probe_below_exit"),
    ],
)
def test_clean_profit_reentry_confirmation_allows_new_edge_or_better_price_probe(
    action,
    decision_price,
    probe_intent,
    expected_reason,
):
    decision = handlers._evaluate_rising_missed_clean_profit_reentry_confirmation(
        {
            "allowed": False,
            "reentry_action": "confirm",
            "last_exit_at": 1000.0,
            "last_exit_price": 109600,
            "last_exit_profit_rate": 0.5,
            "risk_remaining_sec": 50,
        },
        {
            "last_watching_ai_action": action,
            "last_watching_ai_result_source": "live",
            "last_watching_ai_confirmed_at": 1010.0,
            "last_watching_ai_snapshot_id": "aims-new",
            "last_watching_ai_decision_trace_id": "analyze-target-new",
            "last_watching_ai_decision_price": decision_price,
            "last_watching_ai_probe_intent": probe_intent,
        },
    )

    assert decision["allowed"] is True
    assert decision["reason"] == expected_reason


def test_scanner_entry_ai_attempt_preserves_latest_trusted_decision_on_preflight_block():
    generation = _generation("KRX")
    stock = {
        "last_watching_ai_action": "WAIT",
        "last_watching_ai_score": 63.0,
        "last_watching_ai_result_source": "live",
        "last_watching_ai_snapshot_id": "aims-trusted",
        "last_watching_ai_decision_trace_id": "aidt-trusted",
    }

    trusted = handlers._record_scanner_entry_ai_attempt(
        stock,
        ai_decision={
            "action": "DROP",
            "score": 0,
            "reason": "ai_input_preflight_blocked",
            "provider_called": False,
            "parse_ok": False,
            "ai_decision_snapshot_id": "aims-blocked",
            "ai_decision_trace_id": "aidt-blocked",
        },
        action="DROP",
        score=0.0,
        result_source="input_preflight_blocked",
        completed_epoch=1001.0,
        generation=generation,
        decision_price=1005,
        state_signature={"available_axes": ["quote_freshness"]},
        source_quality_fields={"ai_result_source": "input_preflight_blocked"},
        trigger_reason="rising_missed_entry_ai_not_evaluated_async_v1",
    )

    assert trusted is False
    assert stock["last_watching_ai_action"] == "WAIT"
    assert stock["last_watching_ai_score"] == 63.0
    assert stock["last_watching_ai_snapshot_id"] == "aims-trusted"
    assert stock["last_watching_ai_attempt_action"] == "DROP"
    assert stock["last_watching_ai_attempt_result_source"] == (
        "input_preflight_blocked"
    )
    assert stock["last_watching_ai_attempt_snapshot_id"] == "aims-blocked"
    assert stock["last_watching_ai_attempt_trusted"] is False


def test_scanner_entry_ai_attempt_does_not_promote_semantic_reject_live_result():
    generation = _generation("KRX")
    stock = {}

    trusted = handlers._record_scanner_entry_ai_attempt(
        stock,
        ai_decision={
            "action": "DROP",
            "score": 0,
            "reason": "decision_quality_v2_7_semantic_rejected",
            "decision_quality_contract_status": "semantic_rejected",
            "parse_ok": True,
            "ai_decision_snapshot_id": "aims-rejected",
            "ai_decision_trace_id": "aidt-rejected",
        },
        action="DROP",
        score=0.0,
        result_source="live",
        completed_epoch=1002.0,
        generation=generation,
        decision_price=1005,
        state_signature={"available_axes": ["quote_freshness"]},
        source_quality_fields={"ai_result_source": "live"},
        trigger_reason="rising_missed_entry_ai_not_evaluated_async_v1",
    )

    assert trusted is False
    assert "last_watching_ai_action" not in stock
    assert stock["last_watching_ai_attempt_contract_status"] == "semantic_rejected"
    assert stock["last_watching_ai_attempt_snapshot_id"] == "aims-rejected"


def test_scanner_entry_ai_timeout_is_not_stored_as_drop_authority():
    generation = _generation("KRX")
    stock = {
        "last_watching_ai_action": "WAIT",
        "last_watching_ai_score": 63.0,
        "last_watching_ai_result_source": "live",
    }

    trusted = handlers._record_scanner_entry_ai_attempt(
        stock,
        ai_decision={
            "action": "DROP",
            "score": 0,
            "reason": "request timed out",
            "openai_http_timeout_budget_exhausted": True,
            "parse_ok": False,
        },
        action="DROP",
        score=0.0,
        result_source="timeout",
        completed_epoch=1002.0,
        generation=generation,
        decision_price=1005,
        state_signature={"available_axes": ["quote_freshness"]},
        source_quality_fields={"ai_result_source": "timeout"},
        trigger_reason="rising_missed_entry_ai_not_evaluated_async_v1",
    )

    assert trusted is False
    assert stock["last_watching_ai_action"] == "WAIT"
    assert stock["last_watching_ai_score"] == 63.0
    assert stock["last_watching_ai_attempt_action"] == "NOT_EVALUATED"
    assert stock["last_watching_ai_attempt_model_action"] == "DROP"
    assert (
        stock["last_watching_ai_attempt_evaluation_status"]
        == "not_evaluated_transport_timeout"
    )
    assert stock["_scanner_entry_ai_transport_retry_after_epoch"] == 1004.0
    before = handlers._resolve_watching_state_change_refresh(
        stock,
        {},
        now_ts=1003.0,
        last_ai_time=1002.0,
        cooldown_sec=300,
    )
    due = handlers._resolve_watching_state_change_refresh(
        stock,
        {},
        now_ts=1004.0,
        last_ai_time=1002.0,
        cooldown_sec=300,
    )
    assert before["allowed"] is False
    assert before["reason"] == "transport_timeout_retry_backoff"
    assert due["allowed"] is True
    assert due["reason"] == "transport_timeout_fresh_loop_retry"


def test_scanner_entry_ai_attempt_promotes_trusted_terminal_result():
    generation = _generation("KRX")
    stock = {
        "_scanner_entry_ai_transport_retry_after_epoch": 1000.0,
        "_scanner_entry_ai_transport_retry_until_epoch": 1030.0,
    }

    trusted = handlers._record_scanner_entry_ai_attempt(
        stock,
        ai_decision={
            "action": "WAIT",
            "score": 64,
            "reason": "positive edge needs confirmation",
            "decision_quality_contract_status": "pass",
            "entry_probe_intent": True,
            "entry_probe_intent_status": "eligible_wait_probe",
            "entry_probe_intent_prompt_version": "decision_quality_v2_7_probe_v1",
            "entry_setup_live_policy_status": "active_bounded_krx_canary",
            "entry_setup_live_policy_mode": "one_share_exploration",
            "entry_setup_live_policy_runtime_effect": True,
            "entry_setup_live_policy_max_daily_exploration_probes": 3,
            "entry_setup_live_policy_activation_sha256": "activation-async",
            "entry_setup_live_policy_candidate_contract_sha256": "candidate-async",
            "entry_probe_first_required": True,
            "entry_ai_full_entry_forbidden": True,
            "parse_ok": True,
            "ai_decision_snapshot_id": "aims-pass",
            "ai_decision_trace_id": "aidt-pass",
        },
        action="WAIT",
        score=64.0,
        result_source="live",
        completed_epoch=1003.0,
        generation=generation,
        decision_price=1005,
        state_signature={"available_axes": ["quote_freshness"]},
        source_quality_fields={"ai_result_source": "live"},
        trigger_reason="rising_missed_entry_ai_not_evaluated_async_v1",
    )

    assert trusted is True
    assert stock["last_watching_ai_action"] == "WAIT"
    assert stock["last_watching_ai_score"] == 64.0
    assert stock["last_watching_ai_snapshot_id"] == "aims-pass"
    assert stock["last_watching_ai_attempt_trusted"] is True
    assert stock["last_watching_ai_attempt_decision_trace_id"] == "aidt-pass"
    assert stock["last_watching_ai_attempt_probe_intent"] is True
    assert stock["last_watching_ai_probe_intent"] is True
    assert stock["last_watching_ai_probe_intent_status"] == "eligible_wait_probe"
    assert (
        stock["last_watching_ai_probe_intent_prompt_version"]
        == "decision_quality_v2_7_probe_v1"
    )
    assert stock["last_watching_ai_probe_intent_submit_guard_required"] is True
    assert stock["entry_setup_live_policy_mode"] == "one_share_exploration"
    assert stock["entry_opportunity_recheck_exploration_probe_only"] is True
    assert stock["entry_setup_bounded_exploration_probe_only"] is True
    assert stock["entry_split_probe_residual_expand_forbidden"] is True
    assert stock["entry_split_probe_scale_in_forbidden"] is True
    assert stock["probe_expand_forbidden"] is True
    assert stock["entry_setup_live_policy_max_daily_exploration_probes"] == 3
    assert "_scanner_entry_ai_transport_retry_after_epoch" not in stock
    assert "_scanner_entry_ai_transport_retry_until_epoch" not in stock


def test_scanner_entry_ai_attempt_clears_inactive_one_share_policy_residue():
    generation = _generation("KRX")
    stock = {
        "entry_opportunity_recheck_armed": True,
        "entry_opportunity_recheck_exploration_probe_only": True,
        "entry_setup_bounded_exploration_probe_only": True,
        "entry_split_probe_residual_expand_forbidden": True,
        "entry_split_probe_scale_in_forbidden": True,
        "probe_expand_forbidden": True,
        "entry_setup_live_policy_mode": "one_share_exploration",
    }

    trusted = handlers._record_scanner_entry_ai_attempt(
        stock,
        ai_decision={
            "action": "WAIT",
            "score": 64,
            "decision_quality_contract_status": "pass",
            "entry_probe_intent": True,
            "entry_probe_intent_status": "eligible_wait_probe",
            "entry_setup_live_policy_mode": "one_share_exploration",
            "entry_setup_live_policy_runtime_effect": False,
            "entry_probe_first_required": True,
            "entry_ai_full_entry_forbidden": True,
            "parse_ok": True,
            "ai_decision_snapshot_id": "aims-inactive",
            "ai_decision_trace_id": "aidt-inactive",
        },
        action="WAIT",
        score=64.0,
        result_source="live",
        completed_epoch=1003.0,
        generation=generation,
        decision_price=1005,
        state_signature={"available_axes": ["quote_freshness"]},
        source_quality_fields={"ai_result_source": "live"},
        trigger_reason="rising_missed_entry_ai_not_evaluated_async_v1",
    )

    assert trusted is True
    assert stock["entry_opportunity_recheck_armed"] is False
    assert "entry_opportunity_recheck_exploration_probe_only" not in stock
    assert "entry_setup_bounded_exploration_probe_only" not in stock
    assert "entry_split_probe_residual_expand_forbidden" not in stock
    assert "entry_split_probe_scale_in_forbidden" not in stock
    assert "probe_expand_forbidden" not in stock
    assert "entry_setup_live_policy_mode" not in stock


def test_scanner_entry_ai_contract_valid_zero_score_drop_clears_prior_probe_intent():
    generation = _generation("KRX")
    stock = {
        "last_watching_ai_action": "WAIT",
        "last_watching_ai_score": 64.0,
        "last_watching_ai_probe_intent": True,
        "last_watching_ai_confirmed_at": 900.0,
    }

    trusted = handlers._record_scanner_entry_ai_attempt(
        stock,
        ai_decision={
            "action": "DROP",
            "score": 0,
            "reason": "blocking risk",
            "decision_quality_contract_status": "pass",
            "entry_probe_intent": False,
            "entry_probe_intent_status": "not_eligible",
            "parse_ok": True,
            "ai_decision_snapshot_id": "aims-drop",
            "ai_decision_trace_id": "aidt-drop",
        },
        action="DROP",
        score=0.0,
        result_source="live",
        completed_epoch=1004.0,
        generation=generation,
        decision_price=995,
        state_signature={"available_axes": ["quote_freshness"]},
        source_quality_fields={"ai_result_source": "live"},
        trigger_reason="rising_missed_entry_ai_not_evaluated_async_v1",
    )

    assert trusted is True
    assert stock["last_watching_ai_action"] == "DROP"
    assert stock["last_watching_ai_score"] == 0.0
    assert stock["last_watching_ai_probe_intent"] is False
    assert stock["last_watching_ai_attempt_zero_score_drop_trusted"] is True
    assert stock["last_watching_ai_confirmed_at"] == 1004.0


def test_expired_ai_response_arms_fresh_snapshot_recheck(monkeypatch):
    monkeypatch.setenv(
        "KORSTOCKSCAN_SCANNER_ASYNC_EXPIRED_RESPONSE_RECHECK_TTL_SEC",
        "15",
    )
    stock = {}

    fields = handlers._arm_scanner_async_expired_response_recheck(
        stock,
        now_ts=1000.0,
        expired_snapshot_id="aims-expired-1",
    )

    assert fields["scanner_async_expired_response_recheck_armed"] is True
    assert stock["_scanner_async_expired_response_recheck_until_epoch"] == 1015.0
    assert stock["_scanner_async_expired_parent_snapshot_id"] == "aims-expired-1"
    assert (
        handlers._scanner_active_rising_recheck_reason(stock, now_ts=1001.0)
        == "expired_ai_fresh_snapshot_recheck_pending"
    )
    assert (
        handlers._scanner_active_full_eval_budget_source(stock, now_ts=1001.0)
        == "expired_ai_fresh_snapshot_recheck"
    )
    assert fields["scanner_async_expired_response_recheck_runtime_effect"] is False
    assert (
        fields["scanner_async_expired_response_recheck_actual_order_submitted"] is False
    )
    assert (
        fields["scanner_async_expired_response_recheck_broker_order_forbidden"] is True
    )


def test_async_entry_expired_result_is_discarded_and_schedules_fresh_recheck(
    monkeypatch,
):
    generation = _generation("KRX")
    coordinator = ScannerAsyncEvalCoordinator(
        ai_dispatcher=HotPathAIDispatcher(loaded_key_count=1)
    )
    cache_key = "watching:expired-result"
    stock = {
        "id": 7,
        "code": "005930",
        "name": "삼성전자",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "scanner_generation_id": generation.generation_id,
        "scanner_promotion_id": generation.promotion_id,
        "effective_venue": "KRX",
        "venue_resolution": "session_clock_explicit_krx",
        "source_signature": "VALUE_TOP",
        "_scanner_async_generation_id": generation.generation_id,
        "_scanner_async_cache_key": cache_key,
    }
    state_version = handlers._scanner_async_entry_state_version(stock)
    now = time.time()
    result = ScannerAsyncEvalResult(
        request_id=f"{generation.generation_id}:{cache_key}",
        generation_id=generation.generation_id,
        code="005930",
        venue="KRX",
        cache_key=cache_key,
        state_version=state_version,
        status="expired_after_response",
        submitted_epoch=now - 6.0,
        preparation_started_epoch=now - 6.0,
        preparation_completed_epoch=now - 5.5,
        ai_started_epoch=now - 5.5,
        completed_epoch=now - 0.1,
        preparation_wait_sec=0.0,
        preparation_service_sec=0.5,
        ai_dispatch_wait_sec=0.0,
        ai_response_sec=5.4,
        observation_only=True,
        ai_payload={
            "action": "BUY",
            "score": 80,
            "ai_decision_snapshot_id": "aims-expired-integration",
            "ai_decision_trace_id": "aidt-expired-integration",
        },
    )
    with coordinator._lock:
        coordinator._ready[result.request_id] = result
    logs = []
    monkeypatch.setattr(
        handlers,
        "_log_entry_pipeline",
        lambda _stock, _code, event, **fields: logs.append((event, fields)),
    )
    monkeypatch.setattr(handlers, "_has_open_pending_entry_orders", lambda stock: False)
    monkeypatch.setattr(handlers, "COOLDOWNS", {})
    runtime = {
        "scanner_async_eval_coordinator": coordinator,
        "scanner_async_generation": generation,
        "scanner_async_commit_phase": True,
    }
    try:
        resolved = handlers._resolve_scanner_async_entry_ai(
            stock,
            "005930",
            {
                "curr": 1001,
                "orderbook": {"ask": 1002, "bid": 1000},
                "last_ws_update_ts": time.time(),
            },
            _FakeAI(),
            runtime,
            trigger_reason="expired_result_recheck",
            last_ai_time=0,
            current_ai_score=50,
        )
    finally:
        coordinator.shutdown()

    assert resolved == {
        "status": "commit_rejected",
        "reason": "result_not_commit_eligible",
    }
    assert (
        stock["_scanner_async_expired_parent_snapshot_id"] == "aims-expired-integration"
    )
    assert "_scanner_async_cache_key" not in stock
    assert logs[-1][0] == "scanner_async_result_commit"
    assert logs[-1][1]["scanner_async_expired_response_recheck_armed"] is True
    assert logs[-1][1]["scanner_async_ai_decision_trace_id"] == (
        "aidt-expired-integration"
    )


@pytest.mark.parametrize(
    (
        "venue",
        "ws_suffix",
        "ws_route",
        "broker_route",
        "expected_request_code",
    ),
    (
        ("KRX", "", "", "KRX", "005930"),
        ("KRX", "_AL", "krx_nxt_integrated", "SOR", "005930"),
        ("KRX", "_AL", "krx_nxt_integrated", "KRX", "005930"),
        ("PREMARKET_KRX_LIKE", "", "", "KRX", "005930_NX"),
        ("NXT", "", "", "KRX", "005930_NX"),
    ),
)
def test_async_entry_bridge_prepares_off_thread_then_commits_on_current_state(
    monkeypatch,
    venue,
    ws_suffix,
    ws_route,
    broker_route,
    expected_request_code,
):
    monkeypatch.setattr(handlers, "KIWOOM_TOKEN", "token")
    monkeypatch.setattr(
        handlers.kiwoom_orders,
        "resolve_order_dmst_stex_tp",
        lambda: broker_route,
    )
    monkeypatch.setattr(
        handlers,
        "resolve_entry_candle_session",
        lambda *args, **kwargs: "krx_regular",
    )
    requested_codes = []
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_tick_history_ka10003",
        lambda token, code, **kwargs: (
            requested_codes.append(code) or [{"price": 1000}]
        ),
    )
    monkeypatch.setattr(
        handlers,
        "fetch_entry_candles_with_meta",
        lambda *args, **kwargs: ([{"close": 1000}], {"source": "test"}),
    )
    monkeypatch.setattr(
        handlers,
        "build_entry_candle_context",
        lambda *args, **kwargs: {"schema": "test"},
    )
    monkeypatch.setattr(
        handlers,
        "_extract_ai_overlap_snapshot",
        lambda **kwargs: {},
    )
    monkeypatch.setattr(
        handlers,
        "_update_ai_quote_freshness_fields",
        lambda ws_data: None,
    )
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        handlers,
        "_has_open_pending_entry_orders",
        lambda stock: False,
    )
    monkeypatch.setattr(handlers, "COOLDOWNS", {})

    dispatcher = HotPathAIDispatcher(loaded_key_count=2)
    coordinator = ScannerAsyncEvalCoordinator(ai_dispatcher=dispatcher)
    generation = _generation(venue)
    stock = {
        "id": 7,
        "code": "005930",
        "name": "삼성전자",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_generation_id": generation.generation_id,
        "scanner_promotion_id": generation.promotion_id,
        # Promotion reference price is not evidence of an existing position.
        "buy_price": 1000,
        "buy_qty": 0,
        "effective_venue": venue,
        "venue_resolution": f"session_clock_explicit_{venue.lower()}",
        "source_signature": "VALUE_TOP",
    }
    ws_data = {
        "curr": 1001,
        "orderbook": {"ask": 1002, "bid": 1000},
        "last_ws_update_ts": time.time(),
    }
    if ws_suffix:
        ws_data["market_suffix"] = ws_suffix
    if ws_route:
        ws_data["market_route"] = ws_route
    runtime = {
        "scanner_async_eval_coordinator": coordinator,
        "scanner_async_generation": generation,
        "scanner_async_commit_phase": False,
    }
    dispatched = handlers._resolve_scanner_async_entry_ai(
        stock,
        "005930",
        ws_data,
        _FakeAI(),
        runtime,
        trigger_reason="first_call",
        last_ai_time=0,
        current_ai_score=50,
    )
    assert dispatched["status"] == "dispatched"

    deadline = time.time() + 1
    while coordinator.pending_count() and time.time() < deadline:
        coordinator.poll()
        time.sleep(0.005)
    runtime["scanner_async_commit_phase"] = True
    committed = handlers._resolve_scanner_async_entry_ai(
        stock,
        "005930",
        ws_data,
        _FakeAI(),
        runtime,
        trigger_reason="first_call",
        last_ai_time=0,
        current_ai_score=50,
    )
    coordinator.shutdown()

    assert committed["status"] == "completed"
    assert committed["ai_decision"]["action"] == "BUY"
    assert [dict(item) for item in committed["prepared_context"]["recent_ticks"]] == [
        {"price": 1000}
    ]
    assert requested_codes == [expected_request_code]
    assert "_scanner_async_cache_key" not in stock


def test_async_entry_bridge_dispatches_from_context_commit_without_sync_ai(
    monkeypatch,
):
    """A freshness COMMIT may enqueue entry AI, but must not execute it inline."""

    monkeypatch.setattr(handlers, "KIWOOM_TOKEN", "token")
    monkeypatch.setattr(
        handlers.kiwoom_utils,
        "get_tick_history_ka10003",
        lambda *_args, **_kwargs: [{"price": 1000}],
    )
    monkeypatch.setattr(
        handlers,
        "fetch_entry_candles_with_meta",
        lambda *args, **kwargs: ([{"close": 1000}], {"source": "test"}),
    )
    monkeypatch.setattr(
        handlers,
        "build_entry_candle_context",
        lambda *args, **kwargs: {"schema": "test"},
    )
    monkeypatch.setattr(handlers, "_extract_ai_overlap_snapshot", lambda **kwargs: {})
    monkeypatch.setattr(
        handlers, "_update_ai_quote_freshness_fields", lambda ws_data: None
    )
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda *args, **kwargs: None)

    class _CountingAI(_FakeAI):
        calls = 0
        thread_ids = []

        def analyze_target(self, *args, **kwargs):
            self.calls += 1
            self.thread_ids.append(threading.get_ident())
            return super().analyze_target(*args, **kwargs)

    ai = _CountingAI()
    coordinator = ScannerAsyncEvalCoordinator(
        ai_dispatcher=HotPathAIDispatcher(loaded_key_count=1)
    )
    generation = _generation("NXT")
    stock = {
        "id": 7,
        "code": "005930",
        "name": "삼성전자",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "scanner_generation_id": generation.generation_id,
        "scanner_promotion_id": generation.promotion_id,
        "effective_venue": "NXT",
        "venue_resolution": "session_clock_explicit_nxt",
        "source_signature": "VALUE_TOP",
    }
    runtime = {
        "scanner_async_eval_coordinator": coordinator,
        "scanner_async_generation": generation,
        "scanner_async_commit_phase": True,
    }
    try:
        result = handlers._resolve_scanner_async_entry_ai(
            stock,
            "005930",
            {
                "curr": 1001,
                "orderbook": {"ask": 1002, "bid": 1000},
                "last_ws_update_ts": time.time(),
            },
            ai,
            runtime,
            trigger_reason="pre_submit_commit",
            last_ai_time=0,
            current_ai_score=50,
        )

        assert result["status"] == "dispatched"
        assert all(thread_id != threading.get_ident() for thread_id in ai.thread_ids)
    finally:
        coordinator.shutdown()


def test_opening_rotation_context_prepares_off_thread_and_commits_once(monkeypatch):
    monkeypatch.setattr(handlers, "KIWOOM_TOKEN", "token")
    monkeypatch.setattr(
        handlers,
        "_resolve_opening_rotation_freshness_envelope",
        lambda *_args, **_kwargs: (
            {"curr": 1001, "last_ws_update_ts": time.time()},
            {
                "opening_rotation_freshness_envelope_ready": True,
                "market_data_effective_quote_age_ms": 100.0,
                "opening_rotation_freshness_envelope_rest_attempted": False,
            },
        ),
    )
    monkeypatch.setattr(
        handlers,
        "_fetch_opening_rotation_candles_bounded",
        lambda _code: ([{"close": 1000}], "ok"),
    )
    monkeypatch.setattr(
        handlers,
        "extract_scalping_feature_packet",
        lambda *_args, **_kwargs: {"curr": 1001, "quote_stale": False},
    )
    monkeypatch.setattr(
        handlers, "_scanner_async_quote_is_fresh", lambda *_a, **_k: True
    )
    monkeypatch.setattr(
        handlers, "_has_open_pending_entry_orders", lambda _stock: False
    )
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda *args, **kwargs: None)
    monkeypatch.setattr(handlers, "COOLDOWNS", {})

    dispatcher = HotPathAIDispatcher(loaded_key_count=1)
    coordinator = ScannerAsyncEvalCoordinator(ai_dispatcher=dispatcher)
    generation = _generation("KRX")
    stock = {
        "id": 7,
        "code": "005930",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_generation_id": generation.generation_id,
        "scanner_promotion_id": generation.promotion_id,
        "effective_venue": "KRX",
        "venue_resolution": "session_clock_explicit_krx",
        "source_signature": "VALUE_TOP",
    }
    ws_data = {"curr": 1001, "last_ws_update_ts": time.time()}
    runtime = {
        "scanner_async_eval_coordinator": coordinator,
        "scanner_async_generation": generation,
        "scanner_async_commit_phase": False,
    }

    dispatched = handlers._resolve_scanner_async_opening_rotation_context(
        stock, "005930", ws_data, runtime
    )
    assert dispatched["status"] == "dispatched"
    assert "_scanner_opening_rotation_async_cache_key" in stock

    deadline = time.time() + 1
    while coordinator.pending_count() and time.time() < deadline:
        coordinator.poll()
        time.sleep(0.005)
    runtime["scanner_async_commit_phase"] = True
    committed = handlers._resolve_scanner_async_opening_rotation_context(
        stock, "005930", ws_data, runtime
    )
    coordinator.shutdown()

    assert committed["status"] == "completed"
    assert committed["feature_packet"]["curr"] == 1001
    assert "_scanner_opening_rotation_async_cache_key" not in stock


def test_rising_missed_freshness_envelope_prepares_off_thread_then_commits(monkeypatch):
    """Rising Missed REST work must not run in the scheduler heavy callback."""

    generation = _generation("KRX")
    coordinator = ScannerAsyncEvalCoordinator(
        ai_dispatcher=HotPathAIDispatcher(loaded_key_count=1)
    )
    stock = {
        "id": 7,
        "code": "005930",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_generation_id": generation.generation_id,
        "scanner_promotion_id": generation.promotion_id,
        "effective_venue": "KRX",
        "venue_resolution": "session_clock_explicit_krx",
        "source_signature": "VALUE_TOP",
    }
    ws_data = {"curr": 1001, "last_ws_update_ts": time.time()}
    monkeypatch.setattr(
        handlers,
        "_rising_missed_quality_guard_pre_envelope",
        lambda *_args, **_kwargs: (
            {"curr": 1001, "market_data_freshness_state": "fresh"},
            {"market_data_effective_quote_age_ms": 10.0},
        ),
    )
    monkeypatch.setattr(
        handlers,
        "_merge_scanner_market_data_enrichment_into_ws_data",
        lambda _stock, data, _runtime: dict(data),
    )
    monkeypatch.setattr(
        handlers, "_scanner_async_quote_is_fresh", lambda *_a, **_k: True
    )
    monkeypatch.setattr(
        handlers,
        "_snapshot_rising_missed_same_day_reentry_guard",
        lambda *_a, **_k: {"allowed": True, "reason": "pass"},
    )
    monkeypatch.setattr(
        handlers, "_has_open_pending_entry_orders", lambda _stock: False
    )
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda *args, **kwargs: None)
    monkeypatch.setattr(handlers, "COOLDOWNS", {})
    runtime = {
        "scanner_async_eval_coordinator": coordinator,
        "scanner_async_generation": generation,
        "scanner_async_commit_phase": False,
    }

    dispatched = handlers._resolve_scanner_async_rising_missed_context(
        stock, "005930", ws_data, runtime
    )
    assert dispatched["status"] == "dispatched"
    assert stock["_scanner_async_cache_key"].startswith("rising_missed:")

    deadline = time.time() + 1
    while coordinator.pending_count() and time.time() < deadline:
        coordinator.poll()
        time.sleep(0.005)
    runtime["scanner_async_commit_phase"] = True
    committed = handlers._resolve_scanner_async_rising_missed_context(
        stock, "005930", ws_data, runtime
    )
    coordinator.shutdown()

    assert committed["status"] == "completed"
    assert stock["_rising_missed_tp1_decision_envelope_cache"]["code"] == "005930"
    reentry_context = stock["_rising_missed_async_reentry_guard_context"]
    assert reentry_context["generation_id"] == generation.generation_id
    assert reentry_context["prepared_at_epoch"] > 0
    assert reentry_context["guard"] == {"allowed": True, "reason": "pass"}
    assert "_scanner_async_cache_key" not in stock


def test_rising_missed_stale_freshness_commit_arms_bounded_recheck(monkeypatch):
    generation = _generation("KRX")
    coordinator = ScannerAsyncEvalCoordinator(
        ai_dispatcher=HotPathAIDispatcher(loaded_key_count=1)
    )
    stock = {
        "id": 7,
        "code": "005930",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_generation_id": generation.generation_id,
        "scanner_promotion_id": generation.promotion_id,
        "effective_venue": "KRX",
        "venue_resolution": "session_clock_explicit_krx",
        "source_signature": "VALUE_TOP",
    }
    ws_data = {"curr": 1001, "last_ws_update_ts": time.time()}
    logs = []
    monkeypatch.setattr(
        handlers,
        "_rising_missed_quality_guard_pre_envelope",
        lambda *_args, **_kwargs: (
            {"curr": 1001, "market_data_freshness_state": "fresh"},
            {"market_data_effective_quote_age_ms": 10.0},
        ),
    )
    monkeypatch.setattr(
        handlers,
        "_merge_scanner_market_data_enrichment_into_ws_data",
        lambda _stock, data, _runtime: dict(data),
    )
    monkeypatch.setattr(
        handlers,
        "_snapshot_rising_missed_same_day_reentry_guard",
        lambda *_a, **_k: {"allowed": True, "reason": "pass"},
    )
    monkeypatch.setattr(
        handlers, "_has_open_pending_entry_orders", lambda _stock: False
    )
    monkeypatch.setattr(
        handlers,
        "_log_entry_pipeline",
        lambda _stock, _code, stage, **fields: logs.append((stage, fields)),
    )
    monkeypatch.setattr(handlers, "COOLDOWNS", {})
    runtime = {
        "scanner_async_eval_coordinator": coordinator,
        "scanner_async_generation": generation,
        "scanner_async_commit_phase": False,
    }

    dispatched = handlers._resolve_scanner_async_rising_missed_context(
        stock, "005930", ws_data, runtime
    )
    assert dispatched["status"] == "dispatched"

    deadline = time.time() + 1
    while coordinator.pending_count() and time.time() < deadline:
        coordinator.poll()
        time.sleep(0.005)
    monkeypatch.setattr(
        handlers, "_scanner_async_quote_is_fresh", lambda *_a, **_k: False
    )
    runtime["scanner_async_commit_phase"] = True
    committed = handlers._resolve_scanner_async_rising_missed_context(
        stock, "005930", ws_data, runtime
    )
    coordinator.shutdown()

    assert committed == {
        "status": "commit_rejected",
        "reason": "quote_stale_or_missing",
    }
    assert (
        handlers._scanner_active_rising_recheck_reason(stock)
        == "freshness_envelope_recheck_pending"
    )
    assert (
        handlers._scanner_active_full_eval_budget_source(stock)
        == "freshness_envelope_recheck"
    )
    assert logs[-1][0] == "rising_missed_async_freshness_commit"
    assert logs[-1][1]["rising_missed_freshness_envelope_recheck_enqueued"] is True
    assert logs[-1][1]["decision_authority"] == "scanner_main_thread_commit_guard"
    assert logs[-1][1]["actual_order_submitted"] is False
    assert logs[-1][1]["broker_order_forbidden"] is True


def test_rising_missed_async_final_commit_avoids_generic_reentry_history(monkeypatch):
    generation = _generation("KRX")
    stock = {
        "id": 7,
        "code": "005930",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_generation_id": generation.generation_id,
        "_scanner_async_generation_id": generation.generation_id,
        "_scanner_async_cache_key": "rising_missed:test",
        "_rising_missed_async_reentry_guard_context": {
            "generation_id": generation.generation_id,
            "prepared_at_epoch": time.time(),
            "guard": {"allowed": True, "reason": "pass"},
        },
    }
    monkeypatch.setattr(
        handlers, "_manual_control_exclusion_blocked", lambda *_a, **_k: False
    )
    monkeypatch.setattr(handlers, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(handlers, "is_scalping_buy_time_allowed", lambda _time: True)
    monkeypatch.setattr(handlers, "COOLDOWNS", {})
    monkeypatch.setattr(handlers, "ALERTED_STOCKS", set())
    monkeypatch.setattr(
        handlers, "_has_open_pending_entry_orders", lambda _stock: False
    )
    monkeypatch.setattr(
        handlers,
        "evaluate_rising_missed_same_day_reentry_guard",
        lambda *_a, **_k: (_ for _ in ()).throw(
            AssertionError("final commit must use worker-prepared reentry context")
        ),
    )
    called = []

    def _rising_submit(_stock, _code, _ws, _admin_id, runtime, **_kwargs):
        called.append(runtime)
        return True

    monkeypatch.setattr(
        handlers, "_maybe_submit_rising_missed_one_share_entry", _rising_submit
    )

    assert handlers.handle_scanner_async_rising_missed_commit(
        stock,
        "005930",
        {"curr": 1001, "last_ws_update_ts": time.time()},
        admin_id=1,
        now_ts=time.time(),
        now_dt=datetime.now(),
        scanner_async_generation=generation,
    )
    assert len(called) == 1
    assert called[0]["scanner_async_commit_phase"] is True
    assert called[0]["rising_missed_async_final_commit"] is True


def test_rising_missed_async_commit_is_handled_when_ai_dispatch_is_pending(
    monkeypatch,
):
    generation = _generation("NXT")
    stock = {
        "id": 7,
        "code": "005930",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_generation_id": generation.generation_id,
        "_scanner_async_generation_id": generation.generation_id,
        "_scanner_async_cache_key": "rising_missed:test",
    }
    monkeypatch.setattr(
        handlers, "_manual_control_exclusion_blocked", lambda *_a, **_k: False
    )
    monkeypatch.setattr(handlers, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(handlers, "is_scalping_buy_time_allowed", lambda _time: True)
    monkeypatch.setattr(handlers, "COOLDOWNS", {})
    monkeypatch.setattr(handlers, "ALERTED_STOCKS", set())
    monkeypatch.setattr(
        handlers, "_has_open_pending_entry_orders", lambda _stock: False
    )
    calls = []

    def _dispatch_only(_stock, _code, _ws, _admin_id, runtime, **_kwargs):
        calls.append(runtime)
        return False

    monkeypatch.setattr(
        handlers, "_maybe_submit_rising_missed_one_share_entry", _dispatch_only
    )

    handled = handlers.handle_scanner_async_rising_missed_commit(
        stock,
        "005930",
        {"curr": 1001, "last_ws_update_ts": time.time()},
        admin_id=1,
        now_ts=time.time(),
        now_dt=datetime.now(),
        scanner_async_generation=generation,
    )

    assert handled is True
    assert len(calls) == 1
    assert calls[0]["scanner_async_commit_phase"] is True


def test_rising_missed_freshness_commit_dispatches_entry_ai_before_submit(
    monkeypatch,
):
    generation = _generation("KRX")
    coordinator = ScannerAsyncEvalCoordinator(
        ai_dispatcher=HotPathAIDispatcher(loaded_key_count=1)
    )
    logs = []
    monkeypatch.setenv(
        "KORSTOCKSCAN_RISING_MISSED_ONE_SHARE_ENTRY_ENABLED",
        "true",
    )
    monkeypatch.setattr(
        handlers,
        "evaluate_rising_missed_one_share_entry",
        lambda *args, **kwargs: type(
            "Decision",
            (),
            {"allowed": True, "reason": "allowed", "log_fields": {}},
        )(),
    )
    monkeypatch.setattr(
        handlers,
        "_resolve_scanner_async_rising_missed_context",
        lambda *args, **kwargs: {"status": "completed"},
    )
    monkeypatch.setattr(
        handlers,
        "_maybe_retry_rising_missed_entry_ai_not_evaluated",
        lambda *args, **kwargs: {
            "rising_missed_entry_ai_retry_attempted": True,
            "rising_missed_entry_ai_retry_success": False,
            "rising_missed_entry_ai_retry_reason": "async_pending",
            "rising_missed_entry_ai_retry_async_status": "dispatched",
        },
    )
    monkeypatch.setattr(
        handlers,
        "_submit_watching_triggered_entry",
        lambda *args, **kwargs: (_ for _ in ()).throw(
            AssertionError("freshness COMMIT must not submit before entry AI COMMIT")
        ),
    )
    monkeypatch.setattr(
        handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )
    stock = {
        "id": 7,
        "code": "005930",
        "name": "삼성전자",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "rising_missed_buy": True,
        "price_delta_since_first_seen_pct": 2.0,
        "scanner_generation_id": generation.generation_id,
    }

    handled = handlers._maybe_submit_rising_missed_one_share_entry(
        stock,
        "005930",
        {"curr": 70000, "v_pw": 120.0},
        admin_id=1,
        runtime={
            "now_ts": time.time(),
            "rising_missed_async_final_commit": True,
            "scanner_async_eval_coordinator": coordinator,
            "scanner_async_generation": generation,
        },
        strategy="SCALPING",
        pos_tag="SCANNER",
        curr_price=70000,
    )
    coordinator.shutdown()

    assert handled is True
    assert logs[-1][0] == "rising_missed_async_commit_phase"
    assert logs[-1][1]["phase"] == "entry_ai_dispatch_pending"
    assert logs[-1][1]["actual_order_submitted"] is False


def test_rising_missed_context_does_not_claim_followup_generic_ai_commit(monkeypatch):
    generation = _generation("KRX")
    coordinator = ScannerAsyncEvalCoordinator(
        ai_dispatcher=HotPathAIDispatcher(loaded_key_count=1)
    )
    stock = {
        "id": 7,
        "code": "005930",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_generation_id": generation.generation_id,
        "_scanner_async_generation_id": generation.generation_id,
        "_scanner_async_cache_key": "watching:entry-ai-result",
    }
    monkeypatch.setattr(handlers, "_log_entry_pipeline", lambda *args, **kwargs: None)
    runtime = {
        "scanner_async_eval_coordinator": coordinator,
        "scanner_async_generation": generation,
        "scanner_async_commit_phase": True,
    }
    try:
        assert handlers._resolve_scanner_async_rising_missed_context(
            stock,
            "005930",
            {"curr": 1001, "last_ws_update_ts": time.time()},
            runtime,
        ) == {"status": "not_applicable"}
    finally:
        coordinator.shutdown()


def test_rising_missed_context_does_not_overwrite_pending_entry_ai(monkeypatch):
    generation = _generation("NXT")
    coordinator = ScannerAsyncEvalCoordinator(
        ai_dispatcher=HotPathAIDispatcher(loaded_key_count=1)
    )
    stock = {
        "strategy": "SCALPING",
        "scanner_generation_id": generation.generation_id,
        "_scanner_async_generation_id": generation.generation_id,
        "_scanner_async_cache_key": "watching:entry-ai-pending",
    }
    runtime = {
        "scanner_async_eval_coordinator": coordinator,
        "scanner_async_generation": generation,
        "scanner_async_commit_phase": False,
    }
    try:
        result = handlers._resolve_scanner_async_rising_missed_context(
            stock,
            "005930",
            {"curr": 1001, "last_ws_update_ts": time.time()},
            runtime,
        )
    finally:
        coordinator.shutdown()

    assert result == {
        "status": "pending_other_async",
        "reason": "entry_ai_pending_for_generation",
    }
    assert stock["_scanner_async_cache_key"] == "watching:entry-ai-pending"


def test_opening_rotation_async_commit_avoids_generic_watching_reentry(monkeypatch):
    generation = _generation("KRX")
    stock = {
        "id": 7,
        "code": "005930",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_generation_id": generation.generation_id,
        "_scanner_opening_rotation_async_generation_id": generation.generation_id,
        "_scanner_opening_rotation_async_cache_key": "opening_rotation:test",
    }
    monkeypatch.setattr(
        handlers, "_manual_control_exclusion_blocked", lambda *_a, **_k: False
    )
    monkeypatch.setattr(handlers, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(handlers, "is_scalping_buy_time_allowed", lambda _value: True)
    monkeypatch.setattr(
        handlers,
        "evaluate_scalp_same_symbol_loss_reentry_guard",
        lambda *_a, **_k: (_ for _ in ()).throw(
            AssertionError("commit must not hydrate re-entry history")
        ),
    )
    monkeypatch.setattr(handlers, "COOLDOWNS", {})
    monkeypatch.setattr(handlers, "ALERTED_STOCKS", set())
    opened = []

    def _opening_handler(_stock, _code, _ws_data, runtime, _config):
        opened.append(runtime)
        runtime["is_trigger"] = True
        runtime["opening_rotation_1pct_live"] = True
        return True

    submitted = []
    monkeypatch.setattr(handlers, "_handle_watching_opening_rotation", _opening_handler)
    monkeypatch.setattr(
        handlers,
        "_submit_watching_triggered_entry",
        lambda *args: submitted.append(args),
    )

    assert handlers.handle_scanner_async_opening_rotation_commit(
        stock,
        "005930",
        {"curr": 1001},
        admin_id=1,
        now_ts=time.time(),
        now_dt=datetime.now(),
        scanner_async_generation=generation,
    )
    assert len(opened) == 1
    assert len(submitted) == 1
    assert submitted[0][4]["scanner_async_commit_phase"] is True


def test_opening_rotation_async_commit_does_not_claim_generic_result(monkeypatch):
    generation = _generation("KRX")
    stock = {
        "strategy": "SCALPING",
        "_scanner_opening_rotation_async_generation_id": generation.generation_id,
        "_scanner_opening_rotation_async_cache_key": "opening_rotation:test",
        "_scanner_async_cache_key": "watching:test",
    }
    monkeypatch.setattr(
        handlers,
        "_handle_watching_opening_rotation",
        lambda *_a, **_k: (_ for _ in ()).throw(AssertionError("must not run")),
    )

    assert not handlers.handle_scanner_async_opening_rotation_commit(
        stock,
        "005930",
        {"curr": 1001},
        admin_id=1,
        now_ts=time.time(),
        now_dt=datetime.now(),
        scanner_async_generation=generation,
    )


def test_opening_rotation_async_commit_consumes_strategy_miss_without_ai_handoff(
    monkeypatch,
):
    generation = _generation("KRX")
    stock = {
        "strategy": "SCALPING",
        "_scanner_opening_rotation_async_generation_id": generation.generation_id,
        "_scanner_opening_rotation_async_cache_key": "opening_rotation:test",
    }
    monkeypatch.setattr(
        handlers, "_manual_control_exclusion_blocked", lambda *_a, **_k: False
    )
    monkeypatch.setattr(handlers, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(handlers, "is_scalping_buy_time_allowed", lambda _value: True)
    monkeypatch.setattr(handlers, "COOLDOWNS", {})
    monkeypatch.setattr(handlers, "ALERTED_STOCKS", set())

    def _opening_handler(_stock, _code, _ws_data, runtime, _config):
        runtime.update(
            {
                "opening_rotation_entry_owner_handoff": True,
                "opening_rotation_entry_owner_handoff_reason": (
                    "pullback_not_observed"
                ),
                "opening_rotation_entry_owner_handoff_target": (
                    "general_scalping_ai_entry"
                ),
            }
        )
        return False

    monkeypatch.setattr(handlers, "_handle_watching_opening_rotation", _opening_handler)

    assert handlers.handle_scanner_async_opening_rotation_commit(
        stock,
        "005930",
        {"curr": 1001},
        admin_id=1,
        now_ts=time.time(),
        now_dt=datetime.now(),
        scanner_async_generation=generation,
    )
    assert "_opening_rotation_general_entry_handoff_once_generation_id" not in stock


def test_opening_rotation_async_commit_does_not_handoff_unmarked_false_result(
    monkeypatch,
):
    generation = _generation("KRX")
    stock = {
        "strategy": "SCALPING",
        "_scanner_opening_rotation_async_generation_id": generation.generation_id,
        "_scanner_opening_rotation_async_cache_key": "opening_rotation:test",
    }
    monkeypatch.setattr(
        handlers, "_manual_control_exclusion_blocked", lambda *_a, **_k: False
    )
    monkeypatch.setattr(handlers, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(handlers, "is_scalping_buy_time_allowed", lambda _value: True)
    monkeypatch.setattr(handlers, "COOLDOWNS", {})
    monkeypatch.setattr(handlers, "ALERTED_STOCKS", set())
    monkeypatch.setattr(
        handlers,
        "_handle_watching_opening_rotation",
        lambda *_a, **_k: False,
    )

    assert handlers.handle_scanner_async_opening_rotation_commit(
        stock,
        "005930",
        {"curr": 1001},
        admin_id=1,
        now_ts=time.time(),
        now_dt=datetime.now(),
        scanner_async_generation=generation,
    )
    assert "_opening_rotation_general_entry_handoff_once_generation_id" not in stock


def test_opening_rotation_legacy_handoff_marker_has_no_runtime_authority(
    monkeypatch,
):
    generation = _generation("KRX")
    stock = {
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "_opening_rotation_general_entry_handoff_once_generation_id": (
            generation.generation_id
        ),
        "opening_rotation_entry_owner_handoff_reason": "pullback_not_observed",
    }
    runtime = {
        "pos_tag": "SCANNER",
        "now_ts": time.time(),
        "now_dt": datetime.now(),
        "scanner_async_generation": generation,
    }
    monkeypatch.setattr(
        handlers,
        "_resolve_scanner_async_opening_rotation_context",
        lambda *_a, **_k: (_ for _ in ()).throw(
            AssertionError("same generation must not re-evaluate opening rotation")
        ),
    )

    assert not handlers._handle_watching_opening_rotation(
        stock,
        "005930",
        {"curr": 1001},
        runtime,
        {"MIN_SCALP_LIQUIDITY": 500_000_000},
    )
    assert "_opening_rotation_general_entry_handoff_once_generation_id" not in stock
    assert "opening_rotation_entry_owner_handoff" not in runtime
    assert not handlers._handle_watching_opening_rotation(
        stock,
        "005930",
        {"curr": 1002},
        runtime,
        {"MIN_SCALP_LIQUIDITY": 500_000_000},
    )
    assert "_opening_rotation_general_entry_handoff_once_generation_id" not in stock
    assert "opening_rotation_entry_owner_handoff" not in runtime


def test_opening_rotation_handoff_marker_clears_for_new_generation(monkeypatch):
    prior_generation = _generation("KRX")
    next_generation = replace(
        prior_generation,
        revision=prior_generation.revision + 1,
    )
    stock = {
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "_opening_rotation_general_entry_handoff_once_generation_id": (
            prior_generation.generation_id
        ),
        "opening_rotation_entry_owner_handoff_reason": "pullback_not_observed",
    }
    runtime = {
        "pos_tag": "SCANNER",
        "now_ts": time.time(),
        "now_dt": datetime.now(),
        "scanner_async_generation": next_generation,
    }
    monkeypatch.setattr(
        handlers,
        "_resolve_scanner_async_opening_rotation_context",
        lambda *_a, **_k: {
            "status": "blocked",
            "reason": "async_context_commit_rejected",
        },
    )

    handlers._handle_watching_opening_rotation(
        stock,
        "005930",
        {"curr": 1001},
        runtime,
        {"MIN_SCALP_LIQUIDITY": 500_000_000},
    )
    assert "_opening_rotation_general_entry_handoff_once_generation_id" not in stock


def test_async_opening_rotation_defers_reentry_hydration_until_submit(monkeypatch):
    generation = _generation("KRX")
    coordinator = ScannerAsyncEvalCoordinator(
        ai_dispatcher=HotPathAIDispatcher(loaded_key_count=1)
    )
    stock = {
        "id": 7,
        "code": "005930",
        "name": "삼성전자",
        "status": "WATCHING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "source_signature": "VALUE_TOP",
        "scanner_promotion_id": "PROMO-ASYNC-OPENING",
        "opening_rotation_watch_slot_promotion_id": "PROMO-ASYNC-OPENING",
    }
    monkeypatch.setattr(
        handlers, "_observe_entry_cancel_wait_counterfactuals", lambda *a, **k: None
    )
    monkeypatch.setattr(handlers, "_log_watching_state_debug", lambda *a, **k: None)
    monkeypatch.setattr(
        handlers, "_manual_control_exclusion_blocked", lambda *a, **k: False
    )
    monkeypatch.setattr(handlers, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(handlers, "is_scalping_buy_time_allowed", lambda _value: True)
    monkeypatch.setattr(
        handlers,
        "_opening_rotation_yields_to_rising_missed_owner",
        lambda *a, **k: False,
    )
    monkeypatch.setattr(
        handlers, "is_opening_rotation_watch_candidate", lambda **_k: True
    )
    monkeypatch.setattr(
        handlers,
        "evaluate_scalp_same_symbol_loss_reentry_guard",
        lambda *_a, **_k: (_ for _ in ()).throw(
            AssertionError("async Opening Rotation must defer historical hydration")
        ),
    )
    monkeypatch.setattr(
        handlers, "_handle_watching_strategy_branch", lambda *a, **k: False
    )

    try:
        handlers.handle_watching_state(
            stock,
            "005930",
            {"curr": 1001, "fluctuation": 1.0},
            admin_id=1,
            now_ts=time.time(),
            now_dt=datetime.now(),
            scanner_async_eval_coordinator=coordinator,
            scanner_async_generation=generation,
        )
    finally:
        coordinator.shutdown()


def test_scanner_entry_events_inherit_registered_canonical_venue(monkeypatch):
    emitted = []
    monkeypatch.setattr(
        handlers, "_remember_scanner_terminal_block", lambda *a, **k: None
    )
    monkeypatch.setattr(
        handlers,
        "emit_pipeline_event",
        lambda _pipeline, _name, _code, _stage, **kwargs: emitted.append(kwargs),
    )
    monkeypatch.setattr(
        handlers,
        "_maybe_register_rising_missed_nxt_downstream_block_sampler",
        lambda *a, **k: None,
    )
    stock = {
        "id": 7,
        "name": "삼성전자",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "scanner_promotion_id": "PROMO-KRX",
        "effective_venue": "KRX",
        "venue": "KRX",
        "venue_resolution": "consistent_explicit:payload.effective_venue",
        "market_session_bucket": "krx_regular",
    }

    handlers._log_entry_pipeline(stock, "005930", "opening_rotation_1pct_observed")

    assert emitted[-1]["fields"]["effective_venue"] == "KRX"
    assert emitted[-1]["fields"]["venue"] == "KRX"
    assert (
        emitted[-1]["fields"]["venue_resolution"]
        == "consistent_explicit:payload.effective_venue"
    )
