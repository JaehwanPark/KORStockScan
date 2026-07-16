from datetime import datetime

from src.engine import sniper_state_handlers
from src.engine.risk import manual_control_exclusion


def test_manual_control_exclusion_matches_env_codes(monkeypatch):
    monkeypatch.setenv(
        manual_control_exclusion.EXCLUDED_CODES_ENV, "5930, 001820;A000660"
    )
    decision = manual_control_exclusion.evaluate_manual_control_exclusion("005930")

    assert decision.excluded is True
    assert decision.code == "005930"
    assert decision.reason == "operator_manual_control_excluded_symbol"
    assert decision.source == manual_control_exclusion.EXCLUDED_CODES_ENV
    assert decision.as_log_fields()["actual_order_submitted"] is False
    assert decision.as_log_fields()["broker_order_forbidden"] is True
    assert (
        decision.as_log_fields()["decision_authority"]
        == "operator_manual_control_exclusion_no_bot_action"
    )


def test_manual_control_exclusion_loads_file_and_reloads_on_mtime_change(
    monkeypatch, tmp_path
):
    path = tmp_path / "manual_control_excluded_codes.txt"
    path.write_text("005930 # Samsung\n001820\n", encoding="utf-8")
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))

    assert (
        manual_control_exclusion.evaluate_manual_control_exclusion("005930").excluded
        is True
    )
    assert (
        manual_control_exclusion.evaluate_manual_control_exclusion("000660").excluded
        is False
    )

    path.write_text("000660\n", encoding="utf-8")

    assert (
        manual_control_exclusion.evaluate_manual_control_exclusion("005930").excluded
        is False
    )
    assert (
        manual_control_exclusion.evaluate_manual_control_exclusion("000660").excluded
        is True
    )


def test_manual_control_exclusion_append_adds_code_once(monkeypatch, tmp_path):
    path = tmp_path / "manual_control_excluded_codes.txt"
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))

    first = manual_control_exclusion.add_manual_control_exclusion_code(
        "5930",
        comment="auto_open_loss KRX_OPEN profit=-3.00% stop=-2.50%",
    )
    second = manual_control_exclusion.add_manual_control_exclusion_code("005930")

    assert first.excluded is True
    assert first.code == "005930"
    assert second.excluded is True
    assert (
        manual_control_exclusion.evaluate_manual_control_exclusion("005930").excluded
        is True
    )
    assert path.read_text(encoding="utf-8").count("005930") == 1


def test_manual_control_exclusion_remove_deletes_file_code(monkeypatch, tmp_path):
    path = tmp_path / "manual_control_excluded_codes.txt"
    path.write_text(
        "005930 # Samsung manual control\n000660,001820 # grouped\n",
        encoding="utf-8",
    )
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))

    result = manual_control_exclusion.remove_manual_control_exclusion_code(
        "A005930",
        reason="periodic_sync_completed_no_broker_holding",
    )

    assert result.removed is True
    assert result.code == "005930"
    assert (
        manual_control_exclusion.evaluate_manual_control_exclusion("005930").excluded
        is False
    )
    assert (
        manual_control_exclusion.evaluate_manual_control_exclusion("000660").excluded
        is True
    )
    assert "005930" not in path.read_text(encoding="utf-8")


def test_manual_control_exclusion_remove_preserves_other_codes_on_same_line(
    monkeypatch, tmp_path
):
    path = tmp_path / "manual_control_excluded_codes.txt"
    path.write_text("005930,000660,001820 # grouped\n", encoding="utf-8")
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))

    result = manual_control_exclusion.remove_manual_control_exclusion_code("000660")

    assert result.removed is True
    assert (
        manual_control_exclusion.evaluate_manual_control_exclusion("000660").excluded
        is False
    )
    assert (
        manual_control_exclusion.evaluate_manual_control_exclusion("005930").excluded
        is True
    )
    assert (
        manual_control_exclusion.evaluate_manual_control_exclusion("001820").excluded
        is True
    )
    assert path.read_text(encoding="utf-8") == "005930,001820 # grouped\n"


