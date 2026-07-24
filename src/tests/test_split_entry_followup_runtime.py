from datetime import datetime
from types import SimpleNamespace
import threading

import pytest

import src.engine.sniper_execution_receipts as receipts
import src.engine.sniper_state_handlers as state_handlers
import src.engine.sniper_sync as sniper_sync
from src.engine.scalping import entry_split_order_plan as split_plan
from src.utils.threshold_cycle_registry import threshold_family_for_stage


def test_emit_split_entry_followup_shadows_is_off_by_default(monkeypatch):
    logged = []
    monkeypatch.setattr(
        receipts,
        "_log_holding_pipeline",
        lambda *args, **kwargs: logged.append((args, kwargs)),
    )

    target_stock = {"name": "테스트A"}

    receipts._emit_split_entry_followup_shadows(
        target_stock=target_stock,
        code="123456",
        target_id=1,
        now=datetime(2026, 4, 17, 12, 0, 0),
        entry_mode="fallback",
        fill_quality="PARTIAL_FILL",
        requested_entry_qty=9,
        cum_filled_qty=1,
        remaining_qty=8,
        new_qty=1,
    )

    assert logged == []


def test_emit_split_entry_followup_shadows_logs_integrity_and_recheck_when_enabled(
    monkeypatch,
):
    logged = []
    monkeypatch.setattr(
        receipts,
        "_log_holding_pipeline",
        lambda *args, **kwargs: logged.append((args, kwargs)),
    )
    monkeypatch.setattr(
        receipts,
        "TRADING_RULES",
        SimpleNamespace(
            SPLIT_ENTRY_REBASE_INTEGRITY_SHADOW_ENABLED=True,
            SPLIT_ENTRY_IMMEDIATE_RECHECK_SHADOW_ENABLED=True,
            SPLIT_ENTRY_IMMEDIATE_RECHECK_SHADOW_WINDOW_SEC=90,
        ),
    )

    target_stock = {"name": "테스트A"}

    receipts._emit_split_entry_followup_shadows(
        target_stock=target_stock,
        code="123456",
        target_id=1,
        now=datetime(2026, 4, 17, 12, 0, 0),
        entry_mode="fallback",
        fill_quality="PARTIAL_FILL",
        requested_entry_qty=9,
        cum_filled_qty=1,
        remaining_qty=8,
        new_qty=1,
    )
    receipts._emit_split_entry_followup_shadows(
        target_stock=target_stock,
        code="123456",
        target_id=1,
        now=datetime(2026, 4, 17, 12, 0, 0),
        entry_mode="fallback",
        fill_quality="FULL_FILL",
        requested_entry_qty=9,
        cum_filled_qty=12,
        remaining_qty=0,
        new_qty=12,
    )

    stages = [args[3] for args, _ in logged]
    assert stages == [
        "split_entry_rebase_integrity_shadow",
        "split_entry_rebase_integrity_shadow",
        "split_entry_immediate_recheck_shadow",
    ]
    integrity_kwargs = logged[1][1]
    assert (
        integrity_kwargs["integrity_flags"] == "cum_gt_requested,same_ts_multi_rebase"
    )
    assert integrity_kwargs["rebase_count"] == 2
    recheck_kwargs = logged[2][1]
    assert recheck_kwargs["trigger_reason"] == "partial_then_expand"
    assert recheck_kwargs["first_partial_qty"] == 1


def test_clear_split_entry_shadow_state_removes_runtime_keys():
    target_stock = {
        "_split_entry_rebase_shadow_count": 2,
        "_split_entry_rebase_shadow_last_second": "2026-04-17T12:00:00",
        "_split_entry_rebase_shadow_same_second_count": 2,
        "_split_entry_first_partial_qty": 1,
        "_split_entry_last_immediate_recheck_rebase_count": 2,
        "name": "테스트B",
    }

    receipts._clear_split_entry_shadow_state(target_stock)

    assert target_stock == {"name": "테스트B"}


def test_completed_sell_closes_persisted_probe_bundle(monkeypatch, tmp_path):
    class _NoopThread:
        def __init__(self, *args, **kwargs):
            pass

        def start(self):
            return None

    monkeypatch.setattr(receipts.threading, "Thread", _NoopThread)
    monkeypatch.setattr(
        split_plan,
        "PROBE_RUNTIME_STATE_PATH",
        tmp_path / "entry_split_probe_runtime_state.json",
    )
    receipts.highest_prices = {"123456": 10100}
    split_plan.update_probe_runtime_bundle(
        "123456-probe-sold",
        phase="aborted",
        code="123456",
        target_id=7,
        requested_qty=5,
        filled_qty=1,
    )
    stock = {
        "id": 7,
        "code": "123456",
        "name": "PROBE",
        "status": "HOLDING",
        "buy_qty": 1,
        "buy_price": 10000,
        "entry_split_probe_phase": "aborted",
        "entry_split_probe_exit_bundle_id": "123456-probe-sold",
        "entry_split_probe_scale_in_forbidden": True,
        "entry_split_probe_recheck_due_at": 123.0,
        "entry_split_probe_recheck_count": 2,
        "entry_split_probe_deferred_once": True,
        "entry_split_probe_direction_state": "UNKNOWN",
        "entry_split_probe_continuation_action": "DEFER",
        "entry_split_probe_offset_profile": "recovered_wide",
        "entry_split_probe_nxt_wait_fast_tape_bounded_single_leg": True,
        "entry_split_probe_bounded_partial_submission": True,
        "rising_missed_scout_upgraded": True,
    }

    receipts._finalize_standard_sell_execution(
        target_id=7,
        exec_price=9900,
        now=datetime(2026, 7, 20, 18, 0, 0),
        target_stock=stock,
        strategy="SCALPING",
        is_scalp_revive=False,
        code="123456",
    )

    state = split_plan._load_json(split_plan.PROBE_RUNTIME_STATE_PATH)
    persisted = state["bundles"]["123456-probe-sold"]
    assert persisted["phase"] == "complete"
    assert persisted["close_reason"] == "position_sell_completed"
    assert "entry_split_probe_exit_bundle_id" not in stock
    assert "entry_split_probe_recheck_due_at" not in stock
    assert "entry_split_probe_direction_state" not in stock
    assert "entry_split_probe_offset_profile" not in stock
    assert "entry_split_probe_nxt_wait_fast_tape_bounded_single_leg" not in stock
    assert "entry_split_probe_bounded_partial_submission" not in stock
    assert "rising_missed_scout_upgraded" not in stock


def test_probe_hard_guard_abort_records_hard_negative(monkeypatch):
    monkeypatch.setattr(
        state_handlers, "_log_entry_pipeline", lambda *args, **kwargs: None
    )
    stock = {
        "entry_filled_qty": 1,
        "entry_split_probe_phase": "probe_filled",
    }

    state_handlers._abort_entry_split_probe_residual(
        stock,
        "123456",
        "stale_or_conflicted_fresh_quote",
        preserve_position=True,
    )

    assert stock["entry_split_probe_phase"] == "aborted"
    assert stock["entry_split_probe_direction_state"] == "HARD_NEGATIVE"
    assert stock["entry_split_probe_continuation_action"] == "HARD_NEGATIVE"
    assert stock["entry_split_probe_scale_in_forbidden"] is True


