import json
from types import SimpleNamespace

from src.engine import swing_lifecycle_audit as mod


def test_swing_entry_bottleneck_classifies_submit_zero_with_blockers():
    bottleneck = mod.build_swing_entry_bottleneck(
        {
            "raw_counts": {
                "blocked_gatekeeper_reject": 113,
                "blocked_swing_score_vpw": 80,
                "blocked_swing_gap": 58,
            },
            "unique_record_counts": {
                "blocked_gatekeeper_reject": 11,
                "blocked_swing_score_vpw": 9,
                "blocked_swing_gap": 9,
                "swing_probe_entry_candidate": 12,
            },
            "group_unique_counts": {"entry": 15},
            "submitted_unique_records": 0,
            "simulated_order_unique_records": 0,
            "gatekeeper_actions": {"눌림 대기": 113},
            "cooldown_policies": {"pullback_wait": 113},
            "ofi_qi_summary": {
                "stale_missing_ratio": 0.91,
                "stale_missing_group_unique_record_counts": {"entry": 12},
            },
        }
    )

    assert bottleneck["primary"] == "SWING_ENTRY_DROUGHT_CRITICAL"
    assert bottleneck["operator_action_required"] is False
    assert bottleneck["runtime_effect"] is False
    assert bottleneck["allowed_runtime_apply"] is False
    assert "GATEKEEPER_PULLBACK_WAIT" in bottleneck["matches"]
    assert "SUBMIT_ZERO" in bottleneck["matches"]
    assert bottleneck["next_route"] == "code_improvement_workorder"


def test_swing_threshold_openai_review_uses_individual_mini_model(monkeypatch):
    captured = {}

    class _FakeResponses:
        def create(self, **kwargs):
            captured.update(kwargs)
            return SimpleNamespace(output_text=json.dumps({"items": []}), usage=SimpleNamespace())

    class _FakeOpenAI:
        def __init__(self, api_key):
            self.responses = _FakeResponses()

    monkeypatch.setattr("src.engine.daily_threshold_cycle_report._load_threshold_ai_openai_keys", lambda: [("OPENAI_API_KEY", "key")])
    monkeypatch.setattr("openai.OpenAI", _FakeOpenAI)

    _, status = mod._call_openai_swing_threshold_review({"date": "2026-05-27", "candidates": []})

    assert status["model"] == "gpt-5.4-mini"
    assert status["attempted_models"] == ["gpt-5.4-mini"]
    assert status["reasoning_effort"] == "medium"
    assert status["timeout_sec"] == 180
    assert captured["model"] == "gpt-5.4-mini"
    assert captured["reasoning"]["effort"] == "medium"
    assert captured["timeout"] == 180


def test_swing_entry_bottleneck_dry_run_submit_zero_is_not_critical():
    bottleneck = mod.build_swing_entry_bottleneck(
        {
            "raw_counts": {
                "blocked_gatekeeper_reject": 113,
                "blocked_swing_score_vpw": 80,
                "blocked_swing_gap": 58,
                "swing_sim_order_bundle_assumed_filled": 20,
            },
            "unique_record_counts": {
                "blocked_gatekeeper_reject": 11,
                "blocked_swing_score_vpw": 9,
                "blocked_swing_gap": 9,
                "swing_probe_entry_candidate": 12,
                "swing_sim_order_bundle_assumed_filled": 20,
            },
            "group_unique_counts": {"entry": 15},
            "submitted_unique_records": 0,
            "simulated_order_unique_records": 20,
            "gatekeeper_actions": {"눌림 대기": 113},
            "cooldown_policies": {"pullback_wait": 113},
            "ofi_qi_summary": {
                "stale_missing_ratio": 0.91,
                "stale_missing_group_unique_record_counts": {"entry": 0, "holding": 40, "exit": 20},
                "entry_micro_state_counts": {"READY": 5},
            },
        }
    )

    assert bottleneck["primary"] == "SWING_ENTRY_BOTTLENECK_OBSERVE"
    assert bottleneck["critical"] is False
    assert "SUBMIT_ZERO" not in bottleneck["matches"]
    assert "ENTRY_MICRO_CONTEXT_GAP" not in bottleneck["matches"]
    assert bottleneck["counts"]["submitted_zero_ignored_for_dry_run"] is True
    assert bottleneck["counts"]["dry_run_equivalent_submit_unique"] == 20


