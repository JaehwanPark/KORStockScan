import sys
import types
import json

from src.engine import sniper_missed_entry_counterfactual as report_mod


def _make_candle(ts: str, open_p: int, high: int, low: int, close: int) -> dict:
    return {
        "체결시간": ts,
        "시가": open_p,
        "고가": high,
        "저가": low,
        "현재가": close,
    }


def _write_pipeline_events(tmp_path, target_date: str, rows: list[dict]) -> None:
    path = tmp_path / "pipeline_events"
    path.mkdir(parents=True, exist_ok=True)
    with open(path / f"pipeline_events_{target_date}.jsonl", "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def test_build_missed_entry_counterfactual_report(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    target_date = "2026-04-09"
    _write_pipeline_events(
        tmp_path,
        target_date,
        [
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "ai_confirmed",
                "stock_name": "라텐시위너",
                "stock_code": "111111",
                "record_id": 1,
                "fields": {"action": "BUY", "ai_score": "92"},
                "emitted_at": "2026-04-09T10:00:01",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "entry_armed",
                "stock_name": "라텐시위너",
                "stock_code": "111111",
                "record_id": 1,
                "fields": {"ai_score": "92.0", "target_buy_price": "10000"},
                "emitted_at": "2026-04-09T10:00:02",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "budget_pass",
                "stock_name": "라텐시위너",
                "stock_code": "111111",
                "record_id": 1,
                "fields": {"qty": "10", "safe_budget": "100000"},
                "emitted_at": "2026-04-09T10:00:03",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "latency_block",
                "stock_name": "라텐시위너",
                "stock_code": "111111",
                "record_id": 1,
                "fields": {"decision": "REJECT_DANGER", "reason": "latency_state_danger"},
                "emitted_at": "2026-04-09T10:00:04",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "ai_confirmed",
                "stock_name": "리퀴드로저",
                "stock_code": "222222",
                "record_id": 2,
                "fields": {"action": "BUY", "ai_score": "88"},
                "emitted_at": "2026-04-09T10:05:01",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "blocked_liquidity",
                "stock_name": "리퀴드로저",
                "stock_code": "222222",
                "record_id": 2,
                "fields": {"liquidity_value": "70000000", "min_liquidity": "350000000"},
                "emitted_at": "2026-04-09T10:05:02",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "ai_confirmed",
                "stock_name": "제출완료",
                "stock_code": "333333",
                "record_id": 3,
                "fields": {"action": "BUY", "ai_score": "85"},
                "emitted_at": "2026-04-09T10:10:01",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "entry_armed",
                "stock_name": "제출완료",
                "stock_code": "333333",
                "record_id": 3,
                "fields": {"target_buy_price": "30000"},
                "emitted_at": "2026-04-09T10:10:02",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "order_bundle_submitted",
                "stock_name": "제출완료",
                "stock_code": "333333",
                "record_id": 3,
                "fields": {},
                "emitted_at": "2026-04-09T10:10:03",
                "emitted_date": target_date,
            },
        ],
    )

    candle_map = {
        "111111": [
            _make_candle("10:01:00", 10000, 10120, 9995, 10080),
            _make_candle("10:02:00", 10080, 10180, 10040, 10120),
            _make_candle("10:03:00", 10110, 10160, 10070, 10130),
            _make_candle("10:04:00", 10120, 10150, 10090, 10110),
            _make_candle("10:05:00", 10100, 10130, 10080, 10100),
            _make_candle("10:06:00", 10110, 10140, 10090, 10120),
            _make_candle("10:07:00", 10120, 10150, 10090, 10130),
            _make_candle("10:08:00", 10130, 10160, 10100, 10140),
            _make_candle("10:09:00", 10140, 10180, 10110, 10150),
            _make_candle("10:10:00", 10150, 10190, 10120, 10160),
        ],
        "222222": [
            _make_candle("10:06:00", 20000, 20050, 19880, 19920),
            _make_candle("10:07:00", 19920, 19960, 19780, 19820),
            _make_candle("10:08:00", 19820, 19880, 19720, 19760),
            _make_candle("10:09:00", 19760, 19820, 19680, 19720),
            _make_candle("10:10:00", 19720, 19780, 19640, 19680),
            _make_candle("10:11:00", 19680, 19710, 19620, 19660),
            _make_candle("10:12:00", 19660, 19690, 19600, 19640),
            _make_candle("10:13:00", 19640, 19680, 19580, 19620),
            _make_candle("10:14:00", 19620, 19660, 19560, 19600),
            _make_candle("10:15:00", 19600, 19630, 19540, 19580),
        ],
    }
    fake_kiwoom = types.SimpleNamespace(
        get_kiwoom_token=lambda: "dummy",
        get_minute_candles_ka10080=lambda _token, code, limit=700: candle_map.get(code, []),
    )
    import src.utils as utils_pkg
    monkeypatch.setattr(utils_pkg, "kiwoom_utils", fake_kiwoom, raising=False)
    monkeypatch.setitem(sys.modules, "src.utils.kiwoom_utils", fake_kiwoom)

    report = report_mod.build_missed_entry_counterfactual_report(target_date, token="dummy")

    assert report["summary"]["total_candidates"] == 2
    assert report["summary"]["evaluated_candidates"] == 2
    assert report["summary"]["outcome_counts"]["MISSED_WINNER"] == 1
    assert report["summary"]["outcome_counts"]["AVOIDED_LOSER"] == 1
    assert report["metrics"]["missed_winner_rate"] == 50.0
    assert report["metrics"]["avoided_loser_rate"] == 50.0
    blocker_metrics = report["metrics"]["blocker_outcome_metrics"]
    assert blocker_metrics["latency_block"]["missed_winner_rate"] == 100.0
    assert blocker_metrics["blocked_liquidity"]["avoided_loser_rate"] == 100.0
    assert blocker_metrics["latency_block"]["avg_close_10m_pct"] > 0
    assert report["buy_signal_universe"]["metrics"]["total_buy_judged_attempts"] == 3
    assert report["buy_signal_universe"]["metrics"]["entered_attempts"] == 1
    assert report["buy_signal_universe"]["metrics"]["missed_attempts"] == 2
    assert report["top_missed_winners"][0]["stock_code"] == "111111"
    winner = report["top_missed_winners"][0]
    assert winner["counterfactual_qty"] > 0
    assert report["top_missed_winners"][0]["counterfactual_qty_source"] == "sim_virtual_budget_dynamic_formula"
    assert report["top_missed_winners"][0]["virtual_budget_krw"] == 10_000_000
    assert winner["counterfactual_notional_krw"] == winner["entry_price_used"] * winner["counterfactual_qty"]
    assert winner["counterfactual_notional_krw"] <= winner["counterfactual_safe_budget"]
    assert 0.10 <= winner["counterfactual_ratio"] <= 0.30
    assert report["top_avoided_losers"][0]["stock_code"] == "222222"
    stages = {row["stage"] for row in report["reason_breakdown"]}
    assert "latency_block" in stages
    assert "blocked_liquidity" in stages
    tiers = {row["tier"] for row in report["buy_signal_universe"]["confidence_breakdown"]}
    assert "A" in tiers