def test_post_probe_observation_contract_uses_existing_resolver_family(monkeypatch):
    monkeypatch.setenv(
        "KORSTOCKSCAN_DYNAMIC_ENTRY_PRICE_RESOLVER_POST_PROBE_ENABLED", "true"
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED", "true")

    fields = state_handlers._entry_split_probe_observation_contract_fields(
        {
            "entry_execution_cohort": "PREMARKET_KRX_LIKE",
            "market_session_bucket": "krx_like_premarket",
        }
    )

    assert fields["metric_role"] == "real_execution_quality"
    assert fields["decision_authority"] == "dynamic_entry_price_resolver_p1_post_probe"
    assert fields["window_policy"] == "same_day_probe_fill_ttl"
    assert fields["allowed_runtime_apply"] is False
    assert fields["effective_venue"] == "PREMARKET_KRX_LIKE"
    assert fields["market_session_bucket"] == "krx_like_premarket"
    assert {
        threshold_family_for_stage(stage)
        for stage in (
            "probe_continuation_deferred",
            "residual_planned",
            "residual_submitted",
            "residual_blocked",
        )
    } == {"dynamic_entry_price_resolver"}


def test_probe_receipt_marks_fill_once_and_schedules_residual(monkeypatch, tmp_path):
    scheduled = []
    monkeypatch.setenv(
        "KORSTOCKSCAN_DYNAMIC_ENTRY_PRICE_RESOLVER_POST_PROBE_ENABLED", "true"
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED", "true")

    class _ImmediateThread:
        def __init__(self, *, target, args, **kwargs):
            self.target = target
            self.args = args

        def start(self):
            self.target(*self.args)

    events = []
    monkeypatch.setattr(receipts.threading, "Thread", _ImmediateThread)
    monkeypatch.setattr(
        receipts,
        "_probe_fill_continuation_callback",
        lambda stock, code: scheduled.append((stock, code)),
    )
    monkeypatch.setattr(
        receipts,
        "_log_holding_pipeline",
        lambda name, code, target_id, stage, **fields: events.append((stage, fields)),
    )
    monkeypatch.setattr(
        receipts, "_refresh_scalp_preset_exit_order", lambda *args, **kwargs: True
    )
    monkeypatch.setattr(
        split_plan,
        "PROBE_RUNTIME_STATE_PATH",
        tmp_path / "entry_split_probe_runtime_state.json",
    )
    receipts.highest_prices = {}

    stock = {
        "id": 1,
        "name": "PROBE",
        "code": "123456",
        "status": "BUY_ORDERED",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "entry_requested_qty": 10,
        "requested_buy_qty": 10,
        "entry_filled_qty": 0,
        "entry_fill_amount": 0,
        "entry_split_probe_phase": "probe_submitted",
        "entry_split_probe_bundle_id": "123456-probe-test",
        "entry_split_probe_order_no": "P0",
        "entry_split_probe_submit_best_ask": 10000,
        "entry_split_probe_submitted_at": 1.0,
        "entry_execution_cohort": "KRX",
        "market_session_bucket": "krx_regular",
        "pending_entry_orders": [
            {
                "tag": "entry_split_probe_0",
                "ord_no": "P0",
                "qty": 1,
                "filled_qty": 0,
                "price": 0,
                "status": "OPEN",
            }
        ],
    }

    receipts._handle_entry_buy_execution(
        target_id=1,
        target_stock=stock,
        code="123456",
        order_no="P0",
        exec_price=10010,
        exec_qty=1,
        now=datetime(2026, 7, 20, 10, 0, 0),
    )
    receipts._handle_entry_buy_execution(
        target_id=1,
        target_stock=stock,
        code="123456",
        order_no="P0",
        exec_price=10010,
        exec_qty=1,
        now=datetime(2026, 7, 20, 10, 0, 1),
    )

    assert stock["buy_qty"] == 1
    assert stock["entry_filled_qty"] == 1
    assert stock["entry_split_probe_phase"] == "probe_filled"
    assert stock["entry_split_probe_fill_price"] == 10010
    assert stock["entry_split_probe_scale_in_forbidden"] is True
    assert stock["probe_expand_forbidden"] is False
    assert [stage for stage, _ in events].count("probe_filled") == 1
    probe_fields = next(fields for stage, fields in events if stage == "probe_filled")
    assert probe_fields["effective_venue"] == "KRX"
    assert probe_fields["market_session_bucket"] == "krx_regular"
    assert (
        probe_fields["decision_authority"]
        == "dynamic_entry_price_resolver_p1_post_probe"
    )
    assert scheduled == [(stock, "123456")]
    runtime_state = split_plan._load_json(split_plan.PROBE_RUNTIME_STATE_PATH)
    persisted = runtime_state["bundles"]["123456-probe-test"]
    assert persisted["phase"] == "probe_filled"
    assert persisted["entry_split_probe_scale_in_forbidden"] is True
    assert persisted["probe_expand_forbidden"] is False


def test_probe_bundle_completion_rebaselines_peak_before_fast_monitor(monkeypatch):
    class _NoopThread:
        def __init__(self, *args, **kwargs):
            pass

        def start(self):
            pass

    monkeypatch.setattr(receipts.threading, "Thread", _NoopThread)
    monkeypatch.setattr(receipts, "_log_holding_pipeline", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        receipts, "_refresh_scalp_preset_exit_order", lambda *args, **kwargs: True
    )
    monkeypatch.setattr(
        receipts, "update_probe_runtime_bundle", lambda *args, **kwargs: None
    )
    receipts.highest_prices = {"123456": 10_200}
    stock = {
        "id": 1,
        "name": "PROBE",
        "code": "123456",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "buy_qty": 1,
        "buy_price": 10_010,
        "entry_requested_qty": 3,
        "requested_buy_qty": 3,
        "entry_filled_qty": 1,
        "entry_fill_amount": 10_010,
        "entry_split_probe_phase": "residual_submitted",
        "entry_split_probe_bundle_id": "123456-probe-complete",
        "pending_entry_orders": [
            {
                "tag": "entry_split_probe_residual_0",
                "ord_no": "R1",
                "qty": 2,
                "filled_qty": 0,
                "price": 10_000,
                "status": "OPEN",
            }
        ],
    }

    receipts._handle_entry_buy_execution(
        target_id=1,
        target_stock=stock,
        code="123456",
        order_no="R1",
        exec_price=10_000,
        exec_qty=2,
        now=datetime(2026, 7, 23, 10, 0, 0),
    )

    assert stock["entry_split_probe_phase"] == "complete"
    assert stock["peak_rebaseline_pending"] is False
    assert stock["peak_basis_qty"] == 3
    assert stock["peak_basis_avg_price"] == pytest.approx(10_003.3333, abs=0.0001)
    assert receipts.highest_prices["123456"] == pytest.approx(10_003.3333)


def test_probe_fill_callback_uses_fresh_ws_and_submits_immediately(monkeypatch):
    now_ts = 1_774_150_400.0
    stock = {"name": "PROBE", "entry_split_probe_phase": "probe_filled"}
    observed = []
    monkeypatch.setattr(
        state_handlers,
        "WS_MANAGER",
        SimpleNamespace(get_latest_data=lambda code: {"curr": 10010, "code": code}),
    )
    monkeypatch.setattr(state_handlers.time, "time", lambda: now_ts)
    monkeypatch.setattr(
        state_handlers,
        "_maybe_submit_entry_split_probe_residual",
        lambda target, code, ws_data, **kwargs: observed.append(
            (target, code, ws_data, kwargs)
        )
        or True,
    )

    assert state_handlers.submit_entry_split_probe_residual_after_fill(stock, "123456")
    assert observed[0][0:3] == (stock, "123456", {"curr": 10010, "code": "123456"})
    assert observed[0][3]["now_ts"] == now_ts


@pytest.mark.parametrize("rising_missed", [False, True])
def test_probe_residual_submits_once_after_fresh_fill_revalidation(
    monkeypatch, tmp_path, rising_missed
):
    now_ts = 1_774_150_400.0
    sent = []
    events = []
    monkeypatch.setattr(
        split_plan,
        "PROBE_RUNTIME_STATE_PATH",
        tmp_path / "entry_split_probe_runtime_state.json",
    )
    monkeypatch.setattr(state_handlers, "COOLDOWNS", {})
    monkeypatch.setattr(state_handlers, "KIWOOM_TOKEN", "token")
    monkeypatch.setattr(state_handlers, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(
        state_handlers, "is_scalping_buy_time_allowed", lambda _now: True
    )
    monkeypatch.setattr(
        state_handlers, "_has_active_sell_order_pending", lambda _stock: False
    )
    monkeypatch.setattr(
        state_handlers, "_has_open_pending_entry_orders", lambda _stock: False
    )
    monkeypatch.setattr(
        state_handlers,
        "_build_quote_consistency_fields",
        lambda *args, **kwargs: (
            {
                "quote_consistency_state": "ok",
                "quote_consistency_reason": "ws_only_fresh",
                "passive_buy_price": 10000,
            },
            10010,
            10020,
            10000,
        ),
    )
    monkeypatch.setattr(
        state_handlers,
        "_split_policy_pre_submit_price_guard_fields",
        lambda *args, **kwargs: {"pre_submit_price_guard_blocked": False},
    )
    monkeypatch.setattr(
        state_handlers,
        "_probe_residual_account_guard_fields",
        lambda *args, **kwargs: {
            "account_guard_allowed": True,
            "account_guard_reason": "probe_residual_account_guard_passed",
        },
    )
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "describe_buy_order_resolution",
        lambda *args, **kwargs: {
            "requested_order_type": "00",
            "effective_order_type": "00",
            "effective_dmst_stex_tp": "SOR",
            "order_type_remapped": False,
            "order_type_remap_reason": "",
        },
    )

    def _send(_code, qty, price, *_args, **_kwargs):
        order_no = f"R{len(sent) + 1}"
        sent.append((order_no, qty, price))
        return {"return_code": "0", "ord_no": order_no}

    monkeypatch.setattr(state_handlers.kiwoom_orders, "send_buy_order", _send)
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: events.append((stage, fields)),
    )

    stock = {
        "id": 1,
        "name": "PROBE",
        "code": "123456",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_qty": 1,
        "buy_price": 10010,
        "entry_requested_qty": 10,
        "requested_buy_qty": 10,
        "entry_filled_qty": 1,
        "entry_fill_amount": 10010,
        "entry_split_probe_phase": "probe_filled",
        "entry_split_probe_bundle_id": "123456-probe-test",
        "entry_split_probe_requested_qty": 10,
        "entry_split_probe_submit_best_ask": 10000,
        "entry_split_probe_timeout_sec": 3,
        "entry_split_probe_max_slippage_bps": 50,
        "entry_split_probe_submitted_at": now_ts - 0.2,
        "entry_split_probe_filled_at": now_ts - 0.1,
        "entry_split_probe_fill_price": 10010,
        "entry_split_probe_continuation": {
            "base_order": {"tag": "normal", "tif": "DAY", "order_type_code": "00"},
            "requested_qty": 10,
            "residual_qty": 9,
            "residual_leg_count": 2,
            "residual_quantities": [5, 4],
            "price_offsets_ticks": [0, 1],
            "price_offsets_pct": [0.0, 0.3],
            "common_fields": {"entry_split_order_policy_applied": True},
        },
        "pending_entry_orders": [
            {
                "tag": "entry_split_probe_0",
                "ord_no": "P0",
                "qty": 1,
                "filled_qty": 1,
                "status": "FILLED",
                "dmst_stex_tp": "SOR",
            }
        ],
    }
    if rising_missed:
        stock.update(
            {
                "rising_missed_one_share_scout": True,
                "forced_entry_qty": 10,
            }
        )

    submitted = state_handlers._maybe_submit_entry_split_probe_residual(
        stock,
        "123456",
        {"curr": 10010},
        now_ts=now_ts,
        now_dt=datetime(2026, 7, 20, 10, 0, 0),
    )

    assert submitted is True
    assert stock["entry_split_probe_phase"] == "residual_submitted"
    assert [(qty, price) for _, qty, price in sent] == [(5, 10010), (4, 9980)]
    assert sum(qty for _, qty, _ in sent) + stock["buy_qty"] == 10
    assert [stage for stage, _ in events].count("residual_planned") == 1
    assert [stage for stage, _ in events].count("residual_submitted") == 2

    submitted_again = state_handlers._maybe_submit_entry_split_probe_residual(
        stock,
        "123456",
        {"curr": 10010},
        now_ts=now_ts + 0.1,
        now_dt=datetime(2026, 7, 20, 10, 0, 1),
    )
    assert submitted_again is False
    assert len(sent) == 2


def test_post_probe_direction_classifies_strong_weak_neutral_and_source_gap():
    observed_at = 100.0
    quote = {
        "canonical_mark_price": 10_010,
        "passive_buy_price": 10_000,
    }
    strong = state_handlers._post_probe_direction_fields(
        {
            "last_watching_ai_feature_probe_at": observed_at,
            "last_watching_ai_source_quality_fields": {
                "orderbook_micro_state": "bullish",
                "buy_pressure_10t": 60.0,
            },
        },
        {"curr": 10_010},
        quote,
        probe_fill_price=10_000,
        now_ts=100.5,
    )
    weak = state_handlers._post_probe_direction_fields(
        {
            "last_watching_ai_feature_probe_at": observed_at,
            "last_watching_ai_source_quality_fields": {
                "orderbook_micro_state": "bearish",
                "orderbook_micro_qi": 0.20,
                "orderbook_micro_ofi_norm": -0.10,
                "buy_pressure_10t": 20.0,
            },
        },
        {"curr": 9_990},
        {**quote, "canonical_mark_price": 9_990},
        probe_fill_price=10_000,
        now_ts=100.5,
    )
    hanwha_neutral = state_handlers._post_probe_direction_fields(
        {
            "last_watching_ai_feature_probe_at": observed_at,
            "last_watching_ai_source_quality_fields": {
                "true_ofi_ewma": 0.0013,
                "buy_pressure_10t": 21.46,
            },
        },
        {"curr": 83_200},
        {
            "canonical_mark_price": 83_200,
            "passive_buy_price": 83_100,
        },
        probe_fill_price=83_200,
        now_ts=100.5,
    )
    neutral = state_handlers._post_probe_direction_fields(
        {
            "last_watching_ai_feature_probe_at": observed_at,
            "last_watching_ai_source_quality_fields": {
                "buy_pressure_10t": 90.0,
            },
        },
        {"curr": 10_000},
        {
            "canonical_mark_price": 10_000,
            "passive_buy_price": 9_990,
        },
        probe_fill_price=10_000,
        now_ts=100.5,
    )
    source_gap = state_handlers._post_probe_direction_fields(
        {},
        {"curr": 10_000},
        {
            "canonical_mark_price": 10_000,
            "passive_buy_price": 9_990,
        },
        probe_fill_price=10_000,
        now_ts=100.5,
    )

    assert strong["post_probe_direction_state"] == "STRONG"
    assert strong["post_probe_continuation_action"] == "ALLOW_NARROW"
    assert weak["post_probe_direction_state"] == "WEAK"
    assert weak["post_probe_continuation_action"] == "DEFER"
    assert neutral["post_probe_direction_group_count"] == 2
    assert neutral["post_probe_directional_group_count"] == 1
    assert neutral["post_probe_direction_state"] == "NEUTRAL"
    assert neutral["post_probe_continuation_action"] == "ALLOW_NORMAL"
    assert hanwha_neutral["post_probe_direction_state"] == "NEUTRAL"
    assert hanwha_neutral["post_probe_continuation_action"] == "DEFER"
    assert (
        hanwha_neutral["post_probe_direction_reason"]
        == "post_probe_neutral_negative_group_deferred"
    )
    assert source_gap["post_probe_direction_state"] == "UNKNOWN"
    assert source_gap["post_probe_continuation_action"] == "DEFER"


def test_post_probe_wait_uses_submit_timestamp_and_latest_drop_still_vetoes(
    monkeypatch,
):
    monkeypatch.setattr(
        state_handlers,
        "_rising_missed_ai_action_guard_active",
        lambda **_kwargs: True,
    )
    stock = {
        "entry_split_probe_ai_action_at_submit": "WAIT",
        "entry_split_probe_ai_result_source_at_submit": "live",
        "entry_split_probe_ai_confirmed_at_submit": 100.0,
        "last_watching_ai_action": "WAIT",
        "last_watching_ai_result_source": "live",
        "last_watching_ai_confirmed_at": 50.0,
        "last_watching_ai_feature_probe_at": 100.0,
        "last_watching_ai_source_quality_fields": {
            "orderbook_micro_state": "bullish",
            "buy_pressure_10t": 60.0,
        },
    }
    quote = {"canonical_mark_price": 10_010, "passive_buy_price": 10_000}

    wait_result = state_handlers._post_probe_direction_fields(
        stock,
        {"curr": 10_010},
        quote,
        probe_fill_price=10_000,
        now_ts=100.5,
    )

    assert wait_result["post_probe_direction_state"] == "STRONG"
    assert wait_result["post_probe_continuation_action"] == "ALLOW_NARROW"
    assert (
        wait_result["post_probe_direction_ai_context_source"] == "probe_submit_snapshot"
    )
    assert wait_result["post_probe_direction_submit_wait_fresh"] is True
    assert wait_result["post_probe_direction_ai_action_age_sec"] == "0.500"

    stock.update(
        {
            "last_watching_ai_action": "DROP",
            "last_watching_ai_result_source": "live",
            "last_watching_ai_confirmed_at": 100.4,
        }
    )
    drop_result = state_handlers._post_probe_direction_fields(
        stock,
        {"curr": 10_010},
        quote,
        probe_fill_price=10_000,
        now_ts=100.5,
    )

    assert drop_result["post_probe_direction_state"] == "WEAK"
    assert drop_result["post_probe_continuation_action"] == "DEFER"
    assert drop_result["post_probe_hard_veto"] is True
    assert (
        drop_result["post_probe_direction_ai_context_source"]
        == "latest_stock_ai_drop_veto"
    )

    stock.pop("entry_split_probe_ai_confirmed_at_submit")
    stock["last_watching_ai_confirmed_at"] = 50.0
    stale_result = state_handlers._post_probe_direction_fields(
        stock,
        {"curr": 10_010},
        quote,
        probe_fill_price=10_000,
        now_ts=100.5,
    )
    assert stale_result["post_probe_direction_state"] == "STRONG"
    assert stale_result["post_probe_continuation_action"] == "ALLOW_NARROW"
    assert (
        stale_result["post_probe_direction_reason"]
        == "post_probe_stale_wait_two_group_positive_candidate"
    )
    assert (
        stale_result["post_probe_direction_ai_authority"]
        == "stale_wait_non_authoritative_two_group_confirmation"
    )
    assert stale_result["post_probe_direction_submit_wait_fresh"] is False

    stock["entry_split_probe_ai_result_source_at_submit"] = "fallback"
    unverified_result = state_handlers._post_probe_direction_fields(
        stock,
        {"curr": 10_010},
        quote,
        probe_fill_price=10_000,
        now_ts=100.5,
    )
    assert unverified_result["post_probe_direction_state"] == "UNKNOWN"
    assert unverified_result["post_probe_continuation_action"] == "DEFER"
    assert unverified_result["post_probe_direction_reason"] == (
        "post_probe_ai_action_source_unverified"
    )


def test_wait_probe_confirmation_requires_a_new_market_evidence_version(monkeypatch):
    monkeypatch.setattr(
        state_handlers,
        "_post_probe_recheck_interval_sec",
        lambda: 0.25,
    )
    stock = {}
    first = {
        "post_probe_direction_state": "STRONG",
        "post_probe_confirmation_source_version_signature": "snapshot-a",
        "post_probe_confirmation_evidence_version_proven": True,
    }
    ready, count = state_handlers._advance_wait_probe_confirmation(
        stock,
        first,
        now_ts=100.0,
    )
    assert ready is False
    assert count == 1

    same = dict(first)
    ready, count = state_handlers._advance_wait_probe_confirmation(
        stock,
        same,
        now_ts=100.3,
    )
    assert ready is False
    assert count == 1
    assert same["probe_confirmation_evidence_changed"] is False

    changed = {
        **first,
        "post_probe_confirmation_source_version_signature": "snapshot-b",
    }
    ready, count = state_handlers._advance_wait_probe_confirmation(
        stock,
        changed,
        now_ts=100.6,
    )
    assert ready is True
    assert count == 2
    assert changed["probe_confirmation_evidence_changed"] is True


def test_post_probe_source_epoch_normalizes_milliseconds():
    assert state_handlers._post_probe_source_epoch(1_765_000_000.25) == 1_765_000_000.25
    assert state_handlers._post_probe_source_epoch(1_765_000_000_250) == (
        1_765_000_000.25
    )


def test_wait_probe_confirmation_does_not_accept_unversioned_evidence(monkeypatch):
    monkeypatch.setattr(
        state_handlers,
        "_post_probe_recheck_interval_sec",
        lambda: 0.25,
    )
    stock = {}
    first = {
        "post_probe_direction_state": "STRONG",
        "post_probe_confirmation_source_version_signature": "snapshot-a",
        "post_probe_confirmation_evidence_version_proven": False,
    }
    assert state_handlers._advance_wait_probe_confirmation(
        stock,
        first,
        now_ts=100.0,
    ) == (False, 1)
    changed = {
        **first,
        "post_probe_confirmation_source_version_signature": "snapshot-b",
    }
    assert state_handlers._advance_wait_probe_confirmation(
        stock,
        changed,
        now_ts=100.3,
    ) == (False, 1)


def test_post_probe_nxt_stale_wait_requires_existing_fast_tape(monkeypatch):
    monkeypatch.setattr(
        state_handlers,
        "_rising_missed_ai_action_guard_active",
        lambda **_kwargs: True,
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_LATENCY_TRUE_OFI_NXT_FAST_TAPE_CONTINUATION_ENABLED", "true"
    )
    stock = {
        "rising_missed_effective_venue": "NXT",
        "rising_missed_market_session_bucket": "nxt_entry_window",
        "entry_split_probe_ai_action_at_submit": "WAIT",
        "entry_split_probe_ai_result_source_at_submit": "live",
        "entry_split_probe_ai_confirmed_at_submit": 90.0,
        "last_watching_ai_feature_probe_at": 100.0,
        "last_watching_ai_source_quality_fields": {
            "orderbook_micro_state": "bullish",
            "tick_context_quality": "fresh_computed",
            "tick_aggressor_pressure_usable": True,
            "tick_context_stale": False,
            "tick_acceleration_ratio": 2.0,
        },
    }
    quote = {"canonical_mark_price": 10_010, "passive_buy_price": 10_000}
    monkeypatch.setattr(
        state_handlers,
        "_rising_missed_trusted_ws_momentum",
        lambda *_args, **_kwargs: {},
    )

    without_fast_tape = state_handlers._post_probe_direction_fields(
        stock,
        {"curr": 10_010},
        quote,
        probe_fill_price=10_000,
        now_ts=100.0,
        max_context_age_sec=3.0,
    )

    assert without_fast_tape["post_probe_continuation_action"] == "DEFER"
    assert without_fast_tape["post_probe_direction_reason"] == (
        "post_probe_nxt_wait_fast_tape_required"
    )

    monkeypatch.setattr(
        state_handlers,
        "_rising_missed_trusted_ws_momentum",
        lambda *_args, **_kwargs: {
            "rising_missed_tp1_ws_fast_tape_fresh": True,
            "rising_missed_tp1_ws_tick_acceleration_fresh": True,
            "rising_missed_tp1_ws_tick_acceleration": 2.0,
            "rising_missed_tp1_ws_fast_tape_buy_ratio": 90.0,
            "rising_missed_tp1_ws_fast_tape_buy_count": 9,
            "rising_missed_tp1_ws_fast_tape_sell_count": 1,
            "rising_missed_tp1_ws_fast_tape_latest_side": "BUY",
        },
    )
    with_fast_tape = state_handlers._post_probe_direction_fields(
        stock,
        {"curr": 10_010},
        quote,
        probe_fill_price=10_000,
        now_ts=100.0,
        max_context_age_sec=3.0,
    )

    assert with_fast_tape["post_probe_direction_state"] == "STRONG"
    assert with_fast_tape["post_probe_continuation_action"] == "ALLOW_NARROW"
    assert with_fast_tape["post_probe_nxt_wait_fast_tape_ready"] is True


def test_post_probe_chase_guard_caps_fast_rise_and_checks_known_tp_reward_risk(
    monkeypatch,
):
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_CHASE_GUARD_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_MAX_CHASE_BPS", "80")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_MIN_REWARD_RISK", "0.5")

    allowed = state_handlers._post_probe_chase_guard_fields(
        {},
        probe_fill_price=10_000,
        best_bid=10_070,
        best_ask=10_080,
    )
    chase_blocked = state_handlers._post_probe_chase_guard_fields(
        {},
        probe_fill_price=10_000,
        best_bid=10_090,
        best_ask=10_100,
    )
    resolved_price_allowed = state_handlers._post_probe_chase_guard_fields(
        {},
        probe_fill_price=10_000,
        best_bid=10_090,
        best_ask=10_100,
        candidate_price=10_060,
    )
    legacy_preset_tp_ignored = state_handlers._post_probe_chase_guard_fields(
        {"preset_tp_price": 10_060, "hard_stop_pct": -0.7},
        probe_fill_price=10_000,
        best_bid=10_050,
        best_ask=10_060,
    )
    reward_risk_blocked = state_handlers._post_probe_chase_guard_fields(
        {
            "entry_split_probe_reward_target_price": 10_060,
            "hard_stop_pct": -0.7,
        },
        probe_fill_price=10_000,
        best_bid=10_050,
        best_ask=10_060,
    )

    assert allowed["post_probe_chase_guard_blocked"] is False
    assert allowed["post_probe_chase_bps"] == 70.0
    assert chase_blocked["post_probe_chase_guard_blocked"] is True
    assert chase_blocked["post_probe_chase_guard_reason"] == (
        "post_probe_chase_bps_exceeded"
    )
    assert resolved_price_allowed["post_probe_chase_guard_blocked"] is False
    assert resolved_price_allowed["post_probe_chase_candidate_price"] == 10_060
    assert legacy_preset_tp_ignored["post_probe_chase_guard_blocked"] is False
    assert legacy_preset_tp_ignored["post_probe_reward_target_price"] == (
        "not_available"
    )
    assert reward_risk_blocked["post_probe_chase_guard_blocked"] is True
    assert reward_risk_blocked["post_probe_chase_guard_reason"] == (
        "post_probe_reward_risk_below_min"
    )

    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_CHASE_GUARD_ENABLED", "false")
    rollback = state_handlers._post_probe_chase_guard_fields(
        {},
        probe_fill_price=10_000,
        best_bid=10_100,
        best_ask=10_110,
    )
    assert rollback["post_probe_chase_guard_blocked"] is False
    assert rollback["post_probe_chase_guard_reason"] == (
        "post_probe_chase_guard_disabled"
    )


