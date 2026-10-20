import ast
import inspect
from datetime import datetime, time as datetime_time
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from src.engine import kiwoom_sniper_v2, sniper_state_handlers
from src.engine.sniper_overnight_gatekeeper import (
    _eod_label,
    _overnight_gatekeeper_enabled,
    run_scalping_overnight_gatekeeper,
)
from src.engine.sniper_time import TIME_SCALPING_OVERNIGHT_DECISION


@pytest.fixture(autouse=True)
def _isolate_terminal_custody(monkeypatch, tmp_path):
    path = tmp_path / "terminal-manual.txt"
    path.write_text("")
    monkeypatch.setenv("KORSTOCKSCAN_MANUAL_CONTROL_EXCLUDED_CODES_FILE", str(path))
    monkeypatch.delenv("KORSTOCKSCAN_MANUAL_CONTROL_EXCLUDED_CODES", raising=False)


def test_scalping_overnight_decision_default_time_is_1510():
    assert TIME_SCALPING_OVERNIGHT_DECISION.isoformat() == "15:10:00"


def test_eod_label_defaults_to_1510(monkeypatch):
    monkeypatch.setattr(
        "src.engine.sniper_overnight_gatekeeper.TRADING_RULES",
        SimpleNamespace(),
    )

    assert _eod_label() == "15:10"


def test_overnight_gatekeeper_default_disabled(monkeypatch):
    monkeypatch.setattr(
        "src.engine.sniper_overnight_gatekeeper.TRADING_RULES",
        SimpleNamespace(),
    )

    assert _overnight_gatekeeper_enabled() is False


@pytest.mark.parametrize(
    "true_config,true_env",
    [(False, False), (True, False), (False, True), (True, True)],
)
def test_overnight_gatekeeper_ignores_runtime_true_override(
    monkeypatch, true_config, true_env
):
    from src.engine import sniper_overnight_gatekeeper as overnight

    monkeypatch.setattr(
        overnight,
        "TRADING_RULES",
        SimpleNamespace(SCALPING_OVERNIGHT_GATEKEEPER_ENABLED=True)
        if true_config else SimpleNamespace(),
    )
    env_key = "KORSTOCKSCAN_SCALPING_OVERNIGHT_GATEKEEPER_ENABLED"
    if true_env:
        monkeypatch.setenv(env_key, "true")
    else:
        monkeypatch.delenv(env_key, raising=False)
    external = Mock(side_effect=AssertionError("retired overnight side effect"))
    # Even supplied legacy runtime dependencies must never be consumed.
    for name, value in {
        "DB": SimpleNamespace(get_session=external),
        "WS_MANAGER": SimpleNamespace(get_latest_data=external),
        "ACTIVE_TARGETS": [{"id": 1, "code": "005930", "status": "HOLDING"}],
        "event_bus": SimpleNamespace(publish=external),
        "DUAL_PERSONA_ENGINE": SimpleNamespace(submit=external),
        "kiwoom_utils": SimpleNamespace(get_tick_history_ka10003=external,
                                        get_minute_candles_ka10080=external),
        "send_telegram": external,
        "_confirm_cancel_or_reload_remaining": external,
        "_send_market_exit_now": external,
        "process_sell_cancellation": external,
    }.items():
        monkeypatch.setattr(overnight, name, value, raising=False)
    messages = []
    monkeypatch.setattr(overnight, "log_info", messages.append)
    ai = SimpleNamespace(evaluate_scalping_overnight_decision=external,
                         evaluate_scalping_holding_flow=external)

    assert _overnight_gatekeeper_enabled() is False
    assert run_scalping_overnight_gatekeeper(ai_engine=ai) is False
    assert external.mock_calls == []
    assert len(messages) == 1
    assert "비활성화" in messages[0] and f"{env_key}=false" in messages[0]


