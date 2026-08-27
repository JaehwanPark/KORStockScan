from __future__ import annotations

import hashlib
import json
from datetime import date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from src.engine.monitoring import widget_research_watch_collector as watch

KST = ZoneInfo("Asia/Seoul")


def _write_source_report(
    path: Path,
    symbols: list[tuple[str, str]],
    *,
    target_date: str = "2026-08-12",
) -> str:
    report = {
        "schema": "widget_collector_expansion_recommendation_v1",
        "target_date": target_date,
        "recommendations": [
            {
                "stock_code": code,
                "stock_name": name,
                "recommendation_tier": "research_watch",
                "implementation_review_ready": False,
            }
            for code, name in symbols
        ],
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "collector_created": False,
        "service_started": False,
    }
    path.write_text(json.dumps(report), encoding="utf-8")
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_config(
    path: Path,
    *,
    source_report: Path,
    source_sha: str,
    symbols: list[tuple[str, str]],
) -> None:
    path.write_text(
        json.dumps(
            {
                "schema": watch.CONFIG_SCHEMA,
                "enabled": True,
                "effective_from": "2026-08-13",
                "source_target_date": "2026-08-12",
                "source_report": str(source_report),
                "source_report_sha256": source_sha,
                "symbols": [
                    {
                        "stock_code": code,
                        "stock_name": name,
                        "recommendation_tier": "research_watch",
                    }
                    for code, name in symbols
                ],
                "authority": watch.AUTHORITY,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
            }
        ),
        encoding="utf-8",
    )


def test_config_requires_exact_recommendation_lineage(tmp_path):
    symbols = [("111111", "테스트")]
    report_path = tmp_path / "report.json"
    config_path = tmp_path / "config.json"
    source_sha = _write_source_report(report_path, symbols)
    _write_config(
        config_path,
        source_report=report_path,
        source_sha=source_sha,
        symbols=symbols,
    )

    config = watch.load_config(observed_date=date(2026, 8, 13), config_path=config_path)

    assert config["symbols"][0]["stock_code"] == "111111"
    assert config["runtime_effect"] is False
    assert config["allowed_runtime_apply"] is False


def test_config_rejects_symbol_not_present_in_source_report(tmp_path):
    report_path = tmp_path / "report.json"
    config_path = tmp_path / "config.json"
    source_sha = _write_source_report(report_path, [("111111", "테스트")])
    _write_config(
        config_path,
        source_report=report_path,
        source_sha=source_sha,
        symbols=[("222222", "미승인")],
    )

    with pytest.raises(ValueError, match="symbol_not_in_source_report"):
        watch.load_config(observed_date=date(2026, 8, 13), config_path=config_path)


def test_config_rejects_source_not_prior_to_effective_date(tmp_path):
    symbols = [("111111", "테스트")]
    report_path = tmp_path / "report.json"
    config_path = tmp_path / "config.json"
    source_sha = _write_source_report(
        report_path,
        symbols,
        target_date="2026-08-13",
    )
    _write_config(
        config_path,
        source_report=report_path,
        source_sha=source_sha,
        symbols=symbols,
    )
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["source_target_date"] = "2026-08-13"
    config_path.write_text(json.dumps(config), encoding="utf-8")

    with pytest.raises(ValueError, match="source_not_prior_to_effective_date"):
        watch.load_config(observed_date=date(2026, 8, 13), config_path=config_path)


def test_config_accepts_fifteen_bounded_research_watch_symbols(tmp_path):
    symbols = [(f"{index:06d}", f"테스트{index}") for index in range(1, 16)]
    report_path = tmp_path / "report.json"
    config_path = tmp_path / "config.json"
    source_sha = _write_source_report(report_path, symbols)
    _write_config(
        config_path,
        source_report=report_path,
        source_sha=source_sha,
        symbols=symbols,
    )

    config = watch.load_config(observed_date=date(2026, 8, 13), config_path=config_path)

    assert len(config["symbols"]) == 15


def test_default_config_carries_20260827_research_watch_lineage():
    config = watch.load_config(observed_date=date(2026, 8, 28))
    symbols = {row["stock_code"]: row for row in config["symbols"]}

    assert len(symbols) == 13
    assert set(symbols) >= {"361610", "488280"}
    for code in ("361610", "488280"):
        assert symbols[code]["source_target_date"] == "2026-08-27"
        assert symbols[code]["source_report_sha256"] == (
            "d5c5669c1eabb663ac2714ed253de97034453ca24c6e1c8b66f55107a9f7e385"
        )
    assert config["runtime_effect"] is False
    assert config["allowed_runtime_apply"] is False