def test_manual_control_exclusion_remove_file_code_does_not_clear_env_override(
    monkeypatch, tmp_path
):
    path = tmp_path / "manual_control_excluded_codes.txt"
    path.write_text("005930 # Samsung manual control\n", encoding="utf-8")
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_ENV, "005930")
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))

    result = manual_control_exclusion.remove_manual_control_exclusion_code("005930")

    assert result.removed is True
    assert path.read_text(encoding="utf-8") == ""
    decision = manual_control_exclusion.evaluate_manual_control_exclusion("005930")
    assert decision.excluded is True
    assert decision.source == manual_control_exclusion.EXCLUDED_CODES_ENV


def test_manual_control_exclusion_empty_config_does_not_block(monkeypatch, tmp_path):
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(
        manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(tmp_path / "missing.txt")
    )

    decision = manual_control_exclusion.evaluate_manual_control_exclusion("005930")

    assert decision.excluded is False
    assert decision.code == "005930"


def test_manual_control_exclusion_blocks_pending_order_cancellations(monkeypatch):
    emitted = []
    stock = {
        "id": 1,
        "code": "005930",
        "name": "SAMSUNG",
        "status": "BUY_ORDERED",
        "strategy": "SCALPING",
        "odno": "123",
        "order_time": 1.0,
    }
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_ENV, "005930")
    monkeypatch.setattr(
        sniper_state_handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {
                "pipeline": pipeline,
                "name": name,
                "code": code,
                "stage": stage,
                "fields": fields or {},
            }
        ),
    )

    def fail_cancel(*args, **kwargs):
        raise AssertionError(
            "cancel order must not be called for manual-control excluded symbols"
        )

    monkeypatch.setattr(
        sniper_state_handlers.kiwoom_orders, "send_cancel_order", fail_cancel
    )

    assert (
        sniper_state_handlers.process_order_cancellation(
            stock, "005930", "123", db=None, strategy="SCALPING"
        )
        is False
    )

    assert stock["status"] == "BUY_ORDERED"
    assert stock["odno"] == "123"
    assert emitted[-1]["stage"] == "manual_control_excluded_buy_cancel_blocked"
    assert emitted[-1]["fields"]["manual_control_exclusion_applied"] is True


def test_manual_control_exclusion_blocks_holding_handler_before_sell_logic(monkeypatch):
    emitted = []
    stock = {
        "id": 2,
        "code": "005930",
        "name": "SAMSUNG",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 70000,
    }
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_ENV, "005930")
    monkeypatch.setattr(
        sniper_state_handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {
                "pipeline": pipeline,
                "name": name,
                "code": code,
                "stage": stage,
                "fields": fields or {},
            }
        ),
    )

    def fail_reconcile(*args, **kwargs):
        raise AssertionError(
            "holding control path must not run for manual-control excluded symbols"
        )

    monkeypatch.setattr(
        sniper_state_handlers, "_reconcile_pending_entry_orders", fail_reconcile
    )

    sniper_state_handlers.handle_holding_state(
        stock,
        "005930",
        {"curr": 71000},
        admin_id="admin",
        market_regime={},
        now_ts=1000.0,
    )

    assert stock["status"] == "HOLDING"
    assert emitted[-1]["stage"] == "manual_control_excluded_symbol_blocked"
    assert emitted[-1]["fields"]["manual_control_exclusion_applied"] is True


