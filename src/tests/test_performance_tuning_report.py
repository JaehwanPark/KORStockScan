from src.engine import sniper_performance_tuning_report as report_mod


def test_performance_tuning_report_builds_metrics(monkeypatch):
    entry_lines = [
        "[2026-04-03 10:00:00] [ENTRY_PIPELINE] 테스트A(000001) stage=market_regime_pass gatekeeper_eval_ms=420 gatekeeper_cache=miss gatekeeper=즉시|매수",
        "[2026-04-03 10:00:05] [ENTRY_PIPELINE] 테스트B(000002) stage=blocked_gatekeeper_reject action=눌림|대기 gatekeeper_eval_ms=0 gatekeeper_cache=fast_reuse cooldown_sec=1200",
        "[2026-04-03 10:00:05] [ENTRY_PIPELINE] 테스트B(000002) stage=gatekeeper_fast_reuse action=눌림|대기 age_sec=4.2 ws_age_sec=0.30",
        "[2026-04-03 10:00:06] [ENTRY_PIPELINE] 테스트C(000003) stage=gatekeeper_fast_reuse_bypass strategy=SCALPING score=68 age_sec=12.4 ws_age_sec=0.22 reason_codes=sig_changed,score_boundary",
        "[2026-04-03 10:00:07] [ENTRY_PIPELINE] 테스트A(000001) stage=dual_persona_shadow strategy=KOSPI_ML decision_type=gatekeeper dual_mode=shadow gemini_action=ALLOW_ENTRY gemini_score=85 aggr_action=ALLOW_ENTRY aggr_score=90 cons_action=WAIT cons_score=58 cons_veto=true fused_action=WAIT fused_score=69 winner=conservative_veto agreement_bucket=gemini_vs_cons_conflict hard_flags=VWAP_BELOW,LARGE_SELL_PRINT shadow_extra_ms=1320",
    ]
    holding_lines = [
        "[2026-04-03 10:01:00] [HOLDING_PIPELINE] 테스트A(000001) stage=ai_holding_review review_ms=510 ai_cache=miss profit_rate=+0.50",
        "[2026-04-03 10:01:08] [HOLDING_PIPELINE] 테스트A(000001) stage=ai_holding_skip_unchanged ws_age_sec=0.40 reuse_sec=5.0 age_sec=3.1",
        "[2026-04-03 10:01:09] [HOLDING_PIPELINE] 테스트A(000001) stage=ai_holding_reuse_bypass ws_age_sec=0.90 reuse_sec=5.0 age_sec=3.8 reason_codes=price_move,near_low_score",
        "[2026-04-03 10:02:00] [HOLDING_PIPELINE] 테스트A(000001) stage=exit_signal exit_rule=scalp_ai_early_exit profit_rate=-0.90",
        "[2026-04-03 15:15:00] [HOLDING_PIPELINE] 테스트A(000001) stage=dual_persona_shadow strategy=SCALPING decision_type=overnight dual_mode=shadow gemini_action=SELL_TODAY gemini_score=25 aggr_action=HOLD_OVERNIGHT aggr_score=72 cons_action=SELL_TODAY cons_score=38 cons_veto=false fused_action=SELL_TODAY fused_score=42 winner=gemini_hold agreement_bucket=aggr_vs_pair_conflict hard_flags=- shadow_extra_ms=980",
    ]

    def _fake_iter(log_path, *, target_date, marker):
        return entry_lines if marker == "[ENTRY_PIPELINE]" else holding_lines

    monkeypatch.setattr(report_mod, "_iter_target_lines", _fake_iter)
    monkeypatch.setattr(
        report_mod,
        "build_trade_review_report",
        lambda target_date, since_time=None, top_n=10000, scope="all": {
            "meta": {"warnings": []},
            "sections": {
                "recent_trades": [
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
                        "id": 9,
                        "rec_date": target_date,
                        "code": "000009",
                        "name": "복원거래",
                        "status": "COMPLETED",
                        "strategy": "SCALPING",
                        "position_tag": "SCANNER",
                        "buy_price": 57000.0,
                        "buy_qty": 10,
                        "buy_time": "2026-04-03 09:08:57",
                        "sell_price": 56100,
                        "sell_time": "2026-04-03 09:14:45",
                        "profit_rate": -1.58,
                        "realized_pnl_krw": -9000,
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
                ],
            },
        },
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
    assert report["breakdowns"]["holding_reuse_blockers"][0]["label"] == "가격 변화 확대"
    assert report["breakdowns"]["gatekeeper_reuse_blockers"][0]["label"] == "시그니처 변경"
    assert any(item["label"] == "Gatekeeper fast reuse 비율" for item in report["watch_items"])
    assert any(item["label"] == "듀얼 페르소나 충돌률" for item in report["watch_items"])
    assert len(report["strategy_rows"]) >= 2
    assert any(item["label"] == "스캘핑" for item in report["strategy_rows"])
    assert any(item["label"] == "스윙" for item in report["strategy_rows"])
    assert report["meta"]["outcome_basis"] == "기준일 누적 성과 (trade review 정규화)"
    assert report["meta"]["trend_basis"] == "최근 2개 거래일 rolling 성과"
    assert report["strategy_rows"][0]["trends"]["summary_5d"]["date_count"] >= 1
    assert report["strategy_rows"][0]["outcomes"]["completed_rows"] == 2
    assert report["strategy_rows"][0]["outcomes"]["realized_pnl_krw"] == -8000
    assert report["metrics"]["dual_persona_shadow_samples"] == 2
    assert report["metrics"]["dual_persona_gatekeeper_samples"] == 1
    assert report["metrics"]["dual_persona_overnight_samples"] == 1
    assert report["metrics"]["dual_persona_conflict_ratio"] == 100.0
    assert report["metrics"]["dual_persona_conservative_veto_ratio"] == 50.0
    assert report["metrics"]["dual_persona_fused_override_ratio"] == 50.0
    assert report["breakdowns"]["dual_persona_decision_types"][0]["label"] in {"gatekeeper", "overnight"}
    assert report["auto_comments"]


def test_gatekeeper_age_sentinel_handling(monkeypatch):
    """age sentinel ("-") 처리 검증 - p95 오염 방지"""
    entry_lines = [
        # 이벤트 1: age 없음 (초기 상태)
        "[2026-04-03 10:00:00] [ENTRY_PIPELINE] 테스트A(000001) stage=gatekeeper_fast_reuse_bypass strategy=KOSDAQ_ML score=82.5 age_sec=0.5 ws_age_sec=0.1 action_age_sec=- allow_entry_age_sec=- sig_delta=curr_price:12150->12200 reason_codes=missing_action",
        # 이벤트 2: age 정상값
        "[2026-04-03 10:00:05] [ENTRY_PIPELINE] 테스트B(000002) stage=gatekeeper_fast_reuse_bypass strategy=KOSDAQ_ML score=82.5 age_sec=0.5 ws_age_sec=0.1 action_age_sec=5.0 allow_entry_age_sec=5.0 sig_delta=spread_tick:1->2 reason_codes=sig_changed",
    ]
    holding_lines = []

    def _fake_iter(log_path, *, target_date, marker):
        return entry_lines if marker == "[ENTRY_PIPELINE]" else holding_lines

    monkeypatch.setattr(report_mod, "_iter_target_lines", _fake_iter)
    monkeypatch.setattr(
        report_mod,
        "build_trade_review_report",
        lambda target_date, since_time=None, top_n=10000, scope="all": {
            "meta": {"warnings": []},
            "sections": {"recent_trades": [], "open_trades": []},
            "history": [],
        },
    )

    report = report_mod.build_performance_tuning_report(target_date="2026-04-03", since_time=None)

    # p95는 sentinel을 제외한 정상값만 포함해야 함 (5.0만)
    assert report["metrics"]["gatekeeper_action_age_p95"] == 5.0
    assert report["metrics"]["gatekeeper_allow_entry_age_p95"] == 5.0
    # sentinel을 포함한 총 bypass evaluation 샘플 수는 2건
    assert report["metrics"]["gatekeeper_bypass_evaluation_samples"] == 2


def test_gatekeeper_sig_delta_parsing(monkeypatch):
    """sig_delta 파싱 및 필드 추출 검증"""
    entry_lines = [
        "[2026-04-03 10:00:00] [ENTRY_PIPELINE] 테스트A(000001) stage=gatekeeper_fast_reuse_bypass strategy=KOSDAQ_ML score=82.5 age_sec=0.5 ws_age_sec=0.1 action_age_sec=10.0 allow_entry_age_sec=10.0 sig_delta=curr_price:12150->12200,spread_tick:1->2,v_pw_now:5.0->5.2 reason_codes=sig_changed",
        "[2026-04-03 10:00:05] [ENTRY_PIPELINE] 테스트B(000002) stage=gatekeeper_fast_reuse_bypass strategy=KOSDAQ_ML score=82.5 age_sec=0.5 ws_age_sec=0.1 action_age_sec=11.0 allow_entry_age_sec=11.0 sig_delta=curr_price:12200->12250 reason_codes=sig_changed",
    ]
    holding_lines = []

    def _fake_iter(log_path, *, target_date, marker):
        return entry_lines if marker == "[ENTRY_PIPELINE]" else holding_lines

    monkeypatch.setattr(report_mod, "_iter_target_lines", _fake_iter)
    monkeypatch.setattr(
        report_mod,
        "build_trade_review_report",
        lambda target_date, since_time=None, top_n=10000, scope="all": {
            "meta": {"warnings": []},
            "sections": {"recent_trades": [], "open_trades": []},
            "history": [],
        },
    )

    report = report_mod.build_performance_tuning_report(target_date="2026-04-03", since_time=None)

    # sig_deltas 분포 검증: curr_price 2회, spread_tick 1회, v_pw_now 1회
    sig_deltas = report["breakdowns"]["gatekeeper_sig_deltas"]
    sig_deltas_dict = {item["label"]: item["count"] for item in sig_deltas}
    assert sig_deltas_dict["curr_price"] == 2
    assert sig_deltas_dict["spread_tick"] == 1
    assert sig_deltas_dict["v_pw_now"] == 1
    # age 검증
    assert report["metrics"]["gatekeeper_action_age_p95"] == 11.0