def test_missed_entry_counterfactual_splits_ai_and_pre_submit_cohorts(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    target_date = "2026-06-18"
    _write_pipeline_events(
        tmp_path,
        target_date,
        [
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "scalp_entry_action_decision_snapshot",
                "stock_name": "AI모순",
                "stock_code": "111111",
                "record_id": 1,
                "fields": {
                    "chosen_action": "NO_BUY_AI",
                    "ai_score": "62.0",
                    "ai_reason_numeric_inconsistency": True,
                },
                "emitted_at": "2026-06-18T10:00:01",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "ai_numeric_consistency_recheck_failed",
                "stock_name": "재판정실패",
                "stock_code": "333333",
                "record_id": 3,
                "fields": {
                    "original_action": "WAIT",
                    "original_score": "72.0",
                    "recheck_action": "WAIT",
                    "recheck_score": "70.0",
                    "skip_reason": "recheck_still_contradictory",
                },
                "emitted_at": "2026-06-18T10:08:01",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "scalp_entry_action_decision_snapshot",
                "stock_name": "재판정실패",
                "stock_code": "333333",
                "record_id": 3,
                "fields": {
                    "chosen_action": "NO_BUY_AI",
                    "ai_score": "72.0",
                    "ai_reason_numeric_inconsistency": True,
                },
                "emitted_at": "2026-06-18T10:07:59",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "ai_confirmed",
                "stock_name": "리퀴드가드",
                "stock_code": "222222",
                "record_id": 2,
                "fields": {"action": "BUY", "ai_score": "88"},
                "emitted_at": "2026-06-18T10:05:01",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "entry_armed",
                "stock_name": "리퀴드가드",
                "stock_code": "222222",
                "record_id": 2,
                "fields": {"target_buy_price": "20000", "ai_score": "88.0"},
                "emitted_at": "2026-06-18T10:05:02",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "pre_submit_liquidity_guard_block",
                "stock_name": "리퀴드가드",
                "stock_code": "222222",
                "record_id": 2,
                "fields": {"liquidity_value": "70000000", "min_liquidity": "350000000"},
                "emitted_at": "2026-06-18T10:05:03",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "scalp_entry_action_decision_snapshot",
                "stock_name": "강가속재질의",
                "stock_code": "444444",
                "record_id": 4,
                "fields": {
                    "chosen_action": "NO_BUY_AI",
                    "ai_score": "64.0",
                },
                "emitted_at": "2026-06-18T10:12:01",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "early_accel_strong_bundle_recheck_skipped",
                "stock_name": "강가속재질의",
                "stock_code": "444444",
                "record_id": 4,
                "fields": {
                    "original_action": "WAIT",
                    "original_score": "64.0",
                    "skip_reason": "strong_bundle_below_min_pass_count",
                },
                "emitted_at": "2026-06-18T10:12:02",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "ai_confirmed",
                "stock_name": "미제출",
                "stock_code": "555555",
                "record_id": 5,
                "fields": {"action": "BUY", "ai_score": "82"},
                "emitted_at": "2026-06-18T10:20:01",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "entry_armed",
                "stock_name": "미제출",
                "stock_code": "555555",
                "record_id": 5,
                "fields": {"target_buy_price": "50000", "ai_score": "82.0"},
                "emitted_at": "2026-06-18T10:20:02",
                "emitted_date": target_date,
            },
        ],
    )

    candle_map = {
        "111111": [
            _make_candle("10:01:00", 10000, 10200, 9990, 10150),
            _make_candle("10:02:00", 10150, 10250, 10100, 10200),
            _make_candle("10:03:00", 10200, 10260, 10180, 10210),
            _make_candle("10:04:00", 10210, 10280, 10190, 10220),
            _make_candle("10:05:00", 10220, 10290, 10200, 10250),
        ],
        "222222": [
            _make_candle("10:06:00", 20000, 20100, 19800, 19880),
            _make_candle("10:07:00", 19880, 19900, 19750, 19780),
            _make_candle("10:08:00", 19780, 19820, 19690, 19720),
            _make_candle("10:09:00", 19720, 19760, 19620, 19680),
            _make_candle("10:10:00", 19680, 19700, 19590, 19620),
        ],
        "333333": [
            _make_candle("10:09:00", 30000, 30100, 29900, 30080),
            _make_candle("10:10:00", 30080, 30150, 30020, 30100),
            _make_candle("10:11:00", 30100, 30180, 30070, 30120),
            _make_candle("10:12:00", 30120, 30190, 30080, 30140),
            _make_candle("10:13:00", 30140, 30200, 30100, 30160),
        ],
        "444444": [
            _make_candle("10:13:00", 40000, 40120, 39900, 40080),
            _make_candle("10:14:00", 40080, 40150, 40020, 40100),
            _make_candle("10:15:00", 40100, 40180, 40070, 40140),
            _make_candle("10:16:00", 40140, 40200, 40110, 40180),
            _make_candle("10:17:00", 40180, 40240, 40140, 40200),
        ],
        "555555": [
            _make_candle("10:21:00", 50000, 50200, 49900, 50100),
            _make_candle("10:22:00", 50100, 50300, 50050, 50250),
            _make_candle("10:23:00", 50250, 50400, 50200, 50300),
            _make_candle("10:24:00", 50300, 50500, 50280, 50400),
            _make_candle("10:25:00", 50400, 50600, 50350, 50500),
        ],
    }
    fake_kiwoom = types.SimpleNamespace(
        get_kiwoom_token=lambda: "dummy",
        get_minute_candles_ka10080=lambda _token, code, limit=700: candle_map.get(code, []),
    )
    import src.utils as utils_pkg
    monkeypatch.setattr(utils_pkg, "kiwoom_utils", fake_kiwoom, raising=False)
    monkeypatch.setitem(sys.modules, "src.utils.kiwoom_utils", fake_kiwoom)

    report = report_mod.build_missed_entry_counterfactual_report(target_date, token="dummy")

    cohorts = report["metrics"]["cohort_outcome_metrics"]
    assert cohorts["ai_numeric_inconsistency_no_buy"]["evaluated_candidates"] == 1
    assert cohorts["ai_numeric_consistency_recheck_failed"]["evaluated_candidates"] == 1
    assert cohorts["entry_armed_pre_submit_liquidity_block"]["evaluated_candidates"] == 1
    assert cohorts["early_accel_strong_bundle_recheck_skipped"]["evaluated_candidates"] == 1
    assert cohorts["buy_like_no_submit_terminal"]["evaluated_candidates"] == 1
    rows = {row["stock_code"]: row for row in report["rows"]}
    assert rows["111111"]["missed_submit_cohort"] == "ai_numeric_inconsistency_no_buy"
    assert rows["333333"]["missed_submit_cohort"] == "ai_numeric_consistency_recheck_failed"
    assert rows["222222"]["missed_submit_cohort"] == "entry_armed_pre_submit_liquidity_block"
    assert rows["444444"]["missed_submit_cohort"] == "early_accel_strong_bundle_recheck_skipped"
    assert rows["555555"]["missed_submit_cohort"] == "buy_like_no_submit_terminal"
    assert rows["555555"]["no_submit_reason"] == "broker_submit_not_reached"


