import gzip
import json
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from src.engine.monitoring import (
    machine_microstructure_attribution as attribution_module,
)
from src.engine.monitoring.machine_microstructure_attribution import (
    FAST_LIFECYCLE_OBJECTIVE_FOLLOWUP_ID,
    OBJECTIVE_CANDIDATE_BINDING_SCHEMA,
    OBJECTIVE_FOLLOWUP_METRIC_CONTRACT,
    _episode_exit_outcome_provenance,
    _finite_float,
    _fast_lifecycle_objective_followup,
    _anchor_result,
    _dynamic_confirmation_replay,
    _entry_checkpoint_ask_depletion_feature,
    _episode_inventory,
    _lifecycle_objective_summary,
    _micro_entry_confirmation_summary,
    _micro_context,
    _runtime_registration_receipt_binding,
    _rolling_source_contract_recovery,
    _timestamp_regression_row_quarantine_validation,
    _validate_stream_row,
    archive_exact_date_canary_snapshot,
    build_report as build_attribution_report,
    load_prior_owner_diagnostic,
    resolve_completed_machine_target_date,
    write_report,
)
from src.engine.scalping.micro_reversion.collection_targets import (
    build_collection_targets,
)
from src.trading.market.comparison_cost import comparison_cost_contract

KST = ZoneInfo("Asia/Seoul")


def test_finite_float_rejects_boolean_contract_values():
    assert _finite_float(True) is None
    assert _finite_float(False) is None


def test_realized_episode_exit_with_unknown_source_is_not_target_fill():
    provenance = _episode_exit_outcome_provenance(
        {"net_profit_pct": -1.0},
        realized=True,
    )

    assert provenance["exit_execution_class"] == "realized_exit_source_unknown"
    assert provenance["manual_exit_realized"] is False
    assert provenance["autonomous_target_filled"] is False
    assert provenance["realized_loss"] is True








def build_report(*args, **kwargs):
    kwargs.setdefault("canary_snapshot_path", None)
    return build_attribution_report(*args, **kwargs)


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")


def _micro_row(
    symbol: str,
    at: str,
    price: int,
    *,
    eligible: bool = True,
    venue: str = "SOR",
    session: str | None = None,
    sequence_epoch: int = 1,
) -> dict:
    return {
        "schema": "scalp_micro_reversion_market_stream_point_v3",
        "metric_contract_id": "scalp_micro_reversion_market_stream_contract_v3",
        "symbol": symbol,
        "venue": venue,
        "session_bucket": session or f"{venue}_REGULAR",
        "exchange_timestamp": at,
        "local_receive_timestamp": at,
        "source_sequence": 1,
        "series_sequence": 1,
        "sequence_epoch": sequence_epoch,
        "realtime_type": "0B",
        "trade_price": price,
        "trade_qty": 1,
        "best_bid": price - 50,
        "best_ask": price,
        "path_consumer_eligible": eligible,
        "path_order_status": "accept" if eligible else "source_sequence_regression",
        "exchange_timestamp_regression_ms": 0,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "trading_runtime_effect": False,
    }


def _depth_row(
    symbol: str,
    at: str,
    *,
    venue: str = "KRX",
    session: str = "KRX_REGULAR",
    sequence_epoch: int = 1,
) -> dict:
    return {
        "schema": "scalp_micro_reversion_market_depth_point_v1",
        "symbol": symbol,
        "venue": venue,
        "session_bucket": session,
        "exchange_timestamp": at,
        "local_receive_timestamp": at,
        "source_sequence": 1,
        "series_sequence": 1,
        "sequence_epoch": sequence_epoch,
        "item": (
            f"{symbol}_AL"
            if venue == "SOR"
            else f"{symbol}_NX" if venue == "NXT" else symbol
        ),
        "orderbook_time_raw": "100000",
        "bid_depth": 1000,
        "ask_depth": 800,
        "best_bid": 9950,
        "best_ask": 10000,
        "best_bid_qty": 1000,
        "best_ask_qty": 800,
        "bid_levels": [[1, 9950, 1000]],
        "ask_levels": [[1, 10000, 800]],
        "route_depth_totals": {
            "combined": {"bid": 1000, "ask": 800},
        },
        "realtime_type": "0D",
        "metric_contract_id": "scalp_micro_reversion_market_depth_contract_v1",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "trading_runtime_effect": False,
    }


def test_dual_market_axes_are_preserved_source_only_without_venue_inference():
    dual = attribution_module._market_axis_context(
        {
            "venue": "SOR",
            "session_bucket": "KRX_NXT_AFTERMARKET",
            "decision_market_scope": "KRX_NXT_INTEGRATED",
            "market_data_route": "krx_nxt_integrated",
        }
    )
    regular = attribution_module._market_axis_context(
        {"venue": "KRX", "session_bucket": "KRX_REGULAR"}
    )

    assert dual == {
        "decision_market_scope": "KRX_NXT_INTEGRATED",
        "market_data_route": "krx_nxt_integrated",
        "market_session_regime": "KRX_NXT_AFTERMARKET",
        "actual_execution_venue": "UNKNOWN",
        "dual_source_only": True,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
    }
    assert regular["dual_source_only"] is False
    assert regular["decision_market_scope"] == "KRX"
    assert regular["market_data_route"] == "krx_only"


@pytest.mark.parametrize("missing_horizon", [None, 1200])
def test_market_weakness_blocked_signal_uses_depth_backed_1_to_30m_bbo(missing_horizon):
    anchor_at = datetime(2026, 8, 31, 10, 0, tzinfo=KST)
    points = [
        (1, 9_950, 10_000),
        (60, 10_100, 10_150),
        (180, 10_050, 10_100),
        (300, 10_120, 10_170),
        (600, 10_150, 10_200),
        (1200, 10_180, 10_230),
        (1800, 10_200, 10_250),
    ]
    rows = []
    depth_points = []
    for sequence, (offset, bid, ask) in enumerate(points, start=1):
        if offset == missing_horizon:
            continue
        observed_at = anchor_at + timedelta(seconds=offset)
        rows.append(
            {
                "timestamp": observed_at,
                "price": ask,
                "best_bid": bid,
                "best_ask": ask,
                "sequence_epoch": 1,
            }
        )
        depth_points.append(
            {
                "timestamp": observed_at,
                "best_bid": bid,
                "best_ask": ask,
                "best_bid_qty": 1_000,
                "best_ask_qty": 1_000,
                "sequence_epoch": 1,
            }
        )
    result = _anchor_result(
        {
            "anchor_id": "market_weakness_blocked:test",
            "lifecycle_id": "market_weakness_blocked:test",
            "owner": "episode",
            "scope_id": "005930:morning",
            "symbol": "005930",
            "session": "KRX_REGULAR",
            "expected_venues": ["KRX"],
            "expected_session_buckets": ["KRX_REGULAR"],
            "anchor_at": anchor_at.isoformat(),
            "anchor_price": 10_000,
            "owner_target_price": 10_100,
            "owner_requested_quantity": 20,
            "owner_round_trip_cost_pct": 0.23,
            "lifecycle_stage": "entry",
            "anchor_role": "actual_market_weakness_blocked_entry_signal",
            "entry_state": "MARKET_WEAKNESS_BLOCKED",
            "owner_lifecycle_contract_valid": True,
            "owner_policy_tuning_eligible": True,
            "actual_order_submitted": False,
        },
        {
            "observed_row_count": len(rows),
            "invalid_contract_scope_counts": {},
        },
        {
            "rows": rows,
            "depth_points": depth_points,
            "depth_rows": len(depth_points),
            "shock_reference_count": 0,
            "raw_market_rows": [],
            "raw_depth_rows": [],
        },
        partition_loaded=True,
        source_contract_gap=None,
        clean_baseline_allowed=True,
    )

    counterfactual = result["metrics"]["market_weakness_counterfactual"]
    assert counterfactual["source_quality_status"] == (
        "blocked" if missing_horizon else "eligible"
    )
    assert (
        counterfactual["horizon_eligibility"]["30"]["source_quality_status"]
        == "eligible"
    )
    assert counterfactual["horizon_eligibility"]["20"]["source_quality_status"] == (
        "blocked" if missing_horizon else "eligible"
    )
    assert set(counterfactual["horizons_minutes"]) == {
        "1",
        "3",
        "5",
        "10",
        "20",
        "30",
    }
    assert counterfactual["horizons_minutes"]["1"]["cost_aware_net_return_pct"] == 0.77
    assert counterfactual["mfe_executable_bid_pct"] == 2.0
    assert counterfactual["mae_executable_bid_pct"] == -0.5
    assert counterfactual["target_adverse_first_hit"]["state"] == "target_first"


def test_dynamic_confirmation_first_hit_starts_at_exact_checkpoint_bbo() -> None:
    anchor_at = datetime(2026, 8, 31, 10, 0, tzinfo=KST)
    points = [
        (0, 9_990, 10_000),
        (1, 10_000, 10_010),
        (2, 10_020, 10_030),
        (300, 10_010, 10_020),
    ]
    rows = [
        {
            "timestamp": anchor_at + timedelta(seconds=offset),
            "price": ask,
            "best_bid": bid,
            "best_ask": ask,
            "sequence_epoch": 3,
        }
        for offset, bid, ask in points
    ]
    depth_points = [
        {
            "timestamp": row["timestamp"],
            "best_bid": row["best_bid"],
            "best_ask": row["best_ask"],
            "best_bid_qty": 100,
            "best_ask_qty": 100,
            "sequence_epoch": 3,
        }
        for row in rows
    ]

    result = _anchor_result(
        {
            "anchor_id": "episode:test:signal",
            "lifecycle_id": "episode:test",
            "owner": "episode",
            "scope_id": "episode:test",
            "symbol": "005930",
            "session": "KRX_REGULAR",
            "expected_venues": ["KRX"],
            "expected_session_buckets": ["KRX_REGULAR"],
            "anchor_at": anchor_at.isoformat(),
            "anchor_price": 10_000,
            "owner_entry_limit_price": 10_010,
            "owner_target_price": 10_020,
            "owner_requested_quantity": 20,
            "owner_round_trip_cost_pct": 0.23,
            "lifecycle_stage": "entry",
            "anchor_role": "episode_signal_decision_leg",
            "entry_state": "UNSPECIFIED",
            "owner_lifecycle_contract_valid": True,
            "owner_policy_tuning_eligible": True,
            "actual_order_submitted": True,
        },
        {"observed_row_count": len(rows), "invalid_contract_scope_counts": {}},
        {
            "rows": rows,
            "depth_points": depth_points,
            "depth_rows": len(depth_points),
            "shock_reference_count": 0,
            "raw_market_rows": [],
            "raw_depth_rows": [],
        },
        partition_loaded=True,
        source_contract_gap=None,
        clean_baseline_allowed=True,
    )

    first_hit = result["metrics"]["dynamic_confirmation_first_hit_outcomes"]
    checkpoint = first_hit["checkpoint_outcomes"]["0"]
    assert checkpoint["source_quality_status"] == "eligible"
    assert checkpoint["entry"]["ask_price"] == 10_000
    assert checkpoint["target_adverse_first_hit"]["target_price"] == 10_020
    assert checkpoint["target_adverse_first_hit"]["state"] == "target_first"
    assert checkpoint["target_adverse_first_hit"]["target_executable_bid"] == 10_020
    assert (
        checkpoint["target_adverse_first_hit"]["target_available_bid_quantity"] == 100
    )
    assert (
        checkpoint["target_adverse_first_hit"]["target_at"]
        == (anchor_at + timedelta(seconds=2)).isoformat()
    )
    assert checkpoint["timeout_at"] == (anchor_at + timedelta(seconds=300)).isoformat()
    assert checkpoint["timeout_available_bid_quantity"] == 100
    assert checkpoint["timeout_quote_age_ms"] == 0
    assert checkpoint["future_outcome_input_used_by_confirmation_action"] is False
    assert first_hit["counterfactual_only"] is True
    assert first_hit["runtime_effect"] is False
    assert first_hit["trading_decision_effect"] is False
    assert first_hit["actual_order_submitted"] is False


def test_dynamic_confirmation_first_hit_does_not_cross_sequence_epoch() -> None:
    anchor_at = datetime(2026, 8, 31, 10, 0, tzinfo=KST)
    rows = [
        {
            "timestamp": anchor_at,
            "price": 10_000,
            "best_bid": 9_990,
            "best_ask": 10_000,
            "sequence_epoch": 3,
        },
        {
            "timestamp": anchor_at + timedelta(seconds=2),
            "price": 10_030,
            "best_bid": 10_020,
            "best_ask": 10_030,
            "sequence_epoch": 4,
        },
        {
            "timestamp": anchor_at + timedelta(seconds=300),
            "price": 10_030,
            "best_bid": 10_020,
            "best_ask": 10_030,
            "sequence_epoch": 4,
        },
    ]
    depth_points = [
        {
            "timestamp": row["timestamp"],
            "best_bid": row["best_bid"],
            "best_ask": row["best_ask"],
            "best_bid_qty": 100,
            "best_ask_qty": 100,
            "sequence_epoch": row["sequence_epoch"],
        }
        for row in rows
    ]

    result = _anchor_result(
        {
            "anchor_id": "episode:test:cross_epoch",
            "lifecycle_id": "episode:test:cross_epoch",
            "owner": "episode",
            "scope_id": "episode:test",
            "symbol": "005930",
            "session": "KRX_REGULAR",
            "expected_venues": ["KRX"],
            "expected_session_buckets": ["KRX_REGULAR"],
            "anchor_at": anchor_at.isoformat(),
            "anchor_price": 10_000,
            "owner_entry_limit_price": 10_010,
            "owner_target_price": 10_020,
            "owner_requested_quantity": 20,
            "owner_round_trip_cost_pct": 0.23,
            "lifecycle_stage": "entry",
            "anchor_role": "episode_signal_decision_leg",
            "entry_state": "UNSPECIFIED",
            "owner_lifecycle_contract_valid": True,
            "owner_policy_tuning_eligible": True,
            "actual_order_submitted": True,
        },
        {"observed_row_count": len(rows), "invalid_contract_scope_counts": {}},
        {
            "rows": rows,
            "depth_points": depth_points,
            "depth_rows": len(depth_points),
            "shock_reference_count": 0,
            "raw_market_rows": [],
            "raw_depth_rows": [],
        },
        partition_loaded=True,
        source_contract_gap=None,
        clean_baseline_allowed=True,
    )

    checkpoint = result["metrics"]["dynamic_confirmation_first_hit_outcomes"][
        "checkpoint_outcomes"
    ]["0"]
    assert checkpoint["sequence_epoch"] == 3
    assert checkpoint["target_adverse_first_hit"]["state"] == "unresolved"
    assert checkpoint["outcome_mature_5min"] is False
    assert checkpoint["source_quality_status"] == "blocked"
    assert "checkpoint_5min_timeout_bbo_not_mature" in checkpoint["source_gap_reasons"]