def test_terminal_partial_probe_bundle_releases_scale_in_lock(monkeypatch, tmp_path):
    events = []
    monkeypatch.setattr(
        split_plan,
        "PROBE_RUNTIME_STATE_PATH",
        tmp_path / "entry_split_probe_runtime_state.json",
    )
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: events.append((stage, fields)),
    )
    stock = {
        "id": 1,
        "name": "PARTIAL",
        "code": "123456",
        "strategy": "SCALPING",
        "status": "HOLDING",
        "buy_qty": 4,
        "holding_started_at": 100.0,
        "order_time": 150.0,
        "entry_filled_qty": 4,
        "entry_requested_qty": 10,
        "requested_buy_qty": 10,
        "entry_split_probe_phase": "residual_partial_submitted",
        "entry_split_probe_bundle_id": "123456-probe-partial-complete",
        "entry_split_probe_requested_qty": 10,
        "entry_split_probe_scale_in_forbidden": True,
        "probe_expand_forbidden": False,
        "entry_split_probe_reward_target_price": 10_500,
        "pending_entry_orders": [
            {
                "tag": "entry_split_probe_residual_1",
                "ord_no": "R1",
                "qty": 3,
                "filled_qty": 3,
                "status": "FILLED",
            }
        ],
    }

    assert state_handlers._finalize_entry_split_probe_partial_position(
        stock,
        "123456",
        reason="submitted_residual_orders_terminal",
    )
    assert stock["entry_split_probe_phase"] == "partial_complete"
    assert stock["entry_split_probe_partial_complete_qty"] == 4
    assert stock["entry_fill_quality"] == "PARTIAL_FILL"
    assert "entry_split_probe_scale_in_forbidden" not in stock
    assert "probe_expand_forbidden" not in stock
    assert "entry_requested_qty" not in stock
    assert "requested_buy_qty" not in stock
    assert "order_time" not in stock
    assert "entry_split_probe_reward_target_price" not in stock
    assert events[-1][0] == "residual_partial_complete"
    assert events[-1][1]["broker_order_forbidden"] is False


