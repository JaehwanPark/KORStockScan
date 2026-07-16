import json
from datetime import date, timedelta

from src.engine import runtime_apply_bridge as mod


def _write_discovery(path, *, live=True, tier2_status="parsed", with_windows=True):
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
                "auto_promotion_contract": {
                    "tier2_status": tier2_status,
                    "tier2_policy": "fail_closed",
                },
            },
            {
                "bucket_id": "scale_in:arm:pyramid",
                "stage": "scale_in",
                "bucket_type": "arm",
                "bucket_key": "PYRAMID",
                "classification_state": "live_auto_apply_ready",
                "live_auto_apply_family": mod.SCALE_IN_BRIDGE_FAMILY,
                "allowed_runtime_apply": True,
                "broker_order_forbidden": False,
                "source_quality_gate": "pass",
                "ai_review_status": tier2_status,
                "auto_promotion_contract": {
                    "tier2_status": tier2_status,
                    "tier2_policy": "fail_closed",
                },
            },
            {
                "bucket_id": "scale_in:arm:avg_down",
                "stage": "scale_in",
                "bucket_type": "arm",
                "bucket_key": "AVG_DOWN",
                "classification_state": "live_auto_apply_ready",
                "live_auto_apply_family": mod.SCALE_IN_BRIDGE_FAMILY,
                "allowed_runtime_apply": True,
                "broker_order_forbidden": False,
                "source_quality_gate": "pass",
                "ai_review_status": tier2_status,
                "auto_promotion_contract": {
                    "tier2_status": tier2_status,
                    "tier2_policy": "fail_closed",
                },
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
                    "parent_granularity_status": "target_pass",
                },
                "live_auto_apply_candidates": live_candidates,
                "warnings": [],
            }
        ),
        encoding="utf-8",
    )
    if with_windows:
        target_date = path.stem.removeprefix("lifecycle_bucket_discovery_")
        for suffix in ("rolling5d", "rolling10d", "mtd"):
            window_path = (
                path.parent / f"lifecycle_bucket_discovery_{target_date}_{suffix}.json"
            )
            window_path.write_text(path.read_text(encoding="utf-8"), encoding="utf-8")