def test_checkpoint_ask_depletion_never_reads_after_checkpoint(monkeypatch) -> None:
    anchor_at = datetime(2026, 8, 27, 10, 0, tzinfo=KST)
    checkpoint_at = anchor_at + timedelta(seconds=1)
    captured: dict = {}

    def fake_build(**kwargs):
        captured.update(kwargs)
        return {"source_quality_status": "eligible", "source_gap_reasons": []}

    monkeypatch.setattr(attribution_module, "build_confirmation_window", fake_build)
    market_rows = [
        {
            "schema": "scalp_micro_reversion_market_stream_point_v3",
            "realtime_type": "0B",
            "symbol": "005930",
            "venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "sequence_epoch": 7,
            "source_sequence": index,
            "local_receive_timestamp": timestamp.isoformat(),
        }
        for index, timestamp in enumerate(
            (
                anchor_at + timedelta(milliseconds=100),
                anchor_at + timedelta(milliseconds=900),
                anchor_at + timedelta(milliseconds=1_100),
            ),
            start=1,
        )
    ]
    depth_rows = [
        {
            "symbol": "005930",
            "venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "sequence_epoch": 7,
            "source_sequence": index,
            "local_receive_timestamp": timestamp.isoformat(),
        }
        for index, timestamp in enumerate(
            (
                anchor_at,
                anchor_at + timedelta(milliseconds=500),
                anchor_at + timedelta(milliseconds=1_100),
            ),
            start=1,
        )
    ]

    report = _entry_checkpoint_ask_depletion_feature(
        {
            "anchor_id": "episode:test:signal",
            "anchor_at": anchor_at.isoformat(),
            "anchor_role": "episode_signal_decision_leg",
            "symbol": "005930",
            "expected_venues": ["KRX"],
            "expected_session_buckets": ["KRX_REGULAR"],
        },
        {"raw_market_rows": market_rows, "raw_depth_rows": depth_rows},
        source_complete=True,
        checkpoint_sec=1,
    )

    assert report is not None
    assert report["decision_anchor_binding"]["window_horizon_ms"] == 1000
    assert all(
        datetime.fromisoformat(row["local_receive_timestamp"]) < checkpoint_at
        for row in captured["trade_rows"] + captured["depth_rows"]
    )
    assert captured["checkpoint_at_ms"] == int(checkpoint_at.timestamp() * 1_000)
    assert report["decision_anchor_binding"]["checkpoint_at"] == (
        checkpoint_at.isoformat()
    )
    assert report["decision_anchor_binding"]["future_outcome_input_used"] is False




def test_new_episode_symbol_without_micro_is_explicit_gap_not_zero_return(tmp_path):
    target_date = "2026-08-14"
    report_root = tmp_path / "report"
    observation_root = tmp_path / "observations"
    _write_json(
        report_root
        / "low_price_two_leg_expanded_candidate_research"
        / f"low_price_two_leg_expanded_candidate_research_{target_date}.json",
        {
            "schema": "low_price_two_leg_expanded_candidate_research_v5",
            "target_date": target_date,
            "candidate_symbols": {"777777": "new episode symbol"},
            "profiles": {
                "candidate_777777_morning": {
                    "profile_id": "candidate_777777_morning",
                    "symbol": "777777",
                    "name": "new episode symbol",
                    "session": "morning",
                    "discovery_lane": "new_symbol",
                }
            },
        },
    )
    partition = observation_root / f"trade_date={target_date}"
    partition.mkdir(parents=True)

    report = build_report(
        target_date,
        report_root=report_root,
        observation_root=observation_root,
        now=datetime(2026, 8, 14, 21, 0, tzinfo=KST),
    )

    profile = report["consumers"]["episode_machine_postclose_tuning"]["profiles"]
    row = profile["candidate_777777_morning"]
    assert row["scope"] == "prospective_episode_research"
    assert row["micro_context_status"] == "micro_date_partition_missing"
    assert row["micro_tuning_input_allowed"] is False
    assert row["base_owner_tuning_effect"] is False
    assert "metrics" not in row
    assert row["expected_venues"] == ["SOR"]
    assert any(
        gap.get("symbol") == "777777"
        and gap["gap_class"] == "micro_date_partition_missing"
        for gap in report["producer_consumer_gaps"]
    )
    assert report["collection_feedback"]["effective_date"] == "2026-08-18"
    assert report["collection_feedback"]["active_owner_full_coverage"] is True
    assert report["collection_feedback"]["active_owner_overflow_count"] == 0
    assert (
        report["collection_feedback"]["selected_active_owner_count"]
        == report["collection_feedback"]["active_owner_candidate_count"]
    )
    assert (
        report["collection_feedback"]["selected_symbol_count"]
        >= report["collection_feedback"]["active_owner_candidate_count"]
    )
    assert report["collection_feedback"]["policy_sample_selected_symbol_count"] > 0
    assert report["collection_feedback"]["manual_control_exclusion_applied"] is False
    assert report["policy_change_readiness"]["policy_change_allowed"] is False


def test_active_episode_signal_bar_gets_micro_path_metrics(tmp_path):
    target_date = "2026-08-14"
    report_root = tmp_path / "report"
    observation_root = tmp_path / "observations"
    _write_json(
        report_root
        / "low_price_two_leg_tuning"
        / f"low_price_two_leg_tuning_{target_date}.json",
        {
            "schema": "low_price_two_leg_tuning_report_v4",
            "target_date": target_date,
            "daily": {
                "profiles": {
                    "mirae_asset_morning": {
                        "profile_id": "mirae_asset_morning",
                        "target_date": target_date,
                        "symbol": "006800",
                        "session": "morning",
                        "source_quality": "pass",
                        "attempted": True,
                        "eligible_for_tuning": True,
                        "signal_features": {
                            "signal_bar": "2026-08-14T09:30:00+09:00",
                            "signal_close": 20000,
                        },
                        "legs": [
                            {
                                "leg_id": "signal_close",
                                "buy_filled_qty": 10,
                                "buy_filled_at": "2026-08-14T09:30:10+09:00",
                                "fill_price": 20000,
                                "target_filled_qty": 10,
                                "target_filled_at": "2026-08-14T09:30:40+09:00",
                                "target_fill_price": 20100,
                                "target_price": 20100,
                                "gross_no_slippage_return_pct": 0.5,
                                "net_profit_pct": 0.3,
                                "completed": True,
                            }
                        ],
                    }
                }
            },
        },
    )
    _write_jsonl(
        observation_root
        / f"trade_date={target_date}"
        / "venue=SOR"
        / "session=SOR_REGULAR"
        / "market_stream.jsonl",
        [
            _micro_row("006800", "2026-08-14T09:30:05+09:00", 19800),
            _micro_row("006800", "2026-08-14T09:31:00+09:00", 20200),
        ],
    )

    report = build_report(
        target_date,
        report_root=report_root,
        observation_root=observation_root,
        now=datetime(2026, 8, 14, 21, 0, tzinfo=KST),
    )

    row = report["consumers"]["episode_machine_postclose_tuning"]["profiles"][
        "mirae_asset_morning"
    ]
    anchor = row["anchor_results"][0]
    assert anchor["micro_context_status"] == "matched"
    assert anchor["actual_order_submitted"] is True
    assert anchor["metrics"]["mae_bps"] == -100.0
    assert anchor["metrics"]["mfe_bps"] == 100.0
    assert {item["anchor_role"] for item in row["anchor_results"]} == {
        "episode_signal_bar",
        "episode_buy_fill_confirmed",
        "episode_target_fill_confirmed",
    }
    lifecycle = report["fast_lifecycle_objective_alignment"]["lifecycle_coverage"]
    assert lifecycle["matched_decision_lifecycle_count"] == 1
    assert lifecycle["matched_entry_fill_anchor_count"] == 1
    assert lifecycle["matched_exit_anchor_count"] == 1
    assert lifecycle["timed_owner_outcome_count"] == 1


@pytest.mark.parametrize(
    "defect",
    [
        None,
        "missing_receipt",
        "wrong_symbol",
        "wrong_date",
        "wrong_order",
        "wrong_leg",
        "quantity",
        "boolean_quantity",
        "price",
        "before_buy",
        "malformed_time",
        "unverified_source",
        "invalid_contract",
    ],
)
def test_verified_target_receipt_unknown_time_is_exclusion_not_realized_sample(
    tmp_path, defect
):
    from src.engine.monitoring.low_price_two_leg_tuning import _sanitize_leg

    day = "2026-09-08"
    raw = {
        "leg_id": "signal_close",
        "status": "COMPLETE",
        "quantity": 10,
        "entry_price": 33700,
        "fill_price": 33700,
        "target_price": 33900,
        "position_qty": 0,
        "buy_filled_qty": 10,
        "target_filled_qty": 10,
        "target_fill_price": 33900,
        "buy_filled_at": day + "T09:38:02+09:00",
        "target_filled_at": "",
        "target_fill_reconciled_at": day + "T15:58:15+09:00",
        "target_order_date": day,
        "target_order_no": "0021943",
        "exit_fill_source": "broker_verified_original_target_receipt",
        "target_exit_reconciliation_receipt": {
            "leg_id": "signal_close",
            "symbol": "015760",
            "source_api": "kt00007",
            "order_date": day,
            "order_no": "0021943",
            "filled_qty": 10,
            "fill_price": 33900,
        },
    }
    leg = _sanitize_leg(raw, 0.23)
    assert leg["target_filled_at"] is None
    assert leg["holding_duration_sec"] is None
    receipt = leg["target_exit_reconciliation_receipt"]
    if defect == "missing_receipt":
        leg.pop("target_exit_reconciliation_receipt")
    if defect == "wrong_symbol":
        receipt["symbol"] = "005930"
    if defect == "wrong_date":
        receipt["order_date"] = "2026-09-07"
    if defect == "wrong_order":
        receipt["order_no"] = "0021944"
    if defect == "wrong_leg":
        receipt["leg_id"] = "other_leg"
    if defect == "quantity":
        receipt["filled_qty"] = 9
    if defect == "boolean_quantity":
        receipt["filled_qty"] = True
    if defect == "price":
        receipt["fill_price"] = 33950
    if defect == "before_buy":
        leg["target_fill_reconciled_at"] = day + "T08:00:00+09:00"
    if defect == "malformed_time":
        leg["target_filled_at"] = "invalid"
    if defect == "unverified_source":
        leg["exit_fill_source"] = "unknown"
    if defect == "invalid_contract":
        leg["contract_valid"] = False
    report_root = tmp_path / "report"
    _write_json(
        report_root
        / "low_price_two_leg_tuning"
        / f"low_price_two_leg_tuning_{day}.json",
        {
            "schema": "low_price_two_leg_tuning_report_v7",
            "target_date": day,
            "cost_pct": 0.23,
            "daily": {
                "profiles": {
                    "kepco_morning": {
                        "profile_id": "kepco_morning",
                        "symbol": "015760",
                        "session": "morning",
                        "target_date": day,
                        "attempted": True,
                        "eligible_for_tuning": True,
                        "source_quality": "pass",
                        "signal_features": {
                            "signal_bar": day + "T09:35:00+09:00",
                            "signal_close": 33750,
                            "signal_decision_at": day + "T09:36:04+09:00",
                            "source_entry_event_id": "exact-kepco-signal",
                        },
                        "legs": [leg],
                    }
                }
            },
        },
    )
    profiles, anchors, _ = _episode_inventory(day, report_root)
    decision = next(
        a for a in anchors if a["anchor_role"] == "episode_signal_decision_leg"
    )
    assert decision["owner_lifecycle_contract_valid"] is False
    assert decision["owner_policy_tuning_eligible"] is False
    assert decision["owner_outcome"]["realized"] is False
    assert decision["owner_outcome"]["holding_duration_ms"] is None
    assert ("owner_terminal_timestamp_exclusion" in decision) is (defect is None)
    labeled = attribution_module._entry_confirmation_label(
        {
            **decision,
            "metrics": {},
            "micro_context_status": "micro_canary_source_quality_missing_or_invalid",
        }
    )
    assert labeled is not None
    assert bool(labeled.get("owner_terminal_timestamp_exclusion")) is (defect is None)
    assert labeled["owner_lifecycle_contract_valid"] is False
    assert profiles["kepco_morning"]["owner_anchor_contract_status"] == "invalid"
    assert not any(a["lifecycle_stage"] == "exit" for a in anchors)


