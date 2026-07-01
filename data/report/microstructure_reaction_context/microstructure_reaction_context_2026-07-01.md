# Microstructure Reaction Context - 2026-07-01

- runtime_effect: `False`
- decision_authority: `entry_confidence_modifier_source_only`
- forbidden_uses: `['standalone_buy', 'broker_guard_bypass', 'threshold_mutation', 'provider_route_change', 'bot_restart', 'cap_release']`

## Summary
- available: `True`
- row_count: `4785`
- ok/missing_or_unusable: `1104` / `3681`
- real_submitted_count: `90`
- status_counts: `{'insufficient_window': 1, 'not_evaluated': 1608, 'ok': 1104, 'source_quality_missing': 8, 'stale': 2064}`
- entry_reaction_quality_counts: `{'favorable_reaction': 17, 'mixed_reaction': 264, 'neutral_unusable': 3681, 'risk_context_only': 348, 'weak_reaction': 475}`
- source_quality_counts: `{'ai_confirmed_terminal_no_budget_source_quality_missing': 72, 'ai_score_50_buy_hold_override_no_tick_audit': 44, 'blocked_ai_score_no_tick_audit': 72, 'fresh_short_window': 1104, 'missing_orderbook': 8, 'pre_ai_liquidity_gate': 60, 'pre_ai_overbought_gate': 242, 'snapshot_pre_contract_backfill': 1054, 'stale_tick_or_quote': 2064, 'tick_sample_lt5': 1, 'watching_ai_cooldown_active': 64}`
- stage_counts: `{'ai_confirmed': 160, 'ai_confirmed_terminal_no_budget': 277, 'ai_cooldown_blocked': 64, 'ai_holding_review': 2130, 'blocked_ai_score': 252, 'blocked_liquidity': 60, 'blocked_overbought': 242, 'order_bundle_failed': 2, 'order_bundle_submitted': 4, 'pre_submit_weak_context_late_entry_guard_block': 2, 'real_weak_pullback_entry_block': 16, 'scalp_entry_action_decision_snapshot': 1576}`
- avg_ask_sweep_score: `47.146`
- avg_post_sweep_hold_score: `49.872`
- avg_bid_replenishment_score: `53.767`
- max_vi_proximity_risk: `59`
- warnings: `[]`
