# LDM Hypothesis Parent Refinement - 2026-07-09

## Contract
- decision_authority: `postclose_lifecycle_parent_refinement_pressure`
- consumer: `lifecycle_bucket_discovery`
- consumption_required: `True`
- runtime_effect: `False`
- allowed_runtime_apply: `False`

## Summary
- hypothesis_match_count: `529`
- runtime_hypothesis_match_count: `529`
- derived_hypothesis_match_count: `0`
- derived_refinement_input_count: `0`
- raw_event_mutated: `False`
- matched_hypothesis_count: `4`
- refinement_input_count: `4`
- classification_counts: `{'parent_conflict': 2, 'taxonomy_gap_candidate': 2}`

## Inputs
- `ldm_refinement_a1782b3585bce622` hypothesis=`ldm_hypothesis_00d0b765311ad7aa` classification=`parent_conflict` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|entry_source_parent=entry_source_blocked_ai_score|submit_quality_parent=submit_price_or_liquidity_guard_block|exit_outcome_parent=exit_missing|major_holding_parent=holding_active_decision|scale_in_parent=scale_in_none']` matches=`276` origin=`runtime_matched` pressure=`3.8374`
- `ldm_refinement_5742709b0b3ca652` hypothesis=`ldm_hypothesis_e04e4d815fd8d0f9` classification=`taxonomy_gap_candidate` gap=`parent_not_found` parents=`[]` matches=`218` origin=`runtime_matched` pressure=`4.0897`
- `ldm_refinement_a5a73ddab7c2dcc3` hypothesis=`ldm_hypothesis_92dfecb5a05caa64` classification=`taxonomy_gap_candidate` gap=`parent_not_found` parents=`[]` matches=`25` origin=`runtime_matched` pressure=`3.8561`
- `ldm_refinement_72f235ced889d33f` hypothesis=`ldm_hypothesis_711caa66c89b3f51` classification=`parent_conflict` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|entry_source_parent=entry_source_wait6579|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing|major_holding_parent=holding_missing|scale_in_parent=scale_in_none']` matches=`10` origin=`runtime_matched` pressure=`6.0257`
