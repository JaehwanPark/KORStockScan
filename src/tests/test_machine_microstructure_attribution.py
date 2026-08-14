import json
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from src.engine.monitoring.machine_microstructure_attribution import (
    build_report,
    write_report,
)

KST = ZoneInfo("Asia/Seoul")


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
) -> dict:
    return {
        "schema": "scalp_micro_reversion_market_stream_point_v3",
        "symbol": symbol,
        "venue": venue,
        "session_bucket": f"{venue}_REGULAR",
        "local_receive_timestamp": at,
        "trade_price": price,
        "best_bid": price - 50,
        "best_ask": price,
        "path_consumer_eligible": eligible,
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
                                }
                            ]
                        }
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
                    "new_live_profile": {
                        "profile_id": "new_live_profile",
                        "symbol": "888888",
                        "session": "morning",
                        "source_quality": "pass",
                        "attempted": True,
                        "signal_features": {
                            "signal_bar": {
                                "timestamp": "2026-08-14T09:30:00+09:00",
                                "close_price": 20000,
                            }
                        },
                        "legs": [{"buy_filled_qty": 10}],
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
            _micro_row("888888", "2026-08-14T09:30:05+09:00", 19800),
            _micro_row("888888", "2026-08-14T09:31:00+09:00", 20200),
        ],
    )

    report = build_report(
        target_date,
        report_root=report_root,
        observation_root=observation_root,
        now=datetime(2026, 8, 14, 21, 0, tzinfo=KST),
    )

    row = report["consumers"]["episode_machine_postclose_tuning"]["profiles"][
        "new_live_profile"
    ]
    anchor = row["anchor_results"][0]
    assert anchor["micro_context_status"] == "matched"
    assert anchor["actual_order_submitted"] is True
    assert anchor["metrics"]["mae_bps"] == -100.0
    assert anchor["metrics"]["mfe_bps"] == 100.0


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
        / "venue=SOR"
        / "session=SOR_REGULAR"
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


def test_widget_late_expansion_report_adds_dynamic_symbol(tmp_path):
    target_date = "2026-08-14"
    report_root = tmp_path / "report"
    _write_json(
        report_root
        / "widget_collector_expansion_recommendation"
        / f"widget_collector_expansion_recommendation_{target_date}.json",
        {
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
