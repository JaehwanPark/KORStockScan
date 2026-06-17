# Microstructure Reaction Context - 2026-06-17

- runtime_effect: `False`
- decision_authority: `entry_confidence_modifier_source_only`
- forbidden_uses: `['standalone_buy', 'broker_guard_bypass', 'threshold_mutation', 'provider_route_change', 'bot_restart', 'cap_release']`

## Summary
- available: `True`
- row_count: `14332`
- ok/missing_or_unusable: `7778` / `6554`
- real_submitted_count: `6`
- status_counts: `{'not_evaluated': 3637, 'ok': 7778, 'stale': 2917}`
- entry_reaction_quality_counts: `{'favorable_reaction': 257, 'mixed_reaction': 2260, 'neutral_unusable': 6554, 'risk_context_only': 2903, 'weak_reaction': 2358}`
- source_quality_counts: `{'ai_score_50_buy_hold_override_no_tick_audit': 614, 'fresh_short_window': 7778, 'pre_ai_liquidity_gate': 1795, 'pre_ai_overbought_gate': 962, 'stale_tick_or_quote': 2917, 'watching_ai_cooldown_active': 266}`
- stage_counts: `{'ai_confirmed': 1948, 'ai_cooldown_blocked': 266, 'ai_holding_review': 3472, 'blocked_ai_score': 2480, 'blocked_liquidity': 1795, 'blocked_overbought': 962, 'order_bundle_submitted': 6, 'pre_submit_liquidity_guard_block': 55, 'real_weak_pullback_entry_block': 16, 'scalp_entry_action_decision_snapshot': 3332}`
- avg_ask_sweep_score: `46.495`
- avg_post_sweep_hold_score: `50.186`
- avg_bid_replenishment_score: `57.812`
- max_vi_proximity_risk: `55`
- warnings: `[]`
