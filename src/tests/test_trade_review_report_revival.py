from src.engine import sniper_trade_review_report as report_mod


def test_trade_review_restores_completed_trade_from_holding_events(monkeypatch):
    holding_lines = [
        "[2026-04-06 09:08:57] [HOLDING_PIPELINE] 심텍(222800) stage=holding_started id=1085 fill_price=57000 fill_qty=10 buy_price=57000.00 buy_qty=10 strategy=SCALPING position_tag=SCANNER",
        "[2026-04-06 09:14:45] [HOLDING_PIPELINE] 심텍(222800) stage=exit_signal id=1085 profit_rate=-1.58 buy_price=57000.0 buy_qty=10 curr_price=56100 exit_rule=scalp_soft_stop_pct",
        "[2026-04-06 09:14:46] [HOLDING_PIPELINE] 심텍(222800) stage=sell_completed id=1085 sell_price=56100 profit_rate=-1.58 revive=True new_watch_id=1103",
    ]

    def _fake_iter(log_paths, *, target_date):
        return holding_lines

    def _fake_fetch(target_date, code=None):
        return ([
            {
                "id": 1085,
                "rec_date": target_date,
                "code": "222800",
                "name": "심텍",
                "status": "WATCHING",
                "strategy": "SCALPING",
                "position_tag": "SCANNER",
                "buy_price": 0.0,
                "buy_qty": 10,
                "buy_time": "2026-04-06 09:08:57",
                "sell_price": 56100,
                "sell_time": "2026-04-06 09:14:45",
                "profit_rate": -1.58,
                "realized_pnl_krw": 0,
            },
            {
                "id": 1103,
                "rec_date": target_date,
                "code": "222800",
                "name": "심텍",
                "status": "WATCHING",
                "strategy": "SCALPING",
                "position_tag": "SCANNER",
                "buy_price": 0.0,
                "buy_qty": 0,
                "buy_time": "",
                "sell_price": 0,
                "sell_time": "",
                "profit_rate": 0.0,
                "realized_pnl_krw": 0,
            },
        ], [])

    monkeypatch.setattr(report_mod, "_iter_target_lines", _fake_iter)
    monkeypatch.setattr(report_mod, "_fetch_trade_rows", _fake_fetch)
    monkeypatch.setattr(report_mod, "find_gatekeeper_snapshot_for_trade", lambda *args, **kwargs: None)

    report = report_mod.build_trade_review_report(target_date="2026-04-06")

    assert report["metrics"]["completed_trades"] == 1
    assert report["metrics"]["open_trades"] == 0
    assert report["metrics"]["realized_pnl_krw"] == -9000

    trade = report["sections"]["completed_trades"][0]
    assert trade["id"] == 1085
    assert trade["status"] == "COMPLETED"
    assert trade["buy_price"] == 57000.0
    assert trade["sell_price"] == 56100
    assert trade["realized_pnl_krw"] == -9000
    assert trade["result_icon"] == "▼"
    assert trade["result_label"] == "손절"
    assert trade["result_tone"] == "bad"


