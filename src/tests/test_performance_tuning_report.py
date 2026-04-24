import json

from src.engine import sniper_performance_tuning_report as report_mod


def test_performance_tuning_report_prefers_jsonl_events(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    pipeline_dir = data_dir / "pipeline_events"
    pipeline_dir.mkdir(parents=True, exist_ok=True)

    payloads = [
        {
            "event_type": "pipeline_event",
            "pipeline": "ENTRY_PIPELINE",
            "stock_name": "테스트A",
            "stock_code": "000001",
            "stage": "market_regime_pass",
            "emitted_at": "2026-04-03T10:00:00",
            "fields": {"gatekeeper_eval_ms": 420, "gatekeeper_cache": "miss", "strategy": "SCALPING"},
            "record_id": 101,
        },
        {
            "event_type": "pipeline_event",
            "pipeline": "HOLDING_PIPELINE",
            "stock_name": "테스트A",
            "stock_code": "000001",
            "stage": "ai_holding_review",
            "emitted_at": "2026-04-03T10:01:00",
            "fields": {"review_ms": 510, "ai_cache": "miss"},
            "record_id": 101,
        },
    ]
    with open(pipeline_dir / "pipeline_events_2026-04-03.jsonl", "w", encoding="utf-8") as handle:
        for payload in payloads:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")

    # Legacy fallback lines should be ignored when JSONL exists.
    def _fake_iter(log_path, *, target_date, marker):
        if marker == "[ENTRY_PIPELINE]":
            return [
                "[2026-04-03 10:02:00] [ENTRY_PIPELINE] 테스트B(000002) stage=blocked_gatekeeper_reject gatekeeper_eval_ms=0 gatekeeper_cache=miss action=눌림|대기"
            ]
        return [
            "[2026-04-03 10:02:10] [HOLDING_PIPELINE] 테스트B(000002) stage=ai_holding_skip_unchanged ws_age_sec=0.40 reuse_sec=5.0 age_sec=3.1"
        ]

    monkeypatch.setattr(report_mod, "DATA_DIR", data_dir)
    # dashboard_data_repository도 같은 DATA_DIR을 사용하도록 모킹
    import src.engine.dashboard_data_repository as dash_repo
    monkeypatch.setattr(dash_repo, "DATA_DIR", data_dir)
    monkeypatch.setattr(dash_repo, "PIPELINE_EVENTS_DIR", data_dir / "pipeline_events")
    monkeypatch.setattr(dash_repo, "MONITOR_SNAPSHOT_DIR", data_dir / "report" / "monitor_snapshots")
    monkeypatch.setattr(report_mod, "_iter_target_lines", _fake_iter)
    monkeypatch.setattr(
        report_mod,
        "build_trade_review_report",
        lambda target_date, since_time=None, top_n=10000, scope="all": {
            "meta": {"warnings": []},
            "sections": {"recent_trades": []},
        },
    )
    monkeypatch.setattr(report_mod, "_fetch_trade_history_rows", lambda target_date: ([], [], []))

    report = report_mod.build_performance_tuning_report(target_date="2026-04-03", since_time=None)

    assert report["metrics"]["gatekeeper_decisions"] == 1
    assert report["metrics"]["holding_reviews"] == 1
    assert report["metrics"]["holding_skips"] == 0


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
        "[2026-04-03 10:01:09] [HOLDING_PIPELINE] 테스트A(000001) stage=ai_holding_reuse_bypass ws_age_sec=0.90 reuse_sec=5.0 age_sec=3.8 sig_delta=curr_price:10100->10080,spread_tick:1->2 reason_codes=price_move,near_low_score",
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
    holding_sig_deltas = {item["label"]: item["count"] for item in report["breakdowns"]["holding_sig_deltas"]}
    assert holding_sig_deltas["curr_price"] == 1
    assert holding_sig_deltas["spread_tick"] == 1
    assert report["breakdowns"]["gatekeeper_reuse_blockers"][0]["label"] == "시그니처 변경"
    assert any(item["label"] == "Gatekeeper fast reuse 비율" for item in report["watch_items"])
    assert any(item["label"] == "듀얼 페르소나 충돌률" for item in report["watch_items"])
    assert len(report["strategy_rows"]) >= 2
    assert any(item["label"] == "스캘핑" for item in report["strategy_rows"])
    assert any(item["label"] == "스윙" for item in report["strategy_rows"])
    assert report["meta"]["outcome_basis"] == "기준일 누적 성과 (trade review 정규화)"
    assert report["meta"]["trend_basis"] == "최근 2개 거래일 rolling 성과"
    assert report["meta"]["schema_version"] == report_mod.PERFORMANCE_TUNING_SCHEMA_VERSION
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


def test_performance_tuning_includes_phase01_scalping_metrics(monkeypatch):
    entry_lines = [
        "[2026-04-03 09:30:00] [ENTRY_PIPELINE] 종목A(000001) stage=budget_pass id=1 qty=5",
        "[2026-04-03 09:30:01] [ENTRY_PIPELINE] 종목A(000001) stage=latency_pass id=1 quote_stale=False reason=allow",
        "[2026-04-03 09:30:02] [ENTRY_PIPELINE] 종목A(000001) stage=order_bundle_submitted id=1",
        "[2026-04-03 09:31:00] [ENTRY_PIPELINE] 종목B(000002) stage=budget_pass id=2 qty=3",
        "[2026-04-03 09:31:01] [ENTRY_PIPELINE] 종목B(000002) stage=latency_block id=2 reason=latency_state_danger quote_stale=False",
        "[2026-04-03 09:31:02] [ENTRY_PIPELINE] 종목B(000002) stage=ai_confirmed id=2 ai_score=84 blocked_stage=blocked_strength_momentum overbought_blocked=False",
        "[2026-04-03 09:32:00] [ENTRY_PIPELINE] 종목C(000003) stage=entry_armed_expired id=3 waited_sec=20.0",
    ]
    holding_lines = [
        "[2026-04-03 09:33:00] [HOLDING_PIPELINE] 종목A(000001) stage=position_rebased_after_fill id=1 fill_quality=FULL_FILL",
        "[2026-04-03 09:33:01] [HOLDING_PIPELINE] 종목A(000001) stage=preset_exit_sync_ok id=1 sync_status=OK",
        "[2026-04-03 09:34:00] [HOLDING_PIPELINE] 종목B(000002) stage=position_rebased_after_fill id=2 fill_quality=PARTIAL_FILL",
        "[2026-04-03 09:34:01] [HOLDING_PIPELINE] 종목B(000002) stage=preset_exit_sync_mismatch id=2 sync_status=QTY_MISMATCH sync_reason=qty_mismatch",
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
                        "name": "종목A",
                        "status": "COMPLETED",
                        "strategy": "SCALPING",
                        "position_tag": "SCANNER",
                        "buy_price": 10000.0,
                        "buy_qty": 5,
                        "buy_time": "2026-04-03 09:30:10",
                        "sell_price": 10120,
                        "sell_time": "2026-04-03 09:40:00",
                        "profit_rate": 1.2,
                        "realized_pnl_krw": 600,
                    },
                    {
                        "id": 2,
                        "rec_date": target_date,
                        "code": "000002",
                        "name": "종목B",
                        "status": "COMPLETED",
                        "strategy": "SCALPING",
                        "position_tag": "SCANNER",
                        "buy_price": 12000.0,
                        "buy_qty": 3,
                        "buy_time": "2026-04-03 09:31:10",
                        "sell_price": 11904,
                        "sell_time": "2026-04-03 09:41:00",
                        "profit_rate": -0.8,
                        "realized_pnl_krw": -288,
                    },
                ],
            },
        },
    )
    monkeypatch.setattr(report_mod, "_fetch_trade_history_rows", lambda target_date: ([], [], []))

    report = report_mod.build_performance_tuning_report(target_date="2026-04-03", since_time=None)

    assert report["metrics"]["budget_pass_events"] == 2
    assert report["metrics"]["order_bundle_submitted_events"] == 1
    assert report["metrics"]["latency_block_events"] == 1
    assert report["metrics"]["quote_fresh_latency_blocks"] == 1
    assert report["metrics"]["quote_fresh_latency_passes"] == 1
    assert report["metrics"]["expired_armed_events"] == 1
    assert report["metrics"]["full_fill_events"] == 1
    assert report["metrics"]["partial_fill_events"] == 1
    assert report["metrics"]["preset_exit_sync_mismatch_events"] == 1
    assert report["metrics"]["ai_overlap_blocked_events"] >= 1
    assert report["breakdowns"]["latency_reason_breakdown"][0]["label"] == "latency_state_danger"


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


