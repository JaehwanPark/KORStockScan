"""Tests for DeepSeek Swing Pattern Lab."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pandas as pd

from analysis.deepseek_swing_pattern_lab import prepare_dataset as prepare_mod
from analysis.deepseek_swing_pattern_lab.prepare_dataset import (
    build_data_quality_report,
    build_swing_lifecycle_funnel_fact,
    build_swing_ofi_qi_fact,
    build_swing_sequence_fact,
    build_swing_trade_fact,
    generate_data_quality_markdown,
)
from analysis.deepseek_swing_pattern_lab.analyze_swing_patterns import (
    analyze_entry_bottleneck,
    analyze_holding_exit_bottleneck,
    analyze_ofi_qi_quality,
    analyze_scale_in_bottleneck,
    analyze_selection_bottleneck,
    build_code_improvement_orders,
    build_swing_pattern_analysis_result,
    classify_finding_route,
)
from analysis.deepseek_swing_pattern_lab import build_deepseek_payload as payload_mod
from analysis.deepseek_swing_pattern_lab.build_deepseek_payload import (
    build_payload_cases,
    build_payload_summary,
    generate_ev_backlog_markdown,
    generate_final_review_markdown,
)


def _sample_funnel_fact() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "date": "2026-05-08",
                "selected_count": 5,
                "csv_rows": 5,
                "db_rows": 0,
                "entered_rows": 0,
                "completed_rows": 0,
                "valid_profit_rows": 0,
                "blocked_swing_gap_unique": 1,
                "blocked_swing_gap_raw": 10,
                "blocked_swing_gap_selection_unique": 1,
                "blocked_swing_gap_carryover_unique": 0,
                "blocked_gatekeeper_reject_unique": 2,
                "blocked_gatekeeper_reject_raw": 15,
                "blocked_gatekeeper_reject_selection_unique": 2,
                "blocked_gatekeeper_reject_carryover_unique": 0,
                "blocked_gatekeeper_missing_unique": 0,
                "blocked_gatekeeper_missing_selection_unique": 0,
                "blocked_gatekeeper_missing_carryover_unique": 0,
                "blocked_gatekeeper_error_unique": 0,
                "blocked_gatekeeper_error_selection_unique": 0,
                "blocked_gatekeeper_error_carryover_unique": 0,
                "market_regime_block_unique": 0,
                "market_regime_block_raw": 0,
                "market_regime_block_selection_unique": 0,
                "market_regime_block_carryover_unique": 0,
                "market_regime_pass_unique": 3,
                "submitted_raw_count": 0,
                "submitted_unique_records": 0,
                "simulated_order_raw_count": 0,
                "simulated_order_unique_records": 0,
                "missed_entry_unique": 0,
                "missed_entry_raw": 0,
                "blocked_reason": "",
                "gatekeeper_action": "",
                "floor_bull": 0.35,
                "floor_bear": 0.40,
                "fallback_written": False,
                "safe_pool_count": 49,
            }
        ]
    )


def _sample_trade_fact() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "date": "2026-05-08",
                "record_id": "1",
                "stock_code": "000001",
                "stock_name": "A",
                "strategy": "KOSPI_ML",
                "position_tag": "META_V2",
                "selection_mode": "SELECTED",
                "hybrid_mean": 0.36,
                "meta_score": 0.01,
                "floor_used": 0.35,
                "score_rank": 1,
                "status": "COMPLETED",
                "buy_qty": 10,
                "buy_price": 50000.0,
                "sell_qty": 10,
                "sell_price": 51500.0,
                "completed": True,
                "valid_profit_rate": 3.0,
                "profit_rate": 3.0,
                "profit": 15000,
                "actual_order_submitted": "",
                "simulation_owner": "",
                "add_count": 0,
                "avg_down_count": 0,
                "pyramid_count": 0,
                "last_add_type": "",
            },
            {
                "date": "2026-05-08",
                "record_id": "2",
                "stock_code": "000002",
                "stock_name": "B",
                "strategy": "KOSPI_ML",
                "position_tag": "META_V2",
                "selection_mode": "SELECTED",
                "hybrid_mean": 0.34,
                "meta_score": 0.02,
                "floor_used": 0.35,
                "score_rank": 2,
                "status": "COMPLETED",
                "buy_qty": 5,
                "buy_price": 30000.0,
                "sell_qty": 5,
                "sell_price": 29500.0,
                "completed": True,
                "valid_profit_rate": -1.67,
                "profit_rate": -1.67,
                "profit": -2500,
                "actual_order_submitted": "",
                "simulation_owner": "",
                "add_count": 1,
                "avg_down_count": 1,
                "pyramid_count": 0,
                "last_add_type": "AVG_DOWN",
            },
        ]
    )


def _sample_sequence_fact() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "date": "2026-05-08",
                "record_id": "1",
                "stock_code": "000001",
                "stock_name": "A",
                "strategy": "KOSPI_ML",
                "stage_count": 2,
                "entered": True,
                "held": False,
                "scale_in_observed": False,
                "exited": True,
                "completed": True,
                "exit_source": "PRESET_TARGET",
                "sell_reason_type": "",
                "holding_flow_action": "",
                "stages_seen": "[]",
            }
        ]
    )


def _sample_ofi_qi_fact() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "date": "2026-05-08",
                "record_id": "1",
                "stock_code": "000001",
                "stock_name": "A",
                "stage": "swing_entry_micro_context_observed",
                "group": "entry",
                "orderbook_micro_ready": True,
                "orderbook_micro_state": "bullish",
                "orderbook_micro_qi": 0.5,
                "orderbook_micro_qi_ewma": None,
                "orderbook_micro_ofi_norm": 0.6,
                "orderbook_micro_ofi_z": None,
                "orderbook_micro_snapshot_age_ms": 100,
                "orderbook_micro_observer_healthy": True,
                "orderbook_micro_ofi_threshold_source": "",
                "orderbook_micro_ofi_bucket_key": "",
                "swing_micro_advice": "SUPPORT_ENTRY",
                "swing_micro_runtime_effect": False,
                "smoothing_action": "",
                "micro_missing_flag": False,
                "micro_stale_flag": False,
                "observer_unhealthy_flag": False,
                "micro_not_ready_flag": False,
                "state_insufficient_flag": False,
                "stale_missing_reasons": "",
                "stale_missing_flag": False,
            },
            {
                "date": "2026-05-08",
                "record_id": "2",
                "stock_code": "000002",
                "stock_name": "B",
                "stage": "holding_flow_ofi_smoothing_applied",
                "group": "exit",
                "orderbook_micro_ready": False,
                "orderbook_micro_state": "insufficient",
                "orderbook_micro_qi": None,
                "orderbook_micro_qi_ewma": None,
                "orderbook_micro_ofi_norm": None,
                "orderbook_micro_ofi_z": None,
                "orderbook_micro_snapshot_age_ms": 0,
                "orderbook_micro_observer_healthy": False,
                "orderbook_micro_ofi_threshold_source": "",
                "orderbook_micro_ofi_bucket_key": "",
                "swing_micro_advice": "MISSING",
                "swing_micro_runtime_effect": False,
                "smoothing_action": "NO_CHANGE",
                "micro_missing_flag": True,
                "micro_stale_flag": False,
                "observer_unhealthy_flag": True,
                "micro_not_ready_flag": True,
                "state_insufficient_flag": True,
                "stale_missing_reasons": "micro_missing,observer_unhealthy,micro_not_ready,state_insufficient",
                "stale_missing_flag": True,
            },
        ]
    )


def _funnel_blocker_defaults() -> dict:
    return {
        "blocked_swing_gap_selection_unique": 0,
        "blocked_swing_gap_carryover_unique": 0,
        "blocked_gatekeeper_reject_selection_unique": 0,
        "blocked_gatekeeper_reject_carryover_unique": 0,
        "blocked_gatekeeper_missing_selection_unique": 0,
        "blocked_gatekeeper_missing_carryover_unique": 0,
        "blocked_gatekeeper_error_selection_unique": 0,
        "blocked_gatekeeper_error_carryover_unique": 0,
        "market_regime_block_selection_unique": 0,
        "market_regime_block_carryover_unique": 0,
    }


class TestPrepareDataset:
    def test_build_swing_trade_fact_from_sample(self):
        fact = build_swing_trade_fact(["2026-05-08"])
        assert isinstance(fact, pd.DataFrame)

    def test_build_swing_funnel_fact_empty(self):
        fact = build_swing_lifecycle_funnel_fact(["2099-01-01"])
        assert isinstance(fact, pd.DataFrame)
        assert len(fact) >= 1

    def test_build_swing_sequence_fact_empty(self):
        fact = build_swing_sequence_fact(["2099-01-01"])
        assert isinstance(fact, pd.DataFrame)

    def test_build_swing_ofi_qi_fact_empty(self):
        fact = build_swing_ofi_qi_fact(["2099-01-01"])
        assert isinstance(fact, pd.DataFrame)

    def test_sim_probe_events_include_broker_forbidden_provenance(self, tmp_path, monkeypatch):
        events_dir = tmp_path / "pipeline_events"
        events_dir.mkdir()
        target_date = "2026-05-08"
        (events_dir / f"pipeline_events_{target_date}.jsonl").write_text(
            "\n".join(
                [
                    json.dumps(
                        {
                            "stage": "swing_sim_buy_order_assumed_filled",
                            "record_id": "sim-1",
                            "stock_code": "000001",
                            "stock_name": "A",
                            "strategy": "KOSPI_ML",
                            "fields": {"profit_rate": "1.2"},
                            "emitted_at": "2026-05-08T10:00:00+09:00",
                        }
                    ),
                    json.dumps(
                        {
                            "stage": "swing_probe_exit_signal",
                            "record_id": "probe-1",
                            "stock_code": "000002",
                            "stock_name": "B",
                            "strategy": "KOSPI_ML",
                            "fields": {"orderbook_micro_ready": False, "swing_micro_advice": "MISSING"},
                            "emitted_at": "2026-05-08T10:01:00+09:00",
                        }
                    ),
                ]
            ),
            encoding="utf-8",
        )
        monkeypatch.setattr(prepare_mod, "PIPELINE_EVENTS_DIR", events_dir)

        sequence = prepare_mod.build_swing_sequence_fact([target_date])
        ofi_qi = prepare_mod.build_swing_ofi_qi_fact([target_date])
        report = prepare_mod.build_data_quality_report(pd.DataFrame(), pd.DataFrame({"date": [target_date]}), sequence, ofi_qi, [target_date])

        assert set(sequence["actual_order_submitted"]) == {False}
        assert set(sequence["broker_order_forbidden"]) == {True}
        assert set(sequence["decision_authority"]) == {"sim_equal_weight", "probe_observe_only"}
        assert bool(ofi_qi.iloc[0]["actual_order_submitted"]) is False
        assert bool(ofi_qi.iloc[0]["broker_order_forbidden"]) is True
        assert ofi_qi.iloc[0]["decision_authority"] == "probe_observe_only"
        assert report["sim_probe_provenance"]["sequence_fact_actual_order_submitted_false"] == 2
        assert report["sim_probe_provenance"]["ofi_qi_fact_broker_order_forbidden_true"] == 1

    def test_build_data_quality_report(self):
        trade = _sample_trade_fact()
        funnel = _sample_funnel_fact()
        seq = _sample_sequence_fact()
        ofi = _sample_ofi_qi_fact()
        report = build_data_quality_report(trade, funnel, seq, ofi, ["2026-05-08"])
        assert report["fact_counts"]["swing_trade_fact_rows"] == 2
        assert report["fact_counts"]["swing_ofi_qi_fact_rows"] == 2
        assert report["completed_trades"] == 2
        assert report["valid_profit_trades"] == 2
        assert report["ofi_qi_quality"]["reason_counts"]["micro_missing"] == 1
        assert report["ofi_qi_quality"]["reason_counts"]["observer_unhealthy"] == 1
        assert report["ofi_qi_quality"]["reason_counts"]["micro_not_ready"] == 1
        assert report["ofi_qi_quality"]["reason_counts"]["state_insufficient"] == 1
        assert report["ofi_qi_quality"]["reason_combination_counts"] == {
            "micro_missing+observer_unhealthy+micro_not_ready+state_insufficient": 1
        }
        assert report["ofi_qi_quality"]["stale_missing_unique_record_count"] == 1
        assert report["ofi_qi_quality"]["reason_combination_unique_record_counts"] == {
            "micro_missing+observer_unhealthy+micro_not_ready+state_insufficient": 1
        }
        assert report["ofi_qi_quality"]["stale_missing_group_counts"] == {"exit": 1}
        assert report["ofi_qi_quality"]["stale_missing_group_unique_record_counts"] == {"exit": 1}
        assert report["ofi_qi_quality"]["observer_unhealthy_overlap"] == {
            "observer_unhealthy_total": 1,
            "observer_unhealthy_with_other_reason": 1,
            "observer_unhealthy_only": 0,
        }
        assert report["ofi_qi_quality"]["examples"][0]["record_id"] == "2"
        assert not any("funnel fact has only" in warning for warning in report["warnings"])

    def test_ofi_qi_ready_neutral_without_advice_is_not_missing(self, tmp_path, monkeypatch):
        target_date = "2026-05-08"
        event_dir = tmp_path / "pipeline_events"
        event_dir.mkdir()
        monkeypatch.setattr(prepare_mod, "PIPELINE_EVENTS_DIR", event_dir)
        (event_dir / f"pipeline_events_{target_date}.jsonl").write_text(
            json.dumps(
                {
                    "stage": "holding_flow_ofi_smoothing_applied",
                    "stock_code": "005930",
                    "record_id": "1",
                    "fields": {
                        "strategy": "KOSPI_ML",
                        "orderbook_micro_ready": "True",
                        "orderbook_micro_state": "neutral",
                        "orderbook_micro_qi": "0.5",
                        "orderbook_micro_ofi_norm": "0.0",
                        "orderbook_micro_observer_healthy": "True",
                    },
                },
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )

        ofi_qi = prepare_mod.build_swing_ofi_qi_fact([target_date])

        assert len(ofi_qi) == 1
        assert bool(ofi_qi.iloc[0]["micro_missing_flag"]) is False
        assert bool(ofi_qi.iloc[0]["stale_missing_flag"]) is False
        report = build_data_quality_report(pd.DataFrame(), pd.DataFrame({"date": [target_date]}), pd.DataFrame(), ofi_qi, [target_date])
        assert not any(str(warning).startswith("OFI/QI stale/missing ratio:") for warning in report["warnings"])

    def test_build_data_quality_report_warns_when_funnel_rows_below_window_floor(self):
        trade = _sample_trade_fact()
        funnel = _sample_funnel_fact().iloc[:1].copy()
        seq = _sample_sequence_fact()
        ofi = _sample_ofi_qi_fact()
        report = build_data_quality_report(trade, funnel, seq, ofi, ["2026-05-08", "2026-05-09"])
        assert "funnel fact has only 1 rows (min 2)" in report["warnings"]

    def test_generate_data_quality_markdown(self):
        report = {
            "analysis_window": {"start": "2026-05-08", "end": "2026-05-08"},
            "fact_counts": {"swing_trade_fact_rows": 2, "swing_lifecycle_funnel_fact_rows": 1, "swing_sequence_fact_rows": 1, "swing_ofi_qi_fact_rows": 2},
            "completed_trades": 2,
            "valid_profit_trades": 2,
            "ofi_qi_quality": {
                "stale_missing_count": 1,
                "stale_missing_unique_record_count": 1,
                "stale_missing_ratio": 0.5,
                "reason_counts": {"micro_missing": 1},
                "reason_combination_counts": {"micro_missing": 1},
                "reason_combination_unique_record_counts": {"micro_missing": 1},
                "stale_missing_group_counts": {"entry": 1},
                "stale_missing_group_unique_record_counts": {"entry": 1},
                "observer_unhealthy_overlap": {"observer_unhealthy_total": 0},
            },
            "warnings": ["test warning"],
        }
        md = generate_data_quality_markdown(report)
        assert "test warning" in md
        assert "reason_counts" in md
        assert "reason_combination_counts" in md
        assert "2026-05-08" in md


class TestAnalyzeSwingPatterns:
    def test_analyze_selection_bottleneck_has_findings(self):
        funnel = _sample_funnel_fact()
        trade = _sample_trade_fact()
        findings = analyze_selection_bottleneck(funnel, trade)
        assert len(findings) >= 0
        for f in findings:
            assert f["runtime_effect"] is False
            assert f["lifecycle_stage"] == "selection"

    def test_analyze_entry_bottleneck_has_findings(self):
        funnel = _sample_funnel_fact()
        findings = analyze_entry_bottleneck(funnel)
        assert len(findings) >= 0
        for f in findings:
            assert f["runtime_effect"] is False
            assert f["lifecycle_stage"] == "entry"

    def test_analyze_holding_exit_bottleneck_has_findings(self):
        funnel = _sample_funnel_fact()
        trade = _sample_trade_fact()
        seq = _sample_sequence_fact()
        findings = analyze_holding_exit_bottleneck(funnel, seq, trade)
        assert len(findings) >= 1
        for f in findings:
            assert f["runtime_effect"] is False

    def test_analyze_scale_in_bottleneck_has_findings(self):
        trade = _sample_trade_fact()
        seq = _sample_sequence_fact()
        findings = analyze_scale_in_bottleneck(seq, trade)
        assert len(findings) >= 1
        for f in findings:
            assert f["runtime_effect"] is False

    def test_analyze_ofi_qi_quality_has_findings(self):
        ofi = _sample_ofi_qi_fact()
        findings = analyze_ofi_qi_quality(ofi)
        assert len(findings) >= 1
        for f in findings:
            assert f["runtime_effect"] is False
        stale_finding = next(f for f in findings if f["finding_id"].endswith("_ofi_qi_stale_missing"))
        assert stale_finding["evidence"]["stale_missing_reason_counts"]["micro_missing"] == 1
        assert stale_finding["evidence"]["stale_missing_reason_combination_counts"] == {
            "micro_missing+observer_unhealthy+micro_not_ready+state_insufficient": 1
        }
        assert stale_finding["evidence"]["stale_missing_unique_record_count"] == 1
        assert stale_finding["evidence"]["stale_missing_reason_combination_unique_record_counts"] == {
            "micro_missing+observer_unhealthy+micro_not_ready+state_insufficient": 1
        }
        assert stale_finding["evidence"]["observer_unhealthy_overlap"]["observer_unhealthy_with_other_reason"] == 1

    def test_build_code_improvement_orders_are_safe(self):
        findings = [
            {
                "finding_id": "test_001",
                "title": "Test finding",
                "lifecycle_stage": "entry",
                "route": "attach_existing_family",
                "mapped_family": "swing_gatekeeper_accept_reject",
                "confidence": "consensus",
                "evidence": {},
                "runtime_effect": False,
                "expected_ev_effect": "Test",
                "decision_classification": "attach_existing_family",
            },
            {
                "finding_id": "test_002",
                "title": "Deferred finding",
                "lifecycle_stage": "selection",
                "route": "defer_evidence",
                "mapped_family": None,
                "confidence": "solo",
                "evidence": {},
                "runtime_effect": False,
                "expected_ev_effect": "N/A",
                "decision_classification": "defer_evidence",
            },
        ]
        orders = build_code_improvement_orders(findings)
        assert len(orders) == 1
        for order in orders:
            assert order["runtime_effect"] is False
            assert order["allowed_runtime_apply"] is False

    def test_classify_finding_route(self):
        finding = {"route": "implement_now"}
        result = classify_finding_route(finding)
        assert result["decision_classification"] == "implement_now"

        finding2 = {"route": "attach_existing_family", "mapped_family": "some_family"}
        result2 = classify_finding_route(finding2)
        assert result2["decision_classification"] == "attach_existing_family"


class TestBuildDeepSeekPayload:
    def test_build_payload_summary(self):
        trade = _sample_trade_fact()
        funnel = _sample_funnel_fact()
        seq = _sample_sequence_fact()
        ofi = _sample_ofi_qi_fact()
        analysis = {"stage_findings": [], "code_improvement_orders": []}
        summary = build_payload_summary(trade, funnel, seq, ofi, analysis)
        assert summary["payload_type"] == "deepseek_swing_pattern_lab_summary"
        assert summary["counts"]["trade_rows"] == 2
        assert summary["case_counts"] == {"selected_trades": 2, "findings_brief": 0, "ofi_qi_samples": 2}
        assert summary["total_cases"] == 4
        assert summary["ofi_qi_summary"]["stale_missing_reason_counts"]["micro_missing"] == 1
        assert summary["ofi_qi_summary"]["stale_missing_reason_combination_counts"] == {
            "micro_missing+observer_unhealthy+micro_not_ready+state_insufficient": 1
        }
        assert summary["ofi_qi_summary"]["stale_missing_unique_record_count"] == 1
        assert summary["ofi_qi_summary"]["stale_missing_reason_combination_unique_record_counts"] == {
            "micro_missing+observer_unhealthy+micro_not_ready+state_insufficient": 1
        }
        assert summary["ofi_qi_summary"]["observer_unhealthy_overlap"]["observer_unhealthy_only"] == 0
        assert summary["feedback_sources"]["runtime_effect"] is False

    def test_build_payload_cases(self):
        trade = _sample_trade_fact()
        seq = _sample_sequence_fact()
        ofi = _sample_ofi_qi_fact()
        analysis = {"stage_findings": [], "code_improvement_orders": []}
        cases = build_payload_cases(trade, seq, ofi, analysis)
        assert cases["payload_type"] == "deepseek_swing_pattern_lab_cases"
        assert len(cases["selected_trades"]) == 2
        assert len(cases["ofi_qi_samples"]) == 2
        assert cases["ofi_qi_samples"][1]["reason_flags"]["micro_not_ready"] is True
        assert cases["feedback_sources"]["runtime_effect"] is False

    def test_generate_final_review_markdown(self):
        analysis = {
            "analysis_start": "2026-05-08",
            "analysis_end": "2026-05-08",
            "runtime_change": False,
            "data_quality": {"trade_rows": 2, "lifecycle_event_rows": 1, "completed_valid_profit_rows": 2, "ofi_qi_rows": 2, "warnings": []},
            "stage_findings": [
                {
                    "finding_id": "test_finding",
                    "title": "Test",
                    "lifecycle_stage": "entry",
                    "route": "defer_evidence",
                    "mapped_family": None,
                    "confidence": "solo",
                    "runtime_effect": False,
                    "expected_ev_effect": "N/A",
                }
            ],
            "code_improvement_orders": [],
        }
        summary = {"findings_count": 1, "order_count": 0}
        md = generate_final_review_markdown(analysis, summary)
        assert "Test" in md
        assert "defer_evidence" in md

    def test_generate_ev_backlog_markdown(self):
        analysis = {
            "runtime_change": False,
            "stage_findings": [
                {
                    "finding_id": "test",
                    "title": "Backlog item",
                    "lifecycle_stage": "selection",
                    "route": "attach_existing_family",
                    "mapped_family": "swing_model_floor",
                    "confidence": "consensus",
                    "expected_ev_effect": "Improve selection",
                }
            ],
        }
        md = generate_ev_backlog_markdown(analysis)
        assert "Backlog item" in md
        assert "MEDIUM" in md


class TestEdgeCases:
    def test_zero_candidates(self):
        funnel = pd.DataFrame(
            [
                {
                    "date": "2026-05-08",
                    "selected_count": 0,
                    "csv_rows": 0,
                    "db_rows": 0,
                    "entered_rows": 0,
                    "completed_rows": 0,
                    "valid_profit_rows": 0,
                    "blocked_swing_gap_unique": 0,
                    "blocked_swing_gap_raw": 0,
                    "blocked_gatekeeper_reject_unique": 0,
                    "blocked_gatekeeper_reject_raw": 0,
                    "blocked_gatekeeper_missing_unique": 0,
                    "blocked_gatekeeper_error_unique": 0,
                    "market_regime_block_unique": 0,
                    "market_regime_block_raw": 0,
                    "market_regime_pass_unique": 0,
                    "submitted_raw_count": 0,
                    "submitted_unique_records": 0,
                    "simulated_order_raw_count": 0,
                    "simulated_order_unique_records": 0,
                    "missed_entry_unique": 0,
                    "missed_entry_raw": 0,
                    "blocked_reason": "",
                    "gatekeeper_action": "",
                    "floor_bull": 0.35,
                    "floor_bear": 0.40,
                    "fallback_written": False,
                    "safe_pool_count": 0,
                }
            ]
        )
        trade = pd.DataFrame()
        findings = analyze_selection_bottleneck(funnel, trade)
        zero_finding = next((f for f in findings if "zero" in f.get("finding_id", "")), None)
        assert zero_finding is not None

    def test_gatekeeper_all_reject(self):
        funnel = pd.DataFrame(
            [
                {
                    **_funnel_blocker_defaults(),
                    "date": "2026-05-08",
                    "selected_count": 3,
                    "csv_rows": 3,
                    "db_rows": 0,
                    "entered_rows": 0,
                    "completed_rows": 0,
                    "valid_profit_rows": 0,
                    "blocked_swing_gap_unique": 0,
                    "blocked_swing_gap_raw": 0,
                    "blocked_gatekeeper_reject_unique": 3,
                    "blocked_gatekeeper_reject_raw": 100,
                    "blocked_gatekeeper_reject_selection_unique": 3,
                    "blocked_gatekeeper_missing_unique": 0,
                    "blocked_gatekeeper_error_unique": 0,
                    "market_regime_block_unique": 0,
                    "market_regime_block_raw": 0,
                    "market_regime_pass_unique": 0,
                    "submitted_raw_count": 0,
                    "submitted_unique_records": 0,
                    "simulated_order_raw_count": 0,
                    "simulated_order_unique_records": 0,
                    "missed_entry_unique": 0,
                    "missed_entry_raw": 0,
                    "blocked_reason": "",
                    "gatekeeper_action": "",
                    "floor_bull": 0.35,
                    "floor_bear": 0.40,
                    "fallback_written": False,
                    "safe_pool_count": 49,
                }
            ]
        )
        findings = analyze_entry_bottleneck(funnel)
        gatekeeper_finding = next((f for f in findings if "gatekeeper" in f.get("finding_id", "")), None)
        assert gatekeeper_finding is not None
        assert gatekeeper_finding["runtime_effect"] is False
        assert gatekeeper_finding["evidence"]["blocked_selection_unique"] == 3

    def test_no_exit_events(self):
        seq = pd.DataFrame()
        trade = pd.DataFrame()
        funnel = _sample_funnel_fact()
        findings = analyze_holding_exit_bottleneck(funnel, seq, trade)
        assert len(findings) >= 1
        for f in findings:
            assert f["runtime_effect"] is False

    def test_scale_in_none(self):
        trade = pd.DataFrame()
        seq = pd.DataFrame()
        findings = analyze_scale_in_bottleneck(seq, trade)
        assert len(findings) == 0

    def test_ofi_qi_stale_missing_high_ratio(self):
        ofi = pd.DataFrame(
            [
                {"stale_missing_flag": True, "swing_micro_advice": "MISSING", "orderbook_micro_state": "missing",
                 "swing_micro_runtime_effect": False, "smoothing_action": "", "group": "entry",
                 "stage": "test", "record_id": "1", "stock_code": "000001", "stock_name": "A", "date": "2026-05-08",
                 "orderbook_micro_ready": False, "orderbook_micro_observer_healthy": False},
                {"stale_missing_flag": False, "swing_micro_advice": "SUPPORT_ENTRY", "orderbook_micro_state": "bullish",
                 "swing_micro_runtime_effect": False, "smoothing_action": "", "group": "entry",
                 "stage": "test", "record_id": "2", "stock_code": "000002", "stock_name": "B", "date": "2026-05-08",
                 "orderbook_micro_ready": True, "orderbook_micro_observer_healthy": True},
            ]
        )
        findings = analyze_ofi_qi_quality(ofi)
        stale_finding = next((f for f in findings if "stale" in f.get("finding_id", "")), None)
        assert stale_finding is not None
        assert stale_finding["route"] == "implement_now"

    def test_all_orders_runtime_effect_false(self):
        findings = [
            {
                "finding_id": "test_001",
                "title": "Test finding",
                "lifecycle_stage": "entry",
                "route": "implement_now",
                "mapped_family": None,
                "confidence": "consensus",
                "evidence": {},
                "runtime_effect": False,
                "expected_ev_effect": "Test",
                "decision_classification": "implement_now",
            },
        ]
        orders = build_code_improvement_orders(findings)
        for order in orders:
            assert order["runtime_effect"] is False
            assert order["allowed_runtime_apply"] is False

    def test_entry_bottleneck_uses_unique_counts_not_raw(self):
        funnel = pd.DataFrame(
            [
                {
                    **_funnel_blocker_defaults(),
                    "date": "2026-05-08",
                    "selected_count": 5,
                    "csv_rows": 5,
                    "db_rows": 0,
                    "entered_rows": 0,
                    "completed_rows": 0,
                    "valid_profit_rows": 0,
                    "blocked_swing_gap_unique": 2,
                    "blocked_swing_gap_raw": 19008,
                    "blocked_swing_gap_selection_unique": 2,
                    "blocked_gatekeeper_reject_unique": 3,
                    "blocked_gatekeeper_reject_raw": 71,
                    "blocked_gatekeeper_reject_selection_unique": 3,
                    "blocked_gatekeeper_missing_unique": 0,
                    "blocked_gatekeeper_error_unique": 0,
                    "market_regime_block_unique": 1,
                    "market_regime_block_raw": 50,
                    "market_regime_block_selection_unique": 1,
                    "market_regime_pass_unique": 2,
                    "submitted_raw_count": 0,
                    "submitted_unique_records": 0,
                    "simulated_order_raw_count": 0,
                    "simulated_order_unique_records": 0,
                    "missed_entry_unique": 0,
                    "missed_entry_raw": 0,
                    "blocked_reason": "",
                    "gatekeeper_action": "",
                    "floor_bull": 0.35,
                    "floor_bear": 0.40,
                    "fallback_written": False,
                    "safe_pool_count": 49,
                }
            ]
        )
        findings = analyze_entry_bottleneck(funnel)
        gap_finding = next((f for f in findings if "gap_block" in f.get("finding_id", "")), None)
        gatekeeper_finding = next((f for f in findings if "gatekeeper_reject" in f.get("finding_id", "")), None)

        assert gap_finding is not None
        assert gap_finding["evidence"]["blocked_selection_unique"] == 2
        assert gap_finding["route"] == "design_family_candidate"
        assert gap_finding["mapped_family"] is None

        assert gatekeeper_finding is not None
        assert gatekeeper_finding["evidence"]["blocked_selection_unique"] == 3

    def test_gap_block_family_mapping_is_design_not_gatekeeper(self):
        funnel = pd.DataFrame(
            [
                {
                    **_funnel_blocker_defaults(),
                    "date": "2026-05-08",
                    "selected_count": 5,
                    "csv_rows": 5,
                    "db_rows": 0,
                    "entered_rows": 0,
                    "completed_rows": 0,
                    "valid_profit_rows": 0,
                    "blocked_swing_gap_unique": 5,
                    "blocked_swing_gap_raw": 100,
                    "blocked_swing_gap_selection_unique": 5,
                    "blocked_gatekeeper_reject_unique": 0,
                    "blocked_gatekeeper_reject_raw": 0,
                    "blocked_gatekeeper_missing_unique": 0,
                    "blocked_gatekeeper_error_unique": 0,
                    "market_regime_block_unique": 0,
                    "market_regime_block_raw": 0,
                    "market_regime_pass_unique": 0,
                    "submitted_raw_count": 0,
                    "submitted_unique_records": 0,
                    "simulated_order_raw_count": 0,
                    "simulated_order_unique_records": 0,
                    "missed_entry_unique": 0,
                    "missed_entry_raw": 0,
                    "blocked_reason": "",
                    "gatekeeper_action": "",
                    "floor_bull": 0.35,
                    "floor_bear": 0.40,
                    "fallback_written": False,
                    "safe_pool_count": 49,
                }
            ]
        )
        findings = analyze_entry_bottleneck(funnel)
        gap_finding = next((f for f in findings if "gap_block" in f.get("finding_id", "")), None)
        assert gap_finding is not None
        assert gap_finding["route"] == "design_family_candidate"
        assert gap_finding["mapped_family"] is None

    def test_blocked_greater_than_selected_population_split(self):
        funnel = pd.DataFrame(
            [
                {
                    **_funnel_blocker_defaults(),
                    "date": "2026-05-08",
                    "selected_count": 5,
                    "csv_rows": 5,
                    "db_rows": 0,
                    "entered_rows": 0,
                    "completed_rows": 0,
                    "valid_profit_rows": 0,
                    "blocked_swing_gap_unique": 10,
                    "blocked_swing_gap_raw": 100,
                    "blocked_swing_gap_selection_unique": 3,
                    "blocked_swing_gap_carryover_unique": 7,
                    "blocked_gatekeeper_reject_unique": 12,
                    "blocked_gatekeeper_reject_raw": 200,
                    "blocked_gatekeeper_reject_selection_unique": 4,
                    "blocked_gatekeeper_reject_carryover_unique": 8,
                    "blocked_gatekeeper_missing_unique": 2,
                    "blocked_gatekeeper_missing_selection_unique": 1,
                    "blocked_gatekeeper_missing_carryover_unique": 1,
                    "blocked_gatekeeper_error_unique": 0,
                    "market_regime_block_unique": 6,
                    "market_regime_block_raw": 50,
                    "market_regime_block_selection_unique": 2,
                    "market_regime_block_carryover_unique": 4,
                    "market_regime_pass_unique": 3,
                    "submitted_raw_count": 0,
                    "submitted_unique_records": 0,
                    "simulated_order_raw_count": 0,
                    "simulated_order_unique_records": 0,
                    "missed_entry_unique": 0,
                    "missed_entry_raw": 0,
                    "blocked_reason": "",
                    "gatekeeper_action": "",
                    "floor_bull": 0.35,
                    "floor_bear": 0.40,
                    "fallback_written": False,
                    "safe_pool_count": 49,
                }
            ]
        )
        findings = analyze_entry_bottleneck(funnel)
        gatekeeper_finding = next((f for f in findings if "gatekeeper_reject" in f.get("finding_id", "")), None)
        assert gatekeeper_finding is not None
        assert gatekeeper_finding["evidence"]["blocked_selection_unique"] == 4
        assert gatekeeper_finding["evidence"]["blocked_carryover_unique"] == 8
        assert gatekeeper_finding["evidence"]["selected_count"] == 5

        gap_finding = next((f for f in findings if "gap_block" in f.get("finding_id", "")), None)
        assert gap_finding is not None
        assert gap_finding["evidence"]["blocked_selection_unique"] == 3
        assert gap_finding["evidence"]["blocked_carryover_unique"] == 7


def test_swing_pattern_lab_automation_blocks_stale_output(tmp_path, monkeypatch):
    from src.engine import swing_pattern_lab_automation as mod
    lab_dir = tmp_path / "analysis" / "deepseek_swing_pattern_lab"
    outputs_dir = lab_dir / "outputs"
    outputs_dir.mkdir(parents=True)
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "DEEPSEEK_SWING_LAB_DIR", lab_dir)
    monkeypatch.setattr(mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", report_dir / "swing_pattern_lab_automation")

    (outputs_dir / "run_manifest.json").write_text(
        json.dumps({"analysis_window": {"start": "2026-05-06", "end": "2026-05-09"}}),
        encoding="utf-8",
    )
    (outputs_dir / "swing_pattern_analysis_result.json").write_text(
        json.dumps(
            {
                "stage_findings": [
                    {
                        "finding_id": "stale_test",
                        "title": "stale",
                        "route": "design_family_candidate",
                        "evidence": {"blocked_carryover_unique": 5, "blocked_selection_unique": 0},
                    },
                    {
                        "finding_id": "stale_test_2",
                        "title": "stale 2",
                        "route": "defer_evidence",
                        "evidence": {"blocked_carryover_unique": 3, "blocked_selection_unique": 1},
                    },
                ],
                "code_improvement_orders": [{"order_id": "stale_order", "title": "stale order", "route": "implement_now", "runtime_effect": False}],
            }
        ),
        encoding="utf-8",
    )
    (outputs_dir / "data_quality_report.json").write_text(
        json.dumps({"warnings": []}), encoding="utf-8"
    )

    report = mod.build_swing_pattern_lab_automation_report("2026-05-08")
    assert report["ev_report_summary"]["deepseek_lab_available"] is False
    assert "analysis_start_mismatch" in report["ev_report_summary"]["stale_reason"]
    assert report["ev_report_summary"]["code_improvement_order_count"] == 0
    assert report["ev_report_summary"]["findings_count"] == 0
    assert len(report["code_improvement_orders"]) == 0
    assert report["ev_report_summary"]["population_split_available"] is False
    assert report["ev_report_summary"]["carryover_warning_count"] == 0
    carryover_raw = report["data_quality"].get("carryover_warnings_raw") or []
    assert len(carryover_raw) == 1
    assert "stale_test" in carryover_raw[0]


def test_swing_pattern_lab_automation_blocks_malformed_json_output(tmp_path, monkeypatch):
    from src.engine import swing_pattern_lab_automation as mod
    lab_dir = tmp_path / "analysis" / "deepseek_swing_pattern_lab"
    outputs_dir = lab_dir / "outputs"
    outputs_dir.mkdir(parents=True)
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "DEEPSEEK_SWING_LAB_DIR", lab_dir)
    monkeypatch.setattr(mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", report_dir / "swing_pattern_lab_automation")

    (outputs_dir / "run_manifest.json").write_text(
        json.dumps({"analysis_window": {"start": "2026-05-08", "end": "2026-05-08"}}),
        encoding="utf-8",
    )
    (outputs_dir / "swing_pattern_analysis_result.json").write_text(
        json.dumps(
            {
                "stage_findings": [{"finding_id": "valid", "title": "valid", "route": "design_family_candidate"}],
                "code_improvement_orders": [{"order_id": "order_valid", "title": "valid", "route": "design_family_candidate", "runtime_effect": False}],
            }
        ),
        encoding="utf-8",
    )
    (outputs_dir / "data_quality_report.json").write_text(
        json.dumps({"warnings": []}), encoding="utf-8"
    )
    (outputs_dir / "deepseek_payload_summary.json").write_text(
        "not valid json {{{",
        encoding="utf-8",
    )

    report = mod.build_swing_pattern_lab_automation_report("2026-05-08")
    assert report["ev_report_summary"]["deepseek_lab_available"] is False
    assert "invalid_required_output" in report["ev_report_summary"]["stale_reason"]
    assert report["ev_report_summary"]["code_improvement_order_count"] == 0
    assert len(report["code_improvement_orders"]) == 0


def test_swing_pattern_lab_automation_blocks_missing_required_output(tmp_path, monkeypatch):
    from src.engine import swing_pattern_lab_automation as mod
    lab_dir = tmp_path / "analysis" / "deepseek_swing_pattern_lab"
    outputs_dir = lab_dir / "outputs"
    outputs_dir.mkdir(parents=True)
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "DEEPSEEK_SWING_LAB_DIR", lab_dir)
    monkeypatch.setattr(mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", report_dir / "swing_pattern_lab_automation")

    (outputs_dir / "run_manifest.json").write_text(
        json.dumps({"analysis_window": {"start": "2026-05-08", "end": "2026-05-08"}}),
        encoding="utf-8",
    )

    report = mod.build_swing_pattern_lab_automation_report("2026-05-08")
    assert report["ev_report_summary"]["deepseek_lab_available"] is False
    assert "missing_required_output" in report["ev_report_summary"]["stale_reason"]
    assert report["ev_report_summary"]["code_improvement_order_count"] == 0
    assert len(report["code_improvement_orders"]) == 0
    assert report["ev_report_summary"]["population_split_available"] is False


def test_swing_pattern_lab_automation_orders_have_allowed_runtime_apply_false(tmp_path, monkeypatch):
    from src.engine import swing_pattern_lab_automation as mod
    lab_dir = tmp_path / "analysis" / "deepseek_swing_pattern_lab"
    outputs_dir = lab_dir / "outputs"
    outputs_dir.mkdir(parents=True)
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "DEEPSEEK_SWING_LAB_DIR", lab_dir)
    monkeypatch.setattr(mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", report_dir / "swing_pattern_lab_automation")

    (outputs_dir / "run_manifest.json").write_text(
        json.dumps({"analysis_window": {"start": "2026-05-08", "end": "2026-05-08"}}),
        encoding="utf-8",
    )
    (outputs_dir / "swing_pattern_analysis_result.json").write_text(
        json.dumps(
            {
                "stage_findings": [{"finding_id": "valid_test", "title": "valid", "route": "design_family_candidate", "lifecycle_stage": "selection"}],
                "code_improvement_orders": [
                    {"order_id": "order_valid", "title": "valid order", "route": "design_family_candidate", "runtime_effect": False}
                ],
            }
        ),
        encoding="utf-8",
    )
    (outputs_dir / "data_quality_report.json").write_text(
        json.dumps({"warnings": []}), encoding="utf-8"
    )
    (outputs_dir / "deepseek_payload_summary.json").write_text(
        json.dumps({"total_cases": 4}), encoding="utf-8"
    )

    report = mod.build_swing_pattern_lab_automation_report("2026-05-08")
    assert report["runtime_effect"] is False
    assert report["runtime_mutation_allowed"] is False
    assert report["decision_authority"] == "swing_pattern_lab_analysis_workorder_source_only"
    for order in report["code_improvement_orders"]:
        assert order.get("runtime_effect") is False
        assert order.get("allowed_runtime_apply") is False, f"order {order.get('order_id')} missing allowed_runtime_apply=false"
        assert order.get("decision_authority") == "swing_pattern_lab_analysis_workorder_source_only"
        assert "swing_real_order_enable" in order.get("forbidden_uses", [])
    for family in report["auto_family_candidates"]:
        assert family.get("runtime_effect") is False
        assert family.get("allowed_runtime_apply") is False
        assert family.get("decision_authority") == "swing_pattern_lab_analysis_workorder_source_only"


def test_swing_pattern_lab_automation_marks_ofi_qi_instrumentation_implemented(tmp_path, monkeypatch):
    from src.engine import swing_pattern_lab_automation as mod

    lab_dir = tmp_path / "analysis" / "deepseek_swing_pattern_lab"
    outputs_dir = lab_dir / "outputs"
    outputs_dir.mkdir(parents=True)
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "DEEPSEEK_SWING_LAB_DIR", lab_dir)
    monkeypatch.setattr(mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", report_dir / "swing_pattern_lab_automation")

    (outputs_dir / "run_manifest.json").write_text(
        json.dumps({"analysis_window": {"start": "2026-05-08", "end": "2026-05-08"}}),
        encoding="utf-8",
    )
    (outputs_dir / "swing_pattern_analysis_result.json").write_text(
        json.dumps(
            {
                "stage_findings": [],
                "code_improvement_orders": [
                    {
                        "order_id": "order_swing_pattern_lab_deepseek_ofi_qi_stale_missing",
                        "title": "OFI/QI stale/missing quality review",
                        "route": "implement_now",
                        "mapped_family": "swing_entry_ofi_qi_execution_quality",
                        "runtime_effect": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (outputs_dir / "data_quality_report.json").write_text(
        json.dumps(
            {
                "warnings": [],
                "ofi_qi_quality": {
                    "sample_count": 3,
                    "stale_missing_count": 1,
                    "stale_missing_ratio": 0.3333,
                    "reason_counts": {"micro_missing": 1},
                    "reason_combination_counts": {"micro_missing": 1},
                    "reason_combination_unique_record_counts": {"micro_missing": 1},
                    "stale_missing_group_counts": {"entry": 1},
                    "stale_missing_group_unique_record_counts": {"entry": 1},
                    "observer_unhealthy_overlap": {
                        "observer_unhealthy_total": 0,
                        "observer_unhealthy_with_other_reason": 0,
                        "observer_unhealthy_only": 0,
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    (outputs_dir / "deepseek_payload_summary.json").write_text(
        json.dumps({"total_cases": 4}),
        encoding="utf-8",
    )

    report = mod.build_swing_pattern_lab_automation_report("2026-05-08")
    order = report["code_improvement_orders"][0]

    assert order["implementation_status"] == "implemented"
    assert order["implementation_provenance"]["decision_authority"] == "swing_pattern_lab_analysis_workorder_source_only"
    assert order["implementation_provenance"]["runtime_effect"] is False
    assert order["implementation_checks"][0]["status"] == "pass"
    contract = report["ev_report_summary"]["source_quality_contracts"]["swing_micro_context"]
    assert contract["source_contract_status"] == "implemented"
    assert contract["metric_role"] == "source_quality_gate"
    assert contract["runtime_effect"] is False
    assert contract["allowed_runtime_apply"] is False
    blocked = report["data_quality"]["source_quality_blocked_families"][0]
    assert blocked["source_contract_version"] == "swing_micro_context_source_quality_v1"
    assert blocked["decision_authority"] == "swing_pattern_lab_analysis_workorder_source_only"


def test_swing_pattern_lab_automation_marks_scale_in_events_observed_implemented(tmp_path, monkeypatch):
    from src.engine import swing_pattern_lab_automation as mod

    lab_dir = tmp_path / "analysis" / "deepseek_swing_pattern_lab"
    outputs_dir = lab_dir / "outputs"
    outputs_dir.mkdir(parents=True)
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "DEEPSEEK_SWING_LAB_DIR", lab_dir)
    monkeypatch.setattr(mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", report_dir / "swing_pattern_lab_automation")

    (outputs_dir / "run_manifest.json").write_text(
        json.dumps({"analysis_window": {"start": "2026-05-08", "end": "2026-05-08"}}),
        encoding="utf-8",
    )
    (outputs_dir / "swing_pattern_analysis_result.json").write_text(
        json.dumps(
            {
                "stage_findings": [],
                "code_improvement_orders": [
                    {
                        "order_id": "order_swing_pattern_lab_deepseek_scale_in_events_observed",
                        "title": "Scale-in events observed for swing positions",
                        "route": "attach_existing_family",
                        "mapped_family": "swing_scale_in_ofi_qi_confirmation",
                        "runtime_effect": False,
                        "evidence": [{"scale_in_events": 7}],
                        "next_postclose_metric": "swing_scale_in_quality_score",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (outputs_dir / "data_quality_report.json").write_text(
        json.dumps({"warnings": []}),
        encoding="utf-8",
    )
    (outputs_dir / "deepseek_payload_summary.json").write_text(
        json.dumps({"total_cases": 4}),
        encoding="utf-8",
    )

    report = mod.build_swing_pattern_lab_automation_report("2026-05-08")
    order = report["code_improvement_orders"][0]

    assert order["implementation_status"] == "implemented"
    assert order["implementation_provenance"]["source_contract"] == (
        "swing_pattern_lab_scale_in_events_source_metric_v1"
    )
    assert (
        order["implementation_provenance"]["implemented_scope"]
        == "swing_scale_in_events_observed_source_metric_provenance"
    )
    assert order["implementation_provenance"]["source_metric_snapshot"]["scale_in_events"] == 7
    assert order["implementation_provenance"]["runtime_effect"] is False
    assert order["implementation_provenance"]["allowed_runtime_apply"] is False
    assert order["implementation_provenance"]["actual_order_submitted"] is False
    assert order["implementation_checks"][0]["status"] == "pass"


def test_swing_pattern_lab_automation_marks_low_candidate_count_source_only(tmp_path, monkeypatch):
    from src.engine import swing_pattern_lab_automation as mod

    lab_dir = tmp_path / "analysis" / "deepseek_swing_pattern_lab"
    outputs_dir = lab_dir / "outputs"
    outputs_dir.mkdir(parents=True)
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "DEEPSEEK_SWING_LAB_DIR", lab_dir)
    monkeypatch.setattr(mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", report_dir / "swing_pattern_lab_automation")

    (outputs_dir / "run_manifest.json").write_text(
        json.dumps({"analysis_window": {"start": "2026-05-08", "end": "2026-05-08"}}),
        encoding="utf-8",
    )
    (outputs_dir / "swing_pattern_analysis_result.json").write_text(
        json.dumps(
            {
                "stage_findings": [],
                "code_improvement_orders": [
                    {
                        "order_id": "order_swing_pattern_lab_deepseek_selection_low_candidate_count",
                        "title": "Low swing candidate count per day",
                        "route": "attach_existing_family",
                        "mapped_family": "swing_selection_top_k",
                        "runtime_effect": False,
                        "evidence": [{"low_selected_dates": 1, "total_dates": 2}],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (outputs_dir / "data_quality_report.json").write_text(
        json.dumps({"warnings": []}),
        encoding="utf-8",
    )
    (outputs_dir / "deepseek_payload_summary.json").write_text(
        json.dumps({"total_cases": 4}),
        encoding="utf-8",
    )

    report = mod.build_swing_pattern_lab_automation_report("2026-05-08")
    order = report["code_improvement_orders"][0]

    assert order["implementation_status"] == "implemented_source_quality_contract_available"
    assert order["implementation_checks"][0]["status"] == "pass"
    assert order["implementation_provenance"]["source_contract"] == (
        "swing_pattern_lab_selection_low_candidate_source_metric_v1"
    )
    assert order["implementation_provenance"]["source_metric_snapshot"]["low_selected_rate"] == 0.5
    assert order["implementation_provenance"]["runtime_effect"] is False
    assert order["implementation_provenance"]["allowed_runtime_apply"] is False
    assert order["implementation_provenance"]["actual_order_submitted"] is False


def test_swing_pattern_lab_automation_marks_entry_submission_gap_implemented(tmp_path, monkeypatch):
    from src.engine import swing_pattern_lab_automation as mod

    lab_dir = tmp_path / "analysis" / "deepseek_swing_pattern_lab"
    outputs_dir = lab_dir / "outputs"
    outputs_dir.mkdir(parents=True)
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "DEEPSEEK_SWING_LAB_DIR", lab_dir)
    monkeypatch.setattr(mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", report_dir / "swing_pattern_lab_automation")

    (outputs_dir / "run_manifest.json").write_text(
        json.dumps({"analysis_window": {"start": "2026-05-08", "end": "2026-05-08"}}),
        encoding="utf-8",
    )
    (outputs_dir / "swing_pattern_analysis_result.json").write_text(
        json.dumps(
            {
                "stage_findings": [],
                "code_improvement_orders": [
                    {
                        "order_id": "order_swing_pattern_lab_deepseek_entry_no_submissions",
                        "title": "All selected candidates failed to reach order submission",
                        "route": "design_family_candidate",
                        "runtime_effect": False,
                        "evidence": [
                            {
                                "selected_count": 3,
                                "submitted_count": 0,
                                "blocked_gatekeeper_selection": 0,
                                "blocked_gap_selection": 0,
                                "blocked_market_selection": 0,
                            }
                        ],
                        "next_postclose_metric": "swing_entry_quality_score",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (outputs_dir / "data_quality_report.json").write_text(
        json.dumps({"warnings": []}),
        encoding="utf-8",
    )
    (outputs_dir / "deepseek_payload_summary.json").write_text(
        json.dumps({"total_cases": 4}),
        encoding="utf-8",
    )

    report = mod.build_swing_pattern_lab_automation_report("2026-05-08")
    order = report["code_improvement_orders"][0]

    assert order["implementation_status"] == "implemented"
    assert (
        order["implementation_provenance"]["source_contract"]
        == "swing_pattern_lab_entry_submission_gap_source_metric_v1"
    )
    assert (
        order["implementation_provenance"]["implemented_scope"]
        == "swing_entry_submission_gap_source_metric_provenance"
    )
    assert order["implementation_provenance"]["source_metric_snapshot"]["selected_count"] == 3
    assert order["implementation_provenance"]["runtime_effect"] is False


def test_swing_pattern_lab_automation_marks_ofi_qi_smoothing_review_implemented(tmp_path, monkeypatch):
    from src.engine import swing_pattern_lab_automation as mod

    lab_dir = tmp_path / "analysis" / "deepseek_swing_pattern_lab"
    outputs_dir = lab_dir / "outputs"
    outputs_dir.mkdir(parents=True)
    report_dir = tmp_path / "data" / "report"
    monkeypatch.setattr(mod, "DEEPSEEK_SWING_LAB_DIR", lab_dir)
    monkeypatch.setattr(mod, "SWING_PATTERN_LAB_AUTOMATION_DIR", report_dir / "swing_pattern_lab_automation")

    (outputs_dir / "run_manifest.json").write_text(
        json.dumps({"analysis_window": {"start": "2026-05-08", "end": "2026-05-08"}}),
        encoding="utf-8",
    )
    (outputs_dir / "swing_pattern_analysis_result.json").write_text(
        json.dumps(
            {
                "stage_findings": [],
                "code_improvement_orders": [
                    {
                        "order_id": "order_swing_pattern_lab_deepseek_ofi_qi_smoothing_review",
                        "title": "OFI/QI exit smoothing action distribution",
                        "route": "attach_existing_family",
                        "mapped_family": "swing_exit_ofi_qi_smoothing",
                        "runtime_effect": False,
                        "evidence": [{"smoothing_actions": {"NO_CHANGE": 9, "CONFIRM_EXIT": 2}}],
                        "next_postclose_metric": "swing_ofi_qi_quality_score",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (outputs_dir / "data_quality_report.json").write_text(
        json.dumps({"warnings": [], "ofi_qi_quality": {}}),
        encoding="utf-8",
    )
    (outputs_dir / "deepseek_payload_summary.json").write_text(
        json.dumps({"total_cases": 4}),
        encoding="utf-8",
    )

    report = mod.build_swing_pattern_lab_automation_report("2026-05-08")
    order = report["code_improvement_orders"][0]

    assert order["implementation_status"] == "implemented"
    assert (
        order["implementation_provenance"]["source_contract"]
        == "swing_pattern_lab_ofi_qi_smoothing_distribution_source_metric_v1"
    )
    assert order["implementation_provenance"]["source_metric_snapshot"]["smoothing_actions"]["CONFIRM_EXIT"] == 2
    assert order["implementation_provenance"]["runtime_effect"] is False


def test_deepseek_payload_feedback_selector_uses_daily_clean_baseline_artifacts(monkeypatch, tmp_path):
    report_dir = tmp_path / "data" / "report"
    ldm_dir = report_dir / "swing_lifecycle_decision_matrix"
    ldm_dir.mkdir(parents=True)
    (ldm_dir / "swing_lifecycle_decision_matrix_2026-06-05_mtd.json").write_text("{}", encoding="utf-8")
    (ldm_dir / "swing_lifecycle_decision_matrix_2026-06-03.json").write_text("{}", encoding="utf-8")
    (ldm_dir / "swing_lifecycle_decision_matrix_2026-06-04.json").write_text("{}", encoding="utf-8")
    monkeypatch.setattr(payload_mod, "REPORT_DIR", report_dir)

    path, source_date = payload_mod._latest_feedback_artifact_path(
        "swing_lifecycle_decision_matrix",
        "swing_lifecycle_decision_matrix",
        "2026-06-05",
    )

    assert path == ldm_dir / "swing_lifecycle_decision_matrix_2026-06-04.json"
    assert source_date == "2026-06-04"
