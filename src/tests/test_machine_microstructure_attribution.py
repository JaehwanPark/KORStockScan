import gzip
import json
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from src.engine.monitoring.machine_microstructure_attribution import (
    FAST_LIFECYCLE_OBJECTIVE_FOLLOWUP_ID,
    OBJECTIVE_CANDIDATE_BINDING_SCHEMA,
    OBJECTIVE_FOLLOWUP_METRIC_CONTRACT,
    _episode_exit_outcome_provenance,
    _fast_lifecycle_objective_followup,
    _anchor_result,
    _episode_inventory,
    _lifecycle_objective_summary,
    _micro_entry_confirmation_summary,
    _rolling_source_contract_recovery,
    _validate_stream_row,
    _widget_advisory_event_index,
    _widget_actual_execution_inventory,
    _widget_inventory,
    archive_exact_date_canary_snapshot,
    build_report as build_attribution_report,
    load_prior_owner_diagnostic,
    resolve_completed_machine_target_date,
    write_report,
)
from src.engine.scalping.micro_reversion.collection_targets import (
    build_collection_targets,
)
from src.engine.monitoring.widget_comparison_cost import comparison_cost_contract

KST = ZoneInfo("Asia/Seoul")


def test_realized_episode_exit_with_unknown_source_is_not_target_fill():
    provenance = _episode_exit_outcome_provenance(
        {"net_profit_pct": -1.0},
        realized=True,
    )

    assert provenance["exit_execution_class"] == "realized_exit_source_unknown"
    assert provenance["manual_exit_realized"] is False
    assert provenance["autonomous_target_filled"] is False
    assert provenance["realized_loss"] is True


def test_widget_advisory_index_accepts_both_producer_timestamp_suffixes(tmp_path):
    target_date = "2026-08-27"
    path = (
        tmp_path
        / "widget_symbol_advisory_observation"
        / "widget_symbol_advisory_034020_20260827.jsonl"
    )

    def payload(event_id: str, sequence: int, observed_at: str) -> dict:
        return {
            "symbol": "034020",
            "observed_at_kst": observed_at,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "advisory": {"session": "KRX_REGULAR"},
            "episode": {
                "sequence": sequence,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "runtime_effect": False,
            },
            "entry_event": {
                "event_id": event_id,
                "event_type": "ENTRY",
                "episode_sequence": sequence,
                "observed_at": observed_at,
                "state": "ENTRY_READY",
                "entry_price_high": 10_000,
                "target_price": 10_100,
                "structural_support": 9_900,
                "source_quality_status": "PASS",
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "runtime_effect": False,
            },
            "exit_event": None,
        }

    _write_jsonl(
        path,
        [
            payload(
                "034020:2026-08-27:ENTRY:01:091600",
                1,
                "2026-08-27T09:16:00+09:00",
            ),
            payload(
                "034020:2026-08-27:ENTRY:02:20260827095500",
                2,
                "2026-08-27T09:55:00+09:00",
            ),
        ],
    )

    entries, _, episodes, source = _widget_advisory_event_index(
        target_date=target_date,
        report_root=tmp_path,
    )

    assert source["status"] == "loaded"
    assert len(entries) == 2
    assert len(episodes) == 2


def test_widget_advisory_index_blocks_episode_identity_conflict(tmp_path):
    target_date = "2026-08-27"
    path = (
        tmp_path
        / "widget_symbol_advisory_observation"
        / "widget_symbol_advisory_034020_20260827.jsonl"
    )
    common = {
        "symbol": "034020",
        "observed_at_kst": "2026-08-27T09:16:00+09:00",
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "advisory": {"session": "KRX_REGULAR"},
        "episode": {
            "sequence": 1,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "runtime_effect": False,
        },
        "exit_event": None,
    }

    def entry(event_id: str, *, event_sequence: int) -> dict:
        return {
            "event_id": event_id,
            "event_type": "ENTRY",
            "episode_sequence": event_sequence,
            "observed_at": "2026-08-27T09:16:00+09:00",
            "state": "ENTRY_READY",
            "entry_price_high": 10_000,
            "target_price": 10_100,
            "structural_support": 9_900,
            "source_quality_status": "PASS",
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "runtime_effect": False,
        }

    _write_jsonl(
        path,
        [
            {
                **common,
                "entry_event": entry(
                    "034020:2026-08-27:ENTRY:01:091600", event_sequence=1
                ),
            },
            {
                **common,
                "entry_event": entry(
                    "034020:2026-08-27:ENTRY:01:091601", event_sequence=1
                ),
            },
            {
                **common,
                "entry_event": entry(
                    "034020:2026-08-27:ENTRY:01:091602", event_sequence=2
                ),
            },
        ],
    )

    _, _, _, source = _widget_advisory_event_index(
        target_date=target_date,
        report_root=tmp_path,
    )

    assert source["status"] == "contract_invalid"
    assert any(
        value.startswith("advisory_episode_event_conflict:")
        for value in source["contract_errors"]
    )
    assert any(
        value.startswith("advisory_entry_event_invalid:")
        for value in source["contract_errors"]
    )


def test_widget_advisory_index_quarantines_non_scalar_event_fields(tmp_path):
    target_date = "2026-08-27"
    path = (
        tmp_path
        / "widget_symbol_advisory_observation"
        / "widget_symbol_advisory_034020_20260827.jsonl"
    )
    _write_jsonl(
        path,
        [
            {
                "symbol": "034020",
                "observed_at_kst": "2026-08-27T09:16:00+09:00",
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "advisory": {"session": "KRX_REGULAR"},
                "episode": {
                    "sequence": 1,
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "runtime_effect": False,
                },
                "entry_event": {
                    "event_id": "034020:2026-08-27:ENTRY:01:091600",
                    "event_type": "ENTRY",
                    "episode_sequence": {"invalid": 1},
                    "observed_at": "2026-08-27T09:16:00+09:00",
                    "state": {"invalid": "ENTRY_READY"},
                    "entry_price_high": 10_000,
                    "target_price": 10_100,
                    "structural_support": 9_900,
                    "source_quality_status": "PASS",
                    "actual_order_submitted": False,
                    "broker_order_forbidden": True,
                    "runtime_effect": False,
                },
                "exit_event": None,
            }
        ],
    )

    entries, _, _, source = _widget_advisory_event_index(
        target_date=target_date,
        report_root=tmp_path,
    )

    assert entries == {}
    assert source["status"] == "contract_invalid"
    assert any(
        value.startswith("advisory_entry_event_invalid:")
        for value in source["contract_errors"]
    )


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


def test_market_weakness_blocked_signal_uses_depth_backed_1_to_30m_bbo():
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
    assert counterfactual["source_quality_status"] == "eligible"
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