def test_entry_micro_context_gap_ignores_holding_exit_stale_ratio():
    bottleneck = mod.build_swing_entry_bottleneck(
        {
            "raw_counts": {},
            "unique_record_counts": {"swing_probe_entry_candidate": 15},
            "group_unique_counts": {"entry": 15, "holding": 30, "exit": 30},
            "submitted_unique_records": 0,
            "simulated_order_unique_records": 20,
            "ofi_qi_summary": {
                "stale_missing_ratio": 0.95,
                "stale_missing_group_unique_record_counts": {"holding": 30, "exit": 30},
                "entry_micro_state_counts": {"READY": 6},
                "holding_micro_state_counts": {"MISSING": 30},
            },
        }
    )

    assert "ENTRY_MICRO_CONTEXT_GAP" not in bottleneck["matches"]
    assert bottleneck["entry_micro_context"]["global_stale_missing_ratio"] == 0.95
    assert bottleneck["entry_micro_context"]["entry_micro_context_gap"] is False


def test_market_regime_prior_alone_does_not_create_entry_drought_critical():
    bottleneck = mod.build_swing_entry_bottleneck(
        {
            "raw_counts": {"market_regime_block": 100},
            "unique_record_counts": {"market_regime_block": 15},
            "group_unique_counts": {"entry": 15},
            "submitted_unique_records": 0,
            "simulated_order_unique_records": 0,
            "ofi_qi_summary": {},
        }
    )

    assert bottleneck["primary"] == "SWING_ENTRY_BOTTLENECK_OBSERVE"
    assert bottleneck["critical"] is False
    assert bottleneck["counts"]["hard_blocker_unique_total"] == 0
    assert bottleneck["counts"]["legacy_prior_event_counts"]["market_regime_block_unique"] == 15


def test_lifecycle_summary_counts_market_regime_prior_reasons():
    summary = mod.summarize_lifecycle_events(
        [
            {
                "stage": "market_regime_prior_observed",
                "record_id": "r1",
                "stock_code": "000001",
                "fields": {
                    "strategy": "KOSPI_ML",
                    "market_regime_prior_reason": "oil_only_recovery_signal_insufficient",
                },
            },
            {
                "stage": "market_regime_block",
                "record_id": "r2",
                "stock_code": "000002",
                "fields": {"strategy": "KOSPI_ML", "market_regime_block_reason": "confirmed_risk_context"},
            },
        ]
    )

    assert summary["raw_counts"]["market_regime_prior_observed"] == 1
    assert summary["raw_counts"]["market_regime_block"] == 1
    assert summary["market_regime_prior_reason_counts"] == {
        "oil_only_recovery_signal_insufficient": 1
    }


def test_lifecycle_summary_ignores_legacy_phase0_real_canary_receipts():
    summary = mod.summarize_lifecycle_events(
        [
            {
                "stage": "swing_one_share_real_canary_blocked",
                "record_id": "r1",
                "stock_code": "000001",
                "fields": {
                    "strategy": "KOSPI_ML",
                    "actual_order_submitted": True,
                },
            },
            {
                "stage": "swing_scale_in_real_canary_order_submitted",
                "record_id": "r2",
                "stock_code": "000002",
                "fields": {
                    "strategy": "KOSPI_ML",
                    "add_type": "PYRAMID",
                    "actual_order_submitted": True,
                },
            },
            {
                "stage": "swing_scale_in_micro_context_observed",
                "record_id": "r3",
                "stock_code": "000003",
                "fields": {
                    "strategy": "KOSPI_ML",
                    "add_type": "PYRAMID",
                    "actual_order_submitted": False,
                },
            },
        ]
    )

    assert summary["raw_counts"]["swing_scale_in_micro_context_observed"] == 1
    assert "swing_one_share_real_canary_blocked" not in summary["raw_counts"]
    assert "swing_scale_in_real_canary_order_submitted" not in summary["raw_counts"]
    assert summary["actual_order_submitted_flags"] == {"false": 1}
    assert summary["scale_in_observation"]["action_groups"] == {"PYRAMID": 1}
    assert summary["scale_in_observation"]["legacy_phase0_real_canary_receipts_ignored"] == {
        "swing_one_share_real_canary_blocked": 1,
        "swing_scale_in_real_canary_order_submitted": 1,
    }


