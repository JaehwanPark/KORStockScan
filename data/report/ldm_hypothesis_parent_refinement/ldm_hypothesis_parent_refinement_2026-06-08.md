# LDM Hypothesis Parent Refinement - 2026-06-08

## Contract
- decision_authority: `postclose_lifecycle_parent_refinement_pressure`
- consumer: `lifecycle_bucket_discovery`
- consumption_required: `True`
- runtime_effect: `False`
- allowed_runtime_apply: `False`

## Summary
- hypothesis_match_count: `4018`
- matched_hypothesis_count: `4`
- refinement_input_count: `4`
- classification_counts: `{'parent_support': 3, 'taxonomy_gap_candidate': 1}`

## Inputs
- `ldm_refinement_2d749f8d73416b0b` hypothesis=`ldm_hypothesis_dead5c62e79220e3` classification=`parent_support` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|entry_source_parent=entry_source_observed_other|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing|major_holding_parent=holding_missing|scale_in_parent=scale_in_none']` matches=`2722` pressure=`2.6395`
- `ldm_refinement_609338c27b7ebd42` hypothesis=`ldm_hypothesis_00d0b765311ad7aa` classification=`parent_support` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|entry_source_parent=entry_source_blocked_ai_score|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing|major_holding_parent=holding_missing|scale_in_parent=scale_in_none']` matches=`1181` pressure=`2.7987`
- `ldm_refinement_8616dc7215087e28` hypothesis=`ldm_hypothesis_92dfecb5a05caa64` classification=`taxonomy_gap_candidate` gap=`parent_not_found` parents=`[]` matches=`71` pressure=`3.8561`
- `ldm_refinement_b1e7cc67c7681985` hypothesis=`ldm_hypothesis_e04e4d815fd8d0f9` classification=`parent_support` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|entry_source_parent=entry_source_wait6579|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing|major_holding_parent=holding_missing|scale_in_parent=scale_in_none']` matches=`44` pressure=`4.1037`
