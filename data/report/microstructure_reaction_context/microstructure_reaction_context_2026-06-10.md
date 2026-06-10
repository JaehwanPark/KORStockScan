# Microstructure Reaction Context - 2026-06-10

- runtime_effect: `False`
- decision_authority: `entry_confidence_modifier_source_only`
- forbidden_uses: `['standalone_buy', 'broker_guard_bypass', 'threshold_mutation', 'provider_route_change', 'bot_restart', 'cap_release']`

## Summary
- available: `True`
- row_count: `16717`
- ok/missing_or_unusable: `7612` / `9105`
- real_submitted_count: `49`
- status_counts: `{'not_evaluated': 6231, 'ok': 7612, 'stale': 2874}`
- entry_reaction_quality_counts: `{'favorable_reaction': 299, 'mixed_reaction': 2329, 'neutral_unusable': 9105, 'risk_context_only': 1862, 'weak_reaction': 3122}`
- source_quality_counts: `{'ai_score_50_buy_hold_override_no_tick_audit': 680, 'fresh_short_window': 7612, 'pre_ai_liquidity_gate': 2405, 'pre_ai_overbought_gate': 1378, 'stale_tick_or_quote': 2874, 'watching_ai_cooldown_active': 1768}`
- stage_counts: `{'ai_confirmed': 1491, 'ai_cooldown_blocked': 1768, 'ai_holding_review': 4935, 'blocked_ai_score': 1738, 'blocked_liquidity': 2405, 'blocked_overbought': 1378, 'order_bundle_failed': 23, 'order_bundle_submitted': 49, 'pre_submit_liquidity_guard_block': 182, 'pre_submit_overbought_pullback_guard_block': 2, 'scalp_entry_action_decision_snapshot': 2743, 'scalp_preset_tp_ai_exit_action': 1, 'scalp_preset_tp_ai_hold_action': 2}`
- avg_ask_sweep_score: `45.755`
- avg_post_sweep_hold_score: `49.988`
- avg_bid_replenishment_score: `58.202`
- max_vi_proximity_risk: `65`
- warnings: `[]`