def test_missed_entry_counterfactual_includes_snapshot_wait_or_skip_paths(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    target_date = "2026-06-18"
    _write_pipeline_events(
        tmp_path,
        target_date,
        [
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "scalp_entry_action_decision_snapshot",
                "stock_name": "대기차단",
                "stock_code": "333333",
                "record_id": 3,
                "fields": {
                    "chosen_action": "WAIT_REQUOTE",
                    "ai_score": "71.0",
                    "target_buy_price": "30000",
                },
                "emitted_at": "2026-06-18T10:10:01",
                "emitted_date": target_date,
            },
        ],
    )

    candle_map = {
        "333333": [
            _make_candle("10:11:00", 30000, 30150, 29980, 30120),
            _make_candle("10:12:00", 30120, 30210, 30080, 30180),
            _make_candle("10:13:00", 30180, 30220, 30110, 30160),
            _make_candle("10:14:00", 30160, 30240, 30120, 30210),
            _make_candle("10:15:00", 30210, 30280, 30180, 30240),
        ],
    }
    fake_kiwoom = types.SimpleNamespace(
        get_kiwoom_token=lambda: "dummy",
        get_minute_candles_ka10080=lambda _token, code, limit=700: candle_map.get(code, []),
    )
    import src.utils as utils_pkg
    monkeypatch.setattr(utils_pkg, "kiwoom_utils", fake_kiwoom, raising=False)
    monkeypatch.setitem(sys.modules, "src.utils.kiwoom_utils", fake_kiwoom)

    report = report_mod.build_missed_entry_counterfactual_report(target_date, token="dummy")

    assert report["summary"]["total_candidates"] == 1
    assert report["summary"]["evaluated_candidates"] == 1
    row = report["rows"][0]
    assert row["stock_code"] == "333333"
    assert row["buy_intent_source"] == "snapshot_decision_path"
    assert row["terminal_stage"] == "scalp_entry_action_decision_snapshot"
    assert row["missed_submit_cohort"] == "entry_armed_latency_or_safety_block"


