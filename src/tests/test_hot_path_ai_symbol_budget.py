from src.engine.ai.hot_path_ai_symbol_budget import HotPathAISymbolBudget


def test_symbol_budget_enforces_shared_total_and_endpoint_group_caps():
    budget = HotPathAISymbolBudget(window_sec=60, total_cap=4, group_cap=2)

    first_entry = budget.reserve(code="087010", endpoint="scanner_entry", now_ts=100.0)
    second_entry = budget.reserve(
        code="087010", endpoint="rising_missed_entry", now_ts=110.0
    )
    third_entry = budget.reserve(code="087010", endpoint="scanner_entry", now_ts=120.0)
    first_holding = budget.reserve(
        code="087010", endpoint="holding_score", now_ts=121.0
    )
    first_scale_in = budget.reserve(
        code="087010", endpoint="scale_in_holding_score", now_ts=122.0
    )
    over_total = budget.reserve(code="087010", endpoint="other_live_ai", now_ts=123.0)

    assert first_entry.allowed is True
    assert second_entry.allowed is True
    assert third_entry.allowed is False
    assert third_entry.reason == "endpoint_group_window_cap"
    assert first_holding.allowed is True
    assert first_scale_in.allowed is True
    assert over_total.allowed is False
    assert over_total.reason == "symbol_window_cap"


def test_symbol_budget_groups_holding_and_scale_in_and_enforces_interval():
    budget = HotPathAISymbolBudget(window_sec=60, total_cap=4, group_cap=2)

    first = budget.reserve(
        code="087010",
        endpoint="holding_score",
        now_ts=100.0,
        min_interval_sec=30.0,
    )
    too_soon = budget.reserve(
        code="087010",
        endpoint="scale_in_holding_score",
        now_ts=120.0,
        min_interval_sec=30.0,
    )
    after_interval = budget.reserve(
        code="087010",
        endpoint="scale_in_holding_score",
        now_ts=131.0,
        min_interval_sec=30.0,
    )

    assert first.allowed is True
    assert too_soon.allowed is False
    assert too_soon.reason == "endpoint_min_interval"
    assert after_interval.allowed is True


def test_symbol_budget_prunes_expired_calls_and_keeps_symbols_independent():
    budget = HotPathAISymbolBudget(window_sec=60, total_cap=1, group_cap=1)

    assert budget.reserve(code="087010", endpoint="scanner_entry", now_ts=100.0).allowed
    assert budget.reserve(code="000660", endpoint="scanner_entry", now_ts=101.0).allowed
    assert not budget.reserve(
        code="087010", endpoint="holding_score", now_ts=159.9
    ).allowed
    assert budget.reserve(code="087010", endpoint="holding_score", now_ts=160.0).allowed


def test_inspect_does_not_retain_empty_symbol_state():
    budget = HotPathAISymbolBudget(window_sec=60, total_cap=4, group_cap=2)

    decision = budget.inspect(
        code="005930",
        endpoint="holding_score",
        now_ts=100.0,
    )

    assert decision.allowed is True
    assert "005930" not in budget._events


def test_release_refunds_only_the_exact_endpoint_group_reservation():
    budget = HotPathAISymbolBudget(window_sec=60, total_cap=4, group_cap=2)
    assert budget.reserve(code="198440", endpoint="scanner_entry", now_ts=100.0).allowed
    assert budget.reserve(code="198440", endpoint="scanner_entry", now_ts=110.0).allowed

    assert budget.release(
        code="198440",
        endpoint="scanner_entry",
        reserved_at=100.0,
    )
    assert not budget.release(
        code="198440",
        endpoint="scanner_entry",
        reserved_at=100.0,
    )
    assert budget.reserve(code="198440", endpoint="scanner_entry", now_ts=120.0).allowed


def test_release_rejects_invalid_or_mismatched_reservations_without_mutation():
    budget = HotPathAISymbolBudget(window_sec=60, total_cap=4, group_cap=2)
    assert budget.reserve(code="198440", endpoint="scanner_entry", now_ts=100.0).allowed

    assert not budget.release(
        code="198440",
        endpoint="holding_score",
        reserved_at=100.0,
    )
    assert not budget.release(
        code="198440",
        endpoint="scanner_entry",
        reserved_at="not-a-timestamp",
    )
    assert (
        budget.inspect(
            code="198440",
            endpoint="scanner_entry",
            now_ts=101.0,
        ).group_count
        == 1
    )


def test_symbol_budget_log_contract_declares_bounded_cadence_effect():
    budget = HotPathAISymbolBudget(window_sec=60, total_cap=4, group_cap=2)
    fields = budget.inspect(
        code="087010", endpoint="scanner_entry", now_ts=100.0
    ).log_fields()

    assert fields["hot_path_ai_symbol_budget_metric_role"] == ("ops_volume_diagnostic")
    assert fields["hot_path_ai_symbol_budget_decision_authority"] == (
        "ai_call_cadence_only"
    )
    assert fields["hot_path_ai_symbol_budget_runtime_effect"] is True
    assert fields["hot_path_ai_symbol_budget_allowed_runtime_apply"] is False
    assert "broker_guard_bypass" in fields["hot_path_ai_symbol_budget_forbidden_uses"]
