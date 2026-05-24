from __future__ import annotations

import json

from src.engine.swing import sim_auto_approval_control_tower as mod


def _swing_discovery() -> dict:
    return {
        "report_type": "swing_lifecycle_bucket_discovery",
        "date": "2026-05-22",
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": False,
        "sim_auto_approved_candidates": [
            {
                "bucket_id": "swing_bucket_entry_combo_probe",
                "lifecycle_stage": "entry",
                "bucket_type": "combo_entry_spot",
                "bucket_key": "probe",
                "source_quality_adjusted_ev_pct": 1.4,
            }
        ],
    }


def _bottom_policy() -> dict:
    return {
        "report_type": "swing_bottom_rebound_policy_auto_loop",
        "date": "2026-05-22",
        "runtime_effect": False,
        "actual_order_submitted": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": False,
        "final_conclusion": {"classification_state": "sim_auto_approved", "promote_policy": True},
        "sim_auto_approved_policy": {
            "policy_version": "bottom_rebound_swing_source_v2",
            "max_candidates": 40,
            "min_backtest_rank_score": 2.5,
            "min_primary_adjusted_ev_pct": 0.1,
        },
    }


def test_control_tower_merges_swing_ldm_and_bottom_rebound_sources() -> None:
    approval = mod.build_swing_sim_auto_approval(
        "2026-05-22",
        swing_lifecycle_bucket_report=_swing_discovery(),
        bottom_rebound_policy_report=_bottom_policy(),
    )

    assert approval["approved"] is True
    assert approval["approved_policy_count"] == 2
    assert approval["approved_source_ids"] == [
        "bottom_rebound_policy_auto_loop",
        "swing_lifecycle_bucket_discovery",
    ]
    assert approval["runtime_effect"] is False
    assert approval["actual_order_submitted"] is False
    assert approval["broker_order_forbidden"] is True
    assert approval["allowed_runtime_apply"] is False
    assert mod.bottom_rebound_is_approved_by_control_tower(approval) is True


def test_control_tower_writes_approval_and_catalog(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(mod, "SIM_AUTO_APPROVAL_DIR", tmp_path / "approvals")
    monkeypatch.setattr(mod, "SWING_SIM_POLICY_DIR", tmp_path / "policies")

    approval = mod.build_swing_sim_auto_approval(
        "2026-05-22",
        swing_lifecycle_bucket_report=_swing_discovery(),
        bottom_rebound_policy_report=_bottom_policy(),
    )
    paths = mod.write_swing_sim_auto_approval(approval)

    written = json.loads(paths["approval"].read_text(encoding="utf-8"))
    catalog = json.loads(paths["catalog"].read_text(encoding="utf-8"))
    assert written["report_type"] == "swing_sim_auto_approval"
    assert catalog["schema_version"] == "swing_sim_policy_catalog_v1"
    assert len(catalog["policies"]) == 2
    assert catalog["broker_order_forbidden"] is True