def test_episode_style_widget_signal_joins_advisory_exit_and_daily_cap_observation(
    tmp_path,
):
    target_date = "2026-08-27"
    report_root = tmp_path / "report"
    state_path = tmp_path / "state.json"
    entry_signal_id = "080220:2026-08-27:ENTRY:01:20260827100000"
    exit_signal_id = "080220:2026-08-27:EXIT:01:20260827100100"
    blocked_signal_id = "080220:2026-08-27:ENTRY:02:20260827101000"
    _write_json(
        state_path,
        {
            "schema_version": 1,
            "execution_authority": "operator_directed_widget_auto_trade_v1",
            "active_date": target_date,
            "symbols": {
                "080220": {
                    "entry_signal_id": entry_signal_id,
                    "orders": [
                        {
                            "broker_accepted": True,
                            "order_no": "B1",
                            "order_date": target_date,
                            "side": "BUY",
                            "order_role": "ENTRY_BUY",
                            "signal_id": entry_signal_id,
                            "market_venue": "KRX",
                            "requested_qty": 10,
                            "filled_qty": 10,
                            "fill_price": 10_000,
                            "status": "FILLED",
                            "last_reconciled_at": "2026-08-27T10:00:02+09:00",
                        },
                        {
                            "broker_accepted": True,
                            "order_no": "S1",
                            "order_date": target_date,
                            "side": "SELL",
                            "order_role": "FINAL_EXIT_SELL",
                            "signal_id": exit_signal_id,
                            "parent_entry_signal_id": entry_signal_id,
                            "market_venue": "KRX",
                            "requested_qty": 10,
                            "filled_qty": 10,
                            "fill_price": 9_900,
                            "limit_price": 9_900,
                            "status": "FILLED",
                            "last_reconciled_at": "2026-08-27T10:01:02+09:00",
                        },
                    ],
                }
            },
            "history": [],
        },
    )

    def actual_event(event_type: str, observed_at: str, **fields):
        return {
            "schema": "widget_signal_auto_trade_event_v1",
            "event_type": event_type,
            "observed_at": observed_at,
            "trade_date": target_date,
            "symbol": "080220",
            "execution_authority": "operator_directed_widget_auto_trade_v1",
            "decision_authority": "operator_directed_widget_auto_trade_v1",
            "runtime_effect": True,
            "actual_order_submitted": True,
            "broker_order_forbidden": False,
            **fields,
        }

    _write_jsonl(
        report_root
        / "widget_signal_auto_trade_events"
        / "widget_signal_auto_trade_events_20260827.jsonl",
        [
            actual_event(
                "order_submitted",
                "2026-08-27T10:00:01+09:00",
                order_no="B1",
                order_role="ENTRY_BUY",
                side="BUY",
                requested_qty=10,
                signal_id=entry_signal_id,
                market_venue="KRX",
            ),
            actual_event(
                "order_execution_reconciled",
                "2026-08-27T10:00:02+09:00",
                order_no="B1",
                order_role="ENTRY_BUY",
                side="BUY",
                requested_qty=10,
                filled_qty=10,
                remaining_qty=0,
                fill_price=10_000,
            ),
            actual_event(
                "order_submitted",
                "2026-08-27T10:01:01+09:00",
                order_no="S1",
                order_role="FINAL_EXIT_SELL",
                side="SELL",
                requested_qty=10,
                signal_id=exit_signal_id,
                parent_entry_signal_id=entry_signal_id,
                market_venue="KRX",
            ),
            actual_event(
                "order_execution_reconciled",
                "2026-08-27T10:01:02+09:00",
                order_no="S1",
                order_role="FINAL_EXIT_SELL",
                side="SELL",
                requested_qty=10,
                filled_qty=10,
                remaining_qty=0,
                fill_price=9_900,
            ),
            {
                **actual_event(
                    "entry_blocked_daily_entry_limit",
                    "2026-08-27T10:10:01+09:00",
                    signal_id=blocked_signal_id,
                    completed_entry_count=1,
                ),
                "actual_order_submitted": False,
            },
        ],
    )

    def advisory_row(
        observed_at: str,
        sequence: int,
        *,
        entry_event: dict | None = None,
        exit_event: dict | None = None,
    ) -> dict:
        return {
            "symbol": "080220",
            "observed_at_kst": observed_at,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "advisory": {"session": "KRX_REGULAR"},
            "episode": {
                "sequence": sequence,
                "actual_order_submitted": False,
                "broker_order_forbidden": True,
                "runtime_effect": False,
            },
            "entry_event": entry_event,
            "exit_event": exit_event,
        }

    def entry_event(event_id: str, observed_at: str, state: str, price: int) -> dict:
        return {
            "event_id": event_id,
            "event_type": "ENTRY",
            "observed_at": observed_at,
            "state": state,
            "entry_price_high": price,
            "target_price": price + 100,
            "structural_support": price - 100,
            "source_quality_status": "PASS",
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "runtime_effect": False,
        }

    def exit_event(event_id: str, observed_at: str, reason: str, price: int) -> dict:
        return {
            "event_id": event_id,
            "event_type": "EXIT",
            "observed_at": observed_at,
            "reason": reason,
            "reference_exit_price": price,
            "source_quality_status": "PASS",
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "runtime_effect": False,
        }

    _write_jsonl(
        report_root
        / "widget_symbol_advisory_observation"
        / "widget_symbol_advisory_080220_20260827.jsonl",
        [
            advisory_row(
                "2026-08-27T10:00:00+09:00",
                1,
                entry_event=entry_event(
                    entry_signal_id,
                    "2026-08-27T10:00:00+09:00",
                    "ENTRY_READY",
                    10_000,
                ),
            ),
            advisory_row(
                "2026-08-27T10:01:00+09:00",
                1,
                exit_event=exit_event(
                    exit_signal_id,
                    "2026-08-27T10:01:00+09:00",
                    "confirmed_support_break",
                    9_900,
                ),
            ),
            advisory_row(
                "2026-08-27T10:10:00+09:00",
                2,
                entry_event=entry_event(
                    blocked_signal_id,
                    "2026-08-27T10:10:00+09:00",
                    "ENTRY_CAUTION",
                    9_800,
                ),
            ),
            advisory_row(
                "2026-08-27T10:12:00+09:00",
                2,
                exit_event=exit_event(
                    "080220:2026-08-27:EXIT:02:20260827101200",
                    "2026-08-27T10:12:00+09:00",
                    "target_observed",
                    9_900,
                ),
            ),
        ],
    )

    _, anchors, sources = _widget_inventory(
        target_date,
        report_root,
        widget_state_path=state_path,
    )

    actual_signal = next(
        row for row in anchors if row.get("anchor_role") == "actual_widget_entry_signal"
    )
    outcome = actual_signal["owner_outcome"]
    assert actual_signal["entry_state"] == "ENTRY_READY"
    assert outcome["exit_reason"] == "confirmed_support_break"
    assert outcome["cost_aware_net_return_pct"] == -1.22785
    assert outcome["modeled_total_cost_krw"] == 227.85
    assert outcome["modeled_costs_broker_receipt_exact"] is False
    blocked = sources["actual_execution_events"][
        "blocked_daily_entry_limit_opportunities"
    ]
    assert len(blocked) == 1
    assert blocked[0]["signal_id"] == blocked_signal_id
    assert blocked[0]["source_only_exit_reason"] == "target_observed"
    assert blocked[0]["actual_order_submitted"] is False


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
            "round_trip_cost_pct": 0.2,
            "comparison_cost_contract": comparison_cost_contract(target_date),
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
    assert (
        report["micro_entry_confirmation"]["summary"]["source_quality_blocked_count"]
        == 1
    )
    assert report["market_weakness_entry_response"]["authority"] == {
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "policy_candidate_ready": False,
    }
    assert (
        report["sources"]["market_weakness_response"]["market_weakness_observations"][
            "status"
        ]
        == "no_schema_v2_observation"
    )


