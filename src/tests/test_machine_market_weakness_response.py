import gzip
import json
from datetime import date
from pathlib import Path
from src.engine.risk.market_weakness_state import STATE_REPLAY_CONTRACT
from src.engine.risk.market_weakness_threshold_policy import (
    resolve_effective_thresholds,
    observation_thresholds,
)
from src.engine.monitoring.machine_market_weakness_response import (
    _load_observations,
    _counterfactual_horizon_gaps,
    _with_source_failure_boundaries,
    _market_timelines,
    _state_at,
)
import pytest

from src.engine.market_panic_breadth_collector import (
    market_weakness_observation_id,
)
from src.engine.monitoring.machine_market_weakness_response import (
    METRIC_CONTRACT,
    _counterfactual_30m_return,
    _cumulative_counterfactual_evidence,
    build_machine_market_weakness_response,
)
from src.engine.scalping.micro_reversion.economic_reference import (
    AUTHORITY_CONTRACT,
    content_sha256,
)

TARGET_DATE = "2026-08-28"


def test_legacy_policy_observation_is_readable_only_for_historical_analysis(tmp_path):
    path = _write_observation(
        tmp_path, minute=2, raw_state="SINGLE_MARKET_WEAKNESS", affected=["KOSPI"]
    )
    payload = json.loads(path.read_text())
    policy = resolve_effective_thresholds(
        target_date=date.fromisoformat(TARGET_DATE), policy_dir=tmp_path / "policies"
    ).observation_contract()
    policy["schema"] = "market_weakness_hysteresis_policy_applied_v1"
    payload["hysteresis_policy"] = policy
    payload["observation_id"] = market_weakness_observation_id(payload)
    path.write_text(json.dumps(payload))
    original = path.read_bytes()
    rows, source = _load_observations(tmp_path, TARGET_DATE)
    assert source["eligible_count"] == 1
    assert rows[0]["observation_id"] == payload["observation_id"]
    assert path.read_bytes() == original
    with pytest.raises(ValueError, match="provenance_invalid"):
        observation_thresholds(payload)
    payload["affected_markets"] = ["KOSDAQ"]
    path.write_text(json.dumps(payload))
    assert _load_observations(tmp_path, TARGET_DATE)[1]["eligible_count"] == 0


def test_only_unrelated_horizon_gaps_are_removed():
    cf = {
        "source_quality_status": "blocked",
        "source_gap_reasons": ["executable_bbo_horizon_20m_missing"],
        "horizons_minutes": {
            "30": {"observed": True, "cost_aware_net_return_pct": -1.0}
        },
    }
    cf.update(
        entry={
            "observed": True,
            "depth_backed": True,
            "ask_price": 10000,
            "required_quantity": 20,
            "available_best_ask_quantity": 100,
        },
        round_trip_cost_pct=0.2,
    )
    cf["horizons_minutes"]["30"].update(
        bid_price=9920,
        depth_backed=True,
        required_quantity=20,
        available_best_bid_quantity=100,
        quote_age_from_horizon_ms=1000,
    )
    row = {
        "counterfactual_source_quality_status": "blocked",
        "counterfactual_source_gap_reasons": list(cf["source_gap_reasons"]),
        "executable_bbo_counterfactual": cf,
    }
    assert _counterfactual_horizon_gaps(cf) == []
    assert _counterfactual_30m_return(row) == -1.0
    for gap in (
        "executable_bbo_horizon_30m_missing",
        "required_quantity_missing_or_invalid",
        "micro_runtime_registration_receipt_missing_or_incomplete",
    ):
        cf["source_gap_reasons"].append(gap)
        assert _counterfactual_30m_return(row) is None
        cf["source_gap_reasons"].pop()
    cf["entry"]["available_best_ask_quantity"] = 1
    assert _counterfactual_30m_return(row) is None


def test_cached_candidate_states_without_new_replay_contract_are_not_promoted():
    row = _threshold_counterfactual_row(TARGET_DATE, 0)
    del row["threshold_candidate_state_contract"]
    result = _cumulative_counterfactual_evidence(
        target_date=TARGET_DATE,
        current_rows=[row],
        history_report_dir=None,
        current_activation_observations=2,
        current_release_observations=3,
    )
    assert result["source_census"]["comparison_exclusion_counts"] == {
        "threshold_candidate_state_contract_missing": 1
    }
    assert result["policy_candidate_ready"] is False


