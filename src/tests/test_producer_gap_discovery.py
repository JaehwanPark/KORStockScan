import gzip
import json
from pathlib import Path

from src.engine.automation.dual_candidate_review import (
    evidence_authority_contract,
    has_evidence_authority_violation,
)
from src.engine.automation import producer_gap_discovery as mod


def test_project_root_resolves_repo_root_after_package_move():
    assert mod.PROJECT_ROOT.name == "KORStockScan"
    assert mod.POST_SELL_DIR == mod.PROJECT_ROOT / "data" / "post_sell"


def test_real_anchor_detectors_have_sim_equivalent_contracts():
    contracts = {item.pattern_type: item for item in mod.DETECTOR_REGISTRY}
    for contract in mod.DETECTOR_REGISTRY:
        if contract.source_scope == "real_anchor" and contract.sim_equivalent_required:
            assert contract.sim_equivalent_pattern
            assert contract.sim_equivalent_pattern in contracts


def test_evidence_authority_contract_is_not_itself_a_violation():
    payload = {"evidence_authority_contract": evidence_authority_contract()}

    assert has_evidence_authority_violation(payload) is False


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")


def _write_gzip_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def _ai_response(candidate_ids: list[str]) -> dict:
    pattern_by_id = {
        "producer_gap_stop_recovery_counterfactual_missing": "stop_recovery_counterfactual_missing",
        "producer_gap_missed_fill_recovery_counterfactual_missing": "missed_fill_recovery_counterfactual_missing",
        "producer_gap_swing_sim_probe_label_gap_missing": "swing_sim_probe_label_gap_missing",
        "producer_gap_scale_in_counterfactual_gap_missing": "scale_in_counterfactual_gap_missing",
        "producer_gap_time_window_policy_exception_missing": "time_window_policy_exception_missing",
        "producer_gap_volatile_runner_exit_counterfactual_missing": "volatile_runner_exit_counterfactual_missing",
        "producer_gap_limit_up_plateau_breakdown_exit_missing": "limit_up_plateau_breakdown_exit_missing",
        "producer_gap_sim_entry_selection_gap_missing": "sim_entry_selection_gap_missing",
        "producer_gap_sim_submit_fill_quality_gap_missing": "sim_submit_fill_quality_gap_missing",
        "producer_gap_sim_holding_runner_gap_missing": "sim_holding_runner_gap_missing",
        "producer_gap_sim_exit_plateau_breakdown_gap_missing": "sim_exit_plateau_breakdown_gap_missing",
        "producer_gap_sim_stop_recovery_gap_missing": "sim_stop_recovery_gap_missing",
        "producer_gap_sim_scale_in_counterfactual_gap_missing": "sim_scale_in_counterfactual_gap_missing",
        "producer_gap_sim_time_window_exception_gap_missing": "sim_time_window_exception_gap_missing",
        "producer_gap_sim_source_quality_join_gap_missing": "sim_source_quality_join_gap_missing",
        "producer_gap_sim_first_coverage_gap": "sim_first_coverage_gap",
    }
    contract_fields = [
        "metric_role",
        "decision_authority",
        "window_policy",
        "sample_floor",
        "primary_decision_metric",
        "source_quality_gate",
        "forbidden_uses",
    ]
    return {
        "schema_version": 1,
        "reviewer": "producer_gap_discovery_ai_review",
        "candidate_reviews": [
            {
                "candidate_id": candidate_id,
                "pattern_type": pattern_by_id.get(candidate_id, candidate_id.replace("producer_gap_", "")),
                "priority": "high",
                "recommended_route": "implement_now",
                "confidence": "high",
                "target_subsystem": "postclose_source_producer",
                "reason": "dedicated source-only producer is required",
                "implementation_requirements": ["preserve runtime_effect=false"],
                "acceptance_tests": ["pytest producer gap tests"],
                "files_likely_touched": ["src/engine/automation/producer_gap_discovery.py"],
            }
            for candidate_id in candidate_ids
        ],
        "ai_tier2_proposals": [
            {
                "candidate_id": candidate_id,
                "proposal_decision": "absorb_as_metric_dimension"
                if "submit_fill_quality" in candidate_id
                else "new_producer",
                "recommended_canonical_bucket": f"producer_gap:{pattern_by_id.get(candidate_id, candidate_id)}",
                "recommended_metric_or_dimension": ["source_quality_adjusted_ev_pct", "diagnostic_win_rate"],
                "reasoning_summary": "AI proposal remains source-only",
                "confidence": "high",
                "required_source_fields": contract_fields,
                "forbidden_uses": mod.FORBIDDEN_USES,
            }
            for candidate_id in candidate_ids
        ],
        "comparative_reviews": [
            {
                "candidate_id": candidate_id,
                "selected_decision": "absorb_as_metric_dimension"
                if "submit_fill_quality" in candidate_id
                else "new_producer",
                "selected_source": "hybrid",
                "recommended_canonical_bucket": f"producer_gap:{pattern_by_id.get(candidate_id, candidate_id)}",
                "recommended_metric_or_dimension": ["source_quality_adjusted_ev_pct", "diagnostic_win_rate"],
                "comparison_summary": "deterministic and AI proposals agree",
                "rejected_alternative_reason": "",
                "confidence": "high",
                "required_source_fields": contract_fields,
                "forbidden_uses": mod.FORBIDDEN_USES,
                "workorder_title": "Review producer gap",
                "workorder_priority": "high",
            }
            for candidate_id in candidate_ids
        ],
        "audit": {
            "status": "pass",
            "issues": [],
            "forbidden_use_violations": [],
            "reason": "source-only authority preserved",
        },
    }


