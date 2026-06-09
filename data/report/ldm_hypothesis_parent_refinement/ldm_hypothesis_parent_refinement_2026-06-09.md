# LDM Hypothesis Parent Refinement - 2026-06-09

## Contract
- decision_authority: `postclose_lifecycle_parent_refinement_pressure`
- consumer: `lifecycle_bucket_discovery`
- consumption_required: `True`
- runtime_effect: `False`
- allowed_runtime_apply: `False`

## Summary
- hypothesis_match_count: `8315`
- matched_hypothesis_count: `4`
- refinement_input_count: `4`
- classification_counts: `{'parent_conflict': 1, 'parent_support': 2, 'taxonomy_gap_candidate': 1}`

## Inputs
- `ldm_refinement_7f6d6ffe442e2c99` hypothesis=`ldm_hypothesis_00d0b765311ad7aa` classification=`parent_conflict` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|entry_source_parent=entry_source_wait6579|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing|major_holding_parent=holding_missing|scale_in_parent=scale_in_none']` matches=`6077` pressure=`3.9683`
- `ldm_refinement_0ab3e7abbebe9ec5` hypothesis=`ldm_hypothesis_e04e4d815fd8d0f9` classification=`parent_support` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|entry_source_parent=entry_source_wait6579|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing|major_holding_parent=holding_missing|scale_in_parent=scale_in_none']` matches=`1646` pressure=`5.8085`
- `ldm_refinement_c31f72d5895b9bf9` hypothesis=`ldm_hypothesis_92dfecb5a05caa64` classification=`taxonomy_gap_candidate` gap=`parent_not_found` parents=`[]` matches=`470` pressure=`3.8561`
- `ldm_refinement_20ef69d9642950b2` hypothesis=`ldm_hypothesis_711caa66c89b3f51` classification=`parent_support` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|entry_source_parent=entry_source_wait6579|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing|major_holding_parent=holding_missing|scale_in_parent=scale_in_none']` matches=`122` pressure=`5.8549`