@pytest.mark.parametrize(
    "defect",
    [
        None,
        "missing_registry",
        "duplicate",
        "owner",
        "date",
        "status",
        "clock_status",
        "applied_time",
        "quantity",
        "boolean_quantity",
        "price",
        "allocated",
        "authority",
        "observed_time",
        "registry_hash",
    ],
)
def test_manual_timestamp_loss_requires_exact_applied_registry(tmp_path, defect):
    from src.engine.monitoring.low_price_two_leg_tuning import _sanitize_leg
    from src.engine.automation.machine_entry_timing_tuning import (
        _immutable_owner_timestamp_exclusion,
    )
    from datetime import date

    day = "2026-09-09"
    receipt = {
        "order_no": "0062072",
        "order_date": day,
        "symbol": "015760",
        "source_api": "kt00007",
        "filled_qty": 10,
        "fill_price": 33950,
        "allocated_qty": 10,
        "allocation_authority": "explicit_owner_whole_position_exit",
    }
    raw = {
        "leg_id": "signal_close",
        "status": "COMPLETE",
        "quantity": 10,
        "entry_price": 34700,
        "fill_price": 34700,
        "target_price": 34900,
        "position_qty": 0,
        "buy_filled_qty": 10,
        "target_filled_qty": 10,
        "target_fill_price": 33950,
        "buy_filled_at": day + "T09:36:10+09:00",
        "target_filled_at": "",
        "target_fill_reconciled_at": day + "T17:15:12+09:00",
        "exit_fill_source": "broker_verified_manual_sell_receipt",
        "manual_exit_receipt": receipt,
    }
    applied = {
        k: receipt[k]
        for k in (
            "order_no",
            "order_date",
            "symbol",
            "source_api",
            "filled_qty",
            "fill_price",
        )
    }
    applied.update(
        owner_id="kepco_morning",
        entry_trade_date=day,
        status="applied",
        fill_timestamp_status="unavailable_from_dated_order_receipt",
        applied_at_kst=raw["target_fill_reconciled_at"],
    )
    registry = {
        "schema": "episode_manual_exit_receipt_registry_v1",
        "receipts": [applied],
    }
    if defect == "missing_registry":
        registry = {}
    if defect == "duplicate":
        registry["receipts"].append(dict(applied))
    if defect == "owner":
        applied["owner_id"] = "other"
    if defect == "date":
        applied["entry_trade_date"] = "2026-09-08"
    if defect == "status":
        applied["status"] = "reserved"
    if defect == "clock_status":
        applied["fill_timestamp_status"] = "unknown"
    if defect == "applied_time":
        applied["applied_at_kst"] = day + "T08:00:00+09:00"
    if defect == "quantity":
        applied["filled_qty"] = 9
    if defect == "boolean_quantity":
        applied["filled_qty"] = True
    if defect == "price":
        applied["fill_price"] = 34000
    if defect == "allocated":
        receipt["allocated_qty"] = 9
    if defect == "authority":
        receipt["allocation_authority"] = "inferred"
    if defect == "observed_time":
        raw["target_filled_at"] = day + "T15:00:00+09:00"
    leg = _sanitize_leg(raw, 0.23)
    assert leg["manual_exit_receipt"] == receipt
    proof = attribution_module._verified_manual_timestamp_loss(
        leg,
        symbol="015760",
        profile_id="kepco_morning",
        target_date=day,
        registry=registry,
        registry_sha256=None if defect == "registry_hash" else "a" * 64,
    )
    assert (proof is not None) is (defect is None)
    if proof:
        assert leg["target_filled_at"] is None and leg["holding_duration_sec"] is None
        row = {
            "owner": "episode",
            "scope_id": "kepco_morning",
            "symbol": "015760",
            "owner_lifecycle_contract_valid": False,
            "owner_policy_tuning_eligible": False,
            "owner_terminal_timestamp_exclusion": {
                "schema": "verified_manual_timestamp_loss_v1",
                "source_date": day,
                "scope_id": "kepco_morning",
                "symbol": "015760",
                "receipts": [proof],
                "timing_sample_eligible": False,
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            },
        }
        assert _immutable_owner_timestamp_exclusion(row, date.fromisoformat(day))
        proof.pop("registry_sha256")
        assert not _immutable_owner_timestamp_exclusion(row, date.fromisoformat(day))


@pytest.mark.parametrize(
    "defect",
    [
        None,
        "running",
        "incomplete",
        "unreadable",
        "manifest",
        "nonempty",
        "source_id",
        "diagnostic",
        "scope_invalid",
        "late_study_only",
        "last_checkpoint",
        "raw_timestamp_missing",
    ],
)
def test_closed_exact_window_exclusion_never_creates_valid_samples(defect):
    from datetime import date
    from src.engine.automation.machine_entry_timing_tuning import (
        _closed_market_window_excluded,
    )

    day = "2026-09-09"
    anchor = {
        "anchor_role": "episode_signal_decision_leg",
        "anchor_at": day + "T10:00:00+09:00",
        "entry_timing_decision_anchor_valid": True,
        "source_entry_event_id": "native-signal",
        "anchor_id": "native-anchor",
        "symbol": "015760",
        "expected_venues": ["SOR"],
        "expected_session_buckets": ["SOR_REGULAR"],
    }
    source = {
        "partition_status": "loaded",
        "source_contract_ready": True,
        "source_exclusion_manifest_status": "loaded",
        "canary_source_quality": {
            "status": "loaded_pass",
            "target_day_complete": True,
            "stopped_clean_closed": True,
            "source_sha256": "a" * 64,
        },
    }
    window = {"rows": [], "raw_market_rows": []}
    inventory = {"invalid_contract_row_count": 0, "invalid_contract_scope_counts": {}}
    if defect == "running":
        source["canary_source_quality"]["stopped_clean_closed"] = False
    if defect == "incomplete":
        source["canary_source_quality"]["target_day_complete"] = False
    if defect == "unreadable":
        source["source_contract_ready"] = False
    if defect == "manifest":
        source["source_exclusion_manifest_status"] = "invalid"
    if defect == "nonempty":
        window["rows"] = [{}]
    if defect == "late_study_only":
        window["rows"] = [
            {"timestamp": datetime.fromisoformat(day + "T10:20:00+09:00")}
        ]
        window["raw_market_rows"] = [
            {"local_receive_timestamp": day + "T10:20:00+09:00"}
        ]
    if defect == "last_checkpoint":
        window["raw_market_rows"] = [
            {"local_receive_timestamp": day + "T10:00:06+09:00"}
        ]
    if defect == "raw_timestamp_missing":
        window["raw_market_rows"] = [{}]
    if defect == "source_id":
        anchor["source_entry_event_id"] = ""
    if defect == "diagnostic":
        anchor["anchor_role"] = "episode_signal_bar"
    if defect == "scope_invalid":
        inventory["invalid_contract_row_count"] = 1
    proof = attribution_module._closed_market_window_exclusion(
        anchor, window, source, inventory, day
    )
    assert (proof is not None) is (defect in (None, "late_study_only"))
    if proof:
        assert proof["timing_sample_eligible"] is False
        row = {**anchor, "closed_market_window_exclusion": proof}
        assert _closed_market_window_excluded(row, date.fromisoformat(day))
        proof["expected_venues"] = ["NXT"]
        assert not _closed_market_window_excluded(row, date.fromisoformat(day))


def test_receipt_projection_preserves_economics_and_rejects_state_change(tmp_path):
    from src.engine.monitoring import low_price_two_leg_tuning as producer

    day = "2026-09-09"
    state_dir, output_dir = tmp_path / "state", tmp_path / "report"
    state_dir.mkdir()
    output_dir.mkdir()
    raw = {
        "leg_id": "signal_close",
        "status": "COMPLETE",
        "quantity": 10,
        "entry_price": 34700,
        "fill_price": 34700,
        "target_price": 34900,
        "position_qty": 0,
        "buy_filled_qty": 10,
        "target_filled_qty": 10,
        "target_fill_price": 33950,
        "buy_filled_at": day + "T09:36:10+09:00",
        "target_filled_at": "",
        "exit_fill_source": "broker_verified_manual_sell_receipt",
        "manual_exit_receipt": {"order_no": "12345"},
    }
    leg = producer._sanitize_leg(raw, 0.23)
    leg.pop("manual_exit_receipt")
    report = {
        "schema": producer.REPORT_SCHEMA,
        "target_date": day,
        "cost_pct": 0.23,
        "daily": {"profiles": {"kepco_morning": {"legs": [leg]}}},
        "windows": {"existing_economics": {"realized_pnl": 1896, "missing_cost": None}},
    }
    report["artifact_hash"] = producer.report_artifact_hash(report)
    path = output_dir / f"{producer.REPORT_TYPE}_{day}.json"
    path.write_text(json.dumps(report))
    state_path = state_dir / "kepco_morning_state.json"
    state_path.write_text(json.dumps({"trade_date": day, "legs": [raw]}))
    updated = producer.refresh_receipt_projection(
        target_date=day, state_dir=state_dir, output_dir=output_dir
    )
    assert updated["windows"] == report["windows"]
    assert (
        updated["daily"]["profiles"]["kepco_morning"]["legs"][0]["manual_exit_receipt"]
        == raw["manual_exit_receipt"]
    )
    assert updated["receipt_metadata_projection"]["broker_calls"] == 0
    assert updated["artifact_hash"] == producer.report_artifact_hash(updated)
    raw["target_fill_price"] = 33900
    state_path.write_text(json.dumps({"trade_date": day, "legs": [raw]}))
    with pytest.raises(ValueError, match="nonmetadata_state_changed"):
        producer.refresh_receipt_projection(
            target_date=day, state_dir=state_dir, output_dir=output_dir
        )


def test_episode_manual_stop_loss_keeps_negative_outcome_and_distinct_exit_role(
    tmp_path,
):
    target_date = "2026-08-28"
    report_root = tmp_path / "report"
    _write_json(
        report_root
        / "low_price_two_leg_tuning"
        / f"low_price_two_leg_tuning_{target_date}.json",
        {
            "schema": "low_price_two_leg_tuning_report_v6",
            "target_date": target_date,
            "cost_pct": 0.23,
            "daily": {
                "profiles": {
                    "nhn_afternoon": {
                        "profile_id": "nhn_afternoon",
                        "target_date": target_date,
                        "symbol": "181710",
                        "session": "afternoon",
                        "source_quality": "pass",
                        "attempted": True,
                        "eligible_for_tuning": True,
                        "signal_features": {
                            "signal_bar": "2026-08-28T14:00:00+09:00",
                            "signal_decision_at": "2026-08-28T14:00:01+09:00",
                            "signal_close": 71_500,
                        },
                        "legs": [
                            {
                                "leg_id": "signal_close",
                                "entry_price": 71_500,
                                "buy_filled_qty": 8,
                                "buy_filled_at": "2026-08-28T14:00:10+09:00",
                                "fill_price": 71_500,
                                "target_filled_qty": 8,
                                "target_filled_at": "2026-08-28T15:00:00+09:00",
                                "target_fill_price": 69_900,
                                "target_price": 71_900,
                                "exit_fill_source": (
                                    "broker_verified_manual_sell_receipt"
                                ),
                                "profit_price_source": "broker_manual_sell_receipt",
                                "exit_execution_class": "manual_operator_exit",
                                "gross_no_slippage_return_pct": -2.237762,
                                "net_profit_pct": -2.467762,
                                "completed": True,
                            }
                        ],
                    }
                }
            },
        },
    )

    profiles, anchors, sources = _episode_inventory(target_date, report_root)

    assert sources["tuning"]["status"] == "loaded"
    assert profiles["nhn_afternoon"]["owner_policy_tuning_eligible"] is True
    decision_anchor = next(
        anchor
        for anchor in anchors
        if anchor["anchor_role"] == "episode_signal_decision_leg"
    )
    exit_anchor = next(
        anchor
        for anchor in anchors
        if anchor["anchor_role"] == "episode_manual_exit_confirmed"
    )
    for anchor in (decision_anchor, exit_anchor):
        outcome = anchor["owner_outcome"]
        assert outcome["realized"] is True
        assert outcome["exit_execution_class"] == "manual_operator_exit"
        assert outcome["manual_exit_realized"] is True
        assert outcome["autonomous_target_filled"] is False
        assert outcome["realized_loss"] is True
        assert outcome["cost_aware_net_return_pct"] < 0


