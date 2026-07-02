from __future__ import annotations

import json

from src.engine.scalping import scalp_sim_auto_approval_control_tower as mod


def _lifecycle_approval() -> dict:
    return {
        "schema_version": "lifecycle_bucket_sim_auto_approval_v1",
        "date": "2026-05-26",
        "policy_id": "lifecycle_bucket_discovery_sim_auto_approval",
        "approved": True,
        "human_approval_required": False,
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "approved_bucket_ids": ["entry_bucket_a", "scale_bucket_b"],
        "approved_bucket_rows": [
            {
                "bucket_id": "entry_bucket_a",
                "source_bucket_id": "entry:combo:full:entry_bucket_a",
                "classification_state": "entry_only_sim_auto_approved",
                "source_bucket_kind": "entry_bucket_sim_policy",
                "stage": "entry",
                "bucket_type": "entry_bucket_attribution",
                "source_quality_adjusted_ev_pct": 1.2,
                "sample": 8,
                "joined_sample": 8,
                "complete_flow_count": None,
                "incomplete_flow_count": None,
            },
            {
                "bucket_id": "scale_bucket_b",
                "source_bucket_id": "scale_in:combo:full:scale_bucket_b",
                "classification_state": "sim_auto_approved",
                "source_bucket_kind": "scale_in_bucket_sim_policy",
                "stage": "scale_in",
                "bucket_type": "scale_in_bucket_attribution",
                "source_quality_adjusted_ev_pct": 0.7,
                "sample": 6,
                "joined_sample": 6,
                "complete_flow_count": None,
                "incomplete_flow_count": None,
            },
        ],
        "approved_bucket_count": 2,
        "approved_unique_source_bucket_count": 2,
    }


def _scale_in_approval() -> dict:
    return {
        "policy_id": "scalp_sim_scale_in_window_expansion",
        "family": "scalp_sim_scale_in_window_expansion",
        "approved": True,
        "approval_state": "sim_auto_approved",
        "human_approval_required": False,
        "runtime_effect": False,
        "allowed_runtime_apply": True,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "source_quality_status": "pass",
        "target_env_keys": ["SCALP_SIM_SCALE_IN_WINDOW_EXPANSION_ENABLED"],
        "recommended_values": {"enabled": True},
    }


def _runtime_bridge() -> dict:
    return {
        "candidates": [
            {
                "family": "scale_in_bucket_runtime_policy_v1",
                "bridge_candidate_state": "live_auto_apply_ready",
                "allowed_runtime_apply": True,
                "live_auto_apply": True,
            }
        ]
    }


def test_scalp_control_tower_merges_lifecycle_and_scale_in_sources(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "SIM_AUTO_APPROVAL_DIR", tmp_path / "approvals")
    monkeypatch.setattr(mod, "SCALP_SIM_POLICY_DIR", tmp_path / "policies")
    catalog = tmp_path / "lifecycle_bucket_catalog_2026-05-26.json"
    catalog.write_text(json.dumps({"buckets": []}), encoding="utf-8")

    approval = mod.build_scalp_sim_auto_approval(
        "2026-05-26",
        lifecycle_sim_approval=_lifecycle_approval(),
        lifecycle_bucket_catalog_path=catalog,
        scale_in_approval=_scale_in_approval(),
        runtime_apply_bridge=_runtime_bridge(),
    )

    assert approval["approved"] is True
    assert approval["approved_policy_count"] == 2
    assert approval["approved_source_ids"] == [
        "lifecycle_bucket_discovery",
        "scalp_sim_scale_in_window_approval",
    ]
    assert approval["runtime_effect"] is False
    assert approval["allowed_runtime_apply"] is False
    assert approval["actual_order_submitted"] is False
    assert approval["broker_order_forbidden"] is True
    assert approval["source_status"]["runtime_apply_bridge"]["live_auto_apply_ready_count"] == 1
    lifecycle_policy = next(item for item in approval["approved_policies"] if item["source_id"] == "lifecycle_bucket_discovery")
    assert lifecycle_policy["approved_bucket_count"] == 2
    assert lifecycle_policy["approved_unique_source_bucket_count"] == 2
    assert [row["source_bucket_id"] for row in lifecycle_policy["approved_bucket_rows"]] == [
        "entry:combo:full:entry_bucket_a",
        "scale_in:combo:full:scale_bucket_b",
    ]
    assert all(item["allowed_runtime_apply"] is False for item in approval["approved_policies"])


