# Microstructure Reaction Context - 2026-06-12

- runtime_effect: `False`
- decision_authority: `entry_confidence_modifier_source_only`
- forbidden_uses: `['standalone_buy', 'broker_guard_bypass', 'threshold_mutation', 'provider_route_change', 'bot_restart', 'cap_release']`

## Summary
- available: `True`
- row_count: `14136`
- ok/missing_or_unusable: `6233` / `7903`
- real_submitted_count: `37`
- status_counts: `{'not_evaluated': 4798, 'ok': 6233, 'stale': 3105}`
- entry_reaction_quality_counts: `{'favorable_reaction': 132, 'mixed_reaction': 1666, 'neutral_unusable': 7903, 'risk_context_only': 2425, 'weak_reaction': 2010}`
- source_quality_counts: `{'ai_score_50_buy_hold_override_no_tick_audit': 500, 'fresh_short_window': 6233, 'pre_ai_liquidity_gate': 1533, 'pre_ai_overbought_gate': 2022, 'stale_tick_or_quote': 3105, 'watching_ai_cooldown_active': 743}`
- stage_counts: `{'ai_confirmed': 1984, 'ai_cooldown_blocked': 743, 'ai_holding_review': 2692, 'blocked_ai_score': 1463, 'blocked_liquidity': 1533, 'blocked_overbought': 2022, 'order_bundle_failed': 15, 'order_bundle_submitted': 37, 'pre_submit_liquidity_guard_block': 49, 'pre_submit_overbought_pullback_guard_block': 10, 'scalp_entry_action_decision_snapshot': 3586, 'scalp_preset_tp_ai_hold_action': 2}`
- avg_ask_sweep_score: `46.686`
- avg_post_sweep_hold_score: `49.987`
- avg_bid_replenishment_score: `56.167`
- max_vi_proximity_risk: `60`
- warnings: `[]`
