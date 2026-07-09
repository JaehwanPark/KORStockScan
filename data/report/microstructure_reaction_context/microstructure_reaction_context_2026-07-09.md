# Microstructure Reaction Context - 2026-07-09

- runtime_effect: `False`
- decision_authority: `entry_confidence_modifier_source_only`
- forbidden_uses: `['standalone_buy', 'broker_guard_bypass', 'threshold_mutation', 'provider_route_change', 'bot_restart', 'cap_release']`

## Summary
- available: `True`
- row_count: `1330`
- ok/missing_or_unusable: `284` / `1046`
- real_submitted_count: `21`
- status_counts: `{'not_evaluated': 267, 'ok': 284, 'source_quality_partial': 8, 'stale': 771}`
- entry_reaction_quality_counts: `{'favorable_reaction': 16, 'mixed_reaction': 81, 'neutral_unusable': 1046, 'risk_context_only': 79, 'weak_reaction': 108}`
- source_quality_counts: `{'ai_score_50_buy_hold_override_no_tick_audit': 15, 'fresh_short_window': 284, 'pre_ai_liquidity_gate': 26, 'pre_ai_overbought_gate': 9, 'snapshot_pre_contract_backfill': 213, 'stale_tick_or_quote': 771, 'tick_aggressor_pressure_unusable': 8, 'watching_ai_cooldown_active': 4}`
- stage_counts: `{'ai_confirmed': 68, 'ai_confirmed_terminal_no_budget': 53, 'ai_cooldown_blocked': 4, 'ai_holding_review': 481, 'blocked_ai_score': 38, 'blocked_liquidity': 26, 'blocked_overbought': 9, 'order_bundle_submitted': 8, 'pre_submit_entry_ai_authority_guard_block': 6, 'pre_submit_micro_unavailable_block': 1, 'real_weak_ai_micro_entry_block': 24, 'rising_missed_tick_speed_entry_block': 57, 'scalp_entry_action_decision_snapshot': 554, 'scalp_preset_tp_ai_hold_action': 1}`
- avg_ask_sweep_score: `48.674`
- avg_post_sweep_hold_score: `50.064`
- avg_bid_replenishment_score: `53.471`
- max_vi_proximity_risk: `12`
- warnings: `[]`
