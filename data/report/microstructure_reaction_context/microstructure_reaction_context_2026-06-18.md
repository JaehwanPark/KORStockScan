# Microstructure Reaction Context - 2026-06-18

- runtime_effect: `False`
- decision_authority: `entry_confidence_modifier_source_only`
- forbidden_uses: `['standalone_buy', 'broker_guard_bypass', 'threshold_mutation', 'provider_route_change', 'bot_restart', 'cap_release']`

## Summary
- available: `True`
- row_count: `13820`
- ok/missing_or_unusable: `6799` / `7021`
- real_submitted_count: `26`
- status_counts: `{'not_evaluated': 4160, 'ok': 6799, 'source_quality_missing': 1, 'stale': 2860}`
- entry_reaction_quality_counts: `{'favorable_reaction': 297, 'mixed_reaction': 2056, 'neutral_unusable': 7021, 'risk_context_only': 2079, 'weak_reaction': 2367}`
- source_quality_counts: `{'ai_score_50_buy_hold_override_no_tick_audit': 371, 'fresh_short_window': 6799, 'missing_orderbook': 1, 'pre_ai_liquidity_gate': 1884, 'pre_ai_overbought_gate': 1556, 'stale_tick_or_quote': 2860, 'watching_ai_cooldown_active': 349}`
- stage_counts: `{'ai_confirmed': 1780, 'ai_cooldown_blocked': 349, 'ai_holding_review': 3897, 'blocked_ai_score': 1979, 'blocked_liquidity': 1884, 'blocked_overbought': 1556, 'order_bundle_failed': 17, 'order_bundle_submitted': 21, 'pre_submit_late_entry_price_drift_guard_block': 16, 'pre_submit_liquidity_guard_block': 104, 'real_weak_pullback_entry_block': 95, 'scalp_entry_action_decision_snapshot': 2122}`
- avg_ask_sweep_score: `46.092`
- avg_post_sweep_hold_score: `50.191`
- avg_bid_replenishment_score: `58.083`
- max_vi_proximity_risk: `60`
- warnings: `[]`
