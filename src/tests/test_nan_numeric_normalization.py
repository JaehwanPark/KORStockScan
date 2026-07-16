import math

from src.engine import kiwoom_sniper_v2
from src.engine import sniper_scale_in
from src.engine import sniper_state_handlers


def test_sniper_safe_numeric_helpers_reject_nan_and_inf():
    assert kiwoom_sniper_v2._safe_int(float("nan"), 7) == 7
    assert kiwoom_sniper_v2._safe_int("inf", 7) == 7
    assert kiwoom_sniper_v2._safe_float(float("-inf"), 1.5) == 1.5

    assert sniper_state_handlers._safe_int(float("nan"), 3) == 3
    assert sniper_state_handlers._safe_float("nan", 2.5) == 2.5


def test_soft_stop_expert_decision_absorbs_nan_runtime_state(monkeypatch):
    monkeypatch.setattr(
        sniper_state_handlers, "_rule_bool", lambda name, default=False: True
    )
    monkeypatch.setattr(
        sniper_state_handlers, "_rule_int", lambda name, default=0: default
    )
    monkeypatch.setattr(
        sniper_state_handlers, "_rule_float", lambda name, default=0.0: default
    )
    monkeypatch.setattr(
        sniper_state_handlers, "_soft_stop_expert_time_gate_active", lambda now_ts: True
    )

    decision = sniper_state_handlers._build_soft_stop_expert_decision(
        {
            "buy_qty": float("nan"),
            "soft_stop_absorption_extension_count": float("nan"),
            "soft_stop_absorption_extension_started_at": float("nan"),
        },
        now_ts=1_777_532_025.0,
        profit_rate=-0.8,
        peak_profit=0.0,
        current_ai_score=60.0,
        held_sec=90,
        curr_price=10000,
        dynamic_stop_pct=-0.7,
        emergency_pct=-2.0,
        grace_elapsed_sec=30,
        grace_sec=20,
    )

    assert decision["extension_count"] == 0
    assert decision["extension_started_at"] == 0.0
    assert decision["would_trim_qty"] == 0


def test_scale_in_qty_absorbs_nan_buy_qty():
    details = sniper_scale_in.describe_scale_in_qty(
        {"buy_qty": math.nan},
        curr_price=10000,
        deposit=1_000_000,
        add_type="PYRAMID",
        strategy="SCALPING",
    )

    assert details["qty"] == 0
