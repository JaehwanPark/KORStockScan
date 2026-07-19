import json
from datetime import datetime
from pathlib import Path

import pytest

from src.engine.scalping.opening_rotation import POSITION_TAG
from src.engine.scalping import opening_rotation_backtest as backtest
from src.engine.scalping.opening_rotation_backtest import build_report, write_report


def _write_events(root: Path, target_date: str, rows: list[dict]) -> None:
    root.mkdir(parents=True, exist_ok=True)
    path = root / f"pipeline_events_{target_date}.jsonl"
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _event(
    stage: str, at: str, *, record_id: int = 1, fields=None, pipeline="ENTRY_PIPELINE"
):
    return {
        "pipeline": pipeline,
        "stage": stage,
        "stock_code": "123456",
        "stock_name": "TEST",
        "record_id": record_id,
        "fields": fields or {},
        "emitted_at": at,
    }


def _complete_fields(price: int) -> dict:
    return {
        "scanner_promotion_id": "SCAN-1",
        "source_signature": "PRICE_JUMP_START,VOLUME_SURGE_POSITIVE",
        "target_position_tag": "SCANNER",
        "fluctuation": 3.2,
        "curr_price": price,
        "quote_age_ms": 100,
        "quote_stale": False,
        "tick_context_stale": False,
        "tick_context_quality": "fresh_computed",
        "tick_aggressor_pressure_usable": True,
        "spread_bp": 8,
        "buy_pressure_10t": 64,
        "tick_aggressor_trusted_count": 8,
        "tick_acceleration_ratio": 1.35,
        "price_change_10t_pct": 0.12,
        "volume_ratio_pct": 125,
        "micro_vwap_available": True,
        "curr_vs_micro_vwap_bp": 24,
        "microstructure_reaction_ask_sweep_score": 72,
        "microstructure_reaction_post_sweep_hold_score": 67,
        "microstructure_reaction_bid_replenishment_score": 61,
        "microstructure_reaction_wall_replenishment_risk_score": 42,
        "microstructure_reaction_vi_proximity_risk": 18,
    }


def _real_completion_fields(**overrides) -> dict:
    fields = {
        "sell_price": 10_150,
        "profit_rate": 1.27,
        "realized_pnl_krw": 50_662,
        "position_tag": POSITION_TAG,
        "trade_status": "COMPLETED",
        "actual_order_submitted": True,
        "broker_order_forbidden": False,
        "metric_role": "exact_real_trade_performance_source",
        "decision_authority": "real_execution_observation_only",
        "window_policy": "clean_baseline_completed_trade_event_time",
        "sample_floor": "consumer_owned_no_direct_runtime_authority",
        "primary_decision_metric": "net_profit_rate_and_realized_pnl_krw",
        "source_quality_gate": (
            "completed_db_status_valid_net_profit_real_broker_receipt"
        ),
        "allowed_runtime_apply": False,
        "forbidden_uses": (
            "live_auto_promotion|runtime_apply_bridge|threshold_mutation"
        ),
    }
    fields.update(overrides)
    return fields


def _qualification_fields(price: int = 10_000, **overrides) -> dict:
    fields = _complete_fields(price)
    fields.update(
        {
            "reason": "pullback_reacceleration_confirmed",
            "metric_role": "bounded_tunable_live_strategy",
            "decision_authority": "operator_requested_real_opening_rotation_1pct",
            "window_policy": (
                "same_day_preopen_configured_observation_and_entry_window_kst"
            ),
            "sample_floor": "not_applicable_operator_requested_live_runtime",
            "primary_decision_metric": (
                "cost_aware_net_profit_rate_and_realized_pnl_krw"
            ),
            "source_quality_gate": (
                "fresh_quote_trusted_ticks_orderbook_and_minute_candles"
            ),
            "allowed_runtime_apply": True,
            "forbidden_uses": "ai_score_submit_permission|broker_guard_bypass",
        }
    )
    fields.update(overrides)
    return fields


