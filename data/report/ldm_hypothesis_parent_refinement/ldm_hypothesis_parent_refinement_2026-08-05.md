# LDM Hypothesis Parent Refinement - 2026-08-05

## Contract
- decision_authority: `postclose_lifecycle_parent_refinement_pressure`
- consumer: `lifecycle_bucket_discovery`
- consumption_required: `True`
- runtime_effect: `False`
- allowed_runtime_apply: `False`

## Summary
- hypothesis_match_count: `202`
- runtime_hypothesis_match_count: `0`
- derived_hypothesis_match_count: `202`
- derived_refinement_input_count: `4`
- raw_event_mutated: `False`
- matched_hypothesis_count: `4`
- refinement_input_count: `4`
- classification_counts: `{'parent_support': 2, 'taxonomy_gap_candidate': 2}`

## Inputs
- `ldm_refinement_6fe819a03603f989` hypothesis=`ldm_hypothesis_00d0b765311ad7aa` classification=`parent_support` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|entry_source_parent=entry_source_blocked_ai_score|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing|major_holding_parent=holding_missing|scale_in_parent=scale_in_none']` matches=`112` origin=`derived_contract_drift_recompute` pressure=`2.7987`
- `ldm_refinement_81dd2fc31b43c8d1` hypothesis=`ldm_hypothesis_e04e4d815fd8d0f9` classification=`taxonomy_gap_candidate` gap=`parent_not_found` parents=`[]` matches=`53` origin=`derived_contract_drift_recompute` pressure=`4.0897`
- `ldm_refinement_9d00aaede38bd61c` hypothesis=`ldm_hypothesis_711caa66c89b3f51` classification=`taxonomy_gap_candidate` gap=`parent_not_found` parents=`[]` matches=`19` origin=`derived_contract_drift_recompute` pressure=`4.0509`
- `ldm_refinement_3ceb2f44b4ced1f1` hypothesis=`ldm_hypothesis_92dfecb5a05caa64` classification=`parent_support` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|entry_source_parent=entry_source_blocked_ai_score|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing|major_holding_parent=holding_missing|scale_in_parent=scale_in_none']` matches=`18` origin=`derived_contract_drift_recompute` pressure=`3.6561`
