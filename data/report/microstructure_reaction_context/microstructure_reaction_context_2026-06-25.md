# Microstructure Reaction Context - 2026-06-25

- runtime_effect: `False`
- decision_authority: `entry_confidence_modifier_source_only`
- forbidden_uses: `['standalone_buy', 'broker_guard_bypass', 'threshold_mutation', 'provider_route_change', 'bot_restart', 'cap_release']`

## Summary
- available: `True`
- row_count: `5485`
- ok/missing_or_unusable: `1450` / `4035`
- real_submitted_count: `12`
- status_counts: `{'insufficient_window': 13, 'not_evaluated': 928, 'ok': 1450, 'source_quality_missing': 6, 'stale': 3088}`
- entry_reaction_quality_counts: `{'favorable_reaction': 16, 'mixed_reaction': 359, 'neutral_unusable': 4035, 'risk_context_only': 508, 'weak_reaction': 567}`
- source_quality_counts: `{'ai_score_50_buy_hold_override_no_tick_audit': 227, 'fresh_short_window': 1450, 'missing_orderbook': 6, 'pre_ai_liquidity_gate': 394, 'pre_ai_overbought_gate': 285, 'stale_tick_or_quote': 3088, 'tick_sample_lt5': 13, 'watching_ai_cooldown_active': 22}`
- stage_counts: `{'ai_confirmed': 793, 'ai_confirmed_terminal_no_budget': 864, 'ai_cooldown_blocked': 22, 'ai_holding_review': 879, 'blocked_ai_score': 734, 'blocked_liquidity': 394, 'blocked_overbought': 285, 'order_bundle_failed': 6, 'order_bundle_submitted': 6, 'pre_submit_liquidity_guard_block': 4, 'real_weak_pullback_entry_block': 6, 'scalp_entry_action_decision_snapshot': 1492}`
- avg_ask_sweep_score: `47.497`
- avg_post_sweep_hold_score: `50.026`
- avg_bid_replenishment_score: `54.003`
- max_vi_proximity_risk: `79`
- warnings: `[]`
