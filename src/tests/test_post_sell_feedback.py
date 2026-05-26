import json
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
    assert candidate_upside["exit_decision_source"] == "-"

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
    evaluations = feedback_mod._load_jsonl(feedback_mod._evaluation_path("2026-04-08"))
    assert "metrics_30m" in evaluations[0]
    assert "metrics_60m" in evaluations[0]

    text = feedback_mod.format_post_sell_feedback_summary(summary)
    assert "MISSED_UPSIDE 1" in text
    assert "GOOD_EXIT 1" in text


def test_record_and_evaluate_sim_post_sell_feedback_isolated(monkeypatch, tmp_path):
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
    feedback_mod._SIM_RECORDED_KEYS.clear()

    candidate = feedback_mod.record_sim_post_sell_candidate(
        sim_record_id="SIM-005950-1",
        sim_parent_record_id="PARENT-1",
        stock={"name": "이수화학", "strategy": "SCALPING", "position_tag": "SCALP_SIM"},
        code="005950",
        sell_time="2026-05-18 10:00:30",
        buy_price=10000,
        sell_price=9746,
        profit_rate=-2.54,
        buy_qty=1,
        exit_rule="scalp_soft_stop_pct",
        sell_reason_type="STOP_LOSS",
    )

    assert candidate is not None
    assert candidate["runtime_effect"] is False
    assert candidate["actual_order_submitted"] is False
    assert candidate["broker_order_forbidden"] is True
    assert candidate["decision_authority"] == "sim_equal_weight_observation_only"
    assert "broker order submit" in candidate["forbidden_uses"]
    assert candidate["entry_time_source"] == "not_recorded_at_source"
    assert candidate["entry_join_status"] == "raw_append_only_unjoined"
    assert candidate["entry_record_id"] == "PARENT-1"
    assert feedback_mod._candidate_path("2026-05-18").exists() is False
    assert feedback_mod._sim_candidate_path("2026-05-18").exists() is True

    candle_map = {
        "005950": [
            _make_candle("10:01:00", 9800, 9700, 9780),
            _make_candle("10:02:00", 9900, 9720, 9850),
            _make_candle("10:03:00", 10050, 9810, 10000),
            _make_candle("10:04:00", 10120, 9900, 10080),
            _make_candle("10:05:00", 10150, 9950, 10100),
            _make_candle("10:06:00", 10180, 10000, 10140),
            _make_candle("10:07:00", 10160, 10020, 10130),
            _make_candle("10:08:00", 10140, 10010, 10120),
            _make_candle("10:09:00", 10130, 10000, 10110),
            _make_candle("10:10:00", 10120, 9990, 10100),
        ],
    }
    fake_kiwoom = types.SimpleNamespace(
        get_kiwoom_token=lambda: "dummy",
        get_minute_candles_ka10080=lambda _token, code, limit=700: candle_map.get(code, []),
    )
    monkeypatch.setitem(sys.modules, "src.utils.kiwoom_utils", fake_kiwoom)
    monkeypatch.setattr(utils_pkg, "kiwoom_utils", fake_kiwoom, raising=False)

    summary = feedback_mod.evaluate_sim_post_sell_candidates("2026-05-18", token="dummy")
    assert summary.total_candidates == 1
    assert summary.evaluated_candidates == 1
    assert summary.outcome_counts.get("MISSED_UPSIDE") == 1
    evaluations = feedback_mod._load_jsonl(feedback_mod._sim_evaluation_path("2026-05-18"))
    assert evaluations[0]["sim_record_id"] == "SIM-005950-1"
    assert evaluations[0]["runtime_effect"] is False
    assert evaluations[0]["metrics_10m"]["mfe_pct"] > 4.0


