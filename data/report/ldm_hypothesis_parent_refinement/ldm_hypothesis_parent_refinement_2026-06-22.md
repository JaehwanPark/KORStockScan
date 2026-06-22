# LDM Hypothesis Parent Refinement - 2026-06-22

## Contract
- decision_authority: `postclose_lifecycle_parent_refinement_pressure`
- consumer: `lifecycle_bucket_discovery`
- consumption_required: `True`
- runtime_effect: `False`
- allowed_runtime_apply: `False`

## Summary
- hypothesis_match_count: `1941`
- runtime_hypothesis_match_count: `1941`
- derived_hypothesis_match_count: `0`
- derived_refinement_input_count: `0`
- raw_event_mutated: `False`
- matched_hypothesis_count: `4`
- refinement_input_count: `4`
- classification_counts: `{'parent_support': 2, 'taxonomy_gap_candidate': 2}`

## Inputs
- `ldm_refinement_9ac4cac762767994` hypothesis=`ldm_hypothesis_e04e4d815fd8d0f9` classification=`taxonomy_gap_candidate` gap=`parent_not_found` parents=`[]` matches=`1557` origin=`runtime_matched` pressure=`4.0897`
- `ldm_refinement_60a7a29f09b5d325` hypothesis=`ldm_hypothesis_711caa66c89b3f51` classification=`parent_support` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|entry_source_parent=entry_source_wait6579|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing|major_holding_parent=holding_missing|scale_in_parent=scale_in_none']` matches=`234` origin=`runtime_matched` pressure=`4.9488`
- `ldm_refinement_ed1b9bf94dd618e7` hypothesis=`ldm_hypothesis_00d0b765311ad7aa` classification=`taxonomy_gap_candidate` gap=`parent_not_found` parents=`[]` matches=`106` origin=`runtime_matched` pressure=`2.7987`
- `ldm_refinement_aa12dea99172113e` hypothesis=`ldm_hypothesis_92dfecb5a05caa64` classification=`parent_support` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|entry_source_parent=entry_source_blocked_ai_score|submit_quality_parent=submit_stale_context_or_quote|exit_outcome_parent=exit_missed_upside|major_holding_parent=holding_observed_other|scale_in_parent=scale_in_none']` matches=`44` origin=`runtime_matched` pressure=`4.8681`
