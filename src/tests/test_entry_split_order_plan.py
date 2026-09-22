from __future__ import annotations

import json
import os
import hashlib

import pytest
from datetime import date, datetime, timezone, timedelta

from src.engine.scalping import entry_split_order_plan as split_plan
from src.engine import sniper_post_sell_feedback as post_sell_feedback


def test_acknowledged_entry_leg_merges_duplicate_policy_receipts():
    """Execute the real post-ack logging expression without a broker call."""
    import ast
    import textwrap
    from pathlib import Path
    from src.engine import sniper_state_handlers as handlers
    source = Path(handlers.__file__).read_text()
    expression = source.split('        entry_submit_event = _log_entry_pipeline(', 1)[1]
    expression = 'entry_submit_event = _log_entry_pipeline(' + expression.split(
        '        _record_lifecycle_submit_telemetry_if_raw_appended(', 1)[0]
    tree = ast.parse(textwrap.dedent(expression))
    stock = dict(entry_split_order_policy_sha256='old', entry_split_order_runtime_pid=1,
                 entry_split_order_runtime_consumed=True, market_session_bucket='KRX_REGULAR')
    env = dict(stock=stock, code='000001', request={'tag':'primary'}, qty=2,
        ord_no='acknowledged-1', price=1000, order_sent_ts=1790036000,
        datetime=datetime, _KST=timezone(timedelta(hours=9)),
        order_resolution_fields={'broker_route':'KRX'}, entry_execution_cohort='KRX',
        split_leg_meta_fields={**stock, 'entry_split_order_policy_sha256':'leg-policy'},
        real_pre_submit_guard_fields={}, submit_revalidation_fields={},
        _entry_price_ai_trace_fields=lambda _: {},
        _merge_entry_pipeline_field_groups=handlers._merge_entry_pipeline_field_groups,
        _log_entry_pipeline=lambda *args, **fields: fields)
    # The session field belongs to the explicit event, not split metadata.
    env['split_leg_meta_fields'].pop('market_session_bucket')
    exec(compile(tree, '<post-ack-entry-log>', 'exec'), env)
    event = env['entry_submit_event']
    assert event['entry_split_order_policy_sha256'] == 'leg-policy'
    assert event['entry_split_order_runtime_pid'] == 1
    assert event['broker_order_no'] == 'acknowledged-1'
    assert event['actual_order_submitted'] is True
    assert event['broker_order_forbidden'] is False


@pytest.fixture(autouse=True)
def isolate_native_replay_generation(monkeypatch, tmp_path):
    """Mock windows must not fingerprint a growing production collector."""
    from src.engine.monitoring import machine_microstructure_attribution as micro
    monkeypatch.setattr(micro, "OBSERVATION_ROOT", tmp_path / "native_observations")
    monkeypatch.setattr(micro, "DEFAULT_SOURCE_EXCLUSION_MANIFEST", tmp_path / "exclusions.json")
    monkeypatch.setattr(micro, "DEFAULT_CANARY_SNAPSHOT_PATH", tmp_path / "canary.json")
    monkeypatch.setattr(micro, "CANARY_DAILY_SNAPSHOT_DIR", tmp_path / "canary_daily")


def _quantity_leg_four_arm_events():
    events = []
    for index in range(30):
        source_date = "2026-09-14" if index < 20 else "2026-09-15"

        def arm(net_return, pnl, capital, fill):
            return {
                "net_return_pct": net_return,
                "net_pnl_krw": pnl,
                "capital_krw_minutes": capital,
                "fill_participation_rate": fill,
                "terminal_conservation_holds": True,
                "cost_complete": True,
                "counterfactual_executable": True,
                "entry_price_receipt_sha256": "d" * 64,
                "exit_policy_sha256": "e" * 64,
                "cost_contract_sha256": "f" * 64,
                "terminal_contract_version": "same-terminal-v1",
                "terminal_observed_at": "2026-09-15T10:30:00+09:00",
            }

        receipt = {
            "schema": split_plan.QUANTITY_LEG_FOUR_ARM_SCHEMA,
            "source_date": source_date,
            "scanner_promotion_id": f"promotion-{index}",
            "evaluation_attempt_id": f"attempt-{index}",
            "stock_code": "005930",
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "policy_bundle_sha256": "a" * 64,
            "eligible_attempt_count": 20 if index < 20 else 10,
            "incumbent_quantity_policy_version": "qty-current",
            "candidate_quantity_policy_version": "qty-candidate",
            "incumbent_leg_policy_version": "leg-current",
            "candidate_leg_policy_version": "leg-candidate",
            "entry_price_policy_sha256": "c" * 64,
            "arms": {
                "incumbent_qty_x_incumbent_leg": arm(0.08, 80, 10, 0.90),
                "candidate_qty_x_incumbent_leg": arm(0.11, 110, 9, 0.92),
                "incumbent_qty_x_candidate_leg": arm(0.12, 120, 8, 0.93),
                "candidate_qty_x_candidate_leg": arm(0.15, 150, 7, 0.95),
            },
        }
        receipt["receipt_sha256"] = hashlib.sha256(
            json.dumps(
                receipt, ensure_ascii=True, sort_keys=True, separators=(",", ":")
            ).encode("ascii")
        ).hexdigest()
        events.append({"entry_quantity_leg_four_arm_evaluation": receipt})

    return events


def test_quantity_leg_four_arm_requires_same_attempt_and_cost_adjusted_edge():
    result = split_plan.build_quantity_leg_four_arm_evaluation(_quantity_leg_four_arm_events())

    assert result["complete_exact_attempt_count"] == 30
    assert result["exact_attempt_join_coverage"] == 1.0
    assert result["promotion_gate"]["passed"] is True
    assert result["arms"]["candidate_qty_x_candidate_leg"][
        "cost_adjusted_net_ev_pct"
    ] == pytest.approx(0.15)
    assert result["incremental_effects"]["combined_net_ev_delta_pct"] == (
        pytest.approx(0.07)
    )
    assert result["promotion_gate"]["applies_to"] == (
        "challenger_automatic_promotion_only"
    )
    assert (
        result["promotion_gate"]["initial_baseline_activation_blocked_by_this_gate"]
        is False
    )


def _resign_four_arm_receipt(receipt):
    body = {key: value for key, value in receipt.items() if key != "receipt_sha256"}
    receipt["receipt_sha256"] = hashlib.sha256(
        json.dumps(body, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode("ascii")
    ).hexdigest()


def test_four_arm_chronology_and_independent_selection_validation():
    evaluation = split_plan.build_quantity_leg_four_arm_evaluation(_quantity_leg_four_arm_events())
    assert split_plan.quantity_leg_promotion_evidence_valid(evaluation)
    assert evaluation["chronological_partitions"]["calibration"]["complete_exact_attempt_count"] == 20
    assert evaluation["chronological_partitions"]["holdout"]["complete_exact_attempt_count"] == 10
    for field, value in (("exact_attempt_join_coverage", True),
                         ("complete_exact_attempt_count", True),
                         ("selection_contract", "legacy")):
        assert not split_plan.quantity_leg_promotion_evidence_valid({**evaluation, field: value})




@pytest.mark.parametrize("mode", ["unsigned", "one_date", "losing_holdout", "small_positive_holdout"])
def test_four_arm_holdout_not_replaced_by_aggregate_or_extra_absolute_floor(mode):
    events = _quantity_leg_four_arm_events()
    for index, event in enumerate(events):
        receipt = event["entry_quantity_leg_four_arm_evaluation"]
        if mode == "unsigned":
            receipt.pop("source_date")
            receipt["eligible_attempt_count"] = 30
        elif mode == "one_date":
            receipt["source_date"] = "2026-09-15"
            receipt["eligible_attempt_count"] = 30
        elif index >= 20:
            receipt["arms"][split_plan.QUANTITY_LEG_FOUR_ARM_IDS[-1]].update(
                net_return_pct=-0.01 if mode == "losing_holdout" else 0.09,
                net_pnl_krw=-10 if mode == "losing_holdout" else 90)
        _resign_four_arm_receipt(receipt)
    evaluation = split_plan.build_quantity_leg_four_arm_evaluation(events)
    assert evaluation["complete_exact_attempt_count"] == 30
    assert evaluation["promotion_gate"]["passed"] is (mode == "small_positive_holdout")
    evaluation["promotion_gate"]["passed"] = True
    evaluation["promotion_gate"]["blockers"] = []
    assert split_plan.quantity_leg_promotion_evidence_valid(evaluation) is (mode == "small_positive_holdout")


@pytest.mark.parametrize("tamper", ["count", "future_date", "aggregate", "hash", "arm_count", "nonfinite"])
def test_four_arm_independent_validator_rejects_tampered_evidence(tamper):
    evaluation = split_plan.build_quantity_leg_four_arm_evaluation(_quantity_leg_four_arm_events())
    holdout = evaluation["chronological_partitions"]["holdout"]
    if tamper == "count":
        holdout["complete_exact_attempt_count"] += 1
    elif tamper == "future_date":
        holdout["source_dates"] = ["2099-01-01"]
    elif tamper == "aggregate":
        evaluation["arms"][split_plan.QUANTITY_LEG_FOUR_ARM_IDS[-1]]["net_pnl_krw"] += 1
    elif tamper == "hash":
        evaluation["validated_source_receipt_sha256s"][1] = evaluation["validated_source_receipt_sha256s"][0]
    elif tamper == "arm_count":
        holdout["arms"][split_plan.QUANTITY_LEG_FOUR_ARM_IDS[-1]]["paired_sample_count"] = True
    else:
        holdout["arms"][split_plan.QUANTITY_LEG_FOUR_ARM_IDS[-1]]["net_pnl_krw"] = float("nan")
    assert not split_plan.quantity_leg_promotion_evidence_valid(evaluation)


@pytest.mark.parametrize("field,value", [
    ("net_return_pct", float("nan")),
    ("net_pnl_krw", float("inf")),
    ("capital_krw_minutes", -1),
    ("capital_krw_minutes", 0),
    ("fill_participation_rate", 1.1),
    ("fill_participation_rate", -0.1),
    ("net_return_pct", True),
])
def test_four_arm_quarantines_invalid_economics(field, value):
    events = _quantity_leg_four_arm_events()
    receipt = events[0]["entry_quantity_leg_four_arm_evaluation"]
    receipt["arms"][split_plan.QUANTITY_LEG_FOUR_ARM_IDS[-1]][field] = value
    _resign_four_arm_receipt(receipt)
    result = split_plan.build_quantity_leg_four_arm_evaluation(events)
    assert result["complete_exact_attempt_count"] == 29
    assert result["excluded_counts"]["arm_economics_or_executability_invalid"] == 1
    assert result["promotion_gate"]["passed"] is False


def test_four_arm_conflicting_duplicate_quarantines_both_versions():
    events = _quantity_leg_four_arm_events()
    conflicting = json.loads(json.dumps(events[0]))
    receipt = conflicting["entry_quantity_leg_four_arm_evaluation"]
    receipt["arms"][split_plan.QUANTITY_LEG_FOUR_ARM_IDS[-1]]["net_pnl_krw"] = 999
    _resign_four_arm_receipt(receipt)
    events.append(conflicting)
    for ordered in (events, list(reversed(events))):
        result = split_plan.build_quantity_leg_four_arm_evaluation(ordered)
        assert result["complete_exact_attempt_count"] == 29
        assert result["excluded_counts"]["conflicting_exact_attempt_quarantined"] == 1
        assert result["promotion_gate"]["passed"] is False


def test_four_arm_invalid_unsigned_duplicate_cannot_hide_valid_attempt():
    events = _quantity_leg_four_arm_events()
    invalid = json.loads(json.dumps(events[0]))
    invalid["entry_quantity_leg_four_arm_evaluation"]["receipt_sha256"] = "0" * 64
    invalid["entry_quantity_leg_four_arm_evaluation"]["eligible_attempt_count"] = 999
    result = split_plan.build_quantity_leg_four_arm_evaluation([invalid, *events])
    assert result["complete_exact_attempt_count"] == 30
    assert result["excluded_counts"]["immutable_receipt_hash_invalid"] == 1
    assert result["promotion_gate"]["passed"] is True


@pytest.mark.parametrize("value", [float("nan"), float("inf"), True, 30.5])
def test_four_arm_invalid_denominator_cannot_promote_or_crash(value):
    events = _quantity_leg_four_arm_events()
    for event in events:
        receipt = event["entry_quantity_leg_four_arm_evaluation"]
        receipt["eligible_attempt_count"] = value
        _resign_four_arm_receipt(receipt)
    result = split_plan.build_quantity_leg_four_arm_evaluation(events)
    assert result["eligible_attempt_count"] == 0
    assert result["exact_attempt_join_coverage"] is None
    assert result["promotion_gate"]["passed"] is False


def test_four_arm_confirmed_no_exposure_stays_in_paired_denominator():
    events = _quantity_leg_four_arm_events()
    receipt = events[0]["entry_quantity_leg_four_arm_evaluation"]
    for arm in receipt["arms"].values():
        arm.update(net_return_pct=0, net_pnl_krw=0, capital_krw_minutes=0, fill_participation_rate=0)
    _resign_four_arm_receipt(receipt)
    result = split_plan.build_quantity_leg_four_arm_evaluation(events)
    assert result["complete_exact_attempt_count"] == 30
    assert result["exact_attempt_join_coverage"] == 1
    assert result["arms"][split_plan.QUANTITY_LEG_FOUR_ARM_IDS[-1]]["positive_terminal_frequency"] == pytest.approx(29 / 30)


def test_quantity_leg_four_arm_sums_daily_eligible_denominators_for_cumulative_gate():
    events = []
    for index in range(30):
        source_date = "2026-09-14" if index < 2 else "2026-09-15"
        eligible_count = 2 if index < 2 else 28

        def arm(net_return, pnl):
            return {
                "net_return_pct": net_return,
                "net_pnl_krw": pnl,
                "capital_krw_minutes": 10,
                "fill_participation_rate": 0.9,
                "terminal_conservation_holds": True,
                "cost_complete": True,
                "counterfactual_executable": True,
                "entry_price_receipt_sha256": "d" * 64,
                "exit_policy_sha256": "e" * 64,
                "cost_contract_sha256": "f" * 64,
                "terminal_contract_version": "same-terminal-v1",
                "terminal_observed_at": "2026-09-15T10:30:00+09:00",
            }

        receipt = {
            "schema": split_plan.QUANTITY_LEG_FOUR_ARM_SCHEMA,
            "source_date": source_date,
            "scanner_promotion_id": f"promotion-{index}",
            "evaluation_attempt_id": f"attempt-{index}",
            "stock_code": "005930",
            "effective_venue": "KRX",
            "session_bucket": "KRX_REGULAR",
            "policy_bundle_sha256": "a" * 64,
            "eligible_attempt_count": eligible_count,
            "incumbent_quantity_policy_version": "qty-current",
            "candidate_quantity_policy_version": "qty-candidate",
            "incumbent_leg_policy_version": "leg-current",
            "candidate_leg_policy_version": "leg-candidate",
            "entry_price_policy_sha256": "c" * 64,
            "arms": {
                "incumbent_qty_x_incumbent_leg": arm(0.08, 80),
                "candidate_qty_x_incumbent_leg": arm(0.11, 110),
                "incumbent_qty_x_candidate_leg": arm(0.12, 120),
                "candidate_qty_x_candidate_leg": arm(0.15, 150),
            },
        }
        receipt["receipt_sha256"] = hashlib.sha256(
            json.dumps(
                receipt, ensure_ascii=True, sort_keys=True, separators=(",", ":")
            ).encode("ascii")
        ).hexdigest()
        events.append(
            {
                "source_date": source_date,
                "entry_quantity_leg_four_arm_evaluation": receipt,
            }
        )

    result = split_plan.build_quantity_leg_four_arm_evaluation(events)

    assert result["eligible_attempt_count"] == 30
    assert result["eligible_source_date_count"] == 2
    assert result["complete_exact_attempt_count"] == 30
    assert result["exact_attempt_join_coverage"] == 1.0
    assert result["promotion_gate"]["passed"] is True
    assert result["floor_attainability"]["bounded_observation_window"] is False


def test_quantity_leg_four_arm_keeps_incomplete_counterfactual_null():
    receipt = {
        "schema": split_plan.QUANTITY_LEG_FOUR_ARM_SCHEMA,
        "scanner_promotion_id": "promotion-1",
        "evaluation_attempt_id": "attempt-1",
        "stock_code": "005930",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "policy_bundle_sha256": "a" * 64,
        "eligible_attempt_count": 1,
        "incumbent_quantity_policy_version": "qty-current",
        "candidate_quantity_policy_version": "qty-candidate",
        "incumbent_leg_policy_version": "leg-current",
        "candidate_leg_policy_version": "leg-candidate",
        "entry_price_policy_sha256": "c" * 64,
        "arms": {},
    }
    receipt["receipt_sha256"] = hashlib.sha256(
        json.dumps(
            receipt, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        ).encode("ascii")
    ).hexdigest()
    result = split_plan.build_quantity_leg_four_arm_evaluation(
        [{"entry_quantity_leg_four_arm_evaluation": receipt}]
    )

    assert result["complete_exact_attempt_count"] == 0
    assert result["excluded_counts"] == {"four_arm_incomplete": 1}
    assert result["incremental_effects"]["combined_net_ev_delta_pct"] is None
    assert result["promotion_gate"]["passed"] is False


def test_quantity_leg_four_arm_rejects_mixed_price_exit_cost_or_terminal_contract():
    def arm(*, terminal_contract_version="same-terminal-v1"):
        return {
            "net_return_pct": 0.15,
            "net_pnl_krw": 150,
            "capital_krw_minutes": 10,
            "fill_participation_rate": 0.9,
            "terminal_conservation_holds": True,
            "cost_complete": True,
            "counterfactual_executable": True,
            "entry_price_receipt_sha256": "d" * 64,
            "exit_policy_sha256": "e" * 64,
            "cost_contract_sha256": "f" * 64,
            "terminal_contract_version": terminal_contract_version,
            "terminal_observed_at": "2026-09-15T10:30:00+09:00",
        }

    receipt = {
        "schema": split_plan.QUANTITY_LEG_FOUR_ARM_SCHEMA,
        "scanner_promotion_id": "promotion-1",
        "evaluation_attempt_id": "attempt-1",
        "stock_code": "005930",
        "effective_venue": "KRX",
        "session_bucket": "KRX_REGULAR",
        "policy_bundle_sha256": "a" * 64,
        "eligible_attempt_count": 1,
        "incumbent_quantity_policy_version": "qty-current",
        "candidate_quantity_policy_version": "qty-candidate",
        "incumbent_leg_policy_version": "leg-current",
        "candidate_leg_policy_version": "leg-candidate",
        "entry_price_policy_sha256": "c" * 64,
        "arms": {
            arm_id: arm(
                terminal_contract_version=(
                    "different-terminal-v1"
                    if arm_id == "candidate_qty_x_candidate_leg"
                    else "same-terminal-v1"
                )
            )
            for arm_id in split_plan.QUANTITY_LEG_FOUR_ARM_IDS
        },
    }
    receipt["receipt_sha256"] = hashlib.sha256(
        json.dumps(
            receipt, ensure_ascii=True, sort_keys=True, separators=(",", ":")
        ).encode("ascii")
    ).hexdigest()

    result = split_plan.build_quantity_leg_four_arm_evaluation(
        [{"entry_quantity_leg_four_arm_evaluation": receipt}]
    )

    assert result["complete_exact_attempt_count"] == 0
    assert result["excluded_counts"][
        "arm_economics_or_executability_invalid"
    ] == 1
    assert result["promotion_gate"]["passed"] is False


def test_runtime_apply_authority_contract_rejects_unknown_semantics():
    valid, reason = split_plan.runtime_apply_authority_contract_status(
        {
            "runtime_apply_allowed": True,
            "runtime_apply_compatibility_semantics": "unknown_union_contract",
            "exploration_seed_allowed": True,
            "ev_validated_runtime_apply_allowed": False,
            "runtime_apply_authority_classes": ["bounded_exploration_seed"],
        }
    )

    assert valid is False
    assert reason == "runtime_apply_compatibility_semantics_invalid"


def test_runtime_apply_authority_contract_rejects_string_boolean():
    valid, reason = split_plan.runtime_apply_authority_contract_status(
        {
            "runtime_apply_allowed": "true",
            "runtime_apply_compatibility_semantics": (
                split_plan.RUNTIME_APPLY_COMPATIBILITY_SEMANTICS
            ),
            "exploration_seed_allowed": True,
            "ev_validated_runtime_apply_allowed": False,
            "runtime_apply_authority_classes": ["bounded_exploration_seed"],
        }
    )

    assert valid is False
    assert reason == "runtime_apply_allowed_not_boolean"


def test_runtime_apply_authority_contract_rejects_malformed_authority_classes():
    valid, reason = split_plan.runtime_apply_authority_contract_status(
        {
            "runtime_apply_allowed": False,
            "runtime_apply_compatibility_semantics": (
                split_plan.RUNTIME_APPLY_COMPATIBILITY_SEMANTICS
            ),
            "exploration_seed_allowed": False,
            "ev_validated_runtime_apply_allowed": False,
            "runtime_apply_authority_classes": "none",
        }
    )

    assert valid is False
    assert reason == "runtime_apply_authority_classes_not_string_list"


def test_runtime_apply_authority_contract_rejects_malformed_child_shape_gate():
    valid, reason = split_plan.runtime_apply_authority_contract_status(
        {
            "runtime_apply_allowed": True,
            "runtime_apply_compatibility_semantics": (
                split_plan.RUNTIME_APPLY_COMPATIBILITY_SEMANTICS
            ),
            "exploration_seed_allowed": True,
            "ev_validated_runtime_apply_allowed": False,
            "runtime_apply_authority_classes": ["bounded_exploration_seed"],
            "buckets": {
                "passive_wide_or_weak": {
                    "runtime_shape_gate": {
                        "schema": "entry_split_runtime_shape_gate_v1",
                        "required_policy_split_variant_id": "parent",
                        "observed_child_variant_id": "parent__child",
                        "required_requested_legs": 3,
                        "required_desired_legs": 2,
                        "required_runtime_first_weight": 0.2,
                        "require_runtime_weight_adjusted": "true",
                        "require_market_first_leg_disabled": True,
                        "require_probe_first_enabled": True,
                        "require_probe_first_eligible": True,
                    }
                }
            },
        }
    )

    assert valid is False
    assert reason == "runtime_shape_gate_require_runtime_weight_adjusted_not_boolean"


def test_runtime_apply_authority_contract_rejects_scoped_default_fallback():
    valid, reason = split_plan.runtime_apply_authority_contract_status(
        {
            "runtime_apply_allowed": True,
            "runtime_apply_compatibility_semantics": (
                split_plan.RUNTIME_APPLY_COMPATIBILITY_SEMANTICS
            ),
            "exploration_seed_allowed": True,
            "ev_validated_runtime_apply_allowed": False,
            "runtime_apply_authority_classes": ["bounded_exploration_seed"],
            "baseline_runtime_defaults_enabled": False,
            "missing_bucket_action": "runtime_default_fallback",
            "explicit_bucket_count": 1,
            "buckets": {"passive_wide_or_weak": {}},
        }
    )

    assert valid is False
    assert reason == "missing_bucket_action_inconsistent_with_baseline_scope"


def test_report_policy_generation_binding_uses_and_validates_immutable_report(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(split_plan, "REPORT_DIR", tmp_path / "reports")
    report_path = tmp_path / "entry_split_order_plan_2026-09-04.json"
    policy = {
        "schema_version": split_plan.POLICY_SCHEMA_VERSION,
        "source_date": "2026-09-04",
        "source_report": str(report_path),
        "policy_version": "entry_split_order_plan:2026-09-04:abc",
        "buckets": {},
    }
    report = {
        "schema_version": split_plan.SCHEMA_VERSION,
        "date": "2026-09-04",
        "recommended_policy": {"policy_version": policy["policy_version"]},
    }
    report, policy = split_plan.bind_report_policy_generation(report, policy)
    report_path.write_text(json.dumps(report), encoding="utf-8")
    generation_id = report["artifact_generation_binding"]["generation_id"]
    immutable_path = split_plan.generation_report_path("2026-09-04", generation_id)
    split_plan._write_json(immutable_path, report)

    assert split_plan.validate_report_policy_generation(report, policy) == (
        True,
        "generation_binding_valid",
    )
    assert split_plan.policy_report_generation_contract_status(policy) == (
        True,
        "generation_binding_valid",
    )

    independently_overwritten = {
        **report,
        "recommended_policy": {"policy_version": "different-generation"},
    }
    report_path.write_text(json.dumps(independently_overwritten), encoding="utf-8")
    assert split_plan.policy_report_generation_contract_status(policy) == (
        True,
        "generation_binding_valid",
    )
    immutable_path.write_text(json.dumps(independently_overwritten), encoding="utf-8")
    assert split_plan.policy_report_generation_contract_status(policy) == (
        False,
        "generation_binding_digest_mismatch",
    )


def test_current_generation_requires_atomic_execution_sizing_handoff():
    policy = {
        "schema_version": split_plan.POLICY_SCHEMA_VERSION,
        "source_date": "2026-09-16",
        "source_report": "/not/read-by-direct-validator.json",
        "policy_version": "entry_split_order_plan:2026-09-16:test",
        "buckets": {},
    }
    report = {
        "schema_version": split_plan.SCHEMA_VERSION,
        "date": "2026-09-16",
        "recommended_policy": {"policy_version": policy["policy_version"]},
    }
    report, policy = split_plan.bind_report_policy_generation(report, policy)

    assert split_plan.validate_report_policy_generation(report, policy) == (
        False,
        "generation_atomic_execution_sizing_policy_invalid",
    )

    policy.update(
        entry_price_plan_schema=split_plan.ATOMIC_PRICE_PLAN_SCHEMA,
        entry_execution_sizing_plan_schema=(split_plan.ATOMIC_EXECUTION_SIZING_SCHEMA),
        entry_execution_sizing_policy=(
            split_plan.ATOMIC_EXECUTION_SIZING_BASELINE_POLICY
        ),
    )
    report["recommended_policy"].update(
        entry_price_plan_schema=split_plan.ATOMIC_PRICE_PLAN_SCHEMA,
        entry_execution_sizing_plan_schema=(split_plan.ATOMIC_EXECUTION_SIZING_SCHEMA),
        entry_execution_sizing_policy=(
            split_plan.ATOMIC_EXECUTION_SIZING_BASELINE_POLICY
        ),
    )
    report, policy = split_plan.bind_report_policy_generation(report, policy)
    assert split_plan.validate_report_policy_generation(report, policy) == (
        True,
        "generation_binding_valid",
    )


def test_price_receipt_handoff_does_not_retroactively_reject_20260915_policy():
    policy = {
        "schema_version": split_plan.POLICY_SCHEMA_VERSION,
        "source_date": "2026-09-15",
        "source_report": "/not/read-by-direct-validator.json",
        "policy_version": "entry_split_order_plan:2026-09-15:test",
        "entry_execution_sizing_plan_schema": (
            split_plan.ATOMIC_EXECUTION_SIZING_SCHEMA
        ),
        "entry_execution_sizing_policy": (
            split_plan.ATOMIC_EXECUTION_SIZING_BASELINE_POLICY
        ),
        "buckets": {},
    }
    report = {
        "schema_version": split_plan.SCHEMA_VERSION,
        "date": "2026-09-15",
        "recommended_policy": {
            "policy_version": policy["policy_version"],
            "entry_execution_sizing_plan_schema": (
                split_plan.ATOMIC_EXECUTION_SIZING_SCHEMA
            ),
            "entry_execution_sizing_policy": (
                split_plan.ATOMIC_EXECUTION_SIZING_BASELINE_POLICY
            ),
        },
    }
    report, policy = split_plan.bind_report_policy_generation(report, policy)

    assert split_plan.validate_report_policy_generation(report, policy) == (
        True,
        "generation_binding_valid",
    )


def test_generation_binding_required_from_activation_date():
    valid, reason = split_plan.policy_report_generation_contract_status(
        {
            "schema_version": split_plan.POLICY_SCHEMA_VERSION,
            "source_date": "2026-09-04",
            "source_report": "/not/used/without/binding.json",
            "policy_version": "entry_split_order_plan:2026-09-04:legacy",
            "buckets": {},
        }
    )

    assert valid is False
    assert reason == "generation_binding_required"


def test_prior_cumulative_state_requires_valid_generation_pair_after_activation(
    monkeypatch, tmp_path
):
    _patch_dirs(monkeypatch, tmp_path)
    monkeypatch.setattr(
        split_plan, "GENERATION_BINDING_REQUIRED_FROM_DATE", date(2026, 9, 4)
    )
    source_date = "2026-09-04"
    target_date = "2026-09-05"
    source_quality = {
        "status": "pass",
        "tuning_input_allowed": True,
        "hard_blocking_contract_gap_count": 0,
        "hard_blocking_excluded_row_count": 0,
        "raw_row_exclusion_applied": False,
        "hard_blocking_stages": [],
    }
    monkeypatch.setattr(
        split_plan, "_available_calibration_dates", lambda _date: [source_date]
    )
    monkeypatch.setattr(
        split_plan, "_source_quality_summary", lambda _date: source_quality
    )
    state = {
        "schema_version": split_plan.CUMULATIVE_STATE_SCHEMA_VERSION,
        "window_policy": "clean_baseline_cumulative_through_target_date",
        "through_date": source_date,
        "clean_tuning_baseline_date": "2026-06-05",
        "source_dates": [source_date],
        "source_quality_contract_bindings": {
            source_date: {
                "contract": split_plan._source_quality_contract(source_quality),
                "contract_sha256": split_plan._source_quality_contract_sha256(
                    source_quality
                ),
            }
        },
    }
    report_path = split_plan.REPORT_DIR / f"entry_split_order_plan_{source_date}.json"
    policy_path = split_plan.POLICY_DIR / f"entry_split_order_policy_{source_date}.json"
    report = {
        "schema_version": split_plan.SCHEMA_VERSION,
        "date": source_date,
        "cumulative_state": state,
        "recommended_policy": {"policy_version": "entry:test"},
    }
    policy = {
        "schema_version": split_plan.POLICY_SCHEMA_VERSION,
        "source_date": source_date,
        "source_report": str(report_path),
        "policy_version": "entry:test",
        "buckets": {},
    }
    report, policy = split_plan.bind_report_policy_generation(report, policy)
    report_path.parent.mkdir(parents=True)
    policy_path.parent.mkdir(parents=True)
    report_path.write_text(json.dumps(report), encoding="utf-8")
    policy_path.write_text(json.dumps(policy), encoding="utf-8")

    loaded, loaded_path = split_plan._latest_prior_cumulative_state(target_date)
    assert loaded == state
    assert loaded_path == str(report_path)

    report["cumulative_state"]["counts"] = {"tampered": {"count": 1}}
    report_path.write_text(json.dumps(report), encoding="utf-8")
    loaded, loaded_path = split_plan._latest_prior_cumulative_state(target_date)
    assert loaded == {}
    assert loaded_path == ""


def _write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows),
        encoding="utf-8",
    )