def test_open_loss_holding_auto_exclusion_blocks_before_reconcile(
    monkeypatch, tmp_path
):
    emitted = []
    path = tmp_path / "manual_control_excluded_codes.txt"
    stock = {
        "id": 3,
        "code": "005930",
        "name": "SAMSUNG",
        "status": "HOLDING",
        "strategy": "KOSPI_ML",
        "position_tag": "BULL",
        "buy_price": 10000,
    }
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))
    monkeypatch.setattr(
        sniper_state_handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {
                "pipeline": pipeline,
                "name": name,
                "code": code,
                "stage": stage,
                "fields": fields or {},
            }
        ),
    )

    def fail_reconcile(*args, **kwargs):
        raise AssertionError(
            "open-loss auto exclusion must run before reconcile/sell control"
        )

    monkeypatch.setattr(
        sniper_state_handlers, "_reconcile_pending_entry_orders", fail_reconcile
    )

    sniper_state_handlers.handle_holding_state(
        stock,
        "005930",
        {"curr": 9700},
        admin_id="admin",
        market_regime="BULL",
        now_ts=1000.0,
        now_dt=datetime(2026, 7, 2, 9, 0, 5),
    )

    assert (
        manual_control_exclusion.evaluate_manual_control_exclusion("005930").excluded
        is True
    )
    assert "005930" in path.read_text(encoding="utf-8")
    assert stock["manual_control_exclusion_blocked"] is True
    assert stock["manual_control_auto_exclusion_session"] == "KRX_OPEN"
    assert emitted[-1]["stage"] == "manual_control_open_loss_auto_excluded"
    assert emitted[-1]["fields"]["manual_control_auto_exclusion_triggered"] is True
    assert emitted[-1]["fields"]["actual_order_submitted"] is False
    assert emitted[-1]["fields"]["broker_order_forbidden"] is True


def test_open_loss_session_resolves_nxt_and_krx_windows(monkeypatch):
    monkeypatch.delenv(
        "KORSTOCKSCAN_MANUAL_CONTROL_OPEN_LOSS_EXCLUSION_WINDOW_SEC", raising=False
    )

    assert (
        sniper_state_handlers._manual_control_open_loss_session(
            datetime(2026, 7, 2, 8, 0, 0)
        )
        == "NXT_OPEN"
    )
    assert (
        sniper_state_handlers._manual_control_open_loss_session(
            datetime(2026, 7, 2, 9, 0, 0)
        )
        == "KRX_OPEN"
    )
    assert (
        sniper_state_handlers._manual_control_open_loss_session(
            datetime(2026, 7, 2, 9, 6, 0)
        )
        == ""
    )


def test_open_loss_holding_auto_exclusion_ignores_non_open_window(
    monkeypatch, tmp_path
):
    path = tmp_path / "manual_control_excluded_codes.txt"
    stock = {
        "id": 4,
        "code": "005930",
        "name": "SAMSUNG",
        "status": "HOLDING",
        "strategy": "KOSPI_ML",
        "buy_price": 10000,
    }
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))

    called = {"reconcile": False}

    def mark_reconcile(*args, **kwargs):
        called["reconcile"] = True

    monkeypatch.setattr(
        sniper_state_handlers, "_reconcile_pending_entry_orders", mark_reconcile
    )
    monkeypatch.setattr(
        sniper_state_handlers,
        "_holding_ws_freshness_recover_or_block",
        lambda *args, **kwargs: (args[2], False, {}),
    )
    monkeypatch.setattr(
        sniper_state_handlers,
        "_maybe_submit_rising_missed_scout_upgrade",
        lambda *args, **kwargs: True,
    )

    sniper_state_handlers.handle_holding_state(
        stock,
        "005930",
        {"curr": 9700},
        admin_id="admin",
        market_regime="BULL",
        now_ts=2000.0,
        now_dt=datetime(2026, 7, 2, 9, 10, 0),
    )

    assert called["reconcile"] is True
    assert (
        manual_control_exclusion.evaluate_manual_control_exclusion("005930").excluded
        is False
    )