def test_producer_gap_ai_review_rejects_real_preapply_primary_ev_claim():
    candidate_id = "producer_gap_sim_submit_fill_quality_gap_missing"
    payload = _ai_response([candidate_id])
    payload["comparative_reviews"][0][
        "comparison_summary"
    ] = "Treat preapply_real primary_ev as decisive and merge_real_pnl_with_sim before policy enablement."

    status, _, warnings = mod._parse_ai_review_response(payload)

    assert status == "parse_rejected"
    assert f"ai_review_comparative_evidence_authority_violation:{candidate_id}" in warnings


def _minimal_runner_fixture(post_sell_dir: Path) -> None:
    _write_jsonl(
        post_sell_dir / "sim_post_sell_candidates_2026-05-26.jsonl",
        [
            {
                "stock_code": "003720",
                "stock_name": "Samyoung",
                "sim_parent_record_id": "p1",
                "sell_time": "09:20:00",
                "profit_rate": -2.4,
                "exit_reason": "hard_stop",
            },
            {
                "stock_code": "003720",
                "stock_name": "Samyoung",
                "sim_parent_record_id": "p1",
                "sell_time": "10:10:00",
                "profit_rate": 2.8,
                "exit_reason": "runner_exit",
            },
        ],
    )


def test_producer_gap_discovery_detects_seven_patterns_and_ai_orders(tmp_path, monkeypatch):
    report_dir = tmp_path / "data" / "report"
    post_sell_dir = tmp_path / "data" / "post_sell"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)

    _write_jsonl(
        post_sell_dir / "sim_post_sell_evaluations_2026-05-26.jsonl",
        [{"code": "036010", "exit_reason": "hard_stop", "profit_rate": -2.5, "mfe_pct": 1.1}],
    )
    _write_jsonl(
        post_sell_dir / "sim_post_sell_candidates_2026-05-26.jsonl",
        [
            {"code": "031330", "entry_time": "09:08:00", "profit_rate": -2.2, "exit_reason": "hard_stop"},
            {"code": "036010", "entry_time": "09:18:00", "profit_rate": -1.1, "exit_reason": "soft_stop"},
            {"code": "000100", "entry_time": "10:40:00", "profit_rate": 0.4, "exit_reason": "take_profit"},
            {
                "stock_code": "003720",
                "stock_name": "Samyoung",
                "sim_parent_record_id": "8198",
                "sell_time": "14:20:47",
                "profit_rate": -2.33,
                "exit_reason": "hard_stop",
            },
            {
                "stock_code": "003720",
                "stock_name": "Samyoung",
                "sim_parent_record_id": "8198",
                "sell_time": "14:33:47",
                "profit_rate": 6.33,
                "exit_reason": "trailing_take_profit",
            },
            {
                "stock_code": "036010",
                "stock_name": "Avaco",
                "sim_parent_record_id": "8077",
                "sell_time": "10:56:21",
                "profit_rate": 0.76,
                "exit_reason": "trailing_take_profit",
            },
            {
                "stock_code": "036010",
                "stock_name": "Avaco",
                "sim_parent_record_id": "8077",
                "sell_time": "14:41:25",
                "profit_rate": -2.68,
                "exit_reason": "hard_stop",
            },
        ],
    )
    _write_jsonl(
        post_sell_dir / "post_sell_candidates_2026-05-26.jsonl",
        [
            {
                "stock_code": "003720",
                "stock_name": "Samyoung",
                "recommendation_id": 8198,
                "sell_time": "14:21:29",
                "profit_rate": 0.73,
                "peak_profit": 2.72,
                "exit_rule": "scalp_trailing_take_profit",
            },
            {
                "stock_code": "036010",
                "stock_name": "Avaco",
                "recommendation_id": 8077,
                "sell_time": "14:42:19",
                "profit_rate": -2.69,
                "peak_profit": 0.96,
                "held_sec": 12674,
                "exit_rule": "scalp_hard_stop_pct",
            }
        ],
    )
    _write_json(
        report_dir / "monitor_snapshots" / "wait6579_ev_cohort_2026-05-26.json",
        {"metrics": {"avg_expected_ev_pct": 0.82, "expected_ev_krw_sum": 12850}},
    )
    _write_json(
        report_dir / "lifecycle_decision_matrix" / "lifecycle_decision_matrix_2026-05-26.json",
        {
            "submit_bucket_attribution": {"rows": [{"reason": "missed_fill defensive_price cancelled"}]},
            "scale_in_bucket_attribution": {"rows": [{"arm": "AVG_DOWN", "blocker_reason": "price_guard_missing"}]},
        },
    )
    _write_json(
        report_dir / "swing_strategy_discovery_ev" / "swing_strategy_discovery_ev_2026-05-26.json",
        {"arms": [{"state": "pending_label", "source_quality": "handoff_missing"}]},
    )

    candidate_ids = [
        str(item["candidate_id"])
        for item in mod._deterministic_candidates("2026-05-26")[0]
    ]
    report = mod.build_producer_gap_discovery_report(
        "2026-05-26",
        provider="openai",
        ai_raw_response=_ai_response(candidate_ids),
    )

    assert report["runtime_effect"] is False
    assert report["allowed_runtime_apply"] is False
    assert report["actual_order_submitted"] is False
    assert report["broker_order_forbidden"] is True
    assert report["status"] == "warning"
    assert report["summary"]["ai_two_pass_review_status"] == "parsed"
    pattern_types = {item["pattern_type"] for item in report["producer_gap_candidates"]}
    assert {
        "stop_recovery_counterfactual_missing",
        "missed_fill_recovery_counterfactual_missing",
        "swing_sim_probe_label_gap_missing",
        "scale_in_counterfactual_gap_missing",
        "time_window_policy_exception_missing",
        "volatile_runner_exit_counterfactual_missing",
        "limit_up_plateau_breakdown_exit_missing",
    }.issubset(pattern_types)
    assert "sim_holding_runner_gap_missing" in pattern_types
    assert "sim_exit_plateau_breakdown_gap_missing" in pattern_types
    time_window_candidate = next(
        item
        for item in report["producer_gap_candidates"]
        if item["pattern_type"] == "time_window_policy_exception_missing"
    )
    assert "operator_seed_cutoff=09:30" in time_window_candidate["evidence"]
    assert (
        "metric_scope=completed_sim_exit_pnl_vs_missed_entry_counterfactual_ev_not_directly_nettable"
        in time_window_candidate["evidence"]
    )
    assert any(item.startswith("time_window_measurement_keys=") for item in time_window_candidate["evidence"])
    assert (
        "required_policy_comparison=allow_all_vs_block_all_vs_block_general_allow_recovery"
        in time_window_candidate["evidence"]
    )
    assert time_window_candidate["recommended_producer_contract"]["preferred_producer_name"] == (
        "time_window_regime_counterfactual"
    )
    assert time_window_candidate["recommended_producer_contract"]["candidate_producer_name"] == (
        "time_window_regime_counterfactual"
    )
    assert time_window_candidate["recommended_producer_contract"]["compare_policies"] == [
        "allow_all_in_window",
        "block_all_in_window",
        "block_general_allow_exception_in_window",
    ]
    runner_candidate = next(
        item
        for item in report["producer_gap_candidates"]
        if item["pattern_type"] == "volatile_runner_exit_counterfactual_missing"
    )
    assert "required_comparison=real_exit_profit_vs_same_parent_sim_runner_profit" in runner_candidate["evidence"]
    assert any("003720:Samyoung" in item for item in runner_candidate["evidence"])
    plateau_candidate = next(
        item
        for item in report["producer_gap_candidates"]
        if item["pattern_type"] == "limit_up_plateau_breakdown_exit_missing"
    )
    assert "required_comparison=current_stop_exit_vs_plateau_take_profit_vs_breakdown_exit" in plateau_candidate["evidence"]
    assert any("036010:Avaco" in item for item in plateau_candidate["evidence"])
    assert len(report["code_improvement_orders"]) >= len(candidate_ids)
    assert report["summary"]["sim_first_pattern_count"] >= 2
    assert all(order["runtime_effect"] is False for order in report["code_improvement_orders"])
    assert all(order["allowed_runtime_apply"] is False for order in report["code_improvement_orders"])
    assert all(order["broker_order_forbidden"] is True for order in report["code_improvement_orders"])
    assert (report_dir / "producer_gap_discovery" / "producer_gap_discovery_2026-05-26.json").exists()