def test_exit_authority_prevents_partial_probe_unlock(monkeypatch):
    stock = {
        "status": "HOLDING",
        "entry_split_probe_phase": "residual_partial_submitted",
        "entry_split_probe_bundle_id": "probe-exit",
        "entry_split_probe_exit_bundle_id": "probe-exit",
        "entry_split_probe_scale_in_forbidden": True,
        "buy_qty": 2,
    }
    monkeypatch.setattr(
        state_handlers,
        "_has_open_pending_entry_orders",
        lambda _stock: False,
    )

    assert (
        state_handlers._finalize_entry_split_probe_partial_position(
            stock,
            "005930",
            reason="submitted_residual_orders_terminal",
        )
        is False
    )
    assert stock["entry_split_probe_phase"] == "residual_partial_submitted"
    assert stock["entry_split_probe_scale_in_forbidden"] is True


def test_exit_authority_cancel_preserves_probe_phase_and_scale_in_lock(monkeypatch):
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda *args, **kwargs: None,
    )
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "send_cancel_order",
        lambda **kwargs: {
            "return_code": "0",
            "ord_no": "C1",
            "return_msg": "ok",
        },
    )
    stock = {
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_qty": 2,
        "entry_filled_qty": 2,
        "entry_split_probe_phase": "residual_partial_submitted",
        "entry_split_probe_bundle_id": "probe-exit-cancel",
        "entry_split_probe_exit_bundle_id": "probe-exit-cancel",
        "entry_split_probe_scale_in_forbidden": True,
        "pending_entry_orders": [
            {
                "tag": "entry_split_probe_residual_1",
                "ord_no": "R1",
                "qty": 3,
                "filled_qty": 0,
                "status": "OPEN",
                "sent_at": 90.0,
            }
        ],
    }

    result = state_handlers._cancel_pending_entry_orders(
        stock,
        "005930",
        force=True,
        now_ts=100.0,
    )

    assert result == "cancelled"
    assert "pending_entry_orders" not in stock
    assert stock["entry_split_probe_phase"] == "residual_partial_submitted"
    assert stock["entry_split_probe_bundle_id"] == "probe-exit-cancel"
    assert stock["entry_split_probe_scale_in_forbidden"] is True