def test_swing_improvement_automation_adds_entry_bottleneck_order():
    audit = {
        "date": "2026-05-22",
        "model_selection": {},
        "recommendation_csv": {},
        "db_lifecycle": {},
        "recommendation_db_load": {},
        "lifecycle_events": {
            "raw_counts": {},
            "unique_record_counts": {"blocked_gatekeeper_reject": 11},
            "group_unique_counts": {"entry": 15, "scale_in": 1},
            "ofi_qi_summary": {},
            "scale_in_observation": {"post_add_outcomes": {"observed": 1}},
            "ai_contract_metrics": {},
        },
        "swing_entry_bottleneck": {
            "primary": "SWING_ENTRY_DROUGHT_CRITICAL",
            "matches": ["GATEKEEPER_PULLBACK_WAIT", "SUBMIT_ZERO"],
            "counts": {
                "entry_unique": 15,
                "submitted_unique_records": 0,
                "blocker_unique_total": 11,
            },
            "ratios": {"probe_to_blocked_unique_pct": 0.0},
            "gatekeeper_actions": {"눌림 대기": 11},
        },
        "swing_lifecycle_contract_gaps": {"gap_count": 0, "gaps": []},
        "observation_axis_summary": {},
        "simulation_opportunity": {},
    }

    report = mod.build_swing_improvement_automation_report(audit)

    order = next(
        item
        for item in report["code_improvement_orders"]
        if item["order_id"] == "order_swing_entry_bottleneck_auto_resolution"
    )
    assert order["priority"] == 0
    assert order["decision_hint"] == "implement_now"
    assert order["mapped_family"] == "swing_gatekeeper_accept_reject"
    assert order["runtime_effect"] is False
    assert order["allowed_runtime_apply"] is False
    assert report["swing_entry_bottleneck"]["primary"] == "SWING_ENTRY_DROUGHT_CRITICAL"


def test_swing_improvement_automation_surfaces_downstream_contract_gap_orders():
    audit = {
        "date": "2026-05-22",
        "model_selection": {},
        "recommendation_csv": {},
        "db_lifecycle": {},
        "recommendation_db_load": {},
        "lifecycle_events": {
            "raw_counts": {},
            "unique_record_counts": {},
            "group_unique_counts": {"holding": 3, "exit": 2, "scale_in": 1},
            "ofi_qi_summary": {},
            "scale_in_observation": {},
            "ai_contract_metrics": {},
        },
        "swing_entry_bottleneck": {
            "primary": "SWING_ENTRY_BOTTLENECK_OBSERVE",
            "matches": [],
        },
        "swing_lifecycle_contract_gaps": {
            "gap_count": 3,
            "gaps": [
                {"gap_id": "SWING_HOLDING_EXIT_CONTRACT_GAP", "next_route": "code_improvement_workorder"},
                {"gap_id": "SWING_SCALE_IN_CONTRACT_GAP", "next_route": "code_improvement_workorder"},
                {"gap_id": "SWING_DISCOVERY_LABEL_CONTRACT_GAP", "next_route": "source_quality_workorder"},
            ],
        },
        "observation_axis_summary": {},
        "simulation_opportunity": {},
    }

    report = mod.build_swing_improvement_automation_report(audit)
    order_ids = {item["order_id"] for item in report["code_improvement_orders"]}

    assert "order_swing_holding_exit_contract_gap_review" in order_ids
    assert "order_swing_scale_in_contract_gap_review" in order_ids
    assert "order_swing_discovery_label_contract_gap_review" in order_ids
    assert all(
        item["runtime_effect"] is False and item["allowed_runtime_apply"] is False
        for item in report["code_improvement_orders"]
        if item["order_id"] in {
            "order_swing_holding_exit_contract_gap_review",
            "order_swing_scale_in_contract_gap_review",
            "order_swing_discovery_label_contract_gap_review",
        }
    )
    for order_id in {
        "order_swing_holding_exit_contract_gap_review",
        "order_swing_scale_in_contract_gap_review",
        "order_swing_discovery_label_contract_gap_review",
    }:
        order = next(item for item in report["code_improvement_orders"] if item["order_id"] == order_id)
        assert order["implementation_status"] == "implemented"
        assert order["implementation_provenance"]["source_contract"] == "swing_lifecycle_contract_gap_v1"
        assert order["implementation_provenance"]["runtime_effect"] is False