def _patch_dirs(monkeypatch, tmp_path):
    data_dir = tmp_path / "data"
    monkeypatch.setattr(split_plan, "DATA_DIR", data_dir)
    monkeypatch.setattr(
        split_plan, "REPORT_DIR", data_dir / "report" / "entry_split_order_plan"
    )
    monkeypatch.setattr(
        split_plan,
        "POLICY_DIR",
        data_dir / "threshold_cycle" / "entry_split_order_policy",
    )
    # Existing allocator tests intentionally exercise a minimal legacy policy.
    # Generation-binding behavior has dedicated exact-pair tests above.
    monkeypatch.setattr(
        split_plan, "GENERATION_BINDING_REQUIRED_FROM_DATE", date(2099, 1, 1)
    )
    return data_dir


def test_postclose_report_consumes_atomic_entry_sizing_receipt(monkeypatch, tmp_path):
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    target_date = "2026-09-15"
    _write_jsonl(
        data_dir / "pipeline_events" / f"pipeline_events_{target_date}.jsonl",
        [
            {
                "date": target_date,
                "emitted_at": f"{target_date}T10:00:00+09:00",
                "stage": "entry_execution_sizing_plan",
                "entry_execution_sizing_plan_id": "entry-sizing-test",
                "entry_execution_sizing_plan_schema": (
                    "entry_execution_sizing_plan_v1"
                ),
                "entry_execution_sizing_valid": True,
                "entry_execution_sizing_quantity_conservation_holds": True,
                "entry_execution_sizing_total_qty": 2,
                "entry_execution_sizing_leg_count": 2,
            },
            {
                "date": target_date,
                "emitted_at": f"{target_date}T10:00:01+09:00",
                "stage": "order_bundle_submitted",
                "actual_order_submitted": True,
                "requested_qty": 2,
                "entry_execution_sizing_plan_id": "entry-sizing-test",
                "entry_execution_sizing_valid": True,
            },
        ],
    )
    source_quality = (
        data_dir
        / "report"
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{target_date}.json"
    )
    source_quality.parent.mkdir(parents=True, exist_ok=True)
    source_quality.write_text(
        json.dumps({"status": "pass", "summary": {"tuning_input_allowed": True}}),
        encoding="utf-8",
    )

    report = split_plan.build_report(target_date, write=False)

    atomic = report["input_summary"]["atomic_execution_sizing"]
    assert atomic["status"] == "pass"
    assert atomic["daily_plan_valid_count"] == 1
    assert atomic["daily_real_submit_with_plan_count"] == 1
    assert atomic["daily_real_submit_missing_plan_count"] == 0


def test_postclose_report_blocks_selection_on_atomic_entry_contract_failure(
    monkeypatch, tmp_path
):
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    target_date = "2026-09-15"
    _write_jsonl(
        data_dir / "pipeline_events" / f"pipeline_events_{target_date}.jsonl",
        [
            {
                "date": target_date,
                "emitted_at": f"{target_date}T10:00:00+09:00",
                "stage": "entry_execution_sizing_plan_block",
                "entry_execution_sizing_plan_id": "entry-sizing-invalid",
                "entry_execution_sizing_plan_schema": (
                    "entry_execution_sizing_plan_v1"
                ),
                "entry_execution_sizing_valid": False,
                "entry_execution_sizing_blockers": ["quantity_conservation_failed"],
            },
            {
                "date": target_date,
                "emitted_at": f"{target_date}T10:00:01+09:00",
                "stage": "order_bundle_submitted",
                "actual_order_submitted": True,
                "requested_qty": 2,
            },
        ],
    )
    source_quality = (
        data_dir
        / "report"
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{target_date}.json"
    )
    source_quality.parent.mkdir(parents=True, exist_ok=True)
    source_quality.write_text(
        json.dumps({"status": "pass", "summary": {"tuning_input_allowed": True}}),
        encoding="utf-8",
    )

    report = split_plan.build_report(target_date, write=False)

    atomic = report["input_summary"]["atomic_execution_sizing"]
    assert atomic["status"] == "fail"
    assert atomic["daily_plan_invalid_count"] == 1
    assert atomic["daily_real_submit_missing_plan_count"] == 1
    assert report["recommended_policy"]["candidate_count"] == 0




def test_split_candidate_disables_previous_policy_after_mature_negative_early_ev():
    grid = split_plan._build_candidate_grid(
        {"balanced_normal": {"real_sample_count": 20}},
        {},
        {},
        {("balanced_normal", split_plan.BASELINE_SPLIT_VARIANT_ID): [-0.2] * 10},
    )

    candidate = grid[0]
    assert candidate["candidate_passed"] is False
    assert candidate["sample_floor_status"] == (
        "hold_early_split_variant_edge_not_positive"
    )
    assert candidate["post_apply_continuation_gate"]["action"] == (
        "disable_previous_policy_next_preopen"
    )


def test_split_candidate_separates_real_submit_sim_fill_and_positive_terminals():
    grid = split_plan._build_candidate_grid(
        {
            "balanced_normal": {
                "real_sample_count": 20,
                "real_submitted_count": 5,
                "sim_sample_count": 10,
                "sim_fill_count": 8,
            }
        },
        {},
        {},
        {
            ("balanced_normal", split_plan.BASELINE_SPLIT_VARIANT_ID): [
                0.2,
                -0.1,
                0.3,
                -0.2,
                0.4,
                0.1,
                -0.1,
                0.2,
                0.1,
                0.2,
            ]
        },
    )

    candidate = grid[0]
    assert candidate["real_submit_count"] == 5
    assert candidate["real_submit_rate_pct"] == 25.0
    assert candidate["sim_fill_count"] == 8
    assert candidate["sim_fill_rate_pct"] == 80.0
    assert candidate["cost_adjusted_positive_terminal_count"] == 7
    assert candidate["cost_adjusted_positive_terminal_rate_pct"] == 70.0
    assert candidate["fill_quality_scope"].startswith("legacy_mixed_")


def test_split_candidate_holds_observation_before_real_submit_floor():
    grid = split_plan._build_candidate_grid(
        {"balanced_normal": {"real_sample_count": 19}},
        {},
        {},
        {},
    )

    candidate = grid[0]
    assert candidate["candidate_passed"] is False
    assert candidate["sample_floor_status"] == "hold_sample"
    assert candidate["post_apply_continuation_gate"]["action"] == ("hold_observation")
    assert candidate["post_apply_continuation_gate"]["pass"] is False
    assert candidate["post_apply_continuation_gate"]["economic_evidence_pass"] is True
    assert candidate["post_apply_continuation_gate"]["reason"] == (
        "real_submit_sample_floor_not_reached"
    )


def test_split_candidate_holds_when_exact_outcome_is_missing_despite_submit_floor():
    grid = split_plan._build_candidate_grid(
        {"balanced_normal": {"real_sample_count": 20}},
        {},
        {},
        {},
    )

    candidate = grid[0]
    assert candidate["candidate_passed"] is True
    assert candidate["post_apply_continuation_gate"]["action"] == (
        "continue_bounded_seed"
    )

    guarded = split_plan._build_candidate_grid(
        {"guarded_or_stale": {"real_sample_count": 20}},
        {},
        {},
        {},
    )[0]
    assert guarded["candidate_passed"] is False
    assert guarded["post_apply_continuation_gate"]["action"] == "hold_observation"


def test_generation_snapshot_path_rejects_non_iso_date():
    report = {
        "date": "../2026-09-04",
        "artifact_generation_binding": {"generation_id": "a" * 64},
    }

    assert split_plan.generation_policy_snapshot_path(report) is None


def test_current_generation_contract_requires_immutable_report(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    monkeypatch.setattr(
        split_plan, "GENERATION_BINDING_REQUIRED_FROM_DATE", date(2026, 9, 4)
    )
    target_date = "2026-09-04"
    report = {"schema_version": split_plan.SCHEMA_VERSION, "date": target_date}
    policy = {
        "schema_version": split_plan.POLICY_SCHEMA_VERSION,
        "source_date": target_date,
        "source_report": str(split_plan.report_paths(target_date)[0]),
    }
    report["recommended_policy"] = {"policy_version": "policy-test"}
    policy["policy_version"] = "policy-test"
    report, policy = split_plan.bind_report_policy_generation(report, policy)
    split_plan._write_json(split_plan.report_paths(target_date)[0], report)

    assert split_plan.policy_report_generation_contract_status(policy) == (
        False,
        "immutable_generation_source_report_missing",
    )


def test_split_candidate_does_not_seed_against_mature_parent_tail_evidence():
    grid = split_plan._build_candidate_grid(
        {"balanced_normal": {"real_sample_count": 20}},
        {},
        {},
        {("balanced_normal", "prior_split_variant"): [-0.4] * 20},
    )

    candidate = grid[0]
    assert candidate["candidate_passed"] is False
    assert (
        candidate["post_apply_continuation_gate"][
            "mature_parent_evidence_contradictory"
        ]
        is True
    )
    assert candidate["sample_floor_status"] == (
        "hold_mature_parent_split_edge_contradicted"
    )


def test_split_candidate_uses_exact_positive_child_shape_not_parent_tail():
    parent_variant = split_plan.RUNTIME_FALLBACK_THREE_LEG_VARIANT_ID
    child_variant = (
        f"{parent_variant}__qty_clipped_legs2__runtime_first_weight_20"
        f"__{split_plan.PROBE_VARIANT_SUFFIX}"
    )
    grid = split_plan._build_candidate_grid(
        {
            "passive_wide_or_weak": {
                "real_sample_count": 20,
                "cancel_or_fail_count": 0,
                "late_fill_count": 0,
            }
        },
        {},
        {},
        {("passive_wide_or_weak", parent_variant): [-3.16] * 20},
        {("passive_wide_or_weak", child_variant): [0.169, 0.5, 0.7]},
    )

    candidate = grid[0]
    assert candidate["candidate_passed"] is True
    assert candidate["policy_mode"] == split_plan.POLICY_MODE_CHILD_SHAPE_EV_SEED
    assert candidate["runtime_apply_scope"] == "child_shape_bounded_seed"
    assert candidate["runtime_apply_authority_class"] == "bounded_exploration_seed"
    assert candidate["source_quality_adjusted_ev_pct"] == pytest.approx(0.4563)
    assert candidate["selected_child_variant_id"] == child_variant
    assert candidate["runtime_shape_gate"] == {
        "schema": "entry_split_runtime_shape_gate_v1",
        "required_policy_split_variant_id": parent_variant,
        "required_requested_legs": 3,
        "required_desired_legs": 2,
        "required_runtime_first_weight": 0.2,
        "require_runtime_weight_adjusted": True,
        "require_market_first_leg_disabled": True,
        "require_probe_first_enabled": True,
        "require_probe_first_eligible": True,
        "observed_child_variant_id": child_variant,
    }
    assert (
        candidate["post_apply_continuation_gate"][
            "mature_parent_tail_applies_to_selected_child_shape"
        ]
        is False
    )


def test_allocator_applies_child_shape_seed_only_for_exact_observed_shape(
    monkeypatch, tmp_path
):
    policy_file = tmp_path / "entry-child-shape-policy.json"
    now = datetime(2026, 7, 14, 9, 30, tzinfo=timezone(timedelta(hours=9)))
    parent_variant = split_plan.RUNTIME_FALLBACK_THREE_LEG_VARIANT_ID
    child_variant = (
        f"{parent_variant}__qty_clipped_legs2__runtime_first_weight_20"
        f"__{split_plan.PROBE_VARIANT_SUFFIX}"
    )
    template = split_plan._child_shape_seed_template(
        "passive_wide_or_weak", child_variant
    )
    assert template is not None
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": split_plan.POLICY_SCHEMA_VERSION,
                "policy_version": "child-shape-seed",
                "source_date": "2026-07-14",
                "runtime_apply_allowed": True,
                "buckets": {"passive_wide_or_weak": template},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(split_plan, "PROBE_RUNTIME_STATE_PATH", tmp_path / "probe.json")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(policy_file))
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_VERSION", "child-shape-seed"
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ACTIVE_DATE", "2026-07-14"
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ACTIVE_DATE", "2026-07-14")

    blocked_orders, blocked_fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 2, "price": 1000}],
        stock={"code": "005930", "id": 1, "strategy": "SCALPING"},
        latency_gate={"spread_bps": 40, "buy_pressure_10t": 40, "action": "BUY"},
        now=now,
    )
    assert blocked_orders == [{"tag": "normal", "qty": 2, "price": 1000}]
    assert blocked_fields["entry_split_order_policy_applied"] is False
    assert blocked_fields["entry_split_order_skip_reason"] == (
        "runtime_shape_gate_mismatch:first_weight"
    )

    orders, fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 2, "price": 1000}],
        stock={"code": "005930", "id": 1, "strategy": "SCALPING"},
        latency_gate={"spread_bps": 40, "buy_pressure_10t": 40, "action": "WAIT"},
        now=now,
    )
    assert fields["entry_split_order_policy_applied"] is True
    assert fields["entry_split_order_policy_variant_id"] == parent_variant
    assert fields["entry_split_order_variant_id"] == child_variant
    assert len(orders) == 1
    assert orders[0]["qty"] == 1


def test_runtime_loader_rejects_preopen_policy_version_mismatch(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target_date = datetime.now(timezone(timedelta(hours=9))).date().isoformat()
    path = split_plan.policy_path(target_date)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": split_plan.POLICY_SCHEMA_VERSION,
                "policy_version": "entry-split-selected",
                "source_date": target_date,
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(path))
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_VERSION", "entry-split-stale"
    )

    loaded, status = split_plan._load_policy_from_env()

    assert loaded == {}
    assert status == "policy_version_mismatch"


def test_build_report_suppresses_policy_candidates_when_source_quality_blocked(
    monkeypatch, tmp_path
):
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    target_date = "2026-07-07"
    events = [
        {
            "date": target_date,
            "stage": (
                "order_leg_sent" if idx < 20 else "scalp_sim_buy_order_assumed_filled"
            ),
            "actual_order_submitted": idx < 20,
            "spread_bps": 5,
            "buy_pressure_10t": 72,
        }
        for idx in range(70)
    ]
    _write_jsonl(
        data_dir / "pipeline_events" / f"pipeline_events_{target_date}.jsonl", events
    )
    source_quality_path = (
        data_dir
        / "report"
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{target_date}.json"
    )
    source_quality_path.parent.mkdir(parents=True, exist_ok=True)
    source_quality_path.write_text(
        json.dumps({"status": "fail", "summary": {"tuning_input_allowed": False}}),
        encoding="utf-8",
    )
    _write_jsonl(
        data_dir / "post_sell" / f"sim_post_sell_evaluations_{target_date}.jsonl",
        [
            {
                "date": target_date,
                "profit_rate": 1.2,
                "spread_bps": 5,
                "buy_pressure_10t": 72,
            }
            for _ in range(50)
        ],
    )
    _write_jsonl(
        data_dir / "post_sell" / f"post_sell_evaluations_{target_date}.jsonl",
        [
            {
                "date": target_date,
                "actual_order_submitted": True,
                "profit_rate": 1.3,
                "spread_bps": 5,
                "buy_pressure_10t": 72,
            }
            for _ in range(20)
        ],
    )

    report = split_plan.build_report(target_date, write=True)

    assert report["source_quality"]["tuning_input_allowed"] is False
    assert report["candidate_grid"] == []
    assert report["input_summary"]["excluded_source_quality_event_count"] == 70
    assert report["recommended_policy"]["candidate_count"] == 0
    assert report["recommended_policy"]["runtime_apply_allowed"] is False
    assert report["recommended_policy"]["baseline_runtime_defaults_enabled"] is False
    policy = json.loads(split_plan.policy_path(target_date).read_text(encoding="utf-8"))
    assert policy["runtime_apply_allowed"] is False
    assert policy["exploration_seed_allowed"] is False
    assert policy["ev_validated_runtime_apply_allowed"] is False
    assert policy["buckets"] == {}


def test_build_report_merges_late_candidate_and_reconstructs_split_provenance(
    monkeypatch, tmp_path
):
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    target_date = "2026-07-07"
    _write_jsonl(
        data_dir / "pipeline_events" / f"pipeline_events_{target_date}.jsonl",
        [
            {
                "date": target_date,
                "stage": "order_bundle_submitted",
                "record_id": 123,
                "actual_order_submitted": True,
                "broker_order_submitted": True,
                "spread_bps": 18,
                "buy_pressure_10t": 55,
                "entry_split_order_policy_applied": True,
                "entry_split_order_policy_mode": "bounded_equal_split_baseline",
                "entry_split_order_variant_id": "equal_50_50_offset_0pct_0_3pct",
                "entry_split_order_leg_count": 2,
            }
        ],
    )
    _write_jsonl(
        data_dir / "post_sell" / f"post_sell_candidates_{target_date}.jsonl",
        [
            {
                "post_sell_id": "late-candidate",
                "signal_date": target_date,
                "recommendation_id": 123,
                "actual_order_submitted": True,
                "profit_rate": 1.25,
                "spread_bps": 18,
                "buy_pressure_10t": 55,
            }
        ],
    )
    _write_jsonl(
        data_dir / "post_sell" / f"post_sell_evaluations_{target_date}.jsonl",
        [
            {
                "post_sell_id": "late-candidate",
                "signal_date": target_date,
                "recommendation_id": 123,
                "actual_order_submitted": True,
                "profit_rate": 1.25,
                "spread_bps": 18,
                "buy_pressure_10t": 55,
            }
        ],
    )
    source_quality_path = (
        data_dir
        / "report"
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{target_date}.json"
    )
    source_quality_path.parent.mkdir(parents=True, exist_ok=True)
    source_quality_path.write_text(
        json.dumps({"status": "warning", "summary": {"tuning_input_allowed": True}}),
        encoding="utf-8",
    )

    report = split_plan.build_report(target_date, write=False)

    balanced = next(
        item
        for item in report["candidate_grid"]
        if item["context_bucket"] == "balanced_normal"
    )
    assert balanced["real_outcome_joined_sample"] == 1
    assert balanced["real_split_variant_outcome_joined_sample"] == 1
    assert balanced["real_split_variant_ev_pct"] == 1.25
    assert balanced["observed_real_split_outcome_count"] == 1
    assert balanced["observed_real_split_variants"] == [
        {
            "split_variant_id": "equal_50_50_offset_0pct_0_3pct",
            "sample_count": 1,
            "equal_weight_avg_profit_pct": 1.25,
        }
    ]
    assert report["input_summary"]["real_post_sell_join"] == {
        "candidate_count": 1,
        "evaluation_count": 1,
        "matched_evaluation_count": 1,
        "pending_evaluation_count": 0,
        "merged_count": 1,
        "reconstructed_split_provenance_count": 1,
    }


