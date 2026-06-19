# LDM Hypothesis Parent Refinement - 2026-06-16

## Contract
- decision_authority: `postclose_lifecycle_parent_refinement_pressure`
- consumer: `lifecycle_bucket_discovery`
- consumption_required: `True`
- runtime_effect: `False`
- allowed_runtime_apply: `False`

## Summary
- hypothesis_match_count: `3567`
- runtime_hypothesis_match_count: `0`
- derived_hypothesis_match_count: `3567`
- derived_refinement_input_count: `4`
- raw_event_mutated: `False`
- matched_hypothesis_count: `4`
- refinement_input_count: `4`
- classification_counts: `{'parent_support': 2, 'taxonomy_gap_candidate': 2}`

## Inputs
- `ldm_refinement_c31972141e831c1c` hypothesis=`ldm_hypothesis_00d0b765311ad7aa` classification=`parent_support` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|entry_source_parent=entry_source_blocked_ai_score|submit_quality_parent=submit_stale_context_or_quote|exit_outcome_parent=exit_missed_upside|major_holding_parent=holding_active_decision|scale_in_parent=scale_in_none']` matches=`2166` origin=`derived_contract_drift_recompute` pressure=`3.6225`
- `ldm_refinement_e7027055c25b76de` hypothesis=`ldm_hypothesis_e04e4d815fd8d0f9` classification=`taxonomy_gap_candidate` gap=`parent_not_found` parents=`[]` matches=`817` origin=`derived_contract_drift_recompute` pressure=`4.0897`
- `ldm_refinement_44a6d1dafc5209ea` hypothesis=`ldm_hypothesis_92dfecb5a05caa64` classification=`parent_support` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|entry_source_parent=entry_source_blocked_ai_score|submit_quality_parent=submit_stale_context_or_quote|exit_outcome_parent=exit_missed_upside|major_holding_parent=holding_active_decision|scale_in_parent=scale_in_none']` matches=`550` origin=`derived_contract_drift_recompute` pressure=`4.8034`
- `ldm_refinement_b72b151c863bdfae` hypothesis=`ldm_hypothesis_711caa66c89b3f51` classification=`taxonomy_gap_candidate` gap=`parent_not_found` parents=`[]` matches=`34` origin=`derived_contract_drift_recompute` pressure=`4.1509`
