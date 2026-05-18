import json
from datetime import datetime

from src.engine import panic_sell_defense_report as report_mod


TARGET_DATE = "2026-05-12"


def _event(
    hhmmss: str,
    *,
    stage: str = "exit_signal",
    pipeline: str = "HOLDING_PIPELINE",
    record_id: int = 1,
    stock_code: str = "000001",
    fields: dict | None = None,
) -> dict:
    return {
        "schema_version": 1,
        "event_type": "pipeline_event",
        "pipeline": pipeline,
        "stage": stage,
        "stock_name": "테스트종목",
        "stock_code": stock_code,
        "record_id": record_id,
        "fields": fields or {},
        "emitted_at": f"{TARGET_DATE}T{hhmmss}",
        "emitted_date": TARGET_DATE,
    }


def _write_events(tmp_path, rows: list[dict]) -> None:
    event_dir = tmp_path / "pipeline_events"
    event_dir.mkdir(parents=True, exist_ok=True)
    with (event_dir / f"pipeline_events_{TARGET_DATE}.jsonl").open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_json(path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _write_market_regime(tmp_path, *, risk_state: str = "NEUTRAL") -> None:
    _write_json(
        tmp_path / "cache" / "market_regime_snapshot.json",
        {
            "risk_state": risk_state,
            "allow_swing_entry": risk_state != "RISK_OFF",
            "swing_score": 35 if risk_state == "RISK_OFF" else 60,
        },
    )


def _write_market_panic_breadth(tmp_path, *, risk_off: bool = True) -> None:
    _write_json(
        tmp_path / "report" / "market_panic_breadth" / f"market_panic_breadth_{TARGET_DATE}.json",
        {
            "as_of": f"{TARGET_DATE}T10:29:00",
            "source_quality": {"status": "ok"},
            "panic_breadth": {
                "risk_off_advisory": risk_off,
                "industry_breadth": {
                    "sample_count": 10,
                    "down_count": 8,
                    "down_ratio_pct": 80.0,
                },
                "market_indices": {
                    "KOSPI": {"code": "001", "name": "종합(KOSPI)", "change_pct": -1.6},
                    "KOSDAQ": {"code": "101", "name": "코스닥", "change_pct": -2.1},
                },
                "reasons": ["market_index_intraday_drop", "industry_breadth_down_ratio_high"],
            },
        },
    )


def _panic_rows() -> list[dict]:
    return [
        _event(
            f"10:{idx:02d}:00",
            record_id=idx,
            fields={"exit_rule": "scalp_soft_stop_loss", "profit_rate": "-2.5"},
        )
        for idx in range(5)
    ]


def _micro_event(hhmmss: str, *, close: float, volume: float = 100.0, buy: float = 52.0, sell: float = 48.0, **fields):
    payload = {
        "curr_price": close,
        "open": fields.pop("open", close),
        "high": fields.pop("high", close),
        "low": fields.pop("low", close),
        "volume": volume,
        "buy_exec_volume": buy,
        "sell_exec_volume": sell,
        **fields,
    }
    return _event(
        hhmmss,
        pipeline="ENTRY_PIPELINE",
        stage="orderbook_stability_observed",
        fields=payload,
    )


def test_normal_state_without_panic_threshold(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        [
            _event(
                "10:00:00",
                fields={"exit_rule": "scalp_trailing_take_profit", "profit_rate": "1.2"},
            )
        ],
    )

    report = report_mod.build_panic_sell_defense_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:30:00"),
    )

    assert report["panic_state"] == "NORMAL"
    assert report["panic_regime_mode"] == "NORMAL"
    assert report["policy"]["runtime_effect"] == "report_only_no_mutation"
    assert report["panic_metrics"]["panic_detected"] is False
    assert report["panic_regime_contract"]["decision_authority"] == "source_quality_only"
    assert report["panic_regime_contract"]["allowed_runtime_apply"] is False


def test_live_market_panic_breadth_can_mark_report_only_panic(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        [
            _micro_event("10:00:00", close=100.0),
            _micro_event("10:01:00", close=99.8),
            _micro_event("10:02:00", close=99.7),
        ],
    )
    _write_market_regime(tmp_path, risk_state="NEUTRAL")
    _write_market_panic_breadth(tmp_path, risk_off=True)

    report = report_mod.build_panic_sell_defense_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:30:00"),
    )

    assert report["panic_state"] == "PANIC_SELL"
    assert report["policy"]["runtime_effect"] == "report_only_no_mutation"
    assert report["microstructure_market_context"]["market_panic_breadth_risk_off_advisory"] is True
    assert "live market panic breadth risk_off advisory" in report["panic_state_reasons"]