def test_config_rejects_more_than_fifteen_research_watch_symbols(tmp_path):
    symbols = [(f"{index:06d}", f"테스트{index}") for index in range(1, 17)]
    report_path = tmp_path / "report.json"
    config_path = tmp_path / "config.json"
    source_sha = _write_source_report(report_path, symbols)
    _write_config(
        config_path,
        source_report=report_path,
        source_sha=source_sha,
        symbols=symbols,
    )

    with pytest.raises(ValueError, match="symbol_count_invalid"):
        watch.load_config(observed_date=date(2026, 8, 13), config_path=config_path)


def test_config_accepts_cumulative_symbols_with_per_symbol_lineage(tmp_path):
    old_report_path = tmp_path / "old_report.json"
    new_report_path = tmp_path / "new_report.json"
    config_path = tmp_path / "config.json"
    old_sha = _write_source_report(
        old_report_path,
        [("111111", "기존")],
        target_date="2026-08-12",
    )
    new_sha = _write_source_report(
        new_report_path,
        [("222222", "신규")],
        target_date="2026-08-19",
    )
    config = {
        "schema": watch.CONFIG_SCHEMA,
        "enabled": True,
        "effective_from": "2026-08-20",
        "source_target_date": "2026-08-19",
        "source_report": str(new_report_path),
        "source_report_sha256": new_sha,
        "source_reports": [
            {
                "target_date": "2026-08-12",
                "path": str(old_report_path),
                "sha256": old_sha,
            },
            {
                "target_date": "2026-08-19",
                "path": str(new_report_path),
                "sha256": new_sha,
            },
        ],
        "symbols": [
            {
                "stock_code": "111111",
                "stock_name": "기존",
                "recommendation_tier": "research_watch",
                "source_target_date": "2026-08-12",
                "source_report_sha256": old_sha,
            },
            {
                "stock_code": "222222",
                "stock_name": "신규",
                "recommendation_tier": "research_watch",
                "source_target_date": "2026-08-19",
                "source_report_sha256": new_sha,
            },
        ],
        "authority": watch.AUTHORITY,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
    }
    config_path.write_text(json.dumps(config), encoding="utf-8")

    loaded = watch.load_config(observed_date=date(2026, 8, 20), config_path=config_path)

    assert len(loaded["source_reports_resolved"]) == 2
    assert loaded["symbols"][0]["source_target_date"] == "2026-08-12"
    assert loaded["symbols"][0]["source_report_sha256"] == old_sha
    assert loaded["symbols"][1]["source_target_date"] == "2026-08-19"
    assert loaded["symbols"][1]["source_report_sha256"] == new_sha


def test_config_rejects_symbol_bound_to_wrong_source_lineage(tmp_path):
    old_report_path = tmp_path / "old_report.json"
    new_report_path = tmp_path / "new_report.json"
    config_path = tmp_path / "config.json"
    old_sha = _write_source_report(old_report_path, [("111111", "기존")])
    new_sha = _write_source_report(
        new_report_path,
        [("222222", "신규")],
        target_date="2026-08-19",
    )
    _write_config(
        config_path,
        source_report=new_report_path,
        source_sha=new_sha,
        symbols=[("111111", "기존")],
    )
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["effective_from"] = "2026-08-20"
    config["source_target_date"] = "2026-08-19"
    config["source_reports"] = [
        {
            "target_date": "2026-08-12",
            "path": str(old_report_path),
            "sha256": old_sha,
        },
        {
            "target_date": "2026-08-19",
            "path": str(new_report_path),
            "sha256": new_sha,
        },
    ]
    config_path.write_text(json.dumps(config), encoding="utf-8")

    with pytest.raises(ValueError, match="symbol_not_in_source_report"):
        watch.load_config(observed_date=date(2026, 8, 20), config_path=config_path)


def test_budget_paced_cycle_scales_without_widening_request_budget():
    assert (
        watch._effective_cycle_interval_sec(configured_interval_sec=60, symbol_count=5)
        == 60
    )
    assert (
        watch._effective_cycle_interval_sec(configured_interval_sec=60, symbol_count=9)
        == 108
    )
    assert (
        watch._effective_cycle_interval_sec(configured_interval_sec=60, symbol_count=10)
        == 120
    )
    assert (
        watch._effective_cycle_interval_sec(configured_interval_sec=60, symbol_count=15)
        == 180
    )


