# LDM Hypothesis Parent Refinement - 2026-06-18

## Contract
- decision_authority: `postclose_lifecycle_parent_refinement_pressure`
- consumer: `lifecycle_bucket_discovery`
- consumption_required: `True`
- runtime_effect: `False`
- allowed_runtime_apply: `False`

## Summary
- hypothesis_match_count: `10449`
- runtime_hypothesis_match_count: `0`
- derived_hypothesis_match_count: `10449`
- derived_refinement_input_count: `4`
- raw_event_mutated: `False`
- matched_hypothesis_count: `4`
- refinement_input_count: `4`
- classification_counts: `{'parent_support': 4}`

## Inputs
- `ldm_refinement_d7138f56101e4dbb` hypothesis=`ldm_hypothesis_e04e4d815fd8d0f9` classification=`parent_support` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing']` matches=`5442` origin=`derived_contract_drift_recompute` pressure=`4.5987`
- `ldm_refinement_26ad5b4482cbfed4` hypothesis=`ldm_hypothesis_00d0b765311ad7aa` classification=`parent_support` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_watch_recovery|submit_quality_parent=submit_price_or_liquidity_guard_block|exit_outcome_parent=exit_good_or_take_profit']` matches=`2868` origin=`derived_contract_drift_recompute` pressure=`3.622`
- `ldm_refinement_6d1c1803e741e4c3` hypothesis=`ldm_hypothesis_711caa66c89b3f51` classification=`parent_support` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|submit_quality_parent=submit_missing|exit_outcome_parent=exit_missing']` matches=`1732` origin=`derived_contract_drift_recompute` pressure=`4.3714`
- `ldm_refinement_a6cb30eeb6159375` hypothesis=`ldm_hypothesis_92dfecb5a05caa64` classification=`parent_support` gap=`-` parents=`['lifecycle_flow:combo_lifecycle_flow:entry_score_parent=score_mid_recovery|submit_quality_parent=submit_stale_context_or_quote|exit_outcome_parent=exit_missing']` matches=`407` origin=`derived_contract_drift_recompute` pressure=`5.6122`
