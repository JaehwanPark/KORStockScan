# 2026-07-16 Scalping Pyramid Quality Calibration

- generated_at: 2026-07-16T20:12:17+09:00
- family: scalping_pyramid_quality_gate
- stage: scale_in
- calibration_state: hold_sample
- calibration_reason: source_quality_not_pass
- allowed_runtime_apply: false
- runtime_effect: false
- decision_authority: postclose_calibration_candidate_preopen_only
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Metrics

- calibration_source_scope: one_share_event_opportunity
- one_share_event_source_present: True
- one_share_closed_pyramid_row_count: 174
- sample_count: 174
- recovered_or_extended_rate: 0.28
- reversal_or_flat_rate: 0.40
- correctly_blocked_rate: 0.32
- one_share_pyramid_avg_opportunity_cost_pct: 0.74
- profit_threshold_grid_status: hold
- profit_threshold_grid_reason: grid_ev_delta_lt_0_20
- profit_threshold_grid_selected_min_profit_pct: 1.7
- profit_threshold_grid_selected_avg_incremental_exit_profit_pct: 0.31
- source_quality_pass: False
- provenance_present: True
