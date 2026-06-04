import json

from src.engine.automation import source_quality_hard_gate as mod


def _write_preflight(tmp_path, target_date, payload):
    path = tmp_path / "observation_source_quality_audit" / f"observation_source_quality_audit_{target_date}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_source_quality_preflight_missing_artifact_blocks_tuning(monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path)

    preflight = mod.load_source_quality_preflight("2026-06-04")

    assert preflight["status"] == "missing"
    assert preflight["tuning_input_allowed"] is False
    assert preflight["allowed_runtime_apply"] is False
    assert preflight["blocked_reason"] == "source_quality_preflight_missing"
    assert mod.source_quality_preflight_blocked(preflight) is True


def test_source_quality_preflight_missing_pre_baseline_is_not_current_gate(monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path)

    preflight = mod.load_source_quality_preflight("2026-05-31")

    assert preflight["status"] == "missing"
    assert preflight["clean_baseline_enforced"] is False
    assert preflight["tuning_input_allowed"] is True
    assert preflight["source_quality_gate"] == "pass_or_not_evaluated"
    assert mod.source_quality_preflight_blocked(preflight) is False


def test_source_quality_preflight_invalid_artifact_blocks_tuning(monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path)
    path = tmp_path / "observation_source_quality_audit" / "observation_source_quality_audit_2026-06-04.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{bad json", encoding="utf-8")

    preflight = mod.load_source_quality_preflight("2026-06-04")

    assert preflight["status"] == "invalid"
    assert preflight["tuning_input_allowed"] is False
    assert preflight["blocked_reason"] == "source_quality_preflight_invalid"
    assert mod.source_quality_preflight_blocked(preflight) is True


def test_source_quality_preflight_unknown_token_only_does_not_block(monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path)
    artifact = _write_preflight(
        tmp_path,
        "2026-06-04",
        {
            "status": "warning",
            "summary": {
                "tuning_input_allowed": True,
                "hard_blocking_contract_gap_count": 0,
                "review_warning_count": 2,
            },
        },
    )

    preflight = mod.load_source_quality_preflight("2026-06-04")

    assert preflight["artifact"] == str(artifact)
    assert preflight["tuning_input_allowed"] is True
    assert preflight["source_quality_gate"] == "pass"
    assert preflight["review_warning_count"] == 2
    assert mod.source_quality_preflight_blocked(preflight) is False


def test_source_quality_preflight_contract_gap_blocks_and_scrubs_runtime_aliases(monkeypatch, tmp_path):
    monkeypatch.setattr(mod, "REPORT_DIR", tmp_path)
    _write_preflight(
        tmp_path,
        "2026-06-04",
        {
            "status": "warning",
            "summary": {
                "tuning_input_allowed": False,
                "blocked_reason": "blocked_contract_gap",
                "hard_blocking_contract_gap_count": 1,
                "hard_blocking_stages": ["scalp_sim_duplicate_buy_signal"],
            },
        },
    )
    preflight = mod.load_source_quality_preflight("2026-06-04")
    report = {
        "runtime_effect": True,
        "allowed_runtime_apply": True,
        "runtime_mutation_allowed": True,
        "approval_requests": [{"family": "entry"}],
        "runtime_approval_candidates": [{"family": "entry"}],
        "runtime_apply_bridge": {
            "selected": [{"family": "entry"}],
            "approved_requests": [{"family": "entry"}],
            "selected_count": 1,
            "approved": 1,
            "env_apply_allowed": True,
        },
        "summary": {
            "runtime_candidate_count": 1,
            "runtime_effect": True,
            "allowed_runtime_apply": True,
        },
    }

    blocked = mod.apply_source_quality_preflight_block(report, preflight)

    assert blocked["status"] == "source_quality_blocked"
    assert blocked["approval_requests"] == []
    assert blocked["runtime_approval_candidates"] == []
    assert blocked["runtime_apply_bridge"]["selected"] == []
    assert blocked["runtime_apply_bridge"]["approved_requests"] == []
    assert blocked["runtime_apply_bridge"]["selected_count"] == 0
    assert blocked["runtime_apply_bridge"]["approved"] == 0
    assert blocked["runtime_apply_bridge"]["env_apply_allowed"] is False
    assert blocked["runtime_mutation_allowed"] is False
    assert blocked["summary"]["runtime_candidate_count"] == 0