def test_post_probe_direction_rejects_stale_watching_features():
    result = state_handlers._post_probe_direction_fields(
        {
            "last_watching_ai_feature_probe_at": 90.0,
            "last_watching_ai_source_quality_fields": {
                "orderbook_micro_state": "bullish",
                "buy_pressure_10t": 80.0,
            },
        },
        {"curr": 10_010},
        {"canonical_mark_price": 10_010, "passive_buy_price": 10_000},
        probe_fill_price=10_000,
        now_ts=100.0,
        max_context_age_sec=3.0,
    )

    assert result["post_probe_direction_state"] == "UNKNOWN"
    assert result["post_probe_feature_probe_fresh"] is False


def test_post_probe_direction_uses_fresh_live_orderbook_observer(monkeypatch):
    monkeypatch.setattr(
        state_handlers,
        "_build_live_orderbook_micro_context",
        lambda *_args, **_kwargs: {
            "ready": True,
            "micro_state": "bullish",
            "qi": 0.7,
            "ofi_norm": 0.1,
            "snapshot_age_ms": 100,
            "observer_healthy": True,
        },
    )

    result = state_handlers._post_probe_direction_fields(
        {},
        {"curr": 10_010, "buy_pressure_10t": 70.0},
        {"canonical_mark_price": 10_010, "passive_buy_price": 10_000},
        probe_fill_price=10_000,
        code="123456",
        now_ts=100.0,
    )

    assert result["post_probe_direction_state"] == "STRONG"
    assert result["post_probe_live_micro_fresh"] is True


def test_post_probe_direction_ignores_untrusted_ws_micro_over_fresh_observer(
    monkeypatch,
):
    monkeypatch.setattr(
        state_handlers,
        "_build_live_orderbook_micro_context",
        lambda *_args, **_kwargs: {
            "ready": True,
            "micro_state": "bullish",
            "qi": 0.7,
            "ofi_norm": 0.1,
            "snapshot_age_ms": 100,
            "observer_healthy": True,
        },
    )

    result = state_handlers._post_probe_direction_fields(
        {},
        {
            "curr": 10_010,
            "orderbook_micro_state": "bearish",
            "orderbook_micro_qi": 0.1,
            "orderbook_micro_ofi_norm": -0.5,
            "buy_pressure_10t": 1.0,
            "tick_context_quality": "stale_tick",
            "tick_aggressor_pressure_usable": False,
        },
        {"canonical_mark_price": 10_010, "passive_buy_price": 10_000},
        probe_fill_price=10_000,
        code="123456",
        now_ts=100.0,
    )

    assert result["post_probe_direction_state"] == "STRONG"
    assert result["post_probe_live_micro_fresh"] is True
    assert result["post_probe_ws_tick_context_fresh"] is False


def test_post_probe_direction_does_not_treat_ws_tick_freshness_as_orderbook_freshness():
    result = state_handlers._post_probe_direction_fields(
        {},
        {
            "curr": 10_010,
            "tick_context_quality": "fresh_computed",
            "tick_aggressor_pressure_usable": True,
            "tick_context_stale": False,
            "tick_acceleration_ratio": 1.2,
            "orderbook_micro_state": "bullish",
            "orderbook_micro_qi": 0.8,
            "orderbook_micro_ofi_norm": 0.5,
        },
        {"canonical_mark_price": 10_010, "passive_buy_price": 10_000},
        probe_fill_price=10_000,
        now_ts=100.0,
    )

    assert result["post_probe_direction_state"] == "UNKNOWN"
    assert result["post_probe_continuation_action"] == "DEFER"
    assert result["post_probe_ws_tick_context_fresh"] is True
    assert result["post_probe_live_micro_fresh"] is False


def test_post_probe_direction_rejects_future_micro_timestamps(monkeypatch):
    monkeypatch.setattr(
        state_handlers,
        "_build_live_orderbook_micro_context",
        lambda *_args, **_kwargs: {
            "ready": True,
            "micro_state": "bullish",
            "qi": 0.7,
            "ofi_norm": 0.1,
            "snapshot_age_ms": -1,
            "observer_healthy": True,
        },
    )

    result = state_handlers._post_probe_direction_fields(
        {
            "last_watching_ai_feature_probe_at": 101.0,
            "last_watching_ai_feature_probe": {"buy_pressure_10t": 80.0},
            "last_watching_ai_source_quality_fields": {
                "orderbook_micro_state": "bullish"
            },
        },
        {"curr": 10_010},
        {"canonical_mark_price": 10_010, "passive_buy_price": 10_000},
        probe_fill_price=10_000,
        code="123456",
        now_ts=100.0,
    )

    assert result["post_probe_direction_state"] == "UNKNOWN"
    assert result["post_probe_live_micro_fresh"] is False
    assert result["post_probe_feature_probe_fresh"] is False


def test_probe_residual_network_path_does_not_hold_shared_receipt_lock(monkeypatch):
    receipt_lock_acquired = threading.Event()

    def _fake_submit(*_args, **_kwargs):
        def _receipt_worker():
            with state_handlers.ENTRY_LOCK:
                receipt_lock_acquired.set()

        worker = threading.Thread(target=_receipt_worker)
        worker.start()
        assert receipt_lock_acquired.wait(0.5)
        worker.join(timeout=0.5)
        return True

    monkeypatch.setattr(
        state_handlers, "_submit_entry_split_probe_residual_locked", _fake_submit
    )

    assert state_handlers._maybe_submit_entry_split_probe_residual(
        {},
        "123456",
        {},
        now_ts=100.0,
        now_dt=datetime(2026, 7, 21, 10, 0, 0),
    )