def test_collects_all_missed_attempts_not_only_latest_per_stock(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    target_date = "2026-04-09"
    _write_pipeline_events(
        tmp_path,
        target_date,
        [
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "ai_confirmed",
                "stock_name": "반복종목",
                "stock_code": "444444",
                "record_id": 9,
                "fields": {"action": "BUY", "ai_score": "90"},
                "emitted_at": "2026-04-09T09:30:01",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "entry_armed",
                "stock_name": "반복종목",
                "stock_code": "444444",
                "record_id": 9,
                "fields": {"target_buy_price": "10000"},
                "emitted_at": "2026-04-09T09:30:02",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "latency_block",
                "stock_name": "반복종목",
                "stock_code": "444444",
                "record_id": 9,
                "fields": {"reason": "latency_state_danger"},
                "emitted_at": "2026-04-09T09:30:03",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "ai_confirmed",
                "stock_name": "반복종목",
                "stock_code": "444444",
                "record_id": 9,
                "fields": {"action": "BUY", "ai_score": "88"},
                "emitted_at": "2026-04-09T10:10:01",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "entry_armed",
                "stock_name": "반복종목",
                "stock_code": "444444",
                "record_id": 9,
                "fields": {"target_buy_price": "10100"},
                "emitted_at": "2026-04-09T10:10:02",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "order_bundle_submitted",
                "stock_name": "반복종목",
                "stock_code": "444444",
                "record_id": 9,
                "fields": {},
                "emitted_at": "2026-04-09T10:10:03",
                "emitted_date": target_date,
            },
        ],
    )

    fake_kiwoom = types.SimpleNamespace(
        get_kiwoom_token=lambda: "dummy",
        get_minute_candles_ka10080=lambda _token, code, limit=700: [
            _make_candle("09:31:00", 10000, 10050, 9950, 10020),
            _make_candle("09:32:00", 10020, 10080, 10000, 10050),
            _make_candle("09:33:00", 10050, 10100, 10020, 10060),
            _make_candle("09:34:00", 10060, 10090, 10030, 10040),
            _make_candle("09:35:00", 10040, 10070, 10010, 10030),
            _make_candle("09:36:00", 10030, 10060, 10000, 10020),
            _make_candle("09:37:00", 10020, 10040, 9990, 10010),
            _make_candle("09:38:00", 10010, 10030, 9980, 10000),
            _make_candle("09:39:00", 10000, 10020, 9970, 9990),
            _make_candle("09:40:00", 9990, 10010, 9960, 9980),
        ],
    )
    import src.utils as utils_pkg
    monkeypatch.setattr(utils_pkg, "kiwoom_utils", fake_kiwoom, raising=False)
    monkeypatch.setitem(sys.modules, "src.utils.kiwoom_utils", fake_kiwoom)

    report = report_mod.build_missed_entry_counterfactual_report(target_date, token="dummy")

    assert report["summary"]["total_candidates"] == 1
    assert report["rows"][0]["stock_code"] == "444444"
    assert report["rows"][0]["terminal_stage"] == "latency_block"
    assert report["buy_signal_universe"]["metrics"]["total_buy_judged_attempts"] == 2
    assert report["buy_signal_universe"]["metrics"]["entered_attempts"] == 1


