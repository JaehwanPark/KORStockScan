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
                "live_auto_apply_family": "entry_bucket_runtime_policy_v1",
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
                            "bucket_key": (
                                "score=score_66_69|source=wait6579_ev_cohort|"
                                "stale=fresh_or_unflagged|liquidity=liquidity_unknown|"
                                "overbought=overbought_unknown|time=time_unknown"
                            ),
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
    assert report["status"] == "retired"
    assert report["runtime_effect"] is False


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
    assert report["status"] == "retired"
    assert report["runtime_effect"] is False


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
    assert report["status"] == "retired"
    assert report["runtime_effect"] is False


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
    assert report["status"] == "retired"
    assert report["runtime_effect"] is False


def test_runtime_apply_bridge_emits_only_scale_candidate_for_stage_local_policy(
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
    assert report["status"] == "retired"
    assert report["runtime_effect"] is False


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
    assert report["status"] == "retired"
    assert report["runtime_effect"] is False


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
    assert report["status"] == "retired"
    assert report["runtime_effect"] is False


def test_runtime_apply_bridge_does_not_emit_wait6579_stage_local_candidate(
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
    assert report["status"] == "retired"
    assert report["runtime_effect"] is False


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
                        "live_auto_apply_family": "entry_bucket_runtime_policy_v1",
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
    assert report["status"] == "retired"
    assert report["runtime_effect"] is False


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
    assert report["status"] == "retired"
    assert report["runtime_effect"] is False


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
                        "live_auto_apply_family": "entry_bucket_runtime_policy_v1",
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
    assert report["status"] == "retired"
    assert report["runtime_effect"] is False


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
    assert report["status"] == "retired"
    assert report["runtime_effect"] is False


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
    assert report["status"] == "retired"
    assert report["runtime_effect"] is False


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
    assert report["status"] == "retired"
    assert report["runtime_effect"] is False


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
                        "live_auto_apply_family": "entry_bucket_runtime_policy_v1",
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
    assert report["status"] == "retired"
    assert report["runtime_effect"] is False