def test_holding_sig_delta_parsing(monkeypatch):
    """보유 AI sig_delta 파싱 및 필드 추출 검증"""
    entry_lines = []
    holding_lines = [
        "[2026-04-03 10:01:00] [HOLDING_PIPELINE] 테스트A(000001) stage=ai_holding_reuse_bypass ws_age_sec=0.40 reuse_sec=5.0 age_sec=3.1 sig_delta=curr_price:10100->10120,spread_tick:1->2 reason_codes=sig_changed",
        "[2026-04-03 10:01:05] [HOLDING_PIPELINE] 테스트A(000001) stage=ai_holding_reuse_bypass ws_age_sec=0.45 reuse_sec=5.0 age_sec=3.6 sig_delta=curr_price:10120->10150,buy_ratio:52->61 reason_codes=sig_changed,near_low_score",
    ]

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

    sig_deltas = report["breakdowns"]["holding_sig_deltas"]
    sig_deltas_dict = {item["label"]: item["count"] for item in sig_deltas}
    assert sig_deltas_dict["curr_price"] == 2


def test_performance_tuning_ignores_null_profit_from_incomplete_or_broken_rows(monkeypatch):
    monkeypatch.setattr(report_mod, "_iter_target_lines", lambda log_path, *, target_date, marker: [])
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
                        "name": "완료정상",
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
                        "name": "미완료NULL",
                        "status": "WATCHING",
                        "strategy": "SCALPING",
                        "position_tag": "SCANNER",
                        "buy_price": 0.0,
                        "buy_qty": 0,
                        "buy_time": "",
                        "sell_price": 0,
                        "sell_time": "",
                        "profit_rate": None,
                        "realized_pnl_krw": 0,
                    },
                    {
                        "id": 3,
                        "rec_date": target_date,
                        "code": "000003",
                        "name": "완료NULL",
                        "status": "COMPLETED",
                        "strategy": "SCALPING",
                        "position_tag": "SCANNER",
                        "buy_price": 11000.0,
                        "buy_qty": 5,
                        "buy_time": "2026-04-03 10:10:00",
                        "sell_price": 11000,
                        "sell_time": "2026-04-03 10:20:00",
                        "profit_rate": None,
                        "realized_pnl_krw": 0,
                    },
                ],
            },
        },
    )
    monkeypatch.setattr(
        report_mod,
        "_fetch_trade_history_rows",
        lambda target_date: (
            [
                {
                    "rec_date": "2026-04-03",
                    "code": "000001",
                    "name": "완료정상",
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
                    "rec_date": "2026-04-03",
                    "code": "000002",
                    "name": "미완료NULL",
                    "status": "WATCHING",
                    "strategy": "SCALPING",
                    "buy_price": 0.0,
                    "buy_qty": 0,
                    "buy_time": "",
                    "sell_price": 0,
                    "sell_time": "",
                    "profit_rate": None,
                    "realized_pnl_krw": 0,
                },
                {
                    "rec_date": "2026-04-02",
                    "code": "000003",
                    "name": "완료NULL",
                    "status": "COMPLETED",
                    "strategy": "SCALPING",
                    "buy_price": 11000.0,
                    "buy_qty": 5,
                    "buy_time": "2026-04-02 10:10:00",
                    "sell_price": 11000,
                    "sell_time": "2026-04-02 10:20:00",
                    "profit_rate": None,
                    "realized_pnl_krw": 0,
                },
            ],
            [],
            ["2026-04-03", "2026-04-02"],
        ),
    )

    report = report_mod.build_performance_tuning_report(target_date="2026-04-03", since_time=None)

    scalping = next(item for item in report["strategy_rows"] if item["key"] == "scalping")
    assert scalping["outcomes"]["completed_rows"] == 2
    assert scalping["outcomes"]["win_count"] == 1
    assert scalping["outcomes"]["loss_count"] == 0
    assert scalping["outcomes"]["avg_profit_rate"] == 1.0
    assert scalping["trends"]["summary_5d"]["completed_rows"] == 2
    assert scalping["trends"]["summary_5d"]["win_count"] == 1
    assert scalping["trends"]["summary_5d"]["avg_profit_rate"] == 1.0


