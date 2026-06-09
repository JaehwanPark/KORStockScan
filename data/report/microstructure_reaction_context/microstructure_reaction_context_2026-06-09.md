# Microstructure Reaction Context - 2026-06-09

- runtime_effect: `False`
- decision_authority: `entry_confidence_modifier_source_only`
- forbidden_uses: `['standalone_buy', 'broker_guard_bypass', 'threshold_mutation', 'provider_route_change', 'bot_restart', 'cap_release']`

## Summary
- available: `True`
- row_count: `18600`
- ok/missing_or_unusable: `8587` / `10013`
- real_submitted_count: `6`
- status_counts: `{'not_evaluated': 6504, 'ok': 8587, 'source_quality_missing': 1, 'stale': 3508}`
- entry_reaction_quality_counts: `{'favorable_reaction': 242, 'mixed_reaction': 2415, 'neutral_unusable': 10013, 'risk_context_only': 3055, 'weak_reaction': 2875}`
- source_quality_counts: `{'ai_score_50_buy_hold_override_no_tick_audit': 617, 'fresh_short_window': 8587, 'missing_orderbook': 1, 'pre_ai_liquidity_gate': 1776, 'pre_ai_overbought_gate': 3500, 'stale_tick_or_quote': 3508, 'watching_ai_cooldown_active': 611}`
- stage_counts: `{'ai_confirmed': 2104, 'ai_cooldown_blocked': 611, 'ai_holding_review': 3986, 'blocked_ai_score': 2704, 'blocked_liquidity': 1776, 'blocked_overbought': 3500, 'order_bundle_failed': 3, 'order_bundle_submitted': 6, 'pre_submit_liquidity_guard_block': 41, 'scalp_entry_action_decision_snapshot': 3869}`
- avg_ask_sweep_score: `46.14`
- avg_post_sweep_hold_score: `50.069`
- avg_bid_replenishment_score: `56.887`
- max_vi_proximity_risk: `79`
- warnings: `[]`
