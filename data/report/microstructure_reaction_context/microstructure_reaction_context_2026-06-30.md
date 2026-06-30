# Microstructure Reaction Context - 2026-06-30

- runtime_effect: `False`
- decision_authority: `entry_confidence_modifier_source_only`
- forbidden_uses: `['standalone_buy', 'broker_guard_bypass', 'threshold_mutation', 'provider_route_change', 'bot_restart', 'cap_release']`

## Summary
- available: `True`
- row_count: `6483`
- ok/missing_or_unusable: `2265` / `4218`
- real_submitted_count: `39`
- status_counts: `{'insufficient_window': 23, 'not_evaluated': 877, 'ok': 2265, 'source_quality_missing': 12, 'stale': 3306}`
- entry_reaction_quality_counts: `{'favorable_reaction': 45, 'mixed_reaction': 613, 'neutral_unusable': 4218, 'risk_context_only': 576, 'weak_reaction': 1031}`
- source_quality_counts: `{'ai_confirmed_terminal_no_budget_source_quality_missing': 93, 'ai_score_50_buy_hold_override_no_tick_audit': 31, 'blocked_ai_score_no_tick_audit': 93, 'fresh_short_window': 2265, 'missing_orderbook': 12, 'pre_ai_liquidity_gate': 77, 'pre_ai_overbought_gate': 128, 'snapshot_pre_contract_backfill': 361, 'stale_tick_or_quote': 3306, 'tick_sample_lt5': 23, 'watching_ai_cooldown_active': 94}`
- stage_counts: `{'ai_confirmed': 200, 'ai_confirmed_terminal_no_budget': 445, 'ai_cooldown_blocked': 94, 'ai_holding_review': 4045, 'blocked_ai_score': 406, 'blocked_liquidity': 77, 'blocked_overbought': 128, 'order_bundle_submitted': 7, 'pre_submit_liquidity_guard_block': 2, 'real_weak_pullback_entry_block': 28, 'scalp_entry_action_decision_snapshot': 1049, 'scalp_preset_tp_ai_hold_action': 2}`
- avg_ask_sweep_score: `45.284`
- avg_post_sweep_hold_score: `49.861`
- avg_bid_replenishment_score: `55.848`
- max_vi_proximity_risk: `53`
- warnings: `[]`
