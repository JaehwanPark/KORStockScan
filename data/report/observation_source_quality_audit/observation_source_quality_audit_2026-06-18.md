# Observation Source Quality Audit - 2026-06-18

- status: `warning`
- event_count: `181513`
- tuning_input_policy: `exclude_defective_rows_not_full_day_raw`
- hard_blocking_excluded_row_count: `18`
- tuning_input_allowed: `False`
- decision_authority: `source_quality_only`
- runtime_effect: `False`
- forbidden_uses: `runtime_threshold_apply, order_submit, provider_route_change, bot_restart, real_execution_quality_approval`

## Warning Stages
- `ai_numeric_consistency_recheck_evaluated` sample=`9` missing=`{'inconsistency_field': 1.0, 'inconsistency_reason': 1.0, 'recheck_action': 1.0, 'recheck_score': 1.0, 'recheck_reason_excerpt': 1.0}` zero=`{}`
- `ai_numeric_consistency_recheck_skipped` sample=`9` missing=`{'inconsistency_field': 1.0, 'inconsistency_reason': 1.0, 'recheck_action': 1.0, 'recheck_score': 1.0, 'recheck_reason_excerpt': 1.0}` zero=`{}`

## Hard Blocking Row Exclusions
- line=`180778` stage=`ai_numeric_consistency_recheck_evaluated` code=`032830` missing=`['inconsistency_field', 'inconsistency_reason', 'recheck_action', 'recheck_score', 'recheck_reason_excerpt']` zero=`[]` invalid=`[]`
- line=`180779` stage=`ai_numeric_consistency_recheck_skipped` code=`032830` missing=`['inconsistency_field', 'inconsistency_reason', 'recheck_action', 'recheck_score', 'recheck_reason_excerpt']` zero=`[]` invalid=`[]`
- line=`180792` stage=`ai_numeric_consistency_recheck_evaluated` code=`122640` missing=`['inconsistency_field', 'inconsistency_reason', 'recheck_action', 'recheck_score', 'recheck_reason_excerpt']` zero=`[]` invalid=`[]`
- line=`180793` stage=`ai_numeric_consistency_recheck_skipped` code=`122640` missing=`['inconsistency_field', 'inconsistency_reason', 'recheck_action', 'recheck_score', 'recheck_reason_excerpt']` zero=`[]` invalid=`[]`
- line=`180805` stage=`ai_numeric_consistency_recheck_evaluated` code=`067370` missing=`['inconsistency_field', 'inconsistency_reason', 'recheck_action', 'recheck_score', 'recheck_reason_excerpt']` zero=`[]` invalid=`[]`
- line=`180806` stage=`ai_numeric_consistency_recheck_skipped` code=`067370` missing=`['inconsistency_field', 'inconsistency_reason', 'recheck_action', 'recheck_score', 'recheck_reason_excerpt']` zero=`[]` invalid=`[]`
- line=`180987` stage=`ai_numeric_consistency_recheck_evaluated` code=`001820` missing=`['inconsistency_field', 'inconsistency_reason', 'recheck_action', 'recheck_score', 'recheck_reason_excerpt']` zero=`[]` invalid=`[]`
- line=`180988` stage=`ai_numeric_consistency_recheck_skipped` code=`001820` missing=`['inconsistency_field', 'inconsistency_reason', 'recheck_action', 'recheck_score', 'recheck_reason_excerpt']` zero=`[]` invalid=`[]`
- line=`181018` stage=`ai_numeric_consistency_recheck_evaluated` code=`159010` missing=`['inconsistency_field', 'inconsistency_reason', 'recheck_action', 'recheck_score', 'recheck_reason_excerpt']` zero=`[]` invalid=`[]`
- line=`181019` stage=`ai_numeric_consistency_recheck_skipped` code=`159010` missing=`['inconsistency_field', 'inconsistency_reason', 'recheck_action', 'recheck_score', 'recheck_reason_excerpt']` zero=`[]` invalid=`[]`
- line=`181060` stage=`ai_numeric_consistency_recheck_evaluated` code=`052690` missing=`['inconsistency_field', 'inconsistency_reason', 'recheck_action', 'recheck_score', 'recheck_reason_excerpt']` zero=`[]` invalid=`[]`
- line=`181061` stage=`ai_numeric_consistency_recheck_skipped` code=`052690` missing=`['inconsistency_field', 'inconsistency_reason', 'recheck_action', 'recheck_score', 'recheck_reason_excerpt']` zero=`[]` invalid=`[]`
- line=`181410` stage=`ai_numeric_consistency_recheck_evaluated` code=`019210` missing=`['inconsistency_field', 'inconsistency_reason', 'recheck_action', 'recheck_score', 'recheck_reason_excerpt']` zero=`[]` invalid=`[]`
- line=`181411` stage=`ai_numeric_consistency_recheck_skipped` code=`019210` missing=`['inconsistency_field', 'inconsistency_reason', 'recheck_action', 'recheck_score', 'recheck_reason_excerpt']` zero=`[]` invalid=`[]`
- line=`181477` stage=`ai_numeric_consistency_recheck_evaluated` code=`314930` missing=`['inconsistency_field', 'inconsistency_reason', 'recheck_action', 'recheck_score', 'recheck_reason_excerpt']` zero=`[]` invalid=`[]`
- line=`181478` stage=`ai_numeric_consistency_recheck_skipped` code=`314930` missing=`['inconsistency_field', 'inconsistency_reason', 'recheck_action', 'recheck_score', 'recheck_reason_excerpt']` zero=`[]` invalid=`[]`
- line=`181492` stage=`ai_numeric_consistency_recheck_evaluated` code=`004310` missing=`['inconsistency_field', 'inconsistency_reason', 'recheck_action', 'recheck_score', 'recheck_reason_excerpt']` zero=`[]` invalid=`[]`
- line=`181493` stage=`ai_numeric_consistency_recheck_skipped` code=`004310` missing=`['inconsistency_field', 'inconsistency_reason', 'recheck_action', 'recheck_score', 'recheck_reason_excerpt']` zero=`[]` invalid=`[]`

