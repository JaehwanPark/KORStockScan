import json

from src.engine import runtime_apply_bridge as mod


def _write_discovery(path, *, live=True, tier2_status="parsed"):
    path.parent.mkdir(parents=True, exist_ok=True)
    live_candidates = []
    if live:
        live_candidates = [
            {
                "bucket_id": "entry:combo_entry_spot:score_66_69",
                "classification_state": "live_auto_apply_ready",
                "live_auto_apply_family": mod.ENTRY_BRIDGE_FAMILY,
                "allowed_runtime_apply": True,
                "broker_order_forbidden": False,
                "source_quality_gate": "pass",
                "ai_review_status": tier2_status,
                "auto_promotion_contract": {"tier2_status": tier2_status, "tier2_policy": "fail_closed"},
            },
            {
                "bucket_id": "scale_in:arm:pyramid",
                "classification_state": "live_auto_apply_ready",
                "live_auto_apply_family": mod.SCALE_IN_BRIDGE_FAMILY,
                "allowed_runtime_apply": True,
                "broker_order_forbidden": False,
                "source_quality_gate": "pass",
                "ai_review_status": tier2_status,
                "auto_promotion_contract": {"tier2_status": tier2_status, "tier2_policy": "fail_closed"},
            },
        ]
    path.write_text(
        json.dumps(
            {
                "date": path.stem.removeprefix("lifecycle_bucket_discovery_"),
                "summary": {
                    "live_auto_apply_ready_count": len(live_candidates),
                    "source_contract_status": "pass",
                    "ai_two_pass_review_status": tier2_status if live else None,
                },
                "live_auto_apply_candidates": live_candidates,
                "warnings": [],
            }
        ),
        encoding="utf-8",
    )


def _write_ldm(path, *, entry_ev=1.2, pyramid_ev=-3.0, avg_down_ev=-1.4):
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
    assert report["summary"]["lifecycle_bucket_discovery_live_followup_count"] == 0
    entry = {item["family"]: item for item in report["candidates"]}[mod.ENTRY_BRIDGE_FAMILY]
    assert entry["allowed_runtime_apply"] is True
    assert "AI_SCORE65_74_RECOVERY_PROBE_ENABLED" in entry["target_env_keys"]
    assert entry["evidence_grade"] == "grade_2_counterfactual"
    assert entry["legacy_family_archived"] is False
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
    assert entry["transition_target"] == "bounded_live_canary"
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


def test_runtime_apply_bridge_blocks_live_when_discovery_tier2_not_parsed(tmp_path, monkeypatch):
    ldm_dir = tmp_path / "ldm"
    ldm_dir.mkdir()
    discovery_path = tmp_path / "discovery" / "lifecycle_bucket_discovery_2026-05-21.json"
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "discovery_report_path", lambda target_date: discovery_path)
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-21.json")
    _write_discovery(discovery_path, live=True, tier2_status="parse_rejected")

    report = mod.build_runtime_apply_bridge_report("2026-05-21")
    states = {item["family"]: item["bridge_candidate_state"] for item in report["candidates"]}

    assert states[mod.ENTRY_BRIDGE_FAMILY] == "runtime_blocked_contract_gap"
    assert states[mod.SCALE_IN_BRIDGE_FAMILY] == "runtime_blocked_contract_gap"


def test_runtime_apply_bridge_accepts_wait6579_live_discovery_candidate(tmp_path, monkeypatch):
    ldm_dir = tmp_path / "ldm"
    ldm_dir.mkdir()
    discovery_path = tmp_path / "discovery" / "lifecycle_bucket_discovery_2026-05-21.json"
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "discovery_report_path", lambda target_date: discovery_path)
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-21.json")
    _write_discovery(discovery_path, live=True, tier2_status="parsed")

    report = mod.build_runtime_apply_bridge_report("2026-05-21")
    entry = {item["family"]: item for item in report["candidates"]}[mod.ENTRY_BRIDGE_FAMILY]

    assert entry["bridge_candidate_state"] == "live_auto_apply_ready"
    assert entry["live_auto_apply"] is True
    assert entry["allowed_runtime_apply"] is True
    assert entry["runtime_effect_after_approval"] == "bounded_entry_probe_recovery_live_auto"


def test_runtime_apply_bridge_scale_ev_floor_miss_is_explicit_hold_not_contract_gap(tmp_path, monkeypatch):
    ldm_dir = tmp_path / "ldm"
    ldm_dir.mkdir()
    discovery_path = tmp_path / "discovery" / "lifecycle_bucket_discovery_2026-05-21.json"
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "discovery_report_path", lambda target_date: discovery_path)
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-21.json", pyramid_ev=0.4, avg_down_ev=-0.4)
    _write_discovery(discovery_path, live=False)

    report = mod.build_runtime_apply_bridge_report("2026-05-21")
    scale = {item["family"]: item for item in report["candidates"]}[mod.SCALE_IN_BRIDGE_FAMILY]

    assert scale["bridge_candidate_state"] == "bootstrap_pending"
    assert scale["allowed_runtime_apply"] is False
    assert scale["rolling_confirmation"]["avg_down"]["runtime_bridge_exclusion_reason"] == (
        "primary_ev_uplift_below_live_floor"
    )
    assert scale["rolling_confirmation"]["avg_down"]["primary_ev_uplift_floor_passed"] is False


def test_runtime_apply_bridge_rejects_malformed_discovery_live_candidate(tmp_path, monkeypatch):
    ldm_dir = tmp_path / "ldm"
    ldm_dir.mkdir()
    discovery_path = tmp_path / "discovery" / "lifecycle_bucket_discovery_2026-05-21.json"
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "discovery_report_path", lambda target_date: discovery_path)
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-21.json")
    discovery_path.parent.mkdir(parents=True, exist_ok=True)
    discovery_path.write_text(
        json.dumps(
            {
                "date": "2026-05-21",
                "summary": {"source_contract_status": "pass", "ai_two_pass_review_status": "parsed"},
                "live_auto_apply_candidates": [
                    {
                        "bucket_id": "entry:combo_entry_spot:score_66_69",
                        "classification_state": "sim_auto_approved",
                        "live_auto_apply_family": mod.ENTRY_BRIDGE_FAMILY,
                        "allowed_runtime_apply": True,
                        "broker_order_forbidden": False,
                        "source_quality_gate": "pass",
                        "ai_review_status": "parsed",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    report = mod.build_runtime_apply_bridge_report("2026-05-21")
    entry = {item["family"]: item for item in report["candidates"]}[mod.ENTRY_BRIDGE_FAMILY]

    assert entry["bridge_candidate_state"] == "runtime_blocked_contract_gap"
    assert entry["allowed_runtime_apply"] is False