class _FakeClient:
    def __init__(self, *, fail_code: str | None = None) -> None:
        self.calls: list[tuple[str, str, dict[str, str]]] = []
        self.fail_code = fail_code

    def post(self, path: str, api_id: str, payload: dict[str, str]) -> dict:
        self.calls.append((path, api_id, payload))
        if payload["stk_cd"] == self.fail_code:
            raise RuntimeError("synthetic_source_failure")
        if api_id == "ka10001":
            return {"cur_prc": "10000"}
        if api_id == "ka10004":
            return {
                "buy_fpr_bid": "9990",
                "sel_fpr_bid": "10000",
                "buy_fpr_req": "100",
                "sel_fpr_req": "90",
                "bid_req_base_tm": "100100",
            }
        if api_id == "ka10080":
            return {
                "stk_min_pole_chart_qry": [
                    {
                        "cntr_tm": "20260813100100",
                        "cur_prc": "10010",
                        "open_pric": "10000",
                        "high_pric": "10020",
                        "low_pric": "9990",
                        "trde_qty": "1234",
                    },
                    {
                        "cntr_tm": "20260813100000",
                        "cur_prc": "10000",
                        "open_pric": "9990",
                        "high_pric": "10010",
                        "low_pric": "9980",
                        "trde_qty": "1000",
                    },
                ]
            }
        raise AssertionError(api_id)


def _runtime_config(symbols: list[tuple[str, str]]) -> dict:
    return {
        "source_target_date": "2026-08-12",
        "source_report_sha256": "a" * 64,
        "symbols": [
            {
                "stock_code": code,
                "stock_name": name,
                "recommendation_tier": "research_watch",
                "source_target_date": "2026-08-12",
                "source_report_sha256": "a" * 64,
            }
            for code, name in symbols
        ],
    }


def test_collector_writes_completed_bar_without_signal_or_order_authority(tmp_path):
    client = _FakeClient()
    collector = watch.WidgetResearchWatchCollector(
        config=_runtime_config([("111111", "테스트")]),
        client=client,
        output_dir=tmp_path / "observations",
        snapshot_dir=tmp_path / "snapshots",
    )
    observed_at = datetime(2026, 8, 13, 10, 1, 30, tzinfo=KST)

    rows = collector.collect_once(observed_at)
    collector.collect_once(observed_at)
    restarted_collector = watch.WidgetResearchWatchCollector(
        config=_runtime_config([("111111", "테스트")]),
        client=client,
        output_dir=tmp_path / "observations",
        snapshot_dir=tmp_path / "snapshots",
    )
    restarted_collector.collect_once(observed_at)

    assert [call[1] for call in client.calls] == [
        "ka10001",
        "ka10004",
        "ka10080",
        "ka10001",
        "ka10004",
        "ka10080",
        "ka10001",
        "ka10004",
        "ka10080",
    ]
    row = rows[0]
    assert row["status"] == "PASS"
    assert row["latest_completed_bar"]["source_time"] == "20260813100000"
    assert row["advisory_generated"] is False
    assert row["entry_event"] is None
    assert row["exit_event"] is None
    assert row["runtime_effect"] is False
    assert row["allowed_runtime_apply"] is False
    assert row["actual_order_submitted"] is False
    assert row["broker_order_forbidden"] is True
    observation = tmp_path / "observations/widget_research_watch_111111_20260813.jsonl"
    assert len(observation.read_text(encoding="utf-8").splitlines()) == 1


def test_one_symbol_source_failure_does_not_block_other_watch_symbol(tmp_path):
    client = _FakeClient(fail_code="111111")
    collector = watch.WidgetResearchWatchCollector(
        config=_runtime_config([("111111", "실패"), ("222222", "정상")]),
        client=client,
        output_dir=tmp_path / "observations",
        snapshot_dir=tmp_path / "snapshots",
    )

    rows = collector.collect_once(datetime(2026, 8, 13, 10, 1, 30, tzinfo=KST))

    assert [row["status"] for row in rows] == ["SOURCE_ERROR", "PASS"]
    assert rows[0]["source_quality_issues"] == ["RuntimeError"]
    assert rows[0]["official_reference"] == watch.OFFICIAL_REFERENCE
    assert rows[0]["token_mode"] == "shared_cache_only_no_issue_no_refresh"


def test_service_is_low_rate_and_has_no_trading_process_dependency():
    service = Path(
        "deploy/systemd/korstockscan-widget-research-watch-collector.service"
    ).read_text(encoding="utf-8")
    timer = Path(
        "deploy/systemd/korstockscan-widget-research-watch-collector.timer"
    ).read_text(encoding="utf-8")

    assert "widget_research_watch_collector --check-config" in service
    assert "widget_research_watch_collector --interval-sec 60" in service
    assert "CPUQuota=10%" in service
    assert "MemoryMax=256M" in service
    assert "order" not in service.lower()
    assert "OnCalendar=Mon..Fri *-*-* 08:58:00 Asia/Seoul" in timer
