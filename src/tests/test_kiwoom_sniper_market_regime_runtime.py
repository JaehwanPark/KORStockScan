from types import SimpleNamespace

from src.engine import kiwoom_sniper_v2
from src.engine import sniper_market_regime
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


def test_risk_off_without_confirmed_context_is_prior_not_block(monkeypatch):
    class FakeMarketRegime:
        def refresh_if_needed(self):
            return SimpleNamespace(
                risk_state="RISK_OFF",
                allow_swing_entry=False,
                swing_score=25,
                debug={"component_scores": {}, "score_threshold": 70},
                reasons=["unit"],
                vix_extreme=False,
                vix_two_day_down=False,
                vix_peak_passed=False,
                oil_reversal=False,
                wti_dead_cross=False,
                wti_from_recent_high_pct=0.0,
                fng_value=0.0,
                fng_prev=0.0,
                fng_recovery=False,
                fng_extreme_fear=False,
                vix_close=0.0,
                wti_rsi=0.0,
            )

    monkeypatch.setattr(sniper_market_regime, "MARKET_REGIME", FakeMarketRegime())
    monkeypatch.setattr(
        sniper_market_regime,
        "_load_confirmed_risk_context",
        lambda: {
            "panic_state": "NORMAL",
            "confirmed_risk_off_advisory": False,
            "risk_off_advisory": False,
            "single_market_risk_off_advisory": False,
            "confirmed_risk_block": False,
        },
    )

    blocked, reason, meta = sniper_market_regime.should_block_swing_entry_by_market_regime("KOSPI_ML")

    assert blocked is False
    assert "risk=RISK_OFF" in reason
    assert "risk_context=not_confirmed" in reason
    assert meta["market_regime_prior_observed"] is True
    assert meta["market_regime_prior_reason"] == "recovery_gate_signal_insufficient"


def test_non_swing_strategy_does_not_refresh_market_regime(monkeypatch):
    class BrokenMarketRegime:
        def refresh_if_needed(self):
            raise AssertionError("non-swing strategy should not refresh market regime")

    monkeypatch.setattr(sniper_market_regime, "MARKET_REGIME", BrokenMarketRegime())

    blocked, reason, meta = sniper_market_regime.should_block_swing_entry_by_market_regime("SCALPING")

    assert blocked is False
    assert reason == ""
    assert meta["strategy_scope"] == "non_swing"
    assert meta["confirmed_risk_block"] is False


def test_single_market_risk_off_is_prior_not_block(monkeypatch):
    class FakeMarketRegime:
        def refresh_if_needed(self):
            return SimpleNamespace(
                risk_state="RISK_OFF",
                allow_swing_entry=False,
                swing_score=25,
                debug={"component_scores": {}, "score_threshold": 70},
                reasons=[],
                vix_extreme=False,
                vix_two_day_down=False,
                vix_peak_passed=False,
                oil_reversal=False,
                wti_dead_cross=False,
                wti_from_recent_high_pct=0.0,
                fng_value=0.0,
                fng_prev=0.0,
                fng_recovery=False,
                fng_extreme_fear=False,
                vix_close=0.0,
                wti_rsi=0.0,
            )

    monkeypatch.setattr(sniper_market_regime, "MARKET_REGIME", FakeMarketRegime())
    monkeypatch.setattr(
        sniper_market_regime,
        "_load_confirmed_risk_context",
        lambda: {
            "panic_state": "NORMAL",
            "confirmed_risk_off_advisory": False,
            "risk_off_advisory": False,
            "single_market_risk_off_advisory": True,
            "confirmed_risk_block": False,
        },
    )

    blocked, _, meta = sniper_market_regime.should_block_swing_entry_by_market_regime("KOSPI_ML")

    assert blocked is False
    assert meta["market_regime_prior_reason"] == "single_market_risk_off_advisory"