def test_scalp_control_tower_allows_active_seed_without_bucket_rows(tmp_path):
    catalog = tmp_path / "lifecycle_bucket_catalog_2026-06-01.json"
    catalog.write_text(json.dumps({"buckets": []}), encoding="utf-8")
    lifecycle = _lifecycle_approval()
    lifecycle["approved_bucket_ids"] = []
    lifecycle["approved_bucket_rows"] = []
    lifecycle["approved_bucket_count"] = 0
    lifecycle["active_sim_priority_seeds"] = [
        {
            "active_seed_id": "active_seed_test",
            "source_parent_bucket_id": "parent_positive",
            "status": "active",
            "observable_prefix": {
                "entry_score_parent": "score_watch_recovery",
                "entry_source_parent": "entry_source_blocked_ai_score",
            },
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
            "runtime_effect": False,
            "allowed_runtime_apply": False,
        }
    ]

    approval = mod.build_scalp_sim_auto_approval(
        "2026-06-01",
        lifecycle_sim_approval=lifecycle,
        lifecycle_bucket_catalog_path=catalog,
        scale_in_approval={},
        runtime_apply_bridge={},
    )
    catalog_payload = mod.build_policy_catalog(approval)

    assert approval["approved"] is True
    assert approval["approved_policy_count"] == 1
    assert catalog_payload["active_sim_priority_seeds"][0]["active_seed_id"] == "active_seed_test"
    assert catalog_payload["runtime_effect"] is False
    assert catalog_payload["broker_order_forbidden"] is True


def test_scalp_control_tower_adds_rising_missed_prior_active_seed(tmp_path):
    prior = {
        "report_type": "rising_missed_classifier_prior",
        "target_date": "2026-07-02",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "rising_missed_classifier_prior_source_only",
        "summary": {"prior_count": 1, "recommendation_counts": {"positive_prior": 1}},
        "priors": [
            {
                "prior_key": "entry_score_parent=score_watch_recovery|entry_source_parent=entry_source_wait6579",
                "recommendation": "positive_prior",
                "confidence": "high",
                "selected_window": "rolling10d",
                "reason": "rolling10d_positive_ev_prior",
                "observable_prefix": {
                    "entry_score_parent": "score_watch_recovery",
                    "entry_source_parent": "entry_source_wait6579",
                },
                "window_metrics": {"rolling10d": {"joined_sample": 33, "ev_pct": 2.97}},
            }
        ],
    }

    approval = mod.build_scalp_sim_auto_approval(
        "2026-07-02",
        lifecycle_sim_approval={},
        lifecycle_bucket_catalog_path=tmp_path / "missing_catalog.json",
        scale_in_approval={},
        runtime_apply_bridge={},
        rising_missed_prior=prior,
    )
    catalog_payload = mod.build_policy_catalog(approval)

    assert approval["approved"] is True
    assert approval["approved_source_ids"] == ["rising_missed_classifier_prior"]
    seed = catalog_payload["active_sim_priority_seeds"][0]
    assert seed["active_seed_id"].startswith("rising_missed_prior_")
    assert seed["status"] == "active"
    assert seed["priority_tier"] == "rising_missed_positive_prior"
    assert seed["observable_prefix"] == {
        "entry_score_parent": "score_watch_recovery",
        "entry_source_parent": "entry_source_wait6579",
    }
    assert catalog_payload["rising_missed_prior_observation_lanes"][0]["recommendation"] == "positive_prior"
    assert catalog_payload["runtime_effect"] is False
    assert catalog_payload["broker_order_forbidden"] is True


