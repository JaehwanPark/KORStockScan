# LDM Hypothesis Parent Refinement - 2026-06-24

## Contract
- decision_authority: `postclose_lifecycle_parent_refinement_pressure`
- consumer: `lifecycle_bucket_discovery`
- consumption_required: `True`
- runtime_effect: `False`
- allowed_runtime_apply: `False`

## Summary
- hypothesis_match_count: `2598`
- runtime_hypothesis_match_count: `2598`
- derived_hypothesis_match_count: `0`
- derived_refinement_input_count: `0`
- raw_event_mutated: `False`
- matched_hypothesis_count: `4`
- refinement_input_count: `4`
- classification_counts: `{'parent_support': 1, 'taxonomy_gap_candidate': 3}`

## Inputs
- `ldm_refinement_78352eb29d13958b` hypothesis=`ldm_hypothesis_e04e4d815fd8d0f9` classification=`taxonomy_gap_candidate` gap=`parent_not_found` parents=`[]` matches=`1636` origin=`runtime_matched` pressure=`4.0897`
- `ldm_refinement_3992b793d785f68e` hypothesis=`ldm_hypothesis_00d0b765311ad7aa` classification=`taxonomy_gap_candidate` gap=`parent_ambiguous` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|entry_source_parent=entry_source_wait6579|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing|major_holding_parent=holding_missing|scale_in_parent=scale_in_none']` matches=`770` origin=`runtime_matched` pressure=`5.1571`
- `ldm_refinement_0c3854e60a4a479c` hypothesis=`ldm_hypothesis_711caa66c89b3f51` classification=`parent_support` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|entry_source_parent=entry_source_wait6579|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing|major_holding_parent=holding_missing|scale_in_parent=scale_in_none']` matches=`119` origin=`runtime_matched` pressure=`4.7421`
- `ldm_refinement_e11cb652bbdc78e9` hypothesis=`ldm_hypothesis_92dfecb5a05caa64` classification=`taxonomy_gap_candidate` gap=`parent_not_found` parents=`[]` matches=`73` origin=`runtime_matched` pressure=`3.8561`
