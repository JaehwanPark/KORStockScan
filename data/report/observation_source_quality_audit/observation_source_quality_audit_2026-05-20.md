# Observation Source Quality Audit - 2026-05-20

- status: `warning`
- event_count: `593358`
- decision_authority: `source_quality_only`
- runtime_effect: `False`
- forbidden_uses: `runtime_threshold_apply, order_submit, provider_route_change, bot_restart, real_execution_quality_approval`

## Warning Stages
- `latency_block` sample=`624` missing=`{'latency_state': 1.0, 'policy_decision': 1.0, 'effective_decision': 1.0, 'ws_age_ms': 0.0048, 'ws_jitter_ms': 0.0048, 'latency_canary_reason': 0.3574, 'threshold_family': 1.0, 'runtime_effect': 1.0, 'actual_order_submitted': 1.0, 'broker_order_forbidden': 1.0}` zero=`{}`
- `scalp_sim_entry_armed` sample=`238` missing=`{'runtime_effect': 1.0}` zero=`{}`
- `scalp_sim_sell_order_assumed_filled` sample=`238` missing=`{'decision_authority': 0.3151}` zero=`{}`
- `scalp_sim_ai_holding_live_call` sample=`1754` missing=`{'sim_record_id': 1.0, 'entry_adm_candidate_id': 1.0}` zero=`{}`
- `scalp_sim_ai_holding_deferred` sample=`715` missing=`{'sim_record_id': 1.0, 'entry_adm_candidate_id': 1.0}` zero=`{}`
- `sim_ai_budget_exhausted` sample=`715` missing=`{'sim_record_id': 1.0, 'entry_adm_candidate_id': 1.0}` zero=`{}`
- `sim_ai_critical_bypass` sample=`692` missing=`{'sim_record_id': 1.0, 'entry_adm_candidate_id': 1.0}` zero=`{}`
- `scalp_sim_panic_entry_blocked` sample=`302` missing=`{'decision_authority': 0.0066}` zero=`{}`

## High Volume Stages Without Source-Like Fields
- none

## Top Stages
- `blocked_swing_score_vpw`: `368504`
- `scalp_sim_panic_action_deduped`: `47298`
- `strength_momentum_observed`: `40970`
- `blocked_strength_momentum`: `40970`
- `blocked_overbought`: `18403`
- `swing_probe_discarded`: `9216`
- `stat_action_decision_snapshot`: `8549`
- `bad_entry_refined_candidate`: `6336`
- `scalp_sim_panic_scale_in_blocked`: `4783`
- `scalp_entry_action_decision_snapshot`: `4508`
- `holding_flow_override_defer_exit`: `4323`
- `blocked_ai_score`: `2815`
- `reversal_add_blocked_reason`: `2478`
- `ai_holding_fast_reuse_band`: `2470`
- `ai_holding_reuse_bypass`: `2469`
- `blocked_vpw`: `2334`
- `ai_confirmed`: `1857`
- `scalp_sim_ai_holding_live_call`: `1754`
- `ai_holding_review`: `1754`
- `scale_in_qty_block`: `1509`
