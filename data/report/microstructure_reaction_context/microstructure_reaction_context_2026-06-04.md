# Microstructure Reaction Context - 2026-06-04

- runtime_effect: `False`
- decision_authority: `entry_confidence_modifier_source_only`
- forbidden_uses: `['standalone_buy', 'broker_guard_bypass', 'threshold_mutation', 'provider_route_change', 'bot_restart', 'cap_release']`

## Summary
- available: `True`
- row_count: `1978`
- ok/missing_or_unusable: `709` / `1269`
- real_submitted_count: `1`
- status_counts: `{'not_evaluated': 1052, 'ok': 709, 'stale': 217}`
- entry_reaction_quality_counts: `{'favorable_reaction': 17, 'mixed_reaction': 228, 'neutral_unusable': 1269, 'risk_context_only': 220, 'weak_reaction': 244}`
- source_quality_counts: `{'ai_score_50_buy_hold_override_no_tick_audit': 86, 'fresh_short_window': 709, 'pre_ai_liquidity_gate': 93, 'pre_ai_overbought_gate': 824, 'stale_tick_or_quote': 217, 'watching_ai_cooldown_active': 49}`
- stage_counts: `{'ai_confirmed': 121, 'ai_cooldown_blocked': 49, 'ai_holding_review': 451, 'blocked_ai_score': 220, 'blocked_liquidity': 93, 'blocked_overbought': 824, 'order_bundle_submitted': 1, 'pre_submit_liquidity_guard_block': 6, 'scalp_entry_action_decision_snapshot': 213}`
- avg_ask_sweep_score: `47.583`
- avg_post_sweep_hold_score: `50.231`
- avg_bid_replenishment_score: `56.017`
- max_vi_proximity_risk: `60`
- warnings: `[]`
