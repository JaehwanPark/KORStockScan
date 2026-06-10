# Observation Source Quality Audit - 2026-06-10

- status: `warning`
- event_count: `14220`
- tuning_input_policy: `exclude_defective_rows_not_full_day_raw`
- hard_blocking_excluded_row_count: `0`
- tuning_input_allowed: `True`
- decision_authority: `source_quality_only`
- runtime_effect: `False`
- forbidden_uses: `runtime_threshold_apply, order_submit, provider_route_change, bot_restart, real_execution_quality_approval`

## Warning Stages
- none

## Hard Blocking Row Exclusions
- none

## Invalid Label Findings
- none

## High Volume Stages Without Source-Like Fields
- none

## Unknown Token Findings
- `scalp_entry_action_decision_snapshot` count=`642` routing=`source_quality_blocker_or_provenance_backfill` fields=`sim_pre_submit_liquidity_guard_action=3(0.0047)`
- `scalp_sim_buy_order_assumed_filled` count=`107` routing=`source_quality_blocker_or_provenance_backfill` fields=`sim_pre_submit_liquidity_guard_action=3(0.028)`
- `scalp_sim_buy_order_virtual_pending` count=`107` routing=`source_quality_blocker_or_provenance_backfill` fields=`sim_pre_submit_liquidity_guard_action=3(0.028)`
- `scalp_sim_entry_armed` count=`107` routing=`source_quality_blocker_or_provenance_backfill` fields=`sim_pre_submit_liquidity_guard_action=3(0.028)`
- `scalp_sim_holding_started` count=`107` routing=`source_quality_blocker_or_provenance_backfill` fields=`sim_pre_submit_liquidity_guard_action=3(0.028)`
- `scalp_sim_pre_submit_overbought_guard_would_pass` count=`107` routing=`source_quality_blocker_or_provenance_backfill` fields=`sim_pre_submit_liquidity_guard_action=3(0.028)`
- `position_rebased_after_fill` count=`24` routing=`source_quality_blocker_or_provenance_backfill` fields=`fill_quality=6(0.25)`
- `preset_exit_sync_ok` count=`18` routing=`source_quality_blocker_or_provenance_backfill` fields=`fill_quality=3(0.1667)`
- `scalp_sim_pre_submit_liquidity_guard_unknown` count=`3` routing=`source_quality_blocker_or_provenance_backfill` fields=`sim_pre_submit_liquidity_guard_action=3(1.0), __stage=3(1.0)`

## Reviewed Unknown Token Findings
- `latency_block` count=`698` routing=`reviewed_unknown_token_provenance` fields=`ws_age_ms=3(reviewed_pre_contract_placeholder), ws_jitter_ms=3(reviewed_pre_contract_placeholder)`
- `order_leg_request` count=`34` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=1(reviewed_missing_risk_regime_context)`
- `scalp_sim_panic_context_warning` count=`32` routing=`reviewed_unknown_token_provenance` fields=`panic_epoch_id=32(reviewed_missing_risk_regime_context), market_risk_state=32(reviewed_missing_risk_regime_context), liquidity_state=32(reviewed_missing_risk_regime_context), risk_regime_epoch_id=32(reviewed_missing_risk_regime_context)`
- `swing_sim_buy_order_assumed_filled` count=`20` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=1(reviewed_missing_risk_regime_context)`
- `swing_sim_order_bundle_assumed_filled` count=`20` routing=`reviewed_unknown_token_provenance` fields=`risk_regime_context=1(reviewed_missing_risk_regime_context)`

## Top Stages
- `budget_pass`: `745`
- `orderbook_stability_observed`: `735`
- `latency_block`: `698`
- `strength_momentum_observed`: `658`
- `blocked_strength_momentum`: `658`
- `scalp_entry_action_decision_snapshot`: `642`
- `swing_entry_policy_evaluated`: `619`
- `bad_entry_refined_candidate`: `614`
- `swing_entry_micro_context_observed`: `588`
- `stat_action_decision_snapshot`: `489`
- `market_regime_prior_observed`: `437`
- `blocked_swing_score_vpw`: `382`
- `swing_probe_discarded`: `265`
- `ai_holding_fast_reuse_band`: `263`
- `ai_holding_reuse_bypass`: `263`
- `gatekeeper_fast_reuse_bypass`: `238`
- `blocked_gatekeeper_reject`: `237`
- `reversal_add_blocked_reason`: `226`
- `scalp_sim_ai_holding_live_call`: `213`
- `ai_holding_review`: `213`