def test_excluded_source_failure_breaks_replayed_consecutive_streak(tmp_path):
    from datetime import datetime

    for minute in (0, 1, 2):
        path = _write_observation(
            tmp_path,
            minute=minute,
            raw_state="SINGLE_MARKET_WEAKNESS",
            affected=["KOSPI"],
        )
        if minute == 1:
            payload = json.loads(path.read_text())
            payload["source_quality_ready"] = False
            payload["observation_id"] = market_weakness_observation_id(payload)
            path.write_text(json.dumps(payload))
    rows, source = _load_observations(tmp_path, TARGET_DATE)
    assert source["eligible_count"] == 2
    assert source["excluded_count"] == 1
    timeline = _market_timelines(
        _with_source_failure_boundaries(rows, source),
        activation_observations=2,
        release_observations=3,
    )["KOSPI"]
    state, _ = _state_at(
        timeline, datetime.fromisoformat(f"{TARGET_DATE}T09:03:00+09:00")
    )
    assert state["active"] is False
    assert state["weak_streak"] == 1


def test_same_timestamp_target_adverse_is_excluded_from_threshold_review():
    assert (
        _counterfactual_30m_return(
            {
                "counterfactual_source_quality_status": "eligible",
                "executable_bbo_counterfactual": {
                    "horizons_minutes": {
                        "30": {
                            "observed": True,
                            "cost_aware_net_return_pct": 0.1,
                        }
                    },
                    "target_adverse_first_hit": {"state": "same_timestamp_ambiguous"},
                },
            }
        )
        is None
    )


def test_threshold_review_flags_structurally_unattainable_collection_yield(tmp_path):
    history_root = tmp_path / "machine_microstructure_attribution"
    history_root.mkdir()

    def blocked_row(day: str, index: int) -> dict:
        row = _threshold_counterfactual_row(day, index)
        row["counterfactual_source_quality_status"] = "blocked"
        row["counterfactual_source_gap_reasons"] = [
            "micro_runtime_registration_receipt_missing_or_incomplete"
        ]
        return row

    for day in ("2026-08-26", "2026-08-27"):
        response = {
            "schema": "machine_market_weakness_response_v2",
            "target_date": day,
            "metric_contract": METRIC_CONTRACT,
            "authority": {
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "broker_order_forbidden": True,
            },
            "entry_responses": [blocked_row(day, index) for index in range(25)],
        }
        (history_root / f"machine_microstructure_attribution_{day}.json").write_text(
            json.dumps({"market_weakness_entry_response": response}),
            encoding="utf-8",
        )

    result = _cumulative_counterfactual_evidence(
        target_date=TARGET_DATE,
        current_rows=[blocked_row(TARGET_DATE, index) for index in range(10)],
        history_report_dir=history_root,
        current_activation_observations=2,
        current_release_observations=3,
    )

    assert result["attainability"]["status"] == "collection_contract_gap"
    assert (
        result["attainability"]["projected_additional_trading_dates_to_signal_floor"]
        is None
    )
    assert result["attainability"]["zero_yield_strata"] == [
        "market:KOSDAQ",
        "market:KOSPI",
        "owner:episode",
        "owner:widget",
    ]
    assert result["source_census"]["counterfactual_30m_eligible_count"] == 0
    assert result["source_census"]["counterfactual_30m_eligible_yield_pct"] == 0.0