@pytest.mark.parametrize(
    ("second_leg_weak", "fast_tape_single_leg", "wait_probe_single_leg"),
    [
        (False, False, False),
        (True, False, False),
        (False, True, False),
        (False, False, True),
        (False, True, True),
    ],
)
def test_post_probe_unknown_defers_then_recovery_reprices_each_p1_leg(
    monkeypatch,
    tmp_path,
    second_leg_weak,
    fast_tape_single_leg,
    wait_probe_single_leg,
):
    sent = []
    direction = {"state": "UNKNOWN", "action": "DEFER", "recovery_calls": 0}
    monkeypatch.setenv(
        "KORSTOCKSCAN_DYNAMIC_ENTRY_PRICE_RESOLVER_POST_PROBE_ENABLED", "true"
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED", "true")
    monkeypatch.setattr(
        state_handlers,
        "_rising_missed_ai_action_guard_active",
        lambda **_kwargs: wait_probe_single_leg,
    )
    if wait_probe_single_leg:
        monkeypatch.setattr(
            state_handlers,
            "_advance_wait_probe_confirmation",
            lambda *_args, **_kwargs: (True, 2),
        )
    monkeypatch.setattr(
        split_plan,
        "PROBE_RUNTIME_STATE_PATH",
        tmp_path / "entry_split_probe_runtime_state.json",
    )
    monkeypatch.setattr(state_handlers, "COOLDOWNS", {})
    monkeypatch.setattr(state_handlers, "KIWOOM_TOKEN", "token")
    monkeypatch.setattr(state_handlers, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(
        state_handlers, "is_scalping_buy_time_allowed", lambda _now: True
    )
    monkeypatch.setattr(
        state_handlers, "_has_active_sell_order_pending", lambda _stock: False
    )
    monkeypatch.setattr(
        state_handlers, "_has_open_pending_entry_orders", lambda _stock: False
    )
    monkeypatch.setattr(
        state_handlers,
        "_build_quote_consistency_fields",
        lambda *args, **kwargs: (
            {
                "quote_consistency_state": "ok",
                "quote_consistency_reason": "ws_only_fresh",
                "canonical_mark_price": 10095,
                "passive_buy_price": 10090,
            },
            10095,
            10100,
            10090,
        ),
    )

    def _direction_fields(*_args, **_kwargs):
        if direction["state"] == "STRONG":
            direction["recovery_calls"] += 1
            if second_leg_weak and direction["recovery_calls"] >= 3:
                return {
                    "post_probe_direction_state": "WEAK",
                    "post_probe_continuation_action": "DEFER",
                    "post_probe_direction_reason": "second_leg_weakened",
                }
        fields = {
            "post_probe_direction_state": direction["state"],
            "post_probe_continuation_action": direction["action"],
            "post_probe_direction_reason": "test",
        }
        if direction["state"] == "STRONG" and fast_tape_single_leg:
            fields["post_probe_nxt_wait_fast_tape_ready"] = True
            fields["post_probe_nxt_wait_fast_tape_bounded_single_leg"] = True
        if direction["state"] == "STRONG" and wait_probe_single_leg:
            fields["post_probe_direction_ai_authority"] = (
                "stale_wait_non_authoritative_two_group_confirmation"
            )
        return fields

    monkeypatch.setattr(
        state_handlers, "_post_probe_direction_fields", _direction_fields
    )
    monkeypatch.setattr(
        state_handlers,
        "_probe_residual_account_guard_fields",
        lambda *args, **kwargs: {
            "account_guard_allowed": True,
            "account_guard_reason": "probe_residual_account_guard_passed",
        },
    )
    monkeypatch.setattr(
        state_handlers,
        "_post_probe_chase_guard_fields",
        lambda *args, **kwargs: {"post_probe_chase_guard_blocked": False},
    )
    monkeypatch.setattr(
        state_handlers,
        "_split_policy_pre_submit_price_guard_fields",
        lambda *args, **kwargs: {"pre_submit_price_guard_blocked": False},
    )
    monkeypatch.setattr(
        state_handlers,
        "WS_MANAGER",
        SimpleNamespace(get_latest_data=lambda _code: {"curr": 10095}),
    )
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "describe_buy_order_resolution",
        lambda *args, **kwargs: {
            "requested_order_type": "00",
            "effective_order_type": "00",
            "effective_dmst_stex_tp": "SOR",
            "order_type_remapped": False,
            "order_type_remap_reason": "",
        },
    )

    def _send(_code, qty, price, *_args, **_kwargs):
        sent.append((qty, price))
        return {"return_code": "0", "ord_no": f"R{len(sent)}"}

    monkeypatch.setattr(state_handlers.kiwoom_orders, "send_buy_order", _send)
    monkeypatch.setattr(state_handlers, "_log_entry_pipeline", lambda *a, **k: None)
    stock = {
        "id": 1,
        "name": "PROBE",
        "code": "123456",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_qty": 1,
        "buy_price": 10000,
        "entry_requested_qty": 5,
        "requested_buy_qty": 5,
        "entry_filled_qty": 1,
        "entry_fill_amount": 10000,
        "entry_split_probe_phase": "probe_filled",
        "entry_split_probe_bundle_id": "123456-probe-direction",
        "entry_split_probe_requested_qty": 5,
        "entry_split_probe_submit_best_ask": 10000,
        "entry_split_probe_timeout_sec": 3,
        "entry_split_probe_max_slippage_bps": 50,
        "entry_split_probe_submitted_at": 100.0,
        "entry_split_probe_filled_at": 100.1,
        "entry_split_probe_fill_price": 10000,
        "entry_split_probe_ai_action_at_submit": (
            "WAIT" if wait_probe_single_leg else "BUY"
        ),
        "entry_split_probe_continuation": {
            "base_order": {"tag": "normal", "tif": "DAY", "order_type_code": "00"},
            "requested_qty": 5,
            "residual_qty": 4,
            "residual_leg_count": 2,
            "residual_quantities": [2, 2],
            "price_offsets_ticks": [0, 1],
            "price_offsets_pct": [0.0, 0.3],
            "common_fields": {"entry_split_order_policy_applied": True},
        },
        "pending_entry_orders": [
            {
                "tag": "entry_split_probe_0",
                "ord_no": "P0",
                "qty": 1,
                "filled_qty": 1,
                "status": "FILLED",
                "dmst_stex_tp": "SOR",
            }
        ],
    }

    assert not state_handlers._maybe_submit_entry_split_probe_residual(
        stock,
        "123456",
        {"curr": 10000},
        now_ts=100.2,
        now_dt=datetime(2026, 7, 20, 10, 0, 0),
    )
    assert stock["entry_split_probe_phase"] == "probe_recheck_pending"
    assert sent == []

    direction.update(state="STRONG", action="ALLOW_NARROW")
    assert state_handlers._maybe_submit_entry_split_probe_residual(
        stock,
        "123456",
        {"curr": 10000},
        now_ts=100.5,
        now_dt=datetime(2026, 7, 20, 10, 0, 1),
    )
    if fast_tape_single_leg or wait_probe_single_leg:
        expected_sent = [
            (
                2,
                10090 if fast_tape_single_leg and not wait_probe_single_leg else 10060,
            )
        ]
    elif second_leg_weak:
        expected_sent = [(2, 10060)]
    else:
        expected_sent = [(2, 10060), (2, 10010)]
    assert sent == expected_sent
    assert stock["entry_split_probe_offset_profile"] == (
        "narrow"
        if fast_tape_single_leg and not wait_probe_single_leg
        else "recovered_wide"
    )
    assert stock["entry_split_probe_phase"] == (
        "residual_partial_submitted"
        if second_leg_weak or fast_tape_single_leg or wait_probe_single_leg
        else "residual_submitted"
    )
    if fast_tape_single_leg or wait_probe_single_leg:
        assert stock["entry_split_probe_abort_reason"] == (
            "post_probe_nxt_wait_fast_tape_single_residual_leg_cap"
            if fast_tape_single_leg
            else "post_probe_wait_single_residual_leg_cap"
        )
        assert stock["entry_split_probe_bounded_partial_submission"] is True


def test_probe_residual_timeout_keeps_one_share_and_releases_pyramid_recheck(
    monkeypatch, tmp_path
):
    events = []
    monkeypatch.setattr(
        split_plan,
        "PROBE_RUNTIME_STATE_PATH",
        tmp_path / "entry_split_probe_runtime_state.json",
    )
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: events.append((stage, fields)),
    )
    stock = {
        "code": "123456",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_qty": 1,
        "buy_price": 10000,
        "entry_requested_qty": 5,
        "entry_filled_qty": 1,
        "entry_split_probe_phase": "probe_filled",
        "entry_split_probe_bundle_id": "123456-probe-timeout",
        "entry_split_probe_requested_qty": 5,
        "entry_split_probe_submitted_at": 100.0,
        "entry_split_probe_filled_at": 101.0,
        "entry_split_probe_fill_price": 10000,
        "entry_split_probe_timeout_sec": 3,
    }

    submitted = state_handlers._maybe_submit_entry_split_probe_residual(
        stock,
        "123456",
        {"curr": 10000},
        now_ts=105.1,
        now_dt=datetime(2026, 7, 20, 10, 0, 5),
    )

    assert submitted is False
    assert stock["entry_split_probe_phase"] == "aborted"
    assert stock["buy_qty"] == 1
    assert stock["entry_split_probe_scale_in_forbidden"] is False
    assert stock["entry_split_probe_soft_abort"] is True
    assert stock["entry_split_probe_scale_in_recheck_allowed"] is True
    assert (
        stock["entry_split_probe_scale_in_recheck_reason"]
        == "residual_revalidation_timeout"
    )
    assert events[-1][0] == "residual_blocked"
    assert events[-1][1]["reason"] == "residual_revalidation_timeout"
    scale_in = state_handlers.can_consider_scale_in(
        stock,
        "123456",
        {"curr": 10000},
        "SCALPING",
        "NORMAL",
    )
    assert scale_in.get("reason") != "entry_split_probe_scale_in_forbidden"


def test_probe_residual_source_quality_timeout_releases_guarded_scale_in_recheck(
    monkeypatch,
):
    monkeypatch.setattr(
        state_handlers,
        "_rising_missed_ai_action_guard_active",
        lambda **_kwargs: True,
    )
    monkeypatch.setattr(
        state_handlers, "_log_entry_pipeline", lambda *_args, **_kwargs: None
    )
    stock = {
        "status": "HOLDING",
        "buy_qty": 1,
        "entry_filled_qty": 1,
        "entry_split_probe_requested_qty": 41,
        "entry_split_probe_direction_reason": "post_probe_ai_action_not_fresh",
    }

    state_handlers._abort_entry_split_probe_residual(
        stock,
        "123456",
        "residual_revalidation_timeout",
        preserve_position=True,
        now_ts=100.0,
    )

    assert stock["entry_split_probe_soft_abort"] is True
    assert stock["entry_split_probe_scale_in_forbidden"] is False
    assert stock["probe_expand_forbidden"] is False
    assert stock["entry_split_probe_source_quality_recheck_released"] is True
    assert stock["entry_split_probe_source_quality_recheck_unfilled_qty"] == 40
    assert stock["entry_split_probe_scale_in_recheck_reason"].endswith(
        ":source_quality_recovery"
    )


