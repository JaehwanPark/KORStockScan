# LDM Hypothesis Parent Refinement - 2026-07-02

## Contract
- decision_authority: `postclose_lifecycle_parent_refinement_pressure`
- consumer: `lifecycle_bucket_discovery`
- consumption_required: `True`
- runtime_effect: `False`
- allowed_runtime_apply: `False`

## Summary
- hypothesis_match_count: `1736`
- runtime_hypothesis_match_count: `1736`
- derived_hypothesis_match_count: `0`
- derived_refinement_input_count: `0`
- raw_event_mutated: `False`
- matched_hypothesis_count: `4`
- refinement_input_count: `4`
- classification_counts: `{'parent_conflict': 1, 'parent_support': 2, 'taxonomy_gap_candidate': 1}`

## Inputs
- `ldm_refinement_4bc5b03bd050c12b` hypothesis=`ldm_hypothesis_e04e4d815fd8d0f9` classification=`parent_conflict` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|entry_source_parent=entry_source_wait6579|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing|major_holding_parent=holding_missing|scale_in_parent=scale_in_none']` matches=`1037` origin=`runtime_matched` pressure=`7.7424`
- `ldm_refinement_ea1e4590d4c9266b` hypothesis=`ldm_hypothesis_00d0b765311ad7aa` classification=`taxonomy_gap_candidate` gap=`parent_ambiguous` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|entry_source_parent=entry_source_wait6579|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing|major_holding_parent=holding_missing|scale_in_parent=scale_in_none', 'lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|entry_source_parent=entry_source_wait6579|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing|major_holding_parent=holding_missing|scale_in_parent=scale_in_none']` matches=`547` origin=`runtime_matched` pressure=`8.2099`
- `ldm_refinement_a8de4ccbb98364f2` hypothesis=`ldm_hypothesis_92dfecb5a05caa64` classification=`parent_support` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|entry_source_parent=entry_source_blocked_ai_score|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing|major_holding_parent=holding_missing|scale_in_parent=scale_in_none']` matches=`102` origin=`runtime_matched` pressure=`3.8561`
- `ldm_refinement_a5c40bee41c7a6ab` hypothesis=`ldm_hypothesis_711caa66c89b3f51` classification=`parent_support` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|entry_source_parent=entry_source_wait6579|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing|major_holding_parent=holding_missing|scale_in_parent=scale_in_none']` matches=`50` origin=`runtime_matched` pressure=`5.4825`