def test_same_session_terminal_exit_uses_last_executable_venue_window(monkeypatch):
    stock = {
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_qty": 3,
    }
    monkeypatch.setattr(
        sniper_state_handlers,
        "_holding_sell_nxt_enabled_status",
        lambda *_args: (False, "test.krx_only"),
    )
    krx = sniper_state_handlers._scalping_same_session_terminal_exit_fields(
        stock,
        "005930",
        strategy="SCALPING",
        now_t=datetime_time(15, 15),
        observed_at=datetime(2026, 9, 11, 15, 15, tzinfo=sniper_state_handlers._KST),
    )
    assert krx["should_exit"] is True
    assert krx["terminal_venue"] == "KRX"

    monkeypatch.setattr(
        sniper_state_handlers,
        "_holding_sell_nxt_enabled_status",
        lambda *_args: (True, "test.nxt"),
    )
    before_nxt_close = (
        sniper_state_handlers._scalping_same_session_terminal_exit_fields(
            stock,
            "005930",
            strategy="SCALPING",
            now_t=datetime_time(15, 15),
            observed_at=datetime(
                2026, 9, 11, 15, 15, tzinfo=sniper_state_handlers._KST
            ),
        )
    )
    nxt_close = sniper_state_handlers._scalping_same_session_terminal_exit_fields(
        stock,
        "005930",
        strategy="SCALPING",
        now_t=datetime_time(19, 45),
        observed_at=datetime(2026, 9, 11, 19, 45, tzinfo=sniper_state_handlers._KST),
    )
    assert before_nxt_close["should_exit"] is False
    assert nxt_close["should_exit"] is True
    assert nxt_close["terminal_venue"] == "NXT"


def test_shutdown_reconciliation_reports_real_and_sim_scalping_positions():
    rows = sniper_state_handlers.unresolved_scalping_terminal_positions(
        [
            {
                "id": 1,
                "code": "005930",
                "strategy": "SCALPING",
                "status": "HOLDING",
                "buy_qty": 3,
            },
            {
                "id": 2,
                "code": "000660",
                "strategy": "SCALPING",
                "status": "SELL_ORDERED",
                "buy_qty": 2,
                "simulation_book": "scalp_ai_buy_all",
            },
            {
                "id": 4,
                "code": "051910",
                "strategy": "SCALPING",
                "status": "BUY_ORDERED",
                "buy_qty": 0,
            },
            {"id": 3, "code": "035420", "strategy": "KOSPI_ML", "status": "HOLDING"},
        ]
    )

    assert [row["code"] for row in rows] == ["005930", "000660", "051910"]
    assert rows[0]["simulation"] is False
    assert rows[1]["simulation"] is True
    assert rows[2]["status"] == "BUY_ORDERED"


def test_shutdown_reconciliation_accepts_cost_adjusted_terminal_hold():
    rows = sniper_state_handlers.unresolved_scalping_terminal_positions(
        [
            {
                "id": 1,
                "code": "005930",
                "strategy": "SCALPING",
                "status": "HOLDING",
                "buy_qty": 3,
                "terminal_exit_hold_authorized": True,
                "terminal_exit_hold_observed_at": "2026-09-14T19:59:45+09:00",
                "terminal_exit_hold_basis": (
                    "fresh_executable_sell_price_after_configured_trade_cost"
                ),
                "terminal_exit_hold_net_ev_pct": -0.01,
                "terminal_exit_hold_source_valid": True,
            }
        ],
        observed_at=datetime(2026, 9, 14, 20, 0, tzinfo=sniper_state_handlers._KST),
    )

    assert rows == []


@pytest.mark.parametrize(
    "hold_override",
    [
        {"terminal_exit_hold_net_ev_pct": 0.01},
        {"terminal_exit_hold_source_valid": False},
        {"terminal_exit_hold_observed_at": "2026-09-11T19:45:00+09:00"},
        {"terminal_exit_hold_observed_at": "2026-09-14T19:58:59+09:00"},
        {"terminal_exit_hold_observed_at": "2026-09-14T20:00:01+09:00"},
        {"terminal_exit_hold_net_ev_pct": float("-inf")},
        {"terminal_exit_hold_net_ev_pct": float("nan")},
        {"exit_token": "in-flight"},
    ],
)
def test_shutdown_reconciliation_rejects_invalid_terminal_hold(hold_override):
    stock = {
        "id": 1,
        "code": "005930",
        "strategy": "SCALPING",
        "status": "HOLDING",
        "buy_qty": 3,
        "terminal_exit_hold_authorized": True,
        "terminal_exit_hold_observed_at": "2026-09-14T19:59:45+09:00",
        "terminal_exit_hold_basis": (
            "fresh_executable_sell_price_after_configured_trade_cost"
        ),
        "terminal_exit_hold_net_ev_pct": -0.01,
        "terminal_exit_hold_source_valid": True,
        **hold_override,
    }

    rows = sniper_state_handlers.unresolved_scalping_terminal_positions(
        [stock],
        observed_at=datetime(2026, 9, 14, 20, 0, tzinfo=sniper_state_handlers._KST),
    )

    assert [row["code"] for row in rows] == ["005930"]


