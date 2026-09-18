import json
from datetime import datetime

from src.engine import panic_sell_defense_report as report_mod

TARGET_DATE = "2026-06-05"


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
    with (event_dir / f"pipeline_events_{TARGET_DATE}.jsonl").open(
        "w", encoding="utf-8"
    ) as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _write_json(path, payload: dict) -> None:
    if path.name in {"scalp_live_simulator_state.json", "swing_intraday_probe_state.json"}:
        payload = {"updated_at": f"{TARGET_DATE}T10:00:00", **payload}
    if path.name == f"post_sell_feedback_{TARGET_DATE}.json":
        payload = {"date": TARGET_DATE, "meta": {"generated_at": f"{TARGET_DATE}T10:00:00"}, **payload}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _write_market_regime(tmp_path, *, risk_state: str = "NEUTRAL") -> None:
    _write_json(
        tmp_path / "cache" / "market_regime_snapshot.json",
        {
            "timestamp": f"{TARGET_DATE}T10:00:00",
            "risk_state": risk_state,
            "allow_swing_entry": risk_state != "RISK_OFF",
            "swing_score": 35 if risk_state == "RISK_OFF" else 60,
        },
    )


def _write_market_panic_breadth(tmp_path, *, risk_off: bool = True) -> None:
    _write_json(
        tmp_path
        / "report"
        / "market_panic_breadth"
        / f"market_panic_breadth_{TARGET_DATE}.json",
        {
            "target_date": TARGET_DATE,
            "as_of": f"{TARGET_DATE}T10:29:00",
            "source_quality": {"status": "ok"},
            "market_weakness_observation": {
                "observation_id": "weakness-test-1",
                "target_date": TARGET_DATE,
                "as_of": f"{TARGET_DATE}T10:29:00",
                "raw_state": "BROAD_WEAKNESS" if risk_off else "RECOVERY_EVIDENCE",
                "source_quality_ready": True,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "release_margin": {"passed": not risk_off},
            },
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
                "reasons": [
                    "market_index_intraday_drop",
                    "industry_breadth_down_ratio_high",
                ],
            },
        },
    )


def _panic_rows() -> list[dict]:
    return [
        _event(
            f"10:{idx:02d}:00",
            record_id=idx,
            fields={
                "exit_rule": "scalp_soft_stop_loss",
                "profit_rate": "-2.5",
                "actual_order_submitted": "true",
                "sell_order_no": f"S{idx:04d}",
            },
        )
        for idx in range(5)
    ]


def _micro_event(
    hhmmss: str,
    *,
    close: float,
    volume: float = 100.0,
    buy: float = 52.0,
    sell: float = 48.0,
    **fields,
):
    payload = {
        "curr_price": close,
        "candle_open": fields.pop("open", close),
        "candle_high": fields.pop("high", close),
        "candle_low": fields.pop("low", close),
        "bar_volume": volume,
        "buy_exec_volume": buy,
        "sell_exec_volume": sell,
        **fields,
    }
    if any(
        key in payload
        for key in (
            "best_bid",
            "best_ask",
            "orderbook_micro_ofi_z",
            "orderbook_micro_state",
        )
    ):
        payload.setdefault(
            "orderbook_micro_captured_at_ms", int(hhmmss.replace(":", "")) * 1000
        )
        payload.setdefault("orderbook_micro_snapshot_age_ms", 100)
    return _event(
        hhmmss,
        pipeline="ENTRY_PIPELINE",
        stage="orderbook_stability_observed",
        fields=payload,
    )


def test_pipeline_input_streaming_retains_only_exit_contract_rows(monkeypatch):
    rows = [
        _event(
            "10:00:00",
            pipeline="ENTRY_PIPELINE",
            stage="scalping_scanner_scheduler_claim_deferred",
            record_id=index,
            fields={"reason": "scheduler_only"},
        )
        for index in range(5_000)
    ]
    rows.extend(
        [
            _micro_event("10:01:00", close=100.0),
            _micro_event("10:02:00", close=99.5),
            _event(
                "10:03:00",
                fields={
                    "exit_rule": "scalp_soft_stop_loss",
                    "profit_rate": "-2.5",
                    "actual_order_submitted": "true",
                    "sell_order_no": "S1",
                },
            ),
            _event(
                "10:04:00",
                stage="scalp_sim_exit_observed",
                fields={
                    "actual_order_submitted": "false",
                    "broker_order_forbidden": "true",
                },
            ),
        ]
    )
    consumed = {"count": 0}

    def iter_once(_path):
        for row in rows:
            consumed["count"] += 1
            yield row

    monkeypatch.setattr(report_mod, "iter_jsonl", iter_once)

    retained, micro, latest_dt, contract = report_mod._stream_pipeline_inputs(
        report_mod.Path("unused.jsonl"),
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:05:00"),
    )

    assert consumed["count"] == len(rows)
    assert len(retained) == 2
    assert contract["memory_bounded_streaming"] is True
    assert contract["full_event_list_materialized"] is False
    assert contract["scanned_row_count"] == len(rows)
    assert contract["retained_exit_event_count"] == 2
    assert micro["streaming_input"]["candidate_event_count"] == 2
    assert latest_dt == datetime.fromisoformat(f"{TARGET_DATE}T10:04:00")


