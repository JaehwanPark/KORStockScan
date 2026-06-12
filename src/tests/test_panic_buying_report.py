import json
from datetime import datetime

from src.engine import panic_buying_report as report_mod


TARGET_DATE = "2026-05-13"


def _event(
    hhmmss: str,
    *,
    stage: str = "orderbook_stability_observed",
    pipeline: str = "ENTRY_PIPELINE",
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


def _write_market_breadth(tmp_path, payload: dict) -> None:
    report_dir = tmp_path / "report" / "market_panic_breadth"
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / f"market_panic_breadth_{TARGET_DATE}.json").write_text(
        json.dumps(payload, ensure_ascii=False),
        encoding="utf-8",
    )


def _micro_event(hhmmss: str, *, close: float, volume: float = 100.0, buy: float = 52.0, sell: float = 48.0, **fields):
    stock_code = fields.pop("stock_code", "000001")
    record_id = fields.pop("record_id", 1)
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
    return _event(hhmmss, stock_code=stock_code, record_id=record_id, fields=payload)


def test_normal_state_without_panic_buying_threshold(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        [
            _micro_event("10:00:00", close=100.0),
            _micro_event("10:01:00", close=100.1),
            _micro_event("10:02:00", close=100.2),
        ],
    )

    report = report_mod.build_panic_buying_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:03:00"),
    )

    assert report["panic_buy_state"] == "NORMAL"
    assert report["panic_buy_regime_mode"] == "NORMAL"
    assert report["panic_buy_regime_contract"]["decision_authority"] == "source_quality_only"
    assert report["panic_buy_regime_contract"]["runtime_effect"] == "report_only_no_mutation"
    assert report["policy"]["runtime_effect"] == "report_only_no_mutation"
    assert report["panic_buy_metrics"]["panic_buy_active_count"] == 0


def test_microstructure_detector_adds_report_only_runner_flags(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        [
            _micro_event("10:00:00", close=100.0),
            _micro_event("10:01:00", close=100.0),
            _micro_event(
                "10:02:00",
                close=102.6,
                open=100.0,
                high=102.8,
                low=99.9,
                volume=430,
                buy=76,
                sell=24,
                best_bid=10250,
                best_ask=10260,
                bid_depth_l5=1300,
                ask_depth_l5=520,
                ask_depth_drop_ratio=0.48,
                bid_depth_support_ratio=1.30,
                panic_buy_spread_ratio=2.0,
                orderbook_micro_ofi_z=3.0,
                orderbook_micro_qi_ewma=0.68,
                orderbook_micro_state="bullish",
                orderbook_micro_ready=True,
                orderbook_micro_observer_healthy=True,
            ),
            _micro_event(
                "10:03:00",
                close=103.2,
                open=102.5,
                high=103.4,
                low=102.4,
                volume=440,
                buy=75,
                sell=25,
                best_bid=10310,
                best_ask=10320,
                bid_depth_l5=1350,
                ask_depth_l5=500,
                ask_depth_drop_ratio=0.50,
                bid_depth_support_ratio=1.35,
                panic_buy_spread_ratio=2.1,
                orderbook_micro_ofi_z=3.1,
                orderbook_micro_qi_ewma=0.70,
                orderbook_micro_state="bullish",
                orderbook_micro_ready=True,
                orderbook_micro_observer_healthy=True,
            ),
        ],
    )

    report = report_mod.build_panic_buying_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:04:00"),
    )

    micro = report["microstructure_detector"]
    assert report["panic_buy_state"] == "PANIC_BUY"
    assert report["panic_buy_regime_mode"] == "PANIC_BUY_CONTINUATION"
    assert report["risk_regime_gate_state"] == "source_quality_blocked"
    assert report["risk_regime_threshold_mode"] == "insufficient_sample"
    assert report["policy"]["runtime_effect"] == "report_only_no_mutation"
    assert "report_runner_hold_candidate" in report["panic_buy_regime_contract"]["allowed_actions"]
    assert "auto_buy" in report["panic_buy_regime_contract"]["forbidden_uses"]
    assert "full_market_sell" in report["panic_buy_regime_contract"]["forbidden_uses"]
    assert micro["panic_buy_active_count"] == 1
    assert micro["allow_tp_override_count"] == 1
    assert micro["allow_runner_count"] == 1
    assert micro["latest_signals"][0]["allow_tp_override"] is True
    assert micro["policy"]["does_not_submit_orders"] is True
    assert micro["micro_cusum_observer"]["decision_authority"] == "source_quality_only"
    assert micro["micro_cusum_observer"]["consensus_pass_symbol_count"] == 1
    assert "order_submit" in micro["micro_cusum_observer"]["forbidden_uses"]
    assert all(item["allowed_runtime_apply"] is False for item in report["canary_candidates"])
    assert report["canary_candidates"][0]["status"] == "hold_source_quality_blocked"


