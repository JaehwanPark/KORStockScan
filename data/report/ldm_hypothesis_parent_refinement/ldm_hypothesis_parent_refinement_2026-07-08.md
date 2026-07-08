# LDM Hypothesis Parent Refinement - 2026-07-08

## Contract
- decision_authority: `postclose_lifecycle_parent_refinement_pressure`
- consumer: `lifecycle_bucket_discovery`
- consumption_required: `True`
- runtime_effect: `False`
- allowed_runtime_apply: `False`

## Summary
- hypothesis_match_count: `1420`
- runtime_hypothesis_match_count: `0`
- derived_hypothesis_match_count: `1420`
- derived_refinement_input_count: `4`
- raw_event_mutated: `False`
- matched_hypothesis_count: `4`
- refinement_input_count: `4`
- classification_counts: `{'parent_conflict': 1, 'taxonomy_gap_candidate': 3}`

## Inputs
- `ldm_refinement_f47f95f874caea62` hypothesis=`ldm_hypothesis_e04e4d815fd8d0f9` classification=`taxonomy_gap_candidate` gap=`parent_not_found` parents=`[]` matches=`1037` origin=`derived_contract_drift_recompute` pressure=`4.0897`
- `ldm_refinement_759ec2cd1f464fd3` hypothesis=`ldm_hypothesis_00d0b765311ad7aa` classification=`taxonomy_gap_candidate` gap=`parent_not_found` parents=`[]` matches=`358` origin=`derived_contract_drift_recompute` pressure=`2.7987`
- `ldm_refinement_e1a5c77384383c31` hypothesis=`ldm_hypothesis_92dfecb5a05caa64` classification=`taxonomy_gap_candidate` gap=`parent_not_found` parents=`[]` matches=`18` origin=`derived_contract_drift_recompute` pressure=`3.6561`
- `ldm_refinement_f619f1630d367f43` hypothesis=`ldm_hypothesis_711caa66c89b3f51` classification=`parent_conflict` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|entry_source_parent=entry_source_wait6579|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing|major_holding_parent=holding_missing|scale_in_parent=scale_in_none']` matches=`7` origin=`derived_contract_drift_recompute` pressure=`5.9045`
