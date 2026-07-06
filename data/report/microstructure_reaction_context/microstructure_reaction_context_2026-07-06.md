# Microstructure Reaction Context - 2026-07-06

- runtime_effect: `False`
- decision_authority: `entry_confidence_modifier_source_only`
- forbidden_uses: `['standalone_buy', 'broker_guard_bypass', 'threshold_mutation', 'provider_route_change', 'bot_restart', 'cap_release']`

## Summary
- available: `True`
- row_count: `3403`
- ok/missing_or_unusable: `810` / `2593`
- real_submitted_count: `23`
- status_counts: `{'not_evaluated': 743, 'ok': 810, 'source_quality_partial': 25, 'stale': 1825}`
- entry_reaction_quality_counts: `{'favorable_reaction': 22, 'mixed_reaction': 290, 'neutral_unusable': 2593, 'risk_context_only': 192, 'weak_reaction': 306}`
- source_quality_counts: `{'ai_confirmed_terminal_no_budget_source_quality_missing': 43, 'ai_score_50_buy_hold_override_no_tick_audit': 80, 'blocked_ai_score_no_tick_audit': 29, 'fresh_short_window': 810, 'pre_ai_liquidity_gate': 177, 'pre_ai_overbought_gate': 134, 'snapshot_pre_contract_backfill': 269, 'stale_tick_or_quote': 1825, 'tick_aggressor_pressure_unusable': 25, 'watching_ai_cooldown_active': 11}`
- stage_counts: `{'ai_confirmed': 240, 'ai_confirmed_terminal_no_budget': 314, 'ai_cooldown_blocked': 11, 'ai_holding_review': 1430, 'blocked_ai_score': 294, 'blocked_liquidity': 177, 'blocked_overbought': 134, 'order_bundle_submitted': 2, 'pre_submit_liquidity_guard_block': 1, 'real_weak_pullback_entry_block': 2, 'scalp_entry_action_decision_snapshot': 798}`
- avg_ask_sweep_score: `48.373`
- avg_post_sweep_hold_score: `49.856`
- avg_bid_replenishment_score: `54.111`
- max_vi_proximity_risk: `55`
- warnings: `[]`