@pytest.mark.parametrize("marker", ["manual_operator", "auto_hard_stop_handoff"])
def test_terminal_census_excludes_proven_manual_hold_without_changing_custody(
    monkeypatch, tmp_path, marker
):
    path = tmp_path / "manual.txt"
    original = f"196170 # {marker} source=test\n"
    path.write_text(original)
    monkeypatch.setenv("KORSTOCKSCAN_MANUAL_CONTROL_EXCLUDED_CODES_FILE", str(path))
    stock = {"id": 1, "code": "196170", "strategy": "SCALPING",
             "status": "HOLDING", "buy_qty": 1}
    before = dict(stock)
    assert sniper_state_handlers.unresolved_scalping_terminal_positions([stock]) == []
    assert stock == before and path.read_text() == original


@pytest.mark.parametrize("override", [
    {"status": "BUY_ORDERED"},
    {"status": "SELL_ORDERED"},
    {"exit_token": "in-flight"},
    {"simulation_book": "scalp_ai_buy_all"},
    {"aftermarket_close_reconciliation": {
        "side": "SELL", "symbol": "196170", "state": "OPEN", "terminal": False,
        "intent_sha256": "a" * 64, "source_sha256s": ["b" * 64]}},
])
def test_terminal_census_keeps_manual_symbol_unresolved_orders_and_simulation(
    monkeypatch, tmp_path, override
):
    path = tmp_path / "manual.txt"
    path.write_text("196170 # auto_hard_stop_handoff source=test\n")
    monkeypatch.setenv("KORSTOCKSCAN_MANUAL_CONTROL_EXCLUDED_CODES_FILE", str(path))
    stock = {"id": 1, "code": "196170", "strategy": "SCALPING",
             "status": "HOLDING", "buy_qty": 1, **override}
    rows = sniper_state_handlers.unresolved_scalping_terminal_positions([stock])
    assert [row["id"] for row in rows] == [1]


@pytest.mark.parametrize("reason", ["manual_control_exclusion_file_fail_closed:OSError",
    "symbol_owner_policy_fail_closed:ValueError", "exact_date_owner_policy_blocks_main_bot_custody"])
def test_terminal_census_does_not_infer_manual_handoff_from_policy_failure(monkeypatch, reason):
    monkeypatch.setattr(sniper_state_handlers, "evaluate_main_bot_control_exclusion",
        lambda *a, **kw: SimpleNamespace(excluded=True, reason=reason))
    stock = {"id": 1, "code": "196170", "strategy": "SCALPING",
             "status": "HOLDING", "buy_qty": 1, "manual_control_exclusion_blocked": True}
    assert len(sniper_state_handlers.unresolved_scalping_terminal_positions([stock])) == 1


