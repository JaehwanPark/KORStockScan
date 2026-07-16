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


class _CountingAIEngine(_DummyAIEngine):
    def __init__(self):
        self.calls = 0

    def evaluate_realtime_gatekeeper(self, **kwargs):
        self.calls += 1
        return super().evaluate_realtime_gatekeeper(**kwargs)


def test_watching_state_debug_log_is_disabled_by_default(monkeypatch):
    monkeypatch.setattr(
        state_handlers,
        "TRADING_RULES",
        SimpleNamespace(WATCHING_STATE_DEBUG_LOG_ENABLED=False),
    )
    messages = []
    monkeypatch.setattr(
        state_handlers,
        "log_info",
        lambda msg, send_telegram=False: messages.append(msg),
    )

    state_handlers._log_watching_state_debug(
        {"name": "테스트", "strategy": "SCALPING", "position_tag": "SCANNER"},
        "123456",
        radar=object(),
        ai_engine=object(),
    )

    assert messages == []


def test_watching_state_debug_log_can_be_enabled(monkeypatch):
    monkeypatch.setattr(
        state_handlers,
        "TRADING_RULES",
        SimpleNamespace(WATCHING_STATE_DEBUG_LOG_ENABLED=True),
    )
    messages = []
    monkeypatch.setattr(
        state_handlers,
        "log_info",
        lambda msg, send_telegram=False: messages.append(msg),
    )

    state_handlers._log_watching_state_debug(
        {"name": "테스트", "strategy": "SCALPING", "position_tag": "SCANNER"},
        "123456",
        radar=object(),
        ai_engine=object(),
    )

    assert len(messages) == 1
    assert "[DEBUG] handle_watching_state 시작: 테스트 (123456)" in messages[0]


def test_gatekeeper_fast_reuse_bypass_logs_sentinel_when_fast_timestamp_missing(
    monkeypatch,
):
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
    monkeypatch.setattr(
        state_handlers, "estimate_turnover_hint", lambda *args, **kwargs: 0
    )
    monkeypatch.setattr(
        state_handlers,
        "get_dynamic_swing_gap_threshold",
        lambda strategy, marcap, turnover_hint=0: {
            "threshold": 3.2,
            "bucket_label": "중소형주",
        },
    )
    monkeypatch.setattr(
        state_handlers.kiwoom_utils,
        "build_realtime_analysis_context",
        lambda **kwargs: {"code": kwargs.get("code"), "score": kwargs.get("score")},
    )
    monkeypatch.setattr(
        state_handlers, "record_gatekeeper_snapshot", lambda **kwargs: None
    )
    monkeypatch.setattr(
        state_handlers, "_submit_gatekeeper_dual_persona_shadow", lambda **kwargs: None
    )
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

    bypass_log = next(
        fields
        for stage, fields in captured_logs
        if stage == "gatekeeper_fast_reuse_bypass"
    )

    assert bypass_log["age_sec"] == "-"
    assert bypass_log["action_age_sec"] == "-"
    assert bypass_log["allow_entry_age_sec"] == "-"


