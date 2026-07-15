from __future__ import annotations

from pathlib import Path

from src.engine.swing.bottom_rebound_policy_auto_loop import (
    PolicyAutoLoopConfig,
    build_policy_auto_loop_report,
    write_policy_auto_loop_report,
)
from src.engine.swing import bottom_rebound_policy_auto_loop as loop_mod


def _has_hangul(text: str) -> bool:
    return any("\uac00" <= char <= "\ud7a3" for char in text)


def _research() -> dict:
    return {
        "report_type": "bottom_rebound_pattern_research",
        "decision_authority": "research_only",
        "runtime_effect": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": False,
        "summary": {"top_primary_source_quality_adjusted_ev_pct": 1.0},
    }


def _candidate_source() -> dict:
    return {
        "report_type": "swing_bottom_rebound_candidate_source",
        "decision_authority": "swing_sim_candidate_source_only",
        "runtime_effect": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": False,
    }


def _ev_report(ev: float = 1.02, sample_count: int = 8) -> dict:
    return {
        "report_type": "swing_strategy_discovery_ev",
        "decision_authority": "swing_sim_exploration_only",
        "runtime_effect": False,
        "broker_order_forbidden": True,
        "allowed_runtime_apply": False,
        "aggregates": {
            "volatility_bucket": [
                {
                    "volatility_bucket": "bottom_rebound",
                    "sample_count": sample_count,
                    "source_quality_adjusted_ev_pct": ev,
                }
            ]
        },
    }


def _write_sources(
    tmp_path: Path, *, ev: float = 1.02, sample_count: int = 8
) -> dict[str, Path]:
    paths = {
        "bottom_rebound_research": tmp_path / "research.json",
        "candidate_source": tmp_path / "candidate_source.json",
        "swing_strategy_discovery_ev": tmp_path / "ev.json",
    }
    paths["bottom_rebound_research"].write_text(
        __import__("json").dumps(_research()), encoding="utf-8"
    )
    paths["candidate_source"].write_text(
        __import__("json").dumps(_candidate_source()), encoding="utf-8"
    )
    paths["swing_strategy_discovery_ev"].write_text(
        __import__("json").dumps(_ev_report(ev, sample_count)), encoding="utf-8"
    )
    return paths


def test_policy_auto_loop_promotes_sim_only_when_tier2_ai_passes_and_one_percent_better(
    tmp_path: Path,
) -> None:
    paths = _write_sources(tmp_path, ev=1.02, sample_count=8)
    ai_payload = {
        "schema_version": 1,
        "interpretation": {"policy_edge_state": "candidate_policy_better"},
        "audit": {
            "status": "pass",
            "explicit_gaps": [],
            "forbidden_use_violations": [],
        },
        "final_conclusion": {
            "classification_state": "sim_auto_approved",
            "promote_policy": True,
            "reason": "1 percent improvement rule passed.",
        },
    }

    report = build_policy_auto_loop_report(
        "2026-05-22",
        config=PolicyAutoLoopConfig(target_date="2026-05-22", min_sample_count=5),
        provider="openai",
        ai_raw_response=ai_payload,
        source_paths=paths,
    )

    assert report["final_conclusion"]["classification_state"] == "sim_auto_approved"
    assert (
        report["sim_auto_approved_policy"]["policy_version"]
        == "bottom_rebound_swing_source_v2"
    )
    assert report["runtime_effect"] is False
    assert report["allowed_runtime_apply"] is False
    assert report["broker_order_forbidden"] is True
    assert "broker_order_submit" in report["forbidden_uses"]


def test_policy_auto_loop_tier2_prompt_contract_is_english_ascii() -> None:
    instructions = loop_mod._ai_instructions()

    assert "Tier-2 swing simulation policy reviewer" in instructions
    assert not _has_hangul(instructions)