def test_recovery_unlock_pre_submit_overbought_block_is_counted_as_missed_candidate(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    target_date = "2026-06-12"
    _write_pipeline_events(
        tmp_path,
        target_date,
        [
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "ai_cooldown_blocked",
                "stock_name": "원익IPS",
                "stock_code": "240810",
                "record_id": 10240,
                "fields": {"ai_score": "62.0"},
                "emitted_at": "2026-06-12T10:55:42.956195",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "score65_74_recovery_probe_entry_unlocked",
                "stock_name": "원익IPS",
                "stock_code": "240810",
                "record_id": 10240,
                "fields": {"ai_score": "62.0", "source": "score65_74_recovery_probe"},
                "emitted_at": "2026-06-12T10:55:42.957493",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "entry_armed",
                "stock_name": "원익IPS",
                "stock_code": "240810",
                "record_id": 10240,
                "fields": {"ai_score": "62.0", "target_buy_price": "174300"},
                "emitted_at": "2026-06-12T10:55:42.959217",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "budget_pass",
                "stock_name": "원익IPS",
                "stock_code": "240810",
                "record_id": 10240,
                "fields": {"qty": "12", "safe_budget": "2091600"},
                "emitted_at": "2026-06-12T10:55:43.105597",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "latency_pass",
                "stock_name": "원익IPS",
                "stock_code": "240810",
                "record_id": 10240,
                "fields": {"signal_price": "175200"},
                "emitted_at": "2026-06-12T10:55:44.307067",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "pre_submit_overbought_pullback_guard_block",
                "stock_name": "원익IPS",
                "stock_code": "240810",
                "record_id": 10240,
                "fields": {
                    "submitted_order_price": "174300",
                    "mark_price_at_submit": "175200",
                    "pre_submit_overbought_reason": "pullback_or_rebreak_not_confirmed",
                },
                "emitted_at": "2026-06-12T10:55:44.324678",
                "emitted_date": target_date,
            },
        ],
    )

    fake_kiwoom = types.SimpleNamespace(
        get_kiwoom_token=lambda: "dummy",
        get_minute_candles_ka10080=lambda _token, code, limit=700: [
            _make_candle("10:56:00", 174300, 174900, 174200, 174800),
            _make_candle("10:57:00", 174800, 175100, 174700, 174900),
            _make_candle("10:58:00", 174900, 175000, 174800, 174850),
            _make_candle("10:59:00", 174850, 175900, 174800, 175900),
            _make_candle("11:00:00", 175900, 176000, 175000, 175300),
            _make_candle("11:01:00", 175300, 175400, 175000, 175100),
            _make_candle("11:02:00", 175100, 175200, 174700, 174800),
            _make_candle("11:03:00", 174800, 175600, 174700, 175400),
            _make_candle("11:04:00", 175400, 176200, 175300, 176200),
            _make_candle("11:05:00", 176200, 176250, 176000, 176150),
        ],
    )
    import src.utils as utils_pkg
    monkeypatch.setattr(utils_pkg, "kiwoom_utils", fake_kiwoom, raising=False)
    monkeypatch.setitem(sys.modules, "src.utils.kiwoom_utils", fake_kiwoom)

    report = report_mod.build_missed_entry_counterfactual_report(target_date, token="dummy")

    assert report["summary"]["total_candidates"] == 1
    assert report["summary"]["evaluated_candidates"] == 1
    row = report["rows"][0]
    assert row["stock_code"] == "240810"
    assert row["terminal_stage"] == "pre_submit_overbought_pullback_guard_block"
    assert row["buy_intent_source"] == "inferred_entry_armed_path"
    assert row["signal_price"] == 174300
    assert row["close_10m_pct"] > 0


