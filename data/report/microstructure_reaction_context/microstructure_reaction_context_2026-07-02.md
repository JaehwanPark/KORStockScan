# Microstructure Reaction Context - 2026-07-02

- runtime_effect: `False`
- decision_authority: `entry_confidence_modifier_source_only`
- forbidden_uses: `['standalone_buy', 'broker_guard_bypass', 'threshold_mutation', 'provider_route_change', 'bot_restart', 'cap_release']`

## Summary
- available: `True`
- row_count: `3617`
- ok/missing_or_unusable: `795` / `2822`
- real_submitted_count: `15`
- status_counts: `{'not_evaluated': 800, 'ok': 795, 'source_quality_missing': 2, 'stale': 2020}`
- entry_reaction_quality_counts: `{'favorable_reaction': 26, 'mixed_reaction': 226, 'neutral_unusable': 2822, 'risk_context_only': 260, 'weak_reaction': 283}`
- source_quality_counts: `{'ai_confirmed_terminal_no_budget_source_quality_missing': 34, 'ai_score_50_buy_hold_override_no_tick_audit': 96, 'blocked_ai_score_no_tick_audit': 34, 'fresh_short_window': 795, 'missing_orderbook': 2, 'pre_ai_liquidity_gate': 213, 'pre_ai_overbought_gate': 239, 'snapshot_pre_contract_backfill': 143, 'stale_tick_or_quote': 2020, 'watching_ai_cooldown_active': 41}`
- stage_counts: `{'ai_confirmed': 275, 'ai_confirmed_terminal_no_budget': 369, 'ai_cooldown_blocked': 41, 'ai_holding_review': 1318, 'blocked_ai_score': 343, 'blocked_liquidity': 213, 'blocked_overbought': 239, 'order_bundle_submitted': 3, 'pre_submit_liquidity_guard_block': 1, 'real_weak_pullback_entry_block': 7, 'scalp_entry_action_decision_snapshot': 808}`
- avg_ask_sweep_score: `48.112`
- avg_post_sweep_hold_score: `49.98`
- avg_bid_replenishment_score: `53.558`
- max_vi_proximity_risk: `51`
- warnings: `[]`
