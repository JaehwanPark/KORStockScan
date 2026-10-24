import math
from decimal import Decimal
from unittest.mock import Mock

import pytest

from src.engine import kiwoom_sniper_v2
from src.engine import sniper_scale_in
from src.engine import sniper_state_handlers
from src.utils.numeric import safe_float


@pytest.mark.parametrize(
    "consumer", [kiwoom_sniper_v2, sniper_state_handlers, sniper_scale_in]
)
def test_numeric_consumers_share_one_function(consumer):
    assert consumer._safe_float is safe_float


def test_shared_numeric_owner_remains_in_recorded_and_loaded_policy_identity(
    monkeypatch,
):
    import hashlib
    from pathlib import Path
    from src.engine.lifecycle import avg_down_policy_replay as replay
    from src.utils import numeric

    assert (
        replay.implementation_identity()["src/utils/numeric.py"]
        == hashlib.sha256(Path(numeric.__file__).read_bytes()).hexdigest()
    )
    key = "src.utils.numeric.safe_float"
    before = replay.loaded_code_identity(sniper_state_handlers)
    assert key in before

    def changed(value, default=0.0):
        return default

    monkeypatch.setattr(safe_float, "__code__", changed.__code__)
    after = replay.loaded_code_identity(sniper_state_handlers)
    assert before[key] != after[key]


@pytest.mark.parametrize(
    "value",
    [
        None,
        "",
        "  ",
        "NaN",
        " NaT ",
        "none",
        "inf",
        "+inf",
        "-inf",
        math.nan,
        math.inf,
        -math.inf,
        "1e309",
        "1,000",
        "5%",
        "bad",
        10**1000,
    ],
)
@pytest.mark.parametrize("default", [0.0, None, -7.5, math.nan, object()])
def test_invalid_numeric_input_preserves_default_identity(value, default):
    assert safe_float(value, default) is default


@pytest.mark.parametrize(
    "value,expected",
    [
        (False, 0.0),
        (True, 1.0),
        (0, 0.0),
        (-2.5, -2.5),
        (" 1.25 ", 1.25),
        ("1e3", 1000.0),
        (b"2.5", 2.5),
        (Decimal("-1.25"), -1.25),
        (-0.0, -0.0),
        ("-0", -0.0),
    ],
)
def test_numeric_input_preserves_float_semantics(value, expected):
    actual = safe_float(value, None)
    assert type(actual) is float
    assert actual == expected
    assert math.copysign(1, actual) == math.copysign(1, expected)


def test_numeric_conversion_protocol_runs_once_and_does_not_catch_base_exception():
    calls = []

    class Value:
        def __float__(self):
            calls.append("convert")
            return 2.5

    class Invalid:
        def __float__(self):
            raise RuntimeError("invalid input")

    class Interrupted:
        def __float__(self):
            raise KeyboardInterrupt

    assert safe_float(Value()) == 2.5
    assert calls == ["convert"]
    assert safe_float(Invalid(), None) is None
    assert safe_float(Invalid()) == 0.0
    with pytest.raises(KeyboardInterrupt):
        safe_float(Interrupted())


def test_sniper_safe_numeric_helpers_reject_nan_and_inf():
    assert kiwoom_sniper_v2._safe_int(float("nan"), 7) == 7
    assert kiwoom_sniper_v2._safe_int("inf", 7) == 7
    assert kiwoom_sniper_v2._safe_float(float("-inf"), 1.5) == 1.5

    assert sniper_state_handlers._safe_int(float("nan"), 3) == 3
    assert sniper_state_handlers._safe_float("nan", 2.5) == 2.5


@pytest.mark.parametrize("field", ["buy_price", "buy_qty"])
@pytest.mark.parametrize("invalid", [None, "nan", math.nan, math.inf, -math.inf])
def test_active_fast_exit_rejects_invalid_position_numbers(monkeypatch, field, invalid):
    # The old soft-stop expert is retired. Exercise the current numeric guard
    # before quote recovery, state mutation, or SELL dispatch instead.
    stock = {
        "strategy": "SCALPING",
        "status": "HOLDING",
        "buy_price": 10000,
        "buy_qty": 3,
    }
    stock[field] = invalid
    before = stock.copy()
    for name, result in (
        ("_scalp_fast_exit_guard_active", True),
        ("_is_any_simulated_position", False),
        ("_has_active_sell_order_pending", False),
        ("_manual_control_exclusion_blocked", False),
    ):
        monkeypatch.setattr(sniper_state_handlers, name, Mock(return_value=result))
    peak = Mock(side_effect=AssertionError("invalid position reached quote evaluation"))
    dispatch = Mock(
        side_effect=AssertionError("invalid position reached SELL dispatch")
    )
    monkeypatch.setattr(sniper_state_handlers, "_scalp_trailing_trusted_peak", peak)
    monkeypatch.setattr(sniper_state_handlers, "_dispatch_scalp_preset_exit", dispatch)

    assert (
        sniper_state_handlers._evaluate_and_dispatch_fast_scalp_exit(
            stock, "005930", {}, now_ts=1_777_532_025.0
        )
        is False
    )
    peak.assert_not_called()
    dispatch.assert_not_called()
    assert stock == before


def test_scale_in_qty_absorbs_nan_buy_qty():
    details = sniper_scale_in.describe_scale_in_qty(
        {"buy_qty": math.nan},
        curr_price=10000,
        deposit=1_000_000,
        add_type="AVG_DOWN",
        strategy="SCALPING",
    )

    assert details["qty"] == 0