def test_widget_calibration_cost_contract_mismatch_blocks_policy_tuning(
    tmp_path: Path,
) -> None:
    target_date = "2026-08-18"
    report_root = tmp_path / "report"
    calibration = {
        "schema": "widget_auto_trade_policy_calibration_report_v1",
        "target_date": target_date,
        "round_trip_cost_pct": 0.23,
        "comparison_cost_contract": {
            **comparison_cost_contract(target_date),
            "contract_sha256": "mismatched",
        },
        "symbols": {
            "999999": {
                "name": "dynamic",
                "sessions": {
                    "KRX_REGULAR": {
                        "selected_trades": [
                            {
                                "trade_date": target_date,
                                "entry_at": "2026-08-18T10:00:00+09:00",
                                "entry_price": 10_000,
                                "exit_reason": "right_censored",
                            }
                        ]
                    }
                },
            }
        },
    }
    _write_json(
        report_root
        / "widget_auto_trade_policy_calibration"
        / f"widget_auto_trade_policy_calibration_{target_date}.json",
        calibration,
    )

    _, anchors, sources = _widget_inventory(
        target_date,
        report_root,
        widget_state_path=tmp_path / "missing_widget_state.json",
    )

    assert anchors[0]["owner_policy_tuning_eligible"] is False
    assert sources["comparison_cost"]["status"] == (
        "calibration_declared_cost_mismatch"
    )
    assert sources["comparison_cost"]["optional_when_absent"] is False


def test_micro_entry_confirmation_keeps_owner_and_entry_state_cohorts_separate():
    def result(owner: str, state: str, role: str) -> dict:
        return {
            "anchor_id": f"{owner}:{state}",
            "lifecycle_id": f"lifecycle:{owner}:{state}",
            "owner": owner,
            "symbol": "005930",
            "session": "KRX_REGULAR",
            "entry_state": state,
            "anchor_role": role,
            "micro_context_status": "matched",
            "actual_order_submitted": owner == "widget",
            "owner_outcome": {
                "realized": True,
                "cost_aware_net_return_pct": 0.1,
            },
            "metrics": {
                "entry_confirmation_bbo_horizons": {
                    str(horizon): {
                        "observed": True,
                        "bid_return_bps": 0.0,
                    }
                    for horizon in (1, 3, 5)
                },
                "entry_ask_depletion": {
                    "source_quality_status": "eligible_source_only_feature_ablation",
                    "source_gap_reasons": [],
                    "horizons": [
                        {
                            "horizon_ms": horizon * 1000,
                            "eligible_for_feature_ablation": True,
                            "refill_ratio": 0.0,
                            "aggressive_buy_trade_backed_ratio": 1.0,
                            "downward_reprice_observed": False,
                        }
                        for horizon in (1, 3, 5)
                    ],
                },
            },
        }

    summary = _micro_entry_confirmation_summary(
        [
            result("widget", "ENTRY_READY", "actual_widget_entry_signal"),
            result("episode", "UNSPECIFIED", "episode_signal_bar"),
        ],
        widget_sources={"actual_execution_events": {}},
        target_date="2026-08-27",
    )

    assert summary["summary"]["owner_state_cohort_count"] == 2
    assert all(
        row["classification"] == "supportive_confirmation_candidate"
        for row in summary["entry_anchors"]
    )
    assert {
        (row["owner"], row["entry_state"]) for row in summary["owner_state_cohorts"]
    } == {("widget", "ENTRY_READY"), ("episode", "UNSPECIFIED")}