def _write_observation(
    root: Path,
    *,
    minute: int,
    raw_state: str,
    affected: list[str] | None = None,
    recovered: list[str] | None = None,
    suffix: str = "",
) -> Path:
    directory = root / TARGET_DATE
    directory.mkdir(parents=True, exist_ok=True)
    affected_markets = sorted(affected or [])
    recovery_markets = sorted(recovered or [])
    global_recovery = raw_state == "RECOVERY_EVIDENCE"
    market_checks = {
        market: {
            "passed": market in recovery_markets,
            "source_quality_ready": True,
            "checks": {
                "market_index_recovered": market in recovery_markets,
                "industry_down_ratio_recovered": market in recovery_markets,
                "industry_severe_down_ratio_recovered": market in recovery_markets,
                "stock_fall_ratio_recovered": market in recovery_markets,
            },
        }
        for market in ("KOSPI", "KOSDAQ")
    }
    payload = {
        "schema_version": 2,
        "target_date": TARGET_DATE,
        "as_of": f"{TARGET_DATE}T09:{minute:02d}:00+09:00",
        "raw_state": raw_state,
        "affected_markets": affected_markets,
        "recovery_evidence_markets": recovery_markets,
        "source_quality_ready": True,
        "source_quality_status": "ok",
        "metric_role": "market_weakness_observation",
        "decision_authority": "source_quality_observation_only",
        "window_policy": "intraday_consecutive_unique_snapshot_hysteresis",
        "sample_floor": {
            "market_index_count": 2,
            "industry_row_count": 3,
            "activation_unique_observations": 2,
            "release_unique_observations": 3,
        },
        "primary_decision_metric": "raw_state_with_release_margin",
        "forbidden_uses": [
            "runtime_threshold_apply",
            "order_submit",
            "auto_sell",
            "bot_restart",
            "provider_route_change",
            "widget_entry_block",
            "episode_entry_block",
            "open_buy_cancel",
            "target_order_cancel",
            "holding_policy_change",
            "price_or_quantity_change",
            "position_exit",
        ],
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "evidence": {
            "affected_markets": affected_markets,
            "recovery_evidence_markets": recovery_markets,
            "market_states": {
                market: {"source_quality_ready": True} for market in ("KOSPI", "KOSDAQ")
            },
        },
        "release_margin": {
            "passed": global_recovery,
            "thresholds": {
                "each_market_index_above_pct": -0.9,
                "weighted_market_index_above_pct": -0.9,
                "industry_down_ratio_below_pct": 55.0,
                "industry_severe_down_ratio_below_pct": 10.0,
                "max_stock_fall_ratio_below_pct": 60.0,
            },
            "checks": {
                "each_market_index_recovered": global_recovery,
                "weighted_market_index_recovered": global_recovery,
                "industry_down_ratio_recovered": global_recovery,
                "industry_severe_down_ratio_recovered": global_recovery,
                "stock_fall_ratio_recovered": global_recovery,
            },
            "markets": market_checks,
        },
        "response_research_contract": {
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "control": "current_owner_behavior_unchanged",
        },
    }
    payload["observation_id"] = market_weakness_observation_id(payload)
    path = directory / f"market_weakness_observation_{minute:02d}{suffix}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _write_master(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    source_sha256 = "a" * 64
    source_reference = (
        f"policy://micro-reversion/symbol_product_master.json#sha256={source_sha256}"
    )
    records = [
        {
            "symbol": "005930",
            "listing_market": "KOSPI",
            "instrument_type": "EQUITY",
            "instrument_tax_class": "ordinary_taxable_equity_20bps",
            "conflict_status": "clean",
            "effective_from": TARGET_DATE,
            "effective_to": None,
            "metadata_source": "official_symbol_product_master_v2",
            "source_reference": source_reference,
            "verified_at": f"{TARGET_DATE}T20:00:00+09:00",
        },
        {
            "symbol": "080220",
            "listing_market": "KOSDAQ",
            "instrument_type": "EQUITY",
            "instrument_tax_class": "ordinary_taxable_equity_20bps",
            "conflict_status": "clean",
            "effective_from": TARGET_DATE,
            "effective_to": None,
            "metadata_source": "official_symbol_product_master_v2",
            "source_reference": source_reference,
            "verified_at": f"{TARGET_DATE}T20:00:00+09:00",
        },
    ]
    source_artifact = {
        "source_id": "kis-official-common-stock-master-test",
        "kind": "symbol_product_master",
        "logical_path": "policy://micro-reversion/symbol_product_master.json",
        "resolved_path": "/fixture/symbol_product_master.json",
        "expected_sha256": source_sha256,
        "observed_sha256": source_sha256,
        "expected_size_bytes": 1,
        "observed_size_bytes": 1,
        "effective_from": TARGET_DATE,
        "effective_to": None,
        "payload_schema": "micro_reversion_raw_symbol_product_master_v3",
        "record_count": len(records),
        "status": "verified",
        "verified": True,
        "blockers": [],
        **AUTHORITY_CONTRACT,
    }
    body = {
        "schema": "scalp_micro_reversion_symbol_master_v1",
        "artifact_id": f"main-ai-economic-reference-{TARGET_DATE}-symbol-master",
        "source_contract_schema": "micro_reversion_raw_symbol_product_master_v3",
        "verification_status": "verified",
        "verified": True,
        **AUTHORITY_CONTRACT,
        "decision_authority": "instrument_metadata_source_only",
        "source_artifacts": [source_artifact],
        "census": {"record_count": len(records), "symbol_count": len(records)},
        "records": records,
    }
    payload = {**body, "content_sha256": content_sha256(body)}
    (root / f"micro_reversion_symbol_master_{TARGET_DATE}.json").write_text(
        json.dumps(payload), encoding="utf-8"
    )


