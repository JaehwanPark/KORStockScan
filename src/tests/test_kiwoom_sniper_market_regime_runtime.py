from types import SimpleNamespace

from src.engine import kiwoom_sniper_v2
from src.engine import sniper_market_regime
from src.utils.constants import TRADING_RULES


class _RuntimeRecordSession:
    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return False


class _RuntimeRecordDB:
    def __init__(self, record_id):
        self.record_id = record_id

    def get_session(self):
        return _RuntimeRecordSession()

    def find_reusable_watching_record(self, session, *, rec_date, stock_code, strategy=None):
        return SimpleNamespace(id=self.record_id)


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


def test_scalping_scanner_promoted_target_attaches_active_watching(monkeypatch):
    emitted = []
    published = []
    monkeypatch.setattr(kiwoom_sniper_v2, "ACTIVE_TARGETS", [])
    monkeypatch.setattr(kiwoom_sniper_v2, "_resolve_stock_marcap", lambda stock, code: 123456789)
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"pipeline": pipeline, "name": name, "code": code, "stage": stage, "fields": fields or {}}
        ),
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda name, payload: published.append((name, payload))),
    )

    attached = kiwoom_sniper_v2.handle_scalping_scanner_promoted_target(
        {
            "record_id": 77,
            "code": "005930",
            "name": "SAMSUNG",
            "strategy": "SCALPING",
            "trade_type": "SCALP",
            "status": "WATCHING",
            "position_tag": "SCANNER",
            "buy_price": 70000,
            "added_time": 1000.0,
            "entry_armed_at_epoch": 1000.0,
            "scanner_promotion_id": "SCANPROM-005930-1000000",
            "scanner_promotion_reason": "rank_jump_acceleration",
            "scanner_promotion_emitted_epoch": "1000.000",
            "source_signature": "REALTIME_RANK_START",
            "current_price_observed": 70000,
            "price_delta_since_first_seen_pct": "0.50",
            "scanner_source_family": "scalping_scanner_rising_start_source_v1",
            "scanner_source_role": "primary_rising_start",
        }
    )

    assert attached is True
    assert kiwoom_sniper_v2.ACTIVE_TARGETS == [
        {
            "id": 77,
            "code": "005930",
            "name": "SAMSUNG",
            "strategy": "SCALPING",
            "status": "WATCHING",
            "type": "SCALP",
            "buy_price": 70000,
            "added_time": 1000.0,
            "entry_armed_at_epoch": 1000.0,
            "position_tag": "SCANNER",
            "scanner_promotion_id": "SCANPROM-005930-1000000",
            "scanner_promotion_reason": "rank_jump_acceleration",
            "scanner_promotion_emitted_epoch": "1000.000",
            "source_signature": "REALTIME_RANK_START",
            "marcap": 123456789,
        }
    ]
    assert published == [("COMMAND_WS_REG", {"codes": ["005930"]})]
    assert emitted[-1]["stage"] == "scalping_scanner_runtime_target_attach"
    assert emitted[-1]["fields"]["runtime_target_attach_outcome"] == "attached"
    assert emitted[-1]["fields"]["actual_order_submitted"] is False
    assert emitted[-1]["fields"]["broker_order_forbidden"] is True


def test_scalping_scanner_promoted_target_does_not_override_holding(monkeypatch):
    emitted = []
    published = []
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "ACTIVE_TARGETS",
        [{"code": "005930", "name": "SAMSUNG", "strategy": "SCALPING", "status": "HOLDING"}],
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda name, payload: published.append((name, payload))),
    )

    attached = kiwoom_sniper_v2.handle_scalping_scanner_promoted_target(
        {
            "record_id": 78,
            "code": "005930",
            "name": "SAMSUNG",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "buy_price": 70000,
            "scanner_promotion_id": "SCANPROM-005930-1000001",
            "scanner_promotion_emitted_epoch": "1000.001",
            "source_signature": "PRICE_JUMP_START",
        }
    )

    assert attached is False
    assert kiwoom_sniper_v2.ACTIVE_TARGETS == [
        {"code": "005930", "name": "SAMSUNG", "strategy": "SCALPING", "status": "HOLDING"}
    ]
    assert published == []
    assert emitted[-1]["fields"]["runtime_target_attach_outcome"] == "skipped"
    assert emitted[-1]["fields"]["runtime_target_attach_reason"] == "same_symbol_active_order_or_holding"


