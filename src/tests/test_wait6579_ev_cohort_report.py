import json
import sys
import types

from src.engine import wait6579_ev_cohort_report as report_mod


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


def test_build_wait6579_ev_cohort_report(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    target_date = "2026-04-21"
    _write_pipeline_events(
        tmp_path,
        target_date,
        [
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "wait65_79_ev_candidate",
                "stock_name": "풀체결후보",
                "stock_code": "111111",
                "record_id": 101,
                "fields": {
                    "action": "WAIT",
                    "ai_score": "68",
                    "buy_pressure": "72.0",
                    "tick_accel": "1.30",
                    "micro_vwap_bp": "2.2",
                    "latency_state": "SAFE",
                    "parse_ok": "True",
                    "ai_response_ms": "280",
                },
                "emitted_at": "2026-04-21T10:00:01",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "entry_armed",
                "stock_name": "풀체결후보",
                "stock_code": "111111",
                "record_id": 101,
                "fields": {"target_buy_price": "10000"},
                "emitted_at": "2026-04-21T10:00:02",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "budget_pass",
                "stock_name": "풀체결후보",
                "stock_code": "111111",
                "record_id": 101,
                "fields": {"qty": "10", "safe_budget": "100000"},
                "emitted_at": "2026-04-21T10:00:03",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "blocked_ai_score",
                "stock_name": "풀체결후보",
                "stock_code": "111111",
                "record_id": 101,
                "fields": {"threshold": "75"},
                "emitted_at": "2026-04-21T10:00:04",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "wait65_79_ev_candidate",
                "stock_name": "부분체결후보",
                "stock_code": "222222",
                "record_id": 202,
                "fields": {
                    "action": "WAIT",
                    "ai_score": "76",
                    "buy_pressure": "66.5",
                    "tick_accel": "1.21",
                    "micro_vwap_bp": "0.8",
                    "latency_state": "CAUTION",
                    "parse_ok": "True",
                    "ai_response_ms": "520",
                },
                "emitted_at": "2026-04-21T10:05:01",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "entry_armed",
                "stock_name": "부분체결후보",
                "stock_code": "222222",
                "record_id": 202,
                "fields": {"target_buy_price": "20000"},
                "emitted_at": "2026-04-21T10:05:02",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "budget_pass",
                "stock_name": "부분체결후보",
                "stock_code": "222222",
                "record_id": 202,
                "fields": {"qty": "5", "safe_budget": "100000"},
                "emitted_at": "2026-04-21T10:05:03",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "latency_block",
                "stock_name": "부분체결후보",
                "stock_code": "222222",
                "record_id": 202,
                "fields": {"reason": "latency_state_danger"},
                "emitted_at": "2026-04-21T10:05:04",
                "emitted_date": target_date,
            },
        ],
    )

    candle_map = {
        "111111": [
            _make_candle("10:01:00", 10000, 10120, 9990, 10080),
            _make_candle("10:02:00", 10080, 10140, 10040, 10100),
            _make_candle("10:03:00", 10100, 10180, 10080, 10150),
            _make_candle("10:04:00", 10150, 10190, 10100, 10160),
            _make_candle("10:05:00", 10160, 10200, 10120, 10180),
            _make_candle("10:06:00", 10180, 10220, 10130, 10200),
            _make_candle("10:07:00", 10200, 10230, 10160, 10210),
            _make_candle("10:08:00", 10210, 10250, 10170, 10230),
            _make_candle("10:09:00", 10230, 10260, 10190, 10240),
            _make_candle("10:10:00", 10240, 10270, 10200, 10250),
        ],
        "222222": [
            _make_candle("10:06:00", 20050, 20090, 20020, 20060),
            _make_candle("10:07:00", 20060, 20120, 20030, 20080),
            _make_candle("10:08:00", 20080, 20130, 20040, 20100),
            _make_candle("10:09:00", 20100, 20140, 20050, 20120),
            _make_candle("10:10:00", 20120, 20160, 20080, 20140),
            _make_candle("10:11:00", 20140, 20170, 20100, 20150),
            _make_candle("10:12:00", 20150, 20190, 20110, 20160),
            _make_candle("10:13:00", 20160, 20200, 20120, 20170),
            _make_candle("10:14:00", 20170, 20210, 20130, 20180),
            _make_candle("10:15:00", 20180, 20220, 20140, 20190),
        ],
    }
    fake_kiwoom = types.SimpleNamespace(
        get_kiwoom_token=lambda: "dummy",
        get_minute_candles_ka10080=lambda _token, code, limit=700: candle_map.get(code, []),
    )
    import src.utils as utils_pkg
    monkeypatch.setattr(utils_pkg, "kiwoom_utils", fake_kiwoom, raising=False)
    monkeypatch.setitem(sys.modules, "src.utils.kiwoom_utils", fake_kiwoom)

    report = report_mod.build_wait6579_ev_cohort_report(target_date, token="dummy")

    assert report["metrics"]["total_candidates"] == 2
    assert report["metrics"]["missed_attempts"] == 2
    assert len(report["rows"]) == 2
    row_keys = set(report["rows"][0].keys())
    assert {
        "buy_pressure",
        "tick_accel",
        "micro_vwap_bp",
        "latency_state",
        "parse_ok",
        "ai_response_ms",
        "terminal_blocker",
        "submission_blocker",
        "has_budget_pass",
        "has_latency_block",
        "has_recovery_check",
    }.issubset(row_keys)

    split_map = {row["fill_type"]: row["samples"] for row in report["fill_split"]}
    assert split_map.get("FULL", 0) == 1
    assert split_map.get("PARTIAL", 0) == 1

    terminal_map = {row["terminal_blocker"]: row["samples"] for row in report["terminal_breakdown"]}
    assert terminal_map["blocked_ai_score"] == 1
    assert terminal_map["latency_block"] == 1
    assert report["preflight"]["behavior_change"] == "none"
    assert report["preflight"]["budget_pass_candidates"] == 2
    assert report["preflight"]["latency_block_candidates"] == 1
    assert report["preflight"]["submitted_candidates"] == 0
    blocker_map = {row["label"]: row["samples"] for row in report["preflight"]["submission_blocker_breakdown"]}
    assert blocker_map["no_recovery_check"] == 1
    assert blocker_map["latency_block"] == 1
    assert report["approval_gate"]["min_sample_gate_passed"] is False


