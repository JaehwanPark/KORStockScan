# Microstructure Reaction Context - 2026-06-15

- runtime_effect: `False`
- decision_authority: `entry_confidence_modifier_source_only`
- forbidden_uses: `['standalone_buy', 'broker_guard_bypass', 'threshold_mutation', 'provider_route_change', 'bot_restart', 'cap_release']`

## Summary
- available: `True`
- row_count: `13594`
- ok/missing_or_unusable: `7125` / `6469`
- real_submitted_count: `11`
- status_counts: `{'not_evaluated': 3913, 'ok': 7125, 'stale': 2556}`
- entry_reaction_quality_counts: `{'favorable_reaction': 174, 'mixed_reaction': 1915, 'neutral_unusable': 6469, 'risk_context_only': 2979, 'weak_reaction': 2057}`
- source_quality_counts: `{'ai_score_50_buy_hold_override_no_tick_audit': 853, 'fresh_short_window': 7125, 'pre_ai_liquidity_gate': 1112, 'pre_ai_overbought_gate': 1368, 'stale_tick_or_quote': 2556, 'watching_ai_cooldown_active': 580}`
- stage_counts: `{'ai_confirmed': 1798, 'ai_cooldown_blocked': 580, 'ai_holding_review': 2959, 'blocked_ai_score': 2583, 'blocked_liquidity': 1112, 'blocked_overbought': 1368, 'order_bundle_failed': 6, 'order_bundle_submitted': 11, 'pre_submit_liquidity_guard_block': 54, 'pre_submit_price_guard_block': 3, 'real_weak_pullback_entry_block': 19, 'scalp_entry_action_decision_snapshot': 3101}`
- avg_ask_sweep_score: `46.304`
- avg_post_sweep_hold_score: `50.058`
- avg_bid_replenishment_score: `56.692`
- max_vi_proximity_risk: `58`
- warnings: `[]`