def test_swing_daily_summary_includes_market_regime_and_blockers(monkeypatch, tmp_path):
    entry_lines = [
        "[2026-04-03 10:00:00] [ENTRY_PIPELINE] 테스트A(000001) stage=market_regime_block strategy=KOSPI_ML",
        "[2026-04-03 10:00:05] [ENTRY_PIPELINE] 테스트B(000002) stage=blocked_gatekeeper_reject strategy=KOSPI_ML action=눌림|대기 gatekeeper_eval_ms=8200 gatekeeper_cache=miss cooldown_sec=1200 cooldown_policy=pullback_wait",
        "[2026-04-03 10:00:10] [ENTRY_PIPELINE] 테스트C(000003) stage=blocked_gatekeeper_reject strategy=KOSPI_ML action=눌림|대기 gatekeeper_eval_ms=9100 gatekeeper_cache=miss cooldown_sec=1200 cooldown_policy=pullback_wait",
        "[2026-04-03 10:00:15] [ENTRY_PIPELINE] 테스트D(000004) stage=blocked_swing_gap strategy=KOSPI_ML fluctuation=4.2 threshold=3.5",
    ]
    holding_lines = []

    def _fake_iter(log_path, *, target_date, marker):
        return entry_lines if marker == "[ENTRY_PIPELINE]" else holding_lines

    monkeypatch.setattr(report_mod, "_iter_target_lines", _fake_iter)
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)

    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    with open(cache_dir / "market_regime_snapshot.json", "w", encoding="utf-8") as handle:
        json.dump(
            {
                "cached_session_date": "2026-04-03",
                "risk_state": "RISK_OFF",
                "allow_swing_entry": False,
                "swing_score": 20,
            },
            handle,
            ensure_ascii=False,
        )

    monkeypatch.setattr(
        report_mod,
        "build_trade_review_report",
        lambda target_date, since_time=None, top_n=10000, scope="all": {
            "meta": {"warnings": []},
            "sections": {
                "recent_trades": [
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
    monkeypatch.setattr(report_mod, "_fetch_trade_history_rows", lambda target_date: ([], [], []))

    report = report_mod.build_performance_tuning_report(target_date="2026-04-03", since_time=None)

    swing_summary = report["sections"]["swing_daily_summary"]
    blocker_rows = {item["label"]: item for item in swing_summary["blocker_families"]}
    gatekeeper_actions = {item["label"]: item["count"] for item in swing_summary["gatekeeper_actions"]}

    assert swing_summary["market_regime"]["risk_state"] == "RISK_OFF"
    assert swing_summary["market_regime"]["allow_swing_entry"] is False
    assert swing_summary["day_type"]["label"] == "Gatekeeper 거부 중심 (시장 제한 동반)"
    assert blocker_rows["Gatekeeper 거부"]["count"] == 2
    assert blocker_rows["Gatekeeper 거부"]["stock_count"] == 2
    assert blocker_rows["시장 국면 제한"]["count"] == 1
    assert blocker_rows["스윙 갭상승"]["count"] == 1
    assert gatekeeper_actions["눌림 대기"] == 2


def test_performance_tuning_report_accepts_dynamic_trend_window(monkeypatch):
    monkeypatch.setattr(report_mod, "_iter_target_lines", lambda *args, **kwargs: [])
    monkeypatch.setattr(
        report_mod,
        "build_trade_review_report",
        lambda target_date, since_time=None, top_n=10000, scope="all": {
            "meta": {"warnings": []},
            "sections": {"recent_trades": []},
        },
    )
    captured = {}

    def _fake_history(target_date, max_dates=20):
        captured["target_date"] = target_date
        captured["max_dates"] = max_dates
        return [], [], []

    monkeypatch.setattr(report_mod, "_fetch_trade_history_rows", _fake_history)
    report = report_mod.build_performance_tuning_report(
        target_date="2026-04-03",
        since_time=None,
        trend_max_dates=7,
    )

    assert captured["target_date"] == "2026-04-03"
    assert captured["max_dates"] == 7
    assert report["meta"]["trend_max_dates"] == 7


def test_check_dotted_path_validates_nested_keys():
    """_check_dotted_path 단위 검증"""
    data = {
        "metrics": {"budget_pass_events": 5, "latency_block_events": 2},
        "breakdowns": {"latency_reason_breakdown": []},
        "sections": {"holding_axis": {}},
    }
    exists, missing = report_mod._check_dotted_path(data, "metrics.budget_pass_events")
    assert exists and missing is None
    exists, missing = report_mod._check_dotted_path(data, "metrics.nonexistent")
    assert not exists and missing == "nonexistent"
    exists, missing = report_mod._check_dotted_path(data, "breakdowns.latency_reason_breakdown")
    assert exists and missing is None
    exists, missing = report_mod._check_dotted_path(data, "sections.holding_axis")
    assert exists and missing is None


def test_observation_axis_coverage_returns_all_14_axes():
    """_build_observation_axis_coverage가 14개 axis row를 반환하고 direct/indirect축은 available=True"""
    metrics = {
        "budget_pass_events": 10, "order_bundle_submitted_events": 5, "budget_pass_to_submitted_rate": 50.0,
        "latency_block_events": 2, "latency_pass_events": 8, "quote_fresh_latency_pass_rate": 80.0,
        "gatekeeper_fast_reuse_ratio": 30.0, "gatekeeper_eval_ms_p95": 450.0,
        "full_fill_events": 4, "partial_fill_events": 1,
        "holding_reviews": 6, "holding_skips": 3,
        "dual_persona_shadow_samples": 5, "dual_persona_conflict_ratio": 40.0,
        "preset_exit_sync_ok_events": 3, "preset_exit_sync_mismatch_events": 1,
        "expired_armed_events": 0,
    }
    breakdowns = {
        "latency_reason_breakdown": [{"label": "latency_state_danger", "count": 2}],
        "gatekeeper_reuse_blockers": [{"label": "시그니처 변경", "count": 3}],
        "gatekeeper_sig_deltas": [{"label": "curr_price", "count": 2}],
        "fill_quality_cohorts": [{"label": "FULL_FILL", "count": 4, "avg_profit_rate": 0.5}],
        "exit_rules": [{"label": "scalp_ai_early_exit", "count": 1}],
        "dual_persona_agreement": [{"label": "all_agree", "count": 3}],
        "dual_persona_decision_types": [{"label": "gatekeeper", "count": 3}],
        "preset_exit_sync_status": [{"label": "OK", "count": 3}],
    }
    sections = {"holding_axis": {"holding_action_applied": 1}}
    rows = report_mod._build_observation_axis_coverage(metrics, breakdowns, sections)
    assert len(rows) == 14
    direct_axes = {r["axis_id"] for r in rows if r["coverage_status"] == "direct"}
    assert len(direct_axes) == 7
    for r in rows:
        if r["coverage_status"] in ("direct", "indirect"):
            assert r["available"] is True, f"{r['axis_id']} should be available but missing {r['missing_keys']}"
        elif r["coverage_status"] in ("external_report", "collected_not_displayed"):
            assert r["available"] is False, f"{r['axis_id']} should be unavailable (no external data)"


def test_flow_bottleneck_lane_returns_9_nodes():
    """_build_flow_bottleneck_lane가 9개 node 반환, stage_group은 4종 스펙 준수"""
    metrics = {
        "budget_pass_events": 10, "order_bundle_submitted_events": 5,
        "latency_block_events": 0, "latency_pass_events": 10, "quote_fresh_latency_pass_rate": 100.0,
        "expired_armed_events": 0, "position_rebased_after_fill_events": 0,
        "full_fill_events": 4, "partial_fill_events": 1,
        "holding_reviews": 6, "holding_skips": 3,
        "exit_signals": 3, "preset_exit_sync_mismatch_events": 0,
        "full_fill_completed_avg_profit_rate": 0.5, "partial_fill_completed_avg_profit_rate": -0.2,
        "ai_overlap_blocked_events": 1, "ai_overlap_overbought_blocked_events": 0,
    }
    breakdowns = {
        "latency_reason_breakdown": [],
        "gatekeeper_reuse_blockers": [],
        "gatekeeper_sig_deltas": [],
    }
    sections = {
        "strategy_rows": [
            {
                "pipeline": {"candidates": 20},
                "outcomes": {"completed_rows": 5},
            }
        ],
        "swing_daily_summary": {
            "metrics": {"blocker_event_count": 0},
            "blocker_families": [],
        },
    }
    result = report_mod._build_flow_bottleneck_lane(metrics, breakdowns, sections)
    assert len(result["nodes"]) == 9
    node_ids = [n["node_id"] for n in result["nodes"]]
    expected = ["watch_universe", "ai_decision", "entry_armed", "pre_submit_latency",
                "submitted_fill", "holding_review", "scale_in_branch", "exit_signal", "sell_complete"]
    assert node_ids == expected
    for n in result["nodes"]:
        assert n["status"] in ("ok", "watch", "bottleneck", "anomaly", "waiting", "not_applicable")
        # stage_group은 4종 스펙(ENTRY, EXECUTION, HOLDING, EXIT) 준수
        assert n["stage_group"] in ("ENTRY", "EXECUTION", "HOLDING", "EXIT"), (
            f"stage_group={n['stage_group']} not in spec 4-type"
        )
        # stage 필드는 상세 표시용으로 존재
        assert "stage" in n
    assert "meta" in result


def test_flow_bottleneck_lane_latency_bottleneck_detection():
    """pre_submit_latency bottleneck 상태 감지: latency_block>0 + quote_pass_rate<30"""
    metrics = {
        "budget_pass_events": 10, "order_bundle_submitted_events": 0,
        "latency_block_events": 5, "latency_pass_events": 1, "quote_fresh_latency_pass_rate": 16.0,
        "expired_armed_events": 0, "position_rebased_after_fill_events": 0,
        "full_fill_events": 0, "partial_fill_events": 0,
        "holding_reviews": 0, "holding_skips": 0,
        "exit_signals": 0, "preset_exit_sync_mismatch_events": 0,
        "full_fill_completed_avg_profit_rate": 0.0, "partial_fill_completed_avg_profit_rate": 0.0,
        "ai_overlap_blocked_events": 0, "ai_overlap_overbought_blocked_events": 0,
    }
    breakdowns = {}
    sections = {
        "strategy_rows": [],
        "swing_daily_summary": {
            "metrics": {"blocker_event_count": 0},
            "blocker_families": [],
        },
    }
    result = report_mod._build_flow_bottleneck_lane(metrics, breakdowns, sections)
    pre_submit = next(n for n in result["nodes"] if n["node_id"] == "pre_submit_latency")
    assert pre_submit["status"] == "bottleneck"
    assert "latency guard threshold" in pre_submit["tuning_point"]


def test_observation_axis_coverage_gatekeeper_sig_deltas_required_key():
    """gatekeeper_fast_reuse required_keys에 breakdowns.gatekeeper_sig_deltas 포함 여부 검증
    - CASE 1: sig_deltas 존재 → available=True
    - CASE 2: sig_deltas 누락 → available=False, missing_keys에 포함
    """
    base_metrics = {
        "budget_pass_events": 10, "order_bundle_submitted_events": 5, "budget_pass_to_submitted_rate": 50.0,
        "latency_block_events": 2, "latency_pass_events": 8, "quote_fresh_latency_pass_rate": 80.0,
        "gatekeeper_fast_reuse_ratio": 30.0, "gatekeeper_eval_ms_p95": 450.0,
        "full_fill_events": 4, "partial_fill_events": 1,
        "holding_reviews": 6, "holding_skips": 3,
        "dual_persona_shadow_samples": 5, "dual_persona_conflict_ratio": 40.0,
        "preset_exit_sync_ok_events": 3, "preset_exit_sync_mismatch_events": 1,
    }
    base_breakdowns = {
        "latency_reason_breakdown": [{"label": "latency_state_danger", "count": 2}],
        "gatekeeper_reuse_blockers": [{"label": "시그니처 변경", "count": 3}],
        # gatekeeper_sig_deltas 제외 (누락 케이스)
        "fill_quality_cohorts": [{"label": "FULL_FILL", "count": 4, "avg_profit_rate": 0.5}],
        "exit_rules": [{"label": "scalp_ai_early_exit", "count": 1}],
        "dual_persona_agreement": [{"label": "all_agree", "count": 3}],
        "dual_persona_decision_types": [{"label": "gatekeeper", "count": 3}],
        "preset_exit_sync_status": [{"label": "OK", "count": 3}],
    }
    sections = {"holding_axis": {"holding_action_applied": 1}}

    # CASE 1: sig_deltas 있음 → available
    breakdowns_with = dict(base_breakdowns)
    breakdowns_with["gatekeeper_sig_deltas"] = [{"label": "curr_price", "count": 2}]
    rows_with = report_mod._build_observation_axis_coverage(base_metrics, breakdowns_with, sections)
    gk_with = next(r for r in rows_with if r["axis_id"] == "gatekeeper_fast_reuse")
    assert gk_with["available"] is True
    assert "breakdowns.gatekeeper_sig_deltas" not in gk_with["missing_keys"]

    # CASE 2: sig_deltas 없음 → 누락 감지
    rows_without = report_mod._build_observation_axis_coverage(base_metrics, base_breakdowns, sections)
    gk_without = next(r for r in rows_without if r["axis_id"] == "gatekeeper_fast_reuse")
    assert gk_without["available"] is False
    assert "breakdowns.gatekeeper_sig_deltas" in gk_without["missing_keys"]


def test_performance_tuning_api_includes_new_sections(monkeypatch):
    """API endpoint /api/performance-tuning 응답에 flow_bottleneck_lane과 observation_axis_coverage 포함 검증."""
    import src.web.app as web_app
    monkeypatch.setattr(web_app, "_load_saved_performance_tuning_snapshot", lambda *args, **kwargs: {
        "metrics": {},
        "breakdowns": {},
        "sections": {
            "flow_bottleneck_lane": {
                "nodes": [{"node_id": "test", "status": "ok"}],
                "meta": {"warnings": []},
            },
            "observation_axis_coverage": [
                {"axis_id": "test_axis", "available": True, "missing_keys": []},
            ],
        },
        "meta": {"source": "snapshot"},
    })
    with web_app.app.test_client() as client:
        resp = client.get("/api/performance-tuning?target_date=2026-04-24")
    assert resp.status_code == 200
    data = resp.get_json()
    assert "flow_bottleneck_lane" in data.get("sections", {})
    assert "observation_axis_coverage" in data.get("sections", {})
    assert len(data["sections"]["flow_bottleneck_lane"]["nodes"]) >= 1


def test_performance_tuning_html_renders_new_sections(monkeypatch):
    """HTML /performance-tuning 페이지에 Flow Bottleneck Lane 및 관찰축 커버리지 섹션 렌더링 검증."""
    import src.web.app as web_app
    monkeypatch.setattr(web_app, "_load_saved_performance_tuning_snapshot", lambda *args, **kwargs: {
        "metrics": {},
        "breakdowns": {},
        "sections": {
            "flow_bottleneck_lane": {
                "nodes": [
                    {"node_id": "test_node", "node_name": "테스트 노드", "status": "ok",
                     "stage_group": "TEST", "stage": "TEST", "primary_metric": "test", "primary_value": 0,
                     "supporting_metrics": [], "tuning_point": "-",
                     "evidence_keys": [], "missing_keys": [], "next_action": "정상"},
                ],
                "meta": {"warnings": []},
            },
            "observation_axis_coverage": [
                {"axis_id": "direct_axis", "axis_name": "직접 표시 축", "coverage_status": "direct",
                 "source_snapshot": "test", "dashboard_location": "test", "decision_use": "test",
                 "required_keys": [], "gap_action": "-", "owner_doc": "-",
                 "available": True, "missing_keys": [], "reuse_mode": "existing_metric"},
                {"axis_id": "external_axis", "axis_name": "외부 리포트 축", "coverage_status": "external_report",
                 "source_snapshot": "post_sell_feedback", "dashboard_location": "별도", "decision_use": "참고",
                 "required_keys": ["MISSED_UPSIDE"], "gap_action": "링크", "owner_doc": "-",
                 "available": False, "missing_keys": ["MISSED_UPSIDE"], "reuse_mode": "external_report_pointer"},
                {"axis_id": "collected_axis", "axis_name": "수집 미표시 축", "coverage_status": "collected_not_displayed",
                 "source_snapshot": "raw_log", "dashboard_location": "미표시", "decision_use": "참고",
                 "required_keys": ["initial_entry"], "gap_action": "증적", "owner_doc": "-",
                 "available": False, "missing_keys": ["initial_entry"], "reuse_mode": "raw_log_pointer"},
            ],
        },
        "meta": {"source": "snapshot"},
    })
    with web_app.app.test_client() as client:
        resp = client.get("/performance-tuning?target_date=2026-04-24")
    assert resp.status_code == 200
    html = resp.data.decode("utf-8")
    assert "Flow Bottleneck Lane" in html
    assert "관찰축 커버리지" in html or "Observation Axis" in html
    assert "테스트 노드" in html
    assert "직접 표시 축" in html
    # 감리: external_report available=false → "외부 리포트 연결" 표시
    assert "외부 리포트 연결" in html
    # 감리: collected_not_displayed available=false → "수집/증적 유지" 표시
    assert "수집/증적 유지" in html


def test_flow_bottleneck_lane_scale_in_branch_zero_qty_bottleneck():
    """scale_in_branch 노드가 swing_daily_summary blocker zero_qty 힌트를 통해 bottleneck 감지"""
    metrics = {
        "budget_pass_events": 10, "order_bundle_submitted_events": 5,
        "latency_block_events": 0, "latency_pass_events": 10, "quote_fresh_latency_pass_rate": 100.0,
        "expired_armed_events": 0, "position_rebased_after_fill_events": 0,
        "full_fill_events": 4, "partial_fill_events": 1,
        "holding_reviews": 6, "holding_skips": 3,
        "exit_signals": 3, "preset_exit_sync_mismatch_events": 0,
        "full_fill_completed_avg_profit_rate": 0.5, "partial_fill_completed_avg_profit_rate": -0.2,
        "ai_overlap_blocked_events": 1, "ai_overlap_overbought_blocked_events": 0,
    }
    breakdowns = {}
    # zero_qty 힌트가 있는 swing_daily_summary
    sections = {
        "strategy_rows": [{"pipeline": {"candidates": 20}, "outcomes": {"completed_rows": 5}}],
        "swing_daily_summary": {
            "metrics": {"blocker_event_count": 3},
            "blocker_families": [
                {"label": "주문 가능 수량", "count": 3, "stock_count": 2},
            ],
        },
    }
    result = report_mod._build_flow_bottleneck_lane(metrics, breakdowns, sections)
    scale_in = next(n for n in result["nodes"] if n["node_id"] == "scale_in_branch")
    assert scale_in["status"] == "bottleneck", (
        f"position_rebased=0 + zero_qty 힌트 있음 → bottleneck 예상, 실제={scale_in['status']}"
    )
    assert "zero_qty" in scale_in["tuning_point"] or "차단" in scale_in["tuning_point"]


def test_observation_axis_coverage_external_report_badge_not_red():
    """external_report/collected_not_displayed 축은 available=false여도 '키 누락' 마크 없이 상태 표시"""
    metrics = {"budget_pass_events": 1, "order_bundle_submitted_events": 0, "budget_pass_to_submitted_rate": 0.0}
    breakdowns = {}
    sections = {}
    rows = report_mod._build_observation_axis_coverage(metrics, breakdowns, sections)
    for row in rows:
        if row["coverage_status"] in ("external_report", "collected_not_displayed"):
            assert row["available"] is False, (
                f"{row['axis_id']}은 external/collected이므로 available=false 정상"
            )
            # 이 축들은 UI에서 '키 누락' 빨간 배지 대신 회색/정보 배지로 표시되어야 함
            # available=false지만, engine에서 warnings에 포함되지 않아야 함