def test_recovery_unlock_pre_submit_resume_loop_is_deduped(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    target_date = "2026-06-12"
    rows = []
    for idx, (stage, emitted_at, target_price) in enumerate(
        [
            ("entry_armed", "2026-06-12T10:35:05", "13220"),
            ("pre_submit_overbought_pullback_guard_block", "2026-06-12T10:35:06", "13220"),
            ("entry_armed_resume", "2026-06-12T10:35:13", "13230"),
            ("pre_submit_overbought_pullback_guard_block", "2026-06-12T10:35:14", "13230"),
            ("entry_armed_resume", "2026-06-12T10:36:18", "13270"),
            ("pre_submit_overbought_pullback_guard_block", "2026-06-12T10:36:19", "13270"),
        ],
        start=1,
    ):
        fields = {"ai_score": "66.0", "target_buy_price": target_price}
        if stage == "pre_submit_overbought_pullback_guard_block":
            fields = {
                "submitted_order_price": target_price,
                "mark_price_at_submit": "13300",
                "pre_submit_overbought_reason": "pullback_or_rebreak_not_confirmed",
            }
        rows.append(
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": stage,
                "stock_name": "에스오에스랩",
                "stock_code": "464080",
                "record_id": 10357,
                "fields": fields,
                "emitted_at": emitted_at,
                "emitted_date": target_date,
            }
        )
    _write_pipeline_events(tmp_path, target_date, rows)

    fake_kiwoom = types.SimpleNamespace(
        get_kiwoom_token=lambda: "dummy",
        get_minute_candles_ka10080=lambda _token, code, limit=700: [
            _make_candle("10:36:00", 13220, 13300, 13220, 13280),
            _make_candle("10:37:00", 13280, 13340, 13280, 13330),
            _make_candle("10:38:00", 13330, 13340, 13300, 13310),
            _make_candle("10:39:00", 13310, 13330, 13300, 13320),
            _make_candle("10:40:00", 13320, 13330, 13300, 13310),
            _make_candle("10:41:00", 13310, 13320, 13300, 13310),
            _make_candle("10:42:00", 13310, 13330, 13300, 13320),
            _make_candle("10:43:00", 13320, 13330, 13300, 13310),
            _make_candle("10:44:00", 13310, 13320, 13300, 13310),
            _make_candle("10:45:00", 13310, 13320, 13300, 13310),
        ],
    )
    import src.utils as utils_pkg
    monkeypatch.setattr(utils_pkg, "kiwoom_utils", fake_kiwoom, raising=False)
    monkeypatch.setitem(sys.modules, "src.utils.kiwoom_utils", fake_kiwoom)

    report = report_mod.build_missed_entry_counterfactual_report(target_date, token="dummy")

    assert report["summary"]["total_candidates"] == 1
    assert report["summary"]["evaluated_candidates"] == 1
    assert report["reason_breakdown"][0]["stage"] == "pre_submit_overbought_pullback_guard_block"
    assert report["reason_breakdown"][0]["candidates"] == 1
    assert report["rows"][0]["buy_intent_source"] == "inferred_entry_armed_path"
