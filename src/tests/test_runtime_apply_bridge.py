import json

from src.engine import runtime_apply_bridge as mod


def _write_discovery(path, *, live=True):
    path.parent.mkdir(parents=True, exist_ok=True)
    live_candidates = []
    if live:
        live_candidates = [
            {
                "bucket_id": "entry:combo_entry_spot:score_66_69",
                "classification_state": "live_auto_apply_ready",
                "live_auto_apply_family": mod.ENTRY_BRIDGE_FAMILY,
                "ai_review_status": "unavailable",
                "ai_review_followup_required": "post_apply_verification",
                "ai_review_block_ignored_reason": "ambiguous_or_non_contract_gap_live_then_verify",
            },
            {
                "bucket_id": "scale_in:arm:pyramid",
                "classification_state": "live_auto_apply_ready",
                "live_auto_apply_family": mod.SCALE_IN_BRIDGE_FAMILY,
            },
        ]
    path.write_text(
        json.dumps(
            {
                "date": path.stem.removeprefix("lifecycle_bucket_discovery_"),
                "summary": {
                    "live_auto_apply_ready_count": len(live_candidates),
                    "source_contract_status": "pass",
                    "ai_two_pass_review_status": "unavailable" if live else None,
                },
                "live_auto_apply_candidates": live_candidates,
                "warnings": ["ai_two_pass_review_unavailable_live_auto_deferred_to_post_apply"] if live else [],
            }
        ),
        encoding="utf-8",
    )


def _write_ldm(path, *, entry_ev=1.2, pyramid_ev=-3.0, avg_down_ev=-0.4):
    path.write_text(
        json.dumps(
            {
                "date": path.stem.removeprefix("lifecycle_decision_matrix_"),
                "entry_bucket_attribution": {
                    "buckets": [
                        {
                            "bucket_type": "combo_entry_spot",
                            "bucket_key": mod.ENTRY_TARGET_BUCKET_KEY,
                            "joined_sample": 44,
                            "source_quality_adjusted_ev_pct": entry_ev,
                            "source_quality_gate": "pass",
                            "recommended_route": "candidate_recovery_or_relax",
                        }
                    ]
                },
                "scale_in_bucket_attribution": {
                    "buckets": [
                        {
                            "bucket_type": "arm",
                            "bucket_key": "PYRAMID",
                            "joined_sample": 38,
                            "source_quality_adjusted_ev_pct": pyramid_ev,
                            "source_quality_gate": "pass",
                            "recommended_route": "candidate_tighten_or_exclude",
                        },
                        {
                            "bucket_type": "blocker_namespace",
                            "bucket_key": "AVG_DOWN_ONLY",
                            "joined_sample": 2712,
                            "source_quality_adjusted_ev_pct": avg_down_ev,
                            "source_quality_gate": "pass",
                            "recommended_route": "candidate_tighten_or_exclude",
                        },
                        {
                            "bucket_type": "blocker_reason",
                            "bucket_key": "pnl_out_of_range(0.32)",
                            "joined_sample": 48,
                            "source_quality_adjusted_ev_pct": 0.32,
                            "source_quality_gate": "pass",
                            "recommended_route": "candidate_recovery_or_relax",
                        },
                    ]
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_runtime_apply_bridge_marks_daily_only_bucket_live_auto_ready(tmp_path, monkeypatch):
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "bridge"
    ldm_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    discovery_path = tmp_path / "discovery" / "lifecycle_bucket_discovery_2026-05-21.json"
    monkeypatch.setattr(mod, "discovery_report_path", lambda target_date: discovery_path)
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-21.json")
    _write_discovery(discovery_path)

    report = mod.write_runtime_apply_bridge_report("2026-05-21")

    states = {item["family"]: item["bridge_candidate_state"] for item in report["candidates"]}
    assert states[mod.ENTRY_BRIDGE_FAMILY] == "live_auto_apply_ready"
    assert states[mod.SCALE_IN_BRIDGE_FAMILY] == "live_auto_apply_ready"
    assert report["summary"]["live_auto_apply_ready_count"] == 2
    assert report["summary"]["lifecycle_bucket_discovery_live_followup_count"] == 1
    assert "lifecycle_bucket_discovery_live_auto_post_apply_followup_required" in report["warnings"]
    entry = {item["family"]: item for item in report["candidates"]}[mod.ENTRY_BRIDGE_FAMILY]
    assert entry["lifecycle_bucket_discovery_ai_followup_required"] == "post_apply_verification"
    assert entry["lifecycle_bucket_discovery_ai_block_ignored_reason"] == "ambiguous_or_non_contract_gap_live_then_verify"
    assert report["summary"]["approval_required_count"] == 0
    assert report["summary"]["runtime_mutation_performed"] is False
    assert (report_dir / "runtime_apply_bridge_2026-05-21.json").exists()
    assert (report_dir / "runtime_apply_bridge_2026-05-21.md").exists()


def test_runtime_apply_bridge_keeps_rolling_confirmed_entry_and_scale_candidates_live_auto(tmp_path, monkeypatch):
    ldm_dir = tmp_path / "ldm"
    ldm_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    discovery_path = tmp_path / "discovery" / "lifecycle_bucket_discovery_2026-05-21.json"
    monkeypatch.setattr(mod, "discovery_report_path", lambda target_date: discovery_path)
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-20.json")
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-21.json")
    _write_discovery(discovery_path)

    report = mod.build_runtime_apply_bridge_report("2026-05-21")
    by_family = {item["family"]: item for item in report["candidates"]}
    entry = by_family[mod.ENTRY_BRIDGE_FAMILY]
    scale = by_family[mod.SCALE_IN_BRIDGE_FAMILY]

    assert entry["bridge_candidate_state"] == "live_auto_apply_ready"
    assert entry["approval_required"] is False
    assert entry["allowed_runtime_apply"] is True
    assert entry["recommended_values"]["min_score"] == 66
    assert entry["recommended_values"]["max_score"] == 69
    assert scale["bridge_candidate_state"] == "live_auto_apply_ready"
    assert scale["approval_required"] is False
    assert scale["allowed_runtime_apply"] is True
    assert scale["recommended_values"]["scalping_enable_pyramid"] is False
    assert scale["recommended_values"]["reversal_add_min_ai_score"] == 65
    assert scale["observe_only_reference_buckets"][0]["role"] == "observe_only_reference"


def test_runtime_apply_bridge_blocks_live_when_discovery_does_not_confirm(tmp_path, monkeypatch):
    ldm_dir = tmp_path / "ldm"
    ldm_dir.mkdir()
    discovery_path = tmp_path / "discovery" / "lifecycle_bucket_discovery_2026-05-21.json"
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "discovery_report_path", lambda target_date: discovery_path)
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-21.json")
    _write_discovery(discovery_path, live=False)

    report = mod.build_runtime_apply_bridge_report("2026-05-21")
    states = {item["family"]: item["bridge_candidate_state"] for item in report["candidates"]}

    assert states[mod.ENTRY_BRIDGE_FAMILY] == "runtime_blocked_contract_gap"
    assert states[mod.SCALE_IN_BRIDGE_FAMILY] == "runtime_blocked_contract_gap"
    assert report["summary"]["live_auto_apply_ready_count"] == 0
