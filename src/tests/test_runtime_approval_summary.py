import json

import pytest

from src.engine import runtime_approval_summary as mod


@pytest.fixture(autouse=True)
def _isolate_pattern_lab_audit_dirs(tmp_path, monkeypatch):
    monkeypatch.setattr(mod, "PATTERN_LAB_CURRENTNESS_AUDIT_DIR", tmp_path / "missing_currentness_audit")
    monkeypatch.setattr(mod, "PATTERN_LAB_PROPAGATION_AUDIT_DIR", tmp_path / "missing_propagation_audit")


def test_runtime_approval_summary_combines_scalping_and_swing(tmp_path, monkeypatch):
    ev_dir = tmp_path / "threshold_cycle_ev"
    env_dir = tmp_path / "runtime_env"
    swing_dir = tmp_path / "swing_runtime_approval"
    out_dir = tmp_path / "runtime_approval_summary"
    ev_dir.mkdir(parents=True)
    env_dir.mkdir(parents=True)
    swing_dir.mkdir(parents=True)
    monkeypatch.setattr(
        mod,
        "ev_report_paths",
        lambda target_date: (
            ev_dir / f"threshold_cycle_ev_{target_date}.json",
            ev_dir / f"threshold_cycle_ev_{target_date}.md",
        ),
    )
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_DIR", swing_dir)
    monkeypatch.setattr(mod, "SUMMARY_DIR", out_dir)

    env_path = env_dir / "threshold_runtime_env_2026-05-11.env"
    env_path.write_text("export KORSTOCKSCAN_THRESHOLD_RUNTIME_AUTO_APPLY_ENABLED=true\n", encoding="utf-8")
    (ev_dir / "threshold_cycle_ev_2026-05-11.json").write_text(
        json.dumps(
            {
                "runtime_apply": {
                    "selected_families": ["score65_74_recovery_probe"],
                    "runtime_env_file": str(env_path),
                },
                "calibration_outcome": {
                    "decisions": [
                        {
                            "family": "score65_74_recovery_probe",
                            "calibration_state": "adjust_up",
                            "confidence": 1.0,
                            "sample_count": 712,
                            "sample_floor": 20,
                        },
                        {
                            "family": "position_sizing_cap_release",
                            "calibration_state": "hold_sample",
                            "confidence": 0.8,
                            "sample_count": 49,
                            "sample_floor": 30,
                        },
                    ]
                },
            }
        ),
        encoding="utf-8",
    )
    (swing_dir / "swing_runtime_approval_2026-05-11.json").write_text(
        json.dumps(
            {
                "summary": {"requested": 0, "approved": 0},
                "candidates": [
                    {
                        "family": "swing_model_floor",
                        "sample_count": 3,
                        "sample_floor": 3,
                    }
                ],
                "blocked_requests": [
                    {
                        "family": "swing_model_floor",
                        "calibration_state": "freeze",
                        "tradeoff_score": 0.8657,
                        "block_reasons": ["critical_instrumentation_gap", "db_load_gap"],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = mod.build_runtime_approval_summary("2026-05-11")

    assert report["runtime_mutation_allowed"] is False
    assert report["summary"]["scalping_items"] == 2
    assert report["summary"]["scalping_selected_auto_bounded_live"] == 1
    assert report["summary"]["scalping_legacy_hard_gate_risk_counts"]["no_unreviewed_hard_gate"] == 1
    assert report["summary"]["swing_blocked"] == 1
    assert report["summary"]["swing_legacy_hard_gate_risk_counts"]["no_unreviewed_hard_gate"] == 1
    assert report["application_timing"]["runtime_env_file"] == str(env_path)
    assert "WAIT 구간" in report["scalping"][0]["description"]
    assert report["scalping"][0]["current_application"] == "PREOPEN env 적용: 당일 runtime 변경 대상"
    assert report["scalping"][0]["gate_review_class"] == "entry_unlock_probe"
    assert report["scalping"][0]["legacy_hard_gate_risk"] == "no_unreviewed_hard_gate"
    assert "PREOPEN env" in report["scalping"][0]["state_interpretation"]
    assert report["scalping"][1]["reason_label"] == "표본 부족"
    assert "표본 부족" in report["scalping"][1]["state_interpretation"]
    assert report["swing"][0]["reason_label"] == "계측 gap, DB gap"
    assert report["swing"][0]["current_application"] == "스윙 dry-run/probe 관찰: 실주문 변경 없음"
    assert report["swing"][0]["gate_review_class"] == "approval_route_available"
    markdown = (out_dir / "runtime_approval_summary_2026-05-11.md").read_text(encoding="utf-8")
    assert "## Scalping" in markdown
    assert "score65_74_recovery_probe" in markdown
    assert "설명" in markdown
    assert "현재 적용" in markdown
    assert "Gate 분류" in markdown
    assert "판정 해석" in markdown
    assert "## Swing" in markdown
    assert "swing_model_floor" in markdown


def test_runtime_approval_summary_warns_when_sources_missing(tmp_path, monkeypatch):
    ev_dir = tmp_path / "threshold_cycle_ev"
    swing_dir = tmp_path / "swing_runtime_approval"
    out_dir = tmp_path / "runtime_approval_summary"
    monkeypatch.setattr(
        mod,
        "ev_report_paths",
        lambda target_date: (
            ev_dir / f"threshold_cycle_ev_{target_date}.json",
            ev_dir / f"threshold_cycle_ev_{target_date}.md",
        ),
    )
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_DIR", swing_dir)
    monkeypatch.setattr(mod, "SUMMARY_DIR", out_dir)

    report = mod.build_runtime_approval_summary("2026-05-11")

    assert "threshold_cycle_ev_missing" in report["warnings"]
    assert "swing_runtime_approval_missing" in report["warnings"]


def test_runtime_approval_summary_classifies_legacy_gate_and_contract_gaps(tmp_path, monkeypatch):
    ev_dir = tmp_path / "threshold_cycle_ev"
    swing_dir = tmp_path / "swing_runtime_approval"
    out_dir = tmp_path / "runtime_approval_summary"
    ev_dir.mkdir(parents=True)
    swing_dir.mkdir(parents=True)
    monkeypatch.setattr(
        mod,
        "ev_report_paths",
        lambda target_date: (
            ev_dir / f"threshold_cycle_ev_{target_date}.json",
            ev_dir / f"threshold_cycle_ev_{target_date}.md",
        ),
    )
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_DIR", swing_dir)
    monkeypatch.setattr(mod, "SUMMARY_DIR", out_dir)

    (ev_dir / "threshold_cycle_ev_2026-05-15.json").write_text(
        json.dumps(
            {
                "calibration_outcome": {
                    "decisions": [
                        {"family": "liquidity_gate_refined_candidate", "calibration_state": "hold"},
                        {"family": "pre_submit_price_guard", "calibration_state": "freeze"},
                    ]
                }
            }
        ),
        encoding="utf-8",
    )
    (swing_dir / "swing_runtime_approval_2026-05-15.json").write_text(
        json.dumps(
            {
                "date": "2026-05-15",
                "summary": {"requested": 0, "approved": 0},
                "candidates": [
                    {"family": "swing_gatekeeper_accept_reject", "sample_count": 27, "sample_floor": 5}
                ],
                "blocked_requests": [
                    {
                        "family": "swing_gatekeeper_accept_reject",
                        "calibration_state": "freeze",
                        "tradeoff_score": 0.8361,
                        "block_reasons": ["runtime_family_guard_missing"],
                    }
                ],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = mod.build_runtime_approval_summary("2026-05-15")

    scalping = {row["family"]: row for row in report["scalping"]}
    assert scalping["liquidity_gate_refined_candidate"]["gate_review_class"] == "superseded_legacy_pre_ai_gate"
    assert scalping["liquidity_gate_refined_candidate"]["legacy_hard_gate_risk"] == "legacy_summary_superseded"
    assert scalping["pre_submit_price_guard"]["legacy_hard_gate_risk"] == "intentional_safety_guard"
    swing = report["swing"][0]
    assert swing["gate_review_class"] == "legacy_hard_gate_contract_gap"
    assert swing["legacy_hard_gate_risk"] == "contract_gap"
    assert "blocked_gatekeeper_reject" in swing["analysis_coverage"]
    assert report["summary"]["scalping_legacy_hard_gate_risk_counts"]["legacy_summary_superseded"] == 1
    assert report["summary"]["swing_legacy_hard_gate_risk_counts"]["contract_gap"] == 1


def test_runtime_approval_summary_surfaces_swing_one_share_approval_request(tmp_path, monkeypatch):
    ev_dir = tmp_path / "threshold_cycle_ev"
    swing_dir = tmp_path / "swing_runtime_approval"
    approval_dir = tmp_path / "approvals"
    out_dir = tmp_path / "runtime_approval_summary"
    ev_dir.mkdir(parents=True)
    swing_dir.mkdir(parents=True)
    approval_dir.mkdir(parents=True)
    monkeypatch.setattr(
        mod,
        "ev_report_paths",
        lambda target_date: (
            ev_dir / f"threshold_cycle_ev_{target_date}.json",
            ev_dir / f"threshold_cycle_ev_{target_date}.md",
        ),
    )
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_DIR", swing_dir)
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_ARTIFACT_DIR", approval_dir)
    monkeypatch.setattr(mod, "SUMMARY_DIR", out_dir)

    (ev_dir / "threshold_cycle_ev_2026-05-15.json").write_text(
        json.dumps({"calibration_outcome": {"decisions": []}}),
        encoding="utf-8",
    )
    (swing_dir / "swing_runtime_approval_2026-05-15.json").write_text(
        json.dumps(
            {
                "date": "2026-05-15",
                "summary": {"requested": 1, "approved": 0},
                "approval_requests": [
                    {
                        "family": "swing_one_share_real_canary_phase0",
                        "policy_id": "swing_one_share_real_canary_phase0",
                        "approval_id": "swing_one_share_real_canary:2026-05-15:phase0",
                        "calibration_state": "approval_required",
                    }
                ],
                "blocked_requests": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    report = mod.build_runtime_approval_summary("2026-05-15")

    assert report["summary"]["swing_requested"] == 1
    assert report["swing"][0]["family"] == "swing_one_share_real_canary_phase0"
    assert report["swing"][0]["state"] == "approval_required"
    assert report["swing"][0]["reason_label"] == "1주 real canary approval artifact 없음"
    assert report["swing"][0]["approval_id"] == "swing_one_share_real_canary:2026-05-15:phase0"


def test_runtime_approval_summary_surfaces_panic_approval_requests(tmp_path, monkeypatch):
    ev_dir = tmp_path / "threshold_cycle_ev"
    calibration_dir = tmp_path / "threshold_cycle_calibration"
    swing_dir = tmp_path / "swing_runtime_approval"
    out_dir = tmp_path / "runtime_approval_summary"
    ev_dir.mkdir(parents=True)
    calibration_dir.mkdir(parents=True)
    calibration_path = calibration_dir / "threshold_cycle_calibration_2026-05-13.json"
    calibration_path.write_text(
        json.dumps(
            {
                "calibration_source_bundle": {
                    "source_metrics": {
                        "panic_sell_defense": {
                            "runtime_effect": "report_only_no_mutation",
                            "panic_state": "PANIC_SELL",
                            "panic_regime_mode": "PANIC_DETECTED",
                            "panic_regime_decision_authority": "source_quality_only",
                            "panic_regime_runtime_effect": "report_only_no_mutation",
                            "stop_loss_exit_count": 2,
                            "confirmation_eligible_exit_count": 1,
                            "microstructure_max_panic_score": 0.91,
                            "candidate_status": {"panic_stop_confirmation": "report_only_candidate"},
                        },
                        "panic_buying": {
                            "runtime_effect": "report_only_no_mutation",
                            "panic_buy_state": "PANIC_BUY",
                            "panic_buy_regime_mode": "PANIC_BUY_CONTINUATION",
                            "panic_buy_regime_decision_authority": "source_quality_only",
                            "panic_buy_regime_runtime_effect": "report_only_no_mutation",
                            "panic_buy_active_count": 1,
                            "tp_counterfactual_count": 3,
                            "trailing_winner_count": 1,
                            "max_panic_buy_score": 0.88,
                            "market_wide_panic_buy_confirmed": True,
                            "market_breadth_risk_on_advisory": True,
                            "candidate_status": {"panic_buy_runner_tp_canary": "report_only_candidate"},
                        },
                    }
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (ev_dir / "threshold_cycle_ev_2026-05-13.json").write_text(
        json.dumps({"sources": {"calibration": str(calibration_path)}, "calibration_outcome": {"decisions": []}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        mod,
        "ev_report_paths",
        lambda target_date: (
            ev_dir / f"threshold_cycle_ev_{target_date}.json",
            ev_dir / f"threshold_cycle_ev_{target_date}.md",
        ),
    )
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_DIR", swing_dir)
    monkeypatch.setattr(mod, "SUMMARY_DIR", out_dir)

    report = mod.build_runtime_approval_summary("2026-05-13")

    assert report["summary"]["panic_approval_requested"] == 0
    assert {row["family"] for row in report["panic"]} == {
        "panic_entry_freeze_guard",
        "panic_buy_runner_tp_canary",
    }
    assert all(row["state"] == "approval_contract_missing" for row in report["panic"])
    assert all(row["approval_contract_status"] == "contract_missing" for row in report["panic"])
    assert all(row["selected_auto_bounded_live"] is False for row in report["panic"])
    panic_sell = next(row for row in report["panic"] if row["family"] == "panic_entry_freeze_guard")
    assert panic_sell["panic_regime_mode"] == "PANIC_DETECTED"
    assert panic_sell["panic_regime_decision_authority"] == "source_quality_only"
    assert "entry_pre_submit_runtime_guard" in panic_sell["approval_contract_missing_components"]
    panic_buy = next(row for row in report["panic"] if row["family"] == "panic_buy_runner_tp_canary")
    assert panic_buy["panic_buy_regime_mode"] == "PANIC_BUY_CONTINUATION"
    assert panic_buy["panic_buy_regime_decision_authority"] == "source_quality_only"
    assert panic_buy["market_wide_panic_buy_confirmed"] is True
    assert panic_buy["market_breadth_risk_on_advisory"] is True
    markdown = (out_dir / "runtime_approval_summary_2026-05-13.md").read_text(encoding="utf-8")
    assert "## Panic" in markdown
    assert "panic_buy_runner_tp_canary" in markdown


def test_runtime_approval_summary_freezes_panic_request_on_source_quality_blocker(tmp_path, monkeypatch):
    ev_dir = tmp_path / "threshold_cycle_ev"
    calibration_dir = tmp_path / "threshold_cycle_calibration"
    swing_dir = tmp_path / "swing_runtime_approval"
    out_dir = tmp_path / "runtime_approval_summary"
    ev_dir.mkdir(parents=True)
    calibration_dir.mkdir(parents=True)
    calibration_path = calibration_dir / "threshold_cycle_calibration_2026-05-14.json"
    calibration_path.write_text(
        json.dumps(
            {
                "calibration_source_bundle": {
                    "source_metrics": {
                        "panic_sell_defense": {
                            "runtime_effect": "report_only_no_mutation",
                            "panic_state": "NORMAL",
                            "active_sim_probe_positions": 3,
                            "microstructure_max_panic_score": 0.84,
                            "candidate_status": {"panic_entry_freeze_guard": "report_only_candidate"},
                            "source_quality_blockers": ["market_regime_not_risk_off"],
                            "market_breadth_followup_candidate": True,
                        },
                        "panic_buying": {
                            "runtime_effect": "report_only_no_mutation",
                            "panic_buy_state": "PANIC_BUY",
                            "panic_buy_regime_mode": "PANIC_BUY_CONTINUATION",
                            "panic_buy_regime_decision_authority": "source_quality_only",
                            "panic_buy_regime_runtime_effect": "report_only_no_mutation",
                            "panic_buy_active_count": 1,
                            "tp_counterfactual_count": 3,
                            "max_panic_buy_score": 0.88,
                            "market_wide_panic_buy_confirmed": False,
                            "market_breadth_risk_on_advisory": False,
                            "source_quality_blockers": ["panic_buy_local_unconfirmed_by_market_breadth"],
                            "candidate_status": {"panic_buy_runner_tp_canary": "report_only_candidate"},
                        },
                    }
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (ev_dir / "threshold_cycle_ev_2026-05-14.json").write_text(
        json.dumps({"sources": {"calibration": str(calibration_path)}, "calibration_outcome": {"decisions": []}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        mod,
        "ev_report_paths",
        lambda target_date: (
            ev_dir / f"threshold_cycle_ev_{target_date}.json",
            ev_dir / f"threshold_cycle_ev_{target_date}.md",
        ),
    )
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_DIR", swing_dir)
    monkeypatch.setattr(mod, "SUMMARY_DIR", out_dir)

    report = mod.build_runtime_approval_summary("2026-05-14")

    rows = {row["family"]: row for row in report["panic"]}
    row = rows["panic_entry_freeze_guard"]
    assert row["state"] == "freeze"
    assert "source_quality_blocker" in row["reasons"]
    assert row["source_quality_blockers"] == ["market_regime_not_risk_off"]
    assert row["market_breadth_followup_candidate"] is True
    panic_buy = rows["panic_buy_runner_tp_canary"]
    assert panic_buy["state"] == "freeze"
    assert "source_quality_blocker" in panic_buy["reasons"]
    assert panic_buy["source_quality_blockers"] == ["panic_buy_local_unconfirmed_by_market_breadth"]


def test_runtime_approval_summary_does_not_request_for_inactive_panic_candidate_status(tmp_path, monkeypatch):
    ev_dir = tmp_path / "threshold_cycle_ev"
    calibration_dir = tmp_path / "threshold_cycle_calibration"
    swing_dir = tmp_path / "swing_runtime_approval"
    out_dir = tmp_path / "runtime_approval_summary"
    ev_dir.mkdir(parents=True)
    calibration_dir.mkdir(parents=True)
    calibration_path = calibration_dir / "threshold_cycle_calibration_2026-05-14.json"
    calibration_path.write_text(
        json.dumps(
            {
                "calibration_source_bundle": {
                    "source_metrics": {
                        "panic_sell_defense": {
                            "runtime_effect": "report_only_no_mutation",
                            "panic_state": "NORMAL",
                            "active_sim_probe_positions": 10,
                            "candidate_status": {
                                "panic_entry_freeze_guard": "inactive_no_panic",
                                "panic_attribution_pack": "active_report_only",
                            },
                            "market_breadth_followup_candidate": True,
                        }
                    }
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    (ev_dir / "threshold_cycle_ev_2026-05-14.json").write_text(
        json.dumps({"sources": {"calibration": str(calibration_path)}, "calibration_outcome": {"decisions": []}}),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        mod,
        "ev_report_paths",
        lambda target_date: (
            ev_dir / f"threshold_cycle_ev_{target_date}.json",
            ev_dir / f"threshold_cycle_ev_{target_date}.md",
        ),
    )
    monkeypatch.setattr(mod, "SWING_RUNTIME_APPROVAL_DIR", swing_dir)
    monkeypatch.setattr(mod, "SUMMARY_DIR", out_dir)

    report = mod.build_runtime_approval_summary("2026-05-14")

    assert report["summary"]["panic_approval_requested"] == 0
    row = report["panic"][0]
    assert row["state"] == "hold"
    assert row["reasons"] == ["hold"]
