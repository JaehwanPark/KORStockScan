# Microstructure Reaction Context - 2026-06-11

- runtime_effect: `False`
- decision_authority: `entry_confidence_modifier_source_only`
- forbidden_uses: `['standalone_buy', 'broker_guard_bypass', 'threshold_mutation', 'provider_route_change', 'bot_restart', 'cap_release']`

## Summary
- available: `True`
- row_count: `14159`
- ok/missing_or_unusable: `7499` / `6660`
- real_submitted_count: `41`
- status_counts: `{'not_evaluated': 4367, 'ok': 7499, 'stale': 2293}`
- entry_reaction_quality_counts: `{'favorable_reaction': 238, 'mixed_reaction': 2001, 'neutral_unusable': 6660, 'risk_context_only': 2553, 'weak_reaction': 2707}`
- source_quality_counts: `{'ai_score_50_buy_hold_override_no_tick_audit': 538, 'fresh_short_window': 7499, 'pre_ai_liquidity_gate': 1584, 'pre_ai_overbought_gate': 1527, 'stale_tick_or_quote': 2293, 'watching_ai_cooldown_active': 718}`
- stage_counts: `{'ai_confirmed': 1862, 'ai_cooldown_blocked': 718, 'ai_holding_review': 3301, 'blocked_ai_score': 1608, 'blocked_liquidity': 1584, 'blocked_overbought': 1527, 'order_bundle_submitted': 41, 'pre_submit_liquidity_guard_block': 30, 'scalp_entry_action_decision_snapshot': 3488}`
- avg_ask_sweep_score: `45.456`
- avg_post_sweep_hold_score: `49.971`
- avg_bid_replenishment_score: `58.007`
- max_vi_proximity_risk: `80`
- warnings: `[]`
