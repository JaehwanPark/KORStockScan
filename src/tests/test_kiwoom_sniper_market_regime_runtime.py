from types import SimpleNamespace

from src.engine import kiwoom_sniper_v2
from src.utils.constants import TRADING_RULES


def test_current_market_regime_code_returns_regime_code(monkeypatch):
    class FakeMarketRegime:
        def refresh_if_needed(self):
            return SimpleNamespace(
                risk_state="RISK_ON",
                allow_swing_entry=True,
                swing_score=80,
            )

    monkeypatch.setattr(kiwoom_sniper_v2, "MARKET_REGIME", FakeMarketRegime())

    assert kiwoom_sniper_v2._current_market_regime_code() == "BULL"


def test_current_market_regime_code_falls_back_to_neutral(monkeypatch):
    class BrokenMarketRegime:
        def refresh_if_needed(self):
            raise RuntimeError("boom")

    monkeypatch.setattr(kiwoom_sniper_v2, "MARKET_REGIME", BrokenMarketRegime())

    assert kiwoom_sniper_v2._current_market_regime_code() == "NEUTRAL"


def test_restore_holding_runtime_state_rehydrates_scalping_defaults(monkeypatch):
    monkeypatch.setattr(kiwoom_sniper_v2, "highest_prices", {})

    targets = [
        {
            "id": 1,
            "code": "123456",
            "name": "TEST",
            "status": "HOLDING",
            "strategy": "SCALPING",
            "position_tag": "SCALP_BASE",
            "buy_price": 10000,
            "buy_qty": 5,
            "buy_time": "2026-04-08 09:10:00",
        }
    ]

    kiwoom_sniper_v2._restore_holding_runtime_state(targets)
    stock = targets[0]

    assert stock["exit_mode"] == "SCALP_PRESET_TP"
    assert int(stock["preset_tp_price"]) > 10000
    assert stock["hard_stop_pct"] == TRADING_RULES.SCALP_PRESET_HARD_STOP_PCT
    assert stock["buy_qty"] == 5
    assert stock["holding_started_at"] == "2026-04-08 09:10:00"
    assert kiwoom_sniper_v2.highest_prices["123456"] == 10000
