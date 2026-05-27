import gzip
import json
from dataclasses import replace
from datetime import datetime

from src.engine import lifecycle_ai_context as mod


def test_lifecycle_ai_context_builds_stage_contexts_with_forbidden_uses(tmp_path, monkeypatch):
    report_dir = tmp_path / "report"
    monkeypatch.setattr(mod, "REPORT_DIR", report_dir)
    monkeypatch.setattr(mod, "CONTEXT_DIR", report_dir / "lifecycle_ai_context")
    monkeypatch.setattr(mod, "ATTRIBUTION_DIR", report_dir / "lifecycle_ai_context_attribution")

    ldm_dir = report_dir / "lifecycle_decision_matrix"
    attr_dir = report_dir / "lifecycle_ai_context_attribution"
    ldm_dir.mkdir(parents=True)
    attr_dir.mkdir(parents=True)
    (ldm_dir / "lifecycle_decision_matrix_2026-05-20.json").write_text(
        json.dumps(
            {
                "matrix_version": "lifecycle_decision_matrix_v1_2026-05-20",
                "policy_entries": [
                    {
                        "stage": "entry",
                        "policy_key": "entry:weighted_adm_v1",
                        "selected_action": "WAIT_REQUOTE",
                        "confidence": 0.8,
                        "stage_ev_composite_pct": 0.42,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (attr_dir / "lifecycle_ai_context_attribution_2026-05-20.json").write_text(
        json.dumps(
            {
                "stage_attribution": {
                    "entry": {
                        "context_contribution_score": 0.5,
                        "bounded_auxiliary_weight": 0.075,
                        "attribution_quality_status": "sampled_replay",
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    report = mod.build_lifecycle_ai_context_report("2026-05-20")

    assert report["runtime_effect"] is False
    assert report["decision_authority"] == "ai_advisory_prompt_context_only"
    assert report["stage_contexts"][0]["stage"] == "entry"
    assert report["stage_contexts"][0]["prompt_injection_allowed"] is True
    assert report["stage_contexts"][0]["context_contribution_score"] == 0.5
    assert "real_order_gate" in report["stage_contexts"][0]["forbidden_uses"]


def test_lifecycle_ai_context_attribution_counts_runtime_provenance(tmp_path, monkeypatch):
    pipeline_dir = tmp_path / "pipeline_events"
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "ATTRIBUTION_DIR", tmp_path / "report" / "lifecycle_ai_context_attribution")
    pipeline_dir.mkdir(parents=True)
    (pipeline_dir / "pipeline_events_2026-05-20.jsonl").write_text(
        "\n".join(
            [
                json.dumps(
                    {
                        "stage": "ai_result",
                        "fields": {
                            "lifecycle_ai_context_enabled": True,
                            "lifecycle_ai_context_applied": True,
                            "lifecycle_ai_context_stage": "entry",
                            "lifecycle_ai_context_alignment_hint": "WAIT_REQUOTE",
                            "action": "WAIT",
                            "score": 63,
                            "profit_rate": 0.4,
                            "no_context_replay_action": "BUY",
                            "no_context_replay_score": 72,
                        },
                    }
                ),
                json.dumps(
                    {
                        "stage": "holding_review",
                        "fields": {
                            "lifecycle_ai_context_enabled": True,
                            "lifecycle_ai_context_applied": False,
                            "lifecycle_ai_context_stage": "holding",
                        },
                    }
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    report = mod.build_lifecycle_ai_context_attribution_report("2026-05-20", replay_budget=30)

    entry = report["stage_attribution"]["entry"]
    assert report["runtime_effect"] is False
    assert entry["context_eligible_count"] == 1
    assert entry["context_applied_count"] == 1
    assert entry["ai_action_alignment_rate"] == 1.0
    assert entry["no_context_replay_observed"] == 1
    assert entry["ai_action_delta_rate"] == 1.0
    assert entry["actual_order_submitted"] is False
    assert entry["broker_order_forbidden"] is True


def test_lifecycle_ai_context_attribution_reads_gzip_pipeline_events(tmp_path, monkeypatch):
    pipeline_dir = tmp_path / "pipeline_events"
    monkeypatch.setattr(mod, "PIPELINE_EVENTS_DIR", pipeline_dir)
    monkeypatch.setattr(mod, "ATTRIBUTION_DIR", tmp_path / "report" / "lifecycle_ai_context_attribution")
    pipeline_dir.mkdir(parents=True)
    with gzip.open(pipeline_dir / "pipeline_events_2026-05-20.jsonl.gz", "wt", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {
                    "stage": "ai_result",
                    "fields": {
                        "lifecycle_ai_context_enabled": True,
                        "lifecycle_ai_context_applied": True,
                        "lifecycle_ai_context_stage": "entry",
                        "lifecycle_ai_context_alignment_hint": "WAIT_REQUOTE",
                        "action": "WAIT",
                    },
                }
            )
            + "\n"
        )

    report = mod.build_lifecycle_ai_context_attribution_report("2026-05-20", replay_budget=30)

    assert report["stage_attribution"]["entry"]["context_eligible_count"] == 1
    assert report["implementation_status"] == "implemented"
    assert report["implementation_provenance"]["runtime_effect"] is False
    assert report["implementation_checks"][0]["status"] == "pass"


def test_runtime_context_applies_prompt_fields_without_action_mutation(tmp_path, monkeypatch):
    context_file = tmp_path / "lifecycle_ai_context_2026-05-20.json"
    context_file.write_text(
        json.dumps(
            {
                "date": "2026-05-20",
                "context_version": "lifecycle_ai_context_v1_2026-05-20",
                "stage_contexts": [
                    {
                        "stage": "entry",
                        "prompt_injection_allowed": True,
                        "policy_key": "entry:weighted_adm_v1",
                        "alignment_hint": "WAIT_REQUOTE",
                        "context_text": "[Lifecycle AI Context]\n- stage: entry",
                        "context_hash": "abc123",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        mod,
        "TRADING_RULES",
        replace(
            mod.TRADING_RULES,
            LIFECYCLE_AI_CONTEXT_ENABLED=True,
            LIFECYCLE_AI_CONTEXT_FILE=str(context_file),
            LIFECYCLE_AI_CONTEXT_VERSION="lifecycle_ai_context_v1_2026-05-20",
        ),
    )

    context = mod.build_lifecycle_ai_runtime_context(
        prompt_profile="entry",
        now=datetime.fromisoformat("2026-05-21T09:00:00"),
    )
    merged = mod.merge_lifecycle_ai_context_fields({"action": "BUY", "score": 70}, context)

    assert context["applied"] is True
    assert "stage: entry" in context["prompt_context"]
    assert merged["action"] == "BUY"
    assert merged["lifecycle_ai_context_applied"] is True
    assert merged["lifecycle_ai_context_decision_authority"] == "ai_advisory_prompt_context_only"
