import gzip
import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.engine.monitoring.machine_microstructure_attribution import (
    _lifecycle_objective_summary,
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

KST = ZoneInfo("Asia/Seoul")


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
            else f"{symbol}_NX"
            if venue == "NXT"
            else symbol
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


def test_dynamic_widget_symbol_is_matched_without_changing_owner_policy(tmp_path):
    target_date = "2026-08-14"
    report_root = tmp_path / "report"
    observation_root = tmp_path / "observations"
    _write_json(
        report_root
        / "widget_auto_trade_policy_calibration"
        / f"widget_auto_trade_policy_calibration_{target_date}.json",
        {
            "schema": "widget_auto_trade_policy_calibration_report_v1",
            "target_date": target_date,
            "symbols": {
                "999999": {
                    "name": "dynamic",
                    "sessions": {
                        "KRX_REGULAR": {
                            "selected_trades": [
                                {
                                    "trade_date": target_date,
                                    "entry_at": "2026-08-14T10:00:00+09:00",
                                    "entry_price": 10000,
                                    "exit_reason": "right_censored",
                                }
                            ]
                        }
                    },
                },
            },
        },
    )
    _write_jsonl(
        observation_root
        / f"trade_date={target_date}"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl",
        [
            _micro_row(
                "999999",
                "2026-08-14T10:00:01+09:00",
                9900,
                eligible=False,
                venue="KRX",
            ),
            _micro_row("999999", "2026-08-14T10:00:02+09:00", 9950, venue="KRX"),
            _micro_row("999999", "2026-08-14T10:00:03+09:00", 10100, venue="KRX"),
        ],
    )

    report = build_report(
        target_date,
        report_root=report_root,
        observation_root=observation_root,
        now=datetime(2026, 8, 14, 21, 0, tzinfo=KST),
    )

    row = report["consumers"]["widget_postclose_tuning"]["symbols"]["999999"]
    assert row["owner_inventory_source"] == "target_date_postclose_report"
    assert row["micro_context_status"] == "matched"
    assert row["micro_tuning_input_allowed"] is True
    assert row["base_owner_tuning_effect"] is False
    assert row["micro_source_inventory"]["ineligible_row_count"] == 1
    assert row["anchor_results"][0]["metrics"]["mfe_bps"] == 100.0
    assert report["authority"]["runtime_effect"] is False
    assert report["authority"]["allowed_runtime_apply"] is False
    assert report["policy_promotion_candidates"] == []
    assert (
        report["promotion_candidate_intake_contract"]["consumer"]
        == "src.engine.automation.machine_microstructure_policy_approval"
    )


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
    assert report["collection_feedback"]["selected_symbol_count"] == 4
    assert report["collection_feedback"]["overflow_symbol_count"] > 0
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
            "schema": "low_price_two_leg_tuning_report_v3",
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


def test_report_writer_creates_json_and_markdown(tmp_path):
    report = {
        "target_date": "2026-08-14",
        "status": "warning",
        "decision": "partial_owner_or_micro_source_gap_base_tuning_unchanged",
        "summary": {
            "dynamic_symbol_count": 1,
            "widget_symbol_count": 1,
            "episode_profile_count": 0,
            "anchor_count": 0,
            "matched_anchor_count": 0,
            "producer_consumer_gap_count": 1,
        },
        "producer_consumer_gaps": [
            {
                "owner": "widget",
                "scope_id": "999999",
                "symbol": "999999",
                "gap_class": "micro_symbol_not_observed",
                "effect": "micro_context_unavailable_base_owner_tuning_unchanged",
            }
        ],
    }
    json_path, md_path = write_report(report, tmp_path)

    assert json.loads(json_path.read_text(encoding="utf-8"))["status"] == "warning"
    assert "Missing micro data is not imputed" in md_path.read_text(encoding="utf-8")


def test_invalid_source_exclusion_manifest_blocks_only_micro_context(tmp_path):
    target_date = "2026-08-14"
    report_root = tmp_path / "report"
    observation_root = tmp_path / "observations"
    _write_json(
        report_root
        / "widget_auto_trade_policy_calibration"
        / f"widget_auto_trade_policy_calibration_{target_date}.json",
        {
            "schema": "widget_auto_trade_policy_calibration_report_v1",
            "target_date": target_date,
            "symbols": {
                "999999": {
                    "sessions": {
                        "KRX_REGULAR": {
                            "selected_trades": [
                                {
                                    "trade_date": target_date,
                                    "entry_at": "2026-08-14T10:00:00+09:00",
                                    "entry_price": 10000,
                                }
                            ]
                        }
                    }
                }
            },
        },
    )
    _write_jsonl(
        observation_root
        / f"trade_date={target_date}"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl",
        [_micro_row("999999", "2026-08-14T10:00:01+09:00", 10050, venue="KRX")],
    )

    report = build_report(
        target_date,
        report_root=report_root,
        observation_root=observation_root,
        source_exclusion_manifest_path=tmp_path / "missing_manifest.json",
        now=datetime(2026, 8, 14, 21, 0, tzinfo=KST),
    )

    row = report["consumers"]["widget_postclose_tuning"]["symbols"]["999999"]
    assert (
        row["micro_context_status"]
        == "micro_source_exclusion_manifest_missing_or_invalid"
    )
    assert row["micro_tuning_input_allowed"] is False
    assert row["base_owner_tuning_effect"] is False


def test_exact_date_canary_source_quality_is_required_when_requested(tmp_path):
    target_date = "2026-08-14"
    report_root = tmp_path / "report"
    observation_root = tmp_path / "observations"
    _write_json(
        report_root
        / "widget_auto_trade_policy_calibration"
        / f"widget_auto_trade_policy_calibration_{target_date}.json",
        {
            "schema": "widget_auto_trade_policy_calibration_report_v1",
            "target_date": target_date,
            "symbols": {
                "999999": {
                    "sessions": {
                        "KRX_REGULAR": {
                            "selected_trades": [
                                {
                                    "trade_date": target_date,
                                    "entry_at": "2026-08-14T10:00:00+09:00",
                                    "entry_price": 10000,
                                    "exit_reason": "right_censored",
                                }
                            ]
                        }
                    }
                }
            },
        },
    )
    _write_jsonl(
        observation_root
        / f"trade_date={target_date}"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl",
        [_micro_row("999999", "2026-08-14T10:00:01+09:00", 10050, venue="KRX")],
    )
    canary_path = tmp_path / "canary.json"

    missing = build_attribution_report(
        target_date,
        report_root=report_root,
        observation_root=observation_root,
        canary_snapshot_path=canary_path,
        canary_snapshot_dir=tmp_path / "daily_canary",
        now=datetime(2026, 8, 14, 20, 10, tzinfo=KST),
    )
    missing_row = missing["consumers"]["widget_postclose_tuning"]["symbols"]["999999"]
    assert missing_row["micro_context_status"] == (
        "micro_canary_target_date_evidence_unavailable"
    )

    _write_json(
        canary_path,
        {
            "schema": "scalp_micro_reversion_canary_monitor_v1",
            "generated_at": "2026-08-14T17:00:00+09:00",
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
        },
    )
    incomplete = build_attribution_report(
        target_date,
        report_root=report_root,
        observation_root=observation_root,
        canary_snapshot_path=canary_path,
        canary_snapshot_dir=tmp_path / "daily_canary",
        now=datetime(2026, 8, 14, 20, 10, tzinfo=KST),
    )
    incomplete_row = incomplete["consumers"]["widget_postclose_tuning"]["symbols"][
        "999999"
    ]
    assert incomplete_row["micro_context_status"] == (
        "micro_canary_target_date_evidence_incomplete"
    )
    assert (
        incomplete["sources"]["micro_reversion"]["canary_source_quality"]["status"]
        == "target_date_evidence_incomplete"
    )

    payload = json.loads(canary_path.read_text(encoding="utf-8"))
    payload["generated_at"] = "2026-08-14T20:10:00+09:00"
    _write_json(canary_path, payload)
    healthy = build_attribution_report(
        target_date,
        report_root=report_root,
        observation_root=observation_root,
        canary_snapshot_path=canary_path,
        canary_snapshot_dir=tmp_path / "daily_canary",
        now=datetime(2026, 8, 14, 20, 10, tzinfo=KST),
    )
    healthy_row = healthy["consumers"]["widget_postclose_tuning"]["symbols"]["999999"]
    assert healthy_row["micro_context_status"] == "matched"
    assert (
        healthy["sources"]["micro_reversion"]["canary_source_quality"]["status"]
        == "loaded_pass"
    )

    payload = json.loads(canary_path.read_text(encoding="utf-8"))
    payload["valid_until_epoch"] = datetime(2026, 8, 14, 20, 9, tzinfo=KST).timestamp()
    _write_json(canary_path, payload)
    stale = build_attribution_report(
        target_date,
        report_root=report_root,
        observation_root=observation_root,
        canary_snapshot_path=canary_path,
        canary_snapshot_dir=tmp_path / "daily_canary",
        now=datetime(2026, 8, 14, 20, 10, tzinfo=KST),
    )
    stale_row = stale["consumers"]["widget_postclose_tuning"]["symbols"]["999999"]
    assert stale_row["micro_context_status"] == (
        "micro_canary_target_date_evidence_stale"
    )

    payload["generated_at"] = "2026-08-15T07:00:00+09:00"
    _write_json(canary_path, payload)
    newer_latest = build_attribution_report(
        target_date,
        report_root=report_root,
        observation_root=observation_root,
        canary_snapshot_path=canary_path,
        canary_snapshot_dir=tmp_path / "daily_canary",
        now=datetime(2026, 8, 14, 20, 10, tzinfo=KST),
    )
    newer_row = newer_latest["consumers"]["widget_postclose_tuning"]["symbols"][
        "999999"
    ]
    assert newer_row["micro_context_status"] == (
        "micro_canary_target_date_evidence_unavailable"
    )
    assert (
        newer_latest["sources"]["micro_reversion"]["canary_source_quality"]["status"]
        == "target_date_evidence_unavailable"
    )


def test_widget_late_expansion_report_adds_dynamic_symbol(tmp_path):
    target_date = "2026-08-14"
    report_root = tmp_path / "report"
    _write_json(
        report_root
        / "widget_collector_expansion_recommendation"
        / f"widget_collector_expansion_recommendation_{target_date}.json",
        {
            "schema": "widget_collector_expansion_recommendation_v1",
            "target_date": target_date,
            "recommendations": [
                {
                    "stock_code": "123456",
                    "stock_name": "late candidate",
                    "recommendation_tier": "research_watch",
                }
            ],
        },
    )

    report = build_report(
        target_date,
        report_root=report_root,
        observation_root=tmp_path / "observations",
        now=datetime(2026, 8, 14, 21, 30, tzinfo=KST),
    )

    row = report["consumers"]["widget_postclose_tuning"]["symbols"]["123456"]
    assert "prospective_widget_collector_expansion" in row["scopes"]
    assert row["owner_inventory_source"] == "target_date_postclose_report"
    assert row["micro_context_status"] == "micro_date_partition_missing"


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
                    "doosan_enerbility_morning": {
                        "profile_id": "doosan_enerbility_morning",
                        "target_date": target_date,
                        "symbol": "034020",
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
        [_micro_row("034020", "2026-08-14T09:30:00+09:00", 20000)],
    )

    report = build_report(
        target_date,
        report_root=report_root,
        observation_root=tmp_path / "observations",
    )

    row = report["consumers"]["episode_machine_postclose_tuning"]["profiles"][
        "doosan_enerbility_morning"
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
    nested = mismatched["daily"]["profiles"]["doosan_enerbility_morning"]
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
    ]["doosan_enerbility_morning"]
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
                    "doosan_enerbility_morning": {
                        "profile_id": "doosan_enerbility_morning",
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
    known = profiles["doosan_enerbility_morning"]
    assert known["symbol"] == "034020"
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


def test_prospective_widget_and_episode_target_date_episodes_create_anchors(tmp_path):
    target_date = "2026-08-14"
    report_root = tmp_path / "report"
    _write_json(
        report_root
        / "widget_symbol_signal_policy_research"
        / f"widget_symbol_signal_policy_research_{target_date}.json",
        {
            "schema": "widget_symbol_signal_policy_research_v2",
            "end_date": target_date,
            "symbols": {
                "111111": {
                    "name": "widget research",
                    "holdout": {
                        "episodes": [
                            {
                                "trade_date": target_date,
                                "entry_at": "2026-08-14T10:00:00+09:00",
                                "entry_price": 10000,
                                "target_price": 10050,
                                "exit_at": "2026-08-14T10:01:00+09:00",
                                "exit_price": 10050,
                                "exit_reason": "target",
                                "net_return_pct": 0.3,
                            }
                        ]
                    },
                }
            },
        },
    )
    _write_json(
        report_root
        / "low_price_two_leg_expanded_candidate_research"
        / f"low_price_two_leg_expanded_candidate_research_{target_date}.json",
        {
            "schema": "low_price_two_leg_expanded_candidate_research_v5",
            "target_date": target_date,
            "profiles": {
                "candidate_222222_morning": {
                    "profile_id": "candidate_222222_morning",
                    "symbol": "222222",
                    "session": "morning",
                    "selected": {
                        "full": {
                            "episodes": [
                                {
                                    "date": target_date,
                                    "signal_at": "2026-08-14T09:20:00+09:00",
                                    "signal_close": 20000,
                                    "legs": [
                                        {
                                            "entry_price": 20000,
                                            "fill_at": "2026-08-14T09:21:00+09:00",
                                            "target_at": "2026-08-14T09:22:00+09:00",
                                            "target_price": 20100,
                                            "status": "COMPLETE",
                                            "net_profit_pct": 0.3,
                                        }
                                    ],
                                }
                            ]
                        }
                    },
                }
            },
        },
    )
    widget_stream = (
        tmp_path
        / "observations"
        / f"trade_date={target_date}"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl"
    )
    episode_stream = (
        tmp_path
        / "observations"
        / f"trade_date={target_date}"
        / "venue=SOR"
        / "session=SOR_REGULAR"
        / "market_stream.jsonl"
    )
    _write_jsonl(
        widget_stream,
        [
            _micro_row("111111", "2026-08-14T10:00:01+09:00", 10000, venue="KRX"),
            _micro_row("111111", "2026-08-14T10:01:01+09:00", 10050, venue="KRX"),
        ],
    )
    _write_jsonl(
        episode_stream,
        [
            _micro_row("222222", "2026-08-14T09:20:01+09:00", 20000),
            _micro_row("222222", "2026-08-14T09:22:01+09:00", 20100),
        ],
    )

    report = build_report(
        target_date,
        report_root=report_root,
        observation_root=tmp_path / "observations",
    )

    widget = report["consumers"]["widget_postclose_tuning"]["symbols"]["111111"]
    assert widget["expected_venues"] == ["KRX"]
    assert widget["owner_scope_expected_venues"] == {
        "research:111111:KRX_REGULAR": ["KRX"]
    }
    assert {anchor["anchor_role"] for anchor in widget["anchor_results"]} == {
        "prospective_widget_research_entry",
        "prospective_widget_research_exit",
    }
    episode = report["consumers"]["episode_machine_postclose_tuning"]["profiles"][
        "candidate_222222_morning"
    ]
    assert {anchor["anchor_role"] for anchor in episode["anchor_results"]} == {
        "prospective_episode_research_signal",
        "prospective_episode_research_buy_fill",
        "prospective_episode_research_target_fill",
    }
    assert episode["micro_context_status"] == "matched"


def test_depth_context_is_past_only_and_session_exact(tmp_path):
    target_date = "2026-08-14"
    report_root = tmp_path / "report"
    observation_root = tmp_path / "observations"
    _write_json(
        report_root
        / "widget_auto_trade_policy_calibration"
        / f"widget_auto_trade_policy_calibration_{target_date}.json",
        {
            "schema": "widget_auto_trade_policy_calibration_report_v1",
            "target_date": target_date,
            "symbols": {
                "999999": {
                    "sessions": {
                        "KRX_REGULAR": {
                            "selected_trades": [
                                {
                                    "trade_date": target_date,
                                    "entry_at": "2026-08-14T10:00:00+09:00",
                                    "entry_price": 10000,
                                    "exit_reason": "right_censored",
                                }
                            ]
                        }
                    }
                }
            },
        },
    )
    session_dir = (
        observation_root
        / f"trade_date={target_date}"
        / "venue=KRX"
        / "session=KRX_REGULAR"
    )
    _write_jsonl(
        session_dir / "market_stream.jsonl",
        [
            _micro_row(
                "999999",
                "2026-08-14T09:59:59+09:00",
                10000,
                venue="KRX",
                session="KRX_PREMARKET",
            ),
            _micro_row("999999", "2026-08-14T10:00:00+09:00", 10000, venue="KRX"),
        ],
    )
    _write_jsonl(
        session_dir / "market_depth_stream.jsonl",
        [_depth_row("999999", "2026-08-14T10:00:01+09:00")],
    )

    future_only = build_report(
        target_date,
        report_root=report_root,
        observation_root=observation_root,
    )
    metrics = future_only["consumers"]["widget_postclose_tuning"]["symbols"]["999999"][
        "anchor_results"
    ][0]["metrics"]
    assert metrics["eligible_window_row_count"] == 1
    assert metrics["depth_context_covered_row_count"] == 0

    _write_jsonl(
        session_dir / "market_depth_stream.jsonl",
        [
            _depth_row(
                "999999",
                "2026-08-14T09:59:59+09:00",
                sequence_epoch=2,
            )
        ],
    )
    cross_epoch = build_report(
        target_date,
        report_root=report_root,
        observation_root=observation_root,
    )
    cross_epoch_metrics = cross_epoch["consumers"]["widget_postclose_tuning"][
        "symbols"
    ]["999999"]["anchor_results"][0]["metrics"]
    assert cross_epoch_metrics["depth_context_covered_row_count"] == 0

    _write_jsonl(
        session_dir / "market_depth_stream.jsonl",
        [_depth_row("999999", "2026-08-14T09:59:59+09:00")],
    )
    past_only = build_report(
        target_date,
        report_root=report_root,
        observation_root=observation_root,
    )
    past_metrics = past_only["consumers"]["widget_postclose_tuning"]["symbols"][
        "999999"
    ]["anchor_results"][0]["metrics"]
    assert past_metrics["depth_context_covered_row_count"] == 1
    assert past_metrics["depth_window_coverage_pct"] == 100.0

    wrong_item = _depth_row("999999", "2026-08-14T09:59:59+09:00")
    wrong_item["item"] = "111111"
    _write_jsonl(session_dir / "market_depth_stream.jsonl", [wrong_item])
    invalid_depth = build_report(
        target_date,
        report_root=report_root,
        observation_root=observation_root,
    )
    invalid_depth_row = invalid_depth["consumers"]["widget_postclose_tuning"][
        "symbols"
    ]["999999"]
    assert invalid_depth_row["micro_context_status"] == (
        "micro_scope_source_contract_invalid"
    )


def test_rotated_gzip_market_stream_shard_is_consumed(tmp_path):
    target_date = "2026-08-14"
    report_root = tmp_path / "report"
    observation_root = tmp_path / "observations"
    _write_json(
        report_root
        / "widget_auto_trade_policy_calibration"
        / f"widget_auto_trade_policy_calibration_{target_date}.json",
        {
            "schema": "widget_auto_trade_policy_calibration_report_v1",
            "target_date": target_date,
            "symbols": {
                "999999": {
                    "sessions": {
                        "KRX_REGULAR": {
                            "selected_trades": [
                                {
                                    "trade_date": target_date,
                                    "entry_at": "2026-08-14T10:00:00+09:00",
                                    "entry_price": 10000,
                                    "exit_reason": "right_censored",
                                }
                            ]
                        }
                    }
                }
            },
        },
    )
    session_dir = (
        observation_root
        / f"trade_date={target_date}"
        / "venue=KRX"
        / "session=KRX_REGULAR"
    )
    _write_jsonl(session_dir / "market_stream.jsonl", [])
    shard = session_dir / "market_stream.part-000001.jsonl.gz"
    shard.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(shard, "wt", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                _micro_row("999999", "2026-08-14T10:00:01+09:00", 10050, venue="KRX")
            )
            + "\n"
        )

    report = build_report(
        target_date,
        report_root=report_root,
        observation_root=observation_root,
    )

    row = report["consumers"]["widget_postclose_tuning"]["symbols"]["999999"]
    assert row["micro_context_status"] == "matched"
    assert report["sources"]["micro_reversion"]["market_stream_file_count"] == 2


def test_nontrading_attribution_skips_collection_feedback_write_contract(tmp_path):
    report = build_report(
        "2026-08-16",
        report_root=tmp_path / "report",
        observation_root=tmp_path / "observations",
    )

    assert report["collection_feedback"] == {
        "schema": "scalp_micro_reversion_collection_targets_v1",
        "effective_date": None,
        "status": "source_date_not_krx_trading_day_write_skipped",
        "selected_symbol_count": 0,
        "repair_gap_selected_symbol_count": 0,
        "policy_sample_selected_symbol_count": 0,
        "overflow_symbol_count": 0,
        "manual_control_exclusion_applied": False,
        "market_data_subscription_effect": False,
        "trading_runtime_effect": False,
    }


def test_prior_owner_diagnostic_handoff_is_exact_date_and_fail_closed(tmp_path):
    report_dir = tmp_path / "machine"
    prior_date = "2026-08-13"
    payload = {
        "schema": "machine_microstructure_attribution_v1",
        "target_date": prior_date,
        "status": "warning",
        "authority": {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        },
        "consumers": {
            "widget_postclose_tuning": {"symbols": {"999999": {"ok": True}}},
            "episode_machine_postclose_tuning": {"profiles": {}},
        },
    }
    _write_json(
        report_dir / f"machine_microstructure_attribution_{prior_date}.json",
        payload,
    )

    loaded = load_prior_owner_diagnostic(
        target_date=datetime(2026, 8, 14, tzinfo=KST).date(),
        owner="widget",
        report_dir=report_dir,
    )
    assert loaded["status"] == "loaded"
    assert loaded["source_date"] == prior_date
    assert loaded["selection_effect"] is False
    assert loaded["owner_payload"]["symbols"]["999999"]["ok"] is True

    payload["authority"]["broker_order_forbidden"] = False
    _write_json(
        report_dir / f"machine_microstructure_attribution_{prior_date}.json",
        payload,
    )
    invalid = load_prior_owner_diagnostic(
        target_date=datetime(2026, 8, 14, tzinfo=KST).date(),
        owner="widget",
        report_dir=report_dir,
    )
    assert invalid["status"] == "invalid"
    assert invalid["owner_payload"] is None


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


def test_widget_exit_before_entry_is_contract_gap_not_fast_realized_outcome(tmp_path):
    target_date = "2026-08-14"
    report_root = tmp_path / "report"
    _write_json(
        report_root
        / "widget_auto_trade_policy_calibration"
        / f"widget_auto_trade_policy_calibration_{target_date}.json",
        {
            "schema": "widget_auto_trade_policy_calibration_report_v1",
            "target_date": target_date,
            "symbols": {
                "999999": {
                    "sessions": {
                        "KRX_REGULAR": {
                            "selected_trades": [
                                {
                                    "trade_date": target_date,
                                    "entry_at": "2026-08-14T10:00:00+09:00",
                                    "entry_price": 10000,
                                    "exit_at": "2026-08-14T09:59:59+09:00",
                                    "exit_price": 10050,
                                    "exit_reason": "fixed_average_take_profit",
                                    "gross_return_pct": 0.5,
                                    "net_return_pct": 0.3,
                                }
                            ]
                        }
                    }
                }
            },
        },
    )
    _write_jsonl(
        tmp_path
        / "observations"
        / f"trade_date={target_date}"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl",
        [_micro_row("999999", "2026-08-14T10:00:01+09:00", 10000, venue="KRX")],
    )

    report = build_report(
        target_date,
        report_root=report_root,
        observation_root=tmp_path / "observations",
    )

    row = report["consumers"]["widget_postclose_tuning"]["symbols"]["999999"]
    assert row["micro_context_status"] == "owner_anchor_contract_invalid"
    assert [item["lifecycle_stage"] for item in row["anchor_results"]] == ["entry"]
    objective = report["fast_lifecycle_objective_alignment"]
    assert objective["identified"] is False
    assert objective["lifecycle_coverage"]["realized_owner_outcome_count"] == 0
    assert objective["gross_no_slippage_diagnostic"]["completed_within_180s_count"] == 0


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


def test_invalid_micro_row_isolated_by_scope_but_unscoped_invalid_fails_closed(
    tmp_path,
):
    target_date = "2026-08-14"
    report_root = tmp_path / "report"
    stream_path = (
        tmp_path
        / "observations"
        / f"trade_date={target_date}"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl"
    )
    nxt_stream_path = (
        tmp_path
        / "observations"
        / f"trade_date={target_date}"
        / "venue=NXT"
        / "session=NXT_REGULAR"
        / "market_stream.jsonl"
    )
    _write_json(
        report_root
        / "widget_auto_trade_policy_calibration"
        / f"widget_auto_trade_policy_calibration_{target_date}.json",
        {
            "schema": "widget_auto_trade_policy_calibration_report_v1",
            "target_date": target_date,
            "symbols": {
                "999999": {
                    "sessions": {
                        "KRX_REGULAR": {
                            "selected_trades": [
                                {
                                    "trade_date": target_date,
                                    "entry_at": "2026-08-14T10:00:00+09:00",
                                    "entry_price": 10000,
                                    "exit_reason": "right_censored",
                                }
                            ]
                        }
                    }
                }
            },
        },
    )
    invalid_nxt = _micro_row(
        "999999",
        "2026-08-14T10:00:01+09:00",
        10000,
        venue="NXT",
        session="NXT_REGULAR",
    )
    invalid_nxt["best_bid"] = 10100
    invalid_nxt["best_ask"] = 10000
    valid_krx = _micro_row("999999", "2026-08-14T10:00:02+09:00", 10000, venue="KRX")
    _write_jsonl(stream_path, [valid_krx])
    _write_jsonl(nxt_stream_path, [invalid_nxt])

    isolated = build_report(
        target_date,
        report_root=report_root,
        observation_root=tmp_path / "observations",
    )
    isolated_row = isolated["consumers"]["widget_postclose_tuning"]["symbols"]["999999"]
    assert isolated_row["micro_context_status"] == "matched"
    assert isolated_row["micro_source_inventory"]["invalid_contract_row_count"] == 1

    unscoped = dict(invalid_nxt)
    unscoped.pop("venue")
    unscoped.pop("session_bucket")
    _write_jsonl(stream_path, [unscoped, valid_krx])
    _write_jsonl(nxt_stream_path, [])
    blocked = build_report(
        target_date,
        report_root=report_root,
        observation_root=tmp_path / "observations",
    )
    blocked_row = blocked["consumers"]["widget_postclose_tuning"]["symbols"]["999999"]
    assert blocked_row["micro_context_status"] == (
        "micro_scope_source_contract_invalid"
    )


def test_row_cannot_claim_a_different_scope_than_its_physical_partition(tmp_path):
    target_date = "2026-08-14"
    report_root = tmp_path / "report"
    observation_root = tmp_path / "observations"
    _write_json(
        report_root
        / "widget_auto_trade_policy_calibration"
        / f"widget_auto_trade_policy_calibration_{target_date}.json",
        {
            "schema": "widget_auto_trade_policy_calibration_report_v1",
            "target_date": target_date,
            "symbols": {
                "999999": {
                    "sessions": {
                        "SOR_REGULAR": {
                            "selected_trades": [
                                {
                                    "trade_date": target_date,
                                    "entry_at": "2026-08-14T10:00:00+09:00",
                                    "entry_price": 10000,
                                    "exit_reason": "right_censored",
                                }
                            ]
                        }
                    }
                }
            },
        },
    )
    _write_jsonl(
        observation_root
        / f"trade_date={target_date}"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl",
        [_micro_row("999999", "2026-08-14T10:00:01+09:00", 10000)],
    )

    report = build_report(
        target_date,
        report_root=report_root,
        observation_root=observation_root,
    )

    row = report["consumers"]["widget_postclose_tuning"]["symbols"]["999999"]
    assert row["micro_context_status"] == "micro_expected_venue_not_observed"
    assert row["anchor_results"][0]["micro_context_status"] == (
        "micro_anchor_window_not_observed"
    )
    assert row["micro_source_inventory"]["invalid_contract_scope_counts"] == {
        "KRX|KRX_REGULAR": 1
    }
    assert (
        report["sources"]["micro_reversion"]["partition_scope_mismatch_row_count"] == 1
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


def test_wrong_schema_exact_date_owner_report_is_not_consumed(tmp_path):
    target_date = "2026-08-14"
    report_root = tmp_path / "report"
    _write_json(
        report_root
        / "widget_auto_trade_policy_calibration"
        / f"widget_auto_trade_policy_calibration_{target_date}.json",
        {
            "schema": "wrong_owner_report_v1",
            "target_date": target_date,
            "symbols": {"999999": {"sessions": {}}},
        },
    )

    report = build_report(
        target_date,
        report_root=report_root,
        observation_root=tmp_path / "observations",
    )

    assert "999999" not in report["consumers"]["widget_postclose_tuning"]["symbols"]
    assert report["sources"]["widget"]["calibration"]["status"] == ("schema_mismatch")
    assert any(
        gap.get("gap_class") == "owner_source_schema_mismatch"
        for gap in report["producer_consumer_gaps"]
    )


def test_malformed_event_reference_is_explicit_scope_gap_without_timestamp_crash(
    tmp_path,
):
    target_date = "2026-08-14"
    report_root = tmp_path / "report"
    session_dir = (
        tmp_path
        / "observations"
        / f"trade_date={target_date}"
        / "venue=KRX"
        / "session=KRX_REGULAR"
    )
    _write_json(
        report_root
        / "widget_auto_trade_policy_calibration"
        / f"widget_auto_trade_policy_calibration_{target_date}.json",
        {
            "schema": "widget_auto_trade_policy_calibration_report_v1",
            "target_date": target_date,
            "symbols": {
                "999999": {
                    "sessions": {
                        "KRX_REGULAR": {
                            "selected_trades": [
                                {
                                    "trade_date": target_date,
                                    "entry_at": "2026-08-14T10:00:00+09:00",
                                    "entry_price": 10000,
                                    "exit_reason": "right_censored",
                                }
                            ]
                        }
                    }
                }
            },
        },
    )
    _write_jsonl(
        session_dir / "market_stream.jsonl",
        [_micro_row("999999", "2026-08-14T10:00:01+09:00", 10000, venue="KRX")],
    )
    _write_jsonl(
        session_dir / "market_stream_event_references.jsonl",
        [
            {
                "schema": "scalp_micro_reversion_path_event_reference_v2",
                "symbol": "999999",
                "venue": "KRX",
                "session_bucket": "KRX_REGULAR",
                "event_detected_at_ms": 10**100,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "trading_runtime_effect": False,
            }
        ],
    )

    report = build_report(
        target_date,
        report_root=report_root,
        observation_root=tmp_path / "observations",
    )

    row = report["consumers"]["widget_postclose_tuning"]["symbols"]["999999"]
    assert row["micro_context_status"] == "micro_scope_source_contract_invalid"