def test_daily_cap_reallocation_requires_realized_cost_bound_prior_entry() -> None:
    target_date = "2026-08-27"
    cost_contract = comparison_cost_contract(target_date)

    def result(role: str, anchor_at: str, event_id: str, *, realized: bool) -> dict:
        return {
            "anchor_id": f"{role}:{event_id}",
            "lifecycle_id": f"lifecycle:{event_id}",
            "owner": "widget",
            "symbol": "080220",
            "session": "KRX_REGULAR",
            "entry_state": "ENTRY_READY",
            "anchor_at": anchor_at,
            "anchor_role": role,
            "source_entry_event_id": event_id,
            "micro_context_status": "matched",
            "actual_order_submitted": role == "actual_widget_entry_signal",
            "owner_outcome": {
                "realized": realized,
                "cost_aware_net_return_pct": -1.0 if realized else None,
                "cost_contract_sha256": cost_contract["contract_sha256"],
            },
            "metrics": {
                "entry_confirmation_bbo_horizons": {
                    str(horizon): {"observed": True, "bid_return_bps": 0.0}
                    for horizon in (1, 3, 5)
                },
                "entry_ask_depletion": {
                    "source_gap_reasons": [],
                    "horizons": [
                        {
                            "horizon_ms": horizon * 1000,
                            "eligible_for_feature_ablation": True,
                            "refill_ratio": 0.1,
                            "aggressive_buy_trade_backed_ratio": 0.8,
                            "downward_reprice_observed": False,
                        }
                        for horizon in (1, 3, 5)
                    ],
                },
            },
        }

    blocked_signal_id = "080220:2026-08-27:ENTRY:02:20260827101000"
    opportunity = {
        "symbol": "080220",
        "signal_id": blocked_signal_id,
        "observed_at": "2026-08-27T10:10:00+09:00",
        "session": "KRX_REGULAR",
        "entry_price": 10_000,
        "source_only_exit_price": 10_100,
        "source_only_exit_reason": "target_observed",
    }
    blocked_result = result(
        "actual_widget_daily_cap_blocked_entry_signal",
        "2026-08-27T10:10:00+09:00",
        blocked_signal_id,
        realized=False,
    )

    unresolved = _micro_entry_confirmation_summary(
        [
            result(
                "actual_widget_entry_signal",
                "2026-08-27T10:00:00+09:00",
                "prior",
                realized=False,
            ),
            blocked_result,
        ],
        widget_sources={
            "actual_execution_events": {
                "blocked_daily_entry_limit_opportunities": [opportunity]
            }
        },
        target_date=target_date,
    )
    realized = _micro_entry_confirmation_summary(
        [
            result(
                "actual_widget_entry_signal",
                "2026-08-27T10:00:00+09:00",
                "prior",
                realized=True,
            ),
            blocked_result,
        ],
        widget_sources={
            "actual_execution_events": {
                "blocked_daily_entry_limit_opportunities": [opportunity]
            }
        },
        target_date=target_date,
    )

    assert (
        unresolved["daily_cap_reallocation_observations"][0]["comparison_status"]
        == "source_quality_blocked"
    )
    assert (
        realized["daily_cap_reallocation_observations"][0]["comparison_status"]
        == "source_only_reallocation_evidence_ready"
    )
    assert (
        realized["daily_cap_reallocation_observations"][0]["daily_cap_mutation_allowed"]
        is False
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
            "schema": "widget_symbol_signal_policy_research_v3",
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
            "cost_pct": 0.2,
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
    episode_fill = next(
        anchor
        for anchor in episode["anchor_results"]
        if anchor["anchor_role"] == "prospective_episode_research_buy_fill"
    )
    assert episode_fill["owner_round_trip_cost_pct"] == 0.2
    assert episode_fill["owner_round_trip_cost_provenance"] == (
        "low_price_two_leg_expanded_candidate_research.cost_pct"
    )
    assert episode_fill["owner_outcome"]["entry_notional_krw"] == 20_000
    assert episode_fill["owner_outcome"]["quantity_basis"] == (
        "one_share_normalized_source_only"
    )


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
        "schema": "scalp_micro_reversion_collection_targets_v2",
        "effective_date": None,
        "status": "source_date_not_krx_trading_day_write_skipped",
        "coverage_policy": (
            "all_active_owner_symbols_then_bounded_prospective_rotation"
        ),
        "coverage_stage": "exact_date_target_manifest_selection",
        "runtime_registration_receipt_required": True,
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


def test_actual_widget_execution_journal_is_attributed_as_real_lifecycle(tmp_path):
    target_date = "2026-08-14"
    report_root = tmp_path / "report"
    observation_root = tmp_path / "observations"
    state_path = tmp_path / "widget_state.json"
    signal_id = "005930:2026-08-14:ENTRY:KRX_REGULAR:2026-08-14T10:00:00+09:00"
    _write_json(
        report_root
        / "widget_auto_trade_policy_calibration"
        / f"widget_auto_trade_policy_calibration_{target_date}.json",
        {
            "schema": "widget_auto_trade_policy_calibration_report_v1",
            "target_date": target_date,
            "round_trip_cost_pct": 0.2,
            "symbols": {
                "005930": {
                    "name": "Samsung",
                    "sessions": {"KRX_REGULAR": {"selected_trades": []}},
                }
            },
        },
    )
    _write_json(
        state_path,
        {
            "schema_version": 1,
            "execution_authority": "operator_directed_widget_auto_trade_v1",
            "active_date": target_date,
            "symbols": {
                "005930": {
                    "entry_signal_id": signal_id,
                    "orders": [
                        {
                            "broker_accepted": True,
                            "order_no": "B1",
                            "order_date": target_date,
                            "side": "BUY",
                            "order_role": "ENTRY_BUY",
                            "signal_id": signal_id,
                            "market_venue": "KRX",
                            "broker_execution_venue": "KRX",
                            "requested_qty": 10,
                            "filled_qty": 10,
                            "fill_price": 10_000,
                            "last_reconciled_at": "2026-08-14T10:00:02+09:00",
                        },
                        {
                            "broker_accepted": True,
                            "order_no": "S1",
                            "order_date": target_date,
                            "side": "SELL",
                            "order_role": "FINAL_EXIT_SELL",
                            "signal_id": "EXIT-1",
                            "market_venue": "KRX",
                            "broker_execution_venue": "KRX",
                            "requested_qty": 10,
                            "filled_qty": 10,
                            "fill_price": 10_100,
                            "limit_price": 10_100,
                            "last_reconciled_at": "2026-08-14T10:01:00+09:00",
                        },
                    ],
                }
            },
            "history": [],
        },
    )

    def event(event_type: str, observed_at: str, **fields):
        return {
            "schema": "widget_signal_auto_trade_event_v1",
            "event_type": event_type,
            "observed_at": observed_at,
            "trade_date": target_date,
            "symbol": "005930",
            "name": "Samsung",
            "execution_authority": "operator_directed_widget_auto_trade_v1",
            "decision_authority": "operator_directed_widget_auto_trade_v1",
            "runtime_effect": True,
            "actual_order_submitted": True,
            "broker_order_forbidden": False,
            **fields,
        }

    _write_jsonl(
        report_root
        / "widget_signal_auto_trade_events"
        / "widget_signal_auto_trade_events_20260814.jsonl",
        [
            event(
                "order_submitted",
                "2026-08-14T10:00:01+09:00",
                order_no="B1",
                order_role="ENTRY_BUY",
                side="BUY",
                requested_qty=10,
                signal_id=signal_id,
                market_venue="KRX",
            ),
            event(
                "order_execution_reconciled",
                "2026-08-14T10:00:01.500000+09:00",
                order_no="B1",
                order_role="ENTRY_BUY",
                side="BUY",
                requested_qty=10,
                filled_qty=5,
                remaining_qty=5,
                fill_price=9_950,
                broker_execution_venue="KRX",
            ),
            event(
                "order_execution_reconciled",
                "2026-08-14T10:00:02+09:00",
                order_no="B1",
                order_role="ENTRY_BUY",
                side="BUY",
                requested_qty=10,
                filled_qty=10,
                remaining_qty=0,
                fill_price=10_000,
                broker_execution_venue="KRX",
            ),
            event(
                "order_submitted",
                "2026-08-14T10:00:03+09:00",
                order_no="S1",
                order_role="FINAL_EXIT_SELL",
                side="SELL",
                requested_qty=10,
                signal_id="EXIT-1",
                market_venue="KRX",
            ),
            event(
                "order_execution_reconciled",
                "2026-08-14T10:00:30+09:00",
                order_no="S1",
                order_role="FINAL_EXIT_SELL",
                side="SELL",
                requested_qty=10,
                filled_qty=5,
                remaining_qty=5,
                fill_price=10_050,
                broker_execution_venue="KRX",
            ),
            event(
                "order_execution_reconciled",
                "2026-08-14T10:01:00+09:00",
                order_no="S1",
                order_role="FINAL_EXIT_SELL",
                side="SELL",
                requested_qty=10,
                filled_qty=10,
                remaining_qty=0,
                broker_execution_venue="KRX",
            ),
        ],
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
                "005930", "2026-08-14T10:00:00.500000+09:00", 10_000, venue="KRX"
            ),
            _micro_row(
                "005930", "2026-08-14T10:00:01.600000+09:00", 10_005, venue="KRX"
            ),
            _micro_row(
                "005930", "2026-08-14T10:00:02.500000+09:00", 10_010, venue="KRX"
            ),
            _micro_row(
                "005930", "2026-08-14T10:00:30.500000+09:00", 10_050, venue="KRX"
            ),
            _micro_row(
                "005930", "2026-08-14T10:01:00.500000+09:00", 10_100, venue="KRX"
            ),
        ],
    )

    report = build_report(
        target_date,
        report_root=report_root,
        observation_root=observation_root,
        widget_state_path=state_path,
        now=datetime(2026, 8, 14, 21, 0, tzinfo=KST),
    )

    source = report["sources"]["widget"]["actual_execution_events"]
    assert source["status"] == "loaded"
    assert source["actual_lifecycle_count"] == 1
    actual_scope = report["consumers"]["widget_postclose_tuning"]["symbols"]["005930"][
        "session_contexts"
    ]["actual:005930:KRX_REGULAR"]
    assert actual_scope["micro_context_status"] == "matched"
    assert {row["anchor_role"] for row in actual_scope["anchor_results"]} == {
        "actual_widget_entry_signal",
        "actual_widget_entry_submit_accept_recorded",
        "actual_widget_entry_partial_fill_reconciled",
        "actual_widget_entry_fill_reconciled",
        "actual_widget_exit_submit_accept_recorded",
        "actual_widget_exit_partial_fill_reconciled",
        "actual_widget_exit_fill_reconciled",
    }
    partial_anchor = next(
        row
        for row in actual_scope["anchor_results"]
        if row["anchor_role"] == "actual_widget_entry_partial_fill_reconciled"
    )
    assert partial_anchor["anchor_price"] == 9_950
    full_fill_anchor = next(
        row
        for row in actual_scope["anchor_results"]
        if row["anchor_role"] == "actual_widget_entry_fill_reconciled"
    )
    assert full_fill_anchor["execution_order_role"] == "ENTRY_BUY"
    assert full_fill_anchor["broker_execution_venue"] == "KRX"
    assert full_fill_anchor["owner_round_trip_cost_pct"] == 0.2
    assert report["summary"]["matched_anchor_count_by_stage"]["entry_partial_fill"] == 1
    assert report["summary"]["matched_anchor_count_by_stage"]["entry_submit"] == 1
    assert report["summary"]["matched_anchor_count_by_stage"]["exit_submit"] == 1
    assert report["summary"]["matched_anchor_count_by_stage"]["exit_partial_fill"] == 1
    submit_anchor = next(
        row
        for row in actual_scope["anchor_results"]
        if row["anchor_role"] == "actual_widget_entry_submit_accept_recorded"
    )
    assert "broker_execution_venue" not in submit_anchor
    assert submit_anchor["eventual_broker_execution_venue"] == "KRX"
    objective = report["fast_lifecycle_objective_alignment"]
    actual_cohort = objective["gross_no_slippage_diagnostic"]["cohorts"][
        "actual_widget_execution"
    ]
    assert actual_cohort["realized_sample_count"] == 1
    assert actual_cohort["gross_no_slippage_avg_return_pct"] == 1.0
    actual_outcome = next(
        row["owner_outcome"]
        for row in actual_scope["anchor_results"]
        if row["anchor_role"] == "actual_widget_entry_signal"
    )
    assert actual_outcome["signal_to_entry_submit_record_ms"] == 1_000
    assert actual_outcome["entry_submit_record_to_first_fill_confirmation_ms"] == 500
    assert actual_outcome["entry_execution_venues"] == ["KRX"]
    assert actual_outcome["exit_execution_venues"] == ["KRX"]
    assert actual_outcome["execution_venue_alignment_state"] == "aligned"
    assert (
        actual_outcome["first_fill_confirmation_to_first_exit_submit_record_ms"]
        == 1_500
    )
    assert (
        actual_outcome["first_exit_submit_record_to_final_exit_fill_confirmation_ms"]
        == 57_000
    )
    assert (
        objective["cost_aware_owner_outcome_diagnostic"]["cohorts"][
            "actual_widget_execution"
        ]["equal_weight_avg_profit_pct"]
        == 0.8
    )
    actual_research = next(
        row
        for row in report["rolling_paired_policy_research"]["cohorts"]
        if row["scope_id"] == "actual:005930:KRX_REGULAR"
    )
    assert actual_research["policy_eligible_unique_lifecycle_count"] == 1


