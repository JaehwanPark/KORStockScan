import json

from src.engine import runtime_apply_bridge as mod


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


def test_runtime_apply_bridge_marks_daily_only_bucket_bootstrap_pending(tmp_path, monkeypatch):
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "bridge"
    ldm_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-21.json")

    report = mod.write_runtime_apply_bridge_report("2026-05-21")

    states = {item["family"]: item["bridge_candidate_state"] for item in report["candidates"]}
    assert states[mod.ENTRY_BRIDGE_FAMILY] == "bootstrap_pending"
    assert states[mod.SCALE_IN_BRIDGE_FAMILY] == "bootstrap_pending"
    assert report["summary"]["runtime_mutation_performed"] is False
    assert (report_dir / "runtime_apply_bridge_2026-05-21.json").exists()
    assert (report_dir / "runtime_apply_bridge_2026-05-21.md").exists()


def test_runtime_apply_bridge_promotes_rolling_confirmed_entry_and_scale_candidates(tmp_path, monkeypatch):
    ldm_dir = tmp_path / "ldm"
    ldm_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-20.json")
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-21.json")

    report = mod.build_runtime_apply_bridge_report("2026-05-21")
    by_family = {item["family"]: item for item in report["candidates"]}
    entry = by_family[mod.ENTRY_BRIDGE_FAMILY]
    scale = by_family[mod.SCALE_IN_BRIDGE_FAMILY]

    assert entry["bridge_candidate_state"] == "ready_for_approval"
    assert entry["allowed_runtime_apply"] is True
    assert entry["recommended_values"]["min_score"] == 66
    assert entry["recommended_values"]["max_score"] == 69
    assert scale["bridge_candidate_state"] == "ready_for_approval"
    assert scale["allowed_runtime_apply"] is True
    assert scale["recommended_values"]["scalping_enable_pyramid"] is False
    assert scale["recommended_values"]["reversal_add_min_ai_score"] == 65
    assert scale["observe_only_reference_buckets"][0]["role"] == "observe_only_reference"