def test_provenance_reconstruction_ignores_false_split_flags_and_keeps_explicit_bucket():
    rows = [
        {
            "recommendation_id": 123,
            "actual_order_submitted": True,
            "profit_rate": 1.0,
        },
        {
            "recommendation_id": 456,
            "actual_order_submitted": True,
            "profit_rate": 2.0,
        },
    ]
    events = [
        {
            "stage": "order_bundle_submitted",
            "record_id": 123,
            "entry_split_order_policy_applied": False,
            "entry_split_order_runtime_default_policy_applied": False,
        },
        {
            "stage": "order_bundle_submitted",
            "record_id": 456,
            "entry_split_order_policy_applied": True,
            "entry_split_order_bucket": "balanced_normal",
            "entry_split_order_policy_mode": "bounded_equal_split_baseline",
            "entry_split_order_variant_id": "equal_50_50_offset_0pct_0_3pct",
        },
    ]

    enriched, reconstructed_count = split_plan._enrich_real_post_sell_provenance(
        rows, events
    )

    assert reconstructed_count == 1
    assert "entry_split_order_policy_applied" not in enriched[0]
    assert split_plan._context_bucket(enriched[1]) == "balanced_normal"


def test_build_report_reads_threshold_cycle_events_from_contract_path(
    monkeypatch, tmp_path
):
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    target_date = "2026-07-07"
    _write_jsonl(
        data_dir / "threshold_cycle" / f"threshold_events_{target_date}.jsonl",
        [
            {
                "date": target_date,
                "stage": "order_leg_sent",
                "actual_order_submitted": True,
                "requested_qty": 2,
                "spread_bps": 5,
                "buy_pressure_10t": 72,
            }
        ],
    )
    source_quality_path = (
        data_dir
        / "report"
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{target_date}.json"
    )
    source_quality_path.parent.mkdir(parents=True, exist_ok=True)
    source_quality_path.write_text(
        json.dumps({"status": "warning", "summary": {"tuning_input_allowed": True}}),
        encoding="utf-8",
    )

    report = split_plan.build_report(target_date, write=False)

    assert report["input_summary"]["source_paths"]["threshold_events"] == str(
        data_dir / "threshold_cycle" / f"threshold_events_{target_date}.jsonl"
    )
    assert report["input_summary"]["loaded_event_count"] == 1
    assert report["candidate_grid"][0]["real_sample_count"] == 1


def test_build_report_updates_cumulative_judgment_from_one_mature_outcome(
    monkeypatch, tmp_path
):
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    source_date = "2026-07-06"
    target_date = "2026-07-07"
    for day in (source_date, target_date):
        _write_jsonl(
            data_dir / "pipeline_events" / f"pipeline_events_{day}.jsonl",
            [
                {
                    "date": day,
                    "stage": "order_bundle_submitted",
                    "record_id": 100 if day == source_date else 200,
                    "actual_order_submitted": True,
                    "broker_order_submitted": True,
                    "spread_bps": 18,
                    "buy_pressure_10t": 55,
                    "entry_split_order_policy_applied": True,
                    "entry_split_order_policy_mode": ("bounded_equal_split_baseline"),
                    "entry_split_order_variant_id": ("equal_50_50_offset_0pct_0_3pct"),
                }
            ],
        )
        source_quality_path = (
            data_dir
            / "report"
            / "observation_source_quality_audit"
            / f"observation_source_quality_audit_{day}.json"
        )
        source_quality_path.parent.mkdir(parents=True, exist_ok=True)
        source_quality_path.write_text(
            json.dumps(
                {
                    "status": "warning",
                    "summary": {"tuning_input_allowed": True},
                }
            ),
            encoding="utf-8",
        )
    _write_jsonl(
        data_dir / "post_sell" / f"post_sell_evaluations_{source_date}.jsonl",
        [
            {
                "date": source_date,
                "recommendation_id": 100,
                "actual_order_submitted": True,
                "profit_rate": 1.25,
                "spread_bps": 18,
                "buy_pressure_10t": 55,
                "entry_split_order_variant_id": ("equal_50_50_offset_0pct_0_3pct"),
            }
        ],
    )

    report = split_plan.build_report(target_date, write=False)

    balanced = next(
        item
        for item in report["candidate_grid"]
        if item["context_bucket"] == "balanced_normal"
    )
    assert report["execution_contract"] == {
        "schedule": "daily_postclose",
        "wrapper_default_enabled": True,
        "calibration_window": "clean_baseline_cumulative_through_target_date",
    }
    assert report["input_summary"]["source_dates"] == [source_date, target_date]
    assert balanced["real_sample_count"] == 2
    assert balanced["target_date_contribution"]["real_sample_count"] == 1
    assert balanced["cumulative_judgment_quality"] == {
        "learning_sample_floor": 1,
        "learning_sample_count": 1,
        "learning_updated": True,
        "learning_update_policy": (
            "one_mature_split_variant_outcome_updates_cumulative_judgment_quality"
        ),
        "equal_weight_avg_profit_pct": 1.25,
        "runtime_promotion_sample_floor": {
            "real_submit": 20,
            "real_split_variant_outcome": 20,
            "minimum_cost_adjusted_ev_pct": 0.1,
        },
        "split_variant_quality": [
            {
                "split_variant_id": "equal_50_50_offset_0pct_0_3pct",
                "sample_count": 1,
                "equal_weight_avg_profit_pct": 1.25,
                "learning_sample_floor": 1,
                "learning_updated": True,
                "runtime_promotion_sample_floor": 20,
                "runtime_promotion_sample_ready": False,
                "downside_p10_profit_rate": 1.25,
                "runtime_evidence_ready": False,
                "runtime_promotion_requires_shape_provenance": True,
            }
        ],
        "learning_floor_grants_runtime_promotion": False,
    }
    assert balanced["candidate_passed"] is False
    assert report["recommended_policy"]["runtime_apply_allowed"] is False


def test_quality_counts_deduplicates_submit_lifecycle_and_ignores_propagated_flag():
    events = [
        {
            "source_date": "2026-07-07",
            "stage": "order_bundle_submitted",
            "record_id": 123,
            "stock_code": "005930",
            "actual_order_submitted": True,
            "broker_order_submitted": True,
            "requested_qty": 2,
            "spread_bps": 18,
            "buy_pressure_10t": 55,
        },
        {
            "source_date": "2026-07-07",
            "stage": "order_leg_sent",
            "record_id": 123,
            "stock_code": "005930",
            "actual_order_submitted": True,
            "broker_order_submitted": True,
            "requested_qty": 2,
            "spread_bps": 18,
            "buy_pressure_10t": 55,
        },
        {
            "source_date": "2026-07-07",
            "stage": "sell_completed",
            "record_id": 123,
            "stock_code": "005930",
            "actual_order_submitted": True,
            "spread_bps": 18,
            "buy_pressure_10t": 55,
        },
    ]

    counts, excluded = split_plan._quality_counts(
        events, {"tuning_input_allowed": True}
    )

    assert excluded == 0
    assert counts["balanced_normal"]["real_sample_count"] == 1
    assert counts["balanced_normal"]["real_submitted_count"] == 1


def test_quality_counts_keeps_one_share_submit_out_of_split_eligible_denominator():
    counts, excluded = split_plan._quality_counts(
        [
            {
                "source_date": "2026-07-07",
                "stage": "order_bundle_submitted",
                "record_id": 123,
                "stock_code": "005930",
                "actual_order_submitted": True,
                "broker_order_submitted": True,
                "requested_qty": 1,
                "spread_bps": 18,
                "buy_pressure_10t": 55,
            }
        ],
        {"tuning_input_allowed": True},
    )

    assert excluded == 0
    assert counts["balanced_normal"]["real_observed_entry_count"] == 1
    assert counts["balanced_normal"].get("real_sample_count", 0) == 0


def test_split_variant_uses_parent_policy_identity_and_keeps_child_diagnostic():
    fields = {
        "entry_split_order_policy_variant_id": "parent-policy",
        "entry_split_order_variant_id": "parent-policy__runtime_first_weight_40",
    }

    assert split_plan._split_variant_id_from_fields(fields) == "parent-policy"
    assert (
        split_plan._split_child_variant_id_from_fields(fields)
        == "parent-policy__runtime_first_weight_40"
    )


def test_split_variant_recovers_parent_from_known_historical_runtime_suffixes():
    historical_child = (
        "equal_50_50_offset_0pct_0_3pct"
        "__qty_clipped_legs1__runtime_first_weight_40"
        f"__{split_plan.PROBE_VARIANT_SUFFIX}"
    )
    fields = {"entry_split_order_variant_id": historical_child}

    assert split_plan._split_variant_id_from_fields(fields) == (
        "equal_50_50_offset_0pct_0_3pct"
    )
    assert split_plan._split_child_variant_id_from_fields(fields) == historical_child


def test_build_report_uses_prior_cumulative_state_for_daily_increment(
    monkeypatch, tmp_path
):
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    source_date = "2026-07-06"
    target_date = "2026-07-07"
    for day, record_id, profit_rate in (
        (source_date, 100, 1.0),
        (target_date, 200, 2.0),
    ):
        _write_jsonl(
            data_dir / "pipeline_events" / f"pipeline_events_{day}.jsonl",
            [
                {
                    "date": day,
                    "stage": "order_bundle_submitted",
                    "record_id": record_id,
                    "actual_order_submitted": True,
                    "broker_order_submitted": True,
                    "spread_bps": 18,
                    "buy_pressure_10t": 55,
                    "entry_split_order_variant_id": ("equal_50_50_offset_0pct_0_3pct"),
                }
            ],
        )
        _write_jsonl(
            data_dir / "post_sell" / f"post_sell_evaluations_{day}.jsonl",
            [
                {
                    "date": day,
                    "recommendation_id": record_id,
                    "actual_order_submitted": True,
                    "profit_rate": profit_rate,
                    "spread_bps": 18,
                    "buy_pressure_10t": 55,
                    "entry_split_order_variant_id": ("equal_50_50_offset_0pct_0_3pct"),
                }
            ],
        )
        source_quality_path = (
            data_dir
            / "report"
            / "observation_source_quality_audit"
            / f"observation_source_quality_audit_{day}.json"
        )
        source_quality_path.parent.mkdir(parents=True, exist_ok=True)
        source_quality_path.write_text(
            json.dumps(
                {
                    "status": "warning",
                    "summary": {"tuning_input_allowed": True},
                }
            ),
            encoding="utf-8",
        )

    split_plan.build_report(source_date, write=True)
    (data_dir / "pipeline_events" / f"pipeline_events_{source_date}.jsonl").unlink()
    (data_dir / "post_sell" / f"post_sell_evaluations_{source_date}.jsonl").unlink()

    report = split_plan.build_report(target_date, write=False)

    balanced = next(
        item
        for item in report["candidate_grid"]
        if item["context_bucket"] == "balanced_normal"
    )
    assert (
        report["input_summary"]["aggregation_mode"]
        == "incremental_gap_replay_from_prior_cumulative_state"
    )
    assert report["input_summary"]["source_dates"] == [source_date, target_date]
    assert report["cumulative_state"]["through_date"] == target_date
    assert report["cumulative_state"]["clean_tuning_baseline_date"] == "2026-06-05"
    assert balanced["real_sample_count"] == 2
    assert balanced["cumulative_judgment_quality"]["learning_sample_count"] == 2
    assert balanced["cumulative_judgment_quality"]["equal_weight_avg_profit_pct"] == 1.5


def test_prior_cumulative_state_survives_equivalent_source_quality_refresh(
    monkeypatch, tmp_path
):
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    source_date = "2026-07-06"
    source_quality_path = (
        data_dir
        / "report"
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{source_date}.json"
    )
    source_quality_path.parent.mkdir(parents=True, exist_ok=True)
    source_quality_path.write_text(
        json.dumps(
            {
                "status": "pass",
                "summary": {"tuning_input_allowed": True},
            }
        ),
        encoding="utf-8",
    )
    report_path = split_plan.REPORT_DIR / f"entry_split_order_plan_{source_date}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "schema_version": split_plan.SCHEMA_VERSION,
                "cumulative_state": {
                    "schema_version": split_plan.CUMULATIVE_STATE_SCHEMA_VERSION,
                    "window_policy": ("clean_baseline_cumulative_through_target_date"),
                    "through_date": source_date,
                    "clean_tuning_baseline_date": "2026-06-05",
                    "source_dates": [source_date],
                    "source_quality_contract_bindings": (
                        split_plan._source_quality_contract_bindings([source_date])
                    ),
                },
            }
        ),
        encoding="utf-8",
    )
    os.utime(report_path, (1, 1))

    state, state_path = split_plan._latest_prior_cumulative_state("2026-07-07")

    assert state["through_date"] == source_date
    assert state_path == str(report_path)


def test_build_report_replays_all_dates_after_latest_complete_cumulative_state(
    monkeypatch, tmp_path
):
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    source_dates = ["2026-07-06", "2026-07-07", "2026-07-08"]
    for index, source_date in enumerate(source_dates, start=1):
        _write_jsonl(
            data_dir / "pipeline_events" / f"pipeline_events_{source_date}.jsonl",
            [
                {
                    "date": source_date,
                    "stage": "order_bundle_submitted",
                    "record_id": index,
                    "stock_code": f"{index:06d}",
                    "actual_order_submitted": True,
                    "broker_order_submitted": True,
                    "requested_qty": 2,
                    "spread_bps": 18,
                    "buy_pressure_10t": 55,
                    "entry_split_order_policy_variant_id": "parent-policy",
                    "entry_split_order_variant_id": "parent-policy__runtime",
                }
            ],
        )
        quality_path = (
            data_dir
            / "report"
            / "observation_source_quality_audit"
            / f"observation_source_quality_audit_{source_date}.json"
        )
        quality_path.parent.mkdir(parents=True, exist_ok=True)
        quality_path.write_text(
            json.dumps({"status": "pass", "summary": {"tuning_input_allowed": True}}),
            encoding="utf-8",
        )

    split_plan.build_report(source_dates[0], write=True)
    incomplete_path = (
        split_plan.REPORT_DIR / f"entry_split_order_plan_{source_dates[1]}.json"
    )
    incomplete_path.write_text(
        json.dumps(
            {
                "schema_version": split_plan.SCHEMA_VERSION,
                "cumulative_state": {
                    "schema_version": split_plan.CUMULATIVE_STATE_SCHEMA_VERSION,
                    "window_policy": "clean_baseline_cumulative_through_target_date",
                    "through_date": source_dates[1],
                    "clean_tuning_baseline_date": "2026-06-05",
                    "source_dates": [source_dates[1]],
                },
            }
        ),
        encoding="utf-8",
    )

    report = split_plan.build_report(source_dates[2], write=False)
    balanced = next(
        row
        for row in report["candidate_grid"]
        if row["context_bucket"] == "balanced_normal"
    )

    assert report["input_summary"]["replayed_source_dates"] == source_dates[1:]
    assert report["input_summary"]["source_dates"] == source_dates
    assert balanced["real_sample_count"] == 3


def test_prior_cumulative_state_is_rejected_after_source_quality_contract_change(
    monkeypatch, tmp_path
):
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    source_date = "2026-07-06"
    source_quality_path = (
        data_dir
        / "report"
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{source_date}.json"
    )
    source_quality_path.parent.mkdir(parents=True, exist_ok=True)
    source_quality_path.write_text(
        json.dumps({"status": "pass", "summary": {"tuning_input_allowed": True}}),
        encoding="utf-8",
    )
    binding = split_plan._source_quality_contract_bindings([source_date])
    report_path = split_plan.REPORT_DIR / f"entry_split_order_plan_{source_date}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "schema_version": split_plan.SCHEMA_VERSION,
                "cumulative_state": {
                    "schema_version": split_plan.CUMULATIVE_STATE_SCHEMA_VERSION,
                    "window_policy": "clean_baseline_cumulative_through_target_date",
                    "through_date": source_date,
                    "clean_tuning_baseline_date": "2026-06-05",
                    "source_dates": [source_date],
                    "source_quality_contract_bindings": binding,
                },
            }
        ),
        encoding="utf-8",
    )
    source_quality_path.write_text(
        json.dumps(
            {
                "status": "warning",
                "summary": {
                    "tuning_input_allowed": True,
                    "hard_blocking_stages": ["changed_stage"],
                },
            }
        ),
        encoding="utf-8",
    )

    state, state_path = split_plan._latest_prior_cumulative_state("2026-07-07")

    assert state == {}
    assert state_path == ""


def test_prior_cumulative_state_requires_complete_source_quality_bindings(
    monkeypatch, tmp_path
):
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    source_date = "2026-07-06"
    source_quality_path = (
        data_dir
        / "report"
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{source_date}.json"
    )
    source_quality_path.parent.mkdir(parents=True, exist_ok=True)
    source_quality_path.write_text(
        json.dumps({"status": "pass", "summary": {"tuning_input_allowed": True}}),
        encoding="utf-8",
    )
    report_path = split_plan.REPORT_DIR / f"entry_split_order_plan_{source_date}.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        json.dumps(
            {
                "schema_version": split_plan.SCHEMA_VERSION,
                "cumulative_state": {
                    "schema_version": split_plan.CUMULATIVE_STATE_SCHEMA_VERSION,
                    "window_policy": "clean_baseline_cumulative_through_target_date",
                    "through_date": source_date,
                    "clean_tuning_baseline_date": "2026-06-05",
                    "source_dates": [source_date],
                    "source_quality_contract_bindings": {},
                },
            }
        ),
        encoding="utf-8",
    )

    state, state_path = split_plan._latest_prior_cumulative_state("2026-07-07")

    assert state == {}
    assert state_path == ""


def test_build_report_creates_bounded_equal_baseline_without_real_outcome(
    monkeypatch, tmp_path
):
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    target_date = "2026-09-04"
    _write_jsonl(
        data_dir / "pipeline_events" / f"pipeline_events_{target_date}.jsonl",
        [
            {
                "date": target_date,
                "stage": "order_leg_sent",
                "actual_order_submitted": True,
                "broker_order_submitted": True,
                "requested_qty": 2,
                "spread_bps": 18,
                "buy_pressure_10t": 55,
            }
            for _ in range(20)
        ],
    )
    source_quality_path = (
        data_dir
        / "report"
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{target_date}.json"
    )
    source_quality_path.parent.mkdir(parents=True, exist_ok=True)
    source_quality_path.write_text(
        json.dumps({"status": "warning", "summary": {"tuning_input_allowed": True}}),
        encoding="utf-8",
    )

    report = split_plan.build_report(target_date, write=True)

    balanced = next(
        item
        for item in report["candidate_grid"]
        if item["context_bucket"] == "balanced_normal"
    )
    assert balanced["real_sample_count"] == 20
    assert balanced["real_outcome_joined_sample"] == 0
    assert balanced["candidate_passed"] is True
    assert balanced["policy_mode"] == "bounded_equal_split_baseline"
    assert balanced["leg_count"] == 2
    assert balanced["price_offsets_ticks"] == [0, 1]
    assert balanced["qty_weight_min"] == 0.5
    assert balanced["qty_weight_max"] == 0.5
    assert balanced["source_quality_adjusted_ev_pct"] is None
    assert report["recommended_policy"]["candidate_count"] == 1
    policy = json.loads(split_plan.policy_path(target_date).read_text(encoding="utf-8"))
    assert policy["baseline_runtime_defaults_enabled"] is True
    assert policy["explicit_bucket_count"] == 0
    assert policy["buckets"] == {}

    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE",
        str(split_plan.policy_path(target_date)),
    )
    orders, fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 2, "price": 1000}],
        latency_gate={
            "spread_bps": 18,
            "buy_pressure_10t": 55,
            "latency_state": "SAFE",
            "quote_stale": False,
            "order_price": 1000,
        },
        now=datetime(2026, 9, 5, 8, tzinfo=timezone(timedelta(hours=9))),
    )
    assert fields["entry_split_order_policy_applied"] is True
    assert [item["qty"] for item in orders] == [1, 1]
    assert fields["entry_split_order_price_offsets_pct"] == "0.0,0.3"
    assert [item["price"] for item in orders] == [1000, 997]
    assert (
        fields["entry_split_order_policy_variant_id"]
        == split_plan.RUNTIME_FALLBACK_VARIANT_ID
    )
    assert fields["entry_split_order_variant_id"] == (
        f"{split_plan.RUNTIME_FALLBACK_VARIANT_ID}__runtime_first_weight_40"
    )
    assert fields["entry_split_order_runtime_default_policy_applied"] is True
    assert fields["entry_split_order_runtime_weight_adjustment_applied"] is True


@pytest.mark.parametrize(
    ("profit_rate", "expected_promoted"),
    [(1.4, True), (0.05, False)],
)
def test_build_report_uses_split_variant_outcome_as_primary_ev(
    monkeypatch, tmp_path, profit_rate, expected_promoted
):
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    target_date = "2026-07-07"
    _write_jsonl(
        data_dir / "pipeline_events" / f"pipeline_events_{target_date}.jsonl",
        [
            {
                "date": target_date,
                "stage": "order_leg_sent",
                "actual_order_submitted": True,
                "broker_order_submitted": True,
                "spread_bps": 18,
                "buy_pressure_10t": 55,
            }
            for _ in range(20)
        ],
    )
    source_quality_path = (
        data_dir
        / "report"
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{target_date}.json"
    )
    source_quality_path.parent.mkdir(parents=True, exist_ok=True)
    source_quality_path.write_text(
        json.dumps({"status": "warning", "summary": {"tuning_input_allowed": True}}),
        encoding="utf-8",
    )
    _write_jsonl(
        data_dir / "post_sell" / f"post_sell_evaluations_{target_date}.jsonl",
        [
            {
                "date": target_date,
                "actual_order_submitted": True,
                "profit_rate": profit_rate,
                "spread_bps": 18,
                "buy_pressure_10t": 55,
                "entry_split_order_policy_applied": True,
                "entry_split_order_variant_id": "equal_50_50_offset_0pct_0_3pct",
                "entry_split_order_policy_mode": "bounded_equal_split_baseline",
                "entry_split_order_leg_count": 2,
                "entry_split_order_price_offsets_ticks": "0,1",
                "entry_split_order_qty_weight_min": 0.5,
            }
            for _ in range(20)
        ],
    )

    report = split_plan.build_report(target_date, write=True)

    balanced = next(
        item
        for item in report["candidate_grid"]
        if item["context_bucket"] == "balanced_normal"
    )
    assert balanced["primary_sample_book"] == "real_split_variant"
    assert balanced["real_split_variant_outcome_joined_sample"] == 20
    assert balanced["source_quality_adjusted_ev_pct"] == profit_rate
    assert balanced["candidate_passed"] is expected_promoted
    assert balanced["exploration_seed_allowed"] is False
    assert balanced["ev_validated_runtime_apply_allowed"] is expected_promoted
    if expected_promoted:
        assert balanced["policy_mode"] == "real_primary_ev_optimized"
        assert balanced["runtime_apply_authority_class"] == "ev_validated_variant"
        assert (
            report["recommended_policy"]["ev_validated_runtime_apply_allowed"] is True
        )
    else:
        assert balanced["policy_mode"] == ""
        assert balanced["runtime_apply_authority_class"] == "none"
        assert (
            report["recommended_policy"]["ev_validated_runtime_apply_allowed"] is False
        )


