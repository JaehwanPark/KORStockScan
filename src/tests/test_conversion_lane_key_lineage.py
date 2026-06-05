import json
from pathlib import Path

from src.engine.automation import conversion_lane as lane
from src.engine.automation import key_lineage_ledger as ledger
from src.engine.scalping import scalp_sim_auto_approval_control_tower as scalp_catalog
from src.engine.swing import sim_auto_approval_control_tower as swing_catalog


def _write(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def _patch_dirs(monkeypatch, tmp_path):
    monkeypatch.setattr(ledger, "DATA_DIR", tmp_path)
    monkeypatch.setattr(ledger, "REPORT_DIR", tmp_path / "report" / "key_lineage_ledger")
    monkeypatch.setattr(ledger, "APPLY_PLAN_DIR", tmp_path / "threshold_cycle" / "apply_plans")
    monkeypatch.setattr(ledger, "SCALP_POLICY_DIR", tmp_path / "threshold_cycle" / "scalp_sim_policies")
    monkeypatch.setattr(ledger, "SWING_POLICY_DIR", tmp_path / "threshold_cycle" / "swing_sim_policies")
    monkeypatch.setattr(ledger, "HYPOTHESIS_PLAN_DIR", tmp_path / "threshold_cycle" / "ldm_hypothesis_observation_plans")
    monkeypatch.setattr(lane, "DATA_DIR", tmp_path)
    monkeypatch.setattr(lane, "REPORT_DIR", tmp_path / "report" / "conversion_lane")


def test_active_seed_same_key_continuity_pass(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    _write(
        tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json",
        {"active_sim_priority_seeds": [{"active_seed_id": "seed_a", "status": "active"}], "surfaced_candidates": []},
    )
    _write(
        tmp_path / "threshold_cycle" / "scalp_sim_policies" / f"scalp_sim_policy_catalog_{target}.json",
        {"active_sim_priority_seeds": [{"active_seed_id": "seed_a", "status": "active"}]},
    )
    _write(tmp_path / "threshold_cycle" / "swing_sim_policies" / f"swing_sim_policy_catalog_{target}.json", {})
    _write(
        tmp_path / "threshold_cycle" / "apply_plans" / "threshold_apply_2026-06-05.json",
        {"scalp_sim_auto_approval": {"approved_request": {"active_sim_priority_seed_ids": ["seed_a"]}}},
    )
    event_path = tmp_path / "pipeline_events" / f"pipeline_events_{target}.jsonl"
    event_path.parent.mkdir(parents=True, exist_ok=True)
    event_path.write_text(json.dumps({"fields": {"active_seed_id": "seed_a"}}) + "\n", encoding="utf-8")

    report = ledger.build_key_lineage_ledger(target)

    assert report["summary"]["same_key_continuity_pass_count"] == 1
    assert report["summary"]["key_mismatch_count"] == 0


def test_runtime_observed_seed_not_in_catalog_is_key_mismatch(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    _write(tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json", {})
    _write(tmp_path / "threshold_cycle" / "scalp_sim_policies" / f"scalp_sim_policy_catalog_{target}.json", {})
    _write(tmp_path / "threshold_cycle" / "swing_sim_policies" / f"swing_sim_policy_catalog_{target}.json", {})
    event_path = tmp_path / "pipeline_events" / f"pipeline_events_{target}.jsonl"
    event_path.parent.mkdir(parents=True, exist_ok=True)
    event_path.write_text(json.dumps({"fields": {"active_seed_id": "stale_seed"}}) + "\n", encoding="utf-8")

    report = ledger.build_key_lineage_ledger(target)

    assert report["summary"]["key_mismatch_count"] == 1
    assert report["lineage_rows"][0]["same_key_continuity"] == "fail"
    assert report["lineage_blockers"][0]["blocker_class"] == "key_lineage"


def test_runtime_lineage_uses_target_apply_catalog_not_next_catalog(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    _write(tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json", {})
    _write(
        tmp_path / "threshold_cycle" / "scalp_sim_policies" / "scalp_sim_policy_catalog_2026-06-02.json",
        {"active_sim_priority_seeds": [{"active_seed_id": "runtime_seed", "status": "active"}]},
    )
    _write(
        tmp_path / "threshold_cycle" / "scalp_sim_policies" / f"scalp_sim_policy_catalog_{target}.json",
        {"active_sim_priority_seeds": [{"active_seed_id": "next_day_seed", "status": "active"}]},
    )
    _write(tmp_path / "threshold_cycle" / "swing_sim_policies" / "swing_sim_policy_catalog_2026-06-02.json", {})
    _write(
        tmp_path / "threshold_cycle" / "apply_plans" / f"threshold_apply_{target}.json",
        {
            "source_date": "2026-06-02",
            "scalp_sim_auto_approval": {
                "catalog": str(tmp_path / "threshold_cycle" / "scalp_sim_policies" / "scalp_sim_policy_catalog_2026-06-02.json"),
                "approved_request": {"active_sim_priority_seed_ids": ["runtime_seed"]},
            },
            "swing_sim_auto_approval": {
                "catalog": str(tmp_path / "threshold_cycle" / "swing_sim_policies" / "swing_sim_policy_catalog_2026-06-02.json"),
            },
        },
    )
    _write(
        tmp_path / "threshold_cycle" / "apply_plans" / "threshold_apply_2026-06-05.json",
        {"scalp_sim_auto_approval": {"approved_request": {"active_sim_priority_seed_ids": ["next_day_seed"]}}},
    )
    event_path = tmp_path / "pipeline_events" / f"pipeline_events_{target}.jsonl"
    event_path.parent.mkdir(parents=True, exist_ok=True)
    event_path.write_text(json.dumps({"fields": {"active_seed_id": "runtime_seed"}}) + "\n", encoding="utf-8")

    report = ledger.build_key_lineage_ledger(target)

    assert report["summary"]["key_mismatch_count"] == 0
    assert report["summary"]["same_key_continuity_pass_count"] == 1


def test_hypothesis_plan_without_catalog_becomes_catalog_missing(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    _write(tmp_path / "threshold_cycle" / "ldm_hypothesis_observation_plans" / "ldm_hypothesis_observation_plan_2026-06-02.json", {"hypotheses": [{"hypothesis_id": "hyp_1"}]})
    _write(tmp_path / "threshold_cycle" / "scalp_sim_policies" / f"scalp_sim_policy_catalog_{target}.json", {})
    _write(tmp_path / "threshold_cycle" / "swing_sim_policies" / f"swing_sim_policy_catalog_{target}.json", {})

    report = ledger.build_key_lineage_ledger(target)

    assert report["summary"]["catalog_missing_count"] == 1


def test_hypothesis_match_attempt_without_id_is_natural_match_zero(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    _write(tmp_path / "threshold_cycle" / "ldm_hypothesis_observation_plans" / "ldm_hypothesis_observation_plan_2026-06-02.json", {"hypotheses": [{"hypothesis_id": "hyp_1"}]})
    _write(
        tmp_path / "threshold_cycle" / "scalp_sim_policies" / f"scalp_sim_policy_catalog_{target}.json",
        {"hypothesis_observation_plan": {"hypotheses": [{"hypothesis_id": "hyp_1"}]}},
    )
    _write(tmp_path / "threshold_cycle" / "swing_sim_policies" / f"swing_sim_policy_catalog_{target}.json", {})
    _write(tmp_path / "threshold_cycle" / "apply_plans" / f"threshold_apply_{target}.json", {"source_date": target})
    event_path = tmp_path / "pipeline_events" / f"pipeline_events_{target}.jsonl"
    event_path.parent.mkdir(parents=True, exist_ok=True)
    event_path.write_text(
        json.dumps({"fields": {"ldm_hypothesis_matched": "False", "ldm_hypothesis_candidate_features": "{}"}}) + "\n",
        encoding="utf-8",
    )

    report = ledger.build_key_lineage_ledger(target)

    assert report["summary"]["natural_match_0_count"] == 1
    assert report["summary"]["not_instrumented_count"] == 0


def test_runtime_matched_lifecycle_bucket_source_id_closes_bucket_continuity(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    source_bucket_id = "lifecycle_flow:combo_entry:abc123"
    _write(tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json", {})
    _write(
        tmp_path / "threshold_cycle" / "scalp_sim_policies" / f"scalp_sim_policy_catalog_{target}.json",
        {
            "policies": [
                {
                    "policy_id": "lifecycle_bucket_discovery_sim_auto_approval",
                    "approved_bucket_rows": [
                        {
                            "bucket_id": "lifecycle_flow:combo_entry",
                            "source_bucket_id": source_bucket_id,
                            "classification_state": "lifecycle_flow_sim_probe_candidate",
                            "source_bucket_kind": "lifecycle_flow_sim_probe_policy",
                            "source_quality_adjusted_ev_pct": 0.75,
                            "sample": 4,
                        }
                    ],
                }
            ]
        },
    )
    _write(tmp_path / "threshold_cycle" / "swing_sim_policies" / f"swing_sim_policy_catalog_{target}.json", {})
    _write(tmp_path / "threshold_cycle" / "apply_plans" / f"threshold_apply_{target}.json", {"source_date": target})
    event_path = tmp_path / "pipeline_events" / f"pipeline_events_{target}.jsonl"
    event_path.parent.mkdir(parents=True, exist_ok=True)
    event_path.write_text(
        json.dumps(
            {
                "fields": {
                    "bucket_directed_sim_probe": "True",
                    "lifecycle_bucket_match_status": "matched",
                    "lifecycle_bucket_bucket_id": "lifecycle_flow:combo_entry",
                    "lifecycle_bucket_source_bucket_id": source_bucket_id,
                }
            }
        )
        + "\n",
        encoding="utf-8",
    )

    report = ledger.build_key_lineage_ledger(target)

    bucket_rows = [row for row in report["lineage_rows"] if row["source_key_type"] == "bucket"]
    assert bucket_rows[0]["source_key_id"] == source_bucket_id
    assert bucket_rows[0]["conversion_state"] == "matched"
    assert bucket_rows[0]["same_key_continuity"] == "pass"
    assert report["summary"]["bucket_same_key_continuity_pass_count"] == 1


def test_conversion_lane_adds_runtime_observed_matched_bucket_to_real_queue(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    _write(
        tmp_path / "report" / "key_lineage_ledger" / f"key_lineage_ledger_{target}.json",
        {
            "summary": {"lineage_blocker_count": 0},
            "lineage_rows": [
                {
                    "source_key_id": "lifecycle_flow:combo_entry:abc123",
                    "source_key_type": "bucket",
                    "source_artifact": "scalp_sim_policy_catalog",
                    "same_key_continuity": "pass",
                    "conversion_state": "matched",
                    "evidence": {
                        "classification_state": "lifecycle_flow_sim_probe_candidate",
                        "primary_ev": 0.75,
                        "sample": 4,
                        "bucket_id": "lifecycle_flow:combo_entry",
                    },
                }
            ],
            "lineage_blockers": [],
        },
    )
    _write(tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json", {})

    report = lane.build_conversion_lane(target)

    assert report["summary"]["real_conversion_queue_count"] == 1
    assert report["real_conversion_queue"][0]["conversion_state"] == "runtime_observed"


def test_conversion_lane_promotes_lineage_blocker_to_rank(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-06-04"
    _write(
        tmp_path / "report" / "key_lineage_ledger" / f"key_lineage_ledger_{target}.json",
        {
            "summary": {"lineage_blocker_count": 1},
            "lineage_rows": [],
            "lineage_blockers": [
                {
                    "blocker_id": "b1",
                    "source_key_id": "seed_x",
                    "source_key_type": "active_seed",
                    "next_repair_action": "runtime_observed_seed_not_in_catalog",
                }
            ],
        },
    )
    _write(
        tmp_path / "report" / "lifecycle_bucket_discovery" / f"lifecycle_bucket_discovery_{target}.json",
        {
            "surfaced_candidates": [
                {
                    "bucket_id": "bucket_a",
                    "classification_state": "sim_auto_approved",
                    "source_quality_adjusted_ev_pct": 1.2,
                    "sample": 3,
                }
            ]
        },
    )

    report = lane.build_conversion_lane(target)

    assert report["summary"]["key_lineage_blocker_count"] == 1
    assert report["conversion_blocker_rank"][0]["blocker_class"] == "key_lineage"


def test_conversion_blocker_class_ignores_source_key_field_names():
    row = {
        "source_key_type": "bucket",
        "source_key_id": "bucket_a",
        "next_blocker": "bridge_contract",
        "bridge_state": "blocked_contract_gap",
    }

    assert lane._blocker_class("bridge_contract", row) == "bridge_contract"


def test_sim_policy_catalogs_merge_latest_hypothesis_plan(monkeypatch, tmp_path):
    plan_dir = tmp_path / "threshold_cycle" / "ldm_hypothesis_observation_plans"
    _write(plan_dir / "ldm_hypothesis_observation_plan_2026-06-02.json", {"hypotheses": [{"hypothesis_id": "hyp_1"}]})
    monkeypatch.setattr(scalp_catalog, "LDM_HYPOTHESIS_PLAN_DIR", plan_dir)
    monkeypatch.setattr(swing_catalog, "LDM_HYPOTHESIS_PLAN_DIR", plan_dir)

    scalp = scalp_catalog.build_policy_catalog({"date": "2026-06-04", "approved_policies": []})
    swing = swing_catalog.build_policy_catalog({"date": "2026-06-04", "active_arm_priority_policies": []})

    assert scalp["hypothesis_observation_plan"]["hypotheses"][0]["hypothesis_id"] == "hyp_1"
    assert swing["hypothesis_observation_plan"]["hypotheses"][0]["hypothesis_id"] == "hyp_1"
