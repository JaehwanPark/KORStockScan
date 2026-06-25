# LDM Hypothesis Parent Refinement - 2026-06-25

## Contract
- decision_authority: `postclose_lifecycle_parent_refinement_pressure`
- consumer: `lifecycle_bucket_discovery`
- consumption_required: `True`
- runtime_effect: `False`
- allowed_runtime_apply: `False`

## Summary
- hypothesis_match_count: `1956`
- runtime_hypothesis_match_count: `1956`
- derived_hypothesis_match_count: `0`
- derived_refinement_input_count: `0`
- raw_event_mutated: `False`
- matched_hypothesis_count: `4`
- refinement_input_count: `4`
- classification_counts: `{'parent_conflict': 1, 'parent_support': 1, 'taxonomy_gap_candidate': 2}`

## Inputs
- `ldm_refinement_7c5842bd79497668` hypothesis=`ldm_hypothesis_e04e4d815fd8d0f9` classification=`taxonomy_gap_candidate` gap=`parent_ambiguous` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|entry_source_parent=entry_source_wait6579|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing|major_holding_parent=holding_missing|scale_in_parent=scale_in_none']` matches=`1011` origin=`runtime_matched` pressure=`4.3521`
- `ldm_refinement_eced95099ff6e892` hypothesis=`ldm_hypothesis_00d0b765311ad7aa` classification=`parent_conflict` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|entry_source_parent=entry_source_wait6579|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing|major_holding_parent=holding_missing|scale_in_parent=scale_in_none']` matches=`624` origin=`runtime_matched` pressure=`5.9495`
- `ldm_refinement_5ddc816b3f7061d2` hypothesis=`ldm_hypothesis_711caa66c89b3f51` classification=`parent_support` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|entry_source_parent=entry_source_wait6579|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing|major_holding_parent=holding_missing|scale_in_parent=scale_in_none']` matches=`252` origin=`runtime_matched` pressure=`4.762`
- `ldm_refinement_c5b11d2d65ace5ff` hypothesis=`ldm_hypothesis_92dfecb5a05caa64` classification=`taxonomy_gap_candidate` gap=`parent_not_found` parents=`[]` matches=`69` origin=`runtime_matched` pressure=`3.8561`