def test_gatekeeper_recent_reject_cache_reuses_without_model_call(monkeypatch):
    fixed_now = 1_775_607_000.0
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
        AI_GATEKEEPER_REJECT_CACHE_SEC=90.0,
        ML_GATEKEEPER_ERROR_COOLDOWN=600,
        ML_GATEKEEPER_PULLBACK_WAIT_COOLDOWN=1200,
        ML_GATEKEEPER_REJECT_COOLDOWN=7200,
        ML_GATEKEEPER_NEUTRAL_COOLDOWN=1800,
        MAX_SWING_GAP_UP_PCT=3.0,
        MAX_SWING_GAP_UP_PCT_KOSPI=3.2,
    )

    captured_logs = []
    engine = _CountingAIEngine()

    monkeypatch.setattr(state_handlers.time, "time", lambda: fixed_now)
    monkeypatch.setattr(state_handlers, "datetime", _FakeDateTime)
    monkeypatch.setattr(state_handlers, "is_buy_side_paused", lambda: False)
    monkeypatch.setattr(
        state_handlers, "estimate_turnover_hint", lambda *args, **kwargs: 0
    )
    monkeypatch.setattr(
        state_handlers,
        "get_dynamic_swing_gap_threshold",
        lambda strategy, marcap, turnover_hint=0: {
            "threshold": 3.2,
            "bucket_label": "중소형주",
        },
    )
    monkeypatch.setattr(
        state_handlers.kiwoom_utils,
        "build_realtime_analysis_context",
        lambda **kwargs: (_ for _ in ()).throw(
            AssertionError("model context should not be built")
        ),
    )
    monkeypatch.setattr(
        state_handlers, "record_gatekeeper_snapshot", lambda **kwargs: None
    )
    monkeypatch.setattr(
        state_handlers, "_submit_gatekeeper_dual_persona_shadow", lambda **kwargs: None
    )
    monkeypatch.setattr(
        state_handlers, "_publish_gatekeeper_report_proxy", lambda *args, **kwargs: None
    )
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
        "last_gatekeeper_action": "눌림 대기",
        "last_gatekeeper_action_key": "pullback_wait",
        "last_gatekeeper_report": "recent reject",
        "last_gatekeeper_allow_entry": False,
        "last_gatekeeper_action_at": fixed_now - 30.0,
        "last_gatekeeper_allow_entry_at": fixed_now - 30.0,
        "last_gatekeeper_score": 82.0,
        "last_gatekeeper_curr_price": 939,
        "last_gatekeeper_gap_pct": 2.1,
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
        "orderbook": {"asks": [{"price": 940}], "bids": [{"price": 939}]},
        "last_ws_update_ts": fixed_now,
    }

    state_handlers.handle_watching_state(
        stock=stock,
        code="330590",
        ws_data=ws_data,
        admin_id=1,
        radar=_DummyRadar(),
        ai_engine=engine,
    )

    assert engine.calls == 0
    reuse_log = next(
        fields
        for stage, fields in captured_logs
        if stage == "gatekeeper_reject_cache_reuse"
    )
    assert reuse_log["cache_authority"] == "baseline_prior_feature_only"
    reject_log = next(
        fields
        for stage, fields in captured_logs
        if stage == "blocked_gatekeeper_reject"
    )
    assert reject_log["gatekeeper_cache"] == "reject_cache"


def test_gatekeeper_reject_cache_skips_unknown_and_material_improvement(monkeypatch):
    fixed_now = 1_775_607_000.0
    monkeypatch.setattr(
        state_handlers,
        "TRADING_RULES",
        SimpleNamespace(
            AI_GATEKEEPER_REJECT_CACHE_SEC=90.0,
            AI_GATEKEEPER_REJECT_CACHE_SCORE_IMPROVE_DELTA=5.0,
            AI_GATEKEEPER_REJECT_CACHE_PRICE_CHANGE_PCT=0.8,
            AI_GATEKEEPER_REJECT_CACHE_GAP_DELTA_PCT=0.6,
        ),
    )

    unknown_stock = {
        "last_gatekeeper_action": "UNDECLARED_LABEL",
        "last_gatekeeper_action_key": "unknown",
        "last_gatekeeper_allow_entry": False,
        "last_gatekeeper_action_at": fixed_now - 10.0,
        "last_gatekeeper_score": 82.0,
        "last_gatekeeper_curr_price": 939,
        "last_gatekeeper_gap_pct": 2.1,
    }
    assert (
        state_handlers._build_gatekeeper_reject_cache_result(
            unknown_stock,
            score=82.0,
            curr_price=939,
            gap_pct=2.1,
            now_ts=fixed_now,
        )
        is None
    )

    improved_stock = {
        "last_gatekeeper_action": "눌림 대기",
        "last_gatekeeper_action_key": "pullback_wait",
        "last_gatekeeper_allow_entry": False,
        "last_gatekeeper_action_at": fixed_now - 10.0,
        "last_gatekeeper_score": 82.0,
        "last_gatekeeper_curr_price": 939,
        "last_gatekeeper_gap_pct": 2.1,
    }
    assert (
        state_handlers._build_gatekeeper_reject_cache_result(
            improved_stock,
            score=87.0,
            curr_price=939,
            gap_pct=2.1,
            now_ts=fixed_now,
        )
        is None
    )
