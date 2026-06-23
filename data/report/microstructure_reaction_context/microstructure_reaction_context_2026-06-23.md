# Microstructure Reaction Context - 2026-06-23

- runtime_effect: `False`
- decision_authority: `entry_confidence_modifier_source_only`
- forbidden_uses: `['standalone_buy', 'broker_guard_bypass', 'threshold_mutation', 'provider_route_change', 'bot_restart', 'cap_release']`

## Summary
- available: `True`
- row_count: `5222`
- ok/missing_or_unusable: `1486` / `3736`
- real_submitted_count: `6`
- status_counts: `{'insufficient_window': 1, 'not_evaluated': 943, 'ok': 1486, 'source_quality_missing': 17, 'stale': 2775}`
- entry_reaction_quality_counts: `{'favorable_reaction': 48, 'mixed_reaction': 442, 'neutral_unusable': 3736, 'risk_context_only': 396, 'weak_reaction': 600}`
- source_quality_counts: `{'ai_score_50_buy_hold_override_no_tick_audit': 229, 'fresh_short_window': 1486, 'missing_orderbook': 17, 'pre_ai_liquidity_gate': 437, 'pre_ai_overbought_gate': 254, 'stale_tick_or_quote': 2775, 'tick_sample_lt5': 1, 'watching_ai_cooldown_active': 23}`
- stage_counts: `{'ai_confirmed': 618, 'ai_confirmed_terminal_no_budget': 683, 'ai_cooldown_blocked': 23, 'ai_holding_review': 1275, 'blocked_ai_score': 586, 'blocked_liquidity': 437, 'blocked_overbought': 254, 'order_bundle_submitted': 3, 'pre_submit_liquidity_guard_block': 6, 'real_weak_pullback_entry_block': 3, 'scalp_entry_action_decision_snapshot': 1333, 'scalp_preset_tp_ai_hold_action': 1}`
- avg_ask_sweep_score: `47.519`
- avg_post_sweep_hold_score: `50.08`
- avg_bid_replenishment_score: `54.473`
- max_vi_proximity_risk: `80`
- warnings: `[]`
