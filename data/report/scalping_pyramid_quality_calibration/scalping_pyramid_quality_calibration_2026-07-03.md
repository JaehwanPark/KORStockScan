# 2026-07-03 Scalping Pyramid Quality Calibration

- generated_at: 2026-07-03T20:10:59+09:00
- family: scalping_pyramid_quality_gate
- stage: scale_in
- calibration_state: adjust_down
- calibration_reason: grid_loosen_profit_threshold_direct
- allowed_runtime_apply: true
- runtime_effect: false
- decision_authority: postclose_calibration_candidate_preopen_only
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Metrics

- calibration_source_scope: one_share_event_opportunity
- one_share_event_source_present: True
- one_share_closed_pyramid_row_count: 90
- sample_count: 90
- recovered_or_extended_rate: 0.33
- reversal_or_flat_rate: 0.50
- correctly_blocked_rate: 0.17
- one_share_pyramid_avg_opportunity_cost_pct: 0.96
- profit_threshold_grid_status: adjust_down
- profit_threshold_grid_reason: grid_loosen_profit_threshold_direct
- profit_threshold_grid_selected_min_profit_pct: 1.1
- profit_threshold_grid_selected_avg_incremental_exit_profit_pct: 0.56
- source_quality_pass: True
- provenance_present: True