def _anchor(symbol: str, *, actual: bool = True) -> dict:
    return {
        "anchor_id": f"anchor-{symbol}",
        "owner": "episode" if symbol == "005930" else "widget",
        "scope_id": f"scope-{symbol}",
        "symbol": symbol,
        "anchor_at": f"{TARGET_DATE}T09:05:00+09:00",
        "anchor_role": "actual_entry_signal",
        "actual_order_submitted": actual,
        "classification": "supportive_confirmation_candidate",
        "owner_outcome": {
            "realized": True,
            "cost_aware_net_return_pct": -0.75,
        },
    }


def _threshold_counterfactual_row(day: str, index: int) -> dict:
    states = {
        f"a{activation}_r{release}": False
        for activation in (2, 3, 4)
        for release in (2, 3, 4, 5)
    }
    states["a2_r3"] = True
    return {
        "anchor_id": f"{day}-counterfactual-{index}",
        "threshold_candidate_state_contract": STATE_REPLAY_CONTRACT,
        "historical_state_replay_contract": STATE_REPLAY_CONTRACT,
        "owner": "episode" if index % 2 == 0 else "widget",
        "listing_market": "KOSPI" if index % 2 == 0 else "KOSDAQ",
        "effective_hysteresis": {
            "activation_unique_observations": 2,
            "release_unique_observations": 3,
        },
        "counterfactual_source_quality_status": "eligible",
        "threshold_candidate_states": states,
        "executable_bbo_counterfactual": {
            "horizons_minutes": {
                "30": {
                    "observed": True,
                    "cost_aware_net_return_pct": 0.1,
                }
            },
            "target_adverse_first_hit": {"state": "target_first"},
        },
    }


def test_threshold_review_uses_clean_cumulative_holdout_and_current_neighbor(
    tmp_path,
):
    history_root = tmp_path / "machine_microstructure_attribution"
    history_root.mkdir()
    dates = [
        "2026-08-14",
        "2026-08-18",
        "2026-08-19",
        "2026-08-20",
        "2026-08-21",
        "2026-08-24",
        "2026-08-25",
        "2026-08-26",
        "2026-08-27",
        TARGET_DATE,
    ]
    for day in dates[:-1]:
        response = {
            "schema": "machine_market_weakness_response_v2",
            "target_date": day,
            "metric_contract": METRIC_CONTRACT,
            "authority": {
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "broker_order_forbidden": True,
            },
            "entry_responses": [
                _threshold_counterfactual_row(day, index) for index in range(5)
            ],
        }
        (history_root / f"machine_microstructure_attribution_{day}.json").write_text(
            json.dumps({"market_weakness_entry_response": response}),
            encoding="utf-8",
        )

    result = _cumulative_counterfactual_evidence(
        target_date=TARGET_DATE,
        current_rows=[
            _threshold_counterfactual_row(TARGET_DATE, index) for index in range(5)
        ],
        history_report_dir=history_root,
        current_activation_observations=2,
        current_release_observations=3,
    )

    assert result["counterfactual_entry_signal_count"] == 50
    from src.engine.risk.market_weakness_threshold_policy import (
        validate_threshold_recommendation,
    )

    assert validate_threshold_recommendation(result) == (True, "ready")
    assert result["holdout_dates"] == dates[-3:]
    assert all(result["sample_floor"].values())
    assert result["policy_candidate_ready"] is True
    assert result["selected_policy"]["candidate_key"] == "a3_r3"
    assert result["selected_policy"]["changed_axis"] == (
        "activation_unique_observations"
    )