def test_strict_legacy_replay_qualifies_only_complete_sequence(tmp_path):
    events_dir = tmp_path / "events"
    post_sell_dir = tmp_path / "post_sell"
    _write_events(
        events_dir,
        "2026-07-13",
        [
            _event(
                "scalping_scanner_fast_precheck",
                "2026-07-13T09:10:00",
                fields=_complete_fields(10_100),
            ),
            _event(
                "scalping_scanner_fast_precheck",
                "2026-07-13T09:10:10",
                fields=_complete_fields(10_030),
            ),
            _event(
                "scalping_scanner_fast_precheck",
                "2026-07-13T09:10:20",
                fields=_complete_fields(10_040),
            ),
            _event(
                "scalping_scanner_fast_precheck",
                "2026-07-13T09:10:30",
                fields=_complete_fields(10_050),
            ),
        ],
    )

    report = build_report(
        start_date="2026-07-13",
        end_date="2026-07-13",
        events_dir=events_dir,
        post_sell_dir=post_sell_dir,
    )

    assert report["summary"]["legacy_complete_packet_count"] == 3
    assert report["summary"]["legacy_replay_qualified_count"] == 1
    assert (
        report["legacy_replay_qualified_rows"][0]["outcome_status"]
        == "forward_price_path_unavailable"
    )
    assert report["real_performance"]["equal_weight_avg_profit_pct"] is None


def test_legacy_scanner_row_without_promotion_id_is_not_prefiltered_out(tmp_path):
    events_dir = tmp_path / "events"
    fields = _complete_fields(10_000)
    fields.pop("scanner_promotion_id")
    _write_events(
        events_dir,
        "2026-07-13",
        [
            _event(
                "scalping_scanner_fast_precheck",
                "2026-07-13T09:20:00",
                fields=fields,
            )
        ],
    )

    report = build_report(
        start_date="2026-07-13",
        end_date="2026-07-13",
        events_dir=events_dir,
        post_sell_dir=tmp_path / "post_sell",
    )

    assert report["summary"]["legacy_scanner_event_count"] == 1
    assert report["summary"]["legacy_complete_packet_count"] == 1


def test_incomplete_legacy_packet_is_source_quality_only(tmp_path):
    events_dir = tmp_path / "events"
    fields = _complete_fields(10_000)
    fields.pop("price_change_10t_pct")
    _write_events(
        events_dir,
        "2026-07-13",
        [
            _event(
                "scalping_scanner_fast_precheck", "2026-07-13T09:20:00", fields=fields
            )
        ],
    )

    report = build_report(
        start_date="2026-07-13",
        end_date="2026-07-13",
        events_dir=events_dir,
        post_sell_dir=tmp_path / "post_sell",
    )

    assert report["summary"]["legacy_complete_packet_count"] == 0
    assert report["source_quality"]["missing_field_counts"]["price_change_10t_pct"] == 1
    assert report["summary"]["performance_evaluable"] is False


def test_incomplete_exact_qualification_is_rejected_by_source_quality(tmp_path):
    events_dir = tmp_path / "events"
    _write_events(
        events_dir,
        "2026-07-20",
        [
            _event(
                "opening_rotation_1pct_qualified",
                "2026-07-20T09:10:00",
                fields={"curr_price": 10_000},
            )
        ],
    )

    report = build_report(
        start_date="2026-07-20",
        end_date="2026-07-20",
        events_dir=events_dir,
        post_sell_dir=tmp_path / "post_sell",
    )

    assert report["summary"]["exact_qualification_count"] == 1
    assert report["summary"]["exact_qualification_source_quality_rejected_count"] == 1
    assert report["exact_trade_rows"][0]["qualified"] is False