def test_actual_widget_manual_partial_exit_is_realized_loss_with_residual_custody(
    tmp_path,
):
    target_date = "2026-08-28"
    report_root = tmp_path / "report"
    state_path = tmp_path / "widget_state.json"
    signal_id = "005930:2026-08-28:ENTRY:KRX_REGULAR:2026-08-28T09:45:00+09:00"
    buy_orders = [
        (
            "B1",
            "ENTRY_BUY",
            264_500,
            "2026-08-28T09:45:01+09:00",
            "2026-08-28T09:45:02+09:00",
        ),
        (
            "B2",
            "SCALE_IN_BUY",
            262_000,
            "2026-08-28T10:03:19+09:00",
            "2026-08-28T10:03:20+09:00",
        ),
        (
            "B3",
            "SCALE_IN_BUY",
            260_500,
            "2026-08-28T10:40:01+09:00",
            "2026-08-28T10:40:02+09:00",
        ),
    ]
    state_orders = []
    for order_no, role, price, _submitted_at, filled_at in buy_orders:
        state_orders.append(
            {
                "broker_accepted": True,
                "order_no": order_no,
                "order_date": target_date,
                "side": "BUY",
                "order_role": role,
                "signal_id": (
                    signal_id if role == "ENTRY_BUY" else f"{signal_id}:{role}"
                ),
                "parent_entry_signal_id": None if role == "ENTRY_BUY" else signal_id,
                "market_venue": "KRX",
                "broker_execution_venue": "KRX",
                "requested_qty": 10,
                "filled_qty": 10,
                "fill_price": price,
                "status": "FILLED",
                "last_reconciled_at": filled_at,
            }
        )
    state_orders.append(
        {
            "broker_accepted": True,
            "order_no": "S1",
            "order_date": target_date,
            "side": "SELL",
            "order_role": "MANUAL_OPERATOR_PARTIAL_EXIT",
            "signal_id": f"{signal_id}:MANUAL_PARTIAL_EXIT:10",
            "parent_entry_signal_id": signal_id,
            "market_venue": "NXT",
            "broker_execution_venue": "NXT",
            "requested_qty": 10,
            "filled_qty": 10,
            "fill_price": 256_500,
            "status": "FILLED",
            "last_reconciled_at": "2026-08-28T18:36:25+09:00",
            "operator_authority": "explicit_user_manual_partial_exit",
            "exit_execution_class": "manual_operator_exit",
            "manual_exit_realized": True,
            "manual_partial_exit_requested_qty": 10,
            "manual_exit_receipt": {
                "order_no": "S1",
                "order_date": target_date,
                "symbol": "005930",
                "filled_qty": 10,
                "fill_price": 256_500,
                "owner_id": "widget_auto_trade",
                "source_api": "kt00007",
                "allocation_authority": "explicit_user_manual_partial_exit",
            },
        }
    )
    _write_json(
        state_path,
        {
            "schema_version": 1,
            "execution_authority": "operator_directed_widget_auto_trade_v1",
            "active_date": target_date,
            "symbols": {
                "005930": {"entry_signal_id": signal_id, "orders": state_orders}
            },
            "history": [],
        },
    )

    def event(event_type: str, observed_at: str, **fields):
        return {
            "schema": "widget_signal_auto_trade_event_v1",
            "event_type": event_type,
            "observed_at": observed_at,
            "trade_date": target_date,
            "symbol": "005930",
            "name": "Samsung",
            "execution_authority": "operator_directed_widget_auto_trade_v1",
            "decision_authority": "operator_directed_widget_auto_trade_v1",
            "runtime_effect": True,
            "actual_order_submitted": True,
            "broker_order_forbidden": False,
            **fields,
        }

    events = []
    for order_no, role, price, submitted_at, filled_at in buy_orders:
        order_signal = signal_id if role == "ENTRY_BUY" else f"{signal_id}:{role}"
        parent = None if role == "ENTRY_BUY" else signal_id
        events.extend(
            [
                event(
                    "order_submitted",
                    submitted_at,
                    order_no=order_no,
                    order_role=role,
                    side="BUY",
                    requested_qty=10,
                    signal_id=order_signal,
                    parent_entry_signal_id=parent,
                    market_venue="KRX",
                ),
                event(
                    "order_execution_reconciled",
                    filled_at,
                    order_no=order_no,
                    order_role=role,
                    side="BUY",
                    requested_qty=10,
                    filled_qty=10,
                    remaining_qty=0,
                    fill_price=price,
                    broker_execution_venue="KRX",
                ),
            ]
        )
    events.extend(
        [
            event(
                "order_submitted",
                "2026-08-28T18:36:24+09:00",
                order_no="S1",
                order_role="MANUAL_OPERATOR_PARTIAL_EXIT",
                side="SELL",
                requested_qty=10,
                signal_id=f"{signal_id}:MANUAL_PARTIAL_EXIT:10",
                parent_entry_signal_id=signal_id,
                market_venue="NXT",
            ),
            event(
                "order_execution_reconciled",
                "2026-08-28T18:36:25+09:00",
                order_no="S1",
                order_role="MANUAL_OPERATOR_PARTIAL_EXIT",
                side="SELL",
                requested_qty=10,
                filled_qty=10,
                remaining_qty=0,
                fill_price=256_500,
                broker_execution_venue="NXT",
            ),
        ]
    )
    _write_jsonl(
        report_root
        / "widget_signal_auto_trade_events"
        / "widget_signal_auto_trade_events_20260828.jsonl",
        events,
    )

    symbols = {}
    anchors, source = _widget_actual_execution_inventory(
        target_date=target_date,
        report_root=report_root,
        state_path=state_path,
        symbols=symbols,
    )

    assert source["status"] == "loaded"
    assert source["contract_errors"] == []
    entry = next(
        row for row in anchors if row["anchor_role"] == "actual_widget_entry_signal"
    )
    outcome = entry["owner_outcome"]
    assert outcome["realized"] is True
    assert outcome["realization_scope"] == "partial_manual_exit_cashflow"
    assert outcome["quantity"] == 10
    assert outcome["purchased_quantity"] == 30
    assert outcome["right_censored_residual_quantity"] == 20
    assert outcome["exit_execution_class"] == "manual_operator_exit"
    assert outcome["manual_exit_realized"] is True
    assert outcome["autonomous_target_filled"] is False
    assert outcome["realized_loss"] is True
    assert outcome["cost_aware_net_return_pct"] < 0
    assert outcome["execution_venue_alignment_state"] == "cross_venue"
    scale_in_signals = [
        row for row in anchors if row["anchor_role"] == "actual_widget_scale_in_signal"
    ]
    assert len(scale_in_signals) == 2
    assert all(row["owner_requested_quantity"] == 10 for row in scale_in_signals)
    assert all(
        row["actual_realized_response_eligible"] is False for row in scale_in_signals
    )
    exit_anchor = next(
        row
        for row in anchors
        if row["anchor_role"] == "actual_widget_manual_partial_exit_reconciled"
    )
    assert exit_anchor["owner_outcome"]["leg_id"] == (
        "widget_partial_manual_exit_cashflow"
    )
    objective = _lifecycle_objective_summary(
        [{**entry, "micro_context_status": "matched"}]
    )
    coverage = objective["lifecycle_coverage"]
    assert coverage["widget_manual_operator_exit_owner_outcome_count"] == 1
    assert coverage["widget_manual_operator_exit_loss_owner_outcome_count"] == 1
    assert coverage["episode_manual_operator_exit_owner_outcome_count"] == 0

    malformed_state = json.loads(state_path.read_text(encoding="utf-8"))
    malformed_state["symbols"]["005930"]["orders"][-1]["manual_exit_receipt"][
        "source_api"
    ] = "unknown"
    _write_json(state_path, malformed_state)
    malformed_anchors, malformed_source = _widget_actual_execution_inventory(
        target_date=target_date,
        report_root=report_root,
        state_path=state_path,
        symbols={},
    )
    assert malformed_anchors == []
    assert malformed_source["status"] == "contract_invalid"
    assert malformed_source["contract_errors"] == [
        "manual_partial_exit_state_contract_invalid:005930:S1"
    ]


