# LDM Hypothesis Parent Refinement - 2026-06-19

## Contract
- decision_authority: `postclose_lifecycle_parent_refinement_pressure`
- consumer: `lifecycle_bucket_discovery`
- consumption_required: `True`
- runtime_effect: `False`
- allowed_runtime_apply: `False`

## Summary
- hypothesis_match_count: `1723`
- runtime_hypothesis_match_count: `0`
- derived_hypothesis_match_count: `1723`
- derived_refinement_input_count: `3`
- raw_event_mutated: `False`
- matched_hypothesis_count: `3`
- refinement_input_count: `3`
- classification_counts: `{'parent_support': 2, 'taxonomy_gap_candidate': 1}`

## Inputs
- `ldm_refinement_6c7edc416c7279ba` hypothesis=`ldm_hypothesis_e04e4d815fd8d0f9` classification=`parent_support` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing']` matches=`1247` origin=`derived_contract_drift_recompute` pressure=`5.3499`
- `ldm_refinement_1e1f31ad8abaffd1` hypothesis=`ldm_hypothesis_00d0b765311ad7aa` classification=`taxonomy_gap_candidate` gap=`parent_not_found` parents=`[]` matches=`323` origin=`derived_contract_drift_recompute` pressure=`2.7987`
- `ldm_refinement_1d39f32fcdbc5e3d` hypothesis=`ldm_hypothesis_711caa66c89b3f51` classification=`parent_support` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing']` matches=`153` origin=`derived_contract_drift_recompute` pressure=`4.5205`
