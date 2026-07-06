from datetime import datetime, time as dt_time, timedelta

from src.engine import kiwoom_sniper_v2


def _watching_ws():
    return {
        "curr": 10000,
        "open": 9950,
        "v_pw": 135.0,
        "fluctuation": 0.5,
        "volume": 100000,
        "ask_tot": 70000,
        "bid_tot": 70000,
        "quote_stale": False,
        "tick_context_stale": False,
    }


def _watching_stock(**updates):
    stock = {
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "buy_price": 10000,
        "rt_ai_prob": 0.80,
        "last_watching_ai_action": "BUY",
        "last_watching_ai_result_source": "live",
        "last_watching_ai_parse_ok": True,
    }
    stock.update(updates)
    return stock


def _patch_watching_dependencies(monkeypatch):
    monkeypatch.setattr(kiwoom_sniper_v2, "is_scalping_buy_time_allowed", lambda _now: True)
    monkeypatch.setattr(kiwoom_sniper_v2, "describe_scalping_buy_windows", lambda: "test_window")
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "evaluate_scalping_strength_momentum",
        lambda _ws: {"allowed": True, "reason": "test_pass", "vpw_delta": 0, "window_buy_value": 0, "threshold_profile": "test"},
    )
    monkeypatch.setattr(kiwoom_sniper_v2, "_resolve_stock_marcap", lambda _stock, _code: 100_000_000_000)
    monkeypatch.setattr(kiwoom_sniper_v2, "get_entry_buy_score_threshold", lambda: 75)
    monkeypatch.setattr(
        kiwoom_sniper_v2,
        "entry_buy_decision_allowed",
        lambda action, score: str(action or "").upper() == "BUY",
    )
    kiwoom_sniper_v2.cooldowns = {}
    kiwoom_sniper_v2.alerted_stocks = set()


def test_legacy_watching_blocks_unknown_ai_source_without_score_hard_gate(monkeypatch):
    _patch_watching_dependencies(monkeypatch)
    stock = _watching_stock(last_watching_ai_result_source="")

    reason = kiwoom_sniper_v2.check_watching_conditions(
        stock,
        "005930",
        _watching_ws(),
        admin_id=None,
        radar=object(),
    )

    assert reason.startswith("AI score source unusable")
    assert stock["legacy_entry_score_role_gate"] == "excluded"
    assert stock["entry_score_role_gate"] == "excluded"
    assert stock["legacy_entry_score_excluded_reason"] == "unusable_source:unknown"
    assert stock["entry_score_excluded_reason"] == "unusable_source:unknown"


def test_legacy_watching_fresh_live_buy_score_is_prior_not_hard_gate(monkeypatch):
    _patch_watching_dependencies(monkeypatch)

    low_reason = kiwoom_sniper_v2.check_watching_conditions(
        _watching_stock(rt_ai_prob=0.70),
        "005930",
        _watching_ws(),
        admin_id=None,
        radar=object(),
    )
    pass_reason = kiwoom_sniper_v2.check_watching_conditions(
        _watching_stock(rt_ai_prob=0.80),
        "005930",
        _watching_ws(),
        admin_id=None,
        radar=object(),
    )

    assert low_reason == "관리자 ID 없음"
    assert pass_reason == "관리자 ID 없음"


def _holding_stock(**updates):
    now = datetime.now()
    stock = {
        "rt_ai_prob": 0.10,
        "holding_started_at": now - timedelta(seconds=1000),
        "holding_score_last_effective_at": kiwoom_sniper_v2.time.time(),
        "holding_score_effective": 10.0,
        "holding_score_source": "live",
        "holding_score_data_quality": "fresh",
        "holding_score_effective_usable": True,
    }
    stock.update(updates)
    return stock


def _patch_holding_rules(monkeypatch):
    monkeypatch.setattr(kiwoom_sniper_v2, "TIME_15_30", dt_time(23, 59), raising=False)


def test_legacy_scalping_exit_rejects_stale_low_score_for_momentum_decay(monkeypatch):
    _patch_holding_rules(monkeypatch)
    code = "005930"
    kiwoom_sniper_v2.highest_prices = {code: 10100}
    stock = _holding_stock(
        holding_score_data_quality="stale",
        holding_score_effective_usable=False,
        holding_score_excluded_reason="holding_score_data_quality_stale",
    )

    reason = kiwoom_sniper_v2.evaluate_scalping_exit(
        stock,
        code,
        {"v_pw": 110},
        curr_p=10080,
        buy_p=9960,
        profit_rate=1.20,
        peak_profit=1.40,
    )

    assert reason is None
    assert stock["legacy_holding_score_negative_exit_usable"] is False
    assert stock["holding_score_negative_exit_usable"] is False
    assert stock["legacy_holding_score_negative_exit_excluded_reason"] != "-"
    assert stock["holding_score_negative_exit_excluded_reason"] != "-"


def test_legacy_scalping_exit_allows_fresh_low_score_for_momentum_decay(monkeypatch):
    _patch_holding_rules(monkeypatch)
    code = "005930"
    kiwoom_sniper_v2.highest_prices = {code: 10100}
    stock = _holding_stock()

    reason = kiwoom_sniper_v2.evaluate_scalping_exit(
        stock,
        code,
        {"v_pw": 110},
        curr_p=10080,
        buy_p=9960,
        profit_rate=1.20,
        peak_profit=1.40,
    )

    assert reason.startswith("AI 모멘텀 둔화")
    assert stock["legacy_holding_score_negative_exit_usable"] is True


def test_legacy_scalping_exit_uses_fresh_high_score_for_strong_trailing(monkeypatch):
    _patch_holding_rules(monkeypatch)
    code = "005930"
    kiwoom_sniper_v2.highest_prices = {code: 10100}
    stock = _holding_stock(
        rt_ai_prob=0.80,
        holding_score_effective=80.0,
    )

    reason = kiwoom_sniper_v2.evaluate_scalping_exit(
        stock,
        code,
        {"v_pw": 111},
        curr_p=10050,
        buy_p=9900,
        profit_rate=1.52,
        peak_profit=2.02,
    )

    assert reason is None
    assert stock["legacy_holding_score_negative_exit_usable"] is True