def test_panic_sell_state_from_five_stop_losses_in_30_minutes(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(tmp_path, _panic_rows())

    report = report_mod.build_panic_sell_defense_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:29:00"),
    )

    assert report["panic_state"] == "PANIC_SELL"
    assert report["panic_regime_mode"] == "PANIC_DETECTED"
    assert report["panic_metrics"]["current_30m_stop_loss_exit_count"] == 5
    assert report["panic_metrics"]["panic_by_stop_loss_count"] is True
    assert "candidate_entry_pre_submit_freeze" in report["panic_regime_contract"]["allowed_actions"]
    assert "auto_sell" in report["panic_regime_contract"]["forbidden_uses"]
    freeze = next(item for item in report["canary_candidates"] if item["family"] == "panic_entry_freeze_guard")
    assert freeze["status"] == "report_only_candidate"
    assert freeze["allowed_runtime_apply"] is False


def test_probe_sibling_marks_sparse_exit_signal_as_non_real(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    rows = []
    for idx in range(5):
        rows.append(
            _event(
                f"10:{idx:02d}:00",
                record_id=idx + 1,
                fields={"exit_rule": "scalp_soft_stop_loss", "profit_rate": "-2.5"},
            )
        )
        rows.append(
            _event(
                f"10:{idx:02d}:01",
                stage="swing_probe_exit_signal",
                record_id=idx + 1,
                fields={
                    "exit_rule": "scalp_soft_stop_loss",
                    "profit_rate": "-2.5",
                    "actual_order_submitted": "false",
                    "broker_order_forbidden": "true",
                    "probe_origin_stage": "swing_intraday_probe",
                },
            )
        )
    _write_events(tmp_path, rows)

    report = report_mod.build_panic_sell_defense_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:29:00"),
    )

    assert report["panic_state"] == "NORMAL"
    assert report["panic_metrics"]["real_exit_count"] == 0
    assert report["panic_metrics"]["non_real_exit_count"] == 10
    assert report["panic_metrics"]["stop_loss_exit_count"] == 0
    assert report["panic_metrics"]["panic_by_stop_loss_count"] is False


def test_non_real_assumed_fill_marks_sparse_exit_signal_as_non_real(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        [
            _event(
                "10:00:00",
                record_id=0,
                stock_code="042700",
                fields={"exit_rule": "scalp_soft_stop_loss", "profit_rate": "-2.0"},
            ),
            _event(
                "10:00:01",
                stage="scalp_sim_sell_order_assumed_filled",
                record_id=0,
                stock_code="042700",
                fields={
                    "exit_rule": "scalp_soft_stop_loss",
                    "profit_rate": "-2.0",
                    "simulated_order": "true",
                    "actual_order_submitted": "false",
                    "simulation_book": "scalp_ai_buy_all",
                },
            ),
        ],
    )

    report = report_mod.build_panic_sell_defense_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:29:00"),
    )

    assert report["panic_state"] == "NORMAL"
    assert report["panic_metrics"]["real_exit_count"] == 0
    assert report["panic_metrics"]["non_real_exit_count"] == 1
    assert report["panic_metrics"]["stop_loss_exit_count"] == 0