def test_microstructure_detector_carries_recent_micro_snapshot_to_price_row(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        [
            _micro_event("10:00:00", close=100.0, buy=0, sell=0),
            _micro_event("10:01:00", close=100.4, buy=0, sell=0),
            _event(
                "10:02:30",
                fields={
                    "exec_buy_ratio": 72,
                    "best_bid": 10180,
                    "best_ask": 10190,
                    "bid_depth_l5": 1500,
                    "ask_depth_l5": 450,
                    "ask_depth_drop_ratio": 0.52,
                    "bid_depth_support_ratio": 1.40,
                    "panic_buy_spread_ratio": 2.0,
                    "orderbook_micro_ofi_z": 3.2,
                    "orderbook_micro_qi_ewma": 0.72,
                    "orderbook_micro_state": "bullish",
                    "orderbook_micro_ready": True,
                    "orderbook_micro_observer_healthy": True,
                },
            ),
            _event(
                "10:03:00",
                fields={
                    "curr_price": 102.2,
                    "open": 100.8,
                    "high": 102.4,
                    "low": 100.8,
                    "volume": 430,
                },
            ),
        ],
    )

    report = report_mod.build_panic_buying_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:04:00"),
    )

    micro = report["microstructure_detector"]
    latest = micro["latest_signals"][0]["metrics"]
    assert micro["missing_orderbook_count"] == 0
    assert micro["missing_trade_aggressor_count"] == 0
    assert micro["carried_orderbook_snapshot_count"] == 1
    assert micro["carried_trade_aggressor_snapshot_count"] == 1
    assert latest["orderbook_carried_forward"] is True
    assert latest["trade_flow_carried_forward"] is True
    assert latest["orderbook_age_sec"] == 30.0
    assert latest["trade_flow_age_sec"] == 30.0


def test_panic_buying_report_includes_market_breadth_context(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        [
            _micro_event("10:00:00", close=100.0),
            _micro_event("10:01:00", close=101.5, buy=80, sell=20),
            _micro_event("10:02:00", close=102.8, buy=82, sell=18),
        ],
    )
    _write_market_breadth(
        tmp_path,
        {
            "as_of": f"{TARGET_DATE}T10:02:00",
            "source_quality": {"status": "ok"},
            "panic_breadth": {
                "risk_on_advisory": True,
                "risk_off_advisory": False,
                "industry_breadth": {"up_ratio_pct": 76.0},
                "stock_breadth": {"max_rise_ratio_pct": 81.0},
                "risk_on_reasons": ["market_index_intraday_rise"],
            },
        },
    )

    report = report_mod.build_panic_buying_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:03:00"),
    )

    context = report["market_breadth_context"]
    assert context["decision_authority"] == "source_quality_only"
    assert context["market_panic_breadth_risk_on_advisory"] is True
    assert context["market_panic_breadth_risk_off_advisory"] is False
    assert context["market_panic_breadth_source_quality_status"] == "ok"
    assert context["market_panic_buy_interpretation"] == "market_risk_on_only"
    assert "order_submit" in context["forbidden_uses"]


