from contextlib import contextmanager
import json

import pytest

from src.engine import strategy_position_performance_report as report_mod


def test_main_synchronizes_target_date_without_building_provider_or_runtime_work(
    monkeypatch,
):
    calls = []
    monkeypatch.setattr(
        report_mod,
        "sync_trade_performance_for_date",
        lambda target_date: calls.append(target_date)
        or {"target_date": target_date, "fact_count": 8},
    )

    assert report_mod.main(["--date", "2026-08-25"]) == 0
    assert calls == ["2026-08-25"]


def test_build_trade_fact_rows_normalizes_strategy_and_exit_fields(monkeypatch):
    monkeypatch.setattr(
        report_mod,
        "build_trade_review_report",
        lambda target_date, since_time=None, top_n=100000, scope="entered": {
            "meta": {"warnings": []},
            "sections": {
                "recent_trades": [
                    {
                        "id": 101,
                        "rec_date": target_date,
                        "code": "111111",
                        "name": "테스트A",
                        "status": "COMPLETED",
                        "strategy": "scalp",
                        "position_tag": None,
                        "buy_price": 1000,
                        "buy_qty": 2,
                        "buy_time": "2026-04-06 09:00:00",
                        "sell_price": 1030,
                        "sell_time": "2026-04-06 09:03:00",
                        "profit_rate": 3.0,
                        "realized_pnl_krw": 60,
                        "holding_seconds": 180,
                        "exit_signal": {
                            "exit_rule": "scalp_trailing_take_profit",
                            "sell_reason_type": "TRAILING",
                        },
                        "ai_review_summary": {"headline": "AI 보유 유지 우세"},
                        "gatekeeper_replay": {
                            "action": "즉시 매수",
                            "allow_entry": True,
                        },
                    }
                ]
            },
        },
    )

    facts, warnings = report_mod._build_trade_fact_rows("2026-04-06")

    assert warnings == []
    assert len(facts) == 1
    fact = facts[0]
    assert fact["strategy"] == "SCALPING"
    assert fact["position_tag"] == "SCALP_BASE"
    assert fact["exit_rule"] == "scalp_trailing_take_profit"
    assert fact["sell_reason_type"] == "TRAILING"
    assert fact["ai_review_headline"] == "AI 보유 유지 우세"
    assert fact["gatekeeper_action"] == "즉시 매수"
    assert fact["gatekeeper_allow_entry"] is True