def test_samsung_episode_decision_timestamp_enters_entry_timing_inventory(tmp_path):
    target_date = "2026-08-27"
    report_root = tmp_path / "report"
    _write_json(
        report_root
        / "samsung_machine_entry_tuning"
        / f"samsung_machine_entry_tuning_{target_date}.json",
        {
            "schema": "samsung_machine_entry_tuning_report_v6",
            "target_date": target_date,
            "symbol": "005930",
            "cost_pct": 0.2,
            "daily": {
                "machines": {
                    "midday": {
                        "machine": "midday",
                        "target_date": target_date,
                        "attempted": True,
                        "eligible_for_cumulative_tuning": True,
                        "source_quality": "pass",
                        "source_quality_reasons": [],
                        "signal_features": {
                            "strategy": "midday",
                            "signal_decision_at": "2026-08-27T13:15:00+09:00",
                        },
                        "legs": [
                            {
                                "leg_id": "signal_close",
                                "route": "SOR",
                                "buy_filled_qty": 10,
                                "buy_filled_at": "2026-08-27T13:15:01+09:00",
                                "entry_price": 100_000,
                                "fill_price": 100_000,
                                "target_price": 100_500,
                                "target_filled_qty": 10,
                                "target_filled_at": "2026-08-27T13:16:00+09:00",
                                "target_fill_price": 100_500,
                                "completed": True,
                                "equal_weight_profit_pct": 0.3,
                            }
                        ],
                    }
                }
            },
        },
    )

    profiles, anchors, sources = _episode_inventory(target_date, report_root)

    row = profiles["samsung:midday"]
    assert row["owner_anchor_contract_status"] == "valid"
    assert row["owner_policy_tuning_eligible"] is True
    assert sources["samsung_machine_entry_tuning"]["status"] == "loaded"
    assert len(anchors) == 1
    assert anchors[0]["scope_id"] == "midday"
    assert anchors[0]["session"] == "KRX_REGULAR"
    assert anchors[0]["anchor_role"] == "episode_signal_decision_leg"
    assert anchors[0]["owner_entry_limit_price"] == 100_000
    assert anchors[0]["owner_target_price"] == 100_500
    assert anchors[0]["owner_outcome"]["realized"] is True


def test_held_episode_keeps_diagnostic_anchors_but_never_tuning_authority(tmp_path):
    target_date = "2026-08-14"
    report_root = tmp_path / "report"
    observation_root = tmp_path / "observations"
    _write_json(
        report_root
        / "low_price_two_leg_tuning"
        / f"low_price_two_leg_tuning_{target_date}.json",
        {
            "schema": "low_price_two_leg_tuning_report_v3",
            "target_date": target_date,
            "daily": {
                "profiles": {
                    "sk_eternix_midday": {
                        "target_date": target_date,
                        "symbol": "475150",
                        "session": "midday",
                        "source_quality": "gap",
                        "source_quality_reasons": ["held_or_unresolved_inventory"],
                        "eligible_for_tuning": False,
                        "attempted": True,
                        "signal_features": {
                            "signal_bar": "2026-08-14T11:00:00+09:00",
                            "signal_close": 10000,
                        },
                        "legs": [
                            {
                                "leg_id": "one",
                                "buy_filled_qty": 10,
                                "buy_filled_at": "2026-08-14T11:00:05+09:00",
                                "fill_price": 10000,
                                "target_filled_qty": 5,
                                "target_filled_at": "2026-08-14T11:00:20+09:00",
                                "target_fill_price": 10050,
                                "target_price": 10050,
                                "completed": False,
                            }
                        ],
                    },
                    "mirae_asset_midday": {
                        "target_date": target_date,
                        "symbol": "006800",
                        "session": "midday",
                        "source_quality": "gap",
                        "source_quality_reasons": [
                            "observation_source_quality_audit_blocked"
                        ],
                        "eligible_for_tuning": False,
                        "attempted": True,
                        "signal_features": {
                            "signal_bar": "2026-08-14T11:10:00+09:00",
                            "signal_close": 20000,
                        },
                        "legs": [],
                    },
                }
            },
        },
    )
    _write_jsonl(
        observation_root
        / f"trade_date={target_date}"
        / "venue=SOR"
        / "session=SOR_REGULAR"
        / "market_stream.jsonl",
        [
            _micro_row("475150", "2026-08-14T11:00:01+09:00", 10000),
            _micro_row("475150", "2026-08-14T11:00:06+09:00", 10010),
            _micro_row("475150", "2026-08-14T11:00:21+09:00", 10050),
            _micro_row("006800", "2026-08-14T11:10:01+09:00", 20000),
        ],
    )

    report = build_report(
        target_date,
        report_root=report_root,
        observation_root=observation_root,
    )

    held = report["consumers"]["episode_machine_postclose_tuning"]["profiles"][
        "sk_eternix_midday"
    ]
    assert {item["anchor_role"] for item in held["anchor_results"]} == {
        "episode_signal_bar",
        "episode_buy_fill_confirmed",
        "episode_target_partial_fill_confirmed",
    }
    assert all(
        item["micro_context_status"] == "matched"
        and item["micro_tuning_input_allowed"] is False
        for item in held["anchor_results"]
    )
    assert held["micro_context_status"] == "matched"
    assert held["micro_tuning_input_allowed"] is False
    blocked = report["consumers"]["episode_machine_postclose_tuning"]["profiles"][
        "mirae_asset_midday"
    ]
    assert blocked["anchor_results"] == []
    assert blocked["micro_context_status"] == "owner_anchor_contract_invalid"
    lifecycle = report["fast_lifecycle_objective_alignment"]["lifecycle_coverage"]
    assert lifecycle["context_matched_decision_lifecycle_count"] == 1
    assert lifecycle["policy_eligible_matched_decision_lifecycle_count"] == 0
    assert lifecycle["matched_decision_lifecycle_count"] == 0
    assert lifecycle["matched_exit_anchor_count"] == 0
    assert lifecycle["matched_partial_exit_fill_anchor_count"] == 1
    assert lifecycle["unrealized_owner_outcome_count"] == 1
    assert lifecycle["realized_owner_outcome_count"] == 0
    assert report["summary"]["anchor_count_by_stage"]["exit_partial_fill"] == 1
    assert report["summary"]["matched_anchor_count_by_stage"]["exit_partial_fill"] == 1
    assert (
        sum(report["summary"]["anchor_count_by_stage"].values())
        == report["summary"]["anchor_count"]
    )
    assert report["policy_promotion_candidates"] == []
    assert report["summary"]["objective_followup_required_count"] == 1
    followup = report["objective_followups"][0]
    assert followup["state"] == "EVIDENCE_ACCUMULATING"
    assert followup["followup_required"] is True
    assert followup["attention_class"] == "terminal_reconciliation"
    assert followup["operator_decision_required"] is False
    assert followup["remaining_gap_codes"] == [
        "no_policy_eligible_paired_lifecycle_observed"
    ]
    assert followup["next_action"] == (
        "reconcile_exact_owner_terminal_outcomes_before_waiting"
    )
    assert followup["metric_contract"] == OBJECTIVE_FOLLOWUP_METRIC_CONTRACT
    assert report["rolling_paired_policy_research"]["implementation_boundary"] == {
        "rolling_paired_policy_candidate_producer_present": True,
        "episode_same_day_reentry_or_timeout_tuning_axis_present": True,
        "speed_or_turnover_metric_changes_policy_selection": True,
    }


def test_multi_day_episode_reconciliation_emits_target_date_exit_anchor(tmp_path):
    target_date = "2026-08-14"
    report_root = tmp_path / "report"
    observation_root = tmp_path / "observations"
    _write_json(
        report_root
        / "low_price_two_leg_tuning"
        / f"low_price_two_leg_tuning_{target_date}.json",
        {
            "schema": "low_price_two_leg_tuning_report_v3",
            "target_date": target_date,
            "daily": {"profiles": {}},
            "prior_state_reconciliations": {
                "samsung_heavy_midday": {
                    "source_date": "2026-08-12",
                    "row": {
                        "target_date": "2026-08-12",
                        "symbol": "010140",
                        "session": "midday",
                        "source_quality": "pass",
                        "source_quality_reasons": [],
                        "eligible_for_tuning": True,
                        "attempted": True,
                        "signal_features": {
                            "signal_bar": "2026-08-12T11:00:00+09:00",
                            "signal_close": 30000,
                        },
                        "legs": [
                            {
                                "leg_id": "one",
                                "buy_filled_qty": 10,
                                "buy_filled_at": "2026-08-12T11:00:05+09:00",
                                "fill_price": 30000,
                                "target_filled_qty": 10,
                                "target_filled_at": "2026-08-14T11:00:05+09:00",
                                "target_fill_price": 30100,
                                "target_price": 30100,
                                "gross_no_slippage_return_pct": 0.333333,
                                "net_profit_pct": 0.133333,
                                "completed": True,
                            }
                        ],
                    },
                },
                "sk_eternix_midday": {
                    "source_date": "2026-08-12",
                    "row": {
                        "target_date": "2026-08-12",
                        "symbol": "475150",
                        "session": "midday",
                        "source_quality": "gap",
                        "source_quality_reasons": [
                            "original_date_source_quality_audit_blocked"
                        ],
                        "eligible_for_tuning": False,
                        "attempted": True,
                        "signal_features": {
                            "signal_bar": "2026-08-12T11:10:00+09:00",
                            "signal_close": 40000,
                        },
                        "legs": [
                            {
                                "leg_id": "one",
                                "buy_filled_qty": 10,
                                "buy_filled_at": "2026-08-12T11:10:05+09:00",
                                "fill_price": 40000,
                                "target_filled_qty": 10,
                                "target_filled_at": "2026-08-14T11:10:05+09:00",
                                "target_fill_price": 40100,
                                "target_price": 40100,
                                "completed": True,
                            }
                        ],
                    },
                },
            },
        },
    )
    _write_jsonl(
        observation_root
        / f"trade_date={target_date}"
        / "venue=SOR"
        / "session=SOR_REGULAR"
        / "market_stream.jsonl",
        [
            _micro_row("010140", "2026-08-14T11:00:06+09:00", 30100),
            _micro_row("475150", "2026-08-14T11:10:06+09:00", 40100),
        ],
    )

    report = build_report(
        target_date,
        report_root=report_root,
        observation_root=observation_root,
    )

    row = report["consumers"]["episode_machine_postclose_tuning"]["profiles"][
        "samsung_heavy_midday"
    ]
    assert len(row["anchor_results"]) == 1
    exit_anchor = row["anchor_results"][0]
    assert exit_anchor["anchor_role"] == "episode_target_fill_reconciled"
    assert exit_anchor["owner_original_source_date"] == "2026-08-12"
    assert "2026-08-12T11:00:00+09:00" in exit_anchor["lifecycle_id"]
    assert exit_anchor["micro_context_status"] == "matched"
    blocked = report["consumers"]["episode_machine_postclose_tuning"]["profiles"][
        "sk_eternix_midday"
    ]
    assert blocked["anchor_results"] == []
    assert blocked["micro_context_status"] == "owner_anchor_contract_invalid"
    lifecycle = report["fast_lifecycle_objective_alignment"]["lifecycle_coverage"]
    assert lifecycle["matched_exit_anchor_count"] == 1
    assert lifecycle["matched_decision_lifecycle_count"] == 0

    tuning_path = (
        report_root
        / "low_price_two_leg_tuning"
        / f"low_price_two_leg_tuning_{target_date}.json"
    )
    corrupted = json.loads(tuning_path.read_text(encoding="utf-8"))
    corrupted["prior_state_reconciliations"]["samsung_heavy_midday"]["row"][
        "target_date"
    ] = "2026-08-11"
    _write_json(tuning_path, corrupted)
    corrupted_report = build_report(
        target_date,
        report_root=report_root,
        observation_root=observation_root,
    )
    corrupted_row = corrupted_report["consumers"]["episode_machine_postclose_tuning"][
        "profiles"
    ]["samsung_heavy_midday"]
    assert corrupted_row["anchor_results"] == []
    assert corrupted_row["micro_context_status"] == "owner_anchor_contract_invalid"
    assert corrupted_row["owner_policy_tuning_eligible"] is False
    assert (
        "prior_reconciliation_source_date_contract_invalid"
        in corrupted_row["lifecycle_instrumentation_gaps"]
    )

    carried = corrupted["prior_state_reconciliations"]["samsung_heavy_midday"]
    carried["source_date"] = "2026-06-04"
    carried["row"]["target_date"] = "2026-06-04"
    carried["row"]["signal_features"]["signal_bar"] = "2026-06-04T11:00:00+09:00"
    carried["row"]["legs"][0]["buy_filled_at"] = "2026-06-04T11:00:05+09:00"
    _write_json(tuning_path, corrupted)
    prebaseline_report = build_report(
        target_date,
        report_root=report_root,
        observation_root=observation_root,
    )
    prebaseline_row = prebaseline_report["consumers"][
        "episode_machine_postclose_tuning"
    ]["profiles"]["samsung_heavy_midday"]
    assert prebaseline_row["anchor_results"] == []
    assert (
        "prior_reconciliation_source_date_contract_invalid"
        in prebaseline_row["lifecycle_instrumentation_gaps"]
    )










def test_pre_clean_baseline_is_archive_only(tmp_path):
    report = build_report(
        "2026-06-04",
        report_root=tmp_path / "report",
        observation_root=tmp_path / "observations",
        now=datetime(2026, 8, 14, 21, 30, tzinfo=KST),
    )

    profile = next(
        iter(
            report["consumers"]["episode_machine_postclose_tuning"]["profiles"].values()
        )
    )
    assert report["clean_baseline_allowed"] is False
    assert profile["micro_context_status"] == "pre_clean_baseline_archive_only"
    assert profile["micro_tuning_input_allowed"] is False