def test_trade_review_compacts_long_timeline(monkeypatch):
    holding_lines = [
        "[2026-04-06 09:00:01] [HOLDING_PIPELINE] 테스트(123456) stage=holding_started id=1 fill_price=10000 fill_qty=1 buy_price=10000 buy_qty=1 strategy=SCALPING position_tag=SCANNER",
        "[2026-04-06 09:00:10] [HOLDING_PIPELINE] 테스트(123456) stage=preset_exit_setup id=1 preset_tp_price=10150",
        "[2026-04-06 09:00:20] [HOLDING_PIPELINE] 테스트(123456) stage=ai_holding_review id=1 ai_score=61 profit_rate=+0.10",
        "[2026-04-06 09:00:30] [HOLDING_PIPELINE] 테스트(123456) stage=scale_in_executed id=1 add_count=1 new_buy_qty=2",
        "[2026-04-06 09:00:40] [HOLDING_PIPELINE] 테스트(123456) stage=ai_holding_review id=1 ai_score=58 profit_rate=-0.20",
        "[2026-04-06 09:00:50] [HOLDING_PIPELINE] 테스트(123456) stage=ai_holding_reuse_bypass id=1 reason_codes=age_expired",
        "[2026-04-06 09:01:00] [HOLDING_PIPELINE] 테스트(123456) stage=exit_signal id=1 profit_rate=-0.80 exit_rule=scalp_ai_early_exit",
        "[2026-04-06 09:01:01] [HOLDING_PIPELINE] 테스트(123456) stage=sell_order_sent id=1 qty=2 ord_no=0001",
        "[2026-04-06 09:01:02] [HOLDING_PIPELINE] 테스트(123456) stage=sell_completed id=1 sell_price=9920 profit_rate=-0.80",
    ]

    def _fake_iter(log_paths, *, target_date):
        return holding_lines

    def _fake_fetch(target_date, code=None):
        return ([
            {
                "id": 1,
                "rec_date": target_date,
                "code": "123456",
                "name": "테스트",
                "status": "COMPLETED",
                "strategy": "SCALPING",
                "position_tag": "SCANNER",
                "buy_price": 10000.0,
                "buy_qty": 2,
                "buy_time": "2026-04-06 09:00:01",
                "sell_price": 9920,
                "sell_time": "2026-04-06 09:01:02",
                "profit_rate": -0.8,
                "realized_pnl_krw": -160,
            },
        ], [])

    monkeypatch.setattr(report_mod, "_iter_target_lines", _fake_iter)
    monkeypatch.setattr(report_mod, "_fetch_trade_rows", _fake_fetch)
    monkeypatch.setattr(report_mod, "find_gatekeeper_snapshot_for_trade", lambda *args, **kwargs: None)

    report = report_mod.build_trade_review_report(target_date="2026-04-06")
    trade = report["sections"]["recent_trades"][0]

    assert len(trade["timeline"]) == 9
    assert len(trade["compact_timeline"]) == 8
    omitted = trade["compact_timeline"][4]
    assert omitted["stage"] == "omitted"
    assert omitted["label"] == "중간 2단계 생략"
    assert trade["timeline_hidden_count"] == 2


def test_trade_review_builds_ai_review_summary(monkeypatch):
    holding_lines = [
        "[2026-04-06 09:00:01] [HOLDING_PIPELINE] 테스트(123456) stage=holding_started id=1 fill_price=10000 fill_qty=1 buy_price=10000 buy_qty=1 strategy=SCALPING position_tag=SCANNER",
        "[2026-04-06 09:00:20] [HOLDING_PIPELINE] 테스트(123456) stage=ai_holding_review id=1 ai_score=60 profit_rate=+0.07 low_score_hits=0/3",
        "[2026-04-06 09:00:30] [HOLDING_PIPELINE] 테스트(123456) stage=ai_holding_review id=1 ai_score=45 profit_rate=-0.14 low_score_hits=1/3",
        "[2026-04-06 09:00:40] [HOLDING_PIPELINE] 테스트(123456) stage=ai_holding_review id=1 ai_score=28 profit_rate=-1.06 low_score_hits=3/3",
        "[2026-04-06 09:00:41] [HOLDING_PIPELINE] 테스트(123456) stage=exit_signal id=1 profit_rate=-1.06 exit_rule=scalp_ai_early_exit",
        "[2026-04-06 09:00:42] [HOLDING_PIPELINE] 테스트(123456) stage=sell_completed id=1 sell_price=9890 profit_rate=-1.06",
    ]

    def _fake_iter(log_paths, *, target_date):
        return holding_lines

    def _fake_fetch(target_date, code=None):
        return ([
            {
                "id": 1,
                "rec_date": target_date,
                "code": "123456",
                "name": "테스트",
                "status": "COMPLETED",
                "strategy": "SCALPING",
                "position_tag": "SCANNER",
                "buy_price": 10000.0,
                "buy_qty": 1,
                "buy_time": "2026-04-06 09:00:01",
                "sell_price": 9890,
                "sell_time": "2026-04-06 09:00:42",
                "profit_rate": -1.06,
                "realized_pnl_krw": -110,
            },
        ], [])

    monkeypatch.setattr(report_mod, "_iter_target_lines", _fake_iter)
    monkeypatch.setattr(report_mod, "_fetch_trade_rows", _fake_fetch)
    monkeypatch.setattr(report_mod, "find_gatekeeper_snapshot_for_trade", lambda *args, **kwargs: None)

    report = report_mod.build_trade_review_report(target_date="2026-04-06")
    summary = report["sections"]["recent_trades"][0]["ai_review_summary"]

    assert summary["headline"] == "AI 하방 경고 누적"
    assert "최근 3회 기준 AI 60→28점" in summary["summary"]
    assert any(item["value"] == "3/3" for item in summary["chips"])