## Invalid Label Findings
- none

## High Volume Stages Without Source-Like Fields
- none

## Unknown Token Findings
- none

## Reviewed Unknown Token Findings
- `lifecycle_decision_matrix_runtime_policy` count=`369` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=8(reviewed_missing_risk_regime_context)`
- `order_leg_request` count=`270` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=8(reviewed_missing_risk_regime_context)`
- `swing_sim_buy_order_assumed_filled` count=`254` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=8(reviewed_missing_risk_regime_context)`
- `swing_sim_order_bundle_assumed_filled` count=`254` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=8(reviewed_missing_risk_regime_context)`
- `order_bundle_submitted` count=`16` routing=`reviewed_unknown_token_provenance` fields=`filled_qty=16(reviewed_pre_contract_placeholder), remaining_qty=16(reviewed_pre_contract_placeholder), fill_quality=16(reviewed_pre_contract_placeholder)`
- `position_rebased_after_fill` count=`15` routing=`reviewed_unknown_token_provenance` fields=`fill_quality=2(reviewed_fill_quality_pre_contract_no_requested_qty)`
- `scalp_sim_panic_context_warning` count=`9` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=9(reviewed_missing_risk_regime_context), market_risk_state=9(reviewed_missing_risk_regime_context), liquidity_state=9(reviewed_missing_risk_regime_context), risk_regime_epoch_id=9(reviewed_missing_risk_regime_context)`

## Top Stages
- `scalping_scanner_candidate_observed`: `15851`
- `scalping_scanner_real_source_guard_block`: `15851`
- `strength_momentum_observed`: `14714`
- `blocked_strength_momentum`: `14714`
- `bad_entry_refined_candidate`: `11579`
- `scalp_sim_panic_scale_in_blocked`: `10970`
- `stat_action_decision_snapshot`: `7944`
- `reversal_add_blocked_reason`: `5045`
- `scalp_sim_panic_action_deduped`: `4531`
- `budget_pass`: `4013`
- `orderbook_stability_observed`: `3994`
- `ai_holding_fast_reuse_band`: `3568`
- `ai_holding_reuse_bypass`: `3553`
- `latency_block`: `3537`
- `scalp_sim_panic_level1_partial_skipped_min_remaining`: `3283`
- `swing_entry_policy_evaluated`: `3028`
- `swing_entry_micro_context_observed`: `2971`
- `market_regime_prior_observed`: `2969`
- `ai_holding_review`: `2800`
- `blocked_swing_score_vpw`: `2672`