def test_actual_widget_unfilled_entry_keeps_signal_and_submit_diagnostic(tmp_path):
    target_date = "2026-08-14"
    report_root = tmp_path / "report"
    observation_root = tmp_path / "observations"
    state_path = tmp_path / "state.json"
    signal_id = "005930:2026-08-14:ENTRY:KRX_REGULAR:2026-08-14T10:00:00+09:00"
    _write_json(
        report_root
        / "widget_auto_trade_policy_calibration"
        / f"widget_auto_trade_policy_calibration_{target_date}.json",
        {
            "schema": "widget_auto_trade_policy_calibration_report_v1",
            "target_date": target_date,
            "round_trip_cost_pct": 0.2,
            "symbols": {},
        },
    )
    _write_json(
        state_path,
        {
            "schema_version": 1,
            "execution_authority": "operator_directed_widget_auto_trade_v1",
            "active_date": target_date,
            "symbols": {
                "005930": {
                    "orders": [
                        {
                            "broker_accepted": True,
                            "order_no": "B1",
                            "order_date": target_date,
                            "side": "BUY",
                            "order_role": "ENTRY_BUY",
                            "signal_id": signal_id,
                            "market_venue": "KRX",
                            "requested_qty": 10,
                            "filled_qty": 0,
                            "fill_price": None,
                            "limit_price": 10_000,
                            "status": "SUBMITTED",
                        }
                    ]
                }
            },
            "history": [],
        },
    )
    _write_jsonl(
        report_root
        / "widget_signal_auto_trade_events"
        / "widget_signal_auto_trade_events_20260814.jsonl",
        [
            {
                "schema": "widget_signal_auto_trade_event_v1",
                "event_type": "order_submitted",
                "observed_at": "2026-08-14T10:00:01+09:00",
                "trade_date": target_date,
                "symbol": "005930",
                "execution_authority": "operator_directed_widget_auto_trade_v1",
                "decision_authority": "operator_directed_widget_auto_trade_v1",
                "runtime_effect": True,
                "actual_order_submitted": True,
                "broker_order_forbidden": False,
                "order_no": "B1",
                "order_role": "ENTRY_BUY",
                "side": "BUY",
                "requested_qty": 10,
                "signal_id": signal_id,
                "market_venue": "KRX",
                "limit_price": 10_000,
            }
        ],
    )
    _write_jsonl(
        observation_root
        / f"trade_date={target_date}"
        / "venue=KRX"
        / "session=KRX_REGULAR"
        / "market_stream.jsonl",
        [_micro_row("005930", "2026-08-14T10:00:01.500000+09:00", 10_000, venue="KRX")],
    )

    _, anchors, sources = _widget_inventory(
        target_date, report_root, widget_state_path=state_path
    )

    actual = [
        row
        for row in anchors
        if str(row.get("anchor_role")).startswith("actual_widget")
    ]
    assert sources["actual_execution_events"]["status"] == "loaded"
    assert {row["anchor_role"] for row in actual} == {
        "actual_widget_entry_signal",
        "actual_widget_entry_submit_accept_recorded",
    }
    signal = next(
        row for row in actual if row["anchor_role"] == "actual_widget_entry_signal"
    )
    assert signal["anchor_price"] == 10_000
    assert signal["anchor_price_provenance"] == "accepted_entry_limit_price_unfilled"
    assert signal["owner_policy_tuning_eligible"] is False
    assert signal["owner_requested_quantity"] == 10
    assert signal["owner_outcome"]["entry_fill_status"] == "unfilled"
    assert signal["owner_outcome"]["realized"] is False

    report = build_report(
        target_date,
        report_root=report_root,
        observation_root=observation_root,
        widget_state_path=state_path,
        now=datetime(2026, 8, 14, 21, 0, tzinfo=KST),
    )
    actual_context = report["consumers"]["widget_postclose_tuning"]["symbols"][
        "005930"
    ]["session_contexts"]["actual:005930:KRX_REGULAR"]
    assert actual_context["micro_context_status"] == "matched"
    assert all(
        anchor["micro_tuning_input_allowed"] is False
        for anchor in actual_context["anchor_results"]
    )
    assert all(
        row["scope_id"] != "actual:005930:KRX_REGULAR"
        for row in report["rolling_paired_policy_research"]["cohorts"]
    )