def test_strategy_position_report_falls_back_without_db(monkeypatch):
    monkeypatch.setattr(
        report_mod,
        "build_trade_review_report",
        lambda target_date, since_time=None, top_n=100000, scope="entered": {
            "meta": {"warnings": []},
            "sections": {
                "recent_trades": [
                    {
                        "id": 1,
                        "rec_date": target_date,
                        "code": "111111",
                        "name": "테스트A",
                        "status": "COMPLETED",
                        "strategy": "SCALPING",
                        "position_tag": "SCANNER",
                        "buy_price": 1000,
                        "buy_qty": 1,
                        "buy_time": "2026-04-06 09:00:00",
                        "sell_price": 1050,
                        "sell_time": "2026-04-06 09:02:00",
                        "profit_rate": 5.0,
                        "realized_pnl_krw": 50,
                        "holding_seconds": 120,
                        "exit_signal": {
                            "exit_rule": "take_profit",
                            "sell_reason_type": "PROFIT",
                        },
                    },
                    {
                        "id": 2,
                        "rec_date": target_date,
                        "code": "222222",
                        "name": "테스트B",
                        "status": "COMPLETED",
                        "strategy": "SCALPING",
                        "position_tag": "VCP_NEXT",
                        "buy_price": 2000,
                        "buy_qty": 1,
                        "buy_time": "2026-04-06 09:10:00",
                        "sell_price": 1900,
                        "sell_time": "2026-04-06 09:20:00",
                        "profit_rate": -5.0,
                        "realized_pnl_krw": -100,
                        "holding_seconds": 600,
                        "exit_signal": {
                            "exit_rule": "stop_loss",
                            "sell_reason_type": "LOSS",
                        },
                    },
                    {
                        "id": 4,
                        "rec_date": target_date,
                        "code": "444444",
                        "name": "테스트D",
                        "status": "COMPLETED",
                        "strategy": "SCALPING",
                        "position_tag": "SCANNER",
                        "buy_price": 10000,
                        "buy_qty": 1,
                        "buy_time": "2026-04-06 09:30:00",
                        "sell_price": 11000,
                        "sell_time": "2026-04-06 09:40:00",
                        "profit_rate": 1.0,
                        "realized_pnl_krw": 1000,
                        "holding_seconds": 600,
                        "exit_signal": {
                            "exit_rule": "take_profit",
                            "sell_reason_type": "PROFIT",
                        },
                    },
                    {
                        "id": 5,
                        "rec_date": target_date,
                        "code": "555555",
                        "name": "테스트E",
                        "status": "COMPLETED",
                        "strategy": "SCALPING",
                        "position_tag": "SCANNER",
                        "buy_price": 10000,
                        "buy_qty": 1,
                        "buy_time": "2026-04-06 09:45:00",
                        "sell_price": 9800,
                        "sell_time": "2026-04-06 09:55:00",
                        "profit_rate": -2.0,
                        "realized_pnl_krw": -200,
                        "holding_seconds": 600,
                        "exit_signal": {
                            "exit_rule": "stop_loss",
                            "sell_reason_type": "LOSS",
                        },
                    },
                    {
                        "id": 3,
                        "rec_date": target_date,
                        "code": "333333",
                        "name": "테스트C",
                        "status": "HOLDING",
                        "strategy": "KOSPI_ML",
                        "position_tag": "MIDDLE",
                        "buy_price": 3000,
                        "buy_qty": 1,
                        "buy_time": "2026-04-06 10:00:00",
                        "sell_price": 0,
                        "sell_time": "",
                        "profit_rate": 0.0,
                        "realized_pnl_krw": 0,
                        "holding_seconds": None,
                        "exit_signal": None,
                    },
                ]
            },
        },
    )

    @contextmanager
    def _broken_session():
        raise RuntimeError("db unavailable")
        yield None

    monkeypatch.setattr(report_mod._DB, "get_session", _broken_session)

    report = report_mod.build_strategy_position_performance_report("2026-04-06")

    assert report["summary"]["strategy_count"] == 2
    assert report["summary"]["tag_group_count"] == 3
    assert report["summary"]["entered_count"] == 5
    assert report["summary"]["completed_count"] == 4
    assert report["summary"]["open_count"] == 1
    assert report["summary"]["realized_pnl_krw"] == 696
    assert len(report["kpis"]) == 8
    kpi_map = {item["label"]: item for item in report["kpis"]}
    assert kpi_map["종료 승률"]["value"] == "50.0%"
    assert kpi_map["평균 기대손익"]["value"] == "174원"
    assert kpi_map["미종료 비중"]["value"] == "20.0%"
    assert kpi_map["최고 성과 버킷"]["value"] == "SCALPING/SCANNER"
    assert kpi_map["주의 버킷"]["value"] == "SCALPING/VCP_NEXT"
    assert kpi_map["최고 익절 거래"]["value"] == "테스트D(444444)"
    assert kpi_map["최대 손실 거래"]["value"] == "테스트E(555555)"
    assert kpi_map["최고 익절 거래"]["detail"] == "+9.75% / 975원"
    assert kpi_map["최대 손실 거래"]["detail"] == "-2.23% / -223원"

    row_map = {(row["strategy"], row["position_tag"]): row for row in report["rows"]}
    assert row_map[("SCALPING", "SCANNER")]["realized_pnl_krw"] == 800
    assert row_map[("SCALPING", "VCP_NEXT")]["realized_pnl_krw"] == -104
    assert row_map[("KOSPI_ML", "KOSPI_BASE")]["open_count"] == 1

    assert report["sections"]["top_winners"][0]["stock_code"] == "111111"
    assert report["sections"]["top_losers"][0]["stock_code"] == "222222"


