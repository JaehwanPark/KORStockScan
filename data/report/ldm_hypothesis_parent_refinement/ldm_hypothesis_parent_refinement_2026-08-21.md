# LDM Hypothesis Parent Refinement - 2026-08-21

## Contract
- decision_authority: `postclose_lifecycle_parent_refinement_pressure`
- consumer: `lifecycle_bucket_discovery`
- consumption_required: `True`
- runtime_effect: `False`
- allowed_runtime_apply: `False`

## Summary
- hypothesis_match_count: `90`
- runtime_hypothesis_match_count: `0`
- derived_hypothesis_match_count: `90`
- derived_refinement_input_count: `3`
- raw_event_mutated: `False`
- matched_hypothesis_count: `3`
- refinement_input_count: `3`
- classification_counts: `{'parent_support': 1, 'taxonomy_gap_candidate': 2}`

## Inputs
- `ldm_refinement_3abae619e6a329d9` hypothesis=`ldm_hypothesis_92dfecb5a05caa64` classification=`parent_support` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|entry_source_parent=entry_source_blocked_ai_score|submit_quality_parent=submit_revalidation_ok|exit_outcome_parent=exit_good_or_take_profit|major_holding_parent=holding_active_decision|scale_in_parent=scale_in_none|holding_action_parent=holding_action_wait|exit_rule_parent=exit_rule_take_profit']` matches=`64` origin=`derived_contract_drift_recompute` pressure=`5.593`
- `ldm_refinement_6baf5eafd9a9d4da` hypothesis=`ldm_hypothesis_00d0b765311ad7aa` classification=`taxonomy_gap_candidate` gap=`parent_not_found` parents=`[]` matches=`18` origin=`derived_contract_drift_recompute` pressure=`2.5987`
- `ldm_refinement_52321e19e8039403` hypothesis=`ldm_hypothesis_711caa66c89b3f51` classification=`taxonomy_gap_candidate` gap=`parent_not_found` parents=`[]` matches=`8` origin=`derived_contract_drift_recompute` pressure=`2.9509`