def test_exact_runtime_lifecycle_reports_real_pnl_and_daily_target(tmp_path):
    events_dir = tmp_path / "events"
    _write_events(
        events_dir,
        "2026-07-20",
        [
            _event(
                "opening_rotation_1pct_qualified",
                "2026-07-20T09:10:00",
                fields=_qualification_fields(),
            ),
            _event(
                "order_bundle_submitted",
                "2026-07-20T09:10:01",
                fields={"actual_order_submitted": True},
            ),
            _event(
                "holding_started",
                "2026-07-20T09:10:02",
                pipeline="HOLDING_PIPELINE",
                fields={
                    "buy_price": 10_000,
                    "buy_qty": 400,
                    "position_tag": POSITION_TAG,
                    "actual_order_submitted": True,
                    "broker_order_forbidden": False,
                },
            ),
            _event(
                "opening_rotation_1pct_exit_signal",
                "2026-07-20T09:11:00",
                pipeline="HOLDING_PIPELINE",
                fields={"exit_rule": "opening_rotation_1pct_take_profit"},
            ),
            _event(
                "sell_completed",
                "2026-07-20T09:11:01",
                pipeline="HOLDING_PIPELINE",
                fields=_real_completion_fields(),
            ),
        ],
    )

    report = build_report(
        start_date="2026-07-20",
        end_date="2026-07-20",
        events_dir=events_dir,
        post_sell_dir=tmp_path / "post_sell",
    )

    assert report["status"] == "exact_real_performance_available"
    assert report["real_performance"]["completed_trade_count"] == 1
    assert report["real_performance"]["realized_pnl_krw"] == 50_662
    assert report["real_performance"]["daily_target_hit_days"] == 1
    assert report["real_performance"]["daily_target_hit_rate_pct"] == 100.0
    assert report["real_performance"]["equal_weight_avg_profit_pct"] == 1.27
    assert report["metric_role"] == "descriptive_exact_real_trade_performance"


def test_daily_target_denominator_includes_source_session_without_trade(tmp_path):
    events_dir = tmp_path / "events"
    _write_events(
        events_dir,
        "2026-07-20",
        [
            _event(
                "opening_rotation_1pct_qualified",
                "2026-07-20T09:10:00",
                fields=_qualification_fields(),
            ),
            _event(
                "holding_started",
                "2026-07-20T09:10:02",
                pipeline="HOLDING_PIPELINE",
                fields={
                    "buy_price": 10_000,
                    "buy_qty": 400,
                    "position_tag": POSITION_TAG,
                    "actual_order_submitted": True,
                    "broker_order_forbidden": False,
                },
            ),
            _event(
                "sell_completed",
                "2026-07-20T09:11:01",
                pipeline="HOLDING_PIPELINE",
                fields=_real_completion_fields(),
            ),
        ],
    )
    _write_events(events_dir, "2026-07-21", [])

    report = build_report(
        start_date="2026-07-20",
        end_date="2026-07-21",
        events_dir=events_dir,
        post_sell_dir=tmp_path / "post_sell",
    )

    performance = report["real_performance"]
    assert performance["evaluated_day_count"] == 2
    assert performance["daily_target_hit_rate_pct"] == 50.0
    assert performance["daily_realized_pnl_krw"]["2026-07-21"] == 0


def test_completion_forbidden_for_ev_is_excluded_from_performance(tmp_path):
    events_dir = tmp_path / "events"
    _write_events(
        events_dir,
        "2026-07-20",
        [
            _event(
                "opening_rotation_1pct_qualified",
                "2026-07-20T09:10:00",
                fields=_qualification_fields(),
            ),
            _event(
                "holding_started",
                "2026-07-20T09:10:02",
                pipeline="HOLDING_PIPELINE",
                fields={
                    "buy_price": 10_000,
                    "buy_qty": 400,
                    "position_tag": POSITION_TAG,
                    "actual_order_submitted": True,
                    "broker_order_forbidden": False,
                },
            ),
            _event(
                "sell_completed",
                "2026-07-20T09:11:01",
                pipeline="HOLDING_PIPELINE",
                fields=_real_completion_fields(forbidden_uses="EV|rolling|MTD"),
            ),
        ],
    )

    report = build_report(
        start_date="2026-07-20",
        end_date="2026-07-20",
        events_dir=events_dir,
        post_sell_dir=tmp_path / "post_sell",
    )

    assert report["summary"]["exact_completed_trade_count"] == 0
    assert report["summary"]["completion_source_quality_rejected_count"] == 1
    assert (
        report["source_quality"]["reason_counts"]["producer_contract_forbids_ev"] == 1
    )