def test_scalp_control_tower_rising_missed_prior_cools_down_blocked_existing_seed(tmp_path):
    catalog = tmp_path / "lifecycle_bucket_catalog_2026-07-02.json"
    catalog.write_text(json.dumps({"buckets": []}), encoding="utf-8")
    lifecycle = _lifecycle_approval()
    lifecycle["approved_bucket_ids"] = []
    lifecycle["approved_bucket_rows"] = []
    lifecycle["approved_bucket_count"] = 0
    lifecycle["active_sim_priority_seeds"] = [
        {
            "active_seed_id": "active_seed_mid_wait6579",
            "source_parent_bucket_id": "parent_mid_wait6579",
            "status": "active",
            "observable_prefix": {
                "entry_score_parent": "score_mid_recovery",
                "entry_source_parent": "entry_source_wait6579",
            },
            "runtime_effect": False,
            "allowed_runtime_apply": False,
            "actual_order_submitted": False,
            "broker_order_forbidden": True,
        }
    ]
    prior = {
        "report_type": "rising_missed_classifier_prior",
        "target_date": "2026-07-02",
        "runtime_effect": False,
        "allowed_runtime_apply": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "decision_authority": "rising_missed_classifier_prior_source_only",
        "summary": {"prior_count": 1, "recommendation_counts": {"source_quality_blocked": 1}},
        "priors": [
            {
                "prior_key": "entry_score_parent=score_mid_recovery|entry_source_parent=entry_source_wait6579",
                "recommendation": "source_quality_blocked",
                "confidence": "blocked",
                "reason": "child_conflict_or_source_quality_gap",
                "observable_prefix": {
                    "entry_score_parent": "score_mid_recovery",
                    "entry_source_parent": "entry_source_wait6579",
                },
            }
        ],
    }

    approval = mod.build_scalp_sim_auto_approval(
        "2026-07-02",
        lifecycle_sim_approval=lifecycle,
        lifecycle_bucket_catalog_path=catalog,
        scale_in_approval={},
        runtime_apply_bridge={},
        rising_missed_prior=prior,
    )
    catalog_payload = mod.build_policy_catalog(approval)

    seed = catalog_payload["active_sim_priority_seeds"][0]
    assert seed["active_seed_id"] == "active_seed_mid_wait6579"
    assert seed["status"] == "cooldown"
    assert seed["rising_missed_prior_status_override"]["reason"] == (
        "rising_missed_prior_source_quality_blocked"
    )
    assert catalog_payload["rising_missed_prior_active_seed_status_overrides"][0]["forced_status"] == "cooldown"
    assert approval["source_status"]["rising_missed_classifier_prior"]["active_seed_status_override_count"] == 1


def test_scalp_control_tower_blocks_when_source_contract_invalid(tmp_path):
    bad_lifecycle = _lifecycle_approval()
    bad_lifecycle["runtime_effect"] = True

    approval = mod.build_scalp_sim_auto_approval(
        "2026-05-26",
        lifecycle_sim_approval=bad_lifecycle,
        lifecycle_bucket_catalog_path=tmp_path / "catalog.json",
        scale_in_approval={},
        runtime_apply_bridge={},
    )

    assert approval["approved"] is False
    assert "lifecycle_sim_auto_approval_contract_invalid" in approval["blocked_reasons"]
    assert "sim_policy_candidate_missing" in approval["blocked_reasons"]


def test_scalp_control_tower_writes_approval_and_catalog(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "SIM_AUTO_APPROVAL_DIR", tmp_path / "approvals")
    monkeypatch.setattr(mod, "SCALP_SIM_POLICY_DIR", tmp_path / "policies")
    lifecycle_catalog = tmp_path / "catalog.json"
    lifecycle_catalog.write_text(json.dumps({"buckets": []}), encoding="utf-8")

    approval = mod.build_scalp_sim_auto_approval(
        "2026-05-26",
        lifecycle_sim_approval=_lifecycle_approval(),
        lifecycle_bucket_catalog_path=lifecycle_catalog,
        scale_in_approval=_scale_in_approval(),
        runtime_apply_bridge={},
    )
    paths = mod.write_scalp_sim_auto_approval(approval)

    written = json.loads(paths["approval"].read_text(encoding="utf-8"))
    catalog = json.loads(paths["catalog"].read_text(encoding="utf-8"))
    assert written["report_type"] == "scalp_sim_auto_approval"
    assert catalog["schema_version"] == "scalp_sim_policy_catalog_v1"
    assert catalog["broker_order_forbidden"] is True
    assert len(catalog["policies"]) == 2