def test_threshold_review_rejects_aggregate_gain_that_harms_episode_owner(tmp_path):
    history_root = tmp_path / "machine_microstructure_attribution"
    history_root.mkdir()
    dates = [
        "2026-08-14",
        "2026-08-18",
        "2026-08-19",
        "2026-08-20",
        "2026-08-21",
        "2026-08-24",
        "2026-08-25",
        "2026-08-26",
        "2026-08-27",
        TARGET_DATE,
    ]

    def rows_for_day(day: str) -> list[dict]:
        rows = []
        for index in range(5):
            row = _threshold_counterfactual_row(day, index)
            row["owner"] = "widget" if index < 4 else "episode"
            row["executable_bbo_counterfactual"]["horizons_minutes"]["30"][
                "cost_aware_net_return_pct"
            ] = (0.1 if index < 4 else -0.1)
            row["executable_bbo_counterfactual"]["target_adverse_first_hit"] = {
                "state": "target_first" if index < 4 else "adverse_first"
            }
            rows.append(row)
        return rows

    for day in dates[:-1]:
        response = {
            "schema": "machine_market_weakness_response_v2",
            "target_date": day,
            "metric_contract": METRIC_CONTRACT,
            "authority": {
                "runtime_effect": False,
                "allowed_runtime_apply": False,
                "broker_order_forbidden": True,
            },
            "entry_responses": rows_for_day(day),
        }
        (history_root / f"machine_microstructure_attribution_{day}.json").write_text(
            json.dumps({"market_weakness_entry_response": response}),
            encoding="utf-8",
        )

    result = _cumulative_counterfactual_evidence(
        target_date=TARGET_DATE,
        current_rows=rows_for_day(TARGET_DATE),
        history_report_dir=history_root,
        current_activation_observations=2,
        current_release_observations=3,
    )

    candidate = next(
        row for row in result["candidates"] if row["candidate_key"] == "a3_r3"
    )
    assert candidate["full_incremental_vs_current_policy_avg_pct"] > 0.0
    assert (
        candidate["stratum_guards"]["owner:episode"][
            "full_incremental_vs_current_policy_avg_pct"
        ]
        < 0.0
    )
    assert candidate["review_passed"] is False
    assert result["policy_candidate_ready"] is False


def test_response_joins_only_the_symbols_listing_market(tmp_path):
    observation_root = tmp_path / "market_weakness_observations"
    master_root = tmp_path / "micro_reversion_economic_reference"
    _write_master(master_root)
    _write_observation(
        observation_root,
        minute=0,
        raw_state="SINGLE_MARKET_WEAKNESS",
        affected=["KOSPI"],
    )
    _write_observation(
        observation_root,
        minute=2,
        raw_state="SINGLE_MARKET_WEAKNESS",
        affected=["KOSPI"],
    )
    for minute in (10, 12, 14):
        _write_observation(
            observation_root,
            minute=minute,
            raw_state="NEAR_WEAKNESS_BOUNDARY",
            recovered=["KOSPI"],
        )

    report = build_machine_market_weakness_response(
        {"entry_anchors": [_anchor("005930"), _anchor("080220")]},
        target_date=TARGET_DATE,
        observation_root=observation_root,
        symbol_master_dir=master_root,
    )

    by_symbol = {row["symbol"]: row for row in report["entry_responses"]}
    samsung = by_symbol["005930"]
    jeju = by_symbol["080220"]
    assert samsung["market_state_at_entry"] == "CONFIRMED_WEAKNESS"
    assert (
        samsung["candidate_arms"]["skip_new_entry_during_confirmed_weakness"][
            "incremental_vs_control_pct"
        ]
        == 0.75
    )
    assert (
        samsung["candidate_arms"]["delay_new_entry_until_recovery_confirmed"][
            "release_at"
        ]
        == f"{TARGET_DATE}T09:14:00+09:00"
    )
    assert jeju["market_state_at_entry"] == "NOT_CONFIRMED_OR_NOT_OBSERVED"
    for arm_name in (
        "delay_new_entry_until_recovery_confirmed",
        "relative_strength_and_liquidity_exception",
    ):
        arm = samsung["candidate_arms"][arm_name]
        assert arm["eligible"] is False
        assert arm["automatic_evaluation_enabled"] is False
        assert arm["implementation_status"] == "integration_required"
        assert arm["implementation_owner"] == "machine_entry_timing_tuning"
    assert report["summary"]["confirmed_weakness_entry_count"] == 1
    assert report["summary"]["actual_realized_comparison_count"] == 1
    assert (
        report["clean_baseline_cumulative"]["affected_actual_realized_comparison_count"]
        == 1
    )
    assert report["clean_baseline_cumulative"]["source_only_review_ready"] is False
    assert report["authority"]["runtime_effect"] is False
    assert report["authority"]["policy_candidate_ready"] is False