def test_build_report_uses_post_submit_low_tick_band_for_price_offsets(
    monkeypatch, tmp_path
):
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    target_date = "2026-07-07"
    rows = []
    for idx in range(20):
        rows.append(
            {
                "date": target_date,
                "emitted_at": f"{target_date}T09:{idx:02d}:00",
                "stage": "order_bundle_submitted",
                "record_id": 2000 + idx,
                "stock_code": f"T{idx:05d}"[:6],
                "actual_order_submitted": True,
                "broker_order_submitted": True,
                "requested_qty": 2,
                "order_price": 10000,
                "spread_bps": 18,
                "buy_pressure_10t": 55,
            }
        )
        rows.append(
            {
                "date": target_date,
                "emitted_at": f"{target_date}T09:{idx:02d}:30",
                "stage": "holding_price_observed",
                "record_id": 2000 + idx,
                "stock_code": f"T{idx:05d}"[:6],
                "actual_order_submitted": False,
                "current_price_observed": 9980,
                "spread_bps": 18,
                "buy_pressure_10t": 55,
            }
        )
    _write_jsonl(
        data_dir / "pipeline_events" / f"pipeline_events_{target_date}.jsonl", rows
    )
    source_quality_path = (
        data_dir
        / "report"
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{target_date}.json"
    )
    source_quality_path.parent.mkdir(parents=True, exist_ok=True)
    source_quality_path.write_text(
        json.dumps({"status": "warning", "summary": {"tuning_input_allowed": True}}),
        encoding="utf-8",
    )

    report = split_plan.build_report(target_date, write=True)

    balanced = next(
        item
        for item in report["candidate_grid"]
        if item["context_bucket"] == "balanced_normal"
    )
    assert balanced["policy_mode"] == "post_submit_tick_band_seed"
    assert balanced["optimization_basis"] == "post_submit_observed_low_tick_band"
    assert balanced["leg_count"] == 3
    assert balanced["price_offsets_ticks"] == [0, 1, 2]
    assert balanced["qty_weight_min"] == 0.34
    assert balanced["post_submit_low_tick_band"]["sample_count"] == 20
    assert balanced["post_submit_low_tick_band"]["p75_down_ticks"] == 2.0
    policy = json.loads(split_plan.policy_path(target_date).read_text(encoding="utf-8"))
    assert (
        policy["buckets"]["balanced_normal"]["policy_mode"]
        == "post_submit_tick_band_seed"
    )
    assert policy["buckets"]["balanced_normal"]["price_offsets_ticks"] == [0, 1, 2]
    assert policy["explicit_bucket_count"] == 1


def test_post_submit_tick_band_excludes_source_quality_hard_blocked_rows(
    monkeypatch, tmp_path
):
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    target_date = "2026-07-07"
    rows = []
    for idx in range(20):
        rows.append(
            {
                "date": target_date,
                "emitted_at": f"{target_date}T09:{idx:02d}:00+09:00",
                "stage": "order_bundle_submitted",
                "record_id": 3000 + idx,
                "stock_code": f"B{idx:05d}"[:6],
                "actual_order_submitted": True,
                "broker_order_submitted": True,
                "requested_qty": 2,
                "order_price": 10000,
                "spread_bps": 18,
                "buy_pressure_10t": 55,
            }
        )
        rows.append(
            {
                "date": target_date,
                "emitted_at": f"{target_date}T09:{idx:02d}:30+09:00",
                "stage": "hard_blocked_price_observed",
                "record_id": 3000 + idx,
                "stock_code": f"B{idx:05d}"[:6],
                "current_price_observed": 9980,
                "spread_bps": 18,
                "buy_pressure_10t": 55,
            }
        )
    _write_jsonl(
        data_dir / "pipeline_events" / f"pipeline_events_{target_date}.jsonl", rows
    )
    source_quality_path = (
        data_dir
        / "report"
        / "observation_source_quality_audit"
        / f"observation_source_quality_audit_{target_date}.json"
    )
    source_quality_path.parent.mkdir(parents=True, exist_ok=True)
    source_quality_path.write_text(
        json.dumps(
            {
                "status": "warning",
                "summary": {
                    "tuning_input_allowed": True,
                    "hard_blocking_stages": ["hard_blocked_price_observed"],
                    "raw_row_exclusion_applied": True,
                },
            }
        ),
        encoding="utf-8",
    )

    report = split_plan.build_report(target_date, write=True)

    balanced = next(
        item
        for item in report["candidate_grid"]
        if item["context_bucket"] == "balanced_normal"
    )
    assert balanced["post_submit_low_tick_band"] == {}
    assert balanced["policy_mode"] == "bounded_equal_split_baseline"
    assert balanced["price_offsets_ticks"] == [0, 1]


def test_post_submit_tick_band_stream_prefilters_unrelated_price_rows(
    monkeypatch, tmp_path
):
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    target_date = "2026-07-07"
    submit = {
        "date": target_date,
        "emitted_at": f"{target_date}T09:00:00+09:00",
        "stage": "order_bundle_submitted",
        "record_id": 4000,
        "stock_code": "T04000",
        "actual_order_submitted": True,
        "broker_order_submitted": True,
        "requested_qty": 2,
        "order_price": 10000,
        "spread_bps": 18,
        "buy_pressure_10t": 55,
    }
    rows = [submit]
    rows.extend(
        {
            "date": target_date,
            "emitted_at": f"{target_date}T09:00:10+09:00",
            "stage": "holding_price_observed",
            "record_id": 5000 + index,
            "stock_code": f"U{index:05d}"[:6],
            "current_price_observed": 9990,
        }
        for index in range(100)
    )
    rows.append(
        {
            "date": target_date,
            "emitted_at": f"{target_date}T09:00:30+09:00",
            "stage": "holding_price_observed",
            "record_id": 4000,
            "stock_code": "T04000",
            "current_price_observed": 9980,
        }
    )
    _write_jsonl(
        data_dir / "pipeline_events" / f"pipeline_events_{target_date}.jsonl",
        rows,
    )

    events, _summary = split_plan._iter_input_events(target_date)
    bands, scan = split_plan._build_post_submit_low_tick_bands_from_sources(
        target_date,
        events,
    )

    assert len(events) == 1
    assert bands["balanced_normal"]["sample_count"] == 1
    assert bands["balanced_normal"]["p75_down_ticks"] == 2.0
    assert bands["balanced_normal"]["p50_down_pct"] == 0.2
    assert bands["balanced_normal"]["p90_down_pct"] == 0.2
    assert bands["balanced_normal"]["touch_0_3pct_rate"] == 0.0
    assert bands["balanced_normal"]["no_pullback_rate"] == 0.0
    assert scan["raw_line_count"] == 102
    assert scan["price_token_line_count"] == 101
    assert scan["record_candidate_line_count"] == 1
    assert scan["parsed_observation_count"] == 1
    assert scan["retained_price_event_count"] == 0


def test_post_sell_candidate_preserves_entry_split_variant_metadata(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(post_sell_feedback, "DATA_DIR", tmp_path / "data")
    post_sell_feedback._RECORDED_KEYS.clear()
    stock = {
        "name": "TEST",
        "strategy": "SCALPING",
        "fast_exit_decision_mark_price": 1012,
        "fast_exit_decision_executable_sell_price": 1010,
        "fast_exit_decision_peak_price": 1020,
        "fast_exit_decision_quote_state": "consistent",
        "fast_exit_decision_quote_reason": "ok",
        "pending_entry_orders": [
            {
                "entry_split_order_policy_applied": True,
                "entry_split_order_bucket": "balanced_normal",
                "entry_split_order_policy_version": "entry_split_order_plan:test",
                "entry_split_order_policy_mode": "bounded_equal_split_baseline",
                "entry_split_order_variant_id": "equal_50_50_offset_0pct_0_3pct",
                "entry_split_order_leg_count": 2,
                "entry_split_order_price_offsets_ticks": "0,1",
                "entry_split_order_qty_weight_min": 0.5,
                "entry_split_order_qty_weight_max": 0.5,
                "entry_split_order_runtime_default_policy_applied": True,
            }
        ],
    }

    payload = post_sell_feedback.record_post_sell_candidate(
        recommendation_id=123,
        stock=stock,
        code="000001",
        sell_time=datetime(2026, 7, 7, 10, 30, tzinfo=timezone(timedelta(hours=9))),
        buy_price=1000,
        sell_price=1010,
        profit_rate=1.0,
        buy_qty=2,
        exit_rule="test_exit",
        strategy="SCALPING",
    )

    assert payload is not None
    assert payload["actual_order_submitted"] is True
    assert payload["entry_split_order_policy_applied"] is True
    assert payload["entry_split_order_variant_id"] == "equal_50_50_offset_0pct_0_3pct"
    assert payload["entry_split_order_price_offsets_ticks"] == "0,1"
    assert payload["entry_split_order_runtime_default_policy_applied"] is True
    assert payload["exit_decision_mark_price"] == 1012
    assert payload["exit_decision_executable_sell_price"] == 1010
    assert payload["exit_decision_peak_price"] == 1020
    assert payload["actual_fill_price"] == 1010


def test_post_sell_candidate_prefers_standard_exit_decision_provenance(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(post_sell_feedback, "DATA_DIR", tmp_path / "data")
    post_sell_feedback._RECORDED_KEYS.clear()
    stock = {
        "name": "LG전자",
        "strategy": "SCALPING",
        "last_exit_decision_source": "HOLDING_FLOW_OVERRIDE",
        "exit_decision_mark_price": 184_000,
        "exit_decision_executable_sell_price": 184_000,
        "exit_decision_peak_price": 184_100,
        "exit_decision_quote_state": "single_source",
        "exit_decision_quote_reason": "rest_only_fresh",
        "fast_exit_decision_mark_price": 1,
    }

    payload = post_sell_feedback.record_post_sell_candidate(
        recommendation_id=23086,
        stock=stock,
        code="066570",
        sell_time=datetime(2026, 7, 23, 12, 52, 55),
        buy_price=182_350,
        sell_price=184_000,
        profit_rate=0.67,
        buy_qty=1,
        exit_rule="scalp_low_profit_stagnation_hard_exit",
        strategy="SCALPING",
    )

    assert payload is not None
    assert payload["exit_decision_mark_price"] == 184_000
    assert payload["exit_decision_executable_sell_price"] == 184_000
    assert payload["exit_decision_peak_price"] == 184_100
    assert payload["exit_decision_quote_state"] == "single_source"
    assert payload["exit_decision_quote_reason"] == "rest_only_fresh"


def test_allocator_preserves_qty_and_respects_leg_limits(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target_date = datetime.now(timezone(timedelta(hours=9))).date().isoformat()
    policy_file = split_plan.policy_path(target_date)
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "test-policy",
                "source_date": target_date,
                "buckets": {
                    "urgent_tight_spread": {
                        "leg_count": 3,
                        "price_offsets_ticks": [0, 1, 2],
                        "qty_weight_min": 0.6,
                        "qty_weight_max": 0.8,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(policy_file))

    orders, fields = split_plan.apply_entry_split_order_policy(
        [
            {
                "tag": "normal",
                "qty": 5,
                "price": 1000,
                "order_type_code": "00",
                "tif": "DAY",
            }
        ],
        stock={"buy_pressure_10t": 75},
        latency_gate={
            "spread_bps": 5,
            "latency_state": "SAFE",
            "quote_stale": False,
            "order_price": 1000,
        },
    )

    assert fields["entry_split_order_policy_applied"] is True
    assert len(orders) == 2
    assert sum(item["qty"] for item in orders) == 5
    assert min(item["qty"] for item in orders) >= 1
    assert orders[0]["price"] >= orders[1]["price"]


def test_allocator_uses_runtime_default_for_missing_bucket_policy(
    monkeypatch, tmp_path
):
    _patch_dirs(monkeypatch, tmp_path)
    target_date = datetime.now(timezone(timedelta(hours=9))).date().isoformat()
    policy_file = split_plan.policy_path(target_date)
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "test-policy",
                "source_date": target_date,
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(policy_file))

    orders, fields = split_plan.apply_entry_split_order_policy(
        [
            {
                "tag": "normal",
                "qty": 7,
                "price": 1000,
                "order_type_code": "00",
                "tif": "DAY",
            }
        ],
        latency_gate={
            "spread_bps": 18,
            "buy_pressure_10t": 55,
            "latency_state": "SAFE",
            "order_price": 1000,
        },
    )

    assert fields["entry_split_order_policy_applied"] is True
    assert fields["entry_split_order_runtime_default_policy_applied"] is True
    assert (
        fields["entry_split_order_policy_mode"]
        == "runtime_default_passive_center_40_60_0_3pct"
    )
    assert (
        fields["entry_split_order_policy_variant_id"]
        == "runtime_default_passive_center_40_60_offset_0pct_0_3pct"
    )
    assert (
        fields["entry_split_order_variant_id"]
        == "runtime_default_passive_center_40_60_offset_0pct_0_3pct__runtime_first_weight_40"
    )
    assert fields["entry_split_order_price_offsets_ticks"] == "0,1"
    assert fields["entry_split_order_price_offsets_pct"] == "0.0,0.3"
    assert fields["entry_split_order_policy_original_qty_weight_min"] == 0.5
    assert fields["entry_split_order_qty_weight_min"] == 0.4
    assert fields["entry_split_order_qty_weight_max"] == 0.4
    assert fields["entry_split_order_runtime_weight_adjustment_applied"] is True
    assert (
        fields["entry_split_order_passive_bias_reason"]
        == "passive_center_first_leg_cap"
    )
    assert [item["qty"] for item in orders] == [3, 4]
    assert [item["price"] for item in orders] == [1000, 997]


def test_allocator_uses_three_leg_runtime_default_for_missing_passive_bucket(
    monkeypatch, tmp_path
):
    _patch_dirs(monkeypatch, tmp_path)
    target_date = datetime.now(timezone(timedelta(hours=9))).date().isoformat()
    policy_file = split_plan.policy_path(target_date)
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "test-policy",
                "source_date": target_date,
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(policy_file))
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_MARKET_FIRST_LEG_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_SPLIT_MARKET_FIRST_LEG_ACTIVE_DATE", target_date
    )

    orders, fields = split_plan.apply_entry_split_order_policy(
        [
            {
                "tag": "normal",
                "qty": 10,
                "price": 1000,
                "order_type_code": "00",
                "tif": "DAY",
            }
        ],
        latency_gate={
            "spread_bps": 45,
            "buy_pressure_10t": 40,
            "latency_state": "SAFE",
            "order_price": 1000,
        },
    )

    assert fields["entry_split_order_policy_applied"] is True
    assert fields["entry_split_order_runtime_default_policy_applied"] is True
    assert fields["entry_split_order_policy_requested_leg_count"] == 3
    assert fields["entry_split_order_leg_count"] == 3
    assert fields["entry_split_order_leg_count_clipped"] is False
    assert [item["qty"] for item in orders] == [5, 2, 3]
    assert [item["price"] for item in orders] == [1000, 997, 992]
    assert [item["order_type_code"] for item in orders] == ["3", "00", "00"]
    assert [item["entry_split_order_execution_mode"] for item in orders] == [
        "market_first",
        "resolver_limit",
        "resolver_limit",
    ]
    assert sum(item["qty"] for item in orders) == 10


def test_allocator_records_qty_clipping_for_three_leg_entry_policy(
    monkeypatch, tmp_path
):
    _patch_dirs(monkeypatch, tmp_path)
    target_date = datetime.now(timezone(timedelta(hours=9))).date().isoformat()
    policy_file = split_plan.policy_path(target_date)
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "test-policy",
                "source_date": target_date,
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(policy_file))

    orders, fields = split_plan.apply_entry_split_order_policy(
        [
            {
                "tag": "normal",
                "qty": 4,
                "price": 1000,
                "order_type_code": "00",
                "tif": "DAY",
            }
        ],
        latency_gate={
            "spread_bps": 45,
            "buy_pressure_10t": 40,
            "latency_state": "SAFE",
            "order_price": 1000,
        },
    )

    assert len(orders) == 2
    assert fields["entry_split_order_policy_requested_leg_count"] == 3
    assert fields["entry_split_order_max_leg_count_for_qty"] == 2
    assert fields["entry_split_order_leg_count_clipped"] is True
    assert fields["entry_split_order_variant_id"].endswith(
        "__qty_clipped_legs2__runtime_first_weight_40"
    )
    assert sum(item["qty"] for item in orders) == 4


