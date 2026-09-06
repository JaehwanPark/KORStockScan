import ast
import inspect
from datetime import time as datetime_time
from types import SimpleNamespace

from sqlalchemy.orm.exc import DetachedInstanceError

from src.database.models import RecommendationHistory
from src.engine import kiwoom_sniper_v2, sniper_state_handlers
from src.engine.sniper_overnight_gatekeeper import (
    _apply_overnight_flow_override,
    _clean_telegram_text,
    _eod_label,
    _format_order_error,
    _humanize_eod_action,
    _limit_down_live_overnight_forbidden,
    _overnight_gatekeeper_enabled,
    run_scalping_overnight_gatekeeper,
    _snapshot_record,
    _submit_overnight_dual_persona_shadow,
)
from src.engine.sniper_time import TIME_SCALPING_OVERNIGHT_DECISION


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


def test_overnight_gatekeeper_ignores_runtime_true_override(monkeypatch):
    monkeypatch.setattr(
        "src.engine.sniper_overnight_gatekeeper.TRADING_RULES",
        SimpleNamespace(SCALPING_OVERNIGHT_GATEKEEPER_ENABLED=True),
    )

    assert _overnight_gatekeeper_enabled() is False
    assert run_scalping_overnight_gatekeeper(ai_engine=object()) is False


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
    )
    assert krx["should_exit"] is True
    assert krx["terminal_venue"] == "KRX"

    monkeypatch.setattr(
        sniper_state_handlers,
        "_holding_sell_nxt_enabled_status",
        lambda *_args: (True, "test.nxt"),
    )
    before_nxt_close = sniper_state_handlers._scalping_same_session_terminal_exit_fields(
        stock,
        "005930",
        strategy="SCALPING",
        now_t=datetime_time(15, 15),
    )
    nxt_close = sniper_state_handlers._scalping_same_session_terminal_exit_fields(
        stock,
        "005930",
        strategy="SCALPING",
        now_t=datetime_time(19, 45),
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


def test_limit_down_live_source_forbids_overnight_hold():
    assert _limit_down_live_overnight_forbidden(
        {"source_signature": "PRICE_JUMP_START,LIMIT_DOWN_LIVE_UNLOCK"}
    )
    assert not _limit_down_live_overnight_forbidden(
        {"source_signature": "PRICE_JUMP_START"}
    )


def test_run_scalping_overnight_gatekeeper_returns_false_when_disabled(monkeypatch):
    monkeypatch.setattr(
        "src.engine.sniper_overnight_gatekeeper.TRADING_RULES",
        SimpleNamespace(SCALPING_OVERNIGHT_GATEKEEPER_ENABLED=False),
    )

    assert run_scalping_overnight_gatekeeper(ai_engine=object()) is False


def test_run_sniper_eod_holding_fallback_is_permanently_disabled():
    source = inspect.getsource(kiwoom_sniper_v2.run_sniper)
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


def test_snapshot_record_survives_detached_instance():
    record = RecommendationHistory(
        id=101,
        stock_code="005930",
        stock_name="삼성전자",
        status="HOLDING",
        buy_qty=3,
        buy_price=70100,
        buy_time="09:10:00",
    )

    snapshot = _snapshot_record(record)

    assert snapshot.id == 101
    assert snapshot.stock_code == "005930"
    assert snapshot.stock_name == "삼성전자"
    assert snapshot.status == "HOLDING"
    assert snapshot.buy_qty == 3.0
    assert snapshot.buy_price == 70100.0
    assert snapshot.buy_time == "09:10:00"


def test_snapshot_record_can_be_built_before_detached_refresh_failure():
    record = RecommendationHistory(
        id=102,
        stock_code="000660",
        stock_name="SK하이닉스",
        status="SELL_ORDERED",
        buy_qty=1,
        buy_price=201000,
        buy_time="14:55:00",
    )

    snapshot = _snapshot_record(record)

    # Simulate the practical guarantee we need: gatekeeper should rely on the
    # immutable snapshot, not on the ORM instance after session teardown.
    class DetachedRecord:
        @property
        def status(self):
            raise DetachedInstanceError("detached")

    detached = DetachedRecord()

    assert snapshot.status == "SELL_ORDERED"
    try:
        _ = detached.status
        raised = False
    except DetachedInstanceError:
        raised = True

    assert raised is True


def test_format_order_error_prefers_return_msg_and_code():
    msg = _format_order_error(
        {"return_msg": "[2000](521790:주문 불가능합니다.)", "return_code": 20}
    )
    assert msg == "[2000](521790:주문 불가능합니다.) (code=20)"


def test_format_order_error_fallback_to_string():
    assert _format_order_error("timeout") == "timeout"


def test_format_order_error_unescapes_markdown_style_backslashes():
    msg = _format_order_error(
        {"return_msg": r"[2000]\(521790:주문 불가능합니다\.\)", "return_code": 20}
    )
    assert msg == "[2000](521790:주문 불가능합니다.) (code=20)"


def test_humanize_eod_action_and_clean_text():
    assert _humanize_eod_action("SELL_TODAY") == "당일 청산"
    assert _humanize_eod_action("HOLD_OVERNIGHT") == "오버나이트 유지"
    assert _clean_telegram_text(r"\[ABC\]\(test\)\.") == "[ABC](test)."


def test_submit_overnight_dual_persona_shadow_is_disabled_when_dual_persona_off(
    monkeypatch,
):
    submit_calls = []
    monkeypatch.setattr(
        "src.engine.sniper_overnight_gatekeeper.TRADING_RULES",
        SimpleNamespace(OPENAI_DUAL_PERSONA_ENABLED=False),
    )
    monkeypatch.setattr(
        "src.engine.sniper_overnight_gatekeeper.DUAL_PERSONA_ENGINE",
        SimpleNamespace(
            submit_overnight_shadow=lambda **kwargs: submit_calls.append(kwargs)
        ),
    )

    _submit_overnight_dual_persona_shadow(
        "테스트", "005930", {"curr_price": 70000}, {"action": "SELL_TODAY"}
    )

    assert submit_calls == []


def test_overnight_flow_hold_cannot_override_sell_with_blocked_context(monkeypatch):
    logs = []
    monkeypatch.setattr(
        "src.engine.sniper_overnight_gatekeeper._log_holding_pipeline",
        lambda stock, code, stage, **fields: logs.append((stage, fields)),
    )
    blocked_context = {
        "schema": "holding_decision_context_v1",
        "enabled": True,
        "source_quality": {
            "status": "blocked",
            "hold_defer_allowed": False,
            "blockers": ["order_or_quantity_conflict"],
        },
        "flow_signature": {
            "executable_pnl_pct": -0.4,
            "candle_regime": "range",
            "signed_tape_state": "missing",
            "ofi_regime": "neutral",
            "source_quality_status": "blocked",
        },
    }
    ctx = {
        "avg_price": 10_000,
        "curr_price": 9_960,
        "buy_qty": 3,
        "pnl_pct": -0.4,
        "_holding_decision_context": blocked_context,
        "_holding_recent_ticks": [{"price": 9960, "volume": 10}],
        "_holding_recent_candles": [{"현재가": 9960}],
    }
    record = SimpleNamespace(
        stock_code="005930",
        stock_name="테스트",
        buy_price=10_000,
        buy_qty=3,
        status="HOLDING",
    )

    class HoldAI:
        def evaluate_scalping_holding_flow(self, *args, **kwargs):
            assert kwargs["holding_context"] is blocked_context
            return {
                "action": "HOLD",
                "score": 80,
                "flow_state": "absorption",
                "reason": "hold",
                "evidence": ["support"],
                "ai_parse_fail": False,
            }

    decision = _apply_overnight_flow_override(
        record,
        {"buy_qty": 3},
        {"curr": 9960},
        ctx,
        {"action": "SELL_TODAY", "confidence": 70, "reason": "sell"},
        HoldAI(),
    )

    assert decision["action"] == "SELL_TODAY"
    assert any(
        stage == "overnight_flow_override_exit_confirmed"
        and fields.get("force_reason") == "holding_context_cannot_defer"
        for stage, fields in logs
    )
