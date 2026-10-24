"""Permanent retirement remains neutral despite legacy files and flags."""

from datetime import datetime
import pytest
from src.engine import lifecycle_ai_context as compatibility
from src.engine.ai import retired_lifecycle_context as neutral


@pytest.mark.parametrize(
    "producer",
    [
        compatibility.build_lifecycle_ai_context_report,
        compatibility.build_lifecycle_ai_context_attribution_report,
    ],
)
def test_retired_report_has_no_storage_or_provider_access(
    tmp_path, monkeypatch, producer
):
    prior = tmp_path / "legacy.json"
    prior.write_text('{"stage_contexts":[{"alignment_hint":"BUY"}]}')

    def forbidden(*args, **kwargs):
        raise AssertionError("retired report attempted storage access")

    monkeypatch.setattr(type(prior), "read_text", forbidden)
    monkeypatch.setattr(type(prior), "write_text", forbidden)
    result = producer("2026-10-12")
    assert result["status"] == "retired" and result["runtime_effect"] is False


@pytest.mark.parametrize("stage", ["entry", "submit", "holding", "scale_in", "exit"])
def test_neutral_context_preserves_action_and_has_no_prompt_authority(stage):
    context = neutral.build_lifecycle_ai_runtime_context(
        prompt_profile=stage,
        stage=stage,
        now=datetime.fromisoformat("2026-10-12T09:00:00+09:00"),
    )
    before = dict(action="SELL", score=72, rationale="original")
    merged = neutral.merge_lifecycle_ai_context_fields(before, context)
    assert all(merged[k] == v for k, v in before.items())
    assert context["applied"] is False and context["prompt_context"] == ""
    assert merged["lifecycle_ai_context_stage"] == stage
    assert merged["lifecycle_ai_context_alignment_hint"] == "NO_CHANGE"
    assert merged["lifecycle_ai_context_actual_order_submitted"] is False