def test_scanner_discovery_type_performance_section(monkeypatch):
    monkeypatch.setattr(
        report_mod,
        "build_trade_review_report",
        lambda target_date, since_time=None, top_n=100000, scope="entered": {
            "meta": {"warnings": []},
            "sections": {
                "recent_trades": [
                    {
                        "id": 11,
                        "rec_date": target_date,
                        "code": "111111",
                        "name": "가격급등",
                        "status": "COMPLETED",
                        "strategy": "SCALPING",
                        "position_tag": "SCANNER",
                        "buy_price": 1000,
                        "buy_qty": 1,
                        "buy_time": "2026-04-06 09:10:00",
                        "sell_price": 1020,
                        "sell_time": "2026-04-06 09:20:00",
                        "profit_rate": 2.0,
                        "realized_pnl_krw": 20,
                        "holding_seconds": 600,
                        "exit_signal": {
                            "exit_rule": "take_profit",
                            "sell_reason_type": "PROFIT",
                        },
                    },
                    {
                        "id": 12,
                        "rec_date": target_date,
                        "code": "222222",
                        "name": "저점반등",
                        "status": "COMPLETED",
                        "strategy": "SCALPING",
                        "position_tag": "SCANNER",
                        "buy_price": 1000,
                        "buy_qty": 1,
                        "buy_time": "2026-04-06 10:10:00",
                        "sell_price": 990,
                        "sell_time": "2026-04-06 10:20:00",
                        "profit_rate": -1.0,
                        "realized_pnl_krw": -10,
                        "holding_seconds": 600,
                        "exit_signal": {
                            "exit_rule": "stop_loss",
                            "sell_reason_type": "LOSS",
                        },
                    },
                ]
            },
        },
    )
    monkeypatch.setattr(
        report_mod,
        "_load_scanner_promotion_events",
        lambda target_date: {
            "111111": [
                {
                    "emitted_at": report_mod._parse_datetime("2026-04-06T09:00:00"),
                    "scanner_discovery_type": "price_jump_acceleration",
                    "scanner_promotion_reason": "price_jump_start_acceleration",
                    "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
                    "scanner_source_role": "early_discovery",
                    "scanner_priority_tier": "tier_a_acceleration_confirmed",
                }
            ],
            "222222": [
                {
                    "emitted_at": report_mod._parse_datetime("2026-04-06T10:00:00"),
                    "scanner_discovery_type": "low_rebound_rising_missed",
                    "scanner_promotion_reason": "low_rebound_rising_missed_candidate",
                    "source_signature": "LOW_REBOUND_RISING_MISSED",
                    "scanner_source_role": "rising_missed_low_rebound_candidate",
                    "scanner_priority_tier": "tier_c_volume_confirmation",
                    "rising_missed_lineage": "low_rebound_from_intraday_low",
                }
            ],
        },
    )

    facts, _warnings = report_mod._build_trade_fact_rows("2026-04-06")
    summary_rows = report_mod._aggregate_daily_rows(facts)
    report = report_mod._build_report_payload(
        "2026-04-06",
        [
            {
                **fact,
                "buy_time": (
                    fact["buy_time"].strftime("%Y-%m-%d %H:%M:%S")
                    if fact["buy_time"]
                    else ""
                ),
                "sell_time": (
                    fact["sell_time"].strftime("%Y-%m-%d %H:%M:%S")
                    if fact["sell_time"]
                    else ""
                ),
            }
            for fact in facts
        ],
        [{**row, "rec_date": row["rec_date"].isoformat()} for row in summary_rows],
    )

    scanner_rows = {
        row["scanner_discovery_type"]: row
        for row in report["sections"]["scanner_discovery_rows"]
    }
    assert report["summary"]["scanner_discovery_type_count"] == 2
    assert report["summary"]["scanner_provenance_matched_count"] == 2
    assert scanner_rows["price_jump_acceleration"]["realized_pnl_krw"] == 18
    assert (
        scanner_rows["price_jump_acceleration"]["top_promotion_reason"]
        == "price_jump_start_acceleration"
    )
    assert scanner_rows["low_rebound_rising_missed"]["realized_pnl_krw"] == -12
    assert scanner_rows["low_rebound_rising_missed"]["provenance_missing_count"] == 0