@pytest.mark.parametrize("naive", [True, False])
@pytest.mark.parametrize("bid_price", [209500, 210500, 0])
def test_live_holding_clock_produces_consumer_valid_terminal_hold(monkeypatch, naive, bid_price):
    h = sniper_state_handlers
    observed = datetime.fromisoformat("2026-10-15T19:59:45+09:00")
    stock = {"id": 1, "code": "196170", "name": "TEST", "strategy": "SCALPING",
             "status": "HOLDING", "buy_qty": 1, "buy_price": 210000,
             "entry_execution_broker_route": "NXT"}
    for name in ("_observe_initial_quantity_cap_following_tick", "_observe_avg_down_runtime_config",
                 "_maybe_release_auto_manual_control_at_average_price", "_retry_pending_hard_stop_manual_handoff",
                 "_manual_control_exclusion_blocked", "_sell_cancel_reconciliation_blocks_holding",
                 "_maybe_auto_exclude_open_loss_holding", "_observe_entry_cancel_wait_counterfactuals",
                 "_reconcile_pending_entry_orders", "_finalize_entry_split_probe_partial_position",
                 "_maybe_submit_entry_split_probe_residual", "_persist_scalping_position_peak",
                 "_observe_smoothing_source_only_paths"):
        monkeypatch.setattr(h, name, lambda *a, **kw: False)
    for name, value in (("HIGHEST_PRICES", {}), ("COOLDOWNS", {}),
                        ("LAST_AI_CALL_TIMES", {}), ("ALERTED_STOCKS", set())):
        monkeypatch.setattr(h, name, value)
    monkeypatch.setattr(h, "_holding_ws_freshness_recover_or_block",
        lambda stock, code, ws, **kw: (ws, False, {}))
    monkeypatch.setattr(h, "_build_quote_consistency_fields",
        lambda *a, **kw: ({}, 209500, 209600, bid_price))
    monkeypatch.setattr(h, "get_trade_cost_rate", lambda: 0.0023)
    events = []
    monkeypatch.setattr(h, "_log_holding_pipeline",
        lambda stock, code, stage, **kw: events.append((stage, kw)))
    class AfterTerminalDecision(Exception):
        pass
    def stop_before_other_holding_actions(**kwargs):
        raise AfterTerminalDecision
    monkeypatch.setattr(h, "_holding_context_prohibited_exit_candidate", stop_before_other_holding_actions)
    with pytest.raises(AfterTerminalDecision):
        h.handle_holding_state(stock, "196170", {"curr": 209500}, 1, "BULL",
            now_ts=observed.timestamp(), now_dt=observed.replace(tzinfo=None) if naive else observed)
    valid_hold = bid_price == 209500
    if valid_hold:
        assert stock["terminal_exit_hold_authorized"] is True
        assert stock["terminal_exit_hold_observed_at"] == observed.isoformat()
        assert any(stage == "same_session_terminal_exit_continues_holding" for stage, _ in events)
    elif bid_price == 0:
        assert stock["terminal_exit_hold_source_valid"] is False
    else:
        assert stock["terminal_exit_hold_authorized"] is False
        assert any(stage == "same_session_terminal_exit_selected" for stage, _ in events)
    rows = h.unresolved_scalping_terminal_positions([stock],
        observed_at=datetime.fromisoformat("2026-10-15T20:00:00+09:00"))
    assert len(rows) == (0 if valid_hold else 1)
    assert stock["status"] == "HOLDING" and stock["buy_qty"] == 1


def test_run_scalping_overnight_gatekeeper_returns_false_when_disabled(monkeypatch):
    monkeypatch.setattr(
        "src.engine.sniper_overnight_gatekeeper.TRADING_RULES",
        SimpleNamespace(SCALPING_OVERNIGHT_GATEKEEPER_ENABLED=False),
    )

    assert run_scalping_overnight_gatekeeper(ai_engine=object()) is False


def test_run_sniper_eod_holding_fallback_is_permanently_disabled():
    source = inspect.getsource(kiwoom_sniper_v2._run_sniper_iterations)
    tree = ast.parse(source)

    fallback_assign = None
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if (
                    isinstance(target, ast.Name)
                    and target.id == "eod_ai_holding_fallback"
                ):
                    fallback_assign = node
                    break
        if fallback_assign is not None:
            break

    assert fallback_assign is not None, "eod_ai_holding_fallback assignment not found"
    assert isinstance(fallback_assign.value, ast.Constant)
    assert fallback_assign.value.value is False


def test_main_runtime_has_no_overnight_module_binding_or_gatekeeper_call():
    source = inspect.getsource(kiwoom_sniper_v2)

    assert "bind_overnight_dependencies" not in source
    assert "run_scalping_overnight_gatekeeper" not in source