def test_hard_stop_manual_handoff_registers_and_blocks_real_sell(monkeypatch, tmp_path):
    emitted = []
    path = tmp_path / "manual_control_excluded_codes.txt"
    stock = {
        "id": 5,
        "code": "005930",
        "name": "SAMSUNG",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "buy_price": 10000,
    }
    monkeypatch.setenv("KORSTOCKSCAN_HARD_STOP_MANUAL_HANDOFF_ENABLED", "true")
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)
    monkeypatch.setattr(
        sniper_state_handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )

    blocked = sniper_state_handlers._handoff_hard_stop_to_manual_control_if_enabled(
        stock,
        "005930",
        strategy="SCALPING",
        sell_reason_type="LOSS",
        exit_rule="scalp_hard_stop_pct",
        profit_rate=-2.6,
        peak_profit=0.2,
        curr_price=9750,
        buy_price=10000,
        now_ts=1000.0,
        source_stage="standard_hard_stop_after_quote_revalidation",
    )

    assert blocked is True
    assert (
        manual_control_exclusion.evaluate_manual_control_exclusion("005930").excluded
        is True
    )
    assert path.read_text(encoding="utf-8").count("005930") == 1
    assert stock["status"] == "HOLDING"
    assert stock["manual_control_auto_hard_stop_blocked"] is True
    assert stock["manual_control_hard_stop_handoff_pending"] is False
    assert emitted[-1]["stage"] == "hard_stop_manual_control_handoff"
    assert emitted[-1]["fields"]["actual_order_submitted"] is False
    assert emitted[-1]["fields"]["broker_order_forbidden"] is True
    assert (
        emitted[-1]["fields"]["source_quality_gate"]
        == "manual_control_exclusion_active"
    )


def test_hard_stop_manual_handoff_preserves_emergency_and_simulated_exit(
    monkeypatch, tmp_path
):
    path = tmp_path / "manual_control_excluded_codes.txt"
    monkeypatch.setenv("KORSTOCKSCAN_HARD_STOP_MANUAL_HANDOFF_ENABLED", "true")
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))

    common = {
        "strategy": "SCALPING",
        "sell_reason_type": "LOSS",
        "exit_rule": "scalp_preset_hard_stop_pct",
        "profit_rate": -3.0,
        "peak_profit": 0.0,
        "curr_price": 9700,
        "buy_price": 10000,
        "now_ts": 1000.0,
        "source_stage": "preset_hard_stop_after_quote_confirmation",
    }
    assert (
        sniper_state_handlers._handoff_hard_stop_to_manual_control_if_enabled(
            {"status": "HOLDING", "strategy": "SCALPING"},
            "005930",
            emergency=True,
            **common,
        )
        is False
    )
    assert (
        sniper_state_handlers._handoff_hard_stop_to_manual_control_if_enabled(
            {
                "status": "HOLDING",
                "strategy": "SCALPING",
                "scalp_live_simulator": True,
            },
            "000660",
            **common,
        )
        is False
    )
    assert not path.exists()


def test_hard_stop_manual_handoff_blocks_and_retries_when_registration_fails(
    monkeypatch,
):
    emitted = []
    add_calls = []
    stock = {
        "status": "HOLDING",
        "strategy": "SCALPING",
        "name": "SAMSUNG",
    }
    monkeypatch.setenv("KORSTOCKSCAN_HARD_STOP_MANUAL_HANDOFF_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_HARD_STOP_MANUAL_HANDOFF_RETRY_SEC", "5")

    def fake_add(code, comment=""):
        add_calls.append((code, comment))
        if len(add_calls) == 1:
            return manual_control_exclusion.ManualControlExclusionDecision(
                False,
                "005930",
                "manual_control_exclusion_append_failed:OSError",
                "/read-only/manual.txt",
            )
        return manual_control_exclusion.ManualControlExclusionDecision(
            True,
            "005930",
            "operator_manual_control_excluded_symbol",
            "/tmp/manual.txt",
        )

    monkeypatch.setattr(
        sniper_state_handlers, "add_manual_control_exclusion_code", fake_add
    )
    monkeypatch.setattr(
        sniper_state_handlers,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )

    kwargs = {
        "strategy": "SCALPING",
        "sell_reason_type": "LOSS",
        "exit_rule": "scalp_hard_stop_pct",
        "profit_rate": -2.6,
        "peak_profit": 0.0,
        "curr_price": 9750,
        "buy_price": 10000,
        "source_stage": "standard_hard_stop_after_quote_revalidation",
    }
    assert (
        sniper_state_handlers._handoff_hard_stop_to_manual_control_if_enabled(
            stock, "005930", now_ts=1000.0, **kwargs
        )
        is True
    )
    assert stock["manual_control_hard_stop_handoff_pending"] is True
    assert stock.get("manual_control_auto_hard_stop_blocked") is None
    assert emitted[-1]["stage"] == "hard_stop_manual_control_handoff_deferred"
    assert emitted[-1]["fields"]["broker_order_forbidden"] is True

    assert (
        sniper_state_handlers._retry_pending_hard_stop_manual_handoff(
            stock, "005930", now_ts=1002.0
        )
        is True
    )
    assert len(emitted) == 1
    assert len(add_calls) == 1

    assert (
        sniper_state_handlers._retry_pending_hard_stop_manual_handoff(
            stock, "005930", now_ts=1006.0
        )
        is True
    )
    assert len(add_calls) == 2
    assert stock["manual_control_hard_stop_handoff_pending"] is False
    assert stock["manual_control_auto_hard_stop_blocked"] is True
    assert "manual_control_hard_stop_handoff_exit_rule" not in stock
    assert emitted[-1]["stage"] == "hard_stop_manual_control_handoff"
    assert emitted[-1]["fields"]["hard_stop_manual_handoff_retry_attempt"] is True