def test_tp_counterfactual_does_not_create_order_decision(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        [
            _event(
                "10:00:00",
                pipeline="HOLDING_PIPELINE",
                stage="exit_signal",
                fields={
                    "exit_rule": "scalp_trailing_take_profit",
                    "profit_rate": "1.2",
                    "peak_profit": "1.8",
                    "actual_order_submitted": "True",
                },
            )
        ],
    )

    report = report_mod.build_panic_buying_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:01:00"),
    )

    tp = report["tp_counterfactual_summary"]
    assert tp["tp_like_exit_count"] == 1
    assert tp["trailing_winner_count"] == 1
    assert tp["candidate_context_count"] == 1
    assert tp["real_exit_count"] == 1
    assert tp["unproven_exit_count"] == 0
    assert tp["real_exit_provenance_required"] is True
    assert tp["policy"]["runtime_effect"] == "counterfactual_only_no_order_change"
    assert report["canary_candidates"][0]["family"] == "panic_buy_runner_tp_canary"
    assert report["canary_candidates"][0]["allowed_runtime_apply"] is False


def test_holding_rows_are_excluded_from_panic_buy_micro_detector_but_kept_for_tp(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        [
            _event(
                "10:00:00",
                pipeline="HOLDING_PIPELINE",
                stage="exit_signal",
                fields={
                    "curr_price": "10200",
                    "open": "10000",
                    "high": "10300",
                    "low": "9900",
                    "volume": "500",
                    "buy_exec_volume": "420",
                    "sell_exec_volume": "80",
                    "best_bid": "10190",
                    "best_ask": "10200",
                    "orderbook_micro_ofi_z": "3.4",
                    "panic_buy_spread_ratio": "2.1",
                    "exit_rule": "scalp_trailing_take_profit",
                    "profit_rate": "1.2",
                    "peak_profit": "1.8",
                    "actual_order_submitted": "true",
                },
            )
        ],
    )

    report = report_mod.build_panic_buying_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:01:00"),
    )

    micro = report["microstructure_detector"]
    tp = report["tp_counterfactual_summary"]
    assert micro["evaluated_symbol_count"] == 0
    assert micro["panic_buy_active_count"] == 0
    assert micro["metrics"]["max_panic_buy_score"] == 0.0
    assert micro["input_provenance"]["input_universe"] == "entry_observation_only"
    assert micro["input_provenance"]["excluded_holding_row_count"] == 1
    assert micro["input_provenance"]["excluded_exit_sell_row_count"] == 1
    assert tp["real_exit_count"] == 1
    assert tp["tp_like_exit_count"] == 1
    assert tp["candidate_context_count"] == 1


def test_entry_rows_remain_panic_buy_micro_detector_inputs(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        [
            _micro_event("10:00:00", close=100.0),
            _micro_event("10:01:00", close=100.0),
            _micro_event(
                "10:02:00",
                close=102.6,
                open=100.0,
                high=102.8,
                low=99.9,
                volume=430,
                buy=76,
                sell=24,
                best_bid=10250,
                best_ask=10260,
                bid_depth_l5=1300,
                ask_depth_l5=520,
                ask_depth_drop_ratio=0.48,
                bid_depth_support_ratio=1.30,
                panic_buy_spread_ratio=2.0,
                orderbook_micro_ofi_z=3.0,
                orderbook_micro_state="bullish",
                orderbook_micro_ready=True,
                orderbook_micro_observer_healthy=True,
            ),
            _micro_event(
                "10:03:00",
                close=103.2,
                open=102.5,
                high=103.4,
                low=102.4,
                volume=440,
                buy=75,
                sell=25,
                best_bid=10310,
                best_ask=10320,
                bid_depth_l5=1350,
                ask_depth_l5=500,
                ask_depth_drop_ratio=0.50,
                bid_depth_support_ratio=1.35,
                panic_buy_spread_ratio=2.1,
                orderbook_micro_ofi_z=3.1,
                orderbook_micro_state="bullish",
                orderbook_micro_ready=True,
                orderbook_micro_observer_healthy=True,
            ),
        ],
    )

    report = report_mod.build_panic_buying_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:04:00"),
    )

    micro = report["microstructure_detector"]
    assert micro["input_provenance"]["excluded_event_count"] == 0
    assert micro["evaluated_symbol_count"] == 1
    assert micro["panic_buy_active_count"] == 1
    assert report["panic_buy_state"] == "PANIC_BUY"