def test_sim_first_rolling_detects_runner_plateau_and_ambiguous_chronology(tmp_path, monkeypatch):
    report_dir = tmp_path / "data" / "report"
    post_sell_dir = tmp_path / "data" / "post_sell"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)

    _write_jsonl(
        post_sell_dir / "sim_post_sell_candidates_2026-05-20.jsonl",
        [
            {
                "stock_code": "001740",
                "stock_name": "SK Networks",
                "sim_parent_record_id": "p1",
                "sell_time": "09:22:00",
                "profit_rate": -3.25,
                "exit_reason": "hard_stop",
            },
            {
                "stock_code": "001740",
                "stock_name": "SK Networks",
                "sim_parent_record_id": "p1",
                "sell_time": "09:37:00",
                "profit_rate": 4.43,
                "exit_reason": "runner_exit",
            },
            {
                "stock_code": "036010",
                "stock_name": "Avaco",
                "sim_parent_record_id": "p2",
                "sell_time": "10:56:00",
                "profit_rate": 0.76,
                "exit_reason": "take_profit",
            },
            {
                "stock_code": "036010",
                "stock_name": "Avaco",
                "sim_parent_record_id": "p2",
                "sell_time": "14:41:00",
                "profit_rate": -2.68,
                "exit_reason": "hard_stop",
            },
            {
                "stock_code": "242040",
                "stock_name": "No Time",
                "sim_parent_record_id": "p3",
                "profit_rate": -2.33,
                "exit_reason": "hard_stop",
            },
            {
                "stock_code": "242040",
                "stock_name": "No Time",
                "sim_parent_record_id": "p3",
                "profit_rate": 2.54,
                "exit_reason": "runner_exit",
            },
        ],
    )
    candidate_ids = [
        "producer_gap_sim_holding_runner_gap_missing",
        "producer_gap_sim_exit_plateau_breakdown_gap_missing",
        "producer_gap_sim_stop_recovery_gap_missing",
        "producer_gap_sim_source_quality_join_gap_missing",
    ]

    report = mod.build_producer_gap_discovery_report(
        "2026-05-26",
        provider="openai",
        ai_raw_response=_ai_response(candidate_ids),
        rolling_sim_scan=True,
    )

    runner = next(item for item in report["producer_gap_candidates"] if item["pattern_type"] == "sim_holding_runner_gap_missing")
    plateau = next(item for item in report["producer_gap_candidates"] if item["pattern_type"] == "sim_exit_plateau_breakdown_gap_missing")
    assert "strict_match_count=1" in runner["evidence"]
    assert "ambiguous_match_count=1" in runner["evidence"]
    assert "strict_match_count=1" in plateau["evidence"]
    runner_order = next(
        item
        for item in report["code_improvement_orders"]
        if item["improvement_type"] == "sim_holding_runner_gap_missing"
    )
    assert runner_order["runtime_effect"] is False
    assert "runtime_hook_candidate_contract" not in runner
    assert "runtime_hook_candidate_contract" not in runner_order
    assert report["summary"]["rolling_sim_scan_enabled"] is True
    assert report["summary"]["sim_rows_scanned"] == 6


