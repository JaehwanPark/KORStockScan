from contextlib import contextmanager

from src.engine import strategy_position_performance_report as report_mod


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
                        "gatekeeper_replay": {"action": "즉시 매수", "allow_entry": True},
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
                        "exit_signal": {"exit_rule": "take_profit", "sell_reason_type": "PROFIT"},
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
                        "exit_signal": {"exit_rule": "stop_loss", "sell_reason_type": "LOSS"},
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
                        "exit_signal": {"exit_rule": "take_profit", "sell_reason_type": "PROFIT"},
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
                        "exit_signal": {"exit_rule": "stop_loss", "sell_reason_type": "LOSS"},
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
    assert report["summary"]["realized_pnl_krw"] == 750
    assert len(report["kpis"]) == 8
    kpi_map = {item["label"]: item for item in report["kpis"]}
    assert kpi_map["종료 승률"]["value"] == "50.0%"
    assert kpi_map["평균 기대손익"]["value"] == "188원"
    assert kpi_map["미종료 비중"]["value"] == "20.0%"
    assert kpi_map["최고 성과 버킷"]["value"] == "SCALPING/SCANNER"
    assert kpi_map["주의 버킷"]["value"] == "SCALPING/VCP_NEXT"
    assert kpi_map["최고 익절 거래"]["value"] == "테스트D(444444)"
    assert kpi_map["최대 손실 거래"]["value"] == "테스트E(555555)"
    assert kpi_map["최고 익절 거래"]["detail"] == "+1.00% / 1,000원"
    assert kpi_map["최대 손실 거래"]["detail"] == "-2.00% / -200원"

    row_map = {(row["strategy"], row["position_tag"]): row for row in report["rows"]}
    assert row_map[("SCALPING", "SCANNER")]["realized_pnl_krw"] == 850
    assert row_map[("SCALPING", "VCP_NEXT")]["realized_pnl_krw"] == -100
    assert row_map[("KOSPI_ML", "KOSPI_BASE")]["open_count"] == 1

    assert report["sections"]["top_winners"][0]["stock_code"] == "111111"
    assert report["sections"]["top_losers"][0]["stock_code"] == "222222"