def test_response_never_uses_future_weakness_for_earlier_anchor(tmp_path):
    observation_root = tmp_path / "market_weakness_observations"
    master_root = tmp_path / "micro_reversion_economic_reference"
    _write_master(master_root)
    _write_observation(
        observation_root,
        minute=6,
        raw_state="BROAD_WEAKNESS",
        affected=["KOSPI", "KOSDAQ"],
    )
    _write_observation(
        observation_root,
        minute=8,
        raw_state="BROAD_WEAKNESS",
        affected=["KOSPI", "KOSDAQ"],
    )

    report = build_machine_market_weakness_response(
        {"entry_anchors": [_anchor("005930")]},
        target_date=TARGET_DATE,
        observation_root=observation_root,
        symbol_master_dir=master_root,
    )

    row = report["entry_responses"][0]
    assert row["market_state_at_entry"] == "NOT_CONFIRMED_OR_NOT_OBSERVED"
    assert "past_market_weakness_observation_missing" in row["source_gap_reasons"]


def test_response_does_not_assume_same_timestamp_observation_precedes_entry(tmp_path):
    observation_root = tmp_path / "market_weakness_observations"
    master_root = tmp_path / "micro_reversion_economic_reference"
    _write_master(master_root)
    _write_observation(
        observation_root,
        minute=3,
        raw_state="BROAD_WEAKNESS",
        affected=["KOSPI", "KOSDAQ"],
    )
    _write_observation(
        observation_root,
        minute=5,
        raw_state="BROAD_WEAKNESS",
        affected=["KOSPI", "KOSDAQ"],
    )

    report = build_machine_market_weakness_response(
        {"entry_anchors": [_anchor("005930")]},
        target_date=TARGET_DATE,
        observation_root=observation_root,
        symbol_master_dir=master_root,
    )

    assert (
        report["entry_responses"][0]["market_state_at_entry"]
        == "NOT_CONFIRMED_OR_NOT_OBSERVED"
    )


def test_response_rejects_legacy_unscoped_observation(tmp_path):
    observation_root = tmp_path / "market_weakness_observations"
    master_root = tmp_path / "micro_reversion_economic_reference"
    _write_master(master_root)
    directory = observation_root / TARGET_DATE
    directory.mkdir(parents=True)
    (directory / "market_weakness_observation_legacy.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "observation_id": "legacy",
                "target_date": TARGET_DATE,
                "as_of": f"{TARGET_DATE}T09:00:00+09:00",
                "raw_state": "SINGLE_MARKET_WEAKNESS",
                "source_quality_ready": True,
                "decision_authority": "source_quality_observation_only",
                "runtime_effect": False,
                "allowed_runtime_apply": False,
            }
        ),
        encoding="utf-8",
    )

    report = build_machine_market_weakness_response(
        {"entry_anchors": [_anchor("005930")]},
        target_date=TARGET_DATE,
        observation_root=observation_root,
        symbol_master_dir=master_root,
    )

    source = report["sources"]["market_weakness_observations"]
    assert source["status"] == "no_schema_v2_observation"
    assert source["exclusion_counts"] == {"market_scope_schema_v2_required": 1}
    assert report["authority"]["allowed_runtime_apply"] is False