def test_probe_residual_neutral_negative_timeout_keeps_scale_in_recheck(
    monkeypatch,
):
    monkeypatch.setattr(
        state_handlers,
        "_rising_missed_ai_action_guard_active",
        lambda **_kwargs: True,
    )
    monkeypatch.setattr(
        state_handlers, "_log_entry_pipeline", lambda *_args, **_kwargs: None
    )
    stock = {
        "status": "HOLDING",
        "buy_qty": 1,
        "entry_filled_qty": 1,
        "entry_split_probe_requested_qty": 5,
        "entry_split_probe_direction_reason": (
            "post_probe_neutral_negative_group_deferred"
        ),
    }

    state_handlers._abort_entry_split_probe_residual(
        stock,
        "123456",
        "residual_revalidation_timeout",
        preserve_position=True,
        now_ts=100.0,
    )

    assert stock["entry_split_probe_soft_abort"] is True
    assert stock["entry_split_probe_scale_in_forbidden"] is False
    assert stock["probe_expand_forbidden"] is False
    assert stock["entry_split_probe_source_quality_recheck_released"] is False
    assert (
        stock["entry_split_probe_scale_in_recheck_reason"]
        == "residual_revalidation_timeout"
    )


def test_probe_residual_stale_quote_defers_until_ttl_without_broker_submit(
    monkeypatch, tmp_path
):
    events = []
    monkeypatch.setattr(
        split_plan,
        "PROBE_RUNTIME_STATE_PATH",
        tmp_path / "entry_split_probe_runtime_state.json",
    )
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: events.append((stage, fields)),
    )
    stock = {
        "code": "001520",
        "name": "동양",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_qty": 1,
        "buy_price": 1123,
        "entry_filled_qty": 1,
        "entry_split_probe_bundle_id": "001520-dongyang",
        "entry_split_probe_requested_qty": 1013,
    }

    state_handlers._defer_entry_split_probe_source_quality(
        stock,
        "001520",
        reason="stale_or_conflicted_fresh_quote",
        now_ts=100.5,
        filled_at=100.0,
        timeout_sec=3,
    )

    assert stock["entry_split_probe_phase"] == "probe_recheck_pending"
    assert stock["entry_split_probe_continuation_action"] == "DEFER"
    assert stock["entry_split_probe_source_quality_recheck_pending"] is True
    assert events[-1][0] == "probe_source_quality_deferred"
    assert events[-1][1]["actual_order_submitted"] is False
    assert events[-1][1]["broker_order_forbidden"] is True

    monkeypatch.setattr(
        state_handlers,
        "_rising_missed_ai_action_guard_active",
        lambda **_kwargs: True,
    )
    state_handlers._abort_entry_split_probe_residual(
        stock,
        "001520",
        "residual_revalidation_timeout",
        preserve_position=True,
        now_ts=103.1,
    )
    assert stock["entry_split_probe_phase"] == "aborted"
    assert stock["entry_split_probe_soft_abort"] is True
    assert stock["entry_split_probe_scale_in_recheck_allowed"] is True
    assert stock["entry_split_probe_source_quality_recheck_pending"] is False
    assert stock["entry_split_probe_source_quality_recheck_unfilled_qty"] == 1012


def test_probe_residual_directional_weak_timeout_remains_terminal_with_action_guard(
    monkeypatch, tmp_path
):
    events = []
    monkeypatch.setattr(
        split_plan,
        "PROBE_RUNTIME_STATE_PATH",
        tmp_path / "entry_split_probe_runtime_state.json",
    )
    monkeypatch.setattr(
        state_handlers,
        "_rising_missed_ai_action_guard_active",
        lambda **_kwargs: True,
    )
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: events.append((stage, fields)),
    )
    split_plan.update_probe_runtime_bundle(
        "123456-probe-directional-weak",
        phase="probe_filled",
        code="123456",
        target_id=7,
        requested_qty=41,
        fill_qty=1,
    )
    stock = {
        "id": 7,
        "status": "HOLDING",
        "buy_qty": 1,
        "entry_filled_qty": 1,
        "entry_split_probe_bundle_id": "123456-probe-directional-weak",
        "entry_split_probe_requested_qty": 41,
        "entry_split_probe_direction_reason": "post_probe_multi_group_weak",
        "probe_confirmation_count": 1,
        "probe_confirmation_last_at": 99.75,
        "probe_confirmation_last_state": "STRONG",
        "probe_confirmation_last_signature": "price+tape",
    }

    state_handlers._abort_entry_split_probe_residual(
        stock,
        "123456",
        "residual_revalidation_timeout",
        preserve_position=True,
        now_ts=100.0,
    )

    assert stock["entry_split_probe_soft_abort"] is False
    assert stock["entry_split_probe_scale_in_forbidden"] is True
    assert stock["probe_expand_forbidden"] is True
    assert stock["entry_split_probe_source_quality_recheck_released"] is False
    persisted = split_plan._load_json(split_plan.PROBE_RUNTIME_STATE_PATH)["bundles"][
        "123456-probe-directional-weak"
    ]
    assert persisted["phase"] == "aborted"
    assert persisted["entry_split_probe_scale_in_forbidden"] is True
    assert persisted["probe_expand_forbidden"] is True
    assert persisted["probe_confirmation_count"] == 1
    assert persisted["probe_confirmation_last_state"] == "STRONG"
    stage, event = events[-1]
    assert stage == "residual_blocked"
    assert event["entry_split_probe_phase"] == "aborted"
    assert event["probe_confirmation_count"] == 1
    assert event["probe_confirmation_required_count"] == 2
    assert event["probe_expand_forbidden"] is True
    assert event["entry_split_probe_scale_in_forbidden"] is True


def test_probe_restart_recovery_emits_structured_guard_state(monkeypatch):
    events = []
    monkeypatch.setattr(
        sniper_sync,
        "emit_pipeline_event",
        lambda *args, **kwargs: events.append((args, kwargs)),
    )
    target = {
        "id": 23735,
        "name": "SK이노베이션",
        "code": "096770",
        "entry_split_probe_phase": "aborted",
        "entry_split_probe_bundle_id": "096770-probe-runtime",
        "entry_split_probe_abort_reason": "residual_revalidation_timeout",
        "probe_confirmation_count": 1,
        "probe_confirmation_last_state": "STRONG",
        "probe_expand_forbidden": True,
        "entry_split_probe_scale_in_forbidden": True,
    }

    sniper_sync._emit_probe_recovery_event(
        target,
        {
            "recovered": True,
            "reason": "incomplete_bundle_restored",
            "phase": "aborted",
        },
    )

    assert len(events) == 1
    args, kwargs = events[0]
    assert args[:4] == (
        "HOLDING_PIPELINE",
        "SK이노베이션",
        "096770",
        "probe_restart_recovered",
    )
    assert kwargs["record_id"] == 23735
    fields = kwargs["fields"]
    assert fields["probe_confirmation_count"] == 1
    assert fields["probe_confirmation_required_count"] == 2
    assert fields["probe_expand_forbidden"] is True
    assert fields["entry_split_probe_scale_in_forbidden"] is True
    assert fields["decision_authority"] == "probe_restart_state_reconciliation"
    assert fields["actual_order_submitted"] is False


def test_rising_missed_total_qty_owns_scout_state_and_completed_bundle_stops_upgrade():
    stock = {
        "status": "HOLDING",
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "buy_qty": 4,
        "entry_filled_qty": 4,
        "rising_missed_one_share_scout": True,
        "forced_entry_qty": 4,
    }

    assert state_handlers._is_rising_missed_one_share_scout_holding(
        stock,
        strategy="SCALPING",
        pos_tag="SCANNER",
    )

    stock["rising_missed_scout_upgraded"] = True
    assert not state_handlers._is_rising_missed_one_share_scout_holding(
        stock,
        strategy="SCALPING",
        pos_tag="SCANNER",
    )


def test_probe_residual_account_guard_requires_current_orderable_quantity(monkeypatch):
    monkeypatch.setattr(state_handlers, "KIWOOM_TOKEN", "token")
    monkeypatch.setattr(
        state_handlers.kiwoom_orders, "get_deposit", lambda token: 1_000_000
    )
    monkeypatch.setattr(
        state_handlers,
        "_resolve_scalp_cash_budget_context",
        lambda *args, **kwargs: {
            "account_deposit": 1_000_000,
            "cash_orderable_amount": 1_000_000,
            "cash_orderable_qty_cap": 3,
            "kt00011_error": "",
        },
    )

    blocked = state_handlers._probe_residual_account_guard_fields(
        "123456", unit_price=10000, residual_qty=4
    )
    assert blocked["account_guard_allowed"] is False
    assert blocked["account_guard_reason"] == (
        "probe_residual_account_capacity_insufficient"
    )

    allowed = state_handlers._probe_residual_account_guard_fields(
        "123456", unit_price=10000, residual_qty=3
    )
    assert allowed["account_guard_allowed"] is True


