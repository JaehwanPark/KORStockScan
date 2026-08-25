from __future__ import annotations

import hashlib
import json
import sys
from types import SimpleNamespace

import pytest

from src.engine.scalping import ai_decision_quality as quality
from src.tests.test_ai_decision_quality import (
    _micro_reversion_materialization_fixture,
    _reseal_current_materialized_report,
)


def _materialized_report() -> dict:
    prepared, source_bundle = _micro_reversion_materialization_fixture()
    return quality.materialize_micro_reversion_offline_requests(
        prepared_requests=prepared,
        bridge_source_bundle=source_bundle,
    )


def _requests_by_arm(report: dict) -> dict[str, dict]:
    return {
        str(request["micro_reversion_replay_arm"]): request
        for request in report["requests"]
    }


@pytest.mark.parametrize(
    "field,value",
    (
        ("candidate_schema_correction_errors", ["expected_edge_values_required"]),
        ("offline_provider_attempt_number", 1),
    ),
)
def test_current_materialized_report_rejects_resealed_execution_transient_field(
    field: str,
    value: object,
) -> None:
    report = _materialized_report()
    candidate = _requests_by_arm(report)[
        "replay_candidate_exact_plus_micro_ask_depletion"
    ]
    candidate[field] = value
    _reseal_current_materialized_report(report)

    with pytest.raises(
        ValueError,
        match="micro_reversion_execution_transient_field_persisted",
    ):
        quality._validate_micro_reversion_materialized_report(report)


def test_current_materialized_report_rejects_resealed_extra_feature_axis() -> None:
    report = _materialized_report()
    ask_control = _requests_by_arm(report)[
        "replay_control_exact_plus_micro_ask_depletion"
    ]
    ask_control["uncontracted_feature_axis"] = "second-axis"
    _reseal_current_materialized_report(report)

    with pytest.raises(
        ValueError,
        match="micro_reversion_materialized_feature_only_delta_invalid",
    ):
        quality._validate_micro_reversion_materialized_report(report)


def test_current_materialized_report_rejects_resealed_extra_prompt_axis() -> None:
    report = _materialized_report()
    candidate = _requests_by_arm(report)[
        "replay_candidate_exact_plus_micro_ask_depletion"
    ]
    candidate["candidate"]["persisted_retry_hint"] = "provider-visible"
    _reseal_current_materialized_report(report)

    with pytest.raises(
        ValueError,
        match="micro_reversion_materialized_prompt_only_delta_invalid",
    ):
        quality._validate_micro_reversion_materialized_report(report)


def test_current_materialized_delta_accepts_response_schema_application_axis() -> None:
    report = _materialized_report()
    by_arm = _requests_by_arm(report)
    for arm in (
        "replay_control_exact_plus_micro",
        "replay_control_exact_plus_micro_ask_depletion",
    ):
        contract = by_arm[arm]["candidate"]
        contract["response_schema_application"] = "provider_json_object_openai"
        contract["contract_sha256"] = quality._candidate_contract_sha256(contract)

    quality._validate_current_micro_reversion_ablation_deltas(by_arm)


def test_current_materialized_report_rejects_same_prompt_body_with_role_hashes() -> (
    None
):
    report = _materialized_report()
    by_arm = _requests_by_arm(report)
    control_prompt = by_arm["replay_control_exact_plus_micro_ask_depletion"][
        "candidate"
    ]
    candidate_prompt = by_arm["replay_candidate_exact_plus_micro_ask_depletion"][
        "candidate"
    ]
    candidate_prompt["system_prompt"] = control_prompt["system_prompt"]
    # Candidate contracts historically hash string values through canonical
    # JSON, while stored control prompts use raw UTF-8.  Reproduce that forged
    # but internally valid role-specific declaration.
    candidate_prompt["system_prompt_sha256"] = quality._sha256(
        candidate_prompt["system_prompt"]
    )
    candidate_prompt["contract_sha256"] = quality._candidate_contract_sha256(
        candidate_prompt
    )
    _reseal_current_materialized_report(report)

    with pytest.raises(
        ValueError,
        match="micro_reversion_materialized_prompt_body_not_distinct",
    ):
        quality._validate_micro_reversion_materialized_report(report)


def test_openai_three_arm_requests_share_parent_key_slot(monkeypatch) -> None:
    selected_keys: list[str] = []

    class FakeResponses:
        def create(self, **_kwargs):
            return SimpleNamespace(
                id="response-key-routing",
                output_text=json.dumps({}),
                usage=SimpleNamespace(
                    input_tokens=1,
                    output_tokens=1,
                    total_tokens=2,
                ),
            )

    class FakeOpenAI:
        def __init__(self, *, api_key, max_retries):
            selected_keys.append(api_key)
            assert max_retries == 0
            self.responses = FakeResponses()

    monkeypatch.setitem(sys.modules, "openai", SimpleNamespace(OpenAI=FakeOpenAI))
    api_keys = ["key-0", "key-1", "key-2", "key-3"]
    parent_id = "same-ablation-parent"
    for arm_index in range(3):
        quality.execute_openai_prompt_v2_candidate(
            {
                "paired_replay_parent_id": parent_id,
                "paired_replay_id": f"{parent_id}:arm-{arm_index}",
                "stage": "entry",
                "exact_payload": {"arm_index": arm_index},
                "control": {"provider": "openai", "model": "gpt-test"},
                "candidate": {
                    "provider": "openai",
                    "model": "gpt-test",
                    "reasoning_effort": "minimal",
                    "system_prompt": "Return JSON.",
                    "max_output_tokens": 100,
                },
                **quality.OFFLINE_CONTRACT,
            },
            api_keys=api_keys,
        )

    expected_index = int(
        hashlib.sha256(parent_id.encode("utf-8")).hexdigest(), 16
    ) % len(api_keys)
    assert selected_keys == [api_keys[expected_index]] * 3
