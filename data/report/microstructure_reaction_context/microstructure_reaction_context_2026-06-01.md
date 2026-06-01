# Microstructure Reaction Context - 2026-06-01

- runtime_effect: `False`
- decision_authority: `entry_confidence_modifier_source_only`
- forbidden_uses: `['standalone_buy', 'broker_guard_bypass', 'threshold_mutation', 'provider_route_change', 'bot_restart', 'cap_release']`

## Summary
- available: `True`
- row_count: `26872`
- ok/missing_or_unusable: `9838` / `17034`
- real_submitted_count: `22`
- status_counts: `{'not_evaluated': 15369, 'ok': 9838, 'stale': 1665}`
- entry_reaction_quality_counts: `{'favorable_reaction': 282, 'mixed_reaction': 2863, 'neutral_unusable': 17034, 'risk_context_only': 2886, 'weak_reaction': 3807}`
- source_quality_counts: `{'ai_score_50_buy_hold_override_no_tick_audit': 434, 'fresh_short_window': 9838, 'pre_ai_liquidity_gate': 1323, 'pre_ai_overbought_gate': 12671, 'stale_tick_or_quote': 1665, 'watching_ai_cooldown_active': 941}`
- stage_counts: `{'ai_confirmed': 1675, 'ai_cooldown_blocked': 941, 'ai_holding_review': 4538, 'blocked_ai_score': 2379, 'blocked_liquidity': 1323, 'blocked_overbought': 12671, 'order_bundle_failed': 58, 'order_bundle_submitted': 22, 'pre_submit_liquidity_guard_block': 88, 'pre_submit_price_guard_block': 2, 'scalp_entry_action_decision_snapshot': 3175}`
- avg_ask_sweep_score: `46.142`
- avg_post_sweep_hold_score: `49.965`
- avg_bid_replenishment_score: `56.124`
- max_vi_proximity_risk: `80`
- warnings: `[]`
