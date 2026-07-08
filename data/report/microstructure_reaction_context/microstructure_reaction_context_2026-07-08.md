# Microstructure Reaction Context - 2026-07-08

- runtime_effect: `False`
- decision_authority: `entry_confidence_modifier_source_only`
- forbidden_uses: `['standalone_buy', 'broker_guard_bypass', 'threshold_mutation', 'provider_route_change', 'bot_restart', 'cap_release']`

## Summary
- available: `True`
- row_count: `3787`
- ok/missing_or_unusable: `839` / `2948`
- real_submitted_count: `22`
- status_counts: `{'insufficient_window': 1, 'not_evaluated': 563, 'ok': 839, 'source_quality_partial': 22, 'stale': 2362}`
- entry_reaction_quality_counts: `{'favorable_reaction': 31, 'mixed_reaction': 346, 'neutral_unusable': 2948, 'risk_context_only': 190, 'weak_reaction': 272}`
- source_quality_counts: `{'ai_confirmed_terminal_no_budget_source_quality_missing': 5, 'ai_score_50_buy_hold_override_no_tick_audit': 75, 'blocked_ai_score_no_tick_audit': 5, 'fresh_short_window': 839, 'pre_ai_liquidity_gate': 206, 'pre_ai_overbought_gate': 44, 'snapshot_pre_contract_backfill': 217, 'stale_tick_or_quote': 2362, 'tick_aggressor_pressure_unusable': 22, 'tick_sample_lt5': 1, 'watching_ai_cooldown_active': 11}`
- stage_counts: `{'ai_confirmed': 383, 'ai_confirmed_terminal_no_budget': 398, 'ai_cooldown_blocked': 11, 'ai_holding_review': 1410, 'blocked_ai_score': 307, 'blocked_liquidity': 206, 'blocked_overbought': 44, 'order_bundle_failed': 2, 'order_bundle_submitted': 9, 'pre_submit_entry_ai_authority_guard_block': 1, 'pre_submit_price_guard_block': 2, 'pre_submit_weak_context_late_entry_guard_block': 4, 'real_weak_ai_micro_entry_block': 27, 'real_weak_pullback_entry_block': 1, 'scalp_entry_action_decision_snapshot': 982}`
- avg_ask_sweep_score: `49.338`
- avg_post_sweep_hold_score: `49.933`
- avg_bid_replenishment_score: `54.237`
- max_vi_proximity_risk: `21`
- warnings: `[]`