def test_scalping_scanner_promoted_target_refreshes_existing_watching_and_ws(monkeypatch):
    emitted = []
    published = []
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "ACTIVE_TARGETS",
        [
            {
                "id": 10,
                "code": "005930",
                "name": "OLD",
                "strategy": "SCALPING",
                "status": "WATCHING",
                "position_tag": "SCANNER",
                "buy_price": 69000,
            }
        ],
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda name, payload: published.append((name, payload))),
    )

    refreshed = kiwoom_sniper_v2.handle_scalping_scanner_promoted_target(
        {
            "record_id": 77,
            "code": "005930",
            "name": "NEW",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "buy_price": 70000,
            "added_time": 1001.0,
            "scanner_promotion_id": "SCANPROM-005930-1001000",
            "scanner_promotion_emitted_epoch": "1001.000",
            "source_signature": "PRICE_JUMP_START",
        }
    )

    assert refreshed is True
    assert kiwoom_sniper_v2.ACTIVE_TARGETS[0]["id"] == 77
    assert kiwoom_sniper_v2.ACTIVE_TARGETS[0]["name"] == "NEW"
    assert kiwoom_sniper_v2.ACTIVE_TARGETS[0]["buy_price"] == 70000
    assert published == [("COMMAND_WS_REG", {"codes": ["005930"]})]
    assert emitted[-1]["fields"]["runtime_target_attach_outcome"] == "refreshed"


def test_scalping_scanner_promoted_target_hydrates_missing_record_id(monkeypatch):
    emitted = []
    published = []
    monkeypatch.setattr(kiwoom_sniper_v2, "ACTIVE_TARGETS", [])
    monkeypatch.setattr(kiwoom_sniper_v2, "DB", _RuntimeRecordDB(record_id=88))
    monkeypatch.setattr(kiwoom_sniper_v2, "_resolve_stock_marcap", lambda stock, code: 0)
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "fields": fields or {}}
        ),
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda name, payload: published.append((name, payload))),
    )

    attached = kiwoom_sniper_v2.handle_scalping_scanner_promoted_target(
        {
            "code": "005930",
            "name": "SAMSUNG",
            "strategy": "SCALPING",
            "position_tag": "SCANNER",
            "buy_price": 70000,
            "scanner_promotion_id": "SCANPROM-005930-1001001",
            "scanner_promotion_emitted_epoch": "1001.001",
            "source_signature": "PRICE_JUMP_START",
        }
    )

    assert attached is True
    assert kiwoom_sniper_v2.ACTIVE_TARGETS[0]["id"] == 88
    assert emitted[-1]["fields"]["runtime_record_id"] == 88
    assert published == [("COMMAND_WS_REG", {"codes": ["005930"]})]


def test_db_poll_scanner_target_attach_logs_recovery(monkeypatch):
    emitted = []
    published = []
    targets = []
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "emit_pipeline_event",
        lambda pipeline, name, code, stage, *, record_id=None, fields=None: emitted.append(
            {"stage": stage, "code": code, "fields": fields or {}}
        ),
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda name, payload: published.append((name, payload))),
    )

    attached = kiwoom_sniper_v2.attach_db_poll_target_if_missing(
        {
            "id": 99,
            "code": "005930",
            "name": "SAMSUNG",
            "strategy": "SCALPING",
            "status": "WATCHING",
            "position_tag": "SCANNER",
            "buy_price": 70000,
            "type": "SCALP",
        },
        targets,
        now_ts=1002.0,
    )

    assert attached is True
    assert targets[0]["id"] == 99
    assert targets[0]["added_time"] == 1002.0
    assert published == [("COMMAND_WS_REG", {"codes": ["005930"]})]
    assert emitted[-1]["stage"] == "scalping_scanner_runtime_target_attach"
    assert emitted[-1]["fields"]["runtime_target_attach_outcome"] == "db_poll_attached"
    assert emitted[-1]["fields"]["runtime_target_attach_reason"] == "eventbus_attach_missing_recovered_from_db_poll"
    assert emitted[-1]["fields"]["runtime_record_id"] == 99


def test_db_poll_target_attach_skips_existing_real_target(monkeypatch):
    emitted = []
    published = []
    targets = [{"code": "005930", "strategy": "SCALPING", "status": "WATCHING"}]
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "emit_pipeline_event",
        lambda *args, **kwargs: emitted.append((args, kwargs)),
    )
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "event_bus",
        SimpleNamespace(publish=lambda name, payload: published.append((name, payload))),
    )

    attached = kiwoom_sniper_v2.attach_db_poll_target_if_missing(
        {
            "id": 100,
            "code": "005930",
            "name": "SAMSUNG",
            "strategy": "SCALPING",
            "status": "WATCHING",
            "position_tag": "SCANNER",
        },
        targets,
        now_ts=1003.0,
    )

    assert attached is False
    assert targets == [{"code": "005930", "strategy": "SCALPING", "status": "WATCHING"}]
    assert published == []
    assert emitted == []


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