def test_producer_gap_discovery_reads_gzip_post_sell_sources(tmp_path, monkeypatch):
    report_dir = tmp_path / "data" / "report"
    post_sell_dir = tmp_path / "data" / "post_sell"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)
    _write_gzip_jsonl(
        post_sell_dir / "sim_post_sell_candidates_2026-05-26.jsonl.gz",
        [
            {
                "stock_code": "001740",
                "stock_name": "SK Networks",
                "sim_parent_record_id": "p1",
                "sell_time": "09:22:00",
                "profit_rate": -3.25,
                "exit_reason": "hard_stop",
            },
            {
                "stock_code": "001740",
                "stock_name": "SK Networks",
                "sim_parent_record_id": "p1",
                "sell_time": "09:37:00",
                "profit_rate": 4.43,
                "exit_reason": "runner_exit",
            },
        ],
    )

    report = mod.build_producer_gap_discovery_report(
        "2026-05-26",
        provider="openai",
        ai_raw_response=_ai_response(["producer_gap_sim_holding_runner_gap_missing"]),
        rolling_sim_scan=True,
    )

    assert report["summary"]["sim_rows_scanned"] == 2
    assert any(
        item["pattern_type"] == "sim_holding_runner_gap_missing"
        for item in report["producer_gap_candidates"]
    )
    assert all(item["runtime_effect"] is False for item in report["producer_gap_candidates"])


