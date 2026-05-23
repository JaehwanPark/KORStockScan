from src.engine.ai_response_contracts import AI_RESPONSE_SCHEMA_REGISTRY


def test_ai_response_schema_registry_covers_required_endpoints():
    assert set(AI_RESPONSE_SCHEMA_REGISTRY) == {
        "entry_v1",
        "entry_price_v1",
        "holding_exit_v1",
        "holding_exit_flow_v1",
        "overnight_v1",
        "condition_entry_v1",
        "condition_exit_v1",
        "threshold_ai_correction_v1",
        "lifecycle_ai_context_v1",
        "lifecycle_bucket_discovery_review_v1",
        "pattern_lab_ai_review_v1",
        "runtime_apply_gap_ai_review_v1",
    }