@pytest.mark.parametrize(
    ("failure_mode", "expected_reason", "expected_circuit"),
    [
        ("rejected", "residual_broker_submit_failed", []),
        (
            "missing_order_number",
            "residual_broker_order_number_missing",
            ["residual_broker_order_number_missing"],
        ),
        (
            "exception",
            "residual_broker_submit_exception",
            ["residual_broker_submit_exception"],
        ),
    ],
)
def test_probe_residual_stops_after_first_broker_failure_and_preserves_bundle_qty(
    monkeypatch, tmp_path, failure_mode, expected_reason, expected_circuit
):
    now_ts = 1_774_150_400.0
    sent = []
    circuit_reasons = []
    monkeypatch.setattr(
        split_plan,
        "PROBE_RUNTIME_STATE_PATH",
        tmp_path / "entry_split_probe_runtime_state.json",
    )
    monkeypatch.setattr(state_handlers, "COOLDOWNS", {})
    monkeypatch.setattr(state_handlers, "KIWOOM_TOKEN", "token")
    monkeypatch.setattr(state_handlers, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(
        state_handlers, "is_scalping_buy_time_allowed", lambda _now: True
    )
    monkeypatch.setattr(
        state_handlers, "_has_active_sell_order_pending", lambda _stock: False
    )
    monkeypatch.setattr(
        state_handlers, "_has_open_pending_entry_orders", lambda _stock: False
    )
    monkeypatch.setattr(
        state_handlers,
        "_build_quote_consistency_fields",
        lambda *args, **kwargs: (
            {
                "quote_consistency_state": "ok",
                "quote_consistency_reason": "ws_only_fresh",
                "passive_buy_price": 10000,
            },
            10010,
            10020,
            10000,
        ),
    )
    monkeypatch.setattr(
        state_handlers,
        "_split_policy_pre_submit_price_guard_fields",
        lambda *args, **kwargs: {"pre_submit_price_guard_blocked": False},
    )
    monkeypatch.setattr(
        state_handlers,
        "_probe_residual_account_guard_fields",
        lambda *args, **kwargs: {
            "account_guard_allowed": True,
            "account_guard_reason": "probe_residual_account_guard_passed",
        },
    )
    monkeypatch.setattr(
        state_handlers.kiwoom_orders,
        "describe_buy_order_resolution",
        lambda *args, **kwargs: {
            "requested_order_type": "00",
            "effective_order_type": "00",
            "effective_dmst_stex_tp": "SOR",
            "order_type_remapped": False,
            "order_type_remap_reason": "",
        },
    )

    def _send(_code, qty, price, *_args, **_kwargs):
        sent.append((qty, price))
        if len(sent) == 1:
            return {"return_code": "0", "ord_no": "R1"}
        if failure_mode == "missing_order_number":
            return {"return_code": "0"}
        if failure_mode == "exception":
            raise RuntimeError("broker unavailable")
        return {"return_code": "1", "return_msg": "rejected"}

    monkeypatch.setattr(state_handlers.kiwoom_orders, "send_buy_order", _send)
    monkeypatch.setattr(
        state_handlers,
        "trip_probe_runtime_circuit",
        lambda reason: circuit_reasons.append(reason),
    )
    monkeypatch.setattr(
        state_handlers, "_log_entry_pipeline", lambda *args, **kwargs: None
    )
    stock = {
        "id": 1,
        "name": "PROBE",
        "code": "123456",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_qty": 1,
        "buy_price": 10010,
        "entry_requested_qty": 10,
        "requested_buy_qty": 10,
        "entry_filled_qty": 1,
        "entry_fill_amount": 10010,
        "entry_split_probe_phase": "probe_filled",
        "entry_split_probe_bundle_id": "123456-probe-partial",
        "entry_split_probe_requested_qty": 10,
        "entry_split_probe_submit_best_ask": 10000,
        "entry_split_probe_timeout_sec": 3,
        "entry_split_probe_max_slippage_bps": 50,
        "entry_split_probe_submitted_at": now_ts - 0.2,
        "entry_split_probe_filled_at": now_ts - 0.1,
        "entry_split_probe_fill_price": 10010,
        "entry_split_probe_continuation": {
            "base_order": {"tag": "normal", "tif": "DAY", "order_type_code": "00"},
            "requested_qty": 10,
            "residual_qty": 9,
            "residual_leg_count": 3,
            "residual_quantities": [3, 3, 3],
            "price_offsets_ticks": [0, 1, 2],
            "price_offsets_pct": [0.0, 0.3, 0.6],
            "common_fields": {"entry_split_order_policy_applied": True},
        },
        "pending_entry_orders": [
            {
                "tag": "entry_split_probe_0",
                "ord_no": "P0",
                "qty": 1,
                "filled_qty": 1,
                "status": "FILLED",
                "dmst_stex_tp": "SOR",
            }
        ],
    }

    result = state_handlers._maybe_submit_entry_split_probe_residual(
        stock,
        "123456",
        {"curr": 10010},
        now_ts=now_ts,
        now_dt=datetime(2026, 7, 20, 10, 0, 0),
    )

    assert result is True
    assert len(sent) == 2
    assert stock["entry_split_probe_phase"] == "residual_partial_submitted"
    assert stock["entry_split_probe_abort_reason"] == expected_reason
    assert stock["entry_requested_qty"] == 10
    assert stock["requested_buy_qty"] == 10
    assert stock["entry_split_probe_scale_in_forbidden"] is True
    assert [
        order["ord_no"]
        for order in stock["pending_entry_orders"]
        if order.get("status") == "OPEN"
    ] == ["R1"]
    assert circuit_reasons == expected_circuit


def test_probe_residual_orders_are_cancelled_before_hard_exit_sell(monkeypatch):
    calls = []
    persisted_updates = []
    monkeypatch.setattr(state_handlers, "_remember_exit_context", lambda **kwargs: None)
    monkeypatch.setattr(
        state_handlers, "_log_holding_pipeline", lambda *args, **kwargs: None
    )
    monkeypatch.setattr(
        state_handlers, "_is_scalp_simulated_position", lambda *args: False
    )
    monkeypatch.setattr(
        state_handlers, "_has_open_pending_entry_orders", lambda stock: True
    )
    monkeypatch.setattr(
        state_handlers,
        "_cancel_pending_entry_orders",
        lambda stock, code, force=False: calls.append("cancel_buy") or "cancelled",
    )
    monkeypatch.setattr(
        state_handlers,
        "update_probe_runtime_bundle",
        lambda bundle_id, **fields: persisted_updates.append((bundle_id, fields)),
    )
    monkeypatch.setattr(
        state_handlers,
        "_sell_side_open_time_block_fields",
        lambda **kwargs: {"sell_time_block_applied": False},
    )
    monkeypatch.setattr(
        state_handlers,
        "_confirm_cancel_or_reload_remaining",
        lambda *args: 1,
    )
    monkeypatch.setattr(
        state_handlers,
        "_attempt_late_loss_avg_down_retry_before_sell",
        lambda **kwargs: None,
    )
    monkeypatch.setattr(
        state_handlers, "_loss_recovery_intercepts_sell", lambda result: False
    )
    monkeypatch.setattr(
        state_handlers,
        "_send_exit_best_ioc",
        lambda *args: calls.append("sell") or {"ord_no": "S1"},
    )
    stock = {
        "id": 7,
        "name": "PROBE",
        "code": "123456",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_qty": 1,
        "entry_split_probe_phase": "residual_submitted",
        "entry_split_probe_bundle_id": "123456-probe-exit",
        "pending_entry_orders": [{"ord_no": "R1", "status": "OPEN", "qty": 4}],
    }

    state_handlers._dispatch_scalp_preset_exit(
        stock=stock,
        code="123456",
        now_ts=100.0,
        curr_p=9900,
        buy_p=10000,
        profit_rate=-1.0,
        peak_profit=0.0,
        strategy="SCALPING",
        sell_reason_type="손절",
        reason="hard stop",
        exit_rule="hard_stop",
    )

    assert calls == ["cancel_buy", "sell"]
    assert stock["status"] == "SELL_ORDERED"
    assert stock["entry_split_probe_exit_bundle_id"] == "123456-probe-exit"
    assert stock["entry_split_probe_phase"] == "aborted"
    assert stock["entry_split_probe_abort_reason"] == "exit_authority_precedence"
    assert stock["entry_split_probe_scale_in_forbidden"] is True
    assert stock["probe_expand_forbidden"] is True
    assert len(persisted_updates) == 1
    persisted_bundle_id, persisted_fields = persisted_updates[0]
    assert persisted_bundle_id == "123456-probe-exit"
    assert persisted_fields["phase"] == "aborted"
    assert persisted_fields["target_id"] == 7
    assert persisted_fields["reason"] == "exit_authority_precedence"
    assert persisted_fields["entry_split_probe_scale_in_forbidden"] is True
    assert persisted_fields["probe_expand_forbidden"] is True
    assert persisted_fields["exit_rule"] == "hard_stop"
    assert persisted_fields["exit_requested_at"]

    calls.clear()
    monkeypatch.setattr(
        state_handlers,
        "_cancel_pending_entry_orders",
        lambda stock, code, force=False: calls.append("cancel_buy") or "failed",
    )
    monkeypatch.setattr(
        state_handlers,
        "trip_probe_runtime_circuit",
        lambda reason: calls.append("circuit"),
    )
    failed_cancel_stock = {
        "name": "PROBE",
        "code": "123456",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_qty": 1,
        "entry_split_probe_phase": "residual_submitted",
        "pending_entry_orders": [{"ord_no": "R1", "status": "OPEN", "qty": 4}],
    }
    state_handlers._dispatch_scalp_preset_exit(
        stock=failed_cancel_stock,
        code="123456",
        now_ts=101.0,
        curr_p=9900,
        buy_p=10000,
        profit_rate=-1.0,
        peak_profit=0.0,
        strategy="SCALPING",
        sell_reason_type="손절",
        reason="hard stop",
        exit_rule="hard_stop",
    )
    assert calls == ["cancel_buy", "circuit", "sell"]
    assert failed_cancel_stock["status"] == "SELL_ORDERED"
    assert failed_cancel_stock["entry_split_probe_scale_in_forbidden"] is True