def test_response_builds_deduplicated_clean_baseline_cumulative_evidence(tmp_path):
    observation_root = tmp_path / "market_weakness_observations"
    master_root = tmp_path / "micro_reversion_economic_reference"
    history_root = tmp_path / "machine_microstructure_attribution"
    history_root.mkdir()
    _write_master(master_root)
    for minute in (0, 2):
        _write_observation(
            observation_root,
            minute=minute,
            raw_state="SINGLE_MARKET_WEAKNESS",
            affected=["KOSPI"],
        )
    for day in ("2026-08-24", "2026-08-25", "2026-08-26", "2026-08-27"):
        prior_rows = []
        for index in range(5):
            prior_rows.append(
                {
                    "anchor_id": f"{day}-anchor-{index}",
                    "owner": "episode",
                    "listing_market": "KOSPI",
                    "actual_order_submitted": True,
                    "source_quality_status": "eligible",
                    "control": {
                        "status": "actual_realized",
                        "cost_aware_net_return_pct": -0.25,
                    },
                    "candidate_arms": {
                        "skip_new_entry_during_confirmed_weakness": {
                            "eligible": True,
                            "actual_realized_comparison": True,
                            "zero_exposure_counterfactual_return_pct": 0.0,
                            "incremental_vs_control_pct": 0.25,
                        }
                    },
                }
            )
        (history_root / f"machine_microstructure_attribution_{day}.json").write_text(
            json.dumps(
                {
                    "market_weakness_entry_response": {
                        "schema": "machine_market_weakness_response_v1",
                        "target_date": day,
                        "metric_contract": METRIC_CONTRACT,
                        "authority": {
                            "runtime_effect": False,
                            "allowed_runtime_apply": False,
                            "actual_order_submitted": False,
                            "broker_order_forbidden": True,
                            "policy_candidate_ready": False,
                        },
                        "entry_responses": prior_rows,
                    }
                }
            ),
            encoding="utf-8",
        )

    report = build_machine_market_weakness_response(
        {"entry_anchors": [_anchor("005930")]},
        target_date=TARGET_DATE,
        observation_root=observation_root,
        symbol_master_dir=master_root,
        history_report_dir=history_root,
    )

    cumulative = report["clean_baseline_cumulative"]
    assert cumulative["affected_actual_realized_trading_date_count"] == 5
    assert cumulative["affected_actual_realized_comparison_count"] == 21
    assert cumulative["incremental_vs_control_avg_pct"] > 0.0
    assert cumulative["source_only_review_ready"] is True
    assert cumulative["runtime_effect"] is False
    assert cumulative["source_census"]["primary_key_partition_reconciled"] is True


def test_response_rejects_identity_tampering_and_same_timestamp_conflicts(tmp_path):
    observation_root = tmp_path / "market_weakness_observations"
    master_root = tmp_path / "micro_reversion_economic_reference"
    _write_master(master_root)
    tampered = _write_observation(
        observation_root,
        minute=0,
        raw_state="SINGLE_MARKET_WEAKNESS",
        affected=["KOSPI"],
    )
    payload = json.loads(tampered.read_text(encoding="utf-8"))
    payload["release_margin"]["tampered"] = True
    tampered.write_text(json.dumps(payload), encoding="utf-8")
    _write_observation(
        observation_root,
        minute=2,
        raw_state="SINGLE_MARKET_WEAKNESS",
        affected=["KOSPI"],
        suffix="-a",
    )
    _write_observation(
        observation_root,
        minute=2,
        raw_state="SINGLE_MARKET_WEAKNESS",
        affected=["KOSDAQ"],
        suffix="-b",
    )

    report = build_machine_market_weakness_response(
        {"entry_anchors": [_anchor("005930")]},
        target_date=TARGET_DATE,
        observation_root=observation_root,
        symbol_master_dir=master_root,
    )

    source = report["sources"]["market_weakness_observations"]
    assert source["eligible_count"] == 0
    assert source["partition_reconciled"] is True
    assert source["exclusion_counts"] == {
        "competing_same_timestamp_observation": 2,
        "observation_identity_invalid": 1,
    }


def test_response_reads_verified_symbol_master_from_gzip_only(tmp_path):
    observation_root = tmp_path / "market_weakness_observations"
    master_root = tmp_path / "micro_reversion_economic_reference"
    _write_master(master_root)
    master_path = master_root / f"micro_reversion_symbol_master_{TARGET_DATE}.json"
    compressed = master_path.with_suffix(".json.gz")
    compressed.write_bytes(gzip.compress(master_path.read_bytes()))
    master_path.unlink()
    for minute in (0, 2):
        _write_observation(
            observation_root,
            minute=minute,
            raw_state="SINGLE_MARKET_WEAKNESS",
            affected=["KOSPI"],
        )

    report = build_machine_market_weakness_response(
        {"entry_anchors": [_anchor("005930")]},
        target_date=TARGET_DATE,
        observation_root=observation_root,
        symbol_master_dir=master_root,
    )

    assert report["sources"]["verified_symbol_master"]["status"] == "loaded"
    assert report["entry_responses"][0]["listing_market"] == "KOSPI"


