# Microstructure Reaction Context - 2026-06-22

- runtime_effect: `False`
- decision_authority: `entry_confidence_modifier_source_only`
- forbidden_uses: `['standalone_buy', 'broker_guard_bypass', 'threshold_mutation', 'provider_route_change', 'bot_restart', 'cap_release']`

## Summary
- available: `True`
- row_count: `3288`
- ok/missing_or_unusable: `1039` / `2249`
- real_submitted_count: `2`
- status_counts: `{'not_evaluated': 467, 'ok': 1039, 'stale': 1782}`
- entry_reaction_quality_counts: `{'favorable_reaction': 30, 'mixed_reaction': 287, 'neutral_unusable': 2249, 'risk_context_only': 363, 'weak_reaction': 359}`
- source_quality_counts: `{'ai_score_50_buy_hold_override_no_tick_audit': 175, 'fresh_short_window': 1039, 'pre_ai_liquidity_gate': 229, 'pre_ai_overbought_gate': 63, 'stale_tick_or_quote': 1782}`
- stage_counts: `{'ai_confirmed': 579, 'ai_holding_review': 1097, 'blocked_ai_score': 322, 'blocked_liquidity': 229, 'blocked_overbought': 63, 'order_bundle_submitted': 1, 'pre_submit_liquidity_guard_block': 10, 'real_weak_pullback_entry_block': 3, 'scalp_entry_action_decision_snapshot': 984}`
- avg_ask_sweep_score: `47.335`
- avg_post_sweep_hold_score: `49.965`
- avg_bid_replenishment_score: `54.718`
- max_vi_proximity_risk: `48`
- warnings: `[]`