def test_actual_widget_unfilled_target_submit_is_retained_as_held_lifecycle(tmp_path):
    target_date = "2026-08-14"
    report_root = tmp_path / "report"
    state_path = tmp_path / "state.json"
    signal_id = "005930:2026-08-14:ENTRY:KRX_REGULAR:2026-08-14T10:00:00+09:00"
    _write_json(
        state_path,
        {
            "schema_version": 1,
            "execution_authority": "operator_directed_widget_auto_trade_v1",
            "active_date": target_date,
            "symbols": {
                "005930": {
                    "orders": [
                        {
                            "broker_accepted": True,
                            "order_no": "B1",
                            "order_date": target_date,
                            "side": "BUY",
                            "order_role": "ENTRY_BUY",
                            "signal_id": signal_id,
                            "market_venue": "KRX",
                            "requested_qty": 10,
                            "filled_qty": 10,
                            "fill_price": 10_000,
                            "status": "FILLED",
                            "last_reconciled_at": "2026-08-14T10:00:02+09:00",
                        },
                        {
                            "broker_accepted": True,
                            "order_no": "S1",
                            "order_date": target_date,
                            "side": "SELL",
                            "order_role": "TAKE_PROFIT_SELL",
                            "signal_id": f"{signal_id}:TP:10100",
                            "parent_entry_signal_id": signal_id,
                            "market_venue": "KRX",
                            "requested_qty": 10,
                            "filled_qty": 0,
                            "fill_price": None,
                            "limit_price": 10_100,
                            "status": "SUBMITTED",
                        },
                    ]
                }
            },
            "history": [],
        },
    )
    base = {
        "schema": "widget_signal_auto_trade_event_v1",
        "trade_date": target_date,
        "symbol": "005930",
        "execution_authority": "operator_directed_widget_auto_trade_v1",
        "decision_authority": "operator_directed_widget_auto_trade_v1",
        "runtime_effect": True,
        "actual_order_submitted": True,
        "broker_order_forbidden": False,
    }
    _write_jsonl(
        report_root
        / "widget_signal_auto_trade_events"
        / "widget_signal_auto_trade_events_20260814.jsonl",
        [
            {
                **base,
                "event_type": "order_submitted",
                "observed_at": "2026-08-14T10:00:01+09:00",
                "order_no": "B1",
                "order_role": "ENTRY_BUY",
                "side": "BUY",
                "requested_qty": 10,
                "signal_id": signal_id,
                "market_venue": "KRX",
            },
            {
                **base,
                "event_type": "order_execution_reconciled",
                "observed_at": "2026-08-14T10:00:02+09:00",
                "order_no": "B1",
                "order_role": "ENTRY_BUY",
                "side": "BUY",
                "requested_qty": 10,
                "filled_qty": 10,
                "remaining_qty": 0,
            },
            {
                **base,
                "event_type": "order_submitted",
                "observed_at": "2026-08-14T10:00:03+09:00",
                "order_no": "S1",
                "order_role": "TAKE_PROFIT_SELL",
                "side": "SELL",
                "requested_qty": 10,
                "signal_id": f"{signal_id}:TP:10100",
                "parent_entry_signal_id": signal_id,
                "market_venue": "KRX",
                "limit_price": 10_100,
            },
        ],
    )

    _, anchors, sources = _widget_inventory(
        target_date, report_root, widget_state_path=state_path
    )

    actual = [
        row
        for row in anchors
        if str(row.get("anchor_role")).startswith("actual_widget")
    ]
    assert sources["actual_execution_events"]["status"] == "loaded"
    assert {row["anchor_role"] for row in actual} == {
        "actual_widget_entry_signal",
        "actual_widget_entry_submit_accept_recorded",
        "actual_widget_entry_fill_reconciled",
        "actual_widget_exit_submit_accept_recorded",
    }
    signal = next(
        row for row in actual if row["anchor_role"] == "actual_widget_entry_signal"
    )
    assert signal["owner_outcome"]["realized"] is False
    assert (
        signal["owner_outcome"][
            "first_fill_confirmation_to_first_exit_submit_record_ms"
        ]
        == 1_000
    )


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


def test_widget_accepted_state_order_without_event_journal_is_explicit_gap(tmp_path):
    target_date = "2026-08-14"
    state_path = tmp_path / "widget_state.json"
    _write_json(
        state_path,
        {
            "schema_version": 1,
            "execution_authority": "operator_directed_widget_auto_trade_v1",
            "active_date": target_date,
            "symbols": {
                "005930": {
                    "orders": [
                        {
                            "broker_accepted": True,
                            "order_no": "B1",
                            "order_date": target_date,
                            "side": "BUY",
                            "order_role": "ENTRY_BUY",
                            "signal_id": (
                                "005930:2026-08-14:ENTRY:KRX_REGULAR:"
                                "2026-08-14T10:00:00+09:00"
                            ),
                            "market_venue": "KRX",
                            "requested_qty": 10,
                            "filled_qty": 10,
                            "fill_price": 10_000,
                        }
                    ]
                }
            },
            "history": [],
        },
    )

    report = build_report(
        target_date,
        report_root=tmp_path / "report",
        observation_root=tmp_path / "observations",
        widget_state_path=state_path,
    )

    source = report["sources"]["widget"]["actual_execution_events"]
    assert source["status"] == ("event_journal_missing_with_accepted_state_orders")
    assert any(
        gap.get("gap_class")
        == "owner_source_event_journal_missing_with_accepted_state_orders"
        for gap in report["producer_consumer_gaps"]
    )


def test_widget_accepted_submit_without_exact_date_state_is_contract_invalid(tmp_path):
    target_date = "2026-08-14"
    report_root = tmp_path / "report"
    state_path = tmp_path / "widget_state.json"
    signal_id = "005930:2026-08-14:ENTRY:KRX_REGULAR:2026-08-14T10:00:00+09:00"
    _write_json(
        state_path,
        {
            "schema_version": 1,
            "execution_authority": "operator_directed_widget_auto_trade_v1",
            "active_date": target_date,
            "symbols": {},
            "history": [],
        },
    )
    _write_jsonl(
        report_root
        / "widget_signal_auto_trade_events"
        / "widget_signal_auto_trade_events_20260814.jsonl",
        [
            {
                "schema": "widget_signal_auto_trade_event_v1",
                "event_type": "order_submitted",
                "observed_at": "2026-08-14T10:00:01+09:00",
                "trade_date": target_date,
                "symbol": "005930",
                "execution_authority": "operator_directed_widget_auto_trade_v1",
                "decision_authority": "operator_directed_widget_auto_trade_v1",
                "runtime_effect": True,
                "actual_order_submitted": True,
                "broker_order_forbidden": False,
                "order_no": "B1",
                "order_role": "ENTRY_BUY",
                "side": "BUY",
                "requested_qty": 10,
                "signal_id": signal_id,
                "market_venue": "KRX",
                "limit_price": 10_000,
            }
        ],
    )

    _, anchors, sources = _widget_inventory(
        target_date, report_root, widget_state_path=state_path
    )

    assert anchors == []
    source = sources["actual_execution_events"]
    assert source["status"] == "contract_invalid"
    assert source["contract_errors"] == [
        "accepted_submit_without_exact_date_state:005930:B1"
    ]


