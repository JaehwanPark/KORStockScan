# LDM Hypothesis Parent Refinement - 2026-08-28

## Contract
- decision_authority: `postclose_lifecycle_parent_refinement_pressure`
- consumer: `lifecycle_bucket_discovery`
- consumption_required: `True`
- runtime_effect: `False`
- allowed_runtime_apply: `False`

## Summary
- hypothesis_match_count: `166`
- runtime_hypothesis_match_count: `0`
- derived_hypothesis_match_count: `166`
- derived_refinement_input_count: `3`
- raw_event_mutated: `False`
- matched_hypothesis_count: `3`
- refinement_input_count: `3`
- classification_counts: `{'parent_support': 1, 'taxonomy_gap_candidate': 2}`

## Inputs
- `ldm_refinement_040aae256baffcb8` hypothesis=`ldm_hypothesis_00d0b765311ad7aa` classification=`taxonomy_gap_candidate` gap=`parent_not_found` parents=`[]` matches=`98` origin=`derived_contract_drift_recompute` pressure=`2.7987`
- `ldm_refinement_3dc65746d9484299` hypothesis=`ldm_hypothesis_92dfecb5a05caa64` classification=`parent_support` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|entry_source_parent=entry_source_blocked_ai_score|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing|major_holding_parent=holding_missing|scale_in_parent=scale_in_none']` matches=`51` origin=`derived_contract_drift_recompute` pressure=`3.8561`
- `ldm_refinement_016c68f552bf25b1` hypothesis=`ldm_hypothesis_e04e4d815fd8d0f9` classification=`taxonomy_gap_candidate` gap=`parent_not_found` parents=`[]` matches=`17` origin=`derived_contract_drift_recompute` pressure=`3.7897`