def test_allocator_biases_ai_wait_high_spread_to_passive_leg(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target_date = datetime.now(timezone(timedelta(hours=9))).date().isoformat()
    policy_file = split_plan.policy_path(target_date)
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "test-policy",
                "source_date": target_date,
                "buckets": {
                    "passive_wide_or_weak": {
                        "leg_count": 2,
                        "price_offsets_ticks": [0, 1],
                        "price_offsets_pct": [0.0, 0.3],
                        "qty_weight_min": 0.5,
                        "qty_weight_max": 0.5,
                        "policy_mode": "bounded_equal_split_baseline",
                        "split_variant_id": "equal_50_50_offset_0pct_0_3pct",
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(policy_file))

    orders, fields = split_plan.apply_entry_split_order_policy(
        [
            {
                "tag": "normal",
                "qty": 5,
                "price": 1000,
                "order_type_code": "00",
                "tif": "DAY",
            }
        ],
        latency_gate={
            "spread_bps": 45,
            "buy_pressure_10t": 50,
            "latency_state": "SAFE",
            "quote_stale": False,
            "pre_submit_effective_quote_stale": False,
            "entry_ai_submit_authority_action": "WAIT",
            "reason": "mixed signals with stale quote and high spread",
            "order_price": 1000,
        },
    )

    assert fields["entry_split_order_policy_applied"] is True
    assert fields["entry_split_order_passive_bias_applied"] is True
    assert (
        fields["entry_split_order_policy_variant_id"]
        == "equal_50_50_offset_0pct_0_3pct"
    )
    assert (
        fields["entry_split_order_variant_id"]
        == "equal_50_50_offset_0pct_0_3pct__runtime_first_weight_20"
    )
    assert fields["entry_split_order_policy_original_qty_weight_min"] == 0.5
    assert fields["entry_split_order_qty_weight_min"] == 0.2
    assert fields["entry_split_order_qty_weight_max"] == 0.2
    assert fields["entry_split_order_runtime_weight_adjustment_applied"] is True
    assert fields["entry_split_order_passive_bias_reason"].startswith("ai_wait_with_")
    assert [item["qty"] for item in orders] == [1, 4]
    assert [item["price"] for item in orders] == [1000, 997]
    assert sum(item["qty"] for item in orders) == 5


def test_allocator_passive_centers_buy_action_without_wait_warning(
    monkeypatch, tmp_path
):
    _patch_dirs(monkeypatch, tmp_path)
    target_date = datetime.now(timezone(timedelta(hours=9))).date().isoformat()
    policy_file = split_plan.policy_path(target_date)
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "test-policy",
                "source_date": target_date,
                "buckets": {
                    "passive_wide_or_weak": {
                        "leg_count": 2,
                        "price_offsets_ticks": [0, 1],
                        "price_offsets_pct": [0.0, 0.3],
                        "qty_weight_min": 0.5,
                        "qty_weight_max": 0.5,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(policy_file))

    orders, fields = split_plan.apply_entry_split_order_policy(
        [
            {
                "tag": "normal",
                "qty": 5,
                "price": 1000,
                "order_type_code": "00",
                "tif": "DAY",
            }
        ],
        latency_gate={
            "spread_bps": 45,
            "buy_pressure_10t": 50,
            "latency_state": "SAFE",
            "entry_ai_submit_authority_action": "BUY",
            "reason": "high spread but positive entry confirmation",
            "order_price": 1000,
        },
    )

    assert fields["entry_split_order_policy_applied"] is True
    assert fields["entry_split_order_passive_bias_applied"] is True
    assert (
        fields["entry_split_order_passive_bias_reason"]
        == "passive_center_first_leg_cap"
    )
    assert fields["entry_split_order_policy_original_qty_weight_min"] == 0.5
    assert fields["entry_split_order_qty_weight_min"] == 0.4
    assert fields["entry_split_order_qty_weight_max"] == 0.4
    assert fields["entry_split_order_runtime_weight_adjustment_applied"] is True
    assert [item["qty"] for item in orders] == [2, 3]


def test_allocator_market_first_uses_policy_weight_and_keeps_residual_at_resolver(
    monkeypatch, tmp_path
):
    _patch_dirs(monkeypatch, tmp_path)
    target_date = "2026-07-14"
    policy_file = split_plan.policy_path(target_date)
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "test-market-first",
                "source_date": "2026-07-13",
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ACTIVE_DATE", target_date)
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(policy_file))
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_MARKET_FIRST_LEG_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_SPLIT_MARKET_FIRST_LEG_ACTIVE_DATE", target_date
    )

    orders, fields = split_plan.apply_entry_split_order_policy(
        [
            {
                "tag": "normal",
                "qty": 32,
                "price": 12160,
                "order_type_code": "00",
                "tif": "DAY",
            }
        ],
        latency_gate={
            "spread_bps": 41.017,
            "buy_pressure_10t": 50,
            "latency_state": "CAUTION",
            "quote_stale_at_submit": False,
            "entry_ai_submit_authority_action": "WAIT",
            "best_ask_at_submit": 12240,
            "order_price": 12160,
        },
        now=datetime(2026, 7, 14, 12, 0, tzinfo=timezone(timedelta(hours=9))),
    )

    assert fields["entry_split_order_policy_applied"] is True
    assert fields["entry_split_order_market_first_leg_applied"] is True
    assert fields["entry_split_order_market_first_leg_qty"] == 16
    assert fields["entry_split_order_qty_weight_min"] == 0.5
    assert fields["entry_split_order_passive_bias_reason"] == ""
    assert fields["entry_split_order_runtime_weight_adjustment_applied"] is False
    assert [item["qty"] for item in orders] == [16, 8, 8]
    assert orders[0]["order_type_code"] == "3"
    assert orders[0]["entry_split_order_execution_mode"] == "market_first"
    assert orders[0]["entry_split_order_market_reference_price"] == 12240
    assert orders[1]["order_type_code"] == "00"
    assert orders[1]["entry_split_order_execution_mode"] == "resolver_limit"
    assert orders[1]["price"] < orders[0]["price"]
    assert orders[2]["order_type_code"] == "00"
    assert orders[2]["entry_split_order_execution_mode"] == "resolver_limit"
    assert orders[2]["price"] < orders[1]["price"]


def test_allocator_probe_first_reserves_one_share_and_builds_fill_anchored_residuals(
    monkeypatch, tmp_path
):
    target_date = "2026-07-20"
    policy_file = tmp_path / "entry-policy.json"
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "probe-test",
                "source_date": "2026-07-16",
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        split_plan,
        "PROBE_RUNTIME_STATE_PATH",
        tmp_path / "entry_split_probe_runtime_state.json",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ACTIVE_DATE", target_date)
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(policy_file))
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ACTIVE_DATE", target_date)
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY", "1")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_MAX_BUNDLES", "3")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_MARKET_FIRST_LEG_ENABLED", "false")

    orders, fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 10, "price": 10000, "tif": "DAY"}],
        stock={"id": 7, "code": "123456", "strategy": "SCALPING"},
        latency_gate={
            "latency_state": "SAFE",
            "best_ask_at_submit": 10050,
            "quote_stale_at_submit": False,
            "entry_ai_submit_authority_blocked": False,
            "entry_ai_submit_authority_action": "WAIT",
            "entry_ai_submit_authority_result_source": "live",
            "entry_ai_submit_authority_confirmed_at": 100.25,
            "entry_ai_submit_authority_action_source": "latest_stock_ai",
            "entry_ai_submit_authority_wait_probe_required": True,
            "entry_ai_submit_authority_decision_trace_id": "entry-trace-1",
        },
        now=datetime(2026, 7, 20, 10, 0, tzinfo=timezone(timedelta(hours=9))),
    )

    assert fields["entry_split_order_probe_first_applied"] is True
    assert fields["entry_split_order_split_qty"] == 10
    assert len(orders) == 1
    assert orders[0]["qty"] == 1
    assert orders[0]["entry_split_order_leg_index"] == 0
    assert orders[0]["entry_split_order_execution_mode"] == "probe_first_market"
    continuation = orders[0]["entry_split_order_probe_continuation"]
    assert sum(continuation["residual_quantities"]) == 9
    runtime_state = split_plan.probe_runtime_state_snapshot(
        now=datetime(2026, 7, 20, 10, 0, tzinfo=timezone(timedelta(hours=9)))
    )
    reserved_bundle = runtime_state["bundles"][
        orders[0]["entry_split_order_probe_bundle_id"]
    ]
    assert reserved_bundle["phase"] == "planned"
    assert reserved_bundle["requested_qty"] == 10
    assert reserved_bundle["continuation"] == continuation
    assert reserved_bundle["probe_submit_best_ask"] == 10050
    assert reserved_bundle["timeout_sec"] == 3
    assert reserved_bundle["ai_action_at_submit"] == "WAIT"
    assert reserved_bundle["ai_result_source_at_submit"] == "live"
    assert reserved_bundle["ai_confirmed_at_submit"] == 100.25
    assert reserved_bundle["ai_action_source_at_submit"] == "latest_stock_ai"
    assert reserved_bundle["wait_contract_at_submit"] is True
    assert reserved_bundle["ai_decision_trace_id"] == "entry-trace-1"

    bundle_id = orders[0]["entry_split_order_probe_bundle_id"]
    split_plan.update_probe_runtime_bundle(
        bundle_id,
        phase="probe_submitting",
        now=datetime(2026, 7, 20, 10, 0, tzinfo=timezone(timedelta(hours=9))),
    )
    fill_race_stock = {
        "id": 7,
        "code": "123456",
        "strategy": "SCALPING",
        "entry_split_probe_phase": "probe_submitting",
        "entry_split_probe_bundle_id": bundle_id,
        "entry_split_probe_requested_qty": 10,
        "entry_split_probe_continuation": continuation,
        "entry_split_probe_submit_best_ask": 10050,
        "entry_split_probe_ai_action_at_submit": "-",
        "entry_split_probe_ai_result_source_at_submit": "not_available",
        "entry_split_probe_ai_confirmed_at_submit": 0.0,
        "entry_split_probe_ai_action_source_at_submit": "-",
        "entry_split_probe_ai_decision_trace_id": "-",
    }
    recovered = split_plan.recover_probe_submit_contract_for_fill(
        fill_race_stock,
        now=datetime(2026, 7, 20, 10, 0, tzinfo=timezone(timedelta(hours=9))),
    )
    assert recovered["recovered"] is True
    assert fill_race_stock["entry_split_probe_ai_action_at_submit"] == "WAIT"
    assert fill_race_stock["entry_split_probe_ai_result_source_at_submit"] == "live"
    assert fill_race_stock["entry_split_probe_ai_confirmed_at_submit"] == 100.25
    assert (
        fill_race_stock["entry_split_probe_ai_action_source_at_submit"]
        == "latest_stock_ai"
    )
    assert fill_race_stock["entry_split_probe_wait_contract_at_submit"] is True
    assert fill_race_stock["entry_split_probe_ai_decision_trace_id"] == "entry-trace-1"

    untrusted_orders, _ = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 4, "price": 9000, "tif": "DAY"}],
        stock={"code": "654321", "strategy": "SCALPING"},
        latency_gate={
            "latency_state": "SAFE",
            "best_ask_at_submit": 9050,
            "quote_stale_at_submit": False,
            "entry_ai_submit_authority_blocked": True,
            "entry_ai_submit_authority_action": "WAIT",
            "entry_ai_submit_authority_result_source": "live",
            "entry_ai_submit_authority_confirmed_at": 100.25,
            "entry_ai_submit_authority_wait_probe_required": True,
        },
        now=datetime(2026, 7, 20, 10, 0, tzinfo=timezone(timedelta(hours=9))),
    )
    untrusted_bundle = split_plan.probe_runtime_state_snapshot(
        now=datetime(2026, 7, 20, 10, 0, tzinfo=timezone(timedelta(hours=9)))
    )["bundles"][untrusted_orders[0]["entry_split_order_probe_bundle_id"]]
    assert "ai_action_at_submit" not in untrusted_bundle
    assert "wait_contract_at_submit" not in untrusted_bundle

    drop_orders, _ = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 4, "price": 8900, "tif": "DAY"}],
        stock={"id": 9, "code": "654322", "strategy": "SCALPING"},
        latency_gate={
            "latency_state": "SAFE",
            "best_ask_at_submit": 8950,
            "quote_stale_at_submit": False,
            "entry_ai_submit_authority_blocked": False,
            "entry_ai_submit_authority_action": "DROP",
            "entry_ai_submit_authority_result_source": "live",
            "entry_ai_submit_authority_confirmed_at": 100.25,
            "entry_ai_submit_authority_action_source": "latest_stock_ai",
            "entry_ai_submit_authority_decision_trace_id": "drop-trace",
        },
        now=datetime(2026, 7, 20, 10, 0, tzinfo=timezone(timedelta(hours=9))),
    )
    drop_bundle = split_plan.probe_runtime_state_snapshot(
        now=datetime(2026, 7, 20, 10, 0, tzinfo=timezone(timedelta(hours=9)))
    )["bundles"][drop_orders[0]["entry_split_order_probe_bundle_id"]]
    assert "ai_action_at_submit" not in drop_bundle
    assert "wait_contract_at_submit" not in drop_bundle
    drop_bundle_id = drop_orders[0]["entry_split_order_probe_bundle_id"]
    split_plan.update_probe_runtime_bundle(
        drop_bundle_id,
        phase="probe_submitting",
        now=datetime(2026, 7, 20, 10, 0, tzinfo=timezone(timedelta(hours=9))),
    )
    incomplete_recovery = split_plan.recover_probe_submit_contract_for_fill(
        {
            "id": 9,
            "code": "654322",
            "strategy": "SCALPING",
            "entry_split_probe_phase": "probe_submitting",
            "entry_split_probe_bundle_id": drop_bundle_id,
            "entry_split_probe_requested_qty": 4,
            "entry_split_probe_continuation": drop_bundle["continuation"],
            "entry_split_probe_submit_best_ask": 8950,
        },
        now=datetime(2026, 7, 20, 10, 0, tzinfo=timezone(timedelta(hours=9))),
    )
    assert incomplete_recovery["recovered"] is False
    assert (
        incomplete_recovery["reason"]
        == "probe_submit_bundle_missing_immutable_ai_contract"
    )

    residuals, residual_fields = split_plan.build_probe_residual_orders(
        continuation,
        probe_fill_price=10080,
        best_bid=10000,
        best_ask=10020,
    )

    assert residual_fields["allowed"] is True
    assert residual_fields["probe_anchor_price"] == 10020
    assert 1 + sum(order["qty"] for order in residuals) == 10
    assert residuals[0]["price"] == 10020
    assert all(order["order_type_code"] == "00" for order in residuals)

    p1_prices = [9970] + [9920] * (len(continuation["residual_quantities"]) - 1)
    p1_residuals, p1_fields = split_plan.build_probe_residual_orders(
        continuation,
        probe_fill_price=10080,
        best_bid=10000,
        best_ask=10020,
        resolved_leg_prices=p1_prices,
    )

    assert p1_fields["allowed"] is True
    assert p1_fields["residual_price_authority"] == ("dynamic_entry_price_resolver_p1")
    assert [order["price"] for order in p1_residuals] == p1_prices
    assert all(
        order["entry_split_order_price_authority"] == "dynamic_entry_price_resolver_p1"
        for order in p1_residuals
    )

    fallback_orders, fallback_fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 10, "price": 10000, "tif": "DAY"}],
        stock={"code": "654321", "strategy": "SCALPING"},
        latency_gate={
            "latency_state": "SAFE",
            "best_ask_at_submit": 10050,
            "quote_stale_at_submit": False,
        },
        now=datetime(2026, 7, 20, 10, 1, tzinfo=timezone(timedelta(hours=9))),
    )
    assert fallback_fields["entry_split_order_probe_first_skip_reason"] == (
        "probe_active_bundle_cap_reached"
    )
    assert fallback_orders == []
    assert fallback_fields["entry_split_order_probe_first_required"] is True
    assert fallback_fields["entry_split_order_probe_capacity_deferred"] is True

    split_plan.update_probe_runtime_bundle(
        orders[0]["entry_split_order_probe_bundle_id"],
        phase="complete",
        now=datetime(2026, 7, 20, 10, 1, tzinfo=timezone(timedelta(hours=9))),
    )
    next_orders, next_fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 10, "price": 10000, "tif": "DAY"}],
        stock={"code": "654322", "strategy": "SCALPING"},
        latency_gate={
            "latency_state": "SAFE",
            "best_ask_at_submit": 10050,
            "quote_stale_at_submit": False,
        },
        now=datetime(2026, 7, 20, 10, 2, tzinfo=timezone(timedelta(hours=9))),
    )
    assert next_fields["entry_split_order_probe_first_applied"] is True
    assert len(next_orders) == 1
    assert next_orders[0]["qty"] == 1


def test_probe_first_capacity_counts_all_nonterminal_bundle_phases(
    monkeypatch, tmp_path
):
    target_date = "2026-07-20"
    state_path = tmp_path / "entry_split_probe_runtime_state.json"
    state_path.write_text(
        json.dumps(
            {
                "schema_version": split_plan.PROBE_RUNTIME_STATE_SCHEMA_VERSION,
                "target_date": target_date,
                "submitted_bundle_count": 1,
                "circuit_open": False,
                "circuit_reason": "",
                "bundles": {
                    "inflight": {"phase": "probe_recheck_pending"},
                    "aborted": {"phase": "aborted"},
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(split_plan, "PROBE_RUNTIME_STATE_PATH", state_path)
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ACTIVE_DATE", target_date)
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY", "1")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_MAX_BUNDLES", "1")

    bundle_id, reason = split_plan._reserve_probe_runtime_bundle(
        stock={"code": "654321", "strategy": "SCALPING"},
        total_qty=2,
        submit_contract={
            "continuation": {
                "requested_qty": 2,
                "residual_qty": 1,
                "residual_quantities": [1],
            },
            "probe_submit_best_ask": 10_000,
        },
        now=datetime(2026, 7, 20, 10, 0, tzinfo=timezone(timedelta(hours=9))),
    )

    assert bundle_id == ""
    assert reason == "probe_active_bundle_cap_reached"

    split_plan.update_probe_runtime_bundle(
        "inflight",
        phase="aborted",
        now=datetime(2026, 7, 20, 10, 1, tzinfo=timezone(timedelta(hours=9))),
    )
    released_bundle_id, released_reason = split_plan._reserve_probe_runtime_bundle(
        stock={"code": "654322", "strategy": "SCALPING"},
        total_qty=2,
        submit_contract={
            "continuation": {
                "requested_qty": 2,
                "residual_qty": 1,
                "residual_quantities": [1],
            },
            "probe_submit_best_ask": 10_000,
        },
        now=datetime(2026, 7, 20, 10, 2, tzinfo=timezone(timedelta(hours=9))),
    )

    assert released_bundle_id
    assert released_reason == "reserved"


def test_probe_runtime_reservation_rejects_incomplete_submit_contract(
    monkeypatch, tmp_path
):
    target_date = "2026-07-20"
    state_path = tmp_path / "entry_split_probe_runtime_state.json"
    monkeypatch.setattr(split_plan, "PROBE_RUNTIME_STATE_PATH", state_path)
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ACTIVE_DATE", target_date)
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY", "1")

    bundle_id, reason = split_plan._reserve_probe_runtime_bundle(
        stock={"code": "654323", "strategy": "SCALPING"},
        total_qty=2,
        submit_contract={"continuation": {"requested_qty": 2}},
        now=datetime(2026, 7, 20, 10, 0, tzinfo=timezone(timedelta(hours=9))),
    )

    assert bundle_id == ""
    assert reason == "probe_submit_contract_invalid"
    assert state_path.exists() is False

    empty_bundle_id, empty_reason = split_plan._reserve_probe_runtime_bundle(
        stock={"code": "654324", "strategy": "SCALPING"},
        total_qty=2,
        submit_contract={
            "continuation": {},
            "probe_submit_best_ask": 10_000,
        },
        now=datetime(2026, 7, 20, 10, 1, tzinfo=timezone(timedelta(hours=9))),
    )

    assert empty_bundle_id == ""
    assert empty_reason == "probe_submit_contract_invalid"
    assert state_path.exists() is False


def test_allocator_probe_first_applies_to_real_rising_missed_initial_entry(
    monkeypatch, tmp_path
):
    target_date = "2026-07-21"
    policy_file = tmp_path / "entry-policy.json"
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "rising-missed-probe-test",
                "source_date": "2026-07-16",
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        split_plan,
        "PROBE_RUNTIME_STATE_PATH",
        tmp_path / "entry_split_probe_runtime_state.json",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ACTIVE_DATE", target_date)
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(policy_file))
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ACTIVE_DATE", target_date)
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY", "1")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_MAX_BUNDLES", "5")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_OPERATOR_FALLBACK_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_SPLIT_OPERATOR_FALLBACK_ACTIVE_DATE", target_date
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_MARKET_FIRST_LEG_ENABLED", "false")

    orders, fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 6, "price": 59200, "tif": "DAY"}],
        stock={
            "code": "475150",
            "strategy": "SCALPING",
            "status": "WATCHING",
            "buy_qty": 0,
            "position_tag": "SCANNER",
            "rising_missed_one_share_scout": True,
            "rising_missed_one_share_entry_forced": True,
            # The real initial-scout producer sets this before entering the
            # common submit path. It is not itself an upgrade order marker.
            "rising_missed_scout_upgrade_pending": True,
        },
        latency_gate={
            "latency_state": "SAFE",
            "best_ask_at_submit": 59900,
            "quote_stale_at_submit": False,
        },
        now=datetime(2026, 7, 21, 10, 22, tzinfo=timezone(timedelta(hours=9))),
    )

    assert fields["entry_split_order_probe_first_applied"] is True
    assert len(orders) == 1
    assert orders[0]["qty"] == 1
    assert orders[0]["order_type_code"] == "3"
    assert orders[0]["entry_split_order_execution_mode"] == "probe_first_market"
    assert orders[0]["entry_split_order_probe_continuation"]["residual_qty"] == 5


def test_probe_first_still_excludes_simulated_and_additional_buy_paths():
    opening_rotation = {
        "code": "123456",
        "strategy": "SCALPING",
        "position_tag": "OPENING_ROTATION",
    }
    simulated = {
        "code": "123456",
        "strategy": "SCALPING",
        "rising_missed_one_share_scout": True,
        "scalp_live_simulator": True,
    }
    additional = {
        "code": "123456",
        "strategy": "SCALPING",
        "rising_missed_one_share_scout": True,
        "pending_add_order": True,
    }
    scout_upgrade = {
        "code": "123456",
        "strategy": "SCALPING",
        "status": "HOLDING",
        "buy_qty": 1,
        "rising_missed_one_share_entry_forced": True,
        "rising_missed_one_share_scout": True,
        "rising_missed_scout_upgrade_pending": True,
    }
    scout_upgrade_order_pending = {
        "code": "123456",
        "strategy": "SCALPING",
        "status": "WATCHING",
        "buy_qty": 0,
        "rising_missed_one_share_entry_forced": True,
        "rising_missed_one_share_scout": True,
        "rising_missed_scout_upgrade_pending": True,
        "rising_missed_scout_upgrade_order_pending": True,
    }

    assert split_plan._probe_first_eligible(opening_rotation, 6) == (True, "eligible")
    assert split_plan._probe_first_eligible(simulated, 6) == (
        False,
        "simulated_entry_excluded",
    )
    assert split_plan._probe_first_eligible(additional, 6) == (
        False,
        "non_initial_entry_excluded",
    )
    assert split_plan._probe_first_eligible(scout_upgrade, 6) == (
        False,
        "non_initial_entry_excluded",
    )
    assert split_plan._probe_first_eligible(scout_upgrade_order_pending, 6) == (
        False,
        "non_initial_entry_excluded",
    )


def test_probe_runtime_restart_recovery_restores_bundle_and_fails_closed_on_mismatch(
    monkeypatch, tmp_path
):
    state_path = tmp_path / "entry_split_probe_runtime_state.json"
    monkeypatch.setattr(split_plan, "PROBE_RUNTIME_STATE_PATH", state_path)
    now = datetime(2026, 7, 20, 10, 0, tzinfo=timezone(timedelta(hours=9)))
    continuation = {
        "requested_qty": 5,
        "residual_qty": 4,
        "residual_quantities": [2, 2],
    }
    split_plan.update_probe_runtime_bundle(
        "123456-probe-restart",
        phase="probe_filled",
        now=now,
        code="123456",
        target_id=7,
        requested_qty=5,
        continuation=continuation,
        probe_submit_best_ask=10000,
        timeout_sec=3,
        max_slippage_bps=50,
        anchor_mode="fill_clamped_to_fresh_bbo",
        submitted_at=100.0,
        filled_at=101.0,
        fill_price=10010,
        fill_qty=1,
        order_no="P0",
        broker_route="SOR",
        broker_route_resolution="explicit_request",
        effective_venue="KRX",
        ai_action_at_submit="WAIT",
        ai_result_source_at_submit="live",
        ai_confirmed_at_submit=99.8,
        ai_action_source_at_submit="latest_stock_ai",
        wait_contract_at_submit=True,
        probe_confirmation_count=1,
        probe_confirmation_last_at=101.1,
        probe_confirmation_last_state="STRONG",
        probe_confirmation_last_signature="price+tape",
        entry_split_probe_scale_in_forbidden=True,
        probe_expand_forbidden=False,
        residual_orders=[
            {"tag": "planned_only", "qty": 2, "status": "OPEN"},
            {"tag": "submitted", "qty": 2, "status": "OPEN", "ord_no": "R1"},
        ],
    )

    unrelated_stock = {
        "id": 8,
        "code": "123456",
        "buy_qty": 1,
        "status": "HOLDING",
    }
    unrelated = split_plan.recover_probe_runtime_bundle_for_stock(
        unrelated_stock, now=now
    )
    assert unrelated == {"recovered": False, "reason": "no_incomplete_bundle"}
    assert "entry_split_probe_bundle_id" not in unrelated_stock

    recovered_stock = {
        "id": 7,
        "code": "123456",
        "buy_qty": 1,
        "status": "HOLDING",
    }
    result = split_plan.recover_probe_runtime_bundle_for_stock(recovered_stock, now=now)

    assert result == {
        "recovered": True,
        "reason": "incomplete_bundle_restored",
        "phase": "probe_filled",
    }
    assert recovered_stock["entry_split_probe_phase"] == "probe_filled"
    assert recovered_stock["entry_split_probe_continuation"] == continuation
    assert recovered_stock["entry_split_probe_scale_in_forbidden"] is True
    assert recovered_stock["probe_expand_forbidden"] is False
    assert recovered_stock["probe_confirmation_count"] == 1
    assert recovered_stock["probe_confirmation_last_at"] == 101.1
    assert recovered_stock["probe_confirmation_last_state"] == "STRONG"
    assert recovered_stock["probe_confirmation_last_signature"] == "price+tape"
    assert recovered_stock["entry_split_probe_ai_action_at_submit"] == "WAIT"
    assert recovered_stock["entry_split_probe_wait_contract_at_submit"] is True
    assert recovered_stock["entry_split_probe_ai_result_source_at_submit"] == "live"
    assert recovered_stock["entry_split_probe_ai_confirmed_at_submit"] == 99.8
    assert recovered_stock["entry_execution_broker_route"] == "SOR"
    assert (
        recovered_stock["entry_execution_broker_route_resolution"] == "explicit_request"
    )
    assert recovered_stock["entry_execution_route_recorded_at"] == 100.0
    assert recovered_stock["effective_venue"] == "KRX"
    assert recovered_stock["entry_execution_cohort"] == "KRX"
    assert (
        recovered_stock["entry_split_probe_ai_action_source_at_submit"]
        == "latest_stock_ai"
    )
    assert recovered_stock["pending_entry_orders"] == [
        {"tag": "submitted", "qty": 2, "status": "OPEN", "ord_no": "R1"}
    ]

    mismatched_stock = {
        "id": 7,
        "code": "123456",
        "buy_qty": 2,
        "status": "HOLDING",
    }
    mismatch = split_plan.recover_probe_runtime_bundle_for_stock(
        mismatched_stock, now=now
    )
    assert mismatch["circuit_open"] is True
    assert mismatched_stock["entry_split_probe_phase"] == "aborted"
    assert mismatched_stock["entry_split_probe_scale_in_forbidden"] is True
    assert mismatched_stock["probe_expand_forbidden"] is True
    assert mismatched_stock["entry_execution_broker_route"] == "SOR"
    assert (
        mismatched_stock["entry_execution_broker_route_resolution"]
        == "explicit_request"
    )
    assert mismatched_stock["entry_execution_route_recorded_at"] == 100.0
    assert mismatched_stock["entry_execution_cohort"] == "KRX"
    state = split_plan._load_json(state_path)
    assert state["circuit_open"] is True
    assert state["circuit_reason"] == "probe_restart_recovery_quantity_mismatch"
    assert (
        state["bundles"]["123456-probe-restart"]["entry_split_probe_scale_in_forbidden"]
        is True
    )
    assert state["bundles"]["123456-probe-restart"]["probe_expand_forbidden"] is True


def test_probe_submitted_restart_mismatch_keeps_confirmed_route_fail_closed(
    monkeypatch, tmp_path
):
    state_path = tmp_path / "entry_split_probe_runtime_state.json"
    monkeypatch.setattr(split_plan, "PROBE_RUNTIME_STATE_PATH", state_path)
    now = datetime(2026, 8, 13, 12, 49, tzinfo=timezone(timedelta(hours=9)))
    split_plan.update_probe_runtime_bundle(
        "144960-probe-restart",
        phase="probe_submitted",
        now=now,
        code="144960",
        target_id=31480,
        requested_qty=21,
        submitted_at=100.0,
        order_no="0044348",
        broker_route="SOR",
        broker_route_resolution="explicit_request",
        effective_venue="KRX",
    )
    stock = {
        "id": 31480,
        "code": "144960",
        "buy_qty": 1,
        "status": "HOLDING",
    }

    result = split_plan.recover_probe_runtime_bundle_for_stock(stock, now=now)

    assert result == {
        "recovered": False,
        "reason": "probe_restart_recovery_quantity_mismatch",
        "circuit_open": True,
    }
    assert stock["entry_split_probe_phase"] == "aborted"
    assert stock["entry_split_probe_scale_in_forbidden"] is True
    assert stock["probe_expand_forbidden"] is True
    assert stock["entry_execution_broker_route"] == "SOR"
    assert stock["entry_execution_broker_route_resolution"] == "explicit_request"
    assert stock["entry_execution_route_recorded_at"] == 100.0
    assert stock["entry_execution_cohort"] == "KRX"


def test_probe_restart_mismatch_does_not_overwrite_existing_execution_route(
    monkeypatch, tmp_path
):
    state_path = tmp_path / "entry_split_probe_runtime_state.json"
    monkeypatch.setattr(split_plan, "PROBE_RUNTIME_STATE_PATH", state_path)
    now = datetime(2026, 8, 13, 12, 49, tzinfo=timezone(timedelta(hours=9)))
    split_plan.update_probe_runtime_bundle(
        "123456-probe-existing-route-mismatch",
        phase="probe_submitted",
        now=now,
        code="123456",
        target_id=9,
        requested_qty=5,
        submitted_at=100.0,
        broker_route="SOR",
        broker_route_resolution="explicit_request",
        effective_venue="KRX",
    )
    stock = {
        "id": 9,
        "code": "123456",
        "buy_qty": 1,
        "status": "HOLDING",
        "entry_execution_broker_route": "NXT",
        "entry_execution_broker_route_resolution": "broker_fill_receipt",
        "entry_execution_route_recorded_at": 90.0,
        "entry_execution_cohort": "NXT",
        "effective_venue": "NXT",
    }

    result = split_plan.recover_probe_runtime_bundle_for_stock(stock, now=now)

    assert result["circuit_open"] is True
    assert stock["entry_execution_broker_route"] == "NXT"
    assert stock["entry_execution_broker_route_resolution"] == "broker_fill_receipt"
    assert stock["entry_execution_route_recorded_at"] == 90.0
    assert stock["entry_execution_cohort"] == "NXT"
    assert stock["effective_venue"] == "NXT"