def test_pending_hard_stop_manual_handoff_runtime_off_clears_pending(monkeypatch):
    stock = {
        "status": "HOLDING",
        "strategy": "SCALPING",
        "manual_control_hard_stop_handoff_pending": True,
        "manual_control_hard_stop_handoff_last_attempt_ts": 1000.0,
        "manual_control_hard_stop_handoff_exit_rule": "scalp_hard_stop_pct",
    }
    monkeypatch.setenv("KORSTOCKSCAN_HARD_STOP_MANUAL_HANDOFF_ENABLED", "false")

    assert (
        sniper_state_handlers._retry_pending_hard_stop_manual_handoff(
            stock, "005930", now_ts=1006.0
        )
        is False
    )
    assert "manual_control_hard_stop_handoff_pending" not in stock
    assert "manual_control_hard_stop_handoff_exit_rule" not in stock


def test_holding_handler_retries_pending_hard_stop_handoff_before_quote_logic(
    monkeypatch,
    tmp_path,
):
    path = tmp_path / "manual_control_excluded_codes.txt"
    stock = {
        "id": 6,
        "code": "005930",
        "name": "SAMSUNG",
        "status": "HOLDING",
        "strategy": "SCALPING",
        "manual_control_hard_stop_handoff_pending": True,
        "manual_control_hard_stop_handoff_last_attempt_ts": 1000.0,
        "manual_control_hard_stop_handoff_exit_rule": "scalp_hard_stop_pct",
        "manual_control_hard_stop_handoff_profit_rate": -2.6,
        "manual_control_hard_stop_handoff_peak_profit": 0.1,
        "manual_control_hard_stop_handoff_curr_price": 9750,
        "manual_control_hard_stop_handoff_buy_price": 10000,
        "manual_control_hard_stop_handoff_source_stage": (
            "standard_hard_stop_after_quote_revalidation"
        ),
    }
    monkeypatch.setenv("KORSTOCKSCAN_HARD_STOP_MANUAL_HANDOFF_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_HARD_STOP_MANUAL_HANDOFF_RETRY_SEC", "5")
    monkeypatch.setenv(manual_control_exclusion.EXCLUDED_CODES_FILE_ENV, str(path))
    monkeypatch.delenv(manual_control_exclusion.EXCLUDED_CODES_ENV, raising=False)

    def fail_quote_logic(*args, **kwargs):
        raise AssertionError(
            "pending handoff retry must run before holding quote logic"
        )

    monkeypatch.setattr(
        sniper_state_handlers,
        "_holding_ws_freshness_recover_or_block",
        fail_quote_logic,
    )

    sniper_state_handlers.handle_holding_state(
        stock,
        "005930",
        {"curr": 10100},
        admin_id="admin",
        market_regime="BULL",
        now_ts=1006.0,
        now_dt=datetime(2026, 7, 14, 15, 0, 0),
    )

    assert stock["status"] == "HOLDING"
    assert stock["manual_control_auto_hard_stop_blocked"] is True
    assert (
        manual_control_exclusion.evaluate_manual_control_exclusion("005930").excluded
        is True
    )
