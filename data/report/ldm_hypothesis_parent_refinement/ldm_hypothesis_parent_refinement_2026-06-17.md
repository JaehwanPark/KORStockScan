# LDM Hypothesis Parent Refinement - 2026-06-17

## Contract
- decision_authority: `postclose_lifecycle_parent_refinement_pressure`
- consumer: `lifecycle_bucket_discovery`
- consumption_required: `True`
- runtime_effect: `False`
- allowed_runtime_apply: `False`

## Summary
- hypothesis_match_count: `1010`
- runtime_hypothesis_match_count: `0`
- derived_hypothesis_match_count: `1010`
- derived_refinement_input_count: `4`
- raw_event_mutated: `False`
- matched_hypothesis_count: `4`
- refinement_input_count: `4`
- classification_counts: `{'parent_conflict': 1, 'parent_support': 2, 'taxonomy_gap_candidate': 1}`

## Inputs
- `ldm_refinement_1805782525d1a11d` hypothesis=`ldm_hypothesis_00d0b765311ad7aa` classification=`parent_conflict` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing']` matches=`606` origin=`derived_contract_drift_recompute` pressure=`6.478`
- `ldm_refinement_7fe539eae4f0754e` hypothesis=`ldm_hypothesis_e04e4d815fd8d0f9` classification=`parent_support` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing']` matches=`341` origin=`derived_contract_drift_recompute` pressure=`4.8806`
- `ldm_refinement_52db812d8548be5d` hypothesis=`ldm_hypothesis_92dfecb5a05caa64` classification=`taxonomy_gap_candidate` gap=`parent_not_found` parents=`[]` matches=`39` origin=`derived_contract_drift_recompute` pressure=`3.8561`
- `ldm_refinement_83719e41c3f660bb` hypothesis=`ldm_hypothesis_711caa66c89b3f51` classification=`parent_support` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing']` matches=`24` origin=`derived_contract_drift_recompute` pressure=`4.4101`