def test_policy_auto_loop_refreshes_control_tower_when_written_to_default_report_dir(
    tmp_path: Path, monkeypatch
) -> None:
    paths = _write_sources(tmp_path, ev=1.02, sample_count=8)
    report_dir = tmp_path / "policy_reports"
    approval_dir = tmp_path / "sim_auto_approvals"
    policy_dir = tmp_path / "swing_sim_policies"
    monkeypatch.setattr(loop_mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(
        "src.engine.swing.sim_auto_approval_control_tower.SIM_AUTO_APPROVAL_DIR",
        approval_dir,
    )
    monkeypatch.setattr(
        "src.engine.swing.sim_auto_approval_control_tower.SWING_SIM_POLICY_DIR",
        policy_dir,
    )
    ai_payload = {
        "schema_version": 1,
        "interpretation": {"policy_edge_state": "candidate_policy_better"},
        "audit": {
            "status": "pass",
            "explicit_gaps": [],
            "forbidden_use_violations": [],
        },
        "final_conclusion": {
            "classification_state": "sim_auto_approved",
            "promote_policy": True,
            "reason": "1 percent improvement rule passed.",
        },
    }
    report = build_policy_auto_loop_report(
        "2026-05-22",
        config=PolicyAutoLoopConfig(target_date="2026-05-22", min_sample_count=5),
        provider="openai",
        ai_raw_response=ai_payload,
        source_paths=paths,
    )

    write_policy_auto_loop_report(report, output_dir=report_dir)

    approval = __import__("json").loads(
        (approval_dir / "swing_sim_auto_approval_2026-05-22.json").read_text()
    )
    assert approval["approved_source_ids"] == ["bottom_rebound_policy_auto_loop"]
    assert approval["approved_policy_count"] == 1


def test_policy_auto_loop_blocks_when_tier2_ai_is_disabled(tmp_path: Path) -> None:
    paths = _write_sources(tmp_path, ev=1.05, sample_count=8)

    report = build_policy_auto_loop_report(
        "2026-05-22",
        provider="none",
        source_paths=paths,
    )

    assert report["ai_tier2_review"]["status"] == "disabled_deterministic_review"
    assert (
        report["final_conclusion"]["classification_state"]
        == "source_only_keep_collecting"
    )
    assert report["sim_auto_approved_policy"] is None
    assert "explicit_gap:tier2_ai_review_disabled" in report["warnings"]
    assert report["runtime_effect"] is False


def test_policy_auto_loop_keeps_collecting_when_sample_floor_not_met(
    tmp_path: Path,
) -> None:
    paths = _write_sources(tmp_path, ev=1.05, sample_count=2)
    ai_payload = {
        "schema_version": 1,
        "interpretation": {"policy_edge_state": "candidate_policy_better"},
        "audit": {
            "status": "correction_required",
            "explicit_gaps": ["sample_floor_not_met"],
            "forbidden_use_violations": [],
        },
        "final_conclusion": {
            "classification_state": "source_only_keep_collecting",
            "promote_policy": False,
            "reason": "sample floor not met",
        },
    }

    report = build_policy_auto_loop_report(
        "2026-05-22", ai_raw_response=ai_payload, source_paths=paths
    )

    assert report["sim_auto_approved_policy"] is None
    assert (
        report["final_conclusion"]["classification_state"]
        == "source_only_keep_collecting"
    )
    assert "explicit_gap:sample_floor_not_met" in report["warnings"]


def test_policy_auto_loop_ai_cannot_override_numeric_gate(tmp_path: Path) -> None:
    paths = _write_sources(tmp_path, ev=1.0, sample_count=8)
    ai_payload = {
        "schema_version": 1,
        "interpretation": {"policy_edge_state": "candidate_policy_better"},
        "audit": {
            "status": "pass",
            "explicit_gaps": [],
            "forbidden_use_violations": [],
        },
        "final_conclusion": {
            "classification_state": "sim_auto_approved",
            "promote_policy": True,
            "reason": "AI wants to promote",
        },
    }

    report = build_policy_auto_loop_report(
        "2026-05-22", ai_raw_response=ai_payload, source_paths=paths
    )

    assert report["sim_auto_approved_policy"] is None
    assert (
        report["final_conclusion"]["classification_state"]
        == "source_only_keep_collecting"
    )
    assert "explicit_gap:one_percent_improvement_not_met" in report["warnings"]