def test_ai_runtime_hook_contract_is_ignored_and_cannot_escalate_authority(tmp_path, monkeypatch):
    report_dir = tmp_path / "data" / "report"
    post_sell_dir = tmp_path / "data" / "post_sell"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)
    _minimal_runner_fixture(post_sell_dir)
    response = _ai_response(["producer_gap_sim_holding_runner_gap_missing"])
    response["candidate_reviews"][0]["runtime_hook_candidate_contract"] = {
        "hook_name": "malicious_runtime_hook",
        "runtime_effect": True,
        "allowed_runtime_apply": True,
    }

    report = mod.build_producer_gap_discovery_report(
        "2026-05-26",
        provider="openai",
        ai_raw_response=response,
        rolling_sim_scan=True,
    )

    runner = next(
        item
        for item in report["producer_gap_candidates"]
        if item["pattern_type"] == "sim_holding_runner_gap_missing"
    )
    order = next(
        item
        for item in report["code_improvement_orders"]
        if item["improvement_type"] == "sim_holding_runner_gap_missing"
    )
    assert "runtime_hook_candidate_contract" not in runner
    assert "runtime_hook_candidate_contract" not in order
    assert runner["runtime_effect"] is False
    assert runner["allowed_runtime_apply"] is False
    assert order["runtime_effect"] is False
    assert order["allowed_runtime_apply"] is False


def test_ai_forbidden_use_violation_surfaces_followup_workorder_without_retry(tmp_path, monkeypatch):
    report_dir = tmp_path / "data" / "report"
    post_sell_dir = tmp_path / "data" / "post_sell"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)
    _minimal_runner_fixture(post_sell_dir)
    response = _ai_response(["producer_gap_sim_holding_runner_gap_missing"])
    response["audit"]["forbidden_use_violations"] = ["attempted_runtime_apply_authority"]

    report = mod.build_producer_gap_discovery_report(
        "2026-05-26",
        provider="openai",
        ai_raw_response=response,
        rolling_sim_scan=True,
    )

    assert report["status"] == "warning"
    assert report["summary"]["ai_fail_closed"] is False
    assert report["summary"]["ai_review_followup_required"] is True
    assert report["ai_two_pass_review"]["provider_status"]["retry_attempted"] is False
    assert report["code_improvement_orders"][0]["improvement_type"] == "ai_review_followup"
    assert "forbidden_use_violation" in report["code_improvement_orders"][0]["ai_review_followup_reasons"]


def test_ai_forbidden_use_violation_handled_by_source_quality_blocker_does_not_surface_followup(tmp_path, monkeypatch):
    report_dir = tmp_path / "data" / "report"
    post_sell_dir = tmp_path / "data" / "post_sell"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)
    _minimal_runner_fixture(post_sell_dir)
    response = _ai_response(["producer_gap_sim_holding_runner_gap_missing"])
    response["audit"]["forbidden_use_violations"] = [
        "producer_gap_sim_holding_runner_gap_missing violates real_one_share_as_preapply_primary_ev"
    ]
    response["comparative_reviews"][0]["selected_decision"] = "source_quality_blocker"
    response["comparative_reviews"][0]["selected_source"] = "ai_tier2"

    report = mod.build_producer_gap_discovery_report(
        "2026-05-26",
        provider="openai",
        ai_raw_response=response,
        rolling_sim_scan=True,
    )

    assert report["summary"]["ai_review_followup_required"] is False
    assert report["summary"]["ai_review_followup_reasons"] == []
    assert report["ai_two_pass_review"]["unresolved_forbidden_use_violations"] == []
    assert report["ai_two_pass_review"]["handled_forbidden_use_violations"]
    assert not any(order["improvement_type"] == "ai_review_followup" for order in report["code_improvement_orders"])