def test_entry_rows_with_order_provenance_are_excluded_from_micro_detector(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        [
            _micro_event(
                "10:00:00",
                close=102.0,
                actual_order_submitted="true",
                broker_order_id="12345",
            ),
            {
                **_micro_event("10:01:00", close=103.0),
                "actual_order_submitted": True,
                "broker_order_id": "top-level-1",
            },
        ],
    )

    report = report_mod.build_panic_buying_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:02:00"),
    )

    micro = report["microstructure_detector"]
    assert micro["evaluated_symbol_count"] == 0
    assert micro["input_provenance"]["excluded_reason_counts"]["actual_order_submitted"] == 2


def test_micro_input_provenance_respects_as_of_cutoff(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        [
            _micro_event("10:00:00", close=100.0),
            _micro_event("10:01:00", close=100.1),
            _micro_event("10:02:00", close=100.2),
            _micro_event("10:03:00", close=105.0),
        ],
    )

    report = report_mod.build_panic_buying_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:02:00"),
    )

    micro = report["microstructure_detector"]
    assert micro["input_provenance"]["input_event_count"] == 3
    assert micro["input_provenance"]["future_event_count"] == 1
    assert micro["evaluated_symbol_count"] == 1


def test_panic_buy_regime_mode_maps_exhaustion_and_cooldown():
    assert report_mod._panic_buy_regime_mode(
        "EXHAUSTION_WATCH",
        {"force_exit_runner_count": 0, "allow_runner_count": 0, "latest_signals": []},
    ) == "PANIC_BUY_EXHAUSTION"
    assert report_mod._panic_buy_regime_mode(
        "BUYING_EXHAUSTED",
        {
            "force_exit_runner_count": 1,
            "allow_runner_count": 0,
            "latest_signals": [{"internal_state": "BUYING_EXHAUSTED"}],
        },
    ) == "PANIC_BUY_EXHAUSTION"
    assert report_mod._panic_buy_regime_mode(
        "BUYING_EXHAUSTED",
        {
            "force_exit_runner_count": 0,
            "allow_runner_count": 0,
            "latest_signals": [{"internal_state": "COOLDOWN"}],
        },
    ) == "COOLDOWN"


def test_tp_counterfactual_propagates_non_real_sibling_to_sparse_exit(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        [
            _event(
                "10:00:00",
                pipeline="HOLDING_PIPELINE",
                stage="exit_signal",
                record_id=0,
                stock_code="042700",
                fields={
                    "exit_rule": "scalp_trailing_take_profit",
                    "profit_rate": "1.2",
                    "peak_profit": "1.8",
                },
            ),
            _event(
                "10:00:01",
                pipeline="HOLDING_PIPELINE",
                stage="scalp_sim_sell_order_assumed_filled",
                record_id=0,
                stock_code="042700",
                fields={
                    "exit_rule": "scalp_trailing_take_profit",
                    "profit_rate": "1.2",
                    "peak_profit": "1.8",
                    "simulated_order": "true",
                    "actual_order_submitted": "false",
                    "simulation_book": "scalp_ai_buy_all",
                },
            ),
        ],
    )

    report = report_mod.build_panic_buying_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:01:00"),
    )

    tp = report["tp_counterfactual_summary"]
    assert tp["real_exit_count"] == 0
    assert tp["non_real_exit_count"] == 2
    assert tp["unproven_exit_count"] == 0
    assert tp["tp_like_exit_count"] == 0
    assert tp["non_real_tp_like_exit_count"] == 2