def test_build_wait6579_ev_cohort_report_empty(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    target_date = "2026-04-21"
    _write_pipeline_events(tmp_path, target_date, [])

    report = report_mod.build_wait6579_ev_cohort_report(target_date, token="dummy")

    assert report["metrics"]["total_candidates"] == 0
    assert report["rows"] == []
    assert report["preflight"]["behavior_change"] == "none"
    assert report["preflight"]["observability_passed"] is True
    assert report["approval_gate"]["threshold_relaxation_approved"] is False


def test_build_wait6579_preflight_report_uses_events_only(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    target_date = "2026-04-21"
    _write_pipeline_events(
        tmp_path,
        target_date,
        [
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "wait65_79_ev_candidate",
                "stock_name": "후보",
                "stock_code": "333333",
                "record_id": 303,
                "fields": {"action": "WAIT", "ai_score": "72"},
                "emitted_at": "2026-04-21T10:10:01",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "watching_buy_recovery_canary",
                "stock_name": "후보",
                "stock_code": "333333",
                "record_id": 303,
                "fields": {"promoted": "true"},
                "emitted_at": "2026-04-21T10:10:02",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "wait6579_probe_canary_applied",
                "stock_name": "후보",
                "stock_code": "333333",
                "record_id": 303,
                "fields": {"applied": "true"},
                "emitted_at": "2026-04-21T10:10:03",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "budget_pass",
                "stock_name": "후보",
                "stock_code": "333333",
                "record_id": 303,
                "fields": {"qty": "1"},
                "emitted_at": "2026-04-21T10:10:04",
                "emitted_date": target_date,
            },
            {
                "pipeline": "ENTRY_PIPELINE",
                "stage": "order_bundle_submitted",
                "stock_name": "후보",
                "stock_code": "333333",
                "record_id": 303,
                "fields": {"legs": "1"},
                "emitted_at": "2026-04-21T10:10:05",
                "emitted_date": target_date,
            },
        ],
    )

    report = report_mod.build_wait6579_preflight_report(target_date)

    assert report["preflight"]["behavior_change"] == "none"
    assert report["preflight"]["recovery_check_candidates"] == 1
    assert report["preflight"]["recovery_promoted_candidates"] == 1
    assert report["preflight"]["probe_applied_candidates"] == 1
    assert report["preflight"]["budget_pass_candidates"] == 1
    assert report["preflight"]["submitted_candidates"] == 1
    assert report["rows"][0]["submission_blocker"] == "submitted"
