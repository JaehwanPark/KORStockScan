import sys
import types
from types import SimpleNamespace

from src.engine import sniper_post_sell_feedback as feedback_mod
import src.utils as utils_pkg


def _make_candle(ts: str, high: int, low: int, close: int) -> dict:
    return {
        "체결시간": ts,
        "고가": high,
        "저가": low,
        "현재가": close,
    }


def test_record_and_evaluate_post_sell_feedback(monkeypatch, tmp_path):
    monkeypatch.setattr(feedback_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        feedback_mod,
        "TRADING_RULES",
        SimpleNamespace(
            POST_SELL_FEEDBACK_ENABLED=True,
            POST_SELL_FEEDBACK_EVAL_ENABLED=True,
            POST_SELL_FEEDBACK_MISSED_UPSIDE_MFE_PCT=0.8,
            POST_SELL_FEEDBACK_MISSED_UPSIDE_CLOSE_PCT=0.3,
            POST_SELL_FEEDBACK_GOOD_EXIT_MAE_PCT=-0.6,
            POST_SELL_FEEDBACK_GOOD_EXIT_CLOSE_PCT=-0.2,
        ),
    )
    feedback_mod._RECORDED_KEYS.clear()

    candidate_upside = feedback_mod.record_post_sell_candidate(
        recommendation_id=1,
        stock={"name": "상승후보", "strategy": "SCALPING", "position_tag": "SCALP_BASE"},
        code="111111",
        sell_time="2026-04-08 10:00:30",
        buy_price=9900,
        sell_price=10000,
        profit_rate=1.0,
        buy_qty=10,
        exit_rule="scalp_soft_stop_pct",
        revive=False,
    )
    candidate_good_exit = feedback_mod.record_post_sell_candidate(
        recommendation_id=2,
        stock={"name": "하락후보", "strategy": "SCALPING", "position_tag": "SCALP_BASE"},
        code="222222",
        sell_time="2026-04-08 10:00:30",
        buy_price=10200,
        sell_price=10000,
        profit_rate=-2.0,
        buy_qty=10,
        exit_rule="scalp_ai_early_exit",
        revive=False,
    )
    assert candidate_upside is not None
    assert candidate_good_exit is not None

    candle_map = {
        "111111": [
            _make_candle("10:01:00", 10120, 10010, 10080),
            _make_candle("10:02:00", 10220, 10050, 10160),
            _make_candle("10:03:00", 10250, 10120, 10180),
            _make_candle("10:04:00", 10230, 10130, 10150),
            _make_candle("10:05:00", 10190, 10100, 10120),
            _make_candle("10:06:00", 10180, 10090, 10110),
            _make_candle("10:07:00", 10190, 10100, 10140),
            _make_candle("10:08:00", 10200, 10120, 10160),
            _make_candle("10:09:00", 10210, 10140, 10170),
            _make_candle("10:10:00", 10220, 10150, 10180),
        ],
        "222222": [
            _make_candle("10:01:00", 10020, 9920, 9940),
            _make_candle("10:02:00", 10010, 9880, 9900),
            _make_candle("10:03:00", 9990, 9850, 9880),
            _make_candle("10:04:00", 9970, 9840, 9860),
            _make_candle("10:05:00", 9960, 9830, 9850),
            _make_candle("10:06:00", 9950, 9820, 9840),
            _make_candle("10:07:00", 9940, 9810, 9830),
            _make_candle("10:08:00", 9930, 9800, 9820),
            _make_candle("10:09:00", 9920, 9800, 9810),
            _make_candle("10:10:00", 9920, 9790, 9800),
        ],
    }

    fake_kiwoom = types.SimpleNamespace(
        get_kiwoom_token=lambda: "dummy",
        get_minute_candles_ka10080=lambda _token, code, limit=700: candle_map.get(code, []),
    )
    monkeypatch.setitem(sys.modules, "src.utils.kiwoom_utils", fake_kiwoom)
    monkeypatch.setattr(utils_pkg, "kiwoom_utils", fake_kiwoom, raising=False)

    summary = feedback_mod.evaluate_post_sell_candidates("2026-04-08", token="dummy")
    assert summary.total_candidates == 2
    assert summary.evaluated_candidates == 2
    assert summary.outcome_counts.get("MISSED_UPSIDE", 0) == 1
    assert summary.outcome_counts.get("GOOD_EXIT", 0) == 1

    text = feedback_mod.format_post_sell_feedback_summary(summary)
    assert "MISSED_UPSIDE 1" in text
    assert "GOOD_EXIT 1" in text


def test_post_sell_candidate_dedup(monkeypatch, tmp_path):
    monkeypatch.setattr(feedback_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        feedback_mod,
        "TRADING_RULES",
        SimpleNamespace(
            POST_SELL_FEEDBACK_ENABLED=True,
            POST_SELL_FEEDBACK_EVAL_ENABLED=True,
            POST_SELL_FEEDBACK_MISSED_UPSIDE_MFE_PCT=0.8,
            POST_SELL_FEEDBACK_MISSED_UPSIDE_CLOSE_PCT=0.3,
            POST_SELL_FEEDBACK_GOOD_EXIT_MAE_PCT=-0.6,
            POST_SELL_FEEDBACK_GOOD_EXIT_CLOSE_PCT=-0.2,
        ),
    )
    feedback_mod._RECORDED_KEYS.clear()

    first = feedback_mod.record_post_sell_candidate(
        recommendation_id=55,
        stock={"name": "중복테스트"},
        code="333333",
        sell_time="2026-04-08 11:20:10",
        sell_price=10000,
        buy_price=10100,
        profit_rate=-1.0,
        buy_qty=1,
    )
    second = feedback_mod.record_post_sell_candidate(
        recommendation_id=55,
        stock={"name": "중복테스트"},
        code="333333",
        sell_time="2026-04-08 11:20:40",
        sell_price=10000,
        buy_price=10100,
        profit_rate=-1.0,
        buy_qty=1,
    )
    assert first is not None
    assert second is None


def test_post_sell_ws_retain_window(monkeypatch, tmp_path):
    monkeypatch.setattr(feedback_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        feedback_mod,
        "TRADING_RULES",
        SimpleNamespace(
            POST_SELL_FEEDBACK_ENABLED=True,
            POST_SELL_FEEDBACK_EVAL_ENABLED=True,
            POST_SELL_FEEDBACK_MISSED_UPSIDE_MFE_PCT=0.8,
            POST_SELL_FEEDBACK_MISSED_UPSIDE_CLOSE_PCT=0.3,
            POST_SELL_FEEDBACK_GOOD_EXIT_MAE_PCT=-0.6,
            POST_SELL_FEEDBACK_GOOD_EXIT_CLOSE_PCT=-0.2,
            POST_SELL_WS_RETAIN_MINUTES=3,
        ),
    )
    feedback_mod._RECORDED_KEYS.clear()
    feedback_mod._WS_RETAIN_UNTIL.clear()

    feedback_mod.record_post_sell_candidate(
        recommendation_id=91,
        stock={"name": "유지테스트"},
        code="444444",
        sell_time="2026-04-08 11:00:00",
        sell_price=10000,
        buy_price=10000,
    )

    base_ts = 1_775_636_400.0  # 2026-04-08 11:00:00 KST 근사
    retain_until = base_ts + 180.0
    feedback_mod._WS_RETAIN_UNTIL["444444"] = retain_until

    assert feedback_mod.should_retain_ws_subscription("444444", now_ts=base_ts + 60.0) is True
    assert feedback_mod.should_retain_ws_subscription("444444", now_ts=base_ts + 181.0) is False