def test_swing_improvement_automation_marks_ofi_qi_instrumentation_implemented():
    audit = {
        "date": "2026-05-22",
        "model_selection": {},
        "recommendation_csv": {},
        "db_lifecycle": {},
        "recommendation_db_load": {},
        "lifecycle_events": {
            "raw_counts": {},
            "unique_record_counts": {},
            "group_unique_counts": {"entry": 2},
            "ofi_qi_summary": {
                "stale_missing_count": 1,
                "stale_missing_ratio": 0.5,
                "stale_missing_unique_record_count": 1,
                "stale_missing_reason_counts": {"micro_missing": 1},
                "stale_missing_reason_combination_counts": {"micro_missing": 1},
                "stale_missing_reason_combination_unique_record_counts": {"micro_missing": 1},
                "stale_missing_group_counts": {"entry": 1},
                "stale_missing_group_unique_record_counts": {"entry": 1},
                "stale_missing_reason_counts_by_group": {"entry": {"micro_missing": 1}},
                "stale_missing_reason_unique_record_counts_by_group": {"entry": {"micro_missing": 1}},
                "observer_unhealthy_overlap": {
                    "observer_unhealthy_total": 0,
                    "observer_unhealthy_with_other_reason": 0,
                    "observer_unhealthy_only": 0,
                },
                "orderbook_micro_reason_counts_by_group": {"entry": {"micro_context_missing": 1}},
                "observer_missing_reason_counts_by_group": {"entry": {"UNKNOWN": 1}},
                "source_quality_status_counts_by_group": {"entry": {"source_quality_blocker": 1}},
                "ws_quote_source_counts_by_group": {"entry": {"missing": 1}},
                "ws_quote_stale_counts_by_group": {"entry": {"not_available_no_quote_age": 1}},
                "stale_missing_examples": [{"record_id": "r1"}],
                "entry_micro_state_counts": {"insufficient": 1, "bullish": 1},
                "scale_in_micro_state_counts": {},
                "exit_micro_state_counts": {},
            },
            "scale_in_observation": {},
            "ai_contract_metrics": {},
        },
        "swing_entry_bottleneck": {
            "primary": "SWING_ENTRY_BOTTLENECK_OBSERVE",
            "matches": [],
        },
        "swing_lifecycle_contract_gaps": {"gap_count": 0, "gaps": []},
        "observation_axis_summary": {},
        "simulation_opportunity": {},
    }

    report = mod.build_swing_improvement_automation_report(audit)
    order = next(
        item
        for item in report["code_improvement_orders"]
        if item["order_id"] == "order_swing_ofi_qi_stale_or_missing_context"
    )

    assert order["implementation_status"] == "implemented"
    assert order["implementation_provenance"]["source_contract"] == "swing_orderbook_micro_context_v2"
    assert order["implementation_provenance"]["group"] == "entry"
    assert order["implementation_provenance"]["root_cause_closure_status_hint"] == "root_cause_closed"
    assert order["implementation_provenance"]["runtime_effect"] is False
    assert (
        order["implementation_provenance"]["root_cause_dimensions"]["orderbook_micro_reason_counts_by_group"]
        == {"micro_context_missing": 1}
    )
