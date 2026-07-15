from src.engine.ai_response_contracts import (
    AI_RESPONSE_SCHEMA_REGISTRY,
    build_openai_response_text_format,
    swing_ai_structured_output_eval_contract,
)


def test_ai_response_schema_registry_covers_required_endpoints():
    assert set(AI_RESPONSE_SCHEMA_REGISTRY) == {
        "entry_v1",
        "entry_price_v1",
        "holding_exit_v1",
        "holding_score_v2",
        "holding_exit_flow_v1",
        "overnight_v1",
        "condition_entry_v1",
        "condition_exit_v1",
        "swing_model_tier2_review_v1",
        "threshold_ai_correction_v1",
        "lifecycle_ai_context_v1",
        "lifecycle_bucket_discovery_review_v1",
        "swing_lifecycle_bucket_discovery_review_v1",
        "pattern_lab_ai_review_v1",
        "producer_gap_discovery_ai_review_v1",
        "stage_hook_workorder_discovery_ai_review_v1",
        "runtime_apply_gap_ai_review_v1",
        "swing_bottom_rebound_policy_ai_review_v1",
        "one_share_threshold_opportunity_ai_review_v1",
        "swing_ai_structured_output_eval_v1",
    }


def _assert_object_schemas_are_strict(node):
    if not isinstance(node, dict):
        return
    if node.get("type") == "object":
        assert node.get("additionalProperties") is False
        for child in (node.get("properties") or {}).values():
            _assert_object_schemas_are_strict(child)
    if node.get("type") == "array":
        _assert_object_schemas_are_strict(node.get("items"))
    for key in ("anyOf", "oneOf", "allOf"):
        for child in node.get(key) or []:
            _assert_object_schemas_are_strict(child)


def test_openai_text_format_normalizes_response_schemas_for_strict_outputs():
    for schema_name in (
        "entry_v1",
        "entry_price_v1",
        "holding_exit_v1",
        "condition_entry_v1",
    ):
        text_format = build_openai_response_text_format(schema_name)

        assert text_format["type"] == "json_schema"
        assert text_format["strict"] is True
        _assert_object_schemas_are_strict(text_format["schema"])


def test_lifecycle_bucket_discovery_schema_requires_parent_granularity_reviews():
    schema = AI_RESPONSE_SCHEMA_REGISTRY["lifecycle_bucket_discovery_review_v1"]

    assert "parent_granularity_reviews" in schema["properties"]
    assert "parent_granularity_reviews" in schema["required"]


def test_swing_ai_structured_output_eval_contract_is_report_only():
    contract = swing_ai_structured_output_eval_contract()
    provenance = contract["implementation_provenance"]

    assert (
        contract["implementation_status"]
        == "implemented_source_quality_contract_available"
    )
    assert provenance["decision_authority"] == "swing_ai_contract_eval_report_only"
    assert provenance["runtime_effect"] is False
    assert provenance["allowed_runtime_apply"] is False
    assert provenance["actual_order_submitted"] is False
    assert provenance["broker_order_forbidden"] is True
    assert {item["variant_id"] for item in provenance["prompt_variants"]} == {
        "korean_free_text_gatekeeper",
        "english_control_entry_json",
        "strict_schema_structured_eval",
    }