def test_probe_recovered_execution_provenance_rejects_unconfirmed_requested_route():
    fields = split_plan._probe_recovered_execution_provenance(
        {
            "dmst_stex_tp": "SOR",
            "effective_venue": "UNKNOWN",
            "submitted_at": 100.0,
        }
    )

    assert fields == {}


def test_probe_runtime_restart_backfills_provenance_for_already_hydrated_bundle(
    monkeypatch, tmp_path
):
    runtime_path = tmp_path / "probe_runtime.json"
    monkeypatch.setattr(split_plan, "PROBE_RUNTIME_STATE_PATH", runtime_path)
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_ENABLED", "true")
    now = datetime(2026, 8, 3, 11, 32, tzinfo=timezone(timedelta(hours=9)))
    bundle_id = "123456-probe-already-hydrated"
    split_plan._write_probe_runtime_state(
        {
            "schema_version": split_plan.PROBE_RUNTIME_STATE_SCHEMA_VERSION,
            "target_date": "2026-08-03",
            "submitted_bundle_count": 1,
            "circuit_open": False,
            "circuit_reason": "",
            "bundles": {
                bundle_id: {
                    "bundle_id": bundle_id,
                    "phase": "aborted",
                    "code": "123456",
                    "broker_route": "SOR",
                    "broker_route_resolution": "broker_response",
                    "effective_venue": "KRX",
                    "submitted_at": 100.0,
                }
            },
        }
    )
    stock = {
        "code": "123456",
        "buy_qty": 1,
        "entry_split_probe_bundle_id": bundle_id,
        "effective_venue": "KRX",
    }

    result = split_plan.recover_probe_runtime_bundle_for_stock(stock, now=now)

    assert result == {
        "recovered": True,
        "reason": "already_hydrated_provenance_restored",
        "phase": "aborted",
    }
    assert stock["entry_execution_broker_route"] == "SOR"
    assert stock["entry_execution_broker_route_resolution"] == "broker_response"
    assert stock["entry_execution_route_recorded_at"] == 100.0
    assert stock["entry_execution_cohort"] == "KRX"


def test_probe_runtime_restart_does_not_mix_existing_route_with_bundle_provenance(
    monkeypatch, tmp_path
):
    runtime_path = tmp_path / "probe_runtime.json"
    monkeypatch.setattr(split_plan, "PROBE_RUNTIME_STATE_PATH", runtime_path)
    now = datetime(2026, 8, 3, 11, 32, tzinfo=timezone(timedelta(hours=9)))
    bundle_id = "123456-probe-existing-route"
    split_plan._write_probe_runtime_state(
        {
            "schema_version": split_plan.PROBE_RUNTIME_STATE_SCHEMA_VERSION,
            "target_date": "2026-08-03",
            "submitted_bundle_count": 1,
            "circuit_open": False,
            "circuit_reason": "",
            "bundles": {
                bundle_id: {
                    "bundle_id": bundle_id,
                    "phase": "aborted",
                    "code": "123456",
                    "broker_route": "SOR",
                    "broker_route_resolution": "broker_response",
                    "effective_venue": "KRX",
                    "submitted_at": 100.0,
                }
            },
        }
    )
    stock = {
        "code": "123456",
        "buy_qty": 1,
        "entry_split_probe_bundle_id": bundle_id,
        "entry_execution_broker_route": "NXT",
    }

    result = split_plan.recover_probe_runtime_bundle_for_stock(stock, now=now)

    assert result == {"recovered": False, "reason": "already_hydrated"}
    assert stock["entry_execution_broker_route"] == "NXT"
    assert "entry_execution_broker_route_resolution" not in stock
    assert "entry_execution_cohort" not in stock


def test_probe_runtime_restart_rejects_hydrated_bundle_code_mismatch(
    monkeypatch, tmp_path
):
    runtime_path = tmp_path / "probe_runtime.json"
    monkeypatch.setattr(split_plan, "PROBE_RUNTIME_STATE_PATH", runtime_path)
    now = datetime(2026, 8, 3, 11, 32, tzinfo=timezone(timedelta(hours=9)))
    bundle_id = "654321-probe-mismatched"
    split_plan._write_probe_runtime_state(
        {
            "schema_version": split_plan.PROBE_RUNTIME_STATE_SCHEMA_VERSION,
            "target_date": "2026-08-03",
            "submitted_bundle_count": 1,
            "circuit_open": False,
            "circuit_reason": "",
            "bundles": {
                bundle_id: {
                    "bundle_id": bundle_id,
                    "phase": "aborted",
                    "code": "654321",
                    "broker_route": "SOR",
                    "effective_venue": "KRX",
                }
            },
        }
    )
    stock = {
        "code": "123456",
        "buy_qty": 1,
        "entry_split_probe_bundle_id": bundle_id,
    }

    result = split_plan.recover_probe_runtime_bundle_for_stock(stock, now=now)

    assert result == {"recovered": False, "reason": "hydrated_bundle_code_mismatch"}
    assert "entry_execution_broker_route" not in stock


def test_probe_runtime_restart_backfills_hydrated_immutable_contract(
    monkeypatch, tmp_path
):
    runtime_path = tmp_path / "probe_runtime.json"
    monkeypatch.setattr(split_plan, "PROBE_RUNTIME_STATE_PATH", runtime_path)
    now = datetime(2026, 8, 3, 11, 32, tzinfo=timezone(timedelta(hours=9)))
    bundle_id = "123456-probe-contract"
    split_plan._write_probe_runtime_state(
        {
            "schema_version": split_plan.PROBE_RUNTIME_STATE_SCHEMA_VERSION,
            "target_date": "2026-08-03",
            "submitted_bundle_count": 1,
            "circuit_open": False,
            "circuit_reason": "",
            "bundles": {
                bundle_id: {
                    "bundle_id": bundle_id,
                    "phase": "aborted",
                    "code": "123456",
                    "wait_contract_at_submit": True,
                    "terminal_abort_detail_reason": (
                        "timeout_wait_confirmation_not_reached"
                    ),
                }
            },
        }
    )
    stock = {
        "code": "123456",
        "buy_qty": 1,
        "entry_split_probe_bundle_id": bundle_id,
        "entry_execution_broker_route": "KRX",
    }

    result = split_plan.recover_probe_runtime_bundle_for_stock(stock, now=now)

    assert result == {
        "recovered": True,
        "reason": "already_hydrated_contract_restored",
        "phase": "aborted",
    }
    assert stock["entry_split_probe_wait_contract_at_submit"] is True
    assert (
        stock["entry_split_probe_terminal_abort_detail_reason"]
        == "timeout_wait_confirmation_not_reached"
    )


def test_probe_runtime_restart_clears_pending_recheck_without_opening_circuit(
    monkeypatch, tmp_path
):
    state_path = tmp_path / "entry_split_probe_runtime_state.json"
    monkeypatch.setattr(split_plan, "PROBE_RUNTIME_STATE_PATH", state_path)
    now = datetime(2026, 7, 20, 10, 0, tzinfo=timezone(timedelta(hours=9)))
    split_plan.update_probe_runtime_bundle(
        "123456-probe-recheck-restart",
        phase="probe_recheck_pending",
        now=now,
        code="123456",
        target_id=7,
        requested_qty=5,
        fill_qty=1,
        recheck_count=2,
        post_probe_direction_state="UNKNOWN",
    )
    stock = {
        "id": 7,
        "code": "123456",
        "buy_qty": 1,
        "status": "HOLDING",
    }

    result = split_plan.recover_probe_runtime_bundle_for_stock(stock, now=now)

    assert result == {
        "recovered": True,
        "reason": "post_probe_recheck_cleared_on_restart",
        "phase": "aborted",
    }
    assert stock["entry_split_probe_phase"] == "aborted"
    assert stock["entry_requested_qty"] == 1
    assert stock["entry_split_probe_scale_in_forbidden"] is True
    assert stock["probe_expand_forbidden"] is True
    assert stock["entry_split_probe_residual_expand_forbidden"] is True
    assert stock["probe_confirmation_count"] == 0
    assert stock["probe_confirmation_last_state"] == "UNKNOWN"
    assert "entry_split_probe_direction_state" not in stock
    assert stock["entry_split_probe_terminal_outcome"] == "residual_not_submitted"
    assert (
        stock["entry_split_probe_terminal_abort_reason"]
        == "post_probe_recheck_cleared_on_restart"
    )
    state = split_plan._load_json(state_path)
    assert state["circuit_open"] is False
    persisted = state["bundles"]["123456-probe-recheck-restart"]
    assert persisted["phase"] == "aborted"
    assert persisted["entry_split_probe_scale_in_forbidden"] is True
    assert persisted["probe_expand_forbidden"] is True


def test_probe_runtime_restart_releases_source_quality_recheck_for_scale_in(
    monkeypatch, tmp_path
):
    state_path = tmp_path / "entry_split_probe_runtime_state.json"
    monkeypatch.setattr(split_plan, "PROBE_RUNTIME_STATE_PATH", state_path)
    now = datetime(2026, 7, 23, 12, 22, tzinfo=timezone(timedelta(hours=9)))
    split_plan.update_probe_runtime_bundle(
        "001520-probe-source-recheck",
        phase="probe_recheck_pending",
        now=now,
        code="001520",
        target_id=117,
        requested_qty=1013,
        fill_qty=1,
        recheck_count=5,
        post_probe_direction_state="UNKNOWN",
        post_probe_direction_reason="post_probe_stale_or_conflicted_fresh_quote",
        source_quality_recheck_pending=True,
    )
    stock = {
        "id": 117,
        "code": "001520",
        "buy_qty": 1,
        "status": "HOLDING",
    }

    result = split_plan.recover_probe_runtime_bundle_for_stock(stock, now=now)

    assert result["reason"] == "post_probe_recheck_cleared_on_restart"
    assert stock["entry_split_probe_phase"] == "aborted"
    assert stock["entry_split_probe_soft_abort"] is True
    assert stock["entry_split_probe_scale_in_forbidden"] is False
    assert stock["probe_expand_forbidden"] is False
    assert stock["entry_split_probe_scale_in_recheck_allowed"] is True
    assert (
        stock["entry_split_probe_scale_in_recheck_origin"]
        == "source_quality_restart_recovery"
    )
    assert stock["entry_split_probe_source_quality_recheck_released"] is True
    assert stock["entry_split_probe_source_quality_recheck_unfilled_qty"] == 1012


def test_probe_runtime_restart_preserves_persisted_soft_abort_quantity_truth(
    monkeypatch, tmp_path
):
    state_path = tmp_path / "entry_split_probe_runtime_state.json"
    monkeypatch.setattr(split_plan, "PROBE_RUNTIME_STATE_PATH", state_path)
    now = datetime(2026, 7, 23, 12, 23, tzinfo=timezone(timedelta(hours=9)))
    split_plan.update_probe_runtime_bundle(
        "001520-probe-soft-abort",
        phase="aborted",
        now=now,
        code="001520",
        target_id=117,
        requested_qty=1013,
        fill_qty=1,
        soft_abort=True,
        scale_in_recheck_allowed=True,
        scale_in_recheck_reason=(
            "residual_revalidation_timeout:source_quality_recovery"
        ),
        source_quality_recheck_released=True,
        source_quality_recheck_unfilled_qty=1012,
        source_quality_recheck_reason=("post_probe_stale_or_conflicted_fresh_quote"),
    )
    stock = {
        "id": 117,
        "code": "001520",
        "buy_qty": 1,
        "status": "HOLDING",
    }

    result = split_plan.recover_probe_runtime_bundle_for_stock(stock, now=now)

    assert result["phase"] == "aborted"
    assert stock["entry_split_probe_scale_in_forbidden"] is False
    assert stock["probe_expand_forbidden"] is False
    assert stock["entry_split_probe_scale_in_recheck_allowed"] is True
    assert stock["entry_requested_qty"] == 1
    assert stock["requested_buy_qty"] == 1
    assert stock["entry_split_probe_source_quality_recheck_unfilled_qty"] == 1012
    persisted = split_plan._load_json(state_path)["bundles"]["001520-probe-soft-abort"]
    assert persisted["entry_split_probe_scale_in_forbidden"] is False
    assert persisted["probe_expand_forbidden"] is False


def test_probe_runtime_restart_restores_terminal_abort_guards_and_confirmation(
    monkeypatch, tmp_path
):
    state_path = tmp_path / "entry_split_probe_runtime_state.json"
    monkeypatch.setattr(split_plan, "PROBE_RUNTIME_STATE_PATH", state_path)
    now = datetime(2026, 7, 24, 12, 0, tzinfo=timezone(timedelta(hours=9)))
    split_plan.update_probe_runtime_bundle(
        "096770-probe-hard-abort",
        phase="aborted",
        now=now,
        code="096770",
        target_id=23735,
        requested_qty=8,
        fill_qty=1,
        reason="residual_revalidation_timeout",
        soft_abort=False,
        probe_confirmation_count=1,
        probe_confirmation_last_at=100.25,
        probe_confirmation_last_state="STRONG",
        probe_confirmation_last_signature="price+tape",
        terminal_at=100.5,
        terminal_outcome="residual_not_submitted",
        terminal_abort_reason="residual_revalidation_timeout",
        terminal_abort_detail_reason="timeout_negative_group_persisted",
        terminal_direction_state="WEAK",
        terminal_direction_reason="post_probe_wait_negative_group",
        terminal_continuation_action="DEFER",
        terminal_positive_groups="-",
        terminal_negative_groups="orderbook",
        terminal_confirmation_count=1,
        terminal_failure_signature=(
            "residual_revalidation_timeout|WEAK|"
            "post_probe_wait_negative_group|orderbook|1/2"
        ),
    )
    stock = {
        "id": 23735,
        "code": "096770",
        "buy_qty": 1,
        "status": "HOLDING",
    }

    result = split_plan.recover_probe_runtime_bundle_for_stock(stock, now=now)

    assert result == {
        "recovered": True,
        "reason": "incomplete_bundle_restored",
        "phase": "aborted",
    }
    assert stock["entry_split_probe_scale_in_forbidden"] is True
    assert stock["probe_expand_forbidden"] is True
    assert stock["probe_confirmation_count"] == 1
    assert stock["probe_confirmation_last_at"] == 100.25
    assert stock["probe_confirmation_last_state"] == "STRONG"
    assert stock["probe_confirmation_last_signature"] == "price+tape"
    assert stock["entry_split_probe_terminal_at"] == 100.5
    assert (
        stock["entry_split_probe_abort_detail_reason"]
        == "timeout_negative_group_persisted"
    )
    assert (
        stock["entry_split_probe_terminal_abort_detail_reason"]
        == "timeout_negative_group_persisted"
    )
    assert stock["entry_split_probe_terminal_direction_state"] == "WEAK"
    assert stock["entry_split_probe_terminal_negative_groups"] == "orderbook"
    assert stock["entry_split_probe_terminal_confirmation_count"] == 1
    persisted = split_plan._load_json(state_path)["bundles"]["096770-probe-hard-abort"]
    assert persisted["entry_split_probe_scale_in_forbidden"] is True
    assert persisted["probe_expand_forbidden"] is True


def test_probe_runtime_restart_restores_residual_terminal_scale_in_recheck_lane(
    monkeypatch, tmp_path
):
    state_path = tmp_path / "entry_split_probe_runtime_state.json"
    monkeypatch.setattr(split_plan, "PROBE_RUNTIME_STATE_PATH", state_path)
    now = datetime(2026, 7, 31, 15, 20, tzinfo=timezone(timedelta(hours=9)))
    split_plan.update_probe_runtime_bundle(
        "066570-probe-recheck",
        phase="aborted",
        now=now,
        code="066570",
        target_id=25602,
        requested_qty=2,
        fill_qty=1,
        reason="residual_revalidation_timeout",
        soft_abort=False,
        scale_in_recheck_allowed=True,
        scale_in_recheck_origin="normal_winner_recovery",
        scale_in_recheck_reason="residual_revalidation_timeout",
        entry_split_probe_scale_in_forbidden=False,
        probe_expand_forbidden=True,
        entry_split_probe_residual_expand_forbidden=True,
        terminal_at=1_785_486_344.269,
        terminal_outcome="residual_not_submitted",
        terminal_abort_reason="residual_revalidation_timeout",
        terminal_direction_state="WEAK",
        terminal_direction_reason="post_probe_wait_negative_group",
        terminal_continuation_action="DEFER",
        terminal_positive_groups="-",
        terminal_negative_groups="price_tick,orderbook",
        terminal_confirmation_count=0,
        terminal_failure_signature=(
            "residual_revalidation_timeout|WEAK|"
            "post_probe_wait_negative_group|price_tick,orderbook|0/2"
        ),
    )
    stock = {
        "id": 25602,
        "code": "066570",
        "buy_qty": 1,
        "status": "HOLDING",
    }

    result = split_plan.recover_probe_runtime_bundle_for_stock(stock, now=now)

    assert result["phase"] == "aborted"
    assert stock["probe_expand_forbidden"] is True
    assert stock["entry_split_probe_residual_expand_forbidden"] is True
    assert stock["entry_split_probe_scale_in_forbidden"] is False
    assert stock["entry_split_probe_scale_in_recheck_allowed"] is True
    assert (
        stock["entry_split_probe_scale_in_recheck_origin"] == "normal_winner_recovery"
    )
    assert stock["entry_split_probe_terminal_direction_state"] == "WEAK"
    assert stock["entry_split_probe_terminal_negative_groups"] == "price_tick,orderbook"


def test_probe_runtime_restart_ignores_partial_complete_bundle(monkeypatch, tmp_path):
    state_path = tmp_path / "entry_split_probe_runtime_state.json"
    monkeypatch.setattr(split_plan, "PROBE_RUNTIME_STATE_PATH", state_path)
    now = datetime(2026, 7, 20, 10, 0, tzinfo=timezone(timedelta(hours=9)))
    split_plan.update_probe_runtime_bundle(
        "123456-probe-partial-complete",
        phase="partial_complete",
        now=now,
        code="123456",
        target_id=7,
        requested_qty=10,
        filled_qty=4,
        reason="submitted_residual_orders_terminal",
    )
    stock = {
        "id": 7,
        "code": "123456",
        "buy_qty": 4,
        "status": "HOLDING",
    }

    result = split_plan.recover_probe_runtime_bundle_for_stock(stock, now=now)

    assert result == {"recovered": False, "reason": "no_incomplete_bundle"}
    assert "entry_split_probe_bundle_id" not in stock
    state = split_plan._load_json(state_path)
    assert state["circuit_open"] is False


def test_allocator_date_bounded_policy_becomes_inactive(monkeypatch, tmp_path):
    policy_file = tmp_path / "entry-policy.json"
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "date-bounded",
                "source_date": "2026-07-13",
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ACTIVE_DATE", "2026-07-14"
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(policy_file))

    orders, fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 4, "price": 1000}],
        latency_gate={"spread_bps": 5, "latency_state": "SAFE"},
        now=datetime(2026, 7, 15, 9, 0, tzinfo=timezone(timedelta(hours=9))),
    )

    assert fields["entry_split_order_policy_applied"] is False
    assert fields["entry_split_order_skip_reason"] == "policy_inactive_date"
    assert orders[0]["qty"] == 4


def test_allocator_daily_operator_contract_keeps_probe_first_and_policy_active(
    monkeypatch, tmp_path
):
    policy_file = tmp_path / "entry-policy-daily.json"
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "daily-operator",
                "source_date": "2026-07-01",
                "runtime_apply_allowed": True,
                "baseline_runtime_defaults_enabled": True,
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        split_plan, "PROBE_RUNTIME_STATE_PATH", tmp_path / "probe-state.json"
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "false")
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_SPLIT_DAILY_OPERATOR_CONTRACT_ENABLED", "true"
    )
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_SPLIT_DAILY_BASELINE_POLICY_FILE", str(policy_file)
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_DAILY_BASELINE_ACTIVE_DATE", "DAILY")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_FIRST_ACTIVE_DATE", "DAILY")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_QTY", "1")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_PROBE_MAX_BUNDLES", "5")

    orders, fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 4, "price": 1000}],
        stock={"code": "005930", "id": 1, "strategy": "SCALPING"},
        latency_gate={
            "spread_bps": 18,
            "buy_pressure_10t": 55,
            "latency_state": "SAFE",
            "best_ask": 1000,
            "best_bid": 999,
        },
        now=datetime(2026, 8, 3, 9, 3, tzinfo=timezone(timedelta(hours=9))),
    )

    assert fields["entry_split_order_policy_applied"] is True
    assert fields["entry_split_order_probe_first_applied"] is True
    assert fields["entry_split_order_daily_operator_contract_enabled"] is True
    assert fields["entry_split_order_daily_baseline_fallback_applied"] is True
    assert fields["entry_split_order_stale_policy_operator_authorized"] is True
    assert len(orders) == 1
    assert orders[0]["qty"] == 1


def test_allocator_keeps_original_order_when_scoped_policy_omits_bucket(
    monkeypatch, tmp_path
):
    policy_file = tmp_path / "entry-policy-scoped.json"
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "scoped-child-seed",
                "source_date": "2026-09-01",
                "runtime_apply_allowed": True,
                "runtime_apply_compatibility_semantics": (
                    split_plan.RUNTIME_APPLY_COMPATIBILITY_SEMANTICS
                ),
                "exploration_seed_allowed": True,
                "ev_validated_runtime_apply_allowed": False,
                "runtime_apply_authority_classes": ["bounded_exploration_seed"],
                "baseline_runtime_defaults_enabled": False,
                "missing_bucket_action": "keep_original_order",
                "explicit_bucket_count": 1,
                "buckets": {
                    "passive_wide_or_weak": {
                        "leg_count": 2,
                        "price_offsets_ticks": [0, 1],
                        "qty_weight_min": 0.5,
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(policy_file))

    original_orders = [{"tag": "normal", "qty": 4, "price": 1000}]
    orders, fields = split_plan.apply_entry_split_order_policy(
        original_orders,
        stock={"code": "005930", "id": 1, "strategy": "SCALPING"},
        latency_gate={
            "spread_bps": 18,
            "buy_pressure_10t": 55,
            "latency_state": "SAFE",
        },
        now=datetime(2026, 9, 3, 9, 3, tzinfo=timezone(timedelta(hours=9))),
    )

    assert orders == original_orders
    assert fields["entry_split_order_policy_applied"] is False
    assert fields["entry_split_order_bucket"] == "balanced_normal"
    assert fields["entry_split_order_skip_reason"] == "policy_bucket_not_selected"


def test_allocator_daily_contract_does_not_authorize_stale_standard_policy(
    monkeypatch, tmp_path
):
    policy_file = tmp_path / "entry-policy-stale-standard.json"
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "stale-standard",
                "source_date": "2026-07-01",
                "runtime_apply_allowed": True,
                "baseline_runtime_defaults_enabled": True,
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ACTIVE_DATE", "2026-08-03"
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(policy_file))
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_SPLIT_DAILY_OPERATOR_CONTRACT_ENABLED", "true"
    )

    orders, fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 4, "price": 1000}],
        stock={"code": "005930", "id": 1, "strategy": "SCALPING"},
        latency_gate={"spread_bps": 18, "latency_state": "SAFE"},
        now=datetime(2026, 8, 3, 9, 3, tzinfo=timezone(timedelta(hours=9))),
    )

    assert fields["entry_split_order_policy_applied"] is False
    assert fields["entry_split_order_skip_reason"] == "stale_policy"
    assert orders == [{"tag": "normal", "qty": 4, "price": 1000}]


