"""Frozen non-Samsung pullback proposal; offline only, never registered live."""
from copy import deepcopy

from src.engine.scalping import entry_setup_evidence as E
from src.engine.scalping import entry_strategy_policy as S
from src.engine.scalping.entry_machine_observation import number

RECIPE = 'non_samsung_pullback_buy_flow_report_v1'
SOFT_CONFIRMATION = frozenset({
    'trigger_confirmation_missing', 'volume_confirmation_missing',
    'micro_continuation_unconfirmed', 'no_supported_setup',
})
AUTHORITY = dict(
    schema=RECIPE, runtime_effect=False, allowed_runtime_apply=False,
    actual_order_submitted=False, broker_order_forbidden=True,
    policy_selected=False, registered_runtime_policy=False,
    metric_role='main_entry_win_rate_selection',
    decision_authority='offline_machine_recipe_proposal',
    window_policy='frozen_predecision_capture_and_parent',
    sample_floor='row_source_contract_not_live_promotion',
    primary_decision_metric='cost_bound_target_before_stop',
    source_quality_gate='original_payload_hash_and_parent_source_guards',
    forbidden_uses=['runtime_apply', 'policy_publication', 'realized_profit',
                    'native_identity_synthesis'],
)


def condition(raw):
    from src.engine.scalping.entry_admission_recipe import condition as shared_condition
    return shared_condition(raw)


def evaluate(setup, parent):
    from src.engine.scalping.entry_admission_recipe import evaluate as shared_evaluate
    baseline = E.mechanistic_entry_policy_decision(setup, policy=parent)
    receipt = shared_evaluate(setup, parent, baseline=baseline,
        situation_veto=E._apply_entry_situation_veto)
    return {**receipt, **AUTHORITY}