def test_invalid_actual_episode_signal_contract_is_explicit_gap(tmp_path):
    target_date = "2026-08-14"
    report_root = tmp_path / "report"
    _write_json(
        report_root
        / "low_price_two_leg_tuning"
        / f"low_price_two_leg_tuning_{target_date}.json",
        {
            "schema": "low_price_two_leg_tuning_report_v3",
            "target_date": target_date,
            "daily": {
                "profiles": {
                    "sk_eternix_morning": {
                        "profile_id": "sk_eternix_morning",
                        "target_date": target_date,
                        "symbol": "475150",
                        "session": "morning",
                        "source_quality": "pass",
                        "eligible_for_tuning": True,
                        "attempted": True,
                        "signal_features": {
                            "signal_bar": "not-a-timestamp",
                            "signal_close": 20000,
                        },
                        "legs": [],
                    }
                }
            },
        },
    )
    stream_path = (
        tmp_path
        / "observations"
        / f"trade_date={target_date}"
        / "venue=SOR"
        / "session=SOR_REGULAR"
        / "market_stream.jsonl"
    )
    _write_jsonl(
        stream_path,
        [_micro_row("475150", "2026-08-14T09:30:00+09:00", 20000)],
    )

    report = build_report(
        target_date,
        report_root=report_root,
        observation_root=tmp_path / "observations",
    )

    row = report["consumers"]["episode_machine_postclose_tuning"]["profiles"][
        "sk_eternix_morning"
    ]
    assert row["anchor_results"] == []
    assert row["micro_context_status"] == "owner_anchor_contract_invalid"
    assert row["owner_policy_tuning_eligible"] is False
    assert (
        "signal_bar_or_signal_close_missing_or_invalid"
        in row["lifecycle_instrumentation_gaps"]
    )

    tuning_path = (
        report_root
        / "low_price_two_leg_tuning"
        / f"low_price_two_leg_tuning_{target_date}.json"
    )
    mismatched = json.loads(tuning_path.read_text(encoding="utf-8"))
    nested = mismatched["daily"]["profiles"]["sk_eternix_morning"]
    nested["target_date"] = "2026-08-13"
    nested["signal_features"]["signal_bar"] = "2026-08-14T09:30:00+09:00"
    _write_json(tuning_path, mismatched)
    mismatch_report = build_report(
        target_date,
        report_root=report_root,
        observation_root=tmp_path / "observations",
    )
    mismatch_row = mismatch_report["consumers"]["episode_machine_postclose_tuning"][
        "profiles"
    ]["sk_eternix_morning"]
    assert mismatch_row["anchor_results"] == []
    assert (
        "owner_nested_target_date_contract_invalid"
        in mismatch_row["lifecycle_instrumentation_gaps"]
    )


def test_episode_owner_identity_cannot_forge_collection_symbol(tmp_path):
    target_date = "2026-08-14"
    report_root = tmp_path / "report"
    _write_json(
        report_root
        / "low_price_two_leg_tuning"
        / f"low_price_two_leg_tuning_{target_date}.json",
        {
            "schema": "low_price_two_leg_tuning_report_v3",
            "target_date": target_date,
            "daily": {
                "profiles": {
                    "sk_eternix_morning": {
                        "profile_id": "sk_eternix_morning",
                        "target_date": target_date,
                        "symbol": "999998",
                        "session": "morning",
                        "source_quality": "pass",
                        "eligible_for_tuning": True,
                        "attempted": True,
                    },
                    "unknown_active_profile": {
                        "profile_id": "unknown_active_profile",
                        "target_date": target_date,
                        "symbol": "999997",
                        "session": "morning",
                        "source_quality": "pass",
                        "eligible_for_tuning": True,
                        "attempted": True,
                    },
                }
            },
        },
    )

    report = build_report(
        target_date,
        report_root=report_root,
        observation_root=tmp_path / "observations",
    )

    profiles = report["consumers"]["episode_machine_postclose_tuning"]["profiles"]
    known = profiles["sk_eternix_morning"]
    assert known["symbol"] == "475150"
    assert known["owner_anchor_contract_status"] == "invalid"
    assert known["owner_policy_tuning_eligible"] is False
    assert (
        "owner_profile_identity_contract_invalid"
        in known["lifecycle_instrumentation_gaps"]
    )
    unknown = profiles["unknown_active_profile"]
    assert unknown["symbol"] == ""
    assert unknown["scope"] == "invalid_episode_owner_identity"
    assert unknown["owner_anchor_contract_status"] == "invalid"
    collection_targets = build_collection_targets(report, max_symbols=100)
    collection_symbols = {
        row["symbol"]
        for key in ("selected_targets", "overflow_targets")
        for row in collection_targets[key]
    }
    assert "999998" not in collection_symbols
    assert "999997" not in collection_symbols








def test_nontrading_attribution_skips_collection_feedback_write_contract(tmp_path):
    report = build_report(
        "2026-08-16",
        report_root=tmp_path / "report",
        observation_root=tmp_path / "observations",
    )

    assert report["collection_feedback"] == {
        "schema": "scalp_micro_reversion_collection_targets_v3",
        "effective_date": None,
        "status": "source_date_not_krx_trading_day_write_skipped",
        "coverage_policy": (
            "all_active_owner_symbols_then_bounded_prospective_rotation"
        ),
        "coverage_stage": "exact_date_target_manifest_selection",
        "runtime_registration_receipt_required": True,
        "current_runtime_registration_receipt": {
            "status": "not_required_before_activation",
            "ready": True,
            "global_contract_ready": True,
            "route_isolation_allowed": True,
            "activation_date": "2026-09-04",
            "expected_registration_items": [],
            "complete_registration_items": [],
            "incomplete_registration_items": [],
            "incomplete_active_registration_items": [],
            "runtime_effect": False,
        },
        "active_owner_full_coverage": False,
        "active_owner_candidate_count": 0,
        "selected_active_owner_count": 0,
        "active_owner_overflow_count": 0,
        "selected_symbol_count": 0,
        "repair_gap_selected_symbol_count": 0,
        "policy_sample_selected_symbol_count": 0,
        "overflow_symbol_count": 0,
        "manual_control_exclusion_applied": False,
        "market_data_subscription_effect": False,
        "trading_runtime_effect": False,
    }


def test_runtime_registration_receipt_requires_exact_manifest_and_both_types(
    monkeypatch, tmp_path
):
    configured_at = datetime(2026, 9, 4, 7, 55, tzinfo=KST)
    first_0b = configured_at.timestamp() + 1
    first_0d = configured_at.timestamp() + 2
    last_received = configured_at.timestamp() + 3
    monkeypatch.setattr(
        attribution_module,
        "load_exact_date_collection_targets",
        lambda target_date, root: {
            "status": "loaded",
            "path": str(root / f"targets-{target_date}.json"),
            "registration_items": ["005930", "005930_NX"],
        },
    )
    receipt_root = tmp_path / "receipts"
    receipt_root.mkdir()
    receipt_path = receipt_root / (
        "scalp_micro_reversion_registration_receipt_2026-09-04.json"
    )
    receipt = {
        "schema": "scalp_micro_reversion_registration_receipt_v1",
        "effective_date": "2026-09-04",
        "configured_at": configured_at.isoformat(),
        "configured_at_epoch": configured_at.timestamp(),
        "registration_transport_epoch": 1,
        "source": "test_exact_manifest",
        "decision_authority": "market_data_source_quality_only",
        "runtime_effect": False,
        "trading_runtime_effect": False,
        "trading_decision_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "requested_registration_items": ["005930", "005930_NX"],
        "items": {
            "005930": {
                "required_realtime_types": ["0B", "0D"],
                "received_realtime_types": ["0B", "0D"],
                "first_received_at_epoch_by_type": {"0B": first_0b, "0D": first_0d},
                "last_received_at_epoch": last_received,
                "receipt_count_by_type": {"0B": 1, "0D": 1},
                "transport_epochs": [1],
                "max_interarrival_gap_sec": 1.0,
            },
            "005930_NX": {
                "required_realtime_types": ["0B", "0D"],
                "received_realtime_types": ["0B"],
                "first_received_at_epoch_by_type": {"0B": first_0b},
                "last_received_at_epoch": first_0b,
                "receipt_count_by_type": {"0B": 1},
                "transport_epochs": [1],
                "max_interarrival_gap_sec": 0.0,
            },
        },
        "summary": {"max_interarrival_gap_sec": 3.0},
    }
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")

    blocked = attribution_module._runtime_registration_receipt_status(
        "2026-09-04",
        collection_target_root=tmp_path / "targets",
        receipt_root=receipt_root,
    )
    assert blocked["ready"] is False
    assert blocked["global_contract_ready"] is True
    assert blocked["route_isolation_allowed"] is True
    assert blocked["status"] == "active_route_receipt_incomplete"
    assert blocked["complete_registration_items"] == ["005930"]
    assert blocked["incomplete_registration_items"] == ["005930_NX"]

    krx_binding = _runtime_registration_receipt_binding(
        {"symbol": "005930", "expected_venues": ["KRX"]}, blocked
    )
    nxt_binding = _runtime_registration_receipt_binding(
        {"symbol": "005930", "expected_venues": ["NXT"]}, blocked
    )
    assert krx_binding["status"] == "exact_route_complete"
    assert krx_binding["source_gap_reason"] is None
    assert krx_binding["route_isolated"] is False
    assert nxt_binding["status"] == "exact_route_receipt_incomplete"
    assert nxt_binding["source_gap_reason"] == (
        "micro_runtime_registration_receipt_exact_route_incomplete"
    )
    assert nxt_binding["route_isolated"] is True

    receipt["items"]["005930_NX"] = {
        "required_realtime_types": ["0B", "0D"],
        "received_realtime_types": ["0B", "0D"],
        "first_received_at_epoch_by_type": {"0B": first_0b, "0D": first_0d},
        "last_received_at_epoch": last_received,
        "receipt_count_by_type": {"0B": 1, "0D": 1},
        "transport_epochs": [1],
        "max_interarrival_gap_sec": 1.0,
    }
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    ready = attribution_module._runtime_registration_receipt_status(
        "2026-09-04",
        collection_target_root=tmp_path / "targets",
        receipt_root=receipt_root,
    )
    assert ready["status"] == "complete"
    assert ready["ready"] is True

    receipt["configured_at"] = "2026-09-03T07:55:00+09:00"
    receipt["configured_at_epoch"] -= 86400
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    stale = attribution_module._runtime_registration_receipt_status(
        "2026-09-04",
        collection_target_root=tmp_path / "targets",
        receipt_root=receipt_root,
    )
    assert stale["ready"] is False
    assert stale["global_contract_ready"] is False
    assert stale["temporal_contract_valid"] is False
    assert stale["status"] == "contract_invalid"

    receipt["configured_at"] = configured_at.isoformat()
    receipt["configured_at_epoch"] = configured_at.timestamp()
    receipt["items"]["005930_NX"]["first_received_at_epoch_by_type"]["0D"] = 1e300
    receipt["items"]["005930_NX"]["last_received_at_epoch"] = 1e300
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    invalid_epoch = attribution_module._runtime_registration_receipt_status(
        "2026-09-04",
        collection_target_root=tmp_path / "targets",
        receipt_root=receipt_root,
    )
    assert invalid_epoch["global_contract_ready"] is True
    assert invalid_epoch["ready"] is False
    assert invalid_epoch["incomplete_active_registration_items"] == ["005930_NX"]

    receipt["items"]["005930_NX"]["first_received_at_epoch_by_type"] = {
        "0B": first_0b,
        "0D": first_0d,
    }
    receipt["items"]["005930_NX"]["last_received_at_epoch"] = last_received
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    future_at_evaluation = attribution_module._runtime_registration_receipt_status(
        "2026-09-04",
        collection_target_root=tmp_path / "targets",
        receipt_root=receipt_root,
        evaluated_at=configured_at + timedelta(seconds=1),
    )
    assert future_at_evaluation["global_contract_ready"] is True
    assert future_at_evaluation["ready"] is False
    assert future_at_evaluation["incomplete_active_registration_items"] == [
        "005930",
        "005930_NX",
    ]

    receipt["configured_at"] = (configured_at + timedelta(minutes=1)).isoformat()
    receipt["configured_at_epoch"] = (configured_at + timedelta(minutes=1)).timestamp()
    receipt_path.write_text(json.dumps(receipt), encoding="utf-8")
    future_configuration = attribution_module._runtime_registration_receipt_status(
        "2026-09-04",
        collection_target_root=tmp_path / "targets",
        receipt_root=receipt_root,
        evaluated_at=configured_at,
    )
    assert future_configuration["global_contract_ready"] is False
    assert future_configuration["temporal_contract_valid"] is False