def test_response_excludes_unreconciled_historical_skip_delta(tmp_path):
    observation_root = tmp_path / "market_weakness_observations"
    master_root = tmp_path / "micro_reversion_economic_reference"
    history_root = tmp_path / "machine_microstructure_attribution"
    history_root.mkdir()
    _write_master(master_root)
    for minute in (0, 2):
        _write_observation(
            observation_root,
            minute=minute,
            raw_state="SINGLE_MARKET_WEAKNESS",
            affected=["KOSPI"],
        )
    day = "2026-08-27"
    prior_row = {
        "anchor_id": "bad-delta",
        "owner": "episode",
        "listing_market": "KOSPI",
        "actual_order_submitted": True,
        "source_quality_status": "eligible",
        "control": {
            "status": "actual_realized",
            "cost_aware_net_return_pct": -0.25,
        },
        "candidate_arms": {
            "skip_new_entry_during_confirmed_weakness": {
                "eligible": True,
                "actual_realized_comparison": True,
                "zero_exposure_counterfactual_return_pct": 0.0,
                "incremental_vs_control_pct": 9.99,
            }
        },
    }
    (history_root / f"machine_microstructure_attribution_{day}.json").write_text(
        json.dumps(
            {
                "market_weakness_entry_response": {
                    "schema": "machine_market_weakness_response_v1",
                    "target_date": day,
                    "metric_contract": METRIC_CONTRACT,
                    "authority": {
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                        "actual_order_submitted": False,
                        "broker_order_forbidden": True,
                        "policy_candidate_ready": False,
                    },
                    "entry_responses": [prior_row],
                }
            }
        ),
        encoding="utf-8",
    )

    report = build_machine_market_weakness_response(
        {"entry_anchors": [_anchor("005930")]},
        target_date=TARGET_DATE,
        observation_root=observation_root,
        symbol_master_dir=master_root,
        history_report_dir=history_root,
    )

    source_census = report["clean_baseline_cumulative"]["source_census"]
    assert source_census["comparison_eligible_count"] == 1
    assert source_census["comparison_exclusion_counts"] == {
        "skip_delta_reconciliation_mismatch": 1
    }


def test_cumulative_readiness_never_pools_owner_market_cohorts(tmp_path):
    observation_root = tmp_path / "market_weakness_observations"
    master_root = tmp_path / "micro_reversion_economic_reference"
    history_root = tmp_path / "machine_microstructure_attribution"
    history_root.mkdir()
    _write_master(master_root)
    for minute in (0, 2):
        _write_observation(
            observation_root,
            minute=minute,
            raw_state="BROAD_WEAKNESS",
            affected=["KOSPI", "KOSDAQ"],
        )
    for day in ("2026-08-24", "2026-08-25", "2026-08-26", "2026-08-27"):
        rows = []
        for index in range(5):
            owner = "episode" if index % 2 == 0 else "widget"
            rows.append(
                {
                    "anchor_id": f"{day}-{index}",
                    "owner": owner,
                    "listing_market": "KOSPI" if owner == "episode" else "KOSDAQ",
                    "actual_order_submitted": True,
                    "source_quality_status": "eligible",
                    "control": {
                        "status": "actual_realized",
                        "cost_aware_net_return_pct": -0.25,
                    },
                    "candidate_arms": {
                        "skip_new_entry_during_confirmed_weakness": {
                            "eligible": True,
                            "actual_realized_comparison": True,
                            "zero_exposure_counterfactual_return_pct": 0.0,
                            "incremental_vs_control_pct": 0.25,
                        }
                    },
                }
            )
        (history_root / f"machine_microstructure_attribution_{day}.json").write_text(
            json.dumps(
                {
                    "market_weakness_entry_response": {
                        "schema": "machine_market_weakness_response_v1",
                        "target_date": day,
                        "metric_contract": METRIC_CONTRACT,
                        "authority": {
                            "runtime_effect": False,
                            "allowed_runtime_apply": False,
                            "actual_order_submitted": False,
                            "broker_order_forbidden": True,
                            "policy_candidate_ready": False,
                        },
                        "entry_responses": rows,
                    }
                }
            ),
            encoding="utf-8",
        )

    report = build_machine_market_weakness_response(
        {
            "entry_anchors": [
                _anchor("005930"),
                _anchor("080220"),
            ]
        },
        target_date=TARGET_DATE,
        observation_root=observation_root,
        symbol_master_dir=master_root,
        history_report_dir=history_root,
    )

    cumulative = report["clean_baseline_cumulative"]
    assert cumulative["affected_actual_realized_trading_date_count"] == 5
    assert cumulative["affected_actual_realized_comparison_count"] == 22
    assert cumulative["incremental_vs_control_avg_pct"] > 0.0
    assert cumulative["review_ready_owner_market_cohort_count"] == 0
    assert cumulative["source_only_review_ready"] is False
