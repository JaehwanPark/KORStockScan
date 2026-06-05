# Microstructure Reaction Context - 2026-06-05

- runtime_effect: `False`
- decision_authority: `entry_confidence_modifier_source_only`
- forbidden_uses: `['standalone_buy', 'broker_guard_bypass', 'threshold_mutation', 'provider_route_change', 'bot_restart', 'cap_release']`

## Summary
- available: `True`
- row_count: `14168`
- ok/missing_or_unusable: `8026` / `6142`
- real_submitted_count: `1`
- status_counts: `{'not_evaluated': 4244, 'ok': 8026, 'source_quality_missing': 1, 'stale': 1897}`
- entry_reaction_quality_counts: `{'favorable_reaction': 301, 'mixed_reaction': 2590, 'neutral_unusable': 6142, 'risk_context_only': 2298, 'weak_reaction': 2837}`
- source_quality_counts: `{'ai_score_50_buy_hold_override_no_tick_audit': 451, 'fresh_short_window': 8026, 'missing_orderbook': 1, 'pre_ai_liquidity_gate': 1506, 'pre_ai_overbought_gate': 1673, 'stale_tick_or_quote': 1897, 'watching_ai_cooldown_active': 614}`
- stage_counts: `{'ai_confirmed': 1670, 'ai_cooldown_blocked': 614, 'ai_holding_review': 2741, 'blocked_ai_score': 2470, 'blocked_liquidity': 1506, 'blocked_overbought': 1673, 'order_bundle_submitted': 1, 'pre_submit_liquidity_guard_block': 314, 'scalp_entry_action_decision_snapshot': 3179}`
- avg_ask_sweep_score: `45.973`
- avg_post_sweep_hold_score: `49.967`
- avg_bid_replenishment_score: `59.467`
- max_vi_proximity_risk: `60`
- warnings: `[]`