def test_recovery_watch_uses_active_sim_probe_average(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(tmp_path, _panic_rows())
    _write_json(
        tmp_path / "runtime" / "scalp_live_simulator_state.json",
        {
            "owner": "scalp_ai_buy_all_live_simulator",
            "active_positions": [
                {
                    "stock_code": "000001",
                    "stock_name": "SIM1",
                    "buy_price": 10000,
                    "curr_price": 10110,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                {
                    "stock_code": "000002",
                    "stock_name": "SIM2",
                    "buy_price": 10000,
                    "curr_price": 10000,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
            ],
        },
    )

    report = report_mod.build_panic_sell_defense_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:29:00"),
    )

    assert report["panic_state"] == "RECOVERY_WATCH"
    assert report["panic_regime_mode"] == "STABILIZING"
    active = report["recovery_metrics"]["active_sim_probe"]
    assert active["avg_unrealized_profit_rate_pct"] == 0.55
    assert active["win_rate_pct"] == 50.0
    assert active["provenance_check"]["passed"] is True


def test_recovery_confirmed_keeps_probe_report_only_and_broker_forbidden(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(tmp_path, _panic_rows())
    _write_json(
        tmp_path / "runtime" / "scalp_live_simulator_state.json",
        {
            "active_positions": [
                {
                    "stock_code": "000001",
                    "stock_name": "SIM1",
                    "buy_price": 10000,
                    "curr_price": 10160,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                {
                    "stock_code": "000002",
                    "stock_name": "SIM2",
                    "buy_price": 10000,
                    "curr_price": 10100,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
                {
                    "stock_code": "000003",
                    "stock_name": "SIM3",
                    "buy_price": 10000,
                    "curr_price": 9990,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
            ],
        },
    )

    report = report_mod.build_panic_sell_defense_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:29:00"),
    )

    assert report["panic_state"] == "RECOVERY_CONFIRMED"
    assert report["panic_regime_mode"] == "RECOVERY_CONFIRMED"
    rebound = next(item for item in report["canary_candidates"] if item["family"] == "panic_rebound_probe")
    assert rebound["status"] == "report_only_candidate"
    assert rebound["allowed_runtime_apply"] is False
    assert rebound["provenance_check_passed"] is True
    assert report["policy"]["report_only"] is True


def test_micro_recovery_confirmed_does_not_release_market_risk_off():
    state, reasons = report_mod._resolve_panic_state(
        panic_metrics={"panic_detected": False},
        active_recovery={
            "profit_sample": 0,
            "avg_unrealized_profit_rate_pct": 0.0,
            "win_rate_pct": 0.0,
        },
        post_sell_recovery={
            "rebound_above_sell_10_20m_pct": 0.0,
            "rebound_above_buy_10_20m_pct": 0.0,
        },
        microstructure_detector={
            "risk_off_advisory_count": 1,
            "recovery_confirmed_count": 1,
            "recovery_candidate_count": 0,
        },
        microstructure_market_context={
            "confirmed_risk_off_advisory": True,
            "market_panic_breadth_risk_off_advisory": True,
        },
    )

    assert state == "RECOVERY_WATCH"
    assert "microstructure recovery confirmed but market risk-off remains" in reasons


def test_hard_protect_emergency_exits_are_never_confirmation_eligible():
    hard_rows = [
        _event("10:00:00", fields={"exit_rule": "scalp_hard_stop_pct"}),
        _event("10:01:00", fields={"exit_rule": "protect_hard_stop"}),
        _event("10:02:00", fields={"exit_rule": "emergency_stop"}),
    ]
    eligible_rows = [
        _event("10:03:00", fields={"exit_rule": "scalp_soft_stop_loss"}),
        _event("10:04:00", fields={"exit_rule": "scalp_trailing_take_profit"}),
        _event("10:05:00", fields={"exit_rule": "holding_flow_override_defer_cost"}),
    ]

    assert all(report_mod.is_hard_protect_emergency_exit(row) for row in hard_rows)
    assert not any(report_mod.is_confirmation_eligible_exit(row) for row in hard_rows)
    assert all(report_mod.is_confirmation_eligible_exit(row) for row in eligible_rows)


def test_post_sell_feedback_is_separate_from_closed_pnl(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(tmp_path, _panic_rows())
    _write_json(
        tmp_path / "report" / "monitor_snapshots" / f"post_sell_feedback_{TARGET_DATE}.json",
        {
            "soft_stop_forensics": {
                "total_soft_stop": 5,
                "rebound_above_sell_rate": {"10m": 40.0, "20m": 55.0},
                "rebound_above_buy_rate": {"10m": 12.0, "20m": 20.0},
            }
        },
    )

    report = report_mod.build_panic_sell_defense_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:29:00"),
    )

    assert report["panic_state"] == "RECOVERY_WATCH"
    assert report["panic_metrics"]["avg_exit_profit_rate_pct"] == -2.5
    post_sell = report["recovery_metrics"]["post_sell_feedback"]
    assert post_sell["rebound_above_sell_10_20m_pct"] == 55.0
    assert post_sell["rebound_above_buy_10_20m_pct"] == 20.0


def test_microstructure_detector_adds_report_only_risk_off_without_order_action(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_market_regime(tmp_path, risk_state="RISK_OFF")
    _write_events(
        tmp_path,
        [
            _micro_event("10:00:00", close=100.0),
            _micro_event("10:01:00", close=100.0),
            _micro_event(
                "10:02:00",
                close=97.5,
                open=100.0,
                high=100.1,
                low=97.45,
                volume=420,
                buy=28,
                sell=72,
                best_bid=9700,
                best_ask=9710,
                bid_depth_l5=540,
                ask_depth_l5=1400,
                panic_spread_ratio=2.0,
                orderbook_micro_ofi_z=-2.7,
                orderbook_micro_qi_ewma=0.38,
                orderbook_micro_state="bearish",
                orderbook_micro_ready=True,
                orderbook_micro_observer_healthy=True,
            ),
            _micro_event(
                "10:03:00",
                close=97.0,
                open=97.6,
                high=97.7,
                low=96.9,
                volume=430,
                buy=27,
                sell=73,
                best_bid=9690,
                best_ask=9710,
                bid_depth_l5=500,
                ask_depth_l5=1500,
                panic_spread_ratio=2.1,
                orderbook_micro_ofi_z=-2.8,
                orderbook_micro_qi_ewma=0.36,
                orderbook_micro_state="bearish",
                orderbook_micro_ready=True,
                orderbook_micro_observer_healthy=True,
            ),
        ],
    )

    report = report_mod.build_panic_sell_defense_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:04:00"),
    )

    micro = report["microstructure_detector"]
    assert report["panic_state"] == "PANIC_SELL"
    assert report["policy"]["runtime_effect"] == "report_only_no_mutation"
    assert micro["risk_off_advisory_count"] == 1
    assert micro["allow_new_long_false_count"] == 1
    assert report["microstructure_market_context"]["confirmed_risk_off_advisory"] is True
    assert report["microstructure_market_context"]["market_confirms_risk_off"] is True
    assert micro["latest_signals"][0]["risk_off_advisory"] is True
    assert micro["policy"]["does_not_submit_orders"] is True
    assert micro["micro_cusum_observer"]["decision_authority"] == "source_quality_only"
    assert micro["micro_cusum_observer"]["consensus_pass_symbol_count"] == 1
    assert "order_submit" in micro["micro_cusum_observer"]["forbidden_uses"]
    assert all(item["allowed_runtime_apply"] is False for item in report["canary_candidates"])


def test_microstructure_risk_off_needs_market_or_breadth_confirmation(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_market_regime(tmp_path, risk_state="NEUTRAL")
    _write_events(
        tmp_path,
        [
            _micro_event("10:00:00", close=100.0),
            _micro_event("10:01:00", close=100.0),
            _micro_event(
                "10:02:00",
                close=97.5,
                open=100.0,
                high=100.1,
                low=97.45,
                volume=420,
                buy=28,
                sell=72,
                best_bid=9700,
                best_ask=9710,
                bid_depth_l5=540,
                ask_depth_l5=1400,
                panic_spread_ratio=2.0,
                orderbook_micro_ofi_z=-2.7,
                orderbook_micro_state="bearish",
                orderbook_micro_ready=True,
                orderbook_micro_observer_healthy=True,
            ),
            _micro_event(
                "10:03:00",
                close=97.0,
                open=97.6,
                high=97.7,
                low=96.9,
                volume=430,
                buy=27,
                sell=73,
                best_bid=9690,
                best_ask=9710,
                bid_depth_l5=500,
                ask_depth_l5=1500,
                panic_spread_ratio=2.1,
                orderbook_micro_ofi_z=-2.8,
                orderbook_micro_state="bearish",
                orderbook_micro_ready=True,
                orderbook_micro_observer_healthy=True,
            ),
        ],
    )

    report = report_mod.build_panic_sell_defense_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:04:00"),
    )

    assert report["microstructure_detector"]["risk_off_advisory_count"] == 1
    market_context = report["microstructure_market_context"]
    assert report["panic_state"] == "NORMAL"
    assert market_context["confirmed_risk_off_advisory"] is False
    assert market_context["portfolio_local_risk_off_only"] is True
    assert "market_regime_not_risk_off" in market_context["reasons"]
    assert "microstructure risk_off unconfirmed by market/breadth context" in report["panic_state_reasons"]