def test_completed_row_with_missing_execution_economics_stays_null(monkeypatch):
    monkeypatch.setattr(
        report_mod,
        "build_trade_review_report",
        lambda **_kwargs: {
            "meta": {"warnings": []},
            "sections": {
                "recent_trades": [
                    {
                        "id": 1,
                        "rec_date": "2026-04-06",
                        "code": "111111",
                        "status": "COMPLETED",
                        "strategy": "SCALPING",
                        "position_tag": "SCANNER",
                        "buy_price": 1000,
                        "buy_qty": 1,
                        "buy_time": "2026-04-06 09:00:00",
                        "sell_price": None,
                        "sell_time": None,
                    }
                ]
            },
        },
    )

    facts, warnings = report_mod._build_trade_fact_rows("2026-04-06")
    rows = report_mod._aggregate_daily_rows(facts)

    assert warnings == []
    assert facts[0]["profit_rate"] is None
    assert facts[0]["realized_pnl_krw"] is None
    assert rows[0]["economics_valid_completed_count"] == 0
    assert rows[0]["economics_missing_completed_count"] == 1
    assert rows[0]["realized_pnl_krw"] is None


def test_scanner_provenance_never_uses_future_promotion_event():
    fact = {
        "strategy": "SCALPING",
        "position_tag": "SCANNER",
        "stock_code": "111111",
        "buy_time": report_mod._parse_datetime("2026-04-06 09:00:00"),
    }
    future_event = {
        "emitted_at": report_mod._parse_datetime("2026-04-06 09:01:00"),
        "scanner_discovery_type": "price_jump_acceleration",
    }

    assert (
        report_mod._select_scanner_event_for_trade(fact, {"111111": [future_event]})
        is None
    )


def test_source_warning_preserves_prior_generation_and_writes_blocked_receipt(
    monkeypatch, tmp_path
):
    executed = []

    class _Query:
        def filter(self, *_args):
            return self

        def count(self):
            return 7

    class _Session:
        def query(self, *_args):
            return _Query()

        def execute(self, statement):
            executed.append(statement)

    @contextmanager
    def _session():
        yield _Session()

    monkeypatch.setattr(
        report_mod,
        "_build_trade_fact_rows",
        lambda _target_date: ([], ["DB connection failed"]),
    )
    monkeypatch.setattr(report_mod._DB, "init_db", lambda: None)
    monkeypatch.setattr(report_mod._DB, "get_session", _session)
    monkeypatch.setattr(report_mod, "_FACT_SYNC_STATUS_DIR", tmp_path)

    with pytest.raises(report_mod.FactSyncSourceError):
        report_mod.sync_trade_performance_for_date("2026-04-06")

    assert executed == []
    receipt = json.loads(
        (tmp_path / "strategy_position_fact_sync_2026-04-06.status.json").read_text(
            encoding="utf-8"
        )
    )
    assert receipt["status"] == "source_blocked"
    assert receipt["prior_fact_count"] == 7
    assert receipt["consumer_ready"] is False


def test_fact_sync_receipt_has_a_verifiable_generation_hash(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "_FACT_SYNC_STATUS_DIR", tmp_path)

    receipt = report_mod._write_status(
        "2026-04-06",
        {
            "status": "succeeded",
            "consumer_ready": True,
            "source_fact_count": 1,
            "fact_count": 1,
        },
    )
    persisted = json.loads(
        (tmp_path / "strategy_position_fact_sync_2026-04-06.status.json").read_text(
            encoding="utf-8"
        )
    )
    actual_hash = persisted.pop("artifact_sha256")

    assert actual_hash == receipt["artifact_sha256"]
    assert actual_hash == report_mod._canonical_sha256(persisted)
