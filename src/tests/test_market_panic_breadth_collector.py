from datetime import datetime
from pathlib import Path

import pytest

from src.engine import market_panic_breadth_collector as collector


def test_parse_kiwoom_industry_rows_from_nested_response():
    payload = {
        "all_inds_index": [
            {
                "inds_cd": "001",
                "inds_nm": "종합(KOSPI)",
                "cur_prc": "2,700.10",
                "flu_rt": "-1.45",
            },
            {
                "inds_cd": "101",
                "inds_nm": "코스닥",
                "cur_prc": "850.00",
                "flu_rt": "-2.10",
            },
            {
                "inds_cd": "201",
                "inds_nm": "반도체",
                "cur_prc": "1,000",
                "flu_rt": "-2.40",
            },
        ]
    }

    rows = collector.parse_kiwoom_industry_rows(payload)

    assert len(rows) == 3
    assert rows[0]["code"] == "001"
    assert rows[0]["change_pct"] == -1.45
    assert rows[2]["name"] == "반도체"


def test_summarize_breadth_sets_report_only_risk_off_advisory():
    rows = [
        {"code": "001", "name": "종합(KOSPI)", "change_pct": -1.5},
        {"code": "101", "name": "코스닥", "change_pct": -2.1},
        {"code": "201", "name": "반도체", "change_pct": -2.4},
        {"code": "202", "name": "IT", "change_pct": -1.2},
        {"code": "203", "name": "바이오", "change_pct": -2.2},
        {"code": "204", "name": "운송", "change_pct": 0.2},
    ]

    summary = collector.summarize_breadth(
        rows,
        industry_down_ratio_floor_pct=50.0,
        severe_down_ratio_floor_pct=40.0,
    )

    assert summary["risk_off_advisory"] is True
    assert summary["weighted_market_breadth"]["index_change_pct"] < -1.2
    assert summary["decision_authority"] == "source_quality_only"
    assert "order_submit" in summary["forbidden_uses"]
    assert summary["industry_breadth"]["down_count"] == 3
    assert summary["risk_on_advisory"] is False


def test_summarize_breadth_splits_single_market_risk_off_from_composite():
    rows = [
        {
            "code": "001",
            "name": "종합(KOSPI)",
            "change_pct": 0.4,
            "rising_count": 520,
            "fall_count": 320,
            "listed_count": 900,
        },
        {
            "code": "101",
            "name": "코스닥",
            "change_pct": -1.7,
            "rising_count": 210,
            "fall_count": 780,
            "listed_count": 1000,
        },
        {"code": "201", "name": "반도체", "change_pct": -2.4},
        {"code": "202", "name": "IT", "change_pct": -1.2},
        {"code": "203", "name": "바이오", "change_pct": -2.2},
        {"code": "204", "name": "운송", "change_pct": 0.2},
    ]

    summary = collector.summarize_breadth(
        rows,
        industry_down_ratio_floor_pct=50.0,
        severe_down_ratio_floor_pct=40.0,
    )

    assert summary["risk_off_advisory"] is False
    assert summary["single_market_risk_off_advisory"] is True
    assert summary["weighted_market_breadth"]["index_change_pct"] == -0.335
    assert "single_market_index_intraday_drop" in summary["reasons"]
    assert "live market breadth panic thresholds not breached" in summary["reasons"]


def test_summarize_breadth_sets_report_only_risk_on_advisory():
    rows = [
        {
            "code": "001",
            "name": "종합(KOSPI)",
            "change_pct": 1.5,
            "rising_count": 760,
            "fall_count": 120,
            "listed_count": 900,
        },
        {
            "code": "101",
            "name": "코스닥",
            "change_pct": 2.1,
            "rising_count": 820,
            "fall_count": 130,
            "listed_count": 1000,
        },
        {"code": "201", "name": "반도체", "change_pct": 2.4},
        {"code": "202", "name": "IT", "change_pct": 1.2},
        {"code": "203", "name": "바이오", "change_pct": 2.2},
        {"code": "204", "name": "운송", "change_pct": -0.2},
    ]

    summary = collector.summarize_breadth(
        rows,
        industry_up_ratio_floor_pct=50.0,
        severe_up_ratio_floor_pct=40.0,
    )

    assert summary["risk_on_advisory"] is True
    assert summary["weighted_market_breadth"]["index_change_pct"] > 1.2
    assert summary["risk_off_advisory"] is False
    assert summary["decision_authority"] == "source_quality_only"
    assert "order_submit" in summary["forbidden_uses"]
    assert summary["industry_breadth"]["up_count"] == 3
    assert summary["stock_breadth"]["max_rise_ratio_pct"] >= 80.0


def test_build_market_panic_breadth_report_from_injected_rows():
    report = collector.build_market_panic_breadth_report(
        "2026-05-15",
        as_of=datetime.fromisoformat("2026-05-15T11:30:00"),
        rows=[
            {"code": "001", "name": "종합(KOSPI)", "change_pct": -1.5},
            {"code": "201", "name": "반도체", "change_pct": -2.4},
            {"code": "202", "name": "IT", "change_pct": -2.1},
        ],
    )

    assert report["report_type"] == "market_panic_breadth"
    assert report["policy"]["runtime_effect"] == "report_only_no_mutation"
    assert report["source_quality"]["status"] == "ok"