def _write_ldm(
    path, *, entry_ev=1.2, pyramid_ev=-3.0, avg_down_ev=-1.4, v2=False, avg_v2=None
):
    report_date = path.stem.removeprefix("lifecycle_decision_matrix_").split("_")[0]
    previous_date = (date.fromisoformat(report_date) - timedelta(days=1)).isoformat()
    is_window = path.stem.endswith(("_rolling5d", "_rolling10d", "_mtd"))
    pyramid_coverage = "v2_ready" if v2 else "legacy_only"
    avg_coverage = "v2_ready" if (v2 if avg_v2 is None else avg_v2) else "legacy_only"
    path.write_text(
        json.dumps(
            {
                "date": report_date,
                "window_policy": (
                    path.stem.split("_")[-1]
                    if path.stem.endswith(("_rolling5d", "_rolling10d", "_mtd"))
                    else "daily"
                ),
                "summary": {
                    "source_dates": (
                        [previous_date, report_date] if is_window else [report_date]
                    ),
                    "clean_baseline_excluded_source_dates": [],
                    "excluded_daily_report_dates": {},
                    "unavailable_daily_report_dates": [],
                },
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
                    "window_policy": (
                        path.stem.split("_")[-1]
                        if path.stem.endswith(("_rolling5d", "_rolling10d", "_mtd"))
                        else "daily"
                    ),
                    "scale_in_ev_label_version": (
                        "incremental_counterfactual_v2"
                        if v2
                        else "legacy_state_profit_v1"
                    ),
                    "primary_decision_metric": (
                        "incremental_notional_ev_pct"
                        if v2
                        else "stage_ev_composite_pct"
                    ),
                    "buckets": [
                        {
                            "bucket_type": "arm",
                            "bucket_key": "PYRAMID",
                            "joined_sample": 38,
                            "source_quality_adjusted_ev_pct": pyramid_ev,
                            "source_quality_gate": "pass",
                            "recommended_route": "candidate_tighten_or_exclude",
                            "scale_in_ev_coverage_state": pyramid_coverage,
                            "runtime_authority_ready": bool(v2),
                        },
                        {
                            "bucket_type": "arm",
                            "bucket_key": "AVG_DOWN",
                            "joined_sample": 2712,
                            "source_quality_adjusted_ev_pct": avg_down_ev,
                            "source_quality_gate": "pass",
                            "recommended_route": "candidate_tighten_or_exclude",
                            "scale_in_ev_coverage_state": avg_coverage,
                            "runtime_authority_ready": bool(
                                v2 if avg_v2 is None else avg_v2
                            ),
                        },
                        {
                            "bucket_type": "blocker_reason",
                            "bucket_key": "pnl_out_of_range(0.32)",
                            "joined_sample": 48,
                            "source_quality_adjusted_ev_pct": 0.32,
                            "source_quality_gate": "pass",
                            "recommended_route": "candidate_recovery_or_relax",
                        },
                    ],
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )


def test_runtime_apply_bridge_gates_scale_in_arms_independently(tmp_path, monkeypatch):
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "bridge"
    ldm_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    discovery_path = (
        tmp_path / "discovery" / "lifecycle_bucket_discovery_2026-06-12.json"
    )
    monkeypatch.setattr(
        mod, "discovery_report_path", lambda target_date: discovery_path
    )
    _write_ldm(
        ldm_dir / "lifecycle_decision_matrix_2026-06-11_mtd.json",
        pyramid_ev=-3.0,
        avg_down_ev=-1.4,
        v2=True,
        avg_v2=False,
    )
    _write_ldm(
        ldm_dir / "lifecycle_decision_matrix_2026-06-12.json",
        pyramid_ev=-3.0,
        avg_down_ev=-1.4,
        v2=True,
        avg_v2=False,
    )
    _write_discovery(discovery_path)

    report = mod.build_runtime_apply_bridge_report("2026-06-12")
    scale = {item["family"]: item for item in report["candidates"]}[
        mod.SCALE_IN_BRIDGE_FAMILY
    ]

    assert (
        scale["rolling_confirmation"]["avg_down"]["scale_in_ev_coverage_state"]
        == "legacy_only"
    )
    assert "SCALPING_ENABLE_PYRAMID" in scale["target_env_keys"]
    assert "REVERSAL_ADD_MIN_AI_SCORE" not in scale["target_env_keys"]


def test_runtime_apply_bridge_scale_in_blocked_candidate_has_source_only_contract(
    tmp_path, monkeypatch
):
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "bridge"
    ldm_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    discovery_path = (
        tmp_path / "discovery" / "lifecycle_bucket_discovery_2026-06-12.json"
    )
    monkeypatch.setattr(
        mod, "discovery_report_path", lambda target_date: discovery_path
    )
    _write_discovery(discovery_path, live=False)
    ldm_path = ldm_dir / "lifecycle_decision_matrix_2026-06-12.json"
    ldm_path.write_text(
        json.dumps(
            {
                "date": "2026-06-12",
                "scale_in_bucket_attribution": {
                    "scale_in_ev_label_version": "incremental_counterfactual_v2",
                    "buckets": [
                        {
                            "bucket_type": "arm",
                            "bucket_key": "PYRAMID",
                            "joined_sample": 11,
                            "source_quality_gate": "hold_sample",
                            "recommended_route": "hold_sample",
                            "scale_in_ev_coverage_state": "legacy_only",
                            "runtime_authority_ready": False,
                            "runtime_authority_block_reason": "paired_add_lifecycle_replay_or_final_label_missing",
                        },
                        {
                            "bucket_type": "arm",
                            "bucket_key": "AVG_DOWN",
                            "joined_sample": 22,
                            "source_quality_gate": "hold_sample",
                            "recommended_route": "hold_sample",
                            "scale_in_ev_coverage_state": "legacy_only",
                            "runtime_authority_ready": False,
                            "runtime_authority_block_reason": "paired_add_lifecycle_replay_or_final_label_missing",
                        },
                    ],
                },
            }
        ),
        encoding="utf-8",
    )

    report = mod.build_runtime_apply_bridge_report("2026-06-12")
    scale = {item["family"]: item for item in report["candidates"]}[
        mod.SCALE_IN_BRIDGE_FAMILY
    ]

    assert scale["bridge_candidate_state"] == "blocked_incremental_ev_runtime_authority"
    assert scale["allowed_runtime_apply"] is False
    assert scale["runtime_effect"] is False
    assert scale["target_env_keys"] == []
    assert scale["explicit_runtime_exclusion"] is True
    assert (
        scale["runtime_exclusion_reason"]
        == "paired_add_lifecycle_replay_or_final_label_missing"
    )
    assert scale["source_link"]["source_section"] == "scale_in_bucket_attribution"
    assert scale["source_link"]["source_bucket_keys"] == ["PYRAMID", "AVG_DOWN"]
    assert "target_env_keys_mapped" in scale["reopen_conditions"]


def test_scale_in_rolling_confirmation_excludes_treatment_only_history():
    current = {
        "bucket_type": "arm",
        "bucket_key": "PYRAMID",
        "source_quality_gate": "pass",
        "recommended_route": "candidate_recovery_or_relax",
        "source_quality_adjusted_ev_pct": 1.2,
        "scale_in_ev_coverage_state": "v2_ready",
        "runtime_authority_ready": True,
    }
    treatment_only_history = {
        "scale_in_bucket_attribution": {
            "buckets": [
                {
                    **current,
                    "runtime_authority_ready": False,
                    "source_quality_adjusted_ev_pct": -2.0,
                    "recommended_route": "candidate_tighten_or_exclude",
                }
            ]
        }
    }

    state, meta = mod._state_for_bucket(
        current,
        [treatment_only_history],
        section="scale_in_bucket_attribution",
        bucket_type="arm",
        bucket_key="PYRAMID",
        positive_edge=True,
    )

    assert state == "hold_rolling_confirmation_missing"
    assert meta["confirmation_count"] == 0
    assert meta["conflict_count"] == 0
    assert (
        meta["runtime_bridge_exclusion_reason"]
        == "rolling_authority_confirmation_missing"
    )


def test_scale_confirmation_reports_require_explicit_clean_window(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", tmp_path)
    _write_ldm(tmp_path / "lifecycle_decision_matrix_2026-06-11_mtd.json", v2=True)
    _write_ldm(tmp_path / "lifecycle_decision_matrix_2026-06-12_mtd.json", v2=True)
    _write_ldm(tmp_path / "lifecycle_decision_matrix_2026-06-12.json", v2=True)
    malformed = tmp_path / "lifecycle_decision_matrix_2026-06-11_rolling5d.json"
    _write_ldm(malformed, v2=True)
    payload = json.loads(malformed.read_text(encoding="utf-8"))
    payload["window_policy"] = "daily"
    malformed.write_text(json.dumps(payload), encoding="utf-8")

    reports = mod._scale_confirmation_reports("2026-06-12")

    assert len(reports) == 1
    assert reports[0]["window_policy"] == "mtd"
    assert reports[0]["date"] == "2026-06-11"


def test_scale_confirmation_reports_require_explicit_clean_provenance(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", tmp_path)
    path = tmp_path / "lifecycle_decision_matrix_2026-06-11_mtd.json"
    _write_ldm(path, v2=True)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["summary"].pop("clean_baseline_excluded_source_dates")
    path.write_text(json.dumps(payload), encoding="utf-8")

    assert mod._scale_confirmation_reports("2026-06-12") == []


def test_scale_confirmation_reports_reject_weekday_coverage_gap(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", tmp_path)
    path = tmp_path / "lifecycle_decision_matrix_2026-06-11_mtd.json"
    _write_ldm(path, v2=True)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["summary"]["unavailable_daily_report_dates"] = ["2026-06-09"]
    path.write_text(json.dumps(payload), encoding="utf-8")

    assert mod._scale_confirmation_reports("2026-06-12") == []


def test_scale_confirmation_reports_accept_weekend_coverage_gap(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", tmp_path)
    path = tmp_path / "lifecycle_decision_matrix_2026-06-08_mtd.json"
    _write_ldm(path, v2=True)
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["summary"]["source_dates"] = ["2026-06-05", "2026-06-08"]
    payload["summary"]["unavailable_daily_report_dates"] = ["2026-06-06", "2026-06-07"]
    path.write_text(json.dumps(payload), encoding="utf-8")

    reports = mod._scale_confirmation_reports("2026-06-09")

    assert len(reports) == 1
    assert reports[0]["date"] == "2026-06-08"


def test_scale_confirmation_reports_do_not_fallback_past_invalid_latest(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", tmp_path)
    _write_ldm(tmp_path / "lifecycle_decision_matrix_2026-06-10_mtd.json", v2=True)
    latest = tmp_path / "lifecycle_decision_matrix_2026-06-11_mtd.json"
    _write_ldm(latest, v2=True)
    payload = json.loads(latest.read_text(encoding="utf-8"))
    payload["summary"]["excluded_daily_report_dates"] = {
        "2026-06-11": "daily_lifecycle_source_quality_preflight_blocked"
    }
    latest.write_text(json.dumps(payload), encoding="utf-8")

    assert mod._scale_confirmation_reports("2026-06-12") == []


def test_history_reports_exclude_pre_clean_baseline(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", tmp_path)
    _write_ldm(tmp_path / "lifecycle_decision_matrix_2026-06-03.json")
    _write_ldm(tmp_path / "lifecycle_decision_matrix_2026-06-05.json")

    reports = mod._history_reports("2026-06-12")

    assert [item["date"] for item in reports] == ["2026-06-05"]


def test_scale_in_arm_conflict_does_not_block_other_ready_arm():
    pyramid = {
        "bucket_type": "arm",
        "bucket_key": "PYRAMID",
        "source_quality_gate": "pass",
        "recommended_route": "candidate_recovery_or_relax",
        "source_quality_adjusted_ev_pct": 1.5,
        "scale_in_ev_coverage_state": "v2_ready",
        "runtime_authority_ready": True,
    }
    avg_down = {
        "bucket_type": "arm",
        "bucket_key": "AVG_DOWN",
        "source_quality_gate": "pass",
        "recommended_route": "candidate_tighten_or_exclude",
        "source_quality_adjusted_ev_pct": -1.5,
        "scale_in_ev_coverage_state": "v2_ready",
        "runtime_authority_ready": True,
    }
    current = {
        "scale_in_bucket_attribution": {
            "scale_in_ev_label_version": "incremental_counterfactual_v2",
            "buckets": [pyramid, avg_down],
        }
    }
    history = [
        {
            "scale_in_bucket_attribution": {
                "buckets": [
                    pyramid,
                    {
                        **avg_down,
                        "recommended_route": "candidate_recovery_or_relax",
                        "source_quality_adjusted_ev_pct": 1.5,
                    },
                ]
            }
        }
    ]
    discovery = {
        "live_auto_apply_candidates": [
            {
                "stage": "scale_in",
                "bucket_type": "arm",
                "bucket_key": "PYRAMID",
                "live_auto_apply_family": mod.SCALE_IN_BRIDGE_FAMILY,
                "classification_state": "live_auto_apply_ready",
                "allowed_runtime_apply": True,
                "source_quality_gate": "pass",
                "auto_promotion_contract": {"tier2_status": "parsed"},
            }
        ]
    }

    candidate = mod._scale_candidate(
        current,
        history,
        "2026-06-12",
        discovery_live_families={mod.SCALE_IN_BRIDGE_FAMILY},
        discovery_live_by_family={},
        discovery=discovery,
        discovery_available=True,
    )

    assert candidate["bridge_candidate_state"] == "live_auto_apply_ready"
    assert candidate["rolling_confirmation"]["pyramid_state"] == "live_auto_apply_ready"
    assert (
        candidate["rolling_confirmation"]["avg_down_state"]
        == "blocked_rolling_conflict"
    )
    assert candidate["target_env_keys"] == ["SCALPING_ENABLE_PYRAMID"]


def _copy_discovery_windows(path):
    target_date = path.stem.removeprefix("lifecycle_bucket_discovery_")
    for suffix in ("rolling5d", "rolling10d", "mtd"):
        (
            path.parent / f"lifecycle_bucket_discovery_{target_date}_{suffix}.json"
        ).write_text(
            path.read_text(encoding="utf-8"),
            encoding="utf-8",
        )


def test_runtime_apply_bridge_blocks_daily_only_bucket_without_cumulative_confirmation(
    tmp_path, monkeypatch
):
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "bridge"
    ldm_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    discovery_path = (
        tmp_path / "discovery" / "lifecycle_bucket_discovery_2026-05-21.json"
    )
    monkeypatch.setattr(
        mod, "discovery_report_path", lambda target_date: discovery_path
    )
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-21.json")
    _write_discovery(discovery_path, with_windows=False)

    report = mod.write_runtime_apply_bridge_report("2026-05-21")

    states = {
        item["family"]: item["bridge_candidate_state"] for item in report["candidates"]
    }
    assert states[mod.ENTRY_BRIDGE_FAMILY] == "entry_only_bridge_metadata"
    assert (
        states[mod.SCALE_IN_BRIDGE_FAMILY]
        == "blocked_legacy_v1_label_missing_incremental_ev"
    )
    assert report["summary"]["live_auto_apply_ready_count"] == 0
    assert "promotion_lifecycle_bucket_discovery_missing" in report["warnings"]
    assert report["summary"]["lifecycle_bucket_discovery_live_followup_count"] == 0
    entry = {item["family"]: item for item in report["candidates"]}[
        mod.ENTRY_BRIDGE_FAMILY
    ]
    assert entry["allowed_runtime_apply"] is False
    assert entry["target_env_keys"] == []
    assert entry["evidence_grade"] == "grade_2_counterfactual"
    assert entry["metadata_only"] is True
    assert (
        entry["bridge_exclusion_reason"]
        == "entry_only_bridge_metadata_not_live_candidate"
    )
    assert entry["legacy_family_archived"] is False
    assert report["summary"]["approval_required_count"] == 0
    assert report["summary"]["runtime_mutation_performed"] is False
    assert (report_dir / "runtime_apply_bridge_2026-05-21.json").exists()
    assert (report_dir / "runtime_apply_bridge_2026-05-21.md").exists()


def test_runtime_apply_bridge_ignores_lifecycle_flow_sim_probe_candidate(
    tmp_path, monkeypatch
):
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "bridge"
    ldm_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    discovery_path = (
        tmp_path / "discovery" / "lifecycle_bucket_discovery_2026-05-21.json"
    )
    monkeypatch.setattr(
        mod, "discovery_report_path", lambda target_date: discovery_path
    )
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-21.json")
    discovery_path.parent.mkdir(parents=True, exist_ok=True)
    discovery_path.write_text(
        json.dumps(
            {
                "date": "2026-05-21",
                "summary": {
                    "live_auto_apply_ready_count": 0,
                    "lifecycle_flow_sim_probe_candidate_count": 1,
                    "source_contract_status": "pass",
                    "ai_two_pass_review_status": "parsed",
                },
                "live_auto_apply_candidates": [],
                "sim_auto_approved_candidates": [
                    {
                        "bucket_id": "lifecycle_flow:combo_lifecycle_flow:complete_probe",
                        "stage": "lifecycle_flow",
                        "classification_state": "lifecycle_flow_sim_probe_candidate",
                        "source_bucket_kind": "lifecycle_flow_sim_probe_policy",
                        "live_auto_apply_family": None,
                        "allowed_runtime_apply": False,
                        "broker_order_forbidden": True,
                        "runtime_effect": False,
                        "source_quality_gate": "pass",
                    }
                ],
                "warnings": [],
            }
        ),
        encoding="utf-8",
    )

    report = mod.write_runtime_apply_bridge_report("2026-05-21")

    assert all(
        item["family"] != mod.GREENFIELD_REAL_ENV_FAMILY
        for item in report["candidates"]
    )
    assert report["summary"]["live_auto_apply_ready_count"] == 0
    assert report["summary"]["greenfield_real_env_ready_count"] == 0
    assert (
        report["summary"]["greenfield_policy_emit_state"]
        == "not_emitted_no_complete_lifecycle_flow"
    )
    assert (
        report["summary"]["greenfield_policy_emit_blocker"]
        == "no_complete_lifecycle_flow"
    )
    assert (
        report["summary"]["greenfield_policy_emit_blocker_detail"]
        == "no lifecycle flow candidate is available for greenfield policy emission"
    )
    assert report["summary"]["greenfield_live_auto_ready_lifecycle_flow_count"] == 0


def test_runtime_apply_bridge_keeps_entry_as_metadata_and_scale_candidates_live_auto(
    tmp_path, monkeypatch
):
    ldm_dir = tmp_path / "ldm"
    ldm_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    discovery_path = (
        tmp_path / "discovery" / "lifecycle_bucket_discovery_2026-05-21.json"
    )
    monkeypatch.setattr(
        mod, "discovery_report_path", lambda target_date: discovery_path
    )
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-20.json")
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-21.json")
    _write_discovery(discovery_path)

    report = mod.build_runtime_apply_bridge_report("2026-05-21")
    by_family = {item["family"]: item for item in report["candidates"]}
    entry = by_family[mod.ENTRY_BRIDGE_FAMILY]
    scale = by_family[mod.SCALE_IN_BRIDGE_FAMILY]

    assert entry["bridge_candidate_state"] == "entry_only_bridge_metadata"
    assert entry["approval_required"] is False
    assert entry["allowed_runtime_apply"] is False
    assert entry["target_env_keys"] == []
    assert entry["metadata_only"] is True
    assert entry["transition_target"] == "entry_dimension_provenance_only"
    assert (
        scale["bridge_candidate_state"]
        == "blocked_legacy_v1_label_missing_incremental_ev"
    )
    assert scale["approval_required"] is False
    assert scale["allowed_runtime_apply"] is False
    assert (
        scale["recommended_values"]["legacy_state_label_not_runtime_authority"] is True
    )
    assert scale["recommended_values"]["source_only_keep_collecting"] is True
    assert scale["observe_only_reference_buckets"] == []


def test_runtime_apply_bridge_blocks_live_when_discovery_does_not_confirm(
    tmp_path, monkeypatch
):
    ldm_dir = tmp_path / "ldm"
    ldm_dir.mkdir()
    discovery_path = (
        tmp_path / "discovery" / "lifecycle_bucket_discovery_2026-05-21.json"
    )
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(
        mod, "discovery_report_path", lambda target_date: discovery_path
    )
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-21.json")
    _write_discovery(discovery_path, live=False)

    report = mod.build_runtime_apply_bridge_report("2026-05-21")
    states = {
        item["family"]: item["bridge_candidate_state"] for item in report["candidates"]
    }
    entry = {item["family"]: item for item in report["candidates"]}[
        mod.ENTRY_BRIDGE_FAMILY
    ]

    assert states[mod.ENTRY_BRIDGE_FAMILY] == "entry_only_bridge_metadata"
    assert (
        states[mod.SCALE_IN_BRIDGE_FAMILY]
        == "blocked_legacy_v1_label_missing_incremental_ev"
    )
    assert report["summary"]["live_auto_apply_ready_count"] == 0


def test_runtime_apply_bridge_blocks_live_when_discovery_tier2_not_parsed(
    tmp_path, monkeypatch
):
    ldm_dir = tmp_path / "ldm"
    ldm_dir.mkdir()
    discovery_path = (
        tmp_path / "discovery" / "lifecycle_bucket_discovery_2026-05-21.json"
    )
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(
        mod, "discovery_report_path", lambda target_date: discovery_path
    )
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-21.json")
    _write_discovery(discovery_path, live=True, tier2_status="parse_rejected")

    report = mod.build_runtime_apply_bridge_report("2026-05-21")
    states = {
        item["family"]: item["bridge_candidate_state"] for item in report["candidates"]
    }

    assert states[mod.ENTRY_BRIDGE_FAMILY] == "entry_only_bridge_metadata"
    assert (
        states[mod.SCALE_IN_BRIDGE_FAMILY]
        == "blocked_legacy_v1_label_missing_incremental_ev"
    )


def test_runtime_apply_bridge_keeps_wait6579_discovery_candidate_as_entry_metadata(
    tmp_path, monkeypatch
):
    ldm_dir = tmp_path / "ldm"
    ldm_dir.mkdir()
    discovery_path = (
        tmp_path / "discovery" / "lifecycle_bucket_discovery_2026-05-21.json"
    )
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(
        mod, "discovery_report_path", lambda target_date: discovery_path
    )
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-21.json")
    _write_discovery(discovery_path, live=True, tier2_status="parsed")

    report = mod.build_runtime_apply_bridge_report("2026-05-21")
    entry = {item["family"]: item for item in report["candidates"]}[
        mod.ENTRY_BRIDGE_FAMILY
    ]

    assert entry["bridge_candidate_state"] == "entry_only_bridge_metadata"
    assert entry["live_auto_apply"] is False
    assert entry["allowed_runtime_apply"] is False
    assert entry["target_env_keys"] == []
    assert entry["runtime_effect_after_approval"] == "none"
    assert entry["metadata_only"] is True


def test_runtime_apply_bridge_writes_greenfield_real_env_policy(tmp_path, monkeypatch):
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "bridge"
    policy_dir = tmp_path / "policies"
    ldm_dir.mkdir()
    discovery_path = (
        tmp_path / "discovery" / "lifecycle_bucket_discovery_2026-05-21.json"
    )
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "GREENFIELD_POLICY_DIR", policy_dir)
    monkeypatch.setattr(
        mod, "discovery_report_path", lambda target_date: discovery_path
    )
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-21.json")
    discovery_path.parent.mkdir(parents=True, exist_ok=True)
    discovery_path.write_text(
        json.dumps(
            {
                "date": "2026-05-21",
                "summary": {
                    "live_auto_apply_ready_count": 2,
                    "source_contract_status": "pass",
                    "ai_two_pass_review_status": "parsed",
                    "parent_granularity_status": "target_pass",
                },
                "live_auto_apply_candidates": [
                    {
                        "bucket_id": "entry:combo_entry_spot:score_66_69",
                        "stage": "entry",
                        "recommended_action": "relax_or_recover",
                        "classification_state": "live_auto_apply_ready",
                        "live_auto_apply_family": mod.ENTRY_BRIDGE_FAMILY,
                        "allowed_runtime_apply": True,
                        "broker_order_forbidden": False,
                        "source_quality_gate": "pass",
                        "ai_review_status": "parsed",
                    },
                    {
                        "bucket_id": "lifecycle_flow:combo_lifecycle_flow:complete_good",
                        "stage": "lifecycle_flow",
                        "bucket_type": "combo_lifecycle_flow",
                        "recommended_action": "relax_or_recover",
                        "classification_state": "live_auto_apply_ready",
                        "live_auto_apply_family": mod.GREENFIELD_REAL_ENV_FAMILY,
                        "allowed_runtime_apply": True,
                        "broker_order_forbidden": False,
                        "source_quality_gate": "pass",
                        "ai_review_status": "parsed",
                        "policy_bucket_id": "lifecycle_flow:combo_lifecycle_flow:entry=score_mid_recovery|submit=submit_observed|holding=holding_observed|scale_in=none|exit=exit_observed",
                        "canonical_parent_bucket": "lifecycle_flow:combo_lifecycle_flow:entry=score_mid_recovery|submit=submit_observed|holding=holding_observed|scale_in=none|exit=exit_observed",
                        "parent_live_floor_passed": True,
                        "parent_joined_sample": 22,
                        "parent_primary_sample_book": "real",
                        "parent_real_joined_sample": 22,
                        "selected_parent_level": "L2_default",
                        "parent_granularity_status": "target_pass",
                        "absorbed_child_bucket_ids": [
                            "lifecycle_flow:combo_lifecycle_flow:complete_good",
                            "lifecycle_flow:combo_lifecycle_flow:complete_good_variant",
                        ],
                        "dimension_filters": {
                            "entry_parent": "score_mid_recovery",
                            "submit_detail": "submit:allow_submit:thin_ok",
                        },
                        "lifecycle_flow_bucket_id": "lifecycle_flow:combo_lifecycle_flow:complete_good",
                        "attribution_key": "sim_record_id:SIM-1",
                        "entry_bucket_id": "entry:combo_entry_spot:score_66_69",
                        "submit_bucket_id": "submit:allow_submit:thin_ok",
                        "holding_bucket_id": "holding:flow:baseline_hold",
                        "exit_bucket_id": "exit:rule:baseline_exit",
                        "child_bucket_ids": {
                            "entry": "entry:combo_entry_spot:score_66_69",
                            "submit": "submit:allow_submit:thin_ok",
                            "holding": "holding:flow:baseline_hold",
                            "scale_in": [],
                            "exit": "exit:rule:baseline_exit",
                        },
                        "rollback_guard": "hard_safety_priority_plus_source_quality_and_post_apply_attribution",
                    },
                ],
                "warnings": [],
            }
        ),
        encoding="utf-8",
    )
    _copy_discovery_windows(discovery_path)

    report = mod.write_runtime_apply_bridge_report("2026-05-21")

    greenfield = {item["family"]: item for item in report["candidates"]}[
        mod.GREENFIELD_REAL_ENV_FAMILY
    ]
    policy_path = policy_dir / "greenfield_real_env_policy_2026-05-21.json"
    policy = json.loads(policy_path.read_text(encoding="utf-8"))
    assert greenfield["bridge_candidate_state"] == "live_auto_apply_ready"
    assert greenfield["recommended_values"]["enabled"] is True
    assert greenfield["recommended_values"]["policy_file"] == str(policy_path)
    assert greenfield["target_env_keys"] == [
        "GREENFIELD_REAL_ENV_AUTHORITY_ENABLED",
        "GREENFIELD_REAL_ENV_AUTHORITY_SCOPE",
        "GREENFIELD_REAL_ENV_AUTHORITY_POLICY_FILE",
        "GREENFIELD_REAL_ENV_AUTHORITY_POLICY_VERSION",
        "GREENFIELD_REAL_ENV_TELEGRAM_ENABLED",
    ]
    assert report["summary"]["live_auto_apply_ready_count"] == 1
    assert report["summary"]["greenfield_real_env_ready_count"] == 1
    assert report["summary"]["stage_local_live_auto_apply_ready_count"] == 0
    assert policy["scope"] == "full_lifecycle"
    assert policy["schema_version"] == "greenfield_lifecycle_bundle_policy_v1"
    assert policy["bundle_id"] == "lifecycle_flow:combo_lifecycle_flow:complete_good"
    assert policy["policy_bucket_id"].startswith(
        "lifecycle_flow:combo_lifecycle_flow:entry=score_mid_recovery"
    )
    assert policy["selected_parent_level"] == "L2_default"
    assert policy["parent_granularity_status"] == "target_pass"
    assert policy["absorbed_child_bucket_ids"] == [
        "lifecycle_flow:combo_lifecycle_flow:complete_good",
        "lifecycle_flow:combo_lifecycle_flow:complete_good_variant",
    ]
    assert policy["dimension_filters"]["entry_parent"] == "score_mid_recovery"
    assert policy["attribution_key"] == "sim_record_id:SIM-1"
    assert [row["stage"] for row in policy["allowlist"]] == [
        "entry",
        "submit",
        "holding",
        "exit",
    ]
    assert policy["stages"]["entry"][0]["action"] == "BUY"
    assert policy["stages"]["submit"][0]["action"] == "ALLOW_SUBMIT"
    assert (
        policy["stages"]["entry"][0]["policy_bucket_id"] == policy["policy_bucket_id"]
    )
    assert (
        policy["stages"]["entry"][0]["absorbed_child_bucket_ids"]
        == policy["absorbed_child_bucket_ids"]
    )
    assert (
        policy["stages"]["entry"][0]["dimension_filters"] == policy["dimension_filters"]
    )


def test_runtime_apply_bridge_reports_greenfield_policy_contract_gap_blocker(
    tmp_path, monkeypatch
):
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "bridge"
    policy_dir = tmp_path / "policies"
    ldm_dir.mkdir()
    discovery_path = (
        tmp_path / "discovery" / "lifecycle_bucket_discovery_2026-05-21.json"
    )
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "GREENFIELD_POLICY_DIR", policy_dir)
    monkeypatch.setattr(
        mod, "discovery_report_path", lambda target_date: discovery_path
    )
    monkeypatch.setattr(
        mod,
        "validate_greenfield_policy_payload",
        lambda policy, *, expected_version=None: "incomplete_lifecycle_bundle",
    )
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-21.json")
    discovery_path.parent.mkdir(parents=True, exist_ok=True)
    discovery_path.write_text(
        json.dumps(
            {
                "date": "2026-05-21",
                "summary": {
                    "live_auto_apply_ready_count": 1,
                    "source_contract_status": "pass",
                    "ai_two_pass_review_status": "parsed",
                    "parent_granularity_status": "target_pass",
                },
                "live_auto_apply_candidates": [
                    {
                        "bucket_id": "lifecycle_flow:combo_lifecycle_flow:contract_gap",
                        "stage": "lifecycle_flow",
                        "bucket_type": "combo_lifecycle_flow",
                        "recommended_action": "relax_or_recover",
                        "classification_state": "live_auto_apply_ready",
                        "live_auto_apply_family": mod.GREENFIELD_REAL_ENV_FAMILY,
                        "allowed_runtime_apply": True,
                        "broker_order_forbidden": False,
                        "source_quality_gate": "pass",
                        "ai_review_status": "parsed",
                        "policy_bucket_id": "lifecycle_flow:combo_lifecycle_flow:entry=ok|submit=ok|holding=ok|exit=ok",
                        "canonical_parent_bucket": "lifecycle_flow:combo_lifecycle_flow:entry=ok|submit=ok|holding=ok|exit=ok",
                        "parent_live_floor_passed": True,
                        "parent_joined_sample": 22,
                        "parent_primary_sample_book": "real",
                        "parent_real_joined_sample": 22,
                        "selected_parent_level": "L2_default",
                        "parent_granularity_status": "target_pass",
                        "entry_bucket_id": "entry:combo_entry_spot:score_66_69",
                        "submit_bucket_id": "submit:allow_submit:thin_ok",
                        "holding_bucket_id": "holding:flow:baseline_hold",
                        "exit_bucket_id": "exit:rule:baseline_exit",
                        "rollback_guard": "hard_safety_priority_plus_source_quality_and_post_apply_attribution",
                    },
                ],
                "warnings": [],
            }
        ),
        encoding="utf-8",
    )
    _copy_discovery_windows(discovery_path)

    report = mod.write_runtime_apply_bridge_report("2026-05-21")
    greenfield = {item["family"]: item for item in report["candidates"]}[
        mod.GREENFIELD_REAL_ENV_FAMILY
    ]

    assert greenfield["bridge_candidate_state"] == "runtime_blocked_contract_gap"
    assert (
        greenfield["greenfield_policy_contract_state"] == "incomplete_lifecycle_bundle"
    )
    assert report["summary"]["greenfield_real_env_ready_count"] == 0
    assert (
        report["summary"]["greenfield_policy_emit_state"]
        == "not_emitted_greenfield_policy_contract_gap"
    )
    assert (
        report["summary"]["greenfield_policy_emit_blocker"]
        == "greenfield_policy_contract_gap"
    )
    assert (
        report["summary"]["greenfield_policy_emit_blocker_detail"]
        == "incomplete_lifecycle_bundle"
    )
    assert report["summary"]["greenfield_live_auto_ready_lifecycle_flow_count"] == 1
    assert not (policy_dir / "greenfield_real_env_policy_2026-05-21.json").exists()


def test_runtime_apply_bridge_blocks_entry_only_greenfield_bundle(
    tmp_path, monkeypatch
):
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "bridge"
    policy_dir = tmp_path / "policies"
    ldm_dir.mkdir()
    discovery_path = (
        tmp_path / "discovery" / "lifecycle_bucket_discovery_2026-05-21.json"
    )
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "GREENFIELD_POLICY_DIR", policy_dir)
    monkeypatch.setattr(
        mod, "discovery_report_path", lambda target_date: discovery_path
    )
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-21.json")
    discovery_path.parent.mkdir(parents=True, exist_ok=True)
    discovery_path.write_text(
        json.dumps(
            {
                "date": "2026-05-21",
                "summary": {
                    "live_auto_apply_ready_count": 1,
                    "source_contract_status": "pass",
                    "ai_two_pass_review_status": "parsed",
                },
                "live_auto_apply_candidates": [
                    {
                        "bucket_id": "entry:combo_entry_spot:score_66_69",
                        "stage": "entry",
                        "recommended_action": "relax_or_recover",
                        "classification_state": "live_auto_apply_ready",
                        "live_auto_apply_family": mod.ENTRY_BRIDGE_FAMILY,
                        "allowed_runtime_apply": True,
                        "broker_order_forbidden": False,
                        "source_quality_gate": "pass",
                        "ai_review_status": "parsed",
                    }
                ],
                "warnings": [],
            }
        ),
        encoding="utf-8",
    )

    report = mod.write_runtime_apply_bridge_report("2026-05-21")

    assert mod.GREENFIELD_REAL_ENV_FAMILY not in {
        item["family"] for item in report["candidates"]
    }
    assert not (policy_dir / "greenfield_real_env_policy_2026-05-21.json").exists()
    assert report["summary"]["greenfield_real_env_ready_count"] == 0


def test_runtime_apply_bridge_blocks_child_only_greenfield_without_parent_policy(
    tmp_path, monkeypatch
):
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "bridge"
    policy_dir = tmp_path / "policies"
    ldm_dir.mkdir()
    discovery_path = (
        tmp_path / "discovery" / "lifecycle_bucket_discovery_2026-05-21.json"
    )
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "GREENFIELD_POLICY_DIR", policy_dir)
    monkeypatch.setattr(
        mod, "discovery_report_path", lambda target_date: discovery_path
    )
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-21.json")
    discovery_path.parent.mkdir(parents=True, exist_ok=True)
    discovery_path.write_text(
        json.dumps(
            {
                "date": "2026-05-21",
                "summary": {
                    "live_auto_apply_ready_count": 1,
                    "source_contract_status": "pass",
                    "ai_two_pass_review_status": "parsed",
                },
                "live_auto_apply_candidates": [
                    {
                        "bucket_id": "lifecycle_flow:combo_lifecycle_flow:single_child",
                        "stage": "lifecycle_flow",
                        "bucket_type": "combo_lifecycle_flow",
                        "classification_state": "live_auto_apply_ready",
                        "live_auto_apply_family": mod.GREENFIELD_REAL_ENV_FAMILY,
                        "allowed_runtime_apply": True,
                        "broker_order_forbidden": False,
                        "source_quality_gate": "pass",
                        "ai_review_status": "parsed",
                        "joined_sample": 1,
                        "parent_live_floor_passed": False,
                        "parent_joined_sample": 1,
                        "entry_bucket_id": "entry:combo_entry_spot:score_66_69",
                        "submit_bucket_id": "submit:allow_submit:thin_ok",
                        "holding_bucket_id": "holding:flow:baseline_hold",
                        "exit_bucket_id": "exit:rule:baseline_exit",
                    },
                ],
                "warnings": [],
            }
        ),
        encoding="utf-8",
    )

    report = mod.write_runtime_apply_bridge_report("2026-05-21")

    assert mod.GREENFIELD_REAL_ENV_FAMILY not in {
        item["family"] for item in report["candidates"]
    }
    assert not (policy_dir / "greenfield_real_env_policy_2026-05-21.json").exists()
    assert report["summary"]["greenfield_real_env_ready_count"] == 0


def test_runtime_apply_bridge_blocks_greenfield_when_parent_granularity_not_target(
    tmp_path, monkeypatch
):
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "bridge"
    policy_dir = tmp_path / "policies"
    ldm_dir.mkdir()
    discovery_path = (
        tmp_path / "discovery" / "lifecycle_bucket_discovery_2026-05-21.json"
    )
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "GREENFIELD_POLICY_DIR", policy_dir)
    monkeypatch.setattr(
        mod, "discovery_report_path", lambda target_date: discovery_path
    )
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-21.json")
    discovery_path.parent.mkdir(parents=True, exist_ok=True)
    discovery_path.write_text(
        json.dumps(
            {
                "date": "2026-05-21",
                "summary": {
                    "live_auto_apply_ready_count": 1,
                    "source_contract_status": "pass",
                    "ai_two_pass_review_status": "parsed",
                    "parent_granularity_status": "too_broad",
                },
                "live_auto_apply_candidates": [
                    {
                        "bucket_id": "lifecycle_flow:combo_lifecycle_flow:single_parent",
                        "stage": "lifecycle_flow",
                        "bucket_type": "combo_lifecycle_flow",
                        "classification_state": "live_auto_apply_ready",
                        "live_auto_apply_family": mod.GREENFIELD_REAL_ENV_FAMILY,
                        "allowed_runtime_apply": True,
                        "broker_order_forbidden": False,
                        "source_quality_gate": "pass",
                        "ai_review_status": "parsed",
                        "policy_bucket_id": "lifecycle_flow:combo_lifecycle_flow:too_broad",
                        "canonical_parent_bucket": "lifecycle_flow:combo_lifecycle_flow:too_broad",
                        "parent_live_floor_passed": True,
                        "parent_joined_sample": 22,
                        "selected_parent_level": "L1_broad",
                        "parent_granularity_status": "too_broad",
                        "entry_bucket_id": "entry:combo_entry_spot:score_66_69",
                        "submit_bucket_id": "submit:allow_submit:thin_ok",
                        "holding_bucket_id": "holding:flow:baseline_hold",
                        "exit_bucket_id": "exit:rule:baseline_exit",
                    },
                ],
                "warnings": [],
            }
        ),
        encoding="utf-8",
    )

    report = mod.write_runtime_apply_bridge_report("2026-05-21")

    assert mod.GREENFIELD_REAL_ENV_FAMILY not in {
        item["family"] for item in report["candidates"]
    }
    assert not (policy_dir / "greenfield_real_env_policy_2026-05-21.json").exists()
    assert report["summary"]["greenfield_real_env_ready_count"] == 0


def test_runtime_apply_bridge_scale_ev_floor_miss_is_explicit_hold_not_contract_gap(
    tmp_path, monkeypatch
):
    ldm_dir = tmp_path / "ldm"
    ldm_dir.mkdir()
    discovery_path = (
        tmp_path / "discovery" / "lifecycle_bucket_discovery_2026-05-21.json"
    )
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(
        mod, "discovery_report_path", lambda target_date: discovery_path
    )
    _write_ldm(
        ldm_dir / "lifecycle_decision_matrix_2026-05-21.json",
        pyramid_ev=0.4,
        avg_down_ev=-0.4,
    )
    _write_discovery(discovery_path, live=False)

    report = mod.build_runtime_apply_bridge_report("2026-05-21")
    scale = {item["family"]: item for item in report["candidates"]}[
        mod.SCALE_IN_BRIDGE_FAMILY
    ]

    assert (
        scale["bridge_candidate_state"]
        == "blocked_legacy_v1_label_missing_incremental_ev"
    )
    assert scale["allowed_runtime_apply"] is False
    assert (
        scale["recommended_values"]["legacy_state_label_not_runtime_authority"] is True
    )


def test_runtime_apply_bridge_rejects_malformed_discovery_live_candidate(
    tmp_path, monkeypatch
):
    ldm_dir = tmp_path / "ldm"
    ldm_dir.mkdir()
    discovery_path = (
        tmp_path / "discovery" / "lifecycle_bucket_discovery_2026-05-21.json"
    )
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(
        mod, "discovery_report_path", lambda target_date: discovery_path
    )
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-21.json")
    discovery_path.parent.mkdir(parents=True, exist_ok=True)
    discovery_path.write_text(
        json.dumps(
            {
                "date": "2026-05-21",
                "summary": {
                    "source_contract_status": "pass",
                    "ai_two_pass_review_status": "parsed",
                },
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
    entry = {item["family"]: item for item in report["candidates"]}[
        mod.ENTRY_BRIDGE_FAMILY
    ]

    assert entry["bridge_candidate_state"] == "entry_only_bridge_metadata"
    assert entry["allowed_runtime_apply"] is False