def test_allocator_requires_date_bounded_operator_fallback_for_denied_policy(
    monkeypatch, tmp_path
):
    policy_file = tmp_path / "entry-policy-denied.json"
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "denied-policy",
                "source_date": "2026-07-13",
                "runtime_apply_allowed": False,
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(policy_file))
    now = datetime(2026, 7, 14, 12, 0, tzinfo=timezone(timedelta(hours=9)))

    _, blocked_fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 4, "price": 1000}],
        latency_gate={"spread_bps": 5, "latency_state": "SAFE"},
        now=now,
    )
    assert (
        blocked_fields["entry_split_order_skip_reason"]
        == "policy_runtime_apply_not_allowed"
    )

    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_OPERATOR_FALLBACK_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_SPLIT_OPERATOR_FALLBACK_ACTIVE_DATE", "2026-07-14"
    )
    orders, fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 4, "price": 1000}],
        latency_gate={"spread_bps": 5, "latency_state": "SAFE"},
        now=now,
    )

    assert fields["entry_split_order_policy_applied"] is True
    assert fields["entry_split_order_operator_fallback_authorized"] is True
    assert all(
        item["entry_split_order_operator_fallback_authorized"] is True
        for item in orders
    )


def test_allocator_rejects_contradictory_runtime_apply_authority_contract(
    monkeypatch, tmp_path
):
    policy_file = tmp_path / "entry-policy-invalid-authority.json"
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "invalid-authority",
                "source_date": "2026-07-14",
                "runtime_apply_allowed": True,
                "runtime_apply_compatibility_semantics": (
                    split_plan.RUNTIME_APPLY_COMPATIBILITY_SEMANTICS
                ),
                "exploration_seed_allowed": False,
                "ev_validated_runtime_apply_allowed": False,
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(policy_file))

    orders, fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 4, "price": 1000}],
        latency_gate={"spread_bps": 5, "latency_state": "SAFE"},
        now=datetime(2026, 7, 14, 12, 0, tzinfo=timezone(timedelta(hours=9))),
    )

    assert orders == [{"tag": "normal", "qty": 4, "price": 1000}]
    assert fields["entry_split_order_policy_applied"] is False
    assert fields["entry_split_order_skip_reason"] == (
        "invalid_policy_authority_contract:runtime_apply_authority_union_mismatch"
    )


def test_allocator_allows_split_when_source_quote_stale_recovered_before_submit(
    monkeypatch, tmp_path
):
    _patch_dirs(monkeypatch, tmp_path)
    target_date = datetime.now(timezone(timedelta(hours=9))).date().isoformat()
    policy_file = split_plan.policy_path(target_date)
    policy_file.parent.mkdir(parents=True, exist_ok=True)
    policy_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "test-policy",
                "source_date": target_date,
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(policy_file))

    recovered, recovered_fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 2, "price": 1000}],
        latency_gate={
            "spread_bps": 18,
            "buy_pressure_10t": 55,
            "latency_state": "SAFE",
            "quote_stale": True,
            "quote_stale_at_submit": False,
            "pre_submit_effective_quote_stale": False,
            "order_price": 1000,
        },
    )
    assert recovered_fields["entry_split_order_policy_applied"] is True
    assert [item["qty"] for item in recovered] == [1, 1]

    blocked, blocked_fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 2, "price": 1000}],
        latency_gate={
            "spread_bps": 18,
            "buy_pressure_10t": 55,
            "latency_state": "SAFE",
            "quote_stale": True,
            "quote_stale_at_submit": True,
            "order_price": 1000,
        },
    )
    assert blocked_fields["entry_split_order_skip_reason"] == "stale_quote"
    assert blocked[0]["qty"] == 2