def test_backfill_sim_post_sell_candidates_is_idempotent(monkeypatch, tmp_path):
    monkeypatch.setattr(feedback_mod, "DATA_DIR", tmp_path)
    monkeypatch.setattr(
        feedback_mod,
        "TRADING_RULES",
        SimpleNamespace(
            POST_SELL_FEEDBACK_ENABLED=True,
            POST_SELL_FEEDBACK_EVAL_ENABLED=True,
        ),
    )
    feedback_mod._SIM_RECORDED_KEYS.clear()
    threshold_dir = tmp_path / "threshold_cycle"
    threshold_dir.mkdir(parents=True)
    (threshold_dir / "threshold_events_2026-05-18.jsonl").write_text(
        json.dumps(
            {
                "stage": "scalp_sim_sell_order_assumed_filled",
                "stock_name": "이수화학",
                "stock_code": "005950",
                "emitted_at": "2026-05-18T09:16:46",
                "fields": {
                    "sim_record_id": "SCALPSIM-1",
                    "sim_parent_record_id": "6924",
                    "profit_rate": "-2.54",
                    "buy_price": "10780",
                    "assumed_fill_price": "10530",
                    "qty": "264",
                    "exit_rule": "scalp_hard_stop_pct",
                    "sell_reason_type": "LOSS",
                },
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    first = feedback_mod.backfill_sim_post_sell_candidates_from_threshold_events("2026-05-18")
    second = feedback_mod.backfill_sim_post_sell_candidates_from_threshold_events("2026-05-18")

    assert first["events_seen"] == 1
    assert first["candidates_created"] == 1
    assert second["events_seen"] == 1
    assert second["candidates_created"] == 0
    candidates = feedback_mod._load_jsonl(feedback_mod._sim_candidate_path("2026-05-18"))
    assert len(candidates) == 1


def test_soft_stop_forensics_report(monkeypatch, tmp_path):
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
            POST_SELL_WS_RETAIN_MINUTES=0,
        ),
    )
    feedback_mod._RECORDED_KEYS.clear()
    feedback_mod._WS_RETAIN_UNTIL.clear()

    feedback_mod.record_post_sell_candidate(
        recommendation_id=201,
        stock={"name": "반등A", "strategy": "SCALPING", "position_tag": "SCANNER"},
        code="661111",
        sell_time="2026-04-08 12:00:10",
        buy_price=10100,
        sell_price=9900,
        profit_rate=-1.6,
        buy_qty=10,
        exit_rule="scalp_soft_stop_pct",
        peak_profit=0.1,
        held_sec=220,
        current_ai_score=43,
        soft_stop_threshold_pct=-1.5,
        same_symbol_soft_stop_cooldown_would_block=True,
    )
    feedback_mod.record_post_sell_candidate(
        recommendation_id=202,
        stock={"name": "지속약세B", "strategy": "SCALPING", "position_tag": "OPEN_RECLAIM"},
        code="662222",
        sell_time="2026-04-08 12:00:10",
        buy_price=10000,
        sell_price=9850,
        profit_rate=-2.2,
        buy_qty=10,
        exit_rule="scalp_soft_stop_pct",
        peak_profit=-0.2,
        held_sec=80,
        current_ai_score=38,
        soft_stop_threshold_pct=-1.5,
        same_symbol_soft_stop_cooldown_would_block=True,
    )

    candle_map = {
        "661111": [
            _make_candle("12:01:00", 10020, 9880, 9990),
            _make_candle("12:02:00", 10130, 9950, 10080),
            _make_candle("12:03:00", 10180, 10040, 10120),
            _make_candle("12:04:00", 10160, 10010, 10110),
            _make_candle("12:05:00", 10150, 10020, 10100),
            _make_candle("12:06:00", 10140, 10030, 10090),
            _make_candle("12:07:00", 10150, 10040, 10110),
            _make_candle("12:08:00", 10160, 10050, 10120),
            _make_candle("12:09:00", 10170, 10060, 10130),
            _make_candle("12:10:00", 10180, 10070, 10140),
        ],
        "662222": [
            _make_candle("12:01:00", 9840, 9780, 9810),
            _make_candle("12:02:00", 9850, 9750, 9790),
            _make_candle("12:03:00", 9840, 9720, 9780),
            _make_candle("12:04:00", 9830, 9700, 9770),
            _make_candle("12:05:00", 9820, 9690, 9760),
            _make_candle("12:06:00", 9810, 9680, 9750),
            _make_candle("12:07:00", 9800, 9670, 9740),
            _make_candle("12:08:00", 9790, 9660, 9730),
            _make_candle("12:09:00", 9780, 9650, 9720),
            _make_candle("12:10:00", 9770, 9640, 9710),
        ],
    }
    fake_kiwoom = types.SimpleNamespace(
        get_kiwoom_token=lambda: "dummy",
        get_minute_candles_ka10080=lambda _token, code, limit=700: candle_map.get(code, []),
    )
    monkeypatch.setitem(sys.modules, "src.utils.kiwoom_utils", fake_kiwoom)
    monkeypatch.setattr(utils_pkg, "kiwoom_utils", fake_kiwoom, raising=False)

    feedback_mod.evaluate_post_sell_candidates("2026-04-08", token="dummy")
    report = feedback_mod.build_post_sell_feedback_report("2026-04-08", top_n=5, evaluate_now=False)

    forensic = report["soft_stop_forensics"]
    assert forensic["total_soft_stop"] == 2
    assert forensic["rebound_above_sell_rate"]["1m"] == 50.0
    assert forensic["rebound_above_buy_rate"]["3m"] == 50.0
    assert forensic["rebound_above_sell_rate"]["30m"] == 50.0
    assert forensic["rebound_above_buy_rate"]["60m"] == 50.0
    assert forensic["median_overshoot_pct"] == 0.4
    assert forensic["p95_overshoot_pct"] >= 0.66
    assert forensic["cooldown_would_block_rate"] == 100.0
    assert forensic["tag_buckets"]
    assert forensic["held_sec_buckets"]
    assert forensic["peak_profit_buckets"]
    assert forensic["top_rebound_cases"][0]["stock_code"] == "661111"


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


def test_evaluate_backfills_legacy_horizon_metrics(monkeypatch, tmp_path):
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

    candidate = feedback_mod.record_post_sell_candidate(
        recommendation_id=71,
        stock={"name": "레거시평가"},
        code="771111",
        sell_time="2026-04-08 10:00:30",
        buy_price=10000,
        sell_price=9900,
        profit_rate=-1.0,
        buy_qty=1,
        exit_rule="scalp_soft_stop_pct",
    )
    assert candidate is not None
    feedback_mod._append_jsonl(
        feedback_mod._evaluation_path("2026-04-08"),
        {
            "post_sell_id": candidate["post_sell_id"],
            "signal_date": "2026-04-08",
            "stock_code": "771111",
            "stock_name": "레거시평가",
            "sell_time": "10:00:30",
            "sell_price": 9900,
            "buy_price": 10000,
            "profit_rate": -1.0,
            "outcome": "NEUTRAL",
            "metrics_10m": {"mfe_pct": 0.0, "mae_pct": 0.0, "close_ret_pct": 0.0},
        },
    )

    fake_kiwoom = types.SimpleNamespace(
        get_kiwoom_token=lambda: "dummy",
        get_minute_candles_ka10080=lambda _token, _code, limit=700: [
            _make_candle("10:01:00", 10000, 9880, 9950),
            _make_candle("10:30:00", 10100, 9900, 10050),
            _make_candle("11:00:00", 10200, 9890, 10100),
        ],
    )
    monkeypatch.setitem(sys.modules, "src.utils.kiwoom_utils", fake_kiwoom)
    monkeypatch.setattr(utils_pkg, "kiwoom_utils", fake_kiwoom, raising=False)

    summary = feedback_mod.evaluate_post_sell_candidates("2026-04-08", token="dummy")
    assert summary.evaluated_candidates == 1
    latest = feedback_mod._dedupe_latest_evaluations(
        feedback_mod._load_jsonl(feedback_mod._evaluation_path("2026-04-08"))
    )[0]
    assert "metrics_30m" in latest
    assert "metrics_60m" in latest


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


def test_build_post_sell_feedback_report(monkeypatch, tmp_path):
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
            POST_SELL_WS_RETAIN_MINUTES=0,
        ),
    )
    feedback_mod._RECORDED_KEYS.clear()
    feedback_mod._WS_RETAIN_UNTIL.clear()

    feedback_mod.record_post_sell_candidate(
        recommendation_id=101,
        stock={"name": "상승A", "strategy": "SCALPING", "position_tag": "OPEN_RECLAIM"},
        code="551111",
        sell_time="2026-04-08 10:00:10",
        buy_price=9800,
        sell_price=10000,
        profit_rate=2.0,
        buy_qty=10,
        exit_rule="scalp_soft_stop_pct",
    )
    feedback_mod.record_post_sell_candidate(
        recommendation_id=102,
        stock={"name": "하락B", "strategy": "SCALPING", "position_tag": "SCALP_BASE"},
        code="552222",
        sell_time="2026-04-08 10:00:10",
        buy_price=10200,
        sell_price=10000,
        profit_rate=-2.0,
        buy_qty=10,
        exit_rule="scalp_ai_early_exit",
    )
    feedback_mod.record_post_sell_candidate(
        recommendation_id=103,
        stock={"name": "중립C", "strategy": "KOSPI_ML", "position_tag": "KOSPI_BASE"},
        code="553333",
        sell_time="2026-04-08 10:00:10",
        buy_price=10000,
        sell_price=10000,
        profit_rate=0.0,
        buy_qty=10,
        exit_rule="trailing_take_profit",
    )

    candle_map = {
        "551111": [
            _make_candle("10:01:00", 10120, 10020, 10090),
            _make_candle("10:02:00", 10220, 10080, 10160),
            _make_candle("10:03:00", 10240, 10120, 10190),
            _make_candle("10:04:00", 10200, 10100, 10160),
            _make_candle("10:05:00", 10180, 10090, 10140),
            _make_candle("10:06:00", 10200, 10100, 10160),
            _make_candle("10:07:00", 10220, 10130, 10180),
            _make_candle("10:08:00", 10230, 10120, 10190),
            _make_candle("10:09:00", 10240, 10130, 10200),
            _make_candle("10:10:00", 10250, 10140, 10210),
        ],
        "552222": [
            _make_candle("10:01:00", 10010, 9920, 9950),
            _make_candle("10:02:00", 10000, 9880, 9920),
            _make_candle("10:03:00", 9990, 9860, 9890),
            _make_candle("10:04:00", 9980, 9850, 9880),
            _make_candle("10:05:00", 9970, 9840, 9870),
            _make_candle("10:06:00", 9970, 9830, 9860),
            _make_candle("10:07:00", 9960, 9820, 9850),
            _make_candle("10:08:00", 9960, 9810, 9840),
            _make_candle("10:09:00", 9950, 9800, 9830),
            _make_candle("10:10:00", 9950, 9790, 9820),
        ],
        "553333": [
            _make_candle("10:01:00", 10020, 9980, 10000),
            _make_candle("10:02:00", 10030, 9970, 10010),
            _make_candle("10:03:00", 10020, 9980, 10000),
            _make_candle("10:04:00", 10010, 9990, 10000),
            _make_candle("10:05:00", 10020, 9980, 10000),
            _make_candle("10:06:00", 10020, 9980, 10000),
            _make_candle("10:07:00", 10020, 9980, 10000),
            _make_candle("10:08:00", 10010, 9990, 10000),
            _make_candle("10:09:00", 10020, 9980, 10000),
            _make_candle("10:10:00", 10020, 9980, 10000),
        ],
    }
    fake_kiwoom = types.SimpleNamespace(
        get_kiwoom_token=lambda: "dummy",
        get_minute_candles_ka10080=lambda _token, code, limit=700: candle_map.get(code, []),
    )
    monkeypatch.setitem(sys.modules, "src.utils.kiwoom_utils", fake_kiwoom)
    monkeypatch.setattr(utils_pkg, "kiwoom_utils", fake_kiwoom, raising=False)

    summary = feedback_mod.evaluate_post_sell_candidates("2026-04-08", token="dummy")
    assert summary.evaluated_candidates == 3

    report = feedback_mod.build_post_sell_feedback_report(
        "2026-04-08",
        top_n=5,
        evaluate_now=False,
    )

    assert report["metrics"]["evaluated_candidates"] == 3
    assert report["metrics"]["missed_upside_rate"] > 0.0
    assert report["metrics"]["good_exit_rate"] > 0.0
    assert report["metrics"]["estimated_extra_upside_10m_krw_sum"] > 0
    assert report["metrics"]["estimated_extra_upside_30m_krw_sum"] > 0
    assert report["meta"]["evaluation_horizons_min"] == [1, 3, 5, 10, 20, 30, 60]
    assert len(report["exit_rule_tuning"]) == 3
    assert len(report["tag_tuning"]) == 3
    assert report["priority_actions"]
    assert report["top_missed_upside"]
    assert "soft_stop_forensics" in report