def test_source_bundle_marks_entry_selection_and_missed_fill_candidates_implemented(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "report")
    bundle_path = tmp_path / "report" / "producer_gap_source_bundle" / "producer_gap_source_bundle_2026-05-26.json"
    bundle_path.parent.mkdir(parents=True)
    bundle_path.write_text(
        json.dumps(
            {
                "sections": [
                    {
                        "section_id": "missed_fill_recovery_counterfactual",
                        "pattern_type": "missed_fill_recovery_counterfactual",
                        "source_quality_status": "implemented",
                        "sample_count": 2,
                        "source_paths": ["lifecycle_decision_matrix.json"],
                        "join_keys": ["sim_record_id", "code", "submit_time", "fill_quality"],
                        "missing_fields": [],
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                    },
                    {
                        "section_id": "sim_entry_selection_bucket_producer",
                        "pattern_type": "sim_entry_selection_gap",
                        "source_quality_status": "implemented",
                        "sample_count": 2,
                        "source_paths": ["sim_post_sell_candidates.jsonl"],
                        "join_keys": ["sim_record_id", "candidate_id", "code", "source_stage"],
                        "missing_fields": [],
                        "runtime_effect": False,
                        "allowed_runtime_apply": False,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        mod,
        "producer_gap_source_bundle_paths",
        lambda target_date: (
            bundle_path,
            bundle_path.with_suffix(".md"),
        ),
    )
    candidates = [
        {
            "candidate_id": "producer_gap_missed_fill_recovery_counterfactual_missing",
            "pattern_type": "missed_fill_recovery_counterfactual_missing",
            "priority": "high",
            "source_paths": [],
        },
        {
            "candidate_id": "producer_gap_sim_entry_selection_gap_missing",
            "pattern_type": "sim_entry_selection_gap_missing",
            "priority": "high",
            "source_paths": [],
        },
    ]
    monkeypatch.setattr(
        mod,
        "_deterministic_candidates",
        lambda target_date, rolling_sim_scan=False: (candidates, {"date": target_date}),
    )

    report = mod.build_producer_gap_discovery_report(
        "2026-05-26",
        provider="openai",
        ai_raw_response=_ai_response([item["candidate_id"] for item in candidates]),
    )

    assert {
        item["candidate_id"]: item["implementation_status"]
        for item in report["producer_gap_candidates"]
    } == {
        "producer_gap_missed_fill_recovery_counterfactual_missing": "implemented",
        "producer_gap_sim_entry_selection_gap_missing": "implemented",
    }
    assert report["summary"]["status"] == "pass"
    assert report["summary"]["workorder_count"] == 0
    assert report["summary"]["implemented_candidate_count"] == 2
    assert report["code_improvement_orders"] == []


def test_openai_review_retries_with_low_reasoning_after_parse_reject(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "report")
    monkeypatch.setattr(
        mod,
        "producer_gap_source_bundle_paths",
        lambda target_date: (
            tmp_path / "report" / "producer_gap_source_bundle" / f"producer_gap_source_bundle_{target_date}.json",
            tmp_path / "report" / "producer_gap_source_bundle" / f"producer_gap_source_bundle_{target_date}.md",
        ),
    )
    candidate = {
        "candidate_id": "producer_gap_sim_entry_selection_gap_missing",
        "pattern_type": "sim_entry_selection_gap_missing",
        "lifecycle_stage": "entry",
        "priority": "high",
        "source_scope": "sim_first",
        "evidence": ["strict_match_count=2", "estimated_uplift_pct_sum=1.2"],
        "source_paths": [],
        "deterministic_proposal": {
            "proposal_decision": "new_producer",
            "required_source_fields": list(mod.REQUIRED_METRIC_CONTRACT_FIELDS),
        },
    }
    monkeypatch.setattr(
        mod,
        "_deterministic_candidates",
        lambda target_date, rolling_sim_scan=False: ([candidate], {"date": target_date}),
    )
    calls = []

    def fake_call(context, *, config=None):
        calls.append(config)
        status = {"provider": "openai", "status": "success", **config.provider_status_fields()}
        if len(calls) == 1:
            return "{not-json", status
        return _ai_response([candidate["candidate_id"]]), status

    monkeypatch.setattr(mod, "_call_openai_ai_review", fake_call)

    report = mod.build_producer_gap_discovery_report("2026-05-26", provider="openai")

    provider_status = report["ai_two_pass_review"]["provider_status"]
    assert [call.reasoning_effort for call in calls] == ["medium", "low"]
    assert provider_status["retry_attempted"] is True
    assert provider_status["attempt_role"] == "retry"
    assert provider_status["retry_reason"] == "ai_status_parse_rejected"
    assert provider_status["primary_attempt"]["reasoning_effort"] == "medium"
    assert report["summary"]["ai_fail_closed"] is False


def test_openai_review_does_not_retry_parsed_audit_correction_and_surfaces_workorder(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path / "report")
    monkeypatch.setattr(
        mod,
        "producer_gap_source_bundle_paths",
        lambda target_date: (
            tmp_path / "report" / "producer_gap_source_bundle" / f"producer_gap_source_bundle_{target_date}.json",
            tmp_path / "report" / "producer_gap_source_bundle" / f"producer_gap_source_bundle_{target_date}.md",
        ),
    )
    candidate = {
        "candidate_id": "producer_gap_sim_entry_selection_gap_missing",
        "pattern_type": "sim_entry_selection_gap_missing",
        "lifecycle_stage": "entry",
        "priority": "high",
        "source_scope": "sim_first",
        "evidence": ["strict_match_count=2", "estimated_uplift_pct_sum=1.2"],
        "source_paths": [],
        "deterministic_proposal": {
            "proposal_decision": "new_producer",
            "required_source_fields": list(mod.REQUIRED_METRIC_CONTRACT_FIELDS),
        },
    }
    monkeypatch.setattr(
        mod,
        "_deterministic_candidates",
        lambda target_date, rolling_sim_scan=False: ([candidate], {"date": target_date}),
    )
    calls = []

    def fake_call(context, *, config=None):
        calls.append(config)
        payload = _ai_response([candidate["candidate_id"]])
        payload["audit"]["status"] = "correction_required"
        payload["audit"]["issues"] = ["surface source-quality follow-up"]
        return payload, {"provider": "openai", "status": "success", **config.provider_status_fields()}

    monkeypatch.setattr(mod, "_call_openai_ai_review", fake_call)

    report = mod.build_producer_gap_discovery_report("2026-05-26", provider="openai")

    assert [call.reasoning_effort for call in calls] == ["medium"]
    assert report["summary"]["ai_fail_closed"] is False
    assert report["summary"]["ai_review_followup_required"] is True
    assert report["ai_two_pass_review"]["provider_status"]["retry_attempted"] is False
    assert any(order["improvement_type"] == "ai_review_followup" for order in report["code_improvement_orders"])


def test_main_accepts_ai_review_response_json(tmp_path, monkeypatch):
    report_dir = tmp_path / "data" / "report"
    post_sell_dir = tmp_path / "data" / "post_sell"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)
    _write_jsonl(
        post_sell_dir / "sim_post_sell_evaluations_2026-05-26.jsonl",
        [
            {
                "sim_record_id": "sim-1",
                "stock_code": "000001",
                "exit_reason": "hard_stop",
                "outcome": "MISSED_UPSIDE",
                "profit_rate": -1.0,
                "mfe_pct": 3.0,
                "mfe_10m_pct": 3.0,
                "close_10m_pct": 2.0,
            }
        ],
    )
    response_path = tmp_path / "review.json"
    response_path.write_text(
        json.dumps(_ai_response(["producer_gap_stop_recovery_counterfactual_missing"])),
        encoding="utf-8",
    )

    exit_code = mod.main(
        [
            "--date",
            "2026-05-26",
            "--provider",
            "none",
            "--ai-review-response-json",
            str(response_path),
        ]
    )

    assert exit_code == 0
    report = json.loads(
        (report_dir / "producer_gap_discovery" / "producer_gap_discovery_2026-05-26.json").read_text(
            encoding="utf-8"
        )
    )
    assert report["summary"]["ai_two_pass_review_status"] == "parsed"
    assert report["summary"]["audit_status"] == "pass"
    assert report["ai_two_pass_review"]["provider_status"]["status"] == "provided_response"
    assert report["code_improvement_orders"]


def test_sim_submit_quality_gap_ignores_false_actual_order_submitted(tmp_path, monkeypatch):
    report_dir = tmp_path / "data" / "report"
    post_sell_dir = tmp_path / "data" / "post_sell"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)

    _write_jsonl(
        post_sell_dir / "sim_post_sell_candidates_2026-05-26.jsonl",
        [
            {
                "stock_code": f"000{i:03d}",
                "sim_parent_record_id": f"p{i}",
                "profit_rate": 0.1,
                "actual_order_submitted": False,
            }
            for i in range(12)
        ],
    )

    report = mod.build_producer_gap_discovery_report(
        "2026-05-26",
        provider="openai",
        ai_raw_response=_ai_response(["producer_gap_sim_entry_selection_gap_missing"]),
        rolling_sim_scan=True,
    )

    pattern_types = {item["pattern_type"] for item in report["producer_gap_candidates"]}
    assert "sim_entry_selection_gap_missing" in pattern_types
    assert "sim_submit_fill_quality_gap_missing" not in pattern_types
    assert "sim_first_coverage_gap" not in pattern_types


def test_rolling_scan_dates_reflect_guarded_dates_only(tmp_path, monkeypatch):
    report_dir = tmp_path / "data" / "report"
    post_sell_dir = tmp_path / "data" / "post_sell"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)

    _write_jsonl(post_sell_dir / "sim_post_sell_candidates_2026-05-25.jsonl", [{"stock_code": "000001"}])
    _write_jsonl(post_sell_dir / "sim_post_sell_candidates_2026-05-26.jsonl", [{"stock_code": "000002"}])

    sources = mod._rolling_sim_sources("2026-05-26", rolling_sim_scan=True, max_rows=1)

    assert sources["guard_hit"] is True
    assert sources["paused_reason"] == "max_rows"
    assert sources["available_dates"] == ["2026-05-25", "2026-05-26"]
    assert sources["dates"] == ["2026-05-25"]


def test_producer_gap_discovery_ai_unavailable_fails_closed(tmp_path, monkeypatch):
    report_dir = tmp_path / "data" / "report"
    post_sell_dir = tmp_path / "data" / "post_sell"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)

    _write_jsonl(
        post_sell_dir / "sim_post_sell_evaluations_2026-05-26.jsonl",
        [{"code": "000001", "exit_reason": "hard_stop", "profit_rate": -2.5, "mfe_pct": 0.5}],
    )

    report = mod.build_producer_gap_discovery_report("2026-05-26", provider="none")

    assert report["status"] == "fail"
    assert report["summary"]["ai_fail_closed"] is True
    assert report["summary"]["ai_two_pass_review_status"] == "missing"
    assert report["producer_gap_candidates"]
    assert report["code_improvement_orders"] == []


def test_producer_gap_discovery_uses_time_window_regime_artifact_instead_of_missing_candidate(tmp_path, monkeypatch):
    report_dir = tmp_path / "data" / "report"
    post_sell_dir = tmp_path / "data" / "post_sell"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)

    _write_jsonl(
        post_sell_dir / "sim_post_sell_candidates_2026-05-26.jsonl",
        [
            {"code": "031330", "entry_time": "09:08:00", "profit_rate": -2.2, "exit_reason": "hard_stop"},
            {"code": "036010", "entry_time": "09:18:00", "profit_rate": -1.1, "exit_reason": "soft_stop"},
        ],
    )
    _write_json(
        report_dir / "monitor_snapshots" / "wait6579_ev_cohort_2026-05-26.json",
        {"metrics": {"avg_expected_ev_pct": 0.82, "expected_ev_krw_sum": 12850}},
    )
    _write_json(
        report_dir / "time_window_regime_counterfactual" / "time_window_regime_counterfactual_2026-05-26.json",
        {
            "report_type": "time_window_regime_counterfactual",
            "status": "pass",
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        },
    )

    candidates, _ = mod._deterministic_candidates("2026-05-26")

    assert "time_window_policy_exception_missing" not in {item["pattern_type"] for item in candidates}