def test_allocator_fail_closed_for_qty_one_missing_invalid_and_stale_policy(
    monkeypatch, tmp_path
):
    _patch_dirs(monkeypatch, tmp_path)
    one, one_fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 1, "price": 1000}],
        latency_gate={"spread_bps": 5, "latency_state": "SAFE"},
    )
    assert one_fields["entry_split_order_skip_reason"] == "qty_lte_1"
    assert one[0]["qty"] == 1

    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_ENABLED", "true")
    monkeypatch.setenv(
        "KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(tmp_path / "missing.json")
    )
    _, missing_fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 2, "price": 1000}],
        latency_gate={"spread_bps": 5, "latency_state": "SAFE"},
    )
    assert missing_fields["entry_split_order_skip_reason"] == "policy_file_not_found"

    multi, multi_fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "a", "qty": 1, "price": 1000}, {"tag": "b", "qty": 1, "price": 995}],
        latency_gate={"spread_bps": 5, "latency_state": "SAFE"},
    )
    assert (
        multi_fields["entry_split_order_skip_reason"]
        == "multi_order_input_not_supported_v1"
    )
    assert [item["tag"] for item in multi] == ["a", "b"]

    stale_file = tmp_path / "stale.json"
    stale_file.write_text(
        json.dumps(
            {
                "schema_version": "entry_split_order_policy_v1",
                "policy_version": "stale",
                "source_date": "2026-06-01",
                "buckets": {},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("KORSTOCKSCAN_ENTRY_SPLIT_ORDER_POLICY_FILE", str(stale_file))
    _, stale_fields = split_plan.apply_entry_split_order_policy(
        [{"tag": "normal", "qty": 2, "price": 1000}],
        latency_gate={"spread_bps": 5, "latency_state": "SAFE"},
        now=datetime(2026, 7, 7, tzinfo=timezone(timedelta(hours=9))),
    )
    assert stale_fields["entry_split_order_skip_reason"] == "stale_policy"












@pytest.mark.parametrize("existing", [None, False])
@pytest.mark.parametrize("wrong_target", [False, True])
def test_hydrated_exploration_restores_terminal_guards_exact_target(
    monkeypatch, tmp_path, existing, wrong_target
):
    monkeypatch.setattr(split_plan, "PROBE_RUNTIME_STATE_PATH", tmp_path / "state.json")
    now = datetime(2026, 9, 11, 11, tzinfo=timezone(timedelta(hours=9)))
    split_plan._write_probe_runtime_state(
        {
            "schema_version": split_plan.PROBE_RUNTIME_STATE_SCHEMA_VERSION,
            "target_date": "2026-09-11",
            "bundles": {
                "bundle": {
                    "bundle_id": "bundle",
                    "code": "123456",
                    "target_id": "10",
                    "phase": "aborted",
                    "fill_qty": 1,
                    "terminal_abort_reason": "entry_setup_bounded_exploration_probe_only",
                }
            },
        }
    )
    stock = {
        "id": "11" if wrong_target else "10",
        "code": "123456",
        "buy_qty": 1,
        "entry_split_probe_bundle_id": "bundle",
        "entry_split_probe_scale_in_forbidden": existing,
    }
    before = dict(stock)
    result = split_plan.recover_probe_runtime_bundle_for_stock(stock, now=now)
    if wrong_target:
        assert result["reason"] == "hydrated_bundle_target_mismatch"
        assert stock == before
    else:
        assert result["recovered"]
        for key in (
            "entry_split_probe_scale_in_forbidden",
            "entry_split_probe_residual_expand_forbidden",
            "probe_expand_forbidden",
        ):
            assert stock[key] is True
        assert stock["entry_split_probe_terminal_abort_reason"] == (
            "entry_setup_bounded_exploration_probe_only"
        )


@pytest.mark.parametrize("signed_date,expected", [("2026-09-18", 30), ("2026-09-19", 0)])
def test_four_arm_source_date_uses_kst_and_rejects_future_date(monkeypatch, signed_date, expected):
    instant = datetime(2026, 9, 17, 16, 0, tzinfo=timezone.utc)

    class HostUTCDate(date):
        @classmethod
        def today(cls):
            return instant.date()

    class FixedClock(datetime):
        @classmethod
        def now(cls, tz=None):
            assert tz is not None
            return instant.astimezone(tz)

    monkeypatch.setattr(split_plan, "date", HostUTCDate)
    monkeypatch.setattr(split_plan, "datetime", FixedClock)
    events = _quantity_leg_four_arm_events()
    for event in events:
        receipt = event["entry_quantity_leg_four_arm_evaluation"]
        receipt["source_date"] = signed_date
        for arm in receipt["arms"].values():
            arm["terminal_observed_at"] = "2026-09-18T00:30:00+09:00"
        _resign_four_arm_receipt(receipt)
    result = split_plan.build_quantity_leg_four_arm_evaluation(events)
    assert result["complete_exact_attempt_count"] == expected
    if not expected:
        assert result["excluded_counts"]["source_date_contract_invalid"] == 30


def test_four_arm_latest_source_with_no_completed_receipt_retains_denominator():
    result = split_plan.build_quantity_leg_four_arm_evaluation(_quantity_leg_four_arm_events(),
        source_counts={'2026-09-14': 20, '2026-09-15': 10, '2026-09-17': 1})
    assert result['eligible_attempt_count'] == 31
    assert result['exact_attempt_join_coverage'] == pytest.approx(30 / 31)
    assert result['chronological_partitions']['holdout']['complete_exact_attempt_count'] == 0
    assert not result['promotion_gate']['passed']
    assert not split_plan.quantity_leg_promotion_evidence_valid(result)


@pytest.mark.parametrize('census', [{'2026-09-14': 0, '2026-09-15': 30},
    {'2026-09-14': 10, '2026-09-15': 20}, {'2026-09-15': 30}])
def test_four_arm_census_cannot_shift_or_erase_original_source_dates(census):
    events = _quantity_leg_four_arm_events()
    result = split_plan.build_quantity_leg_four_arm_evaluation(events, source_counts=census)
    assert not result['promotion_gate']['passed']
    assert not split_plan.quantity_leg_promotion_evidence_valid(result)
    valid = split_plan.build_quantity_leg_four_arm_evaluation(events,
        source_counts={'2026-09-14': 20, '2026-09-15': 10})
    assert split_plan.quantity_leg_promotion_evidence_valid(valid)
    valid['native_source_counts'] = census
    assert not split_plan.quantity_leg_promotion_evidence_valid(valid)


def test_four_arm_per_day_count_underflow_blocks_even_with_matching_total():
    events = _quantity_leg_four_arm_events()
    for event in events:
        receipt = event['entry_quantity_leg_four_arm_evaluation']
        receipt['eligible_attempt_count'] = 10 if receipt['source_date'] == '2026-09-14' else 20
        _resign_four_arm_receipt(receipt)
    result = split_plan.build_quantity_leg_four_arm_evaluation(events,
        source_counts={'2026-09-14': 10, '2026-09-15': 20})
    assert result['complete_exact_attempt_count'] == 30
    assert result['excluded_counts']['eligible_population_source_date_underflow'] == 1
    assert not result['promotion_gate']['passed']


@pytest.mark.parametrize('census', [{}, {'2026-09-17': 0}])
def test_four_arm_empty_native_census_preserves_existing_signed_actual_population(census):
    result = split_plan.build_quantity_leg_four_arm_evaluation(_quantity_leg_four_arm_events(),
        source_counts=census)
    assert result['eligible_attempt_count'] == 30
    assert result['promotion_gate']['passed']
    assert split_plan.quantity_leg_promotion_evidence_valid(result)


def test_split_native_replay_persists_census_across_prior_state(monkeypatch, tmp_path):
    from src.tests.test_strategy_owner_replay import entry_owner_event, native_entry_loader
    from src.engine.scalping.strategy_owner_replay import build_entry_opportunity_replays
    from src.engine.monitoring import machine_microstructure_attribution as micro
    _patch_dirs(monkeypatch, tmp_path)
    from src.engine.scalping import strategy_owner_replay as native_replay
    original_replay = native_replay.build_entry_opportunity_replays
    frozen_at = datetime.fromisoformat('2026-09-17T15:00:00+09:00').timestamp()
    monkeypatch.setattr(native_replay, 'build_entry_opportunity_replays',
        lambda *a, **kw: original_replay(*a, **{'evaluated_at': frozen_at, **kw}))
    days = ['2026-09-14', '2026-09-15', '2026-09-17']
    events = []
    for day in days[:-1]:
        native = build_entry_opportunity_replays(day, [entry_owner_event(day, i) for i in range(10)],
            evaluated_at=datetime.fromisoformat('2026-09-17T15:00:00+09:00').timestamp(),
            micro_loader=native_entry_loader)
        events.extend(native['quantity_leg_events'])
    prior = {'quantity_leg_four_arm_events': events, 'source_dates': days[:-1],
        'entry_opportunity_replay_source_counts': {d: 10 for d in days[:-1]}}
    monkeypatch.setattr(split_plan, '_latest_prior_cumulative_state', lambda d: (prior, 'fixture-prior'))
    monkeypatch.setattr(split_plan, '_available_calibration_dates', lambda d: days)
    monkeypatch.setattr(split_plan, '_source_quality_summary', lambda d: {'tuning_input_allowed': True})
    monkeypatch.setattr(split_plan, '_iter_input_events', lambda d: ([],
        {'_entry_opportunity_plan_events': [entry_owner_event(d)]}))
    monkeypatch.setattr(micro, '_micro_context', native_entry_loader)
    report = split_plan.build_report(days[-1], write=False)
    ledger = report['cumulative_state']['entry_opportunity_replay_source_counts']
    assert ledger == {days[0]: 10, days[1]: 10, days[2]: 1}
    assert len(report['cumulative_state']['quantity_leg_four_arm_events']) == 21
    assert report['quantity_leg_four_arm_evaluation']['eligible_attempt_count'] == 21


def test_split_reader_reuses_owner_plan_without_second_pipeline_scan(monkeypatch, tmp_path):
    from src.tests.test_strategy_owner_replay import entry_owner_event, native_entry_loader
    from src.engine import sniper_missed_entry_counterfactual as missed
    from src.engine.monitoring import machine_microstructure_attribution as micro
    data_dir = _patch_dirs(monkeypatch, tmp_path)
    from src.engine.scalping import strategy_owner_replay as native_replay
    original_replay = native_replay.build_entry_opportunity_replays
    frozen_at = datetime.fromisoformat('2026-09-17T15:00:00+09:00').timestamp()
    monkeypatch.setattr(native_replay, 'build_entry_opportunity_replays',
        lambda *a, **kw: original_replay(*a, **{'evaluated_at': frozen_at, **kw}))
    day = '2026-09-17'
    event = entry_owner_event(day)
    row = {'pipeline': 'ENTRY_PIPELINE', 'stage': event.stage, 'emitted_at': event.emitted_at,
        'emitted_date': day, 'stock_code': event.code, 'record_id': event.record_id,
        'fields': {k: str(v) for k, v in event.fields.items()}}
    _write_jsonl(data_dir / 'pipeline_events' / f'pipeline_events_{day}.jsonl', [row])
    monkeypatch.setattr(split_plan, '_available_calibration_dates', lambda d: [day])
    monkeypatch.setattr(split_plan, '_latest_prior_cumulative_state', lambda d: ({}, ''))
    monkeypatch.setattr(split_plan, '_source_quality_summary', lambda d: {'tuning_input_allowed': True})
    def forbidden_second_read(path):
        raise AssertionError('second pipeline read')
    monkeypatch.setattr(missed, 'iter_jsonl', forbidden_second_read)
    monkeypatch.setattr(micro, '_micro_context', native_entry_loader)
    report = split_plan.build_report(day, write=False)
    native = report['input_summary']['daily_diagnostic']['entry_opportunity_executable_replay']
    assert native['counts']['completed'] == 1
    assert report['cumulative_state']['entry_opportunity_replay_source_counts'] == {day: 1}
    assert len(report['cumulative_state']['quantity_leg_four_arm_events']) == 1
    assert '_entry_opportunity_plan_events' not in report['input_summary']['daily_diagnostic']


@pytest.mark.parametrize("actual_qty,model_qty,state,expected", [
    (2, 2, "ORDER_TERMINAL", "ready_for_validation"),
    (0, 0, "ORDER_TERMINAL", "ready_for_validation"),
    (0, 2, "ORDER_TERMINAL", "validation_failed"),
    (2, 0, "ORDER_TERMINAL", "validation_failed"),
    (1, 2, "ORDER_TERMINAL", "validation_failed"),
    (2, 2, "ORDER_BOUND", "terminal_pending"),
])
def test_execution_model_actual_census_and_no_false_economic_pass(actual_qty, model_qty, state, expected):
    at = "2026-09-17T10:00:00+09:00"
    common = dict(owner_type="main_scalping", side="BUY", action="NEW", order_date="2026-09-17",
        intent_id="intent", broker_order_no="007", account_key="account", symbol="123456", quantity=2)
    events = [dict(stage="order_leg_sent", emitted_at=at, actual_order_submitted=True,
        broker_order_no="007", effective_venue="KRX", market_session_bucket="regular", submitted_qty=2,
        entry_execution_sizing_plan_id="parent", entry_execution_sizing_plan_sha256="a" * 64)]
    actual = [dict(common, event="ORDER_BOUND", state="ORDER_BOUND"),
        dict(common, event="FILL_RECORDED", state=state, filled_qty=actual_qty,
            fill_amount=actual_qty * 1000, observed_at_kst=at)]
    arm = dict(modeled_filled_qty=model_qty, modeled_entry_vwap=1000,
        modeled_entry_at=at, modeled_last_fill_at=at)
    replay = dict(status="completed_source_only", schema="model", seed=dict(plan_sha256="a" * 64,
        total_qty=2, stock_code="123456", effective_venue="KRX", session_bucket="regular"),
        incumbent_execution_arm=arm)
    report = split_plan.build_execution_model_validation("2026-09-17", events, [replay], actual)
    assert report["counts"] == {expected: 1}
    assert report["census_conserved"] is True
    assert report["allowed_runtime_apply"] is False
    assert report["actual_net_ev_pct"] is None
    if expected == "ready_for_validation":
        assert report["rows"][0]["reason"] == "tolerance_contract_missing"
    # Same order number on another day cannot join this frozen parent.
    actual[0]["order_date"] = actual[1]["order_date"] = "2026-09-16"
    other = split_plan.build_execution_model_validation("2026-09-17", events, [replay], actual)
    assert other["counts"] == {"source_gap": 1}
    assert other["unclassified_main_buy_parent_count"] == 1
    # A replay conflict stays quarantined even if a third row repeats the first.
    actual[0]["order_date"] = actual[1]["order_date"] = "2026-09-17"
    conflict = {**replay, "schema": "conflicting_model"}
    bad = split_plan.build_execution_model_validation("2026-09-17", events, [replay, conflict, replay], actual)
    if state == "ORDER_TERMINAL":
        assert bad["counts"] == {"source_gap": 1}


def test_execution_model_policy_hash_and_supporting_exit_cannot_promote():
    section = split_plan.build_execution_model_validation("2026-09-17", [], [], [])
    policy = dict(source_date="2026-09-17", execution_model_validation_contract=split_plan.EXECUTION_MODEL_CONTRACT,
        execution_model_validation_sha256=split_plan._canonical_sha256(section), runtime_apply_allowed=False)
    report = dict(execution_model_validation=section)
    assert split_plan.execution_model_policy_contract_status(report, policy)[0]
    assert not split_plan.execution_model_policy_contract_status(report, {**policy, "runtime_apply_allowed": True})[0]
    assert not split_plan.execution_model_policy_contract_status(report, {**policy, "source_date": "2026-09-18"})[0]
    assert not split_plan.execution_model_policy_contract_status(report, {**policy, "execution_model_validation_sha256": "f" * 64})[0]


def test_execution_projection_is_not_valid_empty_and_preserves_exact_contract(monkeypatch, tmp_path):
    monkeypatch.setattr(split_plan, "DATA_DIR", tmp_path)
    rows, source = split_plan._bounded_execution_projection("2026-09-17")
    assert not rows and source["status"] == "source_gap"
    part = tmp_path / "threshold_cycle/date=2026-09-17/family=dynamic_entry_price_resolver/part-000001.jsonl"
    part.parent.mkdir(parents=True)
    event = dict(stage="entry_execution_sizing_plan", emitted_date="2026-09-17",
        fields={"entry_execution_sizing_plan": {"plan_sha256": "a" * 64}})
    part.write_text(json.dumps(event) + "\n" + json.dumps(event) + "\n")
    rows, source = split_plan._bounded_execution_projection("2026-09-17")
    assert rows == [event] and source["full_population_coverage_verified"] is False
    part.write_text(json.dumps({**event, "emitted_date": "2026-09-16"}) + "\n")
    with pytest.raises(ValueError, match="date_mismatch"):
        split_plan._bounded_execution_projection("2026-09-17")


def test_bounded_refresh_reuses_revision_and_rejects_stale_policy(monkeypatch, tmp_path):
    _patch_dirs(monkeypatch, tmp_path)
    target = "2026-09-17"
    path, _ = split_plan.report_paths(target)
    original = dict(schema_version=split_plan.SCHEMA_VERSION, date=target,
        generated_at="2026-09-18T00:14:34+09:00", cumulative_state={"preserved": "frozen"},
        input_summary={"atomic_execution_sizing": {"plan_observed": 3, "invalid": 3}},
        recommended_policy={"runtime_apply_allowed": False, "policy_version": "old",
            "entry_execution_sizing_plan_schema": split_plan.ATOMIC_EXECUTION_SIZING_SCHEMA,
            "entry_execution_sizing_policy": split_plan.ATOMIC_EXECUTION_SIZING_BASELINE_POLICY,
            "entry_price_plan_schema": split_plan.ATOMIC_PRICE_PLAN_SCHEMA}, candidate_grid=[])
    split_plan._write_json(path, original)
    monkeypatch.setattr(split_plan, "_execution_registry_snapshot", lambda: ([], {"status": "verified", "tail_hash": "0" * 64}))
    first = split_plan.refresh_execution_model_only(target, prepared_effective_date="2026-09-21")
    assert first["generated_at"] == original["generated_at"]
    assert first["cumulative_state"] == original["cumulative_state"]
    assert first["recommended_policy"]["missing_bucket_action"] == "keep_original_order"
    assert first["recommended_policy"]["runtime_apply_allowed"] is False
    before = path.read_bytes()
    second = split_plan.refresh_execution_model_only(target, prepared_effective_date="2026-09-21")
    assert first == second and path.read_bytes() == before
    policy = json.loads(split_plan.policy_path(target).read_text())
    assert split_plan.validate_report_policy_generation(first, policy)[0]
    # A source revision invalidates reuse without touching frozen original facts.
    monkeypatch.setattr(split_plan, "_execution_registry_snapshot", lambda: ([], {"status": "verified", "tail_hash": "1" * 64}))
    revised = split_plan.refresh_execution_model_only(target, prepared_effective_date="2026-09-21")
    assert revised["artifact_generation_binding"] != first["artifact_generation_binding"]
    assert revised["cumulative_state"] == original["cumulative_state"]
    policy["execution_model_validation_sha256"] = "bad"
    split_plan._write_json(split_plan.policy_path(target), policy)
    with pytest.raises(ValueError, match="cached_generation_invalid"):
        split_plan.refresh_execution_model_only(target, prepared_effective_date="2026-09-21")




def test_real_atomic_producer_wire_compact_decoder_roundtrip(monkeypatch, tmp_path):
    from types import SimpleNamespace
    from src.tests.test_strategy_owner_replay import entry_owner_event
    from src.tests.test_pipeline_event_logger import _reset_logger_state
    from src.utils import pipeline_event_logger as logger
    from src.engine import sniper_state_handlers as handlers
    from src.engine.sniper_missed_entry_counterfactual import _load_entry_events, _price_ready_plan
    day = datetime.now(timezone(timedelta(hours=9))).date().isoformat()
    original = entry_owner_event(day)
    _reset_logger_state(monkeypatch)
    monkeypatch.setattr(logger, "DATA_DIR", tmp_path)
    monkeypatch.setattr(split_plan, "DATA_DIR", tmp_path)
    monkeypatch.setattr(logger, "TRADING_RULES", SimpleNamespace(PIPELINE_EVENT_JSONL_ENABLED=True,
        PIPELINE_EVENT_SCHEMA_VERSION=3, PIPELINE_EVENT_TEXT_INFO_LOG_ENABLED=False))
    monkeypatch.setattr(logger, "log_info", lambda *a, **k: None)
    monkeypatch.setattr(handlers, "emit_pipeline_event", logger.emit_pipeline_event)
    monkeypatch.setattr(handlers, "observe_candidate_transition_safe", lambda *a, **k: None)
    monkeypatch.setattr(handlers, "_maybe_register_rising_missed_nxt_downstream_block_sampler", lambda *a, **k: None)
    payload = handlers._log_entry_pipeline({"name": "TEST", "id": 77, "strategy": "SCALPING"},
        original.code, original.stage, **original.fields,
        **{f"extra_{i}": str(i) for i in range(60)})
    assert payload["structured_append_succeeded"] is True
    rows, _ = split_plan._bounded_execution_projection(day)
    assert len(rows) == 1
    decoded = _load_entry_events(day, rows=rows)
    assert len(decoded) == 1
    assert _price_ready_plan(decoded[0]) == _price_ready_plan(original)
    assert json.loads(decoded[0].fields["entry_opportunity_replay_seed"]) == original.fields["entry_opportunity_replay_seed"]
    from src.tests.test_strategy_owner_replay import native_entry_loader
    from src.engine.scalping.strategy_owner_replay import build_entry_opportunity_replays
    replay = build_entry_opportunity_replays(day, decoded, micro_loader=native_entry_loader,
        evaluated_at=datetime.fromisoformat(original.emitted_at).timestamp() + 180)
    assert replay["counts"]["completed"] == 1
    assert len(replay["quantity_leg_events"]) == 1
    logger._flush_producer_summary_at_exit()
    monkeypatch.setattr(logger, "_PRODUCER_COMPACTOR", None)


def test_verified_owner_snapshot_preserves_bytes_and_rejects_corruption(tmp_path):
    from src.trading.order.owner_custody_registry import OrderOwnerRegistry, OwnerRegistryError
    registry = OrderOwnerRegistry(tmp_path / "owner.jsonl")
    registry.lock_path.touch()
    registry._append_locked([], {"event": "INTENT_RESERVED", "intent_id": "fixture"})
    before = registry.path.read_bytes()
    rows = registry.verified_events_snapshot()
    assert len(rows) == 1 and registry.path.read_bytes() == before
    with pytest.raises(OwnerRegistryError, match="bounded_projection_required"):
        registry.verified_events_snapshot(max_bytes=1)
    registry.path.write_bytes(before.replace(b"fixture", b"damaged"))
    with pytest.raises(OwnerRegistryError, match="hash_invalid"):
        registry.verified_events_snapshot()



def test_atomic_quantity_leg_loader_cannot_bypass_missing_execution_model(tmp_path):
    split = tmp_path / "split.json"
    split.write_text(json.dumps(dict(source_date="2026-09-17", runtime_apply_allowed=True)))
    policy = dict(source_date="2026-09-17", split_policy_file=str(split),
        split_policy_sha256=hashlib.sha256(split.read_bytes()).hexdigest())
    assert split_plan.quantity_leg_policy_selection_evidence_valid(policy) is False
    split.write_text(json.dumps(dict(source_date="2026-09-17", runtime_apply_allowed=False)))
    policy["split_policy_sha256"] = hashlib.sha256(split.read_bytes()).hexdigest()
    assert split_plan.quantity_leg_policy_selection_evidence_valid(policy) is False



def test_entry_replay_maturity_changes_reuse_identity_only_at_declared_boundary():
    start = datetime.fromisoformat("2026-09-17T10:00:00+09:00").timestamp()
    events = [dict(fields={"entry_opportunity_replay_seed": json.dumps(dict(
        observed_at="2026-09-17T10:00:00+09:00", seed_sha256="a" * 64))})]
    waiting = split_plan._entry_replay_maturity_revision(events, now=start + 179)
    assert waiting == split_plan._entry_replay_maturity_revision(events, now=start + 179.5)
    assert waiting != split_plan._entry_replay_maturity_revision(events, now=start + 180)
    assert split_plan._entry_replay_maturity_revision(events, now=start + 180) == split_plan._entry_replay_maturity_revision(events, now=start + 181)


def _operating_economic_fixture():
    scope='8'*64
    template=dict(leg_count=2,price_offsets_ticks=[0,1],qty_weight_min=.4,qty_weight_max=.4,
        urgency_score=0.,passive_edge_score=0.,policy_mode=split_plan.POLICY_MODE_REAL_PRIMARY_EV,
        candidate_leg_policy_version='entry_split_quantity_fixed_guarded_weights_v1',effective_venue='KRX',
        session_bucket='krx_regular',order_types=['00','00'])
    models=[]
    for day in ['2026-09-08','2026-09-09']:
        for n in range(10):
            models.append(dict(episode_id=f'model-{day}-{n}',scope_sha256=scope,source_date=day,
                status='COMPLETED',origin='real',cost_complete=True,exact_lineage=True,owner='main_scalping',
                vwap_error_bps=0.,receipt_clock_error_sec=.1,quantity_error=0,
                net_error_budget_pct=0.,capital_error_minutes=0.,reserve_error_minutes=0.,false_fill=False,missed_fill=False))
    from src.engine.scalping.strategy_owner_replay import freeze_entry_opportunity, AUTHORITY, ENTRY_OPERATING_SCHEMA, entry_operating_model_identity
    from src.engine.lifecycle.avg_down_policy_replay import snapshot_version
    snapshot={'rules':{},'environment':{},'implementation':{}}
    context=dict(order_leg_ttl_sec=[10,10],order_bundle_hard_ttl_sec=10,order_timeout_owner='explicit_fixture',model_implementation_sha256=entry_operating_model_identity(),schema=ENTRY_OPERATING_SCHEMA,frozen_at='2026-09-08T09:00:00+09:00',policy_snapshot=snapshot,
        exit_policy_version=snapshot_version(snapshot),initial_policy_state={'stock':{'entry_split_order_bucket':'balanced_normal'}},
        budget_krw=100000.,cost_rate=.0023,cost_policy_version='trade_profit_net_realized_pnl:rate=0.0023',
        cost_provenance='frozen_loaded_trade_profit_configuration_not_broker_settlement',stress_cost_rate_increment=.0005,max_frame_gap_sec=5.,**AUTHORITY)
    context['sha256']=split_plan._canonical_sha256(context)
    rows=[]
    for day in ['2026-09-10','2026-09-11']:
        for n in range(15):
            arms={}
            for i,key in enumerate(split_plan.QUANTITY_LEG_FOUR_ARM_IDS):
                arm=dict(**AUTHORITY,status='completed_source_only',actual_fill_evidence=False,requested_qty=10,modeled_filled_qty=10,
                    budget_krw=100000.,net_pnl_krw=200. if i>=2 else 100.,stress_net_pnl_krw=190. if i>=2 else 90.,
                    capital_krw_minutes=100. if i>=2 else 200.,reserve_krw_minutes=10.,fill_participation_rate=1.)
                arm['sha256']=split_plan._canonical_sha256(arm);arms[key]=arm
            plan=dict(valid=True,blockers=[],total_qty=10,deferred_probe_residual_qty=0,
                scanner_promotion_id=f'p-{day}-{n}',action_receipt_id=f'a-{day}-{n}',effective_venue='KRX',
                market_session_bucket='krx_regular',policy_bundle_hash='a'*64,quantity_policy_version='qty-original',
                split_policy_version='leg-original',price_policy_sha256='c'*64,price_plan_sha256='d'*64,
                legs=[dict(qty=8,numeric_price=1000,execution_phase='immediate'),dict(qty=2,numeric_price=999,execution_phase='immediate')])
            seed=freeze_entry_opportunity(plan,stock_code='005930',observed_at=datetime.fromisoformat(day+'T10:00:00+09:00').timestamp()+n*240,operating_context=context)
            scope=split_plan._entry_operating_scope(seed)
            for model in models:model['scope_sha256']=scope
            for arm in arms.values():
                arm.update(modeled_exit_at=day+'T12:00:00+09:00',cost_policy_version=context['cost_policy_version'],
                    cost_provenance=context['cost_provenance'],exit_policy_sha256=context['exit_policy_version'],contract_sha256=context['sha256'],terminal_evidence_sha256='9'*64);arm.pop('sha256');arm['sha256']=split_plan._canonical_sha256(arm)
            row=dict(attempt_id=f'candidate-{day}-{n}',episode_id=f'candidate-episode-{day}-{n}',
                scope_sha256=scope,source_date=day,total_qty=10,budget_krw=100000.,arms=arms,
                context_bucket='balanced_normal',candidate_template=template,origin='counterfactual',owner='main_scalping',seed=seed)
            row['sha256']=split_plan._canonical_sha256(row);rows.append(row)
    return rows,models,{'2026-09-08':10,'2026-09-09':10,'2026-09-10':15,'2026-09-11':15}


def test_operating_economics_positive_and_recomputed_policy_contract(tmp_path):
    rows,models,census=_operating_economic_fixture()
    evidence=split_plan.evaluate_entry_split_operating_economics(rows,models,census,target_date='2026-09-17')
    assert evidence['status']=='positive_candidate'
    assert evidence['primary_operating_ev_pct']==pytest.approx(.2)
    assert evidence['robust_paired_delta_ev_lower_bound_pct']==pytest.approx(.09)
    validation=split_plan.build_execution_model_validation('2026-09-17',[],[],[])
    split_plan._apply_operating_model_support(validation,evidence)
    policy,grid=split_plan._operating_policy('2026-09-17',tmp_path/'report.json',evidence)
    policy.update(execution_model_validation_contract=split_plan.EXECUTION_MODEL_CONTRACT,
        execution_model_validation_sha256=split_plan._canonical_sha256(validation))
    events=split_plan._operating_four_arm_events(evidence)
    proof=split_plan.build_quantity_leg_four_arm_evaluation(events,source_counts={d:n for d,n in census.items() if d>"2026-09-09"})
    assert split_plan.quantity_leg_promotion_evidence_valid(proof)
    report=dict(execution_model_validation=validation,economic_acceptance=evidence,operating_quantity_leg_four_arm_evaluation=proof)
    assert policy['runtime_apply_allowed'] is True and len(grid)==1
    assert split_plan.execution_model_policy_contract_status(report,policy)[0]
    evidence['candidates'][0]['partitions']['holdout']['candidate']['ev_pct']=999.
    assert not split_plan.execution_model_policy_contract_status(report,policy)[0]


@pytest.mark.parametrize('defect,expected', [('no_models','insufficient_sample'),('holdout_error','model_validation_failed'),
    ('no_candidate_holdout','insufficient_sample'),('no_edge','valid_no_edge'),('qty_change','source_gap'),
    ('missing_cost','source_gap')])
def test_operating_economic_dispositions(defect,expected):
    rows,models,census=_operating_economic_fixture()
    if defect=='no_models':models=[]
    if defect=='holdout_error':models[-1]['vwap_error_bps']=1.
    if defect=='no_candidate_holdout':rows=rows[:15];census.pop('2026-09-11')
    if defect=='no_edge':
        for row in rows:
            for key in split_plan.QUANTITY_LEG_FOUR_ARM_IDS[2:]:
                arm=row['arms'][key];arm.update(net_pnl_krw=80.,stress_net_pnl_krw=70.);arm.pop('sha256');arm['sha256']=split_plan._canonical_sha256(arm)
            row.pop('sha256');row['sha256']=split_plan._canonical_sha256(row)
    if defect in ('qty_change','missing_cost'):
        for row in rows:
            arm=row['arms'][split_plan.QUANTITY_LEG_FOUR_ARM_IDS[2]]
            if defect=='qty_change':arm['requested_qty']=11
            else:arm['net_pnl_krw']=None
            arm.pop('sha256');arm['sha256']=split_plan._canonical_sha256(arm);row.pop('sha256');row['sha256']=split_plan._canonical_sha256(row)
    result=split_plan.evaluate_entry_split_operating_economics(rows,models,census,target_date='2026-09-17')
    assert result['status']==expected
    assert not result['candidates']
    assert result['valid_no_edge']==(expected=='valid_no_edge')


def test_operating_holdout_revision_cannot_reuse_a_consumed_date():
    rows,models,census=_operating_economic_fixture()
    first=split_plan.evaluate_entry_split_operating_economics(rows,models,census,target_date='2026-09-17')
    reused=split_plan.evaluate_entry_split_operating_economics(rows,models,census,target_date='2026-09-17',consumed_holdouts=first['consumed_holdouts'])
    assert reused==first
    rows[-1]['attempt_id']='different-after-viewing-holdout';rows[-1].pop('sha256');rows[-1]['sha256']=split_plan._canonical_sha256(rows[-1])
    revised=split_plan.evaluate_entry_split_operating_economics(rows,models,census,target_date='2026-09-17',consumed_holdouts=first['consumed_holdouts'])
    assert revised['status']=='source_gap' and not revised['candidates']


def test_signed_actual_fill_capital_and_reserve_are_distinct():
    diagnostic={'actual_journal_legs':[dict(quantity=10,submitted_price=10000,
        submitted_at='2026-09-17T10:00:00+09:00',terminal_at='2026-09-17T10:00:06+09:00',fills=[
            dict(event_hash='a',observed_at_kst='2026-09-17T10:00:02+09:00',filled_qty=4,fill_amount=40000),
            dict(event_hash='b',observed_at_kst='2026-09-17T10:00:04+09:00',filled_qty=8,fill_amount=80000)])]}
    capital,reserve=split_plan._actual_entry_capital(diagnostic,'2026-09-17T10:01:02+09:00')
    assert capital==pytest.approx(40000+40000*58/60)
    assert reserve==pytest.approx((100000*2+60000*2+20000*2)/60)
    diagnostic['actual_journal_legs'][0]['fills'][1]['filled_qty']=11
    with pytest.raises(ValueError,match='conservation'):split_plan._actual_entry_capital(diagnostic,'2026-09-17T10:01:02+09:00')


def test_post_apply_version_episode_dedup_and_real_only():
    row=dict(episode_id='actual-episode',status='COMPLETED',origin='real',owner='main_scalping',cost_complete=True,
        exact_lineage=True,pid_consumed=True,policy_applied=True,policy_version='v1',policy_sha256='1'*64,
        scope_sha256='2'*64,fill_class='full',completion_date='2026-09-17',net_pnl_krw=200.,profit_rate=.2,reserve_krw_minutes=10.,
        budget_krw=100000.,capital_krw_minutes=100.,net_error_budget_pct=.01)
    result=split_plan.build_entry_split_post_apply_performance([row,row,{**row,'episode_id':'sim','origin':'sim'}],target_date='2026-09-17')
    assert result['groups'][0]['cumulative']['completed_episodes']==1
    assert result['groups'][0]['cumulative']['cost_adjusted_ev_pct']==pytest.approx(.2)
    assert not result['model_delta_ev_is_actual_profit']
    bad=split_plan.build_entry_split_post_apply_performance([row,{**row,'net_pnl_krw':999}],target_date='2026-09-17')
    assert not bad['groups'] and bad['quarantined_episodes']==['actual-episode']




def test_operating_predecessor_state_is_bounded_and_source_bound(monkeypatch,tmp_path):
    monkeypatch.setattr(split_plan,'REPORT_DIR',tmp_path)
    quality={'tuning_input_allowed':True,'status':'PASS'}
    monkeypatch.setattr(split_plan,'_source_quality_summary',lambda day:quality)
    state=dict(through_date='2026-09-16',source_counts={'2026-09-16':2},rows=[],model_rows=[],
        source_quality_bindings={'2026-09-16':split_plan._source_quality_contract_sha256(quality)})
    state['sha256']=split_plan._canonical_sha256(state)
    path=tmp_path/'entry_split_order_plan_2026-09-16.json'
    path.write_text(json.dumps({'operating_economic_state':state}))
    assert split_plan._previous_operating_state('2026-09-17')==state
    quality['tuning_input_allowed']=False
    with pytest.raises(ValueError,match='source_quality_changed'):split_plan._previous_operating_state('2026-09-17')


def test_operating_late_model_availability_and_dispositions():
    rows,models,census=_operating_economic_fixture()
    models[-1]['completion_date']='2026-09-11'
    ev=split_plan.evaluate_entry_split_operating_economics(rows,models,census,target_date='2026-09-17')
    assert not ev['candidates'] and ev['status']=='insufficient_sample'
    for disposition,expected in [('unsupported_scope','unsupported_scope'),('terminal_pending','pending'),('source_gap','source_gap')]:
        row=rows[0].copy();row['arms']={key:{'status':disposition} for key in split_plan.QUANTITY_LEG_FOUR_ARM_IDS}
        ev=split_plan.evaluate_entry_split_operating_economics([row],[],census,target_date='2026-09-17')
        assert ev['status']==expected and ev['primary_operating_ev_pct'] is None


def test_operating_model_change_cannot_reuse_candidate_holdout():
    rows,models,census=_operating_economic_fixture()
    first=split_plan.evaluate_entry_split_operating_economics(rows,models,census,target_date='2026-09-17')
    assert first['candidates']
    models[0]['net_error_budget_pct']=.001
    changed=split_plan.evaluate_entry_split_operating_economics(rows,models,census,target_date='2026-09-17',consumed_holdouts=first['consumed_holdouts'])
    assert changed['status']=='source_gap' and not changed['candidates']
    assert any('already_consumed' in b for c in changed['cohort_checks'] for choice in c['candidates'] for b in choice['blockers'])


def test_initial_seed_survives_baseline_fill_and_completed_cost_producer(monkeypatch,tmp_path):
    from copy import deepcopy
    from src.engine import sniper_state_handlers as handlers
    from src.engine.scalping.strategy_owner_replay import entry_split_actual_economic_receipt
    rows,_,_=_operating_economic_fixture();seed=deepcopy(rows[0]['seed'])
    decision=dict(evaluation_attempt_id=seed['evaluation_attempt_id'],
        machine_bundle_sha256=seed['policy_bundle_sha256'],
        machine_policy_version='machine-v1',machine_policy_sha256='1'*64,
        compact_prompt_version='compact-v1',compact_prompt_sha256='2'*64,
        decision_trace_id='trace-v1',runtime_pid=123)
    decision['sha256']=split_plan._canonical_sha256(decision)
    seed['operating_contract']['entry_decision_version_receipt']=decision
    seed['operating_contract']['sha256']=split_plan._canonical_sha256({
        k:v for k,v in seed['operating_contract'].items() if k!='sha256'})
    seed['seed_sha256']=split_plan._canonical_sha256({k:v for k,v in seed.items() if k!='seed_sha256'})
    order={'qty':10,'entry_split_initial_entry_seed':seed,'entry_split_initial_entry_lineage_conflict':False}
    meta=handlers._split_order_meta_fields(order)
    stock=handlers._entry_split_position_provenance([meta])
    assert stock['entry_split_initial_entry_seed']==seed
    from src.engine import sniper_execution_receipts as receipts
    for keys in (receipts._BUY_RECEIPT_SNAPSHOT_KEYS,receipts._SELL_RECEIPT_SNAPSHOT_KEYS):
        snapshot=receipts._normalized_receipt_snapshot(receipts._receipt_snapshot(stock,keys))
        assert snapshot['entry_split_initial_entry_seed']==seed
    stock.update(code='005930',strategy='SCALPING',realized_pnl_krw=177,sell_execution_receipt_economics_complete=True,sell_execution_receipt_quantity_contract_complete=True)
    # Existing producer accepts KST wall-clock values; no UTC day shift at 20:00.
    result=entry_split_actual_economic_receipt(stock,buy_price=1000,buy_qty=10,profit_rate=1.7654,
        completion_at=datetime.fromisoformat('2026-09-11T20:00:00'))
    assert result['cost_complete'] is True and result['completed_at'].endswith('+09:00')
    assert result['completion_date']=='2026-09-11'
    assert result['entry_decision_pid_consumed'] is True
    assert result['entry_decision_version_receipt']==decision
    assert result['sha256']==split_plan._canonical_sha256({k:v for k,v in result.items() if k!='sha256'})
    monkeypatch.setattr(split_plan,'DATA_DIR',tmp_path)
    path=split_plan._real_post_sell_candidate_path('2026-09-11');path.parent.mkdir(parents=True)
    path.write_text(json.dumps({'fields':{'entry_split_actual_economics':repr(result)}})+'\n')
    found,source=split_plan._bounded_actual_entry_outcomes('2026-09-11')
    assert found==[result] and source['status']=='ready'
    path.write_text('{"incomplete":')
    found,source=split_plan._bounded_actual_entry_outcomes('2026-09-11')
    assert found==[] and source['status']=='source_gap'


def test_actual_pnl_is_reported_with_null_unsupported_model_error():
    row=dict(episode_id='completed-partial',status='COMPLETED',origin='real',owner='main_scalping',cost_complete=True,
        exact_lineage=True,pid_consumed=True,policy_applied=True,policy_version='v1',policy_sha256='1'*64,
        scope_sha256='2'*64,fill_class='partial',completion_date='2026-09-17',net_pnl_krw=200.,profit_rate=.2,
        reserve_krw_minutes=10.,budget_krw=100000.,capital_krw_minutes=100.,net_error_budget_pct=None)
    result=split_plan.build_entry_split_post_apply_performance([row,row],target_date='2026-09-17')
    assert result['groups'][0]['cumulative']['net_pnl_krw']==200.
    assert result['groups'][0]['cumulative']['model_error']['mean_signed_budget_pct'] is None


@pytest.mark.parametrize('missing', ['capital_krw_minutes', 'reserve_krw_minutes'])
def test_completed_net_survives_missing_exposure_with_explicit_gap(missing):
    row=dict(episode_id='actual-missing-exposure',status='COMPLETED',origin='real',owner='main_scalping',cost_complete=True,
        exact_lineage=True,pid_consumed=True,policy_applied=True,policy_version='v1',policy_sha256='1'*64,
        scope_sha256='2'*64,fill_class='full',completion_date='2026-09-17',net_pnl_krw=200.,profit_rate=.2,
        reserve_krw_minutes=10.,budget_krw=100000.,capital_krw_minutes=100.,net_error_budget_pct=None)
    row[missing]=None
    result=split_plan.build_entry_split_post_apply_performance([row,row],target_date='2026-09-17')
    metrics=result['groups'][0]['cumulative']
    assert metrics['completed_episodes']==1 and metrics['net_pnl_krw']==200.
    assert metrics['cost_adjusted_ev_pct']==pytest.approx(.2)
    assert metrics['exposure'][missing] is None
    assert metrics['exposure']['status']=='source_gap'
    assert metrics['exposure']['covered_episodes'][missing]==0
    assert metrics['exposure']['owner'] and metrics['exposure']['closure_test']
    assert result['exposure_gap_episodes']==['actual-missing-exposure']


def test_verified_completed_receipt_survives_capital_join_gap_in_producer():
    rows,_,_=_operating_economic_fixture(); seed=rows[0]['seed']; plan=seed['plan_sha256'];scope=split_plan._entry_operating_scope(seed)
    actual=dict(episode_id='verified-completed-capital-gap',plan_sha256=plan,scope_sha256=scope,
        source_date=seed['source_date'],completion_date=seed['source_date'],completed_at=seed['source_date']+'T12:00:00+09:00',
        entry_qty=10,actual_entry_vwap=1000.,status='COMPLETED',origin='real',owner='main_scalping',cost_complete=True,
        exact_lineage=True,pid_consumed=True,policy_applied=True,policy_version='v1',policy_sha256='1'*64,
        fill_class='full',net_pnl_krw=200.,profit_rate=.2,budget_krw=100000.,
        cost_policy_version=seed['operating_contract']['cost_policy_version'],capital_krw_minutes=None,reserve_krw_minutes=None)
    actual['sha256']=split_plan._canonical_sha256(actual)
    diagnostic=dict(scope={'plan_sha256':plan},actual_filled_qty=10,actual_entry_vwap=1000.,actual_journal_legs=[],
        modeled_filled_qty=10,vwap_error_krw=0.,receipt_clock_error_sec=0.,false_fill=False,missed_fill=False)
    validation={'rows':[diagnostic]}
    models=split_plan._attach_operating_model_outcomes(validation,[{'seed':seed,'operating_arms':rows[0]['arms']}],[actual])
    perf=split_plan.build_entry_split_post_apply_performance(models,target_date='2026-09-17')
    assert perf['groups'][0]['cumulative']['net_pnl_krw']==200.
    assert perf['groups'][0]['cumulative']['exposure']['capital_krw_minutes'] is None
    assert validation['actual_completed_net_comparable_count']==0
    assert models[0]['blocker']=='actual_capital_or_reservation_source_missing'
    evidence=split_plan.evaluate_entry_split_operating_economics(rows,models,{},target_date='2026-09-17')
    assert evidence['status']=='source_gap' and not evidence['candidates'] and not any(x['validated'] for x in evidence['model_scopes'])
