# Microstructure Reaction Context - 2026-06-26

- runtime_effect: `False`
- decision_authority: `entry_confidence_modifier_source_only`
- forbidden_uses: `['standalone_buy', 'broker_guard_bypass', 'threshold_mutation', 'provider_route_change', 'bot_restart', 'cap_release']`

## Summary
- available: `True`
- row_count: `5899`
- ok/missing_or_unusable: `1028` / `4871`
- real_submitted_count: `20`
- status_counts: `{'not_evaluated': 1028, 'ok': 1028, 'source_quality_missing': 2, 'stale': 3841}`
- entry_reaction_quality_counts: `{'favorable_reaction': 44, 'mixed_reaction': 260, 'neutral_unusable': 4871, 'risk_context_only': 328, 'weak_reaction': 396}`
- source_quality_counts: `{'ai_score_50_buy_hold_override_no_tick_audit': 237, 'fresh_short_window': 1028, 'missing_orderbook': 2, 'pre_ai_liquidity_gate': 511, 'pre_ai_overbought_gate': 269, 'stale_tick_or_quote': 3841, 'watching_ai_cooldown_active': 11}`
- stage_counts: `{'ai_confirmed': 781, 'ai_confirmed_terminal_no_budget': 855, 'ai_cooldown_blocked': 11, 'ai_holding_review': 1082, 'blocked_ai_score': 816, 'blocked_liquidity': 511, 'blocked_overbought': 269, 'order_bundle_failed': 2, 'order_bundle_submitted': 10, 'pre_submit_liquidity_guard_block': 1, 'real_weak_pullback_entry_block': 3, 'scalp_entry_action_decision_snapshot': 1558}`
- avg_ask_sweep_score: `48.052`
- avg_post_sweep_hold_score: `49.997`
- avg_bid_replenishment_score: `52.531`
- max_vi_proximity_risk: `80`
- warnings: `[]`