def test_market_weakness_observation_requires_recovery_margin():
    weak_summary = collector.summarize_breadth(
        [
            {"code": "001", "name": "종합(KOSPI)", "change_pct": -1.5},
            {"code": "101", "name": "코스닥", "change_pct": -1.3},
            {"code": "201", "name": "반도체", "change_pct": -2.4},
            {"code": "202", "name": "IT", "change_pct": -1.2},
            {"code": "203", "name": "바이오", "change_pct": -2.2},
        ]
    )
    weak = collector.build_market_weakness_observation(
        weak_summary,
        target_date="2026-08-28",
        as_of="2026-08-28T10:00:00",
        source_quality_status="ok",
    )

    assert weak["raw_state"] == "BROAD_WEAKNESS"
    assert weak["source_quality_ready"] is True
    assert weak["runtime_effect"] is False
    assert weak["allowed_runtime_apply"] is False
    assert weak["sample_floor"]["activation_unique_observations"] == 2
    assert weak["sample_floor"]["release_unique_observations"] == 3

    near_boundary_summary = collector.summarize_breadth(
        [
            {"code": "001", "name": "종합(KOSPI)", "change_pct": -1.0},
            {"code": "101", "name": "코스닥", "change_pct": -0.2},
            {"code": "201", "name": "반도체", "change_pct": -0.4},
            {"code": "202", "name": "IT", "change_pct": -0.2},
            {"code": "203", "name": "바이오", "change_pct": 0.1},
        ]
    )
    near_boundary = collector.build_market_weakness_observation(
        near_boundary_summary,
        target_date="2026-08-28",
        as_of="2026-08-28T10:02:00",
        source_quality_status="ok",
    )
    assert near_boundary["raw_state"] == "NEAR_WEAKNESS_BOUNDARY"
    assert near_boundary["release_margin"]["passed"] is False

    recovered_summary = collector.summarize_breadth(
        [
            {
                "code": "001",
                "name": "종합(KOSPI)",
                "change_pct": -0.4,
                "rising_count": 500,
                "fall_count": 300,
                "listed_count": 900,
            },
            {
                "code": "101",
                "name": "코스닥",
                "change_pct": -0.2,
                "rising_count": 550,
                "fall_count": 350,
                "listed_count": 1000,
            },
            {"code": "201", "name": "반도체", "change_pct": -0.4},
            {"code": "202", "name": "IT", "change_pct": 0.2},
            {"code": "203", "name": "바이오", "change_pct": 0.1},
        ]
    )
    recovered = collector.build_market_weakness_observation(
        recovered_summary,
        target_date="2026-08-28",
        as_of="2026-08-28T10:04:00",
        source_quality_status="ok",
    )
    assert recovered["raw_state"] == "RECOVERY_EVIDENCE"
    assert recovered["release_margin"]["passed"] is True
    assert (
        recovered["response_research_contract"]["status"]
        == "source_only_counterfactual_collection"
    )


def test_market_weakness_source_gate_requires_both_named_markets():
    summary = collector.summarize_breadth(
        [
            {"code": "001", "name": "종합(KOSPI)", "change_pct": -1.5},
            {"code": "201", "name": "반도체", "change_pct": -2.4},
            {"code": "202", "name": "IT", "change_pct": -1.2},
            {"code": "203", "name": "바이오", "change_pct": -2.2},
        ]
    )

    observation = collector.build_market_weakness_observation(
        summary,
        target_date="2026-08-28",
        as_of="2026-08-28T10:00:00",
        source_quality_status="ok",
    )

    assert observation["source_quality_ready"] is False
    assert observation["raw_state"] == "UNKNOWN"


def test_write_report_preserves_immutable_weakness_observation(tmp_path, monkeypatch):
    monkeypatch.setattr(collector, "DATA_DIR", tmp_path)
    report = collector.build_market_panic_breadth_report(
        "2026-08-28",
        as_of=datetime.fromisoformat("2026-08-28T10:00:00"),
        rows=[
            {"code": "001", "name": "종합(KOSPI)", "change_pct": -1.5},
            {"code": "101", "name": "코스닥", "change_pct": -1.3},
            {"code": "201", "name": "반도체", "change_pct": -2.4},
            {"code": "202", "name": "IT", "change_pct": -1.2},
            {"code": "203", "name": "바이오", "change_pct": -2.2},
        ],
    )

    report_path = collector.write_report(report)
    history_path = report["market_weakness_observation"]["history_path"]

    assert report_path.exists()
    assert Path(history_path).exists()


def test_write_report_rejects_weakness_history_path_drift(tmp_path, monkeypatch):
    monkeypatch.setattr(collector, "DATA_DIR", tmp_path)
    report = collector.build_market_panic_breadth_report(
        "2026-08-28",
        as_of=datetime.fromisoformat("2026-08-28T10:00:00"),
        rows=[
            {"code": "001", "name": "종합(KOSPI)", "change_pct": -1.5},
            {"code": "101", "name": "코스닥", "change_pct": -1.3},
            {"code": "201", "name": "반도체", "change_pct": -2.4},
            {"code": "202", "name": "IT", "change_pct": -1.2},
            {"code": "203", "name": "바이오", "change_pct": -2.2},
        ],
    )
    report["market_weakness_observation"]["history_path"] = str(
        tmp_path / "wrong" / "observation.json"
    )

    with pytest.raises(
        ValueError, match="market_weakness_history_path_contract_mismatch"
    ):
        collector.write_report(report)

    assert not collector._report_path("2026-08-28").exists()
