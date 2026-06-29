# LDM Hypothesis Parent Refinement - 2026-06-29

## Contract
- decision_authority: `postclose_lifecycle_parent_refinement_pressure`
- consumer: `lifecycle_bucket_discovery`
- consumption_required: `True`
- runtime_effect: `False`
- allowed_runtime_apply: `False`

## Summary
- hypothesis_match_count: `2285`
- runtime_hypothesis_match_count: `0`
- derived_hypothesis_match_count: `2285`
- derived_refinement_input_count: `4`
- raw_event_mutated: `False`
- matched_hypothesis_count: `4`
- refinement_input_count: `4`
- classification_counts: `{'parent_conflict': 1, 'parent_support': 1, 'taxonomy_gap_candidate': 2}`

## Inputs
- `ldm_refinement_519abfbfb21fbbcc` hypothesis=`ldm_hypothesis_e04e4d815fd8d0f9` classification=`parent_conflict` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|entry_source_parent=entry_source_wait6579|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing|major_holding_parent=holding_missing|scale_in_parent=scale_in_none']` matches=`1356` origin=`derived_contract_drift_recompute` pressure=`6.4398`
- `ldm_refinement_48d41f6d973883ce` hypothesis=`ldm_hypothesis_00d0b765311ad7aa` classification=`taxonomy_gap_candidate` gap=`parent_not_found` parents=`[]` matches=`914` origin=`derived_contract_drift_recompute` pressure=`2.7987`
- `ldm_refinement_4bffb451eb35b281` hypothesis=`ldm_hypothesis_711caa66c89b3f51` classification=`parent_support` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|entry_source_parent=entry_source_wait6579|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing|major_holding_parent=holding_missing|scale_in_parent=scale_in_none']` matches=`8` origin=`derived_contract_drift_recompute` pressure=`3.7037`
- `ldm_refinement_1e20a8785bd2d28c` hypothesis=`ldm_hypothesis_92dfecb5a05caa64` classification=`taxonomy_gap_candidate` gap=`parent_not_found` parents=`[]` matches=`7` origin=`derived_contract_drift_recompute` pressure=`2.5561`
