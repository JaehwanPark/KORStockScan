# 2026-07-03 Scalping Pyramid Quality Calibration

- generated_at: 2026-07-03T13:24:56+09:00
- family: scalping_pyramid_quality_gate
- stage: scale_in
- calibration_state: hold
- calibration_reason: mixed_cluster_hold
- allowed_runtime_apply: false
- runtime_effect: false
- decision_authority: postclose_calibration_candidate_preopen_only
- forbidden_uses: intraday_threshold_mutation, intraday_runtime_apply, hard_safety_relaxation, broker_guard_bypass, order_guard_relaxation, quantity_guard_relaxation, position_cap_release, provider_route_change, bot_restart, real_execution_quality_approval

## Metrics

- calibration_source_scope: one_share_event_opportunity
- one_share_event_source_present: True
- one_share_closed_pyramid_row_count: 82
- sample_count: 82
- recovered_or_extended_rate: 0.33
- reversal_or_flat_rate: 0.49
- correctly_blocked_rate: 0.18
- one_share_pyramid_avg_opportunity_cost_pct: 1.00
- source_quality_pass: True
- provenance_present: True