def test_observed_without_qualification_cannot_be_counted_as_strategy_trade(tmp_path):
    events_dir = tmp_path / "events"
    _write_events(
        events_dir,
        "2026-07-20",
        [
            _event(
                "opening_rotation_1pct_observed",
                "2026-07-20T09:10:00",
                fields={"curr_price": 10_000},
            ),
            _event(
                "holding_started",
                "2026-07-20T09:10:02",
                pipeline="HOLDING_PIPELINE",
                fields={
                    "buy_price": 10_000,
                    "buy_qty": 400,
                    "position_tag": POSITION_TAG,
                    "actual_order_submitted": True,
                    "broker_order_forbidden": False,
                },
            ),
            _event(
                "sell_completed",
                "2026-07-20T09:11:01",
                pipeline="HOLDING_PIPELINE",
                fields=_real_completion_fields(),
            ),
        ],
    )

    report = build_report(
        start_date="2026-07-20",
        end_date="2026-07-20",
        events_dir=events_dir,
        post_sell_dir=tmp_path / "post_sell",
    )

    assert report["summary"]["exact_completed_trade_count"] == 0
    assert (
        report["source_quality"]["reason_counts"][
            "opening_rotation_qualification_missing"
        ]
        == 1
    )


def test_full_and_partial_fill_ev_are_not_merged(tmp_path):
    events_dir = tmp_path / "events"
    rows = []
    for record_id, fill_quality, profit_rate, pnl in (
        (1, "FULL_FILL", 1.2, 40_000),
        (2, "PARTIAL_FILL", -0.4, -10_000),
    ):
        rows.extend(
            [
                _event(
                    "opening_rotation_1pct_qualified",
                    "2026-07-20T09:10:00",
                    record_id=record_id,
                    fields=_qualification_fields(),
                ),
                _event(
                    "holding_started",
                    "2026-07-20T09:10:02",
                    record_id=record_id,
                    pipeline="HOLDING_PIPELINE",
                    fields={
                        "buy_price": 10_000,
                        "buy_qty": 400,
                        "position_tag": POSITION_TAG,
                        "fill_quality": fill_quality,
                        "actual_order_submitted": True,
                        "broker_order_forbidden": False,
                    },
                ),
                _event(
                    "sell_completed",
                    "2026-07-20T09:11:01",
                    record_id=record_id,
                    pipeline="HOLDING_PIPELINE",
                    fields=_real_completion_fields(
                        profit_rate=profit_rate,
                        realized_pnl_krw=pnl,
                    ),
                ),
            ]
        )
    _write_events(events_dir, "2026-07-20", rows)

    report = build_report(
        start_date="2026-07-20",
        end_date="2026-07-20",
        events_dir=events_dir,
        post_sell_dir=tmp_path / "post_sell",
    )

    performance = report["real_performance"]
    assert performance["completed_trade_count"] == 2
    assert performance["combined_fill_quality_ev_suppressed"] is True
    assert performance["equal_weight_avg_profit_pct"] is None
    assert (
        performance["performance_by_fill_quality"]["FULL_FILL"][
            "equal_weight_avg_profit_pct"
        ]
        == 1.2
    )
    assert (
        performance["performance_by_fill_quality"]["PARTIAL_FILL"][
            "equal_weight_avg_profit_pct"
        ]
        == -0.4
    )


