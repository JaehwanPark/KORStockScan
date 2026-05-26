import json
from pathlib import Path

from src.engine import producer_gap_discovery as mod


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def _write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows), encoding="utf-8")


def _ai_response(candidate_ids: list[str]) -> dict:
    pattern_by_id = {
        "producer_gap_stop_recovery_counterfactual_missing": "stop_recovery_counterfactual_missing",
        "producer_gap_missed_fill_recovery_counterfactual_missing": "missed_fill_recovery_counterfactual_missing",
        "producer_gap_swing_sim_probe_label_gap_missing": "swing_sim_probe_label_gap_missing",
        "producer_gap_scale_in_counterfactual_gap_missing": "scale_in_counterfactual_gap_missing",
    }
    return {
        "schema_version": 1,
        "reviewer": "producer_gap_discovery_ai_review",
        "candidate_reviews": [
            {
                "candidate_id": candidate_id,
                "pattern_type": pattern_by_id[candidate_id],
                "priority": "high",
                "recommended_route": "implement_now",
                "confidence": "high",
                "target_subsystem": "postclose_source_producer",
                "reason": "dedicated source-only producer is required",
                "implementation_requirements": ["preserve runtime_effect=false"],
                "acceptance_tests": ["pytest producer gap tests"],
                "files_likely_touched": ["src/engine/producer_gap_discovery.py"],
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


def test_producer_gap_discovery_detects_four_patterns_and_ai_orders(tmp_path, monkeypatch):
    report_dir = tmp_path / "data" / "report"
    post_sell_dir = tmp_path / "data" / "post_sell"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "POST_SELL_DIR", post_sell_dir)

    _write_jsonl(
        post_sell_dir / "sim_post_sell_evaluations_2026-05-26.jsonl",
        [{"code": "036010", "exit_reason": "hard_stop", "profit_rate": -2.5, "mfe_pct": 1.1}],
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
        "producer_gap_stop_recovery_counterfactual_missing",
        "producer_gap_missed_fill_recovery_counterfactual_missing",
        "producer_gap_swing_sim_probe_label_gap_missing",
        "producer_gap_scale_in_counterfactual_gap_missing",
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
    assert {item["pattern_type"] for item in report["producer_gap_candidates"]} == {
        "stop_recovery_counterfactual_missing",
        "missed_fill_recovery_counterfactual_missing",
        "swing_sim_probe_label_gap_missing",
        "scale_in_counterfactual_gap_missing",
    }
    assert len(report["code_improvement_orders"]) == 4
    assert all(order["runtime_effect"] is False for order in report["code_improvement_orders"])
    assert (report_dir / "producer_gap_discovery" / "producer_gap_discovery_2026-05-26.json").exists()


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