def test_normal_state_without_panic_threshold(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        [
            _event(
                "10:00:00",
                fields={
                    "exit_rule": "scalp_trailing_take_profit",
                    "profit_rate": "1.2",
                },
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
    assert (
        report["panic_regime_contract"]["decision_authority"] == "source_quality_only"
    )
    assert report["panic_regime_contract"]["allowed_runtime_apply"] is False


def test_live_market_panic_breadth_only_marks_watch_not_panic(monkeypatch, tmp_path):
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

    assert report["panic_state"] == "RECOVERY_WATCH"
    assert report["panic_regime_mode"] == "STABILIZING"
    assert report["policy"]["runtime_effect"] == "report_only_no_mutation"
    assert (
        report["microstructure_market_context"][
            "market_panic_breadth_risk_off_advisory"
        ]
        is True
    )
    assert report["microstructure_detector"]["panic_signal_count"] == 0
    assert report["market_weakness_observation"]["raw_state"] == "BROAD_WEAKNESS"
    assert report["market_weakness_observation"]["runtime_effect"] is False
    assert (
        "live market panic breadth risk_off advisory" in report["panic_state_reasons"]
    )
    assert (
        "market breadth risk-off watch without panic confirmation"
        in report["panic_state_reasons"]
    )


def test_panic_sell_state_from_five_stop_losses_in_30_minutes(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(tmp_path, _panic_rows())
    _write_market_regime(tmp_path, risk_state="RISK_OFF")
    _write_market_panic_breadth(tmp_path, risk_off=True)

    report = report_mod.build_panic_sell_defense_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:29:00"),
    )

    assert report["panic_state"] == "PANIC_SELL"
    assert report["panic_regime_mode"] == "PANIC_DETECTED"
    assert report["panic_metrics"]["current_30m_stop_loss_exit_count"] == 5
    assert report["panic_metrics"]["panic_by_stop_loss_count"] is True
    assert report["panic_metrics"]["rolling_30m_stop_loss_count_quantile"] == 0.95
    assert (
        report["panic_metrics"]["rolling_30m_stop_loss_count_quantile_threshold"] == 5
    )
    assert report["panic_metrics"]["rolling_30m_stop_loss_count_sample_ready"] is True
    assert (
        "panic thresholds breached with market/microstructure confirmation"
        in report["panic_state_reasons"]
    )
    assert (
        "candidate_entry_pre_submit_freeze"
        in report["panic_regime_contract"]["allowed_actions"]
    )
    assert "auto_sell" in report["panic_regime_contract"]["forbidden_uses"]
    freeze = next(
        item
        for item in report["canary_candidates"]
        if item["family"] == "panic_entry_freeze_guard"
    )
    assert freeze["status"] == "report_only_candidate"
    assert freeze["allowed_runtime_apply"] is False


def test_portfolio_stop_loss_cluster_without_market_confirmation_is_watch(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(tmp_path, _panic_rows())
    _write_market_regime(tmp_path, risk_state="NEUTRAL")
    _write_market_panic_breadth(tmp_path, risk_off=False)

    report = report_mod.build_panic_sell_defense_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:29:00"),
    )

    assert report["panic_state"] == "RECOVERY_WATCH"
    assert report["panic_regime_mode"] == "STABILIZING"
    assert report["panic_metrics"]["panic_by_stop_loss_count"] is True
    assert (
        report["panic_metrics"]["rolling_30m_stop_loss_count_quantile_threshold"] == 5
    )
    assert "portfolio stop-loss cluster observed" in report["panic_state_reasons"]
    assert (
        "portfolio stop-loss cluster unconfirmed by market/breadth context"
        in report["panic_state_reasons"]
    )
    assert (
        "portfolio-local stop-loss cluster watch without panic confirmation"
        in report["panic_state_reasons"]
    )


def test_stop_loss_count_quantile_requires_minimum_sample(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    rows = [
        _event(
            f"10:0{idx}:00",
            record_id=idx,
            fields={
                "exit_rule": "scalp_soft_stop_loss",
                "profit_rate": "-2.5",
                "actual_order_submitted": "true",
                "sell_order_no": f"S{idx:04d}",
            },
        )
        for idx in range(2)
    ]
    _write_events(tmp_path, rows)
    _write_market_regime(tmp_path, risk_state="NEUTRAL")
    _write_market_panic_breadth(tmp_path, risk_off=False)

    report = report_mod.build_panic_sell_defense_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:29:00"),
    )

    assert report["panic_state"] == "NORMAL"
    assert (
        report["panic_metrics"]["rolling_30m_stop_loss_count_quantile_threshold"] == 2
    )
    assert report["panic_metrics"]["rolling_30m_stop_loss_count_sample"] == 2
    assert report["panic_metrics"]["rolling_30m_stop_loss_count_sample_ready"] is False
    assert report["panic_metrics"]["panic_by_stop_loss_count"] is False


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


def test_unproven_exit_signal_is_not_real_panic_basis(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        [
            _event(
                f"10:{idx:02d}:00",
                record_id=idx,
                fields={"exit_rule": "scalp_hard_stop_pct", "profit_rate": "-2.5"},
            )
            for idx in range(5)
        ],
    )

    report = report_mod.build_panic_sell_defense_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:29:00"),
    )

    assert report["panic_state"] == "NORMAL"
    assert (
        report["panic_metrics"]["panic_decision_basis"]
        == "broker_confirmed_exit_identity_deduplicated"
    )
    assert report["panic_metrics"]["real_exit_provenance_required"] is True
    assert report["panic_metrics"]["real_exit_count"] == 0
    assert report["panic_metrics"]["non_real_exit_count"] == 5
    assert report["panic_metrics"]["unproven_exit_count"] == 5
    assert report["panic_metrics"]["stop_loss_exit_count"] == 0
    assert report["panic_metrics"]["panic_detected"] is False


def test_exit_signal_inherits_real_provenance_from_broker_sell_receipt(
    monkeypatch, tmp_path
):
    events = []
    for index in range(3):
        attempt_id = f"SCANPROM-real-{index}"
        events.extend(
            [
                _event(
                    f"10:{index:02d}:00",
                    record_id=100 + index,
                    fields={
                        "main_lifecycle_attempt_id": attempt_id,
                        "exit_rule": "scalp_hard_stop_pct",
                        "reason": "hard stop loss",
                        "profit_rate": -1.0,
                    },
                ),
                _event(
                    f"10:{index:02d}:01",
                    record_id=100 + index,
                    stage="sell_completed",
                    fields={
                        "main_lifecycle_attempt_id": attempt_id,
                        "order_no": f"SELL-{index}",
                        "profit_rate": -1.0,
                    },
                ),
            ]
        )
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(tmp_path, events)

    report = report_mod.build_panic_sell_defense_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:29:00"),
    )

    assert report["panic_metrics"]["real_exit_count"] == 3
    assert report["panic_metrics"]["non_real_exit_count"] == 0
    assert report["panic_metrics"]["stop_loss_exit_count"] == 3
    assert report["panic_metrics"]["unproven_exit_count"] == 0


def test_repeated_exit_signal_is_counted_once_per_broker_order(monkeypatch, tmp_path):
    attempt_id = "SCANPROM-repeated-real-exit"
    events = [
        _event(
            f"10:00:{index:02d}",
            record_id=100 + index,
            fields={
                "main_lifecycle_attempt_id": attempt_id,
                "exit_rule": "scalp_soft_stop_pct",
                "reason": "soft stop loss",
                "profit_rate": -0.8,
            },
        )
        for index in range(10)
    ]
    events.append(
        _event(
            "10:01:00",
            record_id=999,
            stage="sell_completed",
            fields={
                "main_lifecycle_attempt_id": attempt_id,
                "order_no": "SELL-ONE",
                "profit_rate": -0.8,
            },
        )
    )
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(tmp_path, events)

    report = report_mod.build_panic_sell_defense_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:29:00"),
    )

    panic = report["panic_metrics"]
    assert panic["raw_exit_signal_count"] == 10
    assert panic["real_exit_count"] == 1
    assert panic["stop_loss_exit_count"] == 1
    assert panic["duplicate_real_exit_signal_count"] == 9
    assert panic["duplicate_real_exit_signals_excluded_from_panic"] is True
    assert panic["exit_signal_partition_reconciled"] is True
    assert panic["panic_detected"] is False