def test_runtime_registration_receipt_does_not_block_on_prospective_receive_gap(
    monkeypatch, tmp_path
):
    configured_at = datetime(2026, 9, 4, 7, 55, tzinfo=KST)
    first_0b = configured_at.timestamp() + 1
    first_0d = configured_at.timestamp() + 2
    last_received = configured_at.timestamp() + 3
    monkeypatch.setattr(
        attribution_module,
        "load_exact_date_collection_targets",
        lambda target_date, root: {
            "status": "loaded",
            "path": str(root / f"targets-{target_date}.json"),
            "registration_items": ["005930", "000660_NX"],
            "payload": {
                "selected_targets": [
                    {
                        "active_owner": True,
                        "registration_items": ["005930"],
                    },
                    {
                        "active_owner": False,
                        "registration_items": ["000660_NX"],
                    },
                ]
            },
        },
    )
    receipt_root = tmp_path / "receipts"
    receipt_root.mkdir()
    receipt = {
        "schema": "scalp_micro_reversion_registration_receipt_v1",
        "effective_date": "2026-09-04",
        "configured_at": configured_at.isoformat(),
        "configured_at_epoch": configured_at.timestamp(),
        "registration_transport_epoch": 1,
        "source": "test_prospective_gap",
        "decision_authority": "market_data_source_quality_only",
        "runtime_effect": False,
        "trading_runtime_effect": False,
        "trading_decision_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "requested_registration_items": ["000660_NX", "005930"],
        "items": {
            "005930": {
                "required_realtime_types": ["0B", "0D"],
                "received_realtime_types": ["0B", "0D"],
                "first_received_at_epoch_by_type": {"0B": first_0b, "0D": first_0d},
                "last_received_at_epoch": last_received,
                "receipt_count_by_type": {"0B": 1, "0D": 1},
                "transport_epochs": [1],
                "max_interarrival_gap_sec": 1.0,
            },
            "000660_NX": {
                "received_realtime_types": [],
                "first_received_at_epoch_by_type": {},
                "last_received_at_epoch": None,
                "receipt_count_by_type": {},
                "transport_epochs": [],
            },
        },
        "summary": {"max_interarrival_gap_sec": 3.0},
    }
    (
        receipt_root / "scalp_micro_reversion_registration_receipt_2026-09-04.json"
    ).write_text(json.dumps(receipt), encoding="utf-8")

    status = attribution_module._runtime_registration_receipt_status(
        "2026-09-04",
        collection_target_root=tmp_path / "targets",
        receipt_root=receipt_root,
    )

    assert status["ready"] is True
    assert status["global_contract_ready"] is True
    assert status["status"] == "complete_with_prospective_route_gaps"
    assert status["incomplete_registration_items"] == ["000660_NX"]
    assert status["incomplete_active_registration_items"] == []


def test_registration_receipt_route_gap_excludes_only_bound_anchor():
    receipt = {
        "status": "active_route_receipt_incomplete",
        "global_contract_ready": True,
        "expected_registration_items": ["005930", "005930_NX"],
        "complete_registration_items": ["005930"],
    }
    krx_anchor = {
        "anchor_id": "krx-entry",
        "symbol": "005930",
        "expected_venues": ["KRX"],
        "anchor_at": "2026-09-04T10:00:00+09:00",
        "owner_lifecycle_contract_valid": True,
        "owner_policy_tuning_eligible": True,
    }
    nxt_anchor = {
        **krx_anchor,
        "anchor_id": "nxt-entry",
        "expected_venues": ["NXT"],
    }
    inventory = {"observed_row_count": 1, "invalid_contract_scope_counts": {}}
    window = {
        "rows": [
            {
                "timestamp": datetime(2026, 9, 4, 10, 0, tzinfo=KST),
                "price": 10000,
                "best_bid": 9990,
                "best_ask": 10000,
                "sequence_epoch": 1,
            }
        ],
        "depth_points": [],
        "depth_rows": 0,
        "shock_reference_count": 0,
        "raw_market_rows": [],
        "raw_depth_rows": [],
    }

    krx_result = _anchor_result(
        krx_anchor,
        inventory,
        window,
        partition_loaded=True,
        source_contract_gap=None,
        clean_baseline_allowed=True,
        registration_receipt_binding=_runtime_registration_receipt_binding(
            krx_anchor, receipt
        ),
    )
    nxt_result = _anchor_result(
        nxt_anchor,
        inventory,
        window,
        partition_loaded=True,
        source_contract_gap=None,
        clean_baseline_allowed=True,
        registration_receipt_binding=_runtime_registration_receipt_binding(
            nxt_anchor, receipt
        ),
    )

    assert krx_result["micro_context_status"] == "matched"
    assert krx_result["micro_tuning_input_allowed"] is True
    assert nxt_result["micro_context_status"] == (
        "micro_runtime_registration_receipt_exact_route_incomplete"
    )
    assert nxt_result["micro_tuning_input_allowed"] is False


def test_registration_receipt_gap_is_terminal_for_same_date_rerun():
    recovery = _rolling_source_contract_recovery(
        "micro_runtime_registration_receipt_missing_or_incomplete"
    )

    assert recovery["disposition"] == "immutable_source_date_quarantine"
    assert recovery["rerun_same_source_date_allowed"] is False
    assert recovery["excluded_from_rolling_policy_evidence"] is True




def test_default_completed_target_date_is_stable_for_persistent_catchup():
    assert (
        resolve_completed_machine_target_date(
            now=datetime(2026, 8, 14, 19, 59, tzinfo=KST)
        ).isoformat()
        == "2026-08-13"
    )
    assert (
        resolve_completed_machine_target_date(
            now=datetime(2026, 8, 14, 20, 0, tzinfo=KST)
        ).isoformat()
        == "2026-08-14"
    )
    assert (
        resolve_completed_machine_target_date(
            now=datetime(2026, 8, 15, 7, 0, tzinfo=KST)
        ).isoformat()
        == "2026-08-14"
    )




def test_episode_target_before_buy_fill_is_invalid_and_not_realized(tmp_path):
    target_date = "2026-08-14"
    report_root = tmp_path / "report"
    _write_json(
        report_root
        / "low_price_two_leg_tuning"
        / f"low_price_two_leg_tuning_{target_date}.json",
        {
            "schema": "low_price_two_leg_tuning_report_v3",
            "target_date": target_date,
            "daily": {
                "profiles": {
                    "kakao_morning": {
                        "profile_id": "kakao_morning",
                        "target_date": target_date,
                        "symbol": "035720",
                        "session": "morning",
                        "attempted": True,
                        "eligible_for_tuning": True,
                        "source_quality": "pass",
                        "signal_features": {
                            "signal_bar": "2026-08-14T09:30:00+09:00",
                            "signal_close": 20000,
                        },
                        "legs": [
                            {
                                "leg_id": "one",
                                "buy_filled_qty": 10,
                                "buy_filled_at": "2026-08-14T09:30:10+09:00",
                                "fill_price": 20000,
                                "target_filled_qty": 10,
                                "target_filled_at": "2026-08-14T09:30:09+09:00",
                                "target_fill_price": 20100,
                                "target_price": 20100,
                                "completed": True,
                                "net_profit_pct": 0.3,
                            }
                        ],
                    }
                }
            },
        },
    )
    _write_jsonl(
        tmp_path
        / "observations"
        / f"trade_date={target_date}"
        / "venue=SOR"
        / "session=SOR_REGULAR"
        / "market_stream.jsonl",
        [_micro_row("035720", "2026-08-14T09:30:11+09:00", 20000)],
    )

    report = build_report(
        target_date,
        report_root=report_root,
        observation_root=tmp_path / "observations",
    )

    row = report["consumers"]["episode_machine_postclose_tuning"]["profiles"][
        "kakao_morning"
    ]
    assert row["owner_anchor_contract_status"] == "invalid"
    assert row["owner_policy_tuning_eligible"] is False
    assert "one:target_fill_before_buy_fill" in row["lifecycle_instrumentation_gaps"]
    assert not any(
        item["anchor_role"] == "episode_target_fill_confirmed"
        for item in row["anchor_results"]
    )
    assert (
        report["fast_lifecycle_objective_alignment"]["lifecycle_coverage"][
            "realized_owner_outcome_count"
        ]
        == 0
    )






