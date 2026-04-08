from datetime import datetime
from types import SimpleNamespace

import src.engine.sniper_state_handlers as state_handlers


class _FakeDateTime(datetime):
    _fixed_now = datetime(2026, 4, 8, 9, 10, 0)

    @classmethod
    def now(cls, tz=None):
        return cls._fixed_now


class _DummyRadar:
    def analyze_signal_integrated(self, ws_data, ai_prob):
        return 82.0, {"curr": ws_data.get("curr", 0)}, "BUY", [], {"score": 82.0}


class _DummyAIEngine:
    def evaluate_realtime_gatekeeper(self, **kwargs):
        return {
            "allow_entry": False,
            "action_label": "눌림 대기",
            "report": "pullback wait",
            "cache_hit": False,
            "cache_mode": "miss",
        }


def test_gatekeeper_fast_reuse_bypass_logs_sentinel_when_fast_timestamp_missing(monkeypatch):
    state_handlers.COOLDOWNS = {}
    state_handlers.ALERTED_STOCKS = set()
    state_handlers.HIGHEST_PRICES = {}
    state_handlers.LAST_AI_CALL_TIMES = {}
    state_handlers.LAST_LOG_TIMES = {}
    state_handlers.EVENT_BUS = SimpleNamespace(publish=lambda *args, **kwargs: None)
    state_handlers.TRADING_RULES = SimpleNamespace(
        VPW_STRONG_LIMIT=105,
        BUY_SCORE_THRESHOLD=70,
        INVEST_RATIO_KOSPI_MIN=0.10,
        INVEST_RATIO_KOSPI_MAX=0.30,
        AI_SCORE_THRESHOLD_KOSPI=60,
        AI_GATEKEEPER_FAST_REUSE_SEC=20.0,
        AI_GATEKEEPER_FAST_REUSE_MAX_WS_AGE_SEC=2.0,
        ML_GATEKEEPER_ERROR_COOLDOWN=600,
        ML_GATEKEEPER_PULLBACK_WAIT_COOLDOWN=1200,
        ML_GATEKEEPER_REJECT_COOLDOWN=7200,
        ML_GATEKEEPER_NEUTRAL_COOLDOWN=1800,
        MAX_SWING_GAP_UP_PCT=3.0,
        MAX_SWING_GAP_UP_PCT_KOSPI=3.2,
    )

    captured_logs = []

    monkeypatch.setattr(state_handlers, "datetime", _FakeDateTime)
    monkeypatch.setattr(state_handlers, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(state_handlers, "estimate_turnover_hint", lambda *args, **kwargs: 0)
    monkeypatch.setattr(
        state_handlers,
        "get_dynamic_swing_gap_threshold",
        lambda strategy, marcap, turnover_hint=0: {"threshold": 3.2, "bucket_label": "중소형주"},
    )
    monkeypatch.setattr(
        state_handlers.kiwoom_utils,
        "build_realtime_analysis_context",
        lambda **kwargs: {"code": kwargs.get("code"), "score": kwargs.get("score")},
    )
    monkeypatch.setattr(state_handlers, "record_gatekeeper_snapshot", lambda **kwargs: None)
    monkeypatch.setattr(state_handlers, "_submit_gatekeeper_dual_persona_shadow", lambda **kwargs: None)
    monkeypatch.setattr(
        state_handlers,
        "_log_entry_pipeline",
        lambda stock, code, stage, **fields: captured_logs.append((stage, fields)),
    )

    stock = {
        "id": 1326,
        "name": "테스트종목",
        "strategy": "KOSPI_ML",
        "position_tag": "MIDDLE",
        "prob": 0.7,
    }
    ws_data = {
        "curr": 939,
        "fluctuation": 2.1,
        "volume": 250000,
        "v_pw": 110.0,
        "buy_ratio": 64.0,
        "prog_net_qty": 12000,
        "prog_delta_qty": 3000,
        "ask_tot": 180000,
        "bid_tot": 220000,
        "net_bid_depth": 12000,
        "net_ask_depth": -4000,
        "orderbook": {
            "asks": [{"price": 940}],
            "bids": [{"price": 939}],
        },
        "last_ws_update_ts": 1775607000.0,
    }

    state_handlers.handle_watching_state(
        stock=stock,
        code="330590",
        ws_data=ws_data,
        admin_id=1,
        radar=_DummyRadar(),
        ai_engine=_DummyAIEngine(),
    )

    bypass_log = next(fields for stage, fields in captured_logs if stage == "gatekeeper_fast_reuse_bypass")

    assert bypass_log["age_sec"] == "-"
    assert bypass_log["action_age_sec"] == "-"
    assert bypass_log["allow_entry_age_sec"] == "-"
