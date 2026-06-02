# LDM Hypothesis Parent Refinement - 2026-06-02

## Contract
- decision_authority: `postclose_lifecycle_parent_refinement_pressure`
- consumer: `lifecycle_bucket_discovery`
- consumption_required: `True`
- runtime_effect: `False`
- allowed_runtime_apply: `False`

## Summary
- hypothesis_match_count: `5876`
- matched_hypothesis_count: `3`
- refinement_input_count: `3`
- classification_counts: `{'parent_support': 2, 'taxonomy_gap_candidate': 1}`

## Inputs
- `ldm_refinement_4f0fb768bf56ed39` hypothesis=`ldm_hypothesis_00d0b765311ad7aa` classification=`parent_support` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|entry_source_parent=entry_source_blocked_ai_score|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing|major_holding_parent=holding_missing|scale_in_parent=scale_in_none']` matches=`5136` pressure=`2.7987`
- `ldm_refinement_e93968f8c34d2168` hypothesis=`ldm_hypothesis_dead5c62e79220e3` classification=`taxonomy_gap_candidate` gap=`parent_not_found` parents=`[]` matches=`531` pressure=`2.6395`
- `ldm_refinement_da335abcff642f14` hypothesis=`ldm_hypothesis_92dfecb5a05caa64` classification=`parent_support` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|entry_source_parent=entry_source_blocked_ai_score|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing|major_holding_parent=holding_missing|scale_in_parent=scale_in_none']` matches=`209` pressure=`3.8561`