def test_non_real_assumed_fill_marks_sparse_exit_signal_as_non_real(
    monkeypatch, tmp_path
):
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


def test_recovery_confirmed_keeps_probe_report_only_and_broker_forbidden(
    monkeypatch, tmp_path
):
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
    rebound = next(
        item
        for item in report["canary_candidates"]
        if item["family"] == "panic_rebound_probe"
    )
    assert rebound["status"] == "report_only_candidate"
    assert rebound["allowed_runtime_apply"] is False
    assert rebound["provenance_check_passed"] is True
    assert report["policy"]["report_only"] is True
    assert report["economics"]["cost_adjusted_ev_pct"] is None
    assert report["economics"]["daily_net_profit_krw"] is None
    assert report["panic_regime_contract"]["primary_decision_metric"] == "confirmed_panic_risk_regime_state"


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


def test_hard_emergency_exits_are_never_confirmation_eligible():
    hard_rows = [
        _event("10:00:00", fields={"exit_rule": "scalp_hard_stop_pct"}),
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
        tmp_path
        / "report"
        / "monitor_snapshots"
        / f"post_sell_feedback_{TARGET_DATE}.json",
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


def test_microstructure_detector_adds_report_only_risk_off_without_order_action(
    monkeypatch, tmp_path
):
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
    assert (
        report["microstructure_market_context"]["confirmed_risk_off_advisory"] is True
    )
    assert report["microstructure_market_context"]["market_confirms_risk_off"] is True
    assert micro["latest_signals"][0]["risk_off_advisory"] is True
    assert micro["policy"]["does_not_submit_orders"] is True
    assert micro["micro_cusum_observer"]["decision_authority"] == "source_quality_only"
    assert micro["micro_cusum_observer"]["consensus_pass_symbol_count"] == 1
    assert "order_submit" in micro["micro_cusum_observer"]["forbidden_uses"]
    assert all(
        item["allowed_runtime_apply"] is False for item in report["canary_candidates"]
    )
    markdown = report_mod.build_markdown(report)
    assert "duplicate_snapshot_skipped_count" in markdown
    assert "panic_active_confirmation_count" in markdown


def test_microstructure_risk_off_needs_market_or_breadth_confirmation(
    monkeypatch, tmp_path
):
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
    assert (
        "microstructure risk_off unconfirmed by market/breadth context"
        in report["panic_state_reasons"]
    )


def test_as_of_filters_exit_receipts_and_normalizes_market_time(monkeypatch):
    signal = _event("10:20:00", fields={"exit_rule": "scalp_soft_stop_loss"})
    signal["emitted_at"] = f"{TARGET_DATE}T01:20:00+00:00"
    receipt = _event("10:31:00", stage="sell_completed",
                     fields={"actual_order_submitted": True, "sell_order_no": "FUTURE"})
    other_day = _event("10:10:00")
    other_day["emitted_at"] = "2026-06-06T10:10:00+09:00"
    malformed = _event("10:10:00")
    malformed["emitted_at"] = "invalid"
    wrong_declared_day = _event("10:10:00")
    wrong_declared_day["emitted_date"] = "2026-06-06"
    monkeypatch.setattr(report_mod, "iter_jsonl", lambda _: iter(
        [signal, receipt, other_day, malformed, wrong_declared_day]))
    cutoff = datetime.fromisoformat(f"{TARGET_DATE}T10:30:00+09:00")
    retained, _, latest, contract = report_mod._stream_pipeline_inputs(
        report_mod.Path("unused"), as_of=cutoff, target_date=TARGET_DATE)
    assert retained == [signal]
    assert latest == datetime.fromisoformat(f"{TARGET_DATE}T10:20:00")
    assert contract["accepted_time_row_count"] == 1
    assert sum(contract["excluded_time_counts"].values()) == 4
    metrics = report_mod._summarize_exit_metrics(retained, as_of=report_mod._parse_dt(cutoff))
    assert metrics["real_exit_count"] == 0
    assert metrics["unproven_exit_count"] == 1


def test_mutable_market_cache_and_invalid_breadth_cannot_confirm_panic(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_market_panic_breadth(tmp_path)
    breadth = report_mod._market_panic_breadth_path(TARGET_DATE)
    body = json.loads(breadth.read_text())
    body["source_quality"]["status"] = "partial"
    _write_json(breadth, body)
    _write_json(tmp_path / "cache/market_regime_snapshot.json", {
        "timestamp": "2026-06-06T10:00:00", "risk_state": "RISK_OFF"})
    summary = report_mod._load_source_summary(
        TARGET_DATE, as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:30:00"))
    context = report_mod._microstructure_market_context(
        {"evaluated_symbol_count": 1, "risk_off_advisory_count": 1}, summary)
    assert context["confirmed_risk_off_advisory"] is False
    assert context["market_risk_state"] == "UNKNOWN"
    assert summary["market_regime"]["reported_risk_state"] == "RISK_OFF"
    assert summary["market_panic_breadth"]["market_weakness_observation"] == {}
    assert "market_panic_breadth:source_quality_not_ok" in context["threshold_contract"]["source_quality_blockers"]
    body["source_quality"]["status"] = "ok"
    body["as_of"] = f"{TARGET_DATE}T10:31:00+09:00"
    _write_json(breadth, body)
    assert report_mod._load_source_summary(
        TARGET_DATE, as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:30:00"))[
            "market_panic_breadth"]["time_status"] == "source_after_as_of"


def test_stale_or_real_positions_do_not_populate_recovery_baseline(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    position = {"stock_code": "000001", "buy_price": 10000, "curr_price": 10500,
                "actual_order_submitted": False, "broker_order_forbidden": True}
    _write_json(tmp_path / "runtime/swing_intraday_probe_state.json", {
        "updated_at": "2026-06-04T10:00:00", "active_positions": [position]})
    real = {**position, "actual_order_submitted": True, "broker_order_forbidden": False}
    _write_json(tmp_path / "runtime/scalp_live_simulator_state.json", {
        "active_positions": [position, real]})
    active = report_mod._summarize_active_recovery(
        TARGET_DATE, as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:30:00"))
    assert active["observed_active_positions"] == 3
    assert active["active_positions"] == 1
    assert active["excluded_active_positions"] == 2
    assert active["profit_sample"] == 1
    assert active["provenance_check"]["passed"] is False
    assert active["state_sources"]["swing_probe"]["time_status"] == "source_date_mismatch"


def test_zero_trade_feedback_rates_are_not_observation_samples(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    path = report_mod._post_sell_feedback_path(TARGET_DATE)
    _write_json(path, {"soft_stop_forensics": {
        "total_soft_stop": 0, "rebound_above_sell_rate": {"10m": 0.0, "20m": 0.0},
        "rebound_above_buy_rate": {"10m": 0.0, "20m": 0.0}}})
    result = report_mod._post_sell_recovery_metrics(
        TARGET_DATE, as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:30:00"))
    assert result["soft_stop_total"] == 0
    assert result["threshold_contract"]["threshold_mode"] == "insufficient_sample"
    for contract in result["threshold_contract"]["thresholds"].values():
        assert contract["sample_count"] == 0
        assert contract["sample_ready"] is False
        assert contract["dynamic_threshold_value"] is None


def test_feedback_from_after_cutoff_is_not_recovery_evidence(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_json(report_mod._post_sell_feedback_path(TARGET_DATE), {
        "meta": {"generated_at": f"{TARGET_DATE}T10:31:00"},
        "soft_stop_forensics": {"total_soft_stop": 5,
            "rebound_above_sell_rate": {"10m": 90.0, "20m": 95.0}}})
    result = report_mod._post_sell_recovery_metrics(
        TARGET_DATE, as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:30:00"))
    assert result["source_date_status"] == "source_timestamp_missing_or_after_as_of"
    assert result["soft_stop_total"] == 0
    assert result["threshold_contract"]["threshold_mode"] == "insufficient_sample"


def test_repeated_first_order_does_not_displace_second_order_profit():
    rows = [_event(f"10:0{index}:00", fields={
        "actual_order_submitted": True, "sell_order_no": order,
        "exit_rule": "scalp_soft_stop_loss", "profit_rate": profit})
        for index, (order, profit) in enumerate((("A", -1.0), ("A", -1.0), ("B", 2.0)))]
    metrics = report_mod._summarize_exit_metrics(
        rows, as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:30:00"))
    assert metrics["real_exit_count"] == 2
    assert metrics["duplicate_real_exit_signal_count"] == 1
    assert metrics["avg_exit_profit_rate_pct"] == 0.5


def test_missing_pipeline_is_source_unavailable_with_breadth_preserved(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_market_panic_breadth(tmp_path, risk_off=False)
    result = report_mod.build_panic_sell_defense_report(
        TARGET_DATE, as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:30:00"))
    assert result["input_streaming"]["source_status"] == "missing"
    assert result["analysis_status"] == "pipeline_source_unavailable"
    assert "pipeline_source:missing" in result["risk_regime_gate"]["source_quality_blockers"]
    assert result["market_weakness_observation"]["observation_id"] == "weakness-test-1"
