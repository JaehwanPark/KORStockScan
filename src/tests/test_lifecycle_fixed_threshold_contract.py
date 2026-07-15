from src.engine.lifecycle_decision_matrix import fixed_threshold_contract


def test_fixed_threshold_contract_classifies_threshold_roles():
    contract = fixed_threshold_contract()

    roles = contract["roles"]
    assert "broker_submit_guard" in roles["hard_safety"]
    assert "BUY_SCORE_THRESHOLD" in roles["baseline_prior"]
    assert (
        "SCALP_ENTRY_LATENCY_MAX_WS_JITTER_MS_FOR_CAUTION" in roles["bounded_tunable"]
    )
    assert "legacy_latency_composite" in roles["legacy_archive"]

    assert contract["priority"][0] == "hard_safety_veto"
    assert "hard_safety_override" in contract["forbidden_uses"]
    assert "score_monotonic_ev_assumption" in contract["forbidden_uses"]
