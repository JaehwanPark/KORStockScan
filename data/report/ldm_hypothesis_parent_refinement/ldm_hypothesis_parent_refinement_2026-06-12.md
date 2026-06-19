# LDM Hypothesis Parent Refinement - 2026-06-12

## Contract
- decision_authority: `postclose_lifecycle_parent_refinement_pressure`
- consumer: `lifecycle_bucket_discovery`
- consumption_required: `True`
- runtime_effect: `False`
- allowed_runtime_apply: `False`

## Summary
- hypothesis_match_count: `1337`
- runtime_hypothesis_match_count: `0`
- derived_hypothesis_match_count: `1337`
- derived_refinement_input_count: `3`
- raw_event_mutated: `False`
- matched_hypothesis_count: `3`
- refinement_input_count: `3`
- classification_counts: `{'parent_conflict': 1, 'parent_support': 2}`

## Inputs
- `ldm_refinement_8df25ffe7ff6b944` hypothesis=`ldm_hypothesis_e04e4d815fd8d0f9` classification=`parent_support` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|entry_source_parent=entry_source_wait6579|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing|major_holding_parent=holding_missing|scale_in_parent=scale_in_none']` matches=`652` origin=`derived_contract_drift_recompute` pressure=`5.8317`
- `ldm_refinement_dda62c883299b94c` hypothesis=`ldm_hypothesis_00d0b765311ad7aa` classification=`parent_conflict` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|entry_source_parent=entry_source_blocked_ai_score|submit_quality_parent=submit_price_or_liquidity_guard_block|exit_outcome_parent=exit_good_or_take_profit|major_holding_parent=holding_active_decision|scale_in_parent=scale_in_none']` matches=`623` origin=`derived_contract_drift_recompute` pressure=`4.9073`
- `ldm_refinement_8a49a49c35b8db99` hypothesis=`ldm_hypothesis_92dfecb5a05caa64` classification=`parent_support` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|entry_source_parent=entry_source_blocked_ai_score|submit_quality_parent=submit_stale_context_or_quote|exit_outcome_parent=exit_missed_upside|major_holding_parent=holding_active_decision|scale_in_parent=scale_in_none']` matches=`62` origin=`derived_contract_drift_recompute` pressure=`4.7462`