def test_tp_counterfactual_requires_real_order_provenance(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    _write_events(
        tmp_path,
        [
            _event(
                "10:00:00",
                pipeline="HOLDING_PIPELINE",
                stage="exit_signal",
                fields={
                    "exit_rule": "scalp_trailing_take_profit",
                    "profit_rate": "1.2",
                    "peak_profit": "1.8",
                },
            )
        ],
    )

    report = report_mod.build_panic_buying_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:01:00"),
    )

    tp = report["tp_counterfactual_summary"]
    assert tp["real_exit_count"] == 0
    assert tp["unproven_exit_count"] == 1
    assert tp["tp_like_exit_count"] == 0
    assert tp["candidate_context_count"] == 0


def test_confirmed_panic_buy_gate_requires_market_and_sample_ready(monkeypatch, tmp_path):
    monkeypatch.setattr(report_mod, "DATA_DIR", tmp_path)
    rows = []
    for idx in range(8):
        code = f"{idx + 1:06d}"
        rows.extend(
            [
                _micro_event(
                    "10:00:00",
                    close=100.0,
                    stock_code=code,
                    record_id=idx + 1,
                    best_bid=9900,
                    best_ask=10000,
                    bid_depth_l5=1000,
                    ask_depth_l5=1000,
                    orderbook_micro_ready=True,
                    orderbook_micro_observer_healthy=True,
                ),
                _micro_event(
                    "10:01:00",
                    close=100.0,
                    stock_code=code,
                    record_id=idx + 1,
                    best_bid=9900,
                    best_ask=10000,
                    bid_depth_l5=1000,
                    ask_depth_l5=1000,
                    orderbook_micro_ready=True,
                    orderbook_micro_observer_healthy=True,
                ),
            ]
        )
    rows.extend(
        [
            _micro_event("10:02:00", close=102.6, open=100.0, high=102.8, low=99.9, volume=430, buy=76, sell=24, stock_code="000001", record_id=1, best_bid=10250, best_ask=10260, bid_depth_l5=1300, ask_depth_l5=520, ask_depth_drop_ratio=0.48, bid_depth_support_ratio=1.30, panic_buy_spread_ratio=2.0, orderbook_micro_ofi_z=3.0, orderbook_micro_ready=True, orderbook_micro_observer_healthy=True),
            _micro_event("10:03:00", close=103.2, open=102.5, high=103.4, low=102.4, volume=440, buy=75, sell=25, stock_code="000001", record_id=1, best_bid=10310, best_ask=10320, bid_depth_l5=1350, ask_depth_l5=500, ask_depth_drop_ratio=0.50, bid_depth_support_ratio=1.35, panic_buy_spread_ratio=2.1, orderbook_micro_ofi_z=3.1, orderbook_micro_ready=True, orderbook_micro_observer_healthy=True),
            _event(
                "10:03:30",
                pipeline="HOLDING_PIPELINE",
                stage="exit_signal",
                record_id=100,
                stock_code="000001",
                fields={
                    "exit_rule": "scalp_trailing_take_profit",
                    "profit_rate": "1.2",
                    "actual_order_submitted": "true",
                },
            ),
        ]
    )
    _write_events(tmp_path, rows)
    _write_market_breadth(
        tmp_path,
        {
            "as_of": f"{TARGET_DATE}T10:03:00",
            "source_quality": {"status": "ok"},
            "panic_breadth": {"risk_on_advisory": True, "risk_off_advisory": False},
        },
    )

    report = report_mod.build_panic_buying_report(
        TARGET_DATE,
        as_of=datetime.fromisoformat(f"{TARGET_DATE}T10:04:00"),
    )

    assert report["risk_regime_gate_state"] == "confirmed_panic_buy"
    assert report["risk_regime_threshold_mode"] == "dynamic_quantile"
    assert report["canary_candidates"][0]["status"] == "report_only_candidate"
