# Microstructure Reaction Context - 2026-06-29

- runtime_effect: `False`
- decision_authority: `entry_confidence_modifier_source_only`
- forbidden_uses: `['standalone_buy', 'broker_guard_bypass', 'threshold_mutation', 'provider_route_change', 'bot_restart', 'cap_release']`

## Summary
- available: `True`
- row_count: `4870`
- ok/missing_or_unusable: `912` / `3958`
- real_submitted_count: `4`
- status_counts: `{'insufficient_window': 8, 'not_evaluated': 1067, 'ok': 912, 'source_quality_missing': 16, 'stale': 2867}`
- entry_reaction_quality_counts: `{'favorable_reaction': 17, 'mixed_reaction': 175, 'neutral_unusable': 3958, 'risk_context_only': 383, 'weak_reaction': 337}`
- source_quality_counts: `{'ai_score_50_buy_hold_override_no_tick_audit': 183, 'fresh_short_window': 912, 'missing_orderbook': 16, 'pre_ai_liquidity_gate': 340, 'pre_ai_overbought_gate': 523, 'snapshot_pre_contract_backfill': 1, 'stale_tick_or_quote': 2867, 'tick_sample_lt5': 8, 'watching_ai_cooldown_active': 20}`
- stage_counts: `{'ai_confirmed': 641, 'ai_confirmed_terminal_no_budget': 692, 'ai_cooldown_blocked': 20, 'ai_holding_review': 975, 'blocked_ai_score': 505, 'blocked_liquidity': 340, 'blocked_overbought': 523, 'order_bundle_submitted': 2, 'pre_submit_liquidity_guard_block': 4, 'scalp_entry_action_decision_snapshot': 1168}`
- avg_ask_sweep_score: `48.39`
- avg_post_sweep_hold_score: `50.087`
- avg_bid_replenishment_score: `52.472`
- max_vi_proximity_risk: `100`
- warnings: `[]`
