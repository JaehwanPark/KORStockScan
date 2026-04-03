from src.engine import sniper_performance_tuning_report as report_mod


def test_performance_tuning_report_builds_metrics(monkeypatch):
    entry_lines = [
        "[2026-04-03 10:00:00] [ENTRY_PIPELINE] 테스트A(000001) stage=market_regime_pass gatekeeper_eval_ms=420 gatekeeper_cache=miss gatekeeper=즉시|매수",
        "[2026-04-03 10:00:05] [ENTRY_PIPELINE] 테스트B(000002) stage=blocked_gatekeeper_reject action=눌림|대기 gatekeeper_eval_ms=0 gatekeeper_cache=fast_reuse cooldown_sec=1200",
        "[2026-04-03 10:00:05] [ENTRY_PIPELINE] 테스트B(000002) stage=gatekeeper_fast_reuse action=눌림|대기 age_sec=4.2 ws_age_sec=0.30",
    ]
    holding_lines = [
        "[2026-04-03 10:01:00] [HOLDING_PIPELINE] 테스트A(000001) stage=ai_holding_review review_ms=510 ai_cache=miss profit_rate=+0.50",
        "[2026-04-03 10:01:08] [HOLDING_PIPELINE] 테스트A(000001) stage=ai_holding_skip_unchanged ws_age_sec=0.40 reuse_sec=5.0 age_sec=3.1",
        "[2026-04-03 10:02:00] [HOLDING_PIPELINE] 테스트A(000001) stage=exit_signal exit_rule=scalp_ai_early_exit profit_rate=-0.90",
    ]

    def _fake_iter(log_path, *, target_date, marker):
        return entry_lines if marker == "[ENTRY_PIPELINE]" else holding_lines

    monkeypatch.setattr(report_mod, "_iter_target_lines", _fake_iter)
    monkeypatch.setattr(
        report_mod,
        "_fetch_trade_rows",
        lambda target_date: ([
            {
                "id": 1,
                "rec_date": target_date,
                "code": "000001",
                "name": "테스트A",
                "status": "COMPLETED",
                "strategy": "SCALPING",
                "position_tag": "SCANNER",
                "buy_price": 10000.0,
                "buy_qty": 10,
                "buy_time": "2026-04-03 10:00:00",
                "sell_price": 10100,
                "sell_time": "2026-04-03 10:03:00",
                "profit_rate": 1.0,
                "realized_pnl_krw": 1000,
            },
            {
                "id": 2,
                "rec_date": target_date,
                "code": "000002",
                "name": "테스트B",
                "status": "WATCHING",
                "strategy": "KOSPI_ML",
                "position_tag": "SCANNER",
                "buy_price": 0.0,
                "buy_qty": 0,
                "buy_time": "",
                "sell_price": 0,
                "sell_time": "",
                "profit_rate": 0.0,
                "realized_pnl_krw": 0,
            },
        ], []),
    )
    monkeypatch.setattr(
        report_mod,
        "_fetch_trade_history_rows",
        lambda target_date: ([
            {
                "rec_date": "2026-04-03",
                "code": "000001",
                "name": "테스트A",
                "status": "COMPLETED",
                "strategy": "SCALPING",
                "buy_price": 10000.0,
                "buy_qty": 10,
                "buy_time": "2026-04-03 10:00:00",
                "sell_price": 10100,
                "sell_time": "2026-04-03 10:03:00",
                "profit_rate": 1.0,
                "realized_pnl_krw": 1000,
            },
            {
                "rec_date": "2026-04-02",
                "code": "000001",
                "name": "테스트A",
                "status": "COMPLETED",
                "strategy": "SCALPING",
                "buy_price": 10000.0,
                "buy_qty": 10,
                "buy_time": "2026-04-02 10:00:00",
                "sell_price": 9900,
                "sell_time": "2026-04-02 10:03:00",
                "profit_rate": -1.0,
                "realized_pnl_krw": -1000,
            },
            {
                "rec_date": "2026-04-03",
                "code": "000002",
                "name": "테스트B",
                "status": "WATCHING",
                "strategy": "KOSPI_ML",
                "buy_price": 0.0,
                "buy_qty": 0,
                "buy_time": "",
                "sell_price": 0,
                "sell_time": "",
                "profit_rate": 0.0,
                "realized_pnl_krw": 0,
            },
        ], [], ["2026-04-03", "2026-04-02"]),
    )

    report = report_mod.build_performance_tuning_report(target_date="2026-04-03", since_time=None)

    assert report["metrics"]["holding_reviews"] == 1
    assert report["metrics"]["holding_skips"] == 1
    assert report["metrics"]["gatekeeper_decisions"] == 2
    assert report["metrics"]["gatekeeper_fast_reuse_ratio"] == 50.0
    assert report["breakdowns"]["exit_rules"][0]["label"] == "scalp_ai_early_exit"
    assert any(item["label"] == "Gatekeeper fast reuse 비율" for item in report["watch_items"])
    assert len(report["strategy_rows"]) >= 2
    assert any(item["label"] == "스캘핑" for item in report["strategy_rows"])
    assert any(item["label"] == "스윙" for item in report["strategy_rows"])
    assert report["meta"]["outcome_basis"] == "기준일 누적 성과"
    assert report["meta"]["trend_basis"] == "최근 2개 거래일 rolling 성과"
    assert report["strategy_rows"][0]["trends"]["summary_5d"]["date_count"] >= 1
    assert report["auto_comments"]