def test_widget_state_event_execution_venue_mismatch_is_contract_invalid(tmp_path):
    target_date = "2026-08-14"
    report_root = tmp_path / "report"
    state_path = tmp_path / "widget_state.json"
    signal_id = "005930:2026-08-14:ENTRY:KRX_REGULAR:2026-08-14T10:00:00+09:00"
    _write_json(
        state_path,
        {
            "schema_version": 1,
            "execution_authority": "operator_directed_widget_auto_trade_v1",
            "active_date": target_date,
            "symbols": {
                "005930": {
                    "orders": [
                        {
                            "broker_accepted": True,
                            "order_no": "B1",
                            "order_date": target_date,
                            "side": "BUY",
                            "order_role": "ENTRY_BUY",
                            "signal_id": signal_id,
                            "market_venue": "KRX",
                            "broker_execution_venue": "NXT",
                            "requested_qty": 10,
                            "filled_qty": 10,
                            "fill_price": 10_000,
                        }
                    ]
                }
            },
            "history": [],
        },
    )
    base = {
        "schema": "widget_signal_auto_trade_event_v1",
        "trade_date": target_date,
        "symbol": "005930",
        "execution_authority": "operator_directed_widget_auto_trade_v1",
        "decision_authority": "operator_directed_widget_auto_trade_v1",
        "runtime_effect": True,
        "actual_order_submitted": True,
        "broker_order_forbidden": False,
        "order_no": "B1",
        "order_role": "ENTRY_BUY",
        "side": "BUY",
        "requested_qty": 10,
        "signal_id": signal_id,
        "market_venue": "KRX",
    }
    _write_jsonl(
        report_root
        / "widget_signal_auto_trade_events"
        / "widget_signal_auto_trade_events_20260814.jsonl",
        [
            {
                **base,
                "event_type": "order_submitted",
                "observed_at": "2026-08-14T10:00:01+09:00",
            },
            {
                **base,
                "event_type": "order_execution_reconciled",
                "observed_at": "2026-08-14T10:00:02+09:00",
                "filled_qty": 10,
                "remaining_qty": 0,
                "fill_price": 10_000,
                "broker_execution_venue": "KRX",
            },
        ],
    )

    _, anchors, sources = _widget_inventory(
        target_date, report_root, widget_state_path=state_path
    )

    assert anchors == []
    source = sources["actual_execution_events"]
    assert source["status"] == "contract_invalid"
    assert "state_event_execution_venue_mismatch:005930:B1" in source["contract_errors"]


def test_widget_cross_venue_fill_is_separated_from_signal_venue_tuning(tmp_path):
    target_date = "2026-08-14"
    report_root = tmp_path / "report"
    state_path = tmp_path / "widget_state.json"
    signal_id = "005930:2026-08-14:ENTRY:KRX_REGULAR:2026-08-14T10:00:00+09:00"
    _write_json(
        state_path,
        {
            "schema_version": 1,
            "execution_authority": "operator_directed_widget_auto_trade_v1",
            "active_date": target_date,
            "symbols": {
                "005930": {
                    "orders": [
                        {
                            "broker_accepted": True,
                            "order_no": "B1",
                            "order_date": target_date,
                            "side": "BUY",
                            "order_role": "ENTRY_BUY",
                            "signal_id": signal_id,
                            "market_venue": "KRX",
                            "broker_execution_venue": "NXT",
                            "requested_qty": 10,
                            "filled_qty": 10,
                            "fill_price": 10_000,
                            "status": "FILLED",
                            "last_reconciled_at": "2026-08-14T10:00:02+09:00",
                        }
                    ]
                }
            },
            "history": [],
        },
    )
    base = {
        "schema": "widget_signal_auto_trade_event_v1",
        "trade_date": target_date,
        "symbol": "005930",
        "execution_authority": "operator_directed_widget_auto_trade_v1",
        "decision_authority": "operator_directed_widget_auto_trade_v1",
        "runtime_effect": True,
        "actual_order_submitted": True,
        "broker_order_forbidden": False,
        "order_no": "B1",
        "order_role": "ENTRY_BUY",
        "side": "BUY",
        "requested_qty": 10,
        "signal_id": signal_id,
        "market_venue": "KRX",
    }
    _write_jsonl(
        report_root
        / "widget_signal_auto_trade_events"
        / "widget_signal_auto_trade_events_20260814.jsonl",
        [
            {
                **base,
                "event_type": "order_submitted",
                "observed_at": "2026-08-14T10:00:01+09:00",
                "limit_price": 10_000,
            },
            {
                **base,
                "event_type": "order_execution_reconciled",
                "observed_at": "2026-08-14T10:00:02+09:00",
                "filled_qty": 10,
                "remaining_qty": 0,
                "fill_price": 10_000,
                "broker_execution_venue": "NXT",
            },
        ],
    )

    _, anchors, sources = _widget_inventory(
        target_date, report_root, widget_state_path=state_path
    )

    assert sources["actual_execution_events"]["status"] == "loaded"
    signal = next(
        row for row in anchors if row["anchor_role"] == "actual_widget_entry_signal"
    )
    submit = next(
        row
        for row in anchors
        if row["anchor_role"] == "actual_widget_entry_submit_accept_recorded"
    )
    fill = next(
        row
        for row in anchors
        if row["anchor_role"] == "actual_widget_entry_fill_reconciled"
    )
    assert signal["owner_policy_tuning_eligible"] is False
    assert signal["owner_outcome"]["execution_venue_alignment_state"] == "cross_venue"
    assert submit["expected_venues"] == ["KRX"]
    assert submit["eventual_broker_execution_venue"] == "NXT"
    assert fill["expected_venues"] == ["NXT"]
    assert fill["broker_execution_venue"] == "NXT"


def test_widget_partial_only_anchor_uses_latest_confirmation_not_first(tmp_path):
    target_date = "2026-08-14"
    report_root = tmp_path / "report"
    state_path = tmp_path / "widget_state.json"
    signal_id = "005930:2026-08-14:ENTRY:KRX_REGULAR:2026-08-14T10:00:00+09:00"
    _write_json(
        state_path,
        {
            "schema_version": 1,
            "execution_authority": "operator_directed_widget_auto_trade_v1",
            "active_date": target_date,
            "symbols": {
                "005930": {
                    "orders": [
                        {
                            "broker_accepted": True,
                            "order_no": "B1",
                            "order_date": target_date,
                            "side": "BUY",
                            "order_role": "ENTRY_BUY",
                            "signal_id": signal_id,
                            "market_venue": "KRX",
                            "requested_qty": 10,
                            "filled_qty": 7,
                            "fill_price": 10_020,
                            "limit_price": 10_050,
                            "status": "SUBMITTED",
                            "last_reconciled_at": "2026-08-14T10:00:03+09:00",
                        }
                    ]
                }
            },
            "history": [],
        },
    )
    base = {
        "schema": "widget_signal_auto_trade_event_v1",
        "trade_date": target_date,
        "symbol": "005930",
        "execution_authority": "operator_directed_widget_auto_trade_v1",
        "decision_authority": "operator_directed_widget_auto_trade_v1",
        "runtime_effect": True,
        "actual_order_submitted": True,
        "broker_order_forbidden": False,
        "order_no": "B1",
        "order_role": "ENTRY_BUY",
        "side": "BUY",
        "requested_qty": 10,
    }
    _write_jsonl(
        report_root
        / "widget_signal_auto_trade_events"
        / "widget_signal_auto_trade_events_20260814.jsonl",
        [
            {
                **base,
                "event_type": "order_submitted",
                "observed_at": "2026-08-14T10:00:01+09:00",
                "signal_id": signal_id,
                "market_venue": "KRX",
                "limit_price": 10_050,
            },
            {
                **base,
                "event_type": "order_execution_reconciled",
                "observed_at": "2026-08-14T10:00:02+09:00",
                "filled_qty": 3,
                "remaining_qty": 7,
                "fill_price": 10_000,
            },
            {
                **base,
                "event_type": "order_execution_reconciled",
                "observed_at": "2026-08-14T10:00:03+09:00",
                "filled_qty": 7,
                "remaining_qty": 3,
                "fill_price": 10_020,
            },
        ],
    )

    _, anchors, sources = _widget_inventory(
        target_date, report_root, widget_state_path=state_path
    )

    assert sources["actual_execution_events"]["status"] == "loaded"
    fill_anchor = next(
        row
        for row in anchors
        if row["anchor_role"] == "actual_widget_entry_partial_fill_reconciled"
    )
    assert fill_anchor["anchor_at"] == "2026-08-14T10:00:03+09:00"
    assert fill_anchor["anchor_price"] == 10_020
    assert fill_anchor["owner_policy_tuning_eligible"] is False