def test_simulated_fill_is_never_counted_as_real_performance(tmp_path):
    events_dir = tmp_path / "events"
    _write_events(
        events_dir,
        "2026-07-20",
        [
            _event(
                "opening_rotation_1pct_qualified",
                "2026-07-20T09:10:00",
                fields=_qualification_fields(),
            ),
            _event(
                "holding_started",
                "2026-07-20T09:10:02",
                pipeline="HOLDING_PIPELINE",
                fields={
                    "buy_price": 10_000,
                    "buy_qty": 400,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
            ),
            _event(
                "sell_completed",
                "2026-07-20T09:11:01",
                pipeline="HOLDING_PIPELINE",
                fields={
                    "sell_price": 10_150,
                    "profit_rate": 1.27,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                },
            ),
        ],
    )

    report = build_report(
        start_date="2026-07-20",
        end_date="2026-07-20",
        events_dir=events_dir,
        post_sell_dir=tmp_path / "post_sell",
    )

    assert report["summary"]["exact_completed_trade_count"] == 0
    assert report["real_performance"]["realized_pnl_krw"] == 0
    assert report["exact_trade_rows"][0]["execution_lane"] == "sim_probe_or_untagged"


def test_post_sell_inventory_keeps_sim_and_real_separate(tmp_path):
    events_dir = tmp_path / "events"
    post_sell_dir = tmp_path / "post_sell"
    _write_events(events_dir, "2026-07-20", [])
    post_sell_dir.mkdir()
    (post_sell_dir / "post_sell_evaluations_2026-07-20.jsonl").write_text(
        json.dumps({"position_tag": "SCANNER"}) + "\n", encoding="utf-8"
    )
    (post_sell_dir / "sim_post_sell_evaluations_2026-07-20.jsonl").write_text(
        json.dumps({"position_tag": "SCANNER"}) + "\n", encoding="utf-8"
    )

    report = build_report(
        start_date="2026-07-20",
        end_date="2026-07-20",
        events_dir=events_dir,
        post_sell_dir=post_sell_dir,
    )

    inventory = report["auxiliary_post_sell_inventory"]
    assert inventory["real_evaluation_count"] == 1
    assert inventory["sim_evaluation_count"] == 1
    assert inventory["legacy_rows_used_as_exact_outcomes"] == 0


def test_write_report_creates_json_and_markdown(tmp_path):
    report = {
        "start_date": "2026-07-13",
        "end_date": "2026-07-16",
        "status": "source_quality_limited_no_completed_opening_rotation_trade",
        "summary": {},
        "real_performance": {},
        "source_quality": {},
        "auxiliary_post_sell_inventory": {},
    }
    json_path, md_path = write_report(report, tmp_path)
    assert (
        json.loads(json_path.read_text(encoding="utf-8"))["status"] == report["status"]
    )
    assert json_path.name.endswith("_legacy.json")
    markdown = md_path.read_text(encoding="utf-8")
    assert "OPENING_ROTATION_1PCT" in markdown
    assert "평가 불가" in markdown


@pytest.mark.parametrize(
    "policy",
    [
        {"enabled": False, "clean_tuning_baseline_ts_kst": "2026-06-04T14:29:09+09:00"},
        {"enabled": True, "clean_tuning_baseline_ts_kst": "invalid"},
    ],
)
def test_clean_baseline_policy_fails_closed(monkeypatch, tmp_path, policy):
    monkeypatch.setattr(backtest, "clean_baseline_policy", lambda: policy)

    with pytest.raises(ValueError):
        build_report(
            start_date="2026-07-20",
            end_date="2026-07-20",
            events_dir=tmp_path / "events",
            post_sell_dir=tmp_path / "post_sell",
        )


def test_report_identity_pins_config_and_versioned_filename(tmp_path):
    events_dir = tmp_path / "events"
    _write_events(events_dir, "2026-07-20", [])
    report = build_report(
        start_date="2026-07-20",
        end_date="2026-07-20",
        events_dir=events_dir,
        post_sell_dir=tmp_path / "post_sell",
    )

    identity = report["report_identity"]
    assert identity["schema_version"] == 2
    assert identity["entry_config"]["entry_end"] == "10:30:00"
    assert len(identity["config_fingerprint"]) == 12

    json_path, _ = write_report(report, tmp_path / "report")
    assert identity["config_fingerprint"] in json_path.name
