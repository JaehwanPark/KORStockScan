# Microstructure Reaction Context - 2026-06-08

- runtime_effect: `False`
- decision_authority: `entry_confidence_modifier_source_only`
- forbidden_uses: `['standalone_buy', 'broker_guard_bypass', 'threshold_mutation', 'provider_route_change', 'bot_restart', 'cap_release']`

## Summary
- available: `True`
- row_count: `18037`
- ok/missing_or_unusable: `5723` / `12314`
- real_submitted_count: `32`
- status_counts: `{'not_evaluated': 8238, 'ok': 5723, 'stale': 4076}`
- entry_reaction_quality_counts: `{'favorable_reaction': 228, 'mixed_reaction': 1662, 'neutral_unusable': 12314, 'risk_context_only': 1243, 'weak_reaction': 2590}`
- source_quality_counts: `{'ai_score_50_buy_hold_override_no_tick_audit': 319, 'fresh_short_window': 5723, 'pre_ai_liquidity_gate': 1914, 'pre_ai_overbought_gate': 4403, 'stale_tick_or_quote': 4076, 'watching_ai_cooldown_active': 1602}`
- stage_counts: `{'ai_confirmed': 1263, 'ai_cooldown_blocked': 1602, 'ai_holding_review': 5215, 'blocked_ai_score': 1091, 'blocked_liquidity': 1914, 'blocked_overbought': 4403, 'order_bundle_failed': 13, 'order_bundle_submitted': 32, 'pre_submit_liquidity_guard_block': 82, 'pre_submit_overbought_pullback_guard_block': 1, 'scalp_entry_action_decision_snapshot': 2421}`
- avg_ask_sweep_score: `46.458`
- avg_post_sweep_hold_score: `50.168`
- avg_bid_replenishment_score: `55.953`
- max_vi_proximity_risk: `60`
- warnings: `[]`
