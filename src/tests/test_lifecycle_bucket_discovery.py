import json
from types import SimpleNamespace

from src.engine import lifecycle_bucket_discovery as mod


def _ai_keep_response():
    return {
        "schema_version": 1,
        "interpretation": {
            "bucket_reviews": [],
            "source_contract_review": {"status": "pass", "changes": [], "reason": "contract stable"},
        },
        "audit": {"status": "pass", "issues": [], "reason": "two-pass review accepted"},
        "final_conclusions": [],
    }


def _ai_block_response(reason):
    return {
        "schema_version": 1,
        "interpretation": {
            "bucket_reviews": [],
            "source_contract_review": {"status": "pass", "changes": [], "reason": "contract stable"},
        },
        "audit": {"status": "correction_required", "issues": [reason], "reason": reason},
        "final_conclusions": [
            {
                "bucket_id": "entry:combo_entry_spot:score_score_66_69_source_wait6579_ev_cohort_stale_fresh_or_unflagged_liquidity_liquidity_unknown",
                "final_bucket_relation": "existing_bucket_refinement",
                "final_classification_state": "runtime_blocked_contract_gap",
                "final_decision": "block",
                "reason": reason,
            }
        ],
    }


def _write_ldm(path):
    path.write_text(
        json.dumps(
            {
                "date": path.stem.removeprefix("lifecycle_decision_matrix_"),
                "entry_bucket_attribution": {
                    "buckets": [
                        {
                            "bucket_type": "combo_entry_spot",
                            "bucket_key": mod.ENTRY_LIVE_AUTO_BUCKET_KEY,
                            "sample": 44,
                            "joined_sample": 44,
                            "join_rate": 1.0,
                            "source_quality_gate": "pass",
                            "source_quality_adjusted_ev_pct": 1.7,
                            "equal_weight_avg_profit_pct": 3.5,
                            "mfe_10m_pct": 5.0,
                            "mae_10m_pct": -3.1,
                            "recommended_route": "candidate_recovery_or_relax",
                        },
                        {
                            "bucket_type": "combo_entry_spot",
                            "bucket_key": "score=unknown|source=blocked_ai_score",
                            "sample": 12,
                            "joined_sample": 12,
                            "join_rate": 1.0,
                            "source_quality_gate": "pass",
                            "source_quality_adjusted_ev_pct": 2.2,
                            "recommended_route": "candidate_recovery_or_relax",
                        },
                    ]
                },
                "scale_in_bucket_attribution": {
                    "buckets": [
                        {
                            "bucket_type": "arm",
                            "bucket_key": "PYRAMID",
                            "sample": 38,
                            "joined_sample": 38,
                            "join_rate": 1.0,
                            "source_quality_gate": "pass",
                            "source_quality_adjusted_ev_pct": -13.3,
                            "recommended_route": "candidate_tighten_or_exclude",
                        },
                        {
                            "bucket_type": "blocker_reason",
                            "bucket_key": "pnl_out_of_range(0.32)",
                            "sample": 48,
                            "joined_sample": 48,
                            "join_rate": 1.0,
                            "source_quality_gate": "pass",
                            "source_quality_adjusted_ev_pct": 0.32,
                            "recommended_route": "candidate_recovery_or_relax",
                        },
                    ]
                },
                "overnight_bucket_attribution": {"buckets": []},
                "policy_entries": [
                    {
                        "policy_key": "holding:weighted_adm_v1",
                        "stage": "holding",
                        "sample": 25,
                        "joined_sample": 20,
                        "join_rate": 0.8,
                        "source_quality_gate": "pass",
                        "stage_ev_composite_pct": 0.42,
                        "selected_action": "HOLD",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )


def test_lifecycle_bucket_discovery_classifies_live_sim_and_new_buckets(tmp_path, monkeypatch):
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "report"
    catalog_dir = tmp_path / "catalog"
    sim_dir = tmp_path / "sim"
    ldm_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CATALOG_DIR", catalog_dir)
    monkeypatch.setattr(mod, "SIM_AUTO_APPROVAL_DIR", sim_dir)
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-22.json")

    report = mod.write_lifecycle_bucket_discovery_report(
        "2026-05-22",
        ai_raw_response=_ai_keep_response(),
    )

    states = {item["bucket_id"]: item for item in report["surfaced_candidates"]}
    live = [item for item in states.values() if item["classification_state"] == "live_auto_apply_ready"]
    sim = [item for item in states.values() if item["classification_state"] == "sim_auto_approved"]
    new = [item for item in states.values() if item["classification_state"] == "new_bucket_candidate"]
    assert {item["live_auto_apply_family"] for item in live} == {
        mod.ENTRY_LIVE_AUTO_FAMILY,
        mod.SCALE_IN_LIVE_AUTO_FAMILY,
    }
    assert sim
    assert new[0]["bucket_relation"] == "new_bucket_candidate"
    assert report["summary"]["human_intervention_required"] is False
    assert (report_dir / "lifecycle_bucket_discovery_2026-05-22.json").exists()
    assert (catalog_dir / "lifecycle_bucket_catalog_2026-05-22.json").exists()
    auto = json.loads((sim_dir / "lifecycle_bucket_sim_auto_approval_2026-05-22.json").read_text())
    assert auto["approved"] is True
    assert auto["broker_order_forbidden"] is True
    assert auto["actual_order_submitted"] is False


def test_lifecycle_bucket_discovery_keeps_deterministic_live_when_ai_review_disabled(tmp_path, monkeypatch):
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "report"
    catalog_dir = tmp_path / "catalog"
    sim_dir = tmp_path / "sim"
    ldm_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CATALOG_DIR", catalog_dir)
    monkeypatch.setattr(mod, "SIM_AUTO_APPROVAL_DIR", sim_dir)
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-22.json")

    report = mod.write_lifecycle_bucket_discovery_report("2026-05-22", ai_review_provider="none")

    live = [item for item in report["surfaced_candidates"] if item["classification_state"] == "live_auto_apply_ready"]
    deferred = [item for item in live if item.get("ai_review_followup_required") == "post_apply_verification"]
    assert {item["live_auto_apply_family"] for item in live} == {
        mod.ENTRY_LIVE_AUTO_FAMILY,
        mod.SCALE_IN_LIVE_AUTO_FAMILY,
    }
    assert len(deferred) == len(live)
    assert report["summary"]["ai_two_pass_review_status"] == "disabled"
    assert "ai_two_pass_review_disabled_live_auto_deferred_to_post_apply" in report["warnings"]


def test_lifecycle_bucket_discovery_ignores_ambiguous_ai_block_for_live_candidate(tmp_path, monkeypatch):
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "report"
    catalog_dir = tmp_path / "catalog"
    sim_dir = tmp_path / "sim"
    ldm_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CATALOG_DIR", catalog_dir)
    monkeypatch.setattr(mod, "SIM_AUTO_APPROVAL_DIR", sim_dir)
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-22.json")

    report = mod.write_lifecycle_bucket_discovery_report(
        "2026-05-22",
        ai_raw_response=_ai_block_response("effect is only about 1 percent and confidence is low"),
    )

    live = [item for item in report["surfaced_candidates"] if item["classification_state"] == "live_auto_apply_ready"]
    ignored = [item for item in live if item.get("ai_review_block_ignored_reason")]
    assert ignored
    assert report["summary"]["live_auto_apply_ready_count"] == 2
    assert "ai_review_ambiguous_live_candidate_kept_for_post_apply" in report["warnings"]


def test_lifecycle_bucket_discovery_applies_explicit_contract_ai_block_for_live_candidate(tmp_path, monkeypatch):
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "report"
    catalog_dir = tmp_path / "catalog"
    sim_dir = tmp_path / "sim"
    ldm_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CATALOG_DIR", catalog_dir)
    monkeypatch.setattr(mod, "SIM_AUTO_APPROVAL_DIR", sim_dir)
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-22.json")

    report = mod.write_lifecycle_bucket_discovery_report(
        "2026-05-22",
        ai_raw_response=_ai_block_response("env mapping and post-apply attribution contract are missing"),
    )

    blocked = [
        item
        for item in report["surfaced_candidates"]
        if item.get("bucket_id", "").startswith("entry:combo_entry_spot")
        and item["classification_state"] == "runtime_blocked_contract_gap"
    ]
    assert blocked
    assert report["summary"]["live_auto_apply_ready_count"] == 1


def test_lifecycle_bucket_discovery_surfaces_source_contract_drift(tmp_path, monkeypatch):
    ldm_dir = tmp_path / "ldm"
    report_dir = tmp_path / "report"
    catalog_dir = tmp_path / "catalog"
    sim_dir = tmp_path / "sim"
    ldm_dir.mkdir()
    report_dir.mkdir()
    monkeypatch.setattr(mod, "LDM_REPORT_DIR", ldm_dir)
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CATALOG_DIR", catalog_dir)
    monkeypatch.setattr(mod, "SIM_AUTO_APPROVAL_DIR", sim_dir)
    (report_dir / "lifecycle_bucket_discovery_2026-05-21.json").write_text(
        json.dumps(
            {
                "date": "2026-05-21",
                "source_contract": {
                    "schema_version": "lifecycle_source_contract_snapshot_v1",
                    "source_keys": ["removed_source"],
                    "sections": {
                        "entry_bucket_attribution": {
                            "bucket_fields": ["bucket_type", "bucket_key", "removed_field"],
                            "bucket_types": ["combo_entry_spot"],
                            "dimension_keys": ["score"],
                        }
                    },
                    "policy_fields": [],
                },
            }
        ),
        encoding="utf-8",
    )
    _write_ldm(ldm_dir / "lifecycle_decision_matrix_2026-05-22.json")

    report = mod.write_lifecycle_bucket_discovery_report(
        "2026-05-22",
        ai_raw_response=_ai_keep_response(),
    )

    assert report["summary"]["source_contract_status"] == "fail"
    assert report["source_contract_changes"]
    drift = [
        item
        for item in report["surfaced_candidates"]
        if item["stage"] == "source_contract" and item["classification_state"] == "code_patch_required"
    ]
    assert drift


def test_lifecycle_bucket_discovery_openai_review_uses_tier3_schema(monkeypatch):
    captured = {}

    class _FakeResponses:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(output_text=json.dumps(_ai_keep_response()), usage=SimpleNamespace())

    class _FakeOpenAI:
        def __init__(self, api_key):
            self.api_key = api_key
            self.responses = _FakeResponses()

    monkeypatch.setattr("src.engine.daily_threshold_cycle_report._load_threshold_ai_openai_keys", lambda: [("OPENAI_API_KEY", "key")])
    monkeypatch.setattr("openai.OpenAI", _FakeOpenAI)

    raw, status = mod._call_openai_ai_review({"surfaced_candidates": []})

    assert json.loads(raw)["schema_version"] == 1
    assert status["model"] == mod.AI_REVIEW_MODEL
    assert status["reasoning_effort"] == "high"
    assert captured["model"] == mod.AI_REVIEW_MODEL
    assert captured["text"]["format"]["name"] == mod.AI_REVIEW_SCHEMA_NAME
    assert captured["text"]["format"]["strict"] is True