def test_oil_only_recovery_gate_deficit_is_prior_not_block(monkeypatch):
    class FakeMarketRegime:
        def refresh_if_needed(self):
            return SimpleNamespace(
                risk_state="RISK_OFF",
                allow_swing_entry=False,
                swing_score=35,
                swing_entry_recovery_gate_score=35,
                recovery_gate_state="INSUFFICIENT",
                swing_recovery_gate_label="INSUFFICIENT",
                recovery_gate_reason="oil_only_recovery_signal_insufficient",
                oil_only_recovery_prior=True,
                market_regime_continuous_score=73.1543,
                market_regime_continuous_label="RISK_ON",
                market_regime_source_quality="valid",
                debug={"component_scores": {"vix": 0, "oil": 35, "fng": 0, "local_breadth": 0}, "score_threshold": 70},
                reasons=["원유 반전 시그널"],
                vix_extreme=False,
                vix_two_day_down=False,
                vix_peak_passed=False,
                oil_reversal=True,
                wti_dead_cross=False,
                wti_from_recent_high_pct=-5.0,
                fng_value=15.0,
                fng_prev=15.0,
                fng_recovery=False,
                fng_extreme_fear=False,
                vix_close=22.99,
                wti_rsi=45.0,
            )

    monkeypatch.setattr(sniper_market_regime, "MARKET_REGIME", FakeMarketRegime())
    monkeypatch.setattr(
        sniper_market_regime,
        "_load_confirmed_risk_context",
        lambda: {
            "panic_state": "NORMAL",
            "confirmed_risk_off_advisory": False,
            "risk_off_advisory": False,
            "single_market_risk_off_advisory": False,
            "confirmed_risk_block": False,
        },
    )

    blocked, reason, meta = sniper_market_regime.should_block_swing_entry_by_market_regime("KOSPI_ML")

    assert blocked is False
    assert "legacy_recovery_gate_score=35/70" in reason
    assert "continuous_label=RISK_ON" in reason
    assert meta["market_regime_prior_reason"] == "oil_only_recovery_signal_insufficient"
    assert meta["oil_only_recovery_prior"] is True
    assert meta["market_regime_continuous_label"] == "RISK_ON"


def test_confirmed_panic_context_blocks_swing_market_regime(monkeypatch):
    class FakeMarketRegime:
        def refresh_if_needed(self):
            return SimpleNamespace(
                risk_state="RISK_OFF",
                allow_swing_entry=False,
                swing_score=25,
                debug={"component_scores": {}, "score_threshold": 70},
                reasons=[],
                vix_extreme=False,
                vix_two_day_down=False,
                vix_peak_passed=False,
                oil_reversal=False,
                wti_dead_cross=False,
                wti_from_recent_high_pct=0.0,
                fng_value=0.0,
                fng_prev=0.0,
                fng_recovery=False,
                fng_extreme_fear=False,
                vix_close=0.0,
                wti_rsi=0.0,
            )

    monkeypatch.setattr(sniper_market_regime, "MARKET_REGIME", FakeMarketRegime())
    monkeypatch.setattr(
        sniper_market_regime,
        "_load_confirmed_risk_context",
        lambda: {
            "panic_state": "PANIC_SELL",
            "confirmed_risk_off_advisory": False,
            "risk_off_advisory": False,
            "single_market_risk_off_advisory": False,
            "confirmed_risk_block": True,
        },
    )

    blocked, _, meta = sniper_market_regime.should_block_swing_entry_by_market_regime("KOSPI_ML")

    assert blocked is True
    assert meta["confirmed_risk_block"] is True
    assert meta["market_regime_block_reason"] == "confirmed_risk_context"


def test_string_false_risk_flags_do_not_confirm_block(monkeypatch):
    class FakeMarketRegime:
        def refresh_if_needed(self):
            return SimpleNamespace(
                risk_state="RISK_OFF",
                allow_swing_entry=False,
                swing_score=25,
                debug={"component_scores": {}, "score_threshold": 70},
                reasons=[],
                vix_extreme=False,
                vix_two_day_down=False,
                vix_peak_passed=False,
                oil_reversal=False,
                wti_dead_cross=False,
                wti_from_recent_high_pct=0.0,
                fng_value=0.0,
                fng_prev=0.0,
                fng_recovery=False,
                fng_extreme_fear=False,
                vix_close=0.0,
                wti_rsi=0.0,
            )

    monkeypatch.setattr(sniper_market_regime, "MARKET_REGIME", FakeMarketRegime())
    monkeypatch.setattr(
        sniper_market_regime,
        "_load_confirmed_risk_context",
        lambda: {
            "panic_state": "NORMAL",
            "confirmed_risk_off_advisory": "False",
            "risk_off_advisory": "False",
            "single_market_risk_off_advisory": "False",
            "confirmed_risk_block": False,
        },
    )

    blocked, _, meta = sniper_market_regime.should_block_swing_entry_by_market_regime("KOSPI_ML")

    assert blocked is False
    assert meta["market_regime_prior_observed"] is True


def test_truthy_flag_treats_false_strings_as_false():
    assert sniper_market_regime._truthy_flag("False") is False
    assert sniper_market_regime._truthy_flag("0") is False
    assert sniper_market_regime._truthy_flag("true") is True
