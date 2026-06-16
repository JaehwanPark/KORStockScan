# Microstructure Reaction Context - 2026-06-16

- runtime_effect: `False`
- decision_authority: `entry_confidence_modifier_source_only`
- forbidden_uses: `['standalone_buy', 'broker_guard_bypass', 'threshold_mutation', 'provider_route_change', 'bot_restart', 'cap_release']`

## Summary
- available: `True`
- row_count: `13503`
- ok/missing_or_unusable: `7608` / `5895`
- real_submitted_count: `3`
- status_counts: `{'not_evaluated': 2986, 'ok': 7608, 'stale': 2909}`
- entry_reaction_quality_counts: `{'favorable_reaction': 216, 'mixed_reaction': 2382, 'neutral_unusable': 5895, 'risk_context_only': 2509, 'weak_reaction': 2501}`
- source_quality_counts: `{'ai_score_50_buy_hold_override_no_tick_audit': 847, 'fresh_short_window': 7608, 'pre_ai_liquidity_gate': 1397, 'pre_ai_overbought_gate': 586, 'stale_tick_or_quote': 2909, 'watching_ai_cooldown_active': 156}`
- stage_counts: `{'ai_confirmed': 1817, 'ai_cooldown_blocked': 156, 'ai_holding_review': 3539, 'blocked_ai_score': 2682, 'blocked_liquidity': 1397, 'blocked_overbought': 586, 'order_bundle_failed': 1, 'order_bundle_submitted': 3, 'pre_submit_liquidity_guard_block': 33, 'real_weak_pullback_entry_block': 107, 'scalp_entry_action_decision_snapshot': 3182}`
- avg_ask_sweep_score: `46.13`
- avg_post_sweep_hold_score: `49.987`
- avg_bid_replenishment_score: `58.418`
- max_vi_proximity_risk: `80`
- warnings: `[]`