def test_exact_date_canary_archive_is_immutable_when_latest_advances(tmp_path):
    target_date = datetime(2026, 8, 14, tzinfo=KST).date()
    latest = tmp_path / "latest.json"
    daily_root = tmp_path / "daily"
    payload = {
        "schema": "scalp_micro_reversion_canary_monitor_v1",
        "generated_at": "2026-08-14T20:10:00+09:00",
        "valid_until_epoch": datetime(2026, 8, 14, 20, 11, tzinfo=KST).timestamp(),
        "canary_guard": {
            "status": "healthy_observer_canary",
            "stop_required": False,
            "raw_row_exclusion_required": False,
        },
        "collector_snapshot": {
            "collector_lifecycle": "running",
            "sequence_epoch": 1,
            "selection_authority": False,
            "trading_runtime_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        },
    }
    _write_json(latest, payload)
    archived = archive_exact_date_canary_snapshot(
        target_date=target_date,
        source_path=latest,
        daily_root=daily_root,
        now=datetime(2026, 8, 14, 20, 10, tzinfo=KST),
    )
    assert archived is not None
    payload["generated_at"] = "2026-08-15T07:00:00+09:00"
    _write_json(latest, payload)

    report = build_attribution_report(
        target_date.isoformat(),
        report_root=tmp_path / "report",
        observation_root=tmp_path / "observations",
        canary_snapshot_path=latest,
        canary_snapshot_dir=daily_root,
        now=datetime(2026, 8, 15, 7, 0, tzinfo=KST),
    )

    source = report["sources"]["micro_reversion"]["canary_source_quality"]
    assert source["path"] == str(archived)
    assert source["status"] == "loaded_pass"

    payload["generated_at"] = "2026-08-14T20:30:00+09:00"
    payload["valid_until_epoch"] = datetime(2026, 8, 14, 20, 31, tzinfo=KST).timestamp()
    payload["canary_guard"].update({"status": "stop_required", "stop_required": True})
    _write_json(latest, payload)
    failed_latest = build_attribution_report(
        target_date.isoformat(),
        report_root=tmp_path / "report",
        observation_root=tmp_path / "observations",
        canary_snapshot_path=latest,
        canary_snapshot_dir=daily_root,
        now=datetime(2026, 8, 14, 20, 30, tzinfo=KST),
    )
    failed_source = failed_latest["sources"]["micro_reversion"]["canary_source_quality"]
    assert failed_source["path"] == str(latest)
    assert failed_source["status"] == "missing_or_invalid"


def test_stopped_clean_canary_requires_closed_reconciled_collector(tmp_path):
    target_date = datetime(2026, 8, 14, tzinfo=KST).date()
    latest = tmp_path / "latest.json"
    payload = {
        "schema": "scalp_micro_reversion_canary_monitor_v1",
        "generated_at": "2026-08-14T20:10:00+09:00",
        "canary_guard": {
            "status": "stopped_clean",
            "stop_required": False,
            "raw_row_exclusion_required": False,
        },
        "collector_snapshot": {
            "collector_lifecycle": "close_failed",
            "reference_reconciliation_completed": True,
            "sequence_epoch": 1,
            "selection_authority": False,
            "trading_runtime_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        },
    }
    _write_json(latest, payload)

    archived = archive_exact_date_canary_snapshot(
        target_date=target_date,
        source_path=latest,
        daily_root=tmp_path / "daily",
        now=datetime(2026, 8, 14, 20, 10, tzinfo=KST),
    )
    assert archived is None
    report = build_attribution_report(
        target_date.isoformat(),
        report_root=tmp_path / "report",
        observation_root=tmp_path / "observations",
        canary_snapshot_path=latest,
        canary_snapshot_dir=tmp_path / "daily",
        now=datetime(2026, 8, 14, 20, 10, tzinfo=KST),
    )
    source = report["sources"]["micro_reversion"]["canary_source_quality"]
    assert source["status"] == "missing_or_invalid"
    assert source["stopped_clean_closed"] is False

    payload["canary_guard"] = ["malformed"]
    payload["collector_snapshot"] = "malformed"
    _write_json(latest, payload)
    malformed = build_attribution_report(
        target_date.isoformat(),
        report_root=tmp_path / "report",
        observation_root=tmp_path / "observations",
        canary_snapshot_path=latest,
        canary_snapshot_dir=tmp_path / "daily",
        now=datetime(2026, 8, 14, 20, 10, tzinfo=KST),
    )
    assert (
        malformed["sources"]["micro_reversion"]["canary_source_quality"]["status"]
        == "missing_or_invalid"
    )


def test_early_stop_canary_is_archived_as_diagnostic_only(tmp_path):
    target_date = datetime(2026, 8, 19, tzinfo=KST).date()
    latest = tmp_path / "latest.json"
    daily_root = tmp_path / "daily"
    payload = {
        "schema": "scalp_micro_reversion_canary_monitor_v1",
        "generated_at": "2026-08-19T09:03:55+09:00",
        "valid_until_epoch": datetime(2026, 8, 19, 9, 4, tzinfo=KST).timestamp(),
        "canary_guard": {
            "status": "stop_required",
            "stop_required": True,
            "stop_reasons": ["nonzero_stop_metric:observation_queue_full_count=82"],
            "raw_row_exclusion_required": False,
        },
        "collector_snapshot": {
            "collector_lifecycle": "closed",
            "reference_reconciliation_completed": True,
            "sequence_epoch": 1,
            "selection_authority": False,
            "trading_runtime_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        },
    }
    _write_json(latest, payload)

    archived = archive_exact_date_canary_snapshot(
        target_date=target_date,
        source_path=latest,
        daily_root=daily_root,
        now=datetime(2026, 8, 19, 20, 10, tzinfo=KST),
    )

    assert archived is not None
    archived_payload = json.loads(archived.read_text(encoding="utf-8"))
    assert archived_payload["archive_validation"] == {
        "schema": "scalp_micro_reversion_canary_archive_validation_v1",
        "target_date": "2026-08-19",
        "archived_at_kst": "2026-08-19T20:10:00+09:00",
        "target_day_complete": False,
        "source_fresh_at_archive": False,
        "source_generated_not_after_archive": True,
        "source_valid_until_epoch": payload["valid_until_epoch"],
        "diagnostic_only": True,
        "promotion_evidence_eligible": False,
    }
    payload["generated_at"] = "2026-08-20T07:00:00+09:00"
    _write_json(latest, payload)
    report = build_attribution_report(
        target_date.isoformat(),
        report_root=tmp_path / "report",
        observation_root=tmp_path / "observations",
        canary_snapshot_path=latest,
        canary_snapshot_dir=daily_root,
        now=datetime(2026, 8, 20, 7, 0, tzinfo=KST),
    )
    source = report["sources"]["micro_reversion"]["canary_source_quality"]
    assert source["path"] == str(archived)
    assert source["status"] == "target_date_evidence_incomplete"
    assert source["stop_required"] is True


def test_queue_loss_canary_is_archived_without_promotion_authority(tmp_path):
    target_date = datetime(2026, 8, 20, tzinfo=KST).date()
    latest = tmp_path / "latest.json"
    payload = {
        "schema": "scalp_micro_reversion_canary_monitor_v1",
        "generated_at": "2026-08-20T20:10:00+09:00",
        "valid_until_epoch": datetime(2026, 8, 20, 20, 11, tzinfo=KST).timestamp(),
        "canary_guard": {
            "status": "healthy_observer_canary_with_source_row_exclusions",
            "stop_required": False,
            "stop_reasons": [],
            "raw_row_exclusion_required": True,
            "source_quality_row_exclusions": [
                "raw_row_exclusion_required:observation_queue_full_count=1"
            ],
        },
        "collector_snapshot": {
            "collector_lifecycle": "running",
            "sequence_epoch": 1,
            "selection_authority": False,
            "trading_runtime_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        },
    }
    _write_json(latest, payload)

    archived = archive_exact_date_canary_snapshot(
        target_date=target_date,
        source_path=latest,
        daily_root=tmp_path / "daily",
        now=datetime(2026, 8, 20, 20, 10, tzinfo=KST),
    )

    assert archived is not None
    archive_validation = json.loads(archived.read_text(encoding="utf-8"))[
        "archive_validation"
    ]
    assert archive_validation["diagnostic_only"] is True
    assert archive_validation["promotion_evidence_eligible"] is False


def _timestamp_quarantine_canary_payload(target_date: str) -> dict:
    zero_fields = {field: 0 for field in attribution_module.CANARY_LOSS_COUNTERS}
    forbidden_true_fields = {
        field: False for field in attribution_module.CANARY_FORBIDDEN_TRUE_FIELDS
    }
    return {
        "schema": "scalp_micro_reversion_canary_monitor_v1",
        "generated_at": f"{target_date}T20:10:00+09:00",
        "canary_guard": {
            "status": "stopped_clean",
            "stop_required": False,
            "stop_reasons": [],
            "raw_row_exclusion_required": True,
            "source_quality_row_exclusions": [
                "raw_row_exclusion_required:"
                "path_exchange_timestamp_regression_exceeded_count=5"
            ],
        },
        "collector_snapshot": {
            **zero_fields,
            **forbidden_true_fields,
            "collector_lifecycle": "closed",
            "reference_reconciliation_completed": True,
            "sequence_epoch": 1,
            "selection_authority": False,
            "trading_runtime_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "depth_capture_requested": True,
            "path_exchange_timestamp_regression_count": 116,
            "path_exchange_timestamp_regression_quarantined_count": 111,
            "path_exchange_timestamp_regression_exceeded_count": 5,
            "enqueued_count": 1000,
            "worker_processed_count": 1000,
            "writer_persisted_envelope_count": 1000,
            "path_point_submitted_count": 1000,
            "depth_enqueued_count": 200,
            "depth_worker_processed_count": 200,
            "depth_writer_persisted_envelope_count": 200,
            "metric_contracts": {
                "exchange_timestamp_regression_canary": {
                    "metric_role": ("source_quality_incident_and_raw_row_exclusion"),
                    "decision_authority": "observer_row_quarantine_only",
                    "primary_decision_metric": (
                        "path_exchange_timestamp_regression_exceeded_count"
                    ),
                    "source_quality_gate": (
                        "affected_rows_remain_path_consumer_ineligible_and_are_"
                        "skipped_by_p2_reconstruction_without_imputation"
                    ),
                    "forbidden_uses": [
                        "detector_or_path_consumption_of_quarantined_row",
                        "broker_order_submission",
                    ],
                }
            },
        },
    }


def _pre_enqueue_canary_payload(target_date="2026-09-09"):
    from src.engine.scalping.micro_reversion.canary_monitor import (
        timestamp_source_quality_census,
    )

    payload = _timestamp_quarantine_canary_payload(target_date)
    c = payload["collector_snapshot"]
    c.update(
        {
            "sequence_epoch": 2,
            "stale_sequence_epoch_envelope_count": 0,
            "path_exchange_timestamp_regression_count": 0,
            "path_exchange_timestamp_regression_quarantined_count": 0,
            "path_exchange_timestamp_regression_exceeded_count": 0,
            "invalid_exchange_timestamp_count": 0,
            "invalid_depth_timestamp_count": 1,
            "stale_exchange_timestamp_block_count": 0,
            "timestamp_rejection_sample_total": 1,
            "timestamp_rejection_samples": [
                {
                    "process_pid": 10,
                    "symbol": "999999",
                    "item": "999999",
                    "venue": "KRX",
                    "realtime_type": "0D",
                    "local_observer_epoch": 1,
                    "checked_at_ms": 1788932500000,
                    "reason": "invalid_or_future_timestamp",
                    "rejection_stage": "before_observer_enqueue",
                    "rejection_index": 1,
                }
            ],
        }
    )
    census = timestamp_source_quality_census(c)
    payload["canary_guard"]["timestamp_source_quality"] = census
    payload["canary_guard"]["source_quality_row_exclusions"] = census["issues"]
    return payload


@pytest.mark.parametrize(
    "defect",
    [None, "loss", "missing", "authority", "receipt", "epoch", "persistence", "mixed"],
)
def test_pre_enqueue_quarantine_requires_closed_exact_epoch_evidence(defect):
    payload = _pre_enqueue_canary_payload()
    g, c = payload["canary_guard"], payload["collector_snapshot"]
    if defect == "loss":
        c["observation_queue_full_count"] = 1
    if defect == "missing":
        c.pop("writer_error_count")
    if defect == "authority":
        c["trading_runtime_effect"] = True
    if defect == "receipt":
        c["timestamp_rejection_samples"][0]["rejection_index"] = 2
    if defect == "epoch":
        c["timestamp_rejection_samples"][0]["local_observer_epoch"] = 3
    if defect == "persistence":
        c["depth_worker_processed_count"] = 0
    if defect == "mixed":
        g["source_quality_row_exclusions"].append("unknown_loss")
    result = attribution_module.closed_pre_enqueue_epoch_quarantine_validation(g, c)
    assert result["eligible"] is (defect is None)
    if defect is None:
        assert result["allowed_sequence_epoch"] == 2
        assert result["whole_date_approval"] is False
    assert _timestamp_regression_row_quarantine_validation(g, c)["eligible"] is False


def test_pre_enqueue_consumer_fences_market_depth_and_reference_epochs(tmp_path):
    day = "2026-09-09"
    root = tmp_path / "observations"
    partition = root / f"trade_date={day}" / "venue=KRX" / "session=KRX_REGULAR"
    stamp = f"{day}T15:00:00+09:00"
    _write_jsonl(
        partition / "market_stream.jsonl",
        [
            _micro_row("999999", stamp, 10000, venue="KRX", sequence_epoch=e)
            for e in (1, 2, 3)
        ],
    )
    _write_jsonl(
        partition / "market_depth_stream.jsonl",
        [_depth_row("999999", stamp, sequence_epoch=e) for e in (1, 2, 3)],
    )
    # Excluded references cannot reach the reference validator or an anchor join.
    _write_jsonl(
        partition / "market_stream_event_references.jsonl",
        [
            {
                "symbol": "999999",
                "venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "sequence_epoch": e,
            }
            for e in (1, 3)
        ],
    )
    canary = tmp_path / "canary.json"
    _write_json(canary, _pre_enqueue_canary_payload(day))
    source, inventory, _ = _micro_context(
        day,
        root,
        {"999999"},
        [],
        attribution_module.DEFAULT_SOURCE_EXCLUSION_MANIFEST,
        canary,
        datetime(2026, 9, 9, 20, 20, tzinfo=KST),
    )
    assert source["source_contract_ready"] is True
    assert source["canary_source_quality"]["whole_date_approval"] is False
    assert source["unverified_canary_epoch_row_counts"] == {"1": 3, "3": 3}
    assert inventory["999999"]["eligible_row_count"] == 1
    assert inventory["999999"]["depth_row_count"] == 1
    assert inventory["999999"]["source_excluded_row_count"] == 6


def test_overlapping_windows_share_raw_source_rows_without_value_drift(tmp_path):
    day = "2026-09-15"
    root = tmp_path / "observations"
    partition = root / f"trade_date={day}" / "venue=KRX" / "session=KRX_REGULAR"
    stamp = f"{day}T10:00:00+09:00"
    market_row = _micro_row("999999", stamp, 10_000, venue="KRX")
    depth_row = _depth_row("999999", stamp)
    _write_jsonl(partition / "market_stream.jsonl", [market_row])
    _write_jsonl(partition / "market_depth_stream.jsonl", [depth_row])

    common_anchor = {
        "symbol": "999999",
        "anchor_at": stamp,
        "anchor_role": "episode_signal_decision_leg",
        "expected_venues": ["KRX"],
        "expected_session_buckets": ["KRX_REGULAR"],
    }
    _, _, windows = _micro_context(
        day,
        root,
        {"999999"},
        [
            {**common_anchor, "anchor_id": "overlap-a"},
            {**common_anchor, "anchor_id": "overlap-b"},
        ],
        tmp_path / "missing-exclusion-manifest.json",
        None,
        datetime(2026, 9, 15, 20, 20, tzinfo=KST),
    )

    first = windows["overlap-a"]
    second = windows["overlap-b"]
    assert first["raw_market_rows"] == second["raw_market_rows"]
    assert first["raw_depth_rows"] == second["raw_depth_rows"]
    assert first["raw_market_rows"][0]["symbol"] == market_row["symbol"]
    assert first["raw_market_rows"][0]["trade_price"] == market_row["trade_price"]
    assert first["raw_depth_rows"][0]["symbol"] == depth_row["symbol"]
    assert first["raw_depth_rows"][0]["bid_levels"] == depth_row["bid_levels"]
    assert first["raw_market_rows"][0] is second["raw_market_rows"][0]
    assert first["raw_depth_rows"][0] is second["raw_depth_rows"][0]
    assert first["rows"][0] is second["rows"][0]
    assert first["depth_points"][0] is second["depth_points"][0]


def test_timestamp_regression_only_row_quarantine_preserves_remaining_date_source(
    tmp_path,
):
    target_date = "2026-09-04"
    payload = _timestamp_quarantine_canary_payload(target_date)
    canary_path = tmp_path / "canary.json"
    _write_json(canary_path, payload)

    validation = _timestamp_regression_row_quarantine_validation(
        payload["canary_guard"], payload["collector_snapshot"]
    )
    source, _, _ = _micro_context(
        target_date,
        tmp_path / "observations",
        set(),
        [],
        attribution_module.DEFAULT_SOURCE_EXCLUSION_MANIFEST,
        canary_path,
        datetime(2026, 9, 4, 20, 20, tzinfo=KST),
    )

    assert validation == {
        "eligible": True,
        "status": "fully_accounted_consumer_ineligible_rows",
        "quarantined_row_count": 5,
        "invalid_loss_fields": [],
    }
    assert source["canary_source_quality"]["status"] == (
        "loaded_pass_with_row_quarantine"
    )
    assert source["source_contract_ready"] is True


def test_timestamp_row_quarantine_never_masks_capture_loss():
    payload = _timestamp_quarantine_canary_payload("2026-09-04")
    payload["collector_snapshot"]["observation_queue_full_count"] = 1

    validation = _timestamp_regression_row_quarantine_validation(
        payload["canary_guard"], payload["collector_snapshot"]
    )

    assert validation["eligible"] is False
    assert validation["status"] == "capture_loss_or_missing_counter"
    assert validation["invalid_loss_fields"] == ["observation_queue_full_count"]


def test_v3_stream_requires_aware_full_contract_while_v2_is_legacy_compatible():
    v3 = _micro_row("999999", "2026-08-14T10:00:00+09:00", 10000)
    v3["local_receive_timestamp"] = "2026-08-14T10:00:00"
    assert _validate_stream_row(v3)[0] is False

    v2 = _micro_row("999999", "2026-08-14T10:00:00+09:00", 10000)
    v2["schema"] = "scalp_micro_reversion_market_stream_point_v2"
    for field in (
        "metric_contract_id",
        "source_sequence",
        "series_sequence",
        "sequence_epoch",
        "realtime_type",
        "path_order_status",
        "path_consumer_eligible",
        "exchange_timestamp_regression_ms",
    ):
        v2.pop(field, None)
    valid, eligible, *_ = _validate_stream_row(v2)
    assert valid is True
    assert eligible is True


def test_future_generated_canary_cannot_be_archived_or_pass_source_gate(tmp_path):
    target_date = datetime(2026, 8, 14, tzinfo=KST).date()
    latest = tmp_path / "latest.json"
    payload = {
        "schema": "scalp_micro_reversion_canary_monitor_v1",
        "generated_at": "2026-08-14T23:59:00+09:00",
        "valid_until_epoch": datetime(2026, 8, 15, 0, 0, tzinfo=KST).timestamp(),
        "canary_guard": {
            "status": "healthy_observer_canary",
            "stop_required": False,
            "raw_row_exclusion_required": False,
        },
        "collector_snapshot": {
            "collector_lifecycle": "running",
            "sequence_epoch": 1,
            "selection_authority": False,
            "trading_runtime_effect": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        },
    }
    _write_json(latest, payload)

    assert (
        archive_exact_date_canary_snapshot(
            target_date=target_date,
            source_path=latest,
            daily_root=tmp_path / "daily",
            now=datetime(2026, 8, 14, 20, 5, tzinfo=KST),
        )
        is None
    )
    report = build_attribution_report(
        target_date.isoformat(),
        report_root=tmp_path / "report",
        observation_root=tmp_path / "observations",
        canary_snapshot_path=latest,
        canary_snapshot_dir=tmp_path / "daily",
        now=datetime(2026, 8, 14, 20, 5, tzinfo=KST),
    )
    assert (
        report["sources"]["micro_reversion"]["canary_source_quality"]["status"]
        == "missing_or_invalid"
    )


def test_lifecycle_summary_separates_actual_and_counterfactual_cohorts():
    base = {
        "micro_context_status": "matched",
        "lifecycle_stage": "entry",
        "anchor_role": "counterfactual_calibration_entry",
        "owner_lifecycle_contract_valid": True,
    }
    summary = _lifecycle_objective_summary(
        [
            {
                **base,
                "anchor_id": "widget:one",
                "lifecycle_id": "widget:one",
                "actual_order_submitted": False,
                "owner_outcome": {
                    "holding_duration_ms": 60_000,
                    "gross_no_slippage_return_pct": 0.5,
                    "cost_aware_net_return_pct": 0.3,
                    "realized": True,
                },
            },
            {
                **base,
                "anchor_id": "episode:one",
                "lifecycle_id": "episode:one",
                "anchor_role": "episode_signal_bar",
                "actual_order_submitted": True,
                "owner_outcome": {
                    "leg_id": "one",
                    "holding_duration_ms": 120_000,
                    "gross_no_slippage_return_pct": 0.4,
                    "cost_aware_net_return_pct": 0.2,
                    "realized": True,
                },
            },
            {
                **base,
                "anchor_id": "widget:right-censored",
                "lifecycle_id": "widget:right-censored",
                "actual_order_submitted": False,
                "owner_outcome": {
                    "holding_duration_ms": 10_000,
                    "gross_no_slippage_return_pct": None,
                    "cost_aware_net_return_pct": None,
                    "realized": False,
                },
            },
            {
                **base,
                "micro_context_status": "micro_anchor_window_not_observed",
                "anchor_id": "episode:unmatched",
                "lifecycle_id": "episode:unmatched",
                "anchor_role": "episode_signal_bar",
                "actual_order_submitted": True,
                "owner_outcome": {
                    "leg_id": "one",
                    "holding_duration_ms": 1_000,
                    "gross_no_slippage_return_pct": 9.9,
                    "cost_aware_net_return_pct": 9.8,
                    "realized": True,
                },
            },
        ]
    )

    assert summary["identified"] is True
    assert summary["lifecycle_coverage"]["realized_owner_outcome_count"] == 2
    assert summary["lifecycle_coverage"]["timed_owner_outcome_count"] == 2
    assert (
        summary["lifecycle_coverage"]["owner_outcome_not_micro_attributed_count"] == 1
    )
    assert summary["gross_no_slippage_diagnostic"]["avg_return_pct"] is None
    assert (
        summary["cost_aware_owner_outcome_diagnostic"]["equal_weight_avg_profit_pct"]
        is None
    )
    assert (
        summary["gross_no_slippage_diagnostic"]["cohorts"]["actual_episode_execution"][
            "gross_no_slippage_avg_return_pct"
        ]
        == 0.4
    )
    assert (
        summary["gross_no_slippage_diagnostic"]["cohorts"][
            "source_only_counterfactual"
        ]["gross_no_slippage_avg_return_pct"]
        == 0.5
    )


def _objective_bound_candidate(
    candidate_id: str,
    resolved_gap_codes: list[str],
    *,
    followup_id: str = FAST_LIFECYCLE_OBJECTIVE_FOLLOWUP_ID,
) -> dict:
    return {
        "candidate_id": candidate_id,
        "objective_followup_binding": {
            "schema": OBJECTIVE_CANDIDATE_BINDING_SCHEMA,
            "followup_id": followup_id,
            "resolved_gap_codes": resolved_gap_codes,
        },
    }


def test_fast_lifecycle_followup_requires_one_exact_bound_candidate():
    objective = _lifecycle_objective_summary([])
    implementation = _fast_lifecycle_objective_followup(
        target_date="2026-08-14",
        objective_alignment=objective,
        promotion_candidates=[],
    )
    assert implementation["state"] == "IMPLEMENTATION_REQUIRED"
    assert implementation["followup_required"] is True
    assert implementation["operator_decision_required"] is False

    accumulating_objective = json.loads(json.dumps(objective))
    accumulating_objective["implementation_boundary"][
        "rolling_paired_policy_candidate_producer_present"
    ] = True
    accumulating = _fast_lifecycle_objective_followup(
        target_date="2026-08-14",
        objective_alignment=accumulating_objective,
        promotion_candidates=[{"candidate_id": "unbound-candidate"}],
    )
    assert accumulating["state"] == "EVIDENCE_ACCUMULATING"
    assert accumulating["followup_required"] is True
    assert "candidate_handoff_binding" not in accumulating

    unrelated = _fast_lifecycle_objective_followup(
        target_date="2026-08-14",
        objective_alignment=objective,
        promotion_candidates=[
            _objective_bound_candidate(
                "unrelated",
                list(objective["remaining_gaps"]),
                followup_id="other_objective",
            )
        ],
    )
    assert unrelated["state"] == "IMPLEMENTATION_REQUIRED"

    required_gaps = list(objective["remaining_gaps"])
    objective_candidate = _objective_bound_candidate(
        "fast-lifecycle-bound-candidate", required_gaps
    )
    handoff = _fast_lifecycle_objective_followup(
        target_date="2026-08-14",
        objective_alignment=objective,
        promotion_candidates=[objective_candidate],
    )
    assert handoff["state"] == "CANDIDATE_QUEUE_HANDOFF"
    assert handoff["followup_required"] is False
    assert handoff["remaining_gap_codes"] == []
    assert handoff["candidate_handoff_binding"]["candidate_id"] == (
        "fast-lifecycle-bound-candidate"
    )
    assert handoff["candidate_handoff_binding"]["required_gap_codes"] == (required_gaps)
    assert len(handoff["candidate_handoff_binding"]["candidate_sha256"]) == 64

    ambiguous = _fast_lifecycle_objective_followup(
        target_date="2026-08-14",
        objective_alignment=objective,
        promotion_candidates=[
            objective_candidate,
            _objective_bound_candidate("second-bound-candidate", required_gaps),
        ],
    )
    assert ambiguous["state"] == "IMPLEMENTATION_REQUIRED"
    assert ambiguous["followup_required"] is True
    assert "candidate_handoff_binding" not in ambiguous


def test_fast_lifecycle_followup_allows_only_explicit_empty_gap_binding():
    objective = _lifecycle_objective_summary([])
    no_gap_objective = json.loads(json.dumps(objective))
    no_gap_objective["implementation_boundary"][
        "rolling_paired_policy_candidate_producer_present"
    ] = True
    no_gap_objective["remaining_gaps"] = []

    missing_binding = _fast_lifecycle_objective_followup(
        target_date="2026-08-14",
        objective_alignment=no_gap_objective,
        promotion_candidates=[{"candidate_id": "unbound-empty-gap-candidate"}],
    )
    assert missing_binding["state"] == "EVIDENCE_ACCUMULATING"
    assert missing_binding["followup_required"] is True

    handoff = _fast_lifecycle_objective_followup(
        target_date="2026-08-14",
        objective_alignment=no_gap_objective,
        promotion_candidates=[_objective_bound_candidate("bound-empty-gap", [])],
    )
    assert handoff["state"] == "CANDIDATE_QUEUE_HANDOFF"
    assert handoff["candidate_handoff_binding"]["required_gap_codes"] == []


def test_fast_lifecycle_followup_does_not_transfer_non_handoff_runtime_gap():
    objective = _lifecycle_objective_summary([])
    objective["implementation_boundary"][
        "rolling_paired_policy_candidate_producer_present"
    ] = True
    objective["remaining_gaps"] = ["post_apply_attribution_pending"]

    followup = _fast_lifecycle_objective_followup(
        target_date="2026-08-14",
        objective_alignment=objective,
        promotion_candidates=[_objective_bound_candidate("bound-candidate", [])],
    )

    assert followup["state"] == "EVIDENCE_ACCUMULATING"
    assert followup["followup_required"] is True
    assert followup["remaining_gap_codes"] == ["post_apply_attribution_pending"]
    assert "candidate_handoff_binding" not in followup


def test_fast_lifecycle_complete_is_source_declared_without_queue_evidence():
    completed_objective = _lifecycle_objective_summary([])

    completed_objective["reflected_in_real_runtime_policy"] = True
    completed_objective["implementation_boundary"][
        "speed_or_turnover_metric_changes_policy_selection"
    ] = True
    completed_objective["remaining_gaps"] = []
    completed = _fast_lifecycle_objective_followup(
        target_date="2026-08-14",
        objective_alignment=completed_objective,
        promotion_candidates=[],
    )
    assert completed["state"] == "COMPLETE"
    assert completed["followup_required"] is False
    assert "completion_evidence" not in completed














def test_irreversible_current_source_gap_requests_quarantine_not_rerun():
    objective = _lifecycle_objective_summary([])
    objective["implementation_boundary"][
        "rolling_paired_policy_candidate_producer_present"
    ] = True
    objective["remaining_gaps"] = ["current_attribution_source_contract_invalid"]
    objective["current_source_contract_recovery"] = _rolling_source_contract_recovery(
        "micro_canary_target_date_evidence_incomplete"
    )

    followup = _fast_lifecycle_objective_followup(
        target_date="2026-08-19",
        objective_alignment=objective,
        promotion_candidates=[],
    )

    assert followup["state"] == "EVIDENCE_ACCUMULATING"
    assert followup["next_action"] == (
        "quarantine_current_source_date_and_continue_next_exact_date_collection"
    )
    assert (
        followup["source_contract_recovery"]["rerun_same_source_date_allowed"] is False
    )












@pytest.mark.parametrize(
    "defect",
    [None, "running", "loss", "missing_counter", "claimed_row_receipt", "mixed_reason"],
)
def test_closed_ingress_loss_is_quarantine_only_and_requires_complete_evidence(defect):
    payload = _timestamp_quarantine_canary_payload("2026-09-07")
    guard, collector = payload["canary_guard"], payload["collector_snapshot"]
    issue = "timestamp_source_rejected_before_enqueue:invalid_depth_timestamp_count=2"
    guard["source_quality_row_exclusions"] = [issue]
    guard["timestamp_source_quality"] = {
        "counts": {
            "invalid_depth_timestamp_count": 2,
            "invalid_exchange_timestamp_count": 0,
            "stale_exchange_timestamp_block_count": 0,
        },
        "issues": [issue],
        "exact_rejected_row_exclusion_proven": False,
        "rejection_stage": "before_observer_enqueue",
    }
    if defect == "running":
        collector["collector_lifecycle"] = "running"
    if defect == "loss":
        collector["writer_error_count"] = 1
    if defect == "missing_counter":
        collector.pop("writer_error_count")
    if defect == "claimed_row_receipt":
        guard["timestamp_source_quality"]["exact_rejected_row_exclusion_proven"] = True
    if defect == "mixed_reason":
        guard["source_quality_row_exclusions"].append(None)
    assert attribution_module._closed_ingress_receipt_loss(guard, collector) is (
        defect is None
    )
    # Irrecoverable input remains forbidden as evidence even when terminally classified.
    assert (
        _timestamp_regression_row_quarantine_validation(guard, collector)["eligible"]
        is False
    )


def test_closed_ingress_loss_followup_does_not_retry_immutable_date():
    gap = "micro_canary_source_quality_missing_or_invalid"
    assert (
        _rolling_source_contract_recovery(gap)["rerun_same_source_date_allowed"] is True
    )
    recovery = _rolling_source_contract_recovery(
        gap, immutable_ingress_receipt_loss=True
    )
    assert recovery["rerun_same_source_date_allowed"] is False
    assert recovery["excluded_from_rolling_policy_evidence"] is True
    assert recovery["disposition"] == "immutable_source_date_quarantine"
    assert (
        _rolling_source_contract_recovery(
            "micro_source_exclusion_manifest_missing_or_invalid",
            immutable_ingress_receipt_loss=True,
        )["rerun_same_source_date_allowed"]
        is True
    )


def test_exact_date_attribution_reuse_invalidates_when_source_directory_changes(
    tmp_path,
):
    source_root = tmp_path / "source"
    source_root.mkdir()
    (source_root / "one.json").write_text("{}\n", encoding="utf-8")
    generation = attribution_module._source_generation_contract(
        {"micro": {"partition": str(source_root)}}
    )
    generation["source_date"] = "2026-09-14"
    report = {
        "schema": attribution_module.REPORT_SCHEMA,
        "target_date": "2026-09-14",
        "status": "warning",
        "summary": {},
        "authority": {"runtime_effect": False},
        "source_generation": generation,
    }
    report_path = tmp_path / "report.json"
    report_path.write_text(json.dumps(report), encoding="utf-8")

    assert (
        attribution_module._reusable_exact_date_report(
            report_path, target_date="2026-09-14"
        )
        == report
    )
    (source_root / "two.json").write_text("{}\n", encoding="utf-8")
    assert (
        attribution_module._reusable_exact_date_report(
            report_path, target_date="2026-09-14"
        )
        is None
    )
